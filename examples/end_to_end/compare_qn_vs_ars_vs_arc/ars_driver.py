"""ARS (academic-research-skills) driver — runs the academic-paper-reviewer
skill's agent prompts against a paper using QN's `call_llm` so the LLM
backend and token-ledger plumbing match QN's own runs.

ARS itself is a Claude-Code skill pack: the "agents" are markdown prompt
files (`agents/eic_agent.md`, etc.) that Claude Code loads conversationally.
This driver does the equivalent programmatically:

  1. Reads each agent's prompt file
  2. Substitutes the paper text + metadata block
  3. Calls `call_llm(prompt, backend)` for each
  4. Writes the canonical ARS artifact filenames into <outdir>

The 7-agent orchestration order (per ARS academic-paper-reviewer SKILL.md):

  Phase 0:  field_analyst_agent              → reviewer_config.md
  Phase 1:  eic_agent                        → eic_review_card.md
            methodology_reviewer_agent       → methodology_review_card.md
            domain_reviewer_agent            → domain_review_card.md
            perspective_reviewer_agent       → perspective_review_card.md
            devils_advocate_reviewer_agent   → devils_advocate_review_card.md
  Phase 2:  editorial_synthesizer_agent      → editorial_decision_letter.md

Each call writes a _backend_used.json alongside (matching QN's marker
format) so the comparison report can tally tokens and costs head-to-head.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "skills" / "common"))
import llm  # noqa: E402

# Sibling clone of imbad0202/academic-research-skills. Default: next to
# this repo; override with the ARS_REPO env var.
def _find_sibling(name: str) -> Path:
    """First existing candidate: next to the repo, or one level up
    (the local PRJ layout keeps CODE inside a project folder)."""
    for cand in (REPO.parent / name, REPO.parent.parent / name):
        if cand.is_dir():
            return cand
    return REPO.parent / name   # default for the error message


ARS_REPO = Path(os.environ.get("ARS_REPO", "")) \
    if os.environ.get("ARS_REPO") else _find_sibling("academic-research-skills")
ARS_REVIEWER_DIR = ARS_REPO / "academic-paper-reviewer"

if not ARS_REVIEWER_DIR.is_dir():
    sys.exit(f"ERROR: academic-research-skills not found at {ARS_REPO} — "
             f"clone https://github.com/imbad0202/academic-research-skills "
             f"next to this repo or set ARS_REPO. (No LLM calls were made.)")

# (agent prompt file, output filename, friendly stage id)
AGENT_PIPELINE = [
    ("field_analyst_agent.md",          "00_reviewer_config.md",
     "00-field-analyst",          "phase0"),
    ("eic_agent.md",                    "01_eic_review_card.md",
     "01-eic",                    "phase1"),
    ("methodology_reviewer_agent.md",   "02_methodology_review_card.md",
     "02-methodology",            "phase1"),
    ("domain_reviewer_agent.md",        "03_domain_review_card.md",
     "03-domain",                 "phase1"),
    ("perspective_reviewer_agent.md",   "04_perspective_review_card.md",
     "04-perspective",            "phase1"),
    ("devils_advocate_reviewer_agent.md", "05_devils_advocate_review_card.md",
     "05-devils-advocate",        "phase1"),
    ("editorial_synthesizer_agent.md",  "06_editorial_decision_letter.md",
     "06-editorial-synth",        "phase2"),
]


def _load_agent_prompt(name: str) -> str:
    p = ARS_REVIEWER_DIR / "agents" / name
    if not p.is_file():
        raise FileNotFoundError(f"ARS agent prompt missing: {p}")
    return p.read_text(encoding="utf-8")


def _build_prompt(agent_md: str, paper_text: str, paper_title: str,
                  venue: str, prior_outputs: dict[str, str]) -> str:
    """Compose the final prompt sent to the LLM.

    ARS agents normally receive the paper through Claude Code's
    conversational context. Here we explicitly inject the paper text
    plus the agent's own prompt body, plus any upstream agent outputs
    the orchestration expects to be in context.
    """
    # Strip the YAML frontmatter from the agent prompt (Claude Code
    # parses it for routing; the LLM call doesn't need it).
    body = agent_md
    if body.startswith("---"):
        end = body.find("---", 3)
        if end != -1:
            body = body[end + 3:].lstrip()

    parts = [
        "# Paper under review",
        f"**Title:** {paper_title}",
        f"**Venue:** {venue}",
        "",
        "## Paper text (verbatim; the version your review must reference)",
        "",
        paper_text[:200_000],   # cap at 200 KB like QN's deep_research --paper
        "",
        "---",
        "",
        body,
    ]
    if prior_outputs:
        parts.append("\n---\n")
        parts.append("# Upstream agent outputs (in your context)")
        for stage_id, md in prior_outputs.items():
            parts.append(f"\n## From `{stage_id}`\n\n{md[:30_000]}\n")
    return "\n".join(parts)


def _write_backend_marker(out_path: Path, result: llm.LLMResult,
                          stage_id: str, agent_file: str) -> None:
    """Mirror QN's `_backend_used.json` shape so the comparison report
    can read tokens / model / cost / elapsed identically."""
    marker = {
        "stage_id": stage_id,
        "framework": "ARS",
        "agent": agent_file,
        "backend_requested": result.backend_requested,
        "backend_actually_used": result.backend_actually_used,
        "model_id": result.model_id,
        "elapsed_s": result.elapsed_s,
        "usage": {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cache_read_input_tokens": result.cache_read_input_tokens,
            "cache_creation_input_tokens": result.cache_creation_input_tokens,
            "total_cost_usd": result.total_cost_usd,
            "tokens_estimated": result.tokens_estimated,
        },
    }
    out_path.write_text(json.dumps(marker, indent=2), encoding="utf-8")


def run_ars_review(paper_path: Path, paper_title: str, venue: str,
                   outdir: Path, backend: str = "claude") -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    paper_text = paper_path.read_text(encoding="utf-8", errors="replace")

    prior_outputs: dict[str, str] = {}
    summary: list[dict] = []

    for agent_file, out_file, stage_id, phase in AGENT_PIPELINE:
        out_path = outdir / out_file
        marker_path = outdir / out_file.replace(".md", "_backend_used.json")
        prompt_path = outdir / out_file.replace(".md", "_prompt.txt")

        # Idempotent resume: skip if output already present + non-empty.
        if out_path.is_file() and marker_path.is_file() \
                and out_path.stat().st_size > 100:
            prior_outputs[stage_id] = out_path.read_text(encoding="utf-8")
            print(f"  [skip] {stage_id} — present at {out_path}")
            summary.append({"stage_id": stage_id, "agent": agent_file,
                            "rc": 0, "skipped": True})
            continue

        agent_md = _load_agent_prompt(agent_file)
        prompt = _build_prompt(agent_md, paper_text, paper_title, venue,
                                # editor-synth wants prior outputs;
                                # individual reviewers should NOT see each
                                # other (independence is the point).
                                prior_outputs if phase == "phase2" else {})
        prompt_path.write_text(prompt, encoding="utf-8")

        print(f"  [run]  {stage_id} via {backend} → {out_file}")
        t0 = time.monotonic()
        try:
            result = llm.call_llm(prompt, backend=backend, timeout=900)
        except RuntimeError as e:
            print(f"  [FAIL] {stage_id}: {e}")
            summary.append({"stage_id": stage_id, "agent": agent_file,
                            "rc": 1, "skipped": False, "error": str(e)[:200]})
            continue
        elapsed = time.monotonic() - t0
        out_path.write_text(result.text, encoding="utf-8")
        _write_backend_marker(marker_path, result, stage_id, agent_file)
        prior_outputs[stage_id] = result.text
        summary.append({
            "stage_id": stage_id, "agent": agent_file, "rc": 0,
            "skipped": False, "elapsed_s": round(elapsed, 2),
            "model_id": result.model_id,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "total_cost_usd": result.total_cost_usd,
        })
    (outdir / "ars_run_summary.json").write_text(
        json.dumps({"framework": "ARS", "backend": backend,
                    "stages": summary}, indent=2), encoding="utf-8")
    return {"stages": summary}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--title", required=True)
    ap.add_argument("--venue", required=True)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    args = ap.parse_args()
    run_ars_review(args.paper, args.title, args.venue, args.outdir,
                    backend=args.llm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
