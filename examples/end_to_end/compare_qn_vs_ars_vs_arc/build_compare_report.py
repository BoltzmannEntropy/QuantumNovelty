"""Compare QN paper-audit vs ARS academic-paper-reviewer on the same paper.

Produces COMPARE_REPORT.tex with:
  1. Side-by-side pipeline architecture table (QN stages | ARS agents)
  2. Token + cost ledger (both frameworks, same backend)
  3. Stage-by-stage embedded prose (pandoc-converted markdown)
  4. Coverage matrix — which framework caught which finding
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

# QN stages (paper-audit pipeline)
QN_STAGES = [
    ("01_research_review", "research_quality_review.md",
     "Deep-research review",
     "Audit-and-falsify checklist — QN-specific."),
    ("02_reviewer_panel", "review_panel.md",
     "Reviewer panel — 5 voices",
     "EIC + R1 (Physics) + R2 (Novelty) + R3 (Evidence) + Devil's Advocate, "
     "rolled into one stage."),
    ("03_fallacies", "fallacy_report.md",
     "Logical-fallacy report",
     "11 quantum-CS-specific + standard. QN-specific stage."),
    ("04_summary", "process_summary.md",
     "Stage-6 CQE narrative",
     "6-dim Collaboration Quality Evaluation. QN-specific."),
]

# ARS stages (academic-paper-reviewer skill, 7-agent orchestration)
ARS_STAGES = [
    ("00_reviewer_config.md", "Phase 0: Field analyst",
     "Identifies the paper's field, dynamically configures 5 reviewer personas."),
    ("01_eic_review_card.md", "Phase 1a: EIC",
     "Editor-in-Chief — journal fit, originality, overall quality."),
    ("02_methodology_review_card.md", "Phase 1b: Methodology reviewer",
     "Peer Reviewer 1 — research design, statistical validity, reproducibility."),
    ("03_domain_review_card.md", "Phase 1c: Domain reviewer",
     "Peer Reviewer 2 — literature coverage, theoretical framework, contribution."),
    ("04_perspective_review_card.md", "Phase 1d: Perspective reviewer",
     "Peer Reviewer 3 — cross-disciplinary connections, practical impact."),
    ("05_devils_advocate_review_card.md", "Phase 1e: Devil's Advocate",
     "Core argument challenges, logical fallacy detection, counter-arguments."),
    ("06_editorial_decision_letter.md", "Phase 2: Editorial synthesizer",
     "Aggregates all reviews → Editorial Decision + Revision Roadmap."),
]

# ARC stages (peer_review + quality_gate from the 23-stage full pipeline)
ARC_STAGES = [
    ("01_peer_review.md", "Stage 1: Peer review",
     "Simulates 2+ reviewer perspectives (A, B), checks "
     "methodology-evidence consistency, flags fabrication. "
     "Markdown output."),
    ("02_quality_gate.json", "Stage 2: Quality gate",
     "Final JSON verdict — score_1_to_10, strengths, weaknesses, "
     "required_actions, verdict. Threshold-based PROCEED/REVISE."),
]


def _read_json(p: Path) -> dict:
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


# Markdown -> LaTeX conversion is shared with the two-paper builder
# (single source of truth for JSON-stripping, scaffold-heading cleanup,
# and content-proportional table widths).
_TP = Path(__file__).resolve().parent.parent / "two_paper_novelty"
_spec = importlib.util.spec_from_file_location(
    "build_report", _TP / "build_report.py")
_br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_br)


def md_to_latex(md_path: Path) -> str:
    if not md_path.is_file():
        return r"\emph{(stage output missing on disk)}"
    return _br.md_to_latex_fragment(md_path)


def _collect_model_provenance(*frameworks: dict) -> list[tuple[str, str, str]]:
    """(framework, stage label, model id) for every stage that ran."""
    rows = []
    names = ["QN", "ARS", "ARC"]
    for name, fw in zip(names, frameworks):
        for s in fw["stages"]:
            if not s.get("missing") and s.get("model_id"):
                rows.append((name, s["label"], s["model_id"]))
    return rows


def _claude_cli_version() -> str:
    try:
        r = subprocess.run(["claude", "--version"],
                           capture_output=True, text=True, timeout=20)
        return r.stdout.strip() or r.stderr.strip() or "unknown"
    except Exception:
        return "unknown"


def latex_escape(s: str) -> str:
    # Backslash first via a sentinel — replacing it inline would let the
    # braces of \textbackslash{} be re-escaped by the later passes.
    s = s.replace("\\", "\x00")
    s = (s.replace("&", r"\&").replace("%", r"\%")
          .replace("$", r"\$").replace("#", r"\#")
          .replace("_", r"\_").replace("{", r"\{").replace("}", r"\}")
          .replace("~", r"\textasciitilde{}")
          .replace("^", r"\textasciicircum{}"))
    return s.replace("\x00", r"\textbackslash{}")

def fmt_int(n) -> str:
    if n is None:
        return "-"
    try:
        return f"{int(float(n)):,}"
    except (TypeError, ValueError):
        return str(n)


def fmt_cost(c) -> str:
    if c is None:
        return "(est.)"
    if c == 0:
        return r"\$0.00"
    return f"\\${c:.4f}"


def collect_qn(qn_dir: Path) -> dict:
    out: dict = {"stages": [], "totals": {
        "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
        "elapsed_s": 0.0,
    }}
    for sd, primary, label, desc in QN_STAGES:
        d = qn_dir / sd
        marker = _read_json(d / "_backend_used.json")
        rec = {"stage_dir": sd, "label": label, "desc": desc,
               "primary_md": d / primary,
               "missing": not (d / primary).is_file()}
        if marker:
            u = marker.get("usage", {})
            rec.update({
                "model_id": marker.get("model_id", ""),
                "backend": marker.get("backend_actually_used", ""),
                "elapsed_s": marker.get("elapsed_s", 0.0),
                "input_tokens": u.get("input_tokens", 0),
                "output_tokens": u.get("output_tokens", 0),
                "cost_usd": u.get("total_cost_usd"),
                "estimated": u.get("tokens_estimated", False),
            })
            out["totals"]["input_tokens"] += rec.get("input_tokens") or 0
            out["totals"]["output_tokens"] += rec.get("output_tokens") or 0
            out["totals"]["elapsed_s"] += rec.get("elapsed_s") or 0
            if isinstance(rec.get("cost_usd"), (int, float)):
                out["totals"]["cost_usd"] += rec["cost_usd"]
        out["stages"].append(rec)
    out["cqe"] = _read_json(qn_dir / "04_summary" / "cqe_scores.json")
    out["fallacies"] = _read_json(qn_dir / "03_fallacies" / "fallacy_findings.json")
    out["pipeline_summary"] = _read_json(qn_dir / "pipeline_summary.json")
    return out


def collect_arc(arc_dir: Path) -> dict:
    out: dict = {"stages": [], "totals": {
        "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
        "elapsed_s": 0.0,
    }}
    for primary, label, desc in ARC_STAGES:
        md_path = arc_dir / primary
        marker_path = arc_dir / (primary.rsplit(".", 1)[0]
                                  + "_backend_used.json")
        marker = _read_json(marker_path)
        rec = {"primary_md": md_path, "label": label, "desc": desc,
               "missing": not md_path.is_file(),
               "is_json": primary.endswith(".json")}
        if marker:
            u = marker.get("usage", {})
            rec.update({
                "model_id": marker.get("model_id", ""),
                "backend": marker.get("backend_actually_used", ""),
                "elapsed_s": marker.get("elapsed_s", 0.0),
                "input_tokens": u.get("input_tokens", 0),
                "output_tokens": u.get("output_tokens", 0),
                "cost_usd": u.get("total_cost_usd"),
                "estimated": u.get("tokens_estimated", False),
            })
            out["totals"]["input_tokens"] += rec.get("input_tokens") or 0
            out["totals"]["output_tokens"] += rec.get("output_tokens") or 0
            out["totals"]["elapsed_s"] += rec.get("elapsed_s") or 0
            if isinstance(rec.get("cost_usd"), (int, float)):
                out["totals"]["cost_usd"] += rec["cost_usd"]
        out["stages"].append(rec)
    out["quality_gate"] = _read_json(arc_dir / "02_quality_gate.json")
    out["run_summary"] = _read_json(arc_dir / "arc_run_summary.json")
    return out


def collect_ars(ars_dir: Path) -> dict:
    out: dict = {"stages": [], "totals": {
        "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
        "elapsed_s": 0.0,
    }}
    for primary, label, desc in ARS_STAGES:
        md_path = ars_dir / primary
        marker_path = ars_dir / primary.replace(".md", "_backend_used.json")
        marker = _read_json(marker_path)
        rec = {"primary_md": md_path, "label": label, "desc": desc,
               "missing": not md_path.is_file()}
        if marker:
            u = marker.get("usage", {})
            rec.update({
                "model_id": marker.get("model_id", ""),
                "backend": marker.get("backend_actually_used", ""),
                "elapsed_s": marker.get("elapsed_s", 0.0),
                "input_tokens": u.get("input_tokens", 0),
                "output_tokens": u.get("output_tokens", 0),
                "cost_usd": u.get("total_cost_usd"),
                "estimated": u.get("tokens_estimated", False),
            })
            out["totals"]["input_tokens"] += rec.get("input_tokens") or 0
            out["totals"]["output_tokens"] += rec.get("output_tokens") or 0
            out["totals"]["elapsed_s"] += rec.get("elapsed_s") or 0
            if isinstance(rec.get("cost_usd"), (int, float)):
                out["totals"]["cost_usd"] += rec["cost_usd"]
        out["stages"].append(rec)
    out["run_summary"] = _read_json(ars_dir / "ars_run_summary.json")
    return out


def render(args, qn: dict, ars: dict, arc: dict) -> str:
    L: list[str] = []

    def W(s: str = ""):
        L.append(s)

    W(r"\documentclass[10pt,letterpaper]{article}")
    W(r"\usepackage[margin=0.9in]{geometry}")
    W(r"\usepackage{booktabs}")
    W(r"\usepackage{xcolor}")
    W(r"\usepackage{titlesec}")
    W(r"\usepackage{hyperref}")
    W(r"\usepackage{titling}")
    W(r"\usepackage{fancyhdr}")
    W(r"\usepackage{longtable}")
    W(r"\usepackage{calc}")
    W(r"\usepackage{array}")
    W(r"\usepackage[T1]{fontenc}")
    W(r"\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}")
    W(r"\providecommand{\passthrough}[1]{#1}")
    W(r"\providecommand{\pandocbounded}[1]{#1}")
    W(r"\providecommand{\real}[1]{#1}")
    W(r"\usepackage{amssymb}")    # \square, \checkmark, etc.
    W(r"\usepackage{amsmath}")
    W(r"\definecolor{qnblue}{HTML}{1F3A8A}")
    W(r"\definecolor{arsorange}{HTML}{C2410C}")
    W(r"\definecolor{arcgreen}{HTML}{15803D}")
    W(r"\definecolor{muted}{HTML}{4A4D57}")
    W(r"\hypersetup{colorlinks=true, urlcolor=qnblue, linkcolor=qnblue}")
    W(r"\titleformat{\section}{\Large\bfseries\color{qnblue}}{\thesection}{0.6em}{}")
    W(r"\titleformat{\subsection}{\large\bfseries}{\thesubsection}{0.5em}{}")
    W(r"\titleformat{\subsubsection}{\normalsize\bfseries}{\thesubsubsection}{0.5em}{}")
    W(r"\setlength{\droptitle}{-3em}")
    W(r"\pagestyle{fancy}")
    W(r"\fancyhf{}")
    W(r"\rhead{\footnotesize\color{muted}QN vs ARS vs ARC --- Head-to-head}")
    W(r"\lhead{\footnotesize\color{muted}\thepage}")
    W(r"\renewcommand{\headrulewidth}{0pt}")

    W(r"\title{\textbf{\Large QN vs ARS vs ARC}\\")
    W(r"\large Three frameworks. One paper. One backend. "
      + latex_escape(args.paper_title) + r"}")
    W(r"\author{Same paper. Same backend. Three pipelines.}")
    W(rf"\date{{{datetime.date.today().strftime('%B %Y')}}}")
    W(r"\begin{document}")
    W(r"\maketitle")

    # ---------- provenance header ----------
    build_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M %Z").strip()
    cli_ver = _claude_cli_version()
    model_rows = _collect_model_provenance(qn, ars, arc)
    distinct_models = sorted({m for _, _, m in model_rows})
    W(r"\begin{center}")
    W(r"\renewcommand{\arraystretch}{1.25}")
    W(r"\begin{tabular}{ll}")
    W(r"\toprule")
    W(r"\textbf{Project} & QuantumNovelty (QN) --- audit-and-falsify "
      r"framework for quantum-computing research \\")
    W(r"\textbf{Repository} & "
      r"\url{https://github.com/boltzmannentropy/QuantumNovelty} \\")
    W(r"\textbf{Author} & Shlomo Kashani "
      r"(\href{https://qneura.ai/apps.html}{QNeura.ai}) \\")
    W(rf"\textbf{{Paper under review}} & "
      rf"\href{{https://arxiv.org/abs/{args.paper_arxiv}}}"
      rf"{{arXiv:{args.paper_arxiv}}} --- {latex_escape(args.paper_venue)} \\")
    W(r"\textbf{LLM backend} & Claude Code CLI "
      rf"(\texttt{{{latex_escape(cli_ver)}}}) \\")
    if distinct_models:
        W(rf"\textbf{{Model snapshots used}} & "
          + r" \newline ".join(
              rf"\texttt{{{latex_escape(m)}}}" for m in distinct_models)
          + r" \\")
    W(rf"\textbf{{Report generated}} & {latex_escape(build_date)} by "
      r"\texttt{build\_compare\_report.py} \\")
    W(r"\textbf{Run directory} & "
      r"\texttt{examples/end\_to\_end/compare\_qn\_vs\_ars\_vs\_arc/\_run/} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W(r"\end{center}")
    W()

    W(r"\section*{Setup}")
    W(rf"\noindent The paper --- \emph{{{latex_escape(args.paper_title)}}} "
      r"--- was run through three review frameworks on the same backend "
      r"and the same extracted text, so output differences reflect each "
      r"framework's design rather than LLM variance. The per-stage model "
      r"snapshot, exact token counts, and USD cost (from the Claude CLI's "
      r"JSON envelope) appear in the ledger below.\\[0.5em]")
    W(r"\noindent \textbf{\color{qnblue}QN pipeline:} "
      r"\texttt{chain/run.sh --pipeline paper-audit} "
      r"--- 4 stages (research / reviewer / fallacies / cqe).\\")
    W(r"\noindent \textbf{\color{arsorange}ARS pipeline:} "
      r"\texttt{academic-paper-reviewer} (full mode) "
      r"--- 7-agent orchestration (Phase 0 field-analyst, Phase 1a--e "
      r"five reviewers, Phase 2 editorial synthesizer).\\")
    W(r"\noindent \textbf{\color{arcgreen}ARC pipeline:} "
      r"\texttt{peer\_review} + \texttt{quality\_gate} stages "
      r"--- 2-stage review subset extracted from ARC's 23-stage full "
      r"\texttt{python -m researchclaw run} pipeline.")
    W()

    # ---------- architecture map ----------
    W(r"\section{Pipeline architecture map}")
    W(r"How the two frameworks line up. Both run on the same paper text "
      r"and the same backend; differences in output reflect each "
      r"framework's design choices.")
    W()
    W(r"\begin{tabular}{p{0.30\textwidth}p{0.30\textwidth}p{0.30\textwidth}}")
    W(r"\toprule")
    W(r"\textbf{\color{qnblue}QN \texttt{paper-audit}} & "
      r"\textbf{\color{arsorange}ARS \texttt{academic-paper-reviewer}} & "
      r"\textbf{\color{arcgreen}ARC \texttt{peer\_review + quality\_gate}} \\")
    W(r"\midrule")
    rows = [
        (r"\textbf{Stage 1:} \texttt{deep\_research --mode review} "
         r"\newline audit-and-falsify checklist scored against paper text "
         r"(15 items: novelty rigour, baseline coverage, ablations, "
         r"Wilson CIs, etc.) "
         r"\newline \emph{Output:} \texttt{research\_quality\_review.md}",
         r"\textbf{Phase 0:} \texttt{field\_analyst\_agent} "
         r"\newline reads the paper, identifies field, configures 5 "
         r"reviewer personas with named expertise. "
         r"\newline \emph{Output:} reviewer configuration cards (x5)",
         r"\emph{(no dedicated equivalent --- topic context is "
         r"injected via prompt placeholder in both ARC stages.)}"),
        (r"\textbf{Stage 2 (multi-voice):} \texttt{quantum\_reviewer --mode full} "
         r"\newline single LLM call yielding 5-voice panel: "
         r"EIC + R1 (Physics) + R2 (Novelty) + R3 (Evidence) + "
         r"Devil's Advocate + reconciliation. "
         r"\newline \emph{Output:} \texttt{review\_panel.md} (one file)",
         r"\textbf{Phase 1 (5 separate calls):} "
         r"\newline \texttt{eic\_agent} "
         r"\newline \texttt{methodology\_reviewer\_agent} "
         r"\newline \texttt{domain\_reviewer\_agent} "
         r"\newline \texttt{perspective\_reviewer\_agent} "
         r"\newline \texttt{devils\_advocate\_reviewer\_agent} "
         r"\newline \emph{Output:} 5 separate review cards (one per agent)",
         r"\textbf{Stage 1:} \texttt{peer\_review} "
         r"\newline single LLM call yielding 2 reviewer perspectives "
         r"(Reviewer A, Reviewer B) with strengths / weaknesses / "
         r"actionable revisions + methodology-evidence consistency check + "
         r"fabrication-flag scan. "
         r"\newline \emph{Output:} \texttt{01\_peer\_review.md}"),
        (r"\textbf{Stage 3:} \texttt{logical\_fallacies} "
         r"\newline 11 quantum-CS-specific fallacies "
         r"(cherry-picked-baseline, ad-hoc-precision-floor, "
         r"simulator-laundering, pareto-cherry-picked-axes, "
         r"cross-llm-theatre, ...) + standard taxonomy. "
         r"\newline \emph{Output:} \texttt{fallacy\_report.md} + "
         r"\texttt{fallacy\_findings.json}",
         r"\emph{(no dedicated equivalent --- fallacy work is folded "
         r"into the Devil's Advocate agent in Phase 1)}",
         r"\emph{(no dedicated equivalent --- fabrication detection is "
         r"folded into the peer\_review prompt's methodology-evidence "
         r"consistency check)}"),
        (r"\textbf{Stage 4:} \texttt{process\_summary} (Stage-6 CQE) "
         r"\newline 6-dim Collaboration Quality Evaluation, geometric "
         r"mean composite. Mechanical rubric scoring. "
         r"\newline \emph{Output:} \texttt{cqe\_scores.json} + "
         r"\texttt{process\_summary.md}",
         r"\textbf{Phase 2:} \texttt{editorial\_synthesizer\_agent} "
         r"\newline aggregates all 5 review cards, identifies "
         r"consensus + disagreements, makes editorial decision. "
         r"\newline \emph{Output:} editorial decision letter + "
         r"revision roadmap",
         r"\textbf{Stage 2:} \texttt{quality\_gate} "
         r"\newline single LLM call producing JSON verdict: "
         r"\texttt{\{score\_1\_to\_10, verdict, strengths, weaknesses, "
         r"required\_actions\}}. Numeric threshold gate (default 7.0) "
         r"decides PROCEED vs REVISE. "
         r"\newline \emph{Output:} \texttt{02\_quality\_gate.json}"),
    ]
    for q, a, c in rows:
        W(rf"{q} & {a} & {c} \\")
        W(r"\midrule")
    W(r"\bottomrule")
    W(r"\end{tabular}")

    # ---------- token + cost ledger ----------
    W(r"\section{Token + cost ledger --- all three frameworks, same backend}")
    W(r"\begin{tabular}{lllrrrr}")
    W(r"\toprule")
    W(r"Framework & Stage & Model & Input tk & Output tk & Cost (\$) & Elapsed (s) \\")
    W(r"\midrule")
    for fw_color, fw_name, fw in [("qnblue", "QN", qn),
                                   ("arsorange", "ARS", ars),
                                   ("arcgreen", "ARC", arc)]:
        for s in fw["stages"]:
            if s.get("missing"):
                W(rf"\color{{{fw_color}}}{fw_name} & "
                  rf"{latex_escape(s.get('label','?'))} & -- & -- & -- & -- & -- \\")
                continue
            est = r"$\dagger$" if s.get("estimated") else ""
            mid = (s.get("model_id") or "")[:30]
            W(rf"\color{{{fw_color}}}{fw_name} & "
              rf"{latex_escape(s.get('label','?'))} & "
              rf"{latex_escape(mid)} & "
              rf"{fmt_int(s.get('input_tokens'))}{est} & "
              rf"{fmt_int(s.get('output_tokens'))}{est} & "
              rf"{fmt_cost(s.get('cost_usd'))} & "
              rf"{(s.get('elapsed_s') or 0):.1f} \\")
        t = fw["totals"]
        W(rf"\color{{{fw_color}}}\textbf{{{fw_name} total}} & & & "
          rf"\textbf{{{fmt_int(t['input_tokens'])}}} & "
          rf"\textbf{{{fmt_int(t['output_tokens'])}}} & "
          rf"\textbf{{{fmt_cost(t['cost_usd'])}}} & "
          rf"\textbf{{{t['elapsed_s']:.1f}}} \\")
        W(r"\midrule")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W()
    any_estimated = any(
        s.get("estimated") for fw in (qn, ars, arc) for s in fw["stages"])
    if any_estimated:
        W(r"$\dagger$ estimated token counts (char/4); rows without the "
          r"dagger carry exact counts and USD from the Claude CLI's "
          r"JSON envelope.")
    else:
        W(r"All rows carry exact token counts and per-call USD from the "
          r"Claude Code CLI's JSON envelope --- nothing is estimated.")

    # ---------- QN full prose ----------
    W(r"\clearpage")
    W(r"\section{\color{qnblue}QN paper-audit --- full per-stage prose}")
    W(r"\noindent Every subsection below is QN output "
      r"(\texttt{\_run/qn/}); the per-stage model snapshot is shown "
      r"under each heading.")
    for s in qn["stages"]:
        W(rf"\subsection{{\color{{qnblue}}QN --- {latex_escape(s['label'])}}}")
        if s.get("model_id"):
            W(rf"\noindent\textcolor{{muted}}{{\small Model: "
              rf"\texttt{{{latex_escape(s['model_id'])}}} "
              rf"\textperiodcentered\ {latex_escape(s['desc'])}}}")
        else:
            W(rf"\noindent\textcolor{{muted}}{{\small {latex_escape(s['desc'])}}}")
        W()
        if s["primary_md"].is_file():
            W(md_to_latex(s["primary_md"]))
        else:
            W(r"\emph{(stage output missing on disk)}")
        W()

    # ---------- ARS full prose ----------
    W(r"\clearpage")
    W(r"\section{\color{arsorange}ARS academic-paper-reviewer --- "
      r"full per-agent prose}")
    W(r"\noindent Every subsection below is ARS output "
      r"(\texttt{\_run/ars/}). Each agent is one independent LLM call; "
      r"the editorial synthesizer (Phase 2) sees the 5 reviewer cards "
      r"in its context, but the 5 reviewers are blind to each other.")
    for s in ars["stages"]:
        W(rf"\subsection{{\color{{arsorange}}ARS --- {latex_escape(s['label'])}}}")
        if s.get("model_id"):
            W(rf"\noindent\textcolor{{muted}}{{\small Model: "
              rf"\texttt{{{latex_escape(s['model_id'])}}} "
              rf"\textperiodcentered\ {latex_escape(s['desc'])}}}")
        else:
            W(rf"\noindent\textcolor{{muted}}{{\small {latex_escape(s['desc'])}}}")
        W()
        if s["primary_md"].is_file():
            W(md_to_latex(s["primary_md"]))
        else:
            W(r"\emph{(agent output missing on disk)}")
        W()

    # ---------- ARC full prose ----------
    W(r"\clearpage")
    W(r"\section{\color{arcgreen}ARC \texttt{peer\_review} + "
      r"\texttt{quality\_gate} --- full per-stage output}")
    W(r"\noindent Every subsection below is ARC output "
      r"(\texttt{\_run/arc/}). ARC is a 23-stage autonomous research "
      r"pipeline (topic $\to$ empirical paper); for this head-to-head "
      r"we route only the two paper-review stages so the comparison is "
      r"review-vs-review.")
    for s in arc["stages"]:
        W(rf"\subsection{{\color{{arcgreen}}ARC --- {latex_escape(s['label'])}}}")
        if s.get("model_id"):
            W(rf"\noindent\textcolor{{muted}}{{\small Model: "
              rf"\texttt{{{latex_escape(s['model_id'])}}} "
              rf"\textperiodcentered\ {latex_escape(s['desc'])}}}")
        else:
            W(rf"\noindent\textcolor{{muted}}{{\small {latex_escape(s['desc'])}}}")
        W()
        if s["primary_md"].is_file():
            if s.get("is_json"):
                # Render the quality-gate verdict as a decision letter,
                # not raw JSON — JSON has no place in a typeset report.
                gate = _read_json(s["primary_md"])
                if gate:
                    score = gate.get("score_1_to_10")
                    verdict = gate.get("verdict", "")
                    W(rf"The quality gate scores the manuscript "
                      rf"\textbf{{{score}/10}} against a threshold of 7.0. "
                      rf"{latex_escape(str(verdict))}")
                    W()
                    strengths = gate.get("strengths") or []
                    if strengths:
                        W(r"\paragraph{Strengths noted.}")
                        W(latex_escape(" ".join(str(x).rstrip(".") + "."
                                                 for x in strengths)))
                        W()
                    weaknesses = gate.get("weaknesses") or []
                    if weaknesses:
                        W(r"\paragraph{Weaknesses noted.}")
                        W(latex_escape(" ".join(str(x).rstrip(".") + "."
                                                 for x in weaknesses)))
                        W()
                    actions = gate.get("required_actions") or []
                    if actions:
                        W(r"\paragraph{Required actions.}")
                        W(r"\begin{enumerate}")
                        for a in actions:
                            W(rf"\item {latex_escape(str(a))}")
                        W(r"\end{enumerate}")
                else:
                    W(r"\emph{(quality-gate output unparseable)}")
            else:
                W(md_to_latex(s["primary_md"]))
        else:
            W(r"\emph{(stage output missing on disk)}")
        W()

    # ---------- coverage matrix ----------
    W(r"\clearpage")
    W(r"\section{Coverage matrix --- what each framework caught}")
    W(r"All three pipelines run on the same paper text and same backend. "
      r"The 5-voice peer review shape is shared across QN and ARS; ARC's "
      r"review is shorter (2 stages: peer\_review + quality\_gate) "
      r"because ARC's design centre is generation, not review. QN adds "
      r"quantum-CS-specific layers (audit-and-falsify checklist, 11 "
      r"quantum-CS fallacies, Stage-6 CQE) that neither ARS nor ARC "
      r"covers; ARS adds dedicated field-analyst + editorial-synthesizer "
      r"agents; ARC adds a structured-JSON quality verdict with a "
      r"numeric threshold gate.")
    W()
    W(r"\begin{tabular}{p{0.36\textwidth}ccc}")
    W(r"\toprule")
    W(r"Concern & \color{qnblue}QN & \color{arsorange}ARS & "
      r"\color{arcgreen}ARC \\")
    W(r"\midrule")
    coverage = [
        ("Field / discipline identification before review",
         "implicit (skill prompt)",
         "explicit (Phase 0 agent)",
         "implicit (topic prompt)"),
        ("EIC / editor verdict",
         r"\checkmark (in review\_panel.md)",
         r"\checkmark (eic\_review\_card.md)",
         "partial (quality\_gate verdict)"),
        ("Methodology / statistics review",
         r"\checkmark (R1 voice)",
         r"\checkmark (methodology\_reviewer)",
         r"\checkmark (Reviewer A/B)"),
        ("Domain / literature review",
         r"\checkmark (R2 voice)",
         r"\checkmark (domain\_reviewer)",
         "partial (in Reviewer A/B)"),
        ("Cross-disciplinary / practical impact review",
         r"\checkmark (R3 voice)",
         r"\checkmark (perspective\_reviewer)",
         r"--"),
        ("Devil's Advocate / counter-argument review",
         r"\checkmark (Devil's Advocate voice)",
         r"\checkmark (devils\_advocate\_reviewer)",
         r"--"),
        ("Methodology-evidence consistency check",
         "implicit (in panel prose)",
         "implicit (in methodology reviewer)",
         r"\checkmark (ARC-specific; trial count + "
         r"stat-test fabrication scan)"),
        ("Editorial decision letter / revision roadmap",
         r"partial (panel verdict)",
         r"\checkmark (Phase 2 synthesizer)",
         r"partial (required\_actions list)"),
        ("Numeric quality score with threshold gate",
         r"6-dim CQE composite (\checkmark)",
         r"--",
         r"\checkmark (score\_1\_to\_10 + threshold)"),
        ("Audit-and-falsify checklist (deep-research)",
         r"\checkmark (QN-specific)", r"--", r"--"),
        ("Quantum-CS-specific fallacy taxonomy",
         r"\checkmark (QN-specific; 11 fallacies)", r"--", r"--"),
        ("Stage-6 6-dim CQE composite",
         r"\checkmark (QN-specific)", r"--", r"--"),
        ("Token + USD cost ledger per stage",
         r"\checkmark (\_backend\_used.json)",
         r"\checkmark (this driver; same shape)",
         r"\checkmark (this driver; same shape)"),
        ("Structured stage telemetry (pipeline\_summary, etc.)",
         r"\checkmark (chain emits ARC-style shapes)", r"--", r"--"),
    ]
    for row in coverage:
        W(rf"{latex_escape(row[0])} & {row[1]} & {row[2]} & {row[3]} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")

    W(r"\vfill")
    W(r"\begin{center}\small\textcolor{muted}{Made with "
      r"$\heartsuit$ for creators everywhere. "
      r"\href{https://qneura.ai/apps.html}{QNeura.ai} "
      r"\textperiodcentered\ Shlomo Kashani}\end{center}")
    W(r"\end{document}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--paper-tag", required=True)
    ap.add_argument("--paper-title", required=True)
    ap.add_argument("--paper-arxiv", required=True)
    ap.add_argument("--paper-venue", required=True)
    ap.add_argument("--backend", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    qn = collect_qn(args.run_dir / "qn")
    ars = collect_ars(args.run_dir / "ars")
    arc = collect_arc(args.run_dir / "arc")
    args.out.write_text(render(args, qn, ars, arc), encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")

    # Three-way JSON summary
    qg = arc.get("quality_gate") or {}
    summary = {
        "paper": args.paper_tag, "arxiv": args.paper_arxiv,
        "venue": args.paper_venue, "backend": args.backend,
        "qn": {
            "stages": len(qn["stages"]),
            "totals": qn["totals"],
            "cqe_composite": (qn.get("cqe") or {}).get("composite"),
            "fallacy_count": len((qn.get("fallacies") or {}).get("findings") or []),
        },
        "ars": {
            "stages": len(ars["stages"]),
            "totals": ars["totals"],
        },
        "arc": {
            "stages": len(arc["stages"]),
            "totals": arc["totals"],
            "quality_gate_score": qg.get("score_1_to_10"),
            "quality_gate_verdict": qg.get("verdict"),
        },
    }
    (args.out.with_suffix(".json")).write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
