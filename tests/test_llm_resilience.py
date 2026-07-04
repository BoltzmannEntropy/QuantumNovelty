"""Tests for call_llm retry/fallback resilience and the calibration metrics.

No real LLM calls: _dispatch_backend is monkeypatched, and the calibration
metrics function is pure.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "common"))
sys.path.insert(0, str(ROOT / "skills" / "quantum_reviewer"))

import llm  # noqa: E402
from llm import LLMResult, call_llm  # noqa: E402
from calibrate import compute_metrics  # noqa: E402


def _ok(backend: str) -> LLMResult:
    return LLMResult(text="ok", backend_requested=backend,
                     backend_actually_used=backend)


def test_transient_error_is_retried_same_backend(monkeypatch):
    calls = []

    def fake(prompt, backend, timeout, extra_env, acp_session):
        calls.append(backend)
        if len(calls) == 1:
            raise RuntimeError("backend claude: timed out after 600s")
        return _ok(backend)

    monkeypatch.setattr(llm, "_dispatch_backend", fake)
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)
    res = call_llm("p", backend="claude", retries=2, fallback_backends=[])
    assert calls == ["claude", "claude"]
    assert res.backend_actually_used == "claude"
    assert res.extras["resilience"]["fallback_used"] is False
    assert len(res.extras["resilience"]["attempts"]) == 1


def test_permanent_error_falls_back_when_opted_in(monkeypatch):
    calls = []

    def fake(prompt, backend, timeout, extra_env, acp_session):
        calls.append(backend)
        if backend == "claude":
            raise RuntimeError("claude not found on PATH (needed for backend claude)")
        return _ok(backend)

    monkeypatch.setattr(llm, "_dispatch_backend", fake)
    res = call_llm("p", backend="claude", retries=2,
                   fallback_backends=["codex"])
    # permanent error: no retry burn on claude, straight to codex
    assert calls == ["claude", "codex"]
    assert res.backend_requested == "claude"          # original request kept
    assert res.backend_actually_used == "codex"       # fallback visible
    assert res.extras["resilience"]["fallback_used"] is True


def test_no_fallback_by_default(monkeypatch):
    def fake(prompt, backend, timeout, extra_env, acp_session):
        raise RuntimeError("backend claude: timed out after 600s")

    monkeypatch.setattr(llm, "_dispatch_backend", fake)
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="all backends failed"):
        call_llm("p", backend="claude", retries=1, fallback_backends=[])


def test_anthropic_api_refused_as_fallback():
    with pytest.raises(ValueError, match="opt-in only"):
        call_llm("p", backend="claude", retries=0,
                 fallback_backends=["anthropic-api"])


def test_marker_json_surfaces_resilience(monkeypatch):
    def fake(prompt, backend, timeout, extra_env, acp_session):
        if backend == "claude":
            raise RuntimeError("backend claude: empty stdout; stderr_tail=")
        return _ok(backend)

    monkeypatch.setattr(llm, "_dispatch_backend", fake)
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)
    res = call_llm("p", backend="claude", retries=0,
                   fallback_backends=["kimi"])
    marker = res.as_marker_json()
    assert '"fallback_used": true' in marker
    assert '"backend_requested": "claude"' in marker


# ---------------------------------------------------------------------------
# Calibration metrics (pure function)
# ---------------------------------------------------------------------------

def _rec(name, truth, score, passed):
    return {"name": name, "ground_truth": truth,
            "score": score, "panel_pass": passed}


def test_calibration_metrics_perfect_panel():
    records = [
        _rec("good1", "accept", 8.4, True),
        _rec("good2", "accept", 7.6, True),
        _rec("bad1", "reject", 4.2, False),
        _rec("bad2", "reject", 5.8, False),
    ]
    m = compute_metrics(records, threshold=7.0)
    assert m["confusion"] == {"tp": 2, "fn": 0, "tn": 2, "fp": 0}
    assert m["fnr"] == 0.0 and m["fpr"] == 0.0
    assert m["accuracy"] == 1.0
    assert m["auc_mean_score"] == 1.0


def test_calibration_metrics_mixed_panel_and_skips():
    records = [
        _rec("good1", "accept", 8.0, True),
        _rec("good2", "accept", 6.0, False),   # false negative
        _rec("bad1", "reject", 7.5, True),     # false positive
        _rec("bad2", "reject", 3.0, False),
        _rec("broken", "accept", None, None),  # panel failed → skipped
    ]
    m = compute_metrics(records, threshold=7.0)
    assert m["n_usable"] == 4
    assert m["skipped_items"] == ["broken"]
    assert m["confusion"] == {"tp": 1, "fn": 1, "tn": 1, "fp": 1}
    assert m["fnr"] == 0.5 and m["fpr"] == 0.5
    # AUC: pos scores [8.0, 6.0] vs neg [7.5, 3.0] → wins: (8>7.5)+(8>3)+(6<7.5 no)+(6>3) = 3/4
    assert m["auc_mean_score"] == 0.75
