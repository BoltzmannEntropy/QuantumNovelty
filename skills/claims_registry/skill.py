"""claims_registry — deterministic numeric-claim audits. No LLM calls.

Two modes, both adapted from AutoResearchClaw's verification stages
(researchclaw/paper_verifier.py, stage-22 paper_verification and the
verified-registry gate):

  registry (default) — single-document gate. Regex-extracts every numeric
      value, builds a registry from the Results / Experiments / Tables
      sections (the ground truth of what was measured), and gates the
      Abstract / Intro / Discussion against it. Catches the class of
      error where the abstract says "98.3% accuracy" but the experiments
      table says 87%.

  render-audit (--source + --render) — cross-document gate. Every numeric
      in the rendered artifact (LaTeX or text-extracted PDF) must trace
      back to the source-of-truth document. Catches render-time
      fabrication — LLM rewrites that inject numbers.

Outputs (registry mode):
  registry.json             every ground-truth numeric with section + line
  verification_report.json  machine-readable findings
  verification_report.md    typeset-ready findings table

Outputs (render-audit mode):
  paper_verification.json   ARC-schema report with fabrication_rate

Exit codes: 0 clean run (findings may still be present), 2 bad input,
3 render-audit failed its threshold.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from paper_io import load_paper_text  # noqa: E402


# Alternation order matters: the longest, most specific forms must come
# first or the regex engine settles for the plain-number prefix ("1.5e-3"
# would tokenize as "1" + "3", corrupting both registry and findings).
NUMBER_RE = re.compile(
    r"""
    (?<![\w\.])              # not preceded by word char or decimal
    (
        \d+(?:\.\d+)?e[+-]?\d+  # 1.5e-3, 2e6 (scientific notation)
        |\d+/\d+             # fractions like 3/4
        |\d+(?:\.\d+)?(?:%|x)?  # 87, 87.3, 87%, 14.1x (speedup notation)
    )
    (?![\w])                 # not followed by word char
    """,
    re.VERBOSE,
)


def _norm(value: str) -> str:
    """Comparison key: '14.1x' == '14.1' == '14.1%' as the same numeral."""
    return value.rstrip("%x")

DEFAULT_STRICT_SECTIONS = {
    "results", "experiments", "experimental_results", "evaluation",
    "evaluation_results", "main_results", "ablation_studies", "ablation",
    "table", "tables", "figure", "figures", "benchmarks", "measurements",
}

DEFAULT_LENIENT_SECTIONS = {
    "abstract", "introduction", "intro", "related_work", "background",
    "discussion", "conclusion", "conclusions", "limitations",
    "future_work", "outlook", "discussion_and_outlook",
}

# Years and common rhetorical integers never count as fabrications.
TRIVIAL = {str(y) for y in range(1900, 2100)}
TRIVIAL |= {str(n) for n in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100, 1000)}


def normalize_section_name(name: str) -> str:
    return re.sub(r"[\s-]+", "_", name.strip().lower())


# Plain-text heading heuristic for pdftotext output: short line, mostly
# letters, either ALL-CAPS or a numbered heading ("II. RESULTS",
# "3 Discussion"), surrounded by blank-ish lines.
_PLAIN_HEADING_RE = re.compile(
    r"^\s*(?:[IVXLC]+\.|[A-Z]\.|\d+\.?|\d+\.\d+\.?)?\s*"
    r"([A-Z][A-Za-z \-&]{2,55})\s*$"
)


def split_into_sections(text: str) -> dict[str, str]:
    """Split paper text into named sections.

    Tries LaTeX \\section{...}, then markdown headings, then a
    plain-text heuristic for pdftotext output (numbered or ALL-CAPS
    heading lines). Anything before the first heading lands in
    "preamble".
    """
    sections: dict[str, str] = {}
    latex_split = re.split(
        r"\\(?:section|subsection|chapter)\*?\{([^}]+)\}", text)
    if len(latex_split) > 1:
        if latex_split[0].strip():
            sections["preamble"] = latex_split[0]
        for i in range(1, len(latex_split) - 1, 2):
            name = normalize_section_name(latex_split[i])
            sections.setdefault(name, "")
            sections[name] += latex_split[i + 1]
        return sections

    md_split = re.split(r"^#+\s+(.+)$", text, flags=re.MULTILINE)
    if len(md_split) > 1:
        if md_split[0].strip():
            sections["preamble"] = md_split[0]
        for i in range(1, len(md_split) - 1, 2):
            name = normalize_section_name(md_split[i])
            sections.setdefault(name, "")
            sections[name] += md_split[i + 1]
        return sections

    # Plain-text fallback: heading = a line whose normalized name matches
    # a known section vocabulary (strict or lenient). Restricting to the
    # known vocabulary keeps author names / affiliations / figure captions
    # from becoming sections.
    known = DEFAULT_STRICT_SECTIONS | DEFAULT_LENIENT_SECTIONS
    current = "preamble"
    sections = {"preamble": ""}
    for line in text.splitlines():
        m = _PLAIN_HEADING_RE.match(line)
        if m:
            cand = normalize_section_name(m.group(1))
            if cand in known:
                current = cand
                sections.setdefault(current, "")
                continue
        sections[current] = sections.get(current, "") + line + "\n"
    if not sections["preamble"].strip():
        sections.pop("preamble")
    return sections or {"preamble": text}


def is_likely_excluded_numeric(text: str, position: int) -> bool:
    """Skip numbers that are citations, eq/fig/table refs, or years."""
    start = max(0, position - 25)
    context = text[start:position]
    if re.search(r"\\cite\w*\{[^}]*$", context):
        return True
    if re.search(
        r"(?:fig|figure|tab|table|sec|section|eq|equation|refs?|chapter|ch)"
        r"\.?\s*$", context, re.IGNORECASE,
    ):
        return True
    # "[59" — bracketed reference numbers. Parenthesized values like
    # "(87.3%)" are real measurements and must NOT be excluded; years in
    # parens are handled by the TRIVIAL whitelist at check time.
    if re.search(r"\[\s*$", context):
        return True
    return False


def extract_numerics(section_text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for m in NUMBER_RE.finditer(section_text):
        if is_likely_excluded_numeric(section_text, m.start()):
            continue
        line_no = section_text.count("\n", 0, m.start()) + 1
        ctx_start = max(0, m.start() - 40)
        ctx_end = min(len(section_text), m.end() + 40)
        hits.append({
            "value": m.group(1),
            "line": line_no,
            "context": section_text[ctx_start:ctx_end]
            .replace("\n", " ").strip(),
        })
    return hits


def build_registry(sections: dict[str, str],
                   strict_sections: set[str]) -> dict[str, list[dict]]:
    registry: dict[str, list[dict]] = defaultdict(list)
    for sname, text in sections.items():
        if sname not in strict_sections:
            continue
        for hit in extract_numerics(text):
            hit["section"] = sname
            registry[_norm(hit["value"])].append(hit)
    return dict(registry)


def check_section(section_name: str, section_text: str,
                  registry: dict[str, list[dict]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for hit in extract_numerics(section_text):
        raw = hit["value"]
        v = _norm(raw)
        if v in registry:
            continue
        # The round-number whitelist covers rhetorical usage ("100
        # examples", years) — but a suffixed form ("100x speedup",
        # "10%") is always a substantive claim and must trace back.
        if raw == v and v in TRIVIAL:
            continue
        findings.append({
            "section": section_name,
            "value": v,
            "context": hit["context"],
            "line": hit["line"],
            "severity": "WARN",
        })
    return findings


def run_registry(args: argparse.Namespace) -> int:
    text = load_paper_text(args.paper)
    sections = split_into_sections(text)
    strict = {normalize_section_name(s) for s in args.strict_on.split(",")}

    registry = build_registry(sections, strict)
    findings: list[dict[str, Any]] = []
    no_ground_truth = not registry
    if no_ground_truth:
        # No Results/Experiments/Tables section was identified (common
        # for letter-style papers or lossy PDF extraction). Flagging
        # every numeric would be noise — report the condition instead.
        pass
    else:
        for sname, body in sections.items():
            if sname in strict:
                continue
            findings.extend(check_section(sname, body, registry))

    out = args.outdir
    (out / "registry.json").write_text(
        json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "mode": "registry",
        "status": "no-ground-truth" if no_ground_truth else "checked",
        "paper": args.paper.name,
        "sections_indexed": sorted(sections.keys()),
        "strict_sections": sorted(strict & set(sections.keys())),
        "registry_size": len(registry),
        "warnings": len(findings),
        "findings": findings,
    }
    (out / "verification_report.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    md = ["# Numeric-Claim Registry Audit", ""]
    md.append(f"Paper: `{args.paper.name}` --- {len(sections)} sections "
              f"indexed, {len(registry)} distinct ground-truth values "
              f"(from {', '.join(sorted(strict & set(sections.keys()))) or 'none'}).")
    md.append("")
    if no_ground_truth:
        md.append("**Not applicable: no Results/Experiments/Tables "
                  "section was identified**, so there is no in-paper "
                  "ground truth to gate against. This is expected for "
                  "letter-style papers without named section headings or "
                  "for lossy PDF extraction. Run against the LaTeX/"
                  "markdown source, or pass --strict-on with this "
                  "paper's actual section names.")
        md.append("")
    if findings:
        md.append(f"{len(findings)} numeric value(s) outside the strict "
                  "sections do not trace back to a measured value:")
        md.append("")
        md.append("| Section | Value | Context |")
        md.append("|---|---|---|")
        for f in findings:
            ctx = f["context"].replace("|", "\\|")[:100]
            md.append(f"| `{f['section']}` | `{f['value']}` | {ctx} |")
    else:
        md.append("**Clean.** Every numeric in the non-strict sections "
                  "traces back to a value present in Results / "
                  "Experiments / Tables.")
    md.append("")
    (out / "verification_report.md").write_text("\n".join(md),
                                                encoding="utf-8")
    print(f"claims-registry: {len(registry)} ground-truth values; "
          f"{len(findings)} WARN findings -> {out}")
    return 0


def run_render_audit(args: argparse.Namespace) -> int:
    src = load_paper_text(args.source)
    rnd = load_paper_text(args.render)

    source_values = {_norm(m.group(1)) for m in NUMBER_RE.finditer(src)}

    unverified: list[dict[str, Any]] = []
    total = 0
    for m in NUMBER_RE.finditer(rnd):
        total += 1
        raw = m.group(1)
        v = _norm(raw)
        if v in source_values:
            continue
        # Years / rhetorical round numbers pass only in their bare form;
        # a suffixed "100x" / "10%" is a substantive claim and must
        # trace back to the source.
        if raw == v and v in TRIVIAL:
            continue
        try:
            f = float(v)
            if f == int(f) and str(int(f)) in source_values:
                continue
        except ValueError:
            pass
        unverified.append({
            "raw": v,
            "line": rnd.count("\n", 0, m.start()) + 1,
            "context": rnd[max(0, m.start() - 40):m.end() + 40]
            .replace("\n", " ").strip(),
        })

    rate = (len(unverified) / max(total, 1)) if total else 0.0
    passed = rate < args.threshold
    report = {
        "mode": "render-audit",
        "passed": passed,
        "severity": "OK" if passed else "WARN",
        "total_checked": total,
        "total_verified": total - len(unverified),
        "fabrication_rate": round(rate, 4),
        "threshold": args.threshold,
        "unverified_numbers": unverified,
        "source": args.source.name,
        "render": args.render.name,
    }
    (args.outdir / "paper_verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(f"claims-registry render-audit: {total - len(unverified)}/{total} "
          f"verified (rate={rate:.4f} threshold={args.threshold} "
          f"passed={passed})")
    return 0 if passed else 3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", type=Path,
                    help="Single-document registry mode: the manuscript "
                         "(.tex/.md/.txt/.pdf/.docx)")
    ap.add_argument("--source", type=Path,
                    help="Render-audit mode: source-of-truth document")
    ap.add_argument("--render", type=Path,
                    help="Render-audit mode: rendered artifact to check")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--strict-on",
                    default=",".join(sorted(DEFAULT_STRICT_SECTIONS)),
                    help="Comma list of ground-truth section names")
    ap.add_argument("--threshold", type=float, default=0.05,
                    help="Render-audit max fabrication rate (default 0.05)")
    # Accepted for chain-runner uniformity; this skill makes no LLM calls.
    ap.add_argument("--llm", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--journal", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--quantum-lib", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    if args.source and args.render:
        for p in (args.source, args.render):
            if not p.is_file():
                print(f"ERROR: missing input: {p}", file=sys.stderr)
                return 2
        return run_render_audit(args)
    if args.paper and args.paper.is_file():
        return run_registry(args)
    print("ERROR: pass --paper PATH (registry mode) or "
          "--source PATH --render PATH (render-audit mode)",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
