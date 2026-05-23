#!/bin/bash
# tools/stall_watch.sh — background watchdog. Watches heartbeat file mtime.
# Usage: stall_watch.sh <pid> <timeout_seconds> <action>
#   action: ping | abort | meta

set -u
PID=${1:?need pid}
TIMEOUT=${2:-600}
ACTION=${3:-ping}
HEARTBEAT="${HEARTBEAT_FILE:-.auto-production/heartbeat}"
INTERVAL=30

while kill -0 "$PID" 2>/dev/null; do
  if [ -f "$HEARTBEAT" ]; then
    HB=$(stat -c %Y "$HEARTBEAT" 2>/dev/null || echo 0)
  else
    HB=0
  fi
  NOW=$(date +%s)
  AGE=$((NOW - HB))
  if [ "$AGE" -gt "$TIMEOUT" ]; then
    TS=$(date -Iseconds)
    case "$ACTION" in
      ping)
        echo "[$TS] ⚠️  Stall detected (no heartbeat for ${AGE}s, threshold ${TIMEOUT}s)"
        # Best-effort desktop notify, ignore if missing
        command -v notify-send >/dev/null && notify-send "Auto-Production stall" "Agent silent for ${AGE}s"
        ;;
      abort)
        echo "[$TS] 🛑 Aborting PID $PID after ${AGE}s stall"
        kill -INT "$PID"; sleep 5; kill -KILL "$PID" 2>/dev/null
        ;;
      meta)
        mkdir -p .auto-production/meta_opt
        echo "{\"event\":\"stall\",\"at\":\"$TS\",\"pid\":$PID,\"age_s\":$AGE}" \
          >> .auto-production/meta_opt/signals.jsonl
        ;;
    esac
    break
  fi
  sleep "$INTERVAL"
done
