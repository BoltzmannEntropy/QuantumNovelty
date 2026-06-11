# Peer Review Panel: Surface-Code Threshold Improvements via Measurement-Cycle Reordering

---

## Voice 1 — Reviewer 1 (Physics correctness)

The manuscript presents a theoretically motivated approach to improving surface code thresholds through measurement-cycle reordering, which is a legitimate degree of freedom in syndrome extraction circuit design. However, I have significant concerns about the physics rigor and completeness of the presentation. The detector error model framework (Section II.C) is correctly described in principle, but the manuscript fails to specify critical numerical precision details. Circuit-level simulations using Stim typically operate with floating-point arithmetic, yet no discussion is provided regarding whether complex64 versus float64 precision affects the detector graph weight calculations, particularly for the low-probability tails of the error distribution where threshold estimation is most sensitive. Given that edge weights are computed as $w = -\log(p_{\text{mech}})$, numerical underflow or precision loss in the probability estimates could systematically bias threshold estimates.

The treatment of the circuit-level depolarizing noise model in Section II.C is incomplete. The manuscript states that two-qubit gates fail with probability $p$ and are "replaced by a uniformly random two-qubit Pauli error," but this is ambiguous. A two-qubit depolarizing channel has 15 nontrivial Pauli terms (excluding $I \otimes I$), and the conventional parametrization assigns probability $p/15$ to each. The manuscript should clarify whether $p$ is the total error probability or the per-Pauli probability, as this affects threshold estimates by factors of order unity. Furthermore, the idle error model ("depolarizing noise with probability $p$ per time step") does not specify whether this applies to data qubits only, ancilla qubits only, or both, nor whether idle errors during measurement are treated differently from idle errors during gate execution.

The gate ordering constraints described in Section II.D are physically correct for the rotated layout, but the manuscript does not adequately address the hook error problem. In standard syndrome extraction circuits, certain gate orderings create "hook" error mechanisms where a single ancilla error propagates to multiple data qubits, effectively increasing the weight of the error. The wavefront ordering proposed here may exacerbate or mitigate hook errors depending on the sweep direction, but no analysis is provided. The claim that wavefront ordering "naturally incorporates" temporal decorrelation (Section V.A) is asserted without proof. A rigorous analysis would enumerate the hook error pathways for each ordering and demonstrate quantitatively that the proposed ordering reduces their total weight.

The scaling ansatz in Equation (5), $p_L \sim (p/p_{\text{th}})^{(d+1)/2}$, is the standard form for the surface code, but the manuscript does not verify that this ansatz provides a good fit to the simulation data. The fitting procedure described in Section III.D uses a linearized form (Equation 4) with four free parameters, which may overfit sparse data. No goodness-of-fit statistics ($\chi^2$, reduced $\chi^2$, or residual analysis) are reported. Additionally, the critical exponent $\nu$ is stated to be in the range 1.0–1.2, but the fitted value is not reported, making it impossible to assess whether the phase transition universality class is correctly identified. The absence of finite-size scaling analysis is a significant omission for a paper claiming quantitative threshold improvements.

**Verdict: 5/10**

**Recommendation: Major revisions**

---

## Voice 2 — Reviewer 2 (Algorithmic novelty)

The central claim of this manuscript—that measurement-cycle reordering can improve surface code thresholds—must be evaluated against the existing literature on syndrome extraction optimization. The authors cite Fowler et al. (2012) and Tomita & Svore (2014) as prior work on measurement scheduling but characterize these as focused on "parallelization constraints" rather than threshold optimization. This framing is misleading. Tomita & Svore explicitly analyzed different gate orderings for the rotated planar code and reported threshold variations depending on the CNOT sequence. More recently, Gidney & Fowler (arXiv:2302.02192, 2023) systematically compared hook error rates for different syndrome extraction circuits, demonstrating that gate ordering within stabilizer measurements affects threshold by 10-20% relative. The present manuscript does not cite this directly relevant work, raising concerns about the novelty assessment.

