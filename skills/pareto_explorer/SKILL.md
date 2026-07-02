# `pareto_explorer` — DEPRECATED legacy ansatz/Pareto discovery

`pareto_explorer` is retained for reproducing the original VQE/ansatz
experiments and for backward compatibility. It is intentionally narrow:
fixed-Hamiltonian ansatz mutation plus strict-domination Pareto archiving.

For general quantum-computing novelty scouting, use:

```bash
bash chain/run.sh --pipeline scout --topic "your quantum-computing subject"
```

That path can scout algorithms, hardware, control, QEC, QML, compilers,
networks, sensing, simulation, and other quantum subjects, with literature,
arXiv/PDF acquisition, quote substantiation, and recommended avenues.

Legacy behavior: drives an LLM mutation loop over quantum-circuit ansätze, building a
strict-domination Pareto archive over (energy, params, ops, cnots).
Each generation the LLM proposes K candidates; the evaluator measures
them against a fixed Hamiltonian; non-dominated points join the archive.

## Three evaluation modes

**Built-in (default)** — no flags needed. Candidates are JSON gate
lists (never executed as code), evaluated by the bundled numpy
statevector simulator + SPSA optimizer against exact diagonalization:

```bash
bash skills/pareto_explorer/run.sh \
  --hamiltonian TFIM_4q --baseline "HEA-1L,HEA-2L" \
  --generations 4 --samples 4 --outdir OUT
```

Built-in Hamiltonian registry: `TFIM_<n>q`, `HEISENBERG_<n>q`
(n = 2..10), `H2_2q` (2-qubit tapered H2 at R = 0.7414 Å; exact ground
energy −1.857275 Ha). Baseline labels matching `HEA-<L>L` are evaluated
for real; other labels are carried as unevaluated seed rows.

**External evaluator** — `--evaluator-cmd CMD`: candidates are Python
blocks written to files; CMD gets the path as last arg and prints
metrics JSON (`{"energy_ha":..., "params":..., "ops":..., "cnots":...}`).

**Plan only** — `--plan-only`: write the run plan + a stub archive,
zero LLM/evaluator calls.

## Inputs / outputs

Inputs: `--hamiltonian ID`, `--baseline LIST`, `--generations N`,
`--samples K`, `--spsa-iters N` (default 250), `--llm claude`.
Outputs: `archive.json` (input to `novelty_audit`), per-generation
prompts + responses, `candidates/*.json`, `_backend_used.json`.

## Guarantees

- LLM output is data (validated JSON gate lists), not executed code.
- Energies come from exact statevector simulation; `e_exact_ha` ships
  in every row so the error is independently checkable.
- Archive merge uses the same strict-domination comparator (calibrated
  ε) as `novelty_audit`.
