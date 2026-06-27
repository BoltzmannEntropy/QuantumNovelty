"""patent_reviewer skill driver — a simulated USPTO examiner panel.

The quantum-patent analogue of quantum_reviewer. Where the paper reviewer
runs a journal referee panel (EIC + R1/R2/R3 + Devil's Advocate), this
runs a patent examining unit and produces an **Office Action**:

  Voice 1 — Primary Examiner       (35 U.S.C. § 101 eligibility, Alice/Mayo;
                                     overall disposition)
  Voice 2 — § 102 Examiner         (anticipation / novelty; named prior art)
  Voice 3 — § 103 Examiner         (obviousness; KSR combinations of refs)
  Voice 4 — § 112 Examiner         (enablement, written description,
                                     definiteness — critical for quantum)
  Voice 5 — Quantum Technical Spec. (does the claimed quantum invention
                                     actually operate as claimed? operability /
                                     quantum-specific enablement)
  Voice 6 — SPE synthesis          (Supervisory Patent Examiner: reconciles
                                     the examiners and issues the disposition)

Two deterministic, zero-LLM-cost artifacts post-process the panel:
  - `_office_action.json` — the patent analogue of ARC's quality_gate:
    {disposition, rejected_claims[], allowed_claims[], rejections_by_statute,
     votes, passes (== allowance)}. Claim numbers are mechanically parsed
    from each examiner's per-claim rejection table.
  - panel-coverage header — if any of the six voices is missing, a
    code-emitted warning is prepended so the absence is impossible to miss.

Patent review is claim-by-claim by law: a real Office Action rejects
claims individually (claim 1 under § 102, claims 2-7 under § 103, ...).
The prompt enforces a per-claim rejection table from each examiner, and
the gate parses it.
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
from llm import call_llm, write_backend_marker   # noqa: E402
from patent_io import load_patent                 # noqa: E402


MODES: dict[str, str] = {
    "full":  "office_action.md",
    "quick": "quick_examination.md",
}

REQUIRED_VOICES = [
    "Primary Examiner",
    "§ 102 Examiner",
    "§ 103 Examiner",
    "§ 112 Examiner",
    "Quantum Technical Specialist",
    "Supervisory Patent Examiner",
]

# Canonical USPTO dispositions (kebab-case, mirrors quantum_reviewer's
# normalize-then-gate pattern).
_DISPOSITIONS = {
    "allowance", "non-final-rejection", "final-rejection",
    "restriction-requirement",
}
_PASSING = {"allowance"}
_FILING_STANDARD_BLOCKS = {
    "uspto": (
        "## Filing-standard context\n\n"
        "Run the compliance pass under USPTO practice. Claims compliance "
        "must apply 35 U.S.C. § 112(b) definiteness, antecedent basis, "
        "claim structure, and means-plus-function risk. Full-application "
        "review must cover § 112(a) written description / enablement / "
        "best mode, MPEP 608 formalities, abstract, title, drawings, "
        "required sections, and specification-claim support."
    ),
    "epo": (
        "## Filing-standard context\n\n"
        "Run the compliance pass under EPO practice. Claims compliance "
        "must apply EPC Article 84 clarity, support by the description, "
        "essential features, two-part form where appropriate, claim "
        "category structure, and multiple-dependency clarity. "
        "Full-application review must cover specification adequacy, "
        "drawings, abstract, description amendments / support, and EPO "
        "formal requirements."
    ),
    "pct": (
        "## Filing-standard context\n\n"
        "Run the compliance pass under PCT application practice. Claims "
        "compliance must address clarity, support, unity-relevant claim "
        "structure, dependency form, and international-search readability. "
        "Full-application review must cover request/specification/claims/"
        "abstract/drawings completeness, sequence listings if applicable, "
        "and PCT formal requirements."
    ),
    "multi": (
        "## Filing-standard context\n\n"
        "Run the compliance pass under all three standards: USPTO, EPO, "
        "and PCT. Claims compliance must separately flag USPTO § 112(b) "
        "definiteness / antecedent basis / structure issues and EPO "
        "Article 84 clarity / support / two-part-form issues. "
        "Full-application review must separately cover USPTO § 112(a) + "
        "MPEP 608, EPO application formalities, and PCT required sections."
    ),
}


def _load_template(mode: str) -> str:
    p = HERE / "prompts" / f"{mode}.md"
    if not p.is_file():
        raise FileNotFoundError(f"prompt template not found: {p}")
    return p.read_text(encoding="utf-8")


def _check_panel_completeness(text: str) -> list[str]:
    """Return the list of required examiner voices missing from output."""
    return [v for v in REQUIRED_VOICES if v not in text]


# ---------------------------------------------------------------------------
# Deterministic Office Action extraction (no LLM call).
# ---------------------------------------------------------------------------

_DISPO_RE = re.compile(
    r"Disposition[:\s*]+([A-Za-z][A-Za-z \-]*?)(?:[\.\n]|$)", re.IGNORECASE)
# Per-claim rejection rows in the examiner tables, e.g.:
#   | 1 | § 102(a)(1) | anticipated by Smith (US1234) |
#   | 11, 12 | § 112(b) | indefinite |
# Statute cell is § 101 / 102 / 103 / 112 — note 112 is 1-1-2, not 10X.
_CLAIM_ROW_RE = re.compile(
    r"^\|\s*([\d,\s\-–]+?)\s*\|\s*(§?\s*1\s*[01]\s*[0-9][^|]*?)\s*\|",
    re.MULTILINE)
_VALID_STATUTES = {"101", "102", "103", "112"}
# Vote table rows: | <Voice> | <recommendation> | <confidence> |
_VOTE_ROW_RE = re.compile(
    r"^\|\s*(Primary Examiner|§\s*102 Examiner|§\s*103 Examiner|"
    r"§\s*112 Examiner|Quantum Technical Specialist|"
    r"Supervisory Patent Examiner)\s*\|\s*([A-Za-z][A-Za-z \-/]*?)\s*\|"
    r"\s*(\d+(?:\.\d+)?)(?:\s*/\s*10)?\s*\|",
    re.MULTILINE)


def _normalize_disposition(d: str) -> str:
    r = d.strip().lower().replace(" ", "-")
    r = re.sub(r"-{2,}", "-", r).strip("-")
    aliases = {
        "allowed": "allowance", "allow": "allowance",
        "allowable": "allowance",
        "reject": "non-final-rejection",
        "rejected": "non-final-rejection",
        "rejection": "non-final-rejection",
        "non-final": "non-final-rejection",
        "nonfinal-rejection": "non-final-rejection",
        "final": "final-rejection",
        "restriction": "restriction-requirement",
    }
    return aliases.get(r, r)


def _expand_claim_spec(spec: str) -> list[int]:
    """'1, 3-5, 8' -> [1, 3, 4, 5, 8]."""
    out: list[int] = []
    for tok in re.split(r"[,\s]+", spec.strip()):
        if not tok:
            continue
        m = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", tok)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            out.extend(range(min(a, b), max(a, b) + 1))
        elif tok.isdigit():
            out.append(int(tok))
    return out


def _statute_of(cell: str) -> str:
    """Normalize a rejection cell to '101'/'102'/'103'/'112'.

    The statutes are 35 U.S.C. § 101/102/103/112 — note § 112 is 1-1-2,
    which a naive '10X' pattern misses. Match '1', then 0-or-1, then any
    digit, allowing whitespace the HTML/Markdown may have inserted.
    """
    m = re.search(r"1\s*([01])\s*([0-9])", cell)
    if not m:
        return "?"
    return "1" + m.group(1) + m.group(2)


# Canonical SPE block (authoritative; preferred over the per-examiner
# tables, which each use a different column schema):
#   ### Rejections of record
#   - § 101: none
#   - § 103: 1-20
_REJ_LINE_RE = re.compile(
    r"^[\-*\s]*§?\s*(1\s*[01]\s*[0-9])\s*[:\-]\s*(.+?)\s*$", re.MULTILINE)
_ALLOWABLE_LINE_RE = re.compile(
    r"^[\-*\s]*allowable\s*[:\-]\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def _parse_canonical_block(panel_text: str) -> tuple[dict[str, set], list[int]]:
    """Parse the SPE 'Rejections of record' block. Returns (by_statute,
    allowable_claims). Empty dict if the block is absent."""
    m = re.search(r"###\s*Rejections of record\s*(.+?)(?:\n#{1,3}\s|\Z)",
                  panel_text, re.S | re.IGNORECASE)
    if not m:
        return {}, []
    block = m.group(1)
    by_statute: dict[str, set] = {}
    for line in _REJ_LINE_RE.finditer(block):
        statute = re.sub(r"\s", "", line.group(1))
        if statute not in _VALID_STATUTES:
            continue
        claims = _expand_claim_spec(line.group(2))
        if claims:
            by_statute.setdefault(statute, set()).update(claims)
    allowable: list[int] = []
    am = _ALLOWABLE_LINE_RE.search(block)
    if am:
        allowable = _expand_claim_spec(am.group(1))
    return by_statute, allowable


def extract_office_action(panel_text: str, total_claims: int | None) -> dict:
    """Parse the full-mode panel into a machine-actionable Office Action.

    Deterministic — mirrors quantum_reviewer.extract_quality_gate but in
    patent vocabulary. The SPE's disposition decides pass/fail. Rejected
    claims come from the SPE's canonical 'Rejections of record' block when
    present (authoritative — it reconciles the examiners and drops § 101
    eligibility *passes*); otherwise from a per-examiner-table fallback.
    Missing pieces yield nulls/empties, never raises.
    """
    by_statute: dict[str, set] = {}
    allowable_from_block: list[int] = []
    block_statutes, allowable_from_block = _parse_canonical_block(panel_text)
    if block_statutes:
        by_statute = block_statutes
        parse_source = "SPE canonical 'Rejections of record' block"
    else:
        # Fallback: per-examiner rejection tables. Skip § 101 rows whose
        # basis cell says the claim is eligible (Voice 1's table lists
        # *passes*, not rejections).
        for m in _CLAIM_ROW_RE.finditer(panel_text):
            statute = _statute_of(m.group(2))
            if statute not in _VALID_STATUTES:
                continue
            row = m.group(0).lower()
            if statute == "101" and ("eligible" in row or "pass" in row):
                continue
            for c in _expand_claim_spec(m.group(1)):
                by_statute.setdefault(statute, set()).add(c)
        parse_source = "per-examiner rejection tables (canonical block absent)"

    rejected: set = set()
    for claims in by_statute.values():
        rejected |= claims
    rejected_claims = sorted(rejected)
    allowed_claims: list[int] = []
    if total_claims:
        allowed_claims = [c for c in range(1, total_claims + 1)
                          if c not in rejected]

    votes: dict[str, dict] = {}
    for m in _VOTE_ROW_RE.finditer(panel_text):
        voice = re.sub(r"\s+", " ", m.group(1)).strip()
        votes[voice] = {
            "disposition": _normalize_disposition(m.group(2)),
            "confidence": float(m.group(3)),
        }

    # SPE disposition: prefer an explicit "Disposition: X" line, else the
    # SPE's vote-table recommendation.
    dispo = None
    spe_idx = panel_text.find("Voice 6")
    tail = panel_text[spe_idx:] if spe_idx != -1 else panel_text
    m = _DISPO_RE.search(tail)
    if m:
        dispo = _normalize_disposition(m.group(1))
    if dispo not in _DISPOSITIONS:
        spe_vote = (votes.get("Supervisory Patent Examiner") or {})
        dispo = spe_vote.get("disposition", dispo)
    # If any claim is rejected, an "allowance" disposition is inconsistent;
    # downgrade so the gate cannot certify a patent with open rejections.
    if dispo == "allowance" and rejected_claims:
        dispo = "non-final-rejection"

    passes = (dispo in _PASSING) if dispo else None
    return {
        "disposition": dispo,
        "passes": passes,
        "n_claims_examined": total_claims,
        "n_claims_rejected": len(rejected_claims),
        "rejected_claims": rejected_claims,
        "allowed_claims": allowed_claims,
        "allowable_subject_matter": sorted(set(allowable_from_block)),
        "rejections_by_statute": {
            k: sorted(v) for k, v in sorted(by_statute.items())},
        "votes": votes,
        "source": "deterministic parse of office_action.md (USPTO Office "
                  "Action shape; no extra LLM call). Disposition from the "
                  "SPE synthesis; rejected claims from the "
                  + parse_source + ".",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", default="full", choices=sorted(MODES))
    ap.add_argument("--patent", required=True,
                    help="Google Patents URL, publication number "
                         "(US10614371B2), or a local saved .md/.html file")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--art-unit", default=None,
                    help="optional USPTO art-unit / CPC context string "
                         "for the examiner prompt")
    ap.add_argument("--filing-standard", default="uspto",
                    choices=sorted(_FILING_STANDARD_BLOCKS),
                    help="application-review standard: uspto (§112/MPEP), "
                         "epo (Art. 84/EPC), pct, or multi")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    try:
        patent = load_patent(args.patent)
    except Exception as e:                       # noqa: BLE001 — surface clean
        print(f"ERROR: could not load patent {args.patent!r}: {e}",
              file=sys.stderr)
        return 2

    # Persist the examiner-ready patent text so the run is reproducible and
    # downstream stages (fallacies, claims-registry, cqe) can read it.
    patent_md = args.outdir / "_patent_extracted.md"
    patent_md.write_text(patent.to_markdown(), encoding="utf-8")

    template = _load_template(args.mode)
    art_unit_block = (f"## Art unit / classification context\n\n{args.art_unit}"
                      if args.art_unit else
                      "_(no art-unit specified; use general quantum-computing "
                      "examination practice, CPC G06N10/00 family)_")

    class _SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"
    prompt = template.format_map(_SafeDict({
        "patent": patent.to_markdown(),
        "status_line": patent.status_line,
        "n_claims": patent.n_claims(),
        "art_unit_block": art_unit_block,
        "filing_standard": args.filing_standard,
        "filing_standard_block": _FILING_STANDARD_BLOCKS[args.filing_standard],
    }))
    (args.outdir / f"full_prompt_{args.mode}.txt").write_text(
        prompt, encoding="utf-8")

    try:
        result = call_llm(prompt, backend=args.llm, timeout=2400)
    except RuntimeError as e:
        primary = args.outdir / MODES[args.mode]
        primary.write_text(
            f"# ⚠ patent_reviewer ({args.mode}) FAILED\n\n"
            f"Backend {args.llm} did not return output: `{e}`\n",
            encoding="utf-8")
        return 3

    primary_text = result.text

    if args.mode == "full":
        missing = _check_panel_completeness(primary_text)
        if missing:
            primary_text = (
                "<!-- patent_reviewer FULL-mode panel-coverage header — "
                "code-emitted, do not edit -->\n"
                "# ⚠ Panel Coverage Warning\n\n"
                "The USPTO examiner panel did not emit all required voices. "
                f"Missing: {', '.join(missing)}.\n\n"
                "This Office Action was constructed without the "
                "examination perspective(s) above. Re-run with a different "
                "backend if a missing voice is load-bearing.\n\n---\n\n"
                + primary_text)
        office_action = extract_office_action(primary_text, patent.n_claims())
        (args.outdir / "_office_action.json").write_text(
            json.dumps(office_action, indent=2), encoding="utf-8")

    primary = args.outdir / MODES[args.mode]
    primary.write_text(primary_text, encoding="utf-8")
    (args.outdir / "_llm_generation.log").write_text(
        f"--- mode: {args.mode} ---\n"
        f"--- patent: {patent.pub_number} ({patent.kind_code}) ---\n"
        f"--- filing_standard: {args.filing_standard} ---\n"
        f"--- claims: {patent.n_claims()} ---\n"
        f"--- backend: {result.backend_actually_used} ---\n"
        f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
        f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
        encoding="utf-8")
    write_backend_marker(args.outdir, result)
    print(f"patent_reviewer[{args.mode}]: wrote {primary} "
          f"({patent.pub_number}, {patent.n_claims()} claims)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
