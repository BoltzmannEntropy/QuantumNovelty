# UNITED STATES PATENT AND TRADEMARK OFFICE
## OFFICE ACTION — Post-Grant Review Panel Assessment
### Application: US10614371B2 ("Debugging quantum circuits by circuit rewriting")
### Assignee: International Business Machines Corp.
### Panel: Post-Grant / IPR-style validity review

---

**Preliminary statement regarding prior art of record:** No external prior-art references were placed of record for this examination. Accordingly, no § 102 anticipation rejection and no § 103 obviousness rejection may be sustained on this record. The panel confines its substantive rejections to defects evident on the face of the specification and claims under §§ 101 and 112, and expressly declines to fabricate art from memory. Any § 102/§ 103 discussion below is limited to noting the absence of art of record.

---

## Voice 1 — Primary Examiner (§ 101 eligibility + overall)

The claims fall in two structural families: (a) system claims reciting a memory, a processor, and named "components" (claims 1–8, 22–25); (b) computer-implemented method claims (claims 9–14, 19–21); and (c) a computer program product on a non-transitory computer-readable storage medium (claims 15–18). All are directed to rewriting a source quantum circuit into instrumented circuits, executing those instrumented circuits on a quantum computer, and processing the resulting measurement data to infer internal state/process information about the quantum computer.

**Step 2A Prong One.** The claims arguably recite mathematical concepts (circuit rewriting rules, propagation of causal influence, tomographic reconstruction). However, the recitation of rewriting rules and reconstruction algorithms is coupled in every independent claim to (i) *execution* of the rewritten circuits on a quantum computer to *obtain measurement data*, and (ii) processing of that measurement data to output information about internal states/processes of the *quantum computer*. This is not a bare mental process — measurement of qubits is a physical operation on a QPU, and the specification is explicit that the underlying problem (observing internal quantum state without collapse) is a hardware-rooted problem that cannot be performed mentally (spec: "measurement of an internal state changes the execution outcome and is an irreversible process").

**Step 2A Prong Two / Step 2B.** Every independent claim (1, 9, 15, 19, 22) is integrated into a practical application: it improves the *operation of a quantum processor* by enabling debug-style state/process inference that would otherwise be impossible because of measurement-induced collapse. The rewriting step is not decorative — it is what makes the physical execution meaningful (removing dead code past a measurement, propagating causal influence forwards/backwards relative to a breakpoint). This is an improvement to the functioning of a quantum machine, analogous to *Enfish* / *Finjan* improvements to a computer, not an *Alice*-style abstract idea implemented on a generic computer.

Dependent claims narrow to specific tomographic techniques (claims 7, 8, 10, 11, 20, 21, 24, 25), API surfaces (claims 3, 16, 17, 18), breakpoint semantics (claims 4, 5, 12, 13), and dead-code removal (claims 14, 23) — all of which remain tied to the QPU-operational improvement. None reduces to bare math on a generic computer.

**Verdict:** No claim is directed to a judicial exception without a practical application. **§ 101 is not a valid ground of rejection for any claim.**

| Claim(s) | Statute | Basis (one line) |
|---|---|---|
| 1–25 | § 101 | Eligible — improvement to operation of a quantum computer; not a bare abstract idea. |

---

## Voice 2 — § 102 Examiner (anticipation / novelty)

No prior-art references were placed of record. Under a rigorously grounded § 102 analysis, an anticipation rejection requires a single listed reference disclosing every element as arranged. With an empty art-of-record set, no such reference exists on this record.

I decline to recall or invent references from memory. Accordingly, every claim (1–25) is **novel over the prior art of record** for purposes of this examination. This finding is limited to the present record and does not preclude a future § 102 rejection based on properly placed art.

