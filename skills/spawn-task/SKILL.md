---
name: spawn-task
description: "sub-agent fork 模板：给 prompt 模板 + 输出格式约定 + 资源约束 + 完成检测，fork 一个 Agent sub-task 后台跑。比每次手写 Agent prompt 省 10x。Use when user says \"spawn task\", \"fork agent\", \"开个 sub-agent\", \"并行任务\", \"background agent\", \"派活\"."
argument-hint: "[task-description] [--type research|review|code|audit] [--background]"
allowed-tools: Agent, Read, Write
---

# /spawn-task — Sub-Agent Fork Template

> 借鉴 ARIS `/experiment-queue` + AutoResearchClaw sub-agent pattern。

## Overview

把「fork 一个 sub-agent 让它去搞 X」标准化：

| 字段 | 内容 |
|---|---|
| `task_description` | 一句话 |
| `output_format` | JSON schema 或 markdown 段落约定 |
| `resource_constraint` | "max 10 tool calls" 或 "no WebSearch" |
| `completion_signal` | sub-agent 写 `.auto-production/spawn/<id>.done` |
| `timeout` | 默认 30min |

## Workflow

```bash
ID=$(uuidgen | head -c 8)
mkdir -p .auto-production/spawn/$ID

# emit prompt template
python3 tools/spawn_task.py prompt --type $TYPE --task "$TASK" > .auto-production/spawn/$ID/prompt.md

# fork via Agent tool (foreground or --background)
Agent(prompt=prompt_text, description="$TASK", run_in_background=$BG)

# completion: sub-agent should `touch .done`
```

5 个 built-in `--type`：

- `research` — survey + summary
- `review` — code review
- `code` — implement a single function
- `audit` — fact-check / cite-verify
- `freeform` — user 自定 prompt

## Output

- `.auto-production/spawn/<id>/prompt.md`
- `.auto-production/spawn/<id>/result.md`
- `.auto-production/spawn/<id>/.done`

## Composition

- `/research-pipeline` 调多次 spawn (并行 idea-perspective + persona-probe)
- `/audit-driven-retrain` spawn audit sub-agent
- `/cross-review` spawn 2 critic sub-agent
