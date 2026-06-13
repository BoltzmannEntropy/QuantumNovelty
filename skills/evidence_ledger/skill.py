"""evidence_ledger — deterministic reviewer-hallucination guard. No LLM calls.

Adapted from AutoResearchClaw's evidence-ledger gate (ARC's two-pass
"permitted facts" pattern): pre-register what the paper actually says, then
audit the review output against that ledger so a reviewer cannot attribute
claims, quotes, or numbers to the paper that the paper never made.

Two modes:

  ledger (default) — pre-write pass. Reads the source paper (and optional
      .bib files) and extracts a deterministic ledger of permitted facts:
      cite keys, distinct numeric values, section headings, and a
      normalized full-text token field for fuzzy matching. Zero LLM cost.

  audit (--ledger + --run-dir) — post-review pass. Scans every review
      report (.md/.txt) produced in the run directory and flags four
      classes of unsupported attribution to the paper:
        unknown_cite_key              \\cite{KEY} where KEY ∉ ledger
        unanchored_quote              a long verbatim quote attributed to
                                      the paper that is absent from it
        unanchored_paper_claim        "the paper reports X" where most of
                                      X's content words are absent
        unanchored_numeric_in_claim   a number inside a "the paper reports
                                      X" clause absent from the ledger

The audit is INFORMATIONAL — it never fails the chain. It surfaces where a
reviewer voice invented detail about the paper so the operator can suppress
those findings or require an editorial pass. (QN documents absences; it
does not gate on them.)

Outputs (ledger mode):
  ledger.json   permitted facts
  ledger.md     human summary

Outputs (audit mode):
  ledger_audit.json   machine-readable findings
  ledger_audit.md     typeset findings table

Exit codes: 0 clean run (findings may still be present), 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from paper_io import load_paper_text  # noqa: E402


# Same numeral grammar as claims_registry: longest/most-specific forms
# first so "1.5e-3" does not tokenize as "1" + "3".
NUMBER_RE = re.compile(
    r"""
    (?<![\w\.])
    (
        \d+(?:\.\d+)?e[+-]?\d+
        |\d+/\d+
        |\d+(?:\.\d+)?(?:%|x)?
    )
    (?![\w])
    """,
    re.VERBOSE,
)

CITE_RE = re.compile(r"\\cite[a-zA-Z]*\{([^}]+)\}")
BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)", re.MULTILINE)

# Quotes a reviewer attributes to the paper. LaTeX ``...'' is the
# high-precision form (paper-only by convention). The curly / straight
# double-quote forms are pervasive in markdown reviews for proposed edits,
# reviewer questions, and JSON field values, so they only count as a
# paper-attribution when an attribution cue immediately precedes them.
LATEX_QUOTE_RE = re.compile(r"``(.+?)''", re.DOTALL)
PLAIN_QUOTE_RES = [
    re.compile(r"[“](.+?)[”]", re.DOTALL),
    re.compile(r"\"(.+?)\"", re.DOTALL),
]

# An attribution cue in the ~40 chars before a quote: "the paper states:",
# "the authors write", "abstract reads", "reports:". Without one, a quote
# in a review is almost never a verbatim claim about the paper.
ATTRIB_CUE_RE = re.compile(
    r"(?:the\s+(?:paper|authors?|manuscript|study)|states?|claims?|writes?|"
    r"wrote|reports?|says?|asserts?|notes?|argues?|quote[ds]?|verbatim|"
    r"abstract\s+reads?|abstract|conclusion)\s*[:,]?\s*$",
    re.IGNORECASE)

# Quoted spans that open with an imperative verb are proposed edits, not
# paper claims ("Add a comparison table", "Reframe as ...").
_IMPERATIVE_FIRST = {
    "add", "remove", "present", "provide", "include", "specify", "define",
    "report", "reframe", "rephrase", "qualify", "scope", "characterize",
    "perform", "compute", "run", "replace", "state", "clarify", "cite",
    "consider", "use", "ensure", "make", "give", "show", "explain",
}

# "the paper reports/claims/states/finds/shows/demonstrates/asserts X",
# X running to the next sentence boundary. The verb set is what reviewers
# actually use when they attribute a proposition to the manuscript.
PAPER_CLAIMS_RE = re.compile(
    r"\b(?:the\s+)?(?:paper|authors?|manuscript|study|work)\s+"
    r"(?:reports?|claims?|states?|finds?|shows?|demonstrates?|asserts?|"
    r"reports\s+that|argues?)\s+(?:that\s+)?(.+?)(?:[.;]|\n|$)",
    re.IGNORECASE,
)

# Numerals that are never fabrications on their own.
TRIVIAL = {str(y) for y in range(1900, 2100)}
TRIVIAL |= {str(n) for n in range(0, 11)} | {"100", "1000"}

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "that", "this", "these", "those", "is", "are", "was", "were",
    "be", "been", "being", "it", "its", "as", "at", "by", "from", "than",
    "which", "their", "they", "them", "has", "have", "had", "not", "no",
    "can", "could", "would", "should", "may", "might", "more", "most",
    "such", "also", "into", "about", "over", "under", "between", "paper",
    "authors", "author", "manuscript", "study", "work", "report", "reports",
    "claim", "claims", "state", "states", "find", "finds", "show", "shows",
}


def _norm_text(s: str) -> str:
    """Lowercase, strip markup/punctuation to spaces, collapse whitespace."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9.%/+-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _content_words(s: str) -> list[str]:
    return [w for w in _norm_text(s).split()
            if len(w) >= 4 and w not in _STOPWORDS and not w.isdigit()]


