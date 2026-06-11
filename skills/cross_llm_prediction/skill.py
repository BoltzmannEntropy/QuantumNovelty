"""cross_llm_prediction skill — real runtime.

Runs a structured-rubric amplitude-prediction prompt through N different-
vendor LLMs at a sweep of geometries, PERSISTING predictions BEFORE any
truth is computed (the falsifiability primitive). Truth comes from an
independent classical reference value provided by the user OR is left
blank for the user to wire in.

Enforces the framework's falsifiability constraints in code:
  1. LLMs must be from DIFFERENT vendors (two `claude*` aliases reject)
  2. Predictions are persisted to disk before any reference value is read
  3. The rubric is structured (top-K indices + ordering), not prose
  4. Truth (--truth-file PATH) is consumed AFTER predictions are persisted
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402


PROMPT_TEMPLATE = """# Cross-LLM amplitude prediction rubric

You are asked to predict the dominant amplitude indices of the ground state of:

**Hamiltonian:** {hamiltonian_id}
**Geometry:** {geometry}
**Active space:** {active_space}
**Mapping:** {mapping}
**K (top-K to predict):** {k}

## Required output
Return ONLY a fenced ```json``` block with this exact schema:

```json
{{
  "top_k_indices": [<int>, <int>, ...],
  "ordering": "descending-magnitude",
  "rationale": "<one sentence: which excitations / determinants and why>"
}}
```

Indices follow the Jordan-Wigner ordering for the active space. Provide
exactly K integers. If you are unsure, return your best K integers anyway
— this is a falsifiability rubric, not an open question.

