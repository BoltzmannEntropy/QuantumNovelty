"""literature_surfacer skill — real runtime.

Multi-source HTTP-only literature pull (CrossRef + arXiv + Semantic Scholar),
followed by an LLM extractor that drafts a synthesis + a structured
baseline_catalog.json that `novelty_audit` will merge with the user's
Pareto archive.

NO RAG. NO indexing. Every query hits the live sources. Failed sources
degrade individually (we don't fail the whole call if one source is down).

Required env (all optional):
  SERPER_KEY        — enables Google Scholar via Serper.dev (else skipped)

Network failures are returned as structured per-source status, not raised.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker  # noqa: E402


DEFAULT_UA = ("QuantumNovelty/0.1 (literature-surfacer; "
              "mailto:please-set-your-email@example.org)")
DEFAULT_TIMEOUT = 30


# =========================================================================
# Per-source clients
# =========================================================================

@dataclass
class SourceHit:
    title: str
    authors: list[str]
    year: str
    venue: str
    doi: str | None
    arxiv_id: str | None
    abstract: str
    source: str            # "crossref" | "arxiv" | "semantic_scholar" | ...
    cited_by: int | None = None
    url: str | None = None


def _fetch_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[dict | None, str]:
    """Return (data, status). status ∈ {ok, network, parse, not_found}."""
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            try:
                return json.loads(r.read().decode("utf-8")), "ok"
            except json.JSONDecodeError:
                return None, "parse"
    except urllib.error.HTTPError as e:
        return None, "not_found" if e.code == 404 else "network"
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, "network"


def search_crossref(query: str, n: int = 10) -> tuple[list[SourceHit], str]:
    qs = urllib.parse.urlencode({"query": query, "rows": n,
                                  "select": ("DOI,title,author,issued,"
                                              "container-title,abstract,"
                                              "is-referenced-by-count,URL")})
    data, status = _fetch_json(f"https://api.crossref.org/works?{qs}")
    if status != "ok":
        return [], status
    out: list[SourceHit] = []
    for item in (data or {}).get("message", {}).get("items", []):
        out.append(SourceHit(
            title=(item.get("title") or [""])[0],
            authors=[
                f"{a.get('given','')} {a.get('family','')}".strip()
                for a in item.get("author") or []
            ],
            year=str((item.get("issued", {}).get("date-parts")
                      or [[""]])[0][0] or ""),
            venue=(item.get("container-title") or [""])[0],
            doi=item.get("DOI"),
            arxiv_id=None,
            abstract=item.get("abstract", "") or "",
            source="crossref",
            cited_by=item.get("is-referenced-by-count"),
            url=item.get("URL"),
        ))
    return out, "ok"


def search_arxiv(query: str, n: int = 10) -> tuple[list[SourceHit], str]:
    qs = urllib.parse.urlencode({"search_query": f"all:{query}",
                                  "start": 0, "max_results": n,
                                  "sortBy": "relevance"})
    url = f"http://export.arxiv.org/api/query?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError,
            TimeoutError, OSError):
        return [], "network"
    # Minimal XML parse without bringing in lxml — arxiv emits Atom-style XML.
    import re
    entries = re.findall(r"<entry>(.*?)</entry>", raw, re.DOTALL)
    out: list[SourceHit] = []
    for e in entries[:n]:
        title = re.search(r"<title>(.*?)</title>", e, re.DOTALL)
        summary = re.search(r"<summary>(.*?)</summary>", e, re.DOTALL)
        published = re.search(r"<published>(.*?)</published>", e)
        arxiv_id = re.search(r"<id>http[s]?://arxiv\.org/abs/(.*?)(?:v\d+)?</id>", e)
        authors = re.findall(r"<author><name>(.*?)</name>", e)
        out.append(SourceHit(
            title=(title.group(1) if title else "").strip(),
            authors=authors,
            year=(published.group(1)[:4] if published else ""),
            venue="arXiv",
            doi=None,
            arxiv_id=arxiv_id.group(1) if arxiv_id else None,
            abstract=(summary.group(1) if summary else "").strip(),
            source="arxiv",
            cited_by=None,
            url=f"https://arxiv.org/abs/{arxiv_id.group(1)}" if arxiv_id else None,
        ))
    return out, "ok"


def search_semantic_scholar(query: str, n: int = 10) -> tuple[list[SourceHit], str]:
    qs = urllib.parse.urlencode({
        "query": query, "limit": n,
        "fields": "title,authors,year,venue,externalIds,abstract,citationCount,url",
    })
    data, status = _fetch_json(
        f"https://api.semanticscholar.org/graph/v1/paper/search?{qs}"
    )
    if status != "ok":
        return [], status
    out: list[SourceHit] = []
    for p in (data or {}).get("data", []):
        out.append(SourceHit(
            title=p.get("title") or "",
            authors=[a.get("name", "") for a in p.get("authors") or []],
            year=str(p.get("year") or ""),
            venue=p.get("venue") or "",
            doi=(p.get("externalIds") or {}).get("DOI"),
            arxiv_id=(p.get("externalIds") or {}).get("ArXiv"),
            abstract=p.get("abstract") or "",
            source="semantic_scholar",
            cited_by=p.get("citationCount"),
            url=p.get("url"),
        ))
    return out, "ok"


def search_serper_scholar(query: str, n: int = 10) -> tuple[list[SourceHit], str]:
    """Google Scholar via Serper.dev. Skipped without SERPER_KEY."""
    key = os.environ.get("SERPER_KEY")
    if not key:
        return [], "no_key"
    body = json.dumps({"q": query, "num": n}).encode("utf-8")
    req = urllib.request.Request(
        "https://google.serper.dev/scholar",
        data=body,
        headers={"X-API-KEY": key, "Content-Type": "application/json",
                 "User-Agent": DEFAULT_UA},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError,
            TimeoutError, json.JSONDecodeError, OSError):
        return [], "network"
    out: list[SourceHit] = []
    for p in data.get("organic", []):
        out.append(SourceHit(
            title=p.get("title") or "",
            authors=[],
            year=(p.get("year") or ""),
            venue=p.get("publicationInfo", "") or "",
            doi=None,
            arxiv_id=None,
            abstract=p.get("snippet") or "",
            source="serper_scholar",
            cited_by=p.get("citedBy", {}).get("total") if isinstance(
                p.get("citedBy"), dict) else None,
            url=p.get("link"),
        ))
    return out, "ok"


# =========================================================================
# Card extraction + synthesis
# =========================================================================

def dedupe_hits(hits: list[SourceHit]) -> list[SourceHit]:
    """Merge dup hits by DOI/arxiv_id; keep the one with most metadata."""
    by_key: dict[str, SourceHit] = {}
    for h in hits:
        key = (h.doi or h.arxiv_id
               or f"{h.title.lower().strip()}-{h.year}")
        if key not in by_key:
            by_key[key] = h
        else:
            # Prefer the hit with a DOI / abstract / citation count.
            cur = by_key[key]
            score_new = sum(bool(x) for x in
                            (h.doi, h.abstract, h.cited_by))
            score_cur = sum(bool(x) for x in
                            (cur.doi, cur.abstract, cur.cited_by))
            if score_new > score_cur:
                by_key[key] = h
    return list(by_key.values())


def hit_to_card(h: SourceHit) -> dict:
    return {
        "title": h.title,
        "authors": h.authors,
        "year": h.year,
        "venue": h.venue,
        "doi": h.doi,
        "arxiv_id": h.arxiv_id,
        "abstract": h.abstract[:1000],
        "source": h.source,
        "cited_by": h.cited_by,
        "url": h.url,
    }


SYNTHESIS_PROMPT = """# literature_surfacer — synthesis stage

