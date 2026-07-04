# UNITED STATES PATENT AND TRADEMARK OFFICE
## Post-Grant Review — Office Action Analog
### In re U.S. Patent No. 9,985,193 B2 (Dial et al., assigned to IBM Corp.)
### Title: Architecture for coupling quantum bits using localized resonators

**Notice regarding prior art of record:** No external prior art was placed of record in this proceeding. The panel therefore cannot sustain any rejection under 35 U.S.C. § 102 or § 103 based on specifically identified art, and expressly declines to recall or fabricate references. Analysis under § 102 and § 103 is limited accordingly. Rejections, if any, are confined to defects evident on the face of the specification and claims under §§ 101 and 112.

---

## Voice 1 — Primary Examiner (§ 101 eligibility + overall)

The claims are directed to a physical apparatus: a "superconducting microwave cavity" comprising an enclosure (top plate, bottom plate, sidewalls), an array of physical posts of differing heights, and physical qubits mechanically and electrically coupled to those posts. Claims 1 and 15 are the independent claims; both recite tangible superconducting hardware, specific structural relationships (one end of the low-frequency posts shorted to the second/bottom plate; the other end open; high-frequency posts shorted at both ends), and physical connection of qubits to one or two low-frequency posts. Claim 2 further recites physical ports in the first plate configured to drive and measure qubits. Claims 3, 4, 8, 15, 17–19 recite additional hardware (shorted post ends, cylindrical resonators through the bottom plate, superconducting materials).

Alice/Mayo Step 2A Prong One: none of the claims recites a mathematical formula, mental process, or law of nature as such. The claims recite a manufactured article — a cryogenic microwave cavity with a specific post-lattice topology. The mere fact that the cavity is *used* for quantum computation (a field steeped in mathematics) does not convert an apparatus claim into a claim to an abstract idea. See *Diamond v. Diehr*, 450 U.S. 175 (1981).

Alice/Mayo Step 2A Prong Two / Step 2B: even assuming, arguendo, that any recited functional language (e.g., "supporting a localized microwave mode," "configured to couple to, drive, and measure the qubits," "configured to perform a quantum error correcting code" in claim 11) implicated a judicial exception, each claim integrates the recited functionality into a practical application, i.e., a specific hardware architecture that improves the operation of a quantum processor (mode localization to isolate individual qubit addressing; reduced footprint; compatibility with fault-tolerant architectures). This is an improvement to a machine, not an abstract idea on a generic computer. *Enfish, LLC v. Microsoft Corp.*, 822 F.3d 1327 (Fed. Cir. 2016).

