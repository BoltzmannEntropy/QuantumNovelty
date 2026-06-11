# `process_summary` — Stage 6 process record with 6-dimension CQE scoring

The terminating skill of a complete QuantumNovelty pipeline. Reads every
prior stage's outputs (literature → discovery → cross-LLM → novelty-audit →
draft → review), reconstructs the process timeline, and scores the run on
six dimensions of Collaboration Quality (1-100 each).

## Six dimensions

| Dim | Name | Probes | High score = |
|---|---|---|---|
| 1 | **Novelty rigour** | augmented baseline catalog used? strict-domination applied? rediscovery candidly classified? | Did the framework's novelty machinery actually run, or was it bypassed? |
| 2 | **Reproducibility** | `audit_claims.py` present? exits clean? every claim re-derivable from on-disk JSON? code emitted in a real quantum library? | Can a reviewer re-derive the paper without the author's intervention? |
| 3 | **Methodological rigour** | multi-seed runs? Wilson CIs? ablations (LLM-mutator on/off etc.)? float64 reference path? | Would the methodology-focus reviewer pass this paper? |
| 4 | **Falsifiability** | cross-LLM with different vendors? predictions before truth? honest negatives section? | Is the claim structured so it can be refuted? |
| 5 | **Domain depth** | Hamiltonian construction explicit? mapping justified? active space justified? simulator precision floor disclosed? | Does the paper show deep quantum-CS understanding or surface-level use? |
| 6 | **Communication** | abstract / body / conclusion claim-aligned? logical fallacies absent? required-statements present per venue? | Will the paper read coherently to a domain expert? |

Scores are 1-100; sub-scores per probe are 1-100 with linear weighting.
Final composite is the geometric mean (so a 99 on five dimensions and a 30
on the sixth doesn't average away the weakness).

## CLI

```
process_summary/run.sh \
  --run-dir DIR                  # the chain's run output root
  --outdir DIR                   # where to write the summary
  [--llm BACKEND]
```

## Inputs read from `--run-dir`

The skill walks the run directory and looks for these prior-stage outputs:
- `literature_surfacer/baseline_catalog.json`
- `pareto_explorer/archive.json`
- `cross_llm_prediction/results.json`
- `novelty_audit/novelty_verdict.json`, `audit_claims.py`,
  `failure_modes_required.md`, `wilson_annotations.md`, `ratio_recompute.md`
- `ablation_designer/ablation_results.json`
- `quantum_paper/paper.tex`
- `quantum_reviewer/review_panel.md`
- `logical_fallacies/fallacy_findings.json`

Anything absent contributes to a lower score on the relevant dimension —
the framework's discipline scores based on what ran, not on the author's
self-assessment.

## Outputs (in `--outdir`)

- `process_summary.md` — 6-dimension narrative + composite verdict
- `cqe_scores.json` — per-dimension and composite scores (machine-readable)
- `process_timeline.md` — chronological reconstruction of which stages ran,
  in what order, with elapsed time per stage
- `_backend_used.json`
- `full_prompt.txt`
- `_llm_generation.log`

## Composite-score interpretation

| Composite | Interpretation |
|---|---|
| 90-100 | The framework's discipline was fully exercised; the paper should survive strict peer review. |
| 75-89 | Solid; specific gaps named in the report. |
| 60-74 | Material gaps in 1-2 dimensions; revision needed before submission. |
| 40-59 | Structural gaps; the run did not use the framework's machinery as intended. |
| <40 | The composite is low because at least one dimension scored very low; that dimension is the bottleneck. |

## Why composite is geometric, not arithmetic

A paper that's 99/100 on Reproducibility but 30/100 on Falsifiability has a
publication-blocking weakness — falsifiability is not optional. Geometric
mean penalises low dimensions; arithmetic mean would let a high score in
five dimensions paper over a fatal flaw in the sixth.
