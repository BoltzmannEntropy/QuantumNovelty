"""revision_planner — paragraph-anchored revision roadmap.

Takes a completed paper-audit run directory plus the manuscript, and
anchors every revision item to:
  (1) the exact source paragraph(s), via deterministic ¶NNN IDs stamped
      onto the manuscript before prompting;
  (2) verbatim quoted prose evidence from the judge reports that
      diagnosed the problem;
  (3) a concrete proposed edit the author can act on in one sitting.

The roadmap to anchor comes from, in priority order:
  - the editorial-synthesis report (03b_editorial_synthesis), when the
    --with-synthesizer stage ran;
  - else the quality gate's required_actions (02_reviewer_panel).

Judges quoted (whichever exist in the run dir): referee panel, fallacy
report, research review, argument-structure report, disclosure audit.
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


JUDGES = [
    ("referee panel", "02_reviewer_panel/review_panel.md"),
    ("fallacy report", "03_fallacies/fallacy_report.md"),
    ("research review", "01_research_review/research_quality_review.md"),
    ("argument structure", "02d_argument_structure/argument_structure.md"),
    ("disclosure audit", "03e_disclosure_audit/disclosure_audit.md"),
]


def number_paragraphs(text: str) -> str:
    """Stamp deterministic ¶NNN IDs onto blank-line-separated chunks."""
    chunks = re.split(r"\n\s*\n", text.strip())
    numbered = []
    n = 0
    for chunk in chunks:
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        n += 1
        numbered.append(f"¶{n:03d}: {chunk}")
    return "\n\n".join(numbered)


def find_roadmap(run_dir: Path) -> tuple[str, str]:
    """Return (roadmap_text, source_label)."""
    synth_dir = run_dir / "03b_editorial_synthesis"
    if synth_dir.is_dir():
        for md in sorted(synth_dir.glob("*.md")):
            if md.name.startswith("_"):
                continue
            text = md.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                return text, f"editorial synthesis ({md.name})"
    gate = run_dir / "02_reviewer_panel" / "_quality_gate.json"
    if gate.is_file():
        data = json.loads(gate.read_text(encoding="utf-8"))
        actions = data.get("required_actions") or []
        if actions:
            lines = ["## Revision roadmap (from the quality gate)", ""]
            lines += [f"{i}. {a}" for i, a in enumerate(actions, 1)]
            return "\n".join(lines), "quality gate required_actions"
    return "", ""


PROMPT_HEADER = """\
You are an editorial revision planner. Take the revision roadmap below
and anchor each item to (1) the exact source paragraph(s) using the
¶NNN IDs stamped on the manuscript, (2) verbatim quoted evidence from
the judge reports that diagnosed the problem, and (3) a specific
proposed edit concrete enough to act on in one sitting.

Output format — EMIT EXACTLY THIS STRUCTURE in markdown, no preamble,
no closing remarks:

# Anchored Revision Roadmap

For each roadmap item N (preserve the roadmap's ranking + numbering):

## N. <verbatim roadmap item title>

**Severity**: <1-5>  **Effort**: <5 min | 30 min | 2 h | multi-day>  \
**Judges**: <comma-list>

**Source paragraph(s)**: ¶NNN[, ¶MMM...]  (if manuscript-wide, say so
with 2-3 representative ¶NNN exemplars)

**Quoted problem prose** (verbatim from the manuscript, <=2 sentences):
> <exact quoted text>

**Judge evidence** (one bullet per judge that diagnosed this; quote the
judge verbatim, <=1 sentence each):
- <judge>: "<quoted diagnosis>"

**Proposed edit**: <1-3 sentences. Give a literal before/after rewrite
when short and feasible; otherwise say exactly what to add/change.>

**Why this works**: <1 sentence>

---

Rules:
- Anchor every finding to a ¶NNN ID from the manuscript below. Never
  invent IDs; if no anchor exists write "¶?" and say what to search for.
- Quote manuscript prose VERBATIM; if you cannot find verbatim evidence
  write "(no verbatim anchor — structural finding)".
- Quote judge diagnoses VERBATIM; omit a judge's bullet rather than
  invent attribution.
- Preserve the roadmap's numbering and ranking — do not reorder.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--run-dir", required=True, type=Path,
                    help="A paper-audit outdir with stage subdirs")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--journal", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--quantum-lib", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    if not args.paper.is_file():
        print(f"ERROR: --paper not found: {args.paper}", file=sys.stderr)
        return 2
    if not args.run_dir.is_dir():
        print(f"ERROR: --run-dir not found: {args.run_dir}",
              file=sys.stderr)
        return 2
    args.outdir.mkdir(parents=True, exist_ok=True)

    roadmap, roadmap_src = find_roadmap(args.run_dir)
    if not roadmap.strip():
        print("ERROR: no roadmap found (need 03b_editorial_synthesis "
              "output or a quality gate with required_actions)",
              file=sys.stderr)
        return 3

    numbered = number_paragraphs(load_paper_text(args.paper))
    (args.outdir / "_source_numbered.md").write_text(numbered,
                                                     encoding="utf-8")

    parts = [PROMPT_HEADER,
             f"\n## REVISION ROADMAP (source: {roadmap_src})\n",
             roadmap,
             "\n---\n\n## MANUSCRIPT (numbered paragraphs — use these "
             "¶NNN IDs in anchors)\n",
             numbered[:250_000]]
    judges_used = []
    for label, rel in JUDGES:
        p = args.run_dir / rel
        if p.is_file():
            judges_used.append(label)
            parts.append(f"\n---\n\n## JUDGE REPORT — {label}\n")
            parts.append(p.read_text(encoding="utf-8",
                                     errors="replace")[:80_000])
    prompt = "\n".join(parts)
    (args.outdir / "full_prompt.txt").write_text(prompt, encoding="utf-8")

    try:
        result = call_llm(prompt, backend=args.llm, timeout=2700)
    except RuntimeError as e:
        (args.outdir / "anchored_revision_plan.md").write_text(
            f"# revision_planner FAILED\n\nBackend {args.llm}: `{e}`\n",
            encoding="utf-8")
        return 3

    (args.outdir / "anchored_revision_plan.md").write_text(
        result.text, encoding="utf-8")
    write_backend_marker(args.outdir, result)

    n_items = len(re.findall(r"^## \d+\.", result.text, re.MULTILINE))
    print(f"revision_planner: {n_items} anchored items "
          f"(roadmap from {roadmap_src}; judges: "
          f"{', '.join(judges_used) or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
