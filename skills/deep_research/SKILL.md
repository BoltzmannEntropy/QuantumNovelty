# `deep_research` — quantum-aware multi-mode research skill

Seven modes for research on a quantum-computing topic. Inspired by the
deep-research pattern in academic-research-skills; the quantum twist is that
every mode is aware of (a) the Hamiltonian family / ansatz family being
investigated, (b) the simulator-precision floor the user's target library
provides, and (c) the strict-domination comparator that gates novelty claims.

## CLI

```
deep_research/run.sh \
  --mode MODE \
  --topic "STR" \
  --outdir DIR \
  [--llm BACKEND]                  # default: claude
  [--journal SLUG]                 # default: none — generic output
  [--quantum-lib SLUG]             # default: none — library-agnostic
  [--hamiltonian-id STR]           # optional context: e.g. "H2O_4e_4o_8q"
```

## Modes

| Mode | When to use | Trigger phrase (chat skill) |
|---|---|---|
| `full` | Multi-source pull + LLM synthesis + baseline catalog suitable for `novelty_audit` augmentation | "Research the impact of LLM-guided ansatz discovery on small-molecule VQE" |
| `quick` | One-pass brief, no card extraction | "Quick brief on Strang-Suzuki Trotter error scaling" |
| `systematic-review` | PRISMA-style flow on a defined quantum subtopic | "Systematic review on shadow tomography sample complexity" |
| `socratic` | Iterative back-and-forth that helps the user formulate their research question; emits a `research_question.md` + sub-questions tree | "Guide my research on noise-model-aware VQE optimisation" |
| `fact-check` | Verify specific quantitative quantum claims (energy values, gate counts, fidelities) against published sources | "Fact-check: is UCCSD-1-Trotter on LiH 198 gates with 64 CNOTs?" |
| `lit-review` | Extended literature review section ready for direct manuscript inclusion | "Literature review on Pareto-front methods in quantum compilation" |
| `review` | Review a candidate paper's research quality (NOT a peer-review panel — that's `quantum_reviewer`) | "Review this paper's research approach" |

## Quantum twist per mode

- **`full` / `lit-review`**: every surfaced paper is checked for a Hamiltonian-and-active-space match (e.g., H₂O at (4e, 4o)) before being added to the augmented-baseline catalog. Papers with claims at incomparable system sizes are tagged `out-of-scope-for-comparator` so they don't pollute `novelty_audit`.
- **`fact-check`**: where the claim is a numerical quantum-chemistry value (energy, dipole, gap), the skill queries the source paper's data table directly via `literature_surfacer` and reports the displayed value, the unit (Ha / eV / mHa / cm⁻¹), and the active space. Catches the unit-mismatch class of citation errors.
- **`systematic-review`**: PRISMA flow adapted to include a separate "Hamiltonian-class match" inclusion criterion. The exclusion log records every paper rejected for system-size mismatch.
- **`socratic`**: the question tree explicitly distinguishes "physics question" from "algorithmic question" from "engineering question" — three distinct subtrees so the user doesn't conflate them.
- **`review`**: assesses methodology against the audit-and-falsify checklist (augmented baselines? recompute? Wilson CIs? cross-LLM? honest negatives?). Output names which audit checks the paper would pass and which it would fail.

## Outputs (in `--outdir`)

All modes produce:
- `_backend_used.json`
- `full_prompt_<mode>.txt`
- `_llm_generation.log`

Mode-specific:
- `full`: `synthesis.md`, `cards/*.json`, `baseline_catalog.json`
- `quick`: `brief.md`
- `systematic-review`: `prisma_flow.md`, `included.json`, `excluded.json`
- `socratic`: `research_question.md`, `subquestions_tree.json`, `next_steps.md`
- `fact-check`: `factcheck_report.md` (per-claim verdict + source)
- `lit-review`: `lit_review.md`
- `review`: `research_quality_review.md` + audit-checklist verdict

## Provenance

Built on:
- ARS's deep-research pattern (mode taxonomy)
- QN's literature_surfacer + book_acquirer for the data layer
- QN's audit_falsify primitives for the `review` mode's checklist
