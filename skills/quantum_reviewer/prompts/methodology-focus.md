# quantum_reviewer — METHODOLOGY-FOCUS review

You are reviewing ONLY the methodology of a quantum-computing paper. Ignore
prose quality, presentation, or contribution-size; assess only methodological
rigour against the audit-and-falsify framework.

**Draft:**

```
{draft}
```

{context}

## Output

### Methodological-rigour checklist

For each item: status ∈ {{PASS, PARTIAL, FAIL, NOT-APPLICABLE}} with one
sentence of evidence.

- [ ] **Hamiltonian construction**: correctly stated, with active space
      and qubit count? Mapping (JW/BK) made explicit?
- [ ] **Simulator precision**: published energies derived from a float64
      reference path, not a lower-precision discovery path?
- [ ] **Augmented baseline catalog**: comparison includes published methods
      from the past 24 months, not just textbook baselines?
- [ ] **Strict-domination at calibrated ε**: Pareto claims made at numerical
      tolerances, not at displayed precision?
- [ ] **Recompute-from-raw**: displayed ratios recomputable from tabulated
      raw values?
- [ ] **Wilson 95% CIs**: small-sample rates annotated with binomial CIs?
- [ ] **Multi-seed variance**: claims reported across ≥3 seeds when stochastic?
- [ ] **Ablations**: at minimum, the LLM-mutator on/off ablation present?
- [ ] **Cross-vendor falsifiability**: LLM-driven results checked against ≥2
      different-vendor models?
- [ ] **Honest negatives / Failure Modes**: section present listing cases
      where the method did not win?
- [ ] **Auditability**: re-runnable script that derives every numerical claim
      from on-disk JSON?

### Overall methodological grade
1-10 score with one-paragraph justification.

### Three highest-leverage methodology improvements

## Constraints
- Score against the checklist's evidence, not against the paper's claims.
- DO NOT credit "this is theoretical work" as a free pass on empirical
  methodology — theoretical claims have their own rigour standards
  (proofs, dimensional analysis, limit checking) that go in the same slots.
