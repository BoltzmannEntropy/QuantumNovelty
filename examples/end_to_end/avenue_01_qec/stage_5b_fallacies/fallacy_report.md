# Logical Fallacy Audit Report

## Section 1: Markdown Findings

---

**Fallacy:** cherry-picked-baseline

**Severity:** high

**Location:** Section V (Results), Table 1 and surrounding text; Section VI.B (Comparison with Prior Work)

**Evidence:** "The standard block ordering with $X$-type stabilizers measured first achieves a threshold of $p_{\text{th}} = \langle\text{INSERT MEASURED VALUE}\rangle$\%, consistent with previously reported values for the rotated planar code under this noise model"

**Why it's the fallacy:** The paper compares its optimized measurement ordering exclusively against the "standard alternating X-Z measurement ordering" (block ordering) without benchmarking against other published measurement scheduling optimizations. The Discussion section acknowledges related work by Chamberland & Beverland on flag qubits and Gidney on detector error models, but dismisses them as "not specifically optimiz[ing] measurement orderings" rather than demonstrating superiority over any alternative scheduling approaches that may exist in the literature. The baseline is chosen to be the naive standard ordering, not the strongest known competing method for syndrome extraction optimization.

**Suggested fix:** Add a comprehensive literature search for prior measurement scheduling optimizations. If such methods exist, include them as baselines in Table 1. If none exist, explicitly state: "To our knowledge, no prior work has systematically optimized measurement-cycle ordering for threshold improvement; we therefore benchmark against the standard block ordering used in all prior experimental and theoretical studies."

---

**Fallacy:** conflated-regimes

**Severity:** high

**Location:** Section V.C (Scaling with Code Distance), and Section VI (Discussion)

**Evidence:** "The ratio of effective distances for the optimized versus standard ordering is approximately constant at $\langle\text{INSERT MEASURED VALUE}\rangle$ across all code distances studied, indicating that the threshold improvement does not diminish at larger scales."

**Why it's the fallacy:** The simulations cover only code distances d ∈ {3, 5, 7, 9, 11}, which are small-scale systems. The claim that "threshold improvement does not diminish at larger scales" extrapolates from this finite-N demonstration to an implicit asymptotic regime. Distance-11 codes have only 121 data qubits—far from the thousands required for practical fault-tolerant computation. The phrase "larger scales" is ambiguous and could mislead readers into believing the results extend to arbitrarily large systems without additional validation.

**Suggested fix:** Replace the quoted sentence with: "The ratio of effective distances for the optimized versus standard ordering is approximately constant at $\langle\text{INSERT MEASURED VALUE}\rangle$ across the code distances $d \leq 11$ studied here. Extrapolation to larger distances (d > 20) requires further numerical verification, as finite-size effects may emerge at scales not captured by our simulations."

---

**Fallacy:** asymptotic-only-claim

**Severity:** medium

**Location:** Abstract and Conclusion

**Evidence (Abstract):** "Our results establish measurement-cycle optimization as a practical, hardware-agnostic technique for enhancing the performance of near-term quantum error correction experiments."

**Evidence (Conclusion):** "Measurement-cycle optimization is a 'free' improvement in the sense that it requires no additional physical resources, only a reordering of existing operations."

**Why it's the fallacy:** The claim of being "hardware-agnostic" and applicable to "near-term quantum error correction experiments" is made based solely on idealized circuit-level depolarizing noise simulations. No hardware noise calibration, crosstalk modeling, or leakage effects are included. Section VI.C acknowledges this limitation ("Our analysis assumes that idle error rates are comparable to gate error rates; systems with much shorter coherence times may not benefit from reordering") but the Abstract and Conclusion assert generality without this caveat.

**Suggested fix:** Modify the Abstract to: "Our results suggest measurement-cycle optimization as a potentially practical technique for enhancing surface code performance, subject to validation under device-specific noise models." Add to the Conclusion: "The 'hardware-agnostic' nature of this improvement is contingent on the assumption that idle errors do not dominate; experimental validation is required."

---

**Fallacy:** hardware-irrelevant-comparison

**Severity:** medium

**Location:** Section VI.C (Hardware Considerations)