Claim 11 ("wherein a lattice of the qubits is configured to perform a quantum error correcting code") recites a functional/intended-use limitation on a hardware lattice. Because the underlying claim is directed to the hardware lattice (claim 1's array of posts and physically connected qubits), and the "configured to" language ties the lattice's physical arrangement to executing a QEC code on the machine, § 101 is satisfied. This is an operational improvement of a QPU, not a bare algorithm.

Claim 12 ("fabricated using at least one of standard machining techniques, standard micromachining techniques, and 3D printing") is a product-by-process style limitation on the hardware; it does not raise a § 101 concern.

**No claim is rejected under § 101.** All 19 claims are directed to statutory subject matter (a machine).

| Claim(s) | Statute | Basis (one line) |
|---|---|---|
| 1–19 | § 101 | Directed to a superconducting microwave cavity (machine) with concrete hardware structure and QPU-operational improvement; eligible. |

---

## Voice 2 — § 102 Examiner (anticipation / novelty)

No prior art was placed of record in this proceeding. Anticipation under 35 U.S.C. § 102 requires that a *single* prior-art reference disclose every element of the claim, arranged as claimed. Without a reference of record, no such element-by-element read is possible, and the panel will not manufacture one from memory.

Accordingly, all claims 1–19 are treated as **novel over the prior art of record**, and no § 102 rejection is sustained.

| Claim(s) | Listed reference | Element-by-element read |
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

---

## Voice 3 — § 103 Examiner (obviousness)

Obviousness under *Graham v. John Deere*, 383 U.S. 1 (1966), and *KSR Int'l Co. v. Teleflex Inc.*, 550 U.S. 398 (2007), requires (i) the scope and content of the prior art, (ii) differences between the prior art and the claims, (iii) the level of ordinary skill, and (iv) objective indicia. Elements (i)–(ii) cannot be assessed without prior art of record. No listed primary or secondary reference exists in this record; therefore no articulated combination can be sustained.

I decline to invoke Official Notice for structural limitations such as "an array of posts of different heights … including lower resonant frequency posts and higher resonant frequency posts, the higher resonant frequency posts arranged around the lower resonant frequency posts" — these are not the kind of instantly and unquestionably demonstrable facts appropriate for Official Notice under MPEP 2144.03.

All claims 1–19 are treated as **non-obvious over the prior art of record**. No § 103 rejection is sustained.

| Claim(s) | Primary + secondary ref(s) | Rationale to combine |
|---|---|---|
| 1–19 | none | no supporting combination of record |

---

## Voice 4 — § 112 Examiner (enablement / written description / definiteness)

The written description is included in the record, so I may reach § 112(a) as well as § 112(b).

**§ 112(a) — Written description / enablement.** The specification describes the geometry in detail: FIGS. 1A–10 depict the two interpenetrating post arrays (λ/4 low-frequency posts open at the top plate, shorted at the bottom plate; λ/2 high-frequency posts shorted at both plates), the qubit chip suspended between two low-frequency posts, cylindrical readout resonators through the bottom plate, and material choices (niobium, aluminum, NbTi, TiN, NbN, tantalum, or copper). The specification recites concrete dimensional ranges (post heights 0.5 mm–100 mm mapped to 0.75–150 GHz) and expressly discloses a "proof-of-concept device containing five λ/4 resonators and four qubits" that was "produced and characterized," with "measured qubit and resonator parameters … in the range expected." This is sufficient to show possession and to enable the disclosed structural claims (1–10, 12–19) across the recited scope without undue experimentation.

Claim 11 ("wherein a lattice of the qubits is configured to perform a quantum error correcting code") is broad functional language, but § 112(a) is satisfied because (i) the specification devotes a detailed section to the surface code implementation (FIGS. 9A–10), (ii) it identifies specific entangling gates (cross-resonance, resonator-induced phase, CNOT), (iii) it details a five-qubit plaquette operation sequence, and (iv) the "configured to" language is directed to the physical lattice, which is fully described. Enablement of *arbitrary* error-correcting codes is not required — the specification's disclosure of the surface code and the physical connectivity of FIG. 10 supports the recited scope. No § 112(a) defect.

Claim 5 recites qubits selected from "superconducting qubits, semiconductor spin qubits, optically trapped ions, and an impurity center in a crystal." The specification's detailed enablement centers on 3D transmon qubits held between λ/4 posts; the mechanical mounting of trapped ions or impurity centers in a crystal to the λ/4 post structure is not specifically enabled. However, the Markush recitation in claim 5 uses "at least one of," which is satisfied by any one member (i.e., superconducting qubits), so the claim as written is not invalid for enablement — the enabled species reads on the claim. No § 112(a) rejection sustained on this basis.

**§ 112(b) — Definiteness.**

Claim 3 recites "The cavity of claim 1, wherein the higher resonant frequency posts are shorted on both ends…" Claim 1 recites the "first plate" and "second plate" but does not explicitly recite that the higher resonant frequency posts are *present between* the plates (it recites only that the low-frequency posts have one end on the second plate and the other open). Claim 3 imports a shorting relationship of the higher resonant frequency posts to both the first and second plates. Antecedent basis is arguably adequate because claim 1 recites the high-frequency posts and the two plates as claim elements, and a "shorted on both ends" limitation is reasonably certain to a skilled artisan. Not indefinite.

Claim 13: "the array of posts having different the heights are between 0.5 mm and 100 mm in lengths, corresponding to supporting resonating modes from 0.75 GHz to 150 GHz." The phrase "having different the heights" contains an obvious grammatical error ("the" is an extraneous or misplaced article). A person of ordinary skill would understand the intended meaning ("having different heights"), and the numerical ranges are definite. This is a candidate for an examiner's amendment or a certificate of correction rather than an indefiniteness rejection under *Nautilus, Inc. v. Biosig Instruments, Inc.*, 572 U.S. 898 (2014) ("reasonable certainty" standard). No § 112(b) rejection sustained, but the defect is flagged for the compliance review.

Claim 14: "a separation distance between the lower resonant frequency posts in the array of posts is smaller than the heights of the lower resonant frequency posts." Terms are reasonably certain — a comparison of two measurable lengths. Not indefinite.

Claim 2 recites "ports … configured to couple to, drive, and measure the qubits." This is functional language squarely supported by the specification (FIG. 4, input ports 405, individual microwave cylinder connectors 410 capacitively coupled to the lower resonant frequency posts). Not a § 112(f) trap because "ports" is structural. Not indefinite.

Claim 4 recites "configured to provide mode localization for the lower resonant frequency posts." Supported by the mode-isolation physics described in the specification and FIG. 2. Not indefinite.

Claim 7 recites "each of the qubits respectively incorporates its own readout resonator." Antecedent basis is proper; "readout resonator" is introduced here and further limited in claim 8. Not indefinite.

Claim 15 is a self-contained independent apparatus claim reciting the enclosure (top plate, bottom plate, sidewalls), post array, and qubit connections. Its limitations largely track claims 1 + 2 + 3. Not indefinite.

Claim 17 recites the same "own readout resonator" limitation as claim 7; not indefinite.

Claim 19 recites "the top plate, the bottom plate, and the sidewalls are made of superconducting material." The specification identifies specific superconductors. Reasonably certain. Not indefinite.

No concrete § 112(b) defect rises to the level of a rejection under the *Nautilus* "reasonable certainty" standard. All § 112 concerns are handled below in claim-compliance rather than as a rejection.

| Claim | Sub-section | Specific defect |
|---|---|---|
| 1 | — | none |
| 2 | — | none |
| 3 | — | none |
| 4 | — | none |
| 5 | — | none (Markush "at least one of" saves the claim; narrower enablement concern noted but not a rejection) |
| 6 | — | none |
| 7 | — | none |
| 8 | — | none |
| 9 | — | none |
| 10 | — | none |
| 11 | — | none |
| 12 | — | none |
| 13 | § 112(b) grammar only | "having different the heights" — extraneous article; certificate of correction candidate, not a rejection |
| 14 | — | none |
| 15 | — | none |
| 16 | — | none |
| 17 | — | none |
| 18 | — | none |
| 19 | — | none |

### Claim compliance review

| Claim(s) | Standard | Issue | Specific feedback | Amendment target |
|---|---|---|---|---|
| 13 | USPTO § 112(b) | Grammatical error "having different the heights" | Delete the extraneous "the"; intended meaning clear but the language is malformed on the face of the granted claim | Amend to "the array of posts having different heights that are between 0.5 mm and 100 mm in length…" |
| 3 | USPTO § 112(b) | Antecedent-basis softness for "the higher resonant frequency posts" being present between "the first plate" and "the second plate" | Claim 1 recites the higher-frequency posts and the two plates as elements; the shorted-to-both-plates relationship is clear in context but could be tightened | Optionally recite "wherein each of the higher resonant frequency posts extends between the first plate and the second plate, and is shorted at a first end to the first plate and at a second end to the second plate" |
| 5 | USPTO § 112(b) | Markush-style "at least one of A, B, C, and D" is grammatically permissible but risks *Superguide* construction issues (requiring one of each) | Prefer "selected from the group consisting of" or "at least one of A, B, C, or D" | Recite "wherein the qubits comprise at least one of a superconducting qubit, a semiconductor spin qubit, an optically trapped ion, and an impurity center in a crystal" |
| 11 | USPTO § 112(b) | Functional recitation "configured to perform a quantum error correcting code" is broad but supported | Consider narrowing to "a surface-code error correcting scheme" per the specification's disclosure to strengthen the claim against future prior art | Optional narrowing amendment |
| 12 | USPTO § 112(b) | Product-by-process style ("fabricated using") in an apparatus claim carries limited weight for structure and can be construed to add nothing patentable | Product-by-process limitations generally do not distinguish structure absent a resulting structural difference | Optional — retain as-is if desired |

---

## Voice 5 — Quantum Technical Specialist (operability / quantum-specific)

The physics described is sound and standard for cQED architecture circa 2015. Key operability points:

1. **Mode localization physics.** The λ/2 posts, shorted at both ends, act as short-circuited coaxial stubs whose fundamental TEM mode is at c/2h; the λ/4 posts, shorted at one end and open at the other, resonate near c/4d. Provided d ≳ h/2, the λ/4 posts have a *lower* fundamental frequency than the λ/2 posts, so a λ/2 lattice enclosing each λ/4 post presents a photonic bandgap-like barrier to mode leakage between neighboring λ/4 posts at the λ/4 frequency. The specification's assertion that the higher-frequency posts "block the coupling between two or more individual lower resonant frequency posts" is physically credible and, per the specification, demonstrated on the four-qubit / five-resonator proof-of-concept device. Operable.

2. **Qubit coupling.** 3D transmons mounted between two λ/4 posts, capacitively coupled by proximity, is a straightforward extension of the well-established Paik-Schoelkopf 3D transmon architecture. Coupling strength control via post-to-post separation and by the vertical position of the qubit chip on the post slots is physically reasonable.

3. **Readout via cylindrical resonators through the bottom plate.** A pin capacitively coupled to a microstrip resonator on the substrate, protruding into a cylindrical hole under each qubit, is a standard dispersive-readout topology. Operable.

4. **Claim 13's frequency range (0.75–150 GHz).** The upper end (150 GHz) is well above practical dilution-refrigerator microwave hardware and above typical transmon transition frequencies (~4–8 GHz). The claim covers *resonator mode* frequencies, not qubit frequencies, and the specification maps this range to physical post heights of 0.5–100 mm. As a claim to resonator geometry, this is physically well-defined; whether every point in the range yields a *useful* qubit-resonator coupling is a separate question. Because § 112(a) enablement was assessed on the disclosed operative regime (transmon-scale, ~few GHz), and the claim recites the physical post-height range as its primary limitation with the frequency range as a mathematical consequence (c/4d), the claim is operable as an apparatus claim.

5. **Claim 5 — "optically trapped ions" and "impurity center in a crystal."** The specification's mechanical mounting story (qubit chip in a slot on the post, held in place with indium) does not straightforwardly extend to trapped ions (which require RF trap electrodes and UHV, not indium mounting in a microwave cavity) or to impurity centers in a crystal (which are typically read out optically, not via microwave dispersive readout to a λ/4 stub). This is not a *disqualifying* operability defect because claim 5's "at least one of" phrasing is satisfied by superconducting qubits alone, but the alternative species are not credibly enabled by this architecture.

6. **No overreach of physics.** The claims do not assert speedups contingent on complexity conjectures, do not violate no-cloning or Holevo, and do not claim thresholds absent the disclosed fault-tolerant construction (the specification cites the surface code as the target QEC scheme).

Overall: the invention is concrete, physically sound, and the disclosed proof-of-concept lends real support to enablement. No § 101 "law of nature" overreach. No § 112(a) enablement rejection warranted, though the alternative qubit species in claim 5 are weakly supported.

---

## Voice 6 — Supervisory Patent Examiner (SPE) synthesis + disposition

The five examiners are aligned. The Primary Examiner finds all claims patent-eligible under § 101 as directed to a machine with QPU-operational improvement. The § 102 and § 103 Examiners cannot sustain a rejection because no prior art was placed of record — over-rejection based on recalled art would be a hard error and is refused. The § 112 Examiner identifies one grammatical defect in claim 13 that is a certificate-of-correction candidate rather than an indefiniteness rejection, and identifies compliance-level tightening opportunities in claims 3, 5, 11, and 12, but sustains no § 112 rejection. The Quantum Technical Specialist finds the architecture operable and physically sound, with a minor caveat that certain alternative qubit species listed in claim 5 are not credibly enabled by the disclosed mounting/readout scheme — a caveat the "at least one of" phrasing renders non-fatal.

Because (i) no § 101 defect exists, (ii) no prior art of record supports a § 102 or § 103 rejection, and (iii) no concrete § 112(a) or § 112(b) defect rises to the level of a rejection, the correct disposition is allowance. I will not sustain a rejection the record does not support.

`Disposition: allowance`

1. **Claims standing rejected:** None.
2. **Claims containing allowable subject matter:** Claims 1–19, all allowable. No amendment is required to place the application in condition for allowance; it is already granted and the record supports validity as-issued.
3. **Claim-compliance defects worth prosecution / post-grant attention:**
   - Claim 13 grammatical error ("different the heights") — certificate of correction.
   - Claim 5 Markush construction under *Superguide* — optional tightening.
   - Claim 3 antecedent tightening for higher-frequency post presence — optional.
   - Claim 11 optional narrowing to the surface code, since that is what is enabled.
   - Claim 12 product-by-process limitation carries limited structural weight — advisory only.
4. **Full-application defects:** See the review table below. The application is substantively sound; the flaws are cosmetic.
5. **Strongest rejection to overcome:** None. There is no rejection of record.

### Full application review

| Area | Standard | Pass / defect | Evidence from application | Required fix |
|---|---|---|---|---|
| Claims | USPTO § 112(b) | Pass with minor defect in claim 13 | "having different the heights" — extraneous article | Certificate of correction |
| Specification support | USPTO § 112(a) written description | Pass | FIGS. 1A–11 and detailed description describe every claimed structural element (posts, plates, sidewalls, qubits, cylindrical resonators, ports) | None |
| Enablement / possession | USPTO § 112(a) enablement | Pass | Proof-of-concept device (5 λ/4 resonators, 4 qubits) built and characterized; measured parameters in expected range | None |
| Formalities / required sections | MPEP 608 | Pass | Contains Background, Summary, Brief Description of Drawings, Detailed Description, Claims, Abstract, and Federally Sponsored Research statement (Contract W911NF-10-1-0324, IARPA) | None |
| Drawings / abstract / title | MPEP 608.01(b), 608.01(f) | Pass | Eleven figures with reference numerals (10, 20, 25, 30, 35, 40, 305, 405, 410, 805, 810, 815, 850, 905, 910, 920, 925, 930, 950, 1050); title and abstract adequately identify the invention | None |

### Rejections of record
- § 101: none
- § 102: none
- § 103: none
- § 112: none
- allowable: 1–19

## Vote table

| Voice | Recommended disposition | Confidence 1-10 |
|---|---|---|
| Primary Examiner | allowance | 9 |
| § 102 Examiner | allowance (no art of record) | 10 |
| § 103 Examiner | allowance (no art of record) | 10 |
| § 112 Examiner | allowance (claim 13 to certificate of correction) | 8 |
| Quantum Technical Specialist | allowance | 9 |
| Supervisory Patent Examiner | allowance | 9 |