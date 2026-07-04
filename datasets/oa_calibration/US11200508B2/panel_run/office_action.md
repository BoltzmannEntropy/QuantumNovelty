# OFFICE ACTION — Post-Grant Review

**Application:** US11200508B2 — "Modular control in a quantum computing system"
**Assignee:** Rigetti and Co LLC
**Claims examined:** 1–22 (all)
**Status:** Granted (B2). Panel proceeds as post-grant reviewer / IPR petitioner.
**Prior art of record:** NONE placed of record. Panel is expressly barred from citing anticipating or obviousness references from memory. Novelty (§ 102) and non-obviousness (§ 103) presumed absent art.

---

## Voice 1 — Primary Examiner (§ 101 eligibility + overall)

The claims are examined under the Alice/Mayo framework with careful attention to Step 2A Prong Two and Step 2B, which control the disposition here.

**Step 2A Prong One.** Claims 1 and 12 recite assigning subsets of qubit devices to cores, identifying boundary qubits, generating control sequences, and delivering control signals to physical hardware. The "assigning" and "identifying" steps, viewed in isolation, could arguably be characterized as mental steps or an abstract data-organization concept. Dependent claims 5 and 16 recite evaluating a cost function based on an identity error syndrome and minimizing it — arguably mathematical concept. Claims 9 and 20 recite a "unitary operator defined over a Hilbert space" — a mathematical construct. Under Prong One, these limitations touch judicial exceptions.

**Step 2A Prong Two / Step 2B.** Every independent claim is anchored to concrete quantum hardware. Claim 1 requires: (i) a "quantum processor" with physical "qubit devices"; (ii) a "signal delivery system" that receives and delivers *control signals* to that processor; and (iii) actual application of those control signals to the respective cores. Claim 12 is directed to the physical apparatus itself — a "quantum processor comprising an array of qubit devices," a control system, and a signal delivery system. This is not mathematics performed on a generic computer; it is a control architecture that operates a QPU. The purported improvement — modular, core-scoped control that constrains boundary qubits to identity so that cores can be actuated in parallel without full analytic tune-up of every gate primitive — is an improvement to the *operation of a machine* (the quantum processor). That falls squarely within the class of technological improvements the Federal Circuit has held eligible (improvement to the functioning of a computer/machine).

The mathematical elements in claims 5, 9, 16, and 20 do not transform the claims into abstract ideas. Every one of them is recited in the context of generating or defining a *control sequence that is delivered as a physical signal to a QPU core*. They are integrated into the practical application of operating quantum hardware.

**Conclusion under § 101.** No claim is directed to a bare mathematical concept or mental process on a generic computer. Every claim recites or is tied to concrete quantum hardware and to an operational improvement in how that hardware is driven. All claims are patent-eligible.

| Claim(s) | Statute | Basis (one line) |
|---|---|---|
| 1–11 | § 101 | Eligible: method operates a quantum processor via signal-delivery hardware; integrated practical application. |
| 12–22 | § 101 | Eligible: apparatus claim reciting quantum processor, control system, and signal delivery system. |

No § 101 rejection is sustained.

---

## Voice 2 — § 102 Examiner (anticipation / novelty)

No prior art was placed of record for this examination. Under the ground rules stated at the top of this Action, I may cite only references appearing in the "Prior art of record" list, and that list is empty. I therefore cannot construct an element-by-element anticipation read for any claim.

I note affirmatively that a proper § 102 rejection requires a single reference disclosing every limitation arranged as claimed. Without any listed reference, no such showing is possible on this record. Claims 1–22 are accordingly **novel over the prior art of record**.

I flag for the file that a real post-grant proceeding on this patent would ordinarily develop art in the superconducting-qubit control literature (transmon control, optimal control theory / GRAPE-style pulse engineering, quantum compilers targeting subsets of qubits) and in earlier Rigetti and IBM disclosures pre-dating the March 10, 2017 priority date. Absent such art of record, that inquiry is beyond the scope of this Action.

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
| 21 | none | no anticipating reference of record |
| 22 | none | no anticipating reference of record |

No § 102 rejection is sustained.

---

## Voice 3 — § 103 Examiner (obviousness)

The Graham/KSR analysis requires (i) determining the scope and content of the prior art, (ii) ascertaining the differences between the prior art and the claims, (iii) resolving the level of ordinary skill, and (iv) considering objective indicia. Step (i) fails at the threshold: no prior art has been placed of record. I have no primary reference and no secondary reference to combine, and I am expressly barred from importing references from memory or from generalized knowledge of the field.

Consequently, I cannot articulate the KSR rationale-to-combine on any actual reference pair. Any obviousness rejection I attempted to write would rest on an invented combination, which the panel's ground rules identify as a hard error.

I note the specification asserts objective indicia relevant to non-obviousness (the modular approach as a way to sidestep gate-by-gate calibration and to scale OCT beyond the classically tractable core size). Those would be weighed against art if any were of record.

