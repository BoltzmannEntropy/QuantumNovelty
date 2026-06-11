# `novelty_audit` — the audit-and-falsify framework

**This is the one new skill QuantumNovelty contributes on top of ARC + ARS.**

A six-step pipeline that takes a Pareto archive of LLM-discovered ansätze + a manuscript draft, augments the baseline catalog with current published methods, re-runs the strict-domination comparator at calibrated `float64` tolerances, recomputes every ratio in the draft from raw JSON, annotates small-sample rates with Wilson 95 % CIs, and either returns a `novel | rediscovery | interpolation` verdict per claim or refuses to sign off until the manuscript adds a `Failure Modes` section listing the honest negatives.

## When to use

After you have run `pareto_explorer` (or any LLM-in-loop discovery pipeline) and you have a draft manuscript that claims novelty for one or more of the discovered points. Before submission. Not optional.

## CLI surface

```bash
skills/novelty_audit/run.sh \
  --pareto-archive  PATH       # JSON from pareto_explorer
  --augmented-baselines PATH   # JSON from literature_surfacer
  --draft           PATH       # .tex / .md / .docx
  --hamiltonian-id  STR        # e.g. "H2O_4e_4o_8q"
  --outdir          DIR
  --llm             MODEL      # default: claude
  [--strict-eps-abs FLOAT]     # default: 1e-12 (float64 noise floor)
  [--strict-eps-rel FLOAT]     # default: 1e-9
  [--small-sample-threshold N] # default: 30 (Wilson CIs added below this)
  [--require-failure-modes]    # default: true
```

## Inputs

1. **`--pareto-archive`**: JSON in the shape

```json
{
  "hamiltonian_id": "H2O_4e_4o_8q",
  "rows": [
    {"label": "UCCSD-1-Trotter",
     "energy_ha": -74.97080, "params": 14, "ops": 3668, "cnots": 1472,
     "source": "baseline"},
    {"label": "LLM-gen3-s2",
     "energy_ha": -74.96332, "params": 32, "ops": 53,  "cnots": 21,
     "source": "llm", "prompt_hash": "...", "model": "claude-sonnet-4-..."}
  ]
}
```

2. **`--augmented-baselines`**: JSON in the same `rows[]` shape, each row representing a recent published method on the same Hamiltonian configuration. Produced by `literature_surfacer`.

3. **`--draft`**: the manuscript. Plain-text scan for ratio claims (e.g., `14.1\\times`), small-sample rates (e.g., `5/5`, `4 of 5`), and Pareto-position claims (e.g., `strictly dominates`).

## Outputs (in `--outdir`)

| File | Contents |
|---|---|
| `novelty_verdict.json` | Per-claim verdict: `novel` / `interpolation` / `strict-domination` / `rediscovery`. Each verdict carries the comparator's per-axis ε used and the cite key of the augmented baseline that flipped the verdict (if any). |
| `augmented_pareto.json` | The full Pareto archive after merge with augmented baselines, with strict-domination edges recomputed. |
| `ratio_recompute.md` | Every ratio claim in the draft, with the displayed value and the from-raw-JSON value side-by-side. Discrepancies > 0.5 % are highlighted. |
| `wilson_annotations.md` | Every "K of N" rate in the draft, annotated with Wilson 95 % interval. |
| `failure_modes_required.md` | If the augmented baselines surfaced rows the LLM discovery did not dominate, this file lists them as "honest negatives" the manuscript must include. The skill exits rc=2 if `--require-failure-modes` is set and these are missing from the draft. |
| `audit_claims.py` | A re-runnable Python script that re-derives every numerical claim in the draft from on-disk JSON. Drop into `paper/`, run before every commit, exits 0 iff all claims match. |
| `_backend_used.json` | Backend provenance for `audit_backend_fidelity`. |

## Verdict semantics

The novelty verdict is per-row in the LLM-discovered set, against the **augmented** (baseline ∪ literature) catalog.

