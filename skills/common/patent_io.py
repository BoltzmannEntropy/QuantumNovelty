"""Patent ingestion — Google Patents URL (or local file) -> examiner-ready text.

The patent-review skills take a `--patent` file the same way the paper
skills take `--paper`. This module is the SSOT for turning a patent into
that file: it fetches a Google Patents page, pulls the four sections an
examiner needs (bibliographic header, abstract, claims, written
description), and renders them as one structured Markdown document with
the claims numbered exactly as filed.

Why a separate module from paper_io.py: a patent is not a paper. The
load-bearing object is the *claim set* (each claim examined individually
under 35 U.S.C. §§ 101/102/103/112), and the bibliographic header
(kind code, filing/publication dates, assignee) decides whether the panel
is examining a published application (`A1`) or critiquing a granted
patent (`B1`/`B2`). paper_io.py has no concept of either.

Network is stdlib-only (urllib) so the skill has no hard dependency on
requests/bs4. A local `.html`/`.txt`/`.md` file is also accepted, so a
run is reproducible offline once the page has been saved once.
"""
from __future__ import annotations

import html as _html
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) QuantumNovelty/patent_io"
_GP_RE = re.compile(r"patents\.google\.com/patent/([A-Z]{2}[A-Z0-9]+)", re.I)


@dataclass
class Patent:
    """The examiner-relevant projection of a patent document."""
    pub_number: str                       # e.g. US10614371B2
    kind_code: str                        # A1 / B1 / B2 / ...
    title: str
    inventors: list[str] = field(default_factory=list)
    assignee: str = ""
    dates: dict[str, str] = field(default_factory=dict)  # filing/publication
    abstract: str = ""
    claims: str = ""
    description: str = ""
    source_url: str = ""

    @property
    def is_application(self) -> bool:
        """A1/A9 = published application under examination; B* = granted."""
        return self.kind_code.upper().startswith("A")

    @property
    def status_line(self) -> str:
        if self.is_application:
            return (f"PUBLISHED APPLICATION (kind code {self.kind_code}) — "
                    "under examination; NOT yet granted. The panel acts as "
                    "the examining office deciding whether to allow or reject "
                    "these claims.")
        return (f"GRANTED PATENT (kind code {self.kind_code}) — already "
                "issued. The panel acts as a post-grant reviewer / IPR "
                "petitioner assessing validity of the issued claims.")

    def n_claims(self) -> int:
        # Independent + dependent: count "N. " claim openers.
        return len(re.findall(r"(?m)^\s*\d+\s*\.\s", self.claims))

    def to_markdown(self) -> str:
        inv = ", ".join(self.inventors) or "(not listed)"
        dts = "; ".join(f"{k}: {v}" for k, v in self.dates.items()) or "(none)"
        return "\n".join([
            f"# Patent {self.pub_number} — {self.title}",
            "",
            "## Bibliographic data",
            "",
            f"- **Publication number:** {self.pub_number}",
            f"- **Kind code:** {self.kind_code}",
            f"- **Status:** {self.status_line}",
            f"- **Title:** {self.title}",
            f"- **Inventor(s):** {inv}",
            f"- **Assignee/Applicant:** {self.assignee or '(not listed)'}",
            f"- **Dates:** {dts}",
            f"- **Claim count (parsed):** {self.n_claims()}",
            f"- **Source:** {self.source_url}",
            "",
            "## Abstract",
            "",
            self.abstract or "_(abstract not extracted)_",
            "",
            "## Claims",
            "",
            "_(Examine each claim individually. Claim numbers below are as "
            "filed/published.)_",
            "",
            self.claims or "_(claims not extracted)_",
            "",
            "## Written description / specification",
            "",
            self.description or "_(description not extracted)_",
            "",
        ])


# ---------------------------------------------------------------------------
# HTML parsing (Google Patents static markup; no JS needed for these fields)
# ---------------------------------------------------------------------------

