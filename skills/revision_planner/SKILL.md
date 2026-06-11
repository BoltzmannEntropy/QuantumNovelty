# revision_planner — paragraph-anchored revision roadmap

One LLM call. Converts a paper-audit run's findings into an actionable
plan: every item anchored to deterministic ¶NNN paragraph IDs (stamped
on the manuscript before prompting), verbatim quoted problem prose,
verbatim per-judge evidence, and a concrete proposed edit with an
effort estimate.

```bash
bash skills/revision_planner/run.sh \
  --paper paper.pdf --run-dir <paper-audit outdir> --outdir OUT \
  [--llm claude]
```

The roadmap to anchor comes from the editorial-synthesis stage when it
ran (`03b_editorial_synthesis/`), else from the quality gate's
`required_actions`. Judge reports quoted when present: referee panel,
fallacy report, research review, argument structure, disclosure audit.

Outputs: `anchored_revision_plan.md`, `_source_numbered.md` (the
¶NNN-stamped manuscript), `_backend_used.json`.

Anti-hallucination rules baked into the prompt: never invent ¶ IDs,
quote manuscript + judges verbatim or mark the absence, never invent
judge attribution.

## Chain integration

`--with-revision-planner` on the `paper-audit` pipeline; stage
`03f_revision_plan`, runs after synthesis/fallacies.
