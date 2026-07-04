# Office Action — US11455207B2

**Application:** US11455207B2 — "Using flag qubits for fault-tolerant implementations of topological codes with reduced frequency collisions"
**Assignee:** International Business Machines Corp.
**Claims examined:** 1–25
**Filing standard:** USPTO (post-grant / IPR posture)
**Prior art of record:** NONE placed of record.

Preliminary note on the record: No prior-art references were placed of record for this examination. Under the ground rules of this proceeding, the panel MUST NOT cite anticipating or obviousness references from memory. All § 102 and § 103 analyses are therefore confined to what the record supports; substantive rejections, if any, are limited to §§ 101 and 112 defects evident from the four corners of the document.

---

## Voice 1 — Primary Examiner (§ 101 eligibility + overall)

The claims fall into four buckets: a method of quantum error correction operating on a physical qubit lattice (claims 1–11); a method for decoding topological codes via weight-matching graphs derived from flag-qubit measurements (claims 12–17); a quantum system comprising a quantum processor with a specified qubit lattice (claims 18–24); and a non-transitory computer-executable medium that, when executed by a quantum computer, causes a quantum processor to perform stabilizer / gauge measurements and fault-tolerant correction (claim 25).

**Step 2A Prong One.** Claims 1–11 and 18–25 recite operations on and structural arrangements of physical qubits — data qubits, ancilla qubits, and flag qubits — physically arranged in a lattice pattern on the surface of a quantum processor, with specified nearest-neighbor CNOT interactions and stabilizer / gauge-operator measurements. This is not a bare mathematical concept or mental process; it is manipulation of a specific hardware substrate. Claims 12–17 (decoding) recite measuring a flag qubit (a physical measurement), assigning and updating edge weights on a matching graph derived from that physical measurement, and correcting an error on physical edges (data qubits). The decoding sub-step (weight assignment, minimum-weight-path selection) is mathematical, but the claim is anchored to a physical measurement of a flag qubit and a physical correction on data qubits.

**Step 2A Prong Two / Step 2B.** Even to the extent claims 12–17 recite a mathematical procedure (minimum-weight perfect matching over a weighted graph), that procedure is integrated into a practical application: it improves the operation of a quantum processor by enabling fault-tolerant correction "up to the full code distance" on a specific low-degree lattice designed to reduce microwave frequency collisions in fixed-frequency transmon architectures. This is a concrete improvement to the functioning of a machine (a quantum processor), squarely within *Enfish* / *McRO*-type eligibility. The specification ties the decoder directly to physical flag-qubit measurement outcomes and to the physical CNOT scheduling of Figs. 4 and 8.

Claim 25 recites a non-transitory computer-executable medium — statutory subject matter under Beauregard — and expressly requires execution by a quantum computer with a specified physical lattice, which further confirms integration into a practical application.

No claim is directed to a law of nature (no claim asserts a physical constant or a natural correlation). No claim reduces to a bare mental step; the flag-qubit measurement and the physical correction cannot be performed in a human mind.

**§ 101 verdict:** All claims are patent-eligible. No § 101 rejection is sustained.

| Claim(s) | Statute | Basis (one line) |
|---|---|---|
| 1–11 | § 101 | Eligible — improvement to operation of a quantum processor via specified physical qubit lattice and flag-based fault-tolerant correction. |
| 12–17 | § 101 | Eligible — decoding method anchored to physical flag-qubit measurement and physical error correction on data qubits; practical application. |
| 18–24 | § 101 | Eligible — machine claim reciting concrete quantum-processor hardware arrangement. |
| 25 | § 101 | Eligible — Beauregard medium executed by a quantum computer with recited physical lattice. |

---

## Voice 2 — § 102 Examiner (anticipation / novelty)

No prior-art references were placed of record. Under the constraint that only listed references may support a § 102 rejection, and none exist here, I cannot sustain an anticipation rejection against any claim. I have not searched my memory for candidate anticipations (Chamberland-Beverland flag-qubit papers, Bacon-Shor original, Kitaev toric-code disclosures, etc.), and I do not cite them, because doing so would fabricate the record.

Claims 1–25 are therefore treated as **novel over the prior art of record**. This is a record-limited finding, not an affirmative determination that the claimed subject matter is novel over all art that could be searched; a third party in a post-grant proceeding would be expected to place actual references of record before this finding could be revisited.

