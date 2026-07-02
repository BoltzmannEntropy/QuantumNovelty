"""Pipeline orchestrator — stages 1-6 with mid-entry support.

Composes the QuantumNovelty skill catalog into the academic-pipeline pattern
adapted from ARS. Six stages, three entry points:

  Full pipeline (Stage 1 → 6):
    1. Literature surface
    2. Discovery + Pareto archive
    3. Novelty audit (augmented baselines + audit-and-falsify)
    4. Paper draft + cross-LLM falsifiability check
    5. Reviewer panel
    6. Process summary (6-dim CQE)

  Mid-entry at Stage 2.5 (paper already exists, integrity first):
    1.5 (lit surface for the paper's topic) → 3 → 5 → 6

  Mid-entry at Stage 4 (reviewer comments in hand):
    4 (revision) → 5 (re-review) → 6

Each stage runs a single QuantumNovelty skill (or one skill per call) and
writes its output to `<outdir>/stage_<N>_<skill>/`.

Resumability: each stage checks whether its output dir already exists;
re-running with the same `--outdir` skips completed stages unless
`--force` is passed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Local import for structured telemetry helpers (ARC's stage_health /
# pipeline_summary / decision_history / checkpoint pattern).
sys.path.insert(0, str(Path(__file__).resolve().parent / "common"))
import telemetry  # noqa: E402  pylint: disable=wrong-import-position

# Strict-env defaults: no silent backend fallback.
os.environ.setdefault("CLAUDE_DISABLE_CODEX_FALLBACK", "1")
os.environ.setdefault("INVOKE_LLM_NO_FALLBACK", "1")
os.environ.setdefault("QN_DISABLE_BACKEND_FALLBACK", "1")


@dataclass
class StageResult:
    stage: str
    skill: str
    rc: int
    elapsed_s: float
    outdir: Path
    skipped: bool = False
    notes: list[str] = field(default_factory=list)


def _stage_complete(out: Path) -> bool:
    """Heuristic: stage already ran iff its outdir has at least one
    PRIMARY artifact.

    Underscore-prefixed files are scaffolding (telemetry markers like
    _stage_health.json / _heartbeat.txt, backend markers, quality-gate
    extracts) and prompts/logs are process residue — none of them prove
    the stage produced its output. A FAILED stage leaves _stage_health
    + the prompt behind; counting those as "complete" would make the
    resume path skip stages that never ran.
    """
    if not out.is_dir():
        return False
    for p in out.iterdir():
        if not p.is_file():
            continue
        if p.name.startswith("_") or p.name.startswith("full_prompt"):
            continue
        return True
    return False


# Stage execution order for --resume-from comparisons (paper-audit +
# patent-audit ids; patent ids 01-prior-art / 02-examiner share the tail
# stages 03-fallacies / 03c-claims-registry / 04-cqe with paper-audit).
_STAGE_ORDER = ["01-research", "01-prior-art", "00-evidence-ledger",
                "02-reviewer", "02-examiner",
                "02e-requirements-judge", "02b-novelty-audit",
                "02c-cross-llm", "02d-argument-structure",
                "03-fallacies", "03b-synthesizer",
                "03c-claims-registry", "03d-citation-integrity",
                "03e-disclosure-audit", "03f-revision-planner",
                "98-evidence-ledger-audit", "04-cqe"]


def _resumed_past(stage_id: str, resume_from: str | None) -> bool:
    """True when --resume-from says this stage is already complete."""
    if not resume_from:
        return False
    try:
        target = next(i for i, s in enumerate(_STAGE_ORDER)
                      if resume_from in s)
    except StopIteration:
        return False
    try:
        mine = _STAGE_ORDER.index(stage_id)
    except ValueError:
        return False
    return mine < target


def _run_skill(skill: str, outdir: Path, args: list[str],
               force: bool, stage_id: str | None = None,
               run_dir: Path | None = None,
               resume_from: str | None = None) -> StageResult:
    """Run one skill driver as a chain stage.

    Stage-bracketed with structured telemetry: writes _stage_health.json
    (status / duration / artifact-count), appends one decision_history
    entry, and respects the QN_HITL_PAUSE_AFTER env (drops a
    checkpoint.json + sys.exit(0) when the env matches stage_id).
    """
    out = outdir
    stage_id = stage_id or skill
    skill_run_sh = REPO / "skills" / skill / "run.sh"

    # Resume path: skip if --resume-from marks this stage complete, or
    # the outdir is already populated.
    if _resumed_past(stage_id, resume_from) and not force:
        return StageResult(
            stage=skill, skill=skill, rc=0, elapsed_s=0.0, outdir=out,
            skipped=True,
            notes=[f"skipped: --resume-from {resume_from}"]
        )
    if _stage_complete(out) and not force:
        # Emit a health record so pipeline_summary sees the stage — but
        # never clobber an existing one (it holds the REAL duration).
        if not (out / "_stage_health.json").is_file():
            telemetry.stage_health_begin(out, stage_id)
            telemetry.stage_health_end(out, status="done")
        if run_dir is not None:
            telemetry.decision_log(
                run_dir, "proceed",
                rollback_target=None, rollback_stage_num=0, attempt=1,
            )
        return StageResult(
            stage=skill, skill=skill, rc=0, elapsed_s=0.0, outdir=out,
            skipped=True, notes=["resumed: stage outputs present"]
        )

    out.mkdir(parents=True, exist_ok=True)
    telemetry.stage_health_begin(out, stage_id)
    full_args = ["bash", str(skill_run_sh), "--outdir", str(out)] + args
    t0 = time.monotonic()
    r = subprocess.run(full_args)
    elapsed = time.monotonic() - t0

    if r.returncode == 0:
        telemetry.stage_health_end(out, status="done")
        decision = "proceed"
    else:
        telemetry.stage_health_end(
            out, status="failed",
            error=f"skill {skill} exited with rc={r.returncode}",
        )
        decision = "fail"
    if run_dir is not None:
        telemetry.decision_log(
            run_dir, decision, rollback_target=None,
            rollback_stage_num=0, attempt=1,
        )
        # Honor QN_HITL_PAUSE_AFTER (matches substring of stage_id).
        if telemetry.pause_after_stage(run_dir, stage_id):
            sys.exit(0)

    return StageResult(stage=skill, skill=skill, rc=r.returncode,
                       elapsed_s=elapsed, outdir=out,
                       notes=[f"command: {' '.join(full_args)}",
                              f"stage_id: {stage_id}"])


# =========================================================================
# Pipelines
# =========================================================================

def pipeline_full(args: argparse.Namespace) -> int:
    """Full Stage 1 → 6 pipeline."""
    if not args.topic:
        print("ERROR: the full pipeline requires --topic", file=sys.stderr)
        return 2
    results: list[StageResult] = []
    base = args.outdir
    # common_flags carries ONLY --llm. Context flags (--journal,
    # --quantum-lib) are added per-stage below — passing them to a skill
    # whose argparse doesn't define them kills the stage with rc=2.
    common_flags = ["--llm", args.llm]
    journal_flags = (["--journal", args.journal] if args.journal else [])
    qlib_flags = (["--quantum-lib", args.quantum_lib]
                  if args.quantum_lib else [])

    # Stage 1: literature surface
    results.append(_run_skill(
        "deep_research", base / "stage_1_literature",
        ["--mode", "full", "--topic", args.topic]
        + journal_flags + qlib_flags + common_flags,
        force=args.force, stage_id="01-literature", run_dir=base,
    ))

    # Stage 2: pareto discovery (stub at this version)
    if args.hamiltonian:
        results.append(_run_skill(
            "pareto_explorer", base / "stage_2_discovery",
            ["--hamiltonian", args.hamiltonian,
             "--baseline", args.baseline or "UCCSD-1-Trotter"]
            + common_flags,
            force=args.force, stage_id="02-discovery", run_dir=base,
        ))

    # Stage 3: novelty audit (needs pareto archive + augmented catalog)
    pareto_archive = base / "stage_2_discovery" / "archive.json"
    aug_catalog   = base / "stage_1_literature" / "baseline_catalog.json"
    if pareto_archive.is_file() and args.paper:
        results.append(_run_skill(
            "novelty_audit", base / "stage_3_audit",
            ["--pareto-archive", str(pareto_archive),
             "--augmented-baselines", str(aug_catalog),
             "--draft", str(args.paper)] + common_flags,
            force=args.force, stage_id="03-novelty-audit", run_dir=base,
        ))

    # Stage 4: paper draft
    if not args.paper:
        results.append(_run_skill(
            "quantum_paper", base / "stage_4_draft",
            ["--mode", "full", "--topic", args.topic]
            + journal_flags + qlib_flags + common_flags,
            force=args.force, stage_id="04-draft", run_dir=base,
        ))

    # Stage 4a: cross-LLM (if configured)
    if args.hamiltonian and args.geometry_sweep:
        results.append(_run_skill(
            "cross_llm_prediction", base / "stage_4a_xllm",
            ["--hamiltonian", args.hamiltonian,
             "--geometry-sweep", args.geometry_sweep,
             "--llms", args.llms or "claude,codex"] + common_flags,
            force=args.force, stage_id="04a-cross-llm", run_dir=base,
        ))

    # Stage 5: reviewer panel
    paper_for_review = args.paper or (base / "stage_4_draft" / "paper.tex")
    if Path(paper_for_review).is_file():
        results.append(_run_skill(
            "quantum_reviewer", base / "stage_5_review",
            ["--mode", "full", "--draft", str(paper_for_review)]
            + journal_flags + common_flags,
            force=args.force, stage_id="05-reviewer", run_dir=base,
        ))
        results.append(_run_skill(
            "logical_fallacies", base / "stage_5b_fallacies",
            ["--draft", str(paper_for_review)] + common_flags,
            force=args.force, stage_id="05b-fallacies", run_dir=base,
        ))

    # Stage 6: process summary
    results.append(_run_skill(
        "process_summary", base / "stage_6_summary",
        ["--run-dir", str(base)] + common_flags,
        force=args.force, stage_id="06-cqe", run_dir=base,
    ))

    # Chain-end telemetry aggregation.
    base.mkdir(parents=True, exist_ok=True)
    telemetry.pipeline_summary(base)
    telemetry.audit_heartbeats(base)
    final_decision = "proceed" if all(r.rc == 0 for r in results) else "fail"
    telemetry.decision_log(base, final_decision)
    return _emit_pipeline_summary(base, results)


def pipeline_midentry_2_5(args: argparse.Namespace) -> int:
    """Mid-entry: paper exists; integrity-first pass."""
    if not args.paper:
        print("ERROR: mid-entry-stage-2.5 requires --paper", file=sys.stderr)
        return 2
    results: list[StageResult] = []
    base = args.outdir
    common_flags = ["--llm", args.llm]
    journal_flags = (["--journal", args.journal] if args.journal else [])

    # Stage 1.5: literature for the paper's topic (best-effort)
    if args.topic:
        results.append(_run_skill(
            "deep_research", base / "stage_1.5_literature",
            ["--mode", "full", "--topic", args.topic]
            + journal_flags + common_flags,
            force=args.force, stage_id="01.5-literature", run_dir=base,
        ))

    # Stage 3: novelty audit (read paper directly; no pareto archive)
    # The skill accepts a draft alone; will only do the ratio/Wilson passes
    # without a Pareto archive. This is the "integrity first" mode.
    # (Implementation note: novelty_audit currently requires --pareto-archive;
    # for paper-only audits, we feed it an empty archive.)
    empty_archive = base / "_empty_archive.json"
    base.mkdir(parents=True, exist_ok=True)
    empty_archive.write_text(json.dumps({"rows": []}), encoding="utf-8")
    results.append(_run_skill(
        "novelty_audit", base / "stage_3_audit",
        ["--pareto-archive", str(empty_archive),
         "--draft", str(args.paper)] + common_flags,
        force=args.force, stage_id="03-novelty-audit", run_dir=base,
    ))

    # Stage 5: reviewer panel
    results.append(_run_skill(
        "quantum_reviewer", base / "stage_5_review",
        ["--mode", "full", "--draft", str(args.paper)]
        + journal_flags + common_flags,
        force=args.force, stage_id="05-reviewer", run_dir=base,
    ))
    results.append(_run_skill(
        "logical_fallacies", base / "stage_5b_fallacies",
        ["--draft", str(args.paper)] + common_flags,
        force=args.force, stage_id="05b-fallacies", run_dir=base,
    ))

    # Stage 6: process summary
    results.append(_run_skill(
        "process_summary", base / "stage_6_summary",
        ["--run-dir", str(base)] + common_flags,
        force=args.force, stage_id="06-cqe", run_dir=base,
    ))

    # Chain-end telemetry aggregation.
    telemetry.pipeline_summary(base)
    telemetry.audit_heartbeats(base)
    final_decision = "proceed" if all(r.rc == 0 for r in results) else "fail"
    telemetry.decision_log(base, final_decision)
    return _emit_pipeline_summary(base, results)


def pipeline_midentry_4(args: argparse.Namespace) -> int:
    """Mid-entry: reviewer comments in hand; revision pass."""
    if not (args.paper and args.reviewer_comments):
        print("ERROR: mid-entry-stage-4 requires --paper AND "
              "--reviewer-comments", file=sys.stderr)
        return 2
    results: list[StageResult] = []
    base = args.outdir
    common_flags = ["--llm", args.llm]
    journal_flags = (["--journal", args.journal] if args.journal else [])

    # Stage 4 (revision)
    results.append(_run_skill(
        "quantum_paper", base / "stage_4_revision",
        ["--mode", "revision",
         "--draft", str(args.paper),
         "--reviewer-comments", str(args.reviewer_comments)]
        + journal_flags + common_flags,
        force=args.force, stage_id="04-revision", run_dir=base,
    ))
    revised_paper = base / "stage_4_revision" / "paper_v2.tex"

    # Stage 5 (re-review)
    if revised_paper.is_file():
        results.append(_run_skill(
            "quantum_reviewer", base / "stage_5_re_review",
            ["--mode", "re-review",
             "--draft", str(revised_paper),
             "--prior-comments", str(args.reviewer_comments)]
            + journal_flags + common_flags,
            force=args.force, stage_id="05-re-review", run_dir=base,
        ))

    # Stage 6
    results.append(_run_skill(
        "process_summary", base / "stage_6_summary",
        ["--run-dir", str(base)] + common_flags,
        force=args.force, stage_id="06-cqe", run_dir=base,
    ))

    # Chain-end telemetry aggregation.
    base.mkdir(parents=True, exist_ok=True)
    telemetry.pipeline_summary(base)
    telemetry.audit_heartbeats(base)
    final_decision = "proceed" if all(r.rc == 0 for r in results) else "fail"
    telemetry.decision_log(base, final_decision)
    return _emit_pipeline_summary(base, results)


# =========================================================================
# paper-audit pipeline (used by examples/end_to_end/two_paper_novelty)
# =========================================================================
#
# Default-on stages for the paper-audit pipeline:
#   research, reviewer, fallacies, cqe
#
# Each is named so the --skip-<name> / --with-<name> dispatcher in
# chain/run.sh can flip it on or off without editing this file.
# claims-registry is a DEFAULT-ON integrity gate (deterministic, zero
# LLM cost); citation-integrity arms automatically whenever --bib is
# passed. Both stay skippable via --skip-X — QN documents absences
# rather than forbidding them.
PAPER_AUDIT_DEFAULT_ON = ("research", "reviewer", "fallacies",
                          "claims-registry", "cqe")
PAPER_AUDIT_OPTIONAL = ("novelty-audit", "cross-llm", "synthesizer",
                        "argument-structure", "requirements-judge",
                        "citation-integrity", "disclosure-audit",
                        "revision-planner", "evidence-ledger")

# patent-audit: the USPTO-examiner analogue of paper-audit. Default-on
# stages reuse the shared `fallacies` + `cqe` toggles (already registered
# for paper-audit); `prior-art` and `examiner` are patent-specific.
PATENT_AUDIT_DEFAULT_ON = ("prior-art", "examiner", "fallacies", "cqe")
PATENT_AUDIT_OPTIONAL = ("disclosure-audit",)


def _stage_enabled(name: str, args: argparse.Namespace,
                   default_on: bool) -> bool:
    """Per-stage --with-X / --skip-X resolution.

    Precedence: --skip-X always wins; --with-X is required for opt-in
    stages; default_on stages are on unless --skip-X is passed.
    """
    skip_flag = "skip_" + name.replace("-", "_")
    with_flag = "with_" + name.replace("-", "_")
    if getattr(args, skip_flag, False):
        return False
    if default_on:
        return True
    return getattr(args, with_flag, False)


def _log_stage_decision(name: str, enabled: bool, reason: str,
                        notes: list[str]) -> None:
    glyph = "+" if enabled else "-"
    notes.append(f"  [{glyph}] {name:18s}  {reason}")


def pipeline_paper_audit(args: argparse.Namespace) -> int:
    """Audit a single existing paper:

    research -> reviewer -> fallacies -> cqe

    plus opt-in stages (novelty-audit, cross-llm) when their required
    inputs are also passed.
    """
    if not args.paper:
        print("ERROR: paper-audit requires --paper PATH", file=sys.stderr)
        return 2
    results: list[StageResult] = []
    decisions: list[str] = ["# Stage decisions"]
    base = args.outdir
    common_flags = ["--llm", args.llm]
    journal_flags = (["--journal", args.journal] if args.journal else [])
    qlib_flags = (["--quantum-lib", args.quantum_lib]
                  if args.quantum_lib else [])

    venue = args.journal or "generic peer-reviewed journal"
    paper_path = str(args.paper)

    # Stage: research
    if _stage_enabled("research", args, default_on=True):
        _log_stage_decision("research", True, "default-on; deep_research --mode review",
                            decisions)
        research_args = ["--mode", "review", "--paper", paper_path]
        if args.topic:
            research_args += ["--topic", args.topic]
        else:
            research_args += ["--topic", venue]
        results.append(_run_skill(
            "deep_research", base / "01_research_review",
            research_args + journal_flags + qlib_flags + common_flags,
            force=args.force,
            stage_id="01-research", run_dir=base,
            resume_from=args.resume_from,
        ))
    else:
        _log_stage_decision("research", False, "--skip-research passed", decisions)

    # Stage: evidence-ledger (build pass; opt-in). Deterministic
    # pre-registration of the paper's permitted facts so the post-review
    # audit pass (stage 98) can flag reviewer hallucinations. Runs before
    # the LLM review stages.
    if _stage_enabled("evidence-ledger", args, default_on=False):
        _log_stage_decision("evidence-ledger", True,
                            "--with-evidence-ledger; building ledger",
                            decisions)
        ledger_args = ["--mode", "ledger", "--paper", paper_path]
        if args.bib and Path(args.bib).is_file():
            ledger_args += ["--bib", str(args.bib)]
        results.append(_run_skill(
            "evidence_ledger", base / "00_evidence_ledger",
            ledger_args, force=args.force,
            stage_id="00-evidence-ledger", run_dir=base,
            resume_from=args.resume_from,
        ))

    # Stage: reviewer
    if _stage_enabled("reviewer", args, default_on=True):
        _log_stage_decision("reviewer", True, "default-on; quantum_reviewer --mode full",
                            decisions)
        results.append(_run_skill(
            "quantum_reviewer", base / "02_reviewer_panel",
            ["--mode", "full", "--draft", paper_path]
            + journal_flags + common_flags,
            force=args.force,
            stage_id="02-reviewer", run_dir=base,
            resume_from=args.resume_from,
        ))
    else:
        _log_stage_decision("reviewer", False, "--skip-reviewer passed", decisions)

    # Stage: requirements-judge (opt-in). Claim-vs-evidence audit: does the
    # paper's own evidence support its central claims? Emits an
    # allowed/forbidden-claims manifest — the hypothesis-level companion to
    # the deterministic claims-registry numeric gate.
    if _stage_enabled("requirements-judge", args, default_on=False):
        _log_stage_decision("requirements-judge", True,
                            "--with-requirements-judge; claim-vs-evidence "
                            "audit", decisions)
        results.append(_run_skill(
            "requirements_judge", base / "02e_requirements_judge",
            ["--mode", "review", "--paper", paper_path]
            + journal_flags + common_flags, force=args.force,
            stage_id="02e-requirements-judge", run_dir=base,
            resume_from=args.resume_from,
        ))

    # Stage: fallacies
    if _stage_enabled("fallacies", args, default_on=True):
        _log_stage_decision("fallacies", True, "default-on; 11 quantum-CS + standard",
                            decisions)
        results.append(_run_skill(
            "logical_fallacies", base / "03_fallacies",
            ["--draft", paper_path] + common_flags, force=args.force,
            stage_id="03-fallacies", run_dir=base,
            resume_from=args.resume_from,
        ))
    else:
        _log_stage_decision("fallacies", False, "--skip-fallacies passed", decisions)

    # Stage: novelty-audit (opt-in; needs --pareto-archive)
    if _stage_enabled("novelty-audit", args, default_on=False):
        if args.pareto_archive and Path(args.pareto_archive).is_file():
            _log_stage_decision("novelty-audit", True,
                                "--with-novelty-audit; pareto-archive provided",
                                decisions)
            nv_args = ["--pareto-archive", str(args.pareto_archive),
                       "--draft", paper_path]
            if args.augmented_baselines:
                nv_args += ["--augmented-baselines", str(args.augmented_baselines)]
            results.append(_run_skill(
                "novelty_audit", base / "02b_novelty_audit",
                nv_args + common_flags, force=args.force,
                stage_id="02b-novelty-audit", run_dir=base,
            ))
        else:
            _log_stage_decision("novelty-audit", False,
                                "--with-novelty-audit set but --pareto-archive missing",
                                decisions)

    # Stage: cross-llm (opt-in; needs --geometry-sweep + --hamiltonian + --llms)
    if _stage_enabled("cross-llm", args, default_on=False):
        if args.geometry_sweep and args.hamiltonian:
            _log_stage_decision("cross-llm", True,
                                "--with-cross-llm; geometry-sweep + hamiltonian provided",
                                decisions)
            results.append(_run_skill(
                "cross_llm_prediction", base / "02c_cross_llm",
                ["--hamiltonian", args.hamiltonian,
                 "--geometry-sweep", args.geometry_sweep,
                 "--llms", args.llms or "claude,codex"] + common_flags,
                force=args.force,
                stage_id="02c-cross-llm", run_dir=base,
            ))
        else:
            _log_stage_decision("cross-llm", False,
                                "--with-cross-llm set but inputs missing",
                                decisions)

    # Stage: argument-structure (opt-in). Argument-architecture audit:
    # premises -> intermediate claims -> conclusion map, claim-proof
    # gap, Claim/Mechanism/Evidence proportionality, narrative debts.
    if _stage_enabled("argument-structure", args, default_on=False):
        _log_stage_decision("argument-structure", True,
                            "--with-argument-structure", decisions)
        results.append(_run_skill(
            "argument_structure", base / "02d_argument_structure",
            ["--paper", paper_path] + journal_flags + common_flags,
            force=args.force,
            stage_id="02d-argument-structure", run_dir=base,
            resume_from=args.resume_from,
        ))

    # Stage: synthesizer (opt-in; ARS editorial_synthesizer pattern).
    # Consumes the panel + fallacy +
    # research outputs already in this run's outdir; produces the
    # Editorial Decision Package. Runs after fallacies so it can fold
    # CONSENSUS-0 entries for findings only the fallacy stage caught.
    if _stage_enabled("synthesizer", args, default_on=False):
        panel_md = base / "02_reviewer_panel" / "review_panel.md"
        if panel_md.is_file():
            _log_stage_decision("synthesizer", True,
                                "--with-synthesizer; panel output present",
                                decisions)
            synth_args = ["--mode", "synthesis",
                          "--draft", paper_path,
                          "--panel", str(panel_md)]
            fallacy_md = base / "03_fallacies" / "fallacy_report.md"
            if fallacy_md.is_file():
                synth_args += ["--fallacy-report", str(fallacy_md)]
            research_md = (base / "01_research_review"
                           / "research_quality_review.md")
            if research_md.is_file():
                synth_args += ["--research-review", str(research_md)]
            results.append(_run_skill(
                "quantum_reviewer", base / "03b_editorial_synthesis",
                synth_args + journal_flags + common_flags,
                force=args.force,
                stage_id="03b-synthesizer", run_dir=base,
                resume_from=args.resume_from,
            ))
        else:
            _log_stage_decision("synthesizer", False,
                                "--with-synthesizer set but no panel "
                                "output (run the reviewer stage first)",
                                decisions)

    # Stage: claims-registry (DEFAULT-ON integrity gate; deterministic,
    # zero LLM cost). Numeric registry from Results/Experiments/Tables
    # gating the other sections — the "abstract says 98.3%, table says
    # 87%" catcher.
    if _stage_enabled("claims-registry", args, default_on=True):
        _log_stage_decision("claims-registry", True,
                            "default-on integrity gate; deterministic",
                            decisions)
        results.append(_run_skill(
            "claims_registry", base / "03c_claims_registry",
            ["--paper", paper_path], force=args.force,
            stage_id="03c-claims-registry", run_dir=base,
            resume_from=args.resume_from,
        ))

    # Stage: citation-integrity (integrity gate; arms automatically when
    # --bib is provided, --with-citation-integrity also accepted).
    # Deterministic + CrossRef HTTP; no LLM, no RAG.
    if _stage_enabled("citation-integrity", args,
                      default_on=bool(args.bib)):
        if args.bib and Path(args.bib).is_file():
            _log_stage_decision("citation-integrity", True,
                                "integrity gate; --bib provided",
                                decisions)
            results.append(_run_skill(
                "citation_integrity", base / "03d_citation_integrity",
                ["--paper", paper_path, "--bib", str(args.bib)],
                force=args.force,
                stage_id="03d-citation-integrity", run_dir=base,
                resume_from=args.resume_from,
            ))
        else:
            _log_stage_decision("citation-integrity", False,
                                "--with-citation-integrity set but --bib "
                                "missing (needs the manuscript's .bib)",
                                decisions)

    # Stage: disclosure-audit (opt-in). Funding / COI / ethics /
    # data-and-code-availability checklist.
    if _stage_enabled("disclosure-audit", args, default_on=False):
        _log_stage_decision("disclosure-audit", True,
                            "--with-disclosure-audit", decisions)
        results.append(_run_skill(
            "disclosure_audit", base / "03e_disclosure_audit",
            ["--paper", paper_path] + journal_flags + common_flags,
            force=args.force,
            stage_id="03e-disclosure-audit", run_dir=base,
            resume_from=args.resume_from,
        ))

    # Stage: revision-planner (opt-in). Anchors every roadmap item to
    # ¶NNN paragraph IDs + verbatim judge evidence + a proposed edit.
    # Needs the panel (for the gate fallback) — synthesis preferred.
    if _stage_enabled("revision-planner", args, default_on=False):
        # The planner needs an actual roadmap to anchor: a synthesis
        # report, or a quality gate with non-empty required_actions. A
        # gate that parsed no actions would make the skill exit 3, so
        # gate the launch on content, not file existence.
        gate = base / "02_reviewer_panel" / "_quality_gate.json"
        synth = base / "03b_editorial_synthesis"
        roadmap_ok = any(p.suffix == ".md" and not p.name.startswith("_")
                         for p in synth.glob("*.md")) if synth.is_dir() \
            else False
        if not roadmap_ok and gate.is_file():
            try:
                roadmap_ok = bool(json.loads(
                    gate.read_text(encoding="utf-8")).get("required_actions"))
            except (json.JSONDecodeError, OSError):
                roadmap_ok = False
        if roadmap_ok:
            _log_stage_decision("revision-planner", True,
                                "--with-revision-planner; roadmap source "
                                "present", decisions)
            results.append(_run_skill(
                "revision_planner", base / "03f_revision_plan",
                ["--paper", paper_path, "--run-dir", str(base)]
                + common_flags, force=args.force,
                stage_id="03f-revision-planner", run_dir=base,
                resume_from=args.resume_from,
            ))
        else:
            _log_stage_decision("revision-planner", False,
                                "--with-revision-planner set but no "
                                "synthesis report and no quality gate "
                                "with required_actions to anchor",
                                decisions)

    # Stage: evidence-ledger (audit pass; armed by the same
    # --with-evidence-ledger). Scans every review report produced above
    # against the pre-registered ledger and flags reviewer hallucinations.
    # Runs after all review stages, before the CQE summary. Informational —
    # never fails the chain.
    if _stage_enabled("evidence-ledger", args, default_on=False):
        ledger_json = base / "00_evidence_ledger" / "ledger.json"
        if ledger_json.is_file():
            _log_stage_decision("evidence-ledger", True,
                                "audit pass; ledger present", decisions)
            results.append(_run_skill(
                "evidence_ledger", base / "98_evidence_ledger_audit",
                ["--mode", "audit", "--ledger", str(ledger_json),
                 "--run-dir", str(base)], force=args.force,
                stage_id="98-evidence-ledger-audit", run_dir=base,
                resume_from=args.resume_from,
            ))
        else:
            _log_stage_decision("evidence-ledger", False,
                                "audit pass skipped: ledger.json absent "
                                "(build pass did not run)", decisions)

    # Stage: cqe (process_summary, always last)
    if _stage_enabled("cqe", args, default_on=True):
        # paper-audit mode: tell the CQE scorer this is an external paper so it
        # reads the manuscript text rather than scoring absent generative
        # artifacts (the 25/100-vs-6.67/10 mismatch fix).
        cqe_args = ["--run-dir", str(base), "--audit-mode",
                    "--paper", str(args.paper)]
        if args.no_llm_narrative:
            cqe_args.append("--no-llm-narrative")
        _log_stage_decision(
            "cqe", True,
            "default-on; 6-dim composite"
            + ("; --no-llm-narrative" if args.no_llm_narrative else ""),
            decisions)
        results.append(_run_skill(
            "process_summary", base / "04_summary",
            cqe_args + common_flags, force=args.force,
            stage_id="04-cqe", run_dir=base,
            resume_from=args.resume_from,
        ))
    else:
        _log_stage_decision("cqe", False, "--skip-cqe passed", decisions)

    # Ensure base exists even if every stage was skipped via flags.
    base.mkdir(parents=True, exist_ok=True)
    # Chain-end aggregation: per-stage health → pipeline_summary.json
    # and walk heartbeats → HEARTBEAT_AUDIT.md. Both are idempotent and
    # write distinct files from the legacy _run_summary.json that
    # _emit_pipeline_summary writes below.
    telemetry.pipeline_summary(base)
    telemetry.audit_heartbeats(base)
    # Final decision_log entry capturing pipeline outcome.
    final_decision = "proceed" if all(r.rc == 0 for r in results) else "fail"
    telemetry.decision_log(base, final_decision)

    # Persist the chain configuration alongside the pipeline summary so
    # the report builder can quote which stages actually ran.
    chain_config = {
        "pipeline": "paper-audit",
        "llm": args.llm,
        "paper": paper_path,
        "venue": args.journal,
        "topic": args.topic,
        "stages_default_on": list(PAPER_AUDIT_DEFAULT_ON),
        "stages_optional": list(PAPER_AUDIT_OPTIONAL),
        "stages_ran": [r.stage for r in results if not r.skipped],
        "stages_skipped_by_flag": [
            name for name in PAPER_AUDIT_DEFAULT_ON
            if getattr(args, "skip_" + name.replace("-", "_"), False)
        ],
        "stages_opted_in_by_flag": [
            name for name in PAPER_AUDIT_OPTIONAL
            if getattr(args, "with_" + name.replace("-", "_"), False)
        ],
        "pause_after": getattr(args, "pause_after", None),
        "resume_from": getattr(args, "resume_from", None),
        "decision_log": decisions,
    }
    base.mkdir(parents=True, exist_ok=True)
    (base / "_chain_config.json").write_text(
        json.dumps(chain_config, indent=2), encoding="utf-8"
    )
    return _emit_pipeline_summary(base, results)


def _build_patent_report_pdf(base: Path) -> None:
    """Final step of patent-audit: render the styled PDF report.

    Always runs (the pipeline should produce a PDF). Graceful: if the
    builder or a LaTeX engine is missing it logs and returns rather than
    failing the run. Compiles with lualatex (UTF-8-native, for the Greek /
    math glyphs the examiner prose emits), falling back to pdflatex.
    """
    builder = (REPO / "examples" / "end_to_end" / "patent_audit"
               / "build_patent_report.py")
    if not builder.is_file():
        print(f"[patent-audit] report builder not found at {builder}; "
              "skipping PDF")
        return
    tex = base / "PATENT_REPORT.tex"
    try:
        r = subprocess.run(
            [sys.executable, str(builder), "--run-dir", str(base),
             "--out", str(tex)],
            capture_output=True, text=True, timeout=180)
        if r.returncode != 0 or not tex.is_file():
            print("[patent-audit] PDF .tex build failed: "
                  f"{(r.stderr or r.stdout)[:300]}")
            return
    except Exception as e:                       # noqa: BLE001
        print(f"[patent-audit] report builder error: {e}")
        return
    engine = shutil.which("lualatex") or shutil.which("pdflatex")
    if not engine:
        print(f"[patent-audit] wrote {tex}; no lualatex/pdflatex on PATH "
              "— PDF not compiled")
        return
    for _ in range(2):          # two passes for refs/longtables
        try:
            subprocess.run(
                [engine, "-interaction=nonstopmode", tex.name],
                cwd=str(base), capture_output=True, text=True, timeout=240)
        except Exception as e:                   # noqa: BLE001
            print(f"[patent-audit] {Path(engine).name} error: {e}")
            break
    pdf = base / "PATENT_REPORT.pdf"
    if pdf.is_file():
        print(f"[patent-audit] report PDF: {pdf}")
    else:
        print(f"[patent-audit] {Path(engine).name} did not produce {pdf}; "
              f"see PATENT_REPORT.log in {base}")


def pipeline_patent_audit(args: argparse.Namespace) -> int:
    """Audit a single quantum-computing patent (the USPTO-examiner analogue
    of paper-audit):

    prior-art research -> USPTO examiner panel -> fallacies -> cqe

    Input is a patent SOURCE (Google Patents URL, publication number, or a
    saved file) via --patent. The patent is materialized once to a
    structured Markdown file that the text-based stages consume; the
    examiner stage takes the original source so it gets full bibliographic
    metadata (kind code A1 vs B2 decides application-vs-granted framing).
    """
    if not getattr(args, "patent", None):
        print("ERROR: patent-audit requires --patent SOURCE "
              "(URL / publication number / saved file)", file=sys.stderr)
        return 2

    # Materialize the patent once (single fetch) into the run dir so every
    # downstream stage reads the same bytes and the run is reproducible.
    sys.path.insert(0, str(REPO / "skills" / "common"))
    try:
        from patent_io import load_patent  # noqa: E402
        patent = load_patent(str(args.patent))
    except Exception as e:                       # noqa: BLE001 — surface clean
        print(f"ERROR: could not load patent {args.patent!r}: {e}",
              file=sys.stderr)
        return 2

    base = args.outdir
    base.mkdir(parents=True, exist_ok=True)
    patent_md = base / "_patent_extracted.md"
    patent_md.write_text(patent.to_markdown(), encoding="utf-8")
    patent_path = str(patent_md)
    print(f"[patent-audit] {patent.pub_number} ({patent.kind_code}) — "
          f"{patent.n_claims()} claims -> {patent_md}")

    results: list[StageResult] = []
    decisions: list[str] = ["# Stage decisions"]
    common_flags = ["--llm", args.llm]
    journal_flags = (["--journal", args.journal] if args.journal else [])
    qlib_flags = (["--quantum-lib", args.quantum_lib]
                  if args.quantum_lib else [])
    topic = args.topic or patent.title or "quantum-computing patent"

    # Stage: prior-art (deep_research --mode review over the patent text).
    if _stage_enabled("prior-art", args, default_on=True):
        _log_stage_decision("prior-art", True,
                            "default-on; deep_research --mode review "
                            "(prior-art surface)", decisions)
        results.append(_run_skill(
            "deep_research", base / "01_prior_art",
            ["--mode", "review", "--paper", patent_path, "--topic", topic]
            + journal_flags + qlib_flags + common_flags,
            force=args.force, stage_id="01-prior-art", run_dir=base,
            resume_from=args.resume_from,
        ))
    else:
        _log_stage_decision("prior-art", False, "--skip-prior-art passed",
                            decisions)

    # Stage: examiner (the USPTO 6-voice panel -> Office Action).
    if _stage_enabled("examiner", args, default_on=True):
        _log_stage_decision("examiner", True,
                            "default-on; patent_reviewer --mode full "
                            "(USPTO §§101/102/103/112 panel)", decisions)
        exam_args = ["--mode", "full", "--patent", str(args.patent),
                     "--filing-standard", args.filing_standard]
        if getattr(args, "art_unit", None):
            exam_args += ["--art-unit", args.art_unit]
        results.append(_run_skill(
            "patent_reviewer", base / "02_examiner_panel",
            exam_args + common_flags, force=args.force,
            stage_id="02-examiner", run_dir=base,
            resume_from=args.resume_from,
        ))
    else:
        _log_stage_decision("examiner", False, "--skip-examiner passed",
                            decisions)

    # Stage: fallacies (reuse logical_fallacies over the patent text).
    if _stage_enabled("fallacies", args, default_on=True):
        _log_stage_decision("fallacies", True,
                            "default-on; logical_fallacies over claims+spec",
                            decisions)
        results.append(_run_skill(
            "logical_fallacies", base / "03_fallacies",
            ["--draft", patent_path] + common_flags, force=args.force,
            stage_id="03-fallacies", run_dir=base,
            resume_from=args.resume_from,
        ))
    else:
        _log_stage_decision("fallacies", False, "--skip-fallacies passed",
                            decisions)

    # Stage: disclosure-audit (opt-in). For patents this surfaces
    # inventorship / assignee / funding-derived government-rights flags.
    if _stage_enabled("disclosure-audit", args, default_on=False):
        _log_stage_decision("disclosure-audit", True,
                            "--with-disclosure-audit", decisions)
        results.append(_run_skill(
            "disclosure_audit", base / "03e_disclosure_audit",
            ["--paper", patent_path] + journal_flags + common_flags,
            force=args.force, stage_id="03e-disclosure-audit", run_dir=base,
            resume_from=args.resume_from,
        ))

    # Stage: cqe (process_summary, always last; audit-mode reads the patent).
    if _stage_enabled("cqe", args, default_on=True):
        cqe_args = ["--run-dir", str(base), "--audit-mode",
                    "--paper", patent_path]
        if args.no_llm_narrative:
            cqe_args.append("--no-llm-narrative")
        _log_stage_decision("cqe", True, "default-on; 6-dim composite",
                            decisions)
        results.append(_run_skill(
            "process_summary", base / "04_summary",
            cqe_args + common_flags, force=args.force,
            stage_id="04-cqe", run_dir=base,
            resume_from=args.resume_from,
        ))
    else:
        _log_stage_decision("cqe", False, "--skip-cqe passed", decisions)

    base.mkdir(parents=True, exist_ok=True)
    telemetry.pipeline_summary(base)
    telemetry.audit_heartbeats(base)
    final_decision = "proceed" if all(r.rc == 0 for r in results) else "fail"
    telemetry.decision_log(base, final_decision)

    chain_config = {
        "pipeline": "patent-audit",
        "llm": args.llm,
        "patent_source": str(args.patent),
        "filing_standard": args.filing_standard,
        "pub_number": patent.pub_number,
        "kind_code": patent.kind_code,
        "is_application": patent.is_application,
        "n_claims": patent.n_claims(),
        "venue": args.journal,
        "topic": topic,
        "stages_default_on": list(PATENT_AUDIT_DEFAULT_ON),
        "stages_optional": list(PATENT_AUDIT_OPTIONAL),
        "stages_ran": [r.stage for r in results if not r.skipped],
        "stages_skipped_by_flag": [
            name for name in PATENT_AUDIT_DEFAULT_ON
            if getattr(args, "skip_" + name.replace("-", "_"), False)
        ],
        "stages_opted_in_by_flag": [
            name for name in PATENT_AUDIT_OPTIONAL
            if getattr(args, "with_" + name.replace("-", "_"), False)
        ],
        "pause_after": getattr(args, "pause_after", None),
        "resume_from": getattr(args, "resume_from", None),
        "decision_log": decisions,
    }
    (base / "_chain_config.json").write_text(
        json.dumps(chain_config, indent=2), encoding="utf-8")
    rc = _emit_pipeline_summary(base, results)
    # Always render the styled PDF report as the final step.
    _build_patent_report_pdf(base)
    return rc


def pipeline_status(args: argparse.Namespace) -> int:
    """Print the current state of a run-dir without doing any work."""
    if not args.outdir.is_dir():
        print(f"status: outdir does not exist: {args.outdir}")
        return 0
    print(f"# Pipeline status — {args.outdir}\n")
    for stage_dir in sorted(args.outdir.iterdir()):
        name = stage_dir.name
        looks_like_stage = (name.startswith("stage_")
                            or (name[:2].isdigit() and "_" in name))
        if not stage_dir.is_dir() or not looks_like_stage:
            continue
        files = [p.name for p in stage_dir.iterdir() if p.is_file()]
        print(f"## {stage_dir.name}")
        print(f"  files: {len(files)}")
        for f in files[:5]:
            print(f"    - {f}")
        if len(files) > 5:
            print(f"    ... ({len(files) - 5} more)")
        print()
    return 0


# =========================================================================
# Pipeline-summary emitter
# =========================================================================

def _emit_pipeline_summary(base: Path,
                           results: list[StageResult]) -> int:
    """Write QN-native subprocess-RC summary to _run_summary.json.

    Distinct from the stage-health-schema pipeline_summary.json (written by
    telemetry.pipeline_summary and aggregates _stage_health.json files —
    that's the canonical stage-health report). This one captures
    skill-runner exit codes, which the stage-health schema doesn't track.
    """
    base.mkdir(parents=True, exist_ok=True)
    summary = {
        "stages": [
            {"stage": r.stage, "skill": r.skill, "rc": r.rc,
             "elapsed_s": round(r.elapsed_s, 2),
             "outdir": str(r.outdir), "skipped": r.skipped,
             "notes": r.notes}
            for r in results
        ],
        "n_stages_run": sum(1 for r in results if not r.skipped),
        "n_stages_skipped": sum(1 for r in results if r.skipped),
        "n_failures": sum(1 for r in results if r.rc != 0),
    }
    (base / "_run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\n=== run summary (subprocess-RC view) ===")
    print(json.dumps(summary, indent=2))
    return 0 if summary["n_failures"] == 0 else 1


# =========================================================================
# CLI
# =========================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pipeline", choices=[
        "full", "mid-entry-stage-2.5", "mid-entry-stage-4",
        "paper-audit", "patent-audit", "status", "list-stages",
    ])
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--topic", default=None)
    ap.add_argument("--paper", default=None, type=Path)
    ap.add_argument("--patent", default=None,
                    help="patent-audit input: Google Patents URL, "
                         "publication number (US10614371B2), or a saved "
                         "patent file")
    ap.add_argument("--art-unit", default=None,
                    help="optional USPTO art-unit / CPC context for the "
                         "patent examiner panel")
    ap.add_argument("--filing-standard", default="uspto",
                    choices=["uspto", "epo", "pct", "multi"],
                    help="patent-audit application-review standard: uspto "
                         "(§112/MPEP), epo (Art. 84/EPC), pct, or multi")
    ap.add_argument("--reviewer-comments", default=None, type=Path)
    ap.add_argument("--hamiltonian", default=None)
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--geometry-sweep", default=None)
    ap.add_argument("--llms", default=None,
                    help="comma list of LLM backends for cross-LLM stage")
    ap.add_argument("--journal", default=None)
    ap.add_argument("--quantum-lib", default=None)
    ap.add_argument("--pareto-archive", default=None,
                    help="Pareto archive JSON for novelty-audit stage")
    ap.add_argument("--bib", default=None,
                    help="BibTeX file for the citation-integrity stage")
    ap.add_argument("--augmented-baselines", default=None,
                    help="Baseline catalog JSON for novelty-audit stage")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-llm-narrative", action="store_true",
                    help="Disable the LLM-narrative pass in process_summary")

    # Per-stage toggles for the paper-audit + patent-audit pipelines.
    # Registered from the deduped union so shared stages (fallacies, cqe)
    # get exactly one flag while patent-specific stages (prior-art,
    # examiner) and paper-specific stages (research, ...) each get theirs.
    _default_on = list(dict.fromkeys(
        PAPER_AUDIT_DEFAULT_ON + PATENT_AUDIT_DEFAULT_ON))
    _optional = list(dict.fromkeys(
        PAPER_AUDIT_OPTIONAL + PATENT_AUDIT_OPTIONAL))
    # Default-on stages (skip with --skip-<name>):
    for name in _default_on:
        ap.add_argument(f"--skip-{name}",
                        dest=f"skip_{name.replace('-', '_')}",
                        action="store_true",
                        help=f"Skip the {name} stage (default-on; "
                             f"toggling off removes it from the chain)")
    # Optional stages (opt-in with --with-<name>):
    for name in _optional:
        ap.add_argument(f"--with-{name}",
                        dest=f"with_{name.replace('-', '_')}",
                        action="store_true",
                        help=f"Enable the {name} stage (off by default; "
                             f"requires the relevant input flag)")

    # Back-compat + asymmetric toggles for the integrity gates.
    ap.add_argument("--with-claims-registry", dest="with_claims_registry",
                    action="store_true",
                    help="DEPRECATED no-op: claims-registry is now a "
                         "default-on integrity gate (disable with "
                         "--skip-claims-registry)")
    ap.add_argument("--skip-citation-integrity",
                    dest="skip_citation_integrity", action="store_true",
                    help="Disable the citation-integrity gate even when "
                         "--bib is provided")

    # Checkpoint controls.
    ap.add_argument("--pause-after", default=None,
                    help="Pause after this stage name; writes a checkpoint")
    ap.add_argument("--resume-from", default=None,
                    help="Resume execution at this stage; earlier stages "
                         "are treated as already-complete")
    ap.add_argument("--hitl-pause-after", default=None,
                    help="Alias for --pause-after. Sets "
                         "QN_HITL_PAUSE_AFTER env so any stage whose "
                         "stage_id contains this substring will checkpoint "
                         "and exit cleanly.")

    # Cross-vendor fork. Runs the same pipeline twice in
    # <outdir>/claude_branch/ + <outdir>/codex_branch/ so backend
    # disagreement is visible. Off by default.
    ap.add_argument("--with-cross-model", action="store_true",
                    help="Fork the chain on claude + codex (two independent "
                         "runs in claude_branch/ and codex_branch/), then "
                         "write _cross_model_index.json pointing at both. "
                         "Cross-model falsifiability fork.")
    ap.add_argument("--with-codex-fallback", action="store_true",
                    help="Re-enable the legacy silent claude->codex fallback. "
                         "Off by default; framework default is strict.")

    # ARC profile bundles. For each ARC stage that has a QN
    # equivalent, expose a matching flag. Stages without a QN
    # equivalent are still parsed (for surface parity) and recorded but
    # are no-ops at runtime (they emit a "stage planned but not run yet"
    # decision_log entry).
    arc_group = ap.add_argument_group(
        "ARC profile bundles",
        "Pre-/post-generation ARC gates. Bundle via --with-arc-pipeline "
        "or pick individual stages. Off by default.")
    arc_group.add_argument("--with-arc-pipeline", action="store_true",
                           help="Bundle all ARC stages below")
    for f, desc in (
        ("--with-arc-problem-tree",
         "Pre-gen: goal.md + problem_tree.md + topic_evaluation.json"),
        ("--with-arc-literature-pipeline",
         "Pre-gen: search → CrossRef candidates → shortlist → paper cards"),
        ("--with-arc-paper-outline",
         "Pre-gen: structured outline.md with per-section word budgets"),
        ("--with-arc-novelty-check",
         "Pre-gen: novelty assessment against literature corpus"),
        ("--with-arc-draft-quality",
         "Post-gen: per-section word-count + status flags"),
        ("--with-arc-iterative-refine",
         "Post-gen: multi-version refinement sandbox"),
        ("--with-arc-citation-integrity",
         "Post-gen: 4-layer citation verification with CrossRef"),
        ("--with-arc-compilation-quality",
         "Post-gen: LaTeX log → compilation_quality.json"),
        ("--with-arc-paper-verification",
         "Post-gen: render-time numeric fabrication audit"),
        ("--with-arc-pdf-review",
         "Post-gen: LLM 9-axis NeurIPS-style PDF scorecard"),
        ("--with-arc-quality-gate",
         "Post-gen: consolidated quality_report.json + fabrication_flags"),
        ("--with-arc-research-decision",
         "Post-gen: PROCEED/REFINE/PIVOT verdict (decision.md)"),
        ("--with-arc-knowledge-archive",
         "Post-gen: deliverables/ bundle + manifest.json + bundle_index"),
    ):
        dest = f[2:].replace("-", "_")
        arc_group.add_argument(f, dest=dest, action="store_true", help=desc)

    args = ap.parse_args()

    # Honor --pause-after / --hitl-pause-after by exporting the env the
    # telemetry pause hook reads (both spellings work; hitl wins).
    pause_target = (getattr(args, "hitl_pause_after", None)
                    or getattr(args, "pause_after", None))
    if pause_target:
        os.environ["QN_HITL_PAUSE_AFTER"] = pause_target

    # --with-codex-fallback opts out of strict mode.
    if getattr(args, "with_codex_fallback", False):
        os.environ["CLAUDE_DISABLE_CODEX_FALLBACK"] = "0"
        os.environ["INVOKE_LLM_NO_FALLBACK"] = "0"

    # ARC alias: --with-arc-novelty-check is the ARC-profile spelling of
    # QN's --with-novelty-audit. Either flag turns
    # the stage on; presence of pareto_archive arms the actual run.
    if getattr(args, "with_arc_novelty_check", False) \
            and not getattr(args, "with_novelty_audit", False):
        args.with_novelty_audit = True
    # --with-arc-pipeline is the bundle flag; on paper-audit it
    # currently only maps onto novelty-check (the QN-applicable ARC
    # subset). Other ARC stages remain documented placeholders.
    if getattr(args, "with_arc_pipeline", False):
        args.with_novelty_audit = True
        # cross-llm wants explicit inputs; the bundle does NOT auto-arm it
        # — but it does turn the option on so the decision_log records why.
        args.with_cross_llm = True

    if args.pipeline == "list-stages":
        return _print_stage_table()

    # Cross-model fork: run twice (claude + codex branches),
    # write index. Only meaningful for orchestrated pipelines.
    if getattr(args, "with_cross_model", False) \
            and args.pipeline in {"paper-audit", "patent-audit", "full",
                                   "mid-entry-stage-2.5",
                                   "mid-entry-stage-4"}:
        return _run_cross_model_fork(args)

    pipeline_map = {
        "full":                pipeline_full,
        "mid-entry-stage-2.5": pipeline_midentry_2_5,
        "mid-entry-stage-4":   pipeline_midentry_4,
        "paper-audit":         pipeline_paper_audit,
        "patent-audit":        pipeline_patent_audit,
        "status":              pipeline_status,
    }
    return pipeline_map[args.pipeline](args)


def _run_cross_model_fork(args: argparse.Namespace) -> int:
    """Fork pipeline on claude + codex, write index.

    Each branch runs in
    its own subdir; the index points at both branches' pipeline_summary
    + chain_config so disagreement is visible at a glance.
    """
    base = args.outdir
    base.mkdir(parents=True, exist_ok=True)
    summary_pairs: list[dict] = []
    rc_max = 0
    for branch_llm, sub in (("claude", "claude_branch"),
                            ("codex", "codex_branch")):
        branch_dir = base / sub
        # Recurse with the branch's --llm and --outdir; suppress further
        # forking to avoid infinite loops.
        branch_args = argparse.Namespace(**vars(args))
        branch_args.outdir = branch_dir
        branch_args.llm = branch_llm
        branch_args.with_cross_model = False
        pipeline_map = {
            "full":                pipeline_full,
            "mid-entry-stage-2.5": pipeline_midentry_2_5,
            "mid-entry-stage-4":   pipeline_midentry_4,
            "paper-audit":         pipeline_paper_audit,
            "patent-audit":        pipeline_patent_audit,
        }
        try:
            rc = pipeline_map[args.pipeline](branch_args)
        except SystemExit:
            # A SystemExit here is the HITL pause firing inside a branch —
            # propagate it; silently continuing to the next branch would
            # defeat the human-in-the-loop checkpoint.
            raise
        rc_max = max(rc_max, rc)
        summary_pairs.append({
            "branch": sub,
            "llm": branch_llm,
            "rc": rc,
            "pipeline_summary": str(branch_dir / "pipeline_summary.json"),
            "chain_config": str(branch_dir / "_chain_config.json"),
        })
    index = {
        "pipeline": args.pipeline,
        "fork": "cross-model",
        "branches": summary_pairs,
        "note": "Re-run with --with-cross-model. Compare branches' "
                "pipeline_summary.json + CQE composite + reviewer "
                "verdicts to see backend disagreement.",
    }
    (base / "_cross_model_index.json").write_text(
        json.dumps(index, indent=2), encoding="utf-8"
    )
    print(f"[cross-model] index: {base/'_cross_model_index.json'}")
    return rc_max


def _print_stage_table() -> int:
    """Print which stages each pipeline runs and their toggle flags.

    Running this command tells you exactly what `--pipeline X`
    will execute.
    """
    table = [
        ("scout", ("literature", "arxiv-corpus", "source-kb",
                   "quote-substantiation", "ideas"),
         ("pdf-kb-only", "no-arxiv-corpus", "no-live-literature", "no-llm")),
        ("paper-audit", PAPER_AUDIT_DEFAULT_ON, PAPER_AUDIT_OPTIONAL),
        ("patent-audit", PATENT_AUDIT_DEFAULT_ON, PATENT_AUDIT_OPTIONAL),
        ("full", ("literature", "discovery", "audit", "draft",
                  "cross-llm", "review", "fallacies", "cqe"), ()),
        ("mid-entry-stage-2.5",
         ("literature-1.5", "audit", "review", "fallacies", "cqe"), ()),
        ("mid-entry-stage-4",
         ("revision", "re-review", "cqe"), ()),
    ]
    print("# QN chain — stage table\n")
    print(f"{'pipeline':<24}  {'default-on stages':<60}  optional")
    print("-" * 110)
    for pname, default_on, optional in table:
        on = ", ".join(default_on)
        opt = ", ".join(optional) if optional else "-"
        print(f"{pname:<24}  {on:<60}  {opt}")
    print()
    print("Toggle defaults via per-stage flags:")
    print("  --skip-<stage>     turn off a default-on stage")
    print("  --with-<stage>     turn on an opt-in stage")
    print("  --pause-after S    write checkpoint after stage S")
    print("  --resume-from S    treat earlier stages as complete")
    print("  --force            re-run completed stages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
