#!/bin/bash
# tools/sync_probe_generic.sh — minimal env probe (no project-specific assertions).
# Use when no /sync-to-remote stack template fits, or as fallback.
set -u
PROJECT_DIR=${PROJECT_DIR:-$(pwd)}
CONDA_ENV=${CONDA_ENV:-}     # full path; empty = use whatever ssh login activated

cd "$PROJECT_DIR" || { echo "❌ cannot cd $PROJECT_DIR"; exit 2; }
if [ -n "$CONDA_ENV" ]; then
  source "$(conda info --base 2>/dev/null)/etc/profile.d/conda.sh" 2>/dev/null
  conda activate "$CONDA_ENV" 2>/dev/null
fi

echo "===== 1. host info ====="
hostname
uname -a | head -1
echo

echo "===== 2. python + key libs ====="
python3 -c "import sys; print('python', sys.version.split()[0])" 2>/dev/null \
  || { echo "❌ no python3"; exit 1; }
python3 -c "import torch; print('torch', torch.__version__, 'cuda_compiled:', torch.version.cuda)" 2>&1 | head -1
python3 -c "import numpy; print('numpy', numpy.__version__)" 2>&1 | head -1
echo

echo "===== 3. auto-production wired ====="
echo "  skills: $(ls .claude/skills 2>/dev/null | wc -l) (expected 50+)"
[ -f .auto-production/.env ] && source .auto-production/.env
echo "  AUTO_PRODUCTION_REPO: ${AUTO_PRODUCTION_REPO:-(unset)}"
echo

echo "===== 4. project python sources py_compile ====="
python3 -c '
import compileall, pathlib, sys
n_ok = n_fail = 0
for p in pathlib.Path("src").rglob("*.py"):
    ok = compileall.compile_file(str(p), quiet=2)
    n_ok += int(bool(ok)); n_fail += int(not bool(ok))
for p in pathlib.Path("tests").rglob("*.py"):
    ok = compileall.compile_file(str(p), quiet=2)
    n_ok += int(bool(ok)); n_fail += int(not bool(ok))
print(f"  py_compile: {n_ok} ok / {n_fail} fail")
sys.exit(0)
' 2>&1 | tail -3
echo

echo "===== 5. ast_walker ====="
if [ -n "${AUTO_PRODUCTION_REPO:-}" ] && [ -f "$AUTO_PRODUCTION_REPO/tools/ast_walker.py" ]; then
  python3 "$AUTO_PRODUCTION_REPO/tools/ast_walker.py" src/*.py tests/*.py 2>&1 | head -10
  echo "  ast_walker exit=$?"
else
  echo "  (skipped: ast_walker.py not resolvable)"
fi
echo

echo "===== 6. disk ====="
df -h "$PROJECT_DIR" | tail -1
