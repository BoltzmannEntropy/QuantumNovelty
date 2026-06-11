# Peer Review Panel: Flow-VQE Manuscript

---

## Voice 1 — Reviewer 1 (Physics correctness)

The manuscript presents a methodologically sound approach to variational quantum eigensolver optimization through normalizing flows. The Hamiltonian construction follows standard procedures: Jordan-Wigner transformation for fermion-to-qubit mapping, active space selections that are physically reasonable ((4e,4o) for H₄, (6e,5o) for H₂O, (6e,6o) for NH₃ and C₆H₆), and appropriate basis sets (STO-3G for the larger molecules, cc-pVDZ for H₄). The choice of Jordan-Wigner over Bravyi-Kitaev or parity mappings is not justified but is defensible given the modest qubit counts (5-12 qubits). The Z₂ symmetry tapering applied to H₄ is correctly implemented and reduces the qubit count from 8 to 5, which is standard practice.

The Hartree-Fock reference initialization strategy is well-motivated. The authors correctly note that HF typically recovers >99.5% of total electronic energy for small closed-shell molecules, making the remaining correlation energy the critical optimization target. The ansatz choices are appropriate: the hardware-efficient RY-linear ansatz for H₄ and Givens-based singles and doubles (GSD) for the other molecules. The GSD ansatz preserves particle number and spin symmetry by construction, which is crucial for chemical accuracy. However, the manuscript does not discuss the expressibility limits of these ansätze in relation to the active spaces chosen—particularly whether the GSD ansatz with 54-117 parameters can capture the full correlation energy within the selected active spaces.

One concern is the absence of discussion regarding numerical precision. The simulations are performed via PennyLane state-vector simulation, but the manuscript does not specify whether complex128 or complex64 precision was used. For stretched geometries where strong correlation effects dominate (e.g., H₄ at 2.6 Å or H₂O at 1.9 Å), numerical precision can significantly affect the computed energies, particularly when comparing against "exact diagonalization at the same level of theory." The claimed computational accuracy threshold of 1.6×10⁻³ Hartree (~1 kcal/mol) is chemically meaningful, but the authors should verify that numerical artifacts do not contaminate their comparisons at this precision level.

The treatment of stretched bond regions deserves additional scrutiny. The authors acknowledge that "energy errors increase in stretched bond-length regions due to strong correlation effects and the limited expressivity of the employed ansätze." This is physically correct, but the manuscript would benefit from quantifying the multireference character (e.g., via T1 diagnostic or natural orbital occupation numbers) to distinguish between ansatz limitations and Flow-VQE performance. Additionally, the equilibrium geometries and bond stretching ranges are reasonable for benchmarking, but the ammonia inversion coordinate and benzene C-H stretch represent different classes of nuclear motion that test different aspects of the PES—this diversity is a strength, but the physical rationale for these choices could be made more explicit.

**Questions for Authors:**
1. What numerical precision (complex64 vs complex128) was used in the state-vector simulations, and have you verified that precision artifacts do not affect comparisons at the 1.6×10⁻³ Hartree threshold?
2. Can you provide multireference diagnostics (T1 amplitudes or natural orbital occupations) for the stretched geometries to distinguish ansatz expressibility limitations from optimization performance?
3. Why was Jordan-Wigner chosen over Bravyi-Kitaev, given that BK can reduce circuit depth for certain ansätze?
4. For the GSD ansatz, have you verified that 54-117 parameters are sufficient to reach the FCI limit within your active spaces?

**Verdict: 7/10 — Minor Revisions**

---

## Voice 2 — Reviewer 2 (Algorithmic novelty)

The core algorithmic contribution—using conditional normalizing flows trained via preference-based optimization to generate VQE parameters—represents a meaningful advance over prior work, though the novelty claims require careful contextualization. The manuscript correctly identifies key limitations of existing approaches: gradient-based methods incur O(d) overhead per iteration, gradient-free methods scale poorly with dimensionality, and conventional parameter transfer relies on geometric proximity heuristics. Flow-VQE addresses these through a learned conditional prior that can generalize across chemical space.

