---
name: promise-check
description: "agent 一旦说 \"I'll do X\" / \"稍后我会...\" / \"下一步...\"，自动 log 到 promise.json。N 步后没真做就提醒 user。机器化追究 = 减少 agent 拖延。Use when user says \"promise check\", \"agent 说过的话\", \"待办\", \"承诺\", or runs automatically as PostToolUse hook."
argument-hint: "[--list-open] [--close <id>] [--scan <jsonl-or-stdin>]"
allowed-tools: Bash(*), Read, Write, Grep
---

# /promise-check — Agent Promise Ledger

> 借鉴 claude-research 9-hook。横切机制 Part I §3 C1。

## Overview

扫 agent 的 user-facing 输出，正则匹配「承诺类」短语，登记到 `promise.json`。后续 N 步内 grep 是否兑现，否则 ping user。

### 触发短语（regex）

| 中文 | 英文 |
|---|---|
| `我会(在.+?)?(立即\|稍后\|接下来\|完成X后)?` | `I('ll\| will) (do\|run\|fix\|write\|check)` |
| `下一步.+(做\|跑\|改\|写\|加)` | `next step (is\|will be)` |
| `先X再Y` | `first.+then` |
| `等X完了我会Y` | `after.+I('ll\| will)` |

完整 regex pattern 在 `tools/promise_check.py`。

## When to Use

- **As PostToolUse hook** (default registration)
- user 手动 `/promise-check --list-open` 查待办
- agent 自己 `--close` 标兑现

## Constants

- **LEDGER_PATH** = `promise.json`（project root，committed 到 repo）
- **REMINDER_AFTER_TURNS** = `5`（5 turn 没兑现 → 提醒）
- **AUTO_CLOSE_GREP** = `["完成", "已搞定", "done", "fixed", "已修"]`（agent 说这些自动 close）

## Workflow

### `--scan <stdin>` （hook 模式）

```bash
# 从 PostToolUse hook 喂 agent 输出
echo "$AGENT_OUTPUT" | python3 tools/promise_check.py scan \
  --ledger promise.json \
  --turn $(cat .auto-production/turn_count)
```

scan 内部：

```python
for sent in split_sentences(agent_output):
    for pat in PROMISE_PATTERNS:
        if re.search(pat, sent):
            ledger['open'].append({
                'id': uuid4().hex[:8],
                'text': sent,
                'said_at': now_iso(),
                'turn': current_turn,
                'pattern_matched': pat
            })
            break
    for close_kw in AUTO_CLOSE_GREP:
        if close_kw in sent:
            close_matching_open(ledger, sent)
```

### `--list-open`

```bash
python3 tools/promise_check.py list-open
# 输出：
# ⏳ a3f291: "我会在 v6 训完后跑 eval"  (said 2 turns ago)
# ⏳ b7c084: "稍后补 ablation"  (said 7 turns ago, REMINDER overdue)
```

### `--close <id>` (agent 主动调)

```bash
python3 tools/promise_check.py close --id a3f291
```

### Reminder 机制

每 turn end 时 hook 跑：

```python
for p in ledger['open']:
    if current_turn - p['turn'] >= REMINDER_AFTER_TURNS:
        print(f"⚠️ REMINDER: '{p['text']}' said {current_turn - p['turn']} turns ago, still open")
```

## Output

- `promise.json` 结构：

```json
{
  "open": [
    {"id": "a3f291", "text": "...", "said_at": "...", "turn": 12, "pattern_matched": "我会"}
  ],
  "closed": [
    {"id": "9e2c10", "text": "...", "closed_at": "...", "fulfilled_by_turn": 15}
  ]
}
```

## Failure modes

| 现象 | 处理 |
|---|---|
| 误报（agent 在引用 user 的 "我会"）| 用 sentence speaker 启发式过滤；regex 加 `^(?!.*user said)` |
| 同一 promise 多次重复 | 按 hash(text) 去重 |
| ledger 太大（>10K entries）| auto-archive closed entries to `promise_archive.jsonl` |

## Composition

- **Hook**：`hooks/pre_promise_check.sh` 在 PostToolUse 调
- `/status` 自动读 `promise.json` 显 pending
- `/meta-optimize` 收 `closed_unfulfilled`（reminder 后仍没做）做 root cause
