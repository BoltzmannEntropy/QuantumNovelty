# Office Action — US10846608B2

**Patent under post-grant review:** US10846608B2 — "Codes and protocols for distilling T, controlled-S, and Toffoli gates"
**Assignee:** Microsoft Technology Licensing LLC
**Panel posture:** Post-grant / IPR-style validity review of issued claims 1–16.
**Prior art of record:** None supplied. No anticipatory or obviousness reference has been placed of record, and the panel therefore does NOT recall or cite art from memory. All § 102 / § 103 analyses below proceed on that empty record.

---

## Voice 1 — Primary Examiner (§ 101 eligibility + overall)

The claims fall into two independent statutory categories: claim 1 (and dependents 2–8) recite a "method for distilling magic states in a quantum computing device"; claim 9 (and dependents 10–16) recite a "quantum computer system comprising ... a classical computer; and a quantum computing device implementing a plurality of q[u]bits." Both categories fall within § 101's enumerated categories (process, machine).

**Step 2A, Prong One.** Each independent claim recites a mathematical construct (Reed-Muller codes / punctured Reed-Muller codes) and a step of "generating a magic state distillation protocol." Standing alone, protocol *design* could be viewed as a mental process or a mathematical concept. However, both independent claims recite more than the math: claim 1 requires "configuring the quantum computing device to implement the magic state distillation protocol," and claim 9 recites a physical apparatus — a classical computer coupled to a "quantum computing device implementing a plurality of q[u]bits" — programmed to configure that quantum device.

**Step 2A, Prong Two / Step 2B.** Configuring a quantum computing device (physical qubit hardware — superconducting, ion-trap, or Majorana-based, per the specification) to execute a distillation protocol is a concrete technological application. Magic state distillation is a *hardware-operational* improvement: it raises the fidelity of the non-Clifford resource states that a physical quantum processor consumes during execution, directly improving the operation of the quantum processor (fewer physical T-gates per usable magic state, higher output fidelity, lower space overhead per the § III.D space-time tradeoff). This is on all fours with *Enfish* / *McRO*-style improvements to a machine, not a bare mathematical algorithm on a generic computer. The mathematics (Reed-Muller codes, triorthogonality) is the *means* by which the hardware is improved, not the whole of the claim.

The dependent claims (2–8, 10–16) narrow the protocol construction (puncturing, Hamming-distance selection, transversal T / transversal CCZ measurement of stabilizers, order of error reduction). These further tie the claim to the operation of quantum hardware and do not raise a fresh § 101 concern.

Claims 1 and 9 are **eligible under § 101**. No § 101 rejection is sustained.

| Claim(s) | Statute | Basis (one line) |
|---|---|---|
| 1–8 | § 101 | Eligible — configures a quantum computing device; improvement to operation of a machine (Step 2A Prong Two). |
| 9–16 | § 101 | Eligible — recites classical computer + quantum computing device (qubits) programmed to configure the quantum device. |

---

## Voice 2 — § 102 Examiner (anticipation / novelty)

No prior art has been placed of record for this examination. Under the express instruction of the record, I may not recall Bravyi-Haah 2012, Bravyi-Kitaev 2005, Jones 2013, Eastin 2013, Haah-Hastings-Poulin-Wecker 2017, Campbell-Howard 2017, or any other reference cited in the specification's own bibliography as if it were art of record — none of those was supplied to this panel as § 102 art, and treating a specification's own background citations as anticipatory art in an IPR-style review requires the petitioner to place them of record, which has not occurred here.

Because the record contains **zero anticipating references**, no claim of the '608 patent can be rejected under § 102 in this proceeding. Every claim is novel over the prior art of record by default.

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

---

## Voice 3 — § 103 Examiner (obviousness)

