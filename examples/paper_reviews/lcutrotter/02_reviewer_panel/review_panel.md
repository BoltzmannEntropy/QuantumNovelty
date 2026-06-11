# Peer Review Panel: PRX Quantum Submission

## Paper: "Simple and high-precision Hamiltonian simulation by compensating Trotter error with linear combination of unitary operations"

---

## Voice 1 — Reviewer 1 (Physics correctness)

The manuscript presents a compelling theoretical framework for combining Trotter formulas with linear combination of unitaries (LCU) to achieve improved Hamiltonian simulation performance. From a physics correctness standpoint, the core mathematical construction appears sound. The authors correctly identify that the Kth-order Trotter remainder $V_K(x) = U(x)S_K(x)^\dagger$ satisfies the order condition $V_K(x) = I + O(x^{K+1})$, and their subsequent Taylor expansion and pairing strategy exploits this property appropriately. The use of Euler's formula (Eq. 7) to convert anti-Hermitian leading-order terms into Pauli rotations with suppressed 1-norm is mathematically elegant and correctly executed.

However, I have concerns regarding the treatment of specific physical Hamiltonians beyond the abstract lattice model. While the authors claim their method applies to "quantum chemistry Hamiltonians with large L," the paper provides no concrete analysis for molecular systems where the Hamiltonian structure differs significantly from the nearest-neighbor lattice models analyzed in detail. The nested-commutator bounds in Proposition 7 rely critically on the locality structure—specifically that $[H_{j,j+1}, H_{k,k+1}] = 0$ when $|j-k| > 1$. For electronic structure Hamiltonians in second quantization, the commutator structure is far more complex due to the non-local Coulomb integrals. The claim that "0th-order PTSC is particularly useful for quantum chemistry" (page 5) requires explicit verification beyond the $L$-dependence argument. The gate complexity $O(\lambda t)^2$ for 0th-order PTSC may be competitive for small $t$, but quantum chemistry simulations often require $t \sim 10^3$ for phase estimation, where the quadratic scaling becomes prohibitive.

The treatment of numerical precision is adequate for the theoretical framework but incomplete for practical implementation. The random-sampling implementation relies on Proposition 1, which bounds the estimation error as $|Ô - \langle O \rangle_V| \leq \|O\|(3\epsilon + \epsilon_n)$ with sample complexity $N = 2\mu^4 \ln(2/\delta)/\epsilon_n^2$. The $\mu^4$ prefactor when $\mu = 2$ implies a 16× overhead compared to standard sampling—this is stated but its implications for practical circuits deserve more attention. Furthermore, the truncation order $s_c$ in Eq. (48) and (76) introduces systematic bias that depends on $\lambda x$ and the specific Hamiltonian; the authors provide asymptotic bounds but no finite-precision error analysis for realistic parameter regimes.

The comparison with fourth-order Trotter in Fig. 8 is physically meaningful, but I note the comparison uses analytical bounds from Ref. [12] rather than empirical tight bounds. For the Heisenberg model, tighter commutator-aware bounds exist (Proposition M.1 in Ref. [20]), which the authors do use for the NCC comparison. The asymmetry in bound tightness between the PTSC and Trotter comparisons may overstate the PTSC advantage. Additionally, the "2 orders of magnitude" improvement claim for PTSC (Abstract) relies on comparing against analytical fourth-order Trotter bounds, which are known to be loose by factors of 10-100× in practice.

**Verdict: 7/10**

**Recommendation: minor-revisions**

**Questions for Authors:**
1. Can you provide explicit nested-commutator bounds for a molecular Hamiltonian (e.g., H₂ in STO-3G basis) to validate the claim that PTSC is "particularly useful for quantum chemistry"?
2. How does the systematic truncation error at finite $s_c$ compare to the statistical sampling error for realistic parameter choices?
3. Would tighter empirical Trotter bounds (rather than analytical bounds from Ref. [12]) change the claimed improvement factors in Fig. 8(a,b)?
4. What is the expected overhead for implementing the random sampling procedure on a fault-tolerant quantum computer with mid-circuit measurement and reset?

