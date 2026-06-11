"""Quantum-computing journal registry.

When the user selects a target journal (`--journal NAME`), every downstream
skill — paper drafter, format converter, citation checker, disclosure auditor,
reviewer panel — reads the venue's policy from here so the output meets the
journal's actual requirements rather than the LLM's memory of them.

Coverage focused on quantum-computing venues:

  quantum                   Quantum (Verein zur Förderung des Open Access
                            Publizierens in den Quantenwissenschaften — the
                            community-run open-access journal)
  npj-quantum-information   Nature partner journal
  prx-quantum               APS Physical Review X Quantum
  physical-review-letters   APS PRL (general; quantum-info section)
  physical-review-a         APS PRA (general atomic/molecular/optical/quantum)
  physical-review-applied   APS PRApplied
  nature-communications     Nature Comms (quantum subsection)
  communications-physics    Nature Comms Physics
  quantum-science-and-tech  IOP QST
  physics-letters-a         Elsevier PLA
  ieee-tqe                  IEEE Transactions on Quantum Engineering

Use `journal_policy(name)` to look up; raises a clear error if you spell the
slug wrong.

NB: page limits, citation styles, and required statements drift over time.
This registry was authored against the journals' 2025-2026 author guidelines;
re-check before submission. The registry is data, not advice — the framework
will not overrule a user who passes `--journal-custom-policy path.json`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class JournalPolicy:
    """One target venue's policy.

    Defaults are conservative (no page limit, generic author-year citation
    style) so that an unknown venue still produces something submittable; pick
    a specific venue to tighten the constraints.
    """
    name: str
    slug: str
    publisher: str
    open_access: bool
    abstract_word_limit: int | None       # None means no enforced limit
    body_word_limit: int | None
    page_limit: int | None
    citation_style: str                   # "numerical" | "author-year" | "vancouver" | "revtex" | "ieee"
    template: str                         # LaTeX template family preferred
    section_order: list[str] = field(default_factory=list)
    required_statements: list[str] = field(default_factory=list)
    accepts_supplementary: bool = True
    typical_review_load: str = "3 referees, 1 editor"
    notes: str = ""

    def manifest_md(self) -> str:
        """Render a human-readable summary suitable for the chain log."""
        lines = [
            f"# Journal policy — {self.name}",
            "",
            f"- **Publisher:** {self.publisher}",
            f"- **Open access:** {self.open_access}",
            f"- **Citation style:** {self.citation_style}",
            f"- **Template:** {self.template}",
            f"- **Abstract limit:** {self.abstract_word_limit or 'none'} words",
            f"- **Body limit:** {self.body_word_limit or 'none'} words",
            f"- **Page limit:** {self.page_limit or 'none'} pages",
        ]
        if self.section_order:
            lines.append(f"- **Section order:** {' → '.join(self.section_order)}")
        if self.required_statements:
            lines.append("- **Required statements:**")
            for s in self.required_statements:
                lines.append(f"  - {s}")
        if self.notes:
            lines.append("")
            lines.append(f"_Notes:_ {self.notes}")
        return "\n".join(lines)


# =========================================================================
# Registry
# =========================================================================

_REGISTRY: dict[str, JournalPolicy] = {}


def _register(p: JournalPolicy) -> None:
    _REGISTRY[p.slug] = p


_register(JournalPolicy(
    name="Quantum",
    slug="quantum",
    publisher="Verein zur Förderung des Open Access Publizierens in den Quantenwissenschaften",
    open_access=True,
    abstract_word_limit=None,
    body_word_limit=None,
    page_limit=None,
    citation_style="numerical",
    template="quantum-article",
    section_order=["Abstract", "Introduction", "Results", "Discussion", "Methods", "Acknowledgments", "References"],
    required_statements=["Data Availability", "Code Availability",
                         "Author Contributions", "Competing Interests"],
    notes="Community-run open-access journal; uses `quantum-article` LaTeX "
          "class. Strong tradition of detailed Methods. No page limit but "
          "expects supplementary material for code/data.",
))

_register(JournalPolicy(
    name="npj Quantum Information",
    slug="npj-quantum-information",
    publisher="Nature Publishing Group",
    open_access=True,
    abstract_word_limit=250,
    body_word_limit=None,                # No explicit cap but ~12-18k typical
    page_limit=None,
    citation_style="numerical",
    template="revtex4-2",                 # Accepts revtex4-2 with nature-style refs
    section_order=["Introduction", "Results", "Discussion", "Methods",
                   "Author Contributions", "Competing Interests",
                   "Code Availability", "Data Availability", "References"],
    required_statements=["Author Contributions", "Competing Interests",
                         "Data Availability", "Code Availability"],
    notes="Methods at the END (Nature/npj convention). Abstract ≤ 250 words. "
          "Both `revtex4-2` and the `nature` LaTeX class accepted. Required "
          "statements are non-negotiable for publication.",
))

_register(JournalPolicy(
    name="PRX Quantum",
    slug="prx-quantum",
    publisher="American Physical Society",
    open_access=True,
    abstract_word_limit=None,             # Single-paragraph abstract, no hard cap
    body_word_limit=None,
    page_limit=None,
    citation_style="revtex",
    template="revtex4-2",
    section_order=["Abstract", "Introduction", "Methods/Background",
                   "Results", "Discussion", "Conclusion", "Acknowledgments",
                   "References"],
    required_statements=["Acknowledgments", "Competing Interests (if any)"],
    notes="Long-form quantum-info venue; expects deep technical exposition. "
          "PRX-style numbered references. Methods can be inline (not appended).",
))

_register(JournalPolicy(
    name="Physical Review Letters",
    slug="physical-review-letters",
    publisher="American Physical Society",
    open_access=False,
    abstract_word_limit=600,              # Title+abstract+figures+body combined ≤ 4 pages
    body_word_limit=3750,                  # Roughly 4-page equivalent
    page_limit=4,
    citation_style="revtex",
    template="revtex4-2",
    section_order=["Abstract", "Introduction-Results merged", "Discussion",
                   "References"],
    required_statements=["Acknowledgments"],
    notes="STRICT 4-page limit incl. figures/references. PRL papers are "
          "short letters; if the work needs >4 pages, target PRA or PRX-Q. "
          "Supplementary material accepted separately.",
))

_register(JournalPolicy(
    name="Physical Review A",
    slug="physical-review-a",
    publisher="American Physical Society",
    open_access=False,
    abstract_word_limit=None,
    body_word_limit=None,
    page_limit=None,
    citation_style="revtex",
    template="revtex4-2",
    section_order=["Abstract", "Introduction", "Methods", "Results",
                   "Discussion", "Conclusion", "Acknowledgments", "References"],
    required_statements=["Acknowledgments"],
    notes="Long-form companion to PRL. Atomic, molecular, optical, and "
          "quantum information.",
))

_register(JournalPolicy(
    name="Physical Review Applied",
    slug="physical-review-applied",
    publisher="American Physical Society",
    open_access=False,
    abstract_word_limit=None,
    body_word_limit=None,
    page_limit=None,
    citation_style="revtex",
    template="revtex4-2",
    section_order=["Abstract", "Introduction", "Methods", "Results",
                   "Discussion", "References"],
    required_statements=["Acknowledgments"],
    notes="Applications-focused; quantum computing hardware results land "
          "here. Emphasises engineering relevance.",
))

_register(JournalPolicy(
    name="Nature Communications",
    slug="nature-communications",
    publisher="Nature Publishing Group",
    open_access=True,
    abstract_word_limit=150,               # Editorial summary, tight
    body_word_limit=5000,                  # Soft target for main text
    page_limit=None,
    citation_style="numerical",
    template="nature",
    section_order=["Introduction", "Results", "Discussion", "Methods",
                   "Author Contributions", "Competing Interests",
                   "Data Availability", "Code Availability", "References"],
    required_statements=["Author Contributions", "Competing Interests",
                         "Data Availability", "Code Availability"],
    notes="Methods at the END (Nature convention). 150-word abstract is "
          "STRICT. Body ~5000 words for main text; rest goes to Methods + "
          "Extended Data + Supplementary.",
))

_register(JournalPolicy(
    name="Communications Physics",
    slug="communications-physics",
    publisher="Nature Publishing Group",
    open_access=True,
    abstract_word_limit=150,
    body_word_limit=None,
    page_limit=None,
    citation_style="numerical",
    template="nature",
    section_order=["Introduction", "Results", "Discussion", "Methods",
                   "Author Contributions", "Competing Interests",
                   "Data Availability", "Code Availability", "References"],
    required_statements=["Author Contributions", "Competing Interests",
                         "Data Availability", "Code Availability"],
    notes="Nature partner journal for physics; same Methods-at-end convention "
          "as Nature/npj. 150-word abstract.",
))

_register(JournalPolicy(
    name="Quantum Science and Technology",
    slug="quantum-science-and-technology",
    publisher="IOP Publishing",
    open_access=True,
    abstract_word_limit=300,
    body_word_limit=None,
    page_limit=None,
    citation_style="iopart",
    template="iopart",
    section_order=["Abstract", "Introduction", "Methods", "Results",
                   "Discussion", "Conclusion", "Acknowledgments", "References"],
    required_statements=["Acknowledgments", "Data Availability"],
    notes="IOP `iopart` class. Broad quantum-tech scope incl. algorithms, "
          "hardware, networking.",
))

_register(JournalPolicy(
    name="Physics Letters A",
    slug="physics-letters-a",
    publisher="Elsevier",
    open_access=False,
    abstract_word_limit=200,
    body_word_limit=None,
    page_limit=10,
    citation_style="elsarticle-num",
    template="elsarticle",
    section_order=["Abstract", "Introduction", "Methods", "Results",
                   "Discussion", "Conclusion", "References"],
    required_statements=["Declaration of Competing Interest"],
    notes="Elsevier `elsarticle` class with numerical refs. Short-form "
          "physics letters; ~10 pages typical.",
))

_register(JournalPolicy(
    name="IEEE Transactions on Quantum Engineering",
    slug="ieee-tqe",
    publisher="IEEE",
    open_access=True,
    abstract_word_limit=250,
    body_word_limit=None,
    page_limit=None,
    citation_style="ieee",
    template="IEEEtran",
    section_order=["Abstract", "Introduction", "Background", "Methods",
                   "Results", "Discussion", "Conclusion", "References"],
    required_statements=["Acknowledgments", "Competing Interests"],
    notes="IEEE `IEEEtran` class. Engineering-oriented venue; emphasises "
          "implementation detail + reproducibility.",
))


# =========================================================================
# Public API
# =========================================================================

def known_journals() -> list[str]:
    """List of registered journal slugs, sorted."""
    return sorted(_REGISTRY)


def journal_policy(slug: str) -> JournalPolicy:
    """Look up a journal policy by slug. Raises KeyError with all known slugs."""
    try:
        return _REGISTRY[slug]
    except KeyError:
        raise KeyError(
            f"unknown journal slug {slug!r}; known journals: "
            f"{', '.join(known_journals())}"
        )


def load_custom_policy(path: Path) -> JournalPolicy:
    """Load a user-supplied journal policy from JSON.

    Schema must match JournalPolicy's fields. Useful when targeting a venue
    not in the built-in registry.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    return JournalPolicy(**data)


# =========================================================================
# CLI — `python -m skills.common.journals list` / `... show npj-quantum-information`
# =========================================================================

if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="print all known journal slugs")
    show = sub.add_parser("show", help="print a journal's policy in markdown")
    show.add_argument("slug")
    show_json = sub.add_parser("dump", help="print a journal's policy as JSON")
    show_json.add_argument("slug")
    args = ap.parse_args()
    if args.cmd == "list":
        for slug in known_journals():
            p = journal_policy(slug)
            print(f"{slug:35} {p.name}")
    elif args.cmd == "show":
        print(journal_policy(args.slug).manifest_md())
    elif args.cmd == "dump":
        p = journal_policy(args.slug)
        json.dump({k: v for k, v in p.__dict__.items()},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
