<div align="center">

<img src="assets/logo.svg" alt="QuantumNovelty" width="520"/>

<br/>

<code>v1.0.0</code> &nbsp;Claude Code CLI · Quantum Papers &amp; Patents · 152 tests

<b>Shlomo Kashani</b> · <a href="https://qneura.ai/apps.html">QNeura.ai</a>

<h2>Review any quantum paper <em>like a referee</em> · Examine any quantum patent <em>like a USPTO examiner</em> + Agentic Audit-and-Falsify Pipeline</h2>

Nineteen agent skills that write and review quantum-computing papers, and examine quantum patents —<br/>
a 5-voice reviewer panel, a 6-voice USPTO examiner panel (§§101/102/103/112 → an Office Action),<br/>
an 11-fallacy quantum-CS taxonomy, strict-domination novelty audits,<br/>
and an exact token + USD cost ledger on every LLM call.<br/>
Runs on the <b>Claude Code CLI</b> by default; Codex available for cross-vendor falsifiability.

<p>
<a href="#installation"><b>Get Started</b></a> ·
<a href="https://boltzmannentropy.github.io/QuantumNovelty.github.io/"><b>Website</b></a> ·
<a href="https://github.com/BoltzmannEntropy/QuantumNovelty"><b>View on GitHub</b></a>
</p>

Claude Code CLI · MIT licensed · Sister project: <a href="https://github.com/BoltzmannEntropy/osxQ">osxQ — Apple Silicon quantum simulation stack</a>

</div>

> **Paper Audit | 5-Voice Review Panel | Patent Examination (USPTO Office Action) | Quantum-CS Fallacies | Novelty Audit | Editorial Synthesis | Token + USD Ledger**