You are surveying recent published work on a quantum-computing topic. The
candidate cards below were pulled fresh from CrossRef + arXiv + Semantic
Scholar + (optionally) Google Scholar.

## Topic
{topic}

{context}

## Candidate cards
```json
{cards}
```

## Required deliverables

### 1. Synthesis (~600 words connected prose)
Cover: current state of the art (cite Author Year) + open problems +
methodological norms. Stay grounded in the cards above — do NOT invent
citations.

### 2. baseline_catalog (single fenced ```json block, this exact key)
Per-row schema (lower-is-better metrics):
```json
{{
  "rows": [
    {{
      "label": "AuthorYear-Method",
      "energy_ha": <float or null>,
      "params":    <int or null>,
      "ops":       <int or null>,
      "cnots":     <int or null>,
      "source":    "literature",
      "citation":  "Author et al. (Year). Title. Venue."
    }}
  ]
}}
```
Include rows ONLY for papers reporting numerical values from the cards.
Skip rows where the system size does not match the user's --hamiltonian-id.
Use null for values not present in the card; do NOT guess.

## Constraints
- Cite Author Year only.
- Distinguish peer-reviewed venues from preprint (`venue="arXiv"`).
- If no card matches the user's Hamiltonian context closely, return an
  empty `rows` array — empty catalogs are valid output.
