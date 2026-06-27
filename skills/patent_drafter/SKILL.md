---
name: patent_drafter
description: Guided quantum-patent drafting workflow. Starts from an invention disclosure or short topic and drafts a filing package for USPTO, EPO, or multi-standard review: title, abstract, background, summary, drawings plan, detailed description, examples, claims, claim-compliance notes, application formalities, and prosecution checklist.
---

# patent_drafter — guided quantum-patent drafting

`patent_drafter` is the authoring complement to `patent_reviewer`.
`patent_reviewer` examines an existing patent or application; this skill starts
from an invention disclosure and drafts a filing-ready package for a quantum
invention.

## Workflow

The guided mode walks the invention through six drafting phases:

1. **Disclosure intake** — parse the quantum invention, technical problem,
   hardware/software context, and likely implementation variants.
2. **Prior-art search plan** — identify search strings, CPC/IPC classes,
   assignee/inventor searches, and examiner-manual sources to check.
3. **Claim strategy** — draft independent and dependent claims for system,
   method, and computer-readable-medium categories where appropriate.
4. **Application body** — title, abstract, background, summary, brief
   description of drawings, detailed description, examples, and alternatives.
5. **Compliance review** — USPTO 35 U.S.C. § 112(b), EPO Art. 84 clarity /
   two-part form, and PCT clarity/support checks as requested.
6. **Filing handoff** — formalities checklist, drawing list, missing
   information, IDS / prior-art package notes, and attorney review items.

The output is a drafting aid, not legal advice. A qualified patent attorney
or agent must review and sign any filing.

## Usage

```bash
bash skills/patent_drafter/run.sh \
  --mode guided \
  --disclosure invention_disclosure.md \
  --filing-standard multi \
  --outdir runs/patent_draft_demo \
  --llm claude
```

You can also start from a short topic:

```bash
bash chain/run.sh \
  --pipeline patent-draft \
  --topic "fault-tolerant routing of magic-state factories in a modular QPU" \
  --filing-standard uspto \
  --llm codex
```

## Outputs

- `filing_package.md` — the drafted patent package.
- `package_manifest.json` — deterministic run metadata: mode, filing standard,
  source type, output file, and generated sections expected by the prompt.
- `full_prompt_guided.txt` — exact prompt sent to the backend.
- `_backend_used.json` — backend, model, token, cost, and elapsed-time marker.