**Evidence:** "The measurement orderings studied here can be implemented on existing superconducting qubit hardware with no physical modifications... We estimate the circuit depth increases by approximately $\langle\text{INSERT MEASURED VALUE}\rangle$\% relative to the maximally parallel block ordering."

**Why it's the fallacy:** The paper claims hardware implementability while using only simulator results under idealized depolarizing noise. Real superconducting hardware exhibits crosstalk, frequency collisions, leakage to non-computational states, and measurement-induced dephasing—none of which are modeled. The paper does not provide noise calibration data or demonstrate that the wavefront ordering remains beneficial under realistic noise profiles. Claiming the technique works "on existing superconducting qubit hardware" based purely on simulator data is a hardware-irrelevant comparison.

**Suggested fix:** Revise to: "The measurement orderings studied here are compatible with the control constraints of existing superconducting qubit hardware. However, our simulations use idealized depolarizing noise and do not account for device-specific effects such as crosstalk, leakage, or measurement-induced dephasing. Experimental validation is necessary to confirm threshold improvements persist under realistic noise conditions."

---

**Fallacy:** ad-hoc-precision-floor

**Severity:** medium

**Location:** Section V.B (Sub-Threshold Logical Error Rates)

**Evidence:** "At $p = \langle\text{INSERT MEASURED VALUE}\rangle$\%, the optimized ordering reduces the logical error rate by a factor of $\langle\text{INSERT MEASURED VALUE}\rangle$ relative to standard ordering at distance $d = 11$."

**Why it's the fallacy:** While the actual numerical values are placeholders, the structure of the claim implies reporting improvement factors without establishing the noise floor of the Monte Carlo sampling. The paper mentions "bootstrap resampling with $N_{\text{bootstrap}} = 1000$ resamples" for uncertainty quantification but does not specify $N_{\text{samples}}$ or demonstrate that the reported improvement factors exceed statistical uncertainty. For low logical error rates at small distances, Monte Carlo noise can dominate, and quoting improvement factors without explicit error bars risks reporting precision below the noise floor.

**Suggested fix:** Add explicit error bars on all improvement factor claims: "At $p = X\%$, the optimized ordering reduces the logical error rate by a factor of $Y \pm Z$ (1σ) relative to standard ordering." Also specify $N_{\text{samples}}$ and demonstrate that $Y - 1 > 2Z$ (i.e., improvement exceeds 2σ noise).

---

**Fallacy:** active-space-handwave

**Severity:** medium

**Location:** Section VI.E (Extensions and Generalizations)

**Evidence:** "The optimization framework developed here extends naturally to several related settings: (i) Other surface code layouts: The unrotated surface code and the XZZX code have different stabilizer geometries but similar temporal degrees of freedom. Preliminary analysis suggests comparable threshold improvements are achievable."

**Why it's the fallacy:** The paper claims generalization to other code layouts (unrotated surface code, XZZX code) without providing any numerical results for these variants. "Preliminary analysis suggests" is vague—no data, figures, or threshold estimates are provided. This is a handwave claim of generalization without demonstration.

**Suggested fix:** Either (a) remove the claim about other layouts, (b) add explicit results for at least one additional layout (XZZX code) with threshold estimates, or (c) revise to: "We conjecture that the optimization framework may extend to other layouts such as the XZZX code, but this remains to be demonstrated numerically."

---

**Fallacy:** hasty-generalization

**Severity:** medium

**Location:** Section IV (Methods), Subsection IV.B (Detector Graph Weighting)

**Evidence:** "To improve the threshold, we seek measurement orderings that: (i) Reduce the weight of high-probability error mechanisms (lower edge weights in G). (ii) Increase the minimum-weight path between boundary nodes..."

**Why it's the fallacy:** The paper assumes that the three scoring criteria in Equation (4) serve as reliable proxies for threshold performance, with hyperparameters "tuned empirically" (α=1, β=-0.5, γ=0.3). However, the relationship between these proxy metrics and actual threshold is not formally established. The paper provides no validation that optimizing the score function in Eq. (4) correlates with threshold improvement across orderings—it simply selects orderings that score well and then measures their thresholds. This is a hasty generalization from the scoring function to threshold performance without establishing causal or correlative validity.