---

## Voice 2 — Reviewer 2 (Algorithmic novelty)

The central contribution of this manuscript—compensating Trotter error with LCU formulas through order-pairing techniques—represents a genuine algorithmic innovation in the Hamiltonian simulation literature. The key insight that anti-Hermitian leading-order Trotter remainder terms can be paired with the identity using Euler's formula to achieve 1-norm suppression from $1 + O((\lambda x)^{K+1})$ to $1 + O((\lambda x)^{2K+2})$ is novel and non-obvious. This effectively doubles the effective order of accuracy while maintaining the implementation simplicity of lower-order Trotter formulas.

Comparing against recent literature, this work should be contextualized against several relevant papers from 2023-2025. Hagan and Wiebe (Quantum 7, 1181, 2023) explored composite methods but did not achieve the order-pairing structure presented here. Cho, Berry, and Hsieh (Phys. Rev. A 109, 062431, 2024) developed randomized compensation techniques for Trotter errors, sharing conceptual similarities with the random-sampling implementation in Section II.D, but their approach does not achieve the commutator scaling that the NCC algorithm provides. The very recent work by Zhao et al. (Phys. Rev. Lett. 129, 270502, 2022) on time-dependent Hamiltonian simulation uses different techniques entirely. The authors correctly cite these works and distinguish their contributions, though the comparison with Ref. [47] (Cho et al.) deserves more explicit technical differentiation given the methodological overlap in using randomization to compensate Trotter errors.

The claimed complexity improvements in Table I represent legitimate Pareto improvements along specific dimensions. The PTSC algorithms achieve $\tilde{O}(\log(1/\epsilon))$ accuracy dependence (matching post-Trotter methods) while maintaining the $O(n^{1+1/(2K+1)})$ system-size scaling that improves upon the $O(n^2)$ of standard LCU/QSP methods for lattice Hamiltonians. The NCC algorithms achieve $O(\epsilon^{-1/(2K+1)})$ accuracy scaling with nearly-optimal $O(n^{1+2/(2K+1)})$ system-size dependence. These are not claimed as strict dominations across all dimensions—the authors honestly acknowledge trade-offs (e.g., PTSC has worse system-size dependence than Trotter for short times). The improvement ratios in Fig. 8(c) showing "3-4 orders of magnitude higher accuracy" are recomputable from the analytical bounds in Section V.

However, I question whether the claimed novelty fully accounts for the relationship with existing qDRIFT-type algorithms. The random-sampling implementation (Fig. 2) is essentially a structured variant of qDRIFT applied to the Trotter remainder. While the authors cite Refs. [33-35] appropriately, the distinction between their approach and Campbell's qDRIFT (Phys. Rev. Lett. 123, 2019) applied with Trotter pre-processing deserves explicit analysis. Specifically, what prevents one from running first-order Trotter followed by qDRIFT on the multiplicative error $V_K(x)$? The pairing technique provides the novel element, but the random-sampling infrastructure is inherited.

The algorithmic contribution is substantive but not transformative. The complexity improvements are incremental (polynomial factors) rather than asymptotic class changes. For lattice Hamiltonians, the practically relevant improvement is reducing gate counts by constant factors (the "2-4 orders of magnitude" claims) rather than improving scaling exponents from $O(n^{1.25})$ to $O(n^{1.2})$. The paper would be strengthened by explicit resource estimates for a specific target application (e.g., simulating a 100-qubit Heisenberg chain to chemical accuracy) comparing total T-gate counts across all methods.

**Verdict: 7/10**

**Recommendation: minor-revisions**

**Questions for Authors:**
1. How does your method compare to applying qDRIFT directly to the Trotter remainder $V_K(x)$ without the pairing technique? What is the quantitative advantage of pairing?
2. Can you provide an explicit resource comparison (T-gate counts, circuit depth) for a specific application benchmark such as simulating the Fermi-Hubbard model at half-filling?
3. The improvement from $O(t^{1+1/K})$ to $O(t^{1+1/(2K+1)})$ is less significant at high orders—is there an optimal $K$ for practical implementations?
4. For the coherent implementation (Appendix H), how do the ancilla qubit requirements compare to standard QSP implementations?

