# `literature_surfacer` — multi-source literature pull

Surfaces relevant published work for a research question.

**Sources:** CrossRef + arXiv + Semantic Scholar (default); Google Scholar via
Serper (optional, `SERPER_KEY` env). For book/thesis citations the unresolved
queries are passed to `book_acquirer` (Anna's Archive).

**Inputs:** `--topic STR`, `--n INT` (default 30), `--hamiltonian-id STR` (optional)
**Outputs:** `cards/*.json` (one per source), `synthesis.md` (LLM-extracted),
  `baseline_catalog.json` (Pareto-shaped: feeds `novelty_audit` augmented baselines)

**LLM use:** extractor pass (claude default; honors `--llm`).
**No RAG** — literature is fetched fresh per query.

(Ported from upstream ARS's literature stage with the book-acquirer hook added.)