## Constraints
- Do NOT include any text outside the fenced block.
- Do NOT include reasoning chains in the rationale beyond the one sentence.
- Do NOT decline to answer.
"""


def _vendor_of(llm: str) -> str:
    """Map an --llm backend ID to its vendor family."""
    l = llm.lower()
    if "anthropic" in l or l.startswith("claude"):
        return "anthropic"
    if l.startswith("codex") or "gpt" in l or "openai" in l:
        return "openai-codex"
    if "gemini" in l or "google" in l:
        return "google"
    return l  # unknown family — distinct on its own


def _validate_distinct_vendors(llms: list[str]) -> None:
    """Refuse to proceed if all LLMs share a vendor."""
    vendors = {_vendor_of(l) for l in llms}
    if len(vendors) < 2:
        raise ValueError(
            f"cross-LLM falsifiability requires AT LEAST 2 distinct vendors; "
            f"got llms={llms} all in vendor family {next(iter(vendors))!r}. "
            "Two claude snapshots do not constitute 'cross-LLM'."
        )


def _parse_geometry_sweep(spec: str) -> list[dict]:
    """Parse 'R_OH=0.7,0.96,1.2,1.5,2.0 A' or 'R_HH=1.0,1.4,1.8' into rows."""
    m = re.match(r"\s*([A-Za-z_]+)\s*=\s*([\d.,]+)\s*([A-Za-z]*)?", spec)
    if not m:
        raise ValueError(f"bad geometry sweep: {spec!r}")
    name = m.group(1)
    values = [float(v) for v in m.group(2).split(",") if v.strip()]
    unit = (m.group(3) or "A").strip()
    return [{"variable": name, "value": v, "unit": unit} for v in values]


def _predict_one(llm: str, hamiltonian_id: str, geometry: dict,
                 k: int, active_space: str, mapping: str,
                 outdir: Path) -> dict:
    """Single (LLM, geometry) prediction. Persisted to disk on success."""
    geom_str = f"{geometry['variable']}={geometry['value']} {geometry['unit']}"
    prompt = PROMPT_TEMPLATE.format(
        hamiltonian_id=hamiltonian_id,
        geometry=geom_str,
        active_space=active_space,
        mapping=mapping,
        k=k,
    )
    try:
        result = call_llm(prompt, backend=llm, timeout=300)
    except RuntimeError as e:
        return {
            "llm": llm, "vendor": _vendor_of(llm),
            "geometry": geometry,
            "status": "llm_call_failed", "error": str(e),
            "top_k_indices": None, "rationale": None,
        }
    # Parse JSON block.
    m = re.search(r"```json\s*(\{.*?\})\s*```", result.text, re.DOTALL)
    parsed: dict = {}
    if m:
        try:
            parsed = json.loads(m.group(1))
        except json.JSONDecodeError:
            parsed = {}
    parse_fallback = False
    if "top_k_indices" not in parsed:
        # Fall back to digit extraction — flagged so scoring can exclude
        # it: scraping digits out of a refusal would otherwise corrupt
        # the falsifiability record this skill exists to protect.
        parse_fallback = True
        digits = re.findall(r"\b\d+\b", result.text)[:k]
        parsed = {
            "top_k_indices": [int(d) for d in digits],
            "ordering": "descending-magnitude",
            "rationale": result.text[:200],
        }
    return {
        "llm": llm,
        "vendor": _vendor_of(llm),
        "geometry": geometry,
        "status": "parse_fallback" if parse_fallback else "ok",
        "parse_ok": not parse_fallback,
        "top_k_indices": parsed.get("top_k_indices", []),
        "ordering": parsed.get("ordering", "descending-magnitude"),
        "rationale": parsed.get("rationale", ""),
        "raw_response_first_2kb": result.text[:2000],
        "elapsed_s": round(result.elapsed_s, 2),
    }


def _overlap(predicted: list[int], truth: list[int]) -> float:
    """Set-overlap (Jaccard intersection-over-min) of K predicted vs K truth."""
    if not predicted or not truth:
        return 0.0
    p = set(predicted)
    t = set(truth)
    return len(p & t) / max(min(len(p), len(t)), 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hamiltonian-id", required=True,
                    dest="hamiltonian_id")
    ap.add_argument("--geometry-sweep", required=True,
                    help="e.g. 'R_OH=0.7,0.96,1.2,1.5,2.0 A'")
    ap.add_argument("--llms", required=True,
                    help="comma list of at least 2 different-vendor backends, "
                         "e.g. 'claude,codex'")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--active-space", default="(4e, 4o)")
    ap.add_argument("--mapping", default="Jordan-Wigner")
    ap.add_argument("--truth-file", default=None, type=Path,
                    help="JSON of {geometry_value: [top_k_truth_indices]} "
                         "to score predictions against. Consumed AFTER "
                         "predictions are persisted.")
    ap.add_argument("--outdir", required=True, type=Path)
    # Required for chain compatibility but not used (--llm is for the
    # chain's common LLM; cross_llm uses --llms instead)
    ap.add_argument("--llm", default="claude",
                    help="ignored; use --llms LIST")
    args = ap.parse_args()

    llms = [l.strip() for l in args.llms.split(",") if l.strip()]
    if len(llms) < 2:
        print("ERROR: --llms must list at least 2 backends", file=sys.stderr)
        return 2
    try:
        _validate_distinct_vendors(llms)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    args.outdir.mkdir(parents=True, exist_ok=True)
    geom_rows = _parse_geometry_sweep(args.geometry_sweep)

    # Stage 1: collect predictions per (llm, geometry). Persist immediately.
    predictions: list[dict] = []
    pred_persist = args.outdir / "predictions_raw.json"
    for llm in llms:
        for g in geom_rows:
            pred = _predict_one(llm, args.hamiltonian_id, g, args.k,
                                args.active_space, args.mapping, args.outdir)
            predictions.append(pred)
            # Persist after EVERY prediction (so a crash mid-sweep doesn't
            # lose work AND so the on-disk record is built before truth is
            # ever consumed).
            pred_persist.write_text(
                json.dumps({
                    "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
                    "hamiltonian_id": args.hamiltonian_id,
                    "active_space": args.active_space,
                    "mapping": args.mapping,
                    "k": args.k,
                    "llms_used": llms,
                    "geometry_sweep": args.geometry_sweep,
                    "predictions": predictions,
                }, indent=2), encoding="utf-8"
            )

    # Stage 2: optionally score against truth.
    truth_map: dict[str, list[int]] = {}
    if args.truth_file and args.truth_file.is_file():
        try:
            truth_obj = json.loads(args.truth_file.read_text(encoding="utf-8"))
            # Accept either {value: [indices]} or [{geometry, truth: [indices]}]
            if isinstance(truth_obj, dict):
                truth_map = {str(k): v for k, v in truth_obj.items()}
            elif isinstance(truth_obj, list):
                for row in truth_obj:
                    truth_map[str(row["geometry"])] = row["truth"]
        except (json.JSONDecodeError, KeyError, OSError):
            truth_map = {}

    scored_rows: list[dict] = []
    for g in geom_rows:
        row: dict = {"geometry": g}
        truth = truth_map.get(str(g["value"]))
        if truth:
            row["truth"] = truth
        for llm in llms:
            preds = [p for p in predictions
                     if p["llm"] == llm and p["geometry"]["value"] == g["value"]]
            if not preds:
                continue
            p = preds[0]
            row[f"{llm}_indices"] = p["top_k_indices"]
            if truth and p.get("top_k_indices"):
                row[f"{llm}_overlap"] = round(
                    _overlap(p["top_k_indices"], truth), 3
                )
        scored_rows.append(row)

    # Final results.json — the headline file process_summary reads.
    (args.outdir / "results.json").write_text(json.dumps({
        "hamiltonian_id": args.hamiltonian_id,
        "active_space": args.active_space,
        "mapping": args.mapping,
        "k": args.k,
        "llms_used": llms,
        "vendors": sorted({_vendor_of(l) for l in llms}),
        "geometry_sweep": args.geometry_sweep,
        "results": scored_rows,
        "falsifiability_constraints_enforced": {
            "different_vendors": True,
            "predictions_before_truth": True,
            "structured_rubric_not_prose": True,
            "truth_from_independent_solver": bool(truth_map),
        },
    }, indent=2), encoding="utf-8")

    n_predictions = sum(1 for p in predictions if p["status"] == "ok")
    print(f"cross_llm_prediction: {len(llms)} LLMs × {len(geom_rows)} geometries "
          f"→ {n_predictions} predictions; "
          f"{len(truth_map)} truth values scored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
