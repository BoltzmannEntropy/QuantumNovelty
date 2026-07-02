# QN patent_reviewer Evaluation Summary

## Run Configuration
- Mode: full (6-voice USPTO panel)
- N evaluated: 14/14 (errors/timeouts: 0)
- Ground truth: 28 granted USPTO quantum patents (all disposition=granted)
- Sample: 14 patents, one per unique assignee (IBM, Intel, Microsoft, Harvard, D-Wave, Anametric, MIT, Google, US Navy, U Chicago, Northrop Grumman, IonQ, Zapata, Atom Computing)

---

## Metric 1 — Over-rejection Rate

Since all patents are **granted**, any non-allowance disposition is a false positive.

| Stat | Value |
|------|-------|
| Patents evaluated (successful runs) | 14 |
| Patents QN rejected (non-allowance) | 14 |
| **Over-rejection rate** | **100.0%** |
| Mean claims rejected per patent | 17.6 |

### Per-patent dispositions
- US10614371B2: non-final-rejection (claims_rej=22, sections=§103|§112)
- US10665769B2: non-final-rejection (claims_rej=24, sections=§103|§112)
- US10679138B2: non-final-rejection (claims_rej=18, sections=§103|§112)
- US10922617B2: non-final-rejection (claims_rej=13, sections=§103)
- US11023821B2: non-final-rejection (claims_rej=7, sections=§103|§112)
- US11080614B2: non-final-rejection (claims_rej=14, sections=§112)
- US11120360B2: final-rejection (claims_rej=21, sections=§103|§112)
- US11367011B2: non-final-rejection (claims_rej=14, sections=§103|§112)
- US11373112B2: non-final-rejection (claims_rej=20, sections=§103|§112)
- US11416228B2: non-final-rejection (claims_rej=15, sections=§103|§112)
- US11429887B2: non-final-rejection (claims_rej=17, sections=§103|§112)
- US11455563B2: non-final-rejection (claims_rej=19, sections=§103|§112)
- US11468357B2: non-final-rejection (claims_rej=34, sections=§101|§103|§112)
- US11580435B2: non-final-rejection (claims_rej=9, sections=§112)

### Section usage (among rejected patents)
| Section | Count |
|---------|-------|
| §101 (Alice/Mayo) | 1 |
| §102 (Anticipation) | 0 |
| §103 (Obviousness) | 12 |
| §112 (Enablement) | 13 |

---

## Metric 2 — Prior-art Overlap

QN-cited patent numbers (extracted from office_action.md prose) vs. examiner-cited references in ground-truth records.

| Stat | Value |
|------|-------|
| Mean examiner-cited refs per patent | 11.0 |
| Mean QN-cited refs per patent | 2.6 |
| Patents where QN surfaced ≥1 examiner ref | 0/14 (0.0%) |
| Mean overlap per patent | 0.00 |

---

## Errors / Timeouts
None

---

## Caveats & Limitations

1. **Small N (n=14)**: Results may not generalise. Run on all 28 for production use.
2. **Granted = final claims**: The USPTO ultimately allowed every patent in this set. QN reviews the stored claims (final granted form), not the original application claims — this likely makes QN's task harder (examiner already accepted these), so the over-rejection rate here is an upper-bound on real-world over-rejection against pending applications.
3. **No description fed**: `patent_io.load_patent` on a local `.md` receives only `claims_text` — no specification. §112 enablement rejections are penalised by this absence; enablement cannot be properly assessed without the written description. §112 counts should be interpreted as an artefact of the evaluation design.
4. **Examiner-cited ≠ exhaustive prior art**: The ground-truth `cited_prior_art` is from a single office action (non-final in most cases). Examiners cite a subset; QN may legitimately surface additional relevant prior art not in this list. Low overlap does not necessarily mean QN's prior art is wrong.
5. **Prior-art extraction via regex**: QN-cited numbers are extracted by regex from prose text. Numbers embedded in non-citation contexts (e.g., application filing numbers) may inflate `qn_cited_n`; the overlap denominator is correct but `qn_cited_n` may be noisy.
6. **Kind-code normalization**: Both sets normalized by stripping trailing letter+digit (e.g., B2, A1) before comparison — this is best-effort; some pub numbers may differ by country/series that don't reduce cleanly.
