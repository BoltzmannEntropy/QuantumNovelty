#!/usr/bin/env bash
# QN-native two-paper novelty pipeline (chain-runner version).
#
# Fetches Flow-VQE (arXiv:2507.01726, npj Quantum Information) and
# LCU-Trotter (arXiv:2212.04566, PRX Quantum) from arXiv, extracts text,
# and routes each paper through the QuantumNovelty `chain/run.sh
# --pipeline paper-audit` orchestrator — the same chain runner you'd
# use directly. This script is intentionally thin; the chain is the
# product, the bash here is just glue.
#
# Pipeline preset:  paper-audit (default-on stages: research, reviewer,
#                                 fallacies, cqe).
# Backend:          claude (Claude Code CLI; the framework default).
#                   Nested-CLI isolation (scrubbed env + neutral cwd +
#                   --no-session-persistence) is handled by
#                   skills/common/llm.py. Override with QN_LLM=codex only
#                   for cross-vendor falsifiability runs.
# Stage toggles:    available via --skip-X / --with-X.
#                   This script keeps all four default-on stages; the
#                   chain config (which flags were honored) is captured
#                   in _chain_config.json under each paper's outdir and
#                   surfaced in the final PIPELINE_REPORT.pdf.
#
# Pass-through:     any extra arguments to this script are forwarded to
#                   chain/run.sh. To skip stages:
#                     ./run_two_papers.sh --skip-fallacies
#                     ./run_two_papers.sh --skip-research --skip-cqe
#                     ./run_two_papers.sh --with-cross-llm \
#                          --hamiltonian H2 --geometry-sweep "R=0.7,0.9,1.1 A" \
#                          --llms claude,codex
#
# Equivalent direct command (per paper):
#
#   bash $QN/chain/run.sh \
#     --pipeline paper-audit \
#     --llm claude \
#     --paper $RUN/inputs/flowvqe.txt \
#     --journal npj-quantum-information \
#     --topic "Generative flow-based warm start of the VQE" \
#     --outdir $RUN/reports/flowvqe
#
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
QN=$(cd "$HERE/../../.." && pwd)   # repo root, derived — no hardcoded path
RUN=$HERE/_run
mkdir -p $RUN/inputs $RUN/reports

LOG=$HERE/_run.log
exec > >(tee -a $LOG) 2> >(tee -a $LOG >&2)

# Papers
PAPER_A_TAG="flowvqe"
PAPER_A_ARXIV="2507.01726"
PAPER_A_TITLE="Generative flow-based warm start of the VQE"
PAPER_A_VENUE="npj-quantum-information"

PAPER_B_TAG="lcutrotter"
PAPER_B_ARXIV="2212.04566"
PAPER_B_TITLE="Simple and high-precision Hamiltonian simulation by compensating Trotter error with LCU"
PAPER_B_VENUE="prx-quantum"

EXTRA_FLAGS=("$@")
LLM="${QN_LLM:-claude}"

# ---- Stage 0: fetch + extract ------------------------------------------
fetch_paper() {
  local tag="$1" arxiv_id="$2"
  local pdf=$RUN/inputs/${tag}.pdf
  local txt=$RUN/inputs/${tag}.txt
  if [[ ! -s $pdf ]]; then
    echo "[fetch] $tag: arXiv $arxiv_id"
    curl -fsSL "https://arxiv.org/pdf/${arxiv_id}" -o "$pdf" \
      || { rm -f "$pdf"; echo "ERROR: arXiv fetch failed for $arxiv_id" >&2; exit 1; }
  fi
  if [[ ! -s $txt ]]; then
    echo "[extract] $tag: pdftotext"
    pdftotext -layout $pdf $txt
  fi
  local nw=$(wc -w < $txt)
  echo "[ok]    $tag: $(wc -c < $pdf) bytes PDF, $nw words text"
}

fetch_paper "$PAPER_A_TAG" "$PAPER_A_ARXIV"
fetch_paper "$PAPER_B_TAG" "$PAPER_B_ARXIV"

# ---- Per-paper chain run ------------------------------------------------
analyze_paper() {
  local tag="$1" title="$2" venue="$3"
  local txt=$RUN/inputs/${tag}.txt
  local out=$RUN/reports/${tag}

  echo
  echo "==============================================================="
  echo "CHAIN: pipeline=paper-audit  paper=$tag  backend=$LLM"
  echo "  Title: $title"
  echo "  Venue: $venue"
  echo "  Outdir: $out"
  if [[ ${#EXTRA_FLAGS[@]} -gt 0 ]]; then
    echo "  Stage toggles: ${EXTRA_FLAGS[*]}"
  fi
  echo "==============================================================="

  mkdir -p $out
  bash $QN/chain/run.sh \
    --pipeline paper-audit \
    --llm $LLM \
    --paper $txt \
    --topic "$title" \
    --journal "$venue" \
    --outdir $out \
    "${EXTRA_FLAGS[@]+"${EXTRA_FLAGS[@]}"}"
}

analyze_paper "$PAPER_A_TAG" "$PAPER_A_TITLE" "$PAPER_A_VENUE"
analyze_paper "$PAPER_B_TAG" "$PAPER_B_TITLE" "$PAPER_B_VENUE"

# ---- Stage 5: build comparison report + token ledger -------------------
echo
echo "### Stage 5: comparison report + token ledger"
python3 $HERE/build_report.py --run-dir $RUN \
  --paper-a $PAPER_A_TAG --paper-a-title "$PAPER_A_TITLE" \
  --paper-a-arxiv $PAPER_A_ARXIV --paper-a-venue $PAPER_A_VENUE \
  --paper-b $PAPER_B_TAG --paper-b-title "$PAPER_B_TITLE" \
  --paper-b-arxiv $PAPER_B_ARXIV --paper-b-venue $PAPER_B_VENUE \
  --out $RUN/PIPELINE_REPORT.tex

# ---- Stage 6: compile to PDF -------------------------------------------
echo
echo "### Stage 6: compile to PDF (lualatex; UTF-8 native)"
cd $RUN
lualatex -interaction=nonstopmode PIPELINE_REPORT.tex > pdflatex.log 2>&1 || true
lualatex -interaction=nonstopmode PIPELINE_REPORT.tex > pdflatex.log 2>&1 || true
if [[ -s PIPELINE_REPORT.pdf ]]; then
  echo "PDF: $(pdfinfo PIPELINE_REPORT.pdf 2>/dev/null | awk '/Pages:/{print $2}') pages, $(wc -c < PIPELINE_REPORT.pdf) bytes"
else
  echo "PDF compile failed; first error:"
  grep -E "^!" pdflatex.log | head -3 || true
fi

echo
echo "==============================================================="
echo "DONE"
echo "  Outputs:       $RUN"
echo "  Chain config:  $RUN/reports/*/_chain_config.json"
echo "  Report:        $RUN/PIPELINE_REPORT.pdf"
echo "==============================================================="