A framework for **exploring genuine novelty** in quantum-computing research **and patents**. Built on the shoulders of **AutoResearchClaw (ARC)** and [**academic-research-skills (ARS)**](https://github.com/imbad0202/academic-research-skills), with one new contribution of our own: an **audit-and-falsify layer** that refuses to let an LLM-driven discovery loop declare victory until the win has been compared against the strongest known baseline at **strict Pareto-domination tolerances**, and every numerical claim in the resulting paper has been **re-derived from on-disk JSON artifacts**. The same machinery turns on patents: a `patent-audit` pipeline runs a **simulated USPTO examiner panel** that examines every claim under **35 U.S.C. §§ 101/102/103/112** and issues an **Office Action** (with a deterministic disposition + rejections-by-statute gate and a styled PDF report). Tested on five real papers — four peer-reviewed (PRX Quantum / npj Quantum Information / Quantum) plus Microsoft Quantum's tetron preprint — with the full review PDFs and per-call cost receipts shipped in `examples/`.

License: MIT. See [LICENSE](LICENSE).

---

## Why this exists — a personal note

I was researching energy-minimisation for small molecules on my own Apple-Silicon-native quantum simulator (`mlxq`), pushing UCCSD-1-Trotter against a dozen variants of LLM-evolved ansätze on H₂, LiH, BeH₂, H₂O, N₂, CO. I had a chain of evolutionary mutations, a Pareto archive over (energy-error, parameter-count, CNOT-count), and a story that *looked* like AlphaEvolve for VQE.

Then I started reading my own findings the way a reviewer would. The story unravelled — and it unravelled the same way at every scale:

- **The LLM's "discovery" turned out to be in a published baseline I hadn't yet read.** Adding the paper to the comparator turned a strict-domination win into a rediscovery.
- **A "shallow circuit, chemical accuracy" result was running on a `complex64` accumulator** that I'd silently swapped in for speed. The same circuit on `float64` lost the win by 3.5 mHa.
- **A cross-LLM "consensus prediction" was eight identical Anthropic-snapshot calls** dressed up as a multi-model panel.
- **A "novel Trotter ordering" was random ablation with the LLM mutator turned off** that happened to land on the same ordering — i.e., the LLM contributed nothing the random walk wouldn't have.

Every one of these would have been a Sev-5 finding in peer review. None of them showed up in the first six drafts of my paper. They showed up when I built a deterministic audit script — `audit_claims_prx.py` in the example below — that re-derived every numeric claim in the manuscript from the original JSON artefacts, used Wilson 95 % CIs on every small-sample rate, ran cross-LLM with deliberately distinct frontier models, and refused to call something "novel" until a strict-domination comparator had been run against an augmented baseline catalog that *included* the most recent published method.

Once that audit existed, the paper rewrote itself into a calibrated dual-contribution: an empirical headline (LLM evolution finds a 14× shallower LiH ansatz than UCCSD-1-Trotter at chemical accuracy, replicated across five cold starts) plus a methodological honest-negatives section (the same harness produced a clear cross-LLM geometric-transition finding, *and* could not improve on UCCSD for H₂O, N₂, CO at 8 qubits — which is the more interesting result).

That experience is the framework. The paper itself — AlphaQuantum — is currently in development and will be released in its own repository once published; QuantumNovelty ships the *workflow* that produced it.

I built this because I wanted to publish the *workflow* that survived contact with my own findings, not just the findings themselves. If you're a quantum-computing researcher considering an LLM-in-the-loop discovery agent, **QuantumNovelty gives you the audit-and-falsify scaffolding before you've sunk a year into a paper that won't survive peer review.**

— *Shlomo Kashani, June 2026*

---

## What it is

QuantumNovelty is a Python + bash skill catalog plus a workflow chain that composes those skills into pipelines. Each skill is a single-purpose agent (one prompt template + one Python driver) that does one named thing — surface literature, predict amplitudes, run an ablation, audit a Pareto front, write a manuscript section. The chain composes them.

Concretely:

```
QuantumNovelty/
├── skills/                    # The skill catalog. Each subdir = one skill.
│   ├── common/                # Shared infra: LLM backends, Anna's Archive,
│   │   ├── llm.py             # prompt helpers. NOT a skill itself.
│   │   ├── annas_archive.py
│   │   └── prompts.py
│   ├── novelty_audit/         # ← THE ONE WE ADDED (see "Our contribution").
│   ├── audit_falsify/         # Strict-domination Pareto comparator + claim audit
│   ├── pareto_explorer/       # LLM-in-loop Pareto-front discovery
│   ├── ablation_designer/     # Design controlled ablations vs random/LLM mutator
│   ├── cross_llm_prediction/  # Falsifiable amplitude-prediction rubric
│   ├── literature_surfacer/   # Multi-source literature pull (CrossRef + arXiv + S2)
│   └── book_acquirer/         # Anna's Archive download + OCR
├── chain/                     # Workflow dispatcher composing skills into pipelines
│   ├── run.sh
│   └── pipelines.yaml
├── examples/
└── tests/                     # Smoke tests (no LLM cost)
```

## Provenance — what we built on

QuantumNovelty stands on two upstream projects. We took ideas, patterns, and (where applicable) code, and bolted on the one thing they were missing for quantum-computing-novelty work specifically.

### AutoResearchClaw (ARC) — the back-half audit pipeline

ARC contributed the *gate-stack* pattern: every research artefact passes through a series of independent quality gates (citation-integrity → compilation-quality → paper-verification → quality-gate → research-decision → knowledge-archive), each producing structured JSON the next stage consumes. The verdicts compose into a `PROCEED / REFINE / PIVOT` decision the human author can act on.

QuantumNovelty reuses the ARC gate stack verbatim in `chain/`, with one change: we route the `paper-verification` stage through our `audit_falsify` skill (see below) so that "the abstract says 0.005 mHa" gets compared to the on-disk `experiment_summary.json` value, not to whatever the LLM remembers writing.

### academic-research-skills (ARS) — the modular skill pattern

ARS contributed the *skill-as-folder* pattern: each skill is a self-contained directory with `SKILL.md`, `run.sh`, and a Python driver; skills declare their inputs/outputs in a small machine-readable header; a chain composes them by name. We adopted this pattern wholesale — it's what makes adding a new skill a 10-minute job instead of a refactor.

ARS also contributed the `literature_surfacer` style: a multi-source pull (CrossRef + arXiv + Semantic Scholar + optionally Google Scholar via Serper) followed by an LLM extractor that builds per-source cards. Our `skills/literature_surfacer/` is a direct port of that pattern with one addition: every source that fails to resolve gets passed to `skills/book_acquirer/` to attempt an Anna's Archive download.

### Our contribution — `skills/novelty_audit/`

The new skill — the reason QuantumNovelty exists — is **`novelty_audit`**. It implements the audit-and-falsify framework from our paper:

1. **Augmented baseline catalog.** Before declaring an LLM-discovered ansatz "novel", `novelty_audit` runs an automated literature pull (via `literature_surfacer`) for *current* published methods on the same Hamiltonian-and-active-space configuration, ingests them as additional rows in the Pareto archive, and re-runs the strict-domination comparator. The asymmetry argument: additions can only reduce LLM-novelty, never amplify it, so this is a one-sided test.
2. **Strict-domination with calibrated ε.** The comparator uses `(ε_abs, ε_rel) = (10⁻¹², 10⁻⁹)` for energy comparisons, calibrated to `float64` accumulation noise (UCCSD@zero-amplitudes recovering Hartree-Fock to ~1.7×10⁻¹¹ Ha in the reference path). Integer-valued comparisons (gate counts, CNOT counts) have ε=0.
3. **Recompute-derived-ratios-from-raw.** Any ratio claim in the paper draft (`X / Y = N×`) is automatically recomputed from the raw JSON values, not from the displayed rounded numbers. Catches the rounding-induced ratio drift that the example paper had in five places before this audit existed.
4. **Wilson 95 % CIs on small samples.** Every "K of N" rate in the manuscript (e.g., "5/5 cold starts hit chemical accuracy") is auto-annotated with a Wilson 95 % interval (`[0.48, 1.00]` in that case, which the author should consider before claiming 100 %).
5. **Cross-LLM falsifiable prediction rubric.** When a multi-LLM "consensus" is claimed, `novelty_audit` enforces (a) the LLMs must come from different vendors, (b) the prediction must be made before truth is computed, (c) the prediction must be a specific quantitative rubric (amplitude top-K, ordering), not free-form prose.
6. **Honest-negatives section.** If the audit surfaces a result that the framework would otherwise omit because it wasn't a win (e.g., "we tried H₂O at 8 qubits, the LLM produced HF-quality with zero correlation correction"), the framework requires the paper to include it in a `Failure Modes` section. The methodological contribution is the framework's discipline; the negatives are part of the data.

The combination of (1)–(6) is what we mean by "audit-and-falsify". It is not in ARC, not in ARS, not in any other research-agent harness I've found; it is the missing piece for any LLM-in-the-loop scientific-discovery system that wants to publish.

---

## All skills — the full catalog

Eighteen skills under `skills/`. Every one has its own `SKILL.md` with the
full contract; the table below is the at-a-glance summary so you can find
what you need without grepping.

| Skill | Modes | Required inputs | Outputs | When to use |
|---|---|---|---|---|
| **`novelty_audit`** | (single — the marquee skill) | `--pareto-archive PATH` `--draft PATH` (optional `--augmented-baselines PATH`, `--hamiltonian-id ID`) | `novelty_verdict.json`, `augmented_pareto.json`, `ratio_recompute.md`, `wilson_annotations.md`, `failure_modes_required.md`, `audit_claims.py` | Before declaring any LLM-discovered result novel. The audit-and-falsify framework end-to-end. |
| **`claims_registry`** | 2: registry / render-audit | `--paper PATH` (or `--source` + `--render`) | `registry.json`, `verification_report.{json,md}`, `paper_verification.json` | Deterministic numeric-claim gate: the "abstract says 98.3%, table says 87%" catcher. Zero LLM cost. |
| **`citation_integrity`** | (single, 4 layers) | `--paper .tex` `--bib .bib` (optional `--no-network`) | `verification_report.json` with `integrity_score` | Bibkey + completeness + CrossRef DOI + relevance check on every citation. No LLM, no RAG. |
| **`argument_structure`** | (single) | `--paper PATH` (optional `--journal SLUG`) | `argument_structure.{md,json}` | Premises → claims → conclusion map, claim–proof gap, Claim/Mechanism/Evidence balance, narrative debts, sequencing. |
| **`disclosure_audit`** | (single, 16-point checklist) | `--paper PATH` (optional `--journal SLUG`) | `disclosure_audit.md`, `disclosure_findings.json` | Funding / COI / author contributions / data + code availability / ethics / AI-use / rights, severity-grouped. |
| **`revision_planner`** | (single) | `--paper PATH` `--run-dir DIR` (a paper-audit outdir) | `anchored_revision_plan.md`, `_source_numbered.md` | Anchor every revision item to ¶NNN paragraph IDs + verbatim judge quotes + a concrete proposed edit. |
| **`deep_research`** | 7: `full` / `quick` / `systematic-review` / `socratic` / `fact-check` / `lit-review` / `review` | `--mode MODE` `--topic STR` (optional `--paper PATH` to ground in actual text) | mode-specific markdown + `_backend_used.json` | Surface literature, fact-check claims, draft the Related Work section, run a research-rigour assessment on a paper. |
| **`quantum_paper`** | 10: `full` / `plan` / `outline-only` / `revision` / `revision-coach` / `abstract-only` / `lit-review` / `format-convert` / `citation-check` / `disclosure` | `--mode MODE` plus `--topic` or `--draft` per mode | venue-formatted LaTeX or markdown | Author a quantum-computing paper, plan it, revise from reviewer comments, switch venues, write the disclosure block. |
| **`quantum_reviewer`** | 6: `full` (EIC + R1 + R2 + R3 + DA) / `quick` / `guided` / `methodology-focus` / `re-review` / `calibration` | `--mode MODE` `--draft PATH` (optional `--journal SLUG`) | `review_panel.md` (or quick / methodology variants) + verdict | Get a 5-voice reviewer panel on a paper — yours or someone else's. |
| **`logical_fallacies`** | (single) | `--draft PATH` (optional `--severity-threshold {low,medium,high,critical}`) | `fallacy_report.md`, `fallacy_findings.json` | Detect standard fallacies plus 11 quantum-CS-specific ones (cherry-picked-baseline, ad-hoc-precision-floor, simulator-laundering, mapping-by-convenience, pareto-cherry-picked-axes, cross-llm-theatre, …). |
| **`cross_llm_prediction`** | (single) | `--hamiltonian-id ID` `--geometry-sweep STR` `--llms LIST` (must be ≥2 different vendors) `--k N` | per-LLM predictions JSON + overlap-vs-truth table | Build a falsifiable amplitude-prediction rubric across two vendors with predictions persisted before truth. |
| **`pareto_explorer`** | built-in / `--evaluator-cmd` / `--plan-only` | `--hamiltonian ID` `--baseline LIST` (built-in registry: TFIM/Heisenberg 2-10q, H2_2q; or bring your own evaluator) | `archive.json` (strict-domination Pareto archive at calibrated ε) with REAL energies — bundled numpy statevector sim + SPSA | LLM-in-loop ansatz discovery with real numbers out of the box. |
| **`ablation_designer`** | (single, axis-specific) | `--axis NAME` from {`llm-mutator-onoff`, `commutation-hint-onoff`, `pareto-seeding-onoff`, `cross-vendor`} (optional `--results-file PATH`) | `ablation_plan.md`, `ablation_results.json`, `interpretation.md` | Design or interpret the four standard ablations that distinguish "the LLM was load-bearing" from "random would have worked". |
| **`literature_surfacer`** | (single) | `--topic STR` (optional `--n INT`, `--sources LIST`, `--hamiltonian-id`) | `synthesis.md`, `cards/`, `baseline_catalog.json` | Pull literature live from CrossRef + arXiv + Semantic Scholar (+ Serper Google Scholar if `SERPER_KEY`) and emit the Pareto-shaped baseline catalog `novelty_audit` consumes. |
| **`book_acquirer`** | (single) | `--queries-file PATH` or `--queries "q1;q2"` `--target-dir DIR` | downloaded PDFs in `target-dir`, `acquire_report.json` | Download books/theses from Anna's Archive that aren't on arXiv (requires `ANNAS_ARCHIVE_KEY`). |
| **`process_summary`** | (single, optional `--no-llm-narrative`) | `--run-dir PATH` | `cqe_scores.json` (per-dim + geometric-mean composite), `process_summary.md` | Stage 6 — mechanically score a completed run on the 6-dim Collaboration Quality Evaluation. |
| **`chat`** | (single) | `--prompt STR` (optional `--paper`, `--journal`, `--quantum-lib`, `--execute`) | `dispatch_decision.json`, `dispatch.md`, plus the dispatched skill's output if `--execute` | Natural-language frontend. `"Review this paper"` → quantum_reviewer / `"Write a paper on X"` → quantum_paper / `"status"` → pipeline status. |
| **`audit_falsify`** | (library skill) | imported from `skills/audit_falsify/audit_falsify.py` | strict-domination primitives, Wilson CI, ratio-recompute scanner | Compose your own audit pipeline using the same primitives `novelty_audit` uses. |
| **journals + quantum_libs** | (registries, not skills) | `python -m skills.common.journals list` / `quantum_libs list` | per-venue policy + per-library code skeleton | Pass `--journal SLUG` / `--quantum-lib SLUG` to any other skill; it'll adapt. |

For every skill: full surface in `skills/<name>/SKILL.md`, prompt
templates in `skills/<name>/prompts/` (when applicable), Python driver
in `skills/<name>/skill.py`, bash entry in `skills/<name>/run.sh`. The
chain auto-discovers skills via filesystem walk; drop a new one in and
`chain/run.sh --list-skills` finds it.

---

## The chain — workflow options

The skill catalog above is composed into **named pipelines** by `chain/run.sh`, each with per-stage `--skip-X` / `--with-X` toggles.

List the pipelines and their stages:

```
$ bash chain/run.sh --list-stages
# QN chain — stage table

pipeline                  default-on stages                                             optional
--------------------------------------------------------------------------------------------------------------
paper-audit               research, reviewer, fallacies, cqe                            novelty-audit, cross-llm
full                      literature, discovery, audit, draft, cross-llm, review, ...   -
mid-entry-stage-2.5       literature-1.5, audit, review, fallacies, cqe                 -
mid-entry-stage-4         revision, re-review, cqe                                      -

Toggle defaults via per-stage flags:
  --skip-<stage>     turn off a default-on stage
  --with-<stage>     turn on an opt-in stage
  --pause-after S    write checkpoint after stage S
  --resume-from S    treat earlier stages as complete
  --force            re-run completed stages
```

**Audit an existing paper** (the flagship `examples/end_to_end/two_paper_novelty` demo runs exactly this):

```
bash chain/run.sh \
  --pipeline paper-audit \
  --llm codex \
  --paper /path/to/paper.txt \
  --journal npj-quantum-information \
  --topic "Generative flow-based warm start of the VQE" \
  --outdir runs/my_audit
```

This runs the four default-on stages in order:

| Stage      | Skill                  | What it produces                                         |
| ---------- | ---------------------- | -------------------------------------------------------- |
| research   | `deep_research --mode review` | `research_quality_review.md` — audit-and-falsify checklist scored against the paper text |
| reviewer   | `quantum_reviewer --mode full` | `review_panel.md` — 5-voice panel (EIC + R1/R2/R3 + Devil's Advocate) + vote table |
| claims-registry | `claims_registry` | `verification_report.{json,md}` — deterministic numeric-claim gate (Results vs Abstract/Intro/Discussion); zero LLM cost |
| fallacies  | `logical_fallacies`    | `fallacy_report.md` + `fallacy_findings.json` — 11 quantum-CS-specific + standard taxonomy |
| cqe        | `process_summary`      | `cqe_scores.json` + `process_summary.md` — 6-dim Stage-6 composite |

Each stage is **idempotent** — re-running with the same `--outdir` skips completed stages unless `--force` is passed. The resolved configuration (which stages ran, which `--skip-X` / `--with-X` flags were honored, decision log) is written to `_chain_config.json` in the outdir and surfaced in the final PIPELINE_REPORT.pdf.

**Drop or add stages:**

```
# audit-only — drop the 5-voice panel and the CQE pass:
bash chain/run.sh --pipeline paper-audit --skip-reviewer --skip-cqe ...

# add cross-LLM falsifiability prediction (needs --hamiltonian, --geometry-sweep, --llms):
bash chain/run.sh --pipeline paper-audit \
  --with-cross-llm --hamiltonian H2 \
  --geometry-sweep "R_HH=0.7,0.9,1.1,1.3,1.5 A" \
  --llms claude,codex ...

# add novelty-audit (needs a Pareto archive from a prior pareto-discover run):
bash chain/run.sh --pipeline paper-audit \
  --with-novelty-audit --pareto-archive runs/.../archive.json ...

# the deterministic numeric-claim registry gate is DEFAULT-ON (zero LLM
# tokens; drop with --skip-claims-registry). Passing --bib arms the
# 4-layer citation-integrity gate automatically (CrossRef over HTTP —
# no LLM, no RAG; drop with --skip-citation-integrity):
bash chain/run.sh --pipeline paper-audit --bib refs.bib ...

# add the rest of the verification layer — argument-architecture audit,
# disclosure checklist, and a paragraph-anchored revision plan:
bash chain/run.sh --pipeline paper-audit \
  --with-argument-structure --with-disclosure-audit \
  --with-revision-planner ...

# checkpoint + resume:
bash chain/run.sh --pipeline paper-audit --pause-after reviewer ...
# ...inspect outputs, then continue:
bash chain/run.sh --pipeline paper-audit --resume-from fallacies ...
```

**Other pipelines** (`full`, `mid-entry-stage-2.5`, `mid-entry-stage-4`) follow the same toggle pattern. See `chain/pipelines.py` for the canonical stage definitions and `examples/end_to_end/two_paper_novelty/run_two_papers.sh` for a complete end-to-end harness.

### Telemetry — ARC's stage-health pattern

The chain runner implements AutoResearchClaw's structured-telemetry pattern (stage_health / pipeline_summary / decision_history / checkpoint):

- **`chain/common/heartbeat.sh`** — `start_heartbeat` / `stop_heartbeat` / `run_with_heartbeat <stage_dir> <timeout_sec> <cmd...>` / `audit_heartbeats <run_dir>`. Detects silent hangs and kills the chain itself didn't notice (ARC's sentinel pattern).
- **`chain/common/stage_telemetry.sh`** — `stage_health_begin` / `stage_health_end` / `decision_log` / `checkpoint_write` / `pause_after_stage` / `pipeline_summary`.
- **`chain/common/telemetry.py`** — Python port of the same six helpers so `chain/pipelines.py` produces identical JSON when it orchestrates stages from Python.

Every paper-audit run now writes (alongside the per-stage outputs):

| File                              | Schema source                                                              | Purpose                                                                                       |
| --------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `<stage>/_stage_health.json`      | `chain/common/stage_telemetry.sh`                                                    | `stage_id`, `status`, `duration_sec`, `artifacts_count`, `started_iso`, `ended_iso`, `error`  |
| `pipeline_summary.json`           | `stage_telemetry.sh::pipeline_summary`                                                      | Aggregated `stages_executed/done/paused/blocked/failed`, `final_status`, `content_metrics`    |
| `decision_history.json`           | `stage_telemetry.sh::decision_log`                                                          | Append-only log: `proceed` / `refine` / `pivot` / `pause` / `block` / `fail`                  |
| `HEARTBEAT_AUDIT.md`              | `heartbeat.sh::audit_heartbeats`                                                      | Per-stage `OK` / `TIMED_OUT` / `HUNG_OR_KILLED` / `RUNNING` / `UNTRACKED`                     |
| `checkpoint.json`                 | `stage_telemetry.sh::checkpoint_write`                                                      | Resumable pause marker; written when `--hitl-pause-after STAGE` (or `QN_HITL_PAUSE_AFTER` env) matches |
| `_chain_config.json`              | QN-native                                                                  | Resolved chain configuration: pipeline preset, llm, default-on/opt-in stages, decision-log    |
| `_run_summary.json`               | QN-native                                                                  | Subprocess-RC view: per-stage exit codes, elapsed-s, skip status                              |

### ARC profile bundles + cross-model fork

The ARC-profile flag surface:

```
--with-cross-model        Fork the chain on claude + codex (claude_branch/ +
                          codex_branch/), write _cross_model_index.json
                          pointing at both.

--with-codex-fallback     Re-enable the legacy silent claude->codex fallback.
                          Off by default; framework default is strict.

# Strict-env defaults (set at module load; override only when really needed):
#   CLAUDE_DISABLE_CODEX_FALLBACK=1     no silent fallback inside claude CLI
#   INVOKE_LLM_NO_FALLBACK=1            no invoke_llm fallback
#   QN_DISABLE_BACKEND_FALLBACK=1       no QN-level fallback

# ARC profile flags (bundle via --with-arc-pipeline):
--with-arc-pipeline                   bundle all ARC stages
--with-arc-problem-tree               pre-gen: goal.md + problem_tree.md
--with-arc-literature-pipeline        pre-gen: CrossRef + paper cards
--with-arc-paper-outline              pre-gen: structured outline
--with-arc-novelty-check              pre-gen: novelty vs corpus
--with-arc-draft-quality              post-gen: word-count + status flags
--with-arc-iterative-refine           post-gen: refinement sandbox
--with-arc-citation-integrity         post-gen: 4-layer cite verification
--with-arc-compilation-quality        post-gen: LaTeX log analysis
--with-arc-paper-verification         post-gen: numeric fabrication audit
--with-arc-pdf-review                 post-gen: 9-axis NeurIPS PDF scorecard
--with-arc-quality-gate               post-gen: consolidated quality_report
--with-arc-research-decision          post-gen: PROCEED/REFINE/PIVOT
--with-arc-knowledge-archive          post-gen: deliverables bundle
```

The ARC flags currently surface the option-table for parity; the stages they bind to are being ported into QN one-by-one as their inputs become applicable to the quantum-computing pipeline (the QN-applicable subset starts with `novelty-audit`, `cross-llm`, `process-summary` — the ones already shipping in `paper-audit`).

---

## Backends — Claude Code CLI is the default, with options

QuantumNovelty does **not** call the Anthropic API. The default LLM backend is the **Claude Code CLI** (`claude --print`), running under your user's existing Claude Code subscription. This is a deliberate choice: it makes the framework usable without provisioning an API key, it routes through subscription billing (not metered API), and it inherits any tools you've configured for your Claude Code session.

All four supported backends share the same Python interface (`skills/common/llm.py::call_llm(prompt, backend, ...)`). You pick which one with `--llm`:

| Backend | Invocation | When to use |
|---|---|---|
| `claude` (default) | subprocess: `claude --print --dangerously-skip-permissions --no-session-persistence` with a scrubbed env (`CLAUDE_CODE_*`, `ANTHROPIC_*`, `CLAUDECODE` removed) and a neutral cwd | Default for everything. Honors your Claude Code subscription. |
| `codex` | subprocess: `codex exec --skip-git-repo-check -` reading prompt from stdin | When you want a different vendor for cross-LLM falsifiability checks. The `cross_llm_prediction` skill uses this in its codex arm. |
| `codex-acp` | [Agent Client Protocol](https://github.com/zed-industries/agent-client-protocol) via `acpx` — a single persistent codex session across multiple skill invocations. The session carries context built up by earlier stages. | Long pipelines where you want the LLM to remember context across stages without re-stuffing prompts. |
| `codex-mcp` | Codex as an MCP (Model Context Protocol) server. QuantumNovelty exposes its skills as MCP tools, codex consumes them. | When you want the human to drive an interactive review session from Codex while QuantumNovelty serves the skill catalog. |

All four enforce the **nested-CLI isolation playbook** (scrubbed env including `ANTHROPIC_*` so the subscription path is used; neutral cwd to avoid the "tool_use ids must be unique" 400 from nested Claude Code sessions; `--no-session-persistence` to avoid session-state collisions). This is non-optional — every backend goes through the same isolation wrapper.

### Claude Code CLI integration (the default — no API key needed)

QuantumNovelty's default backend is the `claude` binary from your local
Claude Code installation. Every skill that needs an LLM ultimately
reaches `skills/common/llm.py::_call_claude_cli`, which runs:

```text
claude --print
       --output-format json
       --dangerously-skip-permissions
       --no-session-persistence
```

Why each flag matters:

| Flag | Why |
|---|---|
| `--print` | Headless one-shot; no TUI, no interactive prompts |
| `--output-format json` | Returns a structured JSON envelope including `result` (the text), `usage.input_tokens`, `usage.output_tokens`, `usage.cache_*`, `total_cost_usd`, `modelUsage[<snapshot-id>]`. This is what feeds the per-call cost ledger. |
| `--dangerously-skip-permissions` | Needed for nested-CLI calls — without it, sub-tools (WebSearch, WebFetch) prompt for permission and a non-interactive call returns "I don't have permission to do that" |
| `--no-session-persistence` | Avoids session-id collisions with the parent Claude Code session you may be running from |

Around that command, `_call_claude_cli` enforces the **nested-CLI
isolation playbook** every single time:

1. Strip `CLAUDE_CODE_*`, `ANTHROPIC_*`, and `CLAUDECODE` from the
   subprocess env. If `ANTHROPIC_API_KEY` survives into the subprocess,
   Claude Code uses the API path (metered) instead of the subscription;
   if `CLAUDE_CODE_*` survive, the nested call 400s on
   `"tool_use ids must be unique"`.
2. Run the subprocess with `cwd=tempfile.gettempdir()` so a stale
   `.claude` directory in the calling location can't trigger the same
   400.
3. Parse the JSON envelope into an `LLMResult` carrying `model_id`
   (e.g. `claude-opus-4-5-20251101`), `input_tokens`, `output_tokens`,
   `cache_read_input_tokens`, `cache_creation_input_tokens`,
   `total_cost_usd`, `elapsed_s`. Falls back to char/4 estimates only
   if the envelope can't be parsed; in that case
   `tokens_estimated=true` is set so the cost ledger flags it.
4. Refuse to silently fall back to a different backend on failure —
   raises `RuntimeError`, which skills convert to a `⚠ FAILED` stub
   output + exit 3, leaving the user to decide whether to retry or
   swap to codex.

What you actually do as a user:

```bash
# Verify the CLI is reachable
which claude              # /usr/local/bin/claude  (or similar)
claude --version

# Run anything that calls an LLM — the default backend is claude
chain/run.sh --pipeline chat --prompt "Review this paper" --paper p.pdf

# Every per-stage _backend_used.json shows what actually ran:
cat runs/<ts>/claude/<pipeline>/<stage>/_backend_used.json
# { "backend_requested": "claude", "backend_actually_used": "claude",
#   "model_id": "claude-opus-4-5-20251101", "elapsed_s": 24.3,
#   "usage": { "input_tokens": 30097, "output_tokens": 3762,
#              "total_cost_usd": 0.0184, "tokens_estimated": false } }
```

No API key. No HTTP. Every call goes through your Claude Code
subscription, billed flat.

### Codex CLI integration (for cross-LLM falsifiability — or as fallback)

When the framework needs a second vendor (the `cross_llm_prediction`
skill enforces it; the codex branch of `cross-model` runs a parallel
pipeline) or when claude is unreachable, the codex backend takes over.
`_call_codex_cli` runs:

```text
codex exec --skip-git-repo-check -
```

with the prompt on stdin, the same scrubbed env (`ANTHROPIC_*` stripped
too — paranoid; codex doesn't read those but a stray env leak could
still confuse a deeper subprocess), and the same neutral cwd.

Codex's CLI does not surface token usage in its plain output, so the
resulting `LLMResult` carries char/4 estimates flagged with
`tokens_estimated: true` and `total_cost_usd: null`. Honest accounting —
the cost ledger in the two-paper-novelty PDF marks these rows with a
`†` and prints `(estimated)` in the cost column.

What you actually do:

```bash
which codex               # /opt/homebrew/bin/codex  (or similar)
codex --version

# Use codex anywhere claude could be used:
chain/run.sh --pipeline chat --prompt "Review this paper" \
             --paper p.pdf --llm codex

# Mandatory codex for cross-LLM falsifiability:
chain/run.sh --pipeline cross-llm \
             --hamiltonian H2O_4e_4o_8q \
             --geometry-sweep "R_OH=0.7,0.96,1.5,2.0 A" \
             --llms "claude,codex"        # framework REFUSES if both same vendor
```

The framework's vendor-detection logic (in
`skills/common/llm.py::_vendor_of` plus
`skills/cross_llm_prediction/skill.py::_validate_distinct_vendors`)
maps `claude*` → `anthropic`, `codex*`/`gpt*` → `openai-codex`,
`gemini*` → `google`. Pass two `claude` snapshots to `--llms` and the
cross-llm skill exits 2 with `cross-LLM falsifiability requires AT
LEAST 2 distinct vendors`. That's the cross-llm-theatre guard.

### Agent Client Protocol (codex-acp) and MCP

Two further backends are wired but rarely used by the default
workflows:

- **`codex-acp`** — codex through the [Agent Client
  Protocol](https://github.com/zed-industries/agent-client-protocol)
  via `acpx`. A single persistent session across multiple skill calls,
  so the agent remembers context built up by earlier stages. Useful
  for long pipelines where you'd otherwise re-stuff context every call.
- **`codex-mcp`** — codex as an MCP client, with QN's skill catalog
  exposed as MCP tools. Useful for interactive sessions where a human
  is driving codex but wants the QN skills available as callable tools.

Both are documented in `skills/common/llm.py` and selectable via
`--llm codex-acp` / `--llm codex-mcp`.

### Why not the Anthropic API?

Two reasons:

1. **Cost predictability.** A full chain run can do 100+ LLM calls. On the API, that's billable per token; on the Claude Code subscription, it's flat. A graduate student running QuantumNovelty against a sweep of 40 Hamiltonian configurations cannot afford the API path.
2. **Tool access.** Claude Code has `WebSearch`, `WebFetch`, file editing, and bash access that the API doesn't expose unless you reimplement each as a tool definition. Skills like `literature_surfacer` lean on `WebFetch` directly.

If you specifically need the API (e.g., for a CI run where Claude Code isn't installed), `skills/common/llm.py` has a `--llm anthropic-api` mode that requires you to set `ANTHROPIC_API_KEY` explicitly and emits a warning. The default refuses to pick it up.

---

## What's NOT here

Explicit non-features:

- **No RAG.** QuantumNovelty does not run a vector database, does not embed documents, does not maintain a knowledge base. Literature is surfaced fresh per query through CrossRef/arXiv/Semantic Scholar, and book content (when needed) is downloaded via Anna's Archive and OCR'd inline. If you want RAG, build it as a sibling project; QuantumNovelty refuses to take on the indexing-maintenance complexity. (This is a deliberate departure from upstream ARC, which has a RAG layer.)
- **No dependency on any private codebase.** QuantumNovelty is a *peer of ARC* — a framework. The Apple-Silicon simulator and the in-development paper that motivated QN live in a separate repository that will be released once the paper is published; QN does not depend on either.
- **No LaTeX template provided.** The example paper uses `revtex4-2`; you can use whatever template your venue requires. The framework only cares about the audit pipeline, not the typesetting.
- **No GUI.** All workflows are CLI-driven. The chain produces structured JSON + markdown reports; consume them however you like.

## What QuantumNovelty adds on top of ARC + ARS

QN is a peer of [AutoResearchClaw (ARC)](https://github.com/) and
[academic-research-skills (ARS)](https://github.com/imbad0202/academic-research-skills).
The upstreams contributed real foundations; we cherry-picked them and added a
quantum-specific spine. The concrete differences are below — every one is
backed by code in this repo and a worked example under `examples/`.

### Bottom line — QN vs ARS vs ARC for quantum papers

All three were run head-to-head on the same PRX Quantum paper
(LCU-Trotter, arXiv:2212.04566) with the same backend; the measured rows
below come from that run. Full evidence:
`examples/end_to_end/compare_qn_vs_ars_vs_arc/_run/COMPARE_REPORT.pdf`.

| | **QN** (QuantumNovelty) | **ARS** (academic-research-skills) | **ARC** (AutoResearchClaw) |
|---|---|---|---|
| **Review steps** | 4 default stages (+3 opt-in: novelty-audit, cross-llm, synthesizer → up to 7) | 7 agents in 3 phases | 2 review stages (of a 23-stage generative pipeline) |
| **Reviewer "agents"** | 5 voices in **one** LLM call (EIC + Physics + Novelty + Evidence + Devil's Advocate) | 7 **independent** LLM calls (field-analyst, EIC, methodology, domain, perspective, Devil's Advocate, synthesizer) | 1 call simulating Reviewer A + B |
| **Logical fallacies** | ✅ **dedicated stage** — only one with a domain taxonomy: 11 quantum-CS fallacies (simulator-laundering, cherry-picked-baseline, cross-llm-theatre, …) + standard | partial — folded into Devil's Advocate + methodology reviewer | ❌ (fabrication / evidence-consistency check instead) |
| **Devil's Advocate** | ✅ Voice 4 of the panel | ✅ dedicated agent | ❌ |
| **Numeric quality gate** | ✅ deterministic `_quality_gate.json` (ARC's shape, zero LLM cost) | ❌ | ✅ the original (`score_1_to_10` + threshold) |
| **Editorial decision package** | ✅ opt-in `--with-synthesizer` (+ CONSENSUS-0 tags for fallacy-only findings) | ✅ Phase-2 synthesizer (consensus tags, roadmap, response template) | partial (`required_actions` list) |
| **Measured cost (same paper)** | 4 calls, **$2.15 real USD** | 7 calls, **$3.10 real USD** | 2 calls, **$0.66 real USD** |
| **Quantum-specific?** | ✅ **the only one** | ❌ general academic | ❌ general (ML-leaning) |

What each rival still does better: **ARS** gives every reviewer ~1,000
independent words vs QN's ~340/voice in one call — blind independence at
7× the calls. **ARC** is the cheapest sanity check (2 calls, $0.66) and
has deterministic anti-fabrication gates against actual experiment
artifacts. All numbers above are from a single all-claude run (Claude
Code CLI, exact per-call USD). On LCU-Trotter the three architectures
landed in the same revisions band: QN gate 6.0/10 (major revisions),
ARC gate 7/10 (accept with minor revisions), ARS editorial decision
(Minor Revision) — QN's quantum-CS-specific checks make it the
strictest of the three.

### 1. Quantum-specific audit-and-falsify pipeline

`skills/novelty_audit/` enforces a six-step discipline that targets failure
modes characteristic of quantum-computing manuscripts:

- **Augmented baseline catalog**: literature is pulled fresh per run and merged
  into the comparator so a "novel" result is compared against current
  published methods, not a cherry-picked subset
- **Strict-domination with calibrated ε**: `ε_abs=10⁻¹²`, `ε_rel=10⁻⁹`,
  calibrated to `float64` accumulation noise (~1.7×10⁻¹¹ Ha empirical floor),
  so domination claims survive even on noisy simulator backends
- **Recompute-derived-ratios-from-raw**: every `X / Y = N×` claim in the
  draft is recomputed from on-disk JSON; rounding-induced drift becomes
  impossible to hide
- **Wilson 95 % CIs on small samples**: every "K / N" rate gets a binomial
  interval; "5/5" with CI lower bound 0.57 is no longer treated as 100 %
- **Honest-negatives enforcement**: if the augmented baselines include rows
  the LLM did not dominate, the manuscript MUST add a `Failure Modes`
  section listing them, or the skill exits rc=2
- **Re-runnable claim audit**: a `audit_claims.py` is emitted that derives
  every numerical claim from on-disk JSON; drop it into your `paper/` dir,
  run before every commit

This combination is the marquee contribution. ARC has a venue-agnostic gate
stack; QN has a quantum-shaped one.

### 2. Quantum-CS-specific logical fallacy taxonomy

`skills/logical_fallacies/` extends the standard fallacy list with 11
fallacies that appear specifically in quantum-computing papers. None of them
are in upstream's taxonomy:

| Fallacy | What it catches |
|---|---|
| `cherry-picked-baseline` | comparing vs a weak baseline while ignoring stronger published methods on the same Hamiltonian |
| `ad-hoc-precision-floor` | quoting energy diff at sub-noise precision |
| `conflated-regimes` | extrapolating from small Hamiltonians to large without scaling argument |
| `active-space-handwave` | claiming generalisation without running the larger case |
| `hardware-irrelevant-comparison` | simulator results compared against hardware results without noise calibration |
| `asymptotic-only-claim` | N→∞ claim with finite-N demonstration |
| `unit-inflation` | choosing units to inflate apparent magnitude (cm⁻¹ vs Ha) |
| `simulator-laundering` | discover on lib A, evaluate on lib B, conflate |
| `mapping-by-convenience` | JW/BK/parity chosen for cosmetics, not science |
| `pareto-cherry-picked-axes` | domination claimed on a chosen axis subset |
| `cross-llm-theatre` | same-vendor snapshots dressed up as multi-model consensus |

These were extracted from real reviewer concerns raised against the framework's motivating study (paper in development)
and are detected in the real two-paper demo (Flow-VQE caught 8 medium+
findings).

### 3. Tested on real published papers

The flagship showcase is `examples/paper_reviews/` — the `paper-audit`
chain run end-to-end (Claude Code CLI backend, exact tokens + USD per
stage) on **five real papers: four peer-reviewed across all three target
venues (including two on quantum machine learning) plus one high-profile
hardware preprint**, with the combined
[`REVIEWS.pdf`](examples/paper_reviews/REVIEWS.pdf) and every stage's
raw output included:

- **LCU-Trotter** — Pei Zeng, Jinzhao Sun, Liang Jiang, Qi Zhao,
  *Simple and high-precision Hamiltonian simulation by compensating
  Trotter error with linear combination of unitary operations*,
  **PRX Quantum** 6, 010359 (2025),
  [arXiv:2212.04566](https://arxiv.org/abs/2212.04566)
- **Flow-VQE** — Hang Zou, Martin Rahm, Anton Frisk Kockum, Simon
  Olsson, *Generative flow-based warm start of the variational quantum
  eigensolver*, **npj Quantum Information** (2025),
  [arXiv:2507.01726](https://arxiv.org/abs/2507.01726)
- **HW-QML** — Léo Monbroussou, Eliott Z. Mamon, Jonas Landman,
  Alex B. Grilo, Romain Kukla, Elham Kashefi, *Trainability and
  Expressivity of Hamming-Weight Preserving Quantum Circuits for
  Machine Learning*, **Quantum** 9, 1745 (2025),
  [arXiv:2309.15547](https://arxiv.org/abs/2309.15547) — the
  quantum-machine-learning entry
- **QCNN** — Pablo Bermejo, Paolo Braccia, Manuel S. Rudolph,
  Zoë Holmes, Lukasz Cincio, M. Cerezo, *Quantum Convolutional Neural
  Networks are Effectively Classically Simulable*, **PRX Quantum** 7,
  020304 (2026), [arXiv:2408.12739](https://arxiv.org/abs/2408.12739)
  — the QML-dequantization entry
- **Majorana tetron** — Microsoft Quantum, *20 Second Parity Lifetime
  in an InAs–Pb Tetron Device*, preprint,
  [arXiv:2606.03884](https://arxiv.org/abs/2606.03884) — the hardware
  entry: the first non-gate-model paper through the pipeline
  (topological qubits, parity-lifetime claims), audited against the
  PRX Quantum rubric while still a preprint

> **Disclaimer.** The reviews in `examples/paper_reviews/` are generated
> end-to-end by AI and are provided strictly for academic and
> demonstration purposes. We make **no claims about the correctness,
> quality, novelty, or publication-worthiness of the papers under
> review** — four of them passed real peer review at their respective
> journals (the fifth is a public arXiv preprint), and nothing in this
> repository should be read as criticism
> of the authors or as a substitute for human peer review. Paper
> copyrights remain with their authors and publishers.

The earlier `examples/end_to_end/two_paper_novelty/` demo (Flow-VQE +
LCU-Trotter with the chain-runner harness and telemetry walkthrough)
remains as the reproducible-pipeline example.

Plus three scaffolded papers (`examples/end_to_end/avenue_*`) across three
journals (PRX Quantum / npj-QI / Quantum) and three libraries (Qiskit /
PennyLane / QuTiP).

Real CQE scores in the repo (geometric-mean composites): the three
scaffolded avenues 28/100 each (correctly low because they have
no real experiments). The framework grades scaffolded
drafts honestly, not flatteringly.

### 4. Used to generate new quantum papers, not just review them

`skills/quantum_paper/` has 10 modes: `full` / `plan` / `outline-only` /
`revision` / `revision-coach` / `abstract-only` / `lit-review` /
`format-convert` / `citation-check` / `disclosure`. The output is venue-
shaped LaTeX that compiles. We've used it to produce four drafts in this
repo (three scaffolded avenues + revisions of the in-development
motivating paper), and the
generated PDFs are in `examples/end_to_end/avenue_*/stage_4_draft/`.

### 5. Venue + library registries

Two registries in `skills/common/`:

- `journals.py` — 11 quantum-computing venues with abstract limits,
  section orderings, citation styles, required statements: Quantum,
  npj Quantum Information, PRX Quantum, PRL, PRA, PR Applied,
  Nature Communications, Communications Physics, QST, Physics Letters A,
  IEEE Transactions on Quantum Engineering
- `quantum_libs.py` — 7 libraries with canonical imports + ansatz
  skeletons + evaluator patterns: Qiskit, PennyLane, QuTiP, mlxq, Cirq,
  OpenFermion, no-code

Pass `--journal SLUG` and `--quantum-lib SLUG` to any skill; the
generated paper, disclosure block, code snippets, and reviewer rubric all
adapt automatically.

### 6. Token + USD cost ledger in every report

Every LLM call writes `_backend_used.json` containing:

```json
{
  "backend_requested":     "claude",
  "backend_actually_used": "claude",
  "model_id":              "claude-opus-4-5-20251101",
  "elapsed_s":             24.253,
  "exit_code":             0,
  "usage": {
    "input_tokens":              348,
    "output_tokens":             1224,
    "cache_read_input_tokens":   0,
    "cache_creation_input_tokens": 26157,
    "tokens_estimated":          false,
    "total_cost_usd":            0.0184
  }
}
```

Claude calls go through `claude --print --output-format json` so token
counts and USD cost come from the CLI directly. Codex / other backends
that don't surface usage stats use char/4 estimates flagged with
`"tokens_estimated": true`. The two-paper-novelty PDF aggregates the
ledger per paper + per stage + grand total.

### 7. Nested-CLI isolation playbook

`skills/common/llm.py::_scrubbed_env` strips `CLAUDE_CODE_*`,
`ANTHROPIC_*`, and `CLAUDECODE` from every subprocess; the wrapper runs
from `tempfile.gettempdir()`; claude calls pass `--no-session-persistence`.
This defends against the `"tool_use ids must be unique"` 400 that bites
nested `claude --print` calls.

When isolation isn't enough (a session that's already accumulated state),
the framework **refuses to silently swap backends** — it raises
`RuntimeError`, writes a stub output with a `⚠ FAILED` banner, and lets
the user decide whether to retry, switch to `--llm codex`, or address the
underlying state. The cross-vendor design earns its complexity in
`examples/end_to_end/avenue_03_qaoa/` and the two-paper demo, both of
which depend on the codex fallback to produce a clean draft.

### 8. Stage-6 6-dim Collaboration Quality Evaluation

`skills/process_summary/` mechanically scores a run-dir on six dimensions
(Novelty Rigour / Reproducibility / Methodological Rigour / Falsifiability
/ Domain Depth / Communication) and composites them via **geometric
mean**, not arithmetic. A 99 on five dimensions and 30 on Falsifiability
composites at 67/100, not 84/100 — the publication-blocking weakness
cannot be averaged away. The composite method is documented in
`skills/process_summary/SKILL.md` as not user-configurable.

---

## Relationship to other projects

| | What it is | Relationship to QN |
|---|---|---|
| **AutoResearchClaw (ARC)** | upstream research-agent framework with gate-stack pipeline + RAG | **peer** — QN cherry-picks ARC's gate-stack pattern, omits the RAG layer |
| **academic-research-skills (ARS)** | upstream modular skill catalog | **peer** — QN cherry-picks ARS's skill-as-folder pattern, adds the audit-and-falsify layer |
| **DSS** | the user's umbrella research tree | **filesystem parent only** — QN sits under `DSS/artifacts/code/QuantumNovelty/` for convenient backup; has no DSS-specific code |
| **[osxQ](https://github.com/BoltzmannEntropy/osxQ)** | Apple Silicon quantum simulation stack + QuantumStudio UI | sister project — a natural simulator backend for QN-discovered circuits |

Any quantum-computing paper can be the **target** of QN's analysis pipeline.
The in-development motivating paper was the first target; the two-paper analysis at
`examples/end_to_end/two_paper_novelty/` analyses Flow-VQE (arXiv:2507.01726,
*npj Quantum Information*) and LCU-Trotter (arXiv:2212.04566, *PRX Quantum*)
end-to-end with a full token + cost ledger in the resulting PDF.
## Token + cost ledger

Every LLM call's `_backend_used.json` records:

```json
{
  "backend_requested": "claude",
  "backend_actually_used": "claude",
  "model_id": "claude-opus-4-5-20251101",
  "elapsed_s": 24.253,
  "exit_code": 0,
  "usage": {
    "input_tokens": 12,
    "output_tokens": 348,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 26157,
    "tokens_estimated": false,
    "total_cost_usd": 0.0114
  }
}
```

Claude calls go through `--print --output-format json` so token counts and
USD cost come from the CLI directly (no estimation). Codex / other backends
that don't surface usage stats use char/4 estimates flagged with
`"tokens_estimated": true`. Cost is rolled up per stage and per paper in the
two-paper-demo PDF report.

---

## Installation

```bash
git clone <wherever-you-put-it> QuantumNovelty
cd QuantumNovelty
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Verify backend is reachable
which claude    # Claude Code CLI — required for default backend
which codex     # Codex CLI — optional, for cross-LLM
which acpx      # Agent Client Protocol — optional, for codex-acp backend
```

Required system tools:
- `claude` (Claude Code CLI; default LLM backend)
- `python` ≥ 3.11
- `pandoc` (for any `--format docx` outputs)
- `pdflatex` (for compilation-quality gate on `.tex` papers)
- `pdftotext` or `pymupdf` (for PDF ingest in literature stages)

Optional:
- `codex` (Codex CLI; cross-LLM backend)
- `acpx` (ACP shim; for `--llm codex-acp`)
- Anna's Archive API key in `ANNAS_ARCHIVE_KEY` env (for `book_acquirer`)

---

## Quick start — natural-language

The `chat` skill maps free-text into the right pipeline + skill + mode. Every
example below is a real invocation you can run:

```bash
# Full pipeline from a topic
chain/run.sh --pipeline chat --prompt \
  "I want to write a complete research paper on AI-guided VQE ansatz discovery"

# Socratic guidance to formulate the research question
chain/run.sh --pipeline chat --prompt \
  "Guide my research on noise-model-aware VQE optimisation"

# Plan a paper through the contribution ladder
chain/run.sh --pipeline chat --prompt \
  "Guide me through writing a paper on Trotter-error scaling"

# Review an existing paper (5-voice panel: EIC + R1 + R2 + R3 + Devil's Advocate)
chain/run.sh --pipeline chat --prompt "Review this paper" \
  --paper paper.tex --journal npj-quantum-information

# Pipeline status check
chain/run.sh --pipeline chat --prompt "status"
```

### Individual skills — by trigger phrase

**Deep Research** (7 modes)
```
"Research the impact of LLM evolution on small-molecule VQE"     → full
"Quick brief on shadow tomography sample complexity"             → quick
"Systematic review on Pareto methods in quantum compilation"     → systematic-review
"Guide my research on noise-model-aware VQE"                     → socratic
"Fact-check these claims" --paper claims.md                      → fact-check
"Literature review on ADAPT-VQE methods"                         → lit-review
"Review this paper's research quality" --paper paper.tex         → review
```

**Quantum Paper** (10 modes)
```
"Write a paper on LLM-guided ansatz discovery"                   → full
"Guide me through writing a paper on energy minimisation"        → plan
"Build a paper outline on Trotter error"                         → outline-only
"I have a draft and reviewer comments" --paper draft.tex
   --reviewer-comments comments.md                               → revision
"Parse these reviewer comments into a roadmap"                   → revision-coach
"Write an abstract for this paper" --paper draft.tex             → abstract-only
"Turn this into a literature review paper"                       → lit-review
"Convert this paper to prx-quantum format" --paper draft.tex     → format-convert
"Check the citations in this paper" --paper draft.tex            → citation-check
"Generate disclosure block" --paper draft.tex
   --journal npj-quantum-information                             → disclosure
```

**Quantum Reviewer** (6 modes — EIC + R1/R2/R3 + Devil's Advocate)
```
"Review this paper" --paper paper.tex                            → full
"Quick assessment of this paper" --paper paper.tex               → quick
"Guide me to improve this paper" --paper paper.tex               → guided
"Check the methodology" --paper paper.tex                        → methodology-focus
"Verify the revisions" --paper paper.tex
   --prior-comments r1.md                                        → re-review
"Calibrate this reviewer against my gold set" --paper paper.tex
   --gold-set golds/                                             → calibration
```

**Pipeline orchestrator (Stages 1 → 6)**
```
"I want to write a complete research paper"                      → full pipeline
"I already have a paper, review it" --paper paper.tex            → mid-entry at Stage 2.5
"I received reviewer comments" --paper paper.tex
   --reviewer-comments r1.md                                     → mid-entry at Stage 4
"status"                                                         → print run state
```

Stage 6 (the terminating stage) generates a **6-dimension Collaboration Quality
Evaluation (1-100)** scored geometrically across:

| Dim | Name | What it measures |
|---|---|---|
| 1 | Novelty rigour | Did the augmented-baseline catalog + strict-domination comparator actually run? |
| 2 | Reproducibility | Is `audit_claims.py` present? Are claims re-derivable from on-disk JSON? |
| 3 | Methodological rigour | Multi-seed? Wilson CIs? Ablations? `float64` reference path? |
| 4 | Falsifiability | Cross-LLM with different vendors? Honest-negatives section? |
| 5 | Domain depth | Hamiltonian + mapping + active-space + precision-floor explicit? |
| 6 | Communication | Logical fallacies absent? Abstract-body alignment? Required statements? |

Geometric mean (not arithmetic) so a 99 on five dimensions and a 30 on the
sixth doesn't average away the weakness.

### Target-journal selector

Pass `--journal SLUG` to any skill or pipeline. Every prompt template, paper
section ordering, abstract-word-limit check, and required-statements list
respects the chosen venue. Eleven quantum-computing venues registered:

```
quantum                      Quantum (Verein zur Förderung des Open Access ...)
npj-quantum-information      Nature partner journal — Methods at end, 250-word abstract
prx-quantum                  APS PRX Quantum — long-form, methods inline
physical-review-letters      APS PRL — STRICT 4-page limit
physical-review-a            APS PRA — long-form companion to PRL
physical-review-applied      APS PRApplied — applications/hardware
nature-communications        Nature Comms — 150-word abstract, Methods at end
communications-physics       Nature Comms Physics
quantum-science-and-technology  IOP QST
physics-letters-a            Elsevier PLA
ieee-tqe                     IEEE Transactions on Quantum Engineering
```

Inspect a venue: `python -m skills.common.journals show npj-quantum-information`
Add a custom venue: `--journal-custom-policy path/to/policy.json` (any skill).

### Quantum-library selector for code generation

Pass `--quantum-lib SLUG` to skills that emit code. Seven options:

```
qiskit         IBM Qiskit + qiskit-aer
pennylane      Xanadu PennyLane (autodiff, multi-backend)
qutip          QuTiP (open-quantum-systems-focused)
mlxq           Apple Silicon MLX-native (the simulator from osxQ)
cirq           Google Cirq
openfermion    Hamiltonian builder (pair with a simulator)
no-code        Analytical paper only — skip code generation entirely
```

Emit a code skeleton for any library:
```bash
python -m skills.common.quantum_libs skeleton qiskit
```

### Logical fallacies (with quantum-CS taxonomy)

```bash
chain/run.sh --pipeline fallacies --paper paper.tex
```

Detects the standard fallacies (circular reasoning, post-hoc, false dichotomy,
straw man, etc.) PLUS the eleven quantum-CS-specific fallacies QuantumNovelty
introduces:

- `cherry-picked-baseline` · `ad-hoc-precision-floor` · `conflated-regimes`
- `active-space-handwave` · `hardware-irrelevant-comparison` · `asymptotic-only-claim`
- `unit-inflation` · `simulator-laundering` · `mapping-by-convenience`
- `pareto-cherry-picked-axes` · `cross-llm-theatre`

---

## Modes Reference

Every multi-mode skill is documented below: what the mode does, what it
reads, what it writes, defaults, and a worked example. Modes share the
same driver pattern — `--mode NAME` + per-mode prompt template in
`prompts/<mode>.md`.

### `deep_research` — 7 modes

Quantum-aware research surface. Every mode reads `--topic STR` and optionally
`--journal SLUG`, `--quantum-lib SLUG`, `--hamiltonian-id STR` to tailor its
output.

#### `--mode full` — multi-source synthesis with augmented-baseline catalog
- **Reads:** `--topic STR` (required) plus optional context flags.
- **Writes:** `synthesis.md` (600-900 words connected prose), `cards/*.json`
  (one per source), `baseline_catalog.json` (Pareto-shaped rows that
  `novelty_audit` will merge with the user's LLM archive).
- **Defaults:** synthesises against CrossRef + arXiv + Semantic Scholar
  (Google Scholar via Serper if `SERPER_KEY` is set); excludes papers with
  Hamiltonian-class mismatch from the baseline catalog (the asymmetry
  argument requires comparable rows).
- **When to use:** before drafting a paper; before running `novelty_audit`.
- **Example:** `chain/run.sh --pipeline deep-research --mode full
  --topic "VQE for H2O at (4e,4o) active space" --hamiltonian-id H2O_4e_4o_8q`

#### `--mode quick` — one-page expert brief
- **Reads:** `--topic STR`.
- **Writes:** `brief.md` (~300-400 words: What's known / What's contested /
  Why a 2026 paper here is hard).
- **Defaults:** maximum 3 cited Author-Year refs; no card extraction.
- **When to use:** 5-minute reality check before investing a week in a topic.
- **Example:** `chain/run.sh --pipeline deep-research --mode quick
  --topic "Strang-Suzuki Trotter error scaling"`

#### `--mode systematic-review` — PRISMA-2020 flow
- **Reads:** `--topic STR` (treated as the research question).
- **Writes:** `prisma_flow.md` (search-strategy table + inclusion/exclusion
  criteria + PRISMA stage table), `included.json` (per-paper records of
  survivors), `excluded.json` (records with exclusion reasons).
- **Defaults:** Hamiltonian-class match is added as an *additional*
  inclusion criterion (beyond the PRISMA defaults) so system-size mismatched
  papers are explicitly excluded.
- **When to use:** building a defensible literature review section for a
  paper; need to justify the inclusion / exclusion decisions.
- **Example:** `chain/run.sh --pipeline deep-research --mode systematic-review
  --topic "shadow tomography sample complexity"`

#### `--mode socratic` — guided question formulation
- **Reads:** `--topic STR` (the user's still-fuzzy direction).
- **Writes:** `research_question.md` (the LLM's counter-questions to
  sharpen the topic), `subquestions_tree.json` (three branches: Physics /
  Algorithmic / Engineering; 2-4 sub-questions each), `next_steps.md` (the
  1-2 questions to answer first for the most leverage).
- **Defaults:** the three-branch split is enforced (conflating Physics /
  Algorithm / Engineering is the #1 failure mode of quantum-CS proposals).
- **When to use:** very early stage — you have an area of interest but no
  research question yet.
- **Example:** `chain/run.sh --pipeline deep-research --mode socratic
  --topic "noise-model-aware VQE optimisation"`

#### `--mode fact-check` — quantum-numerical claim verification
- **Reads:** `--topic STR` (the claims as free text) or `--paper PATH`
  (a draft to scan claims from).
- **Writes:** `factcheck_report.md` — per-claim verdict with type (energy /
  gate count / fidelity / time), reported precision, source attribution,
  verification status (VERIFIED / DRIFTED / WRONG-UNITS / WRONG-SYSTEM /
  UNVERIFIABLE-FROM-SOURCE / UNCITED), and recommended action.
- **Defaults:** distrusts the LLM's memory — defaults to
  UNVERIFIABLE-FROM-SOURCE unless direct evidence is in scope. Unit
  checking is always on (Ha vs eV vs mHa vs Ry vs cm⁻¹).
- **When to use:** reviewing your own draft; checking a colleague's claim
  before citing it.
- **Example:** `chain/run.sh --pipeline deep-research --mode fact-check
  --topic "UCCSD-1-Trotter on LiH at STO-3G uses 198 gates with 64 CNOTs"`

#### `--mode lit-review` — extended literature review section (1500-2500 words)
- **Reads:** `--topic STR`.
- **Writes:** `lit_review.md` ready for direct manuscript inclusion —
  Historical context → Recent advances (grouped by cluster) → Open problems
  → Connection to user's contribution.
- **Defaults:** distinguishes peer-reviewed from preprint for any work <24
  months old; cites Author-Year only (no invented DOIs).
- **When to use:** writing the Related Work section.
- **Example:** `chain/run.sh --pipeline deep-research --mode lit-review
  --topic "Pareto-front methods in quantum compilation"`

#### `--mode review` — research-quality assessment (NOT peer review)
- **Reads:** `--topic STR` (paraphrase or paper title) optionally with
  `--paper PATH`.
- **Writes:** `research_quality_review.md` scored against the audit-and-
  falsify checklist (augmented baselines? recompute? Wilson CIs? cross-LLM?
  honest negatives? simulator precision? auditable claims?).
- **Defaults:** scores 1-10 on research rigour; names which audit checks
  the paper would pass and which fail.
- **When to use:** quick rigour check on a paper you may cite; distinct
  from `quantum_reviewer` which simulates a 5-voice peer-review panel.
- **Example:** `chain/run.sh --pipeline deep-research --mode review
  --topic "Smith 2025: Pareto methods for quantum simulation"`

---

### `quantum_paper` — 10 modes

Multi-mode quantum-paper authoring. Every mode honors `--journal SLUG`
(section ordering, abstract word limit, required statements) and
`--quantum-lib SLUG` (which library to use for code snippets).

#### `--mode full` — write a complete first draft
- **Reads:** `--topic STR` (required).
- **Writes:** `paper.tex` (or `.md` if no journal template), `figures.md`
  (descriptions of figures the user must produce), `notes_for_author.md`.
- **Defaults:** target ~5000-8000 words for the main text if no journal
  word limit is set; methods placement follows journal policy (end for
  Nature/npj/Comms Physics, inline for PRX/PRL/PRA); roman-numeral
  `enumerate` for in-text lists; placeholder `\cite{Author2024Method}`
  for refs the user must resolve.
- **When to use:** you have measured results and want a first draft.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode full
  --topic "LLM-driven VQE ansatz discovery" --journal npj-quantum-information
  --quantum-lib mlxq`

#### `--mode plan` — guided contribution → method → results → discussion ladder
- **Reads:** `--topic STR`.
- **Writes:** `plan.md` (four-rung ladder: Headline / Mechanism / Method /
  Empirical) plus `questions_for_author.md` (8-12 questions the user must
  answer before drafting — grouped into Physics / Algorithmic /
  Engineering / Evidential).
- **Defaults:** highlights any rung where the lower claims don't yet
  support the higher claim.
- **When to use:** before drafting — when the contribution structure isn't
  yet sharp.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode plan
  --topic "Trotter error in random-coupling Heisenberg chains"`

#### `--mode outline-only` — section-by-section outline with word budget
- **Reads:** `--topic STR`.
- **Writes:** `outline.md` (human-readable per-section purpose + key claims
  + word target) plus `outline.json` (machine-readable budgets that
  downstream `draft_quality` can validate against).
- **Defaults:** section names match the target journal's `section_order`;
  per-section word targets are `[lo, hi]` ranges that sum within ±10% of
  the journal's `body_word_limit`.
- **When to use:** the contribution is sharp; the structure isn't.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode outline-only
  --topic "K=5 amplitude pruning for UCCSD on H2O" --journal prx-quantum`

#### `--mode revision` — apply reviewer comments to a draft
- **Reads:** `--draft PATH` (required), `--reviewer-comments PATH` (required).
- **Writes:** `paper_v2.tex` (the revised draft with `% R1:` inline
  markers), `response_to_reviewers.md` (per-comment Response / Change
  location / ACTIONED status), `change_log.md`.
- **Defaults:** every comment gets a response (no silent drops);
  ACTIONED / PARTIALLY-ACTIONED / NOT-ACTIONED with specific rationale;
  declines politely with audit-and-falsify framework citation when a
  comment would require an unsupported claim.
- **When to use:** you received reviewer comments and need to revise.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode revision
  --paper draft_v1.tex --reviewer-comments r1.md
  --journal npj-quantum-information`

#### `--mode revision-coach` — parse reviewer comments into a prioritised roadmap
- **Reads:** `--reviewer-comments PATH` (required), `--paper PATH` (optional context).
- **Writes:** `roadmap.md` (table of `# / Comment summary / Severity /
  Effort / Touches sections / Action category`) plus `roadmap.json` with
  the same data.
- **Defaults:** Severity ∈ {must-fix, should-fix, nice-to-have}; Effort
  ∈ {S=<1h, M=1-4h, L=4h-1d, XL=>1d}; sequencing groups by section to
  minimize re-reading.
- **When to use:** before starting a revision sprint — to plan the order
  of attack.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode revision-coach
  --paper draft_v1.tex --reviewer-comments r1.md`

#### `--mode abstract-only` — write just the abstract
- **Reads:** `--paper PATH`.
- **Writes:** `abstract.md`.
- **Defaults:** sized to the target journal's `abstract_word_limit` (250
  for npj-QI; 150 for Nature Comms / Comms Physics; 600 for PRL); names
  the Hamiltonian / active space / simulator precision explicitly; no
  "state-of-the-art" without a specific baseline; no marketing words.
- **When to use:** you have a full draft; the abstract needs polish for
  the venue's word limit.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode abstract-only
  --paper draft_v2.tex --journal nature-communications`

#### `--mode lit-review` — convert into a STANDALONE review paper
- **Reads:** `--topic STR`.
- **Writes:** `lit_review_paper.tex` — a full survey article (not a
  section; that's `deep_research --mode lit-review`).
- **Defaults:** structure is Abstract → Scope → Historical → Cluster
  sections → Cross-cluster Pareto map → Open problems → Outlook.
- **When to use:** you want to publish a review article, not a research paper.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode lit-review
  --topic "ADAPT-VQE methods 2020-2026" --journal quantum`

#### `--mode format-convert` — switch templates / citation styles
- **Reads:** `--paper PATH`, `--journal SLUG` (the new target).
- **Writes:** `converted.tex` + `conversion_notes.md` (every substantive
  change made + manual-review flags).
- **Defaults:** swaps `\documentclass`; converts `\cite{}` style;
  reorders sections to match target's `section_order` (e.g., Methods
  inline → Methods at end); adds the target's `required_statements`
  blocks at the right position.
- **When to use:** you drafted for one venue and decided to submit elsewhere.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode format-convert
  --paper draft_prx.tex --journal npj-quantum-information`

#### `--mode citation-check` — verify cites match claims
- **Reads:** `--paper PATH`.
- **Writes:** `citation_report.md` (per-cite verdict: resolves in
  bibliography? claim-to-source fit GOOD / WEAK / MISMATCHED /
  UNVERIFIABLE? recommended fix) + `citation_status.json`.
- **Defaults:** marks UNVERIFIABLE rather than guessing; distinguishes
  textbook cites for foundational results (acceptable) from textbook cites
  for very recent results (problematic); flags concentrated self-citations.
- **When to use:** before submission; lighter / faster than the
  `novelty_audit` integrity pass.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode citation-check
  --paper draft_v2.tex`

#### `--mode disclosure` — generate the venue-required disclosure block
- **Reads:** `--paper PATH`, `--journal SLUG`, `--quantum-lib SLUG`.
- **Writes:** `disclosure_block.tex` + `disclosure_block.md` — `\section*`
  blocks for each required statement in the target journal's policy:
  Funding / Competing Interests / Author Contributions / Data Availability /
  Code Availability / IRB / Preprint Status / AI-Use Disclosure.
- **Defaults:** Code Availability incorporates the chosen `--quantum-lib`
  automatically (e.g., `code is available at <repo URL>, built on Qiskit ...`);
  for `--quantum-lib no-code` writes "No code was generated for this work";
  the AI-Use block discloses use of the audit-and-falsify framework as a
  methodological aid.
- **When to use:** final pre-submission step.
- **Example:** `chain/run.sh --pipeline quantum-paper --mode disclosure
  --paper draft_v2.tex --journal npj-quantum-information
  --quantum-lib mlxq`

---

### `quantum_reviewer` — 6 modes

Peer-review-panel simulation. Every mode reads `--draft PATH` (required) and
optionally `--journal SLUG` (so the panel applies the right rubric).

#### `--mode full` — 5-voice panel (EIC + R1 + R2 + R3 + Devil's Advocate)
- **Reads:** `--draft PATH`, `--journal SLUG`.
- **Writes:** `review_panel.md` containing:
  - **Reviewer 1** (Physics correctness — Hamiltonian, active space, units,
    simulator precision, mappings) — ≥4 paragraphs, verdict 1-10 + recommendation.
  - **Reviewer 2** (Algorithmic novelty — vs current published baselines,
    strict-domination at calibrated ε, ratio recomputability) — ≥4 paragraphs.
  - **Reviewer 3** (Empirical evidence — Wilson CIs, multi-seed variance,
    ablations, honest negatives, audit-script existence) — ≥4 paragraphs.
  - **Devil's Advocate** — strongest possible rejection, ≥4 paragraphs.
  - **Editor-in-Chief** — addresses DA, reconciles R1/R2/R3, final verdict
    (accept / minor-revisions / major-revisions / reject) + numbered
    must-fix list.
  - Vote table.
- **Defaults:** voice presence enforced by the driver (post-hoc grep for the
  5 voice markers); missing voices trigger a deterministic "Panel Coverage
  Warning" prepended to the output. Voice disagreement is encouraged
  ("artificial consensus is a failure mode" appears in the prompt).
- **When to use:** before submission; the most rigorous review mode.
- **Example:** `chain/run.sh --pipeline quantum-reviewer --mode full
  --paper draft_v2.tex --journal npj-quantum-information`

#### `--mode quick` — one experienced reviewer, one page
- **Reads:** `--draft PATH`, `--journal SLUG`.
- **Writes:** `quick_review.md` — two-sentence summary + top 3 strengths
  (with section citations) + top 3 weaknesses (at least one MUST be
  methodological) + recommendation + two-sentence justification.
- **Defaults:** stops at one page; no padding with platitudes.
- **When to use:** quick reality check between drafts.

#### `--mode guided` — iterative coaching session
- **Reads:** `--draft PATH`.
- **Writes:** `improvement_session.md` — strongest 3 elements (preserve)
  + highest-leverage revisions ranked by leverage/effort (max 7) +
  should-not-change list with rationale.
- **Defaults:** every revision is specific (section / paragraph / verbatim
  current text / proposed verbatim replacement / effort estimate).
- **When to use:** between drafts when you want a structured improvement
  plan, not a verdict.

#### `--mode methodology-focus` — methodology only (audit-and-falsify checklist)
- **Reads:** `--draft PATH`.
- **Writes:** `methodology_review.md` + `audit_checklist.json` — per-item
  status (PASS / PARTIAL / FAIL / NOT-APPLICABLE) for: Hamiltonian
  construction, simulator precision, augmented baseline catalog,
  strict-domination at calibrated ε, recompute-from-raw, Wilson 95% CIs,
  multi-seed variance, ablations, cross-vendor falsifiability, honest
  negatives, auditability.
- **Defaults:** scores against checklist evidence, not against the paper's
  claims. Theoretical-work papers still get scored (proofs / dimensional
  analysis / limit checks go in the same slots).
- **When to use:** when you want a methodology-only verdict separate from
  presentation issues.

#### `--mode re-review` — verify revisions addressed prior comments
- **Reads:** `--draft PATH` (the revised paper), `--prior-comments PATH`
  (the previous round's reviewer notes).
- **Writes:** `re_review.md` — per-comment verdict (SATISFIED /
  PARTIALLY-SATISFIED / NOT-SATISFIED / DECLINED-WITH-RATIONALE) with
  evidence locations + overall recommendation + blocking-items list.
- **Defaults:** DECLINED-WITH-RATIONALE is acceptable iff specific;
  silent-drop = NOT-SATISFIED.
- **When to use:** after revising in response to comments.

#### `--mode calibration` — score the reviewer against a gold set
- **Reads:** `--draft PATH`, `--gold-set DIR` (required — directory of
  papers with known labels).
- **Writes:** `calibration_report.md` (gold-set assessment, confusion
  matrix, bias detection, rubric-adjustment recommendations) +
  `confusion_matrix.json`.
- **Defaults:** bias recommendations target the framework's rubric, not
  the gold set.
- **When to use:** establishing or maintaining the reviewer's reliability.

---

### Single-mode skills with significant knobs

#### `novelty_audit` — the audit-and-falsify framework
- **Inputs:** `--pareto-archive PATH` (required), `--augmented-baselines PATH`
  (recommended), `--draft PATH` (required), `--hamiltonian-id STR`.
- **Outputs:** `novelty_verdict.json` (`strict-domination` /
  `interpolation` / `rediscovery` / `dominated`), `augmented_pareto.json`,
  `ratio_recompute.md`, `wilson_annotations.md`,
  `failure_modes_required.md` (only if honest negatives exist),
  `audit_claims.py` (re-runnable per-claim auditor).
- **Defaults:**
  - `--strict-eps-abs 1e-12` — calibrated to `float64` accumulation noise
    (~1.7×10⁻¹¹ Ha empirical floor; ε one order below).
  - `--strict-eps-rel 1e-9` — conservative on any single comparison.
  - `--small-sample-threshold 30` — Wilson CIs added for any K/N with N below.
  - `--require-failure-modes true` — exit rc=2 if the draft has no
    "Failure Modes" section but the augmented baselines include rows the
    LLM-discovered set did not dominate.

#### `logical_fallacies` — fallacy detection with quantum-CS additions
- **Inputs:** `--draft PATH`.
- **Outputs:** `fallacy_report.md` + `fallacy_findings.json`
  (`{name, category, severity, location, evidence, suggested_fix}`).
- **Defaults:**
  - `--severity-threshold medium` — only `medium`, `high`, `critical`
    findings reported.
  - 11 standard fallacies + 11 quantum-CS-specific (cherry-picked-baseline,
    ad-hoc-precision-floor, conflated-regimes, active-space-handwave,
    hardware-irrelevant-comparison, asymptotic-only-claim, unit-inflation,
    simulator-laundering, mapping-by-convenience, pareto-cherry-picked-axes,
    cross-llm-theatre).

#### `process_summary` — Stage 6 CQE
- **Inputs:** `--run-dir PATH`.
- **Outputs:** `process_summary.md` (LLM-written narrative) + `cqe_scores.json`
  (machine-readable scores).
- **Defaults:**
  - 6 dimensions equal-weighted within their probes.
  - Composite method: **geometric mean** (not arithmetic — a 99 on five
    dimensions and 30 on the sixth is correctly penalised; arithmetic
    would have given an averaging-away 87).
  - LLM narrative ON by default; `--no-llm-narrative` for offline runs.
  - Mechanical scoring (no LLM needed for the numbers themselves; the
    LLM only writes the surrounding prose).

#### `chat` — natural-language frontend
- **Inputs:** `--prompt STR` (required), optional `--paper PATH`,
  `--journal SLUG`, `--quantum-lib SLUG`.
- **Outputs:** `dispatch_decision.json` (`{skill, mode, flags, confidence,
  rationale}`) + `dispatch.md`.
- **Defaults:**
  - Pattern-first dispatch (30+ rules, deterministic, confidence=1.0).
  - LLM-fallback if no pattern matches (confidence <1.0).
  - `--execute` is **OFF** by default — chat prints the decision so you
    can review before running. Add `--execute` to actually run the
    dispatched chain command.

---

## Defaults Reference

A single table you can grep when picking flags.

| Component | Knob | Default | Override |
|---|---|---|---|
| **Backend** | LLM backend | `claude` (Claude Code CLI subscription) | `--llm {codex, codex-acp, codex-mcp, anthropic-api}` |
| Backend | Silent backend fallback | **OFF** — failures surface as errors | `QN_DISABLE_BACKEND_FALLBACK=0` env, or `--with-codex-fallback` |
| Backend | Anthropic API path | **OFF** | `--llm anthropic-api` + `ANTHROPIC_API_KEY` env (must be explicit; not used as a fallback) |
| **Paths** | Output root | `runs/<YYYYMMDD_HHMMSS>/<llm_slug>/<pipeline>/` | `--outdir DIR` |
| Paths | Run timestamp | derived once per chain invocation | (override by passing `--outdir`) |
| Paths | LLM slug | the `--llm` value sanitized to alnum + `.` `_` `-` | (uses `--llm` directly) |
| **Anna's Archive** | Mirror | `https://annas-archive.gl` | `QN_ANNAS_MIRROR` env |
| Anna's Archive | Rate limit | 1.0 s per request | `QN_ANNAS_RATE_SECONDS` env |
| Anna's Archive | API key | none (search-only without) | `ANNAS_ARCHIVE_KEY` env (free from annas-archive.org/donate) |
| Anna's Archive | Max downloads per query | 1 | `--max-per-query N` |
| **Journals** | Target venue | none (generic peer-reviewed journal rubric) | `--journal SLUG` (11 venues registered; see `python -m skills.common.journals list`) |
| Journals | Custom policy | none | `--journal-custom-policy PATH/policy.json` |
| **Quantum lib** | Code-generation library | none (library-agnostic) | `--quantum-lib SLUG` (7 options; see `python -m skills.common.quantum_libs list`) |
| **novelty_audit** | `ε_abs` (strict-domination) | `1e-12` (calibrated to float64 noise floor) | `--strict-eps-abs FLOAT` |
| novelty_audit | `ε_rel` (strict-domination) | `1e-9` | `--strict-eps-rel FLOAT` |
| novelty_audit | Small-sample CI threshold | 30 (Wilson CIs added below this N) | `--small-sample-threshold N` |
| novelty_audit | Require Failure Modes section | `true` | `--no-require-failure-modes` |
| **logical_fallacies** | Severity threshold | `medium` | `--severity-threshold {low, medium, high, critical}` |
| **process_summary** | LLM narrative | ON | `--no-llm-narrative` |
| process_summary | Composite method | geometric_mean (not configurable) | n/a — by design |
| **chat** | Pattern dispatch | ON (deterministic) | always on |
| chat | LLM fallback | ON | (no flag to disable; fails through to "could not route" message) |
| chat | Execute dispatched command | **OFF** (prints decision only) | `--execute` |
| **deep_research** | LLM call timeout | 900 s | (no CLI flag; edit driver if needed) |
| **quantum_paper** | LLM call timeout | 1800 s | (no CLI flag; edit driver if needed) |
| **quantum_reviewer** | LLM call timeout | 2400 s | (no CLI flag; edit driver if needed) |
| **All multi-mode skills** | Honest-stub on backend failure | written to the primary output path with a `⚠` banner; rc=3 | (silent fallback NOT enabled) |
| **Pipeline orchestrator** | Stage resumability | ON — stages skip if their output dir is populated | `--force` re-runs all stages |
| Pipeline orchestrator | Stage dir naming | `stage_<N>_<skill>/` under `--outdir` | (uses skill names; not user-configurable) |

---

## Quick tour — exploring novelty for a quantum Hamiltonian

```bash
# 1. Surface what's published.
chain/run.sh --pipeline literature \
  --topic "VQE for H2O at 8 qubits with active-space (4e,4o)" \
  --outdir runs/h2o_lit

# 2. Discover an ansatz; build a Pareto archive over (error, params, CNOT).
chain/run.sh --pipeline pareto-discover \
  --hamiltonian H2O_4e_4o_8q \
  --baseline UCCSD-1-Trotter,UCCSD-K5-pruned,HEA-5L \
  --generations 8 --samples 4 --llm claude \
  --outdir runs/h2o_pareto

# 3. Audit-and-falsify: augment the baseline catalog from step 1,
#    re-run strict-domination, recompute every ratio from raw JSON,
#    annotate small-sample rates with Wilson CIs.
chain/run.sh --pipeline novelty-audit \
  --pareto-archive runs/h2o_pareto/archive.json \
  --augmented-baselines runs/h2o_lit/baseline_catalog.json \
  --outdir runs/h2o_audit

# 4. Cross-LLM falsifiable amplitude prediction (claude vs codex).
chain/run.sh --pipeline cross-llm \
  --hamiltonian H2O_4e_4o_8q \
  --geometry-sweep "R_OH=0.7,0.96,1.2,1.5,2.0 A" \
  --llms claude,codex \
  --outdir runs/h2o_xllm

# 5. Draft a paper around the surviving claims, gated by audit pipeline.
chain/run.sh --pipeline draft-paper \
  --pareto runs/h2o_audit/pareto_final.json \
  --xllm    runs/h2o_xllm/results.json \
  --venue   "npj Quantum Information" \
  --outdir  runs/h2o_paper
```

Each `chain/run.sh --pipeline X` step writes a self-contained directory containing every intermediate artefact, every LLM prompt, every captured response, and a `pipeline_summary.json` mapping stage → status → elapsed time → outputs. Reruns are idempotent: re-pointing at the same `--outdir` resumes from the last completed stage.

---

## The skill catalog at a glance

| Skill | Purpose | Inputs | Outputs |
|---|---|---|---|
| `literature_surfacer` | Multi-source literature pull + LLM card extraction | `--topic`, `--n` | `cards/*.json`, `synthesis.md`, `baseline_catalog.json` |
| `book_acquirer` | Anna's Archive download + OCR + index | `--query`, `--target-dir` | downloaded PDFs, OCR'd `.txt`, source manifest |
| `pareto_explorer` | LLM-in-loop Pareto-front discovery on (Hamiltonian, baselines) | `--hamiltonian`, `--baseline`, `--generations`, `--samples` | `archive.json`, per-generation `circuit.py`, `eval.json` |
| `ablation_designer` | Design controlled ablations (LLM mutator vs random, hint-load-bearing tests) | `--axis`, `--seeds`, `--proposals-per-seed` | `ablation_results.json`, `interpretation.md` |
| `cross_llm_prediction` | Falsifiable amplitude-prediction rubric, multiple vendors | `--hamiltonian`, `--geometry-sweep`, `--llms` | per-LLM prediction JSON + overlap-vs-truth table |
| `audit_falsify` | Strict-domination comparator + ratio recompute + Wilson CIs + audit script | `--archive`, `--draft.tex` | `audit_report.md`, `audit_claims.py`, pass/fail per claim |
| **`novelty_audit`** | **Our contribution** — augmented-baseline pass + audit_falsify + honest-negatives section enforcement | `--pareto-archive`, `--literature-baselines`, `--draft` | `novelty_verdict.json` (`novel` / `rediscovery` / `interpolation`), augmented Pareto map |

Every skill has a `SKILL.md` in its directory documenting its CLI surface, its prompt template, its expected inputs, and its outputs schema.

---

## Example — the motivating paper (in development)

The paper that motivated this framework is currently in development and
will be released in its own repository once published. Its full source —
manuscript, cover letter, measured-results section, the 76-check
deterministic audit pipeline that re-derives every numerical claim from
on-disk JSON in under 100 ms, and the experiment artefacts the audit
reads against — will ship there. Until then, the published-paper reviews
in `examples/paper_reviews/` and the two-paper analysis in
`examples/end_to_end/two_paper_novelty/` are the worked examples to read.

---

## Adding a new skill

A skill is a directory under `skills/`. Minimum contents:

```
skills/my_new_skill/
├── SKILL.md          # CLI surface + inputs + outputs schema
├── run.sh            # bash entry point (parses CLI, calls Python driver)
├── skill.py          # Python driver (does the work)
└── prompts/          # (optional) prompt templates
    └── prompt_v1.md
```

The chain dispatcher in `chain/run.sh` discovers skills by listing `skills/*/run.sh` and exposes each as `--enable <name>` or `--stages <name>`. Adding a skill requires no chain edit — drop in the directory, it shows up in `chain/run.sh --list-skills`.

See `docs/ADDING_SKILLS.md` for the full contract.

---

## Licence

MIT for QuantumNovelty's own code. ARC and ARS pieces remain under their respective upstream licences (see `docs/PROVENANCE.md` for the per-component breakdown).

---

## Cite

If QuantumNovelty's audit-and-falsify framework helps you publish a paper, please cite this repository (a companion paper is in development and will be linked here once published). A machine-readable [`CITATION.cff`](CITATION.cff) ships at the repo root — GitHub's **"Cite this repository"** button generates APA/BibTeX from it — or copy the BibTeX directly:

```bibtex
@software{kashani2026quantumnovelty,
  author  = {Kashani, Shlomo},
  title   = {QuantumNovelty: an audit-and-falsify framework for
             quantum-computing research papers and patents},
  year    = {2026},
  version = {1.0.0},
  license = {MIT},
  url     = {https://github.com/BoltzmannEntropy/QuantumNovelty},
}
```

And if you want to give a nod to the upstreams:

```bibtex
@misc{autoresearchclaw,
  title = {AutoResearchClaw — back-half quality-gate pipeline for LLM-driven research agents},
  howpublished = {\url{https://github.com/}},
}

@misc{academicresearchskills,
  author = {Imbad},
  title = {Academic Research Skills},
  howpublished = {\url{https://github.com/imbad0202/academic-research-skills}},
}
```

---

## A final word

If you build on this and find an audit dimension we missed, please open an issue. The whole point of the framework is that the audit is **falsifiable** — including the audit itself. If you can construct an example where QuantumNovelty's pipeline declares a result "novel" and a competent reviewer would not, that's a bug we want to fix before someone else publishes a paper they have to retract.
