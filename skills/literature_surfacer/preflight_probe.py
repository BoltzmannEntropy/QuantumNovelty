"""preflight_probe — retrieval pre-flight gate for novelty_audit.

Runs a set of known-answer probe queries against the live literature
sources and reports per-probe hit rates. Designed to surface
misconfigured or network-degraded retrieval BEFORE the audit invests
in a full literature pull.

Usage:
  python3 preflight_probe.py --probes FILE --outdir DIR [OPTIONS]

Output: <outdir>/probe_result.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
# Sibling import: add our own directory so we can import skill.py directly.
sys.path.insert(0, str(HERE))

# Import source functions from the sibling skill module.
# We do NOT call them at import time — they are injectable for tests.
import importlib.util as _ilu  # noqa: E402

# Load the sibling skill.py by absolute path so the import is unambiguous
# regardless of how sys.path is ordered (e.g. when running under pytest with
# multiple skill dirs on the path).
# We must register the module in sys.modules BEFORE exec_module so that
# @dataclass decorators (which look up cls.__module__ via sys.modules) work.
_SURF_MOD_NAME = "literature_surfacer_skill"
_surf_skill_path = HERE / "skill.py"
_surf_spec = _ilu.spec_from_file_location(_SURF_MOD_NAME, _surf_skill_path)
_surf_mod = _ilu.module_from_spec(_surf_spec)
sys.modules[_SURF_MOD_NAME] = _surf_mod
_surf_spec.loader.exec_module(_surf_mod)

search_crossref         = _surf_mod.search_crossref
search_arxiv            = _surf_mod.search_arxiv
search_semantic_scholar = _surf_mod.search_semantic_scholar
search_serper_scholar   = _surf_mod.search_serper_scholar
dedupe_hits             = _surf_mod.dedupe_hits
hit_to_card             = _surf_mod.hit_to_card

# =========================================================================
# Probe matching logic (pure — no I/O, fully testable)
# =========================================================================

_ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}$")


def _normalize_arxiv_id(s: str) -> str:
    """Strip trailing version suffix, e.g. '1803.11173v2' -> '1803.11173'."""
    return re.sub(r"v\d+$", "", s.strip())


def card_matches_expected(card: dict, expected_entry: str) -> bool:
    """Return True if `expected_entry` matches this card.

    Matching rule (single function, no branching on type):
      case-insensitive substring search over:
        title + " " + (arxiv_id or "") + " " + (doi or "")
    This handles both human-readable author-year phrases AND bare arXiv IDs.
    """
    haystack = " ".join([
        (card.get("title") or ""),
        (card.get("arxiv_id") or ""),
        (card.get("doi") or ""),
    ]).lower()
    return expected_entry.lower() in haystack


def score_probe(cards: list[dict], expected: list[str]) -> bool:
    """Return True iff at least one card matches at least one expected entry."""
    for entry in expected:
        for card in cards:
            if card_matches_expected(card, entry):
                return True
    return False


# =========================================================================
# Main probe runner (fetch function is injectable for tests)
# =========================================================================

SourceFnMap = dict[str, Callable[[str, int], tuple[list, str]]]

_DEFAULT_SOURCE_FNS: SourceFnMap = {
    "crossref": search_crossref,
    "arxiv": search_arxiv,
    "semantic_scholar": search_semantic_scholar,
    "serper": search_serper_scholar,
}


def run_probes(
    probes: list[dict],
    *,
    sources: list[str] | None = None,
    max_cards: int = 40,
    source_fns: SourceFnMap | None = None,
    threshold: float = 0.67,
) -> dict:
    """Run all probes and return the probe_result dict.

    Parameters
    ----------
    probes:
        List of {"query": str, "expected": [str, ...]} dicts.
    sources:
        Which source keys to query. Defaults to all four.
    max_cards:
        Cap on deduplicated cards per probe.
    source_fns:
        Injectable map of source_name -> fn(query, n) -> (hits, status).
        Defaults to the live network functions.
    threshold:
        Minimum recall fraction to consider the gate passed.
    """
    fns = source_fns if source_fns is not None else _DEFAULT_SOURCE_FNS
    active_sources = sources if sources else list(fns.keys())
    n_per_source = max(1, max_cards // max(len(active_sources), 1))

    probe_results = []
    n_hit = 0
    for probe in probes:
        query = probe["query"]
        expected = probe.get("expected", [])
        all_hits = []
        per_source_status: dict[str, str] = {}
        for src in active_sources:
            fn = fns.get(src)
            if fn is None:
                per_source_status[src] = "unknown_source"
                continue
            hits, status = fn(query, n_per_source)
            per_source_status[src] = f"{status} ({len(hits)} hits)"
            all_hits.extend(hits)
        deduped = dedupe_hits(all_hits)[:max_cards]
        cards = [hit_to_card(h) for h in deduped]
        hit = score_probe(cards, expected)
        if hit:
            n_hit += 1
        probe_results.append({
            "query": query,
            "expected": expected,
            "hit": hit,
            "n_cards": len(cards),
            "per_source_status": per_source_status,
        })

    n_probes = len(probes)
    recall = n_hit / n_probes if n_probes > 0 else 0.0
    return {
        "probes": probe_results,
        "recall": recall,
        "passed": recall >= threshold,
        "threshold": threshold,
        "n_hit": n_hit,
        "n_probes": n_probes,
    }


# =========================================================================
# CLI
# =========================================================================

_DEFAULT_PROBES_PATH = HERE / "probes_quantum_default.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--probes", type=Path, default=None,
        help=f"JSON file with probe list. Default: {_DEFAULT_PROBES_PATH}",
    )
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument(
        "--max-cards", type=int, default=40,
        help="Max deduplicated cards to fetch per probe (default 40)",
    )
    ap.add_argument(
        "--sources", default="crossref,arxiv,semantic_scholar,serper",
        help="Comma list of sources to query (default: crossref,arxiv,semantic_scholar,serper)",
    )
    ap.add_argument(
        "--threshold", type=float, default=0.67,
        help="Minimum recall fraction to pass (default 0.67)",
    )
    args = ap.parse_args()

    probes_path = args.probes or _DEFAULT_PROBES_PATH
    if not probes_path.is_file():
        print(f"ERROR: probes file not found: {probes_path}", file=sys.stderr)
        return 2

    probes = json.loads(probes_path.read_text(encoding="utf-8"))
    if not isinstance(probes, list):
        print("ERROR: probes file must be a JSON array of probe objects",
              file=sys.stderr)
        return 2

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    args.outdir.mkdir(parents=True, exist_ok=True)

    result = run_probes(
        probes,
        sources=sources,
        max_cards=args.max_cards,
        threshold=args.threshold,
    )

    out_path = args.outdir / "probe_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    status = "PASSED" if result["passed"] else "FAILED"
    print(
        f"preflight_probe: {result['n_hit']}/{result['n_probes']} probes hit "
        f"(recall={result['recall']:.2f}, threshold={result['threshold']:.2f}) "
        f"→ {status}"
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
