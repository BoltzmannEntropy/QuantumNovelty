#!/usr/bin/env bash
# Stage telemetry for QuantumNovelty workflow chains.
#
# Adopted 2026-05-23 from AutoResearchClaw's stage_health / pipeline_summary /
# decision_history pattern. Provides four shell helpers that any chain can
# source to emit ARC-compatible structured telemetry alongside the existing
# heartbeat / backend-fidelity / chain-stage logs.
#
#   stage_health_begin   <stage_dir> <stage_id>
#       Records start timestamp + stage_id in a stage-local _stage_health.tmp.
#
#   stage_health_end     <stage_dir> [status] [error]
#       Writes the final _stage_health.json. status defaults to "done";
#       error is optional. Computes duration_sec from begin marker, counts
#       artifacts under stage_dir.
#
#   decision_log         <run_dir> <decision> [target] [stage_num] [attempt]
#       Appends one decision entry to <run_dir>/decision_history.json. The
#       file is created if absent. decision is one of: proceed | refine |
#       pivot | pause | block | fail.
#
#   pipeline_summary     <run_dir>
#       Walks every stage-NN / *_NN_* / NN_* subdir under run_dir, aggregates
#       stage_health.json files, and writes a top-level pipeline_summary.json
#       capturing stages_done / paused / blocked / failed / degraded + final
#       status. Idempotent; safe to call multiple times.
#
# Source it once at the top of run.sh, then bracket each stage with
#   stage_health_begin "$stage_dir" "01-falsificationist"
#   ...
#   stage_health_end "$stage_dir" "done"
# and end the run with `pipeline_summary "$OUTDIR"`.

stage_health_begin() {
  local stage_dir="$1"
  local stage_id="${2:-unknown}"
  [[ -n "$stage_dir" ]] || { echo "[telemetry] stage_health_begin: missing stage_dir" >&2; return 1; }
  mkdir -p "$stage_dir"
  local now_iso
  now_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local now_epoch
  now_epoch="$(date +%s)"
  {
    echo "stage_id=$stage_id"
    echo "started_iso=$now_iso"
    echo "started_epoch=$now_epoch"
  } > "$stage_dir/_stage_health.tmp"
}

stage_health_end() {
  local stage_dir="$1"
  local stage_status="${2:-done}"
  local error="${3:-}"
  [[ -d "$stage_dir" ]] || return 1

  local stage_id=""
  local started_iso=""
  local started_epoch=0
  if [[ -f "$stage_dir/_stage_health.tmp" ]]; then
    stage_id="$(grep -E '^stage_id=' "$stage_dir/_stage_health.tmp" | cut -d= -f2- || echo "")"
    started_iso="$(grep -E '^started_iso=' "$stage_dir/_stage_health.tmp" | cut -d= -f2- || echo "")"
    started_epoch="$(grep -E '^started_epoch=' "$stage_dir/_stage_health.tmp" | cut -d= -f2- || echo 0)"
  fi
  local now_epoch
  now_epoch="$(date +%s)"
  local now_iso
  now_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local duration_sec=0
  if [[ "$started_epoch" -gt 0 ]]; then
    duration_sec=$((now_epoch - started_epoch))
  fi
  # Count artifacts (excluding telemetry / heartbeat / log scaffolding).
  local artifacts_count
  artifacts_count="$(find "$stage_dir" -maxdepth 3 -type f \
                     ! -name '_stage_health*' \
                     ! -name '_heartbeat*' \
                     ! -name '_exit' \
                     ! -name '_timed_out' \
                     ! -name '_backend_used.txt' \
                     ! -name '_chain_stage.log' 2>/dev/null | wc -l | tr -d ' ')"
  # JSON-escape error string (best effort, no newlines/quotes/backslashes).
  local err_escaped
  err_escaped="$(printf '%s' "$error" | tr -d '\n' | sed 's/\\/\\\\/g; s/"/\\"/g')"
  local err_field="null"
  [[ -n "$error" ]] && err_field="\"$err_escaped\""

  cat > "$stage_dir/_stage_health.json" <<EOF
{
  "stage_id": "$stage_id",
  "stage_dir": "$(basename "$stage_dir")",
  "duration_sec": $duration_sec,
  "status": "$stage_status",
  "artifacts_count": $artifacts_count,
  "error": $err_field,
  "started_iso": "$started_iso",
  "ended_iso": "$now_iso"
}
EOF
  rm -f "$stage_dir/_stage_health.tmp"
}

decision_log() {
  local run_dir="$1"
  local decision="$2"
  local target="${3:-}"
  local stage_num="${4:-0}"
  local attempt="${5:-1}"
  [[ -n "$run_dir" && -n "$decision" ]] || {
    echo "[telemetry] decision_log: usage: <run_dir> <decision> [target] [stage_num] [attempt]" >&2
    return 1
  }
  mkdir -p "$run_dir"
  local hist="$run_dir/decision_history.json"
  # Read existing history (initialise as [] if missing or invalid).
  local existing="[]"
  if [[ -s "$hist" ]]; then
    if python3 -c "import json,sys; json.load(open('$hist'))" >/dev/null 2>&1; then
      existing="$(cat "$hist")"
    fi
  fi
  # Append + rewrite via python for safety.
  python3 - <<PY
import json, sys
from datetime import datetime, timezone
hist_path = "$hist"
try:
    data = json.loads('''$existing''')
except Exception:
    data = []
entry = {
    "decision": "$decision",
    "rollback_target": "$target" or None,
    "rollback_stage_num": $stage_num,
    "attempt": $attempt,
    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
}
data.append(entry)
with open(hist_path, "w") as f:
    json.dump(data, f, indent=2)
PY
}

