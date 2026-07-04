#!/usr/bin/env /opt/homebrew/bin/python3.13
"""
build_dataset.py — Quantum Patent Office Actions Dataset Builder
================================================================
Scrapes Google Patents for a curated seed list of known G06N10 quantum-computing
US patents/applications, extracts metadata + claims, and writes the full dataset.

Access constraints discovered (June 2026):
  - USPTO OA Text API (data.uspto.gov): Angular SPA returns 20666-byte HTML for ALL paths
    including /ui/datasets/products/files/PTOFFACT/2017/rejections.csv.zip — not downloadable
    without a logged-in browser session. Requires ID.me identity verification.
  - OARD bulk data (USPTO Office Action Research Dataset for Patents, 2008-2017):
    Listed at data.uspto.gov/ui/datasets/products/files/PTOFFACT/2017/ but every request
    returns the Angular SPA HTML (HTTP 200, size=20666, Content-Type: text/html). Not accessible.
  - USPTO bulkdata.uspto.gov: DNS ENOTFOUND from this environment
  - USPTO PEDS (ped.uspto.gov): DNS ENOTFOUND
  - USPTO EFTS (efts.uspto.gov): DNS ENOTFOUND
  - PatentsView search.patentsview.org: DNS ENOTFOUND
  - PatentsView api.patentsview.org: redirects to Angular SPA (not the API)
  - PatentsView S3 (s3.amazonaws.com/data.patentsview.org): HTTP 403 for all paths
  - Lens.org: HTTP 401 (requires paid API key)
  - USPTO ppubs.uspto.gov dirsearch: HTTP 404
  - BigQuery patents-public-data: gcloud/bq not installed in this environment

Sole working source: Google Patents individual patent pages (HTTP 200).
OA text is NOT programmatically accessible; §101/102/103/112 booleans are null.
OA type/date are extracted from Google Patents legal-event text when present.

Usage:
    /opt/homebrew/bin/python3.13 build_dataset.py [--dry-run] [--limit N]
"""

import json
import csv
import re
import time
import urllib.request
import urllib.error
import urllib.parse
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ── Output paths ──────────────────────────────────────────────────────────────
DATASET_DIR = Path(__file__).parent
RECORDS_DIR = DATASET_DIR / "records"
MANIFEST_CSV = DATASET_DIR / "manifest.csv"
INDEX_JSON = DATASET_DIR / "index.json"

RECORDS_DIR.mkdir(exist_ok=True)

# ── Curated seed list ─────────────────────────────────────────────────────────
# Hand-curated G06N10 quantum computing patents from major assignees.
# Sources: Google Scholar, arXiv patent disclosures, well-known quantum IP portfolios.
# Format: (publication_number, expected_assignee_hint)
# Mix of granted (B1/B2) and published applications (A1/A2).

