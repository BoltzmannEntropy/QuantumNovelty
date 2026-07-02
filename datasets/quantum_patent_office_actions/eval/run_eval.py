#!/usr/bin/env python3.13
"""
QN patent_reviewer evaluation against 28 granted quantum patents.
Runs skill in --mode full on 14 selected patents, computes:
  1. Over-rejection rate (all granted; any rejection = false-positive)
  2. Prior-art overlap (QN-cited vs examiner-cited, kind-code-normalized)
"""
import json
import os
import re
import csv
import subprocess
import sys
from pathlib import Path

DATASET_ROOT = Path(__file__).parent.parent
RECORDS_DIR = DATASET_ROOT / "records"
EVAL_DIR = DATASET_ROOT / "eval"
SKILL_PY = Path(__file__).parents[3] / "skills" / "patent_reviewer" / "skill.py"
PYTHON = "/opt/homebrew/bin/python3.13"

# 14 patents: one per unique assignee for maximum spread
SELECTED = [
    "US10614371B2",   # IBM
    "US10665769B2",   # Intel
    "US10679138B2",   # Microsoft
    "US10922617B2",   # Harvard
    "US11023821B2",   # D-Wave
    "US11080614B2",   # Anametric
    "US11120360B2",   # MIT
    "US11367011B2",   # Google
    "US11373112B2",   # US Navy
    "US11416228B2",   # U Chicago
    "US11429887B2",   # Northrop Grumman
    "US11455563B2",   # IonQ
    "US11468357B2",   # Zapata
    "US11580435B2",   # Atom Computing
]


def normalize_pn(pn: str) -> str:
    """Normalize patent number for comparison.
    - Remove spaces, commas
    - Strip kind code (trailing letter+digit)
    - Convert publication app format: US2017/0364796A1 -> US20170364796
    """
    pn = pn.strip().upper().replace(" ", "").replace(",", "")
    # Strip kind code
    pn = re.sub(r'[A-Z]\d?$', '', pn)
    # Remove slash (US2017/0364796 -> US20170364796)
    pn = pn.replace("/", "")
    return pn


def extract_cited_from_md(md_text: str) -> list[str]:
    """Extract all patent numbers mentioned in the office action markdown.

    Handles formats:
      - US10614371B2 (no spaces)
      - US 9,477,796 B2 (comma-separated, spaces)
      - US 2017/0364796 A1 (publication app number)
      - EP1234567A1, WO2019/123456
    """
    patterns = [
        r'\bUS\s*\d{1,2}[,\s]?\d{3}[,\s]?\d{3}\s*[A-Z]\d?\b',   # US 9,477,796 B2 or US9477796B2
        r'\bUS\s*\d{8,12}\s*[A-Z]\d?\b',                           # US10614371B2 (no comma)
        r'\bUS\s*\d{4}/\d{7}\s*[A-Z]\d?\b',                        # US 2017/0364796 A1
        r'\bEP\s*\d{6,12}\s*[A-Z]?\d?\b',
        r'\bWO\s*\d{4}/\d{6}\s*[A-Z]?\b',
        r'\bCN\s*\d{6,12}\s*[A-Z]?\d?\b',
        r'\bJP\s*\d{6,12}\s*[A-Z]?\d?\b',
    ]
    all_nums: set[str] = set()
    for pat in patterns:
        for m in re.findall(pat, md_text, re.IGNORECASE):
            normalized = m.strip().upper().replace(" ", "").replace(",", "")
            all_nums.add(normalized)
    return list(all_nums)