| Claim | Reference | Element-by-element read |
|---|---|---|
| 1 | none | No anticipating reference of record |
| 2 | none | No anticipating reference of record |
| 3 | none | No anticipating reference of record |
| 4 | none | No anticipating reference of record |
| 5 | none | No anticipating reference of record |
| 6 | none | No anticipating reference of record |
| 7 | none | No anticipating reference of record |
| 8 | none | No anticipating reference of record |
| 9 | none | No anticipating reference of record |
| 10 | none | No anticipating reference of record |
| 11 | none | No anticipating reference of record |
| 12 | none | No anticipating reference of record |
| 13 | none | No anticipating reference of record |
| 14 | none | No anticipating reference of record |
| 15 | none | No anticipating reference of record |
| 16 | none | No anticipating reference of record |
| 17 | none | No anticipating reference of record |
| 18 | none | No anticipating reference of record |
| 19 | none | No anticipating reference of record |
| 20 | none | No anticipating reference of record |
| 21 | none | No anticipating reference of record |
| 22 | none | No anticipating reference of record |
| 23 | none | No anticipating reference of record |
| 24 | none | No anticipating reference of record |
| 25 | none | No anticipating reference of record |

---

## Voice 3 — § 103 Examiner (obviousness)

Obviousness under Graham/KSR requires listed references, properly combined, teaching or suggesting every limitation, together with an articulated rationale to combine. No references were placed of record. No combination is available on this record.

I will not fabricate a primary + secondary reference pair, nor will I recite a "well-known in the art at the time" bare assertion — that is precisely the kind of hand-wave KSR warns against dressing up as a rationale to combine. Accordingly, every claim (1–25) is **non-obvious over the prior art of record** for purposes of this examination.

| Claim | Primary + Secondary | Rationale to combine |
|---|---|---|
| 1–25 | none | No supporting combination of record |

---

## Voice 4 — § 112 Examiner (enablement / written description / definiteness)

The specification (BACKGROUND, SUMMARY, DETAILED DESCRIPTION, and FIGS. 1–12) is included in this examination. I examine (a) enablement, (b) written description, and (b) definiteness.

**(a) Enablement — § 112(a).** The specification describes two concrete rewriting approaches — forward propagation and backward propagation of instrumentation influence relative to a breakpoint (FIGS. 5–8) — and points to well-known state tomography and process tomography as the reconstruction mechanism. A PHOSITA in quantum circuit compilation (as of the 2017 priority date) would be able to implement circuit rewriting on QASM-form representations, propagate causal influence within the "past/future light cone" of a breakpoint, and apply standard tomographic reconstruction, without undue experimentation. The specification does not claim broad functional endpoints such as "fault-tolerant" or "with high fidelity" — the claims are directed to the mechanics of rewriting, executing, and post-processing, which the spec enables. **No § 112(a) enablement defect is identified.**

**(b) Written description — § 112(a).** The specification demonstrates possession of (i) breakpoint insertion between quantum instructions (claims 4, 5, 12, 13; spec ¶ discussing FIG. 4), (ii) forward and backward causal-influence propagation (claims 1, 9, 15, 19, 22; FIGS. 5–8), (iii) dead-code removal as a consequence of instrumentation (claims 14, 23; spec discussion of "dead" code after measurement), (iv) state and process tomography (claims 7, 8, 10, 11, 20, 21, 24, 25; spec statistical estimation component 118), and (v) API-mediated parameter/data flow (claims 3, 16, 17, 18; spec user interface 106/122). **No § 112(a) written-description defect is identified.**

**(b) Definiteness — § 112(b).** I flag the following concrete defects:

1. **Claim 1 — "removal of dead code of the software code corresponding to one or more qubits whose state is causally connected to the instrumentation instruction information."** The antecedent structure is ambiguous: it is unclear whether "dead code . . . corresponding to one or more qubits" means dead code that (i) is *itself* causally connected to the instrumentation, or (ii) operates on qubits whose state is causally connected. Grammatically the modifier attaches to "qubits", not "dead code", which is the opposite of what the specification describes (dead code is removed *because* it lies outside the light cone of measurement — i.e., is *not* causally connected). This ambiguity — arguably an outright inconsistency between claim and spec — is a genuine § 112(b) definiteness issue. Claims 15 and 19 recite the same limitation and inherit the defect.

2. **Claim 1 — "a source quantum circuit representation that represents to the source quantum circuit."** The phrase "represents *to* the source quantum circuit" is grammatically broken. It appears to be a scrivener error for "represents *the* source quantum circuit" (as recited in claims 9, 15, 19, 22). As issued, the phrase is indefinite because a PHOSITA cannot determine what relationship "represents to" denotes. **§ 112(b) defect.**

