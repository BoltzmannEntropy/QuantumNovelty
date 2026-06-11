"""quantum_paper skill driver — 10 modes for quantum-paper authoring.

Shares the multi-mode dispatch pattern with `deep_research`: each mode has
a prompt template in `prompts/<mode>.md` filled with topic/draft/reviewer-
comments/journal/library context, shipped to the LLM, written to a mode-
specific output path.
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
from journals import journal_policy             # noqa: E402
from quantum_libs import library                # noqa: E402
from paper_io import load_paper_text            # noqa: E402


# (mode, primary output filename)
MODES: dict[str, str] = {
    "full":             "paper.tex",
    "plan":             "plan.md",
    "outline-only":     "outline.md",
    "revision":         "paper_v2.tex",
    "revision-coach":   "roadmap.md",
    "abstract-only":    "abstract.md",
    "lit-review":       "lit_review_paper.tex",
    "format-convert":   "converted.tex",
    "citation-check":   "citation_report.md",
    "disclosure":       "disclosure_block.md",
}

# Modes that consume a draft file via --draft
MODES_REQUIRING_DRAFT = {"revision", "revision-coach", "abstract-only",
                         "format-convert", "citation-check", "disclosure"}

# Modes that consume reviewer comments via --reviewer-comments
MODES_REQUIRING_REVIEWER_COMMENTS = {"revision", "revision-coach"}

# Modes that consume a topic string via --topic
MODES_REQUIRING_TOPIC = {"full", "plan", "outline-only", "lit-review"}


def _load_template(mode: str) -> str:
    p = HERE / "prompts" / f"{mode}.md"
    if not p.is_file():
        raise FileNotFoundError(
            f"prompt template not found for mode {mode!r}: {p}"
        )
    return p.read_text(encoding="utf-8")


def _build_context(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.journal:
        try:
            p = journal_policy(args.journal)
            parts.append(f"## Target journal\n\n{p.manifest_md()}")
        except KeyError as e:
            parts.append(f"## Target journal\n\n_unknown slug: {e}_")
    if args.quantum_lib:
        try:
            lib = library(args.quantum_lib)
            parts.append(
                f"## Quantum library for any code snippets\n\n"
                f"- **Name:** {lib.name}\n"
                f"- **Install:** `{lib.install_hint}`\n"
                f"- **Notes:** {lib.notes}"
            )
        except KeyError as e:
            parts.append(f"## Quantum library\n\n_unknown slug: {e}_")
    return "\n\n".join(parts) or "_(no journal/library context provided)_"


def _load_draft(path: Path) -> str:
    return load_paper_text(path)


class _SafeDict(dict):
    """Format helper: leaves `{unknown_key}` literal if not in dict.

    Prompt templates contain LaTeX placeholders like `\\cite{Author2024Method}`
    where the braces are part of the LaTeX command, NOT format variables.
    Python's str.format() would raise KeyError on those; this dict subclass
    returns the literal `{key}` instead so the LLM sees the raw placeholder.
    """
    def __missing__(self, key):
        return "{" + key + "}"


def _fill_prompt(template: str, args: argparse.Namespace) -> str:
    context = _build_context(args)
    fillers: dict[str, str] = {
        "context": context,
        "topic": args.topic or "_(no topic specified)_",
        "draft": "",
        "reviewer_comments": "",
    }
    if args.draft and args.draft.is_file():
        fillers["draft"] = _load_draft(args.draft)
    if args.reviewer_comments and args.reviewer_comments.is_file():
        fillers["reviewer_comments"] = args.reviewer_comments.read_text(
            encoding="utf-8", errors="replace"
        )
    return template.format_map(_SafeDict(fillers))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", required=True, choices=sorted(MODES))
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--journal", default=None)
    ap.add_argument("--quantum-lib", default=None)
    ap.add_argument("--topic", default=None)
    ap.add_argument("--draft", default=None, type=Path)
    ap.add_argument("--reviewer-comments", default=None, type=Path)
    args = ap.parse_args()

    # Validate required inputs per mode.
    if args.mode in MODES_REQUIRING_TOPIC and not args.topic:
        print(f"ERROR: mode {args.mode!r} requires --topic", file=sys.stderr)
        return 2
    if args.mode in MODES_REQUIRING_DRAFT and not (
            args.draft and args.draft.is_file()):
        print(f"ERROR: mode {args.mode!r} requires --draft PATH (file must exist)",
              file=sys.stderr)
        return 2
    if args.mode in MODES_REQUIRING_REVIEWER_COMMENTS and not (
            args.reviewer_comments and args.reviewer_comments.is_file()):
        print(f"ERROR: mode {args.mode!r} requires --reviewer-comments PATH",
              file=sys.stderr)
        return 2

    args.outdir.mkdir(parents=True, exist_ok=True)
    template = _load_template(args.mode)
    prompt = _fill_prompt(template, args)
    (args.outdir / f"full_prompt_{args.mode}.txt").write_text(
        prompt, encoding="utf-8"
    )

    try:
        result = call_llm(prompt, backend=args.llm, timeout=1800)
    except RuntimeError as e:
        primary = args.outdir / MODES[args.mode]
        primary.write_text(
            f"% quantum_paper ({args.mode}) FAILED\n"
            f"% Backend {args.llm} did not return output:\n% {e}\n",
            encoding="utf-8",
        )
        return 3

    # Post-process: when the mode emits a .tex file, the LLM sometimes wraps
    # the LaTeX in a markdown preamble (e.g. "I'll write…" then a ```latex
    # fence). Strip that so the output is a compilable .tex file. Also fix
    # known LLM-typo patterns (mismatched enumerate braces).
    primary = args.outdir / MODES[args.mode]
    text_to_write = result.text
    if primary.suffix == ".tex":
        import re
        # 1. Markdown-fence extraction.
        m = re.search(r"```(?:latex|tex)\s*\n(.*?)```",
                      result.text, re.DOTALL | re.IGNORECASE)
        if m:
            text_to_write = m.group(1).strip()
        else:
            idx = result.text.find("\\documentclass")
            if idx > 0:
                text_to_write = result.text[idx:]
            end_idx = text_to_write.rfind("\\end{document}")
            if end_idx > 0:
                text_to_write = text_to_write[:end_idx + len("\\end{document}")]
        # 2. Known LLM-typo repairs.
        #    `\begin{enumerate}[label=(\roman*)}]` → close with `)]`
        text_to_write = re.sub(
            r"\\roman\*\)\}\]", r"\\roman*)]", text_to_write
        )
        #    Same for alph
        text_to_write = re.sub(
            r"\\alph\*\)\}\]", r"\\alph*)]", text_to_write
        )
        #    Same for arabic
        text_to_write = re.sub(
            r"\\arabic\*\)\}\]", r"\\arabic*)]", text_to_write
        )
    primary.write_text(text_to_write, encoding="utf-8")
    # Also persist the raw response so we can audit the wrapper if needed.
    (args.outdir / f"_raw_response_{args.mode}.txt").write_text(
        result.text, encoding="utf-8"
    )
    (args.outdir / "_llm_generation.log").write_text(
        f"--- mode: {args.mode} ---\n"
        f"--- backend: {result.backend_actually_used} ---\n"
        f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
        f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
        encoding="utf-8",
    )
    write_backend_marker(args.outdir, result)
    print(f"quantum_paper[{args.mode}]: wrote {primary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
