"""requirements_judge — claim-vs-evidence audit + allowed/forbidden manifest.

Adapted from AutoResearchClaw's requirements-judge gate (ARC's intent-vs-
output audit + binding allowed/forbidden-claims manifest). The numeric
`claims_registry` catches "abstract says 98.3%, table says 87%"; this stage
catches the harder, hypothesis-level failure: a contribution the paper
*asserts* that its own evidence does not actually support (an overclaim),
and the converse — claims the evidence does license.

Mode `review` (paper-audit): the judge reads an existing manuscript,
reconstructs its central claims/contributions, and for each one rules on
whether the paper's own reported evidence supports it. It emits:

  requirements   per-claim {requirement, status, evidence, note}
                 status ∈ met | partial | unmet | unevaluable
  allowed_claims claims the evidence supports (what the paper may assert)
  forbidden_claims claims the evidence does NOT support (overclaims)
  verdict        proceed | partial | reject
  delta_feedback if not proceed: what the paper must change

Conservative fallback (ARC pattern): if the LLM output cannot be parsed
into the manifest, verdict defaults to `reject` with empty manifests and a
note to re-run — an unverifiable audit never waves a paper through.

Outputs:
  requirements_report.json   the manifest above + provenance
  requirements_report.md     human-readable

Exit codes: 0 verdict=proceed, 3 verdict ∈ {partial, reject},
2 bad input, 4 backend produced no output.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402
from journals import journal_policy             # noqa: E402
from paper_io import load_paper_text            # noqa: E402

MODES = {"review": "requirements_report.md"}


def _load_template(mode: str) -> str:
    p = HERE / "prompts" / f"{mode}.md"
    if not p.is_file():
        raise FileNotFoundError(f"prompt template not found: {p}")
    return p.read_text(encoding="utf-8")


def _journal_block(journal: str | None) -> str:
    if not journal:
        return "_(no venue rubric specified; use generic peer-review standards)_"
    try:
        return journal_policy(journal).manifest_md()
    except KeyError:
        return f"_(unknown venue slug: {journal})_"


def extract_json(text: str) -> dict[str, Any] | None:
    """Pull the first JSON object from an LLM reply.

    Tries a ```json fenced block first, then the outermost brace span.
    Returns None when nothing parses — the caller applies the conservative
    reject fallback.
    """
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = []
    if fence:
        candidates.append(fence.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


_VALID_STATUS = {"met", "partial", "unmet", "unevaluable"}
_VALID_VERDICT = {"proceed", "partial", "reject"}


def normalize_report(obj: dict[str, Any]) -> dict[str, Any]:
    """Coerce the LLM object into the manifest schema and enforce the
    verdict-consistency rule: a 'proceed' that still has unmet/unevaluable
    requirements is downgraded to 'partial'."""
    reqs_in = obj.get("requirements") or []
    reqs: list[dict[str, Any]] = []
    for r in reqs_in:
        if not isinstance(r, dict):
            continue
        status = str(r.get("status", "unevaluable")).strip().lower()
        if status not in _VALID_STATUS:
            status = "unevaluable"
        reqs.append({
            "requirement": str(r.get("requirement", "")).strip(),
            "status": status,
            "evidence": str(r.get("evidence", "")).strip() or "none",
            "note": str(r.get("note", "")).strip(),
        })

    verdict = str(obj.get("verdict", "")).strip().lower()
    if verdict not in _VALID_VERDICT:
        verdict = "partial"
    statuses = {r["status"] for r in reqs}
    if not reqs:
        verdict = "reject"
    elif verdict == "proceed" and ({"unmet", "unevaluable"} & statuses):
        verdict = "partial"

    def _as_list(key: str) -> list[str]:
        v = obj.get(key) or []
        return [str(x).strip() for x in v if str(x).strip()] \
            if isinstance(v, list) else []

    return {
        "requirements": reqs,
        "verdict": verdict,
        "allowed_claims": _as_list("allowed_claims"),
        "forbidden_claims": _as_list("forbidden_claims"),
        "delta_feedback": str(obj.get("delta_feedback", "")).strip(),
        "judge_parse_ok": True,
    }


def _reject_fallback(reason: str) -> dict[str, Any]:
    return {
        "requirements": [],
        "verdict": "reject",
        "allowed_claims": [],
        "forbidden_claims": [],
        "delta_feedback": reason,
        "judge_parse_ok": False,
    }


def _render_md(report: dict[str, Any], paper_name: str) -> str:
    md = ["# Requirements Judge — claim-vs-evidence audit", ""]
    md.append(f"Paper: `{paper_name}`")
    md.append("")
    verdict = report["verdict"]
    glyph = {"proceed": "✅", "partial": "⚠️", "reject": "❌"}.get(verdict, "")
    md.append(f"**Verdict: {glyph} {verdict.upper()}**")
    if not report["judge_parse_ok"]:
        md.append("")
        md.append("> Judge output was unparseable; this is the conservative "
                  "reject fallback. Re-run before trusting the result.")
    md.append("")
    reqs = report["requirements"]
    if reqs:
        md.append("## Claim ledger")
        md.append("")
        md.append("| Claim | Status | Evidence | Note |")
        md.append("|---|---|---|---|")
        for r in reqs:
            def c(s: str) -> str:
                return str(s).replace("|", "\\|")[:140]
            md.append(f"| {c(r['requirement'])} | {r['status']} | "
                      f"{c(r['evidence'])} | {c(r['note'])} |")
        md.append("")
    if report["allowed_claims"]:
        md.append("## Allowed claims (evidence supports these)")
        md.append("")
        for c in report["allowed_claims"]:
            md.append(f"- {c}")
        md.append("")
    if report["forbidden_claims"]:
        md.append("## Forbidden claims (overclaims — evidence does NOT support)")
        md.append("")
        for c in report["forbidden_claims"]:
            md.append(f"- {c}")
        md.append("")
    if report["delta_feedback"]:
        md.append("## What a sound revision must change")
        md.append("")
        md.append(report["delta_feedback"])
        md.append("")
    return "\n".join(md)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", default="review", choices=sorted(MODES))
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--journal", default=None)
    ap.add_argument("--quantum-lib", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    if not args.paper.is_file():
        print(f"ERROR: --paper file does not exist: {args.paper}",
              file=sys.stderr)
        return 2

    args.outdir.mkdir(parents=True, exist_ok=True)
    paper_text = load_paper_text(args.paper)

    class _SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"
    prompt = _load_template(args.mode).format_map(_SafeDict({
        "paper": paper_text,
        "venue_rubric": _journal_block(args.journal),
    }))
    (args.outdir / f"full_prompt_{args.mode}.txt").write_text(
        prompt, encoding="utf-8")

    try:
        result = call_llm(prompt, backend=args.llm, timeout=2400)
    except RuntimeError as e:
        report = _reject_fallback(
            f"Backend {args.llm} returned no output: {e}")
        (args.outdir / "requirements_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8")
        (args.outdir / "requirements_report.md").write_text(
            _render_md(report, args.paper.name), encoding="utf-8")
        return 4

    obj = extract_json(result.text)
    if obj is None:
        report = _reject_fallback(
            "Requirements judge output unparseable as JSON; re-run the "
            "judge before trusting this audit.")
    else:
        report = normalize_report(obj)
    report["generated_by"] = "requirements_judge"
    report["mode"] = args.mode
    report["paper"] = args.paper.name

    (args.outdir / "requirements_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    (args.outdir / "requirements_report.md").write_text(
        _render_md(report, args.paper.name), encoding="utf-8")
    (args.outdir / "_llm_generation.log").write_text(
        f"--- mode: {args.mode} ---\n"
        f"--- backend: {result.backend_actually_used} ---\n"
        f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
        f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
        encoding="utf-8")
    write_backend_marker(args.outdir, result)

    print(f"requirements_judge[{args.mode}]: verdict={report['verdict']} "
          f"({len(report['requirements'])} claims, "
          f"{len(report['forbidden_claims'])} forbidden) -> {args.outdir}")
    return 0 if report["verdict"] == "proceed" else 3


if __name__ == "__main__":
    sys.exit(main())
