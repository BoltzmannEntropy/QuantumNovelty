# Quantum Patent Office Actions Dataset

Ground-truth benchmark of USPTO quantum-computing patent records for evaluating
QuantumNovelty's `patent_reviewer` against real examination outcomes.

**Built**: 2026-06-29
**Records**: 28 patents
**Source**: Google Patents HTML scrape (patents.google.com)
**License**: USPTO patent data is US Government public domain (17 U.S.C. §105). Google Patents presents public USPTO data; redistribution of the structured fields derived from it is permitted.

---

## Quantum Scope (strict)

Only patents classified in **CPC G06N10** (quantum computing) and its subgroups:

| CPC code | Scope |
|---|---|
| G06N10/00 | Quantum computing (generic) |
| G06N10/20 | Quantum algorithms |
| G06N10/40 | Quantum hardware/qubits |
| G06N10/60 | Quantum simulation |
| G06N10/70 | Quantum error correction |
| G06N10/80 | Quantum benchmarking |

B82Y / H10N60 hardware CPCs are accepted only when the title unambiguously refers to
quantum computing. Every accepted record was validated against this criterion during
the build (`is_quantum_computing()` in `build_dataset.py`).

---

## Coverage

| Field | Count |
|---|---|
| Total records | 28 |
| With claims text | 28 (100%) |
| With OA type label | 28 (100%) |
| Non-final OA | 15 |
| Notice of allowance | 13 |
| With examiner-cited prior art | 28 (296 total refs, avg 10.6/patent) |
| §101/102/103/112 boolean labels | 0 (null — see Access Limitations) |
| Disposition: granted | 28 |

### Assignee distribution

| Assignee | Patents |
|---|---|
| International Business Machines Corp | 8 |
| D Wave Systems Inc | 4 |
| Microsoft Technology Licensing LLC | 3 |
| Google LLC | 2 |
| Zapata Computing Inc | 2 |
| Intel Corp | 1 |
| Harvard University | 1 |
| Anametric Inc | 1 |
| Massachusetts Institute of Technology | 1 |
| US Department of Navy | 1 |
| University of Chicago | 1 |
| Northrop Grumman Systems Corp | 1 |
| IonQ Inc | 1 |
| Atom Computing Inc | 1 |

---

## Schema

### Per-record JSON (`records/<pub_no>.json`)

```json
{
  "application_number": null,
  "publication_number": "US11042812B2",
  "title": "...",
  "assignee": "International Business Machines Corp",
  "filing_date": "2019-05-29",
  "publication_date": "2021-06-22",
  "cpc_codes": ["G06N10/00", "G06N10/20", "G06N10/80"],
  "claims_text": "1. A method comprising...",
  "office_action": {
    "date": null,
    "type": "notice-of-allowance",
    "rejected_claims": null,
    "section_101_rejected": null,
    "section_102_rejected": null,
    "section_103_rejected": null,
    "section_112_rejected": null,
    "cited_prior_art": [
      {"publication_number": "US10082539B2", "source": "google_patents_examiner_cited"}
    ],
    "full_text": null,
    "text_excerpt": null,
    "source_url": "https://patents.google.com/patent/US11042812B2/en",
    "access_note": "OA full text not programmatically accessible..."
  },
  "disposition": "granted",
  "provenance": {
    "title": "https://patents.google.com/patent/US11042812B2/en",
    "assignee": "https://patents.google.com/patent/US11042812B2/en",
    "filing_date": "https://patents.google.com/patent/US11042812B2/en",
    "cpc_codes": "https://patents.google.com/patent/US11042812B2/en",
    "claims_text": "https://patents.google.com/patent/US11042812B2/en",
    "disposition": "https://patents.google.com/patent/US11042812B2/en",
    "office_action_event": "https://patents.google.com/patent/US11042812B2/en",
    "build_date": "2026-06-29T...",
    "source": "google_patents_html_scrape"
  }
}
```

**Null fields and why:**

| Field | Why null |
|---|---|
| `application_number` | USPTO PEDS (ped.uspto.gov) is DNS-unreachable; Google Patents does not expose it in HTML |
| `office_action.date` | Google Patents HTML does not embed OA dates for all patents in a machine-readable form |
| `office_action.section_*_rejected` | Requires OARD bulk data (see Access Limitations); not in Google Patents |
| `office_action.full_text` / `text_excerpt` | USPTO OA text APIs are inaccessible (see Access Limitations) |

