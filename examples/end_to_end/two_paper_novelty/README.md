# Two-paper novelty pipeline — Flow-VQE + LCU-Trotter

End-to-end QuantumNovelty analysis of two recently published quantum-computing
papers, **with full token + USD cost ledger** in the generated PDF.

## Papers under analysis

| Tag | Paper | Venue | arXiv |
|---|---|---|---|
| `flowvqe` | Generative flow-based warm start of the VQE (Zou, Rahm, Kockum, Olsson) | **npj Quantum Information** | [2507.01726](https://arxiv.org/abs/2507.01726) |
| `lcutrotter` | Simple and high-precision Hamiltonian simulation by compensating Trotter error with LCU (Zeng, Sun, Jiang, Zhao) | **PRX Quantum** 6, 010359 | [2212.04566](https://arxiv.org/abs/2212.04566) |

Both sit in QuantumNovelty's target domain (VQE / Trotter / circuit
synthesis), so the framework's audit-and-falsify checklist is directly
applicable to either.

## The pipeline

Per paper, 4 stages:

| Stage | Skill | Output |
|---|---|---|
| 1 | `deep_research --mode review` | `research_quality_review.md` — audit-and-falsify checklist (8 items, PASS/PARTIAL/FAIL/N-A each), 1-10 research-rigour score, highest-leverage improvements |
| 2 | `quantum_reviewer --mode full` | `review_panel.md` — 5-voice panel (EIC + R1 Physics + R2 Novelty + R3 Evidence + Devil's Advocate), per-voice verdict, vote table, final recommendation |
| 3 | `logical_fallacies` | `fallacy_findings.json` — quantum-CS-specific taxonomy (11 standard + 11 QC-specific: cherry-picked-baseline, ad-hoc-precision-floor, simulator-laundering, cross-llm-theatre, etc.) |
| 4 | `process_summary` (no-LLM mode) | `cqe_scores.json` — mechanical 6-dim Collaboration Quality Evaluation; geometric-mean composite |

Then both papers together:

| Stage | Output |
|---|---|
| 5 | `build_report.py` — aggregates every stage's `_backend_used.json` into a token + cost ledger; emits `PIPELINE_REPORT.tex` |
| 6 | `pdflatex` — compiles to `PIPELINE_REPORT.pdf` |

## Token + cost recording

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

Claude calls go through `claude --print --output-format json` so the values
come from the CLI itself, no estimation. Codex calls (no usage stats in the
plain output) fall back to `chars/4` estimates and set
`"tokens_estimated": true` honestly.

`build_report.py` reads these markers across all 8 per-paper stages plus the
process_summary stage and rolls them up per-paper + grand-total into the PDF.

## Reproducing

```bash
cd examples/end_to_end/two_paper_novelty/
./run_two_papers.sh           # fetches both arXiv PDFs, runs 4 stages x 2 papers,
                              # compiles PIPELINE_REPORT.pdf

# Resume-safe: re-running skips per-stage outputs that already exist
# (idempotency via _backend_used.json presence).
```

Requirements:
- `claude` CLI (default) OR `codex` CLI (fallback)
- `curl`, `pdftotext` (poppler-utils)
- `pdflatex` (any TeX distribution)
- Python ≥ 3.11

## Backend choice

The script defaults to `--llm codex` for stability — claude's nested-CLI
isolation playbook reliably handles 1-3 calls in a session but can hit
`tool_use ids must be unique` 400s on longer sessions (the framework refuses
to silently fall back; the call errors out). Codex handles long sessions
without that failure mode.

When claude is available and the session is fresh, swap `--llm codex` →
`--llm claude` in the script for slightly better quality and exact token
counts (codex token counts are char/4 estimates).

## Output tree

```
two_paper_novelty/
├── README.md                          ← this file
├── run_two_papers.sh                  ← driver
├── build_report.py                    ← report builder
└── _run/                              ← generated when you run
    ├── inputs/
    │   ├── flowvqe.pdf
    │   ├── flowvqe.txt
    │   ├── lcutrotter.pdf
    │   └── lcutrotter.txt
    ├── reports/
    │   ├── flowvqe/
    │   │   ├── 01_research_review/{research_quality_review.md, _backend_used.json, full_prompt_review.txt, _llm_generation.log}
    │   │   ├── 02_reviewer_panel/{review_panel.md, _backend_used.json, ...}
    │   │   ├── 03_fallacies/{fallacy_findings.json, fallacy_report.md, _backend_used.json, ...}
    │   │   └── 04_summary/{cqe_scores.json, process_summary.md}
    │   └── lcutrotter/{same tree}
    ├── PIPELINE_REPORT.tex            ← LaTeX comparison report
    ├── PIPELINE_REPORT.pdf            ← compiled PDF with token + cost ledger
    └── PIPELINE_REPORT.json           ← machine-readable summary
```
