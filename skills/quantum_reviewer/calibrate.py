#!/usr/bin/env python3
"""Deterministic reviewer-calibration harness (ARS calibration mode, done in code).

The existing `--mode calibration` asks the LLM to write a calibration report.
This harness instead MEASURES the panel: it runs the full 5-voice review over
a labeled gold set, parses each panel deterministically with
`extract_quality_gate`, and computes confusion counts, FNR/FPR, accuracy, and
a threshold-sweep AUC in code, with zero extra LLM calls beyond the reviews
themselves. Use it before trusting panel verdicts on real submissions.

Gold-set layout (one item per paper):
    goldset/
      paperA.md            (or .pdf/.txt — anything load_paper_text accepts)
      paperA.label.json    {"ground_truth": "accept"}   # or "reject"
      paperB.pdf
      paperB.label.json    {"ground_truth": "reject"}

Usage:
    python skills/quantum_reviewer/calibrate.py \
        --gold-set goldset/ --outdir runs/calibration_01 --llm claude

Outputs:
    <outdir>/<item>/review_panel.md + _quality_gate.json   (per paper)
    <outdir>/_calibration_metrics.json                     (aggregate, code-emitted)
    <outdir>/calibration_report.md                         (aggregate, code-emitted)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

LABEL_SUFFIX = ".label.json"
POSITIVE = "accept"   # panel-should-pass papers
NEGATIVE = "reject"   # panel-should-fail papers


def discover_gold_set(gold_dir: Path) -> list[dict]:
    """Pair each paper file with its .label.json sidecar."""
    items = []
    for label_path in sorted(gold_dir.glob(f"*{LABEL_SUFFIX}")):
        stem = label_path.name[: -len(LABEL_SUFFIX)]
        paper = None
        for ext in (".md", ".txt", ".pdf", ".tex"):
            cand = gold_dir / f"{stem}{ext}"
            if cand.is_file():
                paper = cand
                break
        if paper is None:
            print(f"WARNING: label {label_path.name} has no paper file; skipped",
                  file=sys.stderr)
            continue
        label = json.loads(label_path.read_text(encoding="utf-8"))
        truth = str(label.get("ground_truth", "")).lower()
        if truth not in (POSITIVE, NEGATIVE):
            print(f"WARNING: {label_path.name} ground_truth must be "
                  f"'{POSITIVE}' or '{NEGATIVE}'; skipped", file=sys.stderr)
            continue
        items.append({"name": stem, "paper": paper, "ground_truth": truth})
    return items


def run_panel(paper: Path, outdir: Path, llm: str, threshold: float,
              timeout_s: int = 3000) -> dict | None:
    """Run the full 5-voice panel on one paper; return its quality gate."""
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(HERE / "skill.py"),
        "--mode", "full",
        "--draft", str(paper),
        "--outdir", str(outdir),
        "--llm", llm,
        "--gate-threshold", str(threshold),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout_s, cwd=str(ROOT))
    gate_path = outdir / "_quality_gate.json"
    if proc.returncode != 0 or not gate_path.is_file():
        print(f"WARNING: panel failed for {paper.name} "
              f"(rc={proc.returncode}); stderr tail: "
              f"{(proc.stderr or '')[-300:]}", file=sys.stderr)
        return None
    return json.loads(gate_path.read_text(encoding="utf-8"))


def compute_metrics(records: list[dict], threshold: float) -> dict:
    """Pure function: confusion counts, FNR/FPR, accuracy, and AUC.

    Each record: {"name", "ground_truth", "score" (float|None),
    "panel_pass" (bool|None)}. Records with a missing score are counted as
    unusable and excluded from the rates (reported separately).

    AUC is the Mann-Whitney U statistic over the mean panel score: the
    probability that a randomly chosen accept-labeled paper scores above a
    randomly chosen reject-labeled paper (ties count half).
    """
    usable = [r for r in records
              if r.get("score") is not None and r.get("panel_pass") is not None]
    skipped = [r["name"] for r in records if r not in usable]

    tp = sum(1 for r in usable if r["ground_truth"] == POSITIVE and r["panel_pass"])
    fn = sum(1 for r in usable if r["ground_truth"] == POSITIVE and not r["panel_pass"])
    tn = sum(1 for r in usable if r["ground_truth"] == NEGATIVE and not r["panel_pass"])
    fp = sum(1 for r in usable if r["ground_truth"] == NEGATIVE and r["panel_pass"])

    pos = [r["score"] for r in usable if r["ground_truth"] == POSITIVE]
    neg = [r["score"] for r in usable if r["ground_truth"] == NEGATIVE]
    auc = None
    if pos and neg:
        wins = sum(1.0 if p > n else (0.5 if p == n else 0.0)
                   for p in pos for n in neg)
        auc = round(wins / (len(pos) * len(neg)), 4)

    def _rate(num: int, den: int) -> float | None:
        return round(num / den, 4) if den else None

    return {
        "threshold": threshold,
        "n_items": len(records),
        "n_usable": len(usable),
        "skipped_items": skipped,
        "confusion": {"tp": tp, "fn": fn, "tn": tn, "fp": fp},
        "fnr": _rate(fn, tp + fn),           # accept-labeled papers the panel failed
        "fpr": _rate(fp, tn + fp),           # reject-labeled papers the panel passed
        "accuracy": _rate(tp + tn, len(usable)),
        "auc_mean_score": auc,
        "n_accept_labeled": len(pos),
        "n_reject_labeled": len(neg),
        "source": "deterministic aggregate over per-paper _quality_gate.json "
                  "(code-emitted; no LLM involved in scoring)",
    }


def render_report(metrics: dict, records: list[dict], llm: str) -> str:
    lines = [
        "# Reviewer Calibration Report (code-emitted)",
        "",
        f"Backend: `{llm}` | gate threshold: {metrics['threshold']} | "
        f"items: {metrics['n_items']} (usable: {metrics['n_usable']})",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| FNR (good papers failed) | {metrics['fnr']} |",
        f"| FPR (bad papers passed) | {metrics['fpr']} |",
        f"| Accuracy | {metrics['accuracy']} |",
        f"| AUC (mean panel score) | {metrics['auc_mean_score']} |",
        "",
        "| Paper | Ground truth | Mean score | Panel pass |",
        "|---|---|---|---|",
    ]
    for r in records:
        lines.append(f"| {r['name']} | {r['ground_truth']} | "
                     f"{r.get('score')} | {r.get('panel_pass')} |")
    lines += [
        "",
        "Interpretation: FNR is the fraction of accept-labeled papers the "
        "panel rejected at this threshold; FPR is the fraction of "
        "reject-labeled papers it passed. AUC is threshold-free: the "
        "probability an accept-labeled paper outscores a reject-labeled one.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold-set", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--gate-threshold", default=7.0, type=float)
    ap.add_argument("--max-papers", default=0, type=int,
                    help="cap the number of gold-set items (0 = all)")
    args = ap.parse_args()

    if not args.gold_set.is_dir():
        print(f"ERROR: --gold-set is not a directory: {args.gold_set}",
              file=sys.stderr)
        return 2
    items = discover_gold_set(args.gold_set)
    if not items:
        print("ERROR: gold set contains no usable (paper, label) pairs",
              file=sys.stderr)
        return 2
    if args.max_papers:
        items = items[: args.max_papers]

    args.outdir.mkdir(parents=True, exist_ok=True)
    records = []
    for item in items:
        gate = run_panel(item["paper"], args.outdir / item["name"],
                         args.llm, args.gate_threshold)
        records.append({
            "name": item["name"],
            "ground_truth": item["ground_truth"],
            "score": None if gate is None else gate.get("score_1_to_10"),
            "panel_pass": None if gate is None else gate.get("passes_threshold"),
        })
        print(f"calibrate: {item['name']} truth={item['ground_truth']} "
              f"score={records[-1]['score']} pass={records[-1]['panel_pass']}",
              flush=True)

    metrics = compute_metrics(records, args.gate_threshold)
    metrics["records"] = records
    (args.outdir / "_calibration_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8")
    (args.outdir / "calibration_report.md").write_text(
        render_report(metrics, records, args.llm), encoding="utf-8")
    print(f"calibrate: wrote {args.outdir / 'calibration_report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
