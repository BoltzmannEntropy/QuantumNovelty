# `quantum_paper` — multi-mode quantum-paper authoring skill

Ten modes for authoring a quantum-computing paper, from blank page to
submission-ready. Inspired by ARS's academic-paper pattern; the quantum twist
is venue-aware (every mode reads the target journal's policy) and library-
aware (code-generating modes emit working snippets in the user's chosen
quantum library).

## CLI

```
quantum_paper/run.sh \
  --mode MODE \
  --outdir DIR \
  [--llm BACKEND]                # default: claude
  [--journal SLUG]               # see `python -m skills.common.journals list`
  [--quantum-lib SLUG]           # see `python -m skills.common.quantum_libs list`
  [--topic "STR"]                # required for full / plan / outline-only / lit-review
  [--draft PATH]                 # required for revision / revision-coach /
                                 # abstract-only / format-convert / citation-check / disclosure
  [--reviewer-comments PATH]     # required for revision / revision-coach
```

## Modes

| Mode | Use | Trigger phrase |
|---|---|---|
| `full` | Write a complete first draft from a topic | "Write a paper on LLM-driven ansatz discovery for VQE" |
| `plan` | Guided planning — walks the user through the contribution-then-method-then-results-then-discussion ladder | "Guide me through writing a paper on Trotter error" |
| `outline-only` | Section-by-section outline + per-section word budget keyed to journal limits | "Build a paper outline targeting npj-quantum-information" |
| `revision` | Apply reviewer comments to an existing draft, producing a revised TeX + a response letter | "I have a draft and reviewer comments — produce the revision" |
| `revision-coach` | Parse reviewer comments into a structured roadmap (without applying yet) | "Parse these reviewer comments into a roadmap" |
| `abstract-only` | Write only the abstract, sized to the venue's word limit | "Write an abstract for this paper" |
| `lit-review` | Rewrite as a literature-review paper (different scope than `deep_research --mode lit-review`, which produces a section; this produces a standalone review article) | "Turn this into a literature review paper" |
| `format-convert` | Convert between LaTeX templates / citation styles (e.g., revtex4-2 → IEEEtran, or author-year → numerical) | "Convert this paper to PRX Quantum format" |
| `citation-check` | Verify every `\cite{...}` resolves + matches its claim (light version of `novelty_audit`'s citation pass) | "Check the citations in this paper" |
| `disclosure` | Generate the AI / data / code / COI / IRB / funding disclosure block for the chosen venue | "Generate the disclosure block for npj-quantum-information" |

## Quantum twist per mode

- **`full` / `plan` / `outline-only`**: section ordering follows the target journal's `section_order` policy (e.g., Methods-at-end for Nature/npj-QI, Methods-inline for PRX Quantum). Word budgets per section are derived from the journal's `body_word_limit`.
- **`revision`**: alongside the revised draft, emits a `response_to_reviewers.md` keyed to reviewer line numbers — a hard requirement at most quantum venues.
- **`format-convert`**: knows the canonical LaTeX templates for each registered journal (revtex4-2 / IEEEtran / iopart / elsarticle / nature / quantum-article) and the corresponding citation style.
- **`disclosure`**: the disclosure block uses the venue's `required_statements` list as the spine — Funding, COI, Author Contributions, Data Availability, Code Availability, IRB, Preprint status, AI-use disclosure. The Code Availability section incorporates the chosen `--quantum-lib` automatically.
- **`citation-check`**: the integrity pass uses the comparator logic from `audit_falsify` (network-failure ≠ hallucinated), so transient CrossRef errors don't get reported as fabricated citations.

## Outputs (in `--outdir`)

All modes:
- `_backend_used.json`
- `full_prompt_<mode>.txt`
- `_llm_generation.log`

Mode-specific:
- `full`: `paper.tex` (or `.md` if no journal template), `figures.md`, `notes_for_author.md`
- `plan`: `plan.md`, `questions_for_author.md`
- `outline-only`: `outline.md`, `outline.json` (machine-readable budgets)
- `revision`: `paper_v2.tex`, `response_to_reviewers.md`, `change_log.md`
- `revision-coach`: `roadmap.md`, `roadmap.json` (priority + effort estimate per item)
- `abstract-only`: `abstract.md`
- `lit-review`: `lit_review_paper.tex`
- `format-convert`: converted draft + `conversion_notes.md`
- `citation-check`: `citation_report.md`, `citation_status.json`
- `disclosure`: `disclosure_block.tex`, `disclosure_block.md`

## Composition with other skills

- `quantum_paper --mode full` typically follows `pareto_explorer` + `cross_llm_prediction` (so the paper has real results to write up).
- `quantum_paper --mode revision` typically follows `quantum_reviewer --mode full` (so the reviewer comments came from a structured panel).
- `quantum_paper --mode citation-check` is a lightweight pre-check before `novelty_audit`'s heavier integrity pass.
