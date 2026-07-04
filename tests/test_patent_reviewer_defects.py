"""Zero-LLM, zero-network tests for the three patent_reviewer defect fixes.

DEFECT 1 — OA parser fallback + conflict detection (skill.py)
DEFECT 2 — Prior-art citation direction + temporal guard (build_dataset.py)
DEFECT 3 — Specification fed to panel (patent_io.py + run_eval.py)
"""
from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
DATASET = REPO / "datasets" / "quantum_patent_office_actions"


def _load_skill_module(skill_name: str, module_alias: str):
    common_path = str(SKILLS / "common")
    if common_path not in sys.path:
        sys.path.insert(0, common_path)
    skill_path = SKILLS / skill_name / "skill.py"
    spec = importlib.util.spec_from_file_location(module_alias, skill_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_alias] = mod
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────────────────────────────────────
# DEFECT 1 — parse_conflict + SPE-authoritative disposition
# ─────────────────────────────────────────────────────────────────────────────

# Trimmed fixture reproducing the US10614371B2 failure shape:
# - No "### Rejections of record" canonical block (triggers fallback)
# - Voice 1 table lists claims 1–25 under § 101 with "Eligible" in basis cell
# - SPE declares Disposition: allowance  (9/10 confidence)
# The OLD code would: (1) fail to filter "Eligible" row (bug: regex only
# captured 2 cells, so basis text was invisible), (2) silently downgrade
# allowance → non-final-rejection because rejected_claims was non-empty.
_FIXTURE_NO_CANONICAL_SPE_ALLOWS = textwrap.dedent("""\
    ## Voice 1 — Primary Examiner (§ 101)

    | Claim(s) | Statute | Basis / reason |
    |---|---|---|
    | 1–25 | § 101 | Eligible — improves operation of a quantum computer; not abstract. |

    ## Voice 6 — Supervisory Patent Examiner (SPE) synthesis + disposition

    Having reviewed all five examiners, I find no § 101 defect: the claims are
    directed to an improvement in quantum computer operation and pass the Alice/Mayo
    framework. No § 102 or § 103 rejection is sustained. No § 112 defect.

    Disposition: allowance

    ## Vote table

    | Voice | Recommended disposition | Confidence 1-10 |
    |---|---|---|
    | Primary Examiner | allowance (no § 101 defect) | 9 |
    | § 102 Examiner | allowance | 9 |
    | § 103 Examiner | allowance | 9 |
    | § 112 Examiner | allowance | 9 |
    | Quantum Technical Specialist | allowance | 9 |
    | Supervisory Patent Examiner | allowance | 9 |
""")


def test_defect1_spe_allowance_not_downgraded():
    """SPE allowance must NOT be silently downgraded to non-final-rejection."""
    skill = _load_skill_module("patent_reviewer", "patent_reviewer_d1")
    result = skill.extract_office_action(_FIXTURE_NO_CANONICAL_SPE_ALLOWS, 25)
    assert result["disposition"] == "allowance", (
        f"Expected allowance, got {result['disposition']!r}. "
        "SPE disposition must be authoritative over per-voice fallback tables."
    )
    assert result["passes"] is True


# Fixture for conflict path: canonical block absent, SPE says allowance, but
# a § 103 rejection row (non-pass wording) exists in a per-examiner table.
# This tests the genuine SPE-vs-per-voice disagreement, distinct from the
# "eligible" filter that already handles Voice 1 pass rows.
_FIXTURE_CONFLICT_SPE_ALLOWS_103_ROWS = textwrap.dedent("""\
    ## Voice 3 — § 103 Examiner

    | Claim(s) | Statute | Basis / reason |
    |---|---|---|
    | 1–10 | § 103 | Obvious over Smith (2015) in view of Jones (2014). |

    ## Voice 6 — Supervisory Patent Examiner (SPE) synthesis + disposition

    After reviewing, I find Smith does not actually teach the quantum gate
    rewrite step. The § 103 combination fails. I sustain no rejection.

    Disposition: allowance

    ## Vote table

    | Voice | Recommended disposition | Confidence 1-10 |
    |---|---|---|
    | Primary Examiner | allowance | 8 |
    | § 102 Examiner | allowance | 9 |
    | § 103 Examiner | non-final-rejection | 6 |
    | § 112 Examiner | allowance | 8 |
    | Quantum Technical Specialist | allowance | 8 |
    | Supervisory Patent Examiner | allowance | 9 |
""")


def test_defect1_parse_conflict_flag_set():
    """parse_conflict must be True when fallback tables have unfiltered rejections
    but SPE declares allowance (canonical block absent)."""
    skill = _load_skill_module("patent_reviewer", "patent_reviewer_d1b")
    result = skill.extract_office_action(_FIXTURE_CONFLICT_SPE_ALLOWS_103_ROWS, 10)
    assert result.get("parse_conflict") is True, (
        "parse_conflict must be set when canonical block is absent and "
        "SPE allowance contradicts per-voice fallback rejections."
    )


