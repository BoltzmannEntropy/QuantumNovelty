---
name: patent_prior_art
description: "Real patent prior-art search for the examiner panel. Generates patent-search queries from an invention topic/claims, queries a keyless patent search (Google Patents query endpoint; ddgs site:patents.google.com fallback), and LLM-filters genuine on-topic prior art. Produces a prior-art-of-record reference list that patent_reviewer consumes via --prior-art, so §102/§103 rejections are grounded in named real references instead of fabricated-from-memory citations. Complements literature_surfacer (which covers academic non-patent literature)."
---

# patent_prior_art

Grounds the USPTO examiner panel in REAL patent prior art. Adapted from the
ScienceSkills prior-art search pattern (code_prior_art query-gen + relevance
filter; novelty_check keyless web search).

Outputs: `prior_art.json` (full records), `prior_art_refs.json` (flat list of
relevant publication numbers — feed to `patent_reviewer --prior-art`), and
`prior_art.md`.

Usage: `run.sh --topic "..." [--claims FILE] [--max 20] [--llm claude] [--no-llm] --output DIR`
