#!/bin/bash
# hooks/stop_smoke_gate.sh — Stop hook: refuse stop until smoke gate passes.
# Only enforces during /sleep-research (active heartbeat) or when explicitly
# armed via .auto-production/audit/smoke_required marker. Otherwise the gate
# would block every cc turn from Stage 1 onwards, which is too aggressive.
set -u
REPO="${AUTO_PRODUCTION_REPO:-}"
[ -z "$REPO" ] && exit 0

# skip if not in a git repo
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# only enforce if /sleep-research is currently active, OR the user/agent
# has explicitly armed the gate (touch .auto-production/audit/smoke_required)
SLEEP_PID_FILE=.auto-production/sleep_heartbeat.pid
ARM_FILE=.auto-production/audit/smoke_required

armed=0
if [ -f "$SLEEP_PID_FILE" ] && kill -0 "$(cat "$SLEEP_PID_FILE" 2>/dev/null)" 2>/dev/null; then
  armed=1
fi
[ -f "$ARM_FILE" ] && armed=1

[ $armed -eq 0 ] && exit 0

bash "$REPO/tools/smoke_gate.sh"
