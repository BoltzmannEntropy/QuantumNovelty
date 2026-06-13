"""Build the two-paper-novelty pipeline report PDF.

This is the long-form report — every stage's substantive prose is included,
not just a tally table. Reads each stage's primary markdown output, runs
it through `pandoc` to convert to a LaTeX fragment, and embeds the fragment
under the right section.

Sections per paper:
  1. Deep-research review        (audit-and-falsify checklist)
  2. Reviewer panel              (EIC + R1 + R2 + R3 + Devil's Advocate, vote table)
  3. Logical-fallacy report      (quantum-CS taxonomy + standard fallacies)
  4. 6-dim CQE                   (mechanical scoring breakdown)
  5. Per-stage backend marker    (model, tokens, USD, elapsed)

Plus the comparison sections (token ledger, CQE composites, fallacy counts).
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

STAGES = [
    ("01_research_review",  "research_quality_review.md", "Deep-research review",
        "Audit-and-falsify checklist scored against the paper text. Each item is "
        "PASS / PARTIAL / FAIL / NOT-APPLICABLE with one-line evidence."),
    ("02_reviewer_panel",   "review_panel.md",             "Reviewer panel — 5 voices",
        "Editor-in-Chief + Reviewer 1 (Physics) + Reviewer 2 (Novelty) + "
        "Reviewer 3 (Evidence) + Devil's Advocate. Each voice produces a verdict; "
        "the EIC reconciles."),
    ("03_fallacies",        "fallacy_report.md",            "Logical-fallacy report",
        "Standard fallacies plus 11 quantum-CS-specific (cherry-picked-baseline, "
        "ad-hoc-precision-floor, simulator-laundering, pareto-cherry-picked-axes, "
        "cross-llm-theatre, …). Severity threshold: medium."),
    # Opt-in verification-layer stages. collect_paper() includes a stage
    # only when its primary output exists, so papers audited before these
    # stages shipped render unchanged.
    ("02d_argument_structure", "argument_structure.md",
        "Argument-structure audit",
        "Premises -> intermediate claims -> conclusion map with unsupported "
        "leaps; claim-proof gap; Claim/Mechanism/Evidence proportionality; "
        "narrative-debt register; sequencing diagnosis."),
    ("02e_requirements_judge", "requirements_report.md",
        "Requirements judge — claim vs evidence",
        "LLM audit of whether the paper's central claims are licensed by its "
        "own evidence; per-claim met/partial/unmet/unevaluable verdict plus "
        "an allowed/forbidden-claims manifest."),
    ("03c_claims_registry", "verification_report.md",
        "Numeric-claim registry (deterministic)",
        "Registry of every numeric in the Results/Experiments/Tables "
        "sections gating the Abstract/Intro/Discussion. Zero LLM cost."),
    ("03e_disclosure_audit", "disclosure_audit.md",
        "Disclosure audit",
        "16-point checklist: funding, competing interests, author "
        "contributions, data + code availability, ethics, preprint "
        "status, AI-use disclosures, rights and warranties."),
    ("03f_revision_plan", "anchored_revision_plan.md",
        "Anchored revision plan",
        "Every revision item anchored to a paragraph ID with verbatim "
        "quoted problem prose, per-judge evidence, and a concrete "
        "proposed edit with effort estimate."),
    ("00_evidence_ledger", "ledger.md",
        "Evidence ledger (deterministic)",
        "Pre-registers the paper's permitted facts — cite keys, distinct "
        "numerics, headings, normalized text — as ground truth for the "
        "reviewer-hallucination audit. Zero LLM cost."),
    ("98_evidence_ledger_audit", "ledger_audit.md",
        "Reviewer-hallucination audit (deterministic)",
        "Scans every review report for claims, quotes, or numbers attributed "
        "to the paper that the ledger cannot anchor. Informational; zero LLM "
        "cost."),
    ("04_summary",          "process_summary.md",          "Stage-6 CQE narrative",
        "6-dim Collaboration Quality Evaluation with geometric-mean composite."),
]


def _read_json(p: Path) -> dict:
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _read_json_array(p: Path) -> list:
    if p.is_file():
        try:
            v = json.loads(p.read_text(encoding="utf-8"))
            return v if isinstance(v, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _strip_json_sections(md: str) -> str:
    """Remove machine-readable JSON from prose destined for the PDF.

    Fence-aware: heading detection ignores lines inside fenced code
    blocks (a bash comment in a fence is not a heading), and the json
    fences are matched as whole blocks anchored at line starts so an
    inline mention of a json fence doesn't eat half the document. The
    JSON stays on disk (fallacy_findings.json is extracted from it by
    the skill) — it just has no place in a typeset report.
    """
    lines = md.splitlines()
    out: list[str] = []
    skip_until_level = None
    in_fence = False
    i = 0
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        if stripped.startswith("```"):
            if not in_fence and stripped.lower().startswith("```json"):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    i += 1
                i += 1          # consume the closing fence
                continue
            in_fence = not in_fence
            if skip_until_level is None:
                out.append(ln)
            i += 1
            continue
        if not in_fence:
            m = re.match(r"^(#{1,6})\s+(.*)$", ln)
            if m:
                level = len(m.group(1))
                title = m.group(2).lower()
                if skip_until_level is not None and level <= skip_until_level:
                    skip_until_level = None
                if skip_until_level is None and "machine-readable" in title:
                    skip_until_level = level
                    i += 1
                    continue
        if skip_until_level is None:
            out.append(ln)
        i += 1
    return "\n".join(out)

def _fit_tables(md: str) -> str:
    """Give every markdown pipe table content-proportional column widths.

    Pandoc derives its longtable column proportions from the dash counts
    in the separator row. LLM-emitted tables always use the minimal
    ``|---|---|---|`` separator, so a table with one wide Evidence column
    and two narrow ones gets equal thirds and the wide cell wraps one
    word per line. Rewriting the separator with dashes proportional to
    the actual max cell width per column (clamped so narrow columns keep
    a readable minimum) makes pandoc emit properly weighted ``p{...}``
    columns. Tables inside fenced code blocks are left untouched.
    """
    def _split_row(row: str) -> list[str]:
        cells = re.split(r"(?<!\\)\|", row.strip().strip("|"))
        return [c.strip() for c in cells]

    lines = md.splitlines()
    out: list[str] = []
    in_fence = False
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            out.append(ln)
            i += 1
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if (not in_fence and ln.strip().startswith("|")
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", nxt)):
            header = _split_row(ln)
            ncol = len(header)
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(_split_row(lines[j]))
                j += 1
            # max content width per column, header included
            widths = []
            for c in range(ncol):
                cells = [header[c]] + [r[c] for r in rows if c < len(r)]
                widths.append(max((len(x) for x in cells), default=3))
            # clamp: short columns keep a floor, one huge column can't
            # starve the rest past readability
            weights = [min(max(w, 8), 60) for w in widths]
            total = sum(weights) or 1
            dashes = [max(3, round(w / total * 100)) for w in weights]
            sep = "|" + "|".join(":" + "-" * d for d in dashes) + "|"
            out.append(ln)
            out.append(sep)
            out.extend(lines[i + 2:j])
            i = j
            continue
        out.append(ln)
        i += 1
    return "\n".join(out)


def _strip_scaffold_headings(md: str) -> str:
    """Drop LLM prompt-scaffold headings that mean nothing in a report.

    The fallacy skill asks the model for "Section 1: Markdown Findings"
    + "Section 2: Machine-readable JSON"; the JSON section is removed by
    _strip_json_sections, but the "Section 1: Markdown Findings" heading
    would survive into the PDF as a nonsensical title. Headings whose
    text is pure scaffolding are dropped (content kept); "Section N:"
    prefixes on real headings are trimmed.
    """
    out: list[str] = []
    in_fence = False
    for ln in md.splitlines():
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            out.append(ln)
            continue
        m = None if in_fence else re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            title = re.sub(r"^section\s*\d+\s*[:.—-]\s*", "",
                           m.group(2).strip(), flags=re.I)
            if re.fullmatch(r"(markdown\s+)?findings", title, flags=re.I):
                continue                    # pure scaffold — drop heading
            if title != m.group(2).strip():
                ln = f"{m.group(1)} {title}"   # trimmed "Section N:" prefix
        out.append(ln)
    return "\n".join(out)

def _claude_cli_version() -> str:
    try:
        r = subprocess.run(["claude", "--version"],
                           capture_output=True, text=True, timeout=20)
        return r.stdout.strip() or r.stderr.strip() or "unknown"
    except Exception:
        return "unknown"


def md_to_latex_fragment(md_path: Path) -> str:
    """Convert a markdown file to a LaTeX fragment via pandoc."""
    if not md_path.is_file():
        return r"\emph{(stage output missing)}"
    md = md_path.read_text(encoding="utf-8", errors="replace")
    md = _strip_json_sections(md)
    md = _strip_scaffold_headings(md)
    md = _fit_tables(md)
    try:
        r = subprocess.run(
            ["pandoc", "--from=markdown", "--to=latex",
             "--wrap=preserve", "--no-highlight"],
            input=md, capture_output=True, text=True, timeout=60,
            check=True,
        )
        frag = r.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError) as e:
        return rf"\emph{{(pandoc conversion failed: {latex_escape(str(e)[:120])})}}"
    # Pandoc emits \section / \subsection — we DEMOTE them so they nest
    # under our own \subsection within the per-paper \section.
    frag = re.sub(r"\\subsubsection\{", r"\\paragraph{", frag)
    frag = re.sub(r"\\subsection\{", r"\\subsubsection{", frag)
    frag = re.sub(r"\\section\{", r"\\paragraph{", frag)
    # \hypertarget is a real hyperref command; leave it intact so braces
    # stay balanced. The preamble defines a stub if hyperref isn't loaded.
    return frag


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

def collect_paper(paper_dir: Path) -> dict:
    out: dict = {"stages": [], "totals": {
        "input_tokens": 0, "output_tokens": 0,
        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
        "cost_usd": 0.0, "elapsed_s": 0.0,
    }}
    optional = {"02d_argument_structure", "02e_requirements_judge",
                "03c_claims_registry",
                "03e_disclosure_audit", "03f_revision_plan",
                "00_evidence_ledger", "98_evidence_ledger_audit"}
    for stage_dir, primary, label, desc in STAGES:
        sd = paper_dir / stage_dir
        if stage_dir in optional and not (sd / primary).is_file():
            continue          # opt-in stage that didn't run — no row
        marker = _read_json(sd / "_backend_used.json")
        rec: dict = {
            "stage": stage_dir,
            "label": label,
            "desc": desc,
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
                "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
                "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
                "cost_usd": usage.get("total_cost_usd"),
                "estimated": usage.get("tokens_estimated", False),
            })
            out["totals"]["input_tokens"] += rec.get("input_tokens") or 0
            out["totals"]["output_tokens"] += rec.get("output_tokens") or 0
            out["totals"]["cache_read_input_tokens"] += rec.get(
                "cache_read_input_tokens") or 0
            out["totals"]["cache_creation_input_tokens"] += rec.get(
                "cache_creation_input_tokens") or 0
            out["totals"]["elapsed_s"] += rec.get("elapsed_s") or 0
            if isinstance(rec.get("cost_usd"), (int, float)):
                out["totals"]["cost_usd"] += rec["cost_usd"]
        out["stages"].append(rec)
    out["cqe"] = _read_json(paper_dir / "04_summary" / "cqe_scores.json")
    out["fallacies"] = _read_json(paper_dir / "03_fallacies" / "fallacy_findings.json")
    out["chain_config"] = _read_json(paper_dir / "_chain_config.json")
    # Structured stage telemetry (ARC's stage-health pattern).
    out["pipeline_summary"] = _read_json(paper_dir / "pipeline_summary.json")
    out["decision_history"] = _read_json_array(paper_dir / "decision_history.json")
    heartbeat_audit_path = paper_dir / "HEARTBEAT_AUDIT.md"
    out["heartbeat_audit"] = (heartbeat_audit_path.read_text(encoding="utf-8")
                              if heartbeat_audit_path.is_file() else "")
    panel_path = paper_dir / "02_reviewer_panel" / "review_panel.md"
    out["reviewer_verdict"] = _extract_verdict(
        panel_path.read_text(encoding="utf-8", errors="replace")
        if panel_path.is_file() else ""
    )
    return out


def _extract_verdict(panel_text: str) -> str:
    if not panel_text:
        return "(no panel output)"
    m = re.search(
        r"(?:\*\*Final verdict[:\s]+\*\*|Final verdict[:\s]+)([^\n]+)",
        panel_text, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().rstrip(".").strip("*")[:300]
    m = re.search(r"Recommendation[:\s]+([^\n]+)",
                  panel_text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip(".").strip("*")[:200]
    return "(verdict not extractable)"


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


def render(args, paper_a: dict, paper_b: dict) -> str:
    L: list[str] = []

    def W(s: str = ""):
        L.append(s)

    # ---------- preamble ----------
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
    # Pandoc helper macros — pandoc's LaTeX writer assumes a preamble that
    # provides these. Without them, every converted table errors with
    # "Undefined control sequence" on \real / \tightlist / \passthrough.
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
    W(r"\pagestyle{fancy}")
    W(r"\fancyhf{}")
    W(r"\rhead{\footnotesize\color{muted}QuantumNovelty Pipeline Report}")
    W(r"\lhead{\footnotesize\color{muted}\thepage}")
    W(r"\renewcommand{\headrulewidth}{0pt}")

    W(r"\title{\textbf{\Large QuantumNovelty Pipeline Report}\\[0.4em]")
    W(r"\large Two recent quantum-computing papers, analyzed end-to-end}")
    W(r"\author{Generated by QuantumNovelty}")
    W(rf"\date{{{datetime.date.today().strftime('%B %Y')}}}")
    W(r"\begin{document}")
    W(r"\maketitle")

    # ---------- provenance header ----------
    build_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M").strip()
    cli_ver = _claude_cli_version()
    models = sorted({s.get("model_id") for s in
                     paper_a["stages"] + paper_b["stages"]
                     if s.get("model_id")})
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
    W(r"\textbf{LLM backend} & Claude Code CLI "
      rf"(\texttt{{{latex_escape(cli_ver)}}}) \\")
    if models:
        W(r"\textbf{Model snapshots used} & "
          + r" \newline ".join(
              rf"\texttt{{{latex_escape(m)}}}" for m in models)
          + r" \\")
    W(rf"\textbf{{Report generated}} & {latex_escape(build_date)} by "
      r"\texttt{build\_report.py} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W(r"\end{center}")
    W()

    # ---------- scope ----------
    W(r"\section*{Scope}")
    W(r"This report is produced by the \textbf{QuantumNovelty} framework "
      r"running against two published quantum-computing papers. "
      r"QuantumNovelty is a peer of AutoResearchClaw (ARC) and "
      r"academic-research-skills (ARS); it composes audit-and-falsify "
      r"skills, deep-research, quantum-reviewer, logical-fallacies, and "
      r"Stage-6 process-summary CQE scoring into a reusable pipeline. "
      r"The four per-paper stages (deep-research review, reviewer panel, "
      r"logical-fallacy report, CQE) below are the full substantive "
      r"outputs --- not condensed; this is what the chain wrote.")

    # ---------- papers under analysis ----------
    W(r"\section{Papers under analysis}")
    W(r"\begin{tabular}{lll}")
    W(r"\toprule")
    W(r"Tag & arXiv & Venue \\")
    W(r"\midrule")
    W(rf"\texttt{{{latex_escape(args.paper_a)}}} & "
      rf"\href{{https://arxiv.org/abs/{args.paper_a_arxiv}}}"
      rf"{{{args.paper_a_arxiv}}} & {latex_escape(args.paper_a_venue)} \\")
    W(rf"\texttt{{{latex_escape(args.paper_b)}}} & "
      rf"\href{{https://arxiv.org/abs/{args.paper_b_arxiv}}}"
      rf"{{{args.paper_b_arxiv}}} & {latex_escape(args.paper_b_venue)} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W()
    W(rf"\noindent \textbf{{Paper A:}} \emph{{{latex_escape(args.paper_a_title)}}}")
    W()
    W(rf"\noindent \textbf{{Paper B:}} \emph{{{latex_escape(args.paper_b_title)}}}")

    # ---------- workflow chain configuration ----------
    W(r"\section{Workflow chain configuration}")
    W(r"Both papers are routed through the same QuantumNovelty chain runner: "
      r"\texttt{chain/run.sh --pipeline paper-audit}. The preset names "
      r"four default-on stages (research, reviewer, fallacies, cqe) and "
      r"two opt-in extras (novelty-audit, cross-llm). Stage toggles use "
      r"the per-stage \texttt{--skip-<stage>} / \texttt{--with-<stage>} "
      r"surface; the resolved configuration for this run is captured in "
      r"\texttt{\_chain\_config.json} alongside each paper's outputs.")
    W()
    W(r"\subsection*{Equivalent CLI (per paper)}")
    W(r"\begin{verbatim}")
    W("bash QuantumNovelty/chain/run.sh \\")
    W("  --pipeline paper-audit \\")
    W(f"  --llm <backend>           # claude is the default \\")
    W(f"  --paper <PAPER.txt>       # arXiv text, extracted via pdftotext \\")
    W(f"  --journal <venue>         # passed to skill prompts as context \\")
    W(f"  --topic '<paper title>'   # grounds deep_research --mode review \\")
    W(f"  --outdir <RUN_DIR>/reports/<tag>")
    W(r"")
    W(r"# Optional toggles (none used in this run; defaults shown):")
    W(r"#   --skip-research          drop deep_research --mode review")
    W(r"#   --skip-reviewer          drop 5-voice quantum_reviewer panel")
    W(r"#   --skip-fallacies         drop logical_fallacies")
    W(r"#   --skip-cqe               drop process_summary Stage-6 CQE")
    W(r"#   --with-novelty-audit     add novelty_audit (needs --pareto-archive)")
    W(r"#   --with-cross-llm         add cross_llm_prediction (needs --hamiltonian")
    W(r"#                                                    --geometry-sweep --llms)")
    W(r"#   --pause-after STAGE      checkpoint + exit after STAGE")
    W(r"#   --resume-from STAGE      treat earlier stages as complete")
    W(r"#   --list-stages            print the stage table for every pipeline")
    W(r"\end{verbatim}")
    W()
    W(r"\subsection*{Resolved stage table}")
    W(r"\begin{tabular}{lll}")
    W(r"\toprule")
    W(rf"Stage & Paper A (\\texttt{{{latex_escape(args.paper_a)}}}) & "
      rf"Paper B (\\texttt{{{latex_escape(args.paper_b)}}}) \\\\")
    W(r"\midrule")
    expected_stages = ["research", "reviewer", "fallacies", "cqe"]
    cca = (paper_a.get("chain_config") or {}).get("stages_ran") or []
    ccb = (paper_b.get("chain_config") or {}).get("stages_ran") or []
    # The pipeline records stages_ran by the skill name; map to friendly tag.
    skill_to_tag = {
        "deep_research": "research", "quantum_reviewer": "reviewer",
        "logical_fallacies": "fallacies", "process_summary": "cqe",
        "novelty_audit": "novelty-audit",
        "cross_llm_prediction": "cross-llm",
    }
    cca_tags = {skill_to_tag.get(s, s) for s in cca}
    ccb_tags = {skill_to_tag.get(s, s) for s in ccb}
    for tag in expected_stages:
        a_state = r"\textbf{on}" if tag in cca_tags else "off (skipped)"
        b_state = r"\textbf{on}" if tag in ccb_tags else "off (skipped)"
        # If chain config isn't present (e.g. legacy bash-only run), infer
        # from whether the stage's marker exists.
        if not cca:
            a_state = "on (inferred from artefacts)"
        if not ccb:
            b_state = "on (inferred from artefacts)"
        W(rf"{latex_escape(tag)} & {a_state} & {b_state} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W()

    # ---------- structured telemetry ----------
    W(r"\section{Structured stage telemetry}")
    W(r"The chain runner implements AutoResearchClaw's stage-health "
      r"telemetry pattern (\texttt{chain/common/stage\_telemetry.sh} and "
      r"\texttt{heartbeat.sh}). Each stage "
      r"writes \texttt{\_stage\_health.json} (status, duration, "
      r"artifact-count); the chain end aggregates them into "
      r"\texttt{pipeline\_summary.json} and "
      r"\texttt{HEARTBEAT\_AUDIT.md}. A separate \texttt{decision\_history.json} "
      r"logs every proceed/refine/fail/pause decision.")
    W()
    for (paper_tag, data) in [(args.paper_a, paper_a),
                              (args.paper_b, paper_b)]:
        ps = data.get("pipeline_summary") or {}
        if not ps:
            continue
        W(rf"\subsection*{{{latex_escape(paper_tag)} — pipeline\_summary.json}}")
        W(r"\begin{tabular}{lr}")
        W(r"\toprule")
        for k in ("run_id", "stages_executed", "stages_done",
                  "stages_paused", "stages_blocked", "stages_failed",
                  "degraded", "final_status"):
            v = ps.get(k)
            v_str = str(v) if v is not None else "-"
            W(rf"{latex_escape(k)} & {latex_escape(v_str)} \\")
        cm = ps.get("content_metrics") or {}
        if cm.get("cqe_composite") is not None:
            W(rf"content.cqe\_composite & {cm['cqe_composite']}/100 \\")
        if cm.get("fallacy_count") is not None:
            W(rf"content.fallacy\_count & {cm['fallacy_count']} \\")
        W(r"\bottomrule")
        W(r"\end{tabular}")
        W()
        per_stage = ps.get("per_stage") or []
        if per_stage:
            W(rf"\subsubsection*{{{latex_escape(paper_tag)} per-stage health}}")
            W(r"\begin{tabular}{llrrl}")
            W(r"\toprule")
            W(r"stage\_id & stage\_dir & duration\_s & artifacts & status \\")
            W(r"\midrule")
            for s in per_stage:
                W(rf"{latex_escape(str(s.get('stage_id','')))} "
                  rf"& {latex_escape(str(s.get('stage_dir','')))} "
                  rf"& {s.get('duration_sec') or 0} "
                  rf"& {s.get('artifacts_count') or 0} "
                  rf"& {latex_escape(str(s.get('status','')))} \\")
            W(r"\bottomrule")
            W(r"\end{tabular}")
            W()
        dh = data.get("decision_history") or []
        if dh:
            W(rf"\subsubsection*{{{latex_escape(paper_tag)} decision\_history.json}}")
            W(r"\begin{tabular}{lll}")
            W(r"\toprule")
            W(r"decision & target & timestamp \\")
            W(r"\midrule")
            for d in dh[-8:]:  # last 8 to fit on the page
                W(rf"{latex_escape(str(d.get('decision','')))} "
                  rf"& {latex_escape(str(d.get('rollback_target') or '-'))} "
                  rf"& {latex_escape(str(d.get('timestamp',''))[:19])} \\")
            W(r"\bottomrule")
            W(r"\end{tabular}")
            W()

    # ---------- token + cost ledger ----------
    W(r"\section{Token + cost ledger}")
    W(r"Every LLM call writes \texttt{\_backend\_used.json} with the "
      r"model snapshot ID, input + output token counts, USD cost, and "
      r"elapsed seconds. Claude rows use the JSON envelope from "
      r"\texttt{claude --output-format json} (exact counts); codex rows "
      r"are char/4 estimates flagged with $\dagger$.")
    W()
    W(r"\begin{tabular}{llrrrr}")
    W(r"\toprule")
    W(r"Paper & Stage & Input tk & Output tk & Cost (\$) & Elapsed (s) \\")
    W(r"\midrule")
    for (paper_tag, data) in [(args.paper_a, paper_a),
                              (args.paper_b, paper_b)]:
        for s in data["stages"]:
            if s.get("missing"):
                W(rf"{latex_escape(paper_tag)} & {latex_escape(s['label'])} "
                  rf"& - & - & - & - \\")
                continue
            est = r"$\dagger$" if s.get("estimated") else ""
            W(rf"{latex_escape(paper_tag)} & {latex_escape(s['label'])} "
              rf"& {fmt_int(s.get('input_tokens'))}{est} "
              rf"& {fmt_int(s.get('output_tokens'))}{est} "
              rf"& {fmt_cost(s.get('cost_usd'))} "
              rf"& {(s.get('elapsed_s') or 0):.1f} \\")
        t = data["totals"]
        W(rf"\textbf{{{latex_escape(paper_tag)} total}} & "
          rf"& \textbf{{{fmt_int(t['input_tokens'])}}} "
          rf"& \textbf{{{fmt_int(t['output_tokens'])}}} "
          rf"& \textbf{{{fmt_cost(t['cost_usd'])}}} "
          rf"& \textbf{{{t['elapsed_s']:.1f}}} \\")
        W(r"\midrule")
    grand_in = paper_a["totals"]["input_tokens"] + paper_b["totals"]["input_tokens"]
    grand_out = paper_a["totals"]["output_tokens"] + paper_b["totals"]["output_tokens"]
    grand_cost = paper_a["totals"]["cost_usd"] + paper_b["totals"]["cost_usd"]
    grand_t = paper_a["totals"]["elapsed_s"] + paper_b["totals"]["elapsed_s"]
    W(rf"\textbf{{Grand total}} & "
      rf"& \textbf{{{fmt_int(grand_in)}}} "
      rf"& \textbf{{{fmt_int(grand_out)}}} "
      rf"& \textbf{{{fmt_cost(grand_cost)}}} "
      rf"& \textbf{{{grand_t:.1f}}} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")

    # ---------- composite CQE comparison ----------
    W(r"\section{Composite CQE comparison}")
    W(r"Geometric mean of six dimensions: Novelty Rigour, Reproducibility, "
      r"Methodological Rigour, Falsifiability, Domain Depth, Communication. "
      r"A weakness on any one dimension cannot be averaged away.")
    W()
    W(r"\begin{tabular}{lcc}")
    W(r"\toprule")
    W(r"Paper & Composite & Verdict (reviewer panel) \\")
    W(r"\midrule")
    for (paper_tag, data) in [(args.paper_a, paper_a),
                              (args.paper_b, paper_b)]:
        cqe = data.get("cqe", {})
        composite = cqe.get("composite", "-")
        verdict = data.get("reviewer_verdict", "")[:60]
        W(rf"\texttt{{{latex_escape(paper_tag)}}} & "
          rf"\textbf{{{composite}/100}} & {latex_escape(verdict)} \\")
    W(r"\bottomrule")
    W(r"\end{tabular}")
    W()
    for (paper_tag, data) in [(args.paper_a, paper_a),
                              (args.paper_b, paper_b)]:
        dims = data.get("cqe", {}).get("dimensions", [])
        if not dims:
            continue
        W(rf"\subsection*{{{latex_escape(paper_tag)} per-dimension}}")
        W(r"\begin{tabular}{lr}")
        W(r"\toprule")
        W(r"Dimension & Score \\")
        W(r"\midrule")
        for d in dims:
            W(rf"{latex_escape(d.get('name',''))} & "
              rf"{d.get('score','-')}/100 \\")
        W(r"\bottomrule")
        W(r"\end{tabular}")

    # ---------- per-paper deep dives ----------
    for (paper_tag, data, title, arxiv, venue) in [
        (args.paper_a, paper_a, args.paper_a_title,
         args.paper_a_arxiv, args.paper_a_venue),
        (args.paper_b, paper_b, args.paper_b_title,
         args.paper_b_arxiv, args.paper_b_venue),
    ]:
        W(r"\clearpage")
        W(rf"\section{{Paper {paper_tag} --- \emph{{{latex_escape(title)}}}}}")
        W(rf"\noindent \href{{https://arxiv.org/abs/{arxiv}}}{{arXiv:{arxiv}}} "
          rf"\quad Venue: {latex_escape(venue)}")
        W()
        # Per-paper provenance + token sub-tally
        t = data["totals"]
        W(r"\paragraph{Provenance.} ")
        W(rf"Total LLM calls across the four stages used "
          rf"\textbf{{{fmt_int(t['input_tokens'])}}} input + "
          rf"\textbf{{{fmt_int(t['output_tokens'])}}} output tokens "
          rf"in \textbf{{{t['elapsed_s']:.1f}}}\,s of wall-clock LLM time. "
          rf"Backend marker JSON for every stage is in the run directory.")
        W()

        # Loop through stages with the actual prose
        for s in data["stages"]:
            label = s["label"]
            desc = s["desc"]
            W(rf"\subsection{{{latex_escape(label)}}}")
            if s.get("model_id"):
                W(rf"\noindent\textcolor{{muted}}"
                  rf"{{\small Backend: {latex_escape(s.get('backend', '-'))} "
                  rf"({latex_escape(s.get('model_id') or 'snapshot not surfaced')}) "
                  rf"\textperiodcentered\ "
                  rf"{fmt_int(s.get('input_tokens'))} in / "
                  rf"{fmt_int(s.get('output_tokens'))} out tokens "
                  rf"\textperiodcentered\ "
                  rf"{(s.get('elapsed_s') or 0):.1f}\,s}}")
                W()
            W(rf"\noindent\textcolor{{muted}}{{\small {latex_escape(desc)}}}")
            W()
            md_path = s.get("primary_md")
            if md_path and md_path.is_file():
                frag = md_to_latex_fragment(md_path)
                W(frag)
            else:
                W(r"\emph{(stage output missing on disk)}")
            W()

        # Fallacy findings table (additional structured view)
        fallacies = data.get("fallacies") or {}
        findings = fallacies.get("findings") or []
        if findings:
            W(rf"\subsubsection*{{Structured fallacy table --- {paper_tag}}}")
            W(r"\begin{longtable}{p{0.30\textwidth}p{0.08\textwidth}p{0.50\textwidth}}")
            W(r"\toprule")
            W(r"Fallacy & Severity & Location / evidence \\")
            W(r"\midrule")
            for f in findings:
                name = latex_escape(str(f.get("name", "")))
                sev = latex_escape(str(f.get("severity", "")))
                loc = latex_escape(str(f.get("location", ""))[:200])
                W(rf"{name} & {sev} & {loc} \\")
            W(r"\bottomrule")
            W(r"\end{longtable}")
            W()

    # ---------- reproducibility ----------
    W(r"\clearpage")
    W(r"\section{Reproducing this report}")
    W(r"\begin{verbatim}")
    W(r"cd examples/end_to_end/two_paper_novelty/")
    W(r"./run_two_papers.sh   # fetches both papers from arXiv,")
    W(r"                      # runs 4 stages x 2 papers,")
    W(r"                      # compiles PIPELINE_REPORT.pdf")
    W(r"\end{verbatim}")
    W(r"All raw artefacts (per-paper stage outputs, raw prompts, raw LLM "
      r"responses, backend markers) are persisted under \texttt{\_run/} "
      r"alongside this report. \texttt{PIPELINE\_REPORT.json} carries the "
      r"machine-readable summary.")
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
    ap.add_argument("--paper-a", required=True)
    ap.add_argument("--paper-a-title", required=True)
    ap.add_argument("--paper-a-arxiv", required=True)
    ap.add_argument("--paper-a-venue", required=True)
    ap.add_argument("--paper-b", required=True)
    ap.add_argument("--paper-b-title", required=True)
    ap.add_argument("--paper-b-arxiv", required=True)
    ap.add_argument("--paper-b-venue", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    pa = collect_paper(args.run_dir / "reports" / args.paper_a)
    pb = collect_paper(args.run_dir / "reports" / args.paper_b)

    args.out.write_text(render(args, pa, pb), encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")
    summary = {
        "paper_a": {
            "stages": [{k: (str(v) if isinstance(v, Path) else v)
                        for k, v in s.items() if k != "primary_md"}
                       for s in pa["stages"]],
            "totals": pa["totals"], "cqe": pa["cqe"],
            "fallacies": pa["fallacies"],
            "reviewer_verdict": pa["reviewer_verdict"],
        },
        "paper_b": {
            "stages": [{k: (str(v) if isinstance(v, Path) else v)
                        for k, v in s.items() if k != "primary_md"}
                       for s in pb["stages"]],
            "totals": pb["totals"], "cqe": pb["cqe"],
            "fallacies": pb["fallacies"],
            "reviewer_verdict": pb["reviewer_verdict"],
        },
    }
    (args.out.with_suffix(".json")).write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
