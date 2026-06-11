# `book_acquirer` — Anna's Archive book download + OCR

Acquires books, theses, and old preprints not available on CrossRef/arXiv.

**Inputs:** `--queries-file PATH` (one query per line), `--target-dir DIR`,
  `--max-per-query INT` (default 1)
**Outputs:** downloaded PDFs in `--target-dir`, `acquire_report.json` with per-query status

**Requires:** `ANNAS_ARCHIVE_KEY` env (free from https://annas-archive.org/donate);
without a key the skill returns `status=no_key` for each query without raising.

**Rate limit:** 1 req/s by default (override via `QN_ANNAS_RATE_SECONDS`).
**Mirror:** `https://annas-archive.gl` by default (override via `QN_ANNAS_MIRROR`).
