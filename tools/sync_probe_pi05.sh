#!/bin/bash
# tools/sync_probe_pi05.sh — verify remote env is ready for lerobot pi05 stack.
# Copy + edit per-project before /sync-to-remote → ssh hpcc bash -l /tmp/foo.sh.
#
# Generalized from vla3d hpcc round 3 probe (see /sync-to-remote skill).
set -u
PROJECT_DIR=${PROJECT_DIR:-/bigdata/jlilab/lgong024/proj/vla3d}
CONDA_ENV=${CONDA_ENV:-/bigdata/jlilab/lgong024/.conda/envs/dynamem_pi05}
PROJECT_STUBS=${PROJECT_STUBS:-gaussian_tokenizer decoder_xattn pi05_wrapper}
LEROBOT_FILE=${LEROBOT_FILE:-/bigdata/jlilab/lgong024/proj/dynamem/refs/lerobot/src/lerobot/policies/pi05/modeling_pi05.py}

cd "$PROJECT_DIR" || { echo "❌ cannot cd $PROJECT_DIR"; exit 2; }
source "$(conda info --base 2>/dev/null)/etc/profile.d/conda.sh" 2>/dev/null \
  || { echo "❌ conda not on PATH (use bash -l)"; exit 2; }
conda activate "$CONDA_ENV" || { echo "❌ conda activate $CONDA_ENV failed"; exit 2; }

echo "===== 1. env sanity ====="
python -c "import sys; print('python', sys.version.split()[0])"
python -c "import torch; print('torch', torch.__version__, 'cuda_compiled:', torch.version.cuda)"
python -c "import lerobot; print('lerobot', getattr(lerobot, '__version__', 'unknown'))" 2>&1 | head -1
echo

echo "===== 2. auto-production skill links ====="
echo "  skills: $(ls .claude/skills 2>/dev/null | wc -l)"
echo "  AUTO_PRODUCTION_REPO: ${AUTO_PRODUCTION_REPO:-(not set; check .auto-production/.env)}"
echo

echo "===== 3. vla_audit_loader self_check ====="
if [ -f .auto-production/tools/vla_audit_loader.py ]; then
  python -c '
import sys; sys.path.insert(0, ".auto-production/tools")
import vla_audit_loader as v
ok, issues = v.self_check()
print("  ok:", ok)
[print("    -", i) for i in issues]
'
else
  echo "  (no .auto-production/tools/vla_audit_loader.py — copy from templates/)"
fi
echo

echo "===== 4. project stub imports ====="
python -c "
import sys; sys.path.insert(0, 'src')
for mod in '$PROJECT_STUBS'.split():
    try: __import__(mod); print(' ', mod, ': OK')
    except Exception as e: print(' ', mod, ': FAIL', type(e).__name__, str(e)[:120])
"
echo

echo "===== 5. lerobot pi05 monkey-patch site ====="
if [ -f "$LEROBOT_FILE" ]; then
  LINE=$(grep -n '^    def denoise_step(' "$LEROBOT_FILE" | head -1 | cut -d: -f1)
  echo "  def denoise_step @ line: ${LINE:-NOT-FOUND}"
  echo "  body sentinels found:"
  sed -n "${LINE},$((LINE+45))p" "$LEROBOT_FILE" 2>/dev/null | \
    grep -nE "embed_suffix|paligemma_with_expert.forward|outputs_embeds\[1\]|action_out_proj" | head -10
else
  echo "  ❌ lerobot file not found at $LEROBOT_FILE"
fi
echo

echo "===== 6. hardcoded line# audit (vs current real) ====="
REAL_LINE=$(grep -n '^    def denoise_step(' "$LEROBOT_FILE" 2>/dev/null | head -1 | cut -d: -f1)
if [ -n "$REAL_LINE" ]; then
  STALE=$(grep -rEI \
    --include='*.py' --include='*.md' --include='*.yaml' --include='*.yml' --include='*.txt' \
    --exclude-dir='__pycache__' --exclude-dir='.git' --exclude-dir='runs' \
    "denoise_step.*~?L?[0-9]{3,}|line ~[0-9]{3,}" \
    src/ tests/ docs/ MEMORY.md sprint_contract.yaml task_notes.yaml 2>/dev/null | \
    grep -vE "(~|L|line )$REAL_LINE\b|$REAL_LINE-[0-9]+\b" | head -10)
  if [ -n "$STALE" ]; then
    echo "  ⚠️  possible stale line# refs (real denoise_step is at $REAL_LINE):"
    echo "$STALE"
  else
    echo "  ✓ no stale denoise_step line# refs detected (real=$REAL_LINE)"
  fi
fi
echo

echo "===== 7. disk + slurm summary ====="
df -h "$PROJECT_DIR" | tail -1
echo "  partitions:"
sinfo -o '%P %T %D' 2>/dev/null | sort -u | head -8
echo "  squeue (me):"
squeue -u "$USER" 2>/dev/null | head -5