3. **Claim 12 — "the breakpoint . . . comprises a partition of one or more qubits."** A "breakpoint" is described in the spec as an insertion point in code; the claim says the breakpoint *comprises a partition of qubits*. The scope of "partition of one or more qubits" and how a breakpoint can *comprise* qubits (as opposed to referencing them) is not reasonably certain from the claim language. The spec supports "the breakpoint includes a (partial) partition of the system's qubits", so the defect is on the borderline — I flag it as a marginal § 112(b) issue that would be cleared by amending "comprises" to "identifies" or "specifies".

4. **Claim 6, 22 — "statistical estimation component that evaluates / processes the measurement data to infer information corresponding to one or more internal states or processes."** The term "component" plus purely functional language ("that evaluates", "that processes") raises a § 112(f) means-plus-function question. Under *Williamson v. Citrix*, "component" is a generic nonce term and functional-only recitation triggers § 112(f). The specification does disclose corresponding structure (statistical estimation component 118 performing state/process tomography and reconstruction), so § 112(f) treatment, if invoked, is *supported* — but the claim should either recite the structure or the panel should note the § 112(f) invocation explicitly. This applies equally to "circuit rewriting component" and "execution component" (claims 1, 22). Flag as § 112(f) invocation notice, not a rejection defect per se.

5. **Claim 9 — "measurement data corresponding to different locations in the source quantum circuit"** vs. **claims 15, 19 — "measurement data corresponding to different state data of qubits within the source quantum circuit."** Claim 9's "different locations" is arguably clearer than the parallel claims' phrasing, but the divergence between siblings is not a defect on its own. No rejection.

### Claim compliance review (USPTO)

| Claim(s) | Standard | Issue | Specific feedback | Amendment target |
|---|---|---|---|---|
| 1, 15, 19 | USPTO § 112(b) | Grammatical/logical inversion in "dead code . . . corresponding to one or more qubits whose state is causally connected to the instrumentation instruction information" | Modifier attaches to "qubits" — but dead code is code *outside* the causal light cone. Claim reads opposite to spec. | Rewrite: "removal of dead code of the software code corresponding to one or more qubits whose state is *not* causally connected to the instrumentation, based on propagating . . ." |
| 1 | USPTO § 112(b) | "represents to the source quantum circuit" is grammatically broken | Scrivener error; renders scope uncertain | Amend "represents to the source quantum circuit" → "represents the source quantum circuit" |
| 12 | USPTO § 112(b) marginal | "breakpoint comprises a partition of one or more qubits" | Breakpoint is a code marker; qubits are physical; "comprises" mis-fits | "the breakpoint . . . *identifies* a partition of one or more qubits" |
| 1, 6, 22 | USPTO § 112(f) invocation notice | "circuit rewriting component", "statistical estimation component", "execution component" — nonce term + purely functional recitation | Under *Williamson*, § 112(f) is invoked; construction is limited to structure disclosed in spec (blocks 110, 114, 118 + equivalents) | No amendment required; note invocation on the record |
| 3, 16, 17 | USPTO § 112(b) marginal | "one or more analysis parameters" is undefined | "Analysis parameters" broad but supported by spec (block 444) | Optional narrowing tie to spec examples |
| 2 | USPTO § 112(d) dependency | "applies circuit rewriting rules based on the instrumentation instruction information" — claim 1 already recites rewriting based on that information | Arguably fails to further limit | Recite specific rewriting rules (dead-code removal, causal propagation) explicitly |

Per-claim § 112 table:

| Claim | Sub-section | Defect |
|---|---|---|
| 1 | § 112(b) | "represents to" (broken); causal-connection modifier attaches to wrong noun |
| 2 | § 112(d) marginal | Arguably no further limitation |
| 3 | § 112(b) — allowable as is | "Analysis parameters" broad but supported |
| 4 | — | No defect |
| 5 | — | No defect |
| 6 | § 112(f) invoked | Structure disclosed |
| 7 | — | No defect |
| 8 | — | No defect |
| 9 | — | No defect |
| 10 | — | No defect |
| 11 | — | No defect |
| 12 | § 112(b) marginal | "breakpoint comprises a partition of . . . qubits" |
| 13 | — | No defect |
| 14 | — | No defect |
| 15 | § 112(b) | Same causal-connection modifier defect as claim 1 |
| 16 | — | No defect |
| 17 | — | No defect |
| 18 | — | No defect |
| 19 | § 112(b) | Same causal-connection modifier defect as claim 1 |
| 20 | — | No defect |
| 21 | — | No defect |
| 22 | § 112(f) invoked | Structure disclosed |
| 23 | — | No defect |
| 24 | — | No defect |
| 25 | — | No defect |

