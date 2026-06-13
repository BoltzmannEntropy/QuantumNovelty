# requirements_judge — claim-vs-evidence audit + allowed/forbidden manifest

LLM-as-judge. Adapted from AutoResearchClaw's requirements-judge gate
(ARC's intent-vs-output audit + binding allowed/forbidden-claims manifest).

Where `claims_registry` is the deterministic numeric catcher ("abstract
says 98.3%, table says 87%"), this stage is the hypothesis-level catcher:
a contribution the paper *asserts* that its own evidence does not support
(an overclaim), and the converse — claims the evidence does license.

## Mode

`review` (default): reads an existing manuscript (`--paper`), reconstructs
its central claims, and rules on each against the paper's own reported
evidence.

## Output (`requirements_report.json`)

| Field | Meaning |
|---|---|
| `requirements[]` | per-claim `{requirement, status, evidence, note}`; status ∈ `met` / `partial` / `unmet` / `unevaluable` |
| `allowed_claims[]` | claims the evidence supports (what the paper may assert) |
| `forbidden_claims[]` | overclaims — claims the evidence does NOT support |
| `verdict` | `proceed` / `partial` / `reject` |
| `delta_feedback` | if not proceed: the concrete changes that would make the claims sound |
| `judge_parse_ok` | false when the conservative reject fallback fired |

Also writes `requirements_report.md` (human-readable) and
`_backend_used.json`.

## Robustness

- **Verdict consistency** is enforced post-parse: a `proceed` that still has
  `unmet`/`unevaluable` requirements is downgraded to `partial`; an empty
  requirement list is forced to `reject`.
- **Conservative fallback** (ARC pattern): if the judge's reply will not
  parse into the manifest, the report is `reject` with empty manifests and a
  re-run note — an unverifiable audit never waves a paper through.

## CLI

```bash
python3 skill.py --mode review --paper paper.tex \
  --journal prx-quantum --llm claude --outdir 02e_requirements_judge
```

In the `paper-audit` pipeline it arms via `--with-requirements-judge`
(runs after the reviewer panel).

Exit codes: `0` proceed, `3` partial/reject, `2` bad input, `4` backend
produced no output.
