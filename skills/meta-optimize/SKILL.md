---
name: meta-optimize
description: "周复盘所有 failure log (agent 被 kill、user 打回、重做的步骤)，另一个 agent 分析 root cause → 生成新 skill 或 patch 现有 prompt。长期复利最大项。用户说 'meta optimize' / '复盘' / '学习一下错误' / '总结失败' 时调用。也可设 cron 周末自动跑。"
argument-hint: "[--since 7d] [--projects all|<name>] [--auto-patch|--proposal-only]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent
---

# /meta-optimize — Failure-driven Self-Evolution ⭐

来源 = G1 [ARIS `/meta-optimize` 自演化]。

## What "failure" means

| 类型 | 来源 | 示例 |
|---|---|---|
| sub-agent killed | `~/.claude/projects/*/sessions/*.jsonl` 找 `task_killed` | spawn 后超时被砍 |
| user pushback | 提取 user 消息含「no」「不对」「stop」「revert」「为什么」等 | 「你又自己引入了一个 bug」 |
| re-do | git history 看是否同一文件短期内多次反复 patch | v3 → v4 → v5 → v6 |
| stop hook fired | `promise.json` 里 unfulfilled count > 0 | agent 答应没做 |
| audit blocked | `paper_audit_report.md` / `vla-audit-*.json` 里 FAIL | normalization mismatch |

## Workflow

### Phase 1: Collect window

`--since 7d` 默认。glob 所有 source：

- `~/.claude/projects/**/*.jsonl`
- `.auto-production/cache/*.json`
- `**/sprint_contract.yaml`
- `git log --since="$SINCE"` 跨 project

### Phase 2: Cluster failures

spawn sub-agent 读全部 failure events，按 root-cause 聚类：

- "我 5 次都因为 normalization mismatch BLOCK 训练" → cluster A
- "我 3 次 spawn sub-agent 超时" → cluster B
- ...

输出 `meta_opt_clusters.md`。

### Phase 3: Root cause + remedy

对每 cluster spawn 第二个 sub-agent 写 root-cause 分析 + 提议：

| Cluster | Root cause | Remedy |
|---|---|---|
| A (normalization) | `/vla-audit` 没在 Stage 2 → 4 gate 强制 | patch `docs/GATES.md` METHOD gate 标 MANDATORY |
| B (spawn timeout) | sub-agent prompt 不够窄 | patch `templates/spawn_task.md` 加 scope guard |
| ... | ... | ... |

### Phase 4: Auto-patch vs proposal

- `--auto-patch`: 直接 Edit 改 skill SKILL.md / template / hook，git commit `meta(auto): <cluster>`
- `--proposal-only`（默认）: 写 `meta_opt_proposals.md`，让 user 审完再 commit

### Phase 5: Add to MEMORY.md

每个 remedy 加一条 user-memory tier 的 lesson：

```markdown
## [LEARN:method] VLA normalization audit must run at METHOD gate

发现日期: 2026-05-22
样本: hf-jax v3/v4/v5/v6, OFT, GR00T, MemoryVLA
Remedy: docs/GATES.md METHOD gate 改为 MANDATORY
```

## Output

`.auto-production/meta-opt/<date>/`:

```
clusters.md
proposals.md  (or applied patches)
MEMORY_diff.md
```

+ 总结邮件 / Notion comment / Slack DM (if MCP available)。

## When to run

- 周末 cron (`crontab` 0 6 * * 0 触发)
- `/sleep-research` 结束后自动跑
- 手动 `/meta-optimize --since 30d` 月度复盘

## Failure modes

- 没 failure → 输出 "no failures, you must be doing something right or not enough projects"
- failure 太多 (>500) → 强制 top-20 cluster only
- sub-agent 分析超时 → 部分聚类完成也写

## See also

- [`templates/MEMORY.md`](../../templates/CLAUDE.md) — MEMORY 入口
- ARIS reference: `references/claude-code-skills/Auto-claude-code-research-in-sleep/tools/meta_opt`
