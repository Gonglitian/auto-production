---
name: status
description: "现在怎么样？/ what's running where / 当前状态 / 看看 GPU — 跨所有已配置机器汇总 background task / GPU 占用 / tmux session / slurm queue / 最近 wandb run + chunk metric。用户问'现在怎么样'/'当前状态'/'看看 GPU'/'哪台机器跑啥'时调用。"
argument-hint: "[--host hpcc|bcc|tasl-7|tasl-labserver|all] [--include-metrics]"
allowed-tools: Bash(*), Read
---

# /status — 跨机器实时状态汇总

替代「ssh 进每台机器 nvidia-smi 一遍」的痛苦工作流。来源 = M1 [user 11K 消息中出现 118+ 次]。

## When to Use

- 用户问「现在怎么样」/「what's running」/「当前状态」/「看看 GPU」
- 任何 session 开始前的 sanity check
- `/sleep-research` 周期 heartbeat 报告内嵌

## Workflow

### Phase 0: Resolve hosts

从环境变量 `AUTO_PRODUCTION_HOSTS`（逗号分隔）或 `~/.ssh/config` 读已配置的 host。默认 `hpcc,bcc,tasl-7,tasl-labserver`。

### Phase 1: Per-host probe (parallel ssh)

对每台 host **并行** 执行：

```bash
ssh -o ConnectTimeout=5 $HOST "$(cat <<'EOF'
echo "=== $(hostname) ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null | head
echo "--- tmux ---"
tmux ls 2>/dev/null
echo "--- slurm ---"
squeue -u $USER 2>/dev/null | head
echo "--- recent ---"
ls -t ~/proj/*/runs/*/wandb-summary.json 2>/dev/null | head -3
EOF
)"
```

实现：调 `tools/status.sh` 或直接 inline。失败 host 不阻塞，标 `[unreachable]`。

### Phase 2: Aggregate

输出为 1 张 markdown 表 + 5 段摘要（每 host 一段）。

### Phase 3 (optional, `--include-metrics`)

如果当前目录有 wandb run，调 `tools/auto_viz.py --last-metric-only` 拉最近 chunk 的 4 个核心 metric。

## Output

```markdown
## 跨机状态 @ 2026-05-22 23:14 PDT

| Host | GPUs busy | tmux | slurm pending | Last run |
|---|---|---|---|---|
| hpcc | 4/9 (gpu13) | 2 | 1 | v6-meta-distill |
| bcc | 0/2 | 0 | 0 | — |
| tasl-7 | 1/1 | 1 | — | dynamem precompute |
| tasl-labserver | 3/8 | 4 | — | evomoe stage 2 |

### hpcc
- gpu13: utilisation 87% / 92% / 0% / 12% ...
- tmux: `hf-jax-watch`, `pi05`
- slurm: 1 pending in `raise` partition

...
```

## Failure modes

- ssh 超时 → 该 host 标 `[unreachable]`，继续。
- nvidia-smi 不存在 → 该 host 跳过 GPU 段。
- 无 wandb summary → Phase 3 跳过。

## See also

- [`/cross-host-sync`](../cross-host-sync/SKILL.md) — 把这些状态持久化到 Notion DB
- [`tools/status.sh`](../../tools/status.sh)
