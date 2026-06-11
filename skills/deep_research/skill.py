"""deep_research skill driver — 7 modes for quantum-aware research.

Mode dispatch is template-based: each mode has a prompt template in
`prompts/<mode>.md` that the driver fills with the topic + optional journal
policy + optional library notes + optional Hamiltonian context, then ships
to the LLM via `skills/common/llm.py`. Mode-specific output paths follow
the contract in SKILL.md.

Adding a new mode means dropping a new prompt template into prompts/ and
adding it to MODES below. No driver changes required.
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
from paper_io import load_paper_text            # noqa: E402
from quantum_libs import library                # noqa: E402


# (mode, primary output filename)
MODES: dict[str, str] = {
    "full":              "synthesis.md",
    "quick":             "brief.md",
    "systematic-review": "prisma_flow.md",
    "socratic":          "research_question.md",
    "fact-check":        "factcheck_report.md",
    "lit-review":        "lit_review.md",
    "review":            "research_quality_review.md",
}


def _load_template(mode: str) -> str:
    p = HERE / "prompts" / f"{mode}.md"
    if not p.is_file():
        raise FileNotFoundError(
            f"prompt template not found for mode {mode!r}: {p}"
        )
    return p.read_text(encoding="utf-8")


def _build_context(args: argparse.Namespace) -> str:
    """Assemble the quantum-context block prepended to every mode's prompt."""
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
                f"## Quantum library\n\n"
                f"- **Name:** {lib.name}\n"
                f"- **Install:** `{lib.install_hint}`\n"
                f"- **Notes:** {lib.notes}"
            )
        except KeyError as e:
            parts.append(f"## Quantum library\n\n_unknown slug: {e}_")
    if args.hamiltonian_id:
        parts.append(
            f"## Hamiltonian context\n\n- ID: `{args.hamiltonian_id}`"
        )
    return "\n\n".join(parts)


class _SafeDict(dict):
    """str.format helper — leaves {unknown} literal so LaTeX braces survive."""
    def __missing__(self, key):
        return "{" + key + "}"


def _fill_prompt(template: str, args: argparse.Namespace) -> str:
    context = _build_context(args)
    return template.format_map(_SafeDict({
        "topic": args.topic,
        "context": context if context else "_(no extra context provided)_",
    }))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", required=True, choices=sorted(MODES))
    ap.add_argument("--topic", required=True)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--journal", default=None,
                    help="optional target-journal slug; see "
                         "`python -m skills.common.journals list`")
    ap.add_argument("--quantum-lib", default=None,
                    help="optional quantum-library slug; see "
                         "`python -m skills.common.quantum_libs list`")
    ap.add_argument("--hamiltonian-id", default=None)
    ap.add_argument("--paper", default=None, type=Path,
                    help="optional path to a paper (.tex/.md/.txt) whose text "
                         "is appended verbatim to the prompt. Without this, "
                         "review/fact-check modes assess from the LLM's prior "
                         "knowledge of the title alone, which is much weaker.")
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    template = _load_template(args.mode)
    prompt = _fill_prompt(template, args)
    # Ground modes that benefit from the actual paper text.
    if args.paper and not args.paper.is_file():
        print(f"ERROR: --paper file does not exist: {args.paper}",
              file=sys.stderr)
        return 2
    if args.paper and args.paper.is_file():
        paper_text = load_paper_text(args.paper)
        prompt += (
            "\n\n---\n\n## Paper text (verbatim, for grounding)\n\n```\n"
            + paper_text[:200_000]  # 200 KB cap to stay within context limits
            + "\n```\n"
        )
    (args.outdir / f"full_prompt_{args.mode}.txt").write_text(
        prompt, encoding="utf-8"
    )

    try:
        result = call_llm(prompt, backend=args.llm, timeout=900)
    except RuntimeError as e:
        # Honest stub when the LLM call fails (matches QN's no-silent-fallback policy)
        out_path = args.outdir / MODES[args.mode]
        out_path.write_text(
            f"# ⚠ deep_research ({args.mode}) FAILED\n\n"
            f"Backend {args.llm} did not return output:\n\n"
            f"`{e}`\n\n"
            f"The framework does NOT silently swap to a different backend. "
            f"Re-run after addressing the backend issue (claude is the "
            f"default; see the nested-CLI isolation playbook) or the "
            f"underlying error before relying on this stage's output.\n",
            encoding="utf-8",
        )
        return 3

    primary = args.outdir / MODES[args.mode]
    primary.write_text(result.text, encoding="utf-8")
    (args.outdir / "_llm_generation.log").write_text(
        f"--- mode: {args.mode} ---\n"
        f"--- backend_requested: {result.backend_requested} ---\n"
        f"--- backend_actually_used: {result.backend_actually_used} ---\n"
        f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
        f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
        encoding="utf-8",
    )
    write_backend_marker(args.outdir, result)
    print(f"deep_research[{args.mode}]: wrote {primary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
