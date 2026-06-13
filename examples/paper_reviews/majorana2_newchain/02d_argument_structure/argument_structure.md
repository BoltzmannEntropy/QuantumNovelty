# ARGUMENT STRUCTURE REPORT

## Executive summary
**Overall verdict:** PUBLISH-READY
**Claim–proof gap:** NONE — The paper claims that replacing Al with Pb in tetron devices yields larger topological gaps and longer parity lifetimes, and demonstrates exactly this through material characterization, TGP analysis, and time-resolved parity measurements.
**CME balance:** BALANCED — C:25% / M:30% / E:45%
**Narrative debts:** 5 total (0 load-bearing)
**Sequencing:** EVIDENTIAL

## Argument map

```
P1 (premise, §1): Topological protection gives error rates exponentially suppressed as the topological gap increases [Ref. 34].

P2 (premise, §1): The parent superconducting gap governs the topological gap in superconductor-semiconductor hybrids [Refs. 40–52].

P3 (premise, §2): Pb has a parent gap ∆Pb ≈ 1.3 meV vs Al ≈ 300 µeV.

P4 (premise, §2): The GaSb substrate enables lattice-matched growth and larger spin-orbit coupling (α ~ 12–16 meV nm).

I1 (intermediate, from P2+P3+P4): InAs–Pb devices should exhibit larger topological gaps than Al-based devices.

E1 (evidence, §2–3): TGP analysis shows top-quintile ∆T ~ 70 µeV in Pb devices vs ~30 µeV in Al devices.

E2 (evidence, §3): Localization lengths exceed 1 µm, confirming low disorder.

E3 (evidence, §3): Zero-bias peaks persist over >0.5 T field range at both wire ends.

I2 (intermediate, from I1+E1+E2+E3): The Pb-based platform achieves a robust topological phase with enlarged gap.

P5 (premise, §1): Non-equilibrium quasiparticles limit parity lifetime independently of ∆T.

P6 (premise, §4): Pb's higher gap suppresses Cooper pair breaking and enhances recombination.

E4 (evidence, §4): Measured Z-parity lifetime τZ = 22 ± 1 s via interferometric readout with h/2e periodicity.

E5 (evidence, §4): Prior Al-based devices showed τZ ~ 1–12 ms [Refs. 59, 61].

I3 (intermediate, from P5+P6+E4+E5): Parity lifetime improved by >3 orders of magnitude due to Pb substitution.

E6 (evidence, §3): rf spectroscopy shows EM < 1 µeV across extended parameter regimes.

I4 (intermediate, from E6): Majorana hybridization is suppressed below measurement resolution.

C (conclusion, from I2+I3+I4): Increasing the excitation gap via Pb substitution directly translates to improved device performance: larger topological gap, suppressed Majorana hybridization, and dramatically extended parity lifetime.
```

**Unsupported leaps:** None identified. Each intermediate claim follows from stated premises plus presented evidence.

**Unstated premises:**
1. The parity lifetime measurement faithfully reflects quasiparticle poisoning rate rather than alternative relaxation mechanisms (partially addressed in §4 discussion of Poisson statistics).
2. The single measured tetron is representative of the array; no cross-device statistics are shown for parity lifetime.
3. Floating tetrons will have comparable or better parity lifetimes (acknowledged as expectation, not demonstrated).

## Section A: Controlling idea

**(a) STATED CLAIM**

"Here, we experimentally validate this principle in an InAs–Pb tetron device via interferometric single-shot parity measurements. By replacing aluminum with the higher-gap superconductor lead in our superconductor-semiconductor hybrid devices, we have improved the robustness of our topological phase."

The strongest single sentence appears in §5:

> "Our results confirm a central premise of topological quantum computing: increasing the excitation gap dramatically reduces error mechanisms and improves qubit performance."

**(b) DEMONSTRATED CONCLUSION**

An InAs–Pb tetron device exhibits a measured topological gap of ~70 µeV (vs ~30 µeV in Al), Majorana splitting EM < 1 µeV, and Z-parity lifetime of ~22 s (vs ~1–12 ms in Al), directly demonstrating that substituting a higher-gap superconductor yields quantitative performance improvements across multiple metrics.

**(c) CLAIM–PROOF GAP**

**NONE** — The abstract and introduction claim that increasing the gap improves device performance, and the evidence architecture establishes exactly this through: (i) material characterization showing higher induced gap, (ii) TGP analysis showing larger topological gap, (iii) rf spectroscopy showing low EM, and (iv) time-resolved parity measurement showing ~22 s lifetime. The comparison to prior Al-based devices (Refs. 59, 61) anchors the improvement claim. The paper does not overclaim universality or fault-tolerance; it states these are "implications" and "expectations" for future work.

## Section B: CME proportionality

**CLAIM (C): STRONG — ~25%**

Claims are made in §1 (introduction) and §5 (discussion): improved topological gap, suppressed EM, orders-of-magnitude improvement in parity lifetime, scalability implications. Claims are appropriately scoped to what is demonstrated and clearly distinguish demonstrated results from extrapolated expectations (e.g., "we expect that parity lifetimes in floating tetrons could be even longer").

**MECHANISM (M): STRONG — ~30%**

§1 provides the theoretical framework (topological protection scales with gap, quasiparticle poisoning independent of ∆T). §2 explains why Pb + GaSb substrate should yield improvements (higher parent gap, lattice-matched growth, enhanced spin-orbit). §3 (rf spectroscopy) derives the single-state model Hamiltonian (Eq. 1) and quantum capacitance response (Eq. 2). §4 explains the physical origin of parity lifetime enhancement (harder to break Cooper pairs in Pb, faster recombination). The mechanism story is complete and quantitative.

