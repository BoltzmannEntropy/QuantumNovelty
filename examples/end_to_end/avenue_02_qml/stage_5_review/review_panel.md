# Peer Review Panel: Quantum Kernel Methods for Binary Classification

---

## Voice 1 — Reviewer 1 (Physics correctness)

The theoretical framework presented in this manuscript addresses quantum kernel expressibility through a well-structured mathematical formalism. The definition of quantum kernel effective dimension (Definition 1) appropriately extends classical kernel theory concepts to the quantum domain, and the choice to analyze the kernel matrix eigenvalue spectrum via random matrix theory is methodologically sound. However, I have significant concerns about the completeness and rigor of several physics-related aspects of this work.

The proof sketch for Theorem 1 (Exponential Separation in Effective Dimension) relies on IQP circuit constructions, but the manuscript fails to adequately address the relationship between the encoding function structure and the claimed separation. Specifically, the choice $\theta_{ij}(\mathbf{x}) = x_i x_j$ for the diagonal gates represents a polynomial encoding that may not satisfy the conditions needed for the claimed exponential eigenvalue distribution. The authors assert that "the phase structure generates $2^{n(n-1)/2}$ distinct Fourier modes," but this counting argument requires that the $\binom{n}{2}$ phase terms be algebraically independent over the input distribution—a condition not formally verified. Moreover, the transition from the IQP construction in the Methods section to the "complete graph connectivity" requirement stated in Theorem 1 is unexplained; IQP circuits are diagonal in the computational basis and do not require complete connectivity in the sense typically used for entangling gate architectures.

Theorem 3 (Noise-Induced Distortion Scaling) presents a depolarizing noise analysis that, while standard, contains a subtle error in the derivation. The authors claim $\Delta_\kappa \leq 1 - (1-p)^{2G}$ but the proof sketch arrives at $4\sqrt{pG}$ through a different line of reasoning. These bounds have fundamentally different scaling behaviors: the former is linear in $G$ for small $pG$, while the latter scales as $\sqrt{G}$. The manuscript must reconcile these expressions and clarify which bound is tight. Additionally, the depolarizing noise model assumes uniform error rates across all gates, which does not reflect the heterogeneous error landscape of real superconducting processors where crosstalk, ZZ coupling errors, and state-dependent relaxation introduce correlated noise structures that could either amplify or suppress kernel distortion relative to the idealized model.

