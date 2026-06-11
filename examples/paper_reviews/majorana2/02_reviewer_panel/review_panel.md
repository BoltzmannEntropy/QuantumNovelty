## Voice 1 — Reviewer 1 (Physics correctness)

This manuscript reports on an InAs–Pb hybrid device demonstrating parity lifetimes of approximately 20 seconds, which would represent a substantial improvement over the approximately 1–12 millisecond lifetimes observed in prior aluminum-based tetron devices. The physical premise is straightforward and well-motivated: replacing aluminum (Δ ≈ 300 µeV) with lead (Δ ≈ 1.3 meV) should increase both the parent superconducting gap and, consequently, the topological gap, thereby suppressing both thermal excitations and quasiparticle poisoning. The authors claim to have achieved top-quintile topological gaps of ΔT ≈ 70 µeV, compared to ΔT ≈ 30 µeV in earlier Al-based devices. The basic physics underlying these claims is sound: the exponential dependence of Majorana hybridization on L/ξT, where ξT scales inversely with the gap in clean systems, combined with stronger electron-phonon coupling in Pb facilitating faster quasiparticle recombination, provides a coherent theoretical framework for the observed improvements.

The Hamiltonian introduced in Equation 1 describes a minimal model coupling a single low-energy wire state to a readout quantum dot. While this model is adequate for qualitative understanding, I have concerns about its application to the quantitative extraction of EM. The authors state that EM is extracted with "µeV precision," yet the model assumes a single isolated wire state. In the topological regime, this assumption is appropriate since γ1 and γ2 represent well-separated Majorana zero modes with exponentially small overlap. However, near phase boundaries or in the presence of disorder, multiple low-energy states (quasi-Majoranas) can contribute. The authors acknowledge this possibility by referencing prior work on quasi-MZMs (Ref. 61, 84), but do not explicitly demonstrate that their measurements exclude such scenarios. The claim that EM < 1 µeV throughout the identified topological region would be substantially strengthened by showing the parity-independence of peak width and amplitude predicted by Equation 2 in the deep topological limit where t̃R → 0.

The induced gap measurements deserve careful scrutiny. The authors report Δind ≈ 570 µeV in the lowest subband regime at zero field for the nanowire geometry, which they claim is consistent with simulations accounting for transverse confinement. However, the proximity-induced gap measured in the 2D geometry (Fig. 2b) is 400 µeV. While transverse confinement can indeed enhance the induced gap, the 42% increase from 400 to 570 µeV seems substantial and warrants explicit presentation of the simulation methodology. Additionally, the relationship between the parent Pb gap (ΔPb ≈ 1.3 meV) and the induced gap is governed by interface transparency and the relative density of states in superconductor and semiconductor. The 10 nm Pb film thickness is specified, but the interface characterization that would support claims of "hard" induced gap (absence of subgap states) relies on a citation to prior Coulomb island work (Ref. 53) rather than direct measurement in the present device geometry.

The spin-orbit coupling value α ∼ 12–16 meV nm is extracted from Shubnikov-de Haas oscillations in Pb-proximitized nanowires according to Fig. 2c. The extraction procedure references Ref. 78, but the actual data shown appears to come from van der Pauw devices with fixed density. The authors acknowledge in their footnote (Ref. 77) that this value combines 2D measurements under Pb with weak anti-localization measurements in Hall bars without Pb. This indirect approach introduces systematic uncertainty that is not propagated into the claimed precision. Given that the topological phase boundary depends sensitively on the ratio of spin-orbit energy to Zeeman energy, more direct characterization of α in the actual device geometry would strengthen the conclusions about phase diagram extent.

**Questions for Authors:**

1. Can you provide explicit numerical simulations demonstrating the 42% enhancement of induced gap from transverse confinement, including the specific model assumptions about interface transparency?

2. In the topological region identified in Fig. 5, do the quantum capacitance peaks exhibit parity-independent width and amplitude as predicted by Equation 2 when t̃R → 0, and if so, can you quantify the upper bound on t̃R/tR?

3. What is the estimated systematic uncertainty in the spin-orbit coupling arising from the indirect measurement approach combining van der Pauw and Hall bar data?

**Verdict: 7/10 — minor-revisions**

---

## Voice 2 — Reviewer 2 (Algorithmic novelty)

The central novelty claim of this work is the demonstration that increasing the superconducting gap translates directly into improved topological qubit performance, specifically through the replacement of aluminum with lead in superconductor-semiconductor hybrid devices. While this is indeed a longstanding prediction of topological quantum computing theory, the question of algorithmic or methodological novelty requires careful examination. The rf-based wire spectroscopy technique presented in Section 3 represents a genuine methodological advance over prior DC transport-based tuning protocols, enabling parallel characterization compatible with scalable architectures. This addresses a practical bottleneck identified in earlier work and represents the most novel technical contribution of the manuscript.