Comparing against recent literature (2023-2025), several closely related works warrant discussion. Rudolph et al. (Nat. Commun. 2023, Ref. [25]) demonstrated tensor-network pretraining for parameterized quantum circuits, achieving similar goals of informed initialization. The manuscript does cite this but does not provide direct numerical comparison. More critically, Nakaji et al. (arXiv 2401.09253, Ref. [80]) introduced the Generative Quantum Eigensolver (GQE), which generates entire quantum circuits rather than just parameters—a more ambitious scope that subsumes Flow-VQE's approach. The authors acknowledge this in Section VI as future work but should more directly address how Flow-VQE relates to GQE's published results. Additionally, Chang et al. (arXiv 2505.10842, Ref. [44]) propose LSTM-based parameter prediction specifically for VQE, published after the apparent submission of this work but representing convergent thinking that affects novelty assessment.

The preference-based optimization scheme (Section III.C) is the most novel technical contribution. Drawing from RLHF methods in language models (DPO, Ref. [68]), the authors replace high-variance policy gradients with pairwise comparisons and elite buffer maintenance. This is clever and well-motivated: the observation that "chemically meaningful energy differences translate to extremely weak learning signals" (Section III.B.1) is correct and explains why vanilla REINFORCE would struggle. However, the connection to established preference learning theory is somewhat superficial—the authors do not discuss the implicit reward model induced by their approach or how it relates to Bradley-Terry preferences.

Regarding claimed performance ratios, the headline numbers ("up to two orders of magnitude fewer circuit evaluations," "50-fold acceleration") require scrutiny. Examining Figure 2, the two-orders-of-magnitude claim appears to derive from comparing Flow-VQE-S against gradient descent at specific bond lengths (e.g., H₂O at 1.8 Å shows ~10² improvement). However, the appropriate baseline comparison should be against Adam with properly tuned learning rates, where improvements are 2-5× according to the authors' own text. The 50-fold warm-start acceleration (Table I) occurs at learning rate η=0.001, which is unrealistically conservative for standard VQE—practitioners typically use η∈[0.01, 0.1]. At η=0.02, the improvement is ~27× for H₂O and ~11× for H₄, which are still impressive but more modest. These nuances should be foregrounded rather than buried.

**Questions for Authors:**
1. Can you provide direct numerical comparison against tensor-network pretraining (Rudolph et al.) and/or GQE (Nakaji et al.) on overlapping benchmark molecules?
2. What implicit reward model does your preference-based training induce, and how does it relate to Bradley-Terry or Plackett-Luce models?
3. Why were baseline comparisons performed at η=0.02 rather than grid-searching for optimal baseline learning rates, given that your headline improvements depend on baseline performance?

**Verdict: 6/10 — Major Revisions**

---

## Voice 3 — Reviewer 3 (Empirical evidence)

The experimental methodology presents several concerns regarding statistical rigor, reproducibility, and completeness of ablations. While the numerical results are promising, the empirical evidence does not meet the standards expected for a high-profile computational quantum chemistry publication.

The most significant gap is the absence of uncertainty quantification. All reported circuit evaluation counts and energy errors are point estimates without confidence intervals or multi-seed variance. Given the stochastic nature of both the normalizing flow sampling and the preference-based training, results should be reported over multiple random seeds (n≥5 is typical). For example, the claim that "Flow-VQE-S achieves approximately a two- to five-fold reduction" over Adam lacks error bars—does this range reflect variation across molecules, or could it also reflect run-to-run variance that would widen the comparison? Table I reports final energy errors to 4 significant figures (e.g., 5.932×10⁻⁴ Hartree), but without standard deviations, these precision claims are unverifiable.

The ablation study is incomplete. The authors introduce several design choices—Gaussianization flows versus alternative architectures, 7-20 flow layers, buffer size M=2, batch size B=2, Gaussian noise regularization (σ²=0.001), and linear Hamiltonian embeddings—but do not systematically ablate their contributions. Section VI acknowledges that "Flow-VQE introduces some additional hyperparameters... which may require more empirical tuning," but the reader is left without guidance on which choices are critical. Particularly concerning is the elite buffer size M=2: with only two samples retained per configuration, the training could be highly sensitive to early lucky draws. An ablation varying M∈{1, 2, 5, 10} would clarify whether the method is robust.

The comparison against baselines raises methodological questions. The authors compare Flow-VQE against GD, Adam, and QNSPSA with fixed hyperparameters, but hyperparameter optimization is standard practice for baseline comparisons. The statement "All baseline optimizers use a learning rate of η=0.02" in Figure 2 suggests baselines were not individually tuned, potentially handicapping them. Additionally, the QNSPSA comparison is welcome (as a gradient-free method), but the manuscript does not include other recent gradient-free approaches such as COBYLA, Nelder-Mead, or evolutionary strategies that are commonly used in VQE literature.

