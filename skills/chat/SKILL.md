# `chat` — natural-language frontend that dispatches to the chain

Maps a free-text user request to the right chain pipeline + skill + mode +
flags. Lets the user type "Review this paper" instead of remembering that
the actual command is `chain/run.sh --pipeline novelty-audit --paper PATH`.

## CLI

```
chat/run.sh \
  --prompt "STR"              # the user's natural-language request
  --outdir DIR                # where to write the dispatch decision
  [--paper PATH]              # if the prompt references "this paper"
  [--llm BACKEND]
  [--journal SLUG]
  [--quantum-lib SLUG]
  [--execute]                 # actually run the chain (default: just print)
```

## Routing taxonomy

The dispatcher uses pattern-matching first (cheap, deterministic) and falls
back to LLM classification when the pattern fails. Recognised intents:

| User phrase pattern | → Skill + mode |
|---|---|
| "Write a paper on X" | `quantum_paper --mode full --topic X` |
| "Guide me through writing a paper on X" | `quantum_paper --mode plan --topic X` |
| "Build a paper outline on X" | `quantum_paper --mode outline-only --topic X` |
| "I have a draft, here are reviewer comments" | `quantum_paper --mode revision` |
| "Parse these reviewer comments" | `quantum_paper --mode revision-coach` |
| "Write an abstract" | `quantum_paper --mode abstract-only` |
| "Convert this paper to PRX format" | `quantum_paper --mode format-convert --journal prx-quantum` |
| "Check the citations in this paper" | `quantum_paper --mode citation-check` |
| "Generate disclosure block" | `quantum_paper --mode disclosure` |
| "Research X" | `deep_research --mode full --topic X` |
| "Quick brief on X" | `deep_research --mode quick --topic X` |
| "Systematic review on X" | `deep_research --mode systematic-review --topic X` |
| "Guide my research on X" | `deep_research --mode socratic --topic X` |
| "Fact-check these claims" | `deep_research --mode fact-check --topic <claims>` |
| "Literature review on X" | `deep_research --mode lit-review --topic X` |
| "Review this paper" | `quantum_reviewer --mode full --draft PATH` |
| "Quick assessment of this paper" | `quantum_reviewer --mode quick --draft PATH` |
| "Guide me to improve this paper" | `quantum_reviewer --mode guided --draft PATH` |
| "Check the methodology" | `quantum_reviewer --mode methodology-focus --draft PATH` |
| "Verify the revisions" | `quantum_reviewer --mode re-review --draft PATH` |
| "Calibrate this reviewer" | `quantum_reviewer --mode calibration --draft PATH` |
| "I want to write a complete research paper on X" | `pipelines.py full --topic X` |
| "I already have a paper, review it" | `pipelines.py mid-entry-stage-2.5 --paper PATH` |
| "I received reviewer comments" | `pipelines.py mid-entry-stage-4 --paper PATH --reviewer-comments PATH` |
| "status" | `pipelines.py status` |
| "Find fallacies in this paper" | `logical_fallacies --draft PATH` |

When no pattern matches, the LLM is consulted with the user's prompt + the
recognised skills + their mode lists, and asked to return a structured
dispatch decision as JSON. The dispatcher then EITHER prints it for review
OR (with `--execute`) runs it.

## Outputs (in `--outdir`)

- `dispatch_decision.json` — `{skill, mode, flags, confidence}` keyed
  decision; the dispatcher writes this even when `--execute` is off
- `dispatch.md` — human-readable summary
- Anything the dispatched skill writes (if `--execute` was passed)