---

## Voice 3 — Reviewer 3 (Empirical evidence)

The empirical evidence presented in this manuscript is primarily analytical rather than numerical, which is appropriate for the theoretical nature of the contribution but raises questions about practical validation. The main numerical results appear in Fig. 8, which compares gate counts based on analytical bounds rather than explicit circuit compilation. While this approach is standard in complexity-theoretic Hamiltonian simulation papers, it limits the ability to verify the claimed improvements in practice.

The gate counting methodology in Section II.E and Fig. 8 requires scrutiny. The authors state they "compile their quantum circuits to CNOT gates, single-qubit Clifford gates, and single-qubit Z-axis rotation gates $R_z(\theta)$" and count $R_z$ gates as the resource metric. However, the actual circuit structure for the random-sampling implementation differs from standard Trotter circuits. The controlled-Pauli and controlled-Pauli-rotation gates in Fig. 11 require decomposition that depends on the sampled Pauli weight, which is a random variable. The claimed gate counts should therefore be expected values over the sampling distribution, but the authors do not explicitly compute these expectations—they bound the worst-case Pauli weight by $O(s_c)$. For PTSC with $s_c \sim \log(1/\epsilon)/\log\log(1/\epsilon)$, this introduces logarithmic factors that may not be negligible. A proper empirical validation would sample many random instances and report the distribution of gate counts.

The comparison with fourth-order Trotter uses bounds from Ref. [12] (analytical) and Ref. [20] (commutator-aware), but these represent different tightness levels. The PTSC comparison in Fig. 8(a,b) uses Ref. [12], while the NCC comparison in Fig. 8(c) uses Ref. [20]. This asymmetry is disclosed but complicates interpretation. An honest comparison would use the tightest available bounds for all methods. Furthermore, the y-axis label "Rz Gate" conflates different gate definitions: for Trotter, these are deterministic $R_z$ gates in the circuit; for Trotter-LCU, these include random Pauli rotations whose angles depend on the LCU formula parameters. The resource overhead of computing these angles classically is not accounted for.

The paper lacks statistical analysis appropriate for numerical claims. The "2 orders of magnitude" and "3-4 orders of magnitude" improvement claims are point estimates from analytical formulas, not sample statistics with confidence intervals. While this is common in theoretical papers, the claims would be strengthened by: (1) implementing the sampling procedure in Algorithm 1 and verifying the claimed distribution over Pauli operators; (2) running explicit simulations of small systems (e.g., 4-6 qubits) to verify that the LCU formulas achieve the claimed approximation errors; (3) reporting variance in gate counts across different random samples. The absence of any failure mode analysis or honest-negatives section is notable—the paper does not discuss scenarios where Trotter-LCU might underperform, such as when $\lambda t$ is small or when the Hamiltonian has non-local structure.

The Heisenberg model numerical example in Fig. 8(c) and Algorithm 1 provides the most concrete validation. Algorithm 1 is explicit enough to be reproduced, and the parameter choices ($\theta := \tan^{-1}(16nx^2(1+24x))$) can be verified against the analytical formulas. However, the paper does not report any actual execution of this algorithm—it remains a specification rather than an implementation. An accompanying code repository with scripts to regenerate Fig. 8 would substantially strengthen the empirical contribution.

**Verdict: 6/10**

**Recommendation: major-revisions**

**Questions for Authors:**
1. Can you provide code or pseudocode that reproduces the gate counts in Fig. 8 from the analytical formulas?
2. What is the expected Pauli weight distribution for the sampled operators in Algorithm 1, and how does this affect the average gate count?
3. Have you implemented the sampling procedure and verified the claimed LCU approximation errors on small systems?
4. Under what conditions (e.g., short times, highly non-local Hamiltonians) does your method underperform compared to standard Trotter or QSP?

