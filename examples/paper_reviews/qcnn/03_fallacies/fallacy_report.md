## Section 1: Markdown Findings

**Fallacy:** cherry-picked-baseline
**Severity:** medium
**Location:** Section IV.A, paragraph introducing quantum datasets: "Notably, the classical, weight-truncated QCNN is self-consistently trained to solve the classification tasks, not to faithfully emulate the training of an exact QCNN."
**Why it's the fallacy:** The authors explicitly state they are not comparing their classical surrogate against a faithfully trained QCNN but rather training their classical model directly on the task. This setup avoids the harder comparison of whether their surrogate can match a QCNN that has been optimally trained with full quantum resources. By training the surrogate "self-consistently" rather than benchmarking against the best possible QCNN performance, they sidestep a stronger baseline comparison.
**Suggested fix:** Include explicit comparisons where a QCNN is trained with sufficient shots and optimization iterations to reach its best achievable accuracy, then compare the classical surrogate's accuracy against this optimized QCNN performance on the same datasets.

---

**Fallacy:** conflated-regimes
**Severity:** medium
**Location:** Section V, Discussion: "While we focus here on the two most popular instantiations of QCNNs used in the literature (one-dimensional tracing out and measurement-based architectures), it is clear that these are the easiest to classically simulate. One could, for instance, envision QCNNs in two or more dimensions, as well as more exotic topologies."
**Why it's the fallacy:** The authors acknowledge their results apply specifically to one-dimensional QCNNs but then make broad claims throughout the paper about QCNN simulability in general. The title "Quantum Convolutional Neural Networks are Effectively Classically Simulable" and bold claims like "There is currently no evidence that QCNNs will work on classically non-trivial tasks" extrapolate from the 1D case to all QCNNs without demonstrating results for higher-dimensional or more complex topologies.
**Suggested fix:** Modify the title to "One-Dimensional Quantum Convolutional Neural Networks are Effectively Classically Simulable" and qualify all general statements about QCNNs to explicitly state they apply only to the 1D architectures studied.

---

**Fallacy:** active-space-handwave
**Severity:** medium
**Location:** Section V, Discussion: "We strongly believe that the techniques introduced here can serve as blueprints to classically simulate other architectures."
**Why it's the fallacy:** The authors claim their techniques generalize to other quantum neural network architectures without actually running experiments or providing rigorous proofs for these other architectures. The phrase "we strongly believe" signals speculation rather than demonstrated results. This constitutes handwaving about generalization capability without empirical validation.
**Suggested fix:** Either remove claims about generalization to other architectures or include explicit experimental results demonstrating classical simulation of at least one additional architecture type beyond QCNNs.

---

**Fallacy:** hasty-generalization
**Severity:** medium
**Location:** Section IV.B, Classical datasets conclusion: "Concomitantly, this implies that using QCNN-based QML schemes for classical data appears to be an ill-motivated task."
**Why it's the fallacy:** The authors tested only four classical datasets (MNIST, Fashion-MNIST, EuroSAT, GTSRB) with specific encoding schemes and conclude that QCNNs are "ill-motivated" for all classical data. This sweeping conclusion is drawn from a limited sample that does not represent the full diversity of classical data classification problems or encoding strategies.
**Suggested fix:** Qualify the conclusion to state: "For the classical datasets and encoding schemes tested in this work, QCNN-based approaches appear to offer no advantage over classical simulation. Whether this extends to all classical data problems remains an open question."

---

**Fallacy:** cherry-picked-baseline
**Severity:** medium
**Location:** Section IV.A.3, ANNNI model: "Thus we can reach similar results to those obtained in the literature, at a much smaller measurement budget."
**Why it's the fallacy:** The comparison claims to match "results obtained in the literature" but does not specify which literature results are being compared against, what their experimental conditions were, or whether those prior results used optimized QCNN configurations. Without explicit citations and controlled comparisons, this claim of matching performance lacks rigor.
**Suggested fix:** Add explicit citations to the specific prior QCNN results being compared against, including their reported accuracies, number of measurements used, and experimental conditions, then present a direct numerical comparison table.

---