checkpoint_write() {
  # Write a resumable checkpoint marker after a stage completes. Used by
  # the HITL pause-after-stage flow: when a user wants to pause the chain
  # after a specific stage, we drop a checkpoint.json with the stage_id +
  # ISO timestamp + run-cwd + originally-invoked argv. The user can then
  # inspect, optionally edit artifacts, and resume.
  #
  # Adopted 2026-05-23 from AutoResearchClaw's checkpoint.json schema.
  #
  # Usage: checkpoint_write <run_dir> <stage_id> [next_stage_id] [argv...]
  local run_dir="$1"; shift
  local stage_id="$1"; shift
  local next_stage_id="${1:-}"; [[ -n "$next_stage_id" ]] && shift || true
  [[ -n "$run_dir" && -n "$stage_id" ]] || {
    echo "[hitl] checkpoint_write: usage: <run_dir> <stage_id> [next_stage_id] [argv...]" >&2
    return 1
  }
  mkdir -p "$run_dir"
  local now_iso
  now_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local argv_json="[]"
  if (( $# > 0 )); then
    argv_json="$(python3 -c "import json,sys; print(json.dumps(sys.argv[1:]))" "$@")"
  fi
  cat > "$run_dir/checkpoint.json" <<EOF
{
  "run_id": "$(basename "$run_dir")",
  "paused_after_stage": "$stage_id",
  "next_stage": $([[ -n "$next_stage_id" ]] && printf '"%s"' "$next_stage_id" || printf 'null'),
  "paused_at": "$now_iso",
  "cwd": "$(pwd)",
  "original_argv": $argv_json,
  "resume_hint": "Re-launch with --resume-from <next_stage>"
}
EOF
  echo "[hitl] checkpoint written: $run_dir/checkpoint.json (paused after $stage_id)"
}

pause_after_stage() {
  # If QN_HITL_PAUSE_AFTER matches the current stage_id, write a
  # checkpoint and exit 0. The chain stops cleanly; the user resumes by
  # passing --resume-from <stage> on the next invocation.
  #
  # Usage: pause_after_stage <run_dir> <current_stage_id> [next_stage_id]
  local run_dir="$1"
  local current="$2"
  local next_id="${3:-}"
  local target="${QN_HITL_PAUSE_AFTER:-}"
  if [[ -z "$target" ]]; then
    return 0
  fi
  # Match on substring so users can write "06" or "acquisitions" or full id.
  if [[ "$current" == *"$target"* ]]; then
    checkpoint_write "$run_dir" "$current" "$next_id"
    echo "[hitl] QN_HITL_PAUSE_AFTER=$target matched stage=$current — exiting cleanly."
    echo "[hitl] resume hint: --resume-from $next_id (or rerun without QN_HITL_PAUSE_AFTER)"
    exit 0
  fi
}

pipeline_summary() {
  local run_dir="$1"
  [[ -d "$run_dir" ]] || { echo "[telemetry] pipeline_summary: missing run_dir" >&2; return 1; }
  python3 - "$run_dir" <<'PY'
import json, os, sys, re
from datetime import datetime, timezone
from pathlib import Path

run_dir = Path(sys.argv[1])
healths = []
for sd in sorted(run_dir.rglob("_stage_health.json")):
    try:
        h = json.loads(sd.read_text())
        healths.append(h)
    except Exception:
        pass

# Aggregate counts by status.
counts = {"done": 0, "paused": 0, "blocked": 0, "failed": 0, "degraded": 0}
for h in healths:
    s = h.get("status", "unknown").lower()
    if s in counts:
        counts[s] += 1
    elif s in ("warn", "degraded"):
        counts["degraded"] += 1

# Find first / final stage by stage_dir lexicographic ordering.
sorted_by_dir = sorted(healths, key=lambda h: h.get("stage_dir", ""))
from_stage = 1
final_stage = len(healths)
final_status = "done"
if counts["failed"] > 0:
    final_status = "failed"
elif counts["blocked"] > 0:
    final_status = "blocked"
elif counts["paused"] > 0:
    final_status = "paused"

# Content metrics — read citation-integrity report if present.
content = {}
ver_paths = list(run_dir.rglob("verification_report.json"))
if ver_paths:
    try:
        v = json.loads(ver_paths[0].read_text())
        summary = v.get("summary", {})
        content = {
            "citation_verify_score": summary.get("integrity_score"),
            "total_citations": summary.get("total"),
            "verified_citations": summary.get("verified"),
            "degraded_sources": [r["cite_key"] for r in v.get("results", [])
                                  if r.get("status") not in ("verified", "skipped")],
        }
    except Exception:
        pass

# Quality-gate report?
quality_paths = list(run_dir.rglob("quality_report.json"))
if quality_paths:
    try:
        q = json.loads(quality_paths[0].read_text())
        content["quality_score"] = q.get("overall_score")
    except Exception:
        pass

summary = {
    "run_id": run_dir.name,
    "stages_executed": len(healths),
    "stages_done": counts["done"],
    "stages_paused": counts["paused"],
    "stages_blocked": counts["blocked"],
    "stages_failed": counts["failed"],
    "degraded": counts["degraded"] > 0,
    "from_stage": from_stage,
    "final_stage": final_stage,
    "final_status": final_status,
    "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    "content_metrics": content,
    "per_stage": [
        {
            "stage_id": h.get("stage_id"),
            "stage_dir": h.get("stage_dir"),
            "status": h.get("status"),
            "duration_sec": h.get("duration_sec"),
            "artifacts_count": h.get("artifacts_count"),
        } for h in sorted_by_dir
    ],
}
out = run_dir / "pipeline_summary.json"
out.write_text(json.dumps(summary, indent=2))
print(f"[telemetry] pipeline_summary: {len(healths)} stages → {out}")
PY
}
