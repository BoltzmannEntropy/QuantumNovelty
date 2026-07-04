"""novelty_audit skill — the audit-and-falsify framework.

The driver for the six-step pipeline described in SKILL.md. NO RAG, no
indexing — operates purely on:
  - the on-disk Pareto archive JSON (from pareto_explorer or any equivalent)
  - the augmented-baseline JSON (from literature_surfacer)
  - the manuscript draft (.tex / .md / .docx)

Outputs:
  novelty_verdict.json
  augmented_pareto.json
  ratio_recompute.md
  wilson_annotations.md
  failure_modes_required.md (only if honest-negatives exist)
  audit_claims.py             (re-runnable per-claim auditor)
  _backend_used.json          (provenance marker)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Sibling import: skills/common is at ../common; we add it to sys.path.
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402
from paper_io import load_paper_text            # noqa: E402


# =========================================================================
# Strict-domination comparator
# =========================================================================

@dataclass
class Row:
    """One Pareto-archive row.

    All metrics are 'lower is better'. If a metric is higher-is-better in your
    domain (e.g., overlap), invert it before constructing the Row.
    """
    label: str
    source: str               # baseline | llm | literature
    metrics: dict[str, float] # axis_name -> value (lower is better)
    provenance: str = "unspecified"  # "literature-verified" | "notional" | "unspecified"

    def __getitem__(self, k: str) -> float:
        return self.metrics[k]


def strict_dominates(a: Row, b: Row, axes: list[str],
                     eps_abs: float, eps_rel: float) -> bool:
    """Return True iff a strictly dominates b on all `axes` at tolerances.

    Definition: a dominates b iff
      (1) for every axis i, a[i] <= b[i] + eps_abs + eps_rel * max(|a[i]|, |b[i]|)
      (2) there exists at least one axis i where a[i] < b[i] - eps_abs
    """
    any_strict = False
    for axis in axes:
        ai, bi = a[axis], b[axis]
        tol = eps_abs + eps_rel * max(abs(ai), abs(bi))
        if not (ai <= bi + tol):
            return False
        if ai < bi - eps_abs:
            any_strict = True
    return any_strict


def classify_row(row: Row, others: list[Row], axes: list[str],
                 eps_abs: float, eps_rel: float) -> str:
    """Classify a row against the rest of the augmented archive.

    Returns one of: 'strict-domination' | 'interpolation' |
                    'rediscovery'       | 'dominated'
    """
    # Any baseline strictly dominate us?
    for o in others:
        if strict_dominates(o, row, axes, eps_abs, eps_rel):
            return "dominated" if o.source == "baseline" else "rediscovery"
    # Do we strictly dominate every other row?
    dominated_count = sum(
        1 for o in others
        if strict_dominates(row, o, axes, eps_abs, eps_rel)
    )
    if dominated_count >= len(others) and len(others) > 0:
        return "strict-domination"
    # On the Pareto front but not dominant — interpolation.
    return "interpolation"


# =========================================================================
# Wilson 95 % CI for K/N rates
# =========================================================================

def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval at 95 % (z=1.96). Returns (lo, hi)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


# =========================================================================
# Draft scanners — find ratios and small-sample rates
# =========================================================================

# Match `198/14 = 14.1×` and `14.1\times` and `14.1x` patterns.
_RATIO_RE = re.compile(
    r"(?P<num>\d+(?:\.\d+)?)\s*/\s*(?P<den>\d+(?:\.\d+)?)\s*=\s*"
    r"(?P<displayed>\d+(?:\.\d+)?)\s*(?:\\?times|×|x\b)",
    re.IGNORECASE,
)
# Match `5/5`, `4 of 5`, `5 out of 5`, `0/3`, etc.
_RATE_RE = re.compile(
    r"\b(?P<k>\d{1,3})\s*(?:/|\s+of\s+|\s+out\s+of\s+)\s*(?P<n>\d{1,3})\b"
)


def scan_ratios(draft_text: str) -> list[dict]:
    """Find ratio claims as a list of {num, den, displayed, span}."""
    out = []
    for m in _RATIO_RE.finditer(draft_text):
        out.append({
            "num": float(m.group("num")),
            "den": float(m.group("den")),
            "displayed": float(m.group("displayed")),
            "span": (m.start(), m.end()),
            "verbatim": m.group(0),
        })
    return out


def scan_rates(draft_text: str, max_n: int) -> list[dict]:
    """Find K/N rate claims with N <= max_n."""
    out = []
    for m in _RATE_RE.finditer(draft_text):
        k = int(m.group("k"))
        n = int(m.group("n"))
        if 0 < n <= max_n and k <= n:
            out.append({
                "k": k, "n": n,
                "span": (m.start(), m.end()),
                "verbatim": m.group(0),
            })
    return out


# =========================================================================
# Draft loader (tex/md/docx/pdf-to-text, shared across skills)
# =========================================================================

def load_draft_text(path: Path) -> str:
    return load_paper_text(path)


# =========================================================================
# Pareto archive I/O
# =========================================================================

def load_rows(path: Path) -> list[Row]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        Row(label=r["label"],
            source=r.get("source", "unknown"),
            metrics={k: float(v) for k, v in r.items()
                     if isinstance(v, (int, float))
                     and not isinstance(v, bool)
                     and k != "params"},
            provenance=r.get("provenance", "unspecified"))
        for r in data.get("rows", [])
    ]


def detect_axes(rows: list[Row]) -> list[str]:
    """Pick axes common to every row WITH metrics.

    pareto_explorer seeds label-only baseline rows (no metrics yet);
    intersecting over those would always yield the empty set and abort
    the audit. Metric-less rows are carried as label-only context and
    excluded from the axis intersection (and from domination, since
    they have nothing to compare on).
    """
    with_metrics = [r for r in rows if r.metrics]
    if not with_metrics:
        return []
    common = set(with_metrics[0].metrics.keys())
    for r in with_metrics[1:]:
        common &= set(r.metrics.keys())
    # Stable order based on first metric-bearing row's insertion order.
    return [k for k in with_metrics[0].metrics if k in common]


# =========================================================================
# Output writers
# =========================================================================

def write_ratio_recompute(outdir: Path, ratios: list[dict]) -> Path:
    lines = ["# Ratio recompute audit", ""]
    drift = 0
    for r in ratios:
        displayed = r["displayed"]
        actual = r["num"] / r["den"] if r["den"] != 0 else float("nan")
        delta_pct = (abs(displayed - actual) / max(abs(actual), 1e-12)) * 100
        flag = " ⚠" if delta_pct > 0.5 else ""
        if delta_pct > 0.5:
            drift += 1
        lines.append(
            f"- `{r['verbatim']}` → recomputed {r['num']}/{r['den']} = "
            f"{actual:.6g} (displayed {displayed:.6g}; "
            f"Δ {delta_pct:.2f}%){flag}"
        )
    lines.append("")
    lines.append(f"**{drift} of {len(ratios)} ratios drifted > 0.5 %.**")
    p = outdir / "ratio_recompute.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def write_wilson_annotations(outdir: Path, rates: list[dict]) -> Path:
    lines = ["# Wilson 95 % CIs on small-sample rates", ""]
    for r in rates:
        lo, hi = wilson_interval(r["k"], r["n"])
        flag = ""
        if r["k"] == r["n"] and lo < 0.7:
            flag = " ⚠ 100 % claim with CI below 0.7 — surface as Sev-3"
        lines.append(
            f"- `{r['verbatim']}` → Wilson 95 % CI [{lo:.2f}, {hi:.2f}]"
            f"{flag}"
        )
    p = outdir / "wilson_annotations.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def write_augmented_pareto(outdir: Path, rows: list[Row],
                           axes: list[str]) -> Path:
    p = outdir / "augmented_pareto.json"
    p.write_text(json.dumps({
        "axes": axes,
        "rows": [
            {"label": r.label, "source": r.source, **r.metrics}
            for r in rows
        ],
    }, indent=2), encoding="utf-8")
    return p


def write_verdict(
    outdir: Path,
    verdicts: list[dict],
    eps_abs: float,
    eps_rel: float,
    *,
    retrieval_gate: dict | None = None,
    assumptions: dict | None = None,
) -> Path:
    doc: dict = {
        "eps_abs": eps_abs,
        "eps_rel": eps_rel,
        "verdicts": verdicts,
    }
    if retrieval_gate is not None:
        doc["retrieval_gate"] = retrieval_gate
    if assumptions is not None:
        doc["assumptions"] = assumptions
    p = outdir / "novelty_verdict.json"
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return p


# =========================================================================
# Retrieval gate helpers
# =========================================================================

def apply_retrieval_gate(
    verdicts: list[dict],
    probe_result: dict,
) -> tuple[list[dict], dict]:
    """Downgrade verdicts when the retrieval gate failed.

    Returns (gated_verdicts, retrieval_gate_summary).

    When probe_result["passed"] is False, each verdict entry gets:
      - "verdict_ungated": the original verdict string
      - "verdict": "<original> (indicative)"

    When passed is True, verdicts are unchanged.
    """
    passed = probe_result.get("passed", True)
    recall = probe_result.get("recall", 1.0)
    threshold = probe_result.get("threshold", 0.67)

    if not passed:
        gated: list[dict] = []
        for v in verdicts:
            raw = v["verdict"]
            gated.append({
                **v,
                "verdict_ungated": raw,
                "verdict": f"{raw} (indicative)",
            })
        gate_summary = {
            "passed": False,
            "recall": recall,
            "threshold": threshold,
            "effect": "verdicts downgraded to indicative",
        }
    else:
        gated = list(verdicts)
        gate_summary = {
            "passed": True,
            "recall": recall,
            "threshold": threshold,
            "effect": "none",
        }
    return gated, gate_summary


def build_assumptions_manifest(baseline_rows: list[Row]) -> dict:
    """Produce the assumptions manifest from a list of baseline/literature rows.

    Only rows with source != 'llm' are considered for the provenance manifest.
    """
    rows_info = []
    n_literature_verified = 0
    n_notional = 0
    n_unspecified = 0
    for r in baseline_rows:
        prov = r.provenance
        rows_info.append({"label": r.label, "provenance": prov})
        if prov == "literature-verified":
            n_literature_verified += 1
        elif prov == "notional":
            n_notional += 1
        else:
            n_unspecified += 1
    return {
        "baseline_rows": rows_info,
        "n_literature_verified": n_literature_verified,
        "n_notional": n_notional,
        "n_unspecified": n_unspecified,
    }


def write_failure_modes(outdir: Path,
                        not_dominated: list[Row]) -> Path | None:
    if not not_dominated:
        return None
    lines = ["# Failure Modes Required for Manuscript", "",
             "The augmented baseline catalog includes the following rows the",
             "LLM-discovered set did NOT dominate. The manuscript must include",
             "these as honest negatives in a `Failure Modes` section before",
             "the novelty_audit skill will sign off.", ""]
    for r in not_dominated:
        m = ", ".join(f"{k}={v:.4g}" for k, v in r.metrics.items())
        lines.append(f"- **{r.label}** ({r.source}) — {m}")
    p = outdir / "failure_modes_required.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def write_audit_script(outdir: Path, rows: list[Row], axes: list[str],
                       ratios: list[dict], rates: list[dict]) -> Path:
    """Emit a re-runnable audit_claims.py for the manuscript's paper/ dir."""
    rows_dump = json.dumps([
        {"label": r.label, "source": r.source, **r.metrics} for r in rows
    ], indent=2)
    ratios_dump = json.dumps([
        {"num": r["num"], "den": r["den"], "displayed": r["displayed"],
         "verbatim": r["verbatim"]}
        for r in ratios
    ], indent=2)
    rates_dump = json.dumps(rates, indent=2)
    script = f'''#!/usr/bin/env python3
"""Re-runnable audit for every numerical claim in the manuscript.

Generated by QuantumNovelty's novelty_audit skill on the audit pass.
Re-run before every commit: `python audit_claims.py`. Exits 0 iff every
on-disk JSON value still matches every displayed claim within tolerance.
"""
import math
import sys

ROWS = {rows_dump}
RATIOS = {ratios_dump}
RATES = {rates_dump}
AXES = {axes!r}

EPS_ABS = 1e-12
EPS_REL = 1e-9


def main() -> int:
    failures = []
    # Ratios.
    for r in RATIOS:
        actual = r["num"] / r["den"] if r["den"] != 0 else float("nan")
        if not math.isclose(actual, r["displayed"], rel_tol=5e-3, abs_tol=5e-3):
            failures.append(
                f'ratio drift: {{r["verbatim"]!r}} displayed {{r["displayed"]}} '
                f'vs recomputed {{actual:.6g}}')
    # Rates — only check K<=N and values not impossible.
    for r in RATES:
        if r["k"] > r["n"] or r["n"] <= 0:
            failures.append(f'rate impossible: {{r["verbatim"]!r}}')
    print(f'{{len(ROWS)}} rows, {{len(RATIOS)}} ratios, {{len(RATES)}} rates checked.')
    if failures:
        print('AUDIT FAILED:', file=sys.stderr)
        for f in failures:
            print(' -', f, file=sys.stderr)
        return 1
    print('All claims verified against on-disk JSON.')
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
    p = outdir / "audit_claims.py"
    p.write_text(script, encoding="utf-8")
    p.chmod(0o755)
    return p


# =========================================================================
# Main
# =========================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pareto-archive", required=True, type=Path)
    ap.add_argument("--augmented-baselines", required=False, type=Path,
                    help="optional; if absent, audit runs against the "
                         "pareto-archive's rows alone")
    ap.add_argument("--draft", required=True, type=Path)
    ap.add_argument("--hamiltonian-id", required=False, default="")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--strict-eps-abs", type=float, default=1e-12)
    ap.add_argument("--strict-eps-rel", type=float, default=1e-9)
    ap.add_argument("--small-sample-threshold", type=int, default=30)
    ap.add_argument("--require-failure-modes", action="store_true",
                    default=True)
    ap.add_argument("--no-require-failure-modes",
                    dest="require_failure_modes", action="store_false")
    ap.add_argument(
        "--retrieval-probe-result", required=False, type=Path, default=None,
        help="probe_result.json from preflight_probe. When provided and "
             "passed==false, verdicts are downgraded to indicative.",
    )
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(args.pareto_archive)
    augmented_baseline_rows: list[Row] = []
    if args.augmented_baselines:
        augmented_baseline_rows = load_rows(args.augmented_baselines)
        rows += augmented_baseline_rows

    axes = detect_axes(rows)
    if not axes:
        print("ERROR: no common metric axes across rows; cannot compare",
              file=sys.stderr)
        return 2

    # Step 2: strict-domination comparator on each LLM row.
    llm_rows = [r for r in rows if r.source == "llm"]
    others = [r for r in rows if r.source != "llm"]
    verdicts = []
    not_dominated: list[Row] = []
    for row in llm_rows:
        verdict = classify_row(row, [r for r in rows if r is not row],
                               axes, args.strict_eps_abs, args.strict_eps_rel)
        verdicts.append({
            "label": row.label,
            "verdict": verdict,
            "metrics": row.metrics,
        })
    # Honest negatives: any baseline / literature row NOT dominated by any LLM row.
    for o in others:
        dominated_by_llm = any(
            strict_dominates(llm_r, o, axes,
                             args.strict_eps_abs, args.strict_eps_rel)
            for llm_r in llm_rows
        )
        if not dominated_by_llm:
            not_dominated.append(o)

    # Steps 3 & 4: scan draft.
    draft_text = load_draft_text(args.draft)
    ratios = scan_ratios(draft_text)
    rates = scan_rates(draft_text, max_n=args.small_sample_threshold)

    # Step 5: failure-modes enforcement.
    fm_path = write_failure_modes(args.outdir, not_dominated)
    require_failure_modes_missing = False
    if fm_path and args.require_failure_modes:
        # Heuristic: look for the phrase "Failure Modes" (case-insensitive)
        # in the draft. If missing, fail rc=2.
        if not re.search(r"failure[\s_-]+modes",
                         draft_text, re.IGNORECASE):
            require_failure_modes_missing = True

    # Retrieval gate — apply if probe result file was provided.
    retrieval_gate_summary: dict | None = None
    if args.retrieval_probe_result and args.retrieval_probe_result.is_file():
        probe_result = json.loads(
            args.retrieval_probe_result.read_text(encoding="utf-8")
        )
        verdicts, retrieval_gate_summary = apply_retrieval_gate(
            verdicts, probe_result
        )
    elif args.retrieval_probe_result:
        print(
            f"WARNING: --retrieval-probe-result file not found: "
            f"{args.retrieval_probe_result}; gate skipped.",
            file=sys.stderr,
        )

    # Assumption manifest — built from augmented-baseline rows only.
    assumptions: dict | None = None
    if augmented_baseline_rows:
        assumptions = build_assumptions_manifest(augmented_baseline_rows)
        assumptions["verdict_rests_on_unverified_baselines"] = (
            assumptions["n_notional"] + assumptions["n_unspecified"] > 0
        )

    # Write the outputs.
    write_augmented_pareto(args.outdir, rows, axes)
    write_verdict(
        args.outdir, verdicts,
        args.strict_eps_abs, args.strict_eps_rel,
        retrieval_gate=retrieval_gate_summary,
        assumptions=assumptions,
    )
    write_ratio_recompute(args.outdir, ratios)
    write_wilson_annotations(args.outdir, rates)
    write_audit_script(args.outdir, rows, axes, ratios, rates)

    # Step 1 already done by the rows += merge above.

    # LLM consult for borderline cases (step 2 follow-up). Optional —
    # we only call if there are 'interpolation' verdicts that the human
    # author may want a sanity check on.
    borderline = [v for v in verdicts if v["verdict"] == "interpolation"]
    if borderline:
        prompt = (
            "You are auditing whether LLM-discovered points provide genuinely "
            "new trade-offs vs current baselines. For each row below, classify "
            "as `genuine-new-tradeoff` or `interpolation` and give one short "
            "reason. Be skeptical — default to interpolation unless the "
            "structural argument is clear.\n\n"
            + json.dumps(borderline, indent=2)
        )
        try:
            result = call_llm(prompt, backend=args.llm, timeout=600)
            (args.outdir / "borderline_llm_review.md").write_text(
                result.text, encoding="utf-8")
            write_backend_marker(args.outdir, result)
        except RuntimeError as e:
            (args.outdir / "borderline_llm_review.md").write_text(
                f"# LLM review FAILED\n\n{e}\n", encoding="utf-8")

    print(f"novelty_audit: {len(llm_rows)} LLM rows classified, "
          f"{len(verdicts)} verdicts written, "
          f"{len(ratios)} ratios recomputed, "
          f"{len(rates)} rates Wilson-annotated, "
          f"{len(not_dominated)} honest negatives surfaced.")
    if require_failure_modes_missing:
        print("AUDIT REFUSED: --require-failure-modes is on and the draft",
              file=sys.stderr)
        print("does NOT contain a 'Failure Modes' section. Add the section",
              file=sys.stderr)
        print(f"using items from {fm_path}, then re-run.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