---

## Voice 5 — Quantum Technical Specialist (operability / quantum-specific)

The invention is quantum-operationally sound. The specification correctly identifies the core physical constraint (measurement collapse; no direct single-stepping) and offers a physically legitimate workaround: run *many* rewritten instances of the circuit, each measuring at a different point, and reconstruct the internal state/process by *state tomography* or *process tomography* — both are well-established primitives whose validity is independent of any speedup or fault-tolerance assumption.

Points of technical note:

1. **Forward/backward causal-influence propagation.** The "past light cone" / "future light cone" language (FIGS. 5–8, discussion at block 660 and block 880) is a physically correct abstraction of causal reachability in a quantum circuit under unitary + measurement operations. Dead-code removal outside the light cone of a measurement is sound: gates that cannot influence, and cannot be influenced by, the measurement can be dropped without altering the measurement statistics on the partitioned qubits.

2. **Dead-code caveat.** The spec correctly notes the constraint that this optimization "assumes that the gates act only on the intended qubits" — i.e., no crosstalk on physical hardware. This is a real hardware caveat but not an operability defect for the claimed invention, which is a compilation/rewriting technique operating on the *logical* circuit representation.

3. **Tomography.** State tomography (claims 7, 10, 21, 24) and process tomography (claims 8, 11, 20, 25) are standard reconstruction techniques whose scaling (exponential in number of qubits in the partition) is understood in the art. The claims do *not* assert scalable or fault-tolerant reconstruction — they claim the mechanism, not a scaling result. No overreach.

4. **No violation of physical constraints.** The claims do not implicate no-cloning (no qubit state is copied), Holevo (no superluminal information extraction is claimed), or complexity assumptions. The invention is a *debug harness*, not a speedup claim.

5. **Machine-learning language in the spec.** The spec's laundry list of ML techniques (SVMs, HMMs, Bayesian networks, deep belief networks, etc., in the DETAILED DESCRIPTION) is unmoored from any actual claim limitation — none of the 25 claims recites ML at all. This creates no operability problem, but it is noise that would draw scrutiny in any future continuation attempting to claim ML embodiments.

**Operability verdict:** the invention operates as claimed under the physics; no § 112(a) enablement objection is triggered by any inoperability finding, and no § 101 "law of nature" overreach is present.

---

## Voice 6 — Supervisory Patent Examiner (SPE) — synthesis + disposition

Reconciling the panel:

- Primary Examiner: § 101 eligible across the board.
- § 102 Examiner: no anticipating art of record; all claims novel on this record.
- § 103 Examiner: no combinations of record; all claims non-obvious on this record.
- § 112 Examiner: concrete definiteness defects in claims 1, 15, 19 (grammatical/logical modifier inversion + "represents to" scrivener error) and marginal definiteness in claim 12; § 112(f) invoked but supported for "component" limitations in claims 1, 6, 22.
- Quantum Technical Specialist: physically operable, no overreach.

There is a genuine split. The § 101, § 102, § 103, and quantum voices all reach allowability. The § 112 voice identifies real, non-trivial definiteness defects in three independent claims (1, 15, 19) and one dependent claim (12). Under USPTO practice, a definiteness rejection to one or more claims requires a non-final Office Action; it does not require rejecting the remainder of the claim set.

The most consequential defect is the causal-connection modifier in independent claims 1, 15, and 19: the plain grammar attaches "whose state is causally connected to the instrumentation" to "qubits", producing a claim scope that is the *opposite* of what the specification describes as dead code (dead code is code operating on qubits *outside* the causal cone). A reasonable examiner cannot allow a claim where the plain reading contradicts the disclosure — that is precisely a § 112(b) reasonable-certainty failure under *Nautilus*.