| Claim | Listed primary + secondary | Rationale to combine |
|---|---|---|
| 1–22 | none | no supporting combination of record |

No § 103 rejection is sustained.

---

## Voice 4 — § 112 Examiner (enablement / written description / definiteness)

I address § 112(a) and § 112(b) separately.

**§ 112(a) — written description and enablement.** The specification is provided in full. It describes: the modular-core architecture (FIGS. 1, 3A, 3B); the assignment of qubit subsets to cores with boundary qubits between them; the use of an identity target on boundary qubits and a cost function penalizing boundary excitation; the use of numerical optimal control theory (GRAPE) with closed-loop hardware calibration (Ad-HOC) to synthesize pulses; the signal-delivery chain between control electronics and the QPU; and dynamic reassignment of cores across algorithm steps. This is commensurate with the scope of what the claims actually cover — a control-system method and apparatus that generates and delivers control sequences with identity operations on boundary qubits. The written-description and enablement inquiries do not require the specification to teach an unbounded, fault-tolerant, arbitrary-scale quantum computer; the claims do not require it. Claims 1 and 12 are supported. Claims 5/16 (cost-function minimization on identity error syndrome), 8–10 / 19–21 (instruction sets, unitary operator over the Hilbert space of the core, gate sequences), and 11/22 (reassignment) are all supported by the corresponding passages of the detailed description.

**§ 112(b) — definiteness.** The claims are drafted in reasonably clear method / apparatus form. I examined the following flagged terms and found them adequately definite in context:

- "Boundary qubit devices residing between the cores" — the specification illustrates this in FIGS. 3A / 3B and defines boundary qubits as those not assigned to any core between two adjacent cores. Clear in context.
- "Identity operation" applied to boundary qubits — a term of art in quantum information (the identity unitary Î ). Definite.
- "Identity error syndrome" (claims 5, 16) — defined in the specification as errors observed on the boundary qubits relative to the identity target. Definite.
- "Cost function" (claims 5, 16) — functional but supported by the description of infidelity minimization; not indefinite.
- "Core" — the specification supplies a clear operational definition (a logically or hardware-designated subset of qubit devices treated as a unit for gate-set optimization). Definite.

I do not find § 112(f) means-plus-function claiming. The apparatus claim recites "control system configured to" and "signal delivery system configured to" perform specified operations; those are structural recitations tied to disclosed structure (data processors, signal generators, filters, attenuators, couplers, cabling), not nonce-word "means for" recitations.

No antecedent-basis errors of substance were identified. Claim 4 introduces "first control sequences" by re-labeling the previously-recited "control sequences" — proper. Claim 15 mirrors that. Claim 11 refers to "the cores" as "a first set of cores" then defines "a second, distinct set of cores" — proper.

Claims 1–22 are allowable under § 112.

| Claim | Sub-section | Specific defect |
|---|---|---|
| 1–22 | § 112(a) | none — specification supports the claimed scope |
| 1–22 | § 112(b) | none — terms are reasonably certain in context |
| 1–22 | § 112(f) | none invoked — structure recited or referenced |

### Claim compliance review

| Claim(s) | Standard | Issue | Specific feedback | Amendment target |
|---|---|---|---|---|
| 1, 12 | USPTO § 112(b) | Pass | Independent claims recite clear structure/steps with antecedent basis. | None required. |
| 4, 15 | USPTO § 112(b) | Pass | Re-labeling of "control sequences" as "first control sequences" then introducing "second control sequences" is proper. | None. |
| 5, 16 | USPTO § 112(b) | Pass | "Cost function" and "identity error syndrome" are supported by the detailed description. | None. |
| 8–10, 19–21 | USPTO § 112(b) | Pass | "Instruction sets," "unitary operator … over a Hilbert space," and "sequence of quantum logic gates" are art-recognized and supported. | None. |
| 11, 22 | USPTO § 112(b) | Minor | "The cores comprise a first set of cores" (cl. 11) / "the cores comprise first cores" (cl. 22) both work but 22 is terser; both properly introduce reassignment to a second set. | Optional stylistic harmonization; no rewrite required. |
| 6, 7, 17, 18 | USPTO § 112(b) | Pass | Parallel / serial actuation properly narrows the independent claim. | None. |
| All dependents | USPTO § 112(b) | Pass | Proper dependency form; no multiple-dependent-on-multiple-dependent chains. | None. |

---

## Voice 5 — Quantum Technical Specialist (operability / quantum-specific)

The claimed invention is grounded, buildable engineering. Assigning subsets of physical qubits to logical "cores" and driving each core with a numerically-optimized pulse train — while constraining boundary qubits to identity to suppress crosstalk between cores — is consistent with standard superconducting-transmon physics and with optimal-control-theory pulse synthesis (GRAPE, Ad-HOC, CRAB families). Nothing in the claims requires cloning, transmission above the Holevo bound, or a threshold-theorem construction that the specification fails to disclose.

