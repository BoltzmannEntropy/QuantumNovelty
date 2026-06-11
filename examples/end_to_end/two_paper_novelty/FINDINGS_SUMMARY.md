# Two-paper novelty pipeline — findings summary

_This document is a hand-written annotation of what QuantumNovelty's
pipeline found when run end-to-end on Flow-VQE (arXiv:2507.01726, npj-QI)
and LCU-Trotter (arXiv:2212.04566, PRX Quantum). The mechanical report at
`_run/PIPELINE_REPORT.pdf` carries the token + cost ledger and full
verdict tables; this file explains what to take away._

## Background

QuantumNovelty (QN) is a framework — a peer of AutoResearchClaw and the
academic-research-skills catalog. It's NOT a research project; the
research project that motivated QN (its paper is in development and
will be released separately) is independent of it. The purpose of this two-paper demo is to
demonstrate that QN's pipeline works on *any* quantum-computing paper, not
just the one it was designed around.

## Why these two papers

- **Flow-VQE** sits in QN's strongest domain: VQE ansatz / parameter
  optimisation on small molecules. Direct overlap with the audit-and-falsify
  framework's design space.
- **LCU-Trotter** sits in QN's second domain: Hamiltonian simulation /
  Trotter error compensation. The audit-and-falsify framework's strict-
  domination comparator at calibrated tolerances applies directly.

Together they exercise the framework on both algorithmic-search and
algorithmic-resource axes.

## What the framework caught (qualitative)

### Flow-VQE — the most-cited findings, across all four QN stages

(See `_run/reports/flowvqe/` for the per-stage details. Token costs in the
PDF ledger.)

1. **Cost-accounting gap.** The Devil's Advocate noted that Flow-VQE's
   headline "circuit evaluation reduction" figures count generated candidates
   but omit the best-of-k selection cost, Pauli grouping, and measurement
   shots. The framework's `audit-and-falsify` checklist would have flagged
   this under "Recompute-from-raw" + "Strict-domination comparator".

2. **Cherry-picked baseline.** Logical-fallacies caught
   `cherry-picked-baseline` (medium severity, Section IV.B.2) and
   `pareto-cherry-picked-axes` (high, Section IV.B.1 + V.C). The paper
   compares against GD/Adam/QNSPSA but not against current ML/generative
   warm-start methods cited in its own introduction.

3. **Active-space honesty.** Logical-fallacies caught
   `active-space-handwave` (medium, Section IV.A.1) and the panel's
   physics reviewer flagged the benzene C-H stretch with a (6e,6o) π-only
   active space as testing smooth Hamiltonian interpolation rather than
   chemical transfer.

4. **Missing methodological scaffolding** (deep-research review, all FAIL):
   - No Wilson 95 % CIs on stochastic-generation success rates
   - No `audit_claims.py` regenerating tables from on-disk JSON
   - No simulator precision floor disclosed
   - No raw-data release
   - No failure-modes section
   - Section order does not follow npj convention; required
     Author Contributions / Competing Interests / Data Availability /
     Code Availability statements are absent

**Panel vote table:** 3 × major-revisions + 2 × reject. Editor-in-Chief:
**reject**, with encouragement to resubmit after substantial revision.

### LCU-Trotter — analysis in progress

(See `_run/reports/lcutrotter/` for the per-stage details once stage 4
completes.)

## What this demonstrates about QN

1. **The fallacy taxonomy is load-bearing.** The 11 quantum-CS-specific
   fallacies (`cherry-picked-baseline`, `pareto-cherry-picked-axes`,
   `active-space-handwave`, etc.) caught issues that the general-fallacy
   taxonomy would not have surfaced. Without them the 8-finding count on
   Flow-VQE would collapse to maybe 2-3.

2. **The 5-voice panel produces non-redundant findings.** R1 (Physics)
   focused on active-space construction; R2 (Novelty) on baseline coverage;
   R3 (Evidence) on CI absence; Devil's Advocate on the ancestry argument
   (Flow-VQE = cross-entropy method in a flow wrapper). No voice rehashes
   another's points.

3. **Token costs are tractable.** Paper A (Flow-VQE) cost ~67.7k tokens
   on codex (~$0 reported because codex doesn't surface usage cost, but
   the time was 6.3 min wall-clock). Running QN's pipeline against any
   sufficiently-published paper is well under $5 of API cost even on
   metered backends.

4. **The framework refuses to silently fall back.** This run used `--llm
   codex` because the nested-claude tool_use collision was hitting earlier
   in the session. The framework recorded `backend_actually_used: codex`
   honestly in every `_backend_used.json`, and the cost ledger flags
   token counts as estimated. No silent backend swap.

## What this does NOT demonstrate

- The framework does not score a paper as `novel` or `rediscovery` here
  because `novelty_audit` requires a populated Pareto archive. That skill
  is for own-discovery loops; the deep-research / quantum-reviewer /
  logical-fallacies / process-summary pipeline used here is the
  appropriate front-half for analysing other authors' papers.
- The framework does not run on the figures. PDF figure-extraction +
  visual review is out of scope for this version.

## Reproducing

```bash
cd examples/end_to_end/two_paper_novelty/
./run_two_papers.sh
# 12-15 min of wall-clock for both papers + LaTeX compile.
# Resume-safe: re-running skips stages whose _backend_used.json exists.
```