def _norm_num(value: str) -> str:
    return value.rstrip("%x")


def extract_headings(text: str) -> list[str]:
    heads = re.findall(r"\\(?:section|subsection|chapter)\*?\{([^}]+)\}", text)
    heads += re.findall(r"^#+\s+(.+)$", text, flags=re.MULTILINE)
    return sorted({h.strip() for h in heads if h.strip()})


# ---------------------------------------------------------------------------
# ledger mode
# ---------------------------------------------------------------------------

def build_ledger(paper: Path, bib: Path | None) -> dict[str, Any]:
    text = load_paper_text(paper)
    cite_keys: set[str] = set()
    for m in CITE_RE.finditer(text):
        for key in m.group(1).split(","):
            key = key.strip()
            if key:
                cite_keys.add(key)
    if bib and bib.is_file():
        bib_text = bib.read_text(encoding="utf-8", errors="replace")
        cite_keys |= {m.group(1).strip()
                      for m in BIB_ENTRY_RE.finditer(bib_text)}

    numerics = sorted({_norm_num(m.group(1))
                       for m in NUMBER_RE.finditer(text)})
    return {
        "cite_keys": sorted(cite_keys),
        "numerics": numerics,
        "numerics_count": len(numerics),
        "headings": extract_headings(text),
        "paper_text_norm": _norm_text(text),
        "source_path": str(paper),
        "source_bytes": len(text),
    }


def run_ledger(args: argparse.Namespace) -> int:
    if not args.paper or not args.paper.is_file():
        print(f"ERROR: --paper missing or not a file: {args.paper}",
              file=sys.stderr)
        return 2
    ledger = build_ledger(args.paper, args.bib)
    out = args.outdir
    (out / "ledger.json").write_text(
        json.dumps(ledger, indent=2), encoding="utf-8")

    md = ["# Evidence Ledger (permitted facts)", ""]
    md.append(f"Source: `{args.paper.name}` "
              f"({ledger['source_bytes']:,} extracted chars).")
    md.append("")
    md.append("This deterministic ledger pre-registers what the paper "
              "actually states. The post-review audit gates reviewer "
              "findings against it so no voice can attribute a claim, "
              "quote, or number to the paper that the paper never made.")
    md.append("")
    md.append(f"- **Cite keys:** {len(ledger['cite_keys'])}")
    md.append(f"- **Distinct numerics:** {ledger['numerics_count']}")
    md.append(f"- **Headings detected:** {len(ledger['headings'])}")
    md.append("")
    if ledger["source_bytes"] < 4000:
        md.append("> **Warning:** very little text was extracted. If the "
                  "source is a scanned or figure-heavy PDF, the audit will "
                  "under-detect (fuzzy matches will miss). Prefer the "
                  ".tex / .md source when available.")
        md.append("")
    (out / "ledger.md").write_text("\n".join(md), encoding="utf-8")
    print(f"evidence-ledger: {len(ledger['cite_keys'])} cite keys, "
          f"{ledger['numerics_count']} numerics, "
          f"{len(ledger['headings'])} headings -> {out}")
    return 0