SEED_PATENTS = [
    # IBM / Kyndryl quantum computing
    ("US11042812B2", "IBM/Kyndryl"),      # Optimized testing of quantum-logic circuits
    ("US10755193B2", "IBM"),               # Efficient quantum circuit decomposition
    ("US11468357B2", "IBM"),               # Quantum circuit optimization via commutativity
    ("US10922617B2", "IBM"),               # Noise-adaptive compilation of quantum circuits
    ("US11373112B2", "IBM"),               # Quantum error mitigation
    ("US11551127B2", "IBM"),               # Quantum computing with variational quantum eigensolver
    ("US10810505B2", "IBM"),               # Verifying quantum programs with formal methods
    ("US11244241B2", "IBM"),               # Quantum circuit execution and noise characterization
    ("US10614371B2", "IBM"),               # Quantum advantage in machine learning
    ("US11294797B2", "IBM"),               # Quantum volume benchmarking

    # Google quantum computing
    ("US10679138B2", "Google"),            # Simulating quantum circuits
    ("US11373089B2", "Google"),            # Variational quantum eigensolvers
    ("US11586969B2", "Google"),            # Quantum supremacy via random circuit sampling
    ("US11023821B2", "Google"),            # Surface codes for quantum error correction
    ("US11494681B2", "Google"),            # Quantum processor calibration
    ("US10915821B2", "Google"),            # Quantum circuit compilation

    # IonQ quantum computing (trapped-ion)
    ("US11580435B2", "IonQ"),              # Trapped-ion quantum computing gate fidelity
    ("US11367011B2", "IonQ"),              # Reconfigurable trapped-ion qubit array
    ("US11093848B2", "IonQ"),             # Fault-tolerant quantum gate for trapped ions

    # Rigetti quantum computing (superconducting)
    ("US11307242B2", "Rigetti"),           # Parametric amplification for quantum readout
    ("US10846608B2", "Rigetti"),           # Forest quantum programming language
    ("US11429887B2", "Rigetti"),           # Quantum-classical hybrid algorithms

    # D-Wave (quantum annealing)
    ("US10600516B2", "D-Wave"),            # Analog quantum processor with quantum annealing
    ("US11348024B2", "D-Wave"),            # Hybrid quantum-classical optimization

    # Microsoft / Station Q (topological qubits / quantum error correction)
    ("US10872021B2", "Microsoft"),         # Topological qubit compilation
    ("US11193052B2", "Microsoft"),         # Majorana-based quantum computing
    ("US11416228B2", "Microsoft"),         # Quantum error decoding with neural networks

    # Intel quantum computing (silicon spin qubits)
    ("US11182531B2", "Intel"),             # Silicon spin qubit quantum gate
    ("US10665769B2", "Intel"),             # Qubit device packaging

    # Honeywell / Quantinuum
    ("US11281524B2", "Honeywell"),         # QCCD trapped-ion quantum computing
    ("US11455563B2", "Honeywell"),         # Quantum circuit compilation for QCCD

    # Alibaba/DAMO quantum
    ("US11386136B2", "Alibaba"),           # Quantum random number generation

    # Xanadu (photonic quantum computing)
    ("US11474867B2", "Xanadu"),            # Photonic quantum computing chip

    # Academic/startup quantum algorithms
    ("US11238360B2", "QCI"),               # Quantum computing with optimization
    ("US10755200B2", "Various"),           # Hybrid quantum-classical neural network
]

# ── HTTP helpers ───────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_google_patents(pub_no: str, retries: int = 2) -> str | None:
    """Fetch Google Patents HTML for a publication number. Returns HTML or None."""
    url = f"https://patents.google.com/patent/{pub_no}/en"
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", errors="replace")
                print(f"  [{pub_no}] HTTP {resp.status}", file=sys.stderr)
                return None
        except urllib.error.HTTPError as e:
            print(f"  [{pub_no}] HTTP error {e.code}", file=sys.stderr)
            return None
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            print(f"  [{pub_no}] Error: {e}", file=sys.stderr)
            return None
    return None


# ── Extraction helpers ─────────────────────────────────────────────────────────

def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

def extract_title(html: str) -> str | None:
    m = re.search(r"<title>([^<|]+)", html)
    if m:
        t = m.group(1).strip()
        # Remove " - Google Patents" suffix
        t = re.sub(r"\s*-\s*Google Patents\s*$", "", t).strip()
        return t or None
    return None

def extract_assignee(html: str) -> str | None:
    """
    Extract assignee from DC.contributor meta tags.
    Google Patents encodes: inventor names as early DC.contributor entries,
    the corporate assignee as the last DC.contributor entry that matches an org pattern.
    """
    contributors = re.findall(
        r'<meta[^>]+name=["\']DC\.contributor["\'][^>]+content=["\']([^"\']+)',
        html
    )
    if not contributors:
        return None
    org_patterns = re.compile(
        r'\b(?:Corp(?:oration)?|Inc(?:orporated)?|LLC|Ltd|GmbH|AG|SA|BV|NV|'
        r'University|Institute|Technologies|Systems|Computing|Lab(?:oratories)?|'
        r'Research|Solutions|Semiconductor|Holdings|Group|Foundation|'
        r'Quantinuum|IonQ|Rigetti|Xanadu|Microsoft|Google|IBM|Intel|Honeywell|'
        r'Alibaba|D-Wave|Zapata|Anametric|Atom)\b',
        re.IGNORECASE
    )
    for c in reversed(contributors[-4:]):
        if org_patterns.search(c):
            return c.strip()
    # Fallback: last contributor
    return contributors[-1].strip() if contributors else None

