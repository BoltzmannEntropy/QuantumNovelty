"""Quantum KB/RAG tests.

No LLM, no network, no model downloads. The temporary KB is fully local.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"


def _load_qkb():
    common = str(SKILLS / "common")
    if common not in sys.path:
        sys.path.insert(0, common)
    import quantum_kb
    return quantum_kb


def _write_fixture_docs(src: Path) -> None:
    src.mkdir(parents=True, exist_ok=True)
    (src / "vqe_notes.md").write_text(
        """---
title: VQE Ansatz Notes
author: Test Author
year: 2026
keywords: vqe ansatz hamiltonian energy variational quantum eigensolver
---

# VQE Ansatz Notes

The variational quantum eigensolver uses a parameterized ansatz circuit to
minimize the expectation value of a Hamiltonian. A useful novelty audit compares
energy error, CNOT count, parameter count, optimizer budget, and random-seed
variance against known baselines.
""",
        encoding="utf-8",
    )
    (src / "surface_code.md").write_text(
        """---
title: Surface Code Decoder Notes
author: Test Author
year: 2026
keywords: quantum error correction surface code decoder syndrome
---

# Surface Code Decoder Notes

Quantum error correction with the surface code uses stabilizer measurements and
syndrome decoding to protect a logical qubit. Decoder assumptions and the noise
model must be explicit before threshold claims are compared.
""",
        encoding="utf-8",
    )


def test_quantum_kb_index_and_search(tmp_path):
    qkb = _load_qkb()
    src = tmp_path / "docs"
    kb_root = tmp_path / "quantum-kb"
    _write_fixture_docs(src)

    qkb.create_kb(
        "papers",
        "Quantum Papers",
        "Test KB",
        kb_root=kb_root,
        make_default=True,
    )
    ingest = qkb.ingest_documents("papers", src, kb_root=kb_root)
    assert ingest["copied"] == 2

    stats = qkb.build_index("papers", kb_root=kb_root, purge=True)
    assert stats["document_count"] == 2
    assert stats["chunk_count"] >= 2
    assert stats["vocabulary_terms"] > 0

    results = qkb.search_kbs(
        "VQE ansatz Hamiltonian energy",
        ["papers"],
        kb_root=kb_root,
        max_results=3,
    )
    assert results
    assert results[0].title == "VQE Ansatz Notes"
    assert "ansatz" in results[0].quote.lower()
    assert results[0].quote in results[0].text
    assert results[0].bm25_score > 0


def test_quantum_kb_query_expansion():
    qkb = _load_qkb()
    terms = qkb.expand_query_terms("VQE")
    assert "vqe" in terms
    assert "variational" in terms
    assert "hamiltonian" in terms


def test_quantum_kb_cli_search_writes_outputs(tmp_path):
    src = tmp_path / "docs"
    kb_root = tmp_path / "quantum-kb"
    outdir = tmp_path / "search"
    _write_fixture_docs(src)
    run_sh = SKILLS / "quantum_kb" / "run.sh"

    r = subprocess.run(
        [
            "bash", str(run_sh),
            "--kb-root", str(kb_root),
            "create", "--kb", "papers", "--name", "Quantum Papers", "--default",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r.returncode == 0, r.stderr

    r = subprocess.run(
        [
            "bash", str(run_sh),
            "--kb-root", str(kb_root),
            "ingest", "--kb", "papers", "--source", str(src),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r.returncode == 0, r.stderr

    r = subprocess.run(
        [
            "bash", str(run_sh),
            "--kb-root", str(kb_root),
            "index", "--kb", "papers", "--purge",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r.returncode == 0, r.stderr

    r = subprocess.run(
        [
            "bash", str(run_sh),
            "--kb-root", str(kb_root),
            "search", "--kb", "papers",
            "--query", "surface code decoder syndrome",
            "--outdir", str(outdir),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r.returncode == 0, r.stderr
    payload = json.loads((outdir / "search_results.json").read_text())
    assert payload["result_count"] >= 1
    assert payload["results"][0]["title"] == "Surface Code Decoder Notes"
    assert payload["results"][0]["quote"] in payload["results"][0]["text"]
    assert (outdir / "search_results.md").is_file()
    assert (outdir / "quotes_for_prompt.txt").is_file()
    assert (outdir / "context.md").is_file()


def test_quantum_kb_cli_substantiate_and_review(tmp_path):
    src = tmp_path / "docs"
    kb_root = tmp_path / "quantum-kb"
    outdir = tmp_path / "review"
    _write_fixture_docs(src)
    run_sh = SKILLS / "quantum_kb" / "run.sh"

    for args in (
        ["create", "--kb", "papers", "--name", "Quantum Papers", "--default"],
        ["ingest", "--kb", "papers", "--source", str(src)],
        ["index", "--kb", "papers", "--purge"],
    ):
        r = subprocess.run(
            ["bash", str(run_sh), "--kb-root", str(kb_root), *args],
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert r.returncode == 0, r.stderr

    claim = "A VQE novelty audit should compare an ansatz against known baselines."
    r = subprocess.run(
        [
            "bash", str(run_sh),
            "--kb-root", str(kb_root),
            "review",
            "--kb", "papers",
            "--question", "Does the claim have source support?",
            "--claim", claim,
            "--outdir", str(outdir),
            "--no-llm",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r.returncode == 0, r.stderr

    dossier = json.loads((outdir / "claim_evidence.json").read_text())
    assert dossier["claim_count"] == 1
    evidence = dossier["claims"][0]["evidence"]
    assert evidence
    assert evidence[0]["exact_quote"] is True
    assert evidence[0]["quote"] in evidence[0]["text"]
    assert evidence[0]["citation"]
    assert evidence[0]["citation_short"]
    assert (outdir / "citations.md").read_text().strip()
    review = (outdir / "grounded_review.md").read_text()
    assert "KB-Grounded Quantum Review" in review
    assert claim in review


def test_quantum_kb_cli_perspective_writes_verified_quotes(tmp_path):
    src = tmp_path / "docs"
    kb_root = tmp_path / "quantum-kb"
    outdir = tmp_path / "perspective"
    _write_fixture_docs(src)
    run_sh = SKILLS / "quantum_kb" / "run.sh"

    for args in (
        ["create", "--kb", "papers", "--name", "Quantum Papers", "--default"],
        ["ingest", "--kb", "papers", "--source", str(src)],
        ["index", "--kb", "papers", "--purge"],
    ):
        r = subprocess.run(
            ["bash", str(run_sh), "--kb-root", str(kb_root), *args],
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert r.returncode == 0, r.stderr

    question = "What evidence should evaluate whether a VQE ansatz is novel?"
    r = subprocess.run(
        [
            "bash", str(run_sh),
            "--kb-root", str(kb_root),
            "perspective",
            "--kb", "papers",
            "--question", question,
            "--quote-count", "2",
            "--outdir", str(outdir),
            "--no-llm",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r.returncode == 0, r.stderr

    final = (outdir / "01_quantum_perspective.md").read_text()
    assert "Evidence Standard for a Novel VQE Ansatz" in final
    assert "## Quotes used (verbatim, with source)" in final
    assert "## Claims (verified against cited sources)" in final

    candidates = json.loads((outdir / "quote_candidates.json").read_text())
    assert candidates["quote_count"] >= 2
    for item in candidates["quotes"][:2]:
        assert item["quote"] in final
        assert item["exact_quote"] is True
        assert item["citation"]
        assert item["citation_short"]

    fidelity = json.loads((outdir / "quote_fidelity.json").read_text())
    assert fidelity["quote_count"] >= 2
    assert fidelity["unverified_count"] == 0
    assert fidelity["verified_count"] == fidelity["quote_count"]

    parity = json.loads((outdir / "emma_parity_report.json").read_text())
    assert parity["workflow"] == "quantum-kb-perspective"
    assert parity["verified_quote_spans"] == fidelity["verified_count"]
    assert (outdir / "quotes_for_prompt.txt").is_file()
    assert (outdir / "fact_check.md").is_file()
