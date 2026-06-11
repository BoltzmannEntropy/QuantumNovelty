#!/usr/bin/env bash
# Heartbeat + sentinel wrapper for QuantumNovelty workflow chains.
#
# Adapted from AutoResearchClaw's sentinel pattern (aiming-lab). Provides
# three shell helpers any chain can source:
#
#   start_heartbeat   <stage_dir> [interval_sec]
#       Spawns a background loop that writes timestamp + pid into
#       "$stage_dir/_heartbeat.txt" every $interval_sec seconds. Captures
#       the heartbeat PID in $HEARTBEAT_PID for stop_heartbeat to kill.
#
#   stop_heartbeat
#       Kills the background heartbeat loop (if any) recorded in
#       $HEARTBEAT_PID. Safe to call when no heartbeat is running.
#
#   run_with_heartbeat <stage_dir> <timeout_sec> <command...>
#       Runs <command> with a heartbeat writer + a hard timeout. If the
#       command exceeds the timeout, writes "$stage_dir/_timed_out" with
#       the elapsed seconds and returns 124 (the standard timeout exit
#       code). On success or any other failure, writes "$stage_dir/_exit"
#       with the exit code.
#
#   audit_heartbeats <run_dir>
#       At the end of a run, walks the run dir and reports any stage with
#       a missing or stale heartbeat, a missing _exit marker, or a
#       _timed_out marker. Writes a summary to
#       "$run_dir/HEARTBEAT_AUDIT.md" listing every stage's status. Used
#       to catch silent hangs / kills the chain itself didn't notice.
#
# The chain itself decides what timeout to use per stage. Default is 600s
# (10 min) since that matches the claude CLI subprocess timeout already
# used by run_hypothesis_formulation.py and other python wrappers.
#
# Why we need this:
#   Stages can hang silently when (a) claude CLI deadlocks on a malformed
#   tool-use response, (b) pandoc errors get swallowed by `|| true`,
#   (c) a sub-agent enters a retry loop with no progress. Heartbeat
#   detects (a) and (c); _exit + audit detects (b).
#
# Source it: `source "$ROOT/chain/common/heartbeat.sh"`

# Global state for heartbeat PID tracking. The chain typically runs one
# stage at a time so a single global is sufficient.
HEARTBEAT_PID=""
HEARTBEAT_DIR=""

start_heartbeat() {
  local stage_dir="$1"
  local interval="${2:-30}"
  if [[ -z "$stage_dir" ]]; then
    echo "[heartbeat] start_heartbeat: missing stage_dir" >&2
    return 1
  fi
  mkdir -p "$stage_dir"
  HEARTBEAT_DIR="$stage_dir"
  # Initial beat.
  date -u +"%Y-%m-%dT%H:%M:%SZ pid=$$ stage=$(basename "$stage_dir") interval=$interval" \
    > "$stage_dir/_heartbeat.txt"
  # Background loop. Disown so it survives stage-level set -e fail-fast.
  (
    while true; do
      sleep "$interval"
      date -u +"%Y-%m-%dT%H:%M:%SZ pid=$$" >> "$stage_dir/_heartbeat.txt"
    done
  ) &
  HEARTBEAT_PID=$!
  disown "$HEARTBEAT_PID" 2>/dev/null || true
}

stop_heartbeat() {
  if [[ -n "${HEARTBEAT_PID:-}" ]] && kill -0 "$HEARTBEAT_PID" 2>/dev/null; then
    kill "$HEARTBEAT_PID" 2>/dev/null || true
    # Give it a moment to die before the next stage starts.
    wait "$HEARTBEAT_PID" 2>/dev/null || true
  fi
  HEARTBEAT_PID=""
  HEARTBEAT_DIR=""
}

