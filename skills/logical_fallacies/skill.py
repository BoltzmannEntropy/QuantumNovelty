"""logical_fallacies skill — fallacy detection with quantum-CS additions.

Takes a standard logical-fallacy taxonomy and extends it
with 11 fallacies that appear specifically in quantum-computing manuscripts
(cherry-picked baselines, ad-hoc precision floors, simulator-laundering,
mapping-by-convenience, etc.). See SKILL.md for the full taxonomy.

Output is both human-readable and structured JSON so downstream skills
(quantum_reviewer methodology-focus, process_summary CQE) can consume the
findings without re-parsing markdown.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402
from paper_io import load_paper_text            # noqa: E402


PROMPT_TEMPLATE = """# Logical-fallacy audit of a quantum-computing paper

You are auditing the manuscript below for logical fallacies, using the
extended taxonomy QuantumNovelty maintains for quantum-CS work.

## Severity threshold
Report findings with severity at or above: **{severity}**.

## Taxonomy (use these EXACT category names in the JSON output)

### General fallacies
- circular-reasoning
- appeal-to-authority
- post-hoc-ergo-propter-hoc
- slippery-slope
- false-dichotomy
- hasty-generalization
- straw-man
- equivocation
- ad-hominem
- affirming-the-consequent
- denying-the-antecedent

### Quantum-CS-specific (NEW — apply these aggressively)
- cherry-picked-baseline — comparing against a weak baseline while ignoring
  a stronger published method on the same Hamiltonian
- ad-hoc-precision-floor — quoting energy diff at sub-noise precision
- conflated-regimes — extrapolating from small Hamiltonians to large
- active-space-handwave — claiming generalisation without running it
- hardware-irrelevant-comparison — simulator vs hardware without noise calibration
- asymptotic-only-claim — N→∞ claim with finite-N demonstration
- unit-inflation — choosing units to inflate apparent magnitude
- simulator-laundering — discover on lib A, evaluate on lib B, conflate
- mapping-by-convenience — JW/BK/parity chosen for cosmetics, not science
- pareto-cherry-picked-axes — domination claimed on a chosen axis subset
- cross-llm-theatre — same-vendor snapshots dressed up as multi-model

## Manuscript

```
{draft}
```

## Output

### Section 1: Markdown findings
For each fallacy detected, one paragraph:
- **Fallacy:** category from the taxonomy above
- **Severity:** critical | high | medium | low
- **Location:** section / paragraph / verbatim quote
- **Why it's the fallacy:** specific mechanism
- **Suggested fix:** concrete text change

### Section 2: Machine-readable JSON
Emit a single fenced ```json``` block:

```json
{{
  "findings": [
    {{
      "name": "cherry-picked-baseline",
      "category": "quantum-cs",
      "severity": "high",
      "location": "Section IV, paragraph 2",
      "evidence": "verbatim quote from manuscript",
      "suggested_fix": "what to change"
    }}
  ]
}}
```

## Constraints
- Use EXACT category names from the taxonomy.
- DO NOT report borderline cases below the requested severity threshold.
- DO NOT invent fallacies that aren't in the taxonomy; if you need a new
  category, mark severity:low and category:other with a clear name.
- Each finding MUST include a verbatim evidence quote from the manuscript.
"""


def _load_draft(path: Path) -> str:
    return load_paper_text(path)


def _extract_json(text: str) -> dict | None:
    """Best-effort extraction of the findings ```json``` block.

    The report's Section 1 quotes verbatim evidence which can itself
    contain ```json fences (papers with JSON listings); taking the
    FIRST block grabbed manuscript fragments. Prefer the last block
    whose payload parses and carries a "findings" key.
    """
    candidates = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    for blob in reversed(candidates):
        try:
            parsed = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "findings" in parsed:
            return parsed
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draft", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--severity-threshold",
                    default="medium",
                    choices=["low", "medium", "high", "critical"])
    args = ap.parse_args()

    if not args.draft.is_file():
        print(f"ERROR: --draft not found: {args.draft}", file=sys.stderr)
        return 2
    args.outdir.mkdir(parents=True, exist_ok=True)

    draft_text = _load_draft(args.draft)
    prompt = PROMPT_TEMPLATE.format(draft=draft_text,
                                    severity=args.severity_threshold)
    (args.outdir / "full_prompt.txt").write_text(prompt, encoding="utf-8")

    try:
        result = call_llm(prompt, backend=args.llm, timeout=1800)
    except RuntimeError as e:
        (args.outdir / "fallacy_report.md").write_text(
            f"# ⚠ logical_fallacies FAILED\n\nBackend {args.llm}: `{e}`\n",
            encoding="utf-8")
        return 3

    (args.outdir / "fallacy_report.md").write_text(
        result.text, encoding="utf-8")
    structured = _extract_json(result.text)
    if structured is not None:
        (args.outdir / "fallacy_findings.json").write_text(
            json.dumps(structured, indent=2), encoding="utf-8")
    else:
        (args.outdir / "fallacy_findings.json").write_text(
            json.dumps({
                "findings": [],
                "_note": "no machine-readable JSON block found in LLM output"
            }, indent=2), encoding="utf-8")
    (args.outdir / "_llm_generation.log").write_text(
        f"--- backend: {result.backend_actually_used} ---\n"
        f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
        f"--- threshold: {args.severity_threshold} ---\n"
        f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
        encoding="utf-8")
    write_backend_marker(args.outdir, result)

    n_findings = len(structured.get("findings", [])) if structured else 0
    print(f"logical_fallacies: {n_findings} findings at threshold "
          f"{args.severity_threshold}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
