# Office Action — Post-Grant Review

**Application/Patent:** US10915831B2
**Title:** Reduction and/or mitigation of crosstalk in quantum bit gates
**Assignee:** International Business Machines Corp
**Issue date:** 2019-12-18 (priority 2017-09-29)
**Claims examined:** 1–20
**Filing standard applied:** USPTO (35 U.S.C. §§ 101, 102, 103, 112; MPEP)
**Prior art of record:** NONE PLACED OF RECORD. No § 102 or § 103 rejection can be grounded in listed art. Panel confines substantive rejections to § 112 / § 101 defects evident from the four corners of the document.

---

## Voice 1 — Primary Examiner (§ 101 eligibility + overall)

The claims are directed to control of a quantum computing circuit — specifically, the generation, coordination, and calibration of microwave pulses applied to physical qubits to mitigate control crosstalk (an AC-Stark-shift-driven physical error mechanism recited in the Background and Detailed Description). I apply the Alice/Mayo framework and give full weight to Step 2A Prong Two.

**Step 2A Prong One.** Claims 1–7 recite a "system" comprising memory, processor, a signal generation component that "implements a control sequence that comprises a pulsing operation" on physical qubits, and a coordination component that "performs a calibration operation" on channels of a "quantum circuit" to "selectively reduce a crosstalk." Claims 8–14 recite a corresponding method; claims 15–20 a Beauregard-style computer program product. The claims do recite operations expressible mathematically (SU(2), phase rotations, π/2), but the operations act on **physical qubits via physical channels in a quantum circuit** and are directed to a **hardware-level control problem** (control crosstalk between neighboring qubit lines).

**Step 2A Prong Two / Step 2B.** Even assuming a judicial exception is lurking, the claims integrate that exception into a practical application: they improve the operation of a quantum processor by reducing/mitigating control crosstalk during gate execution. The specification ties the improvement to concrete hardware (AWG channels, configurable attenuators, phase-shifters — see written description at FIGS. 5–6 and accompanying text) and to a physical fault mechanism (AC-Stark shift on off-resonant qubits). This is an improvement to the functioning of a machine, in line with *Enfish* and MPEP 2106.05(a). Not abstract.

**CRM claims (15–20).** The preamble recites "a computer readable storage medium" and the specification (¶ discussing "computer readable storage medium ... is not to be construed as being transitory signals per se") expressly disclaims transitory signals. Passes *In re Nuijten* / MPEP 2106.03.

**Note on claim 15 drafting.** The body of claim 15 recites "**a** control sequence that comprises a pulsing operation…" without the verb "implement." This is a § 112(b) drafting problem (the § 112 examiner addresses it) but not a § 101 problem.

All claims 1–20 are patent-eligible.

| Claim(s) | Statute | Basis (one line) |
|---|---|---|
| 1–7 | § 101 | Eligible — improvement to operation of a quantum processor via hardware-tied crosstalk mitigation; passes Prong Two. |
| 8–14 | § 101 | Eligible — method tied to physical qubits and channels; practical application of pulse coordination on a QPU. |
| 15–20 | § 101 | Eligible — Beauregard CRM; specification disclaims transitory signals; same practical application as system/method. |

---

## Voice 2 — § 102 Examiner (anticipation / novelty)

**No prior art was placed of record.** Under the ground rules, I may cite ONLY references appearing in the record. I therefore cannot sustain any § 102 rejection.

I note for completeness that if art were placed of record — for example, contemporaneous IBM/Rigetti/Google publications on simultaneous randomized benchmarking, dynamical decoupling of idle spectator qubits, virtual-Z / frame-change implementations (McKay et al., "Efficient Z gates for quantum computing," Phys. Rev. A 96, 022330 (2017)), or DRAG pulse shaping (Motzoi et al., Phys. Rev. Lett. 103, 110501 (2009)) — an anticipation analysis of claim 1's very broad "performs a calibration operation … to selectively reduce a crosstalk" limitation might be tested. That inquiry is deferred; on this record, no such reference exists.

