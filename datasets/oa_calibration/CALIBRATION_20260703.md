# Patent-panel calibration — fixed pipeline, 2026-07-03

Nine granted US quantum-computing patents (known outcome: all claims allowed), six-voice panel
(`skills/patent_reviewer`, `--mode full`, claude backend), run AFTER the three pipeline repairs of
2026-07-03 (canonical-disposition parsing + `parse_conflict` flag; backward-citation seeding with
temporal guard; specification included). Panel outputs: `<patent>/panel_run/`.

| Patent | Assignee | Claims | Panel disposition | Rejected | Statutes | parse_conflict |
|---|---|---|---|---|---|---|
| US10915831B2 | IBM | 20 | non-final-rejection | 6 | 112 | no |
| US11455207B2 | IBM | 25 | allowance | 0 | — | yes (resolved to SPE) |
| US11080614B2 | Anametric | 15 | non-final-rejection | 2 | 112 | no |
| US9985193B2 | IBM | 19 | allowance | 0 | — | yes (resolved to SPE) |
| US11200508B2 | Rigetti | 22 | allowance | 0 | — | yes (resolved to SPE) |
| US10614371B2 | IBM | 25 | non-final-rejection | 4 | 112 | no |
| US10679138B2 | Microsoft | 18 | non-final-rejection | 4 | 112 | no |
| US10846608B2 | Microsoft | 16 | allowance | 0 | — | no |
| US11023821B2 | D-Wave | 7 | allowance | 0 | — | yes (resolved to SPE) |

## Aggregate vs the pre-fix sweep

| Metric | Old sweep (14 patents, defective pipeline) | This sweep (9 patents, fixed) |
|---|---|---|
| Over-rejection rate (granted set) | 14/14 = 100% | 4/9 = 44% |
| Mean claims rejected per patent | 17.6 | 1.8 (4.0 among rejected) |
| §102/§103 rejections | 12/14 patents | 0/9 |
| §112 rejections | 13/14 patents | 4/9, narrow (2-6 claims) |
| Allowances recovered | 0/14 | 5/9 |
| Silent allowance→rejection parse flips | undetected | 0 (4 conflicts flagged + resolved to SPE) |

## Caveats
- The two sweeps differ in sample (9 vs 14, partial overlap), prompt, and inputs (spec now included),
  so the improvement confounds the three fixes; per-fix ablation not run.
- All 9 targets are GRANTED patents examined on their final allowed claims, so "allowance" is the
  calibrated answer at the disposition level; a §112 non-final on 2-6 claims is over-rejection
  relative to the final record but not necessarily relative to the as-filed prosecution (real OA
  texts still pending — see README routes; free ODP API key or Patent Center browser session).
- Prior-art overlap vs the REAL examiner's OA citations is not yet measurable (no OA texts on disk).

## Next
1. Obtain real OA texts (Route A key or Patent Center) → section-level and citation-overlap scoring.
2. Per-fix ablation (re-run with --no-spec) to attribute the improvement.
3. Extend to all 28 dataset patents.
