---
name: learn-tag
description: "Agent 发现 lesson 时打 [LEARN:notation] / [LEARN:code] / [LEARN:method] 等 tag，自动入 MEMORY.md 对应 tier。跨 session 自动可被检索。Use when user says \"learn tag\", \"记一下\", \"memory tag\", \"lesson learned\", \"保存到 memory\", \"长期记忆\"."
argument-hint: "[--scan-input | --tier method|code|notation|tooling --content '...']"
allowed-tools: Bash(*), Read, Write, Grep
---

# /learn-tag — `[LEARN]` Tag Routing

> 借鉴 claude-research 9-hook 的 lesson router。

## Overview

Agent 输出含 `[LEARN:<tier>]` tag → 自动 route 到 `MEMORY.md` 该 tier 段。

支持 tier：`method` / `code` / `notation` / `tooling` / `pitfall` / `convention`。

## Workflow

`--scan-input`（hook 模式）：

```python
for m in re.finditer(r'\[LEARN:(\w+)\]\s*(.+?)(?=\n\n|\Z)', text, re.DOTALL):
    tier, content = m.group(1), m.group(2).strip()
    append_to_memory_md_section(tier, content)
```

`--tier X --content Y`：手动 add 一条。

## Output

- `MEMORY.md` 各 tier 段被 append
- 与 Claude Code auto-memory 兼容（同样 markdown）

## Composition

- 作为 PostToolUse hook 自动跑
- `/meta-optimize` 周末整合相似 entry
- `/research-pipeline` 任何 stage 完成都可手动 add