Reproducibility infrastructure is not adequately described. The manuscript mentions "state-vector simulation experiments" using PennyLane and OpenFermion but does not provide: (a) version numbers for software dependencies, (b) hardware specifications for classical computation, (c) wall-clock training times, or (d) code/data availability statements beyond acknowledging NAISS computational resources. For a method whose practical utility depends on the classical overhead remaining "easily tractable with modern machine learning techniques," timing data would strengthen the claims. The required npj Quantum Information statements (Code Availability, Data Availability) appear to be missing from the current draft.

**Questions for Authors:**
1. Can you report multi-seed variance (n≥5) for the key comparisons in Figures 2-4 and Table I?
2. What ablations can you provide for buffer size M, batch size B, flow depth, and regularization noise?
3. Will code and data be released upon publication, and at what URL?
4. What are the wall-clock training times for Flow-VQE-S and Flow-VQE-M on a specified hardware configuration?

**Verdict: 5/10 — Major Revisions**

---

## Voice 4 — Devil's Advocate

This manuscript exemplifies a troubling trend in quantum computing: impressive-sounding improvements over carefully chosen baselines that dissolve under scrutiny. Let me enumerate the fundamental problems that my fellow reviewers have been too generous about.

**The baseline comparisons are rigged.** The entire narrative hinges on comparing against gradient descent, an optimizer no serious VQE practitioner would use for production work. The authors bury the admission that "Flow-VQE-S achieves approximately a two- to five-fold reduction" over Adam—this is the *only* meaningful comparison, and 2-5× improvement is incremental, not transformative. The "two orders of magnitude" headline claim requires comparing against raw GD at η=0.02 without momentum, which is a strawman. Furthermore, baseline optimizers were run with identical learning rates rather than individually tuned, while Flow-VQE's hyperparameters (learning rate, weight decay, flow depth, buffer size, batch size, noise variance) were presumably chosen via undocumented empirical search. This asymmetry invalidates the entire quantitative comparison.

**The method cannot scale.** The authors test on systems with 5-12 qubits and 54-117 parameters. Modern quantum chemistry requires hundreds to thousands of qubits. Section VI's optimistic claim that "the classical overhead in modern normalizing-flow architectures scales linearly in d" ignores the elephant in the room: flow models require O(d) samples to estimate the target distribution in d dimensions, and preference-based training with buffer size M=2 cannot possibly capture a meaningful distribution over 10,000+ parameters. The authors' own Figure 6 shows extensive stagnation plateaus even at d≈100—these will become impassable walls at chemically relevant scales. The comparison against parameter transfer (Figure 4) shows Flow-VQE-M only marginally outperforming PT, which requires no neural network overhead whatsoever.

**The experimental design hides failures.** Why are only four molecules tested? Why these specific geometric distortions? The authors test H₂O bond stretching, H₄ linear chain stretching, NH₃ inversion, and C₆H₆ C-H stretch—but conspicuously absent are: (a) molecules with transition metals, (b) open-shell systems, (c) excited states, (d) strongly correlated systems beyond stretched bonds, and (e) any molecule requiring >12 qubits. The selection bias suggests the authors tried other systems and failed. The manuscript contains no honest negatives, no failure modes section, and no discussion of when Flow-VQE underperforms baselines. Figure 2(b) shows Flow-VQE-S *losing* to Adam at H₄ 0.6 Å—this is mentioned in passing but not analyzed. A rigorous empirical study would characterize the conditions under which the method fails.

**The novelty is overstated.** The core idea—use generative models to propose VQE parameters—appears in multiple prior works: Ceroni et al. (Ref. [34], 2023), Zhang et al. (Ref. [35], 2025), and Nakaji et al. (Ref. [80], 2024). The preference-based training draws directly from DPO in language models without significant adaptation for quantum settings. The Gaussianization flow architecture is off-the-shelf (Meng et al., AISTATS 2020). The conditional embedding via Hamiltonian coefficients is straightforward. Stripping away the quantum framing, this is a routine application of conditional generative modeling to a black-box optimization problem—technically competent but not meeting the novelty bar for a flagship publication.

