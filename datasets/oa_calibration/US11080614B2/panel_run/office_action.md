# OFFICE ACTION — Post-Grant Review

**Application/Patent No.:** US11080614B2
**Title:** Systems and methods for quantum coherence preservation of qubits
**Assignee:** Anametric Inc
**Claims examined:** 1–15
**Status:** Granted patent (B2); reviewed under IPR / post-grant validity standards

**Preliminary note on the record:** No external prior-art set was placed of record for this examination. Per the panel's operating instructions, no § 102 or § 103 reference may be cited from memory. Absent art of record, claims 1–15 are treated as novel under § 102 and non-obvious under § 103, and the panel's rejections are confined to § 112 and § 101 defects evident on the face of the document.

---

## Voice 1 — Primary Examiner (§ 101 eligibility + overall)

**Statutory framework.** Under 35 U.S.C. § 101, an invention is patent-eligible if it falls within a statutory category (process, machine, manufacture, or composition of matter) and is not directed to a judicial exception (abstract idea, law of nature, natural phenomenon) without more. The Alice/Mayo two-step, as elaborated in the 2019 PEG and MPEP § 2106, controls.

**Step 1 — Statutory category.** Every claim (1–15) is drawn to "a quantum circuit," i.e. a *machine* comprising physically-realized quantum logic gates (Hadamard, CNOT, Fredkin, phase-rotation) with defined input/output couplings. Each claim recites an apparatus, not a process or signal per se. Claims 1–15 fall within the "machine" statutory category. Step 1 is satisfied.

**Step 2A Prong One — Directed to a judicial exception?** The panel considered whether the claims recite an abstract idea (mathematical concept, mental process, or method of organizing human activity) or a law of nature (quantum mechanics itself). The claims recite structural interconnections among physical gates — the output of Hadamard gate n is *coupled to* the input of gate n+1, and so on around a feedback loop. This is claim language directed to hardware topology, not to a mathematical algorithm executed in the abstract. The underlying operation of Hadamard, CNOT, and Fredkin gates is described mathematically in the specification (transfer matrices B, B², B³, B⁴), but the claims themselves do not recite those matrices or any mathematical formula as a limitation. The claims recite a cascaded arrangement of *physical* Bell-state generators with a feedback path — a machine topology. Under MPEP § 2106.04(a), this is not a claim to a mathematical concept as such. Prong One is not triggered.

**Step 2A Prong Two — Practical application (arguendo).** Even assuming a reviewer characterized the recited gate operations as invoking mathematical relationships, the claim integrates any such concept into a practical application: a physical qubit-storage / entanglement-preservation apparatus that improves a technology (quantum coherence preservation and Bell-pair regeneration in a hardware ring). The specification ties the claimed topology to concrete technological benefits — regeneration of entangled EPR pairs, monitoring of decoherence through basis-state readouts, and a photonic implementation on a Q-PIC. Under MPEP § 2106.04(d), improvement to the operation of a machine (here, a quantum information-processing apparatus) is a hallmark of integration into a practical application. Prong Two is satisfied.

**Step 2B (arguendo).** Even had Prong Two failed, the ordered combination of four cascaded Bell-state generators in a closed feedback loop is not a well-understood, routine, or conventional arrangement — it is the specific inventive topology the specification identifies as the "Bell State Oscillator." That structural specificity supplies an inventive concept beyond any abstract mathematics.

**Verdict — independent claims.** Claim 1 is directed to patent-eligible subject matter under § 101. Claim 10 (which incorporates a second BSO of the same topology) is likewise eligible. Dependent claims 2–9 and 11–15 recite additional hardware limitations (Fredkin gates, phase-rotation gates, CPHASE gates, quantum coupling circuit of three CNOTs) and inherit eligibility from their independent parents; each adds further hardware structure, not abstraction.

No § 101 rejection is sustained.

| Claim(s) | Statute | Basis (one line) |
|---|---|---|
| 1–15 | § 101 | Eligible — machine claims directed to a hardware qubit-preservation apparatus; any mathematical description of gate operations is integrated into a practical application (improved quantum-coherence hardware). |

---

## Voice 2 — § 102 Examiner (anticipation / novelty)

Anticipation under 35 U.S.C. § 102 requires that a single prior-art reference disclose every limitation of the claim, arranged as claimed. *Verdegaal Bros. v. Union Oil Co.*, 814 F.2d 628 (Fed. Cir. 1987).

