"""process_summary skill — Stage 6 with 6-dim Collaboration Quality Evaluation.

Reads the run directory, computes per-dimension scores deterministically
from the on-disk artefacts (without an LLM call), then optionally asks the
LLM to write the narrative around the scores. The scoring itself is
mechanical — readers should be able to recompute by hand from the JSON
files in run-dir.
"""
from __future__ import annotations

import argparse
import json
import re
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402


# =========================================================================
# Per-dimension probes
# =========================================================================

@dataclass
class Probe:
    name: str
    score: int          # 1-100
    evidence: str       # one sentence


def _probe_exists(p: Path) -> bool:
    return p.exists() and (p.is_dir() or p.stat().st_size > 0)


def _read_json_if_exists(p: Path) -> dict | None:
    try:
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _find_artifact(run: Path, skill: str, filename: str) -> Path | None:
    """Resolve `<skill>/<filename>` under run-dir, tolerating both layouts.

    Pipelines orchestrator writes `stage_<N>_<skill>/<filename>`, but a
    single-skill invocation writes just `<skill>/<filename>`. Try both.
    Returns the first matching Path, or None.
    """
    # 1. Direct <skill>/<filename>
    direct = run / skill / filename
    if direct.is_file():
        return direct
    # 2. Any stage_*_<skill>/<filename>
    for child in sorted(run.iterdir()):
        if not child.is_dir():
            continue
        # Match `stage_<anything>_<skill>` or `stage_<anything>_<skill_alt>`.
        # `<skill>` may use underscores; we look for an exact suffix match.
        name = child.name
        if name.startswith("stage_") and name.endswith(f"_{skill}"):
            candidate = child / filename
            if candidate.is_file():
                return candidate
        # Paper-audit pipeline layout: `<NN><letter?>_<skill>` (e.g.
        # `02e_requirements_judge`, `03c_claims_registry`). The generative
        # pipeline uses the `stage_` prefix above, so this only matches
        # audit-pipeline dirs and is inert for `full`.
        if re.match(rf"^\d+[a-z]?_{re.escape(skill)}$", name):
            candidate = child / filename
            if candidate.is_file():
                return candidate
        # Common-suffix aliases for stages whose dir name differs from the
        # skill name (e.g., `stage_5_review` for `quantum_reviewer`,
        # `stage_4_draft` for `quantum_paper`).
        SKILL_DIR_ALIASES = {
            "quantum_reviewer":   ["stage_5_review", "stage_5_re_review",
                                   "02_reviewer_panel"],
            "quantum_paper":      ["stage_4_draft", "stage_4_revision"],
            "deep_research":      ["stage_1_literature", "stage_1.5_literature",
                                   "01_research_review"],
            # The literature-surfacing role can be filled either by the
            # dedicated `literature_surfacer` skill (single-skill runs)
            # OR by `deep_research --mode full` (pipeline runs). Probe both.
            "literature_surfacer": ["stage_1_literature",
                                    "stage_1.5_literature",
                                    "deep_research"],
            "pareto_explorer":    ["stage_2_discovery"],
            "novelty_audit":      ["stage_3_audit"],
            "cross_llm_prediction": ["stage_4a_xllm"],
            "logical_fallacies":  ["stage_5b_fallacies", "03_fallacies"],
            "ablation_designer":  ["stage_4b_ablation"],
        }
        for alias_name in SKILL_DIR_ALIASES.get(skill, []):
            if name == alias_name:
                candidate = child / filename
                if candidate.is_file():
                    return candidate
    return None


def _read_artifact_json(run: Path, skill: str, filename: str) -> dict | None:
    p = _find_artifact(run, skill, filename)
    return _read_json_if_exists(p) if p else None


def _read_artifact_text(run: Path, skill: str, filename: str) -> str | None:
    p = _find_artifact(run, skill, filename)
    if p and p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return None