**EVIDENCE (E): STRONG — ~45%**

The paper is evidence-rich:
- Material characterization: Fig. 2 (induced gap 400–570 µeV, mobility >350,000 cm²/Vs, spin-orbit 12±2 meV nm)
- TGP analysis: Fig. 3 (∆T ~70 µeV, topological region >1.1 mV·T, zero-bias peaks over >0.5 T)
- rf spectroscopy: Figs. 4–5 (EM extraction with ~1 µeV resolution, correlation maps)
- Parity measurement: Fig. 6 (h/2e periodicity, τZ = 22±1 s from exponential fit to N=324 dwell intervals)

**Verdict: BALANCED**

C:25% / M:30% / E:45%. No dimension dominates by more than ~20 points; evidence is the largest component but appropriately so for an experimental paper.

## Section C: Narrative-debt register

| Promise type | Promise (location) | Status | Load-bearing? |
|---|---|---|---|
| EVIDENCE PROMISE | "we experimentally validate this principle" (abstract) | FULFILLED | N/A |
| EVIDENCE PROMISE | "we have developed an rf measurement technique that resolves low-energy wire-end states and directly measures their energy splitting with µeV precision" (abstract) | FULFILLED — §3 demonstrates resolution ~1 µeV | No |
| EVIDENCE PROMISE | "We employ this technique to bring up a device in a multi-tetron array" (abstract) | FULFILLED — §3–4 operate on the BA tetron in the array | No |
| SCOPE PROMISE | "Further time-resolved measurements reveal a characteristic parity switching time of ~20 s with some instances reaching minute-scale" (abstract) | PARTIAL — τZ = 22±1 s is shown; "minute-scale" instances are not explicitly displayed in Fig. 6(e) distribution | Cosmetic |
| RHETORICAL QUESTION | "we discuss potential implications for the fidelity of Pauli measurements" (abstract) | PARTIAL — §5 discusses qualitatively but does not quantify fidelity | Cosmetic |

**Total narrative debts: 5 (0 load-bearing)**

The "minute-scale" claim is supported by the tail of the exponential distribution but no individual trace is highlighted; this is minor. The fidelity discussion in §5 is qualitative, but the abstract uses "discuss" rather than "quantify," so no strong expectation is violated.

## Section D: Sequencing diagnosis

**Verdict: EVIDENTIAL**

The paper follows a classic escalation structure:
1. §1 (Introduction): Establishes premises (topological protection, roadmap, error mechanisms)
2. §2 (Device design and materials): Describes platform and justifies why it should work
3. §3 (rf spectroscopy): Introduces new characterization method, demonstrates low EM
4. §4 (Parity readout): Presents the headline result (τZ ~ 20 s)
5. §5 (Discussion): Synthesizes and extrapolates

The strongest result (parity lifetime) appears late, after the evidential scaffolding is complete. The abstract front-loads the result, which is standard for physics journals and does not constitute headline-first body organization.

**Proposed resequencing moves:** None required. The current order supports evidential escalation effectively. One optional refinement:

| Current position | Optimal position | Benefit |
|---|---|---|
| §5 paragraph on τX scaling ("the values of EM achieved here are expected to have beneficial implications...") | Could appear earlier in §4 as a framing paragraph | Would connect EM measurements (§3) to parity measurements (§4) more tightly before presenting data |

This is minor and not essential.

## Section E: Structural gaps

| Missing analysis | Where it should appear | CME dimension strengthened |
|---|---|---|
| Cross-device statistics for parity lifetime | §4 or supplementary | Evidence — currently N=1 tetron; showing variance across array would strengthen scalability claim |
| Error bars on ∆T values | §3 (Fig. 3c) | Evidence — "top quintile" is stated but distribution not shown |
| Direct comparison table: Al vs Pb metrics | §5 or §2 | Claim — would make the "3 orders of magnitude" comparison more immediate |
| Noise model for CQ telegraph noise | §4 | Mechanism — would formalize the Poisson assumption and bound systematic errors |
| τX measurement or projection | §5 | Evidence — discussed qualitatively but not measured; would discharge the Pauli-X implication promise |

None of these gaps are critical; the paper is complete for its stated scope.

## Summary diagnosis

The paper claims that substituting lead for aluminum in a tetron device yields dramatically improved topological protection, and demonstrates exactly this: a measured topological gap ~2× larger, Majorana splitting below 1 µeV, and parity lifetime >1000× longer than prior Al-based devices. The argument is evidentially complete, with strong material characterization (TEM, Hall bars, SdH), protocol development (rf spectroscopy), and direct measurement (h/2e-periodic parity readout with τZ = 22±1 s). The CME balance is appropriate for an experimental paper; no dimension is absent or critically thin. Narrative debts are cosmetic. Sequencing is evidential. The paper is what it claims to be: an experimental validation that increasing the superconducting gap improves topological qubit performance. No restructuring is required; minor additions (cross-device statistics, explicit comparison table) would strengthen but are not essential.

```json
{
  "overall_verdict": "PUBLISH-READY",
  "claim_proof_gap": "NONE",
  "cme_balance": "BALANCED",
  "cme_split": {"claim_pct": 25, "mechanism_pct": 30, "evidence_pct": 45},
  "narrative_debts": {"total": 5, "load_bearing": 0},
  "sequencing": "EVIDENTIAL",
  "unsupported_leaps": [],
  "unstated_premises": [
    "Parity lifetime measurement faithfully reflects quasiparticle poisoning rate rather than alternative relaxation mechanisms",
    "Single measured tetron is representative of the array (no cross-device statistics for parity lifetime)",
    "Floating tetrons will have comparable or better parity lifetimes (expectation, not demonstrated)"
  ]
}
```