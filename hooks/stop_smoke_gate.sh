#!/bin/bash
# hooks/stop_smoke_gate.sh — Stop hook: refuse stop until smoke gate passes.
# Skipped if not in a git repo (e.g., transient demos).
set -u
REPO="${AUTO_PRODUCTION_REPO:-}"
[ -z "$REPO" ] && exit 0

# skip if not in a git repo (gate is project-scoped)
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# skip if no sprint_contract.yaml (project hasn't started research)
[ -f sprint_contract.yaml ] || exit 0

bash "$REPO/tools/smoke_gate.sh"