| Verdict | Condition |
|---|---|
| `strict-domination` | The LLM row Pareto-dominates **every** augmented row by at least one axis at strict ε. Genuine novelty win — write the paper. |
| `interpolation` | The LLM row sits on the augmented Pareto front but is not strictly dominant over any baseline at strict ε (lies "between" two baselines on different axes). Honest, qualified novelty — paper should report it as such. |
| `rediscovery` | An augmented baseline strictly dominates the LLM row at strict ε. The "discovery" reproduces or under-performs a known method. NOT a novelty win. |
| `dominated` | A baseline strictly dominates on every axis. Worse than known art. |

## The six steps in detail

### 1. Augmented-baseline merge

Concatenate `pareto-archive.rows` and `augmented-baselines.rows`. Tag each row with `source ∈ {baseline, llm, literature}`. The literature rows came from `literature_surfacer` which ran the day-of, so the baseline catalog reflects **current** published art, not a snapshot from training data.

### 2. Strict-domination comparator at calibrated ε

For row A to strictly dominate row B at tolerances (ε_abs, ε_rel):

```
A dominates B  iff  ∀ axis i: m_i^A ≤ m_i^B + ε_abs + ε_rel * max(|m_i^A|, |m_i^B|)
                    AND      ∃ axis i: m_i^A < m_i^B - ε_abs
```

Default ε calibrated to `float64` accumulation noise — the empirically observed floor of UCCSD@zero-amplitudes recovering Hartree-Fock energy in a NumPy reference path is ~1.7×10⁻¹¹ Ha, so `ε_abs=1e-12` is one order below the noise; `ε_rel=1e-9` is conservative against relative error in any single comparison.

### 3. Recompute-derived-ratios-from-raw

Scan the draft for `\d+(\.\d+)?\s*[×x]` patterns. For each, look up the numerator and denominator in the Pareto archive (e.g., `198 / 14 = 14.1×` → `UCCSD.ops / LLM.ops`), recompute from the raw JSON values, and emit a side-by-side comparison.

Catches the rounding-induced ratio drift that crept into 5 places in the example paper before this check existed.

### 4. Wilson 95 % CIs on small-sample rates

For every `K / N` or `K of N` with N < `--small-sample-threshold` (default 30), compute the Wilson score interval at 95 %. Write a one-line annotation next to the claim. If the CI lower bound is < 0.7 for a "100 %" claim, surface a Sev-3 finding.

### 5. Honest-negatives enforcement

If the augmented baselines include rows the LLM-discovered set did not dominate (rediscoveries OR cases where the LLM did not even attempt because the run terminated early), generate `failure_modes_required.md` listing them. If `--require-failure-modes=true` and the draft does not have a `Failure Modes` (or equivalent) section, exit rc=2.

### 6. Audit script generation

Emit a re-runnable `audit_claims.py` mapping each claim in the draft to its on-disk JSON source. Drop into the paper directory; run before every git commit; if any claim diverges, the script exits non-zero.

A 76-check audit script generated by this skill against the framework's motivating manuscript (in development; to be released with that paper's repository) validates the approach end-to-end.

## Prompt template

The LLM is consulted at two points in the pipeline:

1. **Interpolation vs novelty classification** (step 2): for borderline rows where the strict comparator says "neither dominates", the LLM gets the row, the dominated/dominating baselines, and a short prompt asking whether the LLM-discovered point provides a genuinely new trade-off or just sits between two known points. The classification is gated on having a structural argument; no LLM verdict alone moves the row from `interpolation` to `strict-domination`.

2. **Failure-modes drafting** (step 5): given the list of un-dominated baselines, the LLM drafts a `Failure Modes` section in the manuscript's voice. The drafted section requires human approval before commit; the skill flags it as `_DRAFT_REQUIRES_REVIEW`.

Both prompts are in `prompts/` next to this file.

## Why this skill is the contribution

ARC has gate-stack quality control. ARS has the modular skill pattern. Neither has a falsifiable novelty audit: both will happily declare a discovery `novel` if the human author asserts it, with no programmatic check against current literature, no strict-domination comparator, no ratio recompute, no Wilson CI annotation, no honest-negatives enforcement.

`novelty_audit` is the missing piece for any LLM-in-the-loop scientific-discovery system that wants to publish a result that survives peer review. The skill makes "novel" a property that can be falsified — and refuses to sign off until the falsification attempts (augmented baseline merge + ratio recompute + small-sample CIs + honest negatives) have all run.
