#!/usr/bin/env bash
# QuantumNovelty chain dispatcher.
#
# Composes the skill catalog into named pipelines. Auto-discovers skills
# under ../skills/*/run.sh (--list-skills); per-stage control is via the
# --skip-<stage> / --with-<stage> toggles.
#
# Backends: claude (default), codex, codex-acp, codex-mcp, anthropic-api.
# Backend isolation enforced by skills/common/llm.py (scrubbed env, neutral
# cwd, --no-session-persistence on claude). Codex-fallback is OFF by default
# — silent backend swaps are not allowed in this framework.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SKILLS_DIR="$ROOT/skills"

# ---- Telemetry plumbing (AutoResearchClaw pattern) ----------------------
# heartbeat.sh: start_heartbeat / stop_heartbeat / run_with_heartbeat /
#               audit_heartbeats
# stage_telemetry.sh: stage_health_begin / stage_health_end / decision_log /
#                     checkpoint_write / pause_after_stage / pipeline_summary
# Implements ARC's stage_health / heartbeat / checkpoint pattern.
# shellcheck disable=SC1091
source "$HERE/common/heartbeat.sh"
# shellcheck disable=SC1091
source "$HERE/common/stage_telemetry.sh"

# Strict-env defaults — disable silent claude->codex fallback,
# disable invoke_llm fallback. Pass --with-codex-fallback to override.
export CLAUDE_DISABLE_CODEX_FALLBACK="${CLAUDE_DISABLE_CODEX_FALLBACK:-1}"
export INVOKE_LLM_NO_FALLBACK="${INVOKE_LLM_NO_FALLBACK:-1}"

CHAIN_START_TS="$(date +%Y%m%d_%H%M%S)"

# Defaults
PIPELINE=""
LLM="claude"
OUTDIR=""
FORCE=false
# Pipeline-specific
PAPER=""
PATENT=""
ART_UNIT=""
TOPIC=""
HAMILTONIAN=""
BASELINE=""
GENERATIONS=4
SAMPLES=4
EVALUATOR_CMD=""
PLAN_ONLY=false
PARETO_ARCHIVE=""
AUGMENTED_BASELINES=""
GEOMETRY_SWEEP=""
LLMS=""
VENUE=""

# Per-stage toggles for paper-audit; collected during arg-parse
# and passed through to pipelines.py.
STAGE_TOGGLES=()

# Backend-policy env (off by default; never silently fall back).
export QN_DISABLE_BACKEND_FALLBACK="${QN_DISABLE_BACKEND_FALLBACK:-1}"

