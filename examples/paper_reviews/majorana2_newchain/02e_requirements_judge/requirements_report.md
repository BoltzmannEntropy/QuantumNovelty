# Requirements Judge — claim-vs-evidence audit

Paper: `majorana2_arxiv.pdf`

**Verdict: ⚠️ PARTIAL**

## Claim ledger

| Claim | Status | Evidence | Note |
|---|---|---|---|
| Replacing Al with Pb (higher-gap superconductor) improves topological phase robustness, specifically yielding larger topological gaps | met | Top quintile topological gap ∆T ≈ 70 µeV in InAs–Pb devices vs. ∆T ∼ 30 µeV in Al-based devices (Fig. 3c-d, Section 2); induced gap ∆ind ≈ 5 | Quantitative comparison with prior Al-based devices demonstrates ~2x improvement in topological gap. |
| rf measurement technique resolves low-energy wire-end states with µeV precision | met | Section 3 describes parity-switching spectroscopy extracting EM with resolution ~1 µeV (limited by DAC resolution and lever arm αQD = 0.45 m | Resolution explicitly stated as ~1 µeV, compared favorably to DC transport resolution of ~7.6 µeV. |
| h/2e-periodic bimodal shifts in quantum capacitance observed via interferometric parity measurements | met | Fig. 6b shows flux-periodic standard deviation with periodicity 1.3 ± 0.3 mT, consistent with h/2e periodicity (1.0 ± 0.3 mT expected from l | Periodicity measurement matches h/2e expectation within uncertainty. |
| Characteristic parity switching time of ~20 s achieved | met | Fig. 6d-e: N=324 dwell intervals analyzed; exponential fit yields τZ = 22 ± 1 s; some instances reaching minute-scale mentioned | Statistical analysis with explicit uncertainty provided; methodology (Gaussian mixture model thresholding) described. |
| Parity lifetime improvement of >3 orders of magnitude over Al-based devices | met | τZ = 22 ± 1 s in Pb devices vs. ~1–12 ms in Al-based tetrons (Refs. 59, 61); ratio is ~2000-20000x improvement | Comparison references prior published work on Al-based devices; improvement factor is >1000x as claimed. |
| Extended topological phase region in (Vp, B) parameter space exceeds 1.1 mV·T | met | Fig. 3c shows TGP-identified topological region; text states 'region passing TGP exceeds 1.1 mV T, more than twice that observed Al–InAs pla | Quantitative comparison with prior platform provided. |
| Majorana splitting energy EM < 1 µeV observed in extended parameter regimes | partial | Fig. 4g shows EM at measurement resolution (~1 µeV) in shaded region; Fig. 5d shows EM 'on the order of the measurement resolution ≈ 1 µeV'  | EM is at or below resolution limit, so the claim EM < 1 µeV is consistent with but not definitively proven by the data. |
| Device demonstrates multi-tetron array architecture compatible with scaling | partial | Fig. 1 shows SEM of fabricated prototype unit cell; device described as 'prototype unit cell for multi-tetron devices'; measurements perform | Array fabricated and one tetron measured, but multi-qubit operations not demonstrated. |
| Non-equilibrium quasiparticles no longer limit qubit operations | partial | τZ = 22 s vs. typical operation times ~1 µs gives >7 orders of magnitude margin; exponential dwell time distribution consistent with Poisson | Evidence strongly supports this for Z-parity; no direct measurement of other error sources or full qubit operation fidelity. |
| Localization lengths exceed 1 µm in lowest occupied subband | met | Fig. 3b shows localization length measurements from 14 wires with lengths 1.25 µm and 3 µm; text states 'localization lengths exceeding 1 µm | Multiple devices measured; methodology from Ref. 60 cited. |
| Implications for Pauli-X measurement fidelity improvement | unmet | none | Discussion section mentions τX scales as EM² and 'could be more than an order of magnitude longer' but no τX measurements presented. |

## Allowed claims (evidence supports these)

- InAs–Pb hybrid devices achieve topological gaps of ~70 µeV (top quintile), approximately twice those in prior Al-based devices
- An rf-based spectroscopy technique can extract Majorana splitting energies with ~1 µeV resolution
- In a single tetron from a multi-tetron array, Z-parity lifetime of 22 ± 1 s was measured, representing >1000x improvement over Al-based devices
- h/2e-periodic bimodal quantum capacitance response was observed with periodicity consistent with the interferometric loop area
- The topological phase region in (Vp, B) space exceeds 1.1 mV·T, more than twice that of comparable Al-based devices
- Localization lengths exceeding 1 µm were measured in the lowest subband, indicating low disorder
- The measured EM is at or below the ~1 µeV experimental resolution in identified parameter regions
- A scalable multi-tetron unit cell geometry was fabricated and one tetron was characterized

## Forbidden claims (overclaims — evidence does NOT support)

- 'non-equilibrium quasiparticles no longer limit qubit operations' — only Z-parity lifetime measured; no full qubit operation or fidelity data presented
- 'potential implications for the fidelity of Pauli measurements' and 'τX could be more than an order of magnitude longer' — no X-parity or Pauli measurement fidelity data presented
- 'EM < 1 µeV' stated as a definite result — EM is at the resolution limit, so only 'EM ≤ 1 µeV (resolution-limited)' is supportable
- 'scalable' and 'can be tiled into much larger qubit arrays' — only single-tetron measurements presented; scalability not demonstrated
- 'functions as a modular unit cell for a larger architecture' — no multi-qubit coupling or operation demonstrated
- 'floating (charging-energy protected) tetrons could be even longer' — speculative; no floating tetron parity lifetime measured
- 'high-fidelity, fault-tolerant multi-qubit Majorana arrays' (Discussion) — no fidelity or fault-tolerance metrics reported

## What a sound revision must change

1) Rescope 'non-equilibrium quasiparticles no longer limit qubit operations' to 'Z-parity lifetime of 22 s is >7 orders of magnitude longer than typical µs operation times, suggesting quasiparticle poisoning is not limiting for single-wire parity measurements.' 2) Remove or clearly mark as speculation all claims about Pauli-X measurement improvements and fidelity implications, since no τX data is presented. 3) Change 'EM < 1 µeV' to 'EM ≤ 1 µeV (at or below measurement resolution)' throughout. 4) Rescope scalability claims to 'fabricated a multi-tetron array and characterized one tetron' rather than claiming demonstrated scalability. 5) Remove speculative claims about floating tetron performance. 6) In Discussion, replace 'fault-tolerant multi-qubit Majorana arrays' with acknowledgment that fault-tolerance requires future measurements of multi-qubit operations and fidelity.
