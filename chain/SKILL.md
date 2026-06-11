---
name: qn-chain
description: Modular workflow chain composing the QuantumNovelty skill catalog (deep_research, quantum_reviewer, logical_fallacies, novelty_audit, cross_llm_prediction, pareto_explorer, quantum_paper, process_summary, ...) into named pipelines for quantum-computing research. Per-stage `--with-X` / `--skip-X` toggles, structured telemetry (`pipeline_summary.json`, `decision_history.json`, `_stage_health.json`, `HEARTBEAT_AUDIT.md`, `checkpoint.json` — AutoResearchClaw's stage-health pattern), strict no-fallback env defaults, and a cross-model falsifiability fork. The QN-specific contributions are: paper-audit as a first-class pipeline, the 11 quantum-CS-specific fallacy taxonomy in the fallacies stage, the cross-LLM amplitude-prediction skill (`cross_llm_prediction`) as an opt-in stage, and the audit-and-falsify Pareto novelty check.
---

# QN Chain — workflow runner

A single entry point (`chain/run.sh`, dispatching to `chain/pipelines.py`) that composes the QuantumNovelty skill catalog into modular pipelines with per-stage toggles, resumable checkpoints, and structured telemetry.

## Pipelines

| Pipeline               | Building blocks (in order)                                                                                                      | Use case                                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `paper-audit`          | `deep_research --mode review` → `quantum_reviewer --mode full` → `logical_fallacies` → `process_summary` (Stage-6 CQE)            | Audit an existing paper (PDF / TeX / text). Default 4 stages; opt-in `novelty-audit` + `cross-llm`.   |
| `full`                 | `deep_research --mode full` → `pareto_explorer` → `novelty_audit` → `quantum_paper --mode full` → `cross_llm_prediction` → `quantum_reviewer` → `logical_fallacies` → `process_summary` | Full Stage 1→6 pipeline: literature surface → discovery → audit → draft → cross-LLM → review → CQE.   |
| `mid-entry-stage-2.5`  | `deep_research --mode full` (lit-1.5) → `novelty_audit` (audit-only mode) → `quantum_reviewer` → `logical_fallacies` → `process_summary` | Paper exists; integrity-first pass without the discovery / draft stages.                              |
| `mid-entry-stage-4`    | `quantum_paper --mode revision` → `quantum_reviewer --mode re-review` → `process_summary`                                       | Reviewer comments in hand; revision pass.                                                             |

Run `bash chain/run.sh --list-stages` for the live table.

## Option surface

The full flag surface:

```
# Pipeline + I/O
--pipeline NAME             Pick a pipeline (paper-audit | full | mid-entry-stage-2.5 |
                            mid-entry-stage-4 | status | list-stages)
--llm BACKEND               claude (default) | codex | codex-acp | codex-mcp | anthropic-api
--paper PATH                Existing paper file (text / TeX / PDF-extracted text)
--topic STR                 Research question / paper title — grounds deep_research
--journal STR               Venue context for prompts (npj-quantum-information, prx-quantum, …)
--quantum-lib LIB           Library context for code-gen prompts (qiskit, pennylane, qutip, …)
--outdir DIR                Output root. Auto-derived to runs/<ts>/<llm-slug>/<pipeline>/ if unset.

# Stage toggles (default-on stages of paper-audit shown)
--skip-research             Drop deep_research --mode review
--skip-reviewer             Drop quantum_reviewer --mode full
--skip-fallacies            Drop logical_fallacies
--skip-cqe                  Drop process_summary

# Opt-in stages
--with-novelty-audit        Add novelty_audit  (needs --pareto-archive PATH)
--with-cross-llm            Add cross_llm_prediction  (needs --hamiltonian + --geometry-sweep + --llms)
--with-synthesizer          Add editorial synthesis (ARS editorial_synthesizer
                            pattern). Consumes the panel +
                            fallacy + research outputs already in the outdir;
                            produces an Editorial Decision Package with
                            CONSENSUS-N tags, disagreement resolution,
                            3-priority revision roadmap, response-letter
                            template. Runs as stage 03b, before cqe.

# ARC profile bundles + per-stage flags
--with-arc-pipeline         Bundle: arms every QN-applicable ARC stage
--with-arc-novelty-check    Alias for --with-novelty-audit
--with-arc-problem-tree     | --with-arc-literature-pipeline | --with-arc-paper-outline
--with-arc-draft-quality    | --with-arc-iterative-refine    | --with-arc-citation-integrity
--with-arc-compilation-quality | --with-arc-paper-verification | --with-arc-pdf-review
--with-arc-quality-gate     | --with-arc-research-decision   | --with-arc-knowledge-archive

# Cross-vendor falsifiability
--with-cross-model          Fork the chain on claude + codex (claude_branch/ + codex_branch/),
                            write _cross_model_index.json pointing at both.

# Checkpoints
--pause-after STAGE         Write checkpoint.json after STAGE completes, exit cleanly
--hitl-pause-after STAGE    Alias; same behaviour (sets QN_HITL_PAUSE_AFTER env)
--resume-from STAGE         Treat earlier stages as complete; pick up at STAGE
--force                     Re-run completed stages (override idempotent resume)

# Backend policy
--with-codex-fallback       Re-enable the legacy silent claude→codex fallback.
                            Off by default — framework default is strict.

# Process summary tuning
--no-llm-narrative          Disable the LLM-narrative pass in process_summary
```

## Telemetry

Every paper-audit run writes (alongside the per-stage outputs):

| File                         | Schema source                                          | Purpose                                                                                       |
| ---------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `<stage>/_stage_health.json` | `chain/common/stage_telemetry.sh`                      | `stage_id`, `status`, `duration_sec`, `artifacts_count`, `error`, `started_iso`, `ended_iso`  |
| `pipeline_summary.json`      | `chain/common/telemetry.py::pipeline_summary`          | Aggregate of every `_stage_health.json` + `content_metrics` (CQE composite, fallacy count)    |
| `decision_history.json`      | `chain/common/stage_telemetry.sh::decision_log`        | Append-only log: `proceed` / `refine` / `pivot` / `pause` / `block` / `fail`                  |
| `HEARTBEAT_AUDIT.md`         | `chain/common/heartbeat.sh::audit_heartbeats`          | Per-stage `OK` / `TIMED_OUT` / `HUNG_OR_KILLED` / `RUNNING` / `UNTRACKED`                     |
| `checkpoint.json`            | `chain/common/stage_telemetry.sh::checkpoint_write`    | Resumable pause marker; written when `--hitl-pause-after STAGE` matches                       |
| `_chain_config.json`         | `chain/pipelines.py::pipeline_paper_audit`             | Resolved chain configuration: pipeline preset, llm, default-on/opt-in stages, decision-log    |
| `_run_summary.json`          | `chain/pipelines.py::_emit_pipeline_summary`           | Subprocess-RC view: per-stage exit codes, elapsed-s, skip status                              |
| `02_reviewer_panel/_quality_gate.json` | ARC `quality_gate` shape (deterministic parse) | `{score_1_to_10, verdict, votes, threshold, passes_threshold, required_actions}` — mean of per-voice panel scores gated at `--gate-threshold` (default 7.0). No extra LLM call. |

`chain/common/heartbeat.sh` and `chain/common/stage_telemetry.sh` implement AutoResearchClaw's stage-health / heartbeat / checkpoint pattern in bash. `chain/common/telemetry.py` is a Python port of the same six helpers so `chain/pipelines.py` produces the same JSON shapes when it orchestrates from Python instead of bash.

## Strict-env defaults

Set at module load (override only when really needed):

| Env var                              | Default | Purpose                                                                |
| ------------------------------------ | ------- | ---------------------------------------------------------------------- |
| `CLAUDE_DISABLE_CODEX_FALLBACK`      | `1`     | No silent claude→codex fallback inside the claude CLI                  |
| `INVOKE_LLM_NO_FALLBACK`             | `1`     | No invoke_llm-level fallback                                           |
| `QN_DISABLE_BACKEND_FALLBACK`        | `1`     | No QN-level fallback                                                   |
| `QN_HITL_PAUSE_AFTER`                | unset   | Stage-id substring; when set, the chain checkpoints + exits after match |

## Examples

```
# Default audit of one paper:
bash chain/run.sh --pipeline paper-audit \
  --llm codex --paper paper.txt --journal npj-quantum-information \
  --topic "Generative flow-based warm start of the VQE" --outdir runs/flowvqe

# Reviewer-panel-only run:
bash chain/run.sh --pipeline paper-audit --skip-research --skip-fallacies --skip-cqe ...

# Add cross-LLM falsifiability:
bash chain/run.sh --pipeline paper-audit \
  --with-cross-llm --hamiltonian H2 \
  --geometry-sweep "R_HH=0.7,0.9,1.1,1.3,1.5 A" \
  --llms claude,codex ...

# Cross-model fork:
bash chain/run.sh --pipeline paper-audit --with-cross-model ...

# Checkpoint after reviewer panel, resume from fallacies:
bash chain/run.sh --pipeline paper-audit --hitl-pause-after reviewer ...
# ...inspect outputs...
bash chain/run.sh --pipeline paper-audit --resume-from fallacies ...

# List every pipeline's stages + their toggle flags:
bash chain/run.sh --list-stages
```

## Files

- `chain/run.sh` — bash dispatcher; argparse + auto-discover skills + dispatch to `pipelines.py`
- `chain/pipelines.py` — Python orchestrator with the canonical stage definitions
- `chain/common/heartbeat.sh` — heartbeat + sentinel wrapper (ARC pattern)
- `chain/common/stage_telemetry.sh` — stage-health + checkpoint + decision-log helpers
- `chain/common/telemetry.py` — Python port of the same six helpers
- `tests/test_telemetry.py` — 30+ tests pinning the telemetry schema contract

## What's NOT here yet

A handful of ARC profile flags are surfaced in the option table but currently route to nothing at runtime — they're documented for forward-compatibility and emit a decision_log entry on activation. As QN ports more ARC stages (`--with-arc-citation-integrity` and `--with-arc-quality-gate` are the next ones planned), the flags will start exercising real stages.