def _strip_tags(s: str) -> str:
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = _html.unescape(s)
    s = re.sub(r"[ \t ]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _section(raw: str, itemprop: str) -> str:
    m = re.search(
        r'<section[^>]*itemprop="%s"[^>]*>(.*?)</section>' % itemprop,
        raw, re.S)
    return _strip_tags(m.group(1)) if m else ""


def _meta_all(raw: str, name: str) -> list[str]:
    return [m.strip() for m in re.findall(
        r'<meta[^>]*name="%s"[^>]*content="([^"]*)"' % re.escape(name), raw)]


def _meta(raw: str, name: str) -> str:
    vals = _meta_all(raw, name)
    return vals[0] if vals else ""


def _normalize_claims(text: str) -> str:
    """Put each claim opener ("12 .") on its own paragraph and tidy the
    Google "1 ." spacing into "1." so downstream claim-number parsing
    (the deterministic gate) is robust."""
    text = re.sub(r"(?m)^\s*(\d+)\s*\.\s*", r"\n\1. ", text)
    text = re.sub(r"\bclaim\s+(\d+)\b", r"claim \1", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_google_patents_html(raw: str, source_url: str = "") -> Patent:
    pub_raw = _meta(raw, "citation_patent_publication_number")  # US:2025...:A1
    parts = [p for p in pub_raw.split(":") if p]
    kind = parts[-1] if len(parts) >= 3 else ""
    pub_number = "".join(parts) if parts else ""
    if not pub_number:
        mm = _GP_RE.search(source_url)
        pub_number = mm.group(1) if mm else "(unknown)"
        kind = kind or re.sub(r".*?([A-Z]\d?)$", r"\1", pub_number)

    contributors = _meta_all(raw, "DC.contributor")
    # Google lists inventors then assignee under DC.contributor; the
    # assignee is usually the entry containing Inc/Ltd/Corp/LLC/GmbH/University.
    assignee = ""
    inventors: list[str] = []
    org_re = re.compile(
        r"\b(Inc|Ltd|LLC|L\.L\.C|Corp|Corporation|Company|GmbH|"
        r"University|Limited|Co\b|Technologies|Systems|Laboratories)\b", re.I)
    for c in contributors:
        if org_re.search(c) and not assignee:
            assignee = c
        else:
            inventors.append(c)

    dates: dict[str, str] = {}
    fd = _meta(raw, "citation_date") or _meta(raw, "DC.date")
    if fd:
        dates["publication/issue"] = fd
    times = re.findall(r"<time[^>]*>([0-9]{4}-[0-9]{2}-[0-9]{2})</time>", raw)
    if times:
        dates.setdefault("earliest priority", times[0])
        dates.setdefault("latest event", times[-1])

    return Patent(
        pub_number=pub_number,
        kind_code=kind,
        title=(_meta(raw, "DC.title") or _meta(raw, "citation_title")).strip(),
        inventors=inventors,
        assignee=assignee,
        dates=dates,
        abstract=_section(raw, "abstract"),
        claims=_normalize_claims(_section(raw, "claims")),
        description=_section(raw, "description"),
        source_url=source_url,
    )


def fetch_patent(url: str, timeout: int = 60) -> Patent:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    raw = urllib.request.urlopen(req, timeout=timeout).read().decode(
        "utf-8", "replace")
    return parse_google_patents_html(raw, source_url=url)


def canonicalize_google_url(url: str) -> str:
    """Strip query params + locale noise: keep .../patent/<NUMBER>/en."""
    m = _GP_RE.search(url)
    if m:
        return f"https://patents.google.com/patent/{m.group(1)}/en"
    return url


def load_patent(source: str, timeout: int = 60) -> Patent:
    """Resolve a patent from a URL, a bare publication number, or a local
    saved HTML/text file into a Patent object."""
    p = Path(source)
    if p.is_file():
        raw = p.read_text(encoding="utf-8", errors="replace")
        if "<html" in raw.lower() or "<section" in raw.lower():
            return parse_google_patents_html(raw, source_url=str(p))
        # Already-rendered text/markdown: split on the spec heading if present
        # so description is populated when run_eval.py appends it.
        spec_marker = "## Written description / specification"
        if spec_marker in raw:
            parts = raw.split(spec_marker, 1)
            claims_part = parts[0].strip()
            desc_part = parts[1].strip()
        else:
            claims_part = raw
            desc_part = ""
        return Patent(pub_number=p.stem, kind_code="", title=p.stem,
                      claims=claims_part, source_url=str(p),
                      description=desc_part)
    if "patents.google.com" in source:
        return fetch_patent(canonicalize_google_url(source), timeout=timeout)
    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]+", source.strip()):
        return fetch_patent(
            f"https://patents.google.com/patent/{source.strip()}/en",
            timeout=timeout)
    raise ValueError(
        f"cannot resolve patent source: {source!r} "
        "(expected a Google Patents URL, a publication number like "
        "US10614371B2, or a local saved .html/.txt file)")


def _cli() -> int:
    """`python patent_io.py <url|number|file> --out PATH` — fetch + render."""
    import argparse
    ap = argparse.ArgumentParser(description="Fetch a patent to examiner text")
    ap.add_argument("source", help="Google Patents URL, publication number, "
                                    "or local saved HTML/text file")
    ap.add_argument("--out", required=True, type=Path,
                    help="where to write the rendered Markdown")
    a = ap.parse_args()
    pat = load_patent(a.source)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(pat.to_markdown(), encoding="utf-8")
    print(f"patent_io: {pat.pub_number} ({pat.kind_code}) -> {a.out} "
          f"[{pat.n_claims()} claims, {len(pat.description)} desc chars]")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
