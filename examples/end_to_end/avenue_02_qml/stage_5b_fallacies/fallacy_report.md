# Logical Fallacy Audit: Quantum Kernel Methods Manuscript

## Section 1: Markdown Findings

---

**Fallacy:** cherry-picked-baseline  
**Severity:** high  
**Location:** Section "Classical Baselines" and "Results: Ideal versus Noisy Quantum Kernels"  
**Evidence:** "We compared against the following classical kernel methods: (i) Radial basis function (RBF) kernel... (ii) Polynomial kernel... (iii) Random Fourier features (RFF) kernel approximation... (iv) Classical simulation of ideal quantum kernel via statevector computation."  
**Why it's the fallacy:** The classical baselines are limited to standard kernel methods (RBF, polynomial, RFF) without including stronger published classical methods for the specific datasets tested. For parity-like tasks, classical neural networks with appropriate architecture (e.g., set functions or sparse parity learners) have been shown to perform well. For molecular property prediction, graph neural networks and transformer-based molecular models significantly outperform kernel SVMs. The authors cherry-pick weak classical baselines to inflate the apparent quantum advantage.  
**Suggested fix:** Include state-of-the-art classical methods for each specific task: neural network baselines for parity learning (e.g., sparse parity networks), GNNs or message-passing neural networks for molecular property prediction, and equivariant neural networks for symmetry datasets. Report performance of these alongside kernel methods.

---

**Fallacy:** conflated-regimes  
**Severity:** high  
**Location:** Theorem 1 and Discussion  
**Evidence:** "Then there exist data distributions $\mathcal{D}$ such that the quantum kernel effective dimension satisfies $d_{\text{eff}}^Q(\lambda) = \Omega(2^{n/2})$... These requirements represent a factor of $<$INSERT MEASURED VALUE$>\times$ improvement over current median device performance"  
**Why it's the fallacy:** The theoretical separation in Theorem 1 is proven for specific (possibly adversarial) data distributions and asymptotic regimes, but the experimental evaluation is conducted on small-scale systems ($n$ = small number of qubits) with practical datasets. The paper conflates the asymptotic exponential separation guarantee with finite-size experimental observations without rigorously quantifying how the theoretical advantage scales down to the tested regime.  
**Suggested fix:** Add explicit analysis of finite-size scaling: compute the theoretical effective dimension ratio for the actual qubit counts tested (e.g., n=5, 10, 15) and compare against the asymptotic prediction. Acknowledge that exponential separation may not manifest at small scales.

---

**Fallacy:** asymptotic-only-claim  
**Severity:** high  
**Location:** Theorem 1 (Exponential Separation in Effective Dimension)  
**Evidence:** "$d_{\text{eff}}^Q(\lambda) = \Omega(2^{n/2})$ for $\lambda = \mathcal{O}(1/\text{poly}(n))$, while any classical kernel computable in time $\text{poly}(n)$ has effective dimension $d_{\text{eff}}^C(\lambda) = \mathcal{O}(\text{poly}(n))$"  
**Why it's the fallacy:** The theorem establishes asymptotic scaling ($\Omega$, $\mathcal{O}$ notation) but the experiments are conducted at fixed, finite $n$ values. The claim of "exponential separation" is asymptotic—it does not guarantee any separation at the small $n$ values actually tested. The manuscript does not verify that the asymptotic regime has been reached in the experiments.  
**Suggested fix:** Either (1) provide explicit non-asymptotic bounds showing separation at the tested qubit counts, or (2) clearly state that the theorem provides asymptotic guarantees and the experiments serve only as preliminary validation at pre-asymptotic scales where separation may not yet manifest.

---

**Fallacy:** active-space-handwave  
**Severity:** medium  
**Location:** Discussion, Future Directions  
**Evidence:** "Development of problem-specific quantum feature maps that maximize the alignment between task structure and quantum kernel geometry while minimizing required circuit depth"  
**Why it's the fallacy:** The paper claims quantum kernels can achieve advantages on "structured classification tasks" but only tests three specific synthetic/semi-synthetic benchmarks. It then generalizes to future applicability without demonstrating or even attempting experiments on a broader class of real-world problems. The claim of generalizable advantage is handwaved rather than empirically tested.  
**Suggested fix:** Either (1) test on additional diverse real-world datasets to support generalization claims, or (2) explicitly scope the conclusions to the specific tested benchmarks and remove generalizing language like "structured classification tasks" without qualification.

