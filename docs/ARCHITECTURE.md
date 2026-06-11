# QuantumNovelty Architecture

## One picture

```
                              chain/run.sh
                                   │
                  ┌────────────────┼─────────────────┐
                  ▼                ▼                 ▼
        literature_surfacer  pareto_explorer  cross_llm_prediction
                  │                │                 │
                  └────────────────┼─────────────────┘
                                   ▼
                     ┌─────── novelty_audit ───────┐  ← OUR CONTRIBUTION
                     │  (augmented baseline merge, │
                     │   strict-domination at      │
                     │   calibrated ε,             │
                     │   recompute-from-raw,       │
                     │   Wilson CIs,               │
                     │   honest-negatives,         │
                     │   audit_claims.py emit)     │
                     └─────────────┬───────────────┘
                                   ▼
                              paper_drafter
                                   │
                                   ▼
                     ┌─ ARC-style back-half gates ─┐  ← from ARC
                     │ citation_integrity          │
                     │ compilation_quality         │
                     │ paper_verification          │
                     │ quality_gate                │
                     │ research_decision           │
                     │ knowledge_archive           │
                     └─────────────────────────────┘
```

Skills are independent: each consumes structured JSON, produces structured
JSON. The chain composes them by name. Adding a new skill requires writing
its directory under `skills/`; the chain auto-discovers it.

## Data flow contract

Every skill writes its output to `--outdir`:
- `*.json` — structured outputs (the actual results, consumed by downstream stages)
- `*.md` — human-readable summary
- `_backend_used.json` — backend provenance (which LLM actually ran)
- `full_prompt_*.txt` — the prompt that was sent (when an LLM was called)
- `_llm_generation.log` — full LLM response (when an LLM was called)

A downstream stage reads exactly the `*.json` outputs it declared in its
SKILL.md. No implicit cross-stage state. This makes the chain resumable: re-run
with the same `--outdir` and any stage whose output exists is skipped.

## LLM backend layer

`skills/common/llm.py::call_llm()` is the single entry point. Every skill that
needs an LLM goes through it. The function:
1. Validates backend ∈ KNOWN_BACKENDS
2. Honors `QUANTUMNOVELTY_LLM_STUB` env (test seam — returns stub file contents)
3. Builds a scrubbed env removing `CLAUDE_CODE_*`, `ANTHROPIC_*`, `CLAUDECODE`
4. Spawns subprocess from a neutral cwd (`tempfile.gettempdir()`)
5. Routes to the backend-specific command builder
6. Returns `LLMResult(text, backend_requested, backend_actually_used, ...)`

Silent fallback (claude → codex on failure) is **disallowed by design**. If
the requested backend fails, the function raises `RuntimeError` and the
caller must explicitly decide whether to retry, degrade, or fail.

## Backend isolation policy

| Concern | How we defend |
|---|---|
| Nested `claude --print` 400 ("tool_use ids must be unique") | Scrub `CLAUDE_CODE_*` env + run from `tempfile.gettempdir()` + pass `--no-session-persistence` |
| Silent billing-against-API when ANTHROPIC_API_KEY is in scope | Scrub `ANTHROPIC_*` env on every claude/codex call (it survives only for `--llm anthropic-api`) |
| Codex `tool_use` collisions | `--skip-git-repo-check` plus prompt-on-stdin (avoids cwd-sensitive defaults) |
| Persistent-session collisions across stages | ACP backend uses per-PID session names unless caller supplies `acp_session` explicitly |

## Skill discovery

`chain/run.sh --list-skills` walks `skills/*/run.sh` and prints each as a
discovered skill. To add a skill:

```
skills/my_new_skill/
├── SKILL.md            (description; CLI surface; output schema)
├── run.sh              (bash entry; usually a thin wrapper over skill.py)
├── skill.py            (Python driver; uses skills/common/llm.py)
└── prompts/            (optional; prompt templates)
```

The chain dispatches a skill by invoking its `run.sh` with `--outdir DIR
--llm BACKEND <skill-specific flags>`.

## What's NOT in the architecture

- **No vector database.** Literature is fetched fresh per query through
  HTTP. If a query repeats, the literature_surfacer will hit CrossRef again.
  We accept the latency cost in exchange for not maintaining an index.
- **No central registry.** The chain discovers skills by directory walk; the
  registry is the filesystem. This is deliberate — adding a skill requires
  no chain edit.
- **No prompt templating engine.** Prompts are Python f-strings or `.format()`
  on a template file. We avoided Jinja / Handlebars / mustache to keep the
  dependency graph minimal.
- **No async/await machinery.** Every skill is synchronous subprocess
  composition. If you need concurrency, run multiple `chain/run.sh`
  invocations under `xargs -P` or GNU parallel.

## Open extensions

Roadmap items not yet implemented:
- MCP server (`skills/common/mcp_server.py`) — the codex-mcp backend is wired
  in `llm.py` but the server itself is a stub
- pareto_explorer larger registry — the built-in numpy evaluator covers
  TFIM/Heisenberg (2-10 qubits) + the 2-qubit tapered H2; molecular
  Hamiltonians beyond that still need an external `--evaluator-cmd`
- chain CLI Python entry point (`chain.cli:main` in pyproject.toml) — the
  bash dispatcher is canonical; a Python wrapper is planned for `qn-chain`
