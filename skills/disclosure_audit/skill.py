"""disclosure_audit — funding / COI / ethics / availability audit.

One LLM call against a fixed 16-point disclosure checklist (journal
standards A1-A8, AI-use disclosures B1-B4, rights & warranties C1-C4).
Reports presence + completeness + verbatim evidence per item, grouped
by severity (submission-blocking / revise-before-acceptance /
editorial-discretion).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402
from paper_io import load_paper_text            # noqa: E402


PROMPT_TEMPLATE = """\
You are conducting a publication disclosure and warranty audit of a
quantum-computing manuscript. Objective: identify ALL required
disclosure statements a peer-reviewed journal requires before
submission, and whether this manuscript carries them.

Audit categories — check EACH for presence + completeness + verbatim
evidence:

## A. Journal-standard disclosures (npj, Nature, PRX, Quantum, IEEE):
  A1. Funding statement — every source with grant numbers, or an
      explicit "no external funding".
  A2. Competing interests / conflict-of-interest declaration —
      financial, employment, consulting, advisory, IP, or personal.
  A3. Author contributions — CRediT-style or equivalent per-author roles.
  A4. Data availability — where the data lives, accession IDs, embargo
      periods, justified exceptions.
  A5. Code availability — repo URL, license, version/commit, or
      explicit "available on request" with rationale.
  A6. Ethics / IRB approval — only where human/animal subjects apply;
      mark NOT-APPLICABLE for pure theory/simulation/device papers.
  A7. Preprint / prior-publication status — arXiv ID, or explicit
      statement; thesis/conference reuse.
  A8. Materials availability — devices, fabrication recipes, reagents,
      including MTAs where applicable.

## B. AI-specific disclosures (rising journal requirement):
  B1. AI-assisted text drafting (model, scope, human review).
  B2. AI-generated images/figures with per-image tool chain.
  B3. AI-assisted data analysis or coding.
  B4. AI-assisted pre-submission review.

## C. Rights, warranties, approvals:
  C1. Prior-publication warranty (not under consideration elsewhere).
  C2. Government / institutional / export-control pre-publication
      approval (relevant for quantum-hardware work).
  C3. Third-party rights — reused figures/tables with permissions or
      CC attribution.
  C4. Free-online-version conflict with the target venue's policy.

Output format:

# DISCLOSURE AUDIT REPORT

## Compliance status by category
| Code | Category | Status | Evidence (section or "absent") | Required for venue? |
Status values: PRESENT-COMPLETE, PRESENT-INCOMPLETE, ABSENT,
NOT-APPLICABLE.

## Missing disclosures and warranty gaps
Group by severity: Submission-blocking / Revise-before-acceptance /
Editorial-discretion.

## Submission-ready checklist
One line PER audit code (A1-A8, B1-B4, C1-C4) — 16 lines — pass/fail
with fix text where failing.

Finish with a machine-readable block:

```json
{{"items": [{{"code": "A1", "status": "ABSENT", "severity": "submission-blocking"}}],
  "blocking": 0, "incomplete": 0, "not_applicable": 0}}
```

Constraints:
- Be specific and procedural. Quote the manuscript verbatim as evidence.
- Do not guess facts not present in the manuscript; label unknowns that
  require author confirmation.
- No preamble, no closing remarks.

Venue: {venue}
Title: {title}

---

## MANUSCRIPT

{paper}
"""


def _extract_json(text: str) -> dict | None:
    for blob in reversed(re.findall(r"```json\s*(\{.*?\})\s*```",
                                    text, re.DOTALL)):
        try:
            parsed = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "items" in parsed:
            return parsed
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--journal", default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--quantum-lib", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    if not args.paper.is_file():
        print(f"ERROR: --paper not found: {args.paper}", file=sys.stderr)
        return 2
    args.outdir.mkdir(parents=True, exist_ok=True)

    paper_text = load_paper_text(args.paper)
    prompt = PROMPT_TEMPLATE.format(
        venue=args.journal or "generic peer-reviewed quantum journal",
        title=args.title or args.paper.stem,
        paper=paper_text[:300_000],
    )
    (args.outdir / "full_prompt.txt").write_text(prompt, encoding="utf-8")

    try:
        result = call_llm(prompt, backend=args.llm, timeout=1800)
    except RuntimeError as e:
        (args.outdir / "disclosure_audit.md").write_text(
            f"# disclosure_audit FAILED\n\nBackend {args.llm}: `{e}`\n",
            encoding="utf-8")
        return 3

    (args.outdir / "disclosure_audit.md").write_text(result.text,
                                                     encoding="utf-8")
    structured = _extract_json(result.text)
    (args.outdir / "disclosure_findings.json").write_text(
        json.dumps(structured if structured is not None else
                   {"_note": "no machine-readable JSON block in LLM output"},
                   indent=2), encoding="utf-8")
    write_backend_marker(args.outdir, result)

    blocking = (structured or {}).get("blocking", "?")
    print(f"disclosure_audit: blocking={blocking}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