---

## Voice 4 — Devil's Advocate

This paper should be rejected or require major revisions due to several fundamental issues that the other reviewers have treated too charitably.

**The claimed improvements are primarily artifacts of comparison methodology, not genuine algorithmic advances.** The "2 orders of magnitude" improvement in Fig. 8(a,b) compares PTSC against the *analytical* fourth-order Trotter bound from Ref. [12], which is known to be extremely loose. Childs et al. (Ref. [20]) explicitly demonstrate that commutator-aware bounds can be orders of magnitude tighter. When the authors switch to commutator-aware bounds for the NCC comparison in Fig. 8(c), the improvement shrinks to "3-4 orders of magnitude *in accuracy*"—which means achieving $\epsilon = 10^{-6}$ instead of $10^{-3}$ with the same gate count. But this comparison uses second-order NCC against fourth-order Trotter; a fair comparison would use fourth-order NCC (if the analysis were tractable, which the authors admit it is not: "We leave precise higher-order NCC gate count analysis for future study"). The paper's headline claims are thus based on asymmetric comparisons that systematically favor the new method.

**The random-sampling implementation has hidden costs that undermine the complexity claims.** Proposition 1 states that random-sampling LCU requires $N = O(\mu^4/\epsilon_n^2)$ samples. With $\mu = 2$ (as used in the numerical comparisons), this is a 16× overhead that the authors acknowledge but downplay. More critically, the sampling procedure in Fig. 5 and Algorithm 2 requires *classical* computation of multinomial distributions, Pauli products, and angle parameters that scale with the system size and truncation order. The claimed gate complexity $O((λt)^{1+1/(2K+1)}(\kappa_K L + \log(1/\epsilon)/\log\log(1/\epsilon)))$ (Theorem 1) counts only quantum gates, ignoring the classical preprocessing cost. For the NCC algorithm, the space cost is $O(K\kappa)$ and time cost is $O(K(\log\kappa + \log n))$ per sample (Appendix D), but with $\kappa = 2 \times 5^{K/2-1}$ for $K = 2k$, this grows exponentially in $K$. The fourth-order NCC algorithm would have $\kappa = 10$, making the classical sampling overhead non-negligible for large systems.

**The nested-commutator compensation lacks practical implementation details.** The NCC algorithm requires computing the explicit nested-commutator expansion of the Trotter remainder, which involves exponentially many terms (see Eq. (C17)). The "padding" technique in Section II.D and Fig. 6 introduces virtual ancilla qubits and zero-valued commutators to achieve uniform sampling, but the overhead of this padding is not quantified. For the first-order Heisenberg example (Algorithm 1), the structure is simple, but extending to higher orders or more complex Hamiltonians requires case-by-case analysis that the authors have not completed. The claim that NCC is "easy to implement" (Table I) is misleading for practical implementations.

**The paper lacks honest acknowledgment of failure modes.** The method *requires* $\lambda x < 1/(2\lambda)$ (Proposition 3) for the Taylor expansion to converge, which constrains the minimum segment number $\nu \geq 2\lambda t$. For long-time simulations ($t \sim 10^3$) of large systems ($\lambda \sim n$), this requires $\nu \sim 2000n$ segments, each involving random sampling. The variance of random-sampling estimators grows with the number of sequential samples, introducing error accumulation that is not analyzed. The paper also does not discuss the practical challenge of implementing mid-circuit measurement and reset (Fig. 2(c)) on current fault-tolerant architectures, which may introduce significant overhead.

**Recommendation: major-revisions**

The paper contains a valid theoretical contribution (the order-pairing technique) buried under overstated claims and incomplete analysis. To merit publication in PRX Quantum, the authors must: (1) provide symmetric comparisons using the tightest available bounds for all methods; (2) quantify the classical preprocessing and sampling overhead; (3) implement the algorithms on small systems to validate the theoretical claims; (4) honestly discuss failure modes and parameter regimes where the method underperforms.

---

## Voice 5 — Editor-in-Chief synthesis

