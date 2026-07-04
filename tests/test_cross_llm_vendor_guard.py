"""Unit tests for the cross_llm_prediction vendor-guard paired primitive (M-03).

Exercises the guard/rejection logic as a paired primitive using stub/mock
responses — no live LLM calls, no network, no disk I/O.

Cases:
  (a) Two backends from the SAME vendor → consensus claim REJECTED by guard.
  (b) Two backends from DISTINCT vendors that agree  → consensus ACCEPTED.
  (c) Two backends from DISTINCT vendors that disagree → no consensus.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Wire the skill module without installing it.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "cross_llm_prediction"))

from skill import (  # noqa: E402
    _overlap,
    _validate_distinct_vendors,
    _vendor_of,
)


# ---------------------------------------------------------------------------
# Vendor-family mapping sanity checks
# ---------------------------------------------------------------------------

def test_vendor_of_claude_variants():
    assert _vendor_of("claude") == "anthropic"
    assert _vendor_of("claude-3-opus") == "anthropic"
    assert _vendor_of("claude-sonnet-4") == "anthropic"


def test_vendor_of_openai_variants():
    assert _vendor_of("codex") == "openai-codex"
    assert _vendor_of("gpt-4o") == "openai-codex"
    assert _vendor_of("openai-text") == "openai-codex"


def test_vendor_of_google_variants():
    assert _vendor_of("gemini-pro") == "google"
    assert _vendor_of("google-palm") == "google"


def test_vendor_of_unknown_returns_identity():
    # Unknown vendor → treated as its own distinct family.
    assert _vendor_of("kimi") == "kimi"
    assert _vendor_of("mistral") == "mistral"


# ---------------------------------------------------------------------------
# (a) Same-vendor pair → REJECTED
# ---------------------------------------------------------------------------

def test_same_vendor_two_claude_snapshots_rejected():
    """Two claude aliases share the anthropic vendor family — guard raises."""
    with pytest.raises(ValueError, match="2 distinct vendors"):
        _validate_distinct_vendors(["claude", "claude-3-opus"])


def test_same_vendor_two_openai_variants_rejected():
    with pytest.raises(ValueError, match="2 distinct vendors"):
        _validate_distinct_vendors(["codex", "gpt-4o"])


def test_same_vendor_single_backend_rejected():
    """A solo backend also has only one vendor family."""
    with pytest.raises(ValueError, match="2 distinct vendors"):
        _validate_distinct_vendors(["claude"])


# ---------------------------------------------------------------------------
# (b) Distinct vendors, agreeing predictions → consensus ACCEPTED
# ---------------------------------------------------------------------------

def test_distinct_vendors_accepted_no_error():
    """claude (anthropic) + codex (openai-codex) → guard passes without exception."""
    # Should not raise.
    _validate_distinct_vendors(["claude", "codex"])


def test_distinct_vendors_accepted_three_vendors():
    _validate_distinct_vendors(["claude", "codex", "gemini-pro"])


def test_agreeing_predictions_give_full_overlap():
    """When two vendors predict the same top-K indices, overlap == 1.0."""
    indices_a = [0, 3, 7, 12, 5]   # vendor A (anthropic)
    indices_b = [0, 3, 7, 12, 5]   # vendor B (openai-codex) — identical

    # Guard accepts the pair.
    _validate_distinct_vendors(["claude", "codex"])

    # Consensus is confirmed by overlap.
    score = _overlap(indices_a, indices_b)
    assert score == 1.0, f"expected full overlap, got {score}"


def test_partial_agreement_gives_partial_overlap():
    """Partial set match gives a fractional overlap (not full consensus)."""
    indices_a = [0, 3, 7, 12, 5]
    indices_b = [0, 3, 7, 99, 88]   # 3 of 5 match

    _validate_distinct_vendors(["claude", "codex"])
    score = _overlap(indices_a, indices_b)
    assert 0.0 < score < 1.0


# ---------------------------------------------------------------------------
# (c) Distinct vendors, disagreeing predictions → no consensus
# ---------------------------------------------------------------------------

def test_distinct_vendors_disagreeing_no_consensus():
    """Two different-vendor predictions that share no indices → overlap == 0."""
    indices_a = [0, 1, 2, 3, 4]   # vendor A
    indices_b = [10, 11, 12, 13, 14]  # vendor B — completely different

    _validate_distinct_vendors(["claude", "codex"])
    score = _overlap(indices_a, indices_b)
    assert score == 0.0, f"expected zero overlap (no consensus), got {score}"


def test_vendor_guard_paired_primitive_summary():
    """Integration-style check: exercise all three guard outcomes in sequence."""
    # (a) same vendor → rejected
    with pytest.raises(ValueError):
        _validate_distinct_vendors(["claude", "claude-sonnet-4"])

    # (b) distinct vendors, agree → accepted + full overlap
    _validate_distinct_vendors(["claude", "gemini-pro"])
    assert _overlap([0, 1, 2], [0, 1, 2]) == 1.0

    # (c) distinct vendors, disagree → accepted guard, but zero consensus score
    _validate_distinct_vendors(["claude", "gemini-pro"])
    assert _overlap([0, 1, 2], [5, 6, 7]) == 0.0
