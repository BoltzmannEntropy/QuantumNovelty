"""patent_drafter skill driver — guided quantum-patent drafting."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402


MODES = {"guided": "filing_package.md"}

FILING_STANDARD_BLOCKS = {
    "uspto": (
        "Run the package under USPTO practice: 35 U.S.C. § 112(a)/(b), "
        "MPEP 608 formalities, title, abstract, drawings, required sections, "
        "best mode, written description, enablement, definiteness, antecedent "
        "basis, dependency clarity, and § 112(f) functional-claiming risk."
    ),
    "epo": (
        "Run the package under EPO practice: EPC Art. 84 clarity and support, "
        "two-part form where appropriate, essential features, claim category "
        "consistency, reference signs, description support, drawings, abstract, "
        "and EPO application formalities."
    ),
    "pct": (
        "Run the package under PCT practice: request/specification/claims/"
        "abstract/drawings completeness, clarity and support, dependency form, "
        "unity-relevant structure, sequence listings where applicable, and "
        "international-search readability."
    ),
    "multi": (
        "Run the package under USPTO, EPO, and PCT practice. Separately flag "
        "USPTO § 112(b) definiteness / antecedent-basis / structure issues, "
        "EPO Art. 84 clarity / support / two-part-form issues, and PCT "
        "clarity / support / required-section issues."
    ),
}


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _load_template(mode: str) -> str:
    p = HERE / "prompts" / f"{mode}.md"
    if not p.is_file():
        raise FileNotFoundError(f"prompt template not found: {p}")
    return p.read_text(encoding="utf-8")


def _load_disclosure(path: Path | None, topic: str | None) -> tuple[str, str]:
    if path:
        if not path.is_file():
            raise FileNotFoundError(f"disclosure file not found: {path}")
        return path.read_text(encoding="utf-8", errors="replace"), str(path)
    if topic:
        return topic, "topic"
    raise ValueError("patent_drafter requires --disclosure FILE or --topic STR")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", default="guided", choices=sorted(MODES))
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--disclosure", default=None, type=Path)
    ap.add_argument("--topic", default=None)
    ap.add_argument("--filing-standard", default="uspto",
                    choices=sorted(FILING_STANDARD_BLOCKS))
    ap.add_argument("--art-unit", default=None,
                    help="optional USPTO art-unit / CPC context")
    args = ap.parse_args()

    try:
        disclosure, source = _load_disclosure(args.disclosure, args.topic)
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    args.outdir.mkdir(parents=True, exist_ok=True)
    art_unit_block = (f"## Art unit / classification context\n\n{args.art_unit}"
                      if args.art_unit else
                      "_(no art-unit specified; assume quantum-computing "
                      "classification context such as CPC G06N10/00 when "
                      "appropriate)_")
    prompt = _load_template(args.mode).format_map(_SafeDict({
        "disclosure": disclosure,
        "filing_standard": args.filing_standard,
        "filing_standard_block": FILING_STANDARD_BLOCKS[args.filing_standard],
        "art_unit_block": art_unit_block,
    }))
    (args.outdir / f"full_prompt_{args.mode}.txt").write_text(
        prompt, encoding="utf-8")

    try:
        result = call_llm(prompt, backend=args.llm, timeout=2400)
    except RuntimeError as e:
        primary = args.outdir / MODES[args.mode]
        primary.write_text(
            f"# patent_drafter ({args.mode}) FAILED\n\n"
            f"Backend {args.llm} did not return output: `{e}`\n",
            encoding="utf-8")
        return 3

    primary = args.outdir / MODES[args.mode]
    primary.write_text(result.text, encoding="utf-8")
    manifest = {
        "skill": "patent_drafter",
        "mode": args.mode,
        "filing_standard": args.filing_standard,
        "source": source,
        "output": primary.name,
        "expected_sections": [
            "Intake Summary",
            "Prior-Art Search Plan",
            "Claim Strategy",
            "Draft Claims",
            "Claim Compliance Review",
            "Full Application Review",
            "Filing Handoff Checklist",
        ],
    }
    (args.outdir / "package_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    (args.outdir / "_raw_response_guided.txt").write_text(
        result.text, encoding="utf-8")
    (args.outdir / "_llm_generation.log").write_text(
        f"--- mode: {args.mode} ---\n"
        f"--- filing_standard: {args.filing_standard} ---\n"
        f"--- backend: {result.backend_actually_used} ---\n"
        f"--- elapsed_s: {result.elapsed_s:.2f} ---\n"
        f"--- stdout (first 4KB) ---\n{result.text[:4000]}\n",
        encoding="utf-8")
    write_backend_marker(args.outdir, result)
    print(f"patent_drafter[{args.mode}]: wrote {primary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
