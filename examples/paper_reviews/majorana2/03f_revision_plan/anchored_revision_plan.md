# Anchored Revision Roadmap

## 1. Provide characterization data from at least one additional wire in the multi-tetron array (preferably from a different tetron than BA) demonstrating comparable EM and parity lifetime, or revise all claims about scalability and array-level performance to explicitly acknowledge single-wire scope.

**Severity**: 5  **Effort**: multi-day  **Judges**: Reviewer 2, Reviewer 3, Devil's Advocate, Editor-in-Chief

**Source paragraph(s)**: ¶003, ¶008, ¶024

**Quoted problem prose** (verbatim from the manuscript, <=2 sentences):
> "We employ this technique to bring up a device in a multi-tetron array and perform parity measurements of one of the tetron's hybrid nanowires (NWs)."

**Judge evidence** (one bullet per judge that diagnosed this; quote the judge verbatim, <=1 sentence each):
- Reviewer 3: "What is the wire-to-wire and device-to-device variability in EM and τZ across the multi-tetron array, and what fraction of measured wires fall within the claimed performance specifications?"
- Devil's Advocate: "The multi-tetron array shown in Fig. 1 contains eight nanowires (two per tetron, four tetrons), yet all the detailed measurements (Figs. 4–6) focus exclusively on the top wire of the BA tetron."
- Editor-in-Chief: "Provide characterization data from at least one additional wire in the multi-tetron array (preferably from a different tetron than BA) demonstrating comparable EM and parity lifetime, or revise all claims about scalability and array-level performance to explicitly acknowledge single-wire scope."

**Proposed edit**: Either add a supplementary figure presenting EM extraction and parity lifetime data from at least one additional wire (e.g., the bottom wire of BA or any wire from AA, AB, or BB tetron), or revise ¶003 and ¶024 to read: "We employ this technique to bring up a device in a multi-tetron array and perform parity measurements on *one nanowire of one tetron*; characterization of array-wide performance remains for future work."

**Why this works**: Explicitly scoping the measurement to a single wire eliminates the mismatch between the claimed "scalable multi-tetron array" framing and the single-wire evidence actually presented.

---

## 2. Include either preliminary τX measurements for the Pb-based devices or remove all claims about implications for X-parity operations and general qubit performance, explicitly scoping the results to Z-parity measurements only.

**Severity**: 4  **Effort**: 2 h (if removing claims) or multi-day (if adding measurements)  **Judges**: Reviewer 2, Editor-in-Chief

**Source paragraph(s)**: ¶024

**Quoted problem prose** (verbatim from the manuscript, <=2 sentences):
> "Looking ahead, the values of EM achieved here are expected to have beneficial implications for Pauli-X measurements, whose characteristic switching time τX scales as EM². ... Investigating these effects will be an important direction for future work."

**Judge evidence** (one bullet per judge that diagnosed this; quote the judge verbatim, <=1 sentence each):
- Reviewer 2: "Can you provide even preliminary τX measurements for the Pb-based devices to establish whether the claimed improvements extend to X-parity operations?"
- Editor-in-Chief: "Include either preliminary τX measurements for the Pb-based devices or remove all claims about implications for X-parity operations and general qubit performance, explicitly scoping the results to Z-parity measurements only."

**Proposed edit**: If τX data are unavailable, revise ¶024 to delete the sentence "which suggests that τX could be more than an order of magnitude longer than in previous devices" and replace with: "Experimental characterization of τX in Pb-based devices remains an open direction; the results presented here are limited to Z-parity measurements."

**Why this works**: Removes speculative quantitative claims about unmeasured quantities, aligning claims with the presented evidence.

---

## 3. Present quantitative model comparison (AIC or similar) between exponential and alternative dwell time distributions, including explicit treatment of the "minute-scale instances" tail behavior and characterization of measurement-to-measurement variability in extracted τZ.

**Severity**: 4  **Effort**: 2 h  **Judges**: Reviewer 2, Reviewer 3, Editor-in-Chief

**Source paragraph(s)**: ¶003, ¶022

**Quoted problem prose** (verbatim from the manuscript, <=2 sentences):
> "Further time-resolved measurements reveal a characteristic parity switching time of ∼ 20 s with some instances reaching minute-scale."

**Judge evidence** (one bullet per judge that diagnosed this; quote the judge verbatim, <=1 sentence each):
- Reviewer 2: "Have you performed formal model selection (e.g., Akaike information criterion) comparing exponential versus non-exponential dwell time distributions for the parity switching data?"
- Reviewer 3: "Can you provide a quantile-quantile plot comparing the observed dwell time distribution against the fitted exponential, particularly characterizing the tail behavior that gives rise to 'minute-scale' instances?"
- Editor-in-Chief: "Present quantitative model comparison (AIC or similar) between exponential and alternative dwell time distributions, including explicit treatment of the 'minute-scale instances' tail behavior and characterization of measurement-to-measurement variability in extracted τZ."

