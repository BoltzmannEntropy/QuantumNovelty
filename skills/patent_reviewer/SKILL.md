---
name: patent_reviewer
description: Simulated USPTO examiner panel for quantum-computing patents. Ingests a Google Patents URL / publication number / saved file, examines every claim individually under 35 U.S.C. §§ 101/102/103/112 + a quantum-operability check, and emits an Office Action plus a deterministic machine-actionable `_office_action.json` (disposition, rejected/allowed claims, rejections-by-statute). The patent analogue of quantum_reviewer.
---

# patent_reviewer — USPTO examiner panel

The quantum-patent analogue of `quantum_reviewer`. Where the paper reviewer
runs a journal referee panel, this runs a USPTO **examining unit** and
produces an **Office Action** keyed to the patent statutes.

## Why patents need their own reviewer

Patent review is not peer review. The object is the **claim set**, examined
claim-by-claim under 35 U.S.C.:

- **§ 101** — patent-eligible subject matter (Alice/Mayo; quantum algorithm
  claims draw abstract-idea scrutiny)
- **§ 102** — anticipation / novelty (a single prior-art reference)
- **§ 103** — obviousness (KSR combinations of references)
- **§ 112** — enablement, written description, definiteness (broad
  functional / fidelity language is the usual quantum failure mode)

A journal reviewer asks "is this good science?"; an examiner asks "are these
*claims* patentable?". Different question, different machinery.

## The panel (6 voices)

| Voice | Role |
|---|---|
| 1 | Primary Examiner — § 101 eligibility + overall disposition |
| 2 | § 102 Examiner — anticipation; names a single anticipatory reference |
| 3 | § 103 Examiner — obviousness; builds primary+secondary combinations |
| 4 | § 112 Examiner — enablement / written description / definiteness |
| 5 | Quantum Technical Specialist — operability; no-cloning / Holevo / fault-tolerance overreach |
| 6 | Supervisory Patent Examiner — synthesis + the disposition |

## Modes

| Mode | Output | Use |
|---|---|---|
| `full` (default) | `office_action.md` + `_office_action.json` | the full 6-voice Office Action |
| `quick` | `quick_examination.md` | fast single-voice patentability triage |

## Deterministic artifact — `_office_action.json`

Zero extra LLM cost. Parses the panel into a USPTO Office Action shape
(the patent analogue of ARC's `quality_gate.json`):

```json
{
  "disposition": "non-final-rejection",
  "passes": false,
  "n_claims_examined": 20,
  "n_claims_rejected": 17,
  "rejected_claims": [1, 2, 3, ...],
  "allowed_claims": [14, 19],
  "rejections_by_statute": {"102": [1, 8], "103": [2, 3, 4, ...], "112": [11]},
  "votes": { "Primary Examiner": {"disposition": "...", "confidence": 8.0}, ... }
}
```

Claim numbers are parsed mechanically from each examiner's per-claim
rejection table; the disposition comes from the SPE synthesis. An
`allowance` disposition with any rejected claim is auto-downgraded — the
gate cannot certify a patent that still has open rejections. `passes` is
true only for `allowance`.

## Usage

```bash
# Direct, against a live Google Patents URL:
bash skills/patent_reviewer/run.sh --mode full \
  --patent "https://patents.google.com/patent/US10614371B2/en" \
  --outdir runs/patent_demo --llm claude

# By publication number:
bash skills/patent_reviewer/run.sh --mode full --patent US10614371B2 --outdir out

# Quick triage:
bash skills/patent_reviewer/run.sh --mode quick --patent US10614371B2 --outdir out
```

Granted patents (`B1`/`B2` kind codes) are handled too — the panel reframes
itself as a post-grant validity / IPR-style review rather than an
examining-office Office Action (see `patent_io.Patent.status_line`).

## Files

- `skill.py` — driver: ingest patent → render examiner prompt → call LLM →
  panel-coverage header + `_office_action.json`
- `prompts/full.md` — the 6-voice Office Action panel prompt
- `prompts/quick.md` — single-voice triage prompt
- `../common/patent_io.py` — SSOT patent ingestion (URL / number / file → text)

## In the chain

Wired as the `patent-audit` pipeline in `chain/pipelines.py`
(`bash chain/run.sh --pipeline patent-audit --patent-url URL`): prior-art
research → this examiner panel → logical-fallacy scan → claims-registry →
CQE summary.
