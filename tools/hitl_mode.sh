#!/bin/bash
# tools/hitl_mode.sh — get / set the project HITL mode.
set -u
FILE=.auto-production/hitl_mode
mkdir -p .auto-production
VALID="full-auto gate-only checkpoint co-pilot step-by-step custom"

case "${1:-get}" in
  get)
    cat "$FILE" 2>/dev/null || echo "co-pilot"
    ;;
  set)
    M=${2:?need mode}
    echo " $VALID " | grep -q " $M " || { echo "❌ unknown mode: $M (valid: $VALID)"; exit 1; }
    echo "$M" > "$FILE"
    echo "✅ HITL mode → $M"
    ;;
  list)
    echo "$VALID" | tr ' ' '\n'
    ;;
  *)
    echo "usage: $0 {get|set <mode>|list}"; exit 2 ;;
esac
