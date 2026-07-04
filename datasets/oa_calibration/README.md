# OA Calibration Set — Quantum Computing Patents

Calibration dataset of 9 granted US quantum-computing patents for training
and evaluating Office Action (OA) analysis models. Each patent directory contains:
- The granted patent PDF and pre-grant application publication PDF (as-filed claims)
- `real_oa_summary.json` — machine-readable OA metadata (app number, type, cited refs, route audit)
- `real_oa.txt` — OA full text when obtainable; placeholder with retrieval instructions otherwise

OA full text is **not yet on disk** for any patent — see the Route Audit below for why.
Examiner-cited references are available for all 9 patents (scraped from Google Patents HTML).

**SECURITY/LEGAL**: US20250259089A1 / Anyon Systems is explicitly excluded from this dataset.
Do not add it under any circumstances.

---

## Patent Manifest

| Patent | Title (short) | Assignee | App # | Filed | OA Status |
|--------|---------------|----------|-------|-------|-----------|
| US10915831B2 | Crosstalk mitigation in superconducting quantum bit gates | IBM | 16/719,123 | 2019-12-18 | cited refs only |
| US11455207B2 | Flag qubits for fault-tolerant topological codes | IBM | 16/512,143 | 2019-07-15 | cited refs only |
| US11080614B2 | Quantum coherence preservation of qubits | Anametric Inc | 15/832,285 | 2017-12-05 | cited refs only |
| US9985193B2  | Coupling quantum bits via localized resonators | IBM | 14/755,181 | 2015-06-30 | cited refs only |
| US11200508B2 | Modular control in a quantum computing system | Rigetti & Co LLC | 15/911,964 | 2018-03-05 | cited refs only |
| US10614371B2 | Debugging quantum circuits by circuit rewriting | IBM | 15/720,814 | 2017-09-29 | cited refs only |
| US10679138B2 | Topological qubit fusion | Microsoft Technology Licensing | 15/632,109 | 2017-06-23 | cited refs only |
| US10846608B2 | Codes and protocols for distilling T and Toffoli gates | Microsoft Technology Licensing | 15/982,988 | 2018-05-17 | cited refs only |
| US11023821B2 | Embedding condensed matter system with analog processor | D-Wave Systems Inc | 15/881,260 | 2018-01-26 | cited refs only |

All patents are CPC G06N 10/xx (quantum computing) subject matter.
Assignees span IBM (4), Microsoft (2), Anametric (1), Rigetti (1), D-Wave (1).

---

## Route Audit — OA Text Acquisition (as of 2026-07-03)

All four programmatic acquisition routes were probed. None succeeded without manual
browser access or a free USPTO API key registration.

### Route A — USPTO ODP Patent File Wrapper API

**Endpoint**: `https://api.uspto.gov/api/v1/patent/applications/{app_no_digits}/documents`
**Status**: HTTP 403 (`{"message":"Forbidden"}`) for all applications, anonymously and with `X-API-KEY: DEMO_KEY`
**Root cause**: Free API key required. Register at https://account.uspto.gov (email + name, no fee), then request key at https://account.uspto.gov/api-manager.
**One-command re-run once key obtained**:
```bash
APP=16719123  # US10915831B2
curl -H "X-API-KEY: <your_key>" \
  "https://api.uspto.gov/api/v1/patent/applications/${APP}/documents" \
  | jq '.documentBag[] | select(.documentCode | test("CTNF|CTFR")) | {code:.documentCode, date:.documentDate, href:.href}'
```
Then download each CTNF/CTFR PDF by appending the `href` to the base URL with the same key header.

### Route B — OARD Bulk Data (PatentsView S3)

**Endpoints tried**:
- `s3.amazonaws.com/data.patentsview.org/office-actions/office_action_research_dataset_2019-12-31.tar.gz` — HTTP 403
- `s3.amazonaws.com/data.patentsview.org/office-actions/office_action_research_dataset.tar.gz` — HTTP 403
- `data.uspto.gov/datasets/office-actions` — JavaScript SPA (AWS WAF), static HTML shell only
- `patentsview.org/download/office_action` — JavaScript SPA, no direct download link
- Harvard Dataverse (file 6934467) — HTTP 404
- `pairbulkdata.uspto.gov` — HTTP 000 (decommissioned)
- `bulkdata.uspto.gov` — not reachable

**Status**: BLOCKED. The OARD S3 bucket access model changed; formerly public objects now require auth or have been removed. Coverage was 2008-2017, which would have been ideal for the earlier IBM patents (US9985193B2 filed 2015).

**Alternative for section-label data**: BigQuery `patents-public-data.uspto_oce_office_actions.rejections` JOIN on `cpc_code LIKE 'G06N10%'` — requires GCP account but free tier is sufficient.