**Proposed edit**: Add to ¶022 or a supplementary section: (1) a Q-Q plot of observed dwell times vs. the exponential(τ=22 s) quantiles, (2) AIC values comparing exponential, stretched-exponential, and power-law fits, and (3) a table showing τZ extracted from each of the 9 individual time traces with standard deviation to characterize run-to-run variability.

**Why this works**: Demonstrates that the exponential assumption is justified (or identifies systematic deviations), and quantifies the "minute-scale" tail relative to statistical expectation.

---

## 4. Perform and report sensitivity analysis on the rf tuning protocol thresholds, quantifying how the identified topological region changes with S/σ threshold and cutter configuration requirements.

**Severity**: 3  **Effort**: 2 h  **Judges**: Reviewer 3, Editor-in-Chief

**Source paragraph(s)**: ¶020

**Quoted problem prose** (verbatim from the manuscript, <=2 sentences):
> "To identify regions associated with stable low-energy states, we evaluate, for each point in Vwp and Bz, the fraction of wire-cutter configurations for which the rf response exceeds a signal-to-noise ratio S/σ > 2.5."

**Judge evidence** (one bullet per judge that diagnosed this; quote the judge verbatim, <=1 sentence each):
- Reviewer 3: "The thresholding procedure introduces subjective elements that should be characterized through sensitivity analysis."
- Editor-in-Chief: "Perform and report sensitivity analysis on the rf tuning protocol thresholds, quantifying how the identified topological region changes with S/σ threshold and cutter configuration requirements."

**Proposed edit**: Add a supplementary figure showing the identified region of interest (analogous to Fig. 5c) for S/σ thresholds of 2.0, 2.5, and 3.0, and for requiring 5/10, 7/10, and 9/10 cutter configurations. Include a brief statement in ¶020: "Varying the S/σ threshold from 2.0 to 3.0 shifts the region boundary by approximately X mV in Vwp; qualitative features are preserved."

**Why this works**: Demonstrates robustness (or quantifies sensitivity) of the tuning protocol to threshold choices, addressing concerns about subjectivity.

---

## 5. Either present TGP measurements on the actual tetron device in which parity measurements were performed, or clearly separate test structure characterization from device-level performance with explicit discussion of the expected transfer of properties.

**Severity**: 4  **Effort**: 30 min (if clarifying scope) or multi-day (if adding TGP data)  **Judges**: Devil's Advocate, Editor-in-Chief

**Source paragraph(s)**: ¶012

**Quoted problem prose** (verbatim from the manuscript, <=2 sentences):
> "A representative phase diagram obtained from a NW test device is shown in Fig. 3(c), which was obtained by applying the Topological Gap Protocol (TGP) [60]."

**Judge evidence** (one bullet per judge that diagnosed this; quote the judge verbatim, <=1 sentence each):
- Devil's Advocate: "The TGP measurement was done on a '3 µm-long nanowire test structure' according to the figure caption, whereas the tetron nanowires are 3.5 µm long with different geometry including the narrow backbone junction."
- Editor-in-Chief: "Either present TGP measurements on the actual tetron device in which parity measurements were performed, or clearly separate test structure characterization from device-level performance with explicit discussion of the expected transfer of properties."

**Proposed edit**: Add to ¶012 or the Fig. 3 caption: "The TGP data shown here were obtained from a standalone 3 µm test nanowire; TGP measurements on the integrated tetron device were not performed due to [reason, e.g., lack of transport terminals]. We expect qualitatively similar behavior in the 3.5 µm tetron wires based on [shared material stack / comparable localization lengths], though quantitative ∆T values may differ."

**Why this works**: Breaks the implicit claim that Fig. 3 directly characterizes the device in Figs. 4–6, providing transparency about the evidentiary gap.

---

## 6. Add a data availability statement specifying the accessibility of raw measurement data and analysis code, consistent with PRX Quantum policies on reproducibility.

**Severity**: 3  **Effort**: 5 min  **Judges**: Reviewer 3, Editor-in-Chief

**Source paragraph(s)**: ¶? (structural finding—no data availability section exists)

**Quoted problem prose** (verbatim from the manuscript, <=2 sentences):
> (no verbatim anchor — structural finding)

**Judge evidence** (one bullet per judge that diagnosed this; quote the judge verbatim, <=1 sentence each):
- Reviewer 3: "Is there a data availability statement or analysis code repository that would enable independent verification of the reported numerical results?"
- Editor-in-Chief: "Add a data availability statement specifying the accessibility of raw measurement data and analysis code, consistent with PRX Quantum policies on reproducibility."

**Proposed edit**: Add a new section after Acknowledgments titled "Data Availability" with text such as: "Raw measurement data and analysis scripts used to generate the figures in this work are available from the corresponding author upon reasonable request. [Alternatively: are deposited at DOI:xxxx with CC-BY license.]"

**Why this works**: Satisfies PRX Quantum reproducibility requirements and addresses reviewer concerns about replicability.