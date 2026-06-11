#!/usr/bin/env bash
# Drive the full QN pipeline on one avenue.
#
# Usage: run_avenue.sh <avenue_slug> <topic> <journal> <quantum_lib>
#
# Stages:
#   4   quantum_paper --mode full        → paper.tex
#   4*  pdflatex paper.tex               → paper.pdf
#   5   quantum_reviewer --mode full     → review_panel.md
#   5b  logical_fallacies                → fallacy_findings.json
#   6   process_summary                  → cqe_scores.json + process_summary.md
set -euo pipefail

SLUG="${1:?avenue slug required}"
TOPIC="${2:?topic required}"
JOURNAL="${3:-prx-quantum}"
LIB="${4:-qiskit}"

QN=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)   # repo root, derived
RUN=$QN/examples/end_to_end/avenue_${SLUG}
mkdir -p $RUN/{stage_4_draft,stage_5_review,stage_5b_fallacies,stage_6_summary}

LOG=$RUN/_run.log
exec > >(tee -a $LOG) 2> >(tee -a $LOG >&2)

echo "==============================================================="
echo "AVENUE $SLUG"
echo "  Topic:   $TOPIC"
echo "  Journal: $JOURNAL"
echo "  Lib:     $LIB"
echo "  Run:     $RUN"
echo "==============================================================="

# ---- Stage 4: paper draft -----------------------------------------------
echo
echo "### STAGE 4: quantum_paper --mode full"
t0=$(date +%s)
bash $QN/skills/quantum_paper/run.sh --mode full \
  --topic "$TOPIC" \
  --journal "$JOURNAL" --quantum-lib "$LIB" \
  --outdir $RUN/stage_4_draft \
  --llm claude
echo "  elapsed: $(($(date +%s) - t0))s"

# ---- Stage 4*: compile to PDF --------------------------------------------
echo
echo "### STAGE 4*: pdflatex"
cd $RUN/stage_4_draft
# strip any LLM-emitted fenced code blocks that aren't valid LaTeX preamble
# (defensive: real LLM output usually has the full preamble)
if [[ -f paper.tex ]]; then
  # First pass: try compile as-is
  pdflatex -interaction=nonstopmode -halt-on-error paper.tex > pdflatex.log 2>&1 || true
  pdflatex -interaction=nonstopmode -halt-on-error paper.tex > pdflatex.log 2>&1 || true
  if [[ -f paper.pdf ]]; then
    pages=$(pdfinfo paper.pdf 2>/dev/null | awk '/Pages:/{print $2}')
    size=$(wc -c < paper.pdf)
    echo "  paper.pdf written: ${pages:-?} pages, ${size} bytes"
  else
    echo "  WARN: pdflatex did not produce paper.pdf; see pdflatex.log"
    echo "  (the .tex source is still saved; reviewer panel will run on it)"
  fi
fi
cd $QN

# ---- Stage 5: reviewer panel --------------------------------------------
echo
echo "### STAGE 5: quantum_reviewer --mode full"
t0=$(date +%s)
bash $QN/skills/quantum_reviewer/run.sh --mode full \
  --draft $RUN/stage_4_draft/paper.tex \
  --journal "$JOURNAL" \
  --outdir $RUN/stage_5_review \
  --llm claude
echo "  elapsed: $(($(date +%s) - t0))s"

# ---- Stage 5b: logical fallacies ----------------------------------------
echo
echo "### STAGE 5b: logical_fallacies"
t0=$(date +%s)
bash $QN/skills/logical_fallacies/run.sh \
  --draft $RUN/stage_4_draft/paper.tex \
  --outdir $RUN/stage_5b_fallacies \
  --llm claude || echo "  (fallacies stage failed; continuing)"
echo "  elapsed: $(($(date +%s) - t0))s"

# ---- Stage 6: process summary (CQE) -------------------------------------
echo
echo "### STAGE 6: process_summary (CQE)"
bash $QN/skills/process_summary/run.sh \
  --run-dir $RUN \
  --outdir $RUN/stage_6_summary \
  --no-llm-narrative
cqe=$(python3 -c "import json; print(json.load(open('$RUN/stage_6_summary/cqe_scores.json'))['composite'])")
echo "  CQE composite: ${cqe}/100"

# ---- Wrap up ------------------------------------------------------------
echo
echo "==============================================================="
echo "AVENUE $SLUG COMPLETE"
echo "  CQE composite: ${cqe}/100"
echo "  Outputs: $RUN"
echo "==============================================================="