Graham / KSR obviousness requires (i) scope and content of the prior art, (ii) differences between the claims and that art, (iii) level of ordinary skill, and (iv) objective indicia — anchored to *specific references of record*. The record here supplies none. Without at least one primary reference of record, I cannot articulate a KSR combination: there is no "known technique" and no "known device ready for improvement" placed before this panel that I am permitted to rely on.

I note that the specification's own § II ("Overview of Disclosed Technology") acknowledges a rich background — Reed-Muller-based distillation, triorthogonal codes, Bravyi-Haah 2012, Eastin 2013, Jones 2013, Haah-Hastings-Poulin-Wecker 2017, Campbell-Howard 2017 — and a petitioner in an actual IPR would almost certainly ground a § 103 challenge on Bravyi-Haah + Eastin/Jones. But those references have not been placed of record for THIS examination. I therefore cannot sustain any § 103 rejection.

Every claim is non-obvious over the prior art of record by default. This is a limitation of the record, not an affirmative finding that the claims are patentably distinct from the art in the wild.

| Claim | Primary + secondary ref(s) | Rationale to combine |
|---|---|---|
| 1–16 | none | no supporting combination of record |

---

## Voice 4 — § 112 Examiner (enablement / written description / definiteness)

### § 112(b) definiteness

Reviewing the claim language itself:

- **Claim 1** — "generating a magic state distillation protocol ... wherein the ... protocol includes (a) Reed-Muller codes, or (b) punctured Reed-Muller codes"; "configuring the quantum computing device to implement the ... protocol"; "the ... protocol is for Toffoli gates or controlled-controlled-Z (CCZ) gates." Terms "Reed-Muller codes," "punctured Reed-Muller codes," "Toffoli gates," and "CCZ gates" are terms of art with well-defined meanings, and the specification at § III–§ V gives explicit definitions and examples (RM(r,m), puncturing procedure, [[n,k,d]] parameters). Definite.
- **Claim 2** — "punctured higher-order Reed-Muller codes." "Higher-order" is defined in the specification (§ V.E) as "above first-order," i.e., RM(r,m) with r ≥ 2. Definite as informed by the spec.
- **Claim 3** — "uses Reed-Muller stabilizers." The spec (§ V.B, § V.E) explains the code has X-type stabilizers taken from rows of G₀ derived from a Reed-Muller code. Definite.
- **Claim 4** — "punctured Reed-Muller codes ... selected based on Hamming distances." Broad but definite — Hamming distance is a well-defined metric and § V.E discloses selection by distance.
- **Claim 5** — "selected by random puncturing and unpuncturing." The specification (§ V.E) discloses these exact procedures. Definite.
- **Claim 6** — "measuring a controlled-Z operator using a transversal T gate to measure stabilizers of a CCZ magic state." Terms defined in § VI. Definite.
- **Claim 7** — "second order error reduction or a fourth order error reduction." Order-of-error-reduction terminology is defined operationally in § VI.A / § VI.B (ε_out ∝ p^2 vs. p^4). Definite.
- **Claim 8** — "simultaneously measuring stabilizers of CCZ magic states using one or more transversal CCZ gates." Definite; § VII discloses the identity (VII.1).
- **Claims 9–16** — mirror 1–8 in system form. Same analysis.

Note: claim 9 uses the term "**quoits**" ("a quantum computing device implementing a plurality of quoits"). This is an OCR-introduced typographical artifact for "qubits" (compare "croantum" for "quantum" in the abstract and "cubits" elsewhere in the specification). Standing alone in an issued claim, "quoits" would raise a § 112(b) antecedent / clarity concern — a "quoit" is not a term of art in quantum computing. However, this appears to be a scanned-text artifact of the reproduction, not the language of the issued claim as printed by the USPTO; if the granted claim in fact reads "qubits," there is no § 112(b) defect. I flag it as a **potential clerical issue for verification against the certified copy** rather than sustain a rejection on it.

No claim is rejected under § 112(b).

### § 112(a) enablement / written description