Having reviewed all four assessments, I find substantive merit in the theoretical contribution alongside legitimate concerns about the empirical validation and comparison methodology. The Devil's Advocate raises valid points that require response, though some criticisms are more central than others.

The core theoretical contribution—using Euler's formula to pair anti-Hermitian Trotter remainder terms with the identity, thereby doubling the effective order of 1-norm suppression—is novel and mathematically sound. Reviewers 1 and 2 agree on this point. The resulting complexity improvements in Table I represent genuine (if incremental) advances: PTSC achieves logarithmic accuracy dependence while maintaining sub-quadratic system-size scaling for structured Hamiltonians, and NCC achieves better-than-Trotter accuracy scaling with commutator-aware system-size bounds. These are valuable contributions to the Hamiltonian simulation toolkit.

However, the Devil's Advocate correctly identifies that the comparison methodology is asymmetric and potentially misleading. The "2 orders of magnitude" headline claim compares PTSC against loose analytical Trotter bounds, while the NCC comparison uses tighter commutator-aware bounds. This inconsistency must be addressed before publication. Additionally, Reviewer 3's concern about the lack of numerical implementation is well-founded—for a paper claiming practical improvements of multiple orders of magnitude, some empirical validation beyond analytical bounds is expected, even for a theory-focused venue like PRX Quantum.

The classical preprocessing overhead raised by the Devil's Advocate (exponential in $K$ for NCC due to $\kappa = 2 \times 5^{K/2-1}$) is a legitimate concern for high-order implementations, but the paper primarily advocates for low-order methods (first or second order) where $\kappa \leq 2$. The authors should clarify this limitation explicitly. The 16× sampling overhead ($\mu^4$ with $\mu=2$) is disclosed and is the cost of the random-sampling implementation; the coherent implementation in Appendix H avoids this overhead at the cost of more complex circuits.

Regarding Reviewer 1's questions about quantum chemistry applications: the paper should either provide explicit analysis for molecular Hamiltonians or remove the claim that PTSC is "particularly useful" for this setting. The lattice Hamiltonian analysis is thorough; extending claims beyond this domain requires comparable rigor.

**Final Verdict: minor-revisions**

The paper presents a valid and novel algorithmic contribution suitable for PRX Quantum, but requires revisions to address methodological concerns before acceptance.

**Must-fix items before resubmission (ordered by severity):**

1. **Symmetric comparison methodology:** Regenerate Fig. 8(a,b) using commutator-aware Trotter bounds (Ref. [20] methodology) rather than loose analytical bounds from Ref. [12], or provide explicit justification for why the looser bounds are appropriate.

2. **Quantify classical overhead:** Add a subsection or paragraph explicitly stating the classical preprocessing cost (space and time) for the sampling procedures, particularly noting how $\kappa$ scales with Trotter order $K$ and the implications for practical implementations.

3. **Remove or substantiate quantum chemistry claims:** Either provide explicit nested-commutator bounds for a molecular Hamiltonian or remove the claim that PTSC is "particularly useful for quantum chemistry" (Section II.B).

4. **Add failure modes discussion:** Include a paragraph discussing parameter regimes where Trotter-LCU underperforms (e.g., short simulation times, highly non-local Hamiltonians, small accuracy requirements where the sampling overhead dominates).

5. **Provide reproducibility resources:** Include code or detailed pseudocode sufficient to reproduce the gate counts in Fig. 8, or commit to providing a code repository upon acceptance.

6. **Clarify comparison with qDRIFT:** Add explicit analysis distinguishing the pairing technique from simply applying qDRIFT to the Trotter remainder, including quantitative comparison if possible.

---

## Vote table

| Voice | Recommendation | Confidence 1-10 |
|---|---|---|
| Reviewer 1 | minor-revisions | 7 |
| Reviewer 2 | minor-revisions | 7 |
| Reviewer 3 | major-revisions | 6 |
| Devil's Advocate | major-revisions | 8 |
| Editor-in-Chief | minor-revisions | 7 |