**No prior art was placed of record.** The prior-art-of-record block accompanying this examination is empty. Under the panel's grounding rule, an anticipation rejection cannot be sustained on references recalled from memory. Any such rejection would fabricate the record and is therefore prohibited.

Accordingly, no § 102 rejection is sustained against claims 1–15. Each claim is **novel over the prior art of record**.

| Claim(s) | Listed reference | Element-by-element read |
|---|---|---|
| 1 | none | No anticipating reference of record — allowed under § 102 |
| 2 | none | No anticipating reference of record — allowed under § 102 |
| 3 | none | No anticipating reference of record — allowed under § 102 |
| 4 | none | No anticipating reference of record — allowed under § 102 |
| 5 | none | No anticipating reference of record — allowed under § 102 |
| 6 | none | No anticipating reference of record — allowed under § 102 |
| 7 | none | No anticipating reference of record — allowed under § 102 |
| 8 | none | No anticipating reference of record — allowed under § 102 |
| 9 | none | No anticipating reference of record — allowed under § 102 |
| 10 | none | No anticipating reference of record — allowed under § 102 |
| 11 | none | No anticipating reference of record — allowed under § 102 |
| 12 | none | No anticipating reference of record — allowed under § 102 |
| 13 | none | No anticipating reference of record — allowed under § 102 |
| 14 | none | No anticipating reference of record — allowed under § 102 |
| 15 | none | No anticipating reference of record — allowed under § 102 |

---

## Voice 3 — § 103 Examiner (obviousness)

Obviousness under 35 U.S.C. § 103 is assessed under the Graham factors and *KSR Int'l Co. v. Teleflex Inc.*, 550 U.S. 398 (2007). A § 103 rejection requires listed references teaching or suggesting every limitation, combined with an articulated rationale.

**No prior art was placed of record.** The panel therefore has no primary reference and no secondary references to combine. Under the grounding rule, no obviousness combination may be assembled from memory or general knowledge. The panel notes for the record that a real IPR petitioner would likely marshal references such as Nielsen & Chuang's textbook treatment of Bell-state generators, DiVincenzo (1998), and the Patel *et al.* (2016) Fredkin-gate work cited in the specification's own reference list; however, none of these has been placed of record here, and the panel will not construct a rejection on unlisted art.

Accordingly, no § 103 rejection is sustained against claims 1–15. Each claim is **non-obvious over the prior art of record**.

| Claim(s) | Listed primary + secondary | Rationale to combine |
|---|---|---|
| 1 | none | No supporting combination of record — allowed under § 103 |
| 2 | none | No supporting combination of record — allowed under § 103 |
| 3 | none | No supporting combination of record — allowed under § 103 |
| 4 | none | No supporting combination of record — allowed under § 103 |
| 5 | none | No supporting combination of record — allowed under § 103 |
| 6 | none | No supporting combination of record — allowed under § 103 |
| 7 | none | No supporting combination of record — allowed under § 103 |
| 8 | none | No supporting combination of record — allowed under § 103 |
| 9 | none | No supporting combination of record — allowed under § 103 |
| 10 | none | No supporting combination of record — allowed under § 103 |
| 11 | none | No supporting combination of record — allowed under § 103 |
| 12 | none | No supporting combination of record — allowed under § 103 |
| 13 | none | No supporting combination of record — allowed under § 103 |
| 14 | none | No supporting combination of record — allowed under § 103 |
| 15 | none | No supporting combination of record — allowed under § 103 |

---

## Voice 4 — § 112 Examiner (enablement / written description / definiteness)

**(a) Enablement § 112(a).** The specification is unusually detailed for a quantum-circuit application: it discloses B, B², B³, B⁴ transfer matrices with worked examples for all four basis-state initializations; identifies photonic implementations of Hadamard (half-wave plate or non-polarizing beamsplitter), Bell-state generator (⅓ and ½ non-polarizing beamsplitters with HWPs on control lines), Fredkin gate (Toffoli + two CNOTs, with citations to the Patel *et al.* 2016 experimental realization), and CNOT couplings; and describes a Q-PIC integration path using FTIR nanocouplers and perfluorocyclobutyl polymers. The Wands factors (quantity of experimentation, direction, working examples, state of the art, level of ordinary skill, predictability, breadth) are addressed by the specification's mathematical development and the cited physical implementations. The claims are limited to the specific four-generator cascade + feedback topology (and two-BSO variant with a defined coupling circuit) — narrow enough that the physical implementations disclosed enable the claimed scope. Enablement is satisfied.

