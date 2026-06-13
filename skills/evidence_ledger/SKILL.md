# evidence_ledger — reviewer-hallucination guard

Deterministic, zero-LLM. Adapted from AutoResearchClaw's evidence-ledger
gate (ARC's two-pass "permitted facts" pattern). It closes a hole the
review panel cannot close on its own: a reviewer voice attributing a claim,
quote, or number to the paper that the paper never made.

## Two passes

| Mode | Inputs | Output | When |
|---|---|---|---|
| `ledger` (default) | `--paper PATH` (+ optional `--bib`) | `ledger.json`, `ledger.md` | before the review stages |
| `audit` | `--ledger PATH --run-dir DIR` | `ledger_audit.json`, `ledger_audit.md` | after all review stages |

**Ledger pass** extracts, by regex only:
- `cite_keys` — every `\cite{KEY}` in the paper (+ `@entry` keys if `--bib`)
- `numerics` — every distinct numeric value (percent / exponent / fraction aware)
- `headings` — section/subsection titles
- `paper_text_norm` — normalized full text for fuzzy matching

**Audit pass** scans every `.md`/`.txt` review report under `--run-dir`
(skipping `_`-prefixed scaffolding, `full_prompt*`, and the ledger's own
stage dirs) and flags four classes of unanchored attribution:

| Kind | Trigger |
|---|---|
| `unknown_cite_key` | `\cite{KEY}` whose KEY is not in the ledger |
| `unanchored_quote` | a ≥6-word verbatim quote absent from the paper (verbatim or <70% token overlap) |
| `unanchored_paper_claim` | "the paper reports X" where <50% of X's content words appear in the paper |
| `unanchored_numeric_in_claim` | a non-trivial number inside a "the paper reports X" clause absent from the ledger |

## Gate semantics

**Informational only — never fails the chain.** A finding marks a candidate
reviewer hallucination for the operator to verify. Lossy PDF extraction can
produce false positives; the token-overlap fallbacks (70% for quotes, 50%
for paraphrases) absorb most extraction drift, and auditing against `.tex` /
`.md` source is more precise than against a scanned PDF.

## CLI

```bash
# pass 1 — pre-register the paper's facts
python3 skill.py --mode ledger --paper paper.tex --outdir 00_evidence_ledger

# pass 2 — audit the reviews against the ledger
python3 skill.py --mode audit \
  --ledger 00_evidence_ledger/ledger.json \
  --run-dir <run_root> --outdir 98_evidence_ledger_audit
```

In the `paper-audit` pipeline both passes arm together via
`--with-evidence-ledger` (ledger runs after research; audit runs after the
review stages, before the CQE summary).

Exit codes: `0` clean run (findings may still be present), `2` bad input.