Comparing against recent literature, the Microsoft Quantum group's own prior work on InAs-Al hybrid devices passing the topological gap protocol (Ref. 60, Phys. Rev. B 2023) and interferometric single-shot parity measurements (Ref. 61, Nature 2025) establishes the immediate baseline. The present work demonstrates a three-order-of-magnitude improvement in parity lifetime (∼20 s versus ∼1–12 ms), which is substantial. However, the Kanne et al. Nature Nanotechnology 2021 work (Ref. 53) already demonstrated epitaxial Pb on InAs nanowires with 2e-periodic charging patterns consistent with hard induced gap. The key advance here is not the material system per se but the integration into a multi-tetron array geometry with demonstrable parity protection. Recent work by Song et al. (Nano Lett. 2025, Ref. 55) and Zhang et al. (Nano Lett. 2026, Ref. 56) on PbTe nanowires represents related but distinct materials approaches that do not yet demonstrate comparable parity lifetimes in qubit-relevant geometries.

The claimed parity lifetime of τZ = 22 ± 1 s extracted from exponential fits to dwell time distributions (Fig. 6e) with N = 324 events raises questions about statistical power for distinguishing between competing decay models. The authors assume a homogeneous Poisson process, but non-exponential distributions could arise from time-varying quasiparticle densities or multiple competing poisoning mechanisms with different rates. With only 324 events aggregated across multiple measurements, distinguishing exponential from, say, stretched exponential or power-law tails would require careful model comparison that is not presented. The claim that "some instances reaching minute-scale" in the abstract is particularly concerning—this suggests significant variability that should be characterized systematically rather than highlighted anecdotally.

The comparison framework for establishing Pareto dominance over prior devices is implicitly presented but not rigorously constructed. The key performance metrics appear to be ΔT (topological gap), EM (Majorana splitting), and τZ (parity lifetime). For a Pareto improvement, the InAs-Pb devices should dominate on at least one metric without regression on others. The claimed improvements are ΔT: 70 µeV versus 30 µeV (2.3× improvement), EM: < 1 µeV (comparable or better), τZ: ∼20 s versus ∼1–12 ms (>1000× improvement). However, the authors do not present direct measurements of τX (X-parity lifetime) for the Pb-based devices, instead stating that "investigating these effects will be an important direction for future work." This is a significant gap since τX scales as EM², and improved τZ without corresponding improvement in τX would not constitute strict Pareto dominance for all qubit operations.

**Questions for Authors:**

1. Have you performed formal model selection (e.g., Akaike information criterion) comparing exponential versus non-exponential dwell time distributions for the parity switching data?

2. Can you provide even preliminary τX measurements for the Pb-based devices to establish whether the claimed improvements extend to X-parity operations?

3. How do the fabrication yield and reproducibility of the InAs-Pb devices compare to the Al-based baseline, given that scalability is a central motivation?

**Verdict: 6/10 — major-revisions**

---

## Voice 3 — Reviewer 3 (Empirical evidence)

The statistical treatment of the parity lifetime measurement (Fig. 6) requires more rigorous analysis than currently presented. The authors report τZ = 22 ± 1 s based on exponential fitting of N = 324 dwell intervals aggregated across multiple measurements. The quoted uncertainty of ±1 s appears to represent only the fit uncertainty, not the full sampling variability. For a Poisson process with true rate λ, the maximum likelihood estimator of the mean dwell time has standard error τ/√N ≈ 22/√324 ≈ 1.2 s, which is consistent with the reported uncertainty. However, the aggregation across "multiple measurements" (stated as 9 additional time traces beyond the example in Fig. 6d) and across a range of Vwp = −1.365 13 V ± 10 µV introduces systematic variability that should be characterized. If the true parity lifetime varies with gate voltage even within this 20 µV range, the aggregated distribution would exhibit over-dispersion relative to a homogeneous Poisson model.

The claim of "some instances reaching minute-scale" lifetime requires quantification. Examining Fig. 6e, the histogram extends to approximately 140 s with visible counts in the 100–140 s bins. However, for τ = 22 s, the probability of observing a dwell time exceeding 100 s is exp(−100/22) ≈ 1%, predicting approximately 3 events in a sample of 324. The apparent presence of multiple events at 100+ s could indicate either a heavy tail inconsistent with exponential distribution or simply sampling variability. A quantile-quantile plot against the exponential distribution would clarify whether the tail behavior is anomalous.

