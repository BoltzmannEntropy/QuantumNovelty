# Adding a skill to QuantumNovelty

A skill is a directory under `skills/`. The chain auto-discovers it; no
registration step required.

## Minimum contents

```
skills/my_new_skill/
├── SKILL.md          (required) human-readable contract
├── run.sh            (required) bash entry — chain dispatches via this
└── skill.py          (recommended) Python driver
```

Optional:
```
└── prompts/          prompt templates if the skill uses an LLM
```

## SKILL.md contract

The first markdown header in `SKILL.md` is the skill's one-line description
(used by `chain/run.sh --list-skills`).

The body should cover at minimum:
- **CLI surface**: every flag the run.sh accepts
- **Inputs**: required + optional files/JSON/strings, with schema
- **Outputs**: every file the skill writes to `--outdir`, with schema
- **LLM use**: whether the skill calls an LLM; which prompt template
- **Constraints / failure modes**: what the skill explicitly does NOT do

## run.sh contract

Required CLI surface (all skills must accept these):
- `--outdir DIR` — output directory (chain always provides this)
- `--llm MODEL` — backend ID (passed through to `skills/common/llm.py`)

Skill-specific flags follow. Use long forms (`--input-file`, not `-i`) for
chain composition clarity.

Skeleton:
```bash
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/skill.py" "$@"
```

## skill.py — using the LLM backend

```python
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker

def main():
    # ... parse args ...
    result = call_llm(prompt, backend=args.llm, timeout=600)
    out.write_text(result.text)
    write_backend_marker(outdir, result)  # provenance for audit gates
```

`call_llm` raises `RuntimeError` on failure. Do NOT catch it and silently
swap to a different backend — silent backend swaps are explicitly forbidden
by the framework's design. Supported backend ids are centralized in
`skills/common/llm.py`; currently `claude`, `codex`, `codex-acp`,
`codex-mcp`, `kimi` / `kimi-*` / `moonshot*`, and `anthropic-api`.

## Output schema convention

Every skill writes to `--outdir`:
- `*.json` for structured outputs (the actual results)
- `*.md` for human-readable summaries
- `_backend_used.json` for provenance (automatic via `write_backend_marker`)
- `full_prompt_*.txt` for the prompt that was sent
- `_llm_generation.log` for the LLM response

Downstream skills read your `*.json` outputs by exact path. Document the path
in your SKILL.md so callers know what to consume.

## Test seam

For tests, set `QUANTUMNOVELTY_LLM_STUB=/path/to/canned_response.txt` in the
test fixture. `call_llm` will return the file contents verbatim without
running any subprocess. The `backend_actually_used` field on the result will
read `"stub"` so production code can tell a stubbed run apart from a real one.

## Common pitfalls

- **Don't `subprocess.run(["claude", ...])` directly.** Always go through
  `call_llm`. Direct subprocess calls bypass the isolation playbook and will
  silently fall back to the API path if `ANTHROPIC_API_KEY` is in scope.
- **Don't hand-roll Kimi HTTP calls in a skill.** `call_llm(..., backend="kimi")`
  loads `kikm.sh` / `KIMI_ENV_FILE`, sends Moonshot's required `thinking`
  request field, and writes normal backend provenance.
- **Don't write provenance manually.** Use `write_backend_marker` so the
  schema stays consistent across skills.
- **Don't depend on cross-stage state.** Read what you need from the prior
  stage's `*.json` outputs; declare it in your SKILL.md.
- **Don't hardcode a model snapshot.** Take `--llm` and pass it through.

## Example: a 30-line skill

A minimal skill that calls an LLM with a templated prompt and writes one
markdown output:

```python
# skills/my_minimal/skill.py
import argparse, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "common"))
from llm import call_llm, write_backend_marker

PROMPT = "Explain {topic} in three sentences for a physicist."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--llm", default="claude")
    ap.add_argument("--topic", required=True)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    result = call_llm(PROMPT.format(topic=args.topic), backend=args.llm)
    (args.outdir / "explanation.md").write_text(result.text)
    write_backend_marker(args.outdir, result)
    print(f"my_minimal: wrote explanation.md ({len(result.text)} chars)")

if __name__ == "__main__":
    sys.exit(main())
```

That's a complete skill. Drop it under `skills/my_minimal/` with a `run.sh`
shim and a `SKILL.md`, and the chain will discover it.
