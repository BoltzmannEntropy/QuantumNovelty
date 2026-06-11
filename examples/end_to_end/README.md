# End-to-end examples

> **How this differs from `examples/paper_reviews/`:** that folder is the
> reviewer showcase (the `paper-audit` pipeline run on five real papers,
> one folder per paper with a standalone review PDF each).
> This folder demonstrates the framework itself end-to-end:
> `two_paper_novelty/` (the chain-runner harness + telemetry walkthrough,
> final report [`PIPELINE_REPORT.pdf`](two_paper_novelty/PIPELINE_REPORT.pdf)),
> `compare_qn_vs_ars_vs_arc/` (the QN/ARS/ARC head-to-head, final report
> [`COMPARE_REPORT.pdf`](compare_qn_vs_ars_vs_arc/COMPARE_REPORT.pdf)),
> and `avenue_*` (three papers generated from a blank page, drafts in
> `stage_4_draft/paper.pdf`).

Five worked examples showing QuantumNovelty in action on realistic
quantum-computing tasks. Each example contains:

- The **command(s)** that produce the example
- The **runs/ tree** the commands generate
- The **key output files** annotated with what to look at
- The **CQE score** at the end (when the pipeline ran to Stage 6)

| # | Example | When you'd use this |
|---|---|---|
| [02](#02-full-pipeline-from-a-topic) | Full pipeline from a topic | You have a research question, no paper, want the framework to take you from blank page to draft |
| [03](#03-chat-dispatch-demo) | Chat NL frontend dispatch | You don't want to remember CLI flag combinations — type natural-language instead |
| [04](#04-journal-selection) | Same input, three different venues | You're choosing between npj-QI / PRX Quantum / Quantum and want to see venue-specific drafts |
| [05](#05-cross-llm--quantum-lib) | Cross-LLM + quantum-library matrix | You want falsifiability + library-specific code (Qiskit vs PennyLane vs mlxq) |

Each example's directory contains the populated run-dir so you can browse
the artefacts without running anything.

---


The marquee demonstration: point QN at the paper that motivated it and see
what the audit-and-falsify framework says.

### Command

```bash
QN=/path/to/QuantumNovelty

# 1. Build the Pareto archive from the paper's measurements (already in the
#    example tree as stage_2_discovery/archive.json)
# 2. Run novelty_audit against the augmented baseline catalog
bash $QN/skills/novelty_audit/run.sh \
  --augmented-baselines <your-run>/stage_1_literature/baseline_catalog.json \
  --draft            $PAPER/your_paper.tex \
  --hamiltonian-id   LiH_4q_STO-3G_R1.5A \
  --no-require-failure-modes

# 3. Score the run-dir on the 6-dim CQE (no LLM call required for scoring)
bash $QN/skills/process_summary/run.sh \
  --outdir  <your-run>/stage_6_summary \
  --no-llm-narrative
```

### What the framework produces

```
├── stage_1_literature/
│   └── baseline_catalog.json       ← 7 augmented baselines (LiH + H2O, real values)
├── stage_2_discovery/
│   └── archive.json                ← 6 Pareto rows from the paper's discovery loop
├── stage_3_audit/                  ← OUTPUT of novelty_audit
│   ├── novelty_verdict.json        ← 7 verdicts: interpolation / rediscovery / ...
│   ├── augmented_pareto.json
│   ├── ratio_recompute.md
│   ├── wilson_annotations.md
│   ├── failure_modes_required.md   ← 6 honest negatives surfaced
│   ├── audit_claims.py             ← re-runnable per-claim auditor
│   └── borderline_llm_review.md    ← LLM review of borderline cases (if available)
├── stage_4_draft/
├── stage_4a_xllm/
│   └── results.json                ← cross-LLM amplitude prediction at R_OH ≈ 1.5 Å
├── stage_5_review/
│   └── review_panel.md             ← 5-voice panel (EIC + R1/R2/R3 + DA)
├── stage_5b_fallacies/
│   └── fallacy_findings.json       ← 0 findings ≥ medium severity (paper went through framework)
└── stage_6_summary/
    └── cqe_scores.json             ← REAL composite CQE: 82/100
```


```
Composite (geometric mean): 82/100

Per-dimension:
  Novelty rigour             90/100  ← augmented catalog present + 4 rediscoveries honestly classified
  Reproducibility            80/100  ← audit_claims.py present + Pareto archive structured
  Methodological rigour      65/100  ← Wilson CIs + ratio recompute present; ablations missing in this stub run
  Falsifiability             90/100  ← cross-LLM with 2 vendors + honest-negatives surfaced
  Domain depth               83/100  ← active space + JW mapping + precision floor disclosed
  Communication              85/100  ← 0 fallacies above medium + minor-revisions verdict
```

The framework's own discipline scores its motivating paper at 82/100. The
methodological rigour dimension drags lowest because this particular run-dir
doesn't include `ablation_designer` output; populating that stage would
push the composite into the 86-88 range.

---

## 02. Full pipeline from a topic

Start with a research question, end with a draft + reviewer panel + CQE
score. Six stages, one command.

### Command

```bash
QN=/path/to/QuantumNovelty

# Single command that runs Stages 1 → 6.
# Pipeline orchestrator is in chain/pipelines.py; chain/run.sh dispatches to it.
bash $QN/chain/run.sh --pipeline full-pipeline \
  --topic       "LLM-driven UCCSD pruning for small-molecule VQE" \
  --hamiltonian H2O_4e_4o_8q_STO-3G \
  --baseline    "UCCSD-1-Trotter,UCCSD-K5-pruned,HEA-5L" \
  --geometry-sweep "R_OH=0.7,0.96,1.2,1.5,2.0 A" \
  --llms        "claude,codex" \
  --journal     npj-quantum-information \
  --quantum-lib mlxq \
  --llm         claude
```

### Auto-derived runs/ path

```
runs/
└── 20260610_123022/                ← timestamp (one per chain invocation)
    └── claude/                      ← --llm slug
        └── full-pipeline/           ← --pipeline
            ├── stage_1_literature/  ← deep_research --mode full
            ├── stage_2_discovery/   ← pareto_explorer (requires --evaluator-cmd or --plan-only)
            ├── stage_3_audit/       ← novelty_audit
            ├── stage_4_draft/       ← quantum_paper --mode full
            ├── stage_4a_xllm/       ← cross_llm_prediction
            ├── stage_5_review/      ← quantum_reviewer --mode full
            ├── stage_5b_fallacies/  ← logical_fallacies
            ├── stage_6_summary/     ← process_summary (CQE)
            └── pipeline_summary.json ← per-stage rc + elapsed_s
```

### Resumability

Re-run with the same `--outdir`:

```bash
bash $QN/chain/run.sh --pipeline full-pipeline \
  --topic       "..." \
  --outdir runs/20260610_123022/claude/full-pipeline \
  --hamiltonian H2O_4e_4o_8q_STO-3G \
  --baseline    "UCCSD-1-Trotter,..." \
  ...
```

Stages whose outdirs already exist are skipped (note in
`pipeline_summary.json::stages[].notes`); `--force` re-runs everything.

---

## 03. Chat dispatch demo

Type natural language; QN routes to the right skill + mode.

### Pattern-first dispatch (deterministic, no LLM)

```bash
# "Write a paper on X" → quantum_paper --mode full --topic X
bash chain/run.sh --pipeline chat \
  --prompt "Write a paper on LLM-driven VQE ansatz discovery"

# Routes deterministically with confidence=1.0:
# {
#   "skill": "quantum_paper", "mode": "full",
#   "flags": {"topic": "LLM-driven VQE ansatz discovery"},
#   "confidence": 1.0, "rationale": "pattern match"
# }
```

### Other recognised phrasings

```bash
"Quick brief on shadow tomography"             → deep_research --mode quick
"Systematic review on Pareto methods"          → deep_research --mode systematic-review
"Guide my research on noise-model-aware VQE"   → deep_research --mode socratic
"Build a paper outline on Trotter error"       → quantum_paper --mode outline-only
"Convert this paper to prx-quantum format"     → quantum_paper --mode format-convert --journal prx-quantum
"Review this paper" --paper draft.tex          → quantum_reviewer --mode full
"Check the methodology" --paper draft.tex      → quantum_reviewer --mode methodology-focus
"Find fallacies in this paper" --paper d.tex   → logical_fallacies
"status"                                       → PIPELINE --status
```

### LLM fallback for unrecognised phrasings

```bash
# Phrasings not in the pattern table fall through to LLM routing:
bash chain/run.sh --pipeline chat \
  --prompt "Audit this manuscript and tell me whether it could pass npj review" \
  --paper draft.tex \
  --execute  # actually run the dispatched command
```

LLM-routed dispatches have confidence < 1.0 and a one-sentence rationale.

---

## 04. Journal selection

Same input, three venues. The drafted paper / abstract / disclosure block all
adapt to the journal's policy (`section_order`, `abstract_word_limit`,
`required_statements`).

### Command — same topic, three journals

```bash
TOPIC="K=5 amplitude pruning for UCCSD on H2O"

# 1. npj Quantum Information — Methods at END, 250-word abstract
bash chain/run.sh --pipeline quantum-paper --mode full \
  --topic "$TOPIC" --journal npj-quantum-information \
  --quantum-lib mlxq

# 2. PRX Quantum — Methods inline, no abstract word limit
bash chain/run.sh --pipeline quantum-paper --mode full \
  --topic "$TOPIC" --journal prx-quantum --quantum-lib mlxq

# 3. Physical Review Letters — STRICT 4-page limit
bash chain/run.sh --pipeline quantum-paper --mode full \
  --topic "$TOPIC" --journal physical-review-letters --quantum-lib mlxq
```

### What changes per venue

| Venue | Template | Abstract limit | Methods | Required statements |
|---|---|---|---|---|
| npj-quantum-information | revtex4-2 | 250 words | END of paper | Author Contributions, Competing Interests, Data Availability, Code Availability |
| prx-quantum | revtex4-2 | none | INLINE (Methods/Background section) | Acknowledgments + opt. Competing Interests |
| physical-review-letters | revtex4-2 | ~600 words (whole paper ≤4 pages) | INLINE; everything ≤4 pages | Acknowledgments |

### Inspecting the policy

```bash
# Print the full policy for any venue
python3 -m skills.common.journals show npj-quantum-information

# Dump as JSON for programmatic consumption
python3 -m skills.common.journals dump prx-quantum
```

### Convert between venues

If you draft for npj and decide to submit to PRX:

```bash
bash chain/run.sh --pipeline quantum-paper --mode format-convert \
  --paper draft_npj.tex --journal prx-quantum
# Writes converted.tex + conversion_notes.md
```

---

## 05. Cross-LLM + quantum-lib

Falsifiability rubric across vendors + library-specific code generation.

### Cross-LLM falsifiable amplitude prediction

```bash
# Predict the top-5 dominant amplitudes at five geometries of H2O,
# using TWO DIFFERENT VENDORS. Falsifiability constraints enforced by code:
# (1) different vendors required, (2) predictions persisted BEFORE truth.
bash chain/run.sh --pipeline cross-llm \
  --hamiltonian H2O_4e_4o_8q_STO-3G \
  --geometry-sweep "R_OH=0.7,0.96,1.2,1.5,2.0 A" \
  --llms "claude,codex" \
  --llm claude  # backend for the dispatch (--llms is the prediction set)
```

The skill refuses single-vendor input — two `claude*` snapshots throw a
`ValueError("cross-LLM falsifiability requires AT LEAST 2 distinct vendors")`.

To score against truth, supply `--truth-file` with the FCI top-K indices
per geometry; this is consumed AFTER all predictions have been persisted.

### Quantum-library selection for code generation

When a skill generates code (e.g., `quantum_paper --mode full` with code
snippets, or `pareto_explorer` candidates), the chosen library shapes the
output:

```bash
# Generate the same paper's code skeletons in different libraries
for lib in qiskit pennylane qutip mlxq cirq; do
  python3 -m skills.common.quantum_libs skeleton $lib > /tmp/skeleton_$lib.py
done

# Inspect mlxq's notes (includes the precision-floor lesson)
python3 -m skills.common.quantum_libs show mlxq
```

### "no-code" mode

For analytical / theoretical papers without code:

```bash
bash chain/run.sh --pipeline quantum-paper --mode full \
  --topic "Trotter-error lower bounds for commutator-grouped methods" \
  --journal physical-review-letters \
  --quantum-lib no-code  # skips code generation entirely
```

---

### Running the audit pipeline against your own artefacts

If your paper has on-disk experiment JSON, point the novelty-audit
pipeline at it directly:

```bash
bash chain/run.sh --pipeline novelty-audit \
  --pareto-archive   /path/to/experiments/comparison.json \
  --paper            /path/to/your_paper.tex
```

That run operates on your real on-disk JSON artefacts and your real
manuscript, routed through the QN skills.