| Claim | Listed reference | Element-by-element read |
|---|---|---|
| 1 | none | No anticipating reference of record. |
| 2 | none | No anticipating reference of record. |
| 3 | none | No anticipating reference of record. |
| 4 | none | No anticipating reference of record. |
| 5 | none | No anticipating reference of record. |
| 6 | none | No anticipating reference of record. |
| 7 | none | No anticipating reference of record. |
| 8 | none | No anticipating reference of record. |
| 9 | none | No anticipating reference of record. |
| 10 | none | No anticipating reference of record. |
| 11 | none | No anticipating reference of record. |
| 12 | none | No anticipating reference of record. |
| 13 | none | No anticipating reference of record. |
| 14 | none | No anticipating reference of record. |
| 15 | none | No anticipating reference of record. |
| 16 | none | No anticipating reference of record. |
| 17 | none | No anticipating reference of record. |
| 18 | none | No anticipating reference of record. |
| 19 | none | No anticipating reference of record. |
| 20 | none | No anticipating reference of record. |
| 21 | none | No anticipating reference of record. |
| 22 | none | No anticipating reference of record. |
| 23 | none | No anticipating reference of record. |
| 24 | none | No anticipating reference of record. |
| 25 | none | No anticipating reference of record. |

---

## Voice 3 — § 103 Examiner (obviousness)

*Graham* and *KSR* require identified prior-art references, ascertained differences, and an articulated rationale to combine grounded in that art. The record contains no references. I therefore cannot construct a proper obviousness combination for any claim without fabricating art, which is impermissible.

I note, without citing memory-based art, that the specification asserts specific and non-trivial technical results — a three-frequency assignment in the bulk of the heavy hexagon / heavy square lattices, a demonstrated Monte-Carlo reduction of frequency collisions by roughly an order of magnitude versus the rotated surface code, and simulated fault-tolerance thresholds (~0.3% and ~0.45%) for the disclosed flag decoder. These are objective indicia (unexpected results, solution of a long-standing hardware-yield problem) that would need to be overcome by any hypothetical § 103 combination. Absent art of record, that inquiry does not arise.

Claims 1–25 are therefore treated as **non-obvious over the prior art of record**.

| Claim | Listed primary + secondary ref(s) | Rationale to combine |
|---|---|---|
| 1–25 | none | No supporting combination of record; no § 103 rejection sustainable. |

---

## Voice 4 — § 112 Examiner (enablement / written description / definiteness)

The full specification is included, so § 112(a) is reachable. I run each sub-inquiry.

**(a) Enablement.** The specification provides concrete circuit diagrams (Figs. 4, 8), CNOT schedules with time-step counts (11 for heavy hexagon, 14 for heavy square), an explicit decoding protocol in nine numbered steps, an explicit noise model, Monte-Carlo threshold results, and Appendix A giving closed-form probability expressions for edge weights. A PHOSITA in fault-tolerant quantum error correction could implement the claimed methods on a superconducting transmon device with cross-resonance gates without undue experimentation. Wands factors — quantity of experimentation, direction provided, working examples, predictability — favor enablement. No § 112(a) enablement defect.

**(b) Written description.** The bulk lattice, degree-two/degree-three vertex structure, three-frequency assignment, and flag-qubit decoding are all shown in the drawings and detailed text; the applicant demonstrates possession of the invention as claimed. No § 112(a) written-description defect.

**(b) Definiteness.** I identify the following concrete defects that a post-grant petitioner would press:

- **Claim 1: "adjacent flag qubits both interact with a common ancilla qubit."** The term "adjacent" for flag qubits is not defined in the claim. The specification uses "adjacent" only informally in the drawings. Because a flag qubit does not sit on the data-qubit lattice, "adjacent" between flag qubits is a term of art that requires either a graph-theoretic definition (share a common ancilla? share a common data neighbor?) or a geometric one. The claim wording is arguably circular because the "adjacent" relation is *defined* by co-interaction with the common ancilla, which is the very limitation the term is used to constrain. A PHOSITA can reach a reasonable construction reading on the disclosed lattice, so this is not fatal, but it is a borderline § 112(b) issue worth flagging.
- **Claim 1: "correcting fault-tolerantly."** Standing alone, "fault-tolerantly" is a term of art in QEC and is reasonably certain to a PHOSITA (correction of any weight-t error arising from up to t faults). Not indefinite.
- **Claim 1: "at least a sub-plurality."** "Sub-plurality" is unusual claim vocabulary but simply means "a subset of two or more" of the plurality. In context, reasonably certain. Not indefinite.
- **Claim 2: "a resonance frequency selected from a first frequency, a second frequency, a third frequency or a fourth frequency."** The specification (¶ describing "first, second, third and fourth frequency must be understood broadly to mean a range of frequencies" that do not overlap) supplies the metes. Not indefinite.
- **Claim 12: "a flag qubit in a vicinity of at least one edge and a cross-edge."** "In a vicinity of" is a relative term without a quantitative bound. The specification uses "boomerang edges" as the operative construct (Fig. 12); "vicinity" is not aligned with a defined graph-theoretic neighborhood. A PHOSITA can construct a reasonable reading, but "vicinity" is the sort of relative term that draws § 112(b) attention.
- **Claim 12: "for an X-type gauge operator measurement or for a z-type stabilizer measurement."** Lowercase "z-type" is a typographical inconsistency with the uppercase "X-type" earlier in the same limitation. Non-substantive, but a real formal defect.
- **Claim 13: "calculating a probability of said at least one edge contains the data qubit error."** Ungrammatical ("of ... contains") — should read "of said at least one edge containing the data qubit error." A grammatical slip that borders on ambiguity.
- **Claim 14: "another edge in the plurality of edges not containing the data qubit error."** Antecedent is fine but the recitation of "another edge" is awkward; a PHOSITA reads it against ¶19 of the spec and the boomerang-edge renormalization discussion. Not indefinite.
- **Claim 17: "wherein said edge comprises a data qubit."** Depends from claim 12, which introduces "at least one edge." The antecedent "said edge" is singular but claim 12 recites "at least one edge and a cross-edge," making the referent ambiguous (which edge? the cross-edge? the "at least one" edge?). Minor antecedent-basis issue.
- **Claim 25: preamble structure.** "A non-transitory computer-executable medium which when executed by a quantum computer ... causes a quantum processor ... to: perform measurements ... ; and correct fault-tolerantly quantum errors ..." — the medium is causing the *quantum processor* to perform quantum operations, which raises a definiteness question: is the "computer-executable medium" a classical control program that emits pulse schedules, or is it purported to store quantum instructions on classical media? The specification makes clear it is a classical program that instructs the QPU, and a PHOSITA reads it that way. Not indefinite, but the drafting is loose.

**§ 112(f) means-plus-function.** No claim uses "means for" or a similar generic nonce word. § 112(f) is not invoked.

None of the identified defects is claim-fatal in isolation. A post-grant petitioner could press claims 12–17 harder on the "vicinity" / "said edge" antecedent basis; the panel should note these as prosecution-relevant but insufficient to invalidate.

| Claim | Sub-section | Specific defect |
|---|---|---|
| 1 | § 112(b) | "Adjacent flag qubits" arguably circular; construction supplied by specification saves it — flag only. |
| 12 | § 112(b) | "In a vicinity of" is a relative term without quantitative bound; construable via "boomerang edges" in spec. |
| 12 | § 112(b) | Case inconsistency: "z-type stabilizer" vs "X-type gauge operator" — formal defect. |
| 13 | § 112(b) | Grammatical slip: "probability of said at least one edge contains" — should be "containing." |
| 17 | § 112(b) | Ambiguous antecedent "said edge" vs claim 12's "at least one edge and a cross-edge." |
| 25 | § 112(b) | Loose "medium ... causes a quantum processor" drafting; construable, not fatal. |
| others | — | No concrete § 112 defect identified. |

None of the above rises to a sustainable § 112 rejection in the post-grant posture — each is a construction issue a PHOSITA resolves against the specification. I note them for the record but do not sustain a § 112 rejection.

### Claim compliance review