**Suggested fix:** Add a validation analysis: "Figure X shows the correlation between the score $S(\pi)$ and the measured threshold $p_{\text{th}}(\pi)$ across all evaluated orderings. The Spearman correlation coefficient is $\rho = Y$ (p < Z), validating that our scoring function serves as a reasonable proxy for threshold performance."

---

## Section 2: Machine-Readable JSON

```json
{
  "findings": [
    {
      "name": "cherry-picked-baseline",
      "category": "quantum-cs",
      "severity": "high",
      "location": "Section V (Results), Table 1; Section VI.B (Comparison with Prior Work)",
      "evidence": "The standard block ordering with $X$-type stabilizers measured first achieves a threshold of $p_{\\text{th}} = \\langle\\text{INSERT MEASURED VALUE}\\rangle$\\%, consistent with previously reported values for the rotated planar code under this noise model",
      "suggested_fix": "Add comprehensive literature search for prior measurement scheduling optimizations and include them as baselines; if none exist, explicitly state this with justification for using standard block ordering as baseline"
    },
    {
      "name": "conflated-regimes",
      "category": "quantum-cs",
      "severity": "high",
      "location": "Section V.C (Scaling with Code Distance)",
      "evidence": "The ratio of effective distances for the optimized versus standard ordering is approximately constant at $\\langle\\text{INSERT MEASURED VALUE}\\rangle$ across all code distances studied, indicating that the threshold improvement does not diminish at larger scales.",
      "suggested_fix": "Replace 'larger scales' claim with explicit statement that results are verified only for d ≤ 11 and extrapolation to d > 20 requires further validation"
    },
    {
      "name": "asymptotic-only-claim",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Abstract and Conclusion",
      "evidence": "Our results establish measurement-cycle optimization as a practical, hardware-agnostic technique for enhancing the performance of near-term quantum error correction experiments.",
      "suggested_fix": "Qualify 'hardware-agnostic' claim with acknowledgment that validation under device-specific noise models is required; add caveat about idealized noise model assumptions"
    },
    {
      "name": "hardware-irrelevant-comparison",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section VI.C (Hardware Considerations)",
      "evidence": "The measurement orderings studied here can be implemented on existing superconducting qubit hardware with no physical modifications... We estimate the circuit depth increases by approximately $\\langle\\text{INSERT MEASURED VALUE}\\rangle$\\% relative to the maximally parallel block ordering.",
      "suggested_fix": "Add explicit statement that simulations use idealized depolarizing noise without crosstalk, leakage, or measurement-induced dephasing; note that experimental validation is necessary"
    },
    {
      "name": "ad-hoc-precision-floor",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section V.B (Sub-Threshold Logical Error Rates)",
      "evidence": "At $p = \\langle\\text{INSERT MEASURED VALUE}\\rangle$\\%, the optimized ordering reduces the logical error rate by a factor of $\\langle\\text{INSERT MEASURED VALUE}\\rangle$ relative to standard ordering at distance $d = 11$.",
      "suggested_fix": "Include explicit error bars on improvement factors; specify N_samples; demonstrate that improvement exceeds 2σ statistical uncertainty"
    },
    {
      "name": "active-space-handwave",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section VI.E (Extensions and Generalizations)",
      "evidence": "The optimization framework developed here extends naturally to several related settings: (i) Other surface code layouts: The unrotated surface code and the XZZX code have different stabilizer geometries but similar temporal degrees of freedom. Preliminary analysis suggests comparable threshold improvements are achievable.",
      "suggested_fix": "Either provide numerical results for at least one additional code layout or remove/qualify the generalization claim with explicit acknowledgment that it remains undemonstrated"
    },
    {
      "name": "hasty-generalization",
      "category": "general",
      "severity": "medium",
      "location": "Section IV.B (Detector Graph Weighting), Equation 4",
      "evidence": "The hyperparameters α, β, γ are tuned empirically; we find α = 1, β = -0.5, γ = 0.3 provides a good proxy for threshold performance.",
      "suggested_fix": "Add validation analysis showing correlation between score S(π) and measured threshold p_th(π) across all evaluated orderings with statistical significance test"
    }
  ]
}
```