def test_defect1_per_voice_rejections_preserved():
    """Per-voice rejections must be stored in per_voice_rejections_by_statute."""
    skill = _load_skill_module("patent_reviewer", "patent_reviewer_d1c")
    result = skill.extract_office_action(_FIXTURE_CONFLICT_SPE_ALLOWS_103_ROWS, 10)
    pvr = result.get("per_voice_rejections_by_statute", {})
    assert pvr, "per_voice_rejections_by_statute must be non-empty when conflict detected"
    assert "103" in pvr, "§ 103 per-voice row must be recorded in the conflict field"


def test_defect1_rejected_claims_empty_when_spe_allows():
    """rejected_claims must be empty when SPE wins as authoritative (conflict resolved)."""
    skill = _load_skill_module("patent_reviewer", "patent_reviewer_d1d")
    result = skill.extract_office_action(_FIXTURE_NO_CANONICAL_SPE_ALLOWS, 25)
    assert result["rejected_claims"] == [], (
        "rejected_claims must be cleared when SPE allowance is authoritative."
    )


def test_defect1_eligible_filter_via_basis_cell():
    """§ 101 rows with 'Eligible' in the basis/reason cell must be filtered in fallback."""
    skill = _load_skill_module("patent_reviewer", "patent_reviewer_d1e")
    # Panel where SPE also rejects (not an allowance), so no conflict path —
    # this tests the filter itself in isolation.
    panel = textwrap.dedent("""\
        ## Voice 1 — Primary Examiner (§ 101)

        | Claim(s) | Statute | Basis / reason |
        |---|---|---|
        | 1–5 | § 101 | Eligible — no abstract idea. |
        | 6–10 | § 103 | Obvious over Smith (2015) in view of Jones (2014). |

        ## Voice 6 — SPE

        Disposition: non-final-rejection

        ## Vote table

        | Voice | Recommended disposition | Confidence 1-10 |
        |---|---|---|
        | Primary Examiner | non-final-rejection | 7 |
        | § 102 Examiner | non-final-rejection | 7 |
        | § 103 Examiner | non-final-rejection | 8 |
        | § 112 Examiner | non-final-rejection | 7 |
        | Quantum Technical Specialist | non-final-rejection | 7 |
        | Supervisory Patent Examiner | non-final-rejection | 7 |
    """)
    result = skill.extract_office_action(panel, 10)
    # Claims 1–5 must NOT appear as § 101 rejected (they are eligible-pass rows)
    assert "101" not in result["rejections_by_statute"], (
        "§ 101 'Eligible' rows must be filtered and not appear in rejections_by_statute"
    )
    # Claims 6–10 must appear as § 103 rejected
    assert result["rejections_by_statute"].get("103") == [6, 7, 8, 9, 10]


def test_defect1_canonical_block_no_conflict():
    """When canonical block IS present, parse_conflict must NOT be set."""
    skill = _load_skill_module("patent_reviewer", "patent_reviewer_d1f")
    panel = textwrap.dedent("""\
        ## Voice 6 — SPE

        Disposition: allowance

        ### Rejections of record
        - § 101: none
        - § 102: none
        - § 103: none
        - § 112: none
        - allowable: 1-10

        ## Vote table

        | Voice | Recommended disposition | Confidence 1-10 |
        |---|---|---|
        | Primary Examiner | allowance | 9 |
        | § 102 Examiner | allowance | 9 |
        | § 103 Examiner | allowance | 9 |
        | § 112 Examiner | allowance | 9 |
        | Quantum Technical Specialist | allowance | 9 |
        | Supervisory Patent Examiner | allowance | 9 |
    """)
    result = skill.extract_office_action(panel, 10)
    assert result["disposition"] == "allowance"
    assert result.get("parse_conflict") is None or result.get("parse_conflict") is False, (
        "parse_conflict must NOT be set when canonical block is present"
    )


# ─────────────────────────────────────────────────────────────────────────────
# DEFECT 2 — Prior-art citation direction + temporal guard
# ─────────────────────────────────────────────────────────────────────────────

