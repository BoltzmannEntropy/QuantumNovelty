## Section 1: Markdown Findings

**Fallacy:** cherry-picked-baseline
**Severity:** high
**Location:** Section 1 (Introduction), paragraph 2 and throughout
**Evidence:** "In earlier Al-based devices, we observed typical top quintile gaps of ∆T ∼ 30 µeV [59–61]. In contrast, in the InAs–Pb devices studied here we observe a top quintile gap of ∆T ∼ 70 µeV."
**Why it's the fallacy:** The manuscript exclusively compares its Pb-based devices against the authors' own earlier Al-based devices from their own lab (refs 59-61). While refs 53-56 mention other groups' Pb-based nanowire work, the paper dismisses this prior art with the vague claim that they have "gone beyond previous work which has incorporated larger gap superconductors into nanowire devices [53–56]" without providing any quantitative comparison of topological gaps, parity lifetimes, or other metrics against these published baselines. This selective comparison against only weaker internal baselines while ignoring potentially stronger external results constitutes cherry-picking.
**Suggested fix:** Add a table comparing quantitative metrics (∆T, parity lifetime, EM) against the specific results from refs 53-56 and any other relevant Pb-based or high-gap superconductor nanowire studies. If those studies didn't report comparable metrics, state this explicitly.

---

**Fallacy:** hasty-generalization
**Severity:** medium
**Location:** Section 4 (Interferometric Parity Readout), paragraph on parity lifetime
**Evidence:** "To quantify the lifetime we classify the data by fitting a Gaussian mixture model... By aggregating multiple measurements, we observe a total of N = 324 dwell intervals. The data are consistent with a single exponential distribution... We extract a characteristic parity lifetime and corresponding fit uncertainty of τZ = 22 ± 1 s"
**Why it's the fallacy:** The 20+ second parity lifetime claim—which is the paper's headline result—is derived from measurements on a single nanowire of a single tetron in a single device. The abstract and conclusions generalize this to "InAs–Pb tetron devices" broadly, but there is no demonstration that this result is reproducible across multiple devices, multiple tetrons, or even multiple wires within the same device. The measurement also appears to be taken at a specific optimized operating point (Vwp = −1.365 13 V).
**Suggested fix:** Either present parity lifetime statistics from multiple devices/tetrons/wires, or qualify claims to state "In a single nanowire of one tetron, we measured..." and explicitly note this as a demonstration requiring broader validation.

---

**Fallacy:** conflated-regimes
**Severity:** medium
**Location:** Section 5 (Discussion and Outlook), final paragraphs
**Evidence:** "The multi-tetron array presented here functions as a modular 'unit cell' for a larger architecture; it can be tiled into much larger qubit arrays (e.g., a 12-qubit array) without altering the underlying control or readout approach. The strong parity protection observed in our tetron prototype suggests that, even as the system scales up, each qubit will remain well isolated from non-equilibrium quasiparticles"
**Why it's the fallacy:** The paper extrapolates from a single tetron measurement (one wire, one parity lifetime measurement) to claims about how a 12-qubit array would behave. This conflates the regime of a single isolated device with the regime of scaled arrays where crosstalk, thermal load from additional control lines, and other scaling-specific noise sources may dominate. No evidence is provided that scaling preserves these properties.
**Suggested fix:** Reframe as: "Demonstrating similar performance in scaled arrays remains an important open challenge. Potential scaling concerns include [list specific concerns] which will require investigation in multi-qubit devices."

---

**Fallacy:** active-space-handwave
**Severity:** medium
**Location:** Section 5 (Discussion and Outlook)
**Evidence:** "Looking ahead, the values of EM achieved here are expected to have beneficial implications for Pauli-X measurements, whose characteristic switching time τX scales as EM². Deep in the topological regime, EM ∼ ∆T exp(−L/ξT)... Increasing the NW length L exponentially suppresses EM and thus dramatically extends τX, which suggests that τX could be more than an order of magnitude longer than in previous devices."
**Why it's the fallacy:** The paper claims that τX "could be more than an order of magnitude longer" based on theoretical scaling arguments, but does not actually perform X-parity measurements or demonstrate this. The claim of generalizing to X measurements is made without running the experiment, which constitutes an active-space handwave—claiming a result extends to a regime not actually tested.
**Suggested fix:** Remove the speculative quantitative claim ("more than an order of magnitude") or qualify it as: "Based on theoretical scaling relations, we predict τX improvements, but experimental validation of X-parity lifetimes in Pb-based devices remains for future work."

---

**Fallacy:** ad-hoc-precision-floor
**Severity:** medium
**Location:** Section 3 (RF-Based Wire Spectroscopy), discussion of EM resolution
**Evidence:** "we expect the resolution of this analysis to be limited to ∼ 1 µeV... Notably, the resolution of ∼ 1 µeV significantly exceeds that of conductance measurements which can resolve EM of about the half-width-half-max of a temperature broadened conductance peak EM ∼ 1.76kB T ≈ 7.6 µeV for T = 50 mK."
**Why it's the fallacy:** The paper claims EM values "below our ∼ 1 µeV resolution" as evidence of topological behavior, but this resolution floor is derived from DAC resolution and lever arm estimates, not from demonstrated noise floors or calibration standards. The comparison to "7.6 µeV" for conductance measurements also involves mixing different measurement modalities and conditions without rigorous cross-calibration. Claiming sub-resolution EM values as a positive result approaches the ad-hoc-precision-floor fallacy.
**Suggested fix:** Provide explicit calibration of the 1 µeV resolution claim with known energy scales, or reframe as: "We observe EM consistent with zero within our measurement resolution of approximately 1 µeV, though we cannot exclude finite EM below this threshold."

