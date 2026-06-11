"""ablation_designer skill — real runtime.

Designs and orchestrates the four standard ablation tests that distinguish
"the LLM contributed" from "random would have worked":

  axis 1: llm-mutator-onoff       — LLM mutator vs grammar-respecting random
  axis 2: commutation-hint-onoff  — hint in prompt vs no hint
  axis 3: pareto-seeding-onoff    — Pareto-front seeding vs blank
  axis 4: cross-vendor            — same prompt, different vendor

This skill does NOT execute the ablation runs directly (that requires
your discovery harness — `pareto_explorer` does this in a full pipeline).
Instead it designs the run plan + emits a structured `ablation_results.json`
schema that the user populates by running the variants with their
discovery loop, then reads back here for the LLM-drafted interpretation.

For the simple case where the user already HAS measured per-axis
results, supply `--results-file PATH` and the skill computes a structured
interpretation directly.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402


KNOWN_AXES = {
    "llm-mutator-onoff",
    "commutation-hint-onoff",
    "pareto-seeding-onoff",
    "cross-vendor",
}


PLAN_TEMPLATE = """# Ablation plan

## Axis under test
{axis}

## Hamiltonian
{hamiltonian_id}

## Seeds requested
{seeds}

## Proposals per seed
{proposals_per_seed}

## Required variants

For axis `{axis}`, run:
{variants}

## Per-variant evaluation

For each variant, the discovery loop must produce a JSON record per seed:

```json
{{
  "axis": "{axis}",
  "variant": "<variant-name>",
  "seed": <int>,
  "final_energy_ha": <float>,
  "delta_e_mha": <float>,
  "n_proposals_consumed": <int>,
  "best_circuit_label": "<string>",
  "params": <int>,
  "ops": <int>,
  "cnots": <int>
}}
```

Aggregate the per-seed records into `ablation_results.json` with this schema:

```json
{{
  "axis": "{axis}",
  "hamiltonian_id": "{hamiltonian_id}",
  "variants": {{
    "<variant-name>": [
      {{"seed": <int>, "delta_e_mha": <float>,
       "n_proposals_consumed": <int>, ...}}
    ]
  }}
}}
```

Then re-run this skill with `--results-file ablation_results.json` for
the LLM-drafted interpretation.
"""


INTERPRETATION_PROMPT = """# Ablation interpretation

You are interpreting an ablation result. Be sceptical of "the LLM was
load-bearing" claims; default to "random would have worked" unless the
evidence is clear.

## Axis
{axis}

## Hamiltonian
{hamiltonian_id}

## Per-variant results (from on-disk measurements)
```json
{results}
```

## Required output

### 1. Headline (one sentence)
"On axis X for Hamiltonian Y, variant V was load-bearing / not load-bearing
because Z."

### 2. Quantitative comparison
Per-variant: median ΔE (mHa), median n_proposals, ratio vs control.

### 3. Statistical confidence
For each contrast, state whether the difference is robust or
within-variance. Compute Cohen's d if N≥3 per variant; otherwise say
"underpowered to distinguish."

### 4. Honest negatives
List any variant whose result was WORSE than expected, even if not the
headline. The reader should not learn about a surprise failure only by
reading the JSON.

### 5. What this means for the paper
One paragraph: should the user keep the axis as load-bearing in the
manuscript, or remove the claim?

