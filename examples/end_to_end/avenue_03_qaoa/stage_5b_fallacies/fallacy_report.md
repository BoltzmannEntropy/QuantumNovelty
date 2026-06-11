## Section 1: Markdown Findings

**Fallacy:** hardware-irrelevant-comparison  
**Severity:** high  
**Location:** Abstract / final sentence  
**Evidence:** “the crossover regime where quantum hardware constraints and classical simulation costs become comparable.”  
**Why it's the fallacy:** The manuscript is explicitly based on noiseless classical simulations, yet it frames the calibrated regime as one where “quantum hardware constraints” and classical simulation costs are comparable. No hardware backend, calibration data, noise model, compilation result, or device-specific error budget is supplied. This imports hardware relevance from simulator cost alone.  
**Suggested fix:** Replace with: “the crossover regime where exact classical simulation remains feasible but becomes costly under the stated simulator and optimizer workflow.” Reserve hardware comparisons for a separate section with calibrated noise and compilation data.

**Fallacy:** conflated-regimes  
**Severity:** medium  
**Location:** Abstract / contribution framing  
**Evidence:** “an experimentally reproducible map of how QAOA depth purchases approximation quality in the crossover regime where quantum hardware constraints and classical simulation costs become comparable.”  
**Why it's the fallacy:** The manuscript conflates an empirical simulator boundary with a quantum-classical hardware boundary. A region where exact simulation becomes expensive is not automatically a regime where quantum hardware constraints are comparable or scientifically matched.  
**Suggested fix:** Define two separate regimes: “simulator calibration boundary” and “hardware execution regime.” State that this draft only studies the former unless hardware data are added.

**Fallacy:** cherry-picked-baseline  
**Severity:** medium  
**Location:** Results / Comparison with named classical baselines  
**Evidence:** “The best QAOA depth that exceeds the selected classical baseline by the pre-registered margin is \texttt{<INSERT MEASURED VALUE>}.”  
**Why it's the fallacy:** The claim is organized around a “selected classical baseline” rather than the strongest applicable published or implemented comparator for random 3-regular MaxCut. Even though the manuscript mentions an augmented catalog, the current wording permits choosing a weaker comparator and reporting exceedance against it.  
**Suggested fix:** Replace with: “We report QAOA against every baseline in the pre-registered suite and identify whether it exceeds the strongest applicable baseline under the stated resource model.”

**Fallacy:** pareto-cherry-picked-axes  
**Severity:** medium  
**Location:** Results / Comparison with named classical baselines / table caption  
**Evidence:** “The final manuscript should specify whether budgets are matched by wall-clock time, oracle calls, objective evaluations, or another pre-registered resource.”  
**Why it's the fallacy:** The manuscript allows the comparison axis to remain undecided. QAOA may look favorable under one budget axis and unfavorable under another, so leaving the resource axis open enables domination claims on a selectively chosen subset of axes.  
**Suggested fix:** Pre-register all comparison axes before reporting results: wall-clock, objective evaluations, memory, shots or samples, optimizer restarts, and implementation details. Report paired outcomes on all relevant axes.

**Fallacy:** simulator-laundering  
**Severity:** medium  
**Location:** Methods / QAOA simulation  
**Evidence:** “The primary simulations use \texttt{<INSERT SIMULATOR NAME>} in exact statevector mode… For validation at selected sizes, we compare against a QuTiP reference implementation.”  
**Why it's the fallacy:** The draft risks using one backend for main results and another for validation while treating agreement on selected small cases as general validation of the full simulation workflow. Backend agreement on small instances does not validate optimizer behavior, scaling, memory behavior, or large-instance numerical stability.  
**Suggested fix:** State exactly what the QuTiP validation certifies: “QuTiP validation checks small-instance expectation values only; all scaling, optimizer, and boundary claims are tied solely to the primary simulator.”

## Section 2: Machine-Readable JSON

```json
{
  "findings": [
    {
      "name": "hardware-irrelevant-comparison",
      "category": "quantum-cs",
      "severity": "high",
      "location": "Abstract / final sentence",
      "evidence": "the crossover regime where quantum hardware constraints and classical simulation costs become comparable.",
      "suggested_fix": "Replace with: \"the crossover regime where exact classical simulation remains feasible but becomes costly under the stated simulator and optimizer workflow.\" Reserve hardware comparisons for a separate section with calibrated noise and compilation data."
    },
    {
      "name": "conflated-regimes",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Abstract / contribution framing",
      "evidence": "an experimentally reproducible map of how QAOA depth purchases approximation quality in the crossover regime where quantum hardware constraints and classical simulation costs become comparable.",
      "suggested_fix": "Separate the simulator calibration boundary from any hardware execution regime. State that this draft only studies the simulator boundary unless calibrated hardware or noise-model data are added."
    },
    {
      "name": "cherry-picked-baseline",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Results / Comparison with named classical baselines",
      "evidence": "The best QAOA depth that exceeds the selected classical baseline by the pre-registered margin is \\texttt{<INSERT MEASURED VALUE>}.",
      "suggested_fix": "Report QAOA against every baseline in the pre-registered suite and identify whether it exceeds the strongest applicable baseline under the stated resource model."
    },
    {
      "name": "pareto-cherry-picked-axes",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Results / Comparison with named classical baselines / table caption",
      "evidence": "The final manuscript should specify whether budgets are matched by wall-clock time, oracle calls, objective evaluations, or another pre-registered resource.",
      "suggested_fix": "Pre-register all comparison axes before reporting results: wall-clock, objective evaluations, memory, samples or shots, optimizer restarts, and implementation details. Report paired outcomes on all relevant axes."
    },
    {
      "name": "simulator-laundering",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Methods / QAOA simulation",
      "evidence": "The primary simulations use \\texttt{<INSERT SIMULATOR NAME>} in exact statevector mode. The statevector is initialized as $\\ket{+}^{\\otimes n}$, cost phases are applied in the computational basis, and mixer phases are applied as tensor products of single-qubit $X$ rotations. For validation at selected sizes, we compare against a QuTiP reference implementation.",
      "suggested_fix": "State exactly what the QuTiP validation certifies: small-instance expectation-value agreement only. Do not use it to validate optimizer behavior, scaling, boundary placement, or large-instance numerical stability."
    }
  ]
}
```