Points that could have been operability failures but are NOT, on this record:

- No claim asserts fault tolerance, error-correction threshold performance, or an arbitrary fidelity ceiling. The specification mentions ">99.9%" only aspirationally ("may be achieved"); no claim recites a fidelity number, so there is no § 112(a) overreach tied to unproven fidelity claims.
- No claim asserts quantum speedup or a complexity-class result. There is no BQP / BPP claim to police.
- Boundary-qubit identity conditioning is physically reasonable: it is a soft constraint enforced through the OCT cost function, not a claim that boundary qubits are perfectly decoupled. Claim 5's / 16's "identity error syndrome" acknowledges non-zero boundary excitation and closes the loop with a cost-function minimization — this is honest engineering.
- The "always-on" static-coupling transmon architecture with dispersive Jaynes-Cummings interactions described in the spec is a real device family; OCT pulses that null the entangling phase on boundary qubits are physically constructible.

One theoretical caveat, not a rejection: as core size grows, the classical-simulation cost of GRAPE-style optimization scales exponentially in the core Hilbert-space dimension, and the specification acknowledges this ("place significant computational demands on the numerical optimization process"). The claims wisely do not recite a specific core size, so they do not overreach into the classically-intractable regime.

Operability findings: no § 101 "law-of-nature" overreach, no § 112(a) enablement gap, no impossibility. All claims are technically operable within the scope actually recited.

---

## Voice 6 — Supervisory Patent Examiner (SPE) — synthesis and disposition

Reconciling the five voices:

- Voice 1 (§ 101): all claims eligible; the claims recite and operate concrete quantum hardware via a control and signal-delivery chain.
- Voice 2 (§ 102): no prior art of record; every claim is novel on this record.
- Voice 3 (§ 103): no prior art of record; no obviousness combination can be constructed.
- Voice 4 (§ 112): specification supports the claims; terms are definite; no § 112(f) trap; claim compliance clean.
- Voice 5 (Quantum): the invention operates as claimed; no physics overreach, no unsupported fidelity/threshold claims.

There is no examiner disagreement on outcome. Every voice's analysis converges: on this record, no claim can be sustained as rejected under any statute. Sustaining a rejection here would require either (i) importing prior art from memory, which the ground rules forbid, or (ii) manufacturing a § 112 or § 101 defect where none is evident, which is the over-rejection failure mode the ground rules specifically identify.

**Disposition: allowance**

Claims standing rejected: none.

Claims containing allowable subject matter: all of claims 1–22. No amendment is required to place the application in condition for allowance on this record.

Claim-compliance defects that matter most for prosecution / post-grant validity: none of substance. Minor stylistic point — claims 11 and 22 use slightly different phrasings for the "first set of cores → second set of cores" reassignment; harmonization would be cosmetic.

Full-application defects: none of substance on the record before the panel.

Single strongest rejection the applicant must overcome: none on this record. In a real IPR/PGR with developed art, the strongest attack would likely be § 103 obviousness over the pre-2017 body of transmon control and OCT-pulse literature combined with quantum-compiler / subset-partitioning references — but the panel is barred from constructing that combination without art of record, and does not do so.

### Full application review

| Area | Standard | Pass / defect | Evidence from application | Required fix |
|---|---|---|---|---|
| Claims | USPTO § 112(b) | Pass | Two independent claims (1, 12), 20 dependents with proper form and antecedent basis. | None. |
| Specification support | USPTO § 112(a) written description | Pass | Detailed description walks through FIGS. 1, 2, 3A, 3B; covers core assignment, boundary identity, cost function, OCT/GRAPE, Ad-HOC closed-loop calibration, reassignment. | None. |
| Enablement / possession | USPTO § 112(a) enablement | Pass | Wands factors favor enablement: the art (transmon control, OCT pulse synthesis) is well-developed, the specification identifies concrete tools (GRAPE, Ad-HOC), and the claims do not overreach into unenabled fidelity/scale regimes. | None. |
| Formalities / required sections | MPEP 608 | Pass | Cross-reference to provisional, Background, Description of Drawings, Detailed Description, Claims, Abstract all present. | None. |
| Drawings / abstract / title | MPEP 608 | Pass | FIGS. 1, 2, 3A, 3B described in the specification; abstract present and one paragraph; title descriptive of the subject matter. | None. |

### Rejections of record
- § 101: none
- § 102: none
- § 103: none
- § 112: none
- allowable: 1–22

## Vote table

| Voice | Recommended disposition | Confidence 1-10 |
|---|---|---|
| Primary Examiner | allowance | 8 |
| § 102 Examiner | allowance (novel on this record) | 9 |
| § 103 Examiner | allowance (no combination of record) | 8 |
| § 112 Examiner | allowance | 8 |
| Quantum Technical Specialist | allowance (operable as claimed) | 9 |
| Supervisory Patent Examiner | allowance | 8 |