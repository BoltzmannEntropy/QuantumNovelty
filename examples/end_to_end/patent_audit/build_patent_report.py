"""Build the patent-audit pipeline report PDF — the patent analogue of
two_paper_novelty/build_report.py, in the same LaTeX template style.

Reads ONE patent-audit run directory (the `--outdir` of
`chain/run.sh --pipeline patent-audit`) and renders a single styled PDF:

  - Bibliographic header (pub number, kind code, application-vs-granted,
    inventor, assignee, dates, claim count) from `_chain_config.json`.
  - Office Action summary table from `02_examiner_panel/_office_action.json`
    (disposition + claims rejected per § 101/102/103/112 + allowed claims).
  - Per-stage prose: prior-art review, the USPTO examiner Office Action,
    the logical-fallacy report, and the Stage-6 CQE narrative.
  - Token + USD + elapsed ledger from each stage's `_backend_used.json`.

The pure LaTeX/markdown helpers (latex_escape, md_to_latex_fragment,
provenance, token formatting) are imported from the sibling paper report
builder so the two reports share one template and one escaping contract.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

# Reuse the paper report builder's pure helpers (same template + escaping).
_PAPER_BUILDER = (Path(__file__).resolve().parents[1]
                  / "two_paper_novelty")
sys.path.insert(0, str(_PAPER_BUILDER))
from build_report import (                       # noqa: E402
    latex_escape, md_to_latex_fragment, _read_json, _read_json_array,
    _claude_cli_version, fmt_int, fmt_cost,
)

# Stage dir, primary markdown, section label, one-line description.
STAGES = [
    ("01_prior_art", "research_quality_review.md", "Prior-art review",
     "Deep-research surface of anticipating (§ 102) and rendering-obvious "
     "(§ 103) references for the claim set, scored against the patent text."),
    ("02_examiner_panel", "office_action.md", "USPTO examiner panel (Office Action)",
     "Six voices: Primary Examiner (§ 101 Alice/Mayo), § 102 anticipation, "
     "§ 103 obviousness (KSR), § 112 enablement / written-description / "
     "definiteness, a Quantum Technical Specialist (operability), and the "
     "Supervisory Patent Examiner who issues the disposition. Claims are "
     "examined individually."),
    ("03_fallacies", "fallacy_report.md", "Logical-fallacy report",
     "Standard fallacies plus the 11 quantum-CS-specific checks applied to "
     "the patent's claims and specification."),
    ("04_summary", "process_summary.md", "Stage-6 CQE narrative",
     "6-dim Collaboration Quality Evaluation with geometric-mean composite."),
]

# Descriptive tail only; the "\S~NNN" prefix is emitted as raw LaTeX in the
# table so the section sign renders correctly (a literal "§" pushed through
# latex_escape mis-maps under T1 fontenc).
_STATUTE_LABEL = {
    "101": "(eligibility / Alice-Mayo)",
    "102": "(anticipation / novelty)",
    "103": "(obviousness / KSR)",
    "112": "(enablement / definiteness)",
}


def _fmt_claims(claims: list) -> str:
    """[1,2,3,5,6,7] -> '1-3, 5-7' for compact display."""
    if not claims:
        return "none"
    cs = sorted(set(int(c) for c in claims))
    runs, start, prev = [], cs[0], cs[0]
    for c in cs[1:]:
        if c == prev + 1:
            prev = c
            continue
        runs.append((start, prev)); start = prev = c
    runs.append((start, prev))
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)


def collect(run_dir: Path) -> dict:
    out: dict = {"stages": [], "totals": {
        "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
        "elapsed_s": 0.0}}
    for stage_dir, primary, label, desc in STAGES:
        sd = run_dir / stage_dir
        marker = _read_json(sd / "_backend_used.json")
        rec: dict = {
            "stage": stage_dir, "label": label, "desc": desc,
            "primary_md": sd / primary,
            "missing": not (sd / primary).is_file(),
        }
        if marker:
            usage = marker.get("usage", {})
            rec.update({
                "model_id": marker.get("model_id", ""),
                "backend": marker.get("backend_actually_used", ""),
                "elapsed_s": marker.get("elapsed_s", 0.0),
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "cost_usd": usage.get("total_cost_usd"),
                "estimated": usage.get("tokens_estimated", False),
            })
            out["totals"]["input_tokens"] += rec.get("input_tokens") or 0
            out["totals"]["output_tokens"] += rec.get("output_tokens") or 0
            out["totals"]["elapsed_s"] += rec.get("elapsed_s") or 0
            if isinstance(rec.get("cost_usd"), (int, float)):
                out["totals"]["cost_usd"] += rec["cost_usd"]
        out["stages"].append(rec)
    out["office_action"] = _read_json(
        run_dir / "02_examiner_panel" / "_office_action.json")
    out["chain_config"] = _read_json(run_dir / "_chain_config.json")
    out["pipeline_summary"] = _read_json(run_dir / "pipeline_summary.json")
    out["decision_history"] = _read_json_array(
        run_dir / "decision_history.json")
    out["cqe"] = _read_json(run_dir / "04_summary" / "cqe_scores.json")
    return out


def render(data: dict) -> str:
    L: list[str] = []

    def W(s: str = ""):
        L.append(s)

    cfg = data.get("chain_config") or {}
    oa = data.get("office_action") or {}
    pub = cfg.get("pub_number", "(unknown)")
    kind = cfg.get("kind_code", "")
    is_app = cfg.get("is_application", True)
    status = ("Published application (under examination)"
              if is_app else "Granted patent (post-grant review)")
    title = cfg.get("topic") or pub
    n_claims = cfg.get("n_claims", oa.get("n_claims_examined", "-"))
    source = cfg.get("patent_source", "")

    # ---------- preamble (same template as the paper report) ----------
    W(r"\documentclass[10pt,letterpaper]{article}")
    W(r"\usepackage[margin=0.9in]{geometry}")
    for pkg in ("booktabs", "xcolor", "titlesec", "hyperref", "titling",
                "fancyhdr", "longtable", "calc", "array", "amssymb",
                "amsmath", "xurl"):
        W(rf"\usepackage{{{pkg}}}")
    W(r"\usepackage[T1]{fontenc}")
    W(r"\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}")
    W(r"\providecommand{\passthrough}[1]{#1}")
    W(r"\providecommand{\pandocbounded}[1]{#1}")
    W(r"\providecommand{\real}[1]{#1}")
    W(r"\definecolor{accent}{HTML}{1F3A8A}")
    W(r"\definecolor{muted}{HTML}{4A4D57}")
    W(r"\hypersetup{colorlinks=true, urlcolor=accent, linkcolor=accent}")
    W(r"\titleformat{\section}{\Large\bfseries\color{accent}}{\thesection}{0.6em}{}")
    W(r"\titleformat{\subsection}{\large\bfseries}{\thesubsection}{0.5em}{}")
    W(r"\titleformat{\subsubsection}{\normalsize\bfseries}{\thesubsubsection}{0.5em}{}")
    W(r"\setlength{\droptitle}{-3em}")
    # Running header: the patent under examination, on every page.
    _short_title = str(title)
    if len(_short_title) > 52:
        _short_title = _short_title[:49].rstrip() + "..."
    _hdr = rf"{latex_escape(pub)} --- {latex_escape(_short_title)}"
    W(r"\pagestyle{fancy}")
    W(r"\fancyhf{}")
    W(rf"\rhead{{\footnotesize\color{{muted}}{_hdr}}}")
    W(r"\lhead{\footnotesize\color{muted}\thepage}")
    W(r"\renewcommand{\headrulewidth}{0pt}")

    W(r"\title{\textbf{\Large QuantumNovelty Patent Examination Report}\\[0.4em]")
    W(rf"\large A simulated USPTO Office Action for a quantum patent}}")
    W(r"\author{Generated by QuantumNovelty}")
    W(rf"\date{{{datetime.date.today().strftime('%B %Y')}}}")
    W(r"\begin{document}")
    W(r"\maketitle")

    # ---------- provenance header ----------
    build_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M").strip()
    cli_ver = _claude_cli_version()
    models = sorted({s.get("model_id") for s in data["stages"]
                     if s.get("model_id")})
    W(r"\begin{center}")
    W(r"\renewcommand{\arraystretch}{1.25}")
    W(r"\begin{tabular}{l>{\raggedright\arraybackslash}p{0.62\textwidth}}")
    W(r"\toprule")
    W(r"\textbf{Project} & QuantumNovelty (QN) --- audit-and-falsify "
      r"framework for quantum-computing research \& patents \\")
    W(r"\textbf{Repository} & "
      r"\url{https://github.com/boltzmannentropy/QuantumNovelty} \\")
    W(r"\textbf{Author} & Shlomo Kashani "
      r"(\href{https://qneura.ai/apps.html}{QNeura.ai}) \\")
    W(r"\textbf{LLM backend} & Claude Code CLI "
      rf"(\texttt{{{latex_escape(cli_ver)}}}) \\")
    if models:
        W(r"\textbf{Model snapshots used} & "
          + r" \newline ".join(rf"\texttt{{{latex_escape(m)}}}"
                               for m in models) + r" \\")
    W(rf"\textbf{{Report generated}} & {latex_escape(build_date)} by "
      r"\texttt{build\_patent\_report.py} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W(r"\end{center}")
    W()

    # ---------- scope ----------
    W(r"\section*{Scope}")
    W(r"This report is produced by the \textbf{QuantumNovelty} "
      r"\texttt{patent-audit} pipeline running against a single "
      r"quantum-computing patent. The pipeline composes a prior-art "
      r"deep-research surface, a six-voice simulated USPTO examiner panel "
      r"(the \texttt{patent\_reviewer} skill), a logical-fallacy scan, and "
      r"Stage-6 CQE scoring. The examiner panel reasons under 35 U.S.C. "
      r"\S\S~101/102/103/112 and the MPEP, runs claim-compliance and "
      r"full-application review under the selected filing standard, and "
      r"issues an \textbf{Office Action}; it is a simulation for research "
      r"and drafting support, "
      r"\emph{not} legal advice and not an official USPTO action.")

    # ---------- patent under examination ----------
    W(r"\section{Patent under examination}")
    W(r"\renewcommand{\arraystretch}{1.2}")
    W(r"\begin{tabular}{l>{\raggedright\arraybackslash}p{0.70\textwidth}}")
    W(r"\toprule")
    W(rf"\textbf{{Publication number}} & \texttt{{{latex_escape(pub)}}} \\")
    W(rf"\textbf{{Kind code}} & \texttt{{{latex_escape(kind)}}} "
      rf"--- {latex_escape(status)} \\")
    W(rf"\textbf{{Title}} & {latex_escape(str(title))} \\")
    W(rf"\textbf{{Claims examined}} & {latex_escape(str(n_claims))} \\")
    W(rf"\textbf{{Filing standard}} & "
      rf"\texttt{{{latex_escape(str(cfg.get('filing_standard', 'uspto')))}}} \\")
    if source:
        if source.startswith("http"):
            # Canonical patent URL (drop ?inventor=…&sort=… query noise);
            # xurl lets the remaining path wrap rather than overflow.
            canon = source.split("?", 1)[0]
            W(rf"\textbf{{Source}} & \url{{{canon}}} \\")
        else:
            W(rf"\textbf{{Source}} & {latex_escape(source)} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W()

    # ---------- Office Action summary ----------
    W(r"\section{Office Action summary}")
    if oa:
        dispo = (oa.get("disposition") or "-").replace("-", " ").title()
        n_rej = oa.get("n_claims_rejected", "-")
        n_ex = oa.get("n_claims_examined", "-")
        W(rf"\noindent\textbf{{Disposition:}} "
          rf"\textcolor{{accent}}{{\textbf{{{latex_escape(dispo)}}}}} "
          rf"\quad\textbf{{Claims rejected:}} {latex_escape(str(n_rej))} / "
          rf"{latex_escape(str(n_ex))}")
        W()
        W(r"\renewcommand{\arraystretch}{1.2}")
        W(r"\begin{tabular}{ll}")
        W(r"\toprule")
        W(r"\textbf{Statute} & \textbf{Claims rejected} \\")
        W(r"\midrule")
        by_statute = oa.get("rejections_by_statute") or {}
        for st in ("101", "102", "103", "112"):
            claims = by_statute.get(st) or []
            W(rf"\S~{st} {latex_escape(_STATUTE_LABEL[st])} "
              rf"& {latex_escape(_fmt_claims(claims))} \\")
        W(r"\midrule")
        W(rf"\textbf{{Allowed (no rejection)}} & "
          rf"{latex_escape(_fmt_claims(oa.get('allowed_claims') or []))} \\")
        allowable = oa.get("allowable_subject_matter") or []
        if allowable:
            W(rf"\textbf{{Allowable subject matter}} & "
              rf"{latex_escape(_fmt_claims(allowable))} \\")
        W(r"\bottomrule")
        W(r"\end{tabular}")
        W()
        W(r"\noindent\textcolor{muted}{\small This table is a deterministic, "
          r"zero-LLM-cost parse of the examiner panel "
          r"(\texttt{\_office\_action.json}): the disposition comes from the "
          r"Supervisory Patent Examiner's synthesis and the per-statute claim "
          r"lists from the examiners' reconciled rejection block. An "
          r"\texttt{allowance} disposition with any rejected claim is "
          r"auto-downgraded.}")
    else:
        W(r"\emph{(no \texttt{\_office\_action.json} found)}")
    W()

    # ---------- workflow chain configuration ----------
    W(r"\section{Workflow chain configuration}")
    W(r"The patent is routed through "
      r"\texttt{chain/run.sh --pipeline patent-audit}. Default-on stages: "
      r"prior-art, examiner, fallacies, cqe. The resolved configuration is "
      r"captured in \texttt{\_chain\_config.json} alongside the outputs.")
    W()
    W(r"\subsection*{Equivalent CLI}")
    W(r"\begin{verbatim}")
    W("bash QuantumNovelty/chain/run.sh \\")
    W("  --pipeline patent-audit \\")
    W("  --patent <URL | PUBLICATION_NUMBER | FILE> \\")
    W("  --art-unit '<USPTO art unit / CPC context>' \\")
    W("  --llm <backend>          # claude is the default \\")
    W("  --outdir <RUN_DIR>")
    W(r"\end{verbatim}")
    W()

    # ---------- token + cost ledger ----------
    W(r"\section{Token + cost ledger}")
    W(r"Every LLM call writes \texttt{\_backend\_used.json} with the model "
      r"snapshot ID, token counts, USD cost, and elapsed seconds.")
    W()
    W(r"\begin{tabular}{lrrrr}")
    W(r"\toprule")
    W(r"Stage & Input tk & Output tk & Cost (\$) & Elapsed (s) \\")
    W(r"\midrule")
    for s in data["stages"]:
        if s.get("missing") and not s.get("model_id"):
            W(rf"{latex_escape(s['label'])} & - & - & - & - \\")
            continue
        est = r"$\dagger$" if s.get("estimated") else ""
        W(rf"{latex_escape(s['label'])} "
          rf"& {fmt_int(s.get('input_tokens'))}{est} "
          rf"& {fmt_int(s.get('output_tokens'))}{est} "
          rf"& {fmt_cost(s.get('cost_usd'))} "
          rf"& {(s.get('elapsed_s') or 0):.1f} \\")
    t = data["totals"]
    W(r"\midrule")
    W(rf"\textbf{{Total}} & \textbf{{{fmt_int(t['input_tokens'])}}} "
      rf"& \textbf{{{fmt_int(t['output_tokens'])}}} "
      rf"& \textbf{{{fmt_cost(t['cost_usd'])}}} "
      rf"& \textbf{{{t['elapsed_s']:.1f}}} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W()

    # ---------- per-stage deep dives (full prose) ----------
    W(r"\clearpage")
    W(r"\section{Stage outputs (full prose)}")
    W(r"The four stage outputs below are the complete substantive text the "
      r"chain wrote --- not condensed.")
    for s in data["stages"]:
        W(rf"\subsection{{{latex_escape(s['label'])}}}")
        if s.get("model_id"):
            W(rf"\noindent\textcolor{{muted}}{{\small Backend: "
              rf"{latex_escape(s.get('backend', '-'))} "
              rf"({latex_escape(s.get('model_id') or 'snapshot not surfaced')}) "
              rf"\textperiodcentered\ {fmt_int(s.get('input_tokens'))} in / "
              rf"{fmt_int(s.get('output_tokens'))} out tokens "
              rf"\textperiodcentered\ {(s.get('elapsed_s') or 0):.1f}\,s}}")
            W()
        W(rf"\noindent\textcolor{{muted}}{{\small {latex_escape(s['desc'])}}}")
        W()
        md_path = s.get("primary_md")
        if md_path and md_path.is_file():
            W(md_to_latex_fragment(md_path))
        else:
            W(r"\emph{(stage output missing on disk)}")
        W()

    # ---------- reproducibility + footer ----------
    W(r"\clearpage")
    W(r"\section{Reproducing this report}")
    W(r"\begin{verbatim}")
    W("# 1. Run the patent-audit pipeline")
    W("bash chain/run.sh --pipeline patent-audit \\")
    W(f"  --patent {(source or '<URL>')[:60]} \\")
    W("  --llm claude --outdir runs/<run>")
    W("# 2. Build this PDF (lualatex — UTF-8 native, for Greek/math glyphs)")
    W("python3 examples/end_to_end/patent_audit/build_patent_report.py \\")
    W("  --run-dir runs/<run> --out PATENT_REPORT.tex")
    W("lualatex PATENT_REPORT.tex && lualatex PATENT_REPORT.tex")
    W(r"\end{verbatim}")
    W(r"\vfill")
    W(r"\begin{center}\small\textcolor{muted}{Simulated examination for "
      r"research support --- not legal advice. Made with $\heartsuit$. "
      r"\href{https://qneura.ai/apps.html}{QNeura.ai} \textperiodcentered\ "
      r"Shlomo Kashani}\end{center}")
    W(r"\end{document}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, type=Path,
                    help="a patent-audit run directory (chain --outdir)")
    ap.add_argument("--out", required=True, type=Path,
                    help="output .tex path (PDF compiled alongside)")
    args = ap.parse_args()
    if not args.run_dir.is_dir():
        print(f"ERROR: run-dir not found: {args.run_dir}", file=sys.stderr)
        return 2
    data = collect(args.run_dir)
    args.out.write_text(render(data), encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")
    # Machine-readable side-car.
    side = {
        "office_action": data.get("office_action"),
        "chain_config": data.get("chain_config"),
        "totals": data["totals"],
        "stages": [{k: (str(v) if isinstance(v, Path) else v)
                    for k, v in s.items() if k != "primary_md"}
                   for s in data["stages"]],
    }
    args.out.with_suffix(".json").write_text(
        json.dumps(side, indent=2, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