All claims 1–20 are **novel over the prior art of record** and allowable under § 102.

| Claim | Listed reference | Element-by-element read |
|---|---|---|
| 1 | none | no anticipating reference of record |
| 2 | none | no anticipating reference of record |
| 3 | none | no anticipating reference of record |
| 4 | none | no anticipating reference of record |
| 5 | none | no anticipating reference of record |
| 6 | none | no anticipating reference of record |
| 7 | none | no anticipating reference of record |
| 8 | none | no anticipating reference of record |
| 9 | none | no anticipating reference of record |
| 10 | none | no anticipating reference of record |
| 11 | none | no anticipating reference of record |
| 12 | none | no anticipating reference of record |
| 13 | none | no anticipating reference of record |
| 14 | none | no anticipating reference of record |
| 15 | none | no anticipating reference of record |
| 16 | none | no anticipating reference of record |
| 17 | none | no anticipating reference of record |
| 18 | none | no anticipating reference of record |
| 19 | none | no anticipating reference of record |
| 20 | none | no anticipating reference of record |

---

## Voice 3 — § 103 Examiner (obviousness)

Same posture. Graham factor 1 (scope and content of the prior art) cannot be established with zero references of record. Without at least one listed primary reference, no combination under KSR can be articulated with the required rational underpinning; any attempt would be examiner-supplied hindsight fabricated from memory, which the ground rules forbid.

All claims 1–20 are **non-obvious over the prior art of record** and allowable under § 103.

| Claim | Listed primary + secondary | Rationale to combine |
|---|---|---|
| 1–20 | none | no supporting combination of record |

---

## Voice 4 — § 112 Examiner (enablement / written description / definiteness)

The full specification IS included in the document, so § 112(a) inquiries are available. I apply Wands, *Ariad*, and *Nautilus*.

**(a) § 112(a) enablement.** The specification teaches concrete hardware architectures (single-AWG-channel + per-qubit attenuator + per-qubit phase shifter, FIG. 5; two-channel DRAG-style + per-qubit paired attenuators, FIG. 6), a concrete gate decomposition (`U(a,b,c) = Z(a)·X90·Z(b)·X90·Z(c)`, ¶ discussing FIG. 2), synchronization on integer multiples of the single-qubit gate time (FIG. 4 discussion), and calibration of one X90 per qubit. A PHOSITA in superconducting qubit control could practice the claims without undue experimentation across the disclosed scope. **Enabled.**

**(b) § 112(a) written description.** Independent claims 1, 8, and 15 recite broadly "**a** pulsing operation" and "**a** calibration operation … to selectively reduce a crosstalk." The spec repeatedly emphasizes a **single pulse type** (π/2 / X90) combined with virtual-Z frame changes and lock-step synchronization as the mechanism by which crosstalk becomes calibrable. The broadly-claimed genus of "a calibration operation" untethered from the single-pulse-type / synchronization mechanism is broader than what the inventors demonstrably possessed. Nonetheless, dependents 4–7, 11–14, and 18–20 pull the claims down to species (continuous microwave pulsing; single pulse type; synchronizing; simultaneously applying) that ARE described. On balance, the independent claims skate close to the *Ariad* line but the specification's genus-species discussion (Summary + FIGS. 3–6) is adequate to show possession of the recited breadth. **Described, but noting the breadth issue.**

**(c) § 112(b) definiteness.** Several concrete defects:

1. **Claim 15 — missing verb (grammatical / § 112(b) indefinite).** The Wherefore clause reads:
   > "the program instructions are executable by a processor to cause the processor to:
   > **a control sequence** that comprises a pulsing operation for a first quantum bit … ; and
   > perform a calibration operation …"
   The first bullet lacks a verb. Compare independent claim 8 ("**implementing** … a control sequence") and claim 1 ("**implements** a control sequence"). As issued, claim 15 recites program instructions that cause the processor to **[verb missing] a control sequence**. This is indefinite under § 112(b). This appears to be a printing/prosecution error, but as-issued the claim is unclear; a PHOSITA cannot determine the metes and bounds with reasonable certainty (*Nautilus*). Dependent claims 16–20 inherit the defect.

