#!/bin/bash
# tools/audit_driven_retrain.sh — scancel → audit → patch → retry pipeline.
# Each round saves an audit + patch under .auto-production/retrain/<round>/.
set -u
HYP=${HYP:-"(no hypothesis given)"}
RUN=${RUN:-}
HOST=${HOST:-$(hostname)}

mkdir -p .auto-production/retrain
ROUND=$(($(ls .auto-production/retrain 2>/dev/null | wc -l) + 1))
DIR=.auto-production/retrain/round_${ROUND}
mkdir -p "$DIR"

echo "== /audit-driven-retrain round $ROUND =="
echo "  run: ${RUN:-<auto>}  host: $HOST"
echo "  hypothesis: $HYP"

# Phase 1: scancel (best-effort; needs jobid)
if [ -n "${JOBID:-}" ]; then
  ssh "$HOST" "scancel $JOBID" 2>/dev/null && echo "  ✓ scancel $JOBID"
fi

# Phase 2: emit audit prompt for sub-agent
cat > "$DIR/audit_prompt.md" <<EOF
# Diagnose run ${RUN:-<latest>} on $HOST
Hypothesis from user: $HYP

## Required outputs (write to $DIR/audit.md)
- 5-segment /conclusion-first report
- Root cause hypothesis (confirmed / refuted by what evidence)
- Suggested patches as file:line diff stubs
EOF
echo "  ✓ audit prompt → $DIR/audit_prompt.md"

# Phase 3: prompt user to apply patch
echo
echo "Next: forward $DIR/audit_prompt.md to Claude Agent (general-purpose) →"
echo "      review $DIR/audit.md → apply patch → /smoke-test → /auto-version →"
echo "      sbatch retry on $HOST"
