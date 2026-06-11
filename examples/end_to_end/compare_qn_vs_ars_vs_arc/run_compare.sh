#!/usr/bin/env bash
# Three-way head-to-head: run the SAME paper through:
#   1. QN's paper-audit chain               (4 stages)
#   2. ARS's academic-paper-reviewer skill   (7-agent orchestration)
#   3. ARC's peer_review + quality_gate      (2-stage review subset of
#                                              the full 23-stage pipeline)
#
# Paper: LCU-Trotter (arXiv:2212.04566, PRX Quantum) — already in the
#        two_paper_novelty run cache (QN resumes; ARS + ARC pay LLM cost).
#
# Backend: claude (Claude Code CLI; the framework default). Same backend
#          for all three frameworks so the comparison is like-for-like.
#          Override with QN_LLM=codex for cross-vendor runs.
#
# Outputs:
#   _run/qn/    — QN paper-audit chain output (4 stages, stage telemetry)
#   _run/ars/   — ARS academic-paper-reviewer output (7 agents)
#   _run/arc/   — ARC review output (2 stages)
#   _run/COMPARE_REPORT.pdf  — three-way comparison
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
QN=$(cd "$HERE/../../.." && pwd)   # repo root, derived — no hardcoded path

# Sibling frameworks for the head-to-head. Override via env if cloned
# elsewhere; the drivers print a clean error if these are missing.
if [[ -z "${ARS_REPO:-}" ]]; then
  for c in "$QN/../academic-research-skills" "$QN/../../academic-research-skills"; do
    [[ -d "$c" ]] && ARS_REPO="$c" && break
  done
fi
if [[ -z "${ARC_REPO:-}" ]]; then
  for c in "$QN/../AutoResearchClaw" "$QN/../../AutoResearchClaw"; do
    [[ -d "$c" ]] && ARC_REPO="$c" && break
  done
fi
export ARS_REPO="${ARS_REPO:-$QN/../academic-research-skills}"
export ARC_REPO="${ARC_REPO:-$QN/../AutoResearchClaw}"
[[ -d "$ARS_REPO" ]] || { echo "ERROR: academic-research-skills not found at $ARS_REPO — clone it or set ARS_REPO" >&2; exit 2; }
[[ -d "$ARC_REPO" ]] || { echo "ERROR: AutoResearchClaw not found at $ARC_REPO — clone it or set ARC_REPO" >&2; exit 2; }
RUN=$HERE/_run
mkdir -p $RUN/inputs $RUN/qn $RUN/ars $RUN/arc

LOG=$HERE/_run.log
exec > >(tee -a $LOG) 2> >(tee -a $LOG >&2)

# Paper
PAPER_TAG="lcutrotter"
PAPER_ARXIV="2212.04566"
PAPER_TITLE="Simple and high-precision Hamiltonian simulation by compensating Trotter error with LCU"
PAPER_VENUE="prx-quantum"

# Reuse the LCU-Trotter input from the two_paper run if it exists.
SRC_INPUTS=$QN/examples/end_to_end/two_paper_novelty/_run/inputs
if [[ -s $SRC_INPUTS/${PAPER_TAG}.pdf ]]; then
  cp "$SRC_INPUTS/${PAPER_TAG}.pdf" $RUN/inputs/
  if [[ -s $SRC_INPUTS/${PAPER_TAG}.txt ]]; then
    cp "$SRC_INPUTS/${PAPER_TAG}.txt" $RUN/inputs/
  else
    pdftotext -layout "$RUN/inputs/${PAPER_TAG}.pdf" "$RUN/inputs/${PAPER_TAG}.txt"
  fi
  echo "[reuse] PDF + text from two_paper_novelty run"
