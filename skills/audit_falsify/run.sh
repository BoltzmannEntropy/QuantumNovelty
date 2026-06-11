#!/usr/bin/env bash
# audit_falsify — stub entry point.
#
# This skill is scaffolded but not yet fully implemented in QuantumNovelty's
# initial release. It writes a placeholder output describing what a complete
# implementation would produce, so the chain can complete end-to-end.
#
# See SKILL.md for the contract this skill MUST satisfy when implemented.
set -euo pipefail
OUTDIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --outdir)
      [[ $# -ge 2 ]] || { echo "ERROR: --outdir requires a value" >&2; exit 2; }
      OUTDIR="$2"; shift 2 ;;
    *) shift ;;
  esac
done
[[ -n "$OUTDIR" ]] || { echo "ERROR: --outdir is required" >&2; exit 2; }
mkdir -p "$OUTDIR"
cat > "$OUTDIR/_PLACEHOLDER.md" <<'PLACEHOLDER'
# audit_falsify — placeholder output

This skill is scaffolded. See `SKILL.md` for the full contract.
For now, a real run would emit:
  - structured output JSON matching the schema in SKILL.md
  - human-readable summary markdown
  - `_backend_used.json` provenance marker
PLACEHOLDER
echo "audit_falsify: placeholder output written to $OUTDIR"
