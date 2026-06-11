# `quantum_reviewer` — peer-review panel for quantum-computing papers

Six modes for simulating peer review on a quantum-computing paper. Inspired
by ARS's academic-paper-reviewer; the quantum twist is that the methodology-
focus mode and the calibration mode both lean on the audit-and-falsify
framework's checklist.

## CLI

```
quantum_reviewer/run.sh \
  --mode MODE \
  --draft PATH                  # required (the paper under review)
  --outdir DIR \
  [--llm BACKEND]
  [--journal SLUG]              # so the reviewer applies the right rubric
  [--gold-set DIR]              # for `calibration` mode only
```

## Modes

| Mode | Use | Trigger phrase |
|---|---|---|
| `full` | The complete 5-voice panel: Editor-in-Chief + Reviewer 1 + Reviewer 2 + Reviewer 3 + Devil's Advocate. Each voice writes ≥4 paragraphs; vote table at the end. | "Review this paper" |
| `quick` | One-page assessment by a single experienced reviewer | "Quick assessment of this paper" |
| `guided` | Iterative coaching session: surfaces specific weaknesses + suggests revisions | "Guide me to improve this paper" |
| `methodology-focus` | Reviewer panel ONLY on methodology (simulator precision, statistical reporting, ablations, audit framework adherence) | "Check the methodology" |
| `re-review` | Verify that a revised draft has actually addressed the prior round's reviewer comments | "Verify the revisions" |
| `calibration` | Run the reviewer against a gold set of known-good and known-flawed papers; report the panel's reliability metrics | "Calibrate this reviewer against my gold set" |

## Quantum twist per mode

- **`full` (the panel):**
  - **EIC** synthesises across the three reviewers + DA; produces the
    accept/major-revisions/minor-revisions/reject verdict
  - **R1** focuses on physics correctness (Hamiltonian construction,
    active-space choice, units, simulator precision)
  - **R2** focuses on algorithmic novelty (vs augmented baseline catalog —
    pulls live literature for the topic)
  - **R3** focuses on empirical evidence (statistical CIs, ablations,
    failure modes, audit-pipeline existence)
  - **Devil's Advocate** writes the strongest possible rejection of the
    paper, even if not the verdict's recommendation. Forces the EIC to
    address the worst-case reading.
- **`methodology-focus`**: assesses the paper specifically against the
  audit-and-falsify checklist used by `deep_research --mode review`.
- **`re-review`**: takes the prior round's reviewer comments PLUS the
  revised draft; checks that each comment was addressed at the level the
  reviewer would accept.
- **`calibration`**: runs the panel against the user-supplied gold set,
  reports how often the panel's verdict matches the gold label. Catches
  systematic bias (e.g., panel too generous on novelty, too strict on
  presentation).

## Outputs (in `--outdir`)

All modes:
- `_backend_used.json`
- `full_prompt_<mode>.txt`
- `_llm_generation.log`

Mode-specific:
- `full`: `review_panel.md` (5 voices + EIC verdict + vote table)
- `quick`: `quick_review.md`
- `guided`: `improvement_session.md`
- `methodology-focus`: `methodology_review.md` + `audit_checklist.json`
- `re-review`: `re_review.md` + per-comment satisfaction status
- `calibration`: `calibration_report.md` + `confusion_matrix.json`

## Provenance

Built on:
- ARS's academic-paper-reviewer multi-voice panel pattern
- the multi-voice editorial-board review pattern
  contributed the Devil's Advocate role design
- QN's `audit_falsify` primitives for methodology-focus and re-review
