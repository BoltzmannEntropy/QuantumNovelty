"""chat skill — natural-language → chain dispatch.

Pattern-first, LLM-fallback. The patterns below are deliberately literal;
they catch the most common phrasings. Anything not matched falls through
to the LLM, which is asked to emit a structured JSON dispatch decision
the dispatcher then validates against the known skills + modes.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402


@dataclass
class Dispatch:
    skill: str
    mode: str | None = None
    flags: dict[str, str] = field(default_factory=dict)
    confidence: float = 1.0      # 1.0 = pattern hit; LLM-routed are < 1.0
    rationale: str = "pattern match"

    def as_command(self, root: Path) -> list[str]:
        cmd = [str(root / "skills" / self.skill / "run.sh")]
        if self.mode:
            cmd += ["--mode", self.mode]
        for k, v in self.flags.items():
            cmd += [f"--{k}", v]
        return cmd

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "mode": self.mode,
            "flags": self.flags,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


# =========================================================================
# Pattern catalog — deterministic first pass
# =========================================================================
# Each rule is (regex, dispatch builder). Earlier rules win.
# The builder receives the regex match object + the parsed CLI args.

def _strip_quote(s: str) -> str:
    s = s.strip()
    if (len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'")):
        return s[1:-1]
    return s


_RULES: list[tuple[re.Pattern, callable]] = []


def _rule(pat: str):
    def deco(fn):
        _RULES.append((re.compile(pat, re.IGNORECASE), fn))
        return fn
    return deco


# --- quantum_paper modes ----------------------------------------------------

@_rule(r"^\s*(write|draft)\s+a?\s*paper\s+on\s+(?P<topic>.+)$")
def _r1(m, args):
    return Dispatch("quantum_paper", "full",
                    {"topic": _strip_quote(m["topic"])})


@_rule(r"^\s*guide\s+me\s+through\s+writing\s+a?\s*paper\s+on\s+(?P<topic>.+)$")
def _r2(m, args):
    return Dispatch("quantum_paper", "plan",
                    {"topic": _strip_quote(m["topic"])})


@_rule(r"^\s*build\s+a?\s*paper\s+outline\s+on\s+(?P<topic>.+)$")
@_rule(r"^\s*outline\s+a?\s*paper\s+on\s+(?P<topic>.+)$")
def _r3(m, args):
    return Dispatch("quantum_paper", "outline-only",
                    {"topic": _strip_quote(m["topic"])})


@_rule(r"\b(write|generate)\s+an?\s+abstract\b")
def _r_abs(m, args):
    if not args.paper:
        return None  # need a --paper for abstract-only mode
    return Dispatch("quantum_paper", "abstract-only",
                    {"draft": str(args.paper)})


@_rule(r"convert\s+(?:this\s+)?paper\s+to\s+(?P<j>[a-z\-]+)\s*format")
def _r_conv(m, args):
    if not args.paper:
        return None
    return Dispatch("quantum_paper", "format-convert",
                    {"draft": str(args.paper), "journal": m["j"].lower()})


@_rule(r"\bcheck\s+(?:the\s+)?citations?\b")
def _r_cc(m, args):
    if not args.paper:
        return None
    return Dispatch("quantum_paper", "citation-check",
                    {"draft": str(args.paper)})


@_rule(r"\bgenerate\s+(?:a\s+)?(?:ai\s+)?disclosure(?:\s+statement|\s+block)?\b")
def _r_disc(m, args):
    if not args.paper:
        return None
    flags = {"draft": str(args.paper)}
    if args.journal:
        flags["journal"] = args.journal
    return Dispatch("quantum_paper", "disclosure", flags)


@_rule(r"i\s+have\s+a\s+draft.*reviewer\s+comments?")
def _r_rev(m, args):
    # quantum_paper revision mode hard-requires BOTH inputs.
    if not (args.paper and args.reviewer_comments):
        return None
    return Dispatch("quantum_paper", "revision",
                    {"draft": str(args.paper),
                     "reviewer-comments": str(args.reviewer_comments)})


@_rule(r"parse\s+(?:these\s+)?reviewer\s+comments?")
def _r_rev_coach(m, args):
    if not args.reviewer_comments:
        return None
    flags = {"reviewer-comments": str(args.reviewer_comments)}
    if args.paper:
        flags["draft"] = str(args.paper)
    return Dispatch("quantum_paper", "revision-coach", flags)


# --- deep_research modes ----------------------------------------------------

@_rule(r"^\s*research\s+(?:the\s+)?(?P<topic>.+)$")
@_rule(r"^\s*(?:do\s+)?(?:a\s+)?full\s+research\s+(?:on\s+)?(?P<topic>.+)$")
def _r_research(m, args):
    return Dispatch("deep_research", "full",
                    {"topic": _strip_quote(m["topic"])})


@_rule(r"^\s*(?:give\s+me\s+)?(?:a\s+)?quick\s+brief\s+(?:on\s+)?(?P<topic>.+)$")
def _r_quick(m, args):
    return Dispatch("deep_research", "quick",
                    {"topic": _strip_quote(m["topic"])})


@_rule(r"^\s*(?:do\s+)?(?:a\s+)?systematic\s+review\s+(?:on\s+)?(?P<topic>.+)$")
def _r_sysrev(m, args):
    return Dispatch("deep_research", "systematic-review",
                    {"topic": _strip_quote(m["topic"])})


@_rule(r"^\s*guide\s+my\s+research\s+(?:on\s+)?(?P<topic>.+)$")
def _r_socratic(m, args):
    return Dispatch("deep_research", "socratic",
                    {"topic": _strip_quote(m["topic"])})


@_rule(r"^\s*fact[\s\-]?check\b\s*(?P<topic>.*)$")
def _r_factcheck(m, args):
    return Dispatch("deep_research", "fact-check",
                    {"topic": _strip_quote(m["topic"]) or "see --paper"})


@_rule(r"^\s*(?:do\s+)?(?:a\s+)?lit(?:erature)?\s+review\s+(?:on\s+)?(?P<topic>.+)$")
def _r_litrev(m, args):
    return Dispatch("deep_research", "lit-review",
                    {"topic": _strip_quote(m["topic"])})


@_rule(r"review\s+(?:this\s+)?paper'?s?\s+research\s+quality")
def _r_research_review(m, args):
    return Dispatch("deep_research", "review",
                    {"topic": str(args.paper) if args.paper else "see --paper"})


# --- quantum_reviewer modes -------------------------------------------------

@_rule(r"^\s*review\s+this\s+paper\s*$")
def _r_review_full(m, args):
    if not args.paper:
        return None
    flags = {"draft": str(args.paper)}
    if args.journal:
        flags["journal"] = args.journal
    return Dispatch("quantum_reviewer", "full", flags)


@_rule(r"^\s*quick\s+assessment(?:\s+of\s+(?:this\s+)?paper)?\s*$")
def _r_review_quick(m, args):
    if not args.paper:
        return None
    return Dispatch("quantum_reviewer", "quick", {"draft": str(args.paper)})


@_rule(r"^\s*guide\s+me\s+to\s+improve\s+(?:this\s+)?paper\s*$")
def _r_review_guided(m, args):
    if not args.paper:
        return None
    return Dispatch("quantum_reviewer", "guided", {"draft": str(args.paper)})


@_rule(r"^\s*check\s+(?:the\s+)?methodology\s*$")
def _r_review_meth(m, args):
    if not args.paper:
        return None
    return Dispatch("quantum_reviewer", "methodology-focus",
                    {"draft": str(args.paper)})


@_rule(r"^\s*verify\s+(?:the\s+)?revisions\s*$")
def _r_review_re(m, args):
    if not args.paper:
        return None
    return Dispatch("quantum_reviewer", "re-review", {"draft": str(args.paper)})


@_rule(r"calibrate\s+(?:this\s+)?reviewer\s+against\s+(?:my\s+)?gold\s+set")
def _r_review_calib(m, args):
    if not args.paper:
        return None
    return Dispatch("quantum_reviewer", "calibration", {"draft": str(args.paper)})


# --- logical_fallacies ------------------------------------------------------

@_rule(r"(?:find|check\s+for)\s+(?:logical\s+)?fallacies")
def _r_fallacies(m, args):
    if not args.paper:
        return None
    return Dispatch("logical_fallacies", None, {"draft": str(args.paper)})


# --- pipeline orchestrator entries ------------------------------------------
# These dispatch to the chain at the pipeline level, not a single skill.

@_rule(r"i\s+want\s+to\s+write\s+a?\s*complete\s+research\s+paper(?:\s+on\s+(?P<topic>.+))?")
def _r_full_pipe(m, args):
    flags = {}
    if m.groupdict().get("topic"):
        flags["topic"] = _strip_quote(m["topic"])
    return Dispatch("PIPELINE", "full-pipeline", flags)


@_rule(r"i\s+already\s+have\s+a?\s*paper,?\s+review\s+it")
def _r_midentry_25(m, args):
    if not args.paper:
        return None
    return Dispatch("PIPELINE", "mid-entry-stage-2.5",
                    {"paper": str(args.paper)})


@_rule(r"i\s+received\s+reviewer\s+comments?")
def _r_midentry_4(m, args):
    if not args.paper:
        return None
    return Dispatch("PIPELINE", "mid-entry-stage-4",
                    {"paper": str(args.paper)})


@_rule(r"^\s*status\s*$")
def _r_status(m, args):
    return Dispatch("PIPELINE", "status", {})


# =========================================================================
# Pattern dispatch driver
# =========================================================================

def pattern_dispatch(prompt: str, args: argparse.Namespace) -> Dispatch | None:
    for pat, fn in _RULES:
        m = pat.search(prompt.strip())
        if m:
            d = fn(m, args)
            if d is not None:
                return d
    return None


# =========================================================================
# LLM fallback
# =========================================================================

_FALLBACK_PROMPT = """You are routing a user's natural-language request to
a QuantumNovelty skill. The user said:

