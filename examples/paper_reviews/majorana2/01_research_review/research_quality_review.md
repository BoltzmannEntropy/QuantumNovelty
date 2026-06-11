## 1. One-paragraph summary of what the paper claims

This paper from Microsoft Quantum reports a major advance in topological quantum computing by demonstrating a characteristic parity lifetime of approximately 20 seconds in an InAs-Pb tetron device, representing an improvement of more than three orders of magnitude over previous Al-based devices (which achieved 1–12 ms). The authors attribute this improvement to replacing aluminum with the higher-gap superconductor lead (Pb) in their superconductor-semiconductor hybrid platform, which yields a larger topological gap (∆T ≈ 70 µeV vs. ~30 µeV in Al devices) and a proximity-induced gap of ~570 µeV. They introduce an rf-based wire spectroscopy technique for scalable device bring-up that can resolve Majorana hybridization energies (EM) with µeV precision, and demonstrate h/2e-periodic bimodal quantum capacitance shifts consistent with parity-dependent interference. The paper argues this validates a central premise of topological quantum computing: that increasing the excitation gap dramatically reduces error mechanisms and improves qubit performance.

---

## 2. Audit-and-falsify checklist

| Item | Status | Evidence |
|------|--------|----------|
| **Augmented baseline catalog** | **PASS** | The paper explicitly compares against their own prior Al-InAs devices (Refs. 59–61) with quantitative improvements cited: parity lifetime improvement from 1–12 ms to ~20 s; topological gap from ~30 µeV to ~70 µeV; topological phase region more than doubled; this represents comparison against current state-of-the-art from the same research group. |
| **Strict-domination comparator** | **PARTIAL** | The paper reports "more than three orders of magnitude" improvement in parity lifetime and provides specific values (22 ± 1 s fit), but comparisons like "top quintile gap" thresholds and localization length claims lack explicit tolerance specifications (ε_abs, ε_rel). |
| **Recompute-from-raw** | **PARTIAL** | The paper presents raw data in figures (e.g., time traces in Fig. 6, phase diagrams in Fig. 3) and reports derived values (τZ = 22 ± 1 s from N = 324 dwell intervals), but there is no explicit statement that readers can access raw data or re-derive the numerical claims independently. |
| **Wilson 95% CIs** | **PARTIAL** | The parity lifetime τZ = 22 ± 1 s includes uncertainty from exponential fitting, but the paper does not explicitly provide binomial/Wilson confidence intervals for small-sample statistics; the N = 324 events is reasonably large but the methodology for uncertainty propagation is not fully detailed. |
| **Cross-LLM falsifiability** | **NOT-APPLICABLE** | No LLM-in-the-loop methods were used in this experimental physics paper. |
| **Honest negatives** | **PARTIAL** | The paper acknowledges that "external quasiparticle poisoning events" cause sign switches in their data (Sec. 3–4), and discusses that non-equilibrium quasiparticles can degrade protection, but there is no dedicated "Failure Modes" section systematically cataloging regimes where the device underperforms or the method fails. |
| **Simulator precision floor** | **PARTIAL** | The paper mentions simulations for induced gap values ("consistent with simulations") and uses numerical modeling, but does not explicitly state whether float64 reference paths were used or address numerical precision floors in their calculations. |
| **Auditable claims** | **FAIL** | There is no mention of a re-runnable script (e.g., `audit_claims.py`), on-disk JSON, or any reproducibility infrastructure that would allow independent derivation of numerical claims from raw data. |

---

## 3. Overall assessment

This paper represents solid experimental physics work with clear advances over prior results from the same group. The claims are well-grounded in extensive measurements, the methodology (rf-based spectroscopy, parity injection) is clearly described, and the results are internally consistent. However, from a strict research-rigour audit perspective, the paper falls short in several areas: (1) no publicly accessible raw data or reproducibility infrastructure; (2) uncertainty quantification is present but not comprehensively specified (e.g., explicit confidence interval methodology for the 324-event parity lifetime analysis); (3) baseline comparisons, while appropriate, rely heavily on self-citation without independent verification of the comparison metrics; (4) absence of a systematic failure-modes discussion. The paper would benefit from explicit tolerance specifications in performance claims and a data-availability statement with recomputation scripts. 

**Research rigour score: 6.5/10** — The experimental methodology and results are credible and represent genuine advances, but the paper lacks the reproducibility infrastructure and explicit uncertainty quantification that strict audit standards require.

---

## 4. Three highest-leverage improvements

1. **Add data availability and reproducibility infrastructure**: Include a supplementary package with raw measurement data (time traces, conductance sweeps, TGP outputs) in a standard format (HDF5/JSON) and a script that derives every numerical claim (τZ, ∆T, EM bounds, periodicity estimates) from this data. This would transform the "Auditable claims" item from FAIL to PASS.

2. **Provide explicit uncertainty methodology and confidence intervals**: For the key τZ = 22 ± 1 s result, specify the statistical framework (maximum likelihood estimation on exponential distribution? Bayesian posterior?), report the 95% CI explicitly, and address potential systematic uncertainties (threshold selection sensitivity, drift during long traces). For the EM < 1 µeV claim, quantify the confidence level and detector resolution floor more precisely.

3. **Include a dedicated "Limitations and Failure Modes" section**: Systematically document parameter regimes where the device does not achieve the reported performance (e.g., regions outside the identified cluster in Fig. 5, conditions under which poisoning rates increase, sensitivity to magnetic field misalignment), and discuss any instances where the rf spectroscopy method failed to identify low-energy states. This honest reporting would significantly strengthen the paper's credibility for rigorous reviewers.