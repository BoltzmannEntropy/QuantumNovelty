"""Anna's Archive client for QuantumNovelty's book_acquirer skill.

When the literature_surfacer encounters a citation it cannot resolve through
CrossRef / arXiv / Semantic Scholar (typical for books, theses, conference
proceedings, and older preprints), it hands the unresolved citations to this
module, which searches Anna's Archive and downloads candidates.

Design constraints:
  - Set ANNAS_ARCHIVE_KEY in env for download (free key from
    https://annas-archive.org/donate). Without a key, we only search.
  - Single hardcoded mirror by default (annas-archive.gl); override with
    QN_ANNAS_MIRROR env var if you have a different mirror configured.
  - Rate-limited: default 1 req/s. Override with QN_ANNAS_RATE_SECONDS.
  - Network failures are returned as structured results, NOT raised — the
    caller decides whether to retry or give up. (Contrast with API-billing
    failures, which are always raised.)

No external dependencies beyond stdlib (urllib + json + re + time).
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


DEFAULT_MIRROR = os.environ.get("QN_ANNAS_MIRROR", "https://annas-archive.gl")
DEFAULT_RATE_SECONDS = float(os.environ.get("QN_ANNAS_RATE_SECONDS", "1.0"))
DEFAULT_TIMEOUT = 30
DEFAULT_UA = ("QuantumNovelty/0.1 (book-acquirer; "
              "+https://github.com/your-org/QuantumNovelty)")


# =========================================================================
# Data classes
# =========================================================================

@dataclass
class SearchHit:
    """One Anna's Archive search hit."""
    md5: str
    title: str
    author: str
    year: str
    extension: str
    size_bytes: int
    language: str
    raw_url: str

    def file_basename(self) -> str:
        """A safe filename for the downloaded artefact."""
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_",
                      f"{self.title[:60]}_{self.author[:30]}_{self.year}")
        return f"{safe.strip('_')}.{self.extension}"


@dataclass
class DownloadResult:
    """Outcome of a single download attempt."""
    md5: str
    status: str                  # "ok" | "no_key" | "network" | "skipped" | "error"
    path: Path | None = None
    bytes_written: int = 0
    error: str = ""


@dataclass
class AcquireReport:
    """Per-query acquisition report."""
    query: str
    search_status: str
    n_hits: int
    downloads: list[DownloadResult] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps({
            "query": self.query,
            "search_status": self.search_status,
            "n_hits": self.n_hits,
            "downloads": [
                {"md5": d.md5, "status": d.status,
                 "path": str(d.path) if d.path else None,
                 "bytes_written": d.bytes_written,
                 "error": d.error}
                for d in self.downloads
            ],
        }, indent=2)


# =========================================================================
# Public API
# =========================================================================

def search(query: str,
           limit: int = 5,
           lang: str = "en",
           mirror: str = DEFAULT_MIRROR,
           timeout: int = DEFAULT_TIMEOUT) -> tuple[str, list[SearchHit]]:
    """Search Anna's Archive for `query`. Returns (status, hits).

    status ∈ {"ok", "no_results", "network", "parse"} — same vocabulary as
    citation_integrity, so the chain's quality gates can treat them uniformly.

    Anna's Archive does not have a documented JSON search API, so we scrape
    the public HTML search page. The selectors below are intentionally narrow
    so an upstream HTML change fails loudly (parse status), rather than
    silently returning empty results.
    """
    qs = urllib.parse.urlencode({"q": query, "lang": lang})
    url = f"{mirror}/search?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            html = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError:
        return "network", []
    except (urllib.error.URLError, TimeoutError, OSError):
        return "network", []

    hits = _parse_search_html(html, mirror=mirror, limit=limit)
    if not hits:
        # Distinguish "site responded but no results" from "parse failure".
        # If we see the search-form skeleton but no hits, it's no_results.
        if 'name="q"' in html:
            return "no_results", []
        return "parse", []
    return "ok", hits