usage() {
  cat <<EOF
QuantumNovelty chain dispatcher.

Usage:
  $(basename "$0") --pipeline PIPELINE [OPTIONS]
  $(basename "$0") --list-skills

Pipelines:
  literature        Multi-source literature surface + baseline catalog
  pareto-discover   LLM-in-loop ansatz discovery + Pareto archive
  novelty-audit     Audit-and-falsify framework (the marquee skill)
  cross-llm         Cross-LLM falsifiable amplitude prediction
  draft-paper       Compose results into a manuscript draft
  full              literature -> pareto-discover (-> cross-llm when
                    --llms + --geometry-sweep are given). novelty-audit and
                    draft-paper run separately once you've inspected the
                    Pareto archive. (full-pipeline = the python
                    orchestrator's 6-stage variant.)
  paper-audit       Audit-only chain for an existing paper. Default-on stages:
                    research -> reviewer -> fallacies -> cqe. Opt-in extras
                    (novelty-audit, cross-llm) via --with-X when their inputs
                    are also passed. Used by examples/end_to_end/two_paper_novelty.
  patent-audit      USPTO examiner panel for a quantum patent. Input via
                    --patent URL|NUMBER|FILE (Google Patents). Default-on
                    stages: prior-art -> examiner (6-voice §§101/102/103/112
                    Office Action) -> fallacies -> cqe. Emits
                    02_examiner_panel/_office_action.json.
  chat              Natural-language frontend: describe what you want in
                    --prompt "STR" (optionally with --paper PATH) and the
                    chat skill plans the matching pipeline. Add --execute
                    to run the plan instead of just printing it.
  quantum-paper     Author a paper draft (--mode full/plan/outline-only/...).
  quantum-reviewer  Peer-review panel on an existing --paper (--mode full).
  fallacies         Logical-fallacy scan of an existing --paper.
  deep-research     Quantum-aware research memo (--topic or --paper).

Paper-audit stage toggles:
  --skip-research          Drop deep_research --mode review
  --skip-reviewer          Drop quantum_reviewer --mode full (5-voice panel)
  --skip-fallacies         Drop logical_fallacies (11 quantum-CS + standard)
  --skip-cqe               Drop process_summary (6-dim Stage-6 CQE)
  --with-novelty-audit     Add novelty_audit; requires --pareto-archive PATH
  --with-cross-llm         Add cross_llm_prediction; requires --hamiltonian +
                           --geometry-sweep + --llms
  --with-argument-structure  Add argument-architecture audit (premises ->
                           claims -> conclusion map, CME balance, debts)
  --with-requirements-judge  Add claim-vs-evidence audit: does the paper's
                           own evidence support its central claims? Emits an
                           allowed/forbidden-claims manifest + verdict
                           (the hypothesis-level companion to claims-registry)
  --with-evidence-ledger   Add the reviewer-hallucination guard: a
                           deterministic two-pass gate that pre-registers
                           the paper's facts (cite keys / numerics / quotes)
                           then audits the reviews for claims, quotes, or
                           numbers attributed to the paper that it never made
  --skip-claims-registry   Drop the DEFAULT-ON numeric-claim registry gate
                           (abstract-vs-results fabrication catcher; no LLM)
  --bib PATH               Arms the citation-integrity gate automatically
                           (4-layer: bibkey / completeness / CrossRef DOI /
                           relevance; no LLM, no RAG). Disable with
                           --skip-citation-integrity.
  --with-disclosure-audit  Add funding / COI / ethics / availability audit
  --with-revision-planner  Add paragraph-anchored revision roadmap
                           (every item: ¶NNN anchor + verbatim judge
                           evidence + proposed edit)
  --pause-after STAGE      Write checkpoint + exit after STAGE completes
  --resume-from STAGE      Treat earlier stages as complete; pick up at STAGE
  --list-stages            Print stage table for every pipeline; exit
  --no-llm-narrative       Disable LLM-narrative pass in process_summary

Common:
  --llm MODEL              Backend: claude (default), codex, codex-acp,
                           codex-mcp, anthropic-api
  --outdir DIR             Output root for this run
  --list-skills            Print discovered skills, then exit
  --force                  Re-run stages even if outputs exist
  --help, -h               This help

Pipeline-specific:
  literature:
    --topic "STR"          Required. Research question to surface literature for.
    --hamiltonian ID       Optional. Filter to literature relevant to this Hamiltonian.

  pareto-discover:
    --hamiltonian ID       Required. The Hamiltonian to optimise against.
    --baseline LIST        Required. Comma-separated baseline labels to seed
                           the Pareto archive (e.g. UCCSD-1-Trotter,HEA-5L).
    --generations N        Default 4.
    --samples N            Default 4 (proposals per generation).

  novelty-audit:
    --pareto-archive PATH       Required.
    --augmented-baselines PATH  Required (from literature pipeline output).
    --paper PATH                Required. The draft manuscript.

  cross-llm:
    --hamiltonian ID            Required.
    --geometry-sweep "STR"      Required. e.g. "R_OH=0.7,0.96,1.2,1.5,2.0 A".
    --llms LIST                 Required. Comma list, e.g. "claude,codex".

  draft-paper:
    --pareto-archive PATH       Required.
    --xllm PATH                 Optional. cross_llm_prediction output.
    --venue STR                 Default: "generic peer-reviewed journal".
EOF
}

list_skills() {
  echo "Discovered skills under $SKILLS_DIR:"
  echo
  for d in "$SKILLS_DIR"/*/; do
    name=$(basename "$d")
    [[ "$name" == "common" ]] && continue
    [[ -x "$d/run.sh" ]] || { echo "  $name  (no run.sh; skipping)"; continue; }
    desc=""
    if [[ -f "$d/SKILL.md" ]]; then
      desc=$(grep -m1 '^# ' "$d/SKILL.md" | sed 's/^# //')
    fi
    printf "  %-22s %s\n" "$name" "$desc"
  done
}

# --------- arg parsing ----------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pipeline) PIPELINE="$2"; shift 2 ;;
    --llm)      LLM="$2"; shift 2 ;;
    --outdir)   OUTDIR="$2"; shift 2 ;;
    --enable|--disable|--stages)
      echo "Error: $1 was never implemented — use the per-stage" >&2
      echo "       --skip-<stage> / --with-<stage> toggles instead" >&2
      exit 2 ;;
    --list-skills) list_skills; exit 0 ;;
    --force)    FORCE=true; shift ;;
    --paper)    PAPER="$2"; shift 2 ;;
    --patent|--patent-url) PATENT="$2"; shift 2 ;;
    --art-unit) ART_UNIT="$2"; shift 2 ;;
    --topic)    TOPIC="$2"; shift 2 ;;
    --hamiltonian) HAMILTONIAN="$2"; shift 2 ;;
    --baseline) BASELINE="$2"; shift 2 ;;
    --generations) GENERATIONS="$2"; shift 2 ;;
    --evaluator-cmd) EVALUATOR_CMD="$2"; shift 2 ;;
    --plan-only) PLAN_ONLY=true; shift ;;
    --samples)  SAMPLES="$2"; shift 2 ;;
    --pareto-archive) PARETO_ARCHIVE="$2"; shift 2 ;;
    --augmented-baselines) AUGMENTED_BASELINES="$2"; shift 2 ;;
    --geometry-sweep) GEOMETRY_SWEEP="$2"; shift 2 ;;
    --llms)     LLMS="$2"; shift 2 ;;
    --venue)    VENUE="$2"; shift 2 ;;
    --xllm)     XLLM="$2"; shift 2 ;;
    --journal)  JOURNAL="$2"; shift 2 ;;
    --quantum-lib) QUANTUM_LIB="$2"; shift 2 ;;
    --mode)     MODE="$2"; shift 2 ;;
    --reviewer-comments) REVIEWER_COMMENTS="$2"; shift 2 ;;
    --prompt)   PROMPT="$2"; shift 2 ;;
    --execute)  EXECUTE=true; shift ;;
    # Per-stage toggles for paper-audit. Collected here and
    # passed through to pipelines.py verbatim.
    --skip-research|--skip-reviewer|--skip-fallacies|--skip-cqe) \
      STAGE_TOGGLES+=("$1"); shift ;;
    --skip-prior-art|--skip-examiner) \
      STAGE_TOGGLES+=("$1"); shift ;;
    --with-novelty-audit|--with-cross-llm|--with-synthesizer) \
      STAGE_TOGGLES+=("$1"); shift ;;
    --with-argument-structure|--with-claims-registry|--with-citation-integrity) \
      STAGE_TOGGLES+=("$1"); shift ;;
    --with-disclosure-audit|--with-revision-planner) \
      STAGE_TOGGLES+=("$1"); shift ;;
    --with-requirements-judge|--with-evidence-ledger) \
      STAGE_TOGGLES+=("$1"); shift ;;
    --skip-claims-registry|--skip-citation-integrity) \
      STAGE_TOGGLES+=("$1"); shift ;;
    --bib) STAGE_TOGGLES+=("$1" "$2"); shift 2 ;;
    --with-cross-model|--with-codex-fallback|--with-arc-*) \
      STAGE_TOGGLES+=("$1"); shift ;;
    --hitl-pause-after) STAGE_TOGGLES+=("$1" "$2"); shift 2 ;;
    --no-llm-narrative) STAGE_TOGGLES+=("$1"); shift ;;
    --pause-after) STAGE_TOGGLES+=("$1" "$2"); shift 2 ;;
    --resume-from) STAGE_TOGGLES+=("$1" "$2"); shift 2 ;;
    --list-stages) exec python3 "$HERE/pipelines.py" list-stages --outdir /tmp/_qn_stage_list ;;
    -h|--help)  usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

# Defaults for new flags
: "${JOURNAL:=}"
: "${QUANTUM_LIB:=}"
: "${MODE:=}"
: "${REVIEWER_COMMENTS:=}"
: "${PROMPT:=}"
: "${EXECUTE:=false}"
COMMON_FLAGS=()
[[ -n "$JOURNAL" ]]     && COMMON_FLAGS+=(--journal "$JOURNAL")
[[ -n "$QUANTUM_LIB" ]] && COMMON_FLAGS+=(--quantum-lib "$QUANTUM_LIB")

[[ -n "$PIPELINE" ]] || { echo "Error: --pipeline required" >&2; exit 2; }
if [[ "$PIPELINE" == "status" && -z "$OUTDIR" ]]; then
  echo "Error: --pipeline status requires --outdir (the run to inspect)" >&2
  exit 2
fi

# Outdir auto-derivation.
# Layout: runs/<YYYYMMDD_HHMMSS>/<llm_slug>/<pipeline>/
#   - timestamp = run start (one timestamp per chain invocation; all stages share it)
#   - llm_slug  = backend ID, slug-safe (e.g. claude → claude;
#                 claude-sonnet-4-20250514 → claude-sonnet-4-20250514;
#                 codex-acp → codex-acp). Surfaces which backend a run was on
#                 even before you read the per-stage _backend_used.json marker.
#   - pipeline  = the --pipeline value (literature / chat / full-pipeline / ...)
# Override the whole path with --outdir DIR.
if [[ -z "$OUTDIR" ]]; then
  ts=$(date +%Y%m%d_%H%M%S)
  # Slug-normalize: keep alnums, dots, dashes, underscores; replace everything else.
  llm_slug=$(printf '%s' "$LLM" | sed 's|[^A-Za-z0-9._-]|_|g')
  OUTDIR="$ROOT/runs/${ts}/${llm_slug}/${PIPELINE}"
fi
mkdir -p "$OUTDIR"
OUTDIR="$(cd "$OUTDIR" && pwd)"

echo "==============================================================="
echo "QuantumNovelty chain"
echo "  Pipeline : $PIPELINE"
echo "  Backend  : $LLM"
echo "  Outdir   : $OUTDIR"
echo "==============================================================="

# --------- pipeline dispatch ---------------------------------------------
run_skill() {
  local name="$1"; shift
  local stage_dir="$OUTDIR/$name"
  mkdir -p "$stage_dir"
  local skill="$SKILLS_DIR/$name/run.sh"
  if [[ ! -x "$skill" ]]; then
    echo "[chain] WARNING: skill '$name' not found at $skill; skipping" >&2
    return 0
  fi
  echo "[chain] >> $name"
  "$skill" --outdir "$stage_dir" --llm "$LLM" "$@"
}

case "$PIPELINE" in
  literature)
    [[ -n "$TOPIC" ]] || { echo "Error: --topic required" >&2; exit 2; }
    run_skill literature_surfacer --topic "$TOPIC"
    ;;
  pareto-discover)
    [[ -n "$HAMILTONIAN" && -n "$BASELINE" ]] || \
      { echo "Error: --hamiltonian and --baseline required" >&2; exit 2; }
    PE_ARGS=(--hamiltonian "$HAMILTONIAN" --baseline "$BASELINE"
             --generations "$GENERATIONS" --samples "$SAMPLES")
    [[ -n "$EVALUATOR_CMD" ]] && PE_ARGS+=(--evaluator-cmd "$EVALUATOR_CMD")
    $PLAN_ONLY && PE_ARGS+=(--plan-only)
    run_skill pareto_explorer "${PE_ARGS[@]}"
    ;;
  novelty-audit)
    [[ -n "$PARETO_ARCHIVE" && -n "$PAPER" ]] || \
      { echo "Error: --pareto-archive and --paper required" >&2; exit 2; }
    run_skill novelty_audit \
      --pareto-archive "$PARETO_ARCHIVE" \
      ${AUGMENTED_BASELINES:+--augmented-baselines "$AUGMENTED_BASELINES"} \
      --draft "$PAPER" \
      ${HAMILTONIAN:+--hamiltonian-id "$HAMILTONIAN"}
    ;;
  cross-llm)
    [[ -n "$HAMILTONIAN" && -n "$GEOMETRY_SWEEP" && -n "$LLMS" ]] || \
      { echo "Error: --hamiltonian, --geometry-sweep, --llms required" >&2; exit 2; }
    run_skill cross_llm_prediction \
      --hamiltonian "$HAMILTONIAN" \
      --geometry-sweep "$GEOMETRY_SWEEP" \
      --llms "$LLMS"
    ;;
  # ---- multi-mode skill pipelines (new) ----
  deep-research)
    [[ -n "$TOPIC" && -n "$MODE" ]] || \
      { echo "Error: --topic and --mode required for deep-research" >&2; exit 2; }
    run_skill deep_research --mode "$MODE" --topic "$TOPIC" \
      "${COMMON_FLAGS[@]+"${COMMON_FLAGS[@]}"}"
    ;;
  quantum-paper)
    [[ -n "$MODE" ]] || { echo "Error: --mode required for quantum-paper" >&2; exit 2; }
    QP_ARGS=(--mode "$MODE")
    [[ -n "$TOPIC" ]] && QP_ARGS+=(--topic "$TOPIC")
    [[ -n "$PAPER" ]] && QP_ARGS+=(--draft "$PAPER")
    [[ -n "$REVIEWER_COMMENTS" ]] && QP_ARGS+=(--reviewer-comments "$REVIEWER_COMMENTS")
    run_skill quantum_paper "${QP_ARGS[@]}" "${COMMON_FLAGS[@]+"${COMMON_FLAGS[@]}"}"
    ;;
  quantum-reviewer)
    [[ -n "$MODE" && -n "$PAPER" ]] || \
      { echo "Error: --mode and --paper required for quantum-reviewer" >&2; exit 2; }
    run_skill quantum_reviewer --mode "$MODE" --draft "$PAPER" \
      "${COMMON_FLAGS[@]+"${COMMON_FLAGS[@]}"}"
    ;;
  fallacies)
    [[ -n "$PAPER" ]] || { echo "Error: --paper required for fallacies" >&2; exit 2; }
    run_skill logical_fallacies --draft "$PAPER"
    ;;
  chat)
    [[ -n "$PROMPT" ]] || { echo "Error: --prompt required for chat" >&2; exit 2; }
    CHAT_ARGS=(--prompt "$PROMPT")
    [[ -n "$PAPER" ]] && CHAT_ARGS+=(--paper "$PAPER")
    [[ "$EXECUTE" == true ]] && CHAT_ARGS+=(--execute)
    run_skill chat "${CHAT_ARGS[@]}" "${COMMON_FLAGS[@]+"${COMMON_FLAGS[@]}"}"
    ;;
  process-summary)
    run_skill process_summary --run-dir "$OUTDIR/.."
    ;;
  # ---- multi-stage pipeline orchestrator (new) ----
  full-pipeline|mid-entry-stage-2.5|mid-entry-stage-4|paper-audit|patent-audit|status)
    PIPE_NAME="$PIPELINE"
    [[ "$PIPE_NAME" == "full-pipeline" ]] && PIPE_NAME="full"
    if [[ "$PIPE_NAME" == "patent-audit" && -z "$PATENT" ]]; then
      echo "Error: --pipeline patent-audit requires --patent SOURCE" >&2
      echo "       (Google Patents URL, publication number, or saved file)" >&2
      exit 2
    fi
    PIPE_ARGS=("$PIPE_NAME" --outdir "$OUTDIR" --llm "$LLM")
    [[ -n "$TOPIC" ]]              && PIPE_ARGS+=(--topic "$TOPIC")
    [[ -n "$PAPER" ]]              && PIPE_ARGS+=(--paper "$PAPER")
    [[ -n "$PATENT" ]]            && PIPE_ARGS+=(--patent "$PATENT")
    [[ -n "$ART_UNIT" ]]          && PIPE_ARGS+=(--art-unit "$ART_UNIT")
    [[ -n "$REVIEWER_COMMENTS" ]]  && PIPE_ARGS+=(--reviewer-comments "$REVIEWER_COMMENTS")
    [[ -n "$HAMILTONIAN" ]]        && PIPE_ARGS+=(--hamiltonian "$HAMILTONIAN")
    [[ -n "$BASELINE" ]]           && PIPE_ARGS+=(--baseline "$BASELINE")
    [[ -n "$GEOMETRY_SWEEP" ]]     && PIPE_ARGS+=(--geometry-sweep "$GEOMETRY_SWEEP")
    [[ -n "$LLMS" ]]               && PIPE_ARGS+=(--llms "$LLMS")
    [[ -n "$JOURNAL" ]]            && PIPE_ARGS+=(--journal "$JOURNAL")
    [[ -n "$QUANTUM_LIB" ]]        && PIPE_ARGS+=(--quantum-lib "$QUANTUM_LIB")
    [[ -n "$PARETO_ARCHIVE" ]]     && PIPE_ARGS+=(--pareto-archive "$PARETO_ARCHIVE")
    [[ -n "$AUGMENTED_BASELINES" ]] && PIPE_ARGS+=(--augmented-baselines "$AUGMENTED_BASELINES")
    $FORCE && PIPE_ARGS+=(--force)
    # Stage toggles, verbatim.
    if [[ ${#STAGE_TOGGLES[@]} -gt 0 ]]; then
      PIPE_ARGS+=("${STAGE_TOGGLES[@]}")
    fi
    exec python3 "$HERE/pipelines.py" "${PIPE_ARGS[@]}"
    ;;
  draft-paper)
    [[ -n "$PARETO_ARCHIVE" ]] || \
      { echo "Error: --pareto-archive required" >&2; exit 2; }
    run_skill paper_drafter \
      --pareto-archive "$PARETO_ARCHIVE" \
      ${XLLM:+--xllm "$XLLM"} \
      ${VENUE:+--venue "$VENUE"}
    ;;
  full)
    [[ -n "$TOPIC" && -n "$HAMILTONIAN" && -n "$BASELINE" ]] || \
      { echo "Error: --topic, --hamiltonian, --baseline required for full" >&2; exit 2; }
    run_skill literature_surfacer --topic "$TOPIC"
    PE_ARGS=(--hamiltonian "$HAMILTONIAN" --baseline "$BASELINE"
             --generations "$GENERATIONS" --samples "$SAMPLES")
    [[ -n "$EVALUATOR_CMD" ]] && PE_ARGS+=(--evaluator-cmd "$EVALUATOR_CMD")
    $PLAN_ONLY && PE_ARGS+=(--plan-only)
    run_skill pareto_explorer "${PE_ARGS[@]}"
    [[ -n "$LLMS" && -n "$GEOMETRY_SWEEP" ]] && run_skill cross_llm_prediction \
      --hamiltonian "$HAMILTONIAN" \
      --geometry-sweep "$GEOMETRY_SWEEP" \
      --llms "$LLMS"
    # novelty-audit + draft-paper assumed run separately once the user inspects
    # the Pareto archive.
    ;;
  *) echo "Unknown pipeline: $PIPELINE" >&2; usage; exit 2 ;;
esac

echo
echo "[chain] pipeline '$PIPELINE' complete; outputs in $OUTDIR"