def _extract_paper_text(paper: Path) -> str:
    """Return the audited paper's plain text (paper-audit mode).

    PDFs are run through `pdftotext` if available; .tex/.txt/.md are read
    directly. Returns "" on any failure so scoring degrades gracefully
    (content probes simply report 'not found').
    """
    try:
        if not paper or not paper.is_file():
            return ""
        if paper.suffix.lower() == ".pdf":
            try:
                out = subprocess.run(
                    ["pdftotext", "-q", str(paper), "-"],
                    capture_output=True, text=True, timeout=60)
                return out.stdout or ""
            except (OSError, subprocess.SubprocessError):
                return ""
        return paper.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def score_novelty_rigour(run: Path, paper_text: str = "",
                         audit_mode: bool = False) -> list[Probe]:
    """Dim 1: did the novelty machinery actually run?"""
    probes = []
    if audit_mode:
        # No generative artifacts exist when auditing an external paper;
        # assess from the manuscript text instead of scoring absent files.
        t = paper_text.lower()
        has_aug = any(k in t for k in (
            "commutator-grouped", "augmented baseline", "suzuki-yoshida",
            "group-strang", "primitive-matched", "baseline catalog"))
        has_strict = any(k in t for k in (
            "strict-domination", "strict pareto", "strictly dominat",
            "pareto-domin", "pareto dominant"))
        probes.append(Probe(
            "augmented baseline catalog described in paper",
            90 if has_aug else 35,
            f"augmented/commutator-grouped baseline language present: {has_aug}"))
        probes.append(Probe(
            "strict-domination comparator described in paper",
            85 if has_strict else 35,
            f"strict-domination / Pareto language present: {has_strict}"))
        return probes
    aug = _read_artifact_json(run, "literature_surfacer", "baseline_catalog.json")
    probes.append(Probe(
        "augmented baseline catalog present",
        90 if aug and len(aug.get("rows", [])) >= 3 else
        50 if aug else 10,
        f"baseline_catalog has {len(aug.get('rows', [])) if aug else 0} rows"
    ))
    verdict = _read_artifact_json(run, "novelty_audit", "novelty_verdict.json")
    if verdict and "verdicts" in verdict:
        n_classified = len(verdict["verdicts"])
        probes.append(Probe(
            "strict-domination comparator run",
            85 if n_classified >= 1 else 20,
            f"{n_classified} LLM rows classified by novelty_audit"
        ))
        rediscoveries = sum(1 for v in verdict["verdicts"]
                            if v.get("verdict") in ("rediscovery", "dominated"))
        probes.append(Probe(
            "rediscoveries candidly classified",
            95 if rediscoveries > 0 else 60,
            f"{rediscoveries} rediscoveries surfaced "
            "(>0 means honest classification)"
        ))
    else:
        probes.append(Probe("strict-domination comparator run", 5,
                            "novelty_verdict.json not found"))
    return probes


def score_reproducibility(run: Path, paper_text: str = "",
                          audit_mode: bool = False) -> list[Probe]:
    """Dim 2: can a reviewer re-derive without the author?"""
    probes = []
    if audit_mode:
        t = paper_text.lower()
        has_audit = any(k in t for k in (
            "audit_claims", "audit pipeline", "on-disk json", "re-derive",
            "recomputed from raw", "76 numerical"))
        has_avail = any(k in t for k in (
            "code availability", "reproducib", "zenodo", "figshare",
            "github", "mit licence", "mit license", "publicly release"))
        probes.append(Probe(
            "auditable-claims infrastructure described in paper",
            85 if has_audit else 30,
            f"audit-pipeline / on-disk-artifact language present: {has_audit}"))
        probes.append(Probe(
            "availability / reproducibility statement in paper",
            75 if has_avail else 35,
            f"availability / reproducibility language present: {has_avail}"))
        return probes
    audit_script = _find_artifact(run, "novelty_audit", "audit_claims.py")
    probes.append(Probe(
        "audit_claims.py emitted",
        90 if audit_script else 10,
        f"file exists: {audit_script is not None}"
    ))
    paper = _find_artifact(run, "quantum_paper", "paper.tex")
    probes.append(Probe(
        "paper draft on disk",
        70 if paper else 30,
        f"paper.tex exists: {paper is not None}"
    ))
    pareto = _read_artifact_json(run, "pareto_explorer", "archive.json")
    probes.append(Probe(
        "pareto archive structured",
        80 if pareto and len(pareto.get("rows", [])) > 0 else 20,
        f"archive rows: {len(pareto.get('rows', [])) if pareto else 0}"
    ))
    return probes