---

**Fallacy:** hardware-irrelevant-comparison  
**Severity:** medium  
**Location:** Results Section, "Results: Ideal versus Noisy Quantum Kernels"  
**Evidence:** "ideal quantum kernels achieved test accuracy of $<$INSERT MEASURED VALUE$>$\%... compared to $<$INSERT MEASURED VALUE$>$\% for the best classical baseline"  
**Why it's the fallacy:** The paper compares ideal (noiseless simulator) quantum kernel performance against classical methods, then separately reports noisy hardware results. However, for the primary claims of quantum advantage, the comparison between ideal quantum kernels and classical baselines is misleading because the ideal quantum kernel is not achievable on any real hardware. The relevant comparison for practical advantage claims should be noisy quantum vs. classical, not ideal quantum vs. classical.  
**Suggested fix:** Restructure the results to make the noisy-hardware-vs-classical comparison the primary metric for advantage claims. Report ideal quantum results only as an upper bound to contextualize the noise-induced degradation, not as evidence of advantage.

---

**Fallacy:** hasty-generalization  
**Severity:** medium  
**Location:** Discussion  
**Evidence:** "Our finding that classification accuracy degrades sharply when $\Delta_\kappa$ exceeds approximately $<$INSERT MEASURED VALUE$>$ establishes a concrete target for hardware developers"  
**Why it's the fallacy:** The threshold is derived from experiments on only three datasets with specific structures. Generalizing this threshold as a universal hardware target for "quantum kernel methods" ignores that different datasets, encoding schemes, and tasks will have different sensitivity to kernel distortion. A single threshold from limited experiments does not establish a general hardware requirement.  
**Suggested fix:** Qualify the statement: "For the datasets and encoding schemes tested in this work, we observed that classification accuracy degrades sharply when $\Delta_\kappa$ exceeds approximately X. This threshold may vary for different task structures and feature maps."

---

**Fallacy:** circular-reasoning  
**Severity:** medium  
**Location:** Results Section, Synthetic Parity Dataset  
**Evidence:** "This confirms the theoretical expectation that parity-like functions align well with quantum kernel geometry."  
**Why it's the fallacy:** The synthetic parity dataset was specifically designed to be hard for local classical kernels and amenable to quantum representation. Using performance on this dataset as evidence that quantum kernels are advantageous for parity-like functions is circular: the dataset was constructed to demonstrate precisely this property. The "confirmation" is tautological.  
**Suggested fix:** Reframe: "As expected by construction, the synthetic parity dataset—designed to be hard for local classical kernels—shows strong performance with quantum kernels. This validates our implementation but does not constitute independent evidence of practical quantum advantage."

---

**Fallacy:** affirming-the-consequent  
**Severity:** medium  
**Location:** Connecting Theorems 1 and 2  
**Evidence:** "Theorems~\ref{thm:separation} and~\ref{thm:generalization} together establish that quantum kernels can achieve better generalization than classical kernels when the learning problem structure aligns with the quantum feature map geometry"  
**Why it's the fallacy:** The argument structure is: (1) high effective dimension can lead to better generalization, (2) quantum kernels can have high effective dimension, therefore (3) quantum kernels achieve better generalization. But having high effective dimension is not sufficient—the theorem bounds also depend on $\|\alpha\|_2^2$ and the margin $\gamma$. The conclusion that quantum kernels "achieve better generalization" does not follow without showing these other terms are favorable, which the paper does not demonstrate.  
**Suggested fix:** Add analysis showing that for the tested problems, the full generalization bound (including dual variable norms and margins) favors quantum kernels, not just the effective dimension term. Alternatively, weaken the claim to "may achieve better generalization under specific conditions on the dual variables and margins."

---

## Section 2: Machine-Readable JSON