### Route C — Patent Center REST API

**Endpoints tried**:
- `https://patentcenter.uspto.gov/retrieval/public/v2/application/data?applicationNumberText=15188268` — HTTP 405
- `https://patentcenter.uspto.gov/retrieval/public/v1/application/data` — HTTP 405
- `https://patentcenter.uspto.gov/retrieval/public/v1/application/documents/15188268` — HTTP 405
- `https://patentcenter.uspto.gov/applications/15832285` — SPA HTML shell (Angular app), no data in static HTML
- `https://ped.uspto.gov/api/queries` — HTTP 000 (decommissioned)

**Status**: BLOCKED. Patent Center is a JavaScript SPA; the retrieval API returns HTTP 405 to non-browser clients regardless of headers. Works in a real browser without login.

**Browser recipe** (manual, ~2 min per patent):
1. Open `https://patentcenter.uspto.gov/applications/{app_no_digits}`
2. Click the "Documents" / "IFW" tab
3. Download the first CTNF or CTFR listed (oldest date = non-final rejection)

### Route D — EPO OPS / Espacenet

**Endpoints tried**:
- `https://ops.epo.org/3.2/rest-services/family/publication/epodoc/US9985193/biblio` — HTTP 403 (fair use policy violation)
- `https://ops.epo.org/3.2/rest-services/register/application/epodoc/US15188268A/events` — HTTP 403

**Status**: BLOCKED without OAuth client credentials. EPO OPS is free but requires app registration at epo.org/en/service/developer. Additionally, none of the 9 patents confirmed EP family members (checked Google Patents family listings).

**Espacenet alternative** (manual): `https://register.epo.org/application?number=EP{ep_number}` is fully open if an EP equivalent exists.

### What IS available (no auth required)

| Source | Data obtained | Method |
|--------|--------------|--------|
| `image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/{n}` | Granted patent PDFs + pre-grant publications | curl, bare numeric number |
| `patents.google.com/patent/{n}/en` HTML | Examiner-cited references (from "Cited by examiner" block) | regex on static HTML |
| `patents.google.com/patent/{n}/en` HTML | Application number, filing date, publication date | regex on static HTML |

Examiner-cited references (10-15 per patent) are in `real_oa_summary.json` for all 9 patents.
These are the references the examiner used in the OA — the same set that would appear in a CTNF/CTFR document.

---

## Per-Patent Details

### US10915831B2 — IBM (crosstalk mitigation in superconducting quantum bit gates)

**App #**: 16/719,123 | **Filed**: 2019-12-18 | **Granted**: 2021-02-09
**Google Patents**: https://patents.google.com/patent/US10915831B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/16719123
**CPC**: G06N 10/40 (quantum gates)

Files:
- `US10915831B2_granted.pdf` — 2.0 MB
- `US10915831B2_asfiled_pub.pdf` — 2.0 MB (pub US20200125987A1)
- `real_oa_summary.json` — 15 examiner-cited refs, app number, route audit
- `real_oa.txt` — placeholder with retrieval instructions

---

### US11455207B2 — IBM (flag qubits for fault-tolerant topological codes)

**App #**: 16/512,143 | **Filed**: 2019-07-15 | **Granted**: 2022-09-27
**Google Patents**: https://patents.google.com/patent/US11455207B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/16512143
**CPC**: G06N 10/70 (error correction / fault tolerance)

Files:
- `US11455207B2_granted.pdf` — 2.7 MB
- `US11455207B2_asfiled_pub.pdf` — 2.9 MB (pub US20210019223A1)
- `real_oa_summary.json` — 15 examiner-cited refs
- `real_oa.txt` — placeholder

---

### US11080614B2 — Anametric Inc (quantum coherence preservation)

**App #**: 15/832,285 | **Filed**: 2017-12-05 | **Granted**: 2021-08-03
**Google Patents**: https://patents.google.com/patent/US11080614B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/15832285
**CPC**: G06N 10/70 (quantum decoherence)

Files:
- `US11080614B2_granted.pdf` — 2.4 MB
- `US11080614B2_asfiled_pub.pdf` — 2.2 MB (pub US20180157986A1)
- `real_oa_summary.json` — 12 examiner-cited refs
- `real_oa.txt` — placeholder

---

### US9985193B2 — IBM (coupling quantum bits via localized resonators)

**App #**: 14/755,181 | **Filed**: 2015-06-30 | **Granted**: 2018-05-29
**Google Patents**: https://patents.google.com/patent/US9985193B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/14755181
**CPC**: G06N 10/40 (quantum hardware / qubit coupling)
**Note**: Earliest-filed patent in this set; examination likely within 2015-2017 OARD coverage window.

