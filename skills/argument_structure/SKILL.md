# argument_structure — argument-architecture audit

One LLM call. Audits the argument's architecture rather than its
line-by-line correctness: explicit premises → intermediate claims →
conclusion map (with unsupported leaps and unstated premises),
controlling-idea claim–proof gap, Claim/Mechanism/Evidence
proportionality, a narrative-debt register (promises vs delivery),
sequencing diagnosis, and structural gaps.

```bash
bash skills/argument_structure/run.sh \
  --paper paper.pdf --outdir OUT [--journal prx-quantum] [--llm claude]
```

Outputs: `argument_structure.md` (the report),
`argument_structure.json` (verdict + CME split + debts, machine-
readable), `_backend_used.json` (model + tokens + USD).

Catches the failure class the referee panel reads past: every sentence
individually defensible, but the architecture doesn't support the
headline (fixed-size benchmark sold as scaling result, single-device
measurement sold as architecture demonstration).

## Chain integration

`--with-argument-structure` on the `paper-audit` pipeline; stage
`02d_argument_structure`. Runs on the same `--paper` input as the
panel; the revision planner quotes it as a judge when present.