The written description is included and is substantial (Sections III–X, plus Tables I–II of concrete code parameters and the § V.B explicit generator matrices for m=3, m=6, m=9). The disclosure provides:

- explicit generator matrices (Eqs. V.10, V.11, V.12–V.13);
- explicit punctured RM(2,7) and RM(3,10) codes with distances and puncture coordinates (Tables I–II);
- randomized construction algorithms with proofs (Lemmas 1–3, Theorem 1);
- transversal T / transversal CCZ measurement circuits (§ VI, § VII);
- computing environment (§ XI, Figs. 1–4).

A PHOSITA in quantum error correction can, from this disclosure, construct and implement the claimed protocols on a quantum computing device configured per Fig. 4. Enablement and written description are met for the full scope claimed.

No § 112(a) rejection.

### Claim compliance review

| Claim(s) | Standard | Issue | Specific feedback | Amendment target |
|---|---|---|---|---|
| 1, 9 | USPTO § 112(b) | Alternative claiming with "(a) ... or (b) ..." | Markush-style "(a) Reed-Muller codes, or (b) punctured Reed-Muller codes" is permissible under MPEP 2117; no rejection, but prosecution history should confirm the alternatives are treated as a proper Markush group. | No amendment required. |
| 9 | USPTO § 112(b) | Clerical: "quoits" | Verify against the granted certified copy. If the printed claim reads "quoits," a Certificate of Correction under 35 U.S.C. § 254 would clean this up; the term of art is "qubits." | Certificate of Correction. |
| 2, 10 | USPTO § 112(b) | "higher-order" | The term is informed by spec § V.E as "above first-order." Prosecution-safe as-is. | None. |
| 4, 12 | USPTO § 112(b) | "selected based on Hamming distances" | Broad functional selection language, but Hamming distance is a definite metric and the spec gives the selection procedure. Acceptable. | None. |
| 7, 15 | USPTO § 112(b) | "second order error reduction or a fourth order error reduction" | Order-of-error-reduction is defined operationally in the spec; not indefinite. | None. |
| all | USPTO dependency form | Dependencies well-formed | Claims 2–8 depend from 1; claims 10–16 depend from 9 (with 15 depending from 14). Proper. | None. |

---

## Voice 5 — Quantum Technical Specialist (operability / quantum-specific)

The claimed subject matter is grounded engineering, not physics overreach.

- **No no-cloning violation.** Distillation does not clone magic states; it consumes many noisy copies to *distill* a smaller number of higher-fidelity copies via a stabilizer measurement plus post-selection. This is the standard Bravyi-Kitaev paradigm and is physically consistent.
- **No Holevo-bound issue.** The claims concern gate synthesis and error reduction, not information capacity.
- **Fault-tolerance is grounded.** The specification provides explicit code parameters ([[n,k,d]] triples such as [[887,137,5]], [[912,112,6]], [[937,87,7]], and the 512-qubit m=9 RM code with k_CCZ=10 and distance 8) and computes concrete output error probabilities (e.g., ε_out ≈ 3.0 × 10⁻¹⁷ at ε_in = 10⁻³ for the m=9 code). These are calculable, verifiable claims — not asymptotic hand-waves.
- **Speedup claims.** The specification does not assert an unproven complexity-theoretic speedup; it asserts an *overhead* improvement (T-count per output CCZ, e.g., approaching 51.2 or the § VII asymptotic ~16 T per output CCZ, and the § III.D space-time tradeoff to k+n_X qubits). These are concrete, computable resource-count claims, physically meaningful for near-term FTQC architectures.
- **Hardware tie.** § XI (Figs. 1–4) discloses concrete hardware realizations (superconducting, ion-trap, topological / Majorana). Claim 9's "quantum computing device implementing a plurality of q[u]bits" reads on real, disclosed hardware.

The invention operates as claimed under the physics. No operability § 112(a) or § 101 concern arises from the technical content.

---

