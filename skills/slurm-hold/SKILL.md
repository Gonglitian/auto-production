---
name: slurm-hold
description: "在 slurm 集群上拉一个长占用 placeholder job + tmux session + SSH alias，之后用 srun --overlap 复用节点跑实际训练。模板自 hpcc raise 7-day hold 实战。用户说 'hold 节点' / 'slurm 占位' / '长占用' / '抢节点' 时调用。"
argument-hint: "[--partition raise|gpu] [--gpu 4] [--days 7] [--account <name>] [--qos <qos>]"
allowed-tools: Bash(*), Read, Write
---

# /slurm-hold — Slurm 长占用 + srun overlap

来源 = D4 [hpcc raise 实战]。

## Why

- HPCC 节点抢手，先占住、慢慢用
- 不想每次 sbatch 排队
- 多个实验复用同一个节点（srun --overlap）

## Workflow

### Phase 0: Validate

检查 `sinfo`、partition / account / qos 都存在。

### Phase 1: 生成 hold sbatch script

```bash
#!/bin/bash -l
#SBATCH --job-name=hold-<PROJ>
#SBATCH --partition=$PARTITION
#SBATCH --account=$ACCOUNT
#SBATCH --qos=$QOS
#SBATCH --gres=gpu:$GPU
#SBATCH --time=$DAYS-00:00:00
#SBATCH --output=/dev/null

# Long-sleep placeholder so node is held but does nothing
sleep ${DAYS}d
```

写到 `slurm/hold_<PROJ>.sh`。

### Phase 2: Sbatch + capture jobid

```bash
JID=$(sbatch --parsable slurm/hold_<PROJ>.sh)
echo "$JID" > slurm.jobid
```

### Phase 3: Watch until allocated

```bash
until [ "$(squeue -j $JID -h -o %T)" = "RUNNING" ]; do
  sleep 30
done
NODE=$(squeue -j $JID -h -o %N)
echo "Node allocated: $NODE"
```

### Phase 4: 起 tmux session + SSH config alias

```bash
ssh $HEAD "tmux new-session -d -s hold-<PROJ>-overlap"
echo "
Host slurm-<PROJ>
  HostName $NODE
  ProxyJump $HEAD
" >> ~/.ssh/config
```

### Phase 5: 写使用提示

```markdown
✅ Hold job $JID allocated on $NODE for $DAYS days.

跑训练：
  ssh $HEAD
  tmux a -t hold-<PROJ>-overlap
  srun --jobid=$JID --overlap --gres=gpu:1 --pty bash
  # 然后正常跑 python train.py ...

释放：
  scancel $JID
```

### Phase 6: 调 `/cross-host-sync --push` 把 hold 登记到 Notion

## Output

文字提示 + `slurm/hold_<PROJ>.sh` + `slurm.jobid` 文件。

## Failure modes

- Partition 不存在 → 报错让 user 改
- QOS 不允许 7 天 → 自动降级到 max 允许时长 + 提示
- 一直 PENDING > 1h → 告警让 user 决定 (调小 GPU? 换 partition?)

## See also

- [`/cross-host-sync`](../cross-host-sync/SKILL.md) — hold 起好后自动登记