| Claim(s) | Standard | Issue | Specific feedback | Amendment target |
|---|---|---|---|---|
| 1 | USPTO § 112(b) | Term "adjacent flag qubits" is defined implicitly by co-interaction with common ancilla | Redraft to make graph-theoretic adjacency explicit: "flag qubits that share a common ancilla qubit" | Clarify claim 1 preamble/body |
| 12 | USPTO § 112(b) | "In a vicinity of" is a relative term | Replace with defined graph neighborhood: "a flag qubit associated with at least one edge" or tie to "boomerang edges" as defined in spec | Amend claim 12 |
| 12 | USPTO formalities | "z-type" lowercase inconsistent with "X-type" | Conform capitalization | Certificate of correction / amendment |
| 13 | USPTO § 112(b) | Ungrammatical "probability of said at least one edge contains" | Change to "containing" | Certificate of correction / amendment |
| 17 | USPTO § 112(b) | Antecedent basis for "said edge" ambiguous vs "at least one edge and a cross-edge" in claim 12 | Specify "said at least one edge" | Amend claim 17 |
| 25 | USPTO § 112(b) | "Medium ... causes a quantum processor" drafting loose | Recite "instructions that, when executed by a classical controller of the quantum computer, cause the quantum processor to ..." | Amend claim 25 preamble |
| 2, 19 | USPTO § 112(b) | "Selected from a first, second, third or fourth frequency" is a Markush-adjacent list without "consisting of" | Consider "selected from the group consisting of" or leave as-is with spec support | Optional amendment |
| all | USPTO § 112(b) | "At least a sub-plurality" — unconventional | Substitute "a subset of" or "at least two of" for consistency with MPEP drafting norms | Optional |

---

## Voice 5 — Quantum Technical Specialist (operability / quantum-specific)

The claimed subject matter is physically operable and does not overreach any physical bound.

- **No-cloning:** No claim requires copying an unknown quantum state. Flag qubits are prepared in a fiducial |+⟩ state (or |0⟩) and coupled to ancillas via CNOTs — standard syndrome extraction, no cloning implied.
- **Holevo bound:** Not implicated; no claim asserts extracting more classical information from a qubit than the bound allows. Syndrome measurements are single-bit projections.
- **Threshold claims:** The specification reports simulated thresholds (~0.3% heavy square, ~0.45% heavy hexagon X-errors) obtained under an explicit depolarizing circuit-level noise model with 10⁷ Monte Carlo shots. The construction is fault-tolerant with an articulated flag decoder that provably corrects errors from up to ⌊(d−1)/2⌋ faults (proof sketch given in the detailed description, including the boomerang-edge weight-renormalization argument). This is a genuine fault-tolerance construction, not an unsupported assertion.
- **Bacon-Shor Z-error "no threshold":** The specification is candid that the heavy-hexagon Z-error correction is Bacon-Shor type and therefore has no asymptotic threshold — logical Z error rates improve at finite distances but not asymptotically. The claims do not overclaim asymptotic Z-error threshold behavior for the heavy hexagon; they merely require "correcting fault-tolerantly ... based on a measurement from at least one flag qubit," which the disclosed protocol achieves.
- **Frequency-collision claim:** The Monte-Carlo comparison of Fig. 11 (three-frequency heavy-hex/heavy-square vs five-frequency rotated surface code) is a straightforward combinatorial-geometry-plus-Gaussian-disorder simulation. The physics is sound: fewer distinct required frequencies means larger tolerance to fabrication σ_f before collisions occur.
- **CR-gate architecture:** The described collision conditions (ω₀₁ degeneracy, ω₀₂/2 degeneracy, next-nearest ω₀₁-ω₁₂ degeneracy, control-target detuning constraints for gate rate) match the operating physics of the cross-resonance gate on fixed-frequency transmons. No inoperability.
- **Decoder:** Minimum-weight perfect matching (Edmonds) on a weighted syndrome graph is a well-established polynomial-time classical decoder for surface codes; the flag-augmented version described here is a specific and well-defined extension (edge-weight renormalization by p^m outside boomerangs).

No operability defect. The invention is concrete and sound engineering as claimed.

Tie-back to § 101 / § 112(a): The technical soundness supports Prong Two integration into a practical application (§ 101 pass) and enablement (§ 112(a) pass).

---

## Voice 6 — Supervisory Patent Examiner (SPE) synthesis + disposition