# ---------------------------------------------------------------------------
# audit mode
# ---------------------------------------------------------------------------

def _quote_anchored(quote_norm: str, paper_norm: str) -> bool:
    """A quote is anchored if it appears verbatim (normalized) OR ≥70% of
    its content words are present — the token fallback absorbs lossy-PDF
    extraction drift so honest quotes are not flagged."""
    if not quote_norm:
        return True
    if quote_norm in paper_norm:
        return True
    words = [w for w in quote_norm.split() if len(w) >= 4]
    if not words:
        return True
    paper_tokens = set(paper_norm.split())
    hit = sum(1 for w in words if w in paper_tokens)
    return hit / len(words) >= 0.70


def _claim_anchored(claim: str, paper_norm: str) -> bool:
    """A paraphrased 'the paper reports X' clause is anchored if at least
    half its content words appear in the paper text."""
    words = _content_words(claim)
    if len(words) < 2:
        return True  # too short to judge; do not flag
    paper_tokens = set(paper_norm.split())
    hit = sum(1 for w in words if w in paper_tokens)
    return hit / len(words) >= 0.50


def _iter_report_files(run_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(run_dir.rglob("*.md")) + sorted(run_dir.rglob("*.txt")):
        rel = p.relative_to(run_dir)
        parts = rel.parts
        # Skip the ledger's own stage dirs and process residue.
        if any(part in ("00_evidence_ledger", "98_evidence_ledger_audit")
               for part in parts):
            continue
        if p.name.startswith("_") or p.name.startswith("full_prompt"):
            continue
        files.append(p)
    return files


def audit_file(path: Path, run_dir: Path, ledger: dict[str, Any]
               ) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(run_dir))
    paper_norm = ledger["paper_text_norm"]
    cite_keys = set(ledger["cite_keys"])
    numerics = set(ledger["numerics"])
    findings: list[dict[str, Any]] = []

    def ctx(start: int) -> str:
        return text[max(0, start - 30):start + 50].replace("\n", " ").strip()

    # 1. unknown cite keys
    for m in CITE_RE.finditer(text):
        for key in m.group(1).split(","):
            key = key.strip()
            if key and key not in cite_keys:
                findings.append({"kind": "unknown_cite_key", "value": key,
                                 "context": ctx(m.start()), "file": rel})

    # 2. unanchored quotes (≥6 words). A LaTeX ``...'' span counts on its
    # own; a plain "..." span only counts when an attribution cue precedes
    # it (otherwise it is a proposed edit, a reviewer question, or a JSON
    # value, not a claim about the paper).
    seen_quotes: set[str] = set()

    def _consider_quote(raw: str, start: int, *, require_cue: bool) -> None:
        qn = _norm_text(raw)
        words = qn.split()
        if len(words) < 6 or qn in seen_quotes:
            return
        if words[0] in _IMPERATIVE_FIRST or raw.rstrip().endswith("?"):
            return  # proposed edit / reviewer question, not a paper claim
        if require_cue and not ATTRIB_CUE_RE.search(text[max(0, start - 40):start]):
            return
        seen_quotes.add(qn)
        if not _quote_anchored(qn, paper_norm):
            findings.append({"kind": "unanchored_quote", "value": raw[:160],
                             "context": ctx(start), "file": rel})

    for m in LATEX_QUOTE_RE.finditer(text):
        _consider_quote(m.group(1).strip(), m.start(), require_cue=False)
    for qre in PLAIN_QUOTE_RES:
        for m in qre.finditer(text):
            _consider_quote(m.group(1).strip(), m.start(), require_cue=True)

    # 3 + 4. paraphrased paper-claims and numerics inside them
    for m in PAPER_CLAIMS_RE.finditer(text):
        clause = m.group(1).strip()
        if not _claim_anchored(clause, paper_norm):
            findings.append({"kind": "unanchored_paper_claim",
                             "value": clause[:160],
                             "context": ctx(m.start()), "file": rel})
        for nm in NUMBER_RE.finditer(clause):
            raw = nm.group(1)
            v = _norm_num(raw)
            if v in numerics:
                continue
            if raw == v and v in TRIVIAL:
                continue
            findings.append({"kind": "unanchored_numeric_in_claim",
                             "value": v, "context": clause[:120],
                             "file": rel})
    return findings


