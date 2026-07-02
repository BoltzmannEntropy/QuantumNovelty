"""patent_prior_art skill — real prior-art search for the examiner panel.

QuantumNovelty's `literature_surfacer` finds ACADEMIC non-patent literature
(Crossref / arXiv / Semantic Scholar). The patent examiner (`patent_reviewer`)
also needs PATENT prior art so its § 102 / § 103 rejections are grounded in
real, named references instead of recalled-from-memory (and therefore
fabricated) citations. This skill closes that gap.

Pattern adapted from ScienceSkills' prior-art search
(ai_research_pipeline_addons/scripts/code_prior_art.py query-gen + LLM
relevance filter, and novelty_check.py::web_prior_art keyless web search):
  1. generate patent-oriented search queries from the topic/claims (LLM);
  2. query a KEYLESS patent search — Google Patents' public query endpoint,
     with a ddgs (DuckDuckGo, site:patents.google.com) fallback;
  3. dedupe by publication number;
  4. an LLM relevance pass marks which results are genuine on-topic prior art.

Output (consumable by `patent_reviewer --prior-art`):
  prior_art.json : [{publication_number, title, url, relevant, why}, ...]
  prior_art.md   : a human-readable "Prior art of record" synthesis.

Usage:
  patent_prior_art/skill.py --topic "..." [--claims FILE] [--max 20]
      [--llm claude] [--no-llm] --output DIR
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
try:
    from llm import call_llm   # noqa: E402  QN common LLM (returns LLMResult)
except Exception:              # pragma: no cover - keyless/offline fallback
    call_llm = None


def eprint(*a, **k):
    print(*a, file=sys.stderr, **k)


_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_PUB_RE = re.compile(r"\b([A-Z]{2}\d{6,}(?:[A-Z]\d?)?)\b")


def _llm_text(prompt: str, llm: str, timeout: int) -> str:
    """Call QN's common LLM and return text, tolerating both the LLMResult
    object form (QN) and a raw-string form."""
    if call_llm is None:
        return ""
    try:
        r = call_llm(prompt, backend=llm, timeout=timeout)
    except TypeError:
        r = call_llm(prompt, llm=llm, timeout=timeout)
    return getattr(r, "text", r) or ""


def gen_queries(topic: str, llm: str, use_llm: bool) -> list[str]:
    """LLM-generated patent-search queries; deterministic keyword fallback."""
    if use_llm and call_llm is not None:
        prompt = (
            "Generate 6 short prior-art SEARCH queries to find PATENTS and "
            "published patent applications that are prior art for the "
            "quantum-computing invention below. Favor the technical apparatus / "
            "method terms an examiner would search. Return ONLY a JSON array of "
            f"6 short query strings.\n\nINVENTION: {topic}\n")
        raw = _llm_text(prompt, llm, 180)
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            try:
                qs = [str(q).strip() for q in json.loads(m.group(0))
                      if str(q).strip()]
                if qs:
                    return qs[:6]
            except json.JSONDecodeError:
                pass
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9+-]{2,}", topic.lower())
             if w not in {"the", "and", "for", "with", "does", "can", "a", "an",
                          "using", "via", "into", "from", "that", "quantum"}]
    base = " ".join(words[:6])
    return [q for q in (base, " ".join(words[:4]), " ".join(words[3:9]))
            if q] or [topic[:60]]


def _walk_pubs(obj, out: dict) -> None:
    """Recursively collect {publication_number: title} from a JSON blob."""
    if isinstance(obj, dict):
        pn = obj.get("publication_number") or obj.get("patent_id")
        if isinstance(pn, str) and _PUB_RE.search(pn.replace("-", "")):
            title = (obj.get("title") or obj.get("titleText") or "").strip()
            key = pn.replace("-", "")
            if key not in out or (title and not out[key]):
                out[key] = title
        for v in obj.values():
            _walk_pubs(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk_pubs(v, out)


def gp_xhr_search(query: str, n: int = 10, timeout: int = 20) -> dict:
    """Keyless Google Patents query endpoint. Returns {pub_number: title}."""
    inner = urllib.parse.quote(f"q={query}&num={n}")
    url = f"https://patents.google.com/xhr/query?url={inner}&exp="
    req = urllib.request.Request(url, headers={"User-Agent": _UA,
                                               "Accept": "application/json"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except Exception as e:                            # noqa: BLE001
        eprint(f"WARN: Google Patents query failed for {query!r}: {e}")
        return {}
    out: dict[str, str] = {}
    _walk_pubs(data, out)
    return out


def ddg_patent_search(query: str, n: int = 10) -> dict:
    """Fallback: ddgs (DuckDuckGo) scoped to patents.google.com."""
    try:
        from ddgs import DDGS
    except Exception:
        return {}
    out: dict[str, str] = {}
    try:
        with DDGS() as d:
            for r in d.text(f"site:patents.google.com {query}", max_results=n):
                u = r.get("href") or r.get("url") or ""
                m = re.search(r"/patent/([A-Z]{2}\d{6,}[A-Z]?\d?)", u)
                if m:
                    out.setdefault(m.group(1), (r.get("title") or "").strip())
    except Exception as e:                            # noqa: BLE001
        eprint(f"WARN: ddgs patent search failed for {query!r}: {e}")
    return out


def relevance_filter(topic: str, refs: list[dict], llm: str,
                     use_llm: bool) -> list[dict]:
    if not (use_llm and call_llm is not None and refs):
        for r in refs:
            r.setdefault("relevant", True)
            r.setdefault("why", "")
        return refs
    listing = "\n".join(
        f"- {r['publication_number']}: {r.get('title', '')}" for r in refs)
    prompt = (
        "From the patents below, mark which are GENUINE on-topic prior art for "
        "the quantum-computing invention (references an examiner would cite "
        "under § 102 / § 103), with a one-line reason. Return ONLY a JSON "
        'object mapping publication_number -> {"relevant":true|false,'
        '"why":".."}.\n\n'
        f"INVENTION: {topic}\n\nPATENTS:\n{listing}\n")
    raw = _llm_text(prompt, llm, 300)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    verdicts = {}
    if m:
        try:
            verdicts = json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    for r in refs:
        v = verdicts.get(r["publication_number"], {})
        r["relevant"] = bool(v.get("relevant", True))
        r["why"] = v.get("why", "")
    return refs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topic", required=True,
                    help="invention topic / title (and key claim terms)")
    ap.add_argument("--claims", type=Path, default=None,
                    help="optional claims file; its text is appended to --topic")
    ap.add_argument("--max", type=int, default=20,
                    help="max prior-art references to keep")
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--no-llm", action="store_true",
                    help="skip LLM query-gen + relevance (keyless only)")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    use_llm = not args.no_llm

    topic = args.topic
    if args.claims and args.claims.is_file():
        topic = (topic + "\n\n"
                 + args.claims.read_text(encoding="utf-8", errors="ignore")[:4000])

    queries = gen_queries(topic, args.llm, use_llm)
    found: dict[str, str] = {}
    for q in queries:
        hits = gp_xhr_search(q, n=10) or ddg_patent_search(q, n=10)
        for pn, title in hits.items():
            if pn not in found or (title and not found[pn]):
                found[pn] = title
        time.sleep(1.5)

    refs = [{"publication_number": pn, "title": t,
             "url": f"https://patents.google.com/patent/{pn}/en"}
            for pn, t in found.items()][:args.max]
    refs = relevance_filter(args.topic, refs, args.llm, use_llm)
    relevant = [r for r in refs if r.get("relevant")]

    out = {"topic": args.topic, "queries": queries,
           "n_found": len(refs), "n_relevant": len(relevant),
           "references": refs}
    (args.output / "prior_art.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    # A flat list of relevant publication numbers — directly feedable to
    # patent_reviewer --prior-art.
    (args.output / "prior_art_refs.json").write_text(
        json.dumps([r["publication_number"] for r in relevant], indent=2),
        encoding="utf-8")

    md = ["## Prior art of record (patent search)", "",
          f"_Queries: {', '.join(queries)}_", ""]
    for r in (relevant or refs):
        md.append(f"- **{r['publication_number']}** — {r.get('title', '')}  "
                  f"\n  {r.get('why', '')}  ({r['url']})")
    (args.output / "prior_art.md").write_text("\n".join(md), encoding="utf-8")

    print(f"patent_prior_art: {len(refs)} found, {len(relevant)} relevant "
          f"-> {args.output/'prior_art_refs.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