2. **Antecedent basis — claim 15 recites "**the** crosstalk" and "**the** quantum circuit" in the "perform a calibration operation" step.** "The quantum circuit" has proper antecedent basis in the first (verbless) bullet. "The crosstalk" has NO prior antecedent in the body — the claim recites "reduce **the** crosstalk" without a preceding "a crosstalk." The preamble ("removes crosstalk in a quantum circuit") arguably supplies antecedent basis, and *Energizer* / MPEP 2173.05(e) generally permits preamble-supplied antecedent; I flag but do not sustain a separate rejection on this ground.

3. **"Selectively reduce a crosstalk" (claims 1, 8, 15).** "Selectively" is used without a metric — selectively as opposed to what? Read in light of the specification ("calibrate away … can significantly reduce and/or eliminate crosstalk"), the term is reasonably certain and does not by itself render the claim indefinite. **Not a defect.**

4. **"Frame changes" (claims 2, 9, 16).** Defined in spec (Z gates implemented via frame update). **Not a defect.**

5. **"Single quantum bit SU(2) gate control" (claims 2, 9, 16).** SU(2) is a standard mathematical object; the spec supplies the decomposition. **Not a defect.**

6. **"Continuous microwave pulsing" (claims 4, 11, 18).** Defined and illustrated in FIGS. 3–4. **Not a defect.**

7. **§ 112(f) means-plus-function.** "Signal generation component," "coordination component," "analysis component," "control component," "calibration component" use "component" as a nonce-word substitute for "means." Under MPEP 2181, "component" plus purely functional language can invoke § 112(f). Here the specification discloses corresponding structure (AWG channels, attenuators, phase-shifters, processor executing computer-executable components with disclosed algorithms in FIGS. 7–9). If § 112(f) is invoked, structure IS disclosed. **Not indefinite**, though prosecution history should acknowledge the § 112(f) construction risk.

| Claim(s) | Sub-section | Specific defect |
|---|---|---|
| 15 | § 112(b) | Verb missing from first program-instruction bullet — "the program instructions cause the processor to: **a control sequence that comprises…**" is grammatically incomplete; metes and bounds not reasonably certain. |
| 16–20 | § 112(b) | Depend from indefinite claim 15; inherit the defect. |
| 1–14, 15 (breadth), 15–20 | § 112(a) | No enablement / written-description defect sustained; breadth flagged but adequately described. |
| 1–14 | § 112(b) | No concrete definiteness defect; allowable under § 112. |

### Claim compliance review (USPTO)

| Claim(s) | Standard | Issue | Specific feedback | Amendment target |
|---|---|---|---|---|
| 15 | § 112(b) definiteness | Missing verb ("**implement**") in first program-instruction bullet | Insert "**implement**" so the bullet reads "implement a control sequence that comprises a pulsing operation …"; parallel to claims 1 and 8. | `to: implement a control sequence …; and perform a calibration operation …` |
| 15 | § 112(b) antecedent basis | Preamble supplies "crosstalk" but body says "**the** crosstalk"; borderline. | Either rewrite body to introduce "a crosstalk" and use "the crosstalk" thereafter, or rely on preamble antecedent (MPEP 2173.05(e)). | Introduce "a crosstalk in the quantum circuit" in body. |
| 1, 8, 15 | § 112(b) claim structure | Independent claims recite "a calibration operation" without functional linkage to the single-pulse-type / synchronization mechanism that actually enables calibration. | Consider incorporating the "single pulse type" and/or "synchronizing" limitations into the independents to align claim scope with what the specification actually possesses. | Roll dependent 5/6/12/13/19/20 language into the independents on continuation. |
| 1–20 | § 112(f) risk | "…component that [verb]s…" nonce-word functional claiming. | Acknowledged structure is disclosed (AWG, attenuator, phase-shifter, processor + algorithm); claims survive but litigation will construe under § 112(f). | Optional: recite structure explicitly to opt out of § 112(f). |
| 3, 10, 17 | § 112(b) dependency clarity | "Analyzes the quantum circuit to determine the calibration operation" — "the calibration operation" has antecedent basis in parent; acceptable. | No fix. | — |