The algorithmic contribution—Algorithm 1 for measurement-cycle optimization—is essentially a grid search over a parametrized family of orderings followed by detector graph scoring. The scoring function (Equation 3) combines mean edge weight, minimum cut, and a correlation measure with hand-tuned hyperparameters ($\alpha=1$, $\beta=-0.5$, $\gamma=0.3$). The authors state these values were "tuned empirically" but provide no justification for why this particular combination should correlate with threshold performance. Absent validation that the scoring function rank-orders orderings correctly (i.e., that high-scoring orderings consistently achieve higher thresholds in simulation), Algorithm 1 is not a principled optimization procedure but rather a heuristic whose success may be coincidental. A proper validation would compute thresholds for a random subset of orderings and demonstrate correlation with predicted scores.

The claimed threshold improvements—reported as "$\langle\text{INSERT MEASURED VALUE}\rangle$\%" throughout—cannot be evaluated because no actual values are provided. For a paper submitted to PRX Quantum, this is unacceptable; the draft must include numerical results. However, based on the methodology described, I can assess whether the claimed improvements would represent genuine novelty. The comparison baseline is "standard block ordering," but this is not the strongest baseline in the literature. Recent work by Higgott & Gidney (PRX Quantum, 2023) on sparse blossom matching achieves thresholds of approximately 0.8% for circuit-level depolarizing noise on the rotated planar code. If the "optimized" ordering achieves, say, 0.85%, this would be notable; if it achieves 0.72%, it would merely recover performance already achievable through decoder optimization. The manuscript must situate its results against decoder-optimized baselines, not just against suboptimal scheduling baselines.

The strict-domination criterion for novelty assessment requires that the proposed method achieve better performance on all relevant metrics without sacrificing any. The manuscript acknowledges (Section V.C) that the optimized ordering may increase circuit depth by some unspecified percentage. This is a direct tradeoff: threshold improvement versus circuit duration. For systems with non-negligible idle errors, increased circuit duration directly increases the effective error rate, potentially negating threshold gains. A genuine Pareto improvement would demonstrate that the optimized ordering achieves both higher threshold AND shorter or equal circuit duration. Without this demonstration, the contribution is incremental rather than dominating.

**Verdict: 4/10**

**Recommendation: Major revisions**

---

## Voice 3 — Reviewer 3 (Empirical evidence)

The empirical methodology described in this manuscript has fundamental gaps that preclude acceptance in its current form. Most critically, **every numerical result in the paper is a placeholder** ("$\langle\text{INSERT MEASURED VALUE}\rangle$"). This is not a minor formatting issue; it means the manuscript contains zero verifiable empirical claims. For a paper whose core contribution is demonstrating that measurement reordering improves thresholds, the absence of any threshold values renders the work unpublishable. The placeholder "[INSERT TABLE REF]" and "[INSERT FIG REF]" annotations throughout suggest this is an incomplete draft that was submitted prematurely.

Setting aside the missing data, I can evaluate whether the described methodology would, if executed, produce credible results. The Monte Carlo procedure (Section III.D) specifies that logical error rates are computed as $p_L = N_{\text{errors}}/N_{\text{samples}}$, but $N_{\text{samples}}$ is never specified. For threshold estimation near crossing points, logical error rates are typically in the range 0.1–0.5, requiring sample sizes of at least $10^4$ to achieve 1% relative precision. For sub-threshold characterization (Section IV.B), where $p_L$ may be $10^{-3}$ or smaller, sample sizes of $10^6$ or more are necessary. The manuscript does not report sample sizes, making it impossible to assess statistical validity. Furthermore, bootstrap confidence intervals (mentioned with $N_{\text{bootstrap}}=1000$) are only meaningful if the underlying sample sizes are adequate; bootstrapping cannot compensate for insufficient data.

The manuscript lacks any ablation study or sensitivity analysis. The optimization procedure (Algorithm 1) has multiple design choices: the ordering family $\mathcal{F}$, the scoring function hyperparameters $(\alpha, \beta, \gamma)$, and the noise model parameters. A rigorous empirical study would include ablations demonstrating that (i) the scoring function outperforms random search, (ii) the hyperparameters are not overfit to specific code distances, and (iii) the threshold improvements persist under noise model variations (e.g., different single-qubit vs. two-qubit error ratios, or measurement error asymmetries). None of these ablations are reported. The absence of negative results or failure modes is also concerning—no mention is made of orderings that were tried and failed, or of conditions under which reordering provides no benefit.

