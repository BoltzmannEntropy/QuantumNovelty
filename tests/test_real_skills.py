"""Tests for the 5 newly-implemented skills (literature_surfacer,
book_acquirer, cross_llm_prediction, ablation_designer, pareto_explorer).

NO network. NO LLM. Just structural / contract / unit tests.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"


def _load(skill: str, alias: str):
    common = str(SKILLS / "common")
    if common not in sys.path:
        sys.path.insert(0, common)
    p = SKILLS / skill / "skill.py"
    spec = importlib.util.spec_from_file_location(alias, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# =========================================================================
# literature_surfacer
# =========================================================================

def test_literature_dedupe_keeps_richer_record():
    ls = _load("literature_surfacer", "qn_lit_surf")
    # Same arxiv_id, no DOI for either — they should collapse on key (arxiv_id).
    a = ls.SourceHit(title="X", authors=[], year="2024",
                     venue="arXiv", doi=None, arxiv_id="2401.001",
                     abstract="", source="arxiv")
    b = ls.SourceHit(title="X", authors=[], year="2024",
                     venue="arXiv", doi=None, arxiv_id="2401.001",
                     abstract="rich abstract", source="crossref",
                     cited_by=10)
    deduped = ls.dedupe_hits([a, b])
    assert len(deduped) == 1
    # The hit with the abstract + cited_by should win.
    assert deduped[0].abstract == "rich abstract"
    assert deduped[0].cited_by == 10


def test_literature_dedupe_preserves_distinct_dois():
    """Records with different DOIs are NOT deduped."""
    ls = _load("literature_surfacer", "qn_lit_surf_dist")
    a = ls.SourceHit(title="X", authors=[], year="2024",
                     venue="arXiv", doi="10.1/xx", arxiv_id="2401.001",
                     abstract="", source="arxiv")
    b = ls.SourceHit(title="X", authors=[], year="2024",
                     venue="arXiv", doi="10.1/yy", arxiv_id="2401.001",
                     abstract="rich abstract", source="crossref",
                     cited_by=10)
    deduped = ls.dedupe_hits([a, b])
    # Different DOIs → keep both.
    assert len(deduped) == 2


def test_literature_hit_to_card_truncates_long_abstracts():
    ls = _load("literature_surfacer", "qn_lit_surf2")
    h = ls.SourceHit(title="X", authors=[], year="", venue="",
                     doi=None, arxiv_id=None,
                     abstract="a" * 5000, source="arxiv")
    card = ls.hit_to_card(h)
    assert len(card["abstract"]) <= 1000


# =========================================================================
# book_acquirer
# =========================================================================

def test_book_acquirer_no_queries_returns_error(tmp_path):
    r = subprocess.run(
        ["bash", str(SKILLS / "book_acquirer" / "run.sh"),
         "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 2
    assert "queries" in r.stderr.lower()


def test_book_acquirer_inline_queries_runs_without_key(tmp_path, monkeypatch):
    """With queries supplied but no key, every download returns no_key."""
    monkeypatch.delenv("ANNAS_ARCHIVE_KEY", raising=False)
    # We want to test the wrapper handles inline queries; but the search
    # itself hits the network. Bypass by setting an unreachable mirror.
    monkeypatch.setenv("QN_ANNAS_MIRROR", "http://127.0.0.1:1")
    monkeypatch.setenv("QN_ANNAS_RATE_SECONDS", "0")
    r = subprocess.run(
        ["bash", str(SKILLS / "book_acquirer" / "run.sh"),
         "--queries", "Trotter quantum simulation",
         "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=30
    )
    assert r.returncode == 0
    report = json.loads(
        (tmp_path / "acquire_report.json").read_text()
    )
    assert isinstance(report, list)
    assert report[0]["query"] == "Trotter quantum simulation"
    # No-network mirror → search_status should be "network"
    assert report[0]["search_status"] == "network"


# =========================================================================
# cross_llm_prediction
# =========================================================================

def test_cross_llm_rejects_same_vendor():
    """Two claude snapshots must be rejected (falsifiability)."""
    cxl = _load("cross_llm_prediction", "qn_xllm")
    with pytest.raises(ValueError, match="distinct vendors"):
        cxl._validate_distinct_vendors(["claude", "claude-haiku"])


def test_cross_llm_accepts_different_vendors():
    cxl = _load("cross_llm_prediction", "qn_xllm2")
    # Should not raise
    cxl._validate_distinct_vendors(["claude", "codex"])


def test_cross_llm_vendor_mapping():
    cxl = _load("cross_llm_prediction", "qn_xllm3")
    assert cxl._vendor_of("claude") == "anthropic"
    assert cxl._vendor_of("claude-sonnet-4-X") == "anthropic"
    assert cxl._vendor_of("codex") == "openai-codex"
    assert cxl._vendor_of("gpt-5") == "openai-codex"
    assert cxl._vendor_of("gemini-pro") == "google"


def test_cross_llm_geometry_sweep_parser():
    cxl = _load("cross_llm_prediction", "qn_xllm4")
    rows = cxl._parse_geometry_sweep("R_OH=0.7,0.96,1.5 A")
    assert len(rows) == 3
    assert rows[0]["variable"] == "R_OH"
    assert rows[0]["value"] == 0.7
    assert rows[0]["unit"] == "A"


def test_cross_llm_overlap_metric():
    cxl = _load("cross_llm_prediction", "qn_xllm5")
    assert cxl._overlap([1, 2, 3], [1, 2, 3]) == 1.0
    assert cxl._overlap([1, 2, 3], [4, 5, 6]) == 0.0
    assert cxl._overlap([1, 2, 3], [1, 4, 5]) == 1/3
    assert cxl._overlap([], [1, 2]) == 0.0


def test_cross_llm_smoke_refuses_single_vendor(tmp_path):
    r = subprocess.run(
        ["bash", str(SKILLS / "cross_llm_prediction" / "run.sh"),
         "--hamiltonian-id", "test",
         "--geometry-sweep", "R=1.0",
         "--llms", "claude,claude-haiku",
         "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 2
    assert "distinct vendors" in r.stderr.lower()


# =========================================================================
# ablation_designer
# =========================================================================

def test_ablation_rejects_unknown_axis(tmp_path):
    r = subprocess.run(
        ["bash", str(SKILLS / "ablation_designer" / "run.sh"),
         "--axis", "not-a-real-axis",
         "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 2


def test_ablation_plan_only_writes_files(tmp_path):
    r = subprocess.run(
        ["bash", str(SKILLS / "ablation_designer" / "run.sh"),
         "--axis", "llm-mutator-onoff",
         "--hamiltonian-id", "test",
         "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 0
    assert (tmp_path / "ablation_plan.md").is_file()
    assert (tmp_path / "ablation_results.json").is_file()
    plan = (tmp_path / "ablation_plan.md").read_text()
    assert "llm-on" in plan
    assert "random-on" in plan


def test_ablation_compute_summary():
    ad = _load("ablation_designer", "qn_abl")
    results = {
        "axis": "llm-mutator-onoff",
        "hamiltonian_id": "test",
        "variants": {
            "llm-on": [
                {"seed": 0, "delta_e_mha": 0.005, "n_proposals_consumed": 10},
                {"seed": 1, "delta_e_mha": 0.006, "n_proposals_consumed": 12},
                {"seed": 2, "delta_e_mha": 0.004, "n_proposals_consumed": 8},
            ],
            "random-on": [
                {"seed": 0, "delta_e_mha": 0.5, "n_proposals_consumed": 30},
                {"seed": 1, "delta_e_mha": 0.6, "n_proposals_consumed": 35},
            ],
        }
    }
    summary = ad.compute_summary(results)
    assert summary["per_variant"]["llm-on"]["n_seeds"] == 3
    assert summary["per_variant"]["llm-on"]["delta_e_mha_median"] == 0.005
    # LLM-on median should be << random-on median
    assert (summary["per_variant"]["llm-on"]["delta_e_mha_median"]
            < summary["per_variant"]["random-on"]["delta_e_mha_median"])


# =========================================================================
# pareto_explorer
# =========================================================================

def test_pareto_strict_dominates():
    pe = _load("pareto_explorer", "qn_pareto")
    a = {"energy_ha": -7.86, "params": 10, "ops": 14, "cnots": 4}
    b = {"energy_ha": -7.85, "params": 3, "ops": 198, "cnots": 64}
    # Neither dominates: a has better energy but b has fewer params.
    assert not pe._strict_dominates(a, b, ["energy_ha", "params"])
    assert not pe._strict_dominates(b, a, ["energy_ha", "params"])
    # On (ops, cnots) alone, a dominates b
    assert pe._strict_dominates(a, b, ["ops", "cnots"])


def test_pareto_archive_update_drops_dominated():
    pe = _load("pareto_explorer", "qn_pareto2")
    archive = [
        {"label": "weak", "energy_ha": -7.0, "params": 100,
         "ops": 1000, "cnots": 500},
    ]
    new_candidate = {"label": "strong", "energy_ha": -7.86,
                     "params": 10, "ops": 14, "cnots": 4}
    new_archive = pe._update_archive(archive, new_candidate,
                                     ["energy_ha", "params", "ops", "cnots"])
    assert len(new_archive) == 1
    assert new_archive[0]["label"] == "strong"


def test_pareto_extract_python_blocks():
    pe = _load("pareto_explorer", "qn_pareto3")
    text = """Some prose.