`Disposition: non-final-rejection`

Rejection summary:
1. Claims rejected: **1, 12, 15, 19** under 35 U.S.C. § 112(b) (definiteness). Claims 15 and 19 inherit the causal-connection modifier defect; claim 1 also carries the "represents to" scrivener defect; claim 12 carries the "breakpoint comprises a partition of qubits" marginal defect.
2. Allowable subject matter is present in every claim; the § 112(b) defects are curable by non-substantive amendment. Amendments proposed in the compliance table above (rewrite modifier polarity; fix "represents to"; change "comprises" → "identifies" in claim 12) would place the entire claim set in condition for allowance. Dependents 2–8, 10, 11, 13, 14, 16–18, 20, 21, 23–25 stand allowable pending correction of their independent claims.
3. Prosecution-relevant compliance defects: (a) § 112(f) invocation notice on "component" terms in claims 1, 6, 22 — construction limited to structure disclosed in the spec + equivalents; (b) claim 2 arguably lacks further limitation over claim 1 (§ 112(d)); (c) sibling-claim divergence between claim 9's "different locations" and claims 15/19's "different state data of qubits" is stylistic, not defective.
4. Full-application defects: see checklist below. The specification is adequate but carries several formalities/style issues.
5. Strongest rejection to overcome: the § 112(b) modifier inversion in claims 1, 15, 19 — a straight corrective amendment.

### Full application review

| Area | Standard | Pass / defect | Evidence from application | Required fix |
|---|---|---|---|---|
| Claims — definiteness | USPTO § 112(b) | Defect (claims 1, 12, 15, 19) | Causal-connection modifier attaches to "qubits"; "represents to"; "breakpoint comprises a partition of qubits" | Amend as specified in claim compliance table |
| Claims — § 112(f) | USPTO § 112(f) | Invocation supported | Structure disclosed at debugger 102, rewriting component 110, execution component 114, statistical estimation component 118 | Record § 112(f) construction |
| Claims — dependency (§ 112(d)) | USPTO § 112(d) | Marginal (claim 2) | Claim 2 recites rewriting rules "based on the instrumentation instruction information" — claim 1 already imports this | Rewrite claim 2 to add a concrete rule (dead-code removal, forward/backward propagation) |
| Specification support | USPTO § 112(a) | Pass | FIGS. 4–8 + associated text disclose breakpoint insertion, forward/backward propagation, dead-code removal, tomography | None |
| Enablement / possession | USPTO § 112(a) | Pass | Two rewriting approaches enabled at PHOSITA level; tomography well-known | None |
| Formalities / required sections | USPTO MPEP 608 | Pass with note | Standard sections present (Background, Summary, Description of Drawings, Detailed Description) | None |
| Drawings | MPEP 608 | Pass | FIGS. 1–12 referenced and described | None |
| Abstract | MPEP 608.01(b) | Pass | Under 150 words; describes technical solution | None |
| Title | MPEP 606 | Pass | "Debugging quantum circuits by circuit rewriting" is descriptive | None |
| Spec — ML laundry list | Style / clarity | Note (non-defect) | DETAILED DESCRIPTION recites SVMs, HMMs, Bayesian networks, deep belief networks etc. with no claim tie | Consider trimming in any continuation — noise for continuations attempting ML claims |
| Best mode | USPTO § 112(a) (pre-AIA; still-advisory post-AIA) | Pass | Two concrete approaches (forward/backward propagation) disclosed | None |

### Rejections of record
- § 101: none
- § 102: none
- § 103: none
- § 112: 1, 12, 15, 19
- allowable: 2–11, 13, 14, 16–18, 20–25 (allowable pending correction of their independent claims 1, 15, 19 for those that depend from them)

## Vote table

| Voice | Recommended disposition | Confidence 1-10 |
|---|---|---|
| Primary Examiner | allowance (§ 101 alone) | 9 |
| § 102 Examiner | allowance (no art of record) | 10 |
| § 103 Examiner | allowance (no art of record) | 10 |
| § 112 Examiner | non-final-rejection (claims 1, 12, 15, 19) | 7 |
| Quantum Technical Specialist | allowance | 9 |
| Supervisory Patent Examiner | non-final-rejection | 7 |