## Voice 6 — Supervisory Patent Examiner (SPE) synthesis + disposition

Reconciling the five examining voices:

- Primary Examiner: all claims pass § 101 — configuring a quantum computing device to run an improved distillation protocol is an improvement to a machine, not a bare abstract idea.
- § 102 Examiner: no anticipating art of record; every claim is novel over the record.
- § 103 Examiner: no combination of record; every claim is non-obvious over the record.
- § 112 Examiner: written description and enablement are met by §§ III–X plus Tables I–II; claim terms are definite as informed by the spec. Only clerical concern: "quoits" in claim 9 (likely OCR artifact — verify certified copy; a Certificate of Correction, not a rejection, is the remedy if the granted claim in fact reads that way).
- Quantum Technical Specialist: operability confirmed; hardware tie confirmed; resource claims are concrete and calculable.

No examiner sustains a rejection on the record before this panel. The disposition follows the record, not a default toward rejection.

The single most important caveat for the applicant / patent owner: **this allowance reflects the empty prior-art record supplied to this panel, not an affirmative finding that Bravyi-Haah 2012, Eastin 2013, Jones 2013, Haah-Hastings-Poulin-Wecker 2017, and Campbell-Howard 2017 — all cited in the specification's own § II — would not have supported a real § 103 challenge in an actual IPR.** A petitioner who places those references of record would present a serious obviousness challenge, particularly against claims 1 and 9 read at their broadest ("magic state distillation protocol includes ... Reed-Muller codes"), which read on protocols predating this application. The '608 patent's patentably distinct contribution most likely lies in the *specific* constructions — the 512-qubit m=9 RM-based code distilling 10 CCZ magic states with distance 8, the punctured RM(3,10) codes in Table II, the § VII normal-code T-to-CCZ family approaching ~16 T per CCZ, and the § III.D space-time tradeoff — none of which is fully captured by the broadest independent claims. That is a prosecution-history observation, not a rejection sustainable on this record.

Disposition: allowance

### Full application review

| Area | Standard | Pass / defect | Evidence from application | Required fix |
|---|---|---|---|---|
| Claims | USPTO § 112(b) | Pass (clerical "quoits" in claim 9 flagged for verification) | Claims 1–16 are definite as informed by §§ III–X. | Certificate of Correction if the granted claim in fact prints "quoits." |
| Specification support | USPTO § 112(a) written description | Pass | §§ III–X + Tables I–II + explicit generator matrices (V.10, V.11, V.12–V.13) show possession of the claimed protocols. | None. |
| Enablement / possession | USPTO § 112(a) enablement | Pass | Randomized construction algorithms with proofs (Lemmas 1–3, Theorem 1); explicit puncture coordinates for [[125,3,5]], [[887,137,5]], [[912,112,6]], [[937,87,7]]; transversal-T and transversal-CCZ measurement circuits (§§ VI–VII). | None. |
| Formalities / required sections | MPEP 608 | Pass | Cross-reference to provisional 62/555,800; Field; Summary; Brief Description of the Drawings; Detailed Description; Claims; Abstract all present. | None. |
| Drawings / abstract / title | MPEP 608 | Pass with clerical note | Figs. 1–11 disclosed and described; Abstract present (contains OCR artifact "croantum" for "quantum" — clerical); Title matches subject matter. | Certificate of Correction for OCR artifacts if present in the granted copy. |

### Rejections of record
- § 101: none
- § 102: none
- § 103: none
- § 112: none
- allowable: 1–16

## Vote table

| Voice | Recommended disposition | Confidence 1-10 |
|---|---|---|
| Primary Examiner | allowance | 9 |
| § 102 Examiner | allowance (empty art of record) | 10 |
| § 103 Examiner | allowance (empty art of record) | 8 |
| § 112 Examiner | allowance | 9 |
| Quantum Technical Specialist | allowance | 9 |
| Supervisory Patent Examiner | allowance | 9 |