#!/bin/bash
# tools/simplify_gate.sh — scan source files; warn at SOFT, block at HARD.
set -u
SOFT=${SOFT_LIMIT:-400}
HARD=${HARD_LIMIT:-800}
warn=0; fail=0

# only check tracked source files (skip generated / build dirs)
git ls-files '*.py' '*.ts' '*.tsx' '*.js' '*.jsx' '*.go' '*.rs' '*.java' '*.kt' '*.cpp' '*.c' 2>/dev/null | \
while read -r f; do
  [ -f "$f" ] || continue
  n=$(wc -l < "$f" 2>/dev/null || echo 0)
  if [ "$n" -ge "$HARD" ]; then
    printf '\033[31m❌\033[0m %s: %d lines (≥ %d, must split)\n' "$f" "$n" "$HARD"
    fail=1
  elif [ "$n" -ge "$SOFT" ]; then
    printf '\033[33m⚠️\033[0m  %s: %d lines (≥ %d, consider split)\n' "$f" "$n" "$SOFT"
    warn=$((warn+1))
  fi
done

# Note: the while-loop runs in a subshell so `fail` doesn't propagate.
# We need a separate exit pass:
maxhard=$(git ls-files '*.py' '*.ts' '*.tsx' '*.js' '*.jsx' '*.go' '*.rs' '*.java' '*.kt' '*.cpp' '*.c' 2>/dev/null | \
  xargs -I{} wc -l {} 2>/dev/null | awk -v h=$HARD '$1>=h {f=1} END {print f+0}')
exit "$maxhard"