def extract_filing_date(html: str) -> str | None:
    """
    Extract filing date from Google Patents HTML.
    Primary: itemprop="filingDate" datetime attribute.
    Secondary: DC.date meta with scheme="dateSubmitted".
    Fallback: first DC.date meta value (typically the filing date).
    """
    # itemprop filingDate (most reliable)
    m = re.search(r'itemprop=["\']filingDate["\'][^>]*datetime=["\'](\d{4}-\d{2}-\d{2})', html)
    if m:
        return m.group(1)
    # DC.date with scheme="dateSubmitted"
    m = re.search(
        r'<meta[^>]+name=["\']DC\.date["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2})["\'][^>]+scheme=["\']dateSubmitted["\']',
        html
    )
    if m:
        return m.group(1)
    # Fallback: first DC.date value (filing precedes publication in Google Patents order)
    all_dc = re.findall(r'<meta[^>]+name=["\']DC\.date["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2})["\']', html)
    return all_dc[0] if all_dc else None

def extract_cpcs(html: str) -> list[str]:
    raw = re.findall(r'G06N\s*10[/\w]*', html)
    # Also capture B82Y and H10N60 quantum hardware CPC codes
    raw += re.findall(r'B82Y\s*10/\d+|H10N\s*60/\d+', html)
    # Normalize whitespace in CPC codes
    normalized = [re.sub(r'\s+', '', c) for c in raw]
    # Deduplicate preserving order
    seen = set()
    result = []
    for c in normalized:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result

def extract_claims(html: str) -> str | None:
    # Try the <section class="claims"> block
    m = re.search(r'class=["\']claims["\'\s][^>]*>(.*?)</section>', html, re.DOTALL | re.IGNORECASE)
    if m:
        raw = _strip_html(m.group(1))
        if len(raw) > 50:
            return raw[:8000]  # cap at 8k chars
    # Fallback: find claim-numbered text
    claims = re.findall(r'(?:<claim[^>]*>|claim\s+\d+\.?\s+)(.*?)(?=claim\s+\d+|\Z)', html, re.DOTALL | re.IGNORECASE)
    if claims:
        combined = " ".join(_strip_html(c) for c in claims[:20])
        if len(combined) > 50:
            return combined[:8000]
    return None

def extract_disposition(html: str) -> str | None:
    # Look for grant/pending/abandoned indicators
    if re.search(r'Status[^<]{0,50}(?:Grant|Granted)', html, re.IGNORECASE):
        return "granted"
    if re.search(r'patent\s+grant|granted\s+patent', html, re.IGNORECASE):
        return "granted"
    if re.search(r'Status[^<]{0,50}(?:Abandon|Abandoned|Expired)', html, re.IGNORECASE):
        return "abandoned"
    if re.search(r'Status[^<]{0,50}(?:Pend|Pending|Active)', html, re.IGNORECASE):
        return "pending"
    # B2/B1 suffixes usually mean granted
    return None

def extract_publication_date(html: str) -> str | None:
    """
    Extract publication date from Google Patents HTML.
    Primary: itemprop="publicationDate" datetime attribute.
    Secondary: DC.date meta with scheme="issue".
    Fallback: second DC.date meta value (publication follows filing in Google Patents order).
    """
    # itemprop publicationDate
    m = re.search(r'itemprop=["\']publicationDate["\'][^>]*datetime=["\'](\d{4}-\d{2}-\d{2})', html)
    if m:
        return m.group(1)
    # DC.date with scheme="issue"
    m = re.search(
        r'<meta[^>]+name=["\']DC\.date["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2})["\'][^>]+scheme=["\']issue["\']',
        html
    )
    if m:
        return m.group(1)
    # Fallback: second DC.date value
    all_dc = re.findall(r'<meta[^>]+name=["\']DC\.date["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2})["\']', html)
    return all_dc[1] if len(all_dc) > 1 else None

