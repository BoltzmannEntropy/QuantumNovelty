"""book_acquirer skill — wraps skills/common/annas_archive.py as a chain skill.

Inputs:
  --queries-file PATH  (one query per line)        OR
  --queries "q1; q2"   (semicolon-separated inline)

Reads optional --max-per-query (default 1), --rate-seconds (default 1.0).

Outputs:
  acquire_report.json — per-query acquisition status (ok / no_results /
                        network / parse / no_key / skipped)
  Per-query downloads land in <outdir>/files/ if ANNAS_ARCHIVE_KEY is set.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
import annas_archive  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queries-file", default=None, type=Path)
    ap.add_argument("--queries", default=None,
                    help="semicolon-separated inline queries (alternative to --queries-file)")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--max-per-query", type=int, default=1)
    ap.add_argument("--rate-seconds", type=float,
                    default=annas_archive.DEFAULT_RATE_SECONDS)
    # The skill takes --llm for chain-compatibility but does not use it
    # (acquisition is pure HTTP, no LLM call).
    ap.add_argument("--llm", default="claude")
    args = ap.parse_args()

    if not args.queries_file and not args.queries:
        print("ERROR: either --queries-file or --queries required",
              file=sys.stderr)
        return 2

    queries: list[str] = []
    if args.queries_file and args.queries_file.is_file():
        queries.extend(
            ln.strip() for ln in args.queries_file.read_text(
                encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        )
    if args.queries:
        queries.extend(
            q.strip() for q in args.queries.split(";") if q.strip()
        )
    if not queries:
        print("ERROR: no queries to process", file=sys.stderr)
        return 2

    args.outdir.mkdir(parents=True, exist_ok=True)
    files_dir = args.outdir / "files"

    reports = annas_archive.acquire(
        queries, files_dir,
        max_downloads_per_query=args.max_per_query,
        rate_seconds=args.rate_seconds,
    )

    # Persist combined report
    report_path = args.outdir / "acquire_report.json"
    report_path.write_text(
        json.dumps([
            {
                "query": r.query,
                "search_status": r.search_status,
                "n_hits": r.n_hits,
                "downloads": [
                    {"md5": d.md5, "status": d.status,
                     "path": str(d.path) if d.path else None,
                     "bytes_written": d.bytes_written,
                     "error": d.error}
                    for d in r.downloads
                ],
            } for r in reports
        ], indent=2), encoding="utf-8"
    )

    n_ok = sum(1 for r in reports for d in r.downloads if d.status == "ok")
    n_skipped = sum(1 for r in reports for d in r.downloads if d.status == "skipped")
    n_no_key = sum(1 for r in reports for d in r.downloads if d.status == "no_key")
    n_network = sum(1 for r in reports for d in r.downloads if d.status == "network")
    print(f"book_acquirer: {len(queries)} queries → "
          f"{n_ok} downloaded / {n_skipped} already on disk / "
          f"{n_no_key} blocked (no key) / {n_network} network errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
