# quantum_reviewer — FULL panel (EIC + R1 + R2 + R3 + Devil's Advocate)

You are simulating a complete peer-review panel for a quantum-computing
paper. Output FIVE distinct voices in this exact order, each writing AT
LEAST four substantive paragraphs. Then the Editor-in-Chief synthesises
and a vote table closes.

**Draft:**

```
{draft}
```

{context}

## Required output (exact structure)

---

## Voice 1 — Reviewer 1 (Physics correctness)

Focus: Hamiltonian construction; active-space choice; unit consistency;
simulator precision (complex64 vs float64); fermion-to-qubit mappings
(JW vs BK vs parity); Hartree-Fock reference; chemistry-specific approximations.
At least 4 paragraphs. End with a per-reviewer verdict on a 1-10 scale and a
recommendation in {{accept, minor-revisions, major-revisions, reject}}.

## Voice 2 — Reviewer 2 (Algorithmic novelty)

Focus: novelty against current published baselines (pull literature from the
last 24 months for the topic and name 2-3 specific papers); whether the
strict-domination comparator at calibrated tolerances would actually flag
this as a Pareto win; whether claimed ratios are recomputable from raw
values. At least 4 paragraphs. End with verdict + recommendation.

## Voice 3 — Reviewer 3 (Empirical evidence)

Focus: statistical CIs on small-sample claims (Wilson 95% on K/N rates);
multi-seed variance reporting; ablation completeness (LLM-mutator on/off,
commutation-hint on/off, Pareto-seeding on/off); honest-negatives /
Failure-Modes section presence; whether an `audit_claims.py` (or equivalent)
re-derives every numerical claim from on-disk JSON. At least 4 paragraphs.
End with verdict + recommendation.

## Voice 4 — Devil's Advocate

Write the STRONGEST POSSIBLE rejection of this paper. Find every weakness
the other three reviewers were too generous about. Be specific, technical,
and uncharitable. At least 4 paragraphs. End with a recommendation
(usually `reject`, but defensible if the strongest case is `major-revisions`).

## Voice 5 — Editor-in-Chief synthesis

Read all four reviews above. Address the Devil's Advocate's specific
critiques. Reconcile R1/R2/R3 disagreement if any. Produce a final verdict
keyed to the target journal's standards: accept / minor-revisions /
major-revisions / reject. At least 4 paragraphs. End with a numbered list
of "must-fix before resubmission" items, ordered by severity.

## Vote table

| Voice | Recommendation | Confidence 1-10 |
|---|---|---|
| Reviewer 1 | ... | ... |
| Reviewer 2 | ... | ... |
| Reviewer 3 | ... | ... |
| Devil's Advocate | ... | ... |
| Editor-in-Chief | ... | ... |

## Constraints
- Each voice MUST appear with the exact heading shown above
  (the chain validates voice presence post-hoc).
- Voices must DISAGREE with each other where the paper has weaknesses;
  artificial consensus is a failure mode.
- The Devil's Advocate MUST find something the other three missed.
- Use the audit-and-falsify checklist as the methodological standard.
- Each of R1/R2/R3 must end with a short **Questions for Authors**
  list (2-4 questions a real reviewer would need answered before
  changing their verdict).
- WRITE LIKE A HUMAN REFEREE, not a slide deck: flowing paragraphs of
  argued prose. No bullet lists, no bold-label fragments, no nested
  headings inside a voice, no markdown tables (the Vote table at the
  end is the single exception). Strengths and weaknesses are woven
  into the argument, not enumerated. Cite sections/equations/figures
  inline the way a referee report does.