**The required journal elements are missing.** npj Quantum Information mandates Author Contributions, Competing Interests, Data Availability, and Code Availability statements. None appear in this draft. The Methods section is scattered throughout rather than consolidated at the end per Nature/npj conventions. The abstract (currently 248 words) barely meets the 250-word limit. These are not fatal flaws but indicate either carelessness or unfamiliarity with the target venue.

**Recommendation: Reject.** The contributions do not justify publication in npj Quantum Information. The method shows modest improvements over properly chosen baselines, cannot scale to relevant system sizes, lacks statistical rigor, and does not advance the field beyond concurrent/prior work. The manuscript may be suitable for a computational chemistry venue after substantial revision.

---

## Voice 5 — Editor-in-Chief synthesis

Having carefully considered all four reviews, I observe substantial disagreement regarding the manuscript's merits. Reviewer 1 finds the physics sound with minor concerns about numerical precision and ansatz expressibility. Reviewer 2 identifies legitimate novelty in the preference-based training scheme but requests stronger baseline comparisons and engagement with concurrent work. Reviewer 3 raises serious methodological concerns about statistical rigor and reproducibility that must be addressed. The Devil's Advocate presents the strongest case for rejection, emphasizing baseline selection bias, scalability limitations, and missing journal requirements.

Let me address the Devil's Advocate's critiques specifically, as they represent the highest bar the authors must clear. The baseline comparison criticism has merit: comparing against GD is indeed uninformative, and the Adam comparison should be the primary benchmark. However, the 2-5× improvement over Adam, combined with the generative warm-start capability (Table I), does represent meaningful practical utility—especially for practitioners who must optimize many related molecular configurations. The scalability criticism is fair but applies to essentially all NISQ algorithm papers; the authors appropriately scope their claims to near-term devices. The charge of hidden failures is partially addressed by the H₄ 0.6 Å result where Flow-VQE underperforms, though I agree a dedicated failure analysis would strengthen the work. The novelty critique is the most serious: the manuscript must better differentiate from Nakaji et al. (GQE) and demonstrate why parameter-space generation offers advantages over circuit-space generation.

The statistical concerns raised by Reviewer 3 are non-negotiable for publication. Single-seed results without confidence intervals are insufficient for empirical claims. The missing Data/Code Availability statements violate npj QI policy and must be added. The incomplete ablation study leaves readers unable to assess which design choices are essential versus incidental.

Regarding the physics and chemistry (Reviewer 1), the concerns are addressable through clarifications rather than new experiments. The algorithmic novelty (Reviewer 2) requires engagement with concurrent literature but does not fundamentally undermine the contribution. The preference-based training adapted from RLHF to quantum chemistry contexts is a genuine methodological contribution, even if the components are individually known.

**Final Verdict: Major Revisions**

The manuscript presents a technically sound method with meaningful practical utility for VQE optimization across molecular configurations. However, the current presentation suffers from inflated claims relative to appropriate baselines, inadequate statistical rigor, missing journal-required elements, and insufficient differentiation from concurrent work. Acceptance is possible after substantial revision.

**Must-fix items before resubmission (ordered by severity):**

1. **Add multi-seed variance reporting** (n≥5) for all quantitative comparisons, including Figures 2-4 and Table I. Report 95% confidence intervals or standard deviations.

2. **Include Code and Data Availability statements** per npj QI requirements, with repository URLs and DOIs where applicable.

3. **Revise headline claims** to foreground Adam comparisons (2-5× improvement) rather than GD comparisons (100×). Move GD results to supplementary material or present as secondary.

4. **Add direct comparison with GQE** (Nakaji et al.) or explicitly justify why parameter-space generation is preferable to circuit-space generation for the tested molecules.

5. **Provide ablation study** for buffer size M, flow depth, and regularization noise, minimally as supplementary material.

6. **Consolidate Methods section** at the end of the manuscript per Nature/npj conventions, and add required Author Contributions and Competing Interests statements.

7. **Specify numerical precision** (complex64/128) and verify that precision artifacts do not affect comparisons at the 1.6 mHa threshold.

8. **Add failure mode analysis** discussing conditions under which Flow-VQE underperforms baselines, expanding on the H₄ 0.6 Å observation.

---

## Vote table

| Voice | Recommendation | Confidence 1-10 |
|---|---|---|
| Reviewer 1 | Minor Revisions | 7 |
| Reviewer 2 | Major Revisions | 6 |
| Reviewer 3 | Major Revisions | 8 |
| Devil's Advocate | Reject | 7 |
| Editor-in-Chief | Major Revisions | 8 |