def run_audit(args: argparse.Namespace) -> int:
    if not args.ledger or not args.ledger.is_file():
        print(f"ERROR: --ledger missing or not a file: {args.ledger}",
              file=sys.stderr)
        return 2
    if not args.run_dir or not args.run_dir.is_dir():
        print(f"ERROR: --run-dir missing or not a dir: {args.run_dir}",
              file=sys.stderr)
        return 2
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))

    findings: list[dict[str, Any]] = []
    files = _iter_report_files(args.run_dir)
    for f in files:
        findings.extend(audit_file(f, args.run_dir, ledger))

    by_kind: dict[str, int] = defaultdict(int)
    by_file: dict[str, int] = defaultdict(int)
    for f in findings:
        by_kind[f["kind"]] += 1
        by_file[f["file"]] += 1

    report = {
        "mode": "audit",
        "ledger": str(args.ledger),
        "run_dir": str(args.run_dir),
        "files_scanned": len(files),
        "total_findings": len(findings),
        "by_kind": dict(by_kind),
        "by_file": dict(by_file),
        "findings": findings,
        "note": ("Informational reviewer-hallucination audit; does not "
                 "gate the chain. A finding means a review attributed a "
                 "claim/quote/number to the paper that the deterministic "
                 "ledger could not anchor."),
    }
    out = args.outdir
    (out / "ledger_audit.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    md = ["# Reviewer-Hallucination Audit", ""]
    md.append(f"Scanned **{len(files)}** review file(s) against the "
              f"evidence ledger; **{len(findings)}** unanchored "
              f"attribution(s).")
    md.append("")
    if not findings:
        md.append("**Clean.** Every cite key, long quote, and "
                  "\"the paper reports X\" clause in the reviews traces "
                  "back to the paper's pre-registered facts.")
    else:
        md.append("| Kind | Value | File | Context |")
        md.append("|---|---|---|---|")
        for f in findings:
            val = str(f["value"]).replace("|", "\\|")[:80]
            cx = str(f["context"]).replace("|", "\\|")[:80]
            md.append(f"| `{f['kind']}` | {val} | `{f['file']}` | {cx} |")
        md.append("")
        md.append("These are candidate reviewer hallucinations — verify "
                  "each against the manuscript before trusting the "
                  "finding it appears in. Lossy PDF extraction can produce "
                  "false positives; prefer auditing against .tex / .md "
                  "source.")
    md.append("")
    (out / "ledger_audit.md").write_text("\n".join(md), encoding="utf-8")
    print(f"evidence-ledger audit: {len(files)} files, "
          f"{len(findings)} unanchored attributions -> {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", default="ledger", choices=["ledger", "audit"])
    ap.add_argument("--paper", type=Path, help="ledger mode: the manuscript")
    ap.add_argument("--bib", type=Path, default=None,
                    help="ledger mode: optional .bib to widen cite keys")
    ap.add_argument("--ledger", type=Path, default=None,
                    help="audit mode: ledger.json from the ledger pass")
    ap.add_argument("--run-dir", type=Path, default=None,
                    help="audit mode: run directory of review reports")
    ap.add_argument("--outdir", required=True, type=Path)
    # Accepted for chain-runner uniformity; this skill makes no LLM calls.
    ap.add_argument("--llm", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--journal", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--quantum-lib", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    if args.mode == "audit":
        return run_audit(args)
    return run_ledger(args)


if __name__ == "__main__":
    sys.exit(main())
