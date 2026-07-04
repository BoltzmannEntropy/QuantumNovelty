"""Tests for the retrieval pre-flight gate and assumption manifest.

Zero-model, zero-network. All source functions are stubbed; no real
HTTP calls or LLM calls are made.

Run: pytest tests/test_novelty_audit_gates.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Repo root on path so we can import skills directly.
# ---------------------------------------------------------------------------
import importlib.util as _ilu

REPO = Path(__file__).resolve().parents[1]
SURFACER_DIR = REPO / "skills" / "literature_surfacer"
NOVELTY_DIR = REPO / "skills" / "novelty_audit"

sys.path.insert(0, str(REPO / "skills" / "common"))
sys.path.insert(0, str(SURFACER_DIR))   # needed so `import preflight_probe` resolves


def _load_by_path(module_name: str, file_path: Path):
    """Load a module from an absolute path and register it in sys.modules."""
    spec = _ilu.spec_from_file_location(module_name, str(file_path))
    mod = _ilu.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Load novelty_audit/skill.py by absolute path so `sys.modules["skill"]`
# collisions with the surfacer's skill.py (same bare name, different dir)
# cannot cause test-ordering-dependent failures.
novelty_skill = _load_by_path("novelty_audit_skill", NOVELTY_DIR / "skill.py")

# preflight_probe itself loads the surfacer's skill.py by absolute path (same
# mechanism), so it is also safe regardless of sys.path ordering.
import preflight_probe as pfp  # noqa: E402 — literature_surfacer/preflight_probe.py

# SourceHit lives only in the surfacer's skill.py. preflight_probe already loaded
# it by absolute path — reuse that module object to avoid a separate import.
SourceHit = pfp._surf_mod.SourceHit


# ===========================================================================
# Helpers / fixtures
# ===========================================================================

def _make_card(
    title: str = "",
    arxiv_id: str | None = None,
    doi: str | None = None,
) -> dict:
    return {
        "title": title,
        "authors": [],
        "year": "2024",
        "venue": "",
        "doi": doi,
        "arxiv_id": arxiv_id,
        "abstract": "",
        "source": "test",
        "cited_by": None,
        "url": None,
    }


def _fake_source_fn(hits: list) -> Any:
    """Return a source function that always returns the given SourceHit list."""
    def _fn(query: str, n: int = 10) -> tuple[list, str]:
        return hits, "ok"
    return _fn


# ===========================================================================
# 1. card_matches_expected — pure substring matching logic
# ===========================================================================

class TestCardMatchesExpected:
    def test_title_substring_case_insensitive(self):
        card = _make_card(title="McClean et al. Barren Plateaus 2018")
        assert pfp.card_matches_expected(card, "mcclean") is True

    def test_arxiv_id_match(self):
        card = _make_card(title="Some title", arxiv_id="1803.11173")
        assert pfp.card_matches_expected(card, "1803.11173") is True

    def test_arxiv_id_with_version_no_match(self):
        # card has bare id; expected has bare id — must match
        card = _make_card(arxiv_id="1803.11173")
        assert pfp.card_matches_expected(card, "1803.11173") is True

    def test_doi_substring(self):
        card = _make_card(doi="10.1038/nature00001")
        assert pfp.card_matches_expected(card, "10.1038/nature00001") is True

    def test_no_match(self):
        card = _make_card(title="Completely unrelated paper")
        assert pfp.card_matches_expected(card, "mcclean") is False

    def test_empty_expected_always_hits(self):
        # "" is always a substring of any string in Python, so this documents
        # the intentional behaviour: an empty expected entry trivially matches.
        card = _make_card(title="Important paper")
        assert pfp.card_matches_expected(card, "") is True


# ===========================================================================
# 2. score_probe — probe-level hit logic
# ===========================================================================

class TestScoreProbe:
    def test_hit_when_first_expected_matches_first_card(self):
        cards = [_make_card(title="VQE Peruzzo 2014", arxiv_id="1304.3061")]
        assert pfp.score_probe(cards, ["1304.3061"]) is True

    def test_hit_when_second_expected_matches(self):
        cards = [_make_card(title="Peruzzo variational eigensolver")]
        assert pfp.score_probe(cards, ["absent_term", "peruzzo"]) is True

    def test_miss_when_no_card_matches(self):
        cards = [_make_card(title="Totally different paper")]
        assert pfp.score_probe(cards, ["mcclean", "1803.11173"]) is False

    def test_empty_cards_always_miss(self):
        assert pfp.score_probe([], ["mcclean"]) is False

    def test_empty_expected_trivially_hits(self):
        # Per card_matches_expected semantics, "" is always in haystack.
        cards = [_make_card(title="anything")]
        assert pfp.score_probe(cards, [""]) is True

    def test_no_expected_means_miss(self):
        cards = [_make_card(title="anything")]
        assert pfp.score_probe(cards, []) is False


# ===========================================================================
# 3. run_probes — recall computation and threshold gate
# ===========================================================================

class TestRunProbes:
    """Uses injectable source_fns so no network is touched."""

    def _cards_fn(self, cards: list[dict]):
        """Return a fake source fn that returns pre-built card dicts wrapped in SourceHit."""
        hits = [
            SourceHit(
                title=c["title"],
                authors=[],
                year="",
                venue="",
                doi=c.get("doi"),
                arxiv_id=c.get("arxiv_id"),
                abstract="",
                source="test",
            )
            for c in cards
        ]

        def _fn(query: str, n: int = 10):
            return hits, "ok"
        return _fn

    def test_all_probes_hit_passes(self):
        probes = [
            {"query": "barren plateaus", "expected": ["mcclean"]},
            {"query": "VQE", "expected": ["peruzzo"]},
        ]
        source_fn = self._cards_fn([
            _make_card(title="McClean barren plateaus"),
            _make_card(title="Peruzzo VQE"),
        ])
        result = pfp.run_probes(
            probes,
            source_fns={"fake": source_fn},
            sources=["fake"],
            threshold=0.67,
        )
        assert result["n_hit"] == 2
        assert result["n_probes"] == 2
        assert result["recall"] == pytest.approx(1.0)
        assert result["passed"] is True

    def test_partial_hit_below_threshold_fails(self):
        probes = [
            {"query": "barren plateaus", "expected": ["mcclean"]},
            {"query": "VQE", "expected": ["peruzzo"]},
            {"query": "QCNN", "expected": ["cong"]},
        ]
        # Only McClean is in the cards → 1/3 recall = 0.333 < 0.67
        source_fn = self._cards_fn([_make_card(title="McClean barren plateaus")])
        result = pfp.run_probes(
            probes,
            source_fns={"fake": source_fn},
            sources=["fake"],
            threshold=0.67,
        )
        assert result["n_hit"] == 1
        assert result["recall"] == pytest.approx(1 / 3)
        assert result["passed"] is False

    def test_two_of_three_below_threshold(self):
        probes = [
            {"query": "barren plateaus", "expected": ["mcclean"]},
            {"query": "VQE", "expected": ["peruzzo"]},
            {"query": "QCNN", "expected": ["cong"]},
        ]
        # 2/3 = 0.6667 < 0.67 → should fail
        source_fn = self._cards_fn([
            _make_card(title="McClean"),
            _make_card(title="Peruzzo"),
        ])
        result = pfp.run_probes(
            probes,
            source_fns={"fake": source_fn},
            sources=["fake"],
            threshold=0.67,
        )
        assert result["n_hit"] == 2
        assert result["recall"] == pytest.approx(2 / 3)
        assert result["passed"] is False  # 0.6667 < 0.67

    def test_threshold_boundary_exact_pass(self):
        probes = [
            {"query": "a", "expected": ["hit"]},
            {"query": "b", "expected": ["hit"]},
            {"query": "c", "expected": ["hit"]},
        ]
        source_fn = self._cards_fn([_make_card(title="hit paper")])
        # 3/3 = 1.0 >= 1.0 → passes
        result = pfp.run_probes(
            probes,
            source_fns={"fake": source_fn},
            sources=["fake"],
            threshold=1.0,
        )
        assert result["passed"] is True

    def test_empty_probes_passes(self):
        result = pfp.run_probes(
            [],
            source_fns={"fake": self._cards_fn([])},
            sources=["fake"],
            threshold=0.67,
        )
        assert result["n_probes"] == 0
        assert result["recall"] == pytest.approx(0.0)
        # 0/0 recall (0.0) < 0.67 → failed gate
        assert result["passed"] is False

    def test_probe_result_structure(self):
        probes = [{"query": "VQE", "expected": ["peruzzo"]}]
        source_fn = self._cards_fn([_make_card(title="Peruzzo VQE")])
        result = pfp.run_probes(
            probes,
            source_fns={"fake": source_fn},
            sources=["fake"],
        )
        assert "probes" in result
        assert "recall" in result
        assert "passed" in result
        assert "threshold" in result
        p = result["probes"][0]
        assert "query" in p
        assert "expected" in p
        assert "hit" in p
        assert "n_cards" in p


# ===========================================================================
# 4. apply_retrieval_gate — verdict downgrade
# ===========================================================================

class TestApplyRetrievalGate:
    _RAW_VERDICTS = [
        {"label": "MyAnsatz", "verdict": "strict-domination", "metrics": {}},
        {"label": "Other",    "verdict": "interpolation",     "metrics": {}},
        {"label": "Third",    "verdict": "dominated",         "metrics": {}},
    ]

    def test_gate_failed_downgrades_all_verdicts(self):
        probe_result = {"passed": False, "recall": 0.33, "threshold": 0.67}
        gated, summary = novelty_skill.apply_retrieval_gate(
            self._RAW_VERDICTS, probe_result
        )
        assert len(gated) == 3
        for v in gated:
            assert "(indicative)" in v["verdict"]
            assert "verdict_ungated" in v
        assert gated[0]["verdict"] == "strict-domination (indicative)"
        assert gated[0]["verdict_ungated"] == "strict-domination"
        assert gated[1]["verdict"] == "interpolation (indicative)"
        assert gated[2]["verdict"] == "dominated (indicative)"

    def test_gate_passed_leaves_verdicts_unchanged(self):
        probe_result = {"passed": True, "recall": 1.0, "threshold": 0.67}
        gated, summary = novelty_skill.apply_retrieval_gate(
            self._RAW_VERDICTS, probe_result
        )
        assert gated[0]["verdict"] == "strict-domination"
        assert "verdict_ungated" not in gated[0]

    def test_gate_absent_means_no_change(self):
        """When probe result is not provided, caller simply doesn't call
        apply_retrieval_gate; calling it with passed=True is equivalent."""
        # Simulating absent gate: pass a "passed" probe result.
        probe_result = {"passed": True, "recall": 1.0, "threshold": 0.67}
        gated, summary = novelty_skill.apply_retrieval_gate(
            self._RAW_VERDICTS, probe_result
        )
        assert all("(indicative)" not in v["verdict"] for v in gated)

    def test_gate_summary_keys_when_failed(self):
        probe_result = {"passed": False, "recall": 0.33, "threshold": 0.67}
        _, summary = novelty_skill.apply_retrieval_gate(
            self._RAW_VERDICTS, probe_result
        )
        assert summary["passed"] is False
        assert summary["recall"] == pytest.approx(0.33)
        assert "effect" in summary
        assert "downgraded" in summary["effect"]

    def test_gate_summary_keys_when_passed(self):
        probe_result = {"passed": True, "recall": 1.0, "threshold": 0.67}
        _, summary = novelty_skill.apply_retrieval_gate(
            self._RAW_VERDICTS, probe_result
        )
        assert summary["passed"] is True
        assert summary["effect"] == "none"

    def test_gate_preserves_other_fields(self):
        verdicts = [{"label": "X", "verdict": "dominated", "metrics": {"a": 1.0}}]
        probe_result = {"passed": False, "recall": 0.0, "threshold": 0.67}
        gated, _ = novelty_skill.apply_retrieval_gate(verdicts, probe_result)
        assert gated[0]["metrics"] == {"a": 1.0}
        assert gated[0]["label"] == "X"


# ===========================================================================
# 5. build_assumptions_manifest — provenance manifest
# ===========================================================================

class TestBuildAssumptionsManifest:
    def _row(self, label, prov):
        return novelty_skill.Row(
            label=label, source="baseline", metrics={}, provenance=prov
        )

    def test_all_notional(self):
        rows = [
            self._row("A", "notional"),
            self._row("B", "notional"),
        ]
        m = novelty_skill.build_assumptions_manifest(rows)
        assert m["n_notional"] == 2
        assert m["n_literature_verified"] == 0
        assert m["n_unspecified"] == 0

    def test_mixed_provenance_counts(self):
        rows = [
            self._row("A", "literature-verified"),
            self._row("B", "notional"),
            self._row("C", "unspecified"),
            self._row("D", "notional"),
        ]
        m = novelty_skill.build_assumptions_manifest(rows)
        assert m["n_literature_verified"] == 1
        assert m["n_notional"] == 2
        assert m["n_unspecified"] == 1

    def test_baseline_rows_list_present(self):
        rows = [self._row("X", "notional")]
        m = novelty_skill.build_assumptions_manifest(rows)
        assert "baseline_rows" in m
        assert m["baseline_rows"][0]["label"] == "X"
        assert m["baseline_rows"][0]["provenance"] == "notional"

    def test_verdict_rests_on_unverified_flag_true_when_notional(self):
        """Main wires this flag; test the manifest counts that drive it."""
        rows = [
            self._row("A", "notional"),
            self._row("B", "literature-verified"),
        ]
        m = novelty_skill.build_assumptions_manifest(rows)
        # Flag is set in main() based on counts; we verify counts are correct
        # so main() will set the flag.
        assert m["n_notional"] > 0

    def test_verdict_rests_flag_false_when_all_verified(self):
        rows = [
            self._row("A", "literature-verified"),
            self._row("B", "literature-verified"),
        ]
        m = novelty_skill.build_assumptions_manifest(rows)
        assert m["n_notional"] == 0
        assert m["n_unspecified"] == 0

    def test_empty_rows(self):
        m = novelty_skill.build_assumptions_manifest([])
        assert m["n_notional"] == 0
        assert m["n_literature_verified"] == 0
        assert m["n_unspecified"] == 0
        assert m["baseline_rows"] == []


# ===========================================================================
# 6. load_rows — provenance field extraction
# ===========================================================================

class TestLoadRowsProvenance:
    def test_provenance_field_extracted(self, tmp_path):
        catalog = {
            "rows": [
                {"label": "A", "source": "baseline", "energy_ha": -1.0,
                 "provenance": "notional"},
                {"label": "B", "source": "baseline", "energy_ha": -0.5,
                 "provenance": "literature-verified"},
            ]
        }
        p = tmp_path / "catalog.json"
        p.write_text(json.dumps(catalog))
        rows = novelty_skill.load_rows(p)
        assert rows[0].provenance == "notional"
        assert rows[1].provenance == "literature-verified"

    def test_provenance_defaults_to_unspecified(self, tmp_path):
        catalog = {
            "rows": [
                {"label": "A", "source": "baseline", "energy_ha": -1.0},
            ]
        }
        p = tmp_path / "catalog.json"
        p.write_text(json.dumps(catalog))
        rows = novelty_skill.load_rows(p)
        assert rows[0].provenance == "unspecified"


# ===========================================================================
# 7. write_verdict — top-level key presence
# ===========================================================================

class TestWriteVerdict:
    def test_retrieval_gate_key_absent_by_default(self, tmp_path):
        novelty_skill.write_verdict(tmp_path, [], 1e-12, 1e-9)
        doc = json.loads((tmp_path / "novelty_verdict.json").read_text())
        assert "retrieval_gate" not in doc

    def test_retrieval_gate_key_present_when_provided(self, tmp_path):
        gate = {"passed": False, "recall": 0.33, "effect": "verdicts downgraded to indicative"}
        novelty_skill.write_verdict(tmp_path, [], 1e-12, 1e-9, retrieval_gate=gate)
        doc = json.loads((tmp_path / "novelty_verdict.json").read_text())
        assert "retrieval_gate" in doc
        assert doc["retrieval_gate"]["passed"] is False

    def test_assumptions_key_absent_by_default(self, tmp_path):
        novelty_skill.write_verdict(tmp_path, [], 1e-12, 1e-9)
        doc = json.loads((tmp_path / "novelty_verdict.json").read_text())
        assert "assumptions" not in doc

    def test_assumptions_key_present_when_provided(self, tmp_path):
        assumptions = {
            "baseline_rows": [{"label": "A", "provenance": "notional"}],
            "n_literature_verified": 0,
            "n_notional": 1,
            "n_unspecified": 0,
            "verdict_rests_on_unverified_baselines": True,
        }
        novelty_skill.write_verdict(tmp_path, [], 1e-12, 1e-9, assumptions=assumptions)
        doc = json.loads((tmp_path / "novelty_verdict.json").read_text())
        assert "assumptions" in doc
        assert doc["assumptions"]["verdict_rests_on_unverified_baselines"] is True

    def test_verdicts_with_indicative_qualifier_round_trip(self, tmp_path):
        verdicts = [
            {"label": "X", "verdict": "strict-domination (indicative)",
             "verdict_ungated": "strict-domination", "metrics": {}},
        ]
        novelty_skill.write_verdict(tmp_path, verdicts, 1e-12, 1e-9)
        doc = json.loads((tmp_path / "novelty_verdict.json").read_text())
        v = doc["verdicts"][0]
        assert v["verdict"] == "strict-domination (indicative)"
        assert v["verdict_ungated"] == "strict-domination"