def _infer_pub_year(pub_no: str) -> int | None:
    """Infer publication year from a publication number.

    US utility patents: US7xxxxxxx = 7M+ serial → post-2002; US8xxxxxxx →
    post-2011; US10xxxxxxB2 → 10M+ serial → post-~2018.  For applications
    (US2017xxxxxxA1) the year is embedded as the first 4 digits after "US".
    """
    # Application style: US20YYXXXXXA1 → year = 20YY
    m = re.match(r"US(20\d{2})\d+[A-Z]", pub_no)
    if m:
        return int(m.group(1))
    # EP / WO / JP / CN applications often embed year
    m = re.match(r"(?:EP|WO|JP|CN)((?:19|20)\d{2})\d+", pub_no)
    if m:
        return int(m.group(1))
    # Granted US: serial number correlates with issue year but is not
    # reliably year-encoded; skip to avoid false guards.
    return None


def extract_cited_prior_art(
    html: str, priority_year: int | None = None
) -> list[dict]:
    """Extract backward-citation prior art references (publication numbers).

    Scopes to the "Patent citations" section of Google Patents HTML (backward
    citations — what the patent itself cites as prior art).  The old approach
    scraped "Cited by examiner", which is a *forward*-citation subsection and
    yields post-grant forward references, not prior-art references.

    If *priority_year* is provided, references whose inferred publication year
    post-dates the priority year are dropped (temporal guard) — they cannot
    logically be prior art.  The number of dropped entries is logged to stdout.
    """
    # "Patent citations" is the backward-citation heading on Google Patents.
    # It appears before "Non-patent citations" and "Cited by" sections.
    idx = html.find("Patent citations")
    if idx < 0:
        # Fallback: older Google Patents layout may use "References Cited"
        idx = html.find("References Cited")
    if idx < 0:
        return []
    block = html[idx:idx + 8000]
    # Stop at the next major section (forward citations or family)
    end = re.search(
        r'Non-patent citations|Cited by|Family Cites Families|<section\b',
        block
    )
    if end:
        block = block[:end.start()]
    # Extract US/EP/WO/JP/CN publication numbers
    pub_nos = re.findall(r'(?:US|EP|WO|JP|CN)\d{6,11}[A-Z][0-9]?', block)
    seen: set[str] = set()
    result = []
    dropped = 0
    for pn in pub_nos:
        if pn in seen:
            continue
        seen.add(pn)
        if priority_year is not None:
            pub_year = _infer_pub_year(pn)
            if pub_year is not None and pub_year > priority_year:
                dropped += 1
                continue  # post-dates priority — not prior art
        result.append({"publication_number": pn, "source": "google_patents_backward_citation"})
    if dropped:
        print(f"  [prior-art filter] dropped {dropped} reference(s) "
              f"post-dating priority year {priority_year}")
    return result

