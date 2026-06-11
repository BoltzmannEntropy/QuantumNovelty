# citation_integrity — 4-layer citation verifier

Zero LLM calls, zero RAG. CrossRef is the only network dependency
(HTTP, no client library). Adapted from AutoResearchClaw's stage-23
verification schema.

```bash
bash skills/citation_integrity/run.sh \
  --paper paper.tex --bib refs.bib --outdir OUT [--no-network]
```

| Layer | Check | Failure status |
|---|---|---|
| 1 | every `\cite{KEY}` has a `@entry{KEY,...}` in the .bib | `hallucinated` |
| 2 | entry has author + title + year | `suspicious` |
| 3 | DOI resolves on CrossRef and the title matches (or title-search ≥0.7 sim) | `hallucinated` / `suspicious` |
| 4 | title-vs-manuscript token-overlap relevance, 0..1 | non-gating score |

Transient network failures are reported as `skipped`, never
`hallucinated`. `--no-network` runs layers 1+2 only (test/offline
mode).

Output: `verification_report.json` with
`summary.integrity_score = verified / total`.

## Chain integration

`--with-citation-integrity` on the `paper-audit` pipeline (requires
`--bib PATH`; the stage is skipped with a logged decision when the
manuscript is a PDF without source/bib). Stage `03d_citation_integrity`.
