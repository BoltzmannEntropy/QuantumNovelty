# `quantum_kb` — local quantum KB indexing and RAG search

Builds and queries portable QuantumNovelty knowledge bases. This is the
QuantumNovelty counterpart to ScienceSkills' seed-kb/RAG layer, but it is
offline-first: no LLM, network, resident server, HuggingFace cache, or embedding
model is required.

## Storage layout

```
quantum-kb/
├── kb.json
└── <kb_id>/
    ├── kb_config.json
    ├── documents/
    ├── manifest.jsonl
    ├── cards/
    └── index/
        ├── chunks.jsonl
        ├── lexical_index.json
        ├── hashed_vectors.npz      # when NumPy is available
        ├── hashed_vectors.json     # pure-Python fallback
        └── index_stats.json
```

Set `QUANTUMNOVELTY_KB_PATH` or pass `--kb-root DIR` to keep the KB outside the
repo.

## CLI

```
skills/quantum_kb/run.sh bootstrap
skills/quantum_kb/run.sh create --kb quantum_papers --name "Quantum Papers" --default
skills/quantum_kb/run.sh ingest --kb quantum_papers --source /path/to/papers_or_notes
skills/quantum_kb/run.sh index --kb quantum_papers --purge
skills/quantum_kb/run.sh search --kb quantum_papers --query "surface code threshold decoder" --outdir runs/kb_search
skills/quantum_kb/run.sh substantiate --kb quantum_papers --claim "A VQE novelty claim must compare against UCCSD-inspired ansatz baselines."
skills/quantum_kb/run.sh review --kb quantum_papers --paper draft.md --question "Does this paper substantiate its VQE novelty claims?"
skills/quantum_kb/run.sh perspective --kb quantum_papers --question "What evidence should show that an LLM-discovered VQE ansatz is genuinely novel?"
skills/quantum_kb/run.sh list
skills/quantum_kb/run.sh status --kb quantum_papers
```

## Retrieval

The index combines:

- BM25 sparse postings.
- Deterministic hashed vectors over tokens, bigrams, and character 4-grams.
- Quantum-domain query expansion for VQE, QAOA, QEC, surface-code, Trotter,
  Hamiltonian simulation, QML, and related phrasing.
- Metadata boosts over title, author, year, keywords, and source path.
- Source diversity and near-duplicate suppression in the final result set.

## Inputs

Supported document extensions: `.txt`, `.md`, `.markdown`, `.tex`, `.rst`,
`.bib`, `.json`, `.jsonl`, `.pdf`, and optional `.docx` when `python-docx` is
installed.

Markdown/YAML-style front matter is recognized:

```
---
title: Surface-code decoder notes
author: ...
year: 2026
keywords: surface code decoder qec
---
```

## Outputs

Search writes:

- `search_results.json` - machine-readable result payload.
- `search_results.md` - human-readable results.
- `quotes_for_prompt.txt` - prompt-ready quote snippets.
- `context.md` - compact retrieved context block.

Substantiation writes:

- `claim_evidence.json` - claim-by-claim exact quote evidence.
- `claim_evidence.md` - human-readable evidence dossier.
- `evidence_for_prompt.txt` - prompt-ready claim evidence.
- `citations.md` - deduplicated full citations.

Review writes everything from substantiation plus:

- `review_claims.json` - claims extracted from the paper or passed explicitly.
- `grounded_review_prompt.txt` - the Emma-like review prompt containing only
  the paper context and retrieved evidence.
- `grounded_review.md` - LLM review by default, or deterministic review when
  `--no-llm` is passed.
- `grounded_review_deterministic.md` - always written as an audit fallback.

Perspective writes an Emma Perspectives-parity artifact set:

- `01_quantum_perspective.md` - final post with verified quote and claim
  appendices.
- `quantum_perspective.md` - combined copy of the final post.
- `emma_perspective_prompt.txt` - prompt containing the review question and
  retrieved evidence packet.
- `quotes_for_prompt.txt` and `quote_candidates.json` - exact KB quote packet.
- `quote_fidelity.json` - every body quote checked against indexed KB chunks.
- `claim_audit.json` - deterministic KB-only cited-sentence scaffold.
- `fact_check.md` - KB-only quote-fidelity/fact-check summary.
- `emma_parity_report.json` - counts and artifact paths for parity comparison.
- `citations.md` - deduplicated full citations used by the quote packet.

Indexing writes `index_stats.json`, `manifest.jsonl`, `chunks.jsonl`,
`lexical_index.json`, and either `hashed_vectors.npz` or
`hashed_vectors.json`.

## Emma-like Review Workflows

`review` is the high-level workflow:

1. Accepts explicit `--claim` values, a `--claims-file`, or a `--paper` from
   which reviewable claims are extracted deterministically.
2. Retrieves word-for-word KB quotes for every claim.
3. Emits full and inline citations for every quote.
4. Builds a grounded-review prompt that forbids invented citations and asks the
   reviewer to mark thin evidence as thin.
5. Runs the selected LLM unless `--no-llm` is passed.

Use `--no-llm` for tests and evidence-only audits. Use normal LLM mode for the
full narrative review.

`perspective` is the Emma Perspectives-parity workflow:

1. Accepts a discussion/review `--question`.
2. Retrieves a short packet of exact KB quote fragments with inline and full
   citations.
3. Builds an Emma-style prompt for a concise position/perspective post.
4. Writes an LLM perspective by default, or a deterministic no-LLM perspective
   when `--no-llm` is passed.
5. Verifies every body quote against indexed KB chunks.
6. Appends `## Quotes used (verbatim, with source)` and
   `## Claims (verified against cited sources)` sections.
7. Emits `emma_parity_report.json` so ScienceSkills Emma outputs can be compared
   against QN on quote count, verified quote count, and citation artifacts.