def score_methodological_rigour(run: Path, paper_text: str = "",
                                audit_mode: bool = False) -> list[Probe]:
    """Dim 3: would methodology-focus reviewer pass?"""
    probes = []
    if audit_mode:
        # The wilson/ablation/ratio artifacts are generative-pipeline outputs;
        # in audit mode read whether the paper itself reports these practices.
        t = paper_text.lower()
        has_wilson = "wilson" in t or "binomial confidence" in t
        has_ablation = "ablation" in t
        has_recompute = any(k in t for k in (
            "recomputed from raw", "recompute", "raw on-disk", "displayed rounded"))
        probes.append(Probe(
            "Wilson CIs reported in paper",
            85 if has_wilson else 35,
            f"Wilson / binomial-CI language present: {has_wilson}"))
        probes.append(Probe(
            "ablation reported in paper",
            80 if has_ablation else 40,
            f"ablation language present: {has_ablation}"))
        probes.append(Probe(
            "recompute-from-raw principle stated",
            80 if has_recompute else 40,
            f"recompute-from-raw language present: {has_recompute}"))
    else:
        wilson = _find_artifact(run, "novelty_audit", "wilson_annotations.md")
        probes.append(Probe(
            "Wilson CIs computed",
            85 if wilson else 20,
            f"wilson_annotations.md: {wilson is not None}"
        ))
        ablation = _read_artifact_json(run, "ablation_designer", "ablation_results.json")
        probes.append(Probe(
            "ablation results present",
            80 if ablation else 30,
            f"ablation_results.json: {ablation is not None}"
        ))
        ratio = _find_artifact(run, "novelty_audit", "ratio_recompute.md")
        probes.append(Probe(
            "ratio recompute pass run",
            80 if ratio else 30,
            f"ratio_recompute.md: {ratio is not None}"
        ))
    # Claim-vs-evidence integrity (requirements_judge). Whether the paper's
    # central claims are actually licensed by its own evidence is a
    # methodological question; an unsupported claim is a rigour failure.
    # This artifact DOES exist in paper-audit mode, so the probe runs in both.
    req = _read_artifact_json(run, "requirements_judge",
                              "requirements_report.json")
    if req:
        verdict = req.get("verdict")
        reqs = req.get("requirements", []) or []
        n = len(reqs)
        met = sum(1 for r in reqs if r.get("status") in ("met", "partial"))
        frac = (met / n) if n else 0.0
        forbidden = len(req.get("forbidden_claims", []) or [])
        base = {"proceed": 90, "partial": 55, "reject": 20}.get(verdict, 40)
        score = max(15, min(100, round(base * (0.6 + 0.4 * frac)
                                       - 3 * forbidden)))
        evidence = (f"verdict={verdict}; {met}/{n} claims met-or-partial; "
                    f"{forbidden} overclaim(s) flagged")
    else:
        score = 30
        evidence = "requirements_report.json: False (stage not run)"
    probes.append(Probe("claims supported by own evidence", score, evidence))
    return probes


def score_falsifiability(run: Path, paper_text: str = "",
                         audit_mode: bool = False) -> list[Probe]:
    """Dim 4: is the claim refutable?"""
    probes = []
    if audit_mode:
        t = paper_text.lower()
        has_xllm = any(k in t for k in (
            "cross-llm", "cross llm", "claude", "codex", "gpt-5", "two frontier",
            "distinct frontier"))
        probes.append(Probe(
            "cross-LLM / multi-model falsifiability described",
            85 if has_xllm else 35,
            f"cross-LLM / multi-model language present: {has_xllm}"))
        has_neg = any(k in t for k in (
            "negative result", "failure mode", "stalls at hartree", "honest negativ",
            "does not", "falsif"))
        probes.append(Probe(
            "honest negatives surfaced in paper",
            90 if has_neg else 25,
            f"negative-result / failure-mode language present: {has_neg}"))
        return probes
    xllm = _read_artifact_json(run, "cross_llm_prediction", "results.json")
    probes.append(Probe(
        "cross-LLM with multiple vendors",
        90 if xllm and len(xllm.get("llms_used", [])) >= 2 else 40,
        f"vendors used: {(xllm or {}).get('llms_used', [])}"
    ))
    fm = _find_artifact(run, "novelty_audit", "failure_modes_required.md")
    pt = _read_artifact_text(run, "quantum_paper", "paper.tex")
    has_failure_modes_section = (
        "failure modes" in pt.lower()
        if pt else False
    )
    probes.append(Probe(
        "honest negatives surfaced",
        90 if has_failure_modes_section else
        60 if fm else 20,
        f"failure-modes section in draft: {has_failure_modes_section}; "
        f"audit required them: {fm is not None}"
    ))
    return probes


