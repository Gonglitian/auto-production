#!/bin/bash
# tools/_resolver.sh — 3-layer helper resolver. See docs/RESOLVER.md.
# Usage:
#   helper=$(bash $AUTO_PRODUCTION_REPO/tools/_resolver.sh promise_check.py) || exit 2
#   python3 "$helper" ...
set -u
NAME=${1:?need helper name}

for p in \
  ".auto-production/tools/$NAME" \
  "tools/$NAME" \
  "${AUTO_PRODUCTION_REPO:-}/tools/$NAME"
do
  [ -n "$p" ] && [ -f "$p" ] && { echo "$p"; exit 0; }
done

echo "❌ helper '$NAME' not found in resolver chain (.auto-production/tools, ./tools, \$AUTO_PRODUCTION_REPO/tools)" >&2
exit 2
