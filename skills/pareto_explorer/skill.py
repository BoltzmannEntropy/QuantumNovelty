"""pareto_explorer skill — LLM-in-loop Pareto-front discovery.

Drives an LLM mutation loop on a quantum-circuit ansatz, building a Pareto
archive over (energy, parameter_count, op_count, CNOT_count). Each
generation the LLM proposes K candidate ansätze; the evaluator computes
their metrics against a fixed Hamiltonian; non-dominated points join the
archive at strict-domination tolerances.

Three evaluation modes:

  built-in (default) — candidates are JSON gate lists evaluated by the
      bundled numpy statevector simulator + SPSA optimizer
      (builtin_evaluator.py). Real numbers, no quantum SDK, no code
      execution of LLM output. Hamiltonian registry: TFIM_<n>q,
      HEISENBERG_<n>q (n = 2..10), H2_2q.

  --evaluator-cmd CMD — bring your own simulator. Candidates are Python
      ```python`` blocks written to files; CMD receives the file path as
      its last argument and emits metrics JSON on stdout
      ({"energy_ha": ..., "params": ..., "ops": ..., "cnots": ...}).

  --plan-only — emit the run plan + a stub archive without calling any
      LLM or evaluator.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402


SEED_PROMPT = """# pareto_explorer — generation {gen}

You are evolving variational quantum-circuit ansätze for:

**Hamiltonian:** {hamiltonian_id}
**Qubits:** {n_qubits}

Current Pareto archive (lower-is-better on every axis):

```json
{archive}
```

Baselines for comparison:

```json
{baselines}
```

Propose {samples} new ansatz candidates. Each candidate should ATTEMPT to
strictly dominate at least one existing archive row on at least one axis
(energy_ha, params, ops, cnots) while not regressing on the others.

## Required output

Return exactly {samples} fenced ```python``` blocks, each defining a
function `build_ansatz(params)` that returns a circuit object in the
user's chosen quantum library. Include the parameter count in the
function's docstring as `params: N`.

```python
def build_ansatz(params):
    \"\"\"Candidate g{gen}-s1. params: 10\"\"\"
    # ... circuit body ...
    return circuit
```

## Constraints
- Each candidate must be syntactically valid Python.
- Each candidate must declare its parameter count in the docstring.
- Do NOT repeat ansätze already in the archive.
- Use the commutation structure of the Hamiltonian to inform your choices.
"""


BUILTIN_PROMPT = """# pareto_explorer — generation {gen}

You are evolving variational quantum-circuit ansätze for:

**Hamiltonian:** {hamiltonian_id}
**Qubits:** {n_qubits} (indices 0..{max_q})

Current Pareto archive (lower-is-better on every axis; energy_error_ha
is the gap to the exact ground energy):

```json
{archive}
```

Propose {samples} new ansatz candidates. Each should ATTEMPT to strictly
dominate at least one archive row on at least one axis (energy_ha,
params, ops, cnots) without regressing on the others — e.g. reach the
same energy with fewer parameters or fewer CNOTs.

## Required output — JSON gate lists, NOT framework code

Return exactly {samples} fenced ```json blocks. Each block:

```json
{{"name": "g{gen}-s1",
  "gates": [
    {{"gate": "ry", "q": 0, "param": 0}},
    {{"gate": "cnot", "control": 0, "target": 1}},
    {{"gate": "rz", "q": 1, "param": 1}}
  ]}}
