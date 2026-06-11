"""Shared paper/draft text ingestion for every skill that takes --paper/--draft.

One loader, four formats:
  .tex / .md / .markdown / .txt  -> read as UTF-8 text
  .docx                          -> python-docx (pip install -e ".[ingest]")
  .pdf                           -> pdftotext binary if on PATH, else
                                    pdfminer.six (pip install -e ".[ingest]")

PDF extraction is lossy by nature (no math layout, figures dropped); the
review/audit prompts only need the prose and the numbers, which both
extractors preserve.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

TEXT_SUFFIXES = (".tex", ".md", ".markdown", ".txt")


def _pdf_text(path: Path) -> str:
    if shutil.which("pdftotext"):
        with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
            subprocess.run(["pdftotext", "-layout", str(path), tf.name],
                           check=True)
            return Path(tf.name).read_text(encoding="utf-8", errors="replace")
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        raise RuntimeError(
            f"cannot extract text from {path.name}: install poppler "
            '(`brew install poppler` / `apt install poppler-utils`) for '
            'pdftotext, or `pip install -e ".[ingest]"` for pdfminer.six'
        )
    return extract_text(str(path))


def load_paper_text(path: Path) -> str:
    """Return the plain-text content of a paper/draft file.

    Raises RuntimeError with install guidance when an optional ingest
    dependency is missing, ValueError for genuinely unsupported formats.
    """
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError:
            raise RuntimeError(
                f"loading {path.name} requires python-docx: "
                '`pip install -e ".[ingest]"`'
            )
        return "\n\n".join(p.text for p in Document(str(path)).paragraphs)
    if suffix == ".pdf":
        return _pdf_text(path)
    raise ValueError(
        f"unsupported draft format: {suffix} "
        f"(supported: {', '.join(TEXT_SUFFIXES)}, .docx, .pdf)"
    )
