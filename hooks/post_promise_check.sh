#!/bin/bash
# hooks/post_promise_check.sh — PostToolUse: scan agent output for promises.
# Receives tool result JSON on stdin; extracts text and pipes to promise_check.py.
set -u
REPO="${AUTO_PRODUCTION_REPO:-}"
[ -z "$REPO" ] && exit 0

# extract any text output from tool_response
TEXT=$(python3 - <<'PY' || true
import json, sys
try:
    d = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)
parts = []
tr = d.get("tool_response", {})
for k in ("output", "stdout", "text"):
    v = tr.get(k)
    if isinstance(v, str):
        parts.append(v)
# also assistant message text in some hook payloads
if isinstance(d.get("text"), str):
    parts.append(d["text"])
print("\n".join(parts))
PY
)

[ -z "$TEXT" ] && exit 0

TURN_FILE=.auto-production/turn_count
TURN=$(cat "$TURN_FILE" 2>/dev/null || echo 0)
echo $((TURN + 1)) > "$TURN_FILE"

echo "$TEXT" | python3 "$REPO/tools/promise_check.py" scan --ledger promise.json --turn "$TURN" >/dev/null 2>&1 || true

exit 0
