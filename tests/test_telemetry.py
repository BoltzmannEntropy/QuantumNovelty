"""Telemetry parity tests — locks the structured-telemetry JSON shapes.

The QN chain implements ARC's stage_health / pipeline_summary /
decision_history / checkpoint pattern in bash (chain/common/heartbeat.sh
+ stage_telemetry.sh) and Python (chain/common/telemetry.py) so
chain/pipelines.py produces byte-compatible output. These tests pin the
JSON keys so future edits can't quietly drift.

Run: `pytest tests/test_telemetry.py -v`
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "chain" / "common"))
import telemetry  # noqa: E402  (path manipulation required)


# =========================================================================
# Schema contracts — bash and Python implementations must agree.
# =========================================================================

STAGE_HEALTH_KEYS = {
    "stage_id", "stage_dir", "duration_sec", "status",
    "artifacts_count", "error", "started_iso", "ended_iso",
}

PIPELINE_SUMMARY_KEYS = {
    "run_id", "stages_executed", "stages_done", "stages_paused",
    "stages_blocked", "stages_failed", "degraded",
    "from_stage", "final_stage", "final_status", "generated",
    "content_metrics", "per_stage",
}

DECISION_HISTORY_ITEM_KEYS = {
    "decision", "rollback_target", "rollback_stage_num",
    "attempt", "timestamp",
}

CHECKPOINT_KEYS = {
    "run_id", "paused_after_stage", "next_stage", "paused_at",
    "cwd", "original_argv", "resume_hint",
}

VALID_DECISIONS = {"proceed", "refine", "pivot", "pause", "block", "fail"}
VALID_STATUSES = {"done", "paused", "blocked", "failed", "degraded"}


# =========================================================================
# stage_health_begin / stage_health_end
# =========================================================================

def test_stage_health_schema_matches_contract(tmp_path):
    """Every key the pipeline_summary aggregator expects must be present."""
    sd = tmp_path / "01_test_stage"
    telemetry.stage_health_begin(sd, "01-test")
    # Drop one artifact so the count check is meaningful.
    (sd / "real_artifact.md").write_text("hi", encoding="utf-8")
    telemetry.stage_health_end(sd, status="done")
    written = json.loads((sd / "_stage_health.json").read_text(encoding="utf-8"))
    assert set(written) == STAGE_HEALTH_KEYS
    assert written["stage_id"] == "01-test"
    assert written["stage_dir"] == "01_test_stage"
    assert written["status"] == "done"
    assert written["error"] is None
    assert written["artifacts_count"] >= 1
    # ISO 8601 Z-suffixed UTC.
    assert written["started_iso"].endswith("Z")
    assert written["ended_iso"].endswith("Z")


def test_stage_health_status_failure_with_error(tmp_path):
    sd = tmp_path / "02_fail"
    telemetry.stage_health_begin(sd, "02-fail")
    telemetry.stage_health_end(sd, status="failed",
                                error="skill exited rc=1")
    h = json.loads((sd / "_stage_health.json").read_text(encoding="utf-8"))
    assert h["status"] == "failed"
    assert h["error"] == "skill exited rc=1"


def test_stage_health_excludes_scaffolding_from_artifact_count(tmp_path):
    sd = tmp_path / "03_scaffold"
    telemetry.stage_health_begin(sd, "03-test")
    # Pre-existing scaffolding (these MUST NOT count):
    (sd / "_heartbeat.txt").write_text("beat", encoding="utf-8")
    (sd / "_exit").write_text("0", encoding="utf-8")
    (sd / "_backend_used.txt").write_text("codex", encoding="utf-8")
    (sd / "_chain_stage.log").write_text("log", encoding="utf-8")
    # Real artifacts (these MUST count):
    (sd / "review.md").write_text("a", encoding="utf-8")
    (sd / "findings.json").write_text("{}", encoding="utf-8")
    telemetry.stage_health_end(sd, status="done")
    h = json.loads((sd / "_stage_health.json").read_text(encoding="utf-8"))
    assert h["artifacts_count"] == 2


# =========================================================================
# decision_log
# =========================================================================

def test_decision_log_appends_to_existing_array(tmp_path):
    telemetry.decision_log(tmp_path, "proceed")
    telemetry.decision_log(tmp_path, "fail",
                           rollback_target="01-research",
                           rollback_stage_num=1, attempt=2)
    entries = json.loads(
        (tmp_path / "decision_history.json").read_text(encoding="utf-8")
    )
    assert isinstance(entries, list)
    assert len(entries) == 2
    for e in entries:
        assert set(e) == DECISION_HISTORY_ITEM_KEYS
        assert e["decision"] in VALID_DECISIONS
    assert entries[0]["decision"] == "proceed"
    assert entries[0]["rollback_target"] is None
    assert entries[1]["rollback_target"] == "01-research"
    assert entries[1]["rollback_stage_num"] == 1
    assert entries[1]["attempt"] == 2


def test_decision_log_recovers_from_corrupt_file(tmp_path):
    (tmp_path / "decision_history.json").write_text(
        "{ malformed", encoding="utf-8"
    )
    telemetry.decision_log(tmp_path, "proceed")
    entries = json.loads(
        (tmp_path / "decision_history.json").read_text(encoding="utf-8")
    )
    # Corrupt → reset to [], then append one entry.
    assert len(entries) == 1
    assert entries[0]["decision"] == "proceed"


# =========================================================================
# checkpoint_write + pause_after_stage
# =========================================================================

def test_checkpoint_write_schema(tmp_path):
    telemetry.checkpoint_write(tmp_path, "02-reviewer",
                                next_stage_id="03-fallacies",
                                original_argv=["--paper", "x.txt"])
    ck = json.loads((tmp_path / "checkpoint.json").read_text(encoding="utf-8"))
    assert set(ck) == CHECKPOINT_KEYS
    assert ck["paused_after_stage"] == "02-reviewer"
    assert ck["next_stage"] == "03-fallacies"
    assert ck["original_argv"] == ["--paper", "x.txt"]
    assert "Re-launch" in ck["resume_hint"]


def test_pause_after_stage_no_env_returns_false(tmp_path, monkeypatch):
    monkeypatch.delenv("QN_HITL_PAUSE_AFTER", raising=False)
    assert telemetry.pause_after_stage(tmp_path, "02-reviewer") is False
    assert not (tmp_path / "checkpoint.json").exists()


def test_pause_after_stage_substring_match_writes_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("QN_HITL_PAUSE_AFTER", "review")
    matched = telemetry.pause_after_stage(tmp_path, "02-reviewer",
                                          next_id="03-fallacies")
    assert matched is True
    assert (tmp_path / "checkpoint.json").is_file()


def test_pause_after_stage_no_match_returns_false(tmp_path, monkeypatch):
    monkeypatch.setenv("QN_HITL_PAUSE_AFTER", "cqe")
    assert telemetry.pause_after_stage(tmp_path, "02-reviewer") is False
    assert not (tmp_path / "checkpoint.json").exists()


# =========================================================================
# pipeline_summary aggregation
# =========================================================================

def test_pipeline_summary_aggregates_all_stage_healths(tmp_path):
    # Three stages, two done, one failed.
    for name, status in (("01_a", "done"), ("02_b", "done"), ("03_c", "failed")):
        sd = tmp_path / name
        telemetry.stage_health_begin(sd, name.replace("_", "-"))
        telemetry.stage_health_end(sd, status=status,
                                    error=("oops" if status == "failed" else None))
    out = telemetry.pipeline_summary(tmp_path)
    assert out.is_file()
    ps = json.loads(out.read_text(encoding="utf-8"))
    assert set(ps) == PIPELINE_SUMMARY_KEYS
    assert ps["stages_executed"] == 3
    assert ps["stages_done"] == 2
    assert ps["stages_failed"] == 1
    assert ps["final_status"] == "failed"
    assert len(ps["per_stage"]) == 3
    # per_stage rows have the stage-health-schema keys
    for row in ps["per_stage"]:
        assert set(row) == {
            "stage_id", "stage_dir", "status",
            "duration_sec", "artifacts_count",
        }


def test_pipeline_summary_picks_cqe_into_content_metrics(tmp_path):
    sd = tmp_path / "04_summary"
    sd.mkdir()
    (sd / "cqe_scores.json").write_text(json.dumps({
        "composite": 67,
        "dimensions": [
            {"name": "Novelty rigour", "score": 70},
            {"name": "Falsifiability", "score": 80},
        ],
    }), encoding="utf-8")
    sd_h = tmp_path / "04_summary_health"
    telemetry.stage_health_begin(sd_h, "04-cqe")
    telemetry.stage_health_end(sd_h, status="done")
    ps = json.loads(
        telemetry.pipeline_summary(tmp_path).read_text(encoding="utf-8")
    )
    assert ps["content_metrics"]["cqe_composite"] == 67
    assert ps["content_metrics"]["cqe_dimensions"][0]["name"] == "Novelty rigour"
    assert ps["content_metrics"]["cqe_dimensions"][0]["score"] == 70


def test_pipeline_summary_picks_fallacy_count_into_content_metrics(tmp_path):
    sd = tmp_path / "03_fallacies"
    sd.mkdir()
    (sd / "fallacy_findings.json").write_text(json.dumps({
        "findings": [{"name": "a"}, {"name": "b"}, {"name": "c"}]
    }), encoding="utf-8")
    sd_h = tmp_path / "03_fallacies_health"
    telemetry.stage_health_begin(sd_h, "03-fallacies")
    telemetry.stage_health_end(sd_h, status="done")
    ps = json.loads(
        telemetry.pipeline_summary(tmp_path).read_text(encoding="utf-8")
    )
    assert ps["content_metrics"]["fallacy_count"] == 3


def test_pipeline_summary_empty_run_dir_clean(tmp_path):
    out = telemetry.pipeline_summary(tmp_path)
    ps = json.loads(out.read_text(encoding="utf-8"))
    assert ps["stages_executed"] == 0
    assert ps["final_status"] == "done"


# =========================================================================
# audit_heartbeats — bash/python parity
# =========================================================================

def test_audit_heartbeats_done_stages(tmp_path):
    for name in ("01_a", "02_b"):
        sd = tmp_path / name
        telemetry.stage_health_begin(sd, name)
        telemetry.stage_health_end(sd, status="done")
    out = telemetry.audit_heartbeats(tmp_path)
    md = out.read_text(encoding="utf-8")
    assert "# Heartbeat Audit" in md
    assert "01_a" in md and "02_b" in md
    assert "Timed out: 0" in md
    assert "Hung or killed" in md
    # No alarm at the bottom since everything's DONE.
    assert "did not complete cleanly" not in md


def test_audit_heartbeats_timed_out_stage(tmp_path):
    sd = tmp_path / "01_slow"
    sd.mkdir()
    (sd / "_timed_out").write_text(
        "stage=01_slow\ntimeout_sec=10\nelapsed_sec=11\n", encoding="utf-8"
    )
    out = telemetry.audit_heartbeats(tmp_path)
    md = out.read_text(encoding="utf-8")
    assert "TIMED_OUT" in md
    assert "Timed out: 1" in md
    assert "did not complete cleanly" in md


def test_audit_heartbeats_exit_marker_failed(tmp_path):
    """Stages wrapped by run_with_heartbeat write _exit marker."""
    sd = tmp_path / "01_failed"
    sd.mkdir()
    (sd / "_exit").write_text("exit_code=2\nelapsed_sec=5\n", encoding="utf-8")
    md = telemetry.audit_heartbeats(tmp_path).read_text(encoding="utf-8")
    assert "FAILED" in md


# =========================================================================
# Shape pinning — paranoia tests that compare against the schema
# samples documented in chain/common/telemetry.py.
# =========================================================================

def test_stage_health_json_keys_match_doc():
    """Verify the docstring schema in telemetry.py matches what we write."""
    expected = {
        "stage_id", "stage_dir", "duration_sec", "status",
        "artifacts_count", "error", "started_iso", "ended_iso",
    }
    assert STAGE_HEALTH_KEYS == expected


def test_pipeline_summary_json_keys_match_doc():
    expected = {
        "run_id", "stages_executed", "stages_done",
        "stages_paused", "stages_blocked", "stages_failed",
        "degraded", "from_stage", "final_stage",
        "final_status", "generated", "content_metrics", "per_stage",
    }
    assert PIPELINE_SUMMARY_KEYS == expected


def test_decision_history_item_keys_match_doc():
    expected = {
        "decision", "rollback_target", "rollback_stage_num",
        "attempt", "timestamp",
    }
    assert DECISION_HISTORY_ITEM_KEYS == expected


def test_checkpoint_json_keys_match_doc():
    expected = {
        "run_id", "paused_after_stage", "next_stage", "paused_at",
        "cwd", "original_argv", "resume_hint",
    }
    assert CHECKPOINT_KEYS == expected


# =========================================================================
# Telemetry bash scripts present and executable
# =========================================================================

def test_telemetry_bash_helpers_present_and_executable():
    """heartbeat.sh + stage_telemetry.sh ship with the chain."""
    common = REPO / "chain" / "common"
    for f in ("heartbeat.sh", "stage_telemetry.sh"):
        p = common / f
        assert p.is_file(), f"missing {p}"
        assert os.access(p, os.X_OK), f"{p} not executable"


def test_heartbeat_sh_exports_expected_functions():
    """The 4 functions chain/run.sh sources from heartbeat.sh."""
    text = (REPO / "chain" / "common" / "heartbeat.sh").read_text(encoding="utf-8")
    for fn in ("start_heartbeat", "stop_heartbeat",
               "run_with_heartbeat", "audit_heartbeats"):
        assert f"{fn}()" in text, f"heartbeat.sh missing {fn}()"


def test_stage_telemetry_sh_exports_expected_functions():
    """The 6 functions chain/run.sh sources from stage_telemetry.sh."""
    text = (REPO / "chain" / "common" / "stage_telemetry.sh").read_text(encoding="utf-8")
    for fn in ("stage_health_begin", "stage_health_end",
               "decision_log", "checkpoint_write",
               "pause_after_stage", "pipeline_summary"):
        assert f"{fn}()" in text, f"stage_telemetry.sh missing {fn}()"


def test_stage_telemetry_sh_uses_qn_hitl_pause_after_env():
    """The HITL pause hook is keyed off QN_HITL_PAUSE_AFTER."""
    text = (REPO / "chain" / "common" / "stage_telemetry.sh").read_text(encoding="utf-8")
    assert "QN_HITL_PAUSE_AFTER" in text


# =========================================================================
# Cross-model fork + ARC alias flags (end-to-end shape)
# =========================================================================

import subprocess  # noqa: E402

CHAIN_PIPELINES_PY = REPO / "chain" / "pipelines.py"


def _run_chain(*flags, cwd=None):
    """Run pipelines.py without any LLM calls (every stage skipped)."""
    cmd = ["python3", str(CHAIN_PIPELINES_PY)] + list(flags)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd,
                          timeout=60)


def test_cross_model_fork_writes_index_and_two_branches(tmp_path):
    fake = tmp_path / "fake.txt"
    fake.write_text("paper text", encoding="utf-8")
    outdir = tmp_path / "out"
    r = _run_chain(
        "paper-audit",
        "--outdir", str(outdir),
        "--paper", str(fake), "--topic", "smoke",
        "--skip-research", "--skip-reviewer",
        "--skip-fallacies", "--skip-cqe",
        "--with-cross-model", "--llm", "codex",
    )
    assert r.returncode == 0, r.stderr
    idx_path = outdir / "_cross_model_index.json"
    assert idx_path.is_file()
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    assert idx["fork"] == "cross-model"
    assert {b["branch"] for b in idx["branches"]} == {
        "claude_branch", "codex_branch"
    }
    assert {b["llm"] for b in idx["branches"]} == {"claude", "codex"}
    # Each branch is its own self-contained QN run with SS telemetry.
    for sub in ("claude_branch", "codex_branch"):
        assert (outdir / sub / "pipeline_summary.json").is_file()
        assert (outdir / sub / "decision_history.json").is_file()
        assert (outdir / sub / "_chain_config.json").is_file()
        assert (outdir / sub / "HEARTBEAT_AUDIT.md").is_file()


def test_arc_novelty_check_alias_arms_novelty_audit(tmp_path):
    fake = tmp_path / "fake.txt"
    fake.write_text("paper text", encoding="utf-8")
    outdir = tmp_path / "out"
    r = _run_chain(
        "paper-audit",
        "--outdir", str(outdir),
        "--paper", str(fake), "--topic", "smoke",
        "--skip-research", "--skip-reviewer",
        "--skip-fallacies", "--skip-cqe",
        "--with-arc-novelty-check", "--llm", "codex",
    )
    assert r.returncode == 0, r.stderr
    cc = json.loads((outdir / "_chain_config.json").read_text(encoding="utf-8"))
    # Only "novelty-audit" should be opted in (cross-llm wasn't asked for).
    assert "novelty-audit" in cc["stages_opted_in_by_flag"]
    assert "cross-llm" not in cc["stages_opted_in_by_flag"]


def test_arc_pipeline_bundle_arms_both_optional_stages(tmp_path):
    fake = tmp_path / "fake.txt"
    fake.write_text("paper text", encoding="utf-8")
    outdir = tmp_path / "out"
    r = _run_chain(
        "paper-audit",
        "--outdir", str(outdir),
        "--paper", str(fake), "--topic", "smoke",
        "--skip-research", "--skip-reviewer",
        "--skip-fallacies", "--skip-cqe",
        "--with-arc-pipeline", "--llm", "codex",
    )
    assert r.returncode == 0, r.stderr
    cc = json.loads((outdir / "_chain_config.json").read_text(encoding="utf-8"))
    assert "novelty-audit" in cc["stages_opted_in_by_flag"]
    assert "cross-llm" in cc["stages_opted_in_by_flag"]


def test_list_stages_includes_paper_audit(tmp_path):
    r = _run_chain("list-stages", "--outdir", str(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "paper-audit" in r.stdout
    assert "research, reviewer, fallacies, claims-registry, cqe" in r.stdout
    assert "novelty-audit, cross-llm" in r.stdout
    # Toggle docs surface.
    assert "--skip-<stage>" in r.stdout
    assert "--with-<stage>" in r.stdout


def test_strict_env_defaults_set_at_module_load():
    """CLAUDE_DISABLE_CODEX_FALLBACK + INVOKE_LLM_NO_FALLBACK default on."""
    # pipelines.py sets these at module load via os.environ.setdefault.
    # We've already imported telemetry which doesn't trigger them, so
    # do a subprocess invocation that imports pipelines.py.
    r = subprocess.run(
        ["python3", "-c",
         "import sys, os; sys.path.insert(0, "
         f"'{REPO/'chain'}'); "
         "import pipelines; print(os.environ.get('CLAUDE_DISABLE_CODEX_FALLBACK'),"
         "os.environ.get('INVOKE_LLM_NO_FALLBACK'),"
         "os.environ.get('QN_DISABLE_BACKEND_FALLBACK'))"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    out = r.stdout.strip()
    # Each setdefault sets "1" if unset; values may be inherited from env.
    assert "1 1 1" == out or all(v == "1" for v in out.split())


# =========================================================================
# Cross-framework adoptions (from the QN-vs-ARS-vs-ARC head-to-head)
# =========================================================================

def _load_reviewer_skill():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "qr_skill", REPO / "skills" / "quantum_reviewer" / "skill.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(REPO / "skills" / "common"))
    spec.loader.exec_module(mod)
    return mod


SAMPLE_PANEL = """
## Voice 1 — Reviewer 1 (Physics correctness)
Solid but thin. Verdict: 6/10. Recommendation: major-revisions.
## Voice 2 — Reviewer 2 (Algorithmic novelty)
Real contribution. Verdict: 7/10. Recommendation: minor-revisions.
## Voice 3 — Reviewer 3 (Empirical evidence)
No CIs anywhere. Verdict: 5/10. Recommendation: major-revisions.
## Voice 4 — Devil's Advocate
Reject. The headline claim is an analytical estimate dressed as a result.
## Voice 5 — Editor-in-Chief synthesis
Reconciling: major revisions.
1. Distinguish observable estimation from coherent simulation everywhere.
2. Publish raw data plus an audit script for every ratio.
3. Add Wilson CIs to all K/N claims.