---

## Voice 5 — Quantum Technical Specialist (operability / quantum-specific)

The invention is grounded in real superconducting-qubit control physics. Control crosstalk via AC-Stark shift is a well-known effect on cross-resonance-coupled transmon architectures. The core insight — that if every qubit is *always* driven by the same type of pulse (X90) in lock-step, the crosstalk environment becomes state-independent and can be **absorbed into the single-qubit calibration** — is sound engineering. It exploits the fact that virtual-Z gates via frame update (McKay et al. 2017-style) are exact and instantaneous, so the only physical drives are X90s, and those can be synchronized across all qubits.

Physics checks:

- **π/2 (X90) decomposition of SU(2) via `Z·X90·Z·X90·Z`** — correct; any single-qubit unitary is expressible this way (Euler-angle form).
- **AC-Stark shift as crosstalk mechanism** — correctly identified; the disclosed remedy (make the shift *constant* by always driving, then calibrate it out) is physically sensible.
- **Two-qubit-gate duration = integer multiple of single-qubit-gate time** — realistic on IBM cross-resonance architectures.
- **Idle-qubit "active idling" via dynamical decoupling / echo sequences** — standard practice; the claim reads on doing this in lock-step with the X90 grid.
- **DRAG pulse shaping (FIG. 6)** — correctly attributed; two-quadrature amplitude scaling per qubit is the standard implementation.

No inoperability concerns. No no-cloning / Holevo / speedup overreach. The dependent claims that recite "continuous microwave pulsing" (4, 11, 18) accurately describe the lock-step X90 grid shown in FIGS. 3–4 — "continuous" here means "the qubits are never left completely idle," which is what the spec says, not a literal never-off carrier.

**Machine-learning aside (spec ¶ discussing FIG. 1).** The spec's laundry-list of ML techniques (Bayesian, HMM, SVM, deep belief, etc.) is puffery not claimed — none of claims 1–20 recite ML. No operability issue because it is not in the claims.

The technical core is real and works. Claims are technically operable.

---

## Voice 6 — Supervisory Patent Examiner (SPE) — synthesis + disposition

I reconcile the five voices.

- **Primary Examiner:** all claims pass § 101.
- **§ 102 Examiner:** no anticipating art of record — all claims novel.
- **§ 103 Examiner:** no combinable art of record — no § 103 rejection sustainable.
- **§ 112 Examiner:** claim 15 (and dependents 16–20) is indefinite under § 112(b) because of a missing verb in the first program-instruction bullet. Claims 1–14 have no sustained § 112 defect.
- **Quantum Technical Specialist:** operable and physically sound.

The one live rejection is § 112(b) on claim 15 (and 16–20 by dependency). This is a facial drafting defect visible in the issued patent — the program-instruction step lacks a verb ("**implement**" is missing, compare "implementing" in claim 8 and "implements" in claim 1). Under *Nautilus*, a PHOSITA cannot determine the scope of an instruction whose operative verb is absent. This is a real defect, but it is a narrow one; on reissue or in a post-grant amendment context it is trivially fixed by inserting "implement."

Claims 1–14 stand allowed on this record. Claims 15–20 are rejected under § 112(b).

**Disposition: non-final-rejection**

**Rejections sustained:**
- Claim 15 under § 112(b): missing verb renders scope unclear.
- Claims 16–20 under § 112(b): depend from indefinite claim 15.

**Allowable subject matter:**
- Claims 1–14 contain allowable subject matter as issued (no rejection of record).
- Claims 15–20 contain allowable subject matter that would be placed in condition for allowance by inserting "implement" (or an equivalent verb) at the head of the first program-instruction bullet in claim 15, so that it reads in parallel with claim 8.

