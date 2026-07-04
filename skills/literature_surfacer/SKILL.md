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

## Quantum-domain filter (F-03)

Pass `--require-term` to drop candidate cards whose title+abstract contain
no quantum-domain keyword (`quantum`, `qubit`, `ansatz`, `variational`,
`hamiltonian`, `hilbert`, `entanglement`, `superposition`, `wavefunction`,
`pauli`, `vqe`, `qaoa`, `qcnn`, `qml`, `unitary`, `circuit`, `gate`,
`fidelity`, `decoherence`).

Default: **off** (backward compatible — all existing call-sites are unaffected).

When active, the filter runs after deduplication.  The number of dropped cards
is printed as `"filtered N off-topic cards"` and stored in `candidates.json`
under the key `n_filtered_offtopic`.  Use for quantum queries where Semantic
Scholar over-retrieves off-topic hits.
