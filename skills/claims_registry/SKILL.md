# claims_registry — deterministic numeric-claim audits

Zero LLM calls. Adapted from AutoResearchClaw's verification stages
(`paper_verifier.py`, stage-22 `paper_verification`, verified-registry).

Two modes:

## registry mode (single document)

```bash
bash skills/claims_registry/run.sh --paper paper.pdf --outdir OUT
```

Builds a registry of every numeric value found in the strict sections
(Results / Experiments / Tables / Benchmarks — override with
`--strict-on`), then flags every numeric in the other sections
(Abstract / Intro / Discussion / ...) that does not trace back to a
registry value. This is the "abstract says 98.3%, table says 87%"
catcher.

Inputs: `.tex` / `.md` / `.txt` / `.pdf` / `.docx` (PDF via the shared
`paper_io` extractor; a plain-text heading heuristic recovers sections
from pdftotext output).

Outputs: `registry.json`, `verification_report.json`,
`verification_report.md`.

## render-audit mode (source vs render)

```bash
bash skills/claims_registry/run.sh --source draft.md --render paper.tex \
  --outdir OUT [--threshold 0.05]
```

Every numeric in the rendered artifact must already exist in the
source-of-truth document. Catches render-time fabrication — LLM
rewrites that inject numbers. Exit 3 when `fabrication_rate` exceeds
the threshold.

Output: `paper_verification.json`.

## Chain integration

`--with-claims-registry` on the `paper-audit` pipeline runs registry
mode against the `--paper` input as stage `03c_claims_registry`.