**(b) Written description § 112(a).** The specification shows possession of each claim's topology: FIG. 2A/2B corresponds to claim 1; FIG. 4A + Fredkin discussion corresponds to claim 2; FIG. 4B + U/U⁻¹ discussion corresponds to claims 3–9; FIG. 5 + the three-CNOT quantum coupling circuit corresponds to claims 10–12 (with the coupling limitations of claim 12 traceable to the FIG. 5 CNOTs 922a/922b/922c). Written-description support is present for each claimed limitation.

**(c) Definiteness § 112(b) — concrete defects identified.** The panel identifies the following definiteness issues on the face of the claims:

- **Claim 2 — duplicate word "input":** "a first output coupled to *the input of the input of* the first Hadamard gate of the first Bell state generator." The doubled "the input of the input of" is a facially indefinite formulation; the phrase should be "the input of the first Hadamard gate." A PHOSITA can reconstruct the intended meaning, but the claim as issued contains a literal grammatical defect that clouds antecedent basis.
- **Claim 12 — internally garbled couplings:** the claim recites "a control coupled to the output of *the first CNOT gate of the first CNOT gate of the first Bell state generator* of the first BSO" (redundant / nested "first CNOT gate of the first CNOT gate"), and later "an the output of the second CNOT gate" (spurious article "an"). These are not mere copy-editing slips; they render the second and third couplings of the quantum coupling circuit indefinite because it is not clear whether "the first CNOT gate of the first CNOT gate" refers to a single gate or a nested structure. Under *Nautilus, Inc. v. Biosig Instruments, Inc.*, 572 U.S. 898 (2014), a claim must inform a PHOSITA of its scope with reasonable certainty; claim 12's couplings do not.
- **Claim 12 — antecedent basis / scope of "the second CNOT gate of the second Bell state generator":** the claim references "the second CNOT gate of the second Bell state generator of the second BSO" and "the second CNOT gate of the second Bell state generator of the first BSO," but the second Bell state generator (in the independent-claim topology of claims 1 and 10) has *a* CNOT gate — not a "second CNOT gate." Antecedent basis for "the second CNOT gate of the second Bell state generator" is missing; the recited element does not appear in the parent claims.
- **Claim 7 — "an angle of rotation is an input parameter":** the phrase "is an input parameter" is functional and does not specify whether the angle is a classical control, a qubit-encoded control, or a design-time fixed value. The specification discloses both classical and qubit controls, so the claim is not fatally indefinite, but it is broad-functional and warrants scrutiny under § 112(b). The panel treats this as borderline and does not sustain a rejection on this basis alone.

**Verdict.** Claims 2 and 12 are rejected under § 112(b) as indefinite. Claims 1, 3–11, and 13–15 are not rejected under § 112.

| Claim(s) | Sub-section | Specific defect |
|---|---|---|
| 2 | § 112(b) | "the input of the input of the first Hadamard gate" — duplicated article/preposition; grammatically indefinite. |
| 12 | § 112(b) | (i) "the output of the first CNOT gate of the first CNOT gate of the first Bell state generator" — nested/duplicated "first CNOT gate of the first CNOT gate" is indefinite; (ii) "an the output" — indefinite article/definite article collision; (iii) "the second CNOT gate of the second Bell state generator" lacks antecedent basis in parent claim 10, which recites only *a* CNOT gate per Bell-state generator. |
| 1, 3–11, 13–15 | — | No concrete § 112 defect identified. |

### Claim compliance review

USPTO standard applied (§ 112(b) definiteness, antecedent basis, claim structure, functional-claiming risk, dependency).

| Claim(s) | Standard | Issue | Specific feedback | Amendment target |
|---|---|---|---|---|
| 2 | USPTO § 112(b) | Grammatical defect | "the input of the input of the first Hadamard gate" contains a duplicated "of the input"; on its face indefinite. | Amend to "a first output coupled to the input of the first Hadamard gate of the first Bell state generator." |
| 7 | USPTO § 112(b) (borderline) | Functional recitation | "an angle of rotation is an input parameter" — unclear whether classical or qubit input. Spec supports both; not fatal but flagged. | Amend to specify whether the input parameter is a classical control signal or a control qubit. |
| 12 | USPTO § 112(b) | Antecedent basis + nested reference | "the first CNOT gate of the first CNOT gate of the first Bell state generator" is a nested reference with no clear referent; "an the output" is grammatically defective; "the second CNOT gate of the second Bell state generator" has no antecedent because parent claim 10 recites only one CNOT gate per Bell-state generator. | Rewrite claim 12 to (a) delete the duplicated "of the first CNOT gate"; (b) correct "an the output" to "an output"; (c) either add antecedent basis in claim 10 for a "second CNOT gate of the second Bell state generator" or re-label the coupling target. |
| 1, 3–6, 8–11, 13–15 | USPTO § 112(b) | Pass | No definiteness or antecedent defect identified. | None. |

