# disclosure_audit — funding / COI / ethics / availability audit

One LLM call against a fixed 16-point checklist: journal-standard
disclosures (funding, competing interests, author contributions, data
availability, code availability, ethics, preprint status, materials),
AI-use disclosures (text, figures, analysis, review), and
rights/warranties (prior publication, export control, third-party
rights, open-version conflicts).

```bash
bash skills/disclosure_audit/run.sh \
  --paper paper.pdf --outdir OUT [--journal prx-quantum] [--llm claude]
```

Outputs: `disclosure_audit.md` (per-item status table + severity-
grouped gaps + 16-line submission checklist),
`disclosure_findings.json`, `_backend_used.json`.

## Chain integration

`--with-disclosure-audit` on the `paper-audit` pipeline; stage
`03e_disclosure_audit`.