Files:
- `US9985193B2_granted.pdf` — 974 KB
- `US9985193B2_asfiled_pub.pdf` — 947 KB (pub US20170005255A1)
- `real_oa_summary.json` — 15 examiner-cited refs
- `real_oa.txt` — placeholder

---

### US11200508B2 — Rigetti & Co (modular quantum control)

**App #**: 15/911,964 | **Filed**: 2018-03-05 | **Granted**: 2021-12-14
**Google Patents**: https://patents.google.com/patent/US11200508B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/15911964
**CPC**: G06N 10/40 (quantum control systems)

Files:
- `US11200508B2_granted.pdf` — 966 KB
- `US11200508B2_asfiled_pub.pdf` — 912 KB (pub US20180260730A1)
- `real_oa_summary.json` — 15 examiner-cited refs
- `real_oa.txt` — placeholder

---

### US10614371B2 — IBM (debugging quantum circuits by circuit rewriting)

**App #**: 15/720,814 | **Filed**: 2017-09-29 | **Granted**: 2020-04-07
**Google Patents**: https://patents.google.com/patent/US10614371B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/15720814
**CPC**: G06N 10/20 | G06N 10/70 | G06N 10/80

Files:
- `US10614371B2_granted.pdf` — *(fetch with command below)*
- `real_oa_summary.json` — 11 examiner-cited refs
- `real_oa.txt` — placeholder

---

### US10679138B2 — Microsoft Technology Licensing (topological qubit fusion)

**App #**: 15/632,109 | **Filed**: 2017-06-23 | **Granted**: 2020-06-09
**Google Patents**: https://patents.google.com/patent/US10679138B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/15632109
**CPC**: G06N 10/20 | G06N 10/40 | B82Y10/00 (topological qubits / Majorana)

Files:
- `US10679138B2_granted.pdf` — *(fetch with command below)*
- `real_oa_summary.json` — 10 examiner-cited refs
- `real_oa.txt` — placeholder

---

### US10846608B2 — Microsoft Technology Licensing (T/Toffoli gate distillation protocols)

**App #**: 15/982,988 | **Filed**: 2018-05-17 | **Granted**: 2020-11-24
**Google Patents**: https://patents.google.com/patent/US10846608B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/15982988
**CPC**: G06N 10/20 | G06N 10/70 | G06N 10/80 (fault-tolerant quantum gates)

Files:
- `US10846608B2_granted.pdf` — *(fetch with command below)*
- `real_oa_summary.json` — 11 examiner-cited refs
- `real_oa.txt` — placeholder

---

### US11023821B2 — D-Wave Systems Inc (embedding condensed matter with analog processor)

**App #**: 15/881,260 | **Filed**: 2018-01-26 | **Granted**: 2021-06-01
**Google Patents**: https://patents.google.com/patent/US11023821B2/en
**Patent Center**: https://patentcenter.uspto.gov/applications/15881260
**CPC**: G06N 10/20 | G06N 10/40 (quantum annealing / analog QC)

Files:
- `US11023821B2_granted.pdf` — *(fetch with command below)*
- `real_oa_summary.json` — 11 examiner-cited refs
- `real_oa.txt` — placeholder

---

## Fetch Commands (no registration required)

### Granted PDFs + as-filed publications (original 5)

```bash
BASE="https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf"

# Granted patents (bare numeric number):
curl -s --max-time 90 "${BASE}/10915831" -o US10915831B2/US10915831B2_granted.pdf
curl -s --max-time 90 "${BASE}/11455207" -o US11455207B2/US11455207B2_granted.pdf
curl -s --max-time 90 "${BASE}/11080614" -o US11080614B2/US11080614B2_granted.pdf
curl -s --max-time 90 "${BASE}/9985193"  -o US9985193B2/US9985193B2_granted.pdf
curl -s --max-time 90 "${BASE}/11200508" -o US11200508B2/US11200508B2_granted.pdf

# Application publications (11-digit pub number):
curl -s --max-time 90 "${BASE}/20200125987" -o US10915831B2/US10915831B2_asfiled_pub.pdf
curl -s --max-time 90 "${BASE}/20210019223" -o US11455207B2/US11455207B2_asfiled_pub.pdf
curl -s --max-time 90 "${BASE}/20180157986" -o US11080614B2/US11080614B2_asfiled_pub.pdf
curl -s --max-time 90 "${BASE}/20170005255" -o US9985193B2/US9985193B2_asfiled_pub.pdf
curl -s --max-time 90 "${BASE}/20180260730" -o US11200508B2/US11200508B2_asfiled_pub.pdf
```

### New patents (4 added 2026-07-03)