**Compliance defects most material to post-grant validity:**
1. Claim 15 verb omission (already addressed).
2. Independent claims' breadth — "a calibration operation … to selectively reduce a crosstalk" is broader than the single-pulse-type-plus-synchronization mechanism the specification actually teaches. In an IPR context a challenger with real art of record (e.g., McKay 2017 virtual Z, Motzoi DRAG, Sheldon/Chow cross-resonance calibration papers) would attack claims 1, 8 on that breadth. On this record, however, no such art is before me and I cannot sustain the challenge.
3. § 112(f) nonce-word risk on "…component" language — mitigated by disclosed structure but a live claim-construction issue.

**Full-application defects:** minor — see checklist below. The specification is adequate under § 112(a); the drawings and formalities appear compliant on the face of the document.

**Strongest rejection applicant must overcome:** § 112(b) on claim 15 (verb omission). Trivial to overcome by amendment.

### Full application review (USPTO)

| Area | Standard | Pass / defect | Evidence from application | Required fix |
|---|---|---|---|---|
| Claims (1–14) | § 112(b), MPEP 608.01(m) | Pass | Clear structure, proper dependency, definite terms. | — |
| Claims (15–20) | § 112(b), MPEP 608.01(m) | Defect | Claim 15 first bullet lacks verb ("… cause the processor to: a control sequence that comprises …"). | Insert "**implement**" at head of first bullet. |
| Specification support | § 112(a) written description | Pass | FIGS. 1–6 + accompanying description tie claim terms ("signal generation component," "coordination component," "calibration component," "frame changes," "SU(2) gate control") to disclosed structure and algorithm. | — |
| Enablement / possession | § 112(a) enablement, Wands | Pass | Concrete hardware architectures (FIGS. 5–6), gate decomposition, timing (FIGS. 3–4), and calibration protocol enable PHOSITA practice without undue experimentation. | — |
| Best mode | § 112(a) best mode | Pass on face | Two disclosed hardware implementations (single-AWG-channel; two-channel DRAG); inventors did not visibly conceal a preferred embodiment. | — |
| Formalities (MPEP 608) | Formal | Pass | Title, abstract (single paragraph), background, summary, brief description of drawings, detailed description, claims, all present. | — |
| Abstract | 37 CFR 1.72(b), ≤150 words | Pass | Abstract is a single paragraph within word limit and describes the disclosure. | — |
| Title | 37 CFR 1.72(a) | Pass | Short, descriptive, technical. | — |
| Drawings | 37 CFR 1.83–1.84 | Pass on face | FIGS. 1–10 described in Brief Description; consistent numbering (102, 104, 106, …, 502, 504, …). | — |
| Brief description of drawings | MPEP 608.01(f) | Pass | Present for FIGS. 1–10. | — |
| Detailed description | MPEP 608.01(g) | Pass | Detailed structural and operational description tied to reference numerals. | — |
| Sequence listings / deposits | 37 CFR 1.821 et seq. | N/A | No biological sequences. | — |

### Rejections of record
- § 101: none
- § 102: none
- § 103: none
- § 112: 15, 16, 17, 18, 19, 20
- allowable: 1–14 (as issued); 15–20 (upon insertion of "implement" in claim 15's first program-instruction bullet)

## Vote table

| Voice | Recommended disposition | Confidence 1-10 |
|---|---|---|
| Primary Examiner | allowance under § 101 for all claims | 9 |
| § 102 Examiner | allowance (no art of record) | 10 |
| § 103 Examiner | allowance (no art of record) | 10 |
| § 112 Examiner | non-final-rejection (claims 15–20 under § 112(b); 1–14 allowable) | 8 |
| Quantum Technical Specialist | operability confirmed; defer disposition to statutory voices | 9 |
| Supervisory Patent Examiner | non-final-rejection | 8 |