## Constraints
- DO NOT inflate the LLM's contribution; default to honest negative.
- Cite specific median/mean numbers from the results JSON.
- If N=1 per variant, say so — N=1 is not evidence of robustness.
"""


def design_plan(args: argparse.Namespace) -> str:
    """Render the plan markdown."""
    variants_per_axis = {
        "llm-mutator-onoff": (
            "- `llm-on` — discovery loop with LLM mutator active\n"
            "- `random-on` — same loop with grammar-respecting random mutator (LLM off)"
        ),
        "commutation-hint-onoff": (
            "- `hint-on`  — prompt contains the Hamiltonian's commutation structure\n"
            "- `hint-off` — prompt omits commutation hints"
        ),
        "pareto-seeding-onoff": (
            "- `seeding-on`  — prompt seeded with current Pareto front\n"
            "- `seeding-off` — prompt seeded with empty archive"
        ),
        "cross-vendor": (
            "- `claude`  — same prompt + harness, Anthropic Claude\n"
            "- `codex`   — same prompt + harness, OpenAI Codex"
        ),
    }
    return PLAN_TEMPLATE.format(
        axis=args.axis,
        hamiltonian_id=args.hamiltonian_id or "<set --hamiltonian-id>",
        seeds=args.seeds,
        proposals_per_seed=args.proposals_per_seed,
        variants=variants_per_axis.get(args.axis,
                                        "  (axis not in catalog; define your own variants)"),
    )


def compute_summary(results: dict) -> dict:
    """Deterministic per-variant summary (no LLM)."""
    import statistics
    variants = results.get("variants", {})
    summary: dict = {"axis": results.get("axis"),
                     "per_variant": {}}
    for vname, rows in variants.items():
        if not isinstance(rows, list) or not rows:
            continue
        deltas = [r.get("delta_e_mha") for r in rows
                  if isinstance(r.get("delta_e_mha"), (int, float))]
        props = [r.get("n_proposals_consumed") for r in rows
                 if isinstance(r.get("n_proposals_consumed"), (int, float))]
        summary["per_variant"][vname] = {
            "n_seeds": len(rows),
            "delta_e_mha_median": (statistics.median(deltas)
                                   if deltas else None),
            "delta_e_mha_stdev": (statistics.stdev(deltas)
                                  if len(deltas) >= 2 else None),
            "n_proposals_median": (statistics.median(props)
                                   if props else None),
        }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--axis", required=True, choices=sorted(KNOWN_AXES))
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--hamiltonian-id", default=None)
    ap.add_argument("--seeds", default="0,1,2",
                    help="comma list of seeds, default 0,1,2")
    ap.add_argument("--proposals-per-seed", type=int, default=15)
    ap.add_argument("--results-file", default=None, type=Path,
                    help="if supplied, skip plan emission and compute "
                         "summary + LLM interpretation directly")
    ap.add_argument("--llm", default="claude")
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    # If no results yet, emit the plan and exit.
    if args.results_file and not args.results_file.is_file():
        print(f"ERROR: --results-file does not exist: {args.results_file}",
              file=sys.stderr)
        return 2
    if not (args.results_file and args.results_file.is_file()):
        plan = design_plan(args)
        (args.outdir / "ablation_plan.md").write_text(plan, encoding="utf-8")
        (args.outdir / "ablation_results.json").write_text(
            json.dumps({
                "axis": args.axis,
                "hamiltonian_id": args.hamiltonian_id,
                "_note": "no --results-file supplied; this is a SCHEMA "
                         "placeholder. Run your discovery loop per the "
                         "ablation_plan.md variants, then re-invoke with "
                         "--results-file populated.",
                "variants": {},
            }, indent=2), encoding="utf-8")
        print(f"ablation_designer: plan written to {args.outdir}; "
              "supply --results-file to compute interpretation")
        return 0

    # Else: results in hand — compute summary + LLM interpretation.
    try:
        results = json.loads(args.results_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: could not parse --results-file: {e}", file=sys.stderr)
        return 2

    summary = compute_summary(results)
    (args.outdir / "ablation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    # Persist the results we read (so downstream skills see them under
    # this skill's dir without symlinks).
    (args.outdir / "ablation_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")

    prompt = INTERPRETATION_PROMPT.format(
        axis=results.get("axis", args.axis),
        hamiltonian_id=results.get("hamiltonian_id",
                                    args.hamiltonian_id or "<unspecified>"),
        results=json.dumps({**results, "_summary": summary}, indent=2)[:18000],
    )
    try:
        result = call_llm(prompt, backend=args.llm, timeout=900)
        (args.outdir / "interpretation.md").write_text(
            result.text, encoding="utf-8")
        write_backend_marker(args.outdir, result)
    except RuntimeError as e:
        (args.outdir / "interpretation.md").write_text(
            f"# ⚠ ablation interpretation FAILED\n\n"
            f"Backend {args.llm}: `{e}`\n\nSummary is in "
            "`ablation_summary.json`.\n", encoding="utf-8")

    print(f"ablation_designer: interpreted axis={results.get('axis')}, "
          f"{len(summary['per_variant'])} variants summarised")
    return 0


if __name__ == "__main__":
    sys.exit(main())