For reproducibility, the manuscript mentions a "reference implementation" but provides only a stub Python function with the comment "Implementation details omitted for brevity." The data underlying all figures and tables is not described as being deposited in any repository. There is no equivalent of an `audit_claims.py` script that would allow independent re-derivation of numerical claims from raw simulation output. The citation of Stim and PyMatching is appropriate, but without specifying exact versions and random seeds, results may not be reproducible across environments. A publication-ready manuscript should include, at minimum, a supplementary code repository with all simulation scripts, raw data files (JSON or equivalent), and analysis notebooks that produce each figure and table.

**Verdict: 2/10**

**Recommendation: Reject** (resubmit when numerical results and reproducibility materials are complete)

---

## Voice 4 — Devil's Advocate

This manuscript should be rejected, and I will articulate the case more forcefully than my colleagues have. The fundamental problem is not merely that the numerical results are missing—it is that the entire theoretical framework is built on unsupported assumptions, the claimed novelty is illusory, and the methodology would not support the conclusions even if data were present.

**The theoretical framework is circular.** The authors propose optimizing measurement orderings using a scoring function (Equation 3) that purportedly correlates with threshold performance. But this scoring function was "tuned empirically"—meaning the authors adjusted $(\alpha, \beta, \gamma)$ until the scoring function ranked orderings in a way that matched threshold simulations. This is textbook overfitting. The scoring function has three free parameters and is evaluated on a finite set of orderings; with three degrees of freedom, one can always find weights that produce apparent correlation on the training set. The authors provide no out-of-sample validation, no theoretical justification for why mean edge weight, minimum cut, and detector correlation should combine linearly, and no analysis of identifiability (i.e., whether multiple hyperparameter combinations produce equivalent rankings). Without this validation, Algorithm 1 is not an optimization procedure—it is curve fitting disguised as algorithm design.

**The novelty claim is likely false.** The authors assert that "comparatively less attention has been devoted to optimizing the temporal structure of the syndrome extraction circuit itself," but this directly contradicts the published record. Chamberland & Cross (Quantum 2019) analyzed hook error mitigation through gate reordering. Gidney's Stim paper (Quantum 2021) includes extensive discussion of how circuit structure affects detector error models. The recent Google Quantum AI paper on suppressing errors in surface codes (Nature 2023) explicitly discusses measurement scheduling as part of their optimization pipeline. The present manuscript fails to cite any of these directly relevant works in its novelty framing. If the claimed threshold improvements (once measured) are comparable to what these prior works achieved through related techniques, the contribution is incremental at best and redundant at worst.

**The methodology cannot support quantitative claims.** Even if the authors were to fill in all placeholder values, the experimental design has fatal flaws. The code distances studied ($d \in \{3,5,7,9,11\}$) are too small to reliably extrapolate threshold behavior. At $d=3$, finite-size effects dominate; at $d=11$, the code has only 121 data qubits, which is far from the thermodynamic limit where threshold universality applies. The authors' scaling ansatz (Equation 5) assumes power-law behavior, but for small distances, subleading corrections can be comparable to the leading term. Without simulating $d \geq 15$ and demonstrating that finite-size corrections are under control, any threshold estimate carries systematic uncertainty that likely exceeds the claimed improvements.

**The practical relevance is overstated.** The Discussion (Section V.C) acknowledges that optimized orderings may increase circuit depth, then dismisses this concern by assuming "idle error rates are comparable to gate error rates." This assumption is false for all current superconducting qubit systems. In Google's systems, $T_1$ times are approximately 20 μs, while gate durations are 20-40 ns, meaning a qubit idles through hundreds of gate times during a syndrome extraction round. Increased circuit depth directly increases the number of idle time steps, accumulating additional depolarizing errors. A 15% threshold improvement could easily be negated by a 10% increase in circuit duration under realistic noise budgets. The authors provide no quantitative analysis of this tradeoff, making their claims of "practical, hardware-agnostic" improvement unjustified.

**Verdict: This manuscript presents an incomplete draft with placeholder results, inadequate literature review, circular methodology, and unsupported practical claims. It does not meet the standards for PRX Quantum.**

**Recommendation: Reject**

---

## Voice 5 — Editor-in-Chief synthesis