### `manifest.csv` columns

`publication_number`, `title`, `assignee`, `filing_date`, `publication_date`,
`cpc_codes` (pipe-separated), `disposition`, `oa_date`, `oa_type`,
`section_101_rejected`, `section_102_rejected`, `section_103_rejected`, `section_112_rejected`,
`has_claims_text`, `cited_prior_art_count`, `source_url`

### OA text files (`records/<pub_no>.oa.txt`)

Present for all records. Contains a structured "not available" notice and the
Patent Center manual-retrieval URL for each patent. When OARD bulk access is
obtained, these files should be populated with the real OA text.

---

## Access Limitations

All USPTO programmatic APIs were probed in June 2026. Results:

| Source | Status | Reason |
|---|---|---|
| data.uspto.gov OARD bulk (PTOFFACT/2017) | **Blocked** | Angular SPA returns 20666-byte HTML for all /ui/ paths. Requires ID.me browser login. |
| data.uspto.gov Patent File Wrapper API | **Blocked** | Same Angular SPA WAF |
| bulkdata.uspto.gov | **DNS fail** | ENOTFOUND from this automated environment |
| ped.uspto.gov (PEDS) | **DNS fail** | ENOTFOUND |
| efts.uspto.gov | **DNS fail** | ENOTFOUND |
| ptab.uspto.gov | **DNS fail** | ENOTFOUND |
| api.patentsview.org | **Blocked** | Now serves Angular SPA, not the API |
| search.patentsview.org | **DNS fail** | ENOTFOUND |
| s3.amazonaws.com/data.patentsview.org | **HTTP 403** | Requires signed URLs or registration |
| lens.org API | **HTTP 401** | Requires paid API key |
| ppubs.uspto.gov dirsearch | **HTTP 404** | Endpoint deprecated |
| BigQuery patents-public-data | **Not available** | gcloud/bq not installed |
| patents.google.com | **Working** | HTTP 200, full HTML with claims/CPCs/OA type/citations |

**Path to §-section labels**: Download the OARD rejections CSV from
`data.uspto.gov/ui/datasets/products/files/PTOFFACT/2017/rejections.csv.zip`
in a logged-in browser, then run:
```python
# Intersect OARD rejections with this dataset's publication_numbers
# OARD key is app_id; join via application_number (requires PEDS cross-ref)
```

---

## Files

```
quantum_patent_office_actions/
  README.md                    — this file
  build_dataset.py             — reproducible build script (Python 3.13)
  manifest.csv                 — 28 rows × 16 columns
  index.json                   — same content as JSON + coverage stats
  records/
    US10614371B2.json          — per-application full record
    US10614371B2.oa.txt        — OA text (structured "not available" notice)
    ...  (28 pairs total)
```

---

## Reproducing

```bash
/opt/homebrew/bin/python3.13 build_dataset.py --delay 2.0
```

Options: `--dry-run` (print seeds without fetching), `--limit N` (first N seeds).
Add new seeds to `SEED_PATENTS` in `build_dataset.py` and re-run; existing records
are overwritten with fresh fetches. Run the top-up pattern for incremental additions.

---

## Known Gaps and Future Work

1. **§-section rejection labels**: The highest-value gap. Requires OARD bulk data
   (manual download from data.uspto.gov after ID.me login) or BigQuery
   `patents-public-data.uspto_oce_office_actions.rejections` JOIN on `cpc_code LIKE 'G06N10%'`.

2. **OA full text**: Manual retrieval from USPTO Patent Center
   (patentcenter.uspto.gov → enter publication number → File Wrapper → Office Actions).

3. **Application numbers**: Cross-reference via PEDS once accessible; needed to join
   against OARD (which is keyed by `app_id`, not publication number).

4. **Pre-2012 quantum patents**: G06N10 was formally established ~2012; earlier quantum
   patents may be classified under G06N99 or H03K or legacy CPC codes.

5. **Pending/abandoned applications**: Current seed list is all granted patents (B1/B2).
   Published applications (A1/A2) with non-final rejections would complete the disposition mix.