def run_one(pub: str) -> dict:
    record_path = RECORDS_DIR / f"{pub}.json"
    with open(record_path) as f:
        record = json.load(f)

    # Ground truth examiner-cited prior art
    examiner_refs = record.get("office_action", {}).get("cited_prior_art", [])
    examiner_pns = [r["publication_number"] for r in examiner_refs if isinstance(r, dict)]
    examiner_norm = set(normalize_pn(p) for p in examiner_pns)

    # Write claims_text to a .md file for local load_patent()
    out_dir = EVAL_DIR / pub
    out_dir.mkdir(parents=True, exist_ok=True)
    claims_file = out_dir / f"{pub}.md"
    claims_text = record.get("claims_text", "")
    if not claims_text:
        return {"pub_no": pub, "qn_disposition": "error", "n_claims_rejected": 0,
                "sections_raised": "", "examiner_cited_n": len(examiner_pns),
                "qn_cited_n": 0, "overlap_n": 0, "error": "no claims_text"}

    with open(claims_file, "w") as f:
        f.write(f"# {pub}\n\n")
        f.write(claims_text)

    oa_json_path = out_dir / "_office_action.json"
    oa_md_path = out_dir / "office_action.md"

    if oa_json_path.exists() and oa_md_path.exists():
        print(f"\n>>> {pub} — outputs already exist, reading from cache", flush=True)
    else:
        # Run patent_reviewer
        print(f"\n>>> Running {pub} ...", flush=True)
        cmd = [
            PYTHON, str(SKILL_PY),
            "--mode", "full",
            "--patent", str(claims_file),
            "--outdir", str(out_dir),
            "--llm", "claude",
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(SKILL_PY.parent),
            )
            if result.returncode != 0:
                print(f"  STDERR: {result.stderr[-500:]}", flush=True)
                return {"pub_no": pub, "qn_disposition": "error", "n_claims_rejected": 0,
                        "sections_raised": "", "examiner_cited_n": len(examiner_pns),
                        "qn_cited_n": 0, "overlap_n": 0,
                        "error": f"returncode={result.returncode} {result.stderr[-200:]}"}
        except subprocess.TimeoutExpired:
            return {"pub_no": pub, "qn_disposition": "timeout", "n_claims_rejected": 0,
                    "sections_raised": "", "examiner_cited_n": len(examiner_pns),
                    "qn_cited_n": 0, "overlap_n": 0, "error": "timeout after 600s"}

    # Parse _office_action.json
    qn_data = {}
    if oa_json_path.exists():
        with open(oa_json_path) as f:
            qn_data = json.load(f)
    else:
        print(f"  WARNING: no _office_action.json for {pub}", flush=True)
        return {"pub_no": pub, "qn_disposition": "error", "n_claims_rejected": 0,
                "sections_raised": "", "examiner_cited_n": len(examiner_pns),
                "qn_cited_n": 0, "overlap_n": 0, "error": "no _office_action.json"}

    disposition = qn_data.get("disposition", "unknown")
    n_rejected = len(qn_data.get("rejected_claims", []))

    # Sections raised
    rbs = qn_data.get("rejections_by_statute", {})
    sections = sorted([k for k, v in rbs.items() if v])
    sections_str = "|".join(f"§{s}" for s in sections) if sections else ""

    # Extract cited patent numbers from office_action.md prose
    qn_cited_pns = []
    if oa_md_path.exists():
        with open(oa_md_path) as f:
            md_text = f.read()
        qn_cited_pns = extract_cited_from_md(md_text)

    # Exclude the patent being reviewed from the cited list
    qn_norm = set(normalize_pn(p) for p in qn_cited_pns if normalize_pn(p) != normalize_pn(pub))
    overlap_norm = qn_norm & examiner_norm
    overlap_n = len(overlap_norm)

    print(f"  disposition={disposition}  rejected={n_rejected}  "
          f"sections={sections_str}  examiner_refs={len(examiner_pns)}  "
          f"qn_cited={len(qn_norm)}  overlap={overlap_n}", flush=True)

    return {
        "pub_no": pub,
        "qn_disposition": disposition,
        "n_claims_rejected": n_rejected,
        "sections_raised": sections_str,
        "examiner_cited_n": len(examiner_pns),
        "qn_cited_n": len(qn_norm),
        "overlap_n": overlap_n,
    }


