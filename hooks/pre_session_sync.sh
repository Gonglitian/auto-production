#!/bin/bash
# hooks/pre_session_sync.sh — SessionStart: pull latest skills + verify env.
set -u

REPO="${AUTO_PRODUCTION_REPO:-}"
if [ -z "$REPO" ] || [ ! -d "$REPO" ]; then
  echo "ℹ️  AUTO_PRODUCTION_REPO not set or missing — hooks degraded"
  exit 0
fi

# 1. Fast `git pull` (skip if dirty)
if [ -d "$REPO/.git" ]; then
  if git -C "$REPO" diff --quiet 2>/dev/null && git -C "$REPO" diff --cached --quiet 2>/dev/null; then
    git -C "$REPO" pull --quiet --ff-only 2>/dev/null || true
  fi
fi

# 2. Bootstrap project dir
mkdir -p .auto-production/{audit,cache/citations,meta_opt,baseline}

# 3. Re-arm stall watcher if /sleep-research was active
if [ -f .auto-production/sleep_heartbeat.pid ]; then
  PID=$(cat .auto-production/sleep_heartbeat.pid 2>/dev/null)
  if ! kill -0 "$PID" 2>/dev/null; then
    rm -f .auto-production/sleep_heartbeat.pid
    echo "ℹ️  prior /sleep-research heartbeat is gone; restart with /sleep-research if intended"
  fi
fi

exit 0