else
  echo "[fetch] $PAPER_TAG: arXiv $PAPER_ARXIV"
  curl -fsSL "https://arxiv.org/pdf/${PAPER_ARXIV}" -o "$RUN/inputs/${PAPER_TAG}.pdf" \
    || { rm -f "$RUN/inputs/${PAPER_TAG}.pdf"; echo "ERROR: arXiv fetch failed" >&2; exit 1; }
  pdftotext -layout "$RUN/inputs/${PAPER_TAG}.pdf" "$RUN/inputs/${PAPER_TAG}.txt"
fi
echo "[ok] $(wc -c < $RUN/inputs/${PAPER_TAG}.pdf) bytes PDF, $(wc -w < $RUN/inputs/${PAPER_TAG}.txt) words text"

LLM="${QN_LLM:-claude}"

echo
echo "==============================================================="
echo "PARALLEL RUN — paper=$PAPER_TAG  backend=$LLM"
echo "==============================================================="

# -------- QN paper-audit chain --------------------------------------
echo
echo "### QN paper-audit chain"
SRC_QN=$QN/examples/end_to_end/two_paper_novelty/_run/reports/${PAPER_TAG}
if [[ -d $SRC_QN ]]; then
  echo "[reuse] copying existing QN paper-audit outputs from two_paper_novelty run"
  rsync -a $SRC_QN/ $RUN/qn/ 2>/dev/null || cp -R $SRC_QN/. $RUN/qn/
fi

bash $QN/chain/run.sh \
  --pipeline paper-audit \
  --llm $LLM \
  --paper $RUN/inputs/${PAPER_TAG}.txt \
  --topic "$PAPER_TITLE" \
  --journal "$PAPER_VENUE" \
  --outdir $RUN/qn 2>&1 | tail -10

# -------- ARS academic-paper-reviewer --------------------------------
echo
echo "### ARS academic-paper-reviewer"
python3 $HERE/ars_driver.py \
  --paper $RUN/inputs/${PAPER_TAG}.txt \
  --title "$PAPER_TITLE" \
  --venue "$PAPER_VENUE" \
  --outdir $RUN/ars \
  --llm $LLM 2>&1 | tail -10

# -------- ARC peer_review + quality_gate -----------------------------
echo
echo "### ARC peer_review + quality_gate"
python3 $HERE/arc_driver.py \
  --paper $RUN/inputs/${PAPER_TAG}.txt \
  --title "$PAPER_TITLE" \
  --venue "$PAPER_VENUE" \
  --topic "$PAPER_TITLE" \
  --outdir $RUN/arc \
  --llm $LLM 2>&1 | tail -10

# -------- Build comparison PDF ---------------------------------------
echo
echo "### Build COMPARE_REPORT.pdf"
python3 $HERE/build_compare_report.py \
  --run-dir $RUN \
  --paper-tag $PAPER_TAG \
  --paper-title "$PAPER_TITLE" \
  --paper-arxiv $PAPER_ARXIV \
  --paper-venue $PAPER_VENUE \
  --backend $LLM \
  --out $RUN/COMPARE_REPORT.tex

cd $RUN
lualatex -interaction=nonstopmode COMPARE_REPORT.tex > lualatex.log 2>&1 || true
lualatex -interaction=nonstopmode COMPARE_REPORT.tex > lualatex.log 2>&1 || true
if [[ -s COMPARE_REPORT.pdf ]]; then
  echo "PDF: $(pdfinfo COMPARE_REPORT.pdf 2>/dev/null | awk '/Pages:/{print $2}') pages, $(wc -c < COMPARE_REPORT.pdf) bytes"
else
  echo "PDF compile failed; first error:"
  grep -E "^!" lualatex.log | head -3 || true
fi

echo
echo "==============================================================="
echo "DONE"
echo "  Outputs:        $RUN"
echo "  QN outputs:     $RUN/qn/"
echo "  ARS outputs:    $RUN/ars/"
echo "  ARC outputs:    $RUN/arc/"
echo "  Comparison PDF: $RUN/COMPARE_REPORT.pdf"
echo "==============================================================="
