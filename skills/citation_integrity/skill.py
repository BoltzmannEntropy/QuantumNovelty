"""citation_integrity — 4-layer citation verifier. No LLM calls, no RAG.

Adapted from AutoResearchClaw's stage-23 verification_report.json schema.

Four layers, run in order:

  Layer 1 — Bibkey resolution. Every ``\\cite{KEY}`` in the manuscript
            must have a matching ``@type{KEY, ...}`` entry in the .bib.
            Missing -> ``hallucinated``.

  Layer 2 — Entry completeness. Each cited entry must have
            author/title/year. Missing fields -> ``suspicious``.

  Layer 3 — DOI / title resolvability via CrossRef (HTTP only; no
            knowledge base). DOI 404 -> ``hallucinated``; title mismatch
            -> ``suspicious``; transient network failure -> ``skipped``
            (never counted as hallucinated).

  Layer 4 — Relevance score: token overlap between the entry title and
            the manuscript vocabulary, 0..1, non-gating.

Output: verification_report.json with
``summary.integrity_score = verified / total``.

Usage:
  skill.py --paper PATH --bib PATH --outdir DIR [--no-network] [--timeout 8]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

USER_AGENT = "QuantumNovelty-citation-integrity/1.0"

CITE_RE = re.compile(r"\\cite[a-z]*\*?\{([^}]+)\}")
BIB_ENTRY_RE = re.compile(
    r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)(?=^@|\Z)",
    re.DOTALL | re.MULTILINE,
)


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for m in BIB_ENTRY_RE.finditer(text):
        fields: dict[str, str] = {"_type": m.group(1).lower()}
        for fm in re.finditer(
            r"(\w+)\s*=\s*[\{\"](.+?)[\}\"](?:\s*,|\s*\Z|\s*\n)",
            m.group(3), re.DOTALL,
        ):
            fields[fm.group(1).lower()] = fm.group(2).strip()
        entries[m.group(2).strip()] = fields
    return entries


def collect_cite_keys(text: str) -> list[str]:
    keys: list[str] = []
    for m in CITE_RE.finditer(text):
        keys.extend(k.strip() for k in m.group(1).split(",") if k.strip())
    return keys


def crossref_lookup(doi: str, timeout: int) -> tuple[dict | None, str]:
    """Returns (record, status); status in ok/not_found/network/parse.

    Distinguishing "DOI does not exist" (404) from "the network was
    down" matters: a transient failure must never be reported as a
    hallucinated citation.
    """
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            try:
                data = json.loads(r.read().decode("utf-8"))
            except json.JSONDecodeError:
                return None, "parse"
            return (data.get("message") or None,
                    "ok" if data.get("message") else "not_found")
    except urllib.error.HTTPError as e:
        return None, ("not_found" if e.code == 404 else "network")
    except Exception:
        return None, "network"


def title_similarity(a: str, b: str) -> float:
    def toks(s: str) -> set[str]:
        return {t for t in re.findall(r"\w+", s.lower()) if len(t) >= 3}
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(min(len(ta), len(tb)), 1)


def relevance_score(title: str, manuscript_text: str) -> float:
    def toks(s: str) -> set[str]:
        return {t for t in re.findall(r"\w+", s.lower()) if len(t) >= 5}
    title_toks = toks(title)
    if not title_toks:
        return 0.0
    return round(len(title_toks & toks(manuscript_text))
                 / max(len(title_toks), 1), 2)


def verify_one(key: str, entry: dict[str, str], host_text: str,
               no_network: bool, timeout: int) -> dict[str, Any]:
    title = entry.get("title", "")
    doi = entry.get("doi", "")
    result: dict[str, Any] = {
        "cite_key": key,
        "title": title,
        "status": "verified",
        "confidence": 1.0,
        "method": "unknown",
        "details": "",
        "relevance_score": relevance_score(title, host_text),
    }

    missing = [f for f in ("author", "title", "year") if not entry.get(f)]
    if missing:
        result.update(status="suspicious", confidence=0.6,
                      method="completeness",
                      details=f"Missing fields: {', '.join(missing)}")
        return result

    if no_network:
        result.update(method="offline", confidence=0.8,
                      details="Verified via bibkey+completeness "
                              "(network skipped)")
        return result

    if doi:
        clean_doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi.strip())
        meta, status = crossref_lookup(clean_doi, timeout)
        if status == "ok" and meta:
            cr_title = (meta.get("title") or [""])[0] or ""
            sim = title_similarity(title, cr_title)
            if sim >= 0.5:
                result.update(method="doi", confidence=1.0,
                              details=f"Confirmed via CrossRef: '{cr_title}'")
            else:
                result.update(status="suspicious", confidence=0.5,
                              method="doi_title_mismatch",
                              details=f"DOI resolves but CrossRef title "
                                      f"'{cr_title}' differs "
                                      f"(similarity={sim:.2f})")
        elif status == "not_found":
            result.update(status="hallucinated", confidence=0.2,
                          method="doi_unresolved",
                          details=f"DOI {clean_doi} did not resolve via "
                                  f"CrossRef (404)")
        else:
            result.update(status="skipped", confidence=0.0,
                          method=f"crossref_{status}",
                          details=f"CrossRef lookup for DOI {clean_doi} "
                                  f"could not complete ({status}); retry "
                                  f"when network is available")
        return result

    if title:
        url_q = ("https://api.crossref.org/works?query.title="
                 f"{urllib.parse.quote(title)}&rows=3")
        req = urllib.request.Request(url_q,
                                     headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            items = (data.get("message") or {}).get("items") or []
            best_sim, best_hit = 0.0, ""
            for it in items:
                t = (it.get("title") or [""])[0] or ""
                sim = title_similarity(title, t)
                if sim > best_sim:
                    best_sim, best_hit = sim, t
            if best_sim >= 0.7:
                result.update(method="title_search", confidence=0.9,
                              details=f"Title-search hit '{best_hit}' "
                                      f"(sim={best_sim:.2f})")
            elif best_sim >= 0.4:
                result.update(status="suspicious", confidence=0.5,
                              method="title_partial",
                              details=f"Partial title match '{best_hit}' "
                                      f"(sim={best_sim:.2f})")
            else:
                result.update(status="suspicious", confidence=0.3,
                              method="no_match",
                              details="No high-similarity CrossRef "
                                      "title match")
        except Exception as e:
            result.update(status="skipped", confidence=0.5,
                          method="lookup_failed",
                          details=f"CrossRef lookup failed: {e}")
    else:
        result.update(status="suspicious", confidence=0.4,
                      method="no_title_no_doi",
                      details="Entry has neither title nor DOI")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", required=True, type=Path,
                    help="Manuscript (.tex/.md) containing \\cite{KEY}")
    ap.add_argument("--bib", required=True, type=Path,
                    help="BibTeX file with @entry{KEY, ...}")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--no-network", action="store_true",
                    help="Skip layer 3 (CrossRef) — offline/test mode")
    ap.add_argument("--timeout", type=int, default=8)
    ap.add_argument("--sleep", type=float, default=0.1,
                    help="Pause between CrossRef calls (rate limits)")
    # Accepted for chain-runner uniformity; this skill makes no LLM calls.
    ap.add_argument("--llm", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--journal", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--quantum-lib", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    for p in (args.paper, args.bib):
        if not p.is_file():
            print(f"ERROR: missing input: {p}", file=sys.stderr)
            return 2
    args.outdir.mkdir(parents=True, exist_ok=True)

    paper = args.paper.read_text(encoding="utf-8", errors="ignore")
    entries = parse_bib(args.bib.read_text(encoding="utf-8",
                                           errors="ignore"))
    cited = sorted(set(collect_cite_keys(paper)))
    if not cited:
        print("WARNING: no \\cite{...} commands found — the --paper input "
              "must be LaTeX/markdown source, not a compiled PDF",
              file=sys.stderr)

    results: list[dict[str, Any]] = []
    counts = {"verified": 0, "suspicious": 0, "hallucinated": 0,
              "skipped": 0}
    for k in cited:
        if k not in entries:
            results.append({
                "cite_key": k, "title": "", "status": "hallucinated",
                "confidence": 0.0, "method": "bibkey_unresolved",
                "details": "Cited key has no @entry in the .bib file",
                "relevance_score": 0.0,
            })
            counts["hallucinated"] += 1
            continue
        r = verify_one(k, entries[k], paper, args.no_network, args.timeout)
        results.append(r)
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        if not args.no_network:
            time.sleep(args.sleep)

    total = len(cited)
    integrity = (counts["verified"] / max(total, 1)) if total else 0.0
    report = {
        "summary": {
            "total": total,
            **counts,
            "integrity_score": round(integrity, 4),
        },
        "results": results,
        "paper": args.paper.name,
        "bib": args.bib.name,
        "network_used": not args.no_network,
    }
    out = args.outdir / "verification_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"citation-integrity: verified={counts['verified']} "
          f"suspicious={counts['suspicious']} "
          f"hallucinated={counts['hallucinated']} "
          f"skipped={counts['skipped']} integrity={integrity:.4f} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
