# QN vs ARS vs ARC — three-way head-to-head on one PRX Quantum paper

Run the **same paper** through three review frameworks end-to-end, embed
every stage's full output side-by-side in a single PDF, **with token + USD
cost ledger per framework**.

## Paper under analysis

| Tag | Paper | Venue | arXiv |
|---|---|---|---|
| `lcutrotter` | Simple and high-precision Hamiltonian simulation by compensating Trotter error with LCU (Zeng, Sun, Jiang, Zhao) | **PRX Quantum** 6, 010359 | [2212.04566](https://arxiv.org/abs/2212.04566) |

Reuses the `lcutrotter.pdf` + extracted text from `../two_paper_novelty/`
so QN's chain runner resumes from cache (0 new LLM calls) and only the
ARS + ARC halves cost LLM budget on re-runs.

## The three pipelines

| Framework | Pipeline | Stages | Driver |
|---|---|---|---|
| **QuantumNovelty** | `chain/run.sh --pipeline paper-audit` | 4 (research / reviewer 5-voice / fallacies / cqe) | the chain runner itself |
| **academic-research-skills** (ARS) | `academic-paper-reviewer` skill, full mode | 7-agent orchestration (Phase 0 field-analyst, Phase 1a–e EIC + 4 reviewers + Devil's Advocate, Phase 2 editorial synthesizer) | `ars_driver.py` — loads each `agents/*.md` prompt verbatim, drives via QN's `call_llm()` |
| **AutoResearchClaw** (ARC) | `peer_review` + `quality_gate` (2-stage review subset of ARC's 23-stage full pipeline) | 2 (peer_review prose + quality_gate JSON verdict) | `arc_driver.py` — loads prompts from `prompts.default.yaml`, drives via QN's `call_llm()` |

All three run on the **same paper text** and the **same backend** (codex
or claude) so output differences reflect each framework's design choices,
not LLM variance.

## What's compared

The `build_compare_report.py` script aggregates every stage's
`_backend_used.json` marker and produces:

| Section | Content |
|---|---|
| §1 Pipeline architecture map | 3-column table mapping QN stages ↔ ARS agents ↔ ARC stages |
| §2 Token + cost ledger | Per-stage token counts, model IDs, USD cost, elapsed seconds — all three frameworks side-by-side |
| §3 QN paper-audit | Full per-stage prose (research review, 5-voice panel, fallacy report, CQE narrative) |
| §4 ARS academic-paper-reviewer | Full per-agent prose (7 agents — field-analyst, EIC, methodology, domain, perspective, Devil's Advocate, editorial synthesizer) |
| §5 ARC peer_review + quality_gate | Full Reviewer A/B markdown + verbatim quality_gate JSON (score_1_to_10, strengths, weaknesses, required_actions) |
| §6 Coverage matrix | 14-row × 3-column table showing which framework covers which class of concern |

## How to run

```bash
bash run_compare.sh
```

By default uses the `codex` backend; override with `QN_LLM=claude bash run_compare.sh`.
Each driver is idempotent — re-running skips stages with non-empty outputs unless
their files are deleted first.

## Output layout

```
_run/
├── inputs/                              lcutrotter.{pdf,txt}
├── qn/                                  full paper-audit chain output
│   ├── 01_research_review/
│   ├── 02_reviewer_panel/
│   ├── 03_fallacies/
│   ├── 04_summary/
│   ├── pipeline_summary.json            stage-health aggregate
│   ├── decision_history.json            append-only proceed/fail log
│   ├── HEARTBEAT_AUDIT.md               per-stage health table
│   ├── _chain_config.json               resolved pipeline configuration
│   └── _run_summary.json                subprocess-RC view
├── ars/                                 ARS 7-agent output
│   ├── 00_reviewer_config.md
│   ├── 01..05_*_review_card.md          5 independent peer reviewers
│   ├── 06_editorial_decision_letter.md
│   ├── *_backend_used.json              per-call token + cost marker
│   └── ars_run_summary.json
├── arc/                                 ARC 2-stage output
│   ├── 01_peer_review.md                Reviewer A + B prose
│   ├── 02_quality_gate.json             {score_1_to_10, verdict, strengths, weaknesses, required_actions}
│   ├── *_backend_used.json
│   └── arc_run_summary.json
├── COMPARE_REPORT.pdf                   39-page side-by-side report
├── COMPARE_REPORT.json                  machine-readable summary
└── COMPARE_REPORT.tex                   LaTeX source
```

## Honest provenance

Both `ars_driver.py` and `arc_driver.py` write `_backend_used.json`
markers in QN's exact shape, so the token ledger compares apples-to-apples
across the three frameworks. The markers record `backend_actually_used`
(not just `backend_requested`), so if a backend mid-run switches (e.g.
codex hits usage limit and one stage falls through to claude, or
vice-versa), the marker captures the actual backend that wrote the file.

## Reuse from `../two_paper_novelty/`

`run_compare.sh` looks for `../two_paper_novelty/_run/reports/lcutrotter/`
and copies its 4-stage paper-audit output if present. That lets the
3-way comparison piggy-back on the existing QN run and only pay LLM
budget for ARS (7 calls) and ARC (2 calls).
