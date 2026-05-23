#!/bin/bash
# tools/status.sh — multi-host status probe (per /status skill Phase 1).
# Pure bash + ssh. No external deps.

set -u
HOSTS_DEFAULT="hpcc bcc tasl-7 tasl-labserver"
HOSTS="${HOSTS:-$HOSTS_DEFAULT}"
TIMEOUT="${TIMEOUT_PER_HOST:-8}"

probe_one() {
  local host=$1
  if [ "$host" = "local" ]; then
    bash -lc '
      echo "==HOST=="; hostname
      echo "==NVIDIA=="; nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null
      echo "==TMUX=="; tmux ls 2>/dev/null
      echo "==SLURM=="; squeue -u $USER -o "%.10i %.20j %.8T %.10M %.6D %R" 2>/dev/null
      echo "==WANDB=="; cat ~/.auto-production/active_runs.json 2>/dev/null
    '
  else
    ssh -o ConnectTimeout=$TIMEOUT -o StrictHostKeyChecking=accept-new "$host" bash -lc '
      echo "==HOST=="; hostname
      echo "==NVIDIA=="; nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null
      echo "==TMUX=="; tmux ls 2>/dev/null
      echo "==SLURM=="; squeue -u $USER -o "%.10i %.20j %.8T %.10M %.6D %R" 2>/dev/null
      echo "==WANDB=="; cat ~/.auto-production/active_runs.json 2>/dev/null
    ' 2>&1 || echo "==UNREACHABLE=="
  fi
}

for h in $HOSTS; do
  echo "===== $h ====="
  probe_one "$h" &
done
wait
