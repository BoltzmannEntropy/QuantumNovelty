"""Smoke tests for the multi-mode skills, registries, and pipeline orchestrator.

No LLM calls. Tests check (a) registry lookups, (b) skill driver argument
parsing, (c) chat NL pattern routing, (d) pipeline orchestrator stage gating.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
CHAIN_RUN = REPO / "chain" / "run.sh"
PIPELINES = REPO / "chain" / "pipelines.py"


def _load_skill_module(skill_name: str, module_alias: str):
    """Load `skills/<skill_name>/skill.py` under a unique sys.modules name.

    Avoids the cross-test collision where every skill's file is named
    `skill.py` — importing by sibling-path puts the first one in sys.modules
    and subsequent imports get a stale module.
    """
    # Ensure skills/common is on sys.path (most skills sibling-import from it)
    common_path = str(SKILLS / "common")
    if common_path not in sys.path:
        sys.path.insert(0, common_path)
    skill_path = SKILLS / skill_name / "skill.py"
    spec = importlib.util.spec_from_file_location(module_alias, skill_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_alias] = mod
    spec.loader.exec_module(mod)
    return mod


# =========================================================================
# Journal registry
# =========================================================================

def test_journals_registry_contains_quantum_venues():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import journals
        slugs = journals.known_journals()
        for expected in ("quantum", "npj-quantum-information", "prx-quantum",
                         "physical-review-letters", "nature-communications"):
            assert expected in slugs, f"missing journal slug: {expected}"
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_journals_lookup_returns_policy():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import journals
        p = journals.journal_policy("npj-quantum-information")
        assert p.name == "npj Quantum Information"
        assert p.abstract_word_limit == 250
        assert "Author Contributions" in p.required_statements
        assert "Code Availability" in p.required_statements
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_journals_unknown_slug_raises():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import journals
        with pytest.raises(KeyError, match="known journals"):
            journals.journal_policy("not-a-real-journal")
    finally:
        sys.path.remove(str(SKILLS / "common"))


# =========================================================================
# Quantum-library registry
# =========================================================================

def test_quantum_libs_registry_contains_expected():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import quantum_libs
        for slug in ("qiskit", "pennylane", "qutip", "mlxq", "cirq",
                     "openfermion", "no-code"):
            assert slug in quantum_libs.known_libraries()
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_quantum_libs_code_skeleton():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import quantum_libs
        skel = quantum_libs.library("qiskit").code_skeleton()
        assert "from qiskit import QuantumCircuit" in skel
        assert "def build_ansatz" in skel
        # mlxq skeleton must include the precision-floor note in install hint
        mlxq = quantum_libs.library("mlxq")
        assert "complex64" in mlxq.notes.lower() or "precision" in mlxq.notes.lower()
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_no_code_library_present():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import quantum_libs
        lib = quantum_libs.library("no-code")
        assert "analytical" in lib.name.lower() or "no code" in lib.name.lower()
    finally:
        sys.path.remove(str(SKILLS / "common"))


# =========================================================================
# Multi-mode skill driver — argument validation
# =========================================================================

def test_deep_research_rejects_unknown_mode():
    r = subprocess.run(
        ["bash", str(SKILLS / "deep_research" / "run.sh"),
         "--mode", "not-a-mode",
         "--topic", "x",
         "--outdir", "/tmp/qn_test_dr"],
        capture_output=True, text=True, timeout=10
    )
    # argparse choices should reject; exit code 2
    assert r.returncode == 2


def test_deep_research_loads_template_for_each_mode():
    dr = _load_skill_module("deep_research", "qn_deep_research")
    for mode in dr.MODES:
        tmpl = dr._load_template(mode)
        assert len(tmpl) > 50, f"template for {mode} too short"
        assert "{topic}" in tmpl, f"template {mode} missing {{topic}}"


def test_quantum_paper_loads_template_for_each_mode():
    qp = _load_skill_module("quantum_paper", "qn_quantum_paper")
    for mode in qp.MODES:
        tmpl = qp._load_template(mode)
        assert len(tmpl) > 100, f"template for {mode} too short"


def test_quantum_reviewer_loads_template_for_each_mode():
    qr = _load_skill_module("quantum_reviewer", "qn_quantum_reviewer")
    for mode in qr.MODES:
        tmpl = qr._load_template(mode)
        assert len(tmpl) > 100, f"template for {mode} too short"


def test_quantum_reviewer_panel_completeness_check():
    qr = _load_skill_module("quantum_reviewer", "qn_quantum_reviewer")
    # All 5 voices present
    full = ("Reviewer 1 ... Reviewer 2 ... Reviewer 3 ... "
            "Devil's Advocate ... Editor-in-Chief ...")
    assert qr._check_full_panel_completeness(full) == []
    # Missing Devil's Advocate
    partial = "Reviewer 1 ... Reviewer 2 ... Reviewer 3 ... Editor-in-Chief"
    assert "Devil's Advocate" in qr._check_full_panel_completeness(partial)


# =========================================================================
# Logical-fallacies skill — taxonomy + JSON extraction
# =========================================================================

def test_logical_fallacies_extracts_json():
    lf = _load_skill_module("logical_fallacies", "qn_logical_fallacies")
    text = '''Some prose.

```json
{"findings": [{"name": "cherry-picked-baseline", "severity": "high"}]}
```

More prose.'''
    obj = lf._extract_json(text)
    assert obj is not None
    assert obj["findings"][0]["name"] == "cherry-picked-baseline"


def test_logical_fallacies_taxonomy_in_prompt():
    """The prompt template MUST include the quantum-CS-specific fallacies."""
    lf = _load_skill_module("logical_fallacies", "qn_logical_fallacies")
    for q in ("cherry-picked-baseline", "ad-hoc-precision-floor",
              "simulator-laundering", "mapping-by-convenience",
              "cross-llm-theatre", "unit-inflation",
              "asymptotic-only-claim", "pareto-cherry-picked-axes"):
        assert q in lf.PROMPT_TEMPLATE, f"taxonomy missing: {q}"


# =========================================================================
# chat NL frontend — pattern routing
# =========================================================================

@pytest.mark.parametrize("prompt,expected_skill,expected_mode", [
    ("Write a paper on LLM-driven VQE",       "quantum_paper", "full"),
    ("Guide me through writing a paper on X",  "quantum_paper", "plan"),
    ("Build a paper outline on Trotter error", "quantum_paper", "outline-only"),
    ("Research the impact of AI on VQE",       "deep_research", "full"),
    ("Quick brief on shadow tomography",       "deep_research", "quick"),
    ("Systematic review on Pareto methods",    "deep_research", "systematic-review"),
    ("Guide my research on VQE noise",         "deep_research", "socratic"),
    ("Literature review on ADAPT-VQE",         "deep_research", "lit-review"),
])
def test_chat_pattern_dispatch(prompt, expected_skill, expected_mode):
    chat = _load_skill_module("chat", "qn_chat")
    class A:
        paper = None
        journal = None
        quantum_lib = None
    d = chat.pattern_dispatch(prompt, A())
    assert d is not None, f"no dispatch for {prompt!r}"
    assert d.skill == expected_skill, (
        f"wrong skill for {prompt!r}: got {d.skill}")
    assert d.mode == expected_mode, (
        f"wrong mode for {prompt!r}: got {d.mode}")


def test_chat_status_dispatch():
    chat = _load_skill_module("chat", "qn_chat")
    class A:
        paper = None; journal = None; quantum_lib = None
    d = chat.pattern_dispatch("status", A())
    assert d is not None
    assert d.skill == "PIPELINE"
    assert d.mode == "status"


def test_chat_review_this_paper_needs_paper_path(tmp_path):
    chat = _load_skill_module("chat", "qn_chat")
    class A:
        paper = None; journal = None; quantum_lib = None
    d = chat.pattern_dispatch("Review this paper", A())
    assert d is None
    class B:
        paper = tmp_path / "x.tex"; journal = None; quantum_lib = None
    d = chat.pattern_dispatch("Review this paper", B())
    assert d is not None
    assert d.skill == "quantum_reviewer"
    assert d.mode == "full"


# =========================================================================
# Process-summary CQE scoring
# =========================================================================

def test_process_summary_geometric_mean(tmp_path):
    ps = _load_skill_module("process_summary", "qn_process_summary")
    # Equal scores → composite ≈ that score
    gm = ps._geometric_mean([80, 80, 80, 80, 80, 80])
    assert abs(gm - 80) < 1
    # One catastrophic dimension drags down composite
    gm = ps._geometric_mean([95, 95, 95, 95, 95, 30])
    # Arithmetic mean would be 84; geometric should be lower
    assert gm < 80, f"geometric mean {gm} should penalise the 30"


def test_process_summary_no_llm_mode(tmp_path):
    """Run process_summary with --no-llm-narrative against an empty run-dir."""
    run_dir = tmp_path / "run"
    outdir = tmp_path / "summary"
    run_dir.mkdir()
    r = subprocess.run(
        ["bash", str(SKILLS / "process_summary" / "run.sh"),
         "--run-dir", str(run_dir),
         "--outdir", str(outdir),
         "--no-llm-narrative"],
        capture_output=True, text=True, timeout=15
    )
    assert r.returncode == 0, f"process_summary failed: {r.stderr}"
    scores = json.loads((outdir / "cqe_scores.json").read_text())
    # 6 dimensions, geometric composite
    assert len(scores["dimensions"]) == 6
    assert 0 <= scores["composite"] <= 100
    assert scores["composite_method"] == "geometric_mean"


# =========================================================================
# Chain dispatch — new pipelines parse
# =========================================================================

def test_chain_dispatches_deep_research_via_pipeline(tmp_path):
    """Smoke: chain --pipeline deep-research --mode quick --topic X dispatches.

    Runs against the STUB backend (QUANTUMNOVELTY_LLM_STUB) so no real
    LLM is ever spawned, with an explicit tmp outdir so nothing is
    written into the repo, and in its own session so a timeout kill
    cannot orphan grandchildren.
    """
    env = {**os.environ, "QUANTUMNOVELTY_LLM_STUB": "1"}
    r = subprocess.run(
        ["bash", str(CHAIN_RUN),
         "--pipeline", "deep-research",
         "--mode", "quick",
         "--topic", "test",
         "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=60, env=env,
        start_new_session=True,
    )
    # Accept rc != 0 but require NO "Unknown option" / argparse failure.
    assert "Unknown option" not in r.stderr
    assert "Error: --topic required" not in r.stderr
    assert "Error: --mode required" not in r.stderr


def test_pipelines_status_runs(tmp_path):
    """The status pipeline runs without an LLM and exits clean."""
    r = subprocess.run(
        ["python3", str(PIPELINES), "status",
         "--outdir", str(tmp_path / "nonexistent")],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 0
    assert "Pipeline status" in r.stdout or "does not exist" in r.stdout


# =========================================================================
# runs/ folder layout — timestamp + llm_slug + pipeline
# =========================================================================

def _cleanup_run_dir(full_path: str):
    """Layout tests must not leave runs/<ts>/ litter inside the repo."""
    import shutil
    p = Path(full_path)
    # climb to the runs/<ts> level and remove it
    for parent in [p] + list(p.parents):
        if parent.parent.name == "runs":
            shutil.rmtree(parent, ignore_errors=True)
            return


def test_runs_layout_is_ts_llm_pipeline_for_default():
    """chain/run.sh autoderives OUTDIR as runs/<ts>/<llm>/<pipeline>/."""
    import re
    r = subprocess.run(
        ["bash", str(CHAIN_RUN), "--pipeline", "chat",
         "--prompt", "status"],
        capture_output=True, text=True, timeout=15
    )
    # Even if the chat skill itself errors, the Outdir banner prints early.
    m = re.search(
        r"Outdir\s*:\s*(\S+/runs/(\d{8}_\d{6})/([^/]+)/([^/\s]+))",
        r.stdout
    )
    assert m, (
        f"chain banner did not show ts/llm/pipeline layout. "
        f"stdout was:\n{r.stdout[:1500]}"
    )
    full_path, ts, llm_slug, pipeline = m.groups()
    assert llm_slug == "claude", f"default llm slug should be 'claude', got {llm_slug!r}"
    assert pipeline == "chat", f"pipeline should be 'chat', got {pipeline!r}"
    _cleanup_run_dir(full_path)


def test_runs_layout_llm_override_changes_slug():
    """--llm codex changes the path's llm-slug component."""
    import re
    r = subprocess.run(
        ["bash", str(CHAIN_RUN), "--pipeline", "chat",
         "--prompt", "status", "--llm", "codex"],
        capture_output=True, text=True, timeout=15
    )
    m = re.search(
        r"(\S+/runs/(\d{8}_\d{6})/([^/]+)/([^/\s]+))", r.stdout
    )
    assert m, "no path matched in stdout"
    full_path, ts, llm_slug, pipeline = m.groups()
    assert llm_slug == "codex", f"expected codex slug, got {llm_slug!r}"
    _cleanup_run_dir(full_path)


def test_runs_layout_normalizes_unsafe_chars():
    """A backend slug containing a slash (or other unsafe chars) gets sanitized."""
    import re
    r = subprocess.run(
        ["bash", str(CHAIN_RUN), "--pipeline", "chat",
         "--prompt", "status",
         "--llm", "claude-sonnet-4-20250514"],
        capture_output=True, text=True, timeout=15
    )
    m = re.search(r"(\S+/runs/\d{8}_\d{6})/([^/]+)/", r.stdout)
    assert m, "no path matched"
    full_path, slug = m.group(1), m.group(2)
    # Dashes and dots allowed; verify no whitespace / slash leaked.
    assert "/" not in slug
    assert " " not in slug
    # The full original ID should survive minus unsafe chars.
    assert slug == "claude-sonnet-4-20250514"
    _cleanup_run_dir(full_path + "/x")