```python
def build_ansatz(params):
    return None
```
More prose.
```python
def build_ansatz2(params):
    return None
```
"""
    blocks = pe._extract_python_blocks(text)
    assert len(blocks) == 2
    assert "build_ansatz(" in blocks[0]
    assert "build_ansatz2(" in blocks[1]


def test_pareto_plan_only_smoke(tmp_path):
    r = subprocess.run(
        ["bash", str(SKILLS / "pareto_explorer" / "run.sh"),
         "--hamiltonian", "LiH_4q",
         "--baseline", "UCCSD,HEA",
         "--plan-only",
         "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 0
    archive = json.loads((tmp_path / "archive.json").read_text())
    labels = [r["label"] for r in archive["rows"]]
    assert "UCCSD" in labels
    assert "HEA" in labels
    assert archive["_plan_only"] is True


def test_pareto_defaults_to_builtin_and_validates_hamiltonian(tmp_path):
    """Without --evaluator-cmd the built-in evaluator is the default;
    a Hamiltonian outside its registry fails fast with the registry
    listed (LiH needs an external evaluator)."""
    r = subprocess.run(
        ["bash", str(SKILLS / "pareto_explorer" / "run.sh"),
         "--hamiltonian", "LiH_4q",
         "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=30
    )
    assert r.returncode == 2
    assert "built-in registry" in r.stderr


# =========================================================================
# process_summary alias resolution (regression for the CQE-path bug)
# =========================================================================

def test_process_summary_resolves_stage_aliases(tmp_path):
    """process_summary._find_artifact resolves stage_<N>_<X> aliases."""
    ps = _load("process_summary", "qn_ps_aliases")
    # Build a fake run-dir with stage_3_audit/audit_claims.py present.
    stage_dir = tmp_path / "stage_3_audit"
    stage_dir.mkdir()
    (stage_dir / "audit_claims.py").write_text("# dummy", encoding="utf-8")
    p = ps._find_artifact(tmp_path, "novelty_audit", "audit_claims.py")
    assert p is not None
    assert p.name == "audit_claims.py"
    # And the direct-name layout still works:
    direct_dir = tmp_path / "novelty_audit"
    direct_dir.mkdir()
    (direct_dir / "novelty_verdict.json").write_text("{}", encoding="utf-8")
    p2 = ps._find_artifact(tmp_path, "novelty_audit", "novelty_verdict.json")
    assert p2 is not None
    assert p2.parent.name == "novelty_audit"