The rf-based wire spectroscopy protocol (Section 3, Figs. 4–5) represents a systematic approach to identifying low-energy wire states, but the thresholding procedure introduces subjective elements that should be characterized through sensitivity analysis. The signal-to-noise threshold S/σ > 2.5 and the requirement that at least 7/10 wire cutter configurations show above-threshold signal are reasonable but arbitrary. The authors acknowledge that "the exact boundary of the identified region is in general sensitive to the details of the thresholds used," but do not quantify this sensitivity. Varying these thresholds and reporting the resulting changes in the identified topological region would strengthen confidence that the conclusions are robust.

The manuscript lacks a systematic failure-modes section discussing devices or measurements that did not work as expected. While Section 3 mentions that "additional sign switches are interpreted to be the result of external quasiparticle poisoning events," this is the only acknowledgment of imperfect behavior. Questions arise naturally: What fraction of devices in the multi-tetron array achieved the reported performance? Were there systematic differences between the four tetrons (AA, AB, BA, BB) in the unit cell? Did all nanowires in the device exhibit comparably low EM, or is the top wire of the BA tetron a particularly favorable case? The reproducibility claims implicit in the scalability discussion would be better supported by explicit characterization of device-to-device and wire-to-wire variability within the array.

The data provenance and reproducibility infrastructure are not described. While the authors reference specific gate voltages (e.g., Vwp = −1.365 13 V) and magnetic fields (e.g., B = 3.8 T, Bz in Fig. 5), there is no mention of data availability statements, analysis code, or raw data repositories. For a result with significant implications for quantum computing scalability, the ability to independently verify numerical claims from archived data and analysis scripts would substantially enhance credibility. Even if full data release is not feasible for proprietary reasons, describing the audit trail from raw measurements to reported numbers would address concerns about replicability.

**Questions for Authors:**

1. Can you provide a quantile-quantile plot comparing the observed dwell time distribution against the fitted exponential, particularly characterizing the tail behavior that gives rise to "minute-scale" instances?

2. What is the wire-to-wire and device-to-device variability in EM and τZ across the multi-tetron array, and what fraction of measured wires fall within the claimed performance specifications?

3. Is there a data availability statement or analysis code repository that would enable independent verification of the reported numerical results?

**Verdict: 6/10 — major-revisions**

---

## Voice 4 — Devil's Advocate

This manuscript exhibits a concerning pattern of presenting aspirational claims with insufficient supporting evidence, while downplaying or omitting information that would complicate the triumphalist narrative. Let me be specific about the most serious problems that the other reviewers have been too generous in overlooking.

First, the three-order-of-magnitude improvement in parity lifetime is based on a single wire in a single device, measured over an unspecified total duration, with results aggregated across an unspecified number of measurement sessions potentially spanning days. The authors casually mention that "the measurements in Fig. 4 and Fig. 5 were taken several days apart" with "some small shifts in gate voltages expected" (Ref. 85), revealing that device stability over relevant timescales is not actually demonstrated. If gate voltage drift of hundreds of microvolts occurs between measurement sessions, how can we be confident that the 20-second parity lifetime would be maintained over the operational timescales required for quantum computation? The entire premise of using parity lifetime as a qubit metric assumes stable operating conditions, yet stability is neither demonstrated nor even claimed.

Second, the claimed topological gap of ΔT ≈ 70 µeV (top quintile) is presented as a definitive improvement, but this number comes from the Topological Gap Protocol applied to test device structures (Fig. 3c), not to the actual multi-tetron array (Fig. 1) in which the parity measurements were performed. The TGP measurement was done on a "3 µm-long nanowire test structure" according to the figure caption, whereas the tetron nanowires are 3.5 µm long with different geometry including the narrow backbone junction. The authors provide no evidence that the TGP results transfer to the actual qubit geometry. This is not a minor caveat—the relationship between test structure performance and integrated device performance is the central question for any claim about scalability.

Third, the rf-based wire spectroscopy method, presented as enabling "scalable tuning," has only been demonstrated on one wire of one tetron. The multi-tetron array shown in Fig. 1 contains eight nanowires (two per tetron, four tetrons), yet all the detailed measurements (Figs. 4–6) focus exclusively on the top wire of the BA tetron. Where is the data from the other seven wires? If this is truly a "prototype unit cell for multi-tetron devices" suitable for "scaling to larger qubit arrays," why is there no demonstration of parallel tuning and characterization? The closest the authors come is mentioning that "all of the QDs have been designed to have plunger lever arms in the range 0.4–0.45 meV/mV," which is a design claim, not an experimental demonstration.

Fourth, the attribution of improved parity lifetime to the Pb-Al material difference is correlational, not causal. The authors changed multiple variables simultaneously: the superconductor (Al to Pb), the substrate (implied InP to GaSb), the quantum well composition (adding InAsSb), and presumably numerous fabrication details. While they argue that the larger Pb gap and stronger electron-phonon coupling are responsible for the improvement, they provide no controlled experiment varying only the superconductor while holding other factors constant. The device measured here is not a simple material substitution—it is a complete redesign. Alternative explanations, such as reduced defect density from the GaSb substrate or reduced quasiparticle injection from improved shielding, cannot be excluded.

