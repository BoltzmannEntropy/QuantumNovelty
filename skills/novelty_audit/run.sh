#!/usr/bin/env bash
# novelty_audit skill — bash entry point.
#
# Translates the chain's calling convention into the Python driver's argparse.
# See SKILL.md for the full CLI surface.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/skill.py" "$@"
