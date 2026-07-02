"""QuantumNovelty smoke tests — pure CLI / static-analysis assertions.

No LLM calls. No network. No real subprocess to claude/codex.

Run: `pytest tests/test_smoke.py`
"""
from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
CHAIN_RUN = REPO / "chain" / "run.sh"


# =========================================================================
# 1. Every Python file compiles cleanly.
# =========================================================================

_ARTIFACT_DIRS = ("runs/", "/_run/", "/_run_", "__pycache__",
                  "/_archive")


def _is_artifact(path) -> bool:
    """Run outputs (incl. LLM-generated candidate code under runs/)
    are data, not source — they must not gate the smoke suite."""
    s = str(path)
    return any(d in s for d in _ARTIFACT_DIRS)


@pytest.mark.parametrize("py_path", sorted(
    p for p in REPO.rglob("*.py") if not _is_artifact(p)))
def test_python_files_compile(py_path):
    py_compile.compile(str(py_path), doraise=True)


# =========================================================================
# 2. Every shell script passes bash -n.
# =========================================================================

@pytest.mark.parametrize("sh_path", sorted(
    p for p in REPO.rglob("*.sh") if not _is_artifact(p)))
def test_shell_scripts_parse(sh_path):
    r = subprocess.run(["bash", "-n", str(sh_path)],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"{sh_path} bash -n failed: {r.stderr}"


# =========================================================================
# 3. chain --list-skills discovers all expected skills.
# =========================================================================

def test_chain_list_skills():
    r = subprocess.run(["bash", str(CHAIN_RUN), "--list-skills"],
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
    expected = ["novelty_audit", "literature_surfacer", "pareto_explorer",
                "ablation_designer", "cross_llm_prediction",
                "book_acquirer", "audit_falsify", "patent_drafter",
                "quantum_scout"]
    for name in expected:
        assert name in r.stdout, f"missing skill {name} in --list-skills"


def test_chain_help_lists_pipelines():
    r = subprocess.run(["bash", str(CHAIN_RUN), "--help"],
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
    for pipe in ["literature", "pareto-discover", "novelty-audit",
                 "cross-llm", "draft-paper", "patent-draft", "full",
                 "scout"]:
        assert pipe in r.stdout, f"missing pipeline {pipe} in --help"
    assert "pareto-discover   DEPRECATED" in r.stdout
    assert "Prefer --pipeline scout" in r.stdout
    for flag in [
        "--source-file",
        "--scout-n",
        "--scout-arxiv-max-downloads",
        "--scout-pdf-kb-only",
        "--no-scout-live-literature",
    ]:
        assert flag in r.stdout, f"missing scout flag {flag} in --help"


def test_chain_list_stages_includes_scout():
    r = subprocess.run(["bash", str(CHAIN_RUN), "--list-stages"],
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
    assert "scout" in r.stdout
    assert "quote-substantiation" in r.stdout


def test_chain_rejects_unknown_pipeline():
    r = subprocess.run(["bash", str(CHAIN_RUN), "--pipeline", "does-not-exist"],
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 2
    assert "Unknown pipeline" in r.stderr


def test_quantum_scout_offline_chain_writes_quote_grounded_artifacts(tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    note = src / "decoder_notes.md"
    note.write_text(
        """---
title: Decoder Notes
author: Test Author
year: 2026
keywords: surface code decoder syndrome quantum error correction
---

# Decoder Notes

Surface-code decoders must state the noise model, syndrome extraction schedule,
and threshold metric before any quantum error-correction advantage claim can be
compared against known baselines.
""",
        encoding="utf-8",
    )
    outdir = tmp_path / "scout_run"
    r = subprocess.run(
        [
            "bash", str(CHAIN_RUN),
            "--pipeline", "scout",
            "--topic", "surface code decoder under biased noise",
            "--source-file", str(note),
            "--no-scout-live-literature",
            "--no-llm",
            "--outdir", str(outdir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr

    scout = outdir / "scout"
    assert (scout / "scout_report.md").is_file()
    assert (scout / "scout_references.bib").is_file()
    assert (scout / "claim_ledger.json").is_file()
    assert (scout / "global_literature" / "baseline_catalog.json").is_file()
    assert (scout / "source_kb" / "search_results.json").is_file()
    evidence = json.loads((scout / "substantiation" / "claim_evidence.json").read_text())
    assert evidence["claim_count"] >= 1
    first_evidence = evidence["claims"][0]["evidence"]
    assert first_evidence
    assert first_evidence[0]["exact_quote"] is True
    assert first_evidence[0]["citation"]
    manifest = json.loads((scout / "scout_manifest.json").read_text())
    assert "word-for-word quote substantiation" in manifest["ss_parity_features"]
    assert "broad quantum-subject avenue recommendation" in manifest["ss_parity_features"]
    report = json.loads((scout / "scout_report.json").read_text())
    assert report["ideas"][0]["venue_fit"]
    assert "Pareto" not in report["ideas"][0]["title"]


def test_quantum_scout_pdf_kb_only_skips_ideas_but_indexes_sources(tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    note = src / "decoder_notes.md"
    note.write_text(
        """---
title: Decoder Notes
author: Test Author
year: 2026
keywords: surface code decoder syndrome
---

# Decoder Notes

Surface-code decoders must state the noise model, syndrome extraction schedule,
and threshold metric before any quantum error-correction advantage claim can be
compared against known baselines.
""",
        encoding="utf-8",
    )
    outdir = tmp_path / "pdf_kb_run"
    r = subprocess.run(
        [
            "bash", str(CHAIN_RUN),
            "--pipeline", "scout",
            "--topic", "surface code decoder syndrome",
            "--source-file", str(note),
            "--scout-pdf-kb-only",
            "--no-scout-arxiv-corpus",
            "--no-scout-live-literature",
            "--no-llm",
            "--outdir", str(outdir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    scout = outdir / "scout"
    report = json.loads((scout / "scout_report.json").read_text())
    assert report["pdf_kb_only"] is True
    assert report["ideas"] == []
    search = json.loads((scout / "source_kb" / "search_results.json").read_text())
    assert search["result_count"] >= 1
    quality = json.loads((scout / "scout_quality.json").read_text())
    assert quality["pdf_kb_only"] is True


# =========================================================================
# 4. LLM backend module — env scrub works, KNOWN_BACKENDS is sane.
# =========================================================================

def test_scrubbed_env_removes_anthropic_and_claude_code(monkeypatch):
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sentinel")
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sentinel")
        monkeypatch.setenv("CLAUDECODE", "sentinel")
        scrubbed = llm._scrubbed_env()
        for k in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_SESSION_ID", "CLAUDECODE"):
            assert k not in scrubbed, f"{k} not scrubbed"
        # PATH MUST survive — subprocess needs it.
        assert "PATH" in scrubbed
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_known_backends_set():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        assert llm.KNOWN_BACKENDS == (
            "claude", "codex", "codex-acp", "codex-mcp", "kimi",
            "anthropic-api"
        )
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_call_llm_rejects_unknown_backend():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        with pytest.raises(ValueError, match="unknown backend"):
            llm.call_llm("hi", backend="not-a-real-backend")
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_call_llm_uses_stub_when_set(tmp_path):
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        stub_file = tmp_path / "stub.txt"
        stub_file.write_text("STUBBED RESPONSE", encoding="utf-8")
        os.environ["QUANTUMNOVELTY_LLM_STUB"] = str(stub_file)
        try:
            result = llm.call_llm("anything", backend="claude")
            assert result.text == "STUBBED RESPONSE"
            assert result.backend_actually_used == "stub"
        finally:
            os.environ.pop("QUANTUMNOVELTY_LLM_STUB", None)
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_call_llm_accepts_kimi_stub_backend(tmp_path, monkeypatch):
    """Kimi and explicit kimi-* model ids should validate before stub use."""
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        stub_file = tmp_path / "stub.txt"
        stub_file.write_text("KIMI STUB", encoding="utf-8")
        monkeypatch.setenv("QUANTUMNOVELTY_LLM_STUB", str(stub_file))

        r1 = llm.call_llm("anything", backend="kimi")
        assert r1.text == "KIMI STUB"
        assert r1.backend_requested == "kimi"
        assert r1.backend_actually_used == "stub"

        r2 = llm.call_llm("anything", backend="kimi-k2.7-code")
        assert r2.backend_requested == "kimi-k2.7-code"
        assert r2.backend_actually_used == "stub"
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_kimi_env_file_parser(tmp_path, monkeypatch):
    """QN should load Moonshot Anthropic-compatible config without sourcing."""
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        env_file = tmp_path / "kikm.sh"
        env_file.write_text(
            "\n".join([
                "export ANTHROPIC_BASE_URL=https://api.moonshot.example/anthropic",
                "export ANTHROPIC_AUTH_TOKEN=dummy-token",
                "export ANTHROPIC_MODEL=kimi-k2.7-code",
            ]),
            encoding="utf-8",
        )
        monkeypatch.setenv("KIMI_ENV_FILE", str(env_file))

        assert llm._find_kimi_env_file() == env_file
        parsed = llm._parse_kimi_env_file(env_file)
        assert parsed["ANTHROPIC_BASE_URL"].endswith("/anthropic")
        assert parsed["ANTHROPIC_AUTH_TOKEN"] == "dummy-token"
        assert parsed["ANTHROPIC_MODEL"] == "kimi-k2.7-code"
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_stub_path_records_token_estimates(tmp_path):
    """Stub backend should report estimated token counts + the flag."""
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        stub_file = tmp_path / "stub.txt"
        stub_file.write_text("a" * 400, encoding="utf-8")
        os.environ["QUANTUMNOVELTY_LLM_STUB"] = str(stub_file)
        try:
            r = llm.call_llm("b" * 200, backend="claude")
            assert r.tokens_estimated is True
            # char/4 ≈ 50 input, 100 output
            assert r.input_tokens == 50
            assert r.output_tokens == 100
            assert r.model_id == "stub"
        finally:
            os.environ.pop("QUANTUMNOVELTY_LLM_STUB", None)
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_marker_json_includes_usage_block():
    """as_marker_json() emits a JSON with the full usage subobject."""
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        r = llm.LLMResult(
            text="hi", backend_requested="claude",
            backend_actually_used="claude",
            model_id="claude-test-2026", elapsed_s=1.0,
            input_tokens=42, output_tokens=7,
            total_cost_usd=0.0001,
        )
        marker = json.loads(r.as_marker_json())
        assert marker["model_id"] == "claude-test-2026"
        assert marker["usage"]["input_tokens"] == 42
        assert marker["usage"]["output_tokens"] == 7
        assert marker["usage"]["total_cost_usd"] == 0.0001
        assert marker["usage"]["tokens_estimated"] is False
    finally:
        sys.path.remove(str(SKILLS / "common"))


# =========================================================================
# 5. anthropic-api refuses without ANTHROPIC_API_KEY.
# =========================================================================

def test_anthropic_api_refuses_without_key():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import llm
        # Ensure no key in env for this test.
        saved = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                llm.call_llm("hi", backend="anthropic-api")
        finally:
            if saved is not None:
                os.environ["ANTHROPIC_API_KEY"] = saved
    finally:
        sys.path.remove(str(SKILLS / "common"))


# =========================================================================
# 6. novelty_audit primitives — strict_dominates, wilson, classifier.
# =========================================================================

def _add_audit_to_path():
    sys.path.insert(0, str(SKILLS / "novelty_audit"))
    sys.path.insert(0, str(SKILLS / "common"))
    # Evict any prior `skill` module from sys.modules so we get the right one.
    sys.modules.pop("skill", None)


def _remove_audit_from_path():
    sys.modules.pop("skill", None)
    for p in (str(SKILLS / "novelty_audit"), str(SKILLS / "common")):
        try:
            sys.path.remove(p)
        except ValueError:
            pass


def test_strict_dominates_basic():
    _add_audit_to_path()
    try:
        import skill as novelty_audit
        a = novelty_audit.Row("A", "llm", {"energy": -1.0, "ops": 10, "cnots": 4})
        b = novelty_audit.Row("B", "baseline", {"energy": -0.5, "ops": 20, "cnots": 8})
        # A dominates B on all three axes (lower energy = more negative? in our
        # convention lower-is-better; -1.0 < -0.5 means A is "better" energy).
        assert novelty_audit.strict_dominates(
            a, b, axes=["energy", "ops", "cnots"],
            eps_abs=1e-12, eps_rel=1e-9
        )
        # Reverse should NOT hold.
        assert not novelty_audit.strict_dominates(
            b, a, axes=["energy", "ops", "cnots"],
            eps_abs=1e-12, eps_rel=1e-9
        )
    finally:
        _remove_audit_from_path()


def test_strict_dominates_no_dominance_when_mixed():
    _add_audit_to_path()
    try:
        import skill as novelty_audit
        # A wins on energy, B wins on ops — neither dominates.
        a = novelty_audit.Row("A", "llm", {"energy": -1.0, "ops": 100})
        b = novelty_audit.Row("B", "baseline", {"energy": -0.5, "ops": 10})
        assert not novelty_audit.strict_dominates(
            a, b, axes=["energy", "ops"],
            eps_abs=1e-12, eps_rel=1e-9
        )
        assert not novelty_audit.strict_dominates(
            b, a, axes=["energy", "ops"],
            eps_abs=1e-12, eps_rel=1e-9
        )
    finally:
        _remove_audit_from_path()


def test_wilson_interval_known_values():
    _add_audit_to_path()
    try:
        import skill as novelty_audit
        # k=5, n=5 — Wilson 95 % score interval is approximately [0.566, 1.000]
        # (z=1.96; standard Wilson, not the "plus-4" or adjusted variants).
        lo, hi = novelty_audit.wilson_interval(5, 5)
        assert 0.55 < lo < 0.58, f"lo bound {lo} unexpected for 5/5"
        assert hi >= 0.99, f"hi bound {hi} unexpected for 5/5"
        # k=4, n=5 — Wilson 95 % CI ≈ [0.36, 0.97]
        lo45, hi45 = novelty_audit.wilson_interval(4, 5)
        assert 0.30 < lo45 < 0.45
        assert 0.93 < hi45 < 1.0
        # k=0, n=0 — degenerate, must not crash
        lo0, hi0 = novelty_audit.wilson_interval(0, 0)
        assert lo0 == 0.0 and hi0 == 0.0
    finally:
        _remove_audit_from_path()


def test_scan_ratios_picks_up_displayed_drift():
    _add_audit_to_path()
    try:
        import skill as novelty_audit
        # 198/14 = 14.142857...; if the manuscript writes 14.5x, that's drift.
        text = "we observe a 198/14 = 14.1x reduction in gate count"
        ratios = novelty_audit.scan_ratios(text)
        assert len(ratios) == 1
        r = ratios[0]
        assert r["num"] == 198.0
        assert r["den"] == 14.0
        assert r["displayed"] == 14.1
    finally:
        _remove_audit_from_path()


def test_scan_rates_recognizes_small_samples():
    _add_audit_to_path()
    try:
        import skill as novelty_audit
        text = "Across 5/5 cold starts and 4 of 5 multi-seed runs we observe..."
        rates = novelty_audit.scan_rates(text, max_n=30)
        # Should pick up both "5/5" and "4 of 5"
        kn = {(r["k"], r["n"]) for r in rates}
        assert (5, 5) in kn
        assert (4, 5) in kn
    finally:
        _remove_audit_from_path()


# =========================================================================
# 7. Anna's Archive — parse helpers (no network).
# =========================================================================

def test_annas_parse_size():
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import annas_archive
        assert annas_archive._parse_size("1.5 MB") == int(1.5 * 1024**2)
        assert annas_archive._parse_size("700 KB") == 700 * 1024
        assert annas_archive._parse_size("garbage") == 0
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_annas_download_no_key_returns_status(tmp_path, monkeypatch):
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import annas_archive
        monkeypatch.delenv("ANNAS_ARCHIVE_KEY", raising=False)
        hit = annas_archive.SearchHit(
            md5="0" * 32, title="X", author="Y", year="2024",
            extension="pdf", size_bytes=0, language="en",
            raw_url="https://example.com",
        )
        res = annas_archive.download(hit, tmp_path)
        assert res.status == "no_key"
    finally:
        sys.path.remove(str(SKILLS / "common"))


# =========================================================================
# 8. Example paper reviews shipped in the repo.
# =========================================================================

def test_example_paper_reviews_present():
    reviews = REPO / "examples" / "paper_reviews"
    assert (reviews / "papers.json").is_file()
    assert (reviews / "README.md").is_file()


# =========================================================================
# 9. paper_io — the shared draft loader every --paper skill goes through.
# =========================================================================

def test_paper_io_text_formats(tmp_path):
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        from paper_io import load_paper_text
        md = tmp_path / "draft.md"
        md.write_text("# Title\n\nBody.", encoding="utf-8")
        assert "Body." in load_paper_text(md)
        bad = tmp_path / "draft.xyz"
        bad.write_text("x", encoding="utf-8")
        with pytest.raises(ValueError, match="unsupported draft format"):
            load_paper_text(bad)
    finally:
        sys.path.remove(str(SKILLS / "common"))


def test_paper_io_pdf_quickstart_path():
    """The README quickstart reviews a PDF — that ingest path must work
    whenever either extractor (pdftotext binary or pdfminer.six) exists."""
    import shutil as _shutil
    has_pdftotext = _shutil.which("pdftotext") is not None
    try:
        import pdfminer  # noqa: F401
        has_pdfminer = True
    except ImportError:
        has_pdfminer = False
    if not (has_pdftotext or has_pdfminer):
        pytest.skip("no PDF extractor available in this environment")
    pdf = (REPO / "examples" / "paper_reviews" / "flowvqe"
           / "flowvqe_arxiv.pdf")
    if not pdf.is_file():
        pytest.skip("example PDF not present")
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        from paper_io import load_paper_text
        text = load_paper_text(pdf)
        assert len(text) > 10_000
        assert "variational" in text.lower()
    finally:
        sys.path.remove(str(SKILLS / "common"))


# =========================================================================
# 10. claims_registry + citation_integrity — deterministic audit skills.
# =========================================================================

def test_claims_registry_flags_fabricated_numerics(tmp_path):
    paper = tmp_path / "p.md"
    paper.write_text(
        "# Abstract\n\nWe achieve 98.3% accuracy and a 14.1x speedup.\n\n"
        "# Results\n\nThe model reaches 87.2% accuracy with a 14.1x "
        "speedup and error 0.005 mHa.\n\n"
        "# Discussion\n\nOur 0.005 mHa error and the 47.2x improvement.\n",
        encoding="utf-8")
    out = tmp_path / "out"
    r = subprocess.run(
        ["bash", str(SKILLS / "claims_registry" / "run.sh"),
         "--paper", str(paper), "--outdir", str(out)],
        capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    rep = json.loads((out / "verification_report.json").read_text())
    vals = {f["value"] for f in rep["findings"]}
    assert "98.3" in vals      # abstract claim absent from Results
    assert "47.2" in vals      # discussion claim absent from Results
    assert "0.005" not in vals  # traces back to Results
    assert "14.1" not in vals   # traces back to Results


def test_claims_registry_render_audit(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("Accuracy is 87.2% over 5 seeds.", encoding="utf-8")
    rnd = tmp_path / "rnd.md"
    rnd.write_text("Accuracy is 87.2% over 5 seeds, i.e. 99.9% better.",
                   encoding="utf-8")
    out = tmp_path / "out"
    r = subprocess.run(
        ["bash", str(SKILLS / "claims_registry" / "run.sh"),
         "--source", str(src), "--render", str(rnd),
         "--outdir", str(out), "--threshold", "0.05"],
        capture_output=True, text=True, timeout=60)
    rep = json.loads((out / "paper_verification.json").read_text())
    assert rep["passed"] is False           # 99.9 was injected
    assert r.returncode == 3
    assert any(u["raw"].startswith("99.9")
               for u in rep["unverified_numbers"])


def test_citation_integrity_offline_layers(tmp_path):
    paper = tmp_path / "p.tex"
    paper.write_text(r"We build on \cite{good2024} and \cite{ghost2025}.",
                     encoding="utf-8")
    bib = tmp_path / "r.bib"
    bib.write_text(
        "@article{good2024,\n  author = {A. Author},\n"
        "  title = {A real title},\n  year = {2024},\n}\n",
        encoding="utf-8")
    out = tmp_path / "out"
    r = subprocess.run(
        ["bash", str(SKILLS / "citation_integrity" / "run.sh"),
         "--paper", str(paper), "--bib", str(bib),
         "--outdir", str(out), "--no-network"],
        capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    rep = json.loads((out / "verification_report.json").read_text())
    by_key = {x["cite_key"]: x["status"] for x in rep["results"]}
    assert by_key["ghost2025"] == "hallucinated"
    assert by_key["good2024"] == "verified"
    assert rep["summary"]["integrity_score"] == 0.5


def test_claims_registry_number_tokenizer():
    """Scientific notation and fractions must tokenize whole — the
    plain-number alternative must not eat their prefix ('1.5e-3' as
    '1'+'3' corrupted both registry and findings)."""
    sys.path.insert(0, str(SKILLS / "claims_registry"))
    try:
        import importlib
        import skill as cr
        importlib.reload(cr)
        def toks(s):
            return [m.group(1) for m in cr.NUMBER_RE.finditer(s)]
        assert toks("error of 1.5e-3 Ha") == ["1.5e-3"]
        assert toks("ratio 3/4 achieved") == ["3/4"]
        assert toks("a 14.1x speedup") == ["14.1x"]
        assert toks("87.3% measured") == ["87.3%"]
    finally:
        sys.path.remove(str(SKILLS / "claims_registry"))


def test_claims_registry_suffixed_round_numbers_not_whitelisted(tmp_path):
    """'100x speedup' is a substantive claim — it must not pass via the
    rhetorical round-number whitelist."""
    paper = tmp_path / "p.md"
    paper.write_text(
        "# Abstract\n\nWe obtain a 100x speedup.\n\n"
        "# Results\n\nMeasured speedup: 12.4x.\n",
        encoding="utf-8")
    out = tmp_path / "out"
    subprocess.run(
        ["bash", str(SKILLS / "claims_registry" / "run.sh"),
         "--paper", str(paper), "--outdir", str(out)],
        capture_output=True, text=True, timeout=60, check=True)
    rep = json.loads((out / "verification_report.json").read_text())
    assert "100" in {f["value"] for f in rep["findings"]}


# =========================================================================
# 11. pareto_explorer built-in evaluator — physics + safety.
# =========================================================================

def _be():
    sys.path.insert(0, str(SKILLS / "pareto_explorer"))
    import importlib
    import builtin_evaluator
    importlib.reload(builtin_evaluator)
    sys.path.remove(str(SKILLS / "pareto_explorer"))
    return builtin_evaluator


def test_builtin_evaluator_exact_energies():
    pytest.importorskip("numpy")
    import math
    be = _be()
    H, n = be.build_hamiltonian("TFIM_2q")
    assert n == 2
    # H = -ZZ - X0 - X1 has ground energy -sqrt(5).
    assert abs(be.exact_ground_energy(H) + math.sqrt(5)) < 1e-9
    Hh, nh = be.build_hamiltonian("H2_2q")
    # Published value for the 2-qubit tapered H2 @ R = 0.7414 A.
    assert abs(be.exact_ground_energy(Hh) + 1.857275) < 1e-5


def test_builtin_evaluator_baseline_converges():
    pytest.importorskip("numpy")
    be = _be()
    H, n = be.build_hamiltonian("TFIM_2q")
    rec = be.evaluate_baseline_label("HEA-2L", H, n)
    assert rec["status"] == "ok"
    assert rec["energy_error_ha"] < 5e-3
    assert rec["params"] == 6 and rec["cnots"] == 2
    assert be.evaluate_baseline_label("UCCSD-1-Trotter", H, n) is None


def test_builtin_evaluator_rejects_bad_candidates():
    pytest.importorskip("numpy")
    be = _be()
    with pytest.raises(ValueError):
        be.validate_gates([{"gate": "ry", "q": 7, "param": 0}], 2)
    with pytest.raises(ValueError):
        be.validate_gates([{"gate": "teleport", "q": 0}], 2)
    with pytest.raises(ValueError):
        be.validate_gates([], 2)
    with pytest.raises(ValueError):
        be.build_hamiltonian("TFIM_99q")


# =========================================================================
# 12. Integrity gates + R&R traceability matrix.
# =========================================================================

def test_claims_registry_is_default_on_stage():
    """claims-registry must be a default-on paper-audit stage."""
    sys.path.insert(0, str(REPO / "chain"))
    try:
        import importlib
        import pipelines
        importlib.reload(pipelines)
        assert "claims-registry" in pipelines.PAPER_AUDIT_DEFAULT_ON
        assert "claims-registry" not in pipelines.PAPER_AUDIT_OPTIONAL
    finally:
        sys.path.remove(str(REPO / "chain"))


def test_traceability_matrix_catches_fabricated_evidence():
    sys.path.insert(0, str(SKILLS / "quantum_reviewer"))
    sys.path.insert(0, str(SKILLS / "common"))
    try:
        import importlib
        import skill as qr
        importlib.reload(qr)
        draft = "Speedup 12.4x measured over five seeds."
        review = (
            "## R&R Traceability Matrix\n\n"
            "| # | F | C | E | V |\n|---|---|---|---|---|\n"
            '| 1 | "a" | b | "Speedup 12.4x measured" | VERIFIED |\n'
            '| 2 | "c" | d | "seventeen baselines added" | VERIFIED |\n')
        m = qr.extract_traceability_matrix(review, draft)
        assert m["n_rows"] == 2
        assert m["rows"][0]["effective_verdict"] == "VERIFIED"
        assert m["rows"][1]["effective_verdict"] == "UNSUBSTANTIATED"
        assert m["n_evidence_unverifiable"] == 1
    finally:
        sys.path.remove(str(SKILLS / "quantum_reviewer"))
        sys.path.remove(str(SKILLS / "common"))
