---
name: cross-host-sync
description: "把 4 台机器（hpcc / bcc / tasl-7 / tasl-labserver）上正在跑的 run + ckpt 路径 + conda env + dataset 路径同步到 Notion 数据库。一行命令双向同步。用户说 'sync 状态' / '同步到 notion' / 'cross host' / '哪台机器跑啥' 时调用。"
argument-hint: "[--push|--pull|--diff] [--db <notion-db-id>] [--host <name>]"
allowed-tools: Bash(*), Read, Write, Agent
---

# /cross-host-sync — 4 机器 ↔ Notion 数据库双向同步 ⭐

来源 = D1。解决「哪台机器跑了哪个 run / ckpt 在哪 / 找半天」痛点。

## Notion Schema

数据库每行 = 一个**正在跑或最近跑过的 run**。字段：

| Field | Type | 来源 |
|---|---|---|
| Run name | Title | wandb run name |
| Host | Select | 机器名 |
| Partition | Select | slurm partition (raise / gpu / cpu / —) |
| Job ID | Number | slurm jobid |
| Branch | Text | git branch |
| Commit | Text | git short sha |
| Start time | Date | sbatch start |
| Status | Select | running / done / killed / failed |
| WandB URL | URL | wandb run link |
| Ckpt path | Text | abs path to latest ckpt |
| Conda env | Text | env path |
| Dataset path | Text | abs path to dataset |
| Notes | Text | 一句话目的 |

`NOTION_DB_ID` 环境变量或 `--db` 指定。

## Workflow

### Phase 0: Auth

`NOTION_TOKEN` 环境变量。校验 token + db 可达。

### Phase 1: Direction

- `--push`（默认）：local 状态 → Notion
- `--pull`：Notion → local `EXPERIMENT_STATUS.md`
- `--diff`：列出差异不写

### Phase 2 (push): Probe + upload

对每台 host 并行：

```bash
ssh $HOST 'cd ~/proj && for d in */; do
  cd "$d"
  if [ -d wandb/latest-run ]; then
    cat wandb/latest-run/files/wandb-metadata.json
    git rev-parse --short HEAD
    git branch --show-current
    squeue -j $(cat slurm.jobid 2>/dev/null) -h 2>/dev/null
  fi
  cd -
done'
```

聚合成 row dict，调 `tools/cross_host_sync.py --push`。

### Phase 3 (pull): Notion query + write `EXPERIMENT_STATUS.md`

```python
from tools.cross_host_sync import notion_query
rows = notion_query(db_id, filter={"Status": "running"})
write_markdown_table(rows, "EXPERIMENT_STATUS.md")
```

### Phase 4 (diff): 输出 markdown diff

哪些 row local 有 Notion 没（→ push 补）；哪些 Notion 有 local 没（→ 可能 run 死了忘标 killed）。

## Helper

`tools/cross_host_sync.py` —— 纯 Python stdlib + `urllib` 调 Notion REST API。零依赖。

## Output

```markdown
## Cross-host sync @ 2026-05-22 23:30

**Direction**: push (4 hosts → Notion)

| Host | Probed runs | New rows | Updated rows | Failed |
|---|---|---|---|---|
| hpcc | 3 | 1 | 2 | 0 |
| bcc | 0 | 0 | 0 | 0 |
| tasl-7 | 1 | 0 | 1 | 0 |
| tasl-labserver | 4 | 2 | 2 | 0 |

Notion DB → <url>
```

## Failure modes

- Notion 429 → exponential backoff
- ssh 超时 → 该 host 跳过，最后报告
- 同 jobid 在两台机器 → 报警（不可能但要 sanity）

## See also

- [`/status`](../status/SKILL.md) — 一次性 ephemeral 报告（不存 Notion）
- [`tools/cross_host_sync.py`](../../tools/cross_host_sync.py)