**Fallacy:** asymptotic-only-claim
**Severity:** medium
**Location:** Section IV.A.1, XXX model: "To our knowledge, this constitutes the largest QCNN implementation with classical shadows"
**Why it's the fallacy:** While the authors demonstrate 1024 qubits, they use this finite-N demonstration to support broader claims about QCNN simulability without acknowledging potential scaling issues. The complexity analysis in Appendix E showing χ ~ n^8 bond dimension scaling means simulation cost scales as O(n^24), which could become intractable at larger scales despite the polynomial label.
**Suggested fix:** Include explicit discussion of the scaling limitations, noting that while n=1024 is achievable, the O(n^24) cost scaling means practical limits exist, and specify the largest system size that remains tractable on available hardware.

---

**Fallacy:** pareto-cherry-picked-axes
**Severity:** medium
**Location:** Table I and Section IV.B: "In Table I we show results for all the classification tasks considered. Here we can see that the simulated QCNN result in high test accuracies (showing best out 5 independent runs), comparable to, and even larger than, those found in the literature."
**Why it's the fallacy:** By reporting "best out of 5 independent runs" rather than mean ± standard deviation, the authors cherry-pick the most favorable outcome along the accuracy axis. This selection bias inflates apparent performance by ignoring variability across runs.
**Suggested fix:** Report mean accuracy ± standard deviation across all 5 runs for each dataset and encoding combination, not just the best single run.

```json
{
  "findings": [
    {
      "name": "cherry-picked-baseline",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section IV.A, paragraph on quantum datasets",
      "evidence": "Notably, the classical, weight-truncated QCNN is self-consistently trained to solve the classification tasks, not to faithfully emulate the training of an exact QCNN.",
      "suggested_fix": "Include explicit comparisons where a QCNN is trained with sufficient shots and optimization iterations to reach its best achievable accuracy, then compare the classical surrogate's accuracy against this optimized QCNN performance on the same datasets."
    },
    {
      "name": "conflated-regimes",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section V, Discussion",
      "evidence": "While we focus here on the two most popular instantiations of QCNNs used in the literature (one-dimensional tracing out and measurement-based architectures), it is clear that these are the easiest to classically simulate. One could, for instance, envision QCNNs in two or more dimensions, as well as more exotic topologies.",
      "suggested_fix": "Modify the title to 'One-Dimensional Quantum Convolutional Neural Networks are Effectively Classically Simulable' and qualify all general statements about QCNNs to explicitly state they apply only to the 1D architectures studied."
    },
    {
      "name": "active-space-handwave",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section V, Discussion",
      "evidence": "We strongly believe that the techniques introduced here can serve as blueprints to classically simulate other architectures.",
      "suggested_fix": "Either remove claims about generalization to other architectures or include explicit experimental results demonstrating classical simulation of at least one additional architecture type beyond QCNNs."
    },
    {
      "name": "hasty-generalization",
      "category": "general",
      "severity": "medium",
      "location": "Section IV.B, Classical datasets conclusion",
      "evidence": "Concomitantly, this implies that using QCNN-based QML schemes for classical data appears to be an ill-motivated task.",
      "suggested_fix": "Qualify the conclusion to state: 'For the classical datasets and encoding schemes tested in this work, QCNN-based approaches appear to offer no advantage over classical simulation. Whether this extends to all classical data problems remains an open question.'"
    },
    {
      "name": "cherry-picked-baseline",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section IV.A.3, ANNNI model",
      "evidence": "Thus we can reach similar results to those obtained in the literature, at a much smaller measurement budget.",
      "suggested_fix": "Add explicit citations to the specific prior QCNN results being compared against, including their reported accuracies, number of measurements used, and experimental conditions, then present a direct numerical comparison table."
    },
    {
      "name": "asymptotic-only-claim",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section IV.A.1, XXX model and Appendix E",
      "evidence": "To our knowledge, this constitutes the largest QCNN implementation with classical shadows",
      "suggested_fix": "Include explicit discussion of the scaling limitations, noting that while n=1024 is achievable, the O(n^24) cost scaling means practical limits exist, and specify the largest system size that remains tractable on available hardware."
    },
    {
      "name": "pareto-cherry-picked-axes",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Table I and Section IV.B",
      "evidence": "In Table I we show results for all the classification tasks considered. Here we can see that the simulated QCNN result in high test accuracies (showing best out 5 independent runs), comparable to, and even larger than, those found in the literature.",
      "suggested_fix": "Report mean accuracy ± standard deviation across all 5 runs for each dataset and encoding combination, not just the best single run."
    }
  ]
}
```