```bash
# Granted PDFs:
curl -s --max-time 90 "${BASE}/10614371" -o US10614371B2/US10614371B2_granted.pdf
curl -s --max-time 90 "${BASE}/10679138" -o US10679138B2/US10679138B2_granted.pdf
curl -s --max-time 90 "${BASE}/10846608" -o US10846608B2/US10846608B2_granted.pdf
curl -s --max-time 90 "${BASE}/11023821" -o US11023821B2/US11023821B2_granted.pdf

# As-filed publications:
curl -s --max-time 90 "${BASE}/20190057337" -o US10614371B2/US10614371B2_asfiled_pub.pdf
curl -s --max-time 90 "${BASE}/20190012618" -o US10679138B2/US10679138B2_asfiled_pub.pdf
curl -s --max-time 90 "${BASE}/20190354897" -o US10846608B2/US10846608B2_asfiled_pub.pdf
curl -s --max-time 90 "${BASE}/20190236468" -o US11023821B2/US11023821B2_asfiled_pub.pdf
```

### OA PDFs (requires USPTO ODP API key)

```bash
# Register free at: https://account.uspto.gov → API Manager
# Then for each patent:
KEY="<your_odp_api_key>"
for APP in 16719123 16512143 15832285 14755181 15911964 15720814 15632109 15982988 15881260; do
  echo "=== $APP ==="
  curl -s -H "X-API-KEY: $KEY" \
    "https://api.uspto.gov/api/v1/patent/applications/${APP}/documents" \
    | jq -r '.documentBag[] | select(.documentCode | test("CTNF|CTFR")) | "\(.documentCode) \(.documentDate) \(.href)"'
done
```

---

## Directory Layout

```
oa_calibration/
  README.md                            (this file)
  US10915831B2/
    US10915831B2_granted.pdf           (2.0 MB) ✓
    US10915831B2_asfiled_pub.pdf       (2.0 MB) ✓
    real_oa_summary.json               ✓ (15 cited refs)
    real_oa.txt                        ✓ (placeholder — OA text pending API key)
  US11455207B2/
    US11455207B2_granted.pdf           (2.7 MB) ✓
    US11455207B2_asfiled_pub.pdf       (2.9 MB) ✓
    real_oa_summary.json               ✓ (15 cited refs)
    real_oa.txt                        ✓ (placeholder)
  US11080614B2/
    US11080614B2_granted.pdf           (2.4 MB) ✓
    US11080614B2_asfiled_pub.pdf       (2.2 MB) ✓
    real_oa_summary.json               ✓ (12 cited refs)
    real_oa.txt                        ✓ (placeholder)
  US9985193B2/
    US9985193B2_granted.pdf            (974 KB) ✓
    US9985193B2_asfiled_pub.pdf        (947 KB) ✓
    real_oa_summary.json               ✓ (15 cited refs)
    real_oa.txt                        ✓ (placeholder)
  US11200508B2/
    US11200508B2_granted.pdf           (966 KB) ✓
    US11200508B2_asfiled_pub.pdf       (912 KB) ✓
    real_oa_summary.json               ✓ (15 cited refs)
    real_oa.txt                        ✓ (placeholder)
  US10614371B2/                        (added 2026-07-03)
    real_oa_summary.json               ✓ (11 cited refs)
    real_oa.txt                        ✓ (placeholder)
  US10679138B2/                        (added 2026-07-03)
    real_oa_summary.json               ✓ (10 cited refs)
    real_oa.txt                        ✓ (placeholder)
  US10846608B2/                        (added 2026-07-03)
    real_oa_summary.json               ✓ (11 cited refs)
    real_oa.txt                        ✓ (placeholder)
  US11023821B2/                        (added 2026-07-03)
    real_oa_summary.json               ✓ (11 cited refs)
    real_oa.txt                        ✓ (placeholder)
```

---

## Notes

- US Anyon Systems (US20250259089A1) is explicitly excluded — legal conflict.
- All 9 patents are verified quantum-computing subject matter (CPC G06N 10/xx).
- Assignee diversity: IBM (4), Microsoft (2), Anametric (1), Rigetti (1), D-Wave (1).
- US9985193B2 (filed 2015-06-30) is the earliest; its examination window falls within OARD coverage (2008-2017) — highest priority for OARD BigQuery retrieval when available.
- `real_oa_summary.json` schema: `{publication_number, app_number, title, assignee, filing_date, oa_date, oa_type, sections, cited_refs, source_route, oa_text_available, access_note, patent_center_url, google_patents_url}`
- `oa_date` and `sections` (§101/102/103/112) are `null` / `[]` until OA text is retrieved — these require the OA document itself; they cannot be scraped from Google Patents HTML.
