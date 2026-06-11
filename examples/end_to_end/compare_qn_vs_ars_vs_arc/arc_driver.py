"""ARC (AutoResearchClaw) review driver — runs ARC's `peer_review` +
`quality_gate` stage prompts against a paper using QN's `call_llm` so the
backend and token-ledger plumbing match QN's own runs.

ARC is a 23-stage autonomous research pipeline (topic → empirical paper).
For this head-to-head we route only the two paper-review stages:

  peer_review     → simulates 2+ reviewer perspectives, methodology-evidence
                    consistency check, fabrication-flag scan
  quality_gate    → final JSON verdict (score_1_to_10, strengths,
                    weaknesses, required_actions, verdict)

The prompts are loaded verbatim from ARC's `prompts.default.yaml` so the
output is identical to what `python -m researchclaw run` would produce
for these two stages — just without the surrounding 21 generation stages.

Each call writes a `_backend_used.json` alongside (matching QN's marker
format) so the comparison report can tally tokens and costs head-to-head.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "skills" / "common"))
import llm  # noqa: E402

# Sibling clone of AutoResearchClaw. Default: next to this repo;
# override with the ARC_REPO env var.
def _find_sibling(name: str) -> Path:
    for cand in (REPO.parent / name, REPO.parent.parent / name):
        if cand.is_dir():
            return cand
    return REPO.parent / name


ARC_REPO = Path(os.environ.get("ARC_REPO", "")) \
    if os.environ.get("ARC_REPO") else _find_sibling("AutoResearchClaw")
ARC_PROMPTS = ARC_REPO / "prompts.default.yaml"

if yaml is None:
    sys.exit("ERROR: PyYAML is required for the ARC driver "
             "(pip install pyyaml). (No LLM calls were made.)")
if not ARC_PROMPTS.is_file():
    sys.exit(f"ERROR: AutoResearchClaw not found at {ARC_REPO} — clone it "
             f"next to this repo or set ARC_REPO. (No LLM calls were made.)")

# (stage name in prompts.yaml, output filename, friendly stage id)
ARC_STAGES = [
    ("peer_review",   "01_peer_review.md",      "01-peer-review"),
    ("quality_gate",  "02_quality_gate.json",   "02-quality-gate"),
]


def _load_prompts() -> dict:
    with open(ARC_PROMPTS, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_prompt(system: str, user_template: str, paper_text: str,
                  paper_title: str, topic: str, venue: str,
                  prior_outputs: dict[str, str]) -> str:
    """Substitute template vars and prepend the paper text.

    ARC's templates use {var_name}. The ones we have or can fabricate
    sanely for a review-only run:
      {topic}      paper title (we treat title as topic for review)
      {paper}      paper text
      {revised}    paper text (quality_gate's variable for the revised paper)
      {reviews}    prior peer_review output
      {quality_threshold}  default 7.0
      {evidence}   experiment evidence (none — this is review-only)

    Any other {var_name} we leave as-is; the LLM tolerates dangling
    placeholders as long as the surrounding instructions are clear.
    """
    body = user_template

    # The paper text goes in the preamble (once). If the prompt template
    # references {paper} / {revised}, we replace with a back-reference so
    # we don't duplicate the content.
    paper_ref = "(see *Paper text* section above)"
    substitutions = {
        "{topic}": topic[:200],
        "{paper}": paper_ref,
        "{revised}": paper_ref,
        "{reviews}": prior_outputs.get("01-peer-review", "")[:60_000],
        "{quality_threshold}": "7.0",
        "{evidence}": ("[No experiment evidence available — this is a "
                       "review-only run against an existing published "
                       f"paper at {venue}.]"),
        "{venue}": venue,
        "{paper_title}": paper_title,
    }
    for k, v in substitutions.items():
        body = body.replace(k, v)

    # Compose system + user with the paper text as the SOLE copy.
    parts = [
        f"# System role\n\n{system}",
        "",
        "# Paper under review",
        f"**Title:** {paper_title}",
        f"**Venue:** {venue}",
        "",
        "## Paper text (verbatim)",
        "",
        paper_text[:160_000],
        "",
        "---",
        "",
        "# Task",
        "",
        body,
    ]
    return "\n".join(parts)


def _write_backend_marker(out_path: Path, result: llm.LLMResult,
                          stage_id: str, stage_name: str) -> None:
    marker = {
        "stage_id": stage_id,
        "framework": "ARC",
        "stage_name": stage_name,
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


def _extract_json_from_text(text: str) -> str | None:
    """ARC quality_gate is supposed to return JSON. Be tolerant: find the
    first balanced {...} block and return it verbatim."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return m.group(0) if m else None


def run_arc_review(paper_path: Path, paper_title: str, venue: str,
                   topic: str, outdir: Path,
                   backend: str = "claude") -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    paper_text = paper_path.read_text(encoding="utf-8", errors="replace")
    prompts = _load_prompts()
    stages = prompts.get("stages", {})

    prior_outputs: dict[str, str] = {}
    summary: list[dict] = []

    for stage_name, out_file, stage_id in ARC_STAGES:
        out_path = outdir / out_file
        marker_path = outdir / (out_file.rsplit(".", 1)[0] + "_backend_used.json")
        prompt_path = outdir / (out_file.rsplit(".", 1)[0] + "_prompt.txt")

        if out_path.is_file() and marker_path.is_file() \
                and out_path.stat().st_size > 100:
            prior_outputs[stage_id] = out_path.read_text(encoding="utf-8")
            print(f"  [skip] {stage_id} — present at {out_path}")
            summary.append({"stage_id": stage_id, "stage_name": stage_name,
                            "rc": 0, "skipped": True})
            continue

        stage_spec = stages.get(stage_name, {})
        system = stage_spec.get("system", "")
        user_template = stage_spec.get("user", "")
        if not user_template:
            print(f"  [SKIP] {stage_id}: prompt template missing in "
                  f"ARC's prompts.default.yaml")
            continue

        prompt = _build_prompt(system, user_template, paper_text,
                                paper_title, topic, venue, prior_outputs)
        prompt_path.write_text(prompt, encoding="utf-8")

        print(f"  [run]  {stage_id} via {backend} → {out_file}")
        t0 = time.monotonic()
        try:
            result = llm.call_llm(prompt, backend=backend, timeout=900)
        except RuntimeError as e:
            print(f"  [FAIL] {stage_id}: {e}")
            summary.append({"stage_id": stage_id, "stage_name": stage_name,
                            "rc": 1, "skipped": False, "error": str(e)[:200]})
            continue
        elapsed = time.monotonic() - t0

        # quality_gate is contracted to return JSON; extract if possible.
        if stage_name == "quality_gate":
            json_blob = _extract_json_from_text(result.text)
            if json_blob:
                # Validate it's parseable; if not, fall back to raw text.
                try:
                    parsed = json.loads(json_blob)
                    out_path.write_text(
                        json.dumps(parsed, indent=2), encoding="utf-8"
                    )
                except json.JSONDecodeError:
                    out_path.write_text(result.text, encoding="utf-8")
            else:
                out_path.write_text(result.text, encoding="utf-8")
        else:
            out_path.write_text(result.text, encoding="utf-8")
        _write_backend_marker(marker_path, result, stage_id, stage_name)
        prior_outputs[stage_id] = result.text
        summary.append({
            "stage_id": stage_id, "stage_name": stage_name, "rc": 0,
            "skipped": False, "elapsed_s": round(elapsed, 2),
            "model_id": result.model_id,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "total_cost_usd": result.total_cost_usd,
        })
    (outdir / "arc_run_summary.json").write_text(
        json.dumps({"framework": "ARC", "backend": backend,
                    "stages": summary}, indent=2), encoding="utf-8"
    )
    return {"stages": summary}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--title", required=True)
    ap.add_argument("--venue", required=True)
    ap.add_argument("--topic", default=None,
                    help="Topic for {topic} substitution; defaults to title")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    args = ap.parse_args()
    run_arc_review(args.paper, args.title, args.venue,
                    args.topic or args.title, args.outdir,
                    backend=args.llm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
