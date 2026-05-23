#!/bin/bash
# tools/sync_probe_isaaclab.sh — verify remote env is ready for Isaac Lab stack.
# Adapt PROJECT_DIR + CONDA_ENV + ISAACLAB_PATH per your project.
set -u
PROJECT_DIR=${PROJECT_DIR:-$(pwd)}
CONDA_ENV=${CONDA_ENV:-}
ISAACLAB_PATH=${ISAACLAB_PATH:-/bigdata/jlilab/lgong024/proj/IsaacLab}

cd "$PROJECT_DIR" || { echo "❌ cannot cd $PROJECT_DIR"; exit 2; }
if [ -n "$CONDA_ENV" ]; then
  source "$(conda info --base 2>/dev/null)/etc/profile.d/conda.sh" 2>/dev/null
  conda activate "$CONDA_ENV" 2>/dev/null
fi

echo "===== 1. host + driver ====="
hostname
nvidia-smi --query-gpu=index,name,driver_version --format=csv,noheader 2>/dev/null | head -8 \
  || echo "  (no GPU on this node — login node?)"
echo

echo "===== 2. python + isaac stack ====="
python -c "import sys; print('python', sys.version.split()[0])"
python -c "import torch; print('torch', torch.__version__, 'cuda_compiled:', torch.version.cuda)" 2>&1 | head -1
python -c "import isaacsim; print('isaacsim', getattr(isaacsim, '__version__', 'unknown'))" 2>&1 | head -1
python -c "import omni.isaac.core; print('omni.isaac.core: OK')" 2>&1 | head -1
python -c "import isaaclab; print('isaaclab', getattr(isaaclab, '__version__', 'unknown'))" 2>&1 | head -1
echo

echo "===== 3. IsaacLab repo state ====="
if [ -d "$ISAACLAB_PATH" ]; then
  echo "  IsaacLab @ $ISAACLAB_PATH"
  (cd "$ISAACLAB_PATH" && git log --oneline -1 2>/dev/null)
else
  echo "  ❌ $ISAACLAB_PATH not present"
fi
echo

echo "===== 4. apptainer / container status ====="
which apptainer || which singularity 2>&1 | head -1
ls /bigdata/jlilab/lgong024/containers/ 2>/dev/null | head -5
echo

echo "===== 5. headless GL libs ====="
ldconfig -p | grep -E "libGL|libEGL|libglfw" | head -5
echo

echo "===== 6. project stub imports ====="
python -c "
import sys; sys.path.insert(0, 'src')
for mod in '${PROJECT_STUBS:-}'.split():
    try: __import__(mod); print(' ', mod, ': OK')
    except Exception as e: print(' ', mod, ': FAIL', type(e).__name__, str(e)[:120])
"
echo

echo "===== 7. disk + slurm ====="
df -h "$PROJECT_DIR" | tail -1
sinfo -o '%P %T %D' 2>/dev/null | sort -u | head -5
