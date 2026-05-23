---
name: hitl-mode
description: "启动 project 时选 1 个 HITL 模式全程跑：full-auto / gate-only / checkpoint / co-pilot / step-by-step / custom。整个 project 按这个 mode 跑，不混乱。Use when user says \"hitl mode\", \"co-pilot mode\", \"full auto\", \"checkpoint mode\", \"切模式\", \"interactivity\"."
argument-hint: "[--set full-auto|gate-only|checkpoint|co-pilot|step-by-step|custom]"
allowed-tools: Read, Write
---

# /hitl-mode — Human-in-the-Loop Mode Selector

> 借鉴 AutoResearchClaw HITL。

## Overview

6 模式对照：

| Mode | 何时打断 user |
|---|---|
| **full-auto** | 永不打断（除 stop-hook 条件 / cost cap） |
| **gate-only** | 只在 5 个 named gate 停 |
| **checkpoint** | 每 stage 末停 |
| **co-pilot** | 每个大决策 stop（默认） |
| **step-by-step** | 每个 tool call 前问（debug 用） |
| **custom** | user 自定 trigger 列表 |

写入 `.auto-production/hitl_mode`，所有 skill 读这个文件决定何时 AskUserQuestion。

## Workflow

```bash
MODE=${1:?need --set}
echo "$MODE" > .auto-production/hitl_mode
echo "✅ HITL mode → $MODE"
```

## Output

- `.auto-production/hitl_mode` (单行文件)

## Composition

- `/research-pipeline` 启动时读
- `/pivot` 决策 emit 时按 mode 决定 auto-recommend or AskUserQuestion
- `/sleep-research` 强制 full-auto（睡前临时切换）