def download(hit: SearchHit,
             target_dir: Path,
             api_key: str | None = None,
             mirror: str = DEFAULT_MIRROR,
             timeout: int = DEFAULT_TIMEOUT) -> DownloadResult:
    """Download one search hit to `target_dir`.

    Requires an Anna's Archive API key in `api_key` or env `ANNAS_ARCHIVE_KEY`.
    Without a key, returns status="no_key" without raising.
    """
    api_key = api_key or os.environ.get("ANNAS_ARCHIVE_KEY")
    target_dir.mkdir(parents=True, exist_ok=True)
    if not api_key:
        return DownloadResult(md5=hit.md5, status="no_key",
                              error="ANNAS_ARCHIVE_KEY env var not set")
    out_path = target_dir / hit.file_basename()
    if out_path.exists() and out_path.stat().st_size > 0:
        return DownloadResult(md5=hit.md5, status="skipped",
                              path=out_path,
                              bytes_written=out_path.stat().st_size,
                              error="file already on disk")
    dl_url = f"{mirror}/dyn/api/fast_download.json?md5={hit.md5}&key={api_key}"
    req = urllib.request.Request(dl_url, headers={"User-Agent": DEFAULT_UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return DownloadResult(md5=hit.md5, status="network",
                              error=f"HTTP {e.code}: {e.reason}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return DownloadResult(md5=hit.md5, status="network", error=str(e))
    except json.JSONDecodeError as e:
        return DownloadResult(md5=hit.md5, status="error",
                              error=f"non-JSON download response: {e}")

    direct_url = data.get("download_url") or data.get("url")
    if not direct_url:
        return DownloadResult(
            md5=hit.md5, status="error",
            error=f"no download URL in response: {list(data.keys())}"
        )

    # Download the actual file.
    try:
        req2 = urllib.request.Request(direct_url,
                                      headers={"User-Agent": DEFAULT_UA})
        # Stream to a .part file and rename on success — a mid-stream
        # failure must not leave a truncated file that the size>0 cache
        # check would treat as already-downloaded forever after.
        part_path = out_path.with_suffix(out_path.suffix + ".part")
        try:
            with urllib.request.urlopen(req2, timeout=timeout * 4) as r:
                with open(part_path, "wb") as f:
                    while True:
                        chunk = r.read(64 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
            part_path.replace(out_path)
        except Exception:
            part_path.unlink(missing_ok=True)
            raise
        return DownloadResult(
            md5=hit.md5, status="ok",
            path=out_path,
            bytes_written=out_path.stat().st_size,
        )
    except Exception as e:
        return DownloadResult(md5=hit.md5, status="network",
                              error=f"file fetch failed: {e}")


def acquire(queries: Iterable[str],
            target_dir: Path,
            api_key: str | None = None,
            max_downloads_per_query: int = 1,
            rate_seconds: float = DEFAULT_RATE_SECONDS) -> list[AcquireReport]:
    """High-level driver: search + download for a list of queries.

    Politely rate-limits between requests. Returns one AcquireReport per query.
    Failure of any single query does NOT abort the batch — the report records
    the failure and the loop continues.
    """
    reports: list[AcquireReport] = []
    for q in queries:
        status, hits = search(q)
        report = AcquireReport(query=q, search_status=status,
                               n_hits=len(hits))
        for hit in hits[:max_downloads_per_query]:
            time.sleep(rate_seconds)
            d = download(hit, target_dir, api_key=api_key)
            report.downloads.append(d)
        reports.append(report)
        time.sleep(rate_seconds)
    return reports


# =========================================================================
# HTML parser (narrow selectors so upstream changes fail loudly)
# =========================================================================

# Anna's Archive search result rows carry an MD5 in the href, plus enough
# metadata to surface a usable hit. These regexes are intentionally narrow.
_HIT_RE = re.compile(
    r'<a[^>]+href="/md5/(?P<md5>[a-f0-9]{32})"[^>]*>'
    r'(?P<body>.*?)</a>',
    re.DOTALL | re.IGNORECASE,
)
_TITLE_RE = re.compile(r'<h3[^>]*>(.*?)</h3>', re.DOTALL | re.IGNORECASE)
_META_RE = re.compile(
    r'(?P<lang>\w{2,3}),?\s*(?P<ext>pdf|epub|djvu|mobi|azw3|cbz|cbr),?'
    r'\s*(?P<size>[\d.]+\s*[KMG]B)',
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r'\b(1[89]\d{2}|20[0-3]\d)\b')


def _parse_search_html(html: str, mirror: str,
                       limit: int) -> list[SearchHit]:
    out: list[SearchHit] = []
    for m in _HIT_RE.finditer(html):
        md5 = m.group("md5")
        body = _strip_tags(m.group("body"))
        title_match = _TITLE_RE.search(m.group("body"))
        title = _strip_tags(title_match.group(1)) if title_match else body[:120]
        meta_match = _META_RE.search(body)
        lang = meta_match.group("lang") if meta_match else ""
        ext = (meta_match.group("ext") if meta_match else "pdf").lower()
        size_str = meta_match.group("size") if meta_match else "0 B"
        size_bytes = _parse_size(size_str)
        year_match = _YEAR_RE.search(body)
        year = year_match.group(1) if year_match else "0000"
        out.append(SearchHit(
            md5=md5,
            title=title.strip()[:200],
            author=_guess_author(body),
            year=year,
            extension=ext,
            size_bytes=size_bytes,
            language=lang,
            raw_url=f"{mirror}/md5/{md5}",
        ))
        if len(out) >= limit:
            break
    return out


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s)


def _parse_size(s: str) -> int:
    m = re.match(r"\s*([\d.]+)\s*([KMG]?B)", s, re.IGNORECASE)
    if not m:
        return 0
    n = float(m.group(1))
    unit = m.group(2).upper()
    mult = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}.get(unit, 1)
    return int(n * mult)


def _guess_author(body: str) -> str:
    """Anna's Archive puts the author in a small italic-ish line; best-effort."""
    m = re.search(r"([A-Z][a-z]+(?:\s+[A-Z]\.?)*\s+[A-Z][a-z]+)", body)
    return m.group(1) if m else ""


# =========================================================================
# CLI — `python -m skills.common.annas_archive search "Trotter quantum"`
# =========================================================================

if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser(
        description="Anna's Archive search + download for QuantumNovelty."
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="search only; prints hits as JSON")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=5)
    s.add_argument("--lang", default="en")

    d = sub.add_parser("acquire", help="search + download for queries")
    d.add_argument("--queries-file", type=Path, required=True,
                   help="one query per line")
    d.add_argument("--target-dir", type=Path, required=True)
    d.add_argument("--max-per-query", type=int, default=1)
    d.add_argument("--rate-seconds", type=float,
                   default=DEFAULT_RATE_SECONDS)
    d.add_argument("--report-out", type=Path, default=None)

    args = ap.parse_args()
    if args.cmd == "search":
        status, hits = search(args.query, limit=args.limit, lang=args.lang)
        json.dump({
            "status": status,
            "hits": [h.__dict__ for h in hits],
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        queries = [
            ln.strip() for ln in args.queries_file.read_text(
                encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")
        ]
        reports = acquire(queries, args.target_dir,
                          max_downloads_per_query=args.max_per_query,
                          rate_seconds=args.rate_seconds)
        out_text = "[\n" + ",\n".join(r.to_json() for r in reports) + "\n]\n"
        if args.report_out:
            args.report_out.write_text(out_text, encoding="utf-8")
            print(f"acquire: {len(reports)} reports written to {args.report_out}")
        else:
            sys.stdout.write(out_text)
