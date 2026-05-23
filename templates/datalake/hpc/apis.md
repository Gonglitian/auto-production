# HPC datalake — common commands

Quick reference. Adapt per your cluster's specifics. Seeded from UCR HPCC; the
patterns generalize to most slurm-based clusters.

---

## SSH connection (login node)

```bash
ssh hpcc                          # uses ~/.ssh/config alias
ssh hpcc bash -l                  # interactive login shell (sources .bashrc)
ssh hpcc bash -l /tmp/script.sh   # run script with login shell env (conda etc.)
scp local_file hpcc:/path/        # copy file
rsync -avzP local/ hpcc:/path/    # copy dir, no --delete on incremental
```

## Partitions

```bash
sinfo                             # all partitions + state
sinfo -p gpu -o '%n %G %T'        # gpu partition: nodes + gres + state
sinfo -o '%P %T %D' | sort -u     # partition / state / node-count
```

UCR HPCC partitions as of 2026-05: `batch / epyc / gpu / highclock / highmem`.

## Job submission

```bash
sbatch script.sbatch              # submit a script
sbatch --gres=gpu:1 ...           # request 1 GPU
sbatch -p gpu -t 4:00:00 ...      # partition + walltime
squeue -u $USER                   # my queue
scancel JOBID                     # cancel
scontrol show job JOBID           # detail
```

## Interactive GPU session

```bash
srun -p gpu --gres=gpu:1 -t 1:00:00 --pty bash -l   # 1-hour interactive
srun --jobid=$HOLDJID --overlap --pty bash -l       # attach to a hold-job
```

## Resource holds (long-occupied node)

```bash
# Use /slurm-hold skill, or manually:
sbatch --gres=gpu:4 -t 7-00:00:00 -p gpu hold.sbatch
# hold.sbatch just sleeps + writes heartbeat; then srun --overlap reuses.
```

## Conda

```bash
conda info --envs                                       # list all known envs
conda activate /full/path/to/env                        # safer than by name
source $(conda info --base)/etc/profile.d/conda.sh      # init in non-login shell
```

## Disk / quota

```bash
df -h /bigdata                       # see free
du -sh /bigdata/.../myproj           # see my usage
quota -s                             # if cluster enforces quota
```

## Common env vars to set

```bash
export HF_HOME=/data4/hf_cache       # avoid root/snapshot pollution
export WANDB_DIR=/data4/wandb
export TORCH_HOME=/data4/torch
export CUDA_VISIBLE_DEVICES=0        # honor srun allocation, not nvidia-smi order
export OMP_NUM_THREADS=8             # avoid CPU thrash on multi-job nodes
```

## Common files

| Path | Purpose |
|---|---|
| `~/.bashrc` | login shell init (sourced by `bash -l`) |
| `~/.ssh/config` | host aliases |
| `~/.slurm/` | slurm cache |
| `/bigdata/<lab>/<user>/.conda/envs/` | per-user conda envs (often outside default conda registry) |
| `/data4/` (varies) | high-capacity scratch on tasl-labserver |

## Diagnostics one-liner

```bash
# Run as the first thing in any /sync-to-remote probe script.
ssh $HOST bash -l <<'EOF'
echo === host ===; hostname
echo === conda ===; which conda; conda info --envs | head -10
echo === slurm ===; sinfo -o '%P %T' | sort -u
echo === disk ===; df -h /bigdata | tail -1
echo === gpus on this node ===; nvidia-smi 2>/dev/null || echo no gpu on $(hostname)
EOF
```
