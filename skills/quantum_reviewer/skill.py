"""quantum_reviewer skill driver — 7 modes for peer-review simulation.

Same multi-mode dispatch as deep_research / quantum_paper. The `full` mode
explicitly runs a 5-voice panel (EIC + R1 + R2 + R3 + Devil's Advocate) in
one prompt — voice identity is enforced by the prompt's structure and
validated post-hoc by the driver checking that all 5 voice markers appear.

Cross-framework adoptions (from the QN-vs-ARS-vs-ARC head-to-head):
- `synthesis` mode (ARS editorial_synthesizer_agent): consumes the panel
  output and produces an Editorial Decision Package with CONSENSUS-N
  tags, disagreement resolution, 3-priority revision roadmap, and a
  response-letter template.
- `_quality_gate.json` (ARC quality_gate): deterministic post-processing
  of full-mode output — parses per-voice `Verdict: N/10` scores + the
  vote table into ARC's machine-actionable shape with a numeric
  threshold gate. Zero extra LLM cost.
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


MODES: dict[str, str] = {
    "full":              "review_panel.md",
    "quick":             "quick_review.md",
    "guided":            "improvement_session.md",
    "methodology-focus": "methodology_review.md",
    "re-review":         "re_review.md",
    "calibration":       "calibration_report.md",
    "synthesis":         "editorial_decision.md",
}


def _load_template(mode: str) -> str:
    p = HERE / "prompts" / f"{mode}.md"
    if not p.is_file():
        raise FileNotFoundError(f"prompt template not found: {p}")
    return p.read_text(encoding="utf-8")


def _build_context(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.journal:
        try:
            p = journal_policy(args.journal)
            parts.append(
                f"## Target journal (apply this rubric)\n\n{p.manifest_md()}"
            )
        except KeyError as e:
            parts.append(f"## Target journal\n\n_unknown slug: {e}_")
    return "\n\n".join(parts) or "_(no journal rubric specified; use generic peer-review standards)_"


def _load_draft(path: Path) -> str:
    return load_paper_text(path)


def _check_full_panel_completeness(text: str) -> list[str]:
    """For --mode full, verify all 5 voices appear in the LLM output.

    Returns the list of missing voice IDs (empty list = all present). The
    driver surfaces this as a quality flag in the output, not a hard fail —
    the framework's philosophy is to make absences visible, not to gate.
    """
    required = ["Editor-in-Chief", "Reviewer 1", "Reviewer 2",
                "Reviewer 3", "Devil's Advocate"]
    missing = [v for v in required if v not in text]
    return missing


# ---------------------------------------------------------------------------
# ARC-style quality gate (deterministic; adopted from AutoResearchClaw's
# quality_gate stage shape: {score_1_to_10, verdict, required_actions, ...}).
# ---------------------------------------------------------------------------

_VERDICT_SCORE_RE = re.compile(
    r"Verdict[:\s*]+(\d+(?:\.\d+)?)\s*/\s*10", re.IGNORECASE)
_VOTE_ROW_RE = re.compile(
    r"^\|\s*(Reviewer 1|Reviewer 2|Reviewer 3|Devil's Advocate|"
    r"Editor-in-Chief)\s*\|\s*([A-Za-z][A-Za-z -]*?)\s*\|"
    r"\s*(\d+(?:\.\d+)?)(?:\s*/\s*10)?\s*\|",
    re.MULTILINE)


def _normalize_recommendation(rec: str) -> str:
    """LLMs emit 'Major Revisions' / 'major-revisions' / 'Reject'
    interchangeably; normalize to the canonical kebab-case vocabulary."""
    r = rec.strip().lower().replace(" ", "-")
    if r.endswith("revision"):
        r += "s"
    return r
_PASSING_VERDICTS = {"accept", "minor-revisions"}


def extract_traceability_matrix(review_text: str,
                                draft_text: str) -> dict:
    """Deterministic parse + verification of the R&R Traceability Matrix.

    Parses the matrix table from a re-review report and mechanically
    checks each Evidence quote against the revised draft: a quote that
    does not appear verbatim (whitespace-normalized) gets
    ``evidence_found: false`` and its VERIFIED verdict is downgraded to
    UNSUBSTANTIATED in the summary counts. This is the anti-hallucination
    layer — the reviewer cannot certify a revision with invented quotes.
    """
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip().lower()

    draft_norm = _norm(draft_text)
    rows: list[dict] = []
    section = re.split(r"^##\s+R&R Traceability Matrix\s*$", review_text,
                       flags=re.MULTILINE | re.IGNORECASE)
    if len(section) > 1:
        body = re.split(r"^##\s+", section[1], maxsplit=1,
                        flags=re.MULTILINE)[0]
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 5 or cells[0] in ("#", ""):
                continue
            finding, claim, evidence, verdict = (cells[1], cells[2],
                                                 cells[3], cells[4].upper())
            quote = _norm(evidence).strip('"“”').strip("'. …")
            found = bool(quote) and quote in draft_norm
            effective = verdict
            if verdict == "VERIFIED" and not found:
                effective = "UNSUBSTANTIATED"
            rows.append({
                "n": cells[0],
                "finding": finding,
                "author_claim": claim,
                "evidence": evidence,
                "claimed_verdict": verdict,
                "evidence_found_in_draft": found,
                "effective_verdict": effective,
            })
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["effective_verdict"]] = counts.get(
            r["effective_verdict"], 0) + 1
    return {
        "rows": rows,
        "counts": counts,
        "n_rows": len(rows),
        "n_evidence_unverifiable": sum(
            1 for r in rows if not r["evidence_found_in_draft"]),
        "source": ("deterministic parse of the re-review matrix; evidence "
                   "quotes mechanically checked against the revised draft"),
    }


def extract_quality_gate(panel_text: str,
                         threshold: float = 7.0) -> dict:
    """Parse the full-mode panel into ARC's quality_gate JSON shape.

    Deterministic — no LLM call. score_1_to_10 is the mean of the
    per-voice `Verdict: N/10` scores found in the prose; verdict is the
    EIC's recommendation from the vote table; required_actions come from
    the EIC's "must-fix" numbered list. Missing pieces yield nulls, never
    raises.
    """
    # One score per voice: the EIC's synthesis restates the other
    # reviewers' verdicts, so a whole-document finditer double-counts.
    # Split on the voice headings and take the FIRST match per section.
    scores: list[float] = []
    sections = re.split(r"^## Voice \d", panel_text, flags=re.MULTILINE)
    for sec in sections[1:6]:          # at most the 5 voices
        m = _VERDICT_SCORE_RE.search(sec)
        if m:
            scores.append(float(m.group(1)))
    score = round(sum(scores) / len(scores), 2) if scores else None

    votes = {}
    for m in _VOTE_ROW_RE.finditer(panel_text):
        votes[m.group(1)] = {
            "recommendation": _normalize_recommendation(m.group(2)),
            "confidence": float(m.group(3)),
        }
    eic_verdict = (votes.get("Editor-in-Chief") or {}).get("recommendation")

    # EIC's must-fix list: numbered lines after the EIC voice's synthesis.
    required_actions: list[str] = []
    eic_idx = panel_text.find("Voice 5")
    if eic_idx != -1:
        tail = panel_text[eic_idx:]
        for line in tail.splitlines():
            m = re.match(r"^\s*\d+[\.\)]\s+(.{10,})", line)
            if m:
                required_actions.append(m.group(1).strip())
    passes = None
    if score is not None and eic_verdict is not None:
        passes = (score >= threshold
                  and eic_verdict in _PASSING_VERDICTS)
    return {
        "score_1_to_10": score,
        "verdict": eic_verdict,
        "votes": votes,
        "per_voice_scores": scores,
        "threshold": threshold,
        "passes_threshold": passes,
        "required_actions": required_actions[:12],
        "source": "deterministic parse of review_panel.md "
                  "(ARC quality_gate shape; no extra LLM call)",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", required=True, choices=sorted(MODES))
    ap.add_argument("--draft", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--journal", default=None)
    ap.add_argument("--gold-set", default=None, type=Path)
    ap.add_argument("--prior-comments", default=None, type=Path,
                    help="for --mode re-review: the prior round's "
                         "reviewer comments")
    ap.add_argument("--panel", default=None, type=Path,
                    help="for --mode synthesis: the full-mode panel "
                         "output (review_panel.md)")
    ap.add_argument("--fallacy-report", default=None, type=Path,
                    help="for --mode synthesis: optional fallacy_report.md "
                         "— medium+ findings the panel missed get "
                         "CONSENSUS-0 entries")
    ap.add_argument("--research-review", default=None, type=Path,
                    help="for --mode synthesis: optional "
                         "research_quality_review.md for extra context")
    ap.add_argument("--gate-threshold", default=7.0, type=float,
                    help="quality-gate threshold on the panel's mean "
                         "per-voice score (ARC default: 7.0)")
    args = ap.parse_args()

    if not args.draft.is_file():
        print(f"ERROR: --draft file does not exist: {args.draft}",
              file=sys.stderr)
        return 2
    if args.mode == "calibration" and not (
            args.gold_set and args.gold_set.is_dir()):
        print("ERROR: --mode calibration requires --gold-set DIR",
              file=sys.stderr)
        return 2
    if args.mode == "re-review" and not (
            args.prior_comments and args.prior_comments.is_file()):
        print("ERROR: --mode re-review requires --prior-comments PATH",
              file=sys.stderr)
        return 2
    if args.mode == "synthesis" and not (
            args.panel and args.panel.is_file()):
        print("ERROR: --mode synthesis requires --panel PATH "
              "(the full-mode review_panel.md)", file=sys.stderr)
        return 2

    args.outdir.mkdir(parents=True, exist_ok=True)
    template = _load_template(args.mode)
    draft_text = _load_draft(args.draft)
    context = _build_context(args)
    prior_comments_text = (
        args.prior_comments.read_text(encoding="utf-8")
        if args.prior_comments and args.prior_comments.is_file()
        else ""
    )
    panel_text = (
        args.panel.read_text(encoding="utf-8")
        if args.panel and args.panel.is_file() else ""
    )
    fallacies_block = ""
    if args.fallacy_report and args.fallacy_report.is_file():
        fallacies_block = (
            "**Fallacy report (check for medium+ findings the panel "
            "missed):**\n\n```\n"
            + args.fallacy_report.read_text(encoding="utf-8")[:30_000]
            + "\n```"
        )
    research_block = ""
    if args.research_review and args.research_review.is_file():
        research_block = (
            "**Deep-research review (audit-and-falsify checklist):**\n\n```\n"
            + args.research_review.read_text(encoding="utf-8")[:30_000]
            + "\n```"
        )

    class _SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"
    prompt = template.format_map(_SafeDict({
        "draft": draft_text,
        "context": context,
        "prior_comments": prior_comments_text,
        "panel": panel_text,
        "fallacies_block": fallacies_block,
        "research_block": research_block,
    }))
    (args.outdir / f"full_prompt_{args.mode}.txt").write_text(
        prompt, encoding="utf-8"
    )

    try:
        result = call_llm(prompt, backend=args.llm, timeout=2400)
    except RuntimeError as e:
        primary = args.outdir / MODES[args.mode]
        primary.write_text(
            f"# ⚠ quantum_reviewer ({args.mode}) FAILED\n\n"
            f"Backend {args.llm} did not return output: `{e}`\n",
            encoding="utf-8",
        )
        return 3

    primary_text = result.text

    # --mode full: prepend a deterministic Panel Coverage header listing any
    # missing voices, so absence is impossible to miss.
    if args.mode == "full":
        missing = _check_full_panel_completeness(primary_text)
        if missing:
            coverage_header = (
                f"<!-- quantum_reviewer FULL-mode panel-coverage header — "
                f"code-emitted, do not edit -->\n"
                f"# ⚠ Panel Coverage Warning\n\n"
                f"The 5-voice panel did not emit all required voices. "
                f"Missing: {', '.join(missing)}.\n\n"
                f"This review's verdict was constructed without the "
                f"perspective(s) above. Re-run with `--force` and a different "
                f"backend if the missing voice is load-bearing.\n\n---\n\n"
            )
            primary_text = coverage_header + primary_text
        # ARC-style machine-actionable quality gate — deterministic parse
        # of the panel (mean per-voice score + EIC verdict + must-fix list),
        # gated against --gate-threshold. Zero extra LLM cost.
        gate = extract_quality_gate(primary_text,
                                     threshold=args.gate_threshold)
        (args.outdir / "_quality_gate.json").write_text(
            json.dumps(gate, indent=2), encoding="utf-8"
        )

    # --mode re-review: deterministic R&R traceability matrix — every
    # Evidence quote is mechanically checked against the revised draft.
    if args.mode == "re-review":
        matrix = extract_traceability_matrix(primary_text, draft_text)
        (args.outdir / "_traceability_matrix.json").write_text(
            json.dumps(matrix, indent=2), encoding="utf-8")
        if matrix["n_rows"] == 0:
            print("quantum_reviewer[re-review]: WARNING — no R&R "
                  "Traceability Matrix found in the output",
                  file=sys.stderr)

    primary = args.outdir / MODES[args.mode]
    primary.write_text(primary_text, encoding="utf-8")
    (args.outdir / "_llm_generation.log").write_text(
        f"--- mode: {args.mode} ---\n"
        f"--- backend: {result.backend_actually_used} ---\n"
        f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
        f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
        encoding="utf-8",
    )
    write_backend_marker(args.outdir, result)
    print(f"quantum_reviewer[{args.mode}]: wrote {primary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
