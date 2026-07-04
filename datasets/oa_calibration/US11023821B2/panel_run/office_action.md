# OFFICE ACTION — POST-GRANT REVIEW

**Application/Patent:** US11023821B2
**Title:** Embedding of a condensed matter system with an analog processor
**Assignee:** D-Wave Systems Inc.
**Claims examined:** 1–7
**Art Unit:** General quantum computing (CPC G06N10/00)

**Notice regarding prior art:** No prior-art references were placed of record for this examination. Consequently, no § 102 anticipation rejection and no § 103 obviousness combination can be sustained on this record. Rejections, if any, are limited to defects evident from the four corners of the document itself under §§ 101 and 112.

---

## Voice 1 — Primary Examiner (§ 101 eligibility + overall)

Claim 1 is a method claim reciting: (a) forming logical qubits by assigning ferromagnetic coupling strengths to physical couplers of an analog processor; (b) forming a 3D structure by assigning a second coupling strength to inter-logical-qubit couplers; (c) evolving the analog processor from H_i to H_f according to H_e = (1−s)H_i + sH_f until an intermediate s\*; (d) **pausing** the anneal; (e) **applying a longitudinal flux** to physical qubits during the pause; (f) resuming evolution to a final state; (g) **measuring** characteristics of the logical qubits; and (h) determining a property of the physical material.

**Step 2A Prong One:** Portions of claim 1 recite mathematical relationships (the Hamiltonian equation H_e = (1−s)H_i + sH_f) and an abstract concept (simulating a material). The claim thus arguably touches a judicial exception (math / mental process of "determining a property").

**Step 2A Prong Two:** The claim is integrated into a practical application. The recited acts of assigning coupling strengths to physical couplers of an analog processor, pausing the physical evolution, applying a longitudinal flux to physical flux qubits, and measuring qubit characteristics are concrete operations performed on and by quantum hardware. This is an improvement to the *operation* of a quantum annealer — it defines a specific control protocol (mid-anneal pause + transverse-to-longitudinal field manipulation) that produces measurable susceptibility data from the physical device. Under *Enfish* and MPEP 2106.05(a), this qualifies as an improvement to the functioning of a machine.

**Step 2B:** Not reached; claim is eligible at Prong Two.

Claims 2–7 are dependents adding further hardware/operational limitations (longitudinal flux tied to a modeled magnetic field; antiferromagnetic or zero couplings for doping; susceptibility measurement; phase-transition determination). Each further ties the claim to concrete QPU operation and is likewise eligible.

**§ 101 verdict:** All claims recite a practical application on a physical analog/quantum processor. None is directed to a bare mathematical algorithm or mental process on a generic computer.

| Claim(s) | Statute | Basis (one line) |
|---|---|---|
| 1–7 | § 101 | Eligible — recites concrete control and measurement operations on a physical analog processor; improvement to QPU operation. |

---

## Voice 2 — § 102 Examiner (anticipation / novelty)

No prior-art references were placed of record. Under the standard set out in the case header, I may not cite art from memory, and I decline to fabricate a record. Without at least one identified reference disclosing every element of a claim as arranged, no anticipation rejection can be sustained.

Claims 1–7 are therefore **novel over the prior art of record** and allowable under § 102.

| Claim(s) | Listed reference | Element-by-element read |
|---|---|---|
| 1 | none | No anticipating reference of record |
| 2 | none | No anticipating reference of record |
| 3 | none | No anticipating reference of record |
| 4 | none | No anticipating reference of record |
| 5 | none | No anticipating reference of record |
| 6 | none | No anticipating reference of record |
| 7 | none | No anticipating reference of record |

---

## Voice 3 — § 103 Examiner (obviousness)

An obviousness rejection under KSR and Graham requires identified prior-art references combined with an articulated rationale. The record contains no such references. I cannot manufacture a combination the record does not support, nor may I assert that any limitation — including the pause-and-longitudinal-flux protocol of claim 1 or the doping-probability limitation of claim 4 — is "routine" without art demonstrating it.

Claims 1–7 are **non-obvious over the prior art of record** and allowable under § 103.

| Claim(s) | Listed primary + secondary | Rationale to combine |
|---|---|---|
| 1 | none | No supporting combination of record |
| 2 | none | No supporting combination of record |
| 3 | none | No supporting combination of record |
| 4 | none | No supporting combination of record |
| 5 | none | No supporting combination of record |
| 6 | none | No supporting combination of record |
| 7 | none | No supporting combination of record |

---

## Voice 4 — § 112 Examiner (enablement / written description / definiteness)

The specification is included and is substantial. I apply all three § 112 inquiries.

**§ 112(a) enablement.** The specification teaches (i) a concrete Chimera-topology analog processor with intra-cell and inter-cell couplers (FIG. 1); (ii) a specific logical-qubit construction (four physical qubits forming a chain across three cells, ferromagnetic strength e.g., J1 = −2); (iii) a specific evolution schedule with a pause and longitudinal flux ±φ_∥, with representative numerical values (Δt on the order of 1 ms, |φ_∥| < 100 μΦ₀, ramp of order 500 ns); (iv) a doping protocol using a probability p; and (v) a measurement/inference procedure for susceptibility χ. A PHOSITA in quantum annealing would be enabled to practice claims 1–7 without undue experimentation. No enablement defect.

