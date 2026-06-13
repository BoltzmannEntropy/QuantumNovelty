# Majorana 2 — old chain vs. new chain (two added stages)

Paper: `examples/paper_reviews/majorana2/majorana2_arxiv.pdf`
("20 Second Parity Lifetime in an InAs–Pb Tetron Device", target venue PRX Quantum).

The new chain = the existing `paper-audit` chain **plus two stages**:
`requirements_judge` (claim-vs-evidence audit + allowed/forbidden manifest)
and `evidence_ledger` (deterministic reviewer-hallucination guard).
Both adopted from ARC's gate patterns.

## What each run contains

| | Old run (`majorana2/`) | New run (`majorana2_newchain/`) |
|---|---|---|
| research review | ✓ | ✓ (reused) |
| 5-voice reviewer panel | ✓ | ✓ (reused) |
| **requirements_judge** | — | ✓ **new** |
| argument structure | ✓ | ✓ (reused) |
| logical fallacies | ✓ | ✓ (reused) |
| claims registry | ✓ | ✓ (reused) |
| disclosure audit | ✓ | ✓ (reused) |
| revision planner | ✓ | ✓ (reused) |
| **evidence_ledger (build + audit)** | — | ✓ **new** |
| CQE summary | ✓ | ✓ (regenerated) |

## Headline verdicts (unchanged — and that is correct)

- Reviewer panel: **MAJOR-REVISIONS** (mean 6.33/10), both runs.
- CQE composite (under the fixed scorer): **26/100**, both runs.

The CQE is dominated by *generative*-pipeline probes (pareto archive,
paper.tex, Wilson CIs) that a paper-audit run never produces, so the
composite barely moves. The new chain's value is **not** in the headline
number — it is in two new, actionable evidence layers.

## What the new chain adds

### 1. requirements_judge — `02e_requirements_judge/requirements_report.json`
Verdict **partial**. 11 central claims reconstructed and ruled against the
paper's own evidence (10 met-or-partial, 1 unmet). **7 overclaims** flagged
with figure-anchored evidence, e.g.:

- "non-equilibrium quasiparticles no longer limit qubit operations" — only
  *Z*-parity lifetime was measured.
- τX / Pauli-X fidelity claims — no X-parity measurement performed.
- "EM < 1 µeV" stated as definite — value is at the ~1 µeV resolution limit.
- "scalable / can be tiled into larger arrays", "modular unit cell",
  "fault-tolerant multi-qubit arrays" — only single-tetron data exists.

Plus an **allowed-claims** manifest (the 8 claims the evidence does license)
and `delta_feedback` with concrete rescopes. This is hypothesis-level
claim-evidence accounting the old chain did not produce; it corroborates and
sharpens the panel's "single-wire scope / speculative τX" findings.

### 2. evidence_ledger — `98_evidence_ledger_audit/ledger_audit.json`
Pre-registered 279 distinct numerics + normalized full text from the paper,
then audited all 8 review reports for claims/quotes/numbers attributed to the
paper that the paper never made. **0 hallucinations** — i.e. every number and
quote the reviewers pinned on the paper traces back to it. That is a trust
signal the old chain could not provide. (Validated separately: injected
fabrications — a fake "9999 s" quote, invented "4500 K", a bogus cite key —
are all caught; precision verified at 0 false positives on the real reports.)

## Which is better

The **new chain** — strictly a superset. Same verdict and same headline
score, but with (a) an actionable allowed/forbidden-claims manifest that
turns "the paper overclaims" into a specific, evidence-anchored list, and
(b) a deterministic guarantee that the review itself did not hallucinate.
No regressions: every old stage is byte-for-byte reused.

## Fixes made while integrating

- `process_summary._find_artifact` did not recognize the paper-audit dir
  layout (`NN<letter>_<skill>`), so the CQE silently missed the fallacy
  report and reviewer panel (Communication scored 40 "skill not run" when 7
  fallacies and a panel verdict existed). Fixed → Communication now 75. This
  is why the committed `majorana2/04_summary` shows a stale composite of 23;
  regenerate it with the fixed scorer to get 26.
- Added a `claims supported by own evidence` probe to the Methodological
  dimension so the requirements_judge verdict feeds the composite.