The manuscript's discussion of implications for fault-tolerant quantum computing is premature to the point of being misleading. The abstract claims that "non-equilibrium quasiparticles no longer limit qubit operations in our devices," but no actual qubit operations are demonstrated. There is no coherent manipulation, no gate fidelity measurement, no demonstration of even a single logical operation. The parity measurement is a necessary but not sufficient component of a functioning qubit. By the same logic, I could claim that a very stable piece of iron "no longer limits" magnetic memory operations because it maintains its magnetization for years—but this says nothing about whether it can function as a memory element in an actual computing system.

**Recommendation: major-revisions**

The paper presents genuinely interesting results on material development and measurement techniques for Majorana-based devices, but the claims about qubit performance and scalability are substantially oversold relative to the evidence presented. Major revision is required to either scale back the claims to match the evidence or to provide substantially more data supporting the scalability and reproducibility assertions.

---

## Voice 5 — Editor-in-Chief synthesis

Having considered all four reviews, I find a manuscript that presents legitimate scientific advances alongside claims that substantially exceed the evidentiary support. The disagreement between reviewers reflects genuine tension in the paper between high-quality materials characterization and overreaching implications for quantum computing.

Reviewer 1 finds the physics framework sound but identifies gaps in the quantitative justification, particularly regarding induced gap simulations, spin-orbit coupling extraction methodology, and the connection between the minimal Hamiltonian model and the claim of µeV-resolution EM extraction. These are addressable through additional analysis and clearer presentation of methodology, consistent with minor revisions. Reviewer 2 raises more serious concerns about the novelty claim structure, correctly identifying that the absence of τX measurements for Pb-based devices undermines the Pareto dominance argument for complete qubit performance. This is a substantive gap that requires additional experimental data. Reviewer 3's concerns about statistical rigor, threshold sensitivity in the tuning protocol, and absence of failure-mode documentation are well-founded and align with best practices for high-impact experimental claims.

The Devil's Advocate raises the most damaging critique: the disconnect between the claimed "scalable multi-tetron array" architecture and the actual measurement scope, which focuses exclusively on one wire of one tetron. This criticism is valid and substantially undermines the paper's central narrative about demonstrating a pathway to fault-tolerant quantum computing. The observation that TGP measurements come from test structures rather than the actual qubit device is particularly concerning, as it breaks the evidentiary chain linking material improvements to qubit performance. However, I do not agree with the implicit suggestion that the entire line of reasoning is invalid—the improvements in parity lifetime are real and significant, even if the scalability claims are premature.

Reconciling these perspectives, I find that the manuscript would be appropriate for PRX Quantum after major revisions. The core scientific contribution—demonstration of dramatically improved parity lifetimes in Pb-based devices combined with a scalable rf-based tuning methodology—is significant and timely. However, the presentation must be substantially revised to align claims with evidence. The scalability narrative should be tempered to acknowledge that multi-wire, multi-tetron characterization remains future work. The failure-mode and reproducibility documentation needs expansion. And the statistical treatment of parity lifetime measurements requires the rigor appropriate for a flagship result.

**Must-fix items before resubmission, ordered by severity:**

1. Provide characterization data from at least one additional wire in the multi-tetron array (preferably from a different tetron than BA) demonstrating comparable EM and parity lifetime, or revise all claims about scalability and array-level performance to explicitly acknowledge single-wire scope.

2. Include either preliminary τX measurements for the Pb-based devices or remove all claims about implications for X-parity operations and general qubit performance, explicitly scoping the results to Z-parity measurements only.

3. Present quantitative model comparison (AIC or similar) between exponential and alternative dwell time distributions, including explicit treatment of the "minute-scale instances" tail behavior and characterization of measurement-to-measurement variability in extracted τZ.

4. Perform and report sensitivity analysis on the rf tuning protocol thresholds, quantifying how the identified topological region changes with S/σ threshold and cutter configuration requirements.

5. Either present TGP measurements on the actual tetron device in which parity measurements were performed, or clearly separate test structure characterization from device-level performance with explicit discussion of the expected transfer of properties.

6. Add a data availability statement specifying the accessibility of raw measurement data and analysis code, consistent with PRX Quantum policies on reproducibility.

---

## Vote table

| Voice | Recommendation | Confidence 1-10 |
|---|---|---|
| Reviewer 1 | minor-revisions | 7 |
| Reviewer 2 | major-revisions | 6 |
| Reviewer 3 | major-revisions | 6 |
| Devil's Advocate | major-revisions | 8 |
| Editor-in-Chief | major-revisions | 7 |