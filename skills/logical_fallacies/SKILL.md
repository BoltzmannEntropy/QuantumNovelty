# `logical_fallacies` — fallacy detection with a quantum-computing taxonomy

Detects named logical fallacies in a paper, with a taxonomy extended to cover
fallacies that appear specifically in quantum-computing manuscripts. Adapted
from a standard logical-fallacy taxonomy with the quantum-specific
additions below.

## CLI

```
logical_fallacies/run.sh \
  --draft PATH \
  --outdir DIR \
  [--llm BACKEND]
  [--severity-threshold {{low,medium,high,critical}}]   # default: medium
```

## Fallacy taxonomy

### General fallacies (standard taxonomy)
- Circular reasoning / begging the question
- Appeal to authority
- Post hoc ergo propter hoc
- Slippery slope
- False dichotomy
- Hasty generalization
- Straw man
- Equivocation
- Ad hominem
- Affirming the consequent
- Denying the antecedent

### Quantum-computing-specific additions (NEW in QuantumNovelty)
- **Cherry-picked baseline** — comparing against a deliberately weak
  baseline while ignoring a stronger published method on the same
  Hamiltonian
- **Ad-hoc precision floor** — quoting an energy difference at a precision
  below the simulator's noise floor (e.g., claiming 0.001 mHa win on a
  complex64 backend whose noise floor is ~1.7×10⁻¹¹ Ha = ~17 nHa, which
  is fine, but claiming it on a backend with 3.5 mHa noise is the fallacy)
- **Conflated regimes** — extrapolating from one Hamiltonian class
  (e.g., LiH at 4 qubits) to another (e.g., FeMoco at 100+ qubits) without
  scaling argument
- **Active-space hand-wave** — claiming "this generalises to larger active
  spaces" without running the larger case or proving polynomial overhead
- **Hardware-irrelevant comparison** — comparing simulator results against
  hardware results without noise calibration
- **Asymptotic-only claim** — making a claim that holds only at N→∞ while
  the empirical demonstration is at finite small N
- **Unit-inflation** — quoting a result in units that make it look bigger
  (e.g., reporting energy errors in cm⁻¹ instead of Ha when small)
- **Simulator-laundering** — using one library to discover, a different
  library to evaluate, and reporting the second number as if both were the
  same precision
- **Mapping-by-convenience** — choosing a fermion-to-qubit mapping (JW vs
  BK vs parity) to make the qubit count or gate count look smaller
  without justifying the choice on a fidelity-or-precision axis
- **Pareto-cherry-picked-axes** — declaring Pareto domination on a chosen
  subset of axes while ignoring the axis where the baseline wins
- **Cross-LLM theatre** — calling multiple snapshots of the same model
  family a "multi-model consensus"

## Outputs (in `--outdir`)

- `fallacy_report.md` — per-finding writeup
- `fallacy_findings.json` — structured per-finding records:
  `{name, category, severity, location, evidence, suggested_fix}`
- `_backend_used.json`
- `full_prompt.txt`
- `_llm_generation.log`