**§ 112(a) written description.** Claim 1's "second coupling strength" is disclosed both as ferromagnetic (with |J₂| < |J₁|) and as antiferromagnetic (dependent claim 3) or zero (dependent claim 5). Possession is shown for each dependent variant. "Longitudinal flux based on a magnetic field represented in the model" (claim 2) is supported at the discussion of per-qubit flux biases corresponding to magnetic-field strength. No written-description defect.

**§ 112(b) definiteness.**

- Claim 1 recites "an annealing coefficient s" and "an initial Hamiltonian H_i and a final Hamiltonian H_f" without prior antecedent introduction *before* they appear in the equation. However, the equation itself defines the relationship (H_e = (1−s)H_i + sH_f) and the specification defines each term, so the term is reasonably certain under *Nautilus*. Not indefinite, but on the margin.
- Claim 1: "s\* is an intermediate point in the evolution" — "intermediate" is reasonably certain in context (0 < s\* < 1); definite.
- Claim 1: "a longitudinal flux" — defined in specification (±φ_∥) as the flux applied parallel to the qubit's z-axis during pause; definite.
- Claim 3: "a doping characteristic of the model" — the specification explicitly defines doping via probability p; definite (and further narrowed in claim 4).
- Claim 6: "magnetic susceptibility of at least one of the plurality of qubits" — supported and definite.
- Claim 7: "phase transition response ... to a simulated condition" — "simulated condition" is broad but supported by the specification's discussion of transverse fields Γ, temperatures T, and magnetic fields; definite in context.

No § 112(f) means-plus-function trigger. No concrete definiteness defect.

**§ 112 verdict:** All claims are compliant.

| Claim(s) | Sub-section | Specific defect |
|---|---|---|
| 1–7 | § 112(a)/(b) | None — enablement, written description, and definiteness satisfied |

### Claim compliance review

USPTO standard (§ 112(b), antecedent basis, claim structure, § 112(f), dependency):

| Claim(s) | Standard | Issue | Specific feedback | Amendment target |
|---|---|---|---|---|
| 1 | USPTO § 112(b) antecedent basis | Minor | "the annealing coefficient s" — "the" is used at first appearance ("until a value of the annealing coefficient s reaches s\*"). Antecedent basis is implicit via the equation that immediately follows, but a strict reading prefers introduction with "a". | Optional cleanup: "until a value of an annealing coefficient s reaches an intermediate value s\*". |
| 1 | USPTO § 112(b) claim structure | Pass | Method preamble with sequential wherein/comprising steps; proper transitional phrasing. | None. |
| 1 | USPTO § 112(f) functional claiming | Pass | Verbs (forming, coupling, evolving, pausing, applying, resuming, measuring, determining) are act-form, not "means for"; no § 112(f) invocation. | None. |
| 2 | USPTO § 112(b) | Pass | Proper dependent form; adds a narrowing limitation with antecedent to claim 1. | None. |
| 3 | USPTO § 112(b) | Pass | "a second set of couplers" — new introduction, proper. | None. |
| 4 | USPTO § 112(b) dependency | Pass | Depends from claim 3; "the second set of couplers" has antecedent basis. | None. |
| 5 | USPTO § 112(b) | Minor | Introduces its own "second set of couplers" separate from that in claim 3; both are permissible because claims 3 and 5 are alternative dependents of claim 1, but the identical phrase could invite confusion in litigation. | Consider renaming to "a further set of couplers" in claim 5. |
| 6 | USPTO § 112(b) | Pass | Clear narrowing of "one or more characteristics" from claim 1. | None. |
| 7 | USPTO § 112(b) | Pass | Clear narrowing of "a property of the physical material" from claim 1. | None. |

---

## Voice 5 — Quantum Technical Specialist (operability / quantum-specific)

Substantive quantum-physics assessment:

1. **Logical-qubit chains via strong ferromagnetic couplers.** Standard, well-understood technique for D-Wave-style Chimera/Pegasus embeddings. Operable.

2. **Pause-and-longitudinal-flux protocol.** The specification describes pausing the anneal at intermediate s\*, applying a small longitudinal field ±φ_∥ (< 100 μΦ₀) to *all* qubits, and measuring the difference in magnetization between the +φ_∥ and −φ_∥ runs to infer susceptibility χ = ∂⟨M⟩/∂φ_∥ by finite-difference linear response. This is sound: at fixed s, the annealing Hamiltonian has both transverse (H_D ∝ Σ σ_x) and longitudinal (H_P ∝ Σ h_i σ_z + Σ J_ij σ_z σ_z) components, and adding a small longitudinal probe measures the z-response. Operable.

3. **Doping via random AFM or zero couplings (claims 3–5).** Physically meaningful analog of quenched disorder / bond dilution in a spin-glass or diluted-antiferromagnet model. Operable.