def extract_oa_events(html: str) -> dict | None:
    """
    Extract office-action event type and date from Google Patents legal events.
    Returns dict with type/date or None.
    NOTE: Google Patents does NOT expose §101/102/103/112 rejection labels or OA full text.
    """
    oa_type = None
    oa_date = None

    # Common OA event label patterns that appear in Google Patents HTML
    oa_patterns = [
        (r'NON[-\s]?FINAL\s+(?:OFFICE\s+ACTION|REJECTION|ACTION MAILED)', "non-final"),
        (r'NONFINAL\s+(?:REJECTION|ACTION|OFFICE)', "non-final"),
        (r'FINAL\s+(?:REJECTION|OFFICE\s+ACTION|ACTION MAILED)', "final"),
        (r'NOTICE\s+OF\s+ALLOWANCE', "notice-of-allowance"),
        (r'NOTICE OF ALLOWABILITY', "notice-of-allowance"),
        (r'ADVISORY\s+ACTION', "advisory"),
    ]

    for pattern, label in oa_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            oa_type = label
            # Try to find a date near this event
            m = re.search(
                pattern + r'[^<]{0,100}?(\d{4}-\d{2}-\d{2})',
                html, re.IGNORECASE | re.DOTALL
            )
            if m:
                oa_date = m.group(1)
            else:
                # Search backwards for a date before this pattern
                idx = re.search(pattern, html, re.IGNORECASE)
                if idx:
                    before = html[max(0, idx.start()-200):idx.start()]
                    dm = re.findall(r'\d{4}-\d{2}-\d{2}', before)
                    if dm:
                        oa_date = dm[-1]
            break

    if not oa_type:
        # Check for allowance even without explicit OA
        if re.search(r'ALLOWED|ALLOWANCE|GRANT[^S]', html, re.IGNORECASE):
            oa_type = "notice-of-allowance"

    if oa_type:
        return {"type": oa_type, "date": oa_date}
    return None


def is_quantum_computing(cpcs: list[str], title: str, html: str) -> bool:
    """
    Strict quantum scope filter: must have G06N10 CPC code, OR
    must have B82Y/H10N60 + unambiguous quantum-computing title/abstract.
    """
    for c in cpcs:
        if c.startswith("G06N10"):
            return True
    # B82Y / H10N60 optional path
    has_quantum_hw = any(
        c.startswith("B82Y") or c.startswith("H10N60") for c in cpcs
    )
    if has_quantum_hw:
        quantum_terms = re.compile(
            r'\b(?:qubit|quantum\s+comput|quantum\s+circuit|quantum\s+gate|quantum\s+error|'
            r'superconducting\s+qubit|trapped\s+ion|topological\s+qubit)\b',
            re.IGNORECASE
        )
        if quantum_terms.search(title or ""):
            return True
        # Check abstract/description for unambiguous QC references
        abstract_m = re.search(r'<section[^>]*abstract[^>]*>(.*?)</section>', html, re.DOTALL | re.IGNORECASE)
        if abstract_m and quantum_terms.search(abstract_m.group(1)):
            return True
    return False


# ── Record builder ─────────────────────────────────────────────────────────────

def extract_description(html: str) -> str | None:
    """Extract the written description / specification from Google Patents HTML."""
    m = re.search(
        r'<section[^>]*itemprop=["\']description["\'][^>]*>(.*?)</section>',
        html, re.DOTALL | re.IGNORECASE
    )
    if m:
        raw = _strip_html(m.group(1))
        if len(raw) > 50:
            return raw[:40000]  # cap at 40KB to avoid bloating records
    return None


