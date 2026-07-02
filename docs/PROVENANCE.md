# Provenance — what we built on, who owns what

QuantumNovelty is licenced MIT. Components adapted from upstream projects
retain their original licences. This document records, per component, the
upstream source and the nature of the adaptation.

## AutoResearchClaw (ARC)

**Upstream:** AutoResearchClaw — research-agent gate-stack pipeline.
**Licence:** see upstream repo.
**What we adapted:**
- The gate-stack pattern: a series of independent quality gates each producing
  structured JSON consumed by the next stage. Verdicts compose into a
  `PROCEED / REFINE / PIVOT` decision.
- The back-half gate set: `citation_integrity`, `compilation_quality`,
  `paper_verification`, `quality_gate`, `research_decision`, `knowledge_archive`.
  These appear in `chain/run.sh` for the `draft-paper` pipeline.
- The `_backend_used.json` provenance-marker convention for catching silent
  backend swaps.

**What we changed:**
- Routed `paper_verification` through our `novelty_audit`'s
  recompute-from-raw scanner so abstract numbers are checked against on-disk
  JSON rather than just against the LLM's memory of what it wrote.
- Disabled silent codex fallback by default (`QN_DISABLE_BACKEND_FALLBACK=1`).
  ARC tolerated silent claude→codex degradation in some configurations;
  QuantumNovelty refuses it.

## academic-research-skills (ARS) — https://github.com/imbad0202/academic-research-skills

**Upstream:** Imbad's academic-research-skills.
**Licence:** see upstream repo.
**What we adapted:**
- The modular skill-as-folder pattern: each skill is a self-contained
  directory with `SKILL.md`, `run.sh`, and a Python driver.
- The chain composition: skills are addressed by name; the chain auto-
  discovers them; adding a skill requires no chain edit.
- The literature_surfacer multi-source pull: CrossRef + arXiv + Semantic
  Scholar with per-source card extraction.

**What we changed:**
- Added the book_acquirer hook: literature queries that fail to resolve
  through CrossRef/arXiv/S2 are forwarded to Anna's Archive with OCR.
- Replaced the LLM-call subprocess pattern with a unified `skills/common/llm.py`
  that supports Claude Code CLI (default), codex, codex-acp, codex-mcp,
  Kimi/Moonshot, and anthropic-api as one interface, with backend provenance
  recorded through the same `_backend_used.json` marker.

## Our own contribution — `skills/novelty_audit/`

**The new skill.** The audit-and-falsify framework as described in the
referenced paper:

1. Augmented baseline catalog (literature pull + Pareto merge)
2. Strict-domination comparator at calibrated `float64` tolerances
3. Recompute-derived-ratios-from-raw
4. Wilson 95 % CIs on small-sample rates
5. Honest-negatives enforcement (`Failure Modes` section required)
6. Re-runnable audit script generation (`audit_claims.py`)

This combination of mechanisms is, to our knowledge, the first in any
research-agent harness. It is the reason QuantumNovelty exists as a
standalone framework rather than a fork of either upstream.

## Code provenance log (per-file)

| File | Provenance | Modifications |
|---|---|---|
| `skills/common/llm.py` | New | Original; uses isolation patterns informed by both ARC's nested-claude lessons and the motivating study's session-collision findings |
| `skills/common/annas_archive.py` | Inspired by ARS's literature stage + the upstream Anna's Archive HTTP client conventions | Rewritten from stdlib only |
| `skills/novelty_audit/` | New | Original |
| `skills/audit_falsify/` | New | Original |
| `skills/literature_surfacer/` | ARS pattern | Multi-source pull + book_acquirer hook; LLM backend swapped to `skills/common/llm.py` |
| `skills/book_acquirer/` | New | Original |
| `skills/pareto_explorer/` | Concept from the motivating study (paper in development) | Scaffolded; real implementation deferred to a follow-up commit |
| `skills/ablation_designer/` | Concept from the motivating study (paper in development) | Scaffolded |
| `skills/cross_llm_prediction/` | Concept from the motivating study (paper in development) | Scaffolded |
| `chain/run.sh` | New | Original; pattern informed by ARS chain composition |

## What we did NOT take from upstream

- **No RAG.** ARC has a RAG layer; we deliberately omit it. Literature is
  fetched fresh per query.
- **No central manifest.** ARC has a registry.json; we use filesystem walk.
- **No ARC heartbeat/sentinel pattern.** Useful but adds complexity; deferred.

## Citations

If you build on QuantumNovelty please cite this repository (a citable paper is in development and will be linked here when released); it
introduced the audit-and-falsify framework (see root README). If you also
want to acknowledge the upstreams, citation entries for ARC and ARS are in
the root README.