4. **Susceptibility peak as phase-transition indicator (claim 7 read on FIG. 5).** Correct physics: a divergent (or sharply peaked in finite systems) susceptibility marks a second-order transition or a quantum critical crossover along the annealing path. The claim does not overreach on complexity theory, error correction, or coherence time. No unsupported speedup or fault-tolerance assertion.

5. **No no-cloning / no-Holevo overreach.** The claims do not require cloning, superluminal signaling, or exceeding informational bounds.

6. **Hardware tie-in for § 101/§ 112(a).** The specification's identification of specific coupler and qubit topology (Chimera), a specific evolution schedule with concrete order-of-magnitude timescales, and a specific measurement observable (magnetization difference → χ) satisfies operability and supports enablement.

Operability finding: **operable as claimed** on a D-Wave-class analog quantum processor. Reinforces § 112(a) enablement and § 101 eligibility findings above.

---

## Voice 6 — Supervisory Patent Examiner (SPE) synthesis + disposition

I have reviewed the analyses of the § 101, § 102, § 103, § 112 examiners and the Quantum Technical Specialist.

**Reconciliation.** No examiner sustains a rejection. The § 101 examiner finds the claims tied to a physical analog processor and reflect an improvement to QPU operation. The § 102 and § 103 examiners have no prior art of record and correctly decline to fabricate one. The § 112 examiner finds the specification supports the full scope of the claims, and only offers optional cleanup on minor stylistic points. The Quantum Technical Specialist confirms operability under the physics.

**Disposition: allowance**

1. **Rejected claims:** none.
2. **Allowable subject matter:** claims 1–7 all contain allowable subject matter on this record. No amendment is required to place the application in condition for allowance; the optional antecedent-basis cleanup in claim 1 ("a" instead of "the" annealing coefficient) and the "second set of couplers" naming disambiguation in claim 5 are recommendations only and would not affect allowability.
3. **Prosecution / post-grant validity notes.** In a real post-grant proceeding, a petitioner would likely search for prior art directed to (i) mid-anneal pause techniques on D-Wave hardware; (ii) transverse-to-longitudinal probe protocols for measuring susceptibility on flux-qubit annealers; (iii) chain-based logical-qubit embeddings of 3D lattices onto Chimera topology; and (iv) quenched-disorder simulation via random AFM/zero coupler assignments. If such art (e.g., prior D-Wave publications by King, Boothby, or Harris themselves; prior spin-glass simulation papers on annealers) were placed of record, claims 1, 3–5, and 7 would face the most obviousness pressure, and claim 1's pause-and-longitudinal-flux step would be the strongest point of novelty distinguishing over generic quantum-annealing prior art.
4. **Full-application defects:** none material. The specification is enabling, the drawings are described (FIGS. 1–7), and the required USPTO sections (Field, Background, Brief Summary, Brief Description of Drawings, Detailed Description, Claims, Abstract) are present.
5. **Strongest rejection applicant must overcome:** none on this record.

### Full application review

| Area | Standard | Pass / defect | Evidence from application | Required fix |
|---|---|---|---|---|
| Claims | USPTO § 112(b) | Pass with minor stylistic notes | Claims 1–7 use proper method form, antecedent basis (with one marginal "the annealing coefficient s" first appearance in claim 1), and clear dependency. | Optional: introduce "a" at first appearance of s in claim 1; disambiguate "second set of couplers" between claims 3 and 5. |
| Specification support | USPTO § 112(a) written description | Pass | FIG. 1 and § "DETAILED DESCRIPTION" disclose Chimera topology, logical-qubit chains of four physical qubits, J₁/J₂ magnitudes, and doping protocol. | None. |
| Enablement / possession | USPTO § 112(a) enablement | Pass | Concrete numerical ranges (Δt ~1 ms, |φ_∥| < 100 μΦ₀, ramp ~500 ns, doping p in [0,1]), Hamiltonians H_e, H_D, H_P defined; methods 200, 400, 700 described stepwise. | None. |
| Formalities / required sections | MPEP 608 | Pass | Field, Background, Brief Summary, Brief Description of Drawings, Detailed Description, Abstract all present. Cross-references to prior US and international applications are given. | None. |
| Drawings / abstract / title | MPEP 608 | Pass | Seven figures described in Brief Description; abstract present and under 150 words; title "Embedding of a condensed matter system with an analog processor" reasonably descriptive. | None. |

### Rejections of record
- § 101: none
- § 102: none
- § 103: none
- § 112: none
- allowable: 1–7

## Vote table

| Voice | Recommended disposition | Confidence 1-10 |
|---|---|---|
| Primary Examiner | allowance | 8 |
| § 102 Examiner | allowance (no art of record) | 10 |
| § 103 Examiner | allowance (no art of record) | 10 |
| § 112 Examiner | allowance | 8 |
| Quantum Technical Specialist | allowance (operable) | 9 |
| Supervisory Patent Examiner | allowance | 8 |