Having reviewed all four assessments, I must reconcile substantive disagreements and determine whether this manuscript, after revision, could meet PRX Quantum's standards for technical depth and novelty. I will address the Devil's Advocate's critiques directly, as they represent the most stringent evaluation.

**On the missing numerical results (R3, DA):** The Devil's Advocate and Reviewer 3 correctly identify that a manuscript without numerical data cannot be evaluated for empirical validity. This is not a minor revision issue—it is a fundamental incompleteness. However, I disagree that this alone warrants final rejection. The theoretical framework, if sound, could support strong results once simulations are complete. The appropriate disposition is "reject with invitation to resubmit" once data is available, rather than prejudging the conclusions. That said, the burden on resubmission will be high: the authors must demonstrate not only that their optimized orderings achieve higher thresholds but that this improvement is robust across noise models, decoder choices, and code distances beyond the small-scale regime.

**On novelty (R2, DA):** The Devil's Advocate's critique regarding undercited prior work is valid. The manuscript must engage substantively with Chamberland & Cross (2019), Gidney (2021), Gidney & Fowler (2023), and the Google Nature (2023) experimental paper. If these works already achieved comparable threshold improvements through gate or measurement scheduling, the present contribution is incremental. However, I note that there may be a distinction between gate ordering within a stabilizer measurement (which affects hook errors) and measurement-cycle ordering across stabilizers (which affects temporal correlations). If the authors can demonstrate that their wavefront ordering provides benefits orthogonal to prior hook-error mitigation, this could constitute genuine novelty. The burden of proof lies with the authors.

**On methodology (R1, R2, DA):** Reviewer 1's concerns about noise model specification and fitting procedures are addressable through additional detail. The Devil's Advocate's critique of the scoring function's circularity is more serious. I recommend that on resubmission, the authors (a) provide theoretical motivation for the functional form of Equation 3, (b) demonstrate out-of-sample validation by training on small distances and predicting performance at larger distances, or (c) abandon the scoring function entirely and report exhaustive threshold simulations for all candidate orderings. The claim that wavefront ordering "naturally incorporates" beneficial mechanisms (Section V.A) must be supported by quantitative analysis of hook error weights and temporal correlation functions, not assertion.

**On practical relevance (DA):** The Devil's Advocate's point about idle errors versus circuit duration is well-taken. A credible revision must include a quantitative analysis of the threshold-versus-duration tradeoff under realistic noise budgets (e.g., using published Google or IBM device parameters). If the threshold improvement vanishes when circuit duration is accounted for, the contribution is of limited practical value and should be framed accordingly.

**Final verdict:** This manuscript is not acceptable in its current form. The missing numerical results, inadequate literature engagement, and unvalidated methodology represent serious deficiencies. However, the research direction is legitimate, and a substantially revised manuscript could merit publication if the authors address the following required changes.

**Must-fix before resubmission (ordered by severity):**

1. **Provide all numerical results.** Every placeholder must be replaced with measured values, confidence intervals, and sample sizes. All figures and tables must include actual data.

2. **Cite and compare against relevant prior work.** Explicitly discuss Gidney & Fowler (2023), Chamberland & Cross (2019), and Google (2023). Quantify how the proposed threshold improvements compare to what these works achieved.

3. **Validate the scoring function.** Either provide out-of-sample validation demonstrating predictive power, or replace with exhaustive threshold simulation across all candidate orderings.

4. **Quantify the threshold-versus-duration tradeoff.** Report circuit depths for all orderings and compute effective thresholds under realistic idle-noise budgets.

5. **Extend simulations to larger code distances.** Include $d \geq 13$ to assess finite-size corrections and demonstrate that claimed improvements persist at scale.

6. **Specify noise model parameters unambiguously.** Clarify per-Pauli versus total error probabilities, idle error treatment, and measurement error asymmetries.

7. **Provide reproducibility materials.** Deposit code, data, and analysis scripts in a public repository with version-pinned dependencies.

---

## Vote table

| Voice | Recommendation | Confidence 1-10 |
|---|---|---|
| Reviewer 1 | Major revisions | 6 |
| Reviewer 2 | Major revisions | 7 |
| Reviewer 3 | Reject | 9 |
| Devil's Advocate | Reject | 8 |
| Editor-in-Chief | Reject (resubmit when complete) | 8 |