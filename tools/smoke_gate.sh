#!/bin/bash
# tools/smoke_gate.sh — Stop-hook check: only allow stop if smoke passed
# for current HEAD commit.
set -u
PASSED=.auto-production/audit/smoke_passed.json
HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo "no-git")
if [ ! -f "$PASSED" ]; then
  echo "❌ smoke gate: $PASSED missing — run /smoke-test before stopping"
  exit 1
fi
GOT=$(python3 -c "import json,sys; print(json.load(open('$PASSED')).get('commit',''))" 2>/dev/null)
if [ "$GOT" != "$HEAD" ]; then
  echo "❌ smoke gate: smoke passed for $GOT but HEAD is $HEAD — re-run /smoke-test"
  exit 1
fi
echo "✅ smoke gate: passed for $HEAD"
exit 0
