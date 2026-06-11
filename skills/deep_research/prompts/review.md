# deep_research — REVIEW mode (research-quality assessment of a paper)

You are assessing the research quality of a paper (NOT acting as a peer-
review panel — that's the quantum_reviewer skill). Score against the
audit-and-falsify checklist that QuantumNovelty's framework enforces.

**Paper or research question to review:** {topic}

{context}

## Required output

### 1. One-paragraph summary of what the paper claims
Be neutral; you will assess separately whether the claim survives.

### 2. Audit-and-falsify checklist
For each item, mark PASS / PARTIAL / FAIL / NOT-APPLICABLE and give one
short sentence of evidence.

- [ ] **Augmented baseline catalog:** Did the paper compare against current
      published methods (not just textbook baselines)?
- [ ] **Strict-domination comparator:** Were Pareto claims made at calibrated
      tolerances (`ε_abs`, `ε_rel`) rather than at displayed-precision?
- [ ] **Recompute-from-raw:** Are displayed ratios consistent with the
      tabulated raw values?
- [ ] **Wilson 95% CIs:** Are small-sample rates (e.g., "5/5 cold starts")
      annotated with binomial CIs?
- [ ] **Cross-LLM falsifiability:** If an LLM-in-the-loop method was used,
      were multiple vendors compared with predictions made before truth?
- [ ] **Honest negatives:** Does the paper include cases where the method
      failed (Failure Modes section), or only successes?
- [ ] **Simulator precision floor:** Are published energy comparisons run
      through a float64 reference path, not just complex64?
- [ ] **Auditable claims:** Is there a re-runnable `audit_claims.py` (or
      equivalent) that derives every numerical claim from on-disk JSON?

### 3. Overall assessment
One paragraph: would this paper survive a strict reviewer-mode audit? Score
1-10 on research rigour. Be candid.

### 4. Three highest-leverage improvements
The specific edits that would turn the paper from its current state into one
the framework would sign off on.

## Constraints
- DO NOT confuse rigorous methodology with conservative results. A paper
  with weak findings rigorously reported scores higher than a paper with
  strong findings carelessly reported.
- DO NOT speculate about authors' intent; assess only the evidence on the
  page.