---

## Voice 5 — Quantum Technical Specialist (operability / quantum-specific)

**Operability assessment.** The claimed topology is grounded in well-understood quantum-gate physics. A Bell-state generator formed of a Hadamard followed by a CNOT is textbook (the specification's transfer matrix B is the standard construction). Cascading four such generators yields B⁴, which the specification correctly shows to be a permutation matrix on the four computational basis states — i.e., B⁴ maps |00⟩→|01⟩→|00⟩ and |10⟩→|11⟩→|10⟩. That mathematical claim is verifiable and correct. The intermediate states |φ₁⟩, |φ₂⟩, |φ₃⟩ are indeed superpositions of Bell states, as the specification's examples 1–4 demonstrate. To that extent, the claimed apparatus operates as claimed under the physics.

**Concerns the panel notes for the record (not converted into rejections absent art or § 112 hooks in the claims):**

1. **"Coherence preservation" is not a claim limitation.** The title and abstract emphasize "preservation of quantum coherence" and "long periods of time," but no claim recites a coherence time, a fidelity, or a preservation metric. The claims are structural. The panel does not fault the claims for omitting operational metrics — that is a drafting choice — but it flags that the title's implicit promise is not a claim limitation and cannot be read in as one.
2. **The "quantum channel" / instantaneous-signaling discussion in the specification.** The specification's discussion of using entangled BSOs for signaling ("near instantaneous signaling," submarine paging, GPS-P(Y)-code secret sharing based on triggering an entangled BSO from the football) describes signaling schemes that, if claimed, would run afoul of the no-communication theorem: measurement on one half of an entangled pair cannot be used to signal to the other. The panel notes this only as context — none of claims 1–15 recites such a signaling method or claims superluminal communication; the claims are limited to the hardware topology. Had a method claim recited "communicating a signal from a first BSO to a second BSO by decohering a qubit of the first BSO such that the second BSO's basis state changes," that claim would be inoperable and rejected under § 101 (law of nature / physical impossibility) and § 112(a) (non-enablement). No such claim is present, so no rejection is sustained on this ground. This is a substantial ground the specification supplies but the claims correctly do not press.
3. **Photonic implementation and "regeneration."** The specification's account of continuously regenerating EPR pairs in a photonic ring depends on lossless propagation through the four B blocks and the feedback path. In a physical photonic implementation with beamsplitters that route auxiliary modes to optical absorbers ("dumps"), photon loss is inevitable and the ring will not sustain a coherent oscillation indefinitely. Again, no claim recites indefinite sustainment, so no § 112(a) enablement rejection is sustained; the claims are limited to the topology and a PHOSITA can build the topology.
4. **Claim 2 Fredkin-gate placement.** The claim positions a Fredkin gate between the fourth and first Bell-state generators with control qubit implicit. The Fredkin gate needs a control input; the claim does not recite where the control comes from. The specification supplies it (classical or secondary control qubit). This is a breadth/scope observation, not a § 112(b) defect.

**Bottom line.** The hardware claims are technically sound and correspond to a realizable (though lossy) photonic apparatus. The panel does not sustain an operability-based rejection of any claim.

---

## Voice 6 — Supervisory Patent Examiner (SPE) — synthesis + disposition

The Primary Examiner finds all claims eligible under § 101 — the claims recite a machine topology (cascaded Bell-state generators in a feedback ring, with hardware couplings, Fredkin gates, phase-rotation gates, and a defined inter-BSO coupling circuit). The § 102 and § 103 examiners cannot sustain any rejection because no prior art was placed of record and the grounding rule prohibits fabricating references; they therefore allow all claims over the prior art of record. The § 112 examiner identifies concrete definiteness defects in claims 2 and 12 — a duplicated "input of the input" phrase in claim 2, and a garbled "first CNOT gate of the first CNOT gate" nested reference plus an "an the output" grammatical collision plus a missing antecedent for "the second CNOT gate of the second Bell state generator" in claim 12. The Quantum Technical Specialist finds the hardware topology operable under the physics and flags only extra-claim concerns (signaling schemes discussed in the specification but not claimed).

The claim-compliance review isolates claims 2, 7 (borderline), and 12 as needing amendment. The full-application review below finds the specification adequate in written description and enablement for the claimed structural scope.

**Reconciliation.** No § 101, § 102, or § 103 rejection is sustained. Two claims — 2 and 12 — carry concrete § 112(b) definiteness defects that must be corrected. The remaining thirteen claims (1, 3–11, 13–15) are allowable as issued over the prior art of record and under § 101 / § 112. Because rejections stand against claims 2 and 12, this Office Action cannot be an allowance in full.

**Disposition: non-final-rejection**

1. **Claims rejected:** claims 2 and 12 under § 112(b) as indefinite.
2. **Claims with allowable subject matter:** claims 1, 3–11, and 13–15 are in condition for allowance over the prior art of record. Claims 2 and 12 recite allowable subject matter that would be placed in condition for allowance by the amendments identified in the claim-compliance table (correct the duplicated "input of the input" in claim 2; rewrite claim 12's couplings to remove the nested "first CNOT gate of the first CNOT gate," fix "an the output," and either add antecedent basis in claim 10 for "second CNOT gate of the second Bell state generator" or re-label the coupling target).
3. **Claim-compliance defects that matter most for prosecution or post-grant validity:** the claim 12 antecedent-basis / nested-reference defects are the most serious because claim 12 defines the inter-BSO quantum coupling — the structural feature that makes the two-BSO embodiment distinctive. An IPR petitioner challenging validity would concentrate here. Claim 2's defect is minor but literal.
4. **Full-application defects in the specification, formalities, or required sections:** none identified that would independently support a rejection; see the full-application review table below. The specification is verbose but substantively supports the claimed topologies.
5. **Single strongest ground the applicant must overcome:** § 112(b) indefiniteness of claim 12's quantum coupling circuit language. This is the one issue that clearly survives grounding constraints.

### Full application review

USPTO standard applied (§ 112(a) written description, enablement, best mode; MPEP 608 formalities; title, abstract, drawings, brief description, detailed description, claim support).

| Area | Standard | Pass / defect | Evidence from application | Required fix |
|---|---|---|---|---|
| Claims | USPTO § 112(b) | Defect in claims 2 and 12 | Duplicated "input of the input" (claim 2); nested "first CNOT gate of the first CNOT gate," "an the output," and missing antecedent for "second CNOT gate of the second Bell state generator" (claim 12). | Amend claims 2 and 12 as detailed in the claim-compliance table. |
| Specification support | USPTO § 112(a) | Pass | FIG. 2A/2B supports claim 1; FIG. 4A supports claim 2; FIG. 4B supports claims 3–9; FIG. 5 supports claims 10–15. Transfer matrices B, B², B³, B⁴ are worked out with examples 1–4. | None. |
| Enablement / possession | USPTO § 112(a) | Pass for claimed structural scope | Photonic implementations disclosed (FIGS. 9, 10A–D, 11A–B, 12A–B); Patel *et al.* 2016 cited for experimental Fredkin. Wands factors favor enablement of the claimed topology. Note: the specification's *signaling* discussion (submarine, GPS-P(Y)) is not claimed and is not evaluated here. | None for claimed scope. |
| Formalities / required sections | USPTO MPEP 608 | Pass | Title, abstract, cross-reference to provisional 62/430,501, technical field, background, summary, brief description of drawings, detailed description, references, and claims are all present. | None. |
| Drawings / abstract / title | USPTO | Pass | Drawings FIGS. 1A–12B present and described. Abstract present. Title accurate as to hardware but overstates as to "coherence preservation" (see Quantum Specialist note 1). | Optional: narrow title to reflect BSO ring topology. |

### Rejections of record
- § 101: none
- § 102: none
- § 103: none
- § 112: 2, 12
- allowable: 1, 3–11, 13–15

## Vote table

| Voice | Recommended disposition | Confidence 1-10 |
|---|---|---|
| Primary Examiner | allowance (§ 101 eligible; no other statute in this voice) | 9 |
| § 102 Examiner | allowance (no art of record) | 10 |
| § 103 Examiner | allowance (no art of record) | 10 |
| § 112 Examiner | non-final-rejection (claims 2, 12) | 8 |
| Quantum Technical Specialist | allowance (hardware topology operable; extra-claim signaling concerns not claimed) | 8 |
| Supervisory Patent Examiner | non-final-rejection | 8 |