---

**Fallacy:** appeal-to-authority
**Severity:** medium
**Location:** Section 1 (Introduction), opening paragraph
**Evidence:** "Recently, we presented a roadmap [1] to fault-tolerant quantum computation using topological qubits [2–4] built around Majorana zero modes (MZMs) in superconductor-semiconductor hybrid devices [5–9]. Our roadmap draws on concepts explored in Refs. 10–39."
**Why it's the fallacy:** The paper opens by citing 39 references in the first paragraph, with 30 of them (refs 10-39) bundled into a single "draws on concepts" citation. This mass citation serves more as an appeal to the authority and weight of the cited literature than as specific technical justification. The roadmap ref [1] is the authors' own prior publication, creating a self-referential authority structure.
**Suggested fix:** Cite specific concepts from specific papers where they are used technically, rather than bundling 30 references as general background authority. If a roadmap citation is needed, briefly state which specific elements are being implemented.

---

**Fallacy:** equivocation
**Severity:** medium
**Location:** Throughout, particularly Abstract and Section 4
**Evidence:** Abstract: "parity lifetime of ∼ 20 s with some instances reaching minute-scale"; Section 4: "intrinsic Z-parity lifetime of the device which far exceeds the measurement time"
**Why it's the fallacy:** The paper uses "parity lifetime" to refer to multiple related but distinct quantities: (1) Z-parity lifetime in an interference measurement, (2) quasiparticle poisoning time, and (3) intrinsic parity switching time. The headline "20 second parity lifetime" refers specifically to Z-parity in one measurement configuration, but the discussion sometimes conflates this with general qubit lifetime or poisoning immunity. The phrase "some instances reaching minute-scale" is particularly vague about what operational definition of parity lifetime is being used.
**Suggested fix:** Define "Z-parity lifetime" precisely at first use and use consistent terminology throughout. Clarify whether "minute-scale" instances represent statistical fluctuations in the exponential distribution or a different measurement condition.

---

## Section 2: Machine-readable JSON

```json
{
  "findings": [
    {
      "name": "cherry-picked-baseline",
      "category": "quantum-cs",
      "severity": "high",
      "location": "Section 1 (Introduction), paragraph 2",
      "evidence": "In earlier Al-based devices, we observed typical top quintile gaps of ∆T ∼ 30 µeV [59–61]. In contrast, in the InAs–Pb devices studied here we observe a top quintile gap of ∆T ∼ 70 µeV.",
      "suggested_fix": "Add quantitative comparison table against refs 53-56 and other published Pb-based nanowire results, or explicitly state why such comparison is not possible."
    },
    {
      "name": "hasty-generalization",
      "category": "general",
      "severity": "medium",
      "location": "Section 4 (Interferometric Parity Readout) and Abstract",
      "evidence": "By aggregating multiple measurements, we observe a total of N = 324 dwell intervals. The data are consistent with a single exponential distribution... We extract a characteristic parity lifetime and corresponding fit uncertainty of τZ = 22 ± 1 s",
      "suggested_fix": "Present statistics from multiple devices/tetrons/wires, or qualify claims to specify this is from a single wire in one tetron requiring broader validation."
    },
    {
      "name": "conflated-regimes",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section 5 (Discussion and Outlook), final paragraphs",
      "evidence": "The multi-tetron array presented here functions as a modular 'unit cell' for a larger architecture; it can be tiled into much larger qubit arrays (e.g., a 12-qubit array) without altering the underlying control or readout approach.",
      "suggested_fix": "Reframe scaling claims as hypotheses requiring experimental validation, and list specific scaling concerns that may affect performance in larger arrays."
    },
    {
      "name": "active-space-handwave",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section 5 (Discussion and Outlook)",
      "evidence": "Looking ahead, the values of EM achieved here are expected to have beneficial implications for Pauli-X measurements... which suggests that τX could be more than an order of magnitude longer than in previous devices.",
      "suggested_fix": "Remove quantitative speculation about τX improvements or explicitly state this is a theoretical prediction requiring experimental validation."
    },
    {
      "name": "ad-hoc-precision-floor",
      "category": "quantum-cs",
      "severity": "medium",
      "location": "Section 3 (RF-Based Wire Spectroscopy)",
      "evidence": "we expect the resolution of this analysis to be limited to ∼ 1 µeV... Notably, the resolution of ∼ 1 µeV significantly exceeds that of conductance measurements which can resolve EM of about the half-width-half-max of a temperature broadened conductance peak EM ∼ 1.76kB T ≈ 7.6 µeV",
      "suggested_fix": "Provide explicit calibration of the 1 µeV resolution claim with known energy scales, or reframe sub-resolution EM claims more cautiously."
    },
    {
      "name": "appeal-to-authority",
      "category": "general",
      "severity": "medium",
      "location": "Section 1 (Introduction), opening paragraph",
      "evidence": "Our roadmap draws on concepts explored in Refs. 10–39.",
      "suggested_fix": "Cite specific concepts from specific papers where they are technically used, rather than bundling 30 references as general background authority."
    },
    {
      "name": "equivocation",
      "category": "general",
      "severity": "medium",
      "location": "Abstract and Section 4",
      "evidence": "parity lifetime of ∼ 20 s with some instances reaching minute-scale",
      "suggested_fix": "Define Z-parity lifetime precisely at first use, maintain consistent terminology, and clarify what 'minute-scale instances' operationally means."
    }
  ]
}
```