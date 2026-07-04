# Feature Import Candidates: Hermes / ARC / ARS → QuantumNovelty

Date: 2026-07-02. Sources surveyed: `ScienceSkills/novelty/hermes-agent`,
`ScienceSkills/novelty/AutoResearchClaw` (ARC), and
`ScienceSkills/novelty/academic-research-skills` (ARS). QuantumNovelty already
inherits ARC-style checkpoint/resume, telemetry (`chain/common/telemetry.py`),
mid-entry pipelines, and the multi-voice reviewer, so this list covers only
features it does not have, matched against its measured gaps.

## Tier 1 — fixes a real failure mode (import first)

1. **Retry + provider fallback for LLM calls** (Hermes) — **DONE 2026-07-02**:
   `call_llm()` now retries transient errors with backoff and supports
   strictly opt-in fallback chains (`QN_LLM_FALLBACKS`), with every attempt
   recorded in `_backend_used.json` for the audit gate. See
   `tests/test_llm_resilience.py`.
   - Source: `hermes-agent/agent/credential_pool.py` (key rotation, error
     detection) and the `fallback_model` parameter on `AIAgent`.
   - Gap fixed: `skills/common/llm.py` has no retry, no backoff, no fallback;
     one transient CLI error fails a whole pipeline stage.
   - Landing: wrap `call_llm()` with bounded retry + ordered backend fallback
     (claude → kimi → codex), preserving the `backend_actually_used` field the
     `LLMResult` dataclass already carries.

2. **Checkpointed parallel batch runner** (Hermes)
   - Source: `hermes-agent/batch_runner.py` (multiprocessing, per-prompt
     retry, `checkpoint.json`, `--resume`).
   - Gap fixed: stages run strictly sequentially; independent work (reviewer
     voices, per-paper literature pulls, cross-LLM branches) is serialized.
   - Landing: a `chain/common/parallel.py` used by `quantum_reviewer` (run the
     5 voices concurrently) and `deep_research` (parallel paper retrieval).

3. **Experiment evidence tracking + claim/evidence cross-check** (ARC)
   - Source: `researchclaw/` `experiment_schema`, `experiment_diagnosis`,
     `experiment_repair`, `paper_verifier`/`claim_verifier`.
   - Gap fixed: the biggest scientific one — `pareto_explorer` reasons about
     circuit results via LLM prompting instead of executing anything, and no
     module verifies that drafted claims trace back to recorded evidence.
     `evidence_ledger` records claims but nothing diagnoses or repairs a
     failed experiment, and nothing enforces claim↔artifact alignment.
   - Landing: adopt ARC's experiment schema as the contract between
     `pareto_explorer` and `novelty_audit`; add a claim-verifier pass before
     `04-draft` completes.

4. **Reviewer calibration mode (FNR/FPR/AUC)** (ARS) — **DONE 2026-07-02**:
   `skills/quantum_reviewer/calibrate.py` runs the full panel over a labeled
   gold set and computes FNR/FPR/accuracy/AUC deterministically from the
   per-paper `_quality_gate.json`. (Correction to the survey below: a
   prompt-driven `--mode calibration` already existed; what was missing and
   is now added is the code-emitted metrics harness.)
   - Source: `academic-research-skills/MODE_REGISTRY.md` +
     `skills/academic-paper-reviewer.md` (`calibration` mode).
   - Gap fixed: QuantumNovelty's verdicts (5-voice referee, 6-voice USPTO
     panel, Wilson-ratio novelty gate) are never validated against papers
     with known ground truth, so their error rates are unknown.
   - Landing: a `calibration` mode on `quantum_reviewer` and
     `patent_reviewer` fed by a small labeled corpus (accepted/rejected or
     granted/rejected cases); report FNR/FPR before trusting panel output.

## Tier 2 — high value, moderate effort

5. **Cross-run memory stores** (ARC)
   - Source: `researchclaw/memory/` (`store.py`, `retriever.py`, `decay.py`,
     `embeddings.py`, plus ideation/experiment/writing stores).
   - Gap fixed: every run starts cold; prior novelty audits, baseline-catalog
     lessons, and reviewer feedback are not reusable.
   - Landing: persist per-category memories under a shared
     `~/.quantumnovelty/memory/`, retrieved at stage start.

6. **Budget guard + watchdog** (ARC)
   - Source: `researchclaw` `cost_guard` (time/token budgets,
     `time_budget_sec`) and `sentinel.sh`.
   - Gap fixed: cost is tracked post-hoc only (`total_cost_usd`); no cap can
     stop a runaway pipeline, and non-Claude token counts fall back to a
     chars/4 proxy.
   - Landing: budget check inside `call_llm()` + a sentinel wrapper for
     `chain/pipelines.py` long runs.

7. **Typed stage contracts** (ARS)
   - Source: `academic-research-skills/shared/contracts/` (JSON Schemas per
     role: reviewer, audit, evaluator, submission, writer).
   - Gap fixed: stages hand each other unvalidated markdown/JSON; a malformed
     stage output surfaces as a confusing downstream LLM failure.
   - Landing: schema-validate each stage's output in `_run_skill()` before
     the next stage starts; reuse ARS reviewer/audit schemas nearly as-is.

8. **Per-task auxiliary model overrides** (Hermes)
   - Source: `hermes-agent/agent/auxiliary_client.py`.
   - Gap fixed: every skill uses the same backend; cheap tasks (scoring,
     summaries, title generation) burn the expensive model.
   - Landing: optional `model=` per stage in `chain/pipelines.py` config,
     mapped through `call_llm()`.

## Tier 3 — hygiene and leverage (import opportunistically)

9. **Skill eval harness + freshness CI** (ARS): `evals/` per-skill test cases
   plus `.github/workflows/eval-harness.yml` / `freshness-check.yml`; gives
   QuantumNovelty regression coverage over prompt changes.
10. **Central prompt registry with user overrides** (ARC):
    `prompts.default.yaml` + `--custom-file` adapter pattern; today QN prompts
    are embedded per-skill.
11. **ACP persistent sessions across stages** (Hermes/ARC):
    `agent/copilot_acp_client.py` and ARC's `acp_client.py`; keeps one agent
    context alive across the stage chain instead of cold CLI one-shots
    (ScienceSkills' `lib.sh` already adopted this via `acpx`).
12. **Lazy dependency installer** (Hermes): `tools/lazy_deps.py`; heavy deps
    (embeddings, patent OCR) install on first use.
13. **Path-security + write-approval gates** (Hermes):
    `tools/path_security.py`, `tools/write_approval.py`; sensible before QN
    skills are ever exposed to untrusted PDFs/patent inputs.
14. **Toolset distributions for datagen** (Hermes):
    `toolset_distributions.py`; only relevant if QN ever generates training
    trajectories from its runs.

## Explicitly not worth importing

- Hermes TUI/REPL and skills-hub curator daemon (QN is a batch pipeline, not
  an interactive assistant).
- ARC publisher/subscriber collaboration bus (single-user pipelines; the
  filesystem artifact tree already serves this role).
- Hermes SQLite session resume (QN's outdir-based checkpointing covers the
  same need at pipeline granularity).
