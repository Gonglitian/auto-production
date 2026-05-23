#!/bin/bash
# hooks/pre_destructive_git.sh — PreToolUse(Bash): block destructive ops.
# Reads tool_input from stdin (Claude Code passes JSON). Exits non-zero to block.
set -u

INPUT=$(cat || true)
# tool_input.command is the bash command to be run
CMD=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    print((d.get('tool_input') or {}).get('command', ''))
except Exception:
    pass
" <<<"$INPUT")

[ -z "$CMD" ] && exit 0

DANGER_PATTERNS=(
  'rm -rf'
  'rm -fr'
  'git reset --hard'
  'git push --force'
  'git push -f '
  'git clean -fd'
  'git clean -fdx'
  'git branch -D'
  'dd if='
  'mkfs\.'
  'chmod 777 -R'
)

for p in "${DANGER_PATTERNS[@]}"; do
  if echo "$CMD" | grep -Eq "$p"; then
    echo "🛑 destructive command blocked: $p"
    echo "   command: $CMD"
    echo "   confirm by running directly (without hook) if intentional."
    exit 2   # PreToolUse non-zero blocks the tool call
  fi
done

exit 0
