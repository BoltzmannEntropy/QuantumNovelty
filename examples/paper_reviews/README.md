# Paper reviews — five papers, three venues

The QuantumNovelty `paper-audit` chain run end-to-end on five real
quantum-computing papers — four **peer-reviewed and published** plus one
high-profile **preprint** (Microsoft Quantum's InAs–Pb tetron paper) —
covering every target venue in QN's journal registry, including two on
quantum machine learning. All reviews were generated with the **Claude Code CLI**
backend; every stage records its exact model snapshot, token counts,
and USD cost.

> ## ⚠ Disclaimer — AI-generated reviews
>
> The reviews in this folder are generated end-to-end by AI (the
> QuantumNovelty agent pipeline). They are provided **strictly for
> academic and demonstration purposes** — to show what the framework
> produces on real published papers. We make **no claims about the
> correctness, quality, novelty, or publication-worthiness of the
> papers under review**. Four of the papers passed real peer review at
> their respective journals and the fifth is a public arXiv preprint;
> nothing here should be read as criticism
> of the authors, and an AI review is not a substitute for human peer
> review. Paper copyrights remain with their authors and publishers;
> arXiv PDFs are included for academic convenience under their arXiv
> distribution licenses.

## The papers

| Tag | Paper | Venue | arXiv |
|---|---|---|---|
| `lcutrotter` | Simple and high-precision Hamiltonian simulation by compensating Trotter error with linear combination of unitary operations — Zeng, Sun, Jiang, Zhao | **PRX Quantum** 6, 010359 (2025) | [2212.04566](https://arxiv.org/abs/2212.04566) |
| `flowvqe` | Generative flow-based warm start of the variational quantum eigensolver — Zou, Rahm, Kockum, Olsson | **npj Quantum Information** (2025) | [2507.01726](https://arxiv.org/abs/2507.01726) |
| `hwqml` | Trainability and Expressivity of Hamming-Weight Preserving Quantum Circuits for Machine Learning — Monbroussou, Mamon, Landman, Grilo, Kukla, Kashefi | **Quantum** 9, 1745 (2025) | [2309.15547](https://arxiv.org/abs/2309.15547) |
| `qcnn` | Quantum Convolutional Neural Networks are Effectively Classically Simulable — Bermejo, Braccia, Rudolph, Holmes, Cincio, Cerezo | **PRX Quantum** 7, 020304 (2026) | [2408.12739](https://arxiv.org/abs/2408.12739) |
| `majorana2` | 20 Second Parity Lifetime in an InAs–Pb Tetron Device — Microsoft Quantum | **preprint** (reviewed against the PRX Quantum rubric) | [2606.03884](https://arxiv.org/abs/2606.03884) |

`hwqml` and `qcnn` are the **quantum-machine-learning** entries:
trainability/expressivity of Hamming-weight-preserving circuits, and
the QCNN-dequantization result (classical simulability via Pauli-path
methods) respectively. `majorana2` is the **hardware** entry — the first
non-gate-model paper through the pipeline (topological qubits, parity
lifetime), audited while still a preprint.

> **How this differs from `examples/end_to_end/`:** this folder is the
> *reviewer showcase* — what the `paper-audit` pipeline produces on real
> papers (one folder per paper, plus the typeset review PDFs).
> `examples/end_to_end/` demonstrates the *framework itself* end-to-end:
> the chain-runner harness with telemetry on two papers
> (`two_paper_novelty/`), the QN-vs-ARS-vs-ARC head-to-head
> (`compare_qn_vs_ars_vs_arc/`), and three generated-from-scratch paper
> scaffolds (`avenue_*`).

## What's in each paper's folder

```
<tag>/
├── <tag>_arxiv.pdf                  the paper itself (from arXiv)
├── <TAG>_REVIEW.pdf                 standalone typeset review report
├── 01_research_review/              deep_research --mode review
│   └── research_quality_review.md     audit-and-falsify checklist
├── 02_reviewer_panel/               quantum_reviewer --mode full
│   ├── review_panel.md                5 voices + vote table
│   └── _quality_gate.json             machine-actionable verdict
├── 03_fallacies/                    logical_fallacies
│   ├── fallacy_report.md              prose findings
│   └── fallacy_findings.json          structured findings
├── 04_summary/                      process_summary (Stage-6 CQE)
│   ├── cqe_scores.json
│   └── process_summary.md
└── (per-stage _backend_used.json markers: model, tokens, USD)
```

`majorana2/` additionally carries the opt-in verification-layer stages
(`02d_argument_structure/`, `03c_claims_registry/`,
`03e_disclosure_audit/`, `03f_revision_plan/`) — run via the
`--with-argument-structure --with-claims-registry
--with-disclosure-audit --with-revision-planner` chain flags.

## The combined report

[`REVIEWS.pdf`](REVIEWS.pdf) — one report covering all five papers.
Each paper's folder also ships its own standalone report
(`<TAG>_REVIEW.pdf`, e.g. [`majorana2/MAJORANA2_REVIEW.pdf`](majorana2/MAJORANA2_REVIEW.pdf)).
The combined report contains:
provenance header (project, repository, author, CLI version, model
snapshots), the disclaimer above, token + real-USD ledger, verdict
summary (panel score / EIC verdict / CQE composite per paper), and
every stage's full prose.

## Reproduce

```bash
# per paper (claude is the framework default):
bash ../../chain/run.sh --pipeline paper-audit \
  --paper <paper>.txt --topic "<title>" --journal <venue> \
  --outdir <outdir>

# rebuild the combined PDF:
python3 build_reviews.py --reviews-root <dir-with-tag-subdirs>
lualatex REVIEWS.tex && lualatex REVIEWS.tex
```