def build_record(pub_no: str, hint: str, html: str) -> dict:
    """Build a full structured record from Google Patents HTML."""
    title = extract_title(html) or ""
    assignee = extract_assignee(html)
    filing_date = extract_filing_date(html)
    pub_date = extract_publication_date(html)
    cpcs = extract_cpcs(html)
    claims = extract_claims(html)
    description = extract_description(html)
    disposition = extract_disposition(html)
    # Derive priority_year from filing_date for the temporal guard
    priority_year: int | None = None
    if filing_date:
        try:
            priority_year = int(filing_date[:4])
        except (ValueError, IndexError):
            pass
    cited_art = extract_cited_prior_art(html, priority_year=priority_year)
    oa_event = extract_oa_events(html)

    # Infer disposition from pub suffix if not found in HTML text
    if not disposition:
        if re.search(r'B[12]$', pub_no):
            disposition = "granted"
        elif re.search(r'A[12]$', pub_no):
            disposition = "pending"

    source_url = f"https://patents.google.com/patent/{pub_no}/en"

    record = {
        "application_number": None,   # Not reliably extractable without PEDS
        "publication_number": pub_no,
        "title": title,
        "assignee": assignee or hint,
        "filing_date": filing_date,
        "publication_date": pub_date,
        "cpc_codes": cpcs,
        "claims_text": claims,
        "description_text": description,
        "office_action": {
            "date": oa_event["date"] if oa_event else None,
            "type": oa_event["type"] if oa_event else None,
            "rejected_claims": None,
            # §-section rejection booleans: NOT determinable from Google Patents
            # USPTO OA Text APIs are inaccessible from this environment.
            "section_101_rejected": None,
            "section_102_rejected": None,
            "section_103_rejected": None,
            "section_112_rejected": None,
            "cited_prior_art": cited_art,
            "full_text": None,
            "text_excerpt": None,
            "source_url": source_url if oa_event else None,
            "access_note": (
                "OA full text not programmatically accessible. "
                "USPTO OA Text API (data.uspto.gov), bulkdata.uspto.gov, "
                "PEDS (ped.uspto.gov), and Patent Center retrieval APIs "
                "are all blocked from this environment (DNS failures / SPA WAF). "
                "Retrieve manually at: https://patentcenter.uspto.gov/"
            ),
        },
        "disposition": disposition,
        "provenance": {
            "title": source_url,
            "assignee": source_url,
            "filing_date": source_url,
            "cpc_codes": source_url,
            "claims_text": source_url,
            "disposition": source_url,
            "office_action_event": source_url if oa_event else None,
            "build_date": datetime.now(timezone.utc).isoformat(),
            "source": "google_patents_html_scrape",
        },
    }
    return record


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build quantum patent OA dataset")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be fetched, don't write")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N seeds")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between fetches (seconds)")
    args = parser.parse_args()

    seeds = SEED_PATENTS
    if args.limit:
        seeds = seeds[:args.limit]

    print(f"Building quantum patent OA dataset — {len(seeds)} seeds", file=sys.stderr)
    print(f"Output: {DATASET_DIR}", file=sys.stderr)

    records = []
    skipped = []
    failed = []

    for i, (pub_no, hint) in enumerate(seeds):
        print(f"[{i+1}/{len(seeds)}] {pub_no} ({hint})", file=sys.stderr)

        if args.dry_run:
            print(f"  DRY-RUN: would fetch https://patents.google.com/patent/{pub_no}/en", file=sys.stderr)
            continue

        html = fetch_google_patents(pub_no)
        if not html:
            print(f"  FAILED to fetch {pub_no}", file=sys.stderr)
            failed.append(pub_no)
            continue

        cpcs = extract_cpcs(html)
        title = extract_title(html) or ""

        if not is_quantum_computing(cpcs, title, html):
            print(f"  SKIP {pub_no}: CPCs {cpcs} not G06N10 quantum scope", file=sys.stderr)
            skipped.append({"pub_no": pub_no, "cpcs": cpcs, "reason": "not_quantum_scope"})
            continue

        record = build_record(pub_no, hint, html)
        records.append(record)

        # Write per-record JSON
        rec_path = RECORDS_DIR / f"{pub_no}.json"
        with open(rec_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        # Write OA text file (empty but structured note)
        oa_path = RECORDS_DIR / f"{pub_no}.oa.txt"
        with open(oa_path, "w", encoding="utf-8") as f:
            if record["office_action"]["text_excerpt"]:
                f.write(record["office_action"]["text_excerpt"])
            else:
                f.write(
                    f"[OA text not available for {pub_no}]\n"
                    f"Source limitation: USPTO Office Action text APIs are not accessible\n"
                    f"from automated environments (DNS failures / SPA WAF protection).\n"
                    f"Manual retrieval: https://patentcenter.uspto.gov/ → search {pub_no}\n"
                )

        oa_type = record["office_action"]["type"] or "unknown"
        has_claims = bool(record["claims_text"])
        print(
            f"  OK  title={record['title'][:60]!r}  "
            f"cpcs={record['cpc_codes'][:3]}  "
            f"oa={oa_type}  claims={'yes' if has_claims else 'NO'}",
            file=sys.stderr
        )

        # Polite delay
        if i < len(seeds) - 1:
            time.sleep(args.delay)

    if args.dry_run:
        print(f"DRY-RUN complete: {len(seeds)} seeds would be processed", file=sys.stderr)
        return

    # ── Write manifest.csv ────────────────────────────────────────────────────
    fieldnames = [
        "publication_number", "title", "assignee", "filing_date", "publication_date",
        "cpc_codes", "disposition",
        "oa_date", "oa_type",
        "section_101_rejected", "section_102_rejected",
        "section_103_rejected", "section_112_rejected",
        "has_claims_text", "cited_prior_art_count",
        "source_url",
    ]
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            oa = rec["office_action"]
            writer.writerow({
                "publication_number": rec["publication_number"],
                "title": rec["title"],
                "assignee": rec["assignee"],
                "filing_date": rec["filing_date"] or "",
                "publication_date": rec["publication_date"] or "",
                "cpc_codes": "|".join(rec["cpc_codes"]),
                "disposition": rec["disposition"] or "",
                "oa_date": oa["date"] or "",
                "oa_type": oa["type"] or "",
                "section_101_rejected": "" if oa["section_101_rejected"] is None else str(oa["section_101_rejected"]),
                "section_102_rejected": "" if oa["section_102_rejected"] is None else str(oa["section_102_rejected"]),
                "section_103_rejected": "" if oa["section_103_rejected"] is None else str(oa["section_103_rejected"]),
                "section_112_rejected": "" if oa["section_112_rejected"] is None else str(oa["section_112_rejected"]),
                "has_claims_text": str(bool(rec["claims_text"])),
                "cited_prior_art_count": len(oa["cited_prior_art"]),
                "source_url": rec["provenance"]["title"],
            })

    # ── Write index.json ──────────────────────────────────────────────────────
    index = {
        "dataset": "quantum_patent_office_actions",
        "built": datetime.now(timezone.utc).isoformat(),
        "quantum_scope": "CPC G06N10 (quantum computing) and subgroups G06N10/00, /20, /40, /60, /70, /80",
        "total_records": len(records),
        "total_seeds": len(seeds),
        "skipped_out_of_scope": len(skipped),
        "failed_fetch": len(failed),
        "records": [
            {
                "publication_number": rec["publication_number"],
                "title": rec["title"],
                "assignee": rec["assignee"],
                "filing_date": rec["filing_date"],
                "publication_date": rec["publication_date"],
                "cpc_codes": rec["cpc_codes"],
                "disposition": rec["disposition"],
                "oa_type": rec["office_action"]["type"],
                "oa_date": rec["office_action"]["date"],
                "has_claims_text": bool(rec["claims_text"]),
                "cited_prior_art_count": len(rec["office_action"]["cited_prior_art"]),
                "section_101_rejected": rec["office_action"]["section_101_rejected"],
                "section_102_rejected": rec["office_action"]["section_102_rejected"],
                "section_103_rejected": rec["office_action"]["section_103_rejected"],
                "section_112_rejected": rec["office_action"]["section_112_rejected"],
            }
            for rec in records
        ],
        "failed": failed,
        "skipped": skipped,
    }
    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    n_with_claims = sum(1 for r in records if r["claims_text"])
    n_with_oa_type = sum(1 for r in records if r["office_action"]["type"])
    n_granted = sum(1 for r in records if r["disposition"] == "granted")
    n_pending = sum(1 for r in records if r["disposition"] == "pending")

    print(f"\n=== Dataset Summary ===", file=sys.stderr)
    print(f"  Total records:        {len(records)}", file=sys.stderr)
    print(f"  With claims text:     {n_with_claims}", file=sys.stderr)
    print(f"  With OA type label:   {n_with_oa_type}", file=sys.stderr)
    print(f"  Disposition granted:  {n_granted}", file=sys.stderr)
    print(f"  Disposition pending:  {n_pending}", file=sys.stderr)
    print(f"  Failed fetches:       {len(failed)}", file=sys.stderr)
    print(f"  Out-of-scope skipped: {len(skipped)}", file=sys.stderr)
    print(f"  Output: {DATASET_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