run_with_heartbeat() {
  local stage_dir="$1"; shift
  local timeout_sec="$1"; shift
  if [[ -z "$stage_dir" || -z "$timeout_sec" || $# -eq 0 ]]; then
    echo "[heartbeat] run_with_heartbeat: usage: <stage_dir> <timeout_sec> <command...>" >&2
    return 2
  fi
  mkdir -p "$stage_dir"
  start_heartbeat "$stage_dir" 30
  local started_at
  started_at="$(date +%s)"

  # `timeout` is GNU-coreutils on Linux, gtimeout on macOS Homebrew.
  # If neither is installed (vanilla macOS), use a Bash-native fallback
  # that runs the command in a subshell and kills it via a watchdog
  # subprocess after timeout_sec.
  local timeout_cmd=""
  if command -v timeout >/dev/null 2>&1; then
    timeout_cmd="timeout"
  elif command -v gtimeout >/dev/null 2>&1; then
    timeout_cmd="gtimeout"
  fi

  local rc=0
  if [[ -n "$timeout_cmd" ]]; then
    "$timeout_cmd" "${timeout_sec}s" "$@"
    rc=$?
  else
    # Bash-native timeout: launch cmd + watchdog as siblings; whichever
    # finishes first wins. Watchdog kills cmd's process group on expiry.
    set +e
    ("$@") &
    local cmd_pid=$!
    ( sleep "$timeout_sec"; kill -TERM "$cmd_pid" 2>/dev/null;
      sleep 2; kill -KILL "$cmd_pid" 2>/dev/null ) &
    local guard_pid=$!
    wait "$cmd_pid" 2>/dev/null
    rc=$?
    # If the command finished first, kill the watchdog so it doesn't
    # linger. If the watchdog already fired, it has already exited.
    kill "$guard_pid" 2>/dev/null
    wait "$guard_pid" 2>/dev/null
    set -e 2>/dev/null || true
    # Map SIGTERM-induced exit (143) to the standard 124 so callers can
    # detect timeout the same way GNU `timeout` reports it.
    if [[ $rc -eq 143 || $rc -eq 137 ]]; then
      rc=124
    fi
  fi
  local ended_at
  ended_at="$(date +%s)"
  local elapsed=$((ended_at - started_at))

  if [[ $rc -eq 124 ]]; then
    {
      echo "stage=$(basename "$stage_dir")"
      echo "timeout_sec=$timeout_sec"
      echo "elapsed_sec=$elapsed"
      echo "command=$*"
      echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$stage_dir/_timed_out"
    echo "[heartbeat] stage $(basename "$stage_dir") TIMED OUT after ${elapsed}s" >&2
  fi
  {
    echo "exit_code=$rc"
    echo "elapsed_sec=$elapsed"
    echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$stage_dir/_exit"

  stop_heartbeat
  return $rc
}

audit_heartbeats() {
  local run_dir="$1"
  if [[ -z "$run_dir" || ! -d "$run_dir" ]]; then
    echo "[heartbeat] audit_heartbeats: missing run_dir" >&2
    return 1
  fi
  local out="$run_dir/HEARTBEAT_AUDIT.md"
  local now_epoch
  now_epoch="$(date +%s)"
  local stale_threshold=180   # 3 min — after a stage exits, heartbeat
                              # stops getting written, so anything older
                              # than 3 min on a stage that's still "live"
                              # (no _exit) is suspected hung.

  {
    echo "# Heartbeat Audit"
    echo ""
    echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo ""
    echo "| Stage | Status | Elapsed | Exit | Notes |"
    echo "| --- | --- | --- | --- | --- |"
  } > "$out"

  # Match dirs of the form NN_name at the top level of the run dir.
  local stage_dir
  local stale_count=0
  local hung_count=0
  local timed_out_count=0
  while IFS= read -r -d '' stage_dir; do
    local name
    name="$(basename "$stage_dir")"
    # Skip non-stage dirs. Accept either:
    #   - numbered dirs (paper chain: 01_falsificationist, 99_synthesizer)
    #   - word-prefix dirs (manuscript chain: chapter_logic_analysis,
    #     emma, paper_generation, etc.) — but skip obvious metadata
    #     dirs like .git, __pycache__, _scratch, dot-prefixed dirs.
    case "$name" in
      .*|__*|_scratch|node_modules) continue ;;
    esac

    local status="OK"
    local elapsed="-"
    local exit_code="-"
    local note=""

    if [[ -f "$stage_dir/_timed_out" ]]; then
      status="TIMED_OUT"
      timed_out_count=$((timed_out_count + 1))
      elapsed="$(grep -E '^elapsed_sec=' "$stage_dir/_timed_out" | cut -d= -f2)"
      note="exceeded timeout"
    elif [[ -f "$stage_dir/_exit" ]]; then
      exit_code="$(grep -E '^exit_code=' "$stage_dir/_exit" | cut -d= -f2)"
      elapsed="$(grep -E '^elapsed_sec=' "$stage_dir/_exit" | cut -d= -f2)"
      if [[ "$exit_code" != "0" ]]; then
        status="FAILED"
        note="non-zero exit"
      fi
    else
      # No _exit. Either stage doesn't use run_with_heartbeat, OR it hung
      # / was killed without writing the marker. Distinguish via heartbeat.
      if [[ -f "$stage_dir/_heartbeat.txt" ]]; then
        local last_beat_epoch
        last_beat_epoch="$(stat -f %m "$stage_dir/_heartbeat.txt" 2>/dev/null \
                           || stat -c %Y "$stage_dir/_heartbeat.txt" 2>/dev/null \
                           || echo 0)"
        local age=$((now_epoch - last_beat_epoch))
        if (( age > stale_threshold )); then
          status="HUNG_OR_KILLED"
          hung_count=$((hung_count + 1))
          note="last heartbeat ${age}s ago, no _exit"
        else
          status="RUNNING"
          note="heartbeat live (${age}s ago)"
        fi
      else
        # No heartbeat tracking — stage just ran the legacy way.
        status="UNTRACKED"
        note="no _heartbeat (stage not wrapped)"
      fi
    fi
    echo "| \`$name\` | $status | $elapsed | $exit_code | $note |" >> "$out"
  done < <(find "$run_dir" -mindepth 1 -maxdepth 1 -type d -print0)

  {
    echo ""
    echo "## Summary"
    echo ""
    echo "- Timed out: $timed_out_count"
    echo "- Hung or killed (no _exit, stale heartbeat): $hung_count"
    echo ""
    if (( timed_out_count + hung_count > 0 )); then
      echo "⚠  **One or more stages did not complete cleanly.** Inspect the"
      echo "stage dirs above. A HUNG_OR_KILLED status with no _exit marker"
      echo "indicates the chain itself didn't notice the stage's failure —"
      echo "this is the bug class heartbeat tracking exists to catch."
    fi
  } >> "$out"

  echo "[heartbeat] audit written: $out (timed_out=$timed_out_count hung=$hung_count)"
}
