# quantum_scout

Automatic quantum-novelty scout, shaped for parity with the ScienceSkills
`scout` workflow but implemented as a normal QuantumNovelty skill.

This is the preferred QN discovery path. It is deliberately broader than the
legacy `pareto_explorer`: it should scout and recommend novel avenues in any
quantum-computing related subject, not only VQE, chemistry, or ansatz search.

## Purpose

Given a quantum-computing topic, `quantum_scout` builds a run-local scout
package:

- live multi-source literature surface via `literature_surfacer`
- bounded arXiv PDF acquisition and run-local indexing
- optional run-local source KB from `--source-file` inputs
- candidate research ideas with novelty/risk notes
- recommendation rank, rationale, and venue fit for each avenue
- exact quote substantiation through `quantum_kb`
- references, claim ledger, manifest, and scout report

The skill is intentionally compositional. It does not duplicate
`literature_surfacer` or `quantum_kb`; it orchestrates them into one
SS-like scout output.

Use it for quantum algorithms, QEC/fault tolerance, hardware/control,
compilers, verification, quantum ML, networks, sensing, cryptography,
simulation, benchmarking, and quantum-inspired methods.

## CLI

```bash
skills/quantum_scout/run.sh \
  --topic "Using AI for designing superconducting quantum chips" \
  --outdir runs/scout_demo \
  --llm codex
```

Useful options:

| Flag | Meaning |
|---|---|
| `--source-file FILE` | Repeatable PDF/text/markdown/docx/json source to ingest into the run-local scout KB |
| `--kb KB_IDS` | Comma-separated existing quantum KB IDs to search for quote support |
| `--kb-root DIR` | Existing KB root; defaults to the run-local `quantum-kb/` when source files are provided |
| `--n N` | Number of candidate scout ideas. Default: 6 |
| `--literature-n N` | Hits per source for `literature_surfacer`. Default: 10 |
| `--sources LIST` | Literature sources. Default: `crossref,arxiv,semantic_scholar,serper` |
| `--arxiv-max-downloads N` | Max arXiv PDFs to download and index. Default: 5 |
| `--no-arxiv-corpus` | Disable arXiv PDF acquisition |
| `--pdf-kb-only` | Download/ingest/index/search sources and exit before idea generation |
| `--quotes-per-claim N` | Quote evidence per idea claim. Default: 3 |
| `--no-live-literature` | Skip live literature retrieval; useful for offline tests |
| `--no-llm` | Deterministic idea generation and report scaffolding |

## Outputs

```text
scout_report.md
scout_report.json
scout_references.json
scout_references.bib
claim_ledger.md
claim_ledger.json
substantiation/
  claim_evidence.json
  claim_evidence.md
  evidence_for_prompt.txt
  citations.md
global_literature/
  candidates.json
  synthesis.md
  baseline_catalog.json
arxiv_corpus/
  pdf/
  references.json
  status.json
source_kb/
  status.json
quantum-kb/
scout_manifest.json
scout_quality.json
```

## Chain Usage

```bash
chain/run.sh --pipeline scout \
  --topic "Using AI for designing superconducting quantum chips" \
  --source-file notes.md \
  --llm codex
```

PDF/KB-only mode:

```bash
chain/run.sh --pipeline scout \
  --topic "quantum error correction decoders" \
  --scout-pdf-kb-only \
  --scout-arxiv-max-downloads 20 \
  --llm codex
```