Reconciling the panel: the § 101 examiner finds all claims eligible under Alice/Mayo Prong Two (concrete improvement to a quantum processor's operation and a Beauregard medium reciting quantum hardware execution). The § 102 examiner cannot sustain anticipation because no reference is of record. The § 103 examiner cannot construct an obviousness combination because no reference is of record. The § 112 examiner identifies several drafting-quality issues (relative terms, antecedent basis, one grammatical slip, one case inconsistency) but none rises to a sustainable § 112 rejection — each is construable against the specification. The Quantum Technical Specialist confirms operability and the absence of physical-law overreach.

There is no disagreement to reconcile on disposition: the record contains no basis to sustain a § 101, § 102, § 103, or § 112 rejection. The claim-compliance issues under § 112 are non-fatal drafting matters properly addressed by certificate of correction or, in a post-grant proceeding, by patent-owner amendment; they do not invalidate any claim.

`Disposition: allowance`

1. **Claims standing rejected:** None. All 25 claims are allowable on this record.
2. **Allowable subject matter:** All 25 claims. No amendment is required to place the application in condition for allowance; the § 112(b) drafting notes (claims 12, 13, 17, 25) are non-fatal and can be addressed by certificate of correction if the patent owner elects.
3. **Claim-compliance defects (prosecution / post-grant relevance):**
   - Claim 12: "in a vicinity of" is a relative term; a real IPR petitioner would press this. Recommend clarification tied to defined "boomerang edges."
   - Claim 12: capitalization inconsistency ("z-type" vs "X-type") — cosmetic but real.
   - Claim 13: grammatical error ("probability of ... contains") — should be "containing."
   - Claim 17: ambiguous antecedent "said edge" — should reference "said at least one edge."
   - Claim 25: loose drafting of "medium ... causes a quantum processor to perform measurements ... " — construable via specification but tightening is prudent.
4. **Full-application defects:** None material. The specification is unusually well-supported by drawings, explicit noise model, closed-form probability expressions in Appendix A, and Monte-Carlo threshold data. Formalities under MPEP 608 appear satisfied on the face of the document (title, abstract, brief description of drawings, detailed description, claims). Best mode: the specification identifies the fixed-frequency transmon / CR-gate architecture and the three-frequency assignment as the preferred embodiment.
5. **Strongest rejection the applicant must overcome:** None on this record. A post-grant petitioner would need to place actual anticipating or obviousness art of record — likely the Chamberland/Beverland flag-qubit line of work and prior surface-code / Bacon-Shor literature — before any § 102 or § 103 challenge could be evaluated. The panel expresses no view on whether such art, if properly of record, would sustain a rejection.

### Full application review

| Area | Standard | Pass / defect | Evidence from application | Required fix |
|---|---|---|---|---|
| Claims | USPTO § 112(b) | Pass with minor drafting notes | 25 claims examined; independent claims 1, 12, 18, 25; dependents properly linked | Certificate of correction for claim 12 capitalization, claim 13 grammar, claim 17 antecedent |
| Specification support | USPTO § 112(a) written description | Pass | Detailed description covers heavy-hexagon and heavy-square constructions, gauge/stabilizer groups, CNOT schedules, decoder protocol (9 numbered steps) | None |
| Enablement / possession | USPTO § 112(a) enablement | Pass | Explicit noise model, closed-form edge-weight expressions (Appendix A), simulated thresholds, 10⁷ Monte Carlo shots, worked distance-5 examples | None |
| Formalities / required sections | USPTO MPEP 608 | Pass | Title, Background, Summary, Brief Description of Drawings, Detailed Description, Claims, Abstract all present | None |
| Drawings / abstract / title | USPTO | Pass | 22 figures with letter suffixes; abstract present; title descriptive | None |
| Best mode | USPTO § 112(a) best mode | Pass | Fixed-frequency transmon / CR-gate architecture identified as preferred; three-frequency assignment identified as preferred bulk configuration | None |

### Rejections of record
- § 101: none
- § 102: none
- § 103: none
- § 112: none
- allowable: 1–25

## Vote table

| Voice | Recommended disposition | Confidence 1-10 |
|---|---|---|
| Primary Examiner | allowance | 9 |
| § 102 Examiner | allowance (no art of record) | 10 |
| § 103 Examiner | allowance (no art of record) | 10 |
| § 112 Examiner | allowance with drafting notes | 8 |
| Quantum Technical Specialist | allowance | 9 |
| Supervisory Patent Examiner | allowance | 9 |