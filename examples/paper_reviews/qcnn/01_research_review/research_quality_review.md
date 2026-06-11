## 1. One-paragraph summary of what the paper claims

The paper argues that Quantum Convolutional Neural Networks (QCNNs)—both tracing-out and measurement-based variants—are effectively classically simulable in a practical sense. The authors contend that randomly initialized QCNNs can only extract and process information encoded in low-bodyness (low-weight) Pauli observables of their input states, and that the benchmark datasets used in the literature to demonstrate QCNN success are "locally-easy," meaning they can be classified using only this low-bodyness information. Based on these insights, the authors construct purely classical surrogates using Pauli propagation methods (LOWESA), tensor networks, and classical shadows that match or outperform standard QCNNs on all tested benchmark datasets at scales up to 1024 qubits. They conclude that there is currently no evidence QCNNs will work on classically non-trivial tasks, and challenge the community to identify datasets where QCNNs provide genuine quantum advantage.

---

## 2. Audit-and-falsify checklist

| Item | Status | Evidence |
|------|--------|----------|
| **Augmented baseline catalog** | PARTIAL | The paper compares against "full QCNNs" trained without finite sampling and references prior literature results (e.g., Table I cites accuracies from Refs. [51–69]), but does not systematically benchmark against other recent classical ML baselines (random forests, CNNs, kernel methods) on the same datasets beyond the single random-forest demonstration in Appendix D. |
| **Strict-domination comparator** | FAIL | Claims of "matching or outperforming" are made at displayed precision (e.g., "98% vs. 98%") without specifying tolerance thresholds (ε_abs, ε_rel); no formal Pareto analysis with calibrated tolerances is provided. |
| **Recompute-from-raw** | PARTIAL | Table I displays test accuracies directly, but no raw confusion matrices, per-run values, or derivation scripts are presented; readers cannot independently verify that "best out of 5" selections are consistent with underlying distributions. |
| **Wilson 95% CIs** | FAIL | Small-sample classification results (e.g., 5 independent runs, 100 test points) are reported without binomial confidence intervals; statements like "100/98" accuracy lack uncertainty quantification. |
| **Cross-LLM falsifiability** | NOT-APPLICABLE | No LLM-in-the-loop method is employed in this work. |
| **Honest negatives** | PARTIAL | The authors acknowledge that their results do not constitute full dequantization and note caveats (e.g., 2D QCNNs may be harder to simulate, misclassifications near phase boundaries), but there is no dedicated "Failure Modes" section cataloging cases where the classical surrogate underperformed or failed to converge. |
| **Simulator precision floor** | FAIL | No discussion of numerical precision (float32 vs. float64) in energy or expectation-value comparisons; the DMRG states and shadow tomography reconstructions are not validated against a float64 reference path. |
| **Auditable claims** | FAIL | No `audit_claims.py` or equivalent re-runnable script is referenced; data files (JSON, HDF5) and code are not explicitly linked or described as available for reproducing every numerical claim from raw artifacts. |

---

## 3. Overall assessment

This paper presents a conceptually significant and technically sophisticated argument that QCNNs' heuristic success may be attributable to classically simulable dynamics on locally-easy datasets. The theoretical underpinnings (Result 1, Result 2, Theorem 1) are carefully developed using Weingarten calculus, and the empirical demonstrations span multiple quantum and classical datasets at impressive scales. However, the paper falls short of the research rigor expected by a strict audit framework: quantitative claims lack uncertainty estimates, baseline comparisons are incomplete, numerical precision is unaddressed, and reproducibility infrastructure (auditable scripts, raw data archives) is absent. The "best of 5" reporting and absence of confidence intervals on small-sample accuracies weaken the statistical credibility of the comparative claims. While the core thesis is compelling and the simulations are impressive, the evidentiary standards do not meet those required for a fully auditable, falsifiable research contribution.

**Rigour score: 5/10**

---

## 4. Three highest-leverage improvements

1. **Add Wilson 95% confidence intervals to all reported accuracies.** For every entry in Table I and Figures 3–6, compute and display binomial CIs given the test-set size. Replace statements like "98%" with "98% [92.9–99.8%, Wilson 95% CI, n=100]." This single change would substantially increase statistical credibility.

2. **Provide an `audit_claims.py` script with on-disk JSON artifacts.** Archive all raw experimental outputs (per-run accuracies, shadow samples, trained parameters) in a public repository, and include a single script that re-derives every numerical claim (table entries, figure data points, ratios) from these artifacts. This converts the paper from "trust-based" to "verify-based" reproducibility.

3. **Establish a float64 reference path for simulator precision.** Re-run at least one representative quantum-dataset experiment (e.g., the 1024-qubit XXX model) with float64 throughout the DMRG, shadow tomography, and LOWESA pipelines; compare against the default (likely float32/complex64) results and report the deviation. If deviations are negligible, state this explicitly; if not, adjust conclusions accordingly.