```
{prompt}
```

Available skills + modes:

- deep_research [full, quick, systematic-review, socratic, fact-check, lit-review, review]
- quantum_paper [full, plan, outline-only, revision, revision-coach,
  abstract-only, lit-review, format-convert, citation-check, disclosure]
- quantum_reviewer [full, quick, guided, methodology-focus, re-review, calibration]
- logical_fallacies (no modes)
- novelty_audit (no modes)
- ablation_designer (no modes)
- cross_llm_prediction (no modes)
- pareto_explorer (no modes)
- literature_surfacer (no modes)
- book_acquirer (no modes)
- process_summary (no modes)

Return ONLY a fenced ```json``` block with this shape:

```json
{{
  "skill": "<name>",
  "mode": "<mode or null>",
  "flags": {{"flag_name": "value"}},
  "confidence": 0.85,
  "rationale": "one-sentence reason"
}}
```

Available context flags:
- topic: a research topic string
- draft: path to a paper (only if the user referenced one)
- paper: alias for draft (some skills want one, some the other)
- journal: target journal slug (flag name: journal)
- quantum-lib: target quantum-library slug (use the hyphenated flag name; draft files go under the `draft` flag, not `paper`)
"""


def llm_dispatch(prompt: str, llm_backend: str) -> Dispatch | None:
    full_prompt = _FALLBACK_PROMPT.format(prompt=prompt)
    try:
        result = call_llm(full_prompt, backend=llm_backend, timeout=300)
    except RuntimeError:
        return None
    m = re.search(r"```json\s*(\{.*?\})\s*```", result.text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    raw_flags = obj.get("flags") or {}
    if not isinstance(raw_flags, dict):
        raw_flags = {}
    # Normalize: only string-able scalars; underscore→hyphen flag names;
    # the spec's `paper` means the skills' `--draft`.
    flags = {}
    for k, v in raw_flags.items():
        if v is None or isinstance(v, (dict, list)):
            continue
        k = str(k).replace("_", "-")
        if k == "paper":
            k = "draft"
        flags[k] = str(v)
    conf = obj.get("confidence")
    try:
        conf = float(conf) if conf is not None else 0.5
    except (TypeError, ValueError):
        conf = 0.5
    return Dispatch(
        skill=obj.get("skill", ""),
        mode=obj.get("mode"),
        flags=flags,
        confidence=conf,
        rationale=f"LLM routing: {obj.get('rationale', '')}",
    )


# =========================================================================
# Execution
# =========================================================================

KNOWN_SKILLS = {
    "deep_research", "quantum_paper", "quantum_reviewer",
    "logical_fallacies", "novelty_audit", "ablation_designer",
    "cross_llm_prediction", "pareto_explorer", "literature_surfacer",
    "book_acquirer", "process_summary",
}


def validate_dispatch(d: Dispatch) -> str | None:
    """Return None if OK; an error string if the dispatch is invalid."""
    if d.skill == "PIPELINE":
        # Pipeline-level dispatch validated by the pipeline orchestrator.
        return None
    if d.skill not in KNOWN_SKILLS:
        return f"unknown skill: {d.skill!r}"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--paper", default=None, type=Path)
    ap.add_argument("--reviewer-comments", default=None, type=Path,
                    help="reviewer comments file — required for the "
                         "revision / revision-coach dispatches")
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--journal", default=None)
    ap.add_argument("--quantum-lib", default=None)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    # 1. Pattern dispatch
    dispatch = pattern_dispatch(args.prompt, args)

    # 2. LLM fallback
    if dispatch is None:
        dispatch = llm_dispatch(args.prompt, args.llm)

    if dispatch is None:
        (args.outdir / "dispatch.md").write_text(
            f"# chat: could not route prompt\n\nPrompt: {args.prompt!r}\n"
            f"Try a more direct phrasing (see SKILL.md for patterns), "
            f"or invoke the skill directly via chain/run.sh.\n",
            encoding="utf-8"
        )
        print(f"chat: could not route {args.prompt!r}", file=sys.stderr)
        return 3

    # Pre-fill journal / quantum_lib if provided at CLI and the dispatch
    # doesn't already specify them.
    # ...but only for skills whose argparse actually accepts the flag —
    # an unrecognized argument is an instant rc=2 from the child.
    _ACCEPTS = {
        "deep_research":       {"journal", "quantum-lib"},
        "quantum_paper":       {"journal", "quantum-lib"},
        "literature_surfacer": {"journal", "quantum-lib"},
        "quantum_reviewer":    {"journal"},
    }
    accepts = _ACCEPTS.get(dispatch.skill, set())
    if args.journal and "journal" in accepts \
            and "journal" not in dispatch.flags:
        dispatch.flags["journal"] = args.journal
    if args.quantum_lib and "quantum-lib" in accepts \
            and "quantum-lib" not in dispatch.flags:
        dispatch.flags["quantum-lib"] = args.quantum_lib

    err = validate_dispatch(dispatch)
    if err:
        print(f"chat: invalid dispatch: {err}", file=sys.stderr)
        return 3

    decision = dispatch.to_dict()
    (args.outdir / "dispatch_decision.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8"
    )
    md = (
        f"# chat dispatch\n\n"
        f"**Prompt:** {args.prompt!r}\n\n"
        f"**Routed to:** `{dispatch.skill}`"
        + (f" (mode: `{dispatch.mode}`)" if dispatch.mode else "")
        + f"\n\n"
        f"**Confidence:** {dispatch.confidence:.2f}\n\n"
        f"**Rationale:** {dispatch.rationale}\n\n"
        f"**Flags:** "
        + ("\n" + "\n".join(f"- `--{k}` {v}" for k, v in dispatch.flags.items())
           if dispatch.flags else "_(none)_")
        + "\n"
    )
    (args.outdir / "dispatch.md").write_text(md, encoding="utf-8")

    if not args.execute:
        print(json.dumps(decision, indent=2))
        return 0

    # Execute
    if dispatch.skill == "PIPELINE":
        # Pipeline-level: delegate to chain/run.sh with pipeline name.
        cmd = [str(ROOT / "chain" / "run.sh"),
               "--pipeline", dispatch.mode or "full-pipeline",
               "--outdir", str(args.outdir / "pipeline"),
               "--llm", args.llm]
        for k, v in dispatch.flags.items():
            cmd += [f"--{k}", v]
    else:
        # Forward the user's backend choice — a silent claude default on a
        # codex request would be exactly the silent swap QN forbids.
        cmd = (dispatch.as_command(ROOT)
               + ["--outdir", str(args.outdir / dispatch.skill),
                  "--llm", args.llm])
    print(f"chat: executing → {' '.join(cmd)}")
    r = subprocess.run(cmd)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
