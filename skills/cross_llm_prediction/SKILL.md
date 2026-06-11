# `cross_llm_prediction` — falsifiable amplitude-prediction rubric

Runs the same prediction prompt through N different-vendor LLMs (e.g. claude
+ codex), with predictions made BEFORE truth is computed, and a structured
rubric (top-K amplitude indices + ordering) that can be scored against truth.

**Inputs:** `--hamiltonian ID`, `--geometry-sweep "STR"`, `--llms LIST`
  (e.g. `claude,codex`), `--k INT` (default 5)
**Outputs:** per-LLM prediction JSON, `results.json` with predicted-vs-truth
  overlap, `cross_llm_summary.md`

**Falsifiability constraints (enforced by the skill, not by prompt discipline):**
1. LLMs MUST be from different vendors. Two anthropic-snapshot calls do not
   count as cross-LLM.
2. Predictions are made and persisted before truth is computed.
3. The rubric is specific and quantitative (amplitude indices, not prose).
4. Truth is computed by an independent classical solver (FCI / VQE@truth), not
   by another LLM.

When the prompt asks for "your best guess at the top-5 amplitudes for H2O at
R=1.5 Å", the LLM cannot see the FCI answer; the post-hoc scoring is the test
of whether the LLM picked up on real quantum-chemistry structure or
hallucinated plausibly.