"""


def llm_synthesize(topic: str, cards: list[dict],
                   context: str, llm: str) -> tuple[str, dict]:
    """Returns (synthesis_md, baseline_catalog)."""
    prompt = SYNTHESIS_PROMPT.format(
        topic=topic,
        context=context or "_(no extra context)_",
        cards=json.dumps(cards[:30], indent=2)[:20000],
    )
    try:
        result = call_llm(prompt, backend=llm, timeout=600)
    except RuntimeError as e:
        return (
            f"# ⚠ literature_surfacer synthesis FAILED\n\n"
            f"Backend {llm}: `{e}`\n\nCards above are the surfaced data; "
            "synthesis prose is empty until you re-run with a working backend.\n",
            {"rows": []},
            None,
        )
    # Extract the baseline_catalog JSON block. The model may echo the
    # schema (which doesn't parse) or other json snippets first — scan
    # every block and take the first that parses AND carries "rows".
    import re
    catalog = {"rows": []}
    for blob in re.findall(r"```json\s*(\{.*?\})\s*```",
                            result.text, re.DOTALL):
        try:
            obj = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "rows" in obj:
            catalog = obj
            break
    return result.text, catalog, result


# =========================================================================
# Main
# =========================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topic", required=True)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--n", type=int, default=10,
                    help="hits per source (default 10)")
    ap.add_argument("--sources", default="crossref,arxiv,semantic_scholar,serper",
                    help="comma list; default: crossref,arxiv,semantic_scholar,serper")
    ap.add_argument("--hamiltonian-id", default=None)
    ap.add_argument("--journal", default=None)
    ap.add_argument("--quantum-lib", default=None)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    sources_requested = [s.strip() for s in args.sources.split(",") if s.strip()]
    source_fns = {
        "crossref": search_crossref,
        "arxiv": search_arxiv,
        "semantic_scholar": search_semantic_scholar,
        "serper": search_serper_scholar,
    }
    per_source_status: dict[str, str] = {}
    all_hits: list[SourceHit] = []
    cards_dir = args.outdir / "cards"
    cards_dir.mkdir(exist_ok=True)
    for src in sources_requested:
        fn = source_fns.get(src)
        if not fn:
            per_source_status[src] = "unknown_source"
            continue
        hits, status = fn(args.topic, args.n)
        per_source_status[src] = f"{status} ({len(hits)} hits)"
        all_hits.extend(hits)
        # Persist raw per-source results
        (cards_dir / f"_{src}_raw.json").write_text(
            json.dumps([h.__dict__ for h in hits], indent=2),
            encoding="utf-8")
        time.sleep(0.5)  # polite delay between sources

    deduped = dedupe_hits(all_hits)
    cards = [hit_to_card(h) for h in deduped]
    (args.outdir / "candidates.json").write_text(
        json.dumps({
            "topic": args.topic,
            "n_total": len(all_hits),
            "n_deduped": len(cards),
            "per_source_status": per_source_status,
            "cards": cards,
        }, indent=2), encoding="utf-8")

    # Build the synthesis-context block.
    ctx_parts = []
    if args.hamiltonian_id:
        ctx_parts.append(f"## Hamiltonian context\n\n- ID: `{args.hamiltonian_id}`")
    if args.journal:
        ctx_parts.append(f"## Target journal slug: `{args.journal}`")
    if args.quantum_lib:
        ctx_parts.append(f"## Target quantum library: `{args.quantum_lib}`")
    context = "\n\n".join(ctx_parts)

    synthesis_md, catalog, llm_result = llm_synthesize(
        args.topic, cards, context, args.llm
    )
    (args.outdir / "synthesis.md").write_text(synthesis_md, encoding="utf-8")
    (args.outdir / "baseline_catalog.json").write_text(
        json.dumps(catalog, indent=2), encoding="utf-8")

    # Provenance marker — written from the REAL LLMResult only. A
    # fabricated marker would defeat the backend-fidelity audit; on
    # synthesis failure no marker is written, which audits as missing.
    if llm_result is not None:
        write_backend_marker(args.outdir, llm_result)

    print(f"literature_surfacer: sources={list(per_source_status.keys())}, "
          f"{len(all_hits)} hits → {len(cards)} unique → "
          f"{len(catalog.get('rows', []))} baseline rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
