---
name: sleep-research
description: "夜间 autonomous 模式入口。把 stop-hook + heartbeat + 完成报告格式 + cost cap 打包成一行。已 ad-hoc 用了 200+ 次，固化为命名 skill。Use when user says \"sleep research\", \"夜间\", \"睡觉了你干\", \"通宵跑\", \"autonomous overnight\", \"我去睡觉\", \"overnight\", \"明早\". The user wants to walk away and have the agent push forward until a named goal."
argument-hint: "[goal-description] [— budget: 8h] [— wake-on: pivot|guard-fail|done] [— max-cost-usd: 50]"
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent, Skill
---

# /sleep-research — 夜间自主推进

> 你 200+ 次手写 stop-hook + heartbeat 的固化版。`/research-pipeline` 的夜间 wrapper。

## Overview

把 `/research-pipeline` 包一层：

- stop-hook 条件：`wake-on`（默认 `pivot|guard-fail|done`）
- heartbeat 间隔：5 min（写 `.auto-production/heartbeat`）
- `/stall-detect` 自动起后台 watcher
- 完成报告统一 `/conclusion-first` 5-段
- cost cap：到 100% wall-clock budget 或 max-cost-usd 强制 stop
- 醒来一封报告（写到 `wakeup_report.md`，可选 push 通知）

## When to Use

- 准备睡觉 / 出门 / 长时间 AFK
- 已经 `/sprint-contract` + `/smoke-test` 都过了，只剩 grinding
- 想让 `/research-pipeline` 跑 N 个 sprint 不停下来问

## Constants

- **BUDGET** = `8h`（默认）
- **HEARTBEAT_INTERVAL** = `300s`
- **STALL_TIMEOUT** = `900s`（15 min）—— 比常规严格，夜里没人看
- **WAKE_ON** = `pivot,guard-fail,done`（任一条件触发 stop + 报告 user）
- **MAX_COST_USD** = `50`（如有 cost meter；否则 ignore）
- **CHECKIN_NOTION** = `true`（如 `NOTION_TOKEN` 在）

## Workflow

### Phase 0 — pre-flight checks

```bash
# 必须满足
[ -f sprint_contract.yaml ] || { echo "❌ /sprint-contract --sign first"; exit 1; }
[ -f .auto-production/audit/smoke_passed.json ] || { echo "❌ /smoke-test first"; exit 1; }
[ -f .auto-production/audit/contract_signed.json ] || { echo "❌ contract not signed"; exit 1; }
```

`co-pilot` 模式下任何 missing → AskUserQuestion 是否 init；`full-auto` 直接 init。

### Phase 1 — 起 watchers

```bash
# /stall-detect 后台
Skill(/stall-detect --timeout $STALL_TIMEOUT --action ping)

# heartbeat loop
(while true; do
  echo "$(date -Iseconds) heartbeat $(git rev-parse --short HEAD)" > .auto-production/heartbeat
  sleep $HEARTBEAT_INTERVAL
done) &
echo $! > .auto-production/sleep_heartbeat.pid

# notion check-in
[ -n "$NOTION_TOKEN" ] && Skill(/cross-host-sync --direction push)
```

### Phase 2 — main loop

```
loop:
  Skill(/research-pipeline ${goal} — mode: full-auto — budget: ${remaining})
  if stop condition met → break
  else → continue
```

stop 条件 check（每 Skill 调用之后）：

```python
if last_decision in {"PIVOT"} and "pivot" in WAKE_ON: break
if guard_triggered and "guard-fail" in WAKE_ON: break
if pipeline_done and "done" in WAKE_ON: break
if wall_clock >= BUDGET: break
if cost_so_far >= MAX_COST_USD: break
```

### Phase 3 — wake-up report

```python
# write wakeup_report.md (5-段 /conclusion-first)
write_file("wakeup_report.md", f"""
# Wake-up report — {now}

**Conclusion**: {summary_line}

**What I changed**: {diff_stats}

**What I checked**: {gates_passed_list}

**Risks**: {open_issues}

**Next step**: {what_user_should_decide}

## Decisions log
{tail decisions.jsonl}

## Cost
- Wall-clock: {used}/{BUDGET}
- API cost: ${cost} / ${MAX_COST_USD}
""")
```

可选推送：

```bash
[ -n "$AUTO_PRODUCTION_NOTIFY_URL" ] && curl -X POST "$AUTO_PRODUCTION_NOTIFY_URL" \
  -d "$(cat wakeup_report.md | head -50)"
```

### Phase 4 — cleanup

```bash
kill $(cat .auto-production/sleep_heartbeat.pid) 2>/dev/null
Skill(/stall-detect --stop)
Skill(/cross-host-sync --direction push)  # final state
```

## Output

- `wakeup_report.md`（user 起床第一眼）
- 该期间所有 `findings.md` 新增段
- `decisions.jsonl` 新增 entry
- 视成败：新 ckpt / 新 paper draft / 新 PIVOT

## Failure modes

| 现象 | 处理 |
|---|---|
| budget 用完 pipeline 在 stage N | emit partial report，标 `incomplete: true`，列下次启动建议 |
| Stall watcher 都没救住 → 真卡死 | wakeup_report 写「⚠️ STALL 1h 未恢复」+ kill 主 process |
| API quota 用光 | 切 fallback provider（K2 → cross-provider matrix） |
| disk 满 | emergency 删 `runs/run_zero_*/checkpoint_step_*.pt` 老 ckpt |

## Composition

- 内层调 `/research-pipeline`
- 外层 wrap `/stall-detect` + `/promise-check` + `/cross-host-sync`
- 早上起床 `/status` 看 + 读 `wakeup_report.md`