```json
{
  "findings": [
    {
      "name": "cherry-picked-baseline",
      "category": "quantum-cs",
      "severity": "high",
      "location": "Section 'Classical Baselines' and 'Results: Ideal versus Noisy Quantum Kernels'",
      "evidence": "We compared against the following classical kernel methods: (i) Radial basis function (RBF) kernel... (ii) Polynomial kernel... (iii) Random Fourier features (RFF) kernel approximation... (iv) Classical simulation of ideal quantum kernel via statevector computation.",
      "suggested_fix": "Include state-of-the-art classical methods for each task: neural network baselines for parity learning, GNNs for molecular property prediction, and equivariant neural networks for symmetry datasets."
    },
    {
      "name": "conflated-regimes",
      "category": "quantum-cs",
      "severity": "high",
      "location": "Theorem 1 and Discussion",
      "evidence": "Then there exist data distributions $\\mathcal{D}$ such that the quantum kernel effective dimension satisfies $d_{\\text{eff}}^Q(\\lambda) = \\Omega(2^{n/2})$... These requirements represent a factor of $<$INSERT MEASURED VALUE$>\\times$ improvement over current median device performance",
      "suggested_fix": "Add finite-size scaling analysis computing theoretical effective dimension ratios at actual tested qubit counts and acknowledge exponential separation may not manifest at small scales."
    },
    {
      "name": "asymptotic-only-claim",
      "category": "quantum-cs",
      "severity": "high",
      "location": "Theorem 1 (Exponential Separation in Effective Dimension)",
      "evidence": "$d_{\\text{eff}}^Q(\\lambda) = \\Omega(2^{n/2})$ for $\\lambda = \\mathcal{O}(1/\\text{poly}(n))$, while any classical kernel computable in time $\\text{poly}(n)$ has effective dimension $d_{\\text{eff}}^C(\\lambda) = \\mathcal{O}(\\text{poly}(n))$",
      "suggested_fix": "Provide explicit non-asymptotic bounds at tested qubit counts, or clearly state theorem provides asymptotic guarantees only and experiments are preliminary validation at pre-asymptotic scales."
    },
    {
      "name": "active-space-handwave",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Discussion, Future Directions",
      "evidence": "Development of problem-specific quantum feature maps that maximize the alignment between task structure and quantum kernel geometry while minimizing required circuit depth",
      "suggested_fix": "Test on additional diverse real-world datasets or explicitly scope conclusions to the specific tested benchmarks without generalizing language."
    },
    {
      "name": "hardware-irrelevant-comparison",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Results Section, 'Results: Ideal versus Noisy Quantum Kernels'",
      "evidence": "ideal quantum kernels achieved test accuracy of $<$INSERT MEASURED VALUE$>$\\%... compared to $<$INSERT MEASURED VALUE$>$\\% for the best classical baseline",
      "suggested_fix": "Make noisy-hardware-vs-classical the primary comparison for advantage claims; report ideal quantum only as upper bound to contextualize noise degradation."
    },
    {
      "name": "hasty-generalization",
      "category": "general",
      "severity": "medium",
      "location": "Discussion",
      "evidence": "Our finding that classification accuracy degrades sharply when $\\Delta_\\kappa$ exceeds approximately $<$INSERT MEASURED VALUE$>$ establishes a concrete target for hardware developers",
      "suggested_fix": "Qualify that the threshold derives from only three specific datasets and may vary for different task structures and feature maps."
    },
    {
      "name": "circular-reasoning",
      "category": "general",
      "severity": "medium",
      "location": "Results Section, Synthetic Parity Dataset",
      "evidence": "This confirms the theoretical expectation that parity-like functions align well with quantum kernel geometry.",
      "suggested_fix": "Reframe as validation of implementation on a dataset constructed to favor quantum kernels, not independent evidence of practical advantage."
    },
    {
      "name": "affirming-the-consequent",
      "category": "general",
      "severity": "medium",
      "location": "Connecting Theorems 1 and 2",
      "evidence": "Theorems~\\ref{thm:separation} and~\\ref{thm:generalization} together establish that quantum kernels can achieve better generalization than classical kernels when the learning problem structure aligns with the quantum feature map geometry",
      "suggested_fix": "Add analysis showing full generalization bound (including dual variable norms and margins) favors quantum kernels, or weaken claim to 'may achieve better generalization under specific additional conditions.'"
    }
  ]
}
```