def score_domain_depth(run: Path, paper_text: str = "",
                       audit_mode: bool = False) -> list[Probe]:
    """Dim 5: does the paper show deep quantum-CS understanding?"""
    probes = []
    # In audit mode the manuscript is the audited PDF (paper_text); otherwise
    # read the generated draft. Either way these probes read prose, not files.
    text = (paper_text if audit_mode else
            _read_artifact_text(run, "quantum_paper", "paper.tex")) or ""
    has_active_space = any(k in text.lower() for k in
                           ["active space", "active-space", "(4e,", "(4e, "])
    probes.append(Probe(
        "active space stated explicitly",
        85 if has_active_space else 30,
        f"explicit active-space text found: {has_active_space}"
    ))
    has_mapping = any(k in text for k in
                      ["Jordan-Wigner", "Jordan–Wigner", "JW", "Bravyi-Kitaev",
                       "Bravyi–Kitaev", "BK ", "parity mapping"])
    probes.append(Probe(
        "fermion-to-qubit mapping stated",
        80 if has_mapping else 30,
        f"mapping reference found: {has_mapping}"
    ))
    has_precision_note = any(k in text for k in
                             ["float64", "complex64", "complex128",
                              "precision floor", "noise floor"])
    probes.append(Probe(
        "simulator precision floor disclosed",
        85 if has_precision_note else 30,
        f"precision-floor reference found: {has_precision_note}"
    ))
    return probes


def score_communication(run: Path, paper_text: str = "",
                        audit_mode: bool = False) -> list[Probe]:
    """Dim 6: will the paper read coherently?

    Sources (fallacy findings + reviewer panel verdict) exist in BOTH
    generative and paper-audit runs, so this dimension is mode-agnostic.
    """
    probes = []
    fallacy = _read_artifact_json(run, "logical_fallacies", "fallacy_findings.json")
    if fallacy and fallacy.get("_note"):
        # The skill ran but could not extract its machine-readable block —
        # a parse failure must not masquerade as a clean bill of health.
        probes.append(Probe(
            "logical fallacies absent",
            40,
            "fallacy extraction failed (parse note present); treating as not-run"
        ))
        fallacy = None
    if fallacy and "findings" in fallacy:
        n_critical = sum(1 for f in fallacy["findings"]
                         if f.get("severity") == "critical")
        n_high = sum(1 for f in fallacy["findings"]
                     if f.get("severity") == "high")
        score = 95 if n_critical == 0 and n_high <= 1 else \
                65 if n_critical == 0 else 30
        probes.append(Probe(
            "logical fallacies absent",
            score,
            f"{n_critical} critical, {n_high} high-severity fallacies"
        ))
    else:
        probes.append(Probe(
            "logical fallacies absent",
            40,
            "logical_fallacies skill not run"
        ))
    review_text = _read_artifact_text(run, "quantum_reviewer", "review_panel.md")
    if review_text:
        # If the panel produced a verdict, score based on it (rough heuristic).
        # Check most-positive first (look for the final-verdict line if present).
        # Normalize spacing variants ("Major Revisions" vs
        # "major-revisions") and prefer the vote table's EIC row;
        # check reject BEFORE accept — "not acceptable" / "reject"
        # contains the substring "accept" and used to score 85.
        lower = review_text.lower().replace(" revisions", "-revisions")                                    .replace(" revision", "-revision")
        eic_row = re.search(
            r"\|\s*editor-in-chief\s*\|\s*([a-z-]+)", lower)
        verdict_src = eic_row.group(1) if eic_row else lower
        if "reject" in verdict_src:
            score = 25
        elif "major-revision" in verdict_src:
            score = 55
        elif "minor-revision" in verdict_src:
            score = 75
        elif re.search(r"\baccept\b", verdict_src):
            score = 85
        else:
            score = 35
        probes.append(Probe(
            "reviewer panel verdict",
            score,
            "verdict heuristic from review_panel.md"
        ))
    else:
        probes.append(Probe(
            "reviewer panel verdict",
            40,
            "no review_panel.md found"
        ))
    return probes