```

Allowed gates:
- "rx" / "ry" / "rz": fields "q" (qubit) and "param" (index into a
  shared parameter vector; reusing an index ties the angles).
- "h" / "x" / "z": field "q".
- "cnot" / "cz": fields "control" and "target".

The optimizer tunes all parameters; parameter count = max index + 1.
The initial state is |0...0>. Maximum 500 gates.

## Constraints
- Valid JSON only inside the fences; no comments.
- Do NOT repeat ansätze already in the archive.
- Exploit the Hamiltonian's structure (e.g. ZZ-chain + transverse field
  for TFIM; entangle only where the Hamiltonian couples).
"""


def _strict_dominates(a: dict, b: dict, axes: list[str],
                       eps_abs: float = 1e-12,
                       eps_rel: float = 1e-9) -> bool:
    """Strict-domination at calibrated tolerances (matches novelty_audit)."""
    any_strict = False
    for ax in axes:
        ai, bi = a.get(ax), b.get(ax)
        if ai is None or bi is None:
            continue
        tol = eps_abs + eps_rel * max(abs(ai), abs(bi))
        if not (ai <= bi + tol):
            return False
        if ai < bi - eps_abs:
            any_strict = True
    return any_strict


def _update_archive(archive: list[dict], candidate: dict,
                    axes: list[str]) -> list[dict]:
    """Merge a new candidate into the archive at Pareto-non-dominance."""
    # Drop any archive row strictly dominated by the candidate.
    archive = [r for r in archive
               if not _strict_dominates(candidate, r, axes)]
    # Skip insertion if the candidate is strictly dominated by anything left.
    if any(_strict_dominates(r, candidate, axes) for r in archive):
        return archive
    archive.append(candidate)
    return archive


def _evaluate(candidate_code: str, evaluator_cmd: str,
              outdir: Path, label: str) -> dict | None:
    """Pipe candidate_code to the user's evaluator command. Parse stdout JSON."""
    eval_dir = outdir / "candidates"
    eval_dir.mkdir(exist_ok=True)
    code_path = eval_dir / f"{label}.py"
    code_path.write_text(candidate_code, encoding="utf-8")
    cmd = shlex.split(evaluator_cmd) + [str(code_path)]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"label": label, "status": "eval_failed", "error": str(e)}
    try:
        metrics = json.loads(proc.stdout.strip().split("\n")[-1])
    except (json.JSONDecodeError, IndexError):
        return {"label": label, "status": "eval_parse_failed",
                "stderr_tail": (proc.stderr or "")[-500:]}
    metrics["label"] = label
    metrics["status"] = "ok"
    return metrics


def _extract_python_blocks(text: str) -> list[str]:
    """Pull all fenced ```python``` blocks from an LLM response."""
    return re.findall(r"```python\s*(.*?)```", text, re.DOTALL)


def _extract_json_blocks(text: str) -> list[str]:
    """Pull all fenced ```json``` blocks from an LLM response."""
    return re.findall(r"```json\s*(.*?)```", text, re.DOTALL)


def _load_builtin():
    """Import the bundled evaluator with a clear error if numpy is absent."""
    try:
        import builtin_evaluator
    except ImportError as e:
        raise RuntimeError(
            "the built-in evaluator needs numpy (`pip install numpy`), "
            f"import failed with: {e}") from e
    return builtin_evaluator


def _evaluate_builtin(be, block: str, H, n: int, label: str,
                      outdir: Path, iters: int = 250) -> dict:
    """Parse + validate + simulate one JSON gate-list candidate."""
    eval_dir = outdir / "candidates"
    eval_dir.mkdir(exist_ok=True)
    (eval_dir / f"{label}.json").write_text(block, encoding="utf-8")
    try:
        gates = be.parse_candidate_json(block)
        return be.evaluate_candidate(gates, H, n, label, iters=iters)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        return {"label": label, "status": "eval_failed", "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hamiltonian", required=True,
                    help="Hamiltonian ID (e.g. LiH_4q_STO-3G_R1.5A)")
    ap.add_argument("--baseline", default="",
                    help="comma-separated baseline labels seeding the archive")
    ap.add_argument("--generations", type=int, default=4)
    ap.add_argument("--samples", type=int, default=4,
                    help="proposals per generation")
    ap.add_argument("--n-qubits", type=int, default=4)
    ap.add_argument("--evaluator-cmd", default=None,
                    help="shell command that takes a circuit file path as last "
                         "arg and emits metrics JSON on stdout. Required for "
                         "real runs; omit for --plan-only.")
    ap.add_argument("--baseline-archive", default=None, type=Path,
                    help="optional pre-existing archive.json to seed the loop")
    ap.add_argument("--plan-only", action="store_true",
                    help="emit plan + stub archive, do not call LLM or evaluator")
    ap.add_argument("--spsa-iters", type=int, default=250,
                    help="SPSA iterations per restart in the built-in "
                         "evaluator (default 250; raise for deeper "
                         "convergence on >8-param ansätze)")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    AXES = ["energy_ha", "params", "ops", "cnots"]

    # Seed archive with --baseline labels + optional --baseline-archive.
    archive: list[dict] = []
    if args.baseline_archive and not args.baseline_archive.is_file():
        print(f"ERROR: --baseline-archive does not exist: "
              f"{args.baseline_archive}", file=sys.stderr)
        return 2
    if args.baseline_archive and args.baseline_archive.is_file():
        try:
            seed = json.loads(args.baseline_archive.read_text(encoding="utf-8"))
            archive.extend(seed.get("rows", []))
        except json.JSONDecodeError:
            pass
    baseline_labels = [b.strip() for b in args.baseline.split(",") if b.strip()]

    # Built-in mode is the default when no external evaluator is given.
    use_builtin = not args.evaluator_cmd and not args.plan_only
    be = H = n_qubits = None
    if use_builtin:
        be = _load_builtin()
        try:
            H, n_qubits = be.build_hamiltonian(args.hamiltonian)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
    else:
        n_qubits = args.n_qubits

    for lbl in baseline_labels:
        if any(r.get("label") == lbl for r in archive):
            continue
        if use_builtin:
            rec = be.evaluate_baseline_label(lbl, H, n_qubits)
            if rec is not None and args.spsa_iters != 250:
                rec = be.evaluate_candidate(
                    be.hea_gates(n_qubits, int(lbl.split("-")[1][:-1])),
                    H, n_qubits, lbl, iters=args.spsa_iters)
                rec["source"] = "baseline" 
            if rec is not None:
                archive.append(rec)
                continue
        archive.append({"label": lbl, "source": "baseline"})

    if args.plan_only:
        plan = (
            f"# Pareto-explorer plan\n\n"
            f"Hamiltonian: {args.hamiltonian}\n"
            f"Generations: {args.generations}\n"
            f"Samples per generation: {args.samples}\n"
            f"Baseline seeds: {baseline_labels}\n"
            f"Backend: {args.llm}\n\n"
            f"## To execute\n"
            f"Supply --evaluator-cmd CMD where CMD takes a candidate's circuit "
            f"file as its last arg and emits metrics JSON on stdout.\n"
        )
        (args.outdir / "_PLAN.md").write_text(plan, encoding="utf-8")
        (args.outdir / "archive.json").write_text(json.dumps({
            "hamiltonian_id": args.hamiltonian,
            "rows": archive,
            "_plan_only": True,
        }, indent=2), encoding="utf-8")
        print(f"pareto_explorer (plan-only): wrote {args.outdir / 'archive.json'}")
        return 0

    # Real discovery loop (built-in or external evaluator)
    for gen in range(1, args.generations + 1):
        if use_builtin:
            prompt = BUILTIN_PROMPT.format(
                gen=gen,
                hamiltonian_id=args.hamiltonian,
                n_qubits=n_qubits,
                max_q=n_qubits - 1,
                archive=json.dumps(archive, indent=2)[:8000],
                samples=args.samples,
            )
        else:
            prompt = SEED_PROMPT.format(
                gen=gen,
                hamiltonian_id=args.hamiltonian,
                n_qubits=n_qubits,
                archive=json.dumps(archive, indent=2)[:8000],
                baselines=json.dumps([{"label": l} for l in baseline_labels],
                                     indent=2),
                samples=args.samples,
            )
        (args.outdir / f"gen_{gen}_prompt.txt").write_text(
            prompt, encoding="utf-8")
        try:
            result = call_llm(prompt, backend=args.llm, timeout=1800)
        except RuntimeError as e:
            print(f"[gen {gen}] LLM call failed: {e}", file=sys.stderr)
            continue
        (args.outdir / f"gen_{gen}_response.txt").write_text(
            result.text, encoding="utf-8")
        write_backend_marker(args.outdir, result)
        blocks = (_extract_json_blocks(result.text) if use_builtin
                  else _extract_python_blocks(result.text))
        for s, block in enumerate(blocks, 1):
            label = f"g{gen}_s{s}"
            if use_builtin:
                metrics = _evaluate_builtin(be, block, H, n_qubits,
                                            label, args.outdir,
                                            iters=args.spsa_iters)
            else:
                metrics = _evaluate(block, args.evaluator_cmd,
                                    args.outdir, label)
            if metrics and metrics.get("status") == "ok":
                metrics["source"] = "llm"
                metrics["model"] = result.backend_actually_used
                archive = _update_archive(archive, metrics, AXES)
            else:
                (args.outdir / f"_eval_failed_{label}.json").write_text(
                    json.dumps(metrics or {"label": label}, indent=2),
                    encoding="utf-8")

    (args.outdir / "archive.json").write_text(json.dumps({
        "hamiltonian_id": args.hamiltonian,
        "axes": AXES,
        "evaluator": ("builtin-numpy-spsa" if use_builtin
                      else args.evaluator_cmd),
        "rows": archive,
    }, indent=2), encoding="utf-8")

    print(f"pareto_explorer: {len(archive)} archive rows after "
          f"{args.generations} generations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