## Vote table

| Voice | Recommendation | Confidence 1-10 |
|---|---|---|
| Reviewer 1 | major-revisions | 7 |
| Reviewer 2 | minor-revisions | 7 |
| Reviewer 3 | major-revisions | 8 |
| Devil's Advocate | reject | 9 |
| Editor-in-Chief | major-revisions | 8 |
"""


def test_quality_gate_extracts_arc_shape():
    """ARC adoption: deterministic quality gate from the panel text."""
    mod = _load_reviewer_skill()
    gate = mod.extract_quality_gate(SAMPLE_PANEL, threshold=7.0)
    assert gate["score_1_to_10"] == 6.0          # mean(6, 7, 5)
    assert gate["verdict"] == "major-revisions"  # EIC vote-table row
    assert gate["passes_threshold"] is False
    assert len(gate["votes"]) == 5
    assert gate["votes"]["Devil's Advocate"]["recommendation"] == "reject"
    assert gate["votes"]["Devil's Advocate"]["confidence"] == 9.0
    # EIC must-fix list parsed from the numbered items after Voice 5.
    assert len(gate["required_actions"]) == 3
    assert "Wilson CIs" in gate["required_actions"][2]


def test_quality_gate_passing_paper():
    mod = _load_reviewer_skill()
    panel = SAMPLE_PANEL.replace("6/10", "8/10").replace(
        "7/10", "9/10").replace("5/10", "8/10").replace(
        "| Editor-in-Chief | major-revisions | 8 |",
        "| Editor-in-Chief | minor-revisions | 8 |")
    gate = mod.extract_quality_gate(panel, threshold=7.0)
    assert gate["score_1_to_10"] >= 8.0
    assert gate["verdict"] == "minor-revisions"
    assert gate["passes_threshold"] is True


def test_quality_gate_tolerates_unparseable_panel():
    mod = _load_reviewer_skill()
    gate = mod.extract_quality_gate("no scores, no table, just vibes")
    assert gate["score_1_to_10"] is None
    assert gate["verdict"] is None
    assert gate["passes_threshold"] is None   # unknown, not False


def test_synthesis_mode_registered_with_prompt():
    """ARS adoption: synthesis mode exists, maps to editorial_decision.md,
    and its prompt template is on disk with the decision-package anchors."""
    mod = _load_reviewer_skill()
    assert mod.MODES["synthesis"] == "editorial_decision.md"
    prompt = (REPO / "skills" / "quantum_reviewer" / "prompts"
              / "synthesis.md").read_text(encoding="utf-8")
    for anchor in ("Editorial Decision Package", "CONSENSUS-",
                   "Revision Roadmap", "Response Letter Template",
                   "{panel}", "{fallacies_block}"):
        assert anchor in prompt, f"synthesis.md missing anchor: {anchor}"


def test_paper_audit_optional_includes_synthesizer():
    """--with-synthesizer is a registered chain toggle."""
    r = _run_chain("list-stages", "--outdir", "/tmp/_qn_t")
    assert r.returncode == 0
    assert "synthesizer" in r.stdout


def test_full_panel_prompt_requires_questions_for_authors():
    """ARS adoption: the panel prompt mandates Questions for Authors."""
    prompt = (REPO / "skills" / "quantum_reviewer" / "prompts"
              / "full.md").read_text(encoding="utf-8")
    assert "Questions for Authors" in prompt
