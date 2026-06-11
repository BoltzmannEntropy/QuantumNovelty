"""Python port of chain/common/stage_telemetry.sh + heartbeat.sh.

The bash helpers in chain/common/*.sh implement AutoResearchClaw's
stage_health / pipeline_summary / decision_history / checkpoint pattern
for any chain that wants to shell out. This module gives pipelines.py the
same JSON shapes from Python so a paper-audit run's outputs are
byte-for-byte compatible with that telemetry tooling (stage_health.json /
decision_history.json / pipeline_summary.json / checkpoint.json /
HEARTBEAT_AUDIT.md).

Schemas (mirror the bash helpers verbatim):

  _stage_health.json — per stage:
    {
      "stage_id":       "01-research",
      "stage_dir":      "01_research_review",
      "duration_sec":   42,
      "status":         "done" | "paused" | "blocked" | "failed" | "degraded",
      "artifacts_count":  4,
      "error":          null | "<one-line error string>",
      "started_iso":    "2026-06-10T12:00:00Z",
      "ended_iso":      "2026-06-10T12:00:42Z"
    }

  decision_history.json — append-only log per run:
    [
      { "decision": "proceed", "rollback_target": null,
        "rollback_stage_num": 0, "attempt": 1, "timestamp": "..." },
      ...
    ]

  pipeline_summary.json — aggregate:
    {
      "run_id": "<basename of run dir>",
      "stages_executed": 4, "stages_done": 4,
      "stages_paused": 0, "stages_blocked": 0, "stages_failed": 0,
      "degraded": false, "from_stage": 1, "final_stage": 4,
      "final_status": "done", "generated": "...",
      "content_metrics": { ... },
      "per_stage": [ { "stage_id": ..., "stage_dir": ..., "status": ...,
                       "duration_sec": ..., "artifacts_count": ... }, ... ]
    }

  checkpoint.json — pause/resume marker:
    {
      "run_id": "<basename>",
      "paused_after_stage": "02-reviewer",
      "next_stage": "03-fallacies" | null,
      "paused_at": "...",
      "cwd": "...",
      "original_argv": [...],
      "resume_hint": "Re-launch with --resume-from <next_stage>"
    }
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_TELEMETRY_SCAFFOLDING = {
    "_stage_health.json", "_stage_health.tmp",
    "_heartbeat.txt", "_exit", "_timed_out",
    "_backend_used.txt", "_chain_stage.log",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts_now() -> int:
    return int(time.time())


def stage_health_begin(stage_dir: Path, stage_id: str) -> None:
    """Mark a stage start. Mirrors stage_telemetry.sh::stage_health_begin."""
    stage_dir.mkdir(parents=True, exist_ok=True)
    started_iso = _iso_now()
    started_epoch = _ts_now()
    (stage_dir / "_stage_health.tmp").write_text(
        f"stage_id={stage_id}\n"
        f"started_iso={started_iso}\n"
        f"started_epoch={started_epoch}\n",
        encoding="utf-8",
    )


def stage_health_end(stage_dir: Path,
                     status: str = "done",
                     error: Optional[str] = None) -> dict:
    """Finalize a stage's _stage_health.json.

    Returns the written health dict so callers can use it directly.
    """
    if not stage_dir.is_dir():
        return {}
    stage_id = ""
    started_iso = ""
    started_epoch = 0
    tmp = stage_dir / "_stage_health.tmp"
    if tmp.is_file():
        for line in tmp.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                if k == "stage_id":
                    stage_id = v
                elif k == "started_iso":
                    started_iso = v
                elif k == "started_epoch":
                    try:
                        started_epoch = int(v)
                    except ValueError:
                        pass
    now_epoch = _ts_now()
    duration_sec = max(0, now_epoch - started_epoch) if started_epoch else 0

    # Count artifacts (excluding scaffolding files).
    artifacts_count = 0
    for root, _, files in os.walk(stage_dir):
        for f in files:
            if f in _TELEMETRY_SCAFFOLDING:
                continue
            artifacts_count += 1

    health = {
        "stage_id": stage_id,
        "stage_dir": stage_dir.name,
        "duration_sec": duration_sec,
        "status": status,
        "artifacts_count": artifacts_count,
        "error": error,
        "started_iso": started_iso,
        "ended_iso": _iso_now(),
    }
    (stage_dir / "_stage_health.json").write_text(
        json.dumps(health, indent=2), encoding="utf-8"
    )
    if tmp.is_file():
        tmp.unlink()
    return health


def decision_log(run_dir: Path, decision: str,
                 rollback_target: Optional[str] = None,
                 rollback_stage_num: int = 0,
                 attempt: int = 1) -> None:
    """Append a decision entry to decision_history.json.

    Valid decisions: proceed | refine | pivot | pause | block | fail.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    hist_path = run_dir / "decision_history.json"
    data = []
    if hist_path.is_file():
        try:
            data = json.loads(hist_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except json.JSONDecodeError:
            data = []
    entry = {
        "decision": decision,
        "rollback_target": rollback_target,
        "rollback_stage_num": rollback_stage_num,
        "attempt": attempt,
        "timestamp": datetime.now(timezone.utc)
                      .strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    }
    data.append(entry)
    hist_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def checkpoint_write(run_dir: Path, stage_id: str,
                     next_stage_id: Optional[str] = None,
                     original_argv: Optional[list[str]] = None) -> None:
    """Write a resumable checkpoint marker.

    Mirrors stage_telemetry.sh::checkpoint_write.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_dir.name,
        "paused_after_stage": stage_id,
        "next_stage": next_stage_id,
        "paused_at": _iso_now(),
        "cwd": str(Path.cwd()),
        "original_argv": original_argv or [],
        "resume_hint": "Re-launch with --resume-from <next_stage>",
    }
    (run_dir / "checkpoint.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(f"[hitl] checkpoint written: {run_dir/'checkpoint.json'} "
          f"(paused after {stage_id})", file=sys.stderr)


def pause_after_stage(run_dir: Path, current: str,
                      next_id: Optional[str] = None) -> bool:
    """Return True iff the env QN_HITL_PAUSE_AFTER matches current.

    On match, write checkpoint.json. Caller is responsible for sys.exit(0).
    """
    target = os.environ.get("QN_HITL_PAUSE_AFTER", "").strip()
    if not target:
        return False
    if target in current:
        checkpoint_write(run_dir, current, next_id)
        print(f"[hitl] QN_HITL_PAUSE_AFTER={target} matched stage={current}"
              f" — exiting cleanly.", file=sys.stderr)
        return True
    return False


def pipeline_summary(run_dir: Path) -> Path:
    """Aggregate every _stage_health.json under run_dir into
    pipeline_summary.json. Mirrors stage_telemetry.sh::pipeline_summary.

    Idempotent; safe to call multiple times.
    """
    healths: list[dict] = []
    for sh in sorted(run_dir.rglob("_stage_health.json")):
        try:
            healths.append(json.loads(sh.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue

    counts = {"done": 0, "paused": 0, "blocked": 0,
              "failed": 0, "degraded": 0}
    for h in healths:
        s = (h.get("status") or "unknown").lower()
        if s in counts:
            counts[s] += 1
        elif s in ("warn", "degraded"):
            counts["degraded"] += 1

    sorted_by_dir = sorted(healths, key=lambda h: h.get("stage_dir", ""))
    final_status = "done"
    if counts["failed"] > 0:
        final_status = "failed"
    elif counts["blocked"] > 0:
        final_status = "blocked"
    elif counts["paused"] > 0:
        final_status = "paused"

    # Content metrics — ARC reads citation-integrity + quality-gate reports.
    # QN equivalent: read CQE composite if present.
    content: dict = {}
    cqe_paths = list(run_dir.rglob("cqe_scores.json"))
    if cqe_paths:
        try:
            cqe = json.loads(cqe_paths[0].read_text(encoding="utf-8"))
            content["cqe_composite"] = cqe.get("composite")
            content["cqe_dimensions"] = [
                {"name": d.get("name"), "score": d.get("score")}
                for d in (cqe.get("dimensions") or [])
            ]
        except (json.JSONDecodeError, OSError):
            pass
    fallacy_paths = list(run_dir.rglob("fallacy_findings.json"))
    if fallacy_paths:
        try:
            fall = json.loads(fallacy_paths[0].read_text(encoding="utf-8"))
            content["fallacy_count"] = len(fall.get("findings") or [])
        except (json.JSONDecodeError, OSError):
            pass

    summary = {
        "run_id": run_dir.name,
        "stages_executed": len(healths),
        "stages_done": counts["done"],
        "stages_paused": counts["paused"],
        "stages_blocked": counts["blocked"],
        "stages_failed": counts["failed"],
        "degraded": counts["degraded"] > 0,
        "from_stage": 1,
        "final_stage": len(healths),
        "final_status": final_status,
        "generated": datetime.now(timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "content_metrics": content,
        "per_stage": [
            {
                "stage_id": h.get("stage_id"),
                "stage_dir": h.get("stage_dir"),
                "status": h.get("status"),
                "duration_sec": h.get("duration_sec"),
                "artifacts_count": h.get("artifacts_count"),
            }
            for h in sorted_by_dir
        ],
    }
    out = run_dir / "pipeline_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[telemetry] pipeline_summary: {len(healths)} stages → {out}",
          file=sys.stderr)
    return out


def audit_heartbeats(run_dir: Path) -> Path:
    """Walk every stage dir, classify by heartbeat freshness + _exit marker.

    Writes HEARTBEAT_AUDIT.md. Mirrors heartbeat.sh::audit_heartbeats.
    """
    out = run_dir / "HEARTBEAT_AUDIT.md"
    now = _ts_now()
    stale_threshold = 180
    rows = []
    timed_out_count = hung_count = 0

    for child in sorted(run_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name.startswith("__") \
                or child.name in {"_scratch", "node_modules"}:
            continue
        # Also walk one level deeper (paper-audit puts stages under each
        # paper's outdir).
        candidates = [child]
        if not (child / "_stage_health.json").is_file() \
                and not (child / "_exit").is_file() \
                and not (child / "_heartbeat.txt").is_file():
            for grand in sorted(child.iterdir()) if child.is_dir() else []:
                if grand.is_dir() and not grand.name.startswith("_"):
                    candidates.append(grand)
        for sd in candidates:
            name = sd.relative_to(run_dir).as_posix()
            status = "OK"
            elapsed = "-"
            exit_code = "-"
            note = ""
            timed_out = sd / "_timed_out"
            exit_marker = sd / "_exit"
            heartbeat = sd / "_heartbeat.txt"
            health = sd / "_stage_health.json"
            if timed_out.is_file():
                status = "TIMED_OUT"
                timed_out_count += 1
                for line in timed_out.read_text(encoding="utf-8").splitlines():
                    if line.startswith("elapsed_sec="):
                        elapsed = line.split("=", 1)[1]
                note = "exceeded timeout"
            elif exit_marker.is_file():
                for line in exit_marker.read_text(encoding="utf-8").splitlines():
                    if line.startswith("exit_code="):
                        exit_code = line.split("=", 1)[1]
                    elif line.startswith("elapsed_sec="):
                        elapsed = line.split("=", 1)[1]
                if exit_code != "0":
                    status = "FAILED"
                    note = "non-zero exit"
            elif health.is_file():
                # Python-orchestrated stage (no bash _exit marker).
                try:
                    h = json.loads(health.read_text(encoding="utf-8"))
                    elapsed = str(h.get("duration_sec", "-"))
                    exit_code = "0" if h.get("status") == "done" else "?"
                    status = h.get("status", "OK").upper()
                    if status != "DONE":
                        note = h.get("error") or ""
                except json.JSONDecodeError:
                    pass
            elif heartbeat.is_file():
                age = now - int(heartbeat.stat().st_mtime)
                if age > stale_threshold:
                    status = "HUNG_OR_KILLED"
                    hung_count += 1
                    note = f"last heartbeat {age}s ago, no _exit"
                else:
                    status = "RUNNING"
                    note = f"heartbeat live ({age}s ago)"
            else:
                status = "UNTRACKED"
                note = "no _heartbeat / _stage_health (legacy stage)"
            rows.append((name, status, elapsed, exit_code, note))

    with open(out, "w", encoding="utf-8") as f:
        f.write("# Heartbeat Audit\n\n")
        f.write(f"Generated: {_iso_now()}\n\n")
        f.write("| Stage | Status | Elapsed | Exit | Notes |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for r in rows:
            f.write(f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]} |\n")
        f.write("\n## Summary\n\n")
        f.write(f"- Timed out: {timed_out_count}\n")
        f.write(f"- Hung or killed (no _exit, stale heartbeat): "
                f"{hung_count}\n\n")
        if timed_out_count + hung_count > 0:
            f.write("⚠  **One or more stages did not complete cleanly.** "
                    "Inspect the stage dirs above. A HUNG_OR_KILLED status "
                    "with no _exit marker indicates the chain itself didn't "
                    "notice the stage's failure — this is the bug class "
                    "heartbeat tracking exists to catch.\n")
    print(f"[heartbeat] audit written: {out} "
          f"(timed_out={timed_out_count} hung={hung_count})", file=sys.stderr)
    return out