def main():
    print(f"Patent reviewer skill: {SKILL_PY}", flush=True)
    print(f"Records dir: {RECORDS_DIR}", flush=True)
    print(f"Eval dir: {EVAL_DIR}", flush=True)
    print(f"Running {len(SELECTED)} patents in full mode...\n", flush=True)

    rows = []
    for pub in SELECTED:
        row = run_one(pub)
        rows.append(row)

    # Write results.csv
    csv_path = EVAL_DIR / "results.csv"
    fieldnames = ["pub_no", "qn_disposition", "n_claims_rejected", "sections_raised",
                  "examiner_cited_n", "qn_cited_n", "overlap_n"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nResults written to {csv_path}", flush=True)

    # Compute summary stats
    good_rows = [r for r in rows if r["qn_disposition"] not in ("error", "timeout")]
    n_total = len(SELECTED)
    n_ran = len(good_rows)
    n_rejected_patents = sum(1 for r in good_rows if r["qn_disposition"] != "allowance")
    over_rejection_rate = n_rejected_patents / n_ran if n_ran else 0

    claims_rejected_fracs = []
    for r in good_rows:
        # We don't have total claims count in the JSON directly; use n_claims_rejected as proxy
        # (fractions will be reported as raw count; total claims per patent not available in qn_data)
        pass

    # Sections distribution
    section_counts = {"101": 0, "102": 0, "103": 0, "112": 0}
    for r in good_rows:
        for s in r["sections_raised"].split("|"):
            sec = s.replace("§", "").strip()
            if sec in section_counts:
                section_counts[sec] += 1

    # Prior-art overlap
    has_any_overlap = sum(1 for r in good_rows if r["overlap_n"] > 0)
    mean_overlap = sum(r["overlap_n"] for r in good_rows) / n_ran if n_ran else 0
    mean_examiner_cited = sum(r["examiner_cited_n"] for r in good_rows) / n_ran if n_ran else 0
    mean_qn_cited = sum(r["qn_cited_n"] for r in good_rows) / n_ran if n_ran else 0
    mean_claims_rej = sum(r["n_claims_rejected"] for r in good_rows) / n_ran if n_ran else 0

    # Per-patent dispo listing
    dispo_lines = []
    for r in good_rows:
        dispo_lines.append(f"- {r['pub_no']}: {r['qn_disposition']} "
                           f"(claims_rej={r['n_claims_rejected']}, sections={r['sections_raised']})")
    error_lines = [f"- {r['pub_no']}: {r.get('error','?')}" for r in rows if r['qn_disposition'] in ('error','timeout')]

    summary = f"""# QN patent_reviewer Evaluation Summary

## Run Configuration
- Mode: full (6-voice USPTO panel)
- N evaluated: {n_ran}/{n_total} (errors/timeouts: {n_total - n_ran})
- Ground truth: 28 granted USPTO quantum patents (all disposition=granted)
- Sample: 14 patents, one per unique assignee (IBM, Intel, Microsoft, Harvard, D-Wave, Anametric, MIT, Google, US Navy, U Chicago, Northrop Grumman, IonQ, Zapata, Atom Computing)

---

## Metric 1 — Over-rejection Rate

Since all patents are **granted**, any non-allowance disposition is a false positive.

| Stat | Value |
|------|-------|
| Patents evaluated (successful runs) | {n_ran} |
| Patents QN rejected (non-allowance) | {n_rejected_patents} |
| **Over-rejection rate** | **{over_rejection_rate:.1%}** |
| Mean claims rejected per patent | {mean_claims_rej:.1f} |

### Per-patent dispositions
{chr(10).join(dispo_lines)}

### Section usage (among rejected patents)
| Section | Count |
|---------|-------|
| §101 (Alice/Mayo) | {section_counts['101']} |
| §102 (Anticipation) | {section_counts['102']} |
| §103 (Obviousness) | {section_counts['103']} |
| §112 (Enablement) | {section_counts['112']} |

---

## Metric 2 — Prior-art Overlap

QN-cited patent numbers (extracted from office_action.md prose) vs. examiner-cited references in ground-truth records.

| Stat | Value |
|------|-------|
| Mean examiner-cited refs per patent | {mean_examiner_cited:.1f} |
| Mean QN-cited refs per patent | {mean_qn_cited:.1f} |
| Patents where QN surfaced ≥1 examiner ref | {has_any_overlap}/{n_ran} ({has_any_overlap/n_ran:.1%}) |
| Mean overlap per patent | {mean_overlap:.2f} |

---

## Errors / Timeouts
{"None" if not error_lines else chr(10).join(error_lines)}

---

## Caveats & Limitations

1. **Small N (n={n_ran})**: Results may not generalise. Run on all 28 for production use.
2. **Granted = final claims**: The USPTO ultimately allowed every patent in this set. QN reviews the stored claims (final granted form), not the original application claims — this likely makes QN's task harder (examiner already accepted these), so the over-rejection rate here is an upper-bound on real-world over-rejection against pending applications.
3. **No description fed**: `patent_io.load_patent` on a local `.md` receives only `claims_text` — no specification. §112 enablement rejections are penalised by this absence; enablement cannot be properly assessed without the written description. §112 counts should be interpreted as an artefact of the evaluation design.
4. **Examiner-cited ≠ exhaustive prior art**: The ground-truth `cited_prior_art` is from a single office action (non-final in most cases). Examiners cite a subset; QN may legitimately surface additional relevant prior art not in this list. Low overlap does not necessarily mean QN's prior art is wrong.
5. **Prior-art extraction via regex**: QN-cited numbers are extracted by regex from prose text. Numbers embedded in non-citation contexts (e.g., application filing numbers) may inflate `qn_cited_n`; the overlap denominator is correct but `qn_cited_n` may be noisy.
6. **Kind-code normalization**: Both sets normalized by stripping trailing letter+digit (e.g., B2, A1) before comparison — this is best-effort; some pub numbers may differ by country/series that don't reduce cleanly.
"""

    summary_path = EVAL_DIR / "eval_summary.md"
    with open(summary_path, "w") as f:
        f.write(summary)
    print(f"Summary written to {summary_path}", flush=True)

    # Print key numbers to stdout too
    print(f"\n=== RESULTS ===")
    print(f"N={n_ran} patents run in full mode")
    print(f"Over-rejection rate: {over_rejection_rate:.1%} ({n_rejected_patents}/{n_ran} patents rejected)")
    print(f"Mean claims rejected: {mean_claims_rej:.1f}")
    print(f"Sections: §101={section_counts['101']} §102={section_counts['102']} §103={section_counts['103']} §112={section_counts['112']}")
    print(f"Prior-art overlap: {has_any_overlap}/{n_ran} patents have ≥1 overlap, mean={mean_overlap:.2f}")


if __name__ == "__main__":
    main()