DIMENSIONS = [
    ("Novelty rigour", score_novelty_rigour),
    ("Reproducibility", score_reproducibility),
    ("Methodological rigour", score_methodological_rigour),
    ("Falsifiability", score_falsifiability),
    ("Domain depth", score_domain_depth),
    ("Communication", score_communication),
]


def _geometric_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.exp(sum(math.log(max(v, 1)) for v in values) / len(values))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--no-llm-narrative", action="store_true",
                    help="skip the LLM narrative; emit scores only")
    ap.add_argument("--paper", type=Path, default=None,
                    help="audited paper (PDF/tex/txt). Presence switches the "
                         "content probes to read this manuscript instead of a "
                         "generated draft (paper-audit mode).")
    ap.add_argument("--audit-mode", action="store_true",
                    help="force paper-audit scoring (auto-on when --paper is "
                         "given and no generated draft is in the run-dir).")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    # Paper-audit mode: when auditing an EXTERNAL paper, the generative-pipeline
    # artifacts (paper.tex, pareto archive, baseline_catalog.json,
    # wilson_annotations.md, ...) do not exist. Scoring their absence as content
    # failures produced a meaningless composite (observed: 25/100 on a paper the
    # 5-voice panel scored 6.67/10). In audit mode the content probes read the
    # audited manuscript text and the generative-only artifact probes are
    # replaced by manuscript-derived equivalents.
    generated_draft = _find_artifact(args.run_dir, "quantum_paper", "paper.tex")
    audit_mode = bool(args.audit_mode or (args.paper and not generated_draft))
    paper_text = ""
    if audit_mode and args.paper:
        paper_text = _extract_paper_text(args.paper)

    # Mechanical scoring (no LLM).
    dim_scores: list[dict] = []
    for name, scorer in DIMENSIONS:
        probes = scorer(args.run_dir, paper_text, audit_mode)
        scored = [p for p in probes if p.score is not None]
        dim_score = (int(round(sum(p.score for p in scored) / len(scored)))
                     if scored else None)
        dim_scores.append({
            "name": name,
            "score": dim_score,
            "probes": [{"name": p.name, "score": p.score, "evidence": p.evidence}
                       for p in probes],
        })
    composite = int(round(_geometric_mean(
        [d["score"] for d in dim_scores if d["score"] is not None]
    )))
    cqe = {
        "composite": composite,
        "composite_method": "geometric_mean",
        "mode": "paper-audit" if audit_mode else "generative",
        "dimensions": dim_scores,
    }
    (args.outdir / "cqe_scores.json").write_text(
        json.dumps(cqe, indent=2), encoding="utf-8"
    )

    # Optional LLM-written narrative.
    if not args.no_llm_narrative:
        narrative_prompt = (
            "You are writing the Process Summary for a QuantumNovelty run. "
            "The 6-dimension Collaboration Quality Evaluation scored "
            "as follows:\n\n"
            f"```json\n{json.dumps(cqe, indent=2)}\n```\n\n"
            "Write a 600-900 word narrative covering:\n"
            "1. The composite verdict (1-100 scale interpretation per SKILL.md).\n"
            "2. The strongest dimension and what that says about the run.\n"
            "3. The weakest dimension and what specific stage produced it.\n"
            "4. Three highest-leverage improvements for the next run.\n\n"
            "Be candid. Do NOT inflate scores. Cite the probes by name."
        )
        try:
            result = call_llm(narrative_prompt, backend=args.llm, timeout=900)
            (args.outdir / "process_summary.md").write_text(
                result.text, encoding="utf-8"
            )
            write_backend_marker(args.outdir, result)
        except RuntimeError as e:
            (args.outdir / "process_summary.md").write_text(
                f"# Process Summary — narrative FAILED\n\n"
                f"LLM call failed: `{e}`\n\n"
                f"## Composite: {composite}/100\n\n"
                f"See cqe_scores.json for per-dimension breakdown.\n",
                encoding="utf-8"
            )
    else:
        (args.outdir / "process_summary.md").write_text(
            f"# Process Summary (no-LLM mode)\n\n## Composite: {composite}/100\n\n"
            f"See cqe_scores.json for per-dimension breakdown.\n",
            encoding="utf-8"
        )

    print(f"process_summary: composite CQE = {composite}/100; "
          f"see {args.outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