The experimental implementation section describes a swap test circuit for kernel estimation, but the provided code snippet implements a different construction. The swap test requires $2n+1$ qubits (one ancilla plus two $n$-qubit registers), controlled-SWAP gates, and measures the ancilla. However, the code shows sequential encoding into what appears to be a single register with CNOT entanglement—this is not a swap test implementation. If the authors used direct fidelity estimation $|\langle\phi(\mathbf{x})|\phi(\mathbf{x}')\rangle|^2 = |\langle 0|U^\dagger(\mathbf{x})U(\mathbf{x}')|0\rangle|^2$ via computational basis measurement after applying $U^\dagger(\mathbf{x})U(\mathbf{x}')$, this should be stated explicitly, as the measurement statistics and shot requirements differ substantially from the swap test. The claim that $\kappa_Q = 2 \cdot \Pr[\text{ancilla} = 0] - 1$ is only correct for the swap test; direct overlap estimation gives $\kappa_Q = \Pr[\text{all zeros}]$, which has different sampling complexity.

**Verdict: 5/10**

**Recommendation: Major Revisions**

The physics framework is reasonable but contains errors in the noise analysis, inconsistencies between the theoretical construction and stated theorems, and a significant discrepancy between the described and implemented kernel estimation protocols. These issues must be resolved before publication.

---

## Voice 2 — Reviewer 2 (Algorithmic novelty)

This manuscript addresses the important question of whether theoretical quantum kernel advantages translate to practical benefits on near-term hardware. While this is a timely topic, I find the novelty claims insufficiently differentiated from recent literature, and several of the theoretical contributions appear to be incremental extensions of known results.

The main theoretical contribution—Theorem 1 on exponential separation in effective dimension—closely parallels results from Huang et al. (Nature Communications, 2021) and Liu et al. (Nature Physics, 2021), which the authors cite. The novelty claimed here is the connection to effective dimension rather than sample complexity or computational hardness, but effective dimension bounds for kernel methods are well-established in classical learning theory (Caponnetto & De Vito, 2007, which the authors also cite). The bridge between quantum kernel expressibility and effective dimension, while pedagogically useful, does not constitute a fundamental advance. Moreover, Kübler et al. (NeurIPS 2021) already demonstrated that quantum kernels can fail to provide advantage when the inductive bias does not match the problem structure—a point the authors rediscover empirically but do not advance theoretically.

Recent work directly relevant to this manuscript includes: (1) Thanasilp et al. (Nature Communications, 2024), which the authors cite but whose implications they understate—that paper shows exponential concentration of quantum kernel gradients, directly limiting trainability of kernel hyperparameters and suggesting that fixed quantum kernels may be the only viable paradigm, which strengthens rather than challenges the authors' approach; (2) Bowles et al. (arXiv:2310.XXXXX, 2023), which provides tighter bounds on the classical simulability of quantum kernel computations and demonstrates that many IQP-based kernels can be efficiently approximated classically for smooth input distributions—directly relevant to the authors' IQP construction; (3) Cerezo et al. (Nature Computational Science, 2023), cited by the authors, which provides a comprehensive framework for understanding when quantum machine learning can provide advantage. Against this backdrop, the theoretical contributions here appear incremental.

The noise-aware kernel quality metric (Definition 3 and Theorem 3) is practical but not novel. The observation that kernel distortion scales linearly with gate count under depolarizing noise is a straightforward consequence of channel contractivity, and similar analyses appear in Wang et al. (2021) for variational circuits. The authors' contribution is applying this framework specifically to kernel estimation, which is useful engineering but does not meet the novelty threshold for a venue like npj Quantum Information. A strict-domination comparison would ask: does this paper provide a Pareto improvement over existing work in any dimension (tighter bounds, broader applicability, novel proof techniques, substantially better experiments)? I cannot identify such an improvement.

The empirical contribution—systematic comparison on three datasets with hardware execution—has value, but the presentation undermines this value. All quantitative results are placeholders ($<$INSERT MEASURED VALUE$>$), making it impossible to assess whether the experiments reveal new insights. The choice of benchmarks (parity, symmetry, molecular) is reasonable but follows the template of Huang et al. (2021) rather than introducing novel problem domains. Without concrete numbers, I cannot evaluate claims about "threshold behavior" in accuracy versus kernel distortion or the specific hardware requirements identified.

**Verdict: 4/10**

**Recommendation: Major Revisions**

The manuscript addresses an important question but does not sufficiently advance beyond the recent literature. The theoretical contributions are incremental, and the empirical results, while potentially valuable, are entirely placeholder-dependent. Substantial revision is needed to articulate a clear novelty claim and provide complete experimental data.

---

## Voice 3 — Reviewer 3 (Empirical evidence)

The empirical methodology described in this manuscript has several fundamental deficiencies that preclude confident interpretation of the results. Most critically, the manuscript is submitted with all quantitative values replaced by placeholders, making it impossible to verify any empirical claim. I will assess the methodological framework assuming the placeholders will be filled, but this represents an unusual submission state.

The statistical analysis section describes "$<$INSERT MEASURED VALUE$>$ independent train/test splits" with "95% confidence intervals computed via bootstrap resampling with $<$INSERT MEASURED VALUE$>$ bootstrap samples." Without knowing the actual values, I cannot assess whether the experimental design has adequate statistical power. For binary classification on small quantum devices, typical dataset sizes of 100-500 samples yield wide confidence intervals. If the claimed advantages are on the order of 5-10 percentage points in accuracy, the experiments would need to carefully account for variance. The mention of "paired $t$-tests with Bonferroni correction" is appropriate for multiple comparisons, but the number of comparisons (across three datasets, multiple circuit depths, and four classical baselines) could severely reduce statistical power after correction. I would expect to see Wilson score intervals for binomial proportions (classification accuracy) rather than bootstrap CIs, which can be poorly calibrated for small samples.

The ablation study design is notably incomplete. The manuscript identifies several factors affecting quantum kernel performance: circuit depth, entanglement structure (HEA vs IQP vs tensor network), data encoding scheme, and noise characteristics. However, the experimental results section only varies circuit depth systematically. There is no ablation isolating the effect of entanglement structure with depth held constant, no comparison between different encoding functions $f_i^{(\ell)}(\mathbf{x})$, and no systematic study of shot budget versus accuracy tradeoffs. The claim that "data-dependent encoding schemes partially mitigate [kernel concentration]" is made without quantitative comparison to data-independent encodings. A complete ablation would include: (1) encoding scheme (linear, polynomial, Fourier); (2) entanglement topology (linear, all-to-all, random); (3) circuit depth (1 to maximum before concentration); (4) shot budget (logarithmic sweep); (5) error mitigation (none, ZNE, PEC). The manuscript touches on only (3) with incomplete ZNE results.

The manuscript lacks a dedicated failure modes or honest-negatives section. Scientific rigor requires explicit acknowledgment of when and why the method fails. The authors note that molecular property classification showed "minimal quantum-classical gap," but do not systematically characterize the problem features that predict quantum kernel failure. What properties of a classification task indicate that quantum kernels will not help? The theoretical framework (alignment between problem structure and quantum geometry) is too vague to be actionable. A proper failure analysis would identify: (1) problem dimensionality regimes where classical kernels dominate; (2) noise thresholds below which quantum kernels lose all advantage; (3) circuit structures that consistently underperform classical baselines. Without this analysis, practitioners cannot determine when to apply quantum kernel methods.

Finally, there is no evidence of an automated claim verification system. The Methods section describes experimental procedures but does not indicate whether the claimed numerical results can be automatically rederived from raw experimental data. Best practices in computational reproducibility require that every number in the paper be traceable to a specific computation on archived data. I would expect to see: (1) raw kernel matrix files in a specified format; (2) scripts that compute all reported statistics from these files; (3) version-pinned software environment specifications; (4) checksums or hashes for data integrity verification. The Code Availability statement mentions a repository but provides no URL, and there is no indication that the repository contains automated verification tools.

**Verdict: 3/10**

**Recommendation: Major Revisions**

The empirical methodology is fundamentally incomplete. The submission with placeholder values, inadequate ablation design, missing failure mode analysis, and absent reproducibility infrastructure does not meet the standards for empirical claims in a high-quality venue. The authors must provide complete data, comprehensive ablations, and verifiable computational reproducibility before this work can be properly evaluated.

---

## Voice 4 — Devil's Advocate

This manuscript should be rejected. The reviewers above have been too generous in characterizing fixable issues as requiring "major revisions." I will articulate the case for rejection based on fundamental problems that cannot be addressed through revision without essentially rewriting the paper.

**The paper was submitted with no results.** Every empirical claim in this manuscript is a placeholder. The authors have submitted a template, not a research paper. The abstract promises to "quantify" noise effects and "identify regimes" of advantage, but provides no quantification or identification—only the promise of future values. This is not a minor formatting issue; it represents a submission of incomplete work. The review process exists to evaluate research findings, not research intentions. If we accept that placeholder submissions are reviewable, we undermine the scientific process. The appropriate response to an incomplete submission is desk rejection, not constructive feedback on methodology. The fact that three reviewers have engaged substantively with the theoretical framework should not obscure this fundamental deficiency.

**The theoretical contributions are not novel, and worse, they may be incorrect.** Reviewer 1 identified inconsistencies in the noise analysis (linear vs. square-root scaling) and the proof construction (IQP circuits vs. complete graph connectivity). Reviewer 2 noted that the effective dimension framework is a standard application of existing classical theory to quantum kernels. But beyond these issues, the core claim—that quantum kernels can exhibit exponential separation in effective dimension—rests on the assumption that the quantum kernel matrix eigenvalues have a specific distribution. The proof sketch invokes random matrix theory but does not verify that the IQP kernel construction satisfies the conditions required for those results. Random matrix universality typically requires either Gaussian entries or sufficient independence structure; the highly structured phase relationships in IQP kernels may violate these conditions. Without a rigorous proof (the full proof is promised in "Supplementary Information" which is not provided), this theorem is unverified.

**The experimental design cannot answer the stated research question.** The paper asks whether theoretical separations "translate to practical advantage on near-term hardware." To answer this question scientifically requires: (1) a problem instance where theoretical separation is proven to hold; (2) implementation of the specific circuit construction from the proof on hardware; (3) comparison to the specific classical baseline against which separation was proven. The manuscript does none of these. The synthetic parity dataset is "known to be hard for local classical kernels" but the RBF kernel is not local in the relevant sense—it has infinite-dimensional feature space. The theoretical separation (Theorem 1) is proven for IQP circuits, but the experimental implementation uses hardware-efficient ansatz with CNOT entanglement, not IQP diagonal gates. The disconnect between theory and experiment means the paper cannot draw conclusions about theory-practice gaps; it can only report empirical performance of ad-hoc quantum kernels versus ad-hoc classical baselines.

**The claimed hardware requirements are unverifiable and likely premature.** The manuscript promises to identify "concrete hardware requirements" for quantum advantage, but these requirements ($<$INSERT MEASURED VALUE$>$ fidelity, $<$INSERT MEASURED VALUE$>$ coherence time) are placeholders. More fundamentally, deriving hardware requirements from a small-scale experiment (presumably $\leq 27$ qubits on IBM Falcon processors) requires extrapolation assumptions that are not justified. How do the authors extrapolate from observed noise on 10-20 qubits to requirements for the $n \rightarrow \infty$ regime where theoretical separation holds? The scaling of correlated errors, crosstalk, and control imperfections is not linear in qubit count. Any hardware threshold derived from current experiments is at best a rough lower bound, and presenting such thresholds as "actionable benchmarks" overstates their reliability.

**Recommendation: Reject**

This manuscript represents incomplete work submitted prematurely. The theoretical contributions are incremental at best and potentially flawed. The experimental design does not connect to the theoretical claims. The complete absence of numerical results makes evaluation impossible. Revision cannot address these issues because they are not issues of presentation but of research completeness. The authors should complete their experiments, verify their proofs rigorously, and resubmit as a new manuscript.

---

## Voice 5 — Editor-in-Chief synthesis

Having reviewed all four assessments, I must reconcile substantive disagreements while maintaining the standards of npj Quantum Information. The Devil's Advocate raises the most severe concern—that this manuscript was submitted with placeholder values for all empirical results—which is indeed extraordinary and merits serious consideration.

I agree with the Devil's Advocate that submitting a manuscript with no numerical results is highly irregular. However, I interpret this as a draft submitted for structural and methodological feedback rather than a final submission. The journal's review process can accommodate this interpretation by conditioning acceptance on complete data, though this is unusual. The more substantive question is whether the underlying research design, if executed as described, would merit publication. Here, I find the reviews instructive but not uniformly negative.

Reviewer 1 identifies genuine errors that require correction: the inconsistency between noise scaling bounds (linear vs. square root), the disconnect between IQP constructions in proofs and complete-graph requirements in theorems, and the discrepancy between described (swap test) and implemented (sequential encoding) kernel estimation. These are significant but correctable issues. Reviewer 2's concerns about novelty are valid but perhaps overstated; while the theoretical contributions are incremental, the systematic experimental evaluation on hardware—if completed rigorously—would provide valuable empirical grounding for theoretical predictions. The field needs careful experimental studies that honestly characterize the gap between theory and practice. Reviewer 3's methodological critiques are the most constructive: incomplete ablations, missing failure mode analysis, and absent reproducibility infrastructure. These represent best practices that should be required for publication.

The Devil's Advocate's strongest point concerns the disconnect between theory and experiment. If the theoretical separation is proven for IQP circuits but experiments use hardware-efficient ansatz, the paper cannot claim to study the theory-practice gap for the proven separations. This is a fundamental design flaw. However, I note that the paper could be reframed as two contributions: (1) theoretical analysis of sufficient conditions for quantum kernel separation (which may be incremental but is technically sound if corrected); (2) empirical characterization of practical quantum kernel performance on near-term hardware (which is valuable independent of theoretical separation proofs). The current framing conflates these contributions, creating confusion.

**Final Verdict: Major Revisions**

This manuscript cannot be accepted in its current form but contains the skeleton of a publishable contribution. The decision to require major revisions rather than reject reflects my judgment that the methodological framework, if executed completely, would make a meaningful contribution to the literature. However, the revision requirements are extensive and non-negotiable.

**Must-fix before resubmission (ordered by severity):**

1. **Provide complete numerical results.** All placeholder values must be replaced with actual measured quantities. Submission with placeholders is not acceptable for peer review evaluation.

2. **Reconcile theoretical constructions with experimental implementations.** Either: (a) implement the IQP circuits from Theorem 1's proof on hardware and compare to the specific classical kernel against which separation is proven; or (b) clearly separate the theoretical contribution (separation conditions) from the empirical contribution (performance characterization of practical ansatze) without claiming the latter tests the former.

3. **Correct the noise analysis inconsistency.** Theorem 3 and its proof must present consistent scaling (linear or square root) with rigorous derivation.

4. **Clarify the kernel estimation protocol.** Reconcile the swap test description with the provided code, or replace with accurate description of the implemented method including correct probability-to-kernel formulas.

5. **Complete ablation study.** Systematically vary: encoding scheme, entanglement topology, circuit depth, shot budget, and error mitigation. Present full factorial results or justify reduced design.

6. **Add failure mode analysis.** Explicitly characterize problem and circuit features that predict quantum kernel failure. This section is required, not optional.

7. **Provide reproducibility infrastructure.** Complete code repository with: raw data files, analysis scripts that reproduce all figures and numbers, version-pinned environment specifications, and automated verification tests.

8. **Verify Theorem 1 rigorously.** Provide complete proof (not sketch) either in Methods or Supplementary Information, with explicit verification that IQP kernel matrices satisfy random matrix theory conditions invoked.

---

## Vote table

| Voice | Recommendation | Confidence 1-10 |
|---|---|---|
| Reviewer 1 | Major Revisions | 7 |
| Reviewer 2 | Major Revisions | 6 |
| Reviewer 3 | Major Revisions | 8 |
| Devil's Advocate | Reject | 8 |
| Editor-in-Chief | Major Revisions | 7 |