def _load_build_dataset():
    path = DATASET / "build_dataset.py"
    spec = importlib.util.spec_from_file_location("build_dataset", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_dataset"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_defect2_patent_citations_scraped_not_cited_by():
    """extract_cited_prior_art must use 'Patent citations' section, not 'Cited by examiner'."""
    bd = _load_build_dataset()

    # HTML that has both sections; backward citations are in 'Patent citations'
    html = textwrap.dedent("""\
        <html><body>
        <h3>Patent citations</h3>
        <table>
          <tr><td><a>US9800000B2</a></td></tr>
          <tr><td><a>US9900000B2</a></td></tr>
        </table>
        <h3>Cited by examiner</h3>
        <table>
          <tr><td><a>US11170137B1</a></td></tr>
          <tr><td><a>US20220198309A1</a></td></tr>
        </table>
        </body></html>
    """)
    refs = bd.extract_cited_prior_art(html)
    pns = [r["publication_number"] for r in refs]
    # Must find backward refs
    assert "US9800000B2" in pns, "Must include backward citation from 'Patent citations' section"
    assert "US9900000B2" in pns
    # Must NOT include forward refs from 'Cited by examiner'
    assert "US11170137B1" not in pns, (
        "Must NOT include 'Cited by examiner' forward citations as prior art"
    )
    assert "US20220198309A1" not in pns


def test_defect2_source_label_is_backward_citation():
    """Source label must be 'google_patents_backward_citation', not 'google_patents_examiner_cited'."""
    bd = _load_build_dataset()
    html = "<html><body><h3>Patent citations</h3><td>US9800000B2</td></body></html>"
    refs = bd.extract_cited_prior_art(html)
    assert refs, "Expected at least one reference"
    assert refs[0]["source"] == "google_patents_backward_citation"


def test_defect2_temporal_guard_drops_future_refs():
    """References whose publication year post-dates priority_year must be dropped."""
    bd = _load_build_dataset()
    html = textwrap.dedent("""\
        <html><body>
        <h3>Patent citations</h3>
        <table>
          <tr><td>US20150100000A1</td></tr>
          <tr><td>US20160200000A1</td></tr>
          <tr><td>US20190300000A1</td></tr>
          <tr><td>US20210400000A1</td></tr>
        </table>
        </body></html>
    """)
    # Priority year 2017: 2015 and 2016 pass; 2019 and 2021 fail
    refs = bd.extract_cited_prior_art(html, priority_year=2017)
    pns = [r["publication_number"] for r in refs]
    assert "US20150100000A1" in pns, "2015 ref must pass temporal guard for priority 2017"
    assert "US20160200000A1" in pns, "2016 ref must pass temporal guard for priority 2017"
    assert "US20190300000A1" not in pns, "2019 ref must be dropped (post-dates priority 2017)"
    assert "US20210400000A1" not in pns, "2021 ref must be dropped (post-dates priority 2017)"


def test_defect2_temporal_guard_no_priority_year_passes_all():
    """Without a priority_year, no temporal filtering should occur."""
    bd = _load_build_dataset()
    html = textwrap.dedent("""\
        <html><body>
        <h3>Patent citations</h3>
        <td>US20190300000A1</td>
        <td>US20230100000A1</td>
        </body></html>
    """)
    refs = bd.extract_cited_prior_art(html, priority_year=None)
    pns = [r["publication_number"] for r in refs]
    assert "US20190300000A1" in pns
    assert "US20230100000A1" in pns


def test_defect2_infer_pub_year_application():
    """_infer_pub_year must decode year from application-style pub numbers."""
    bd = _load_build_dataset()
    assert bd._infer_pub_year("US20170364796A1") == 2017
    assert bd._infer_pub_year("US20220198309A1") == 2022
    assert bd._infer_pub_year("WO2019123456A1") == 2019


# ─────────────────────────────────────────────────────────────────────────────
# DEFECT 3 — Specification fed to panel (patent_io.py + run_eval.py)
# ─────────────────────────────────────────────────────────────────────────────

def _load_patent_io():
    path = SKILLS / "common" / "patent_io.py"
    spec = importlib.util.spec_from_file_location("patent_io_d3", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["patent_io_d3"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_defect3_load_patent_md_with_spec_section(tmp_path):
    """load_patent on a .md file with spec heading must populate description."""
    patent_io = _load_patent_io()
    md_content = textwrap.dedent("""\
        # US10614371B2

        1. A method comprising: executing a quantum circuit on a quantum computer.
        2. The method of claim 1, further comprising tomography.

        ## Written description / specification

        The present invention relates to quantum computing. A quantum processor
        executes circuits on physical qubits using gate operations.
    """)
    md_file = tmp_path / "US10614371B2.md"
    md_file.write_text(md_content)

    patent = patent_io.load_patent(str(md_file))
    assert patent.description, "description must be non-empty when spec heading is present"
    assert "quantum processor" in patent.description.lower()


def test_defect3_load_patent_md_without_spec_section(tmp_path):
    """load_patent on a .md file without spec heading returns empty description."""
    patent_io = _load_patent_io()
    md_content = textwrap.dedent("""\
        # US10614371B2

        1. A method comprising: executing a quantum circuit on a quantum computer.
    """)
    md_file = tmp_path / "US10614371B2.md"
    md_file.write_text(md_content)

    patent = patent_io.load_patent(str(md_file))
    # No spec section: description is empty (graceful fallback)
    assert patent.description == ""


def test_defect3_run_one_appends_spec_to_md(tmp_path, monkeypatch):
    """run_eval.run_one must write description_text after spec heading when include_spec=True."""
    # Load run_eval without executing main()
    path = DATASET / "eval" / "run_eval.py"
    spec = importlib.util.spec_from_file_location("run_eval_d3", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_eval_d3"] = mod
    spec.loader.exec_module(mod)

    # Patch RECORDS_DIR and EVAL_DIR to use tmp_path
    monkeypatch.setattr(mod, "RECORDS_DIR", tmp_path / "records")
    monkeypatch.setattr(mod, "EVAL_DIR", tmp_path / "eval")

    pub = "US99999999B2"
    records_dir = tmp_path / "records"
    records_dir.mkdir(parents=True)
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir(parents=True)

    record = {
        "claims_text": "1. A quantum method.",
        "description_text": "The specification describes a quantum method in detail.",
        "office_action": {"cited_prior_art": []},
    }
    (records_dir / f"{pub}.json").write_text(json.dumps(record))

    # Create fake outputs so the subprocess branch is skipped
    out_dir = eval_dir / pub
    out_dir.mkdir(parents=True)
    (out_dir / "_office_action.json").write_text(json.dumps({
        "disposition": "allowance",
        "rejected_claims": [],
        "rejections_by_statute": {},
        "votes": {},
    }))
    (out_dir / "office_action.md").write_text("No prior art cited.")

    mod.run_one(pub, include_spec=True)

    claims_file = out_dir / f"{pub}.md"
    content = claims_file.read_text()
    assert "## Written description / specification" in content, (
        "run_one must append the spec heading when include_spec=True"
    )
    assert "specification describes a quantum method" in content


def test_defect3_run_one_omits_spec_when_flag_false(tmp_path, monkeypatch):
    """run_eval.run_one must NOT write description when include_spec=False."""
    path = DATASET / "eval" / "run_eval.py"
    spec = importlib.util.spec_from_file_location("run_eval_d3b", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_eval_d3b"] = mod
    spec.loader.exec_module(mod)

    monkeypatch.setattr(mod, "RECORDS_DIR", tmp_path / "records")
    monkeypatch.setattr(mod, "EVAL_DIR", tmp_path / "eval")

    pub = "US88888888B2"
    records_dir = tmp_path / "records"
    records_dir.mkdir(parents=True)
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir(parents=True)

    record = {
        "claims_text": "1. A quantum method.",
        "description_text": "Full specification text here.",
        "office_action": {"cited_prior_art": []},
    }
    (records_dir / f"{pub}.json").write_text(json.dumps(record))

    out_dir = eval_dir / pub
    out_dir.mkdir(parents=True)
    (out_dir / "_office_action.json").write_text(json.dumps({
        "disposition": "allowance",
        "rejected_claims": [],
        "rejections_by_statute": {},
        "votes": {},
    }))
    (out_dir / "office_action.md").write_text("No prior art cited.")

    mod.run_one(pub, include_spec=False)

    claims_file = out_dir / f"{pub}.md"
    content = claims_file.read_text()
    assert "## Written description / specification" not in content, (
        "run_one must NOT append spec when include_spec=False"
    )


def test_defect3_run_one_no_spec_in_record(tmp_path, monkeypatch):
    """run_one with include_spec=True but no description_text in record is graceful."""
    path = DATASET / "eval" / "run_eval.py"
    spec = importlib.util.spec_from_file_location("run_eval_d3c", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_eval_d3c"] = mod
    spec.loader.exec_module(mod)

    monkeypatch.setattr(mod, "RECORDS_DIR", tmp_path / "records")
    monkeypatch.setattr(mod, "EVAL_DIR", tmp_path / "eval")

    pub = "US77777777B2"
    records_dir = tmp_path / "records"
    records_dir.mkdir(parents=True)
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir(parents=True)

    record = {
        "claims_text": "1. A quantum method.",
        # No description_text key
        "office_action": {"cited_prior_art": []},
    }
    (records_dir / f"{pub}.json").write_text(json.dumps(record))

    out_dir = eval_dir / pub
    out_dir.mkdir(parents=True)
    (out_dir / "_office_action.json").write_text(json.dumps({
        "disposition": "allowance",
        "rejected_claims": [],
        "rejections_by_statute": {},
        "votes": {},
    }))
    (out_dir / "office_action.md").write_text("")

    result = mod.run_one(pub, include_spec=True)
    # Should not error; description simply not appended
    assert result["qn_disposition"] == "allowance"
    content = (out_dir / f"{pub}.md").read_text()
    assert "## Written description / specification" not in content
