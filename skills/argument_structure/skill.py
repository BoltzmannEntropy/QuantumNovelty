"""argument_structure — argument-architecture audit of a quantum paper.

One LLM call. Maps the paper's argument as premises -> intermediate
claims -> conclusion, then audits five dimensions:

  A. Controlling idea — stated thesis vs demonstrated conclusion
  B. CME proportionality — Claim / Mechanism / Evidence balance
  C. Narrative-debt register — promises made vs fulfilled
  D. Sequencing diagnosis — rhetorical vs evidential ordering
  E. Structural gaps — analysis types entirely absent

This catches a failure class the referee panel reviews past: a paper
whose individual statements are all defensible but whose argument
ARCHITECTURE doesn't support the headline (e.g. a benchmarking study
sold as a scaling result).
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
from journals import journal_policy             # noqa: E402
from paper_io import load_paper_text            # noqa: E402


def _load_template() -> str:
    return (HERE / "prompts" / "argument_structure.md").read_text(
        encoding="utf-8")


def _extract_json(text: str) -> dict | None:
    candidates = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    for blob in reversed(candidates):
        try:
            parsed = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "overall_verdict" in parsed:
            return parsed
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--journal", default=None)
    ap.add_argument("--quantum-lib", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    if not args.paper.is_file():
        print(f"ERROR: --paper not found: {args.paper}", file=sys.stderr)
        return 2
    args.outdir.mkdir(parents=True, exist_ok=True)

    paper_text = load_paper_text(args.paper)
    venue_block = ""
    if args.journal:
        try:
            venue_block = ("\n## Target venue rubric\n\n"
                           + journal_policy(args.journal).manifest_md())
        except KeyError:
            venue_block = f"\n## Target venue\n\n_{args.journal}_ (unknown slug)"

    prompt = (_load_template()
              .replace("{{VENUE_BLOCK}}", venue_block)
              .replace("{{PAPER}}", paper_text[:300_000]))
    (args.outdir / "full_prompt.txt").write_text(prompt, encoding="utf-8")

    try:
        result = call_llm(prompt, backend=args.llm, timeout=2700)
    except RuntimeError as e:
        (args.outdir / "argument_structure.md").write_text(
            f"# argument_structure FAILED\n\nBackend {args.llm}: `{e}`\n",
            encoding="utf-8")
        return 3

    (args.outdir / "argument_structure.md").write_text(
        result.text, encoding="utf-8")
    structured = _extract_json(result.text)
    (args.outdir / "argument_structure.json").write_text(
        json.dumps(structured if structured is not None else
                   {"_note": "no machine-readable JSON block in LLM output"},
                   indent=2), encoding="utf-8")
    write_backend_marker(args.outdir, result)

    verdict = (structured or {}).get("overall_verdict", "?")
    print(f"argument_structure: verdict={verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
