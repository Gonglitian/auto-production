#!/bin/bash
# tools/paper_pipeline.sh — 6-stage paper pipeline driver.
# Calls /paper-mode + /cross-review + /citation-audit + /pubfig sequentially.
set -u
VENUE=${VENUE:-NeurIPS}
START=${START:-1}
EFFORT=${EFFORT:-polished}
REPO="${AUTO_PRODUCTION_REPO:?need AUTO_PRODUCTION_REPO}"

run_stage() {
  local n=$1 desc=$2
  [ $n -lt $START ] && { echo "↷ skip stage $n ($desc)"; return; }
  echo
  echo "==[ stage $n: $desc ]=="
  case $n in
    1) python3 "$REPO/tools/paper_mode.py" --mode outline --venue $VENUE ;;
    2) python3 "$REPO/tools/paper_mode.py" --mode draft --venue $VENUE ;;
    3) echo "→ run /cross-review --rounds 3 (manually or via Skill)" ;;
    4) python3 "$REPO/tools/paper_mode.py" --mode revise --venue $VENUE ;;
    5) python3 "$REPO/tools/pubfig.py" --venue $VENUE --batch ;;
    6) echo "→ run /citation-audit (manually or via Skill)" ;;
  esac
  git add paper/ 2>/dev/null && git commit -m "paper: stage $n ($desc)" --allow-empty 2>/dev/null
}

mkdir -p paper/{sections,figures,tables,reviews,rebuttal,defenses,talk,slides,poster}

run_stage 1 outline
run_stage 2 draft
run_stage 3 review
run_stage 4 revise
run_stage 5 format
run_stage 6 cite-verify

echo
echo "✅ paper pipeline scaffolded — see paper/ and .auto-production/paper_pipeline_log.json"
