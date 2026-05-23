---
name: conclusion-first
description: "Agent 报告强制 5-段格式：Conclusion / What I changed / What I checked / Risks / Next step。替代散漫输出。User 找重点更快。系统 prompt 一句话，永久受益。Use when user says \"conclusion first\", \"5-段\", \"按格式\", \"summary 格式\", \"report format\", or apply as default output style."
argument-hint: ""
allowed-tools: Read, Write
---

# /conclusion-first — 报告 5-段强制格式

> 借鉴 claude-scholar `expression-skill`。横切机制 Part I §1 F9。

## Overview

任何 agent user-facing 报告必须按以下 5 段输出（**严禁**省略段、严禁加新段）：

### 1. Conclusion（一句话）

直接给结论：「成了」/「失败」/「需要 user 决策」+ 一行核心结果。

### 2. What I changed（要点列表）

具体改了什么文件 / config / state。每项一行，file:line 引用。

### 3. What I checked（验证记录）

跑了什么测试 / smoke / 哪些 gate 通过 / 看了什么 log。不写 "我 think 没问题"——必须实证。

### 4. Risks（已知未解决问题）

明确列没覆盖的 case / TODO / 可能踩的雷。**没风险也要写「No known risks」**——不允许跳过这段。

### 5. Next step（建议或问 user）

一行：要么是 agent 接下来 going to do，要么 AskUserQuestion 问 user 拍板。

## When to Use

- **Always**——这是 default output format
- 长任务结束、`/sleep-research` 收尾、`/pivot` decision、跨 turn 总结

## Constants

- **SECTIONS** = `["Conclusion", "What I changed", "What I checked", "Risks", "Next step"]`
- **MAX_LINES_PER_SECTION** = `8`（防 ramble）

## Workflow

这是一个 **template skill**，不实际跑代码——只是 enforce output structure。Agent 应该把它当 system prompt 永久 enable。

注册方式（在 `templates/CLAUDE.md`）：

```markdown
## Output format

Every user-facing report MUST follow `/conclusion-first` 5-section format.
See `<repo>/skills/conclusion-first/SKILL.md`.
```

## Example

错误（散漫）：

```
我把 vla-audit 跑了，结果有 3 个 diff。后来我又看了下 train config，发现 dtype 是 bf16，但 eval 是 fp32。然后我改了 eval config 把 dtype 也设成 bf16。我觉得应该没问题了，要不要再跑一次？
```

正确（5-段）：

```
**Conclusion**: VLA audit 失败，修了 dtype mismatch，建议重跑 audit 确认。

**What I changed**:
- configs/eval.yaml:12 — dtype: fp32 → bf16

**What I checked**:
- /vla-audit 报 3 diff（dtype / normalization / action_range）
- normalization 和 action_range 是 audit 误报（实际相等，浮点误差），已 patch tools/vla_audit.py:88

**Risks**:
- bf16 eval 数值精度可能比 fp32 低，eval SR 可能掉 ~0.5%
- 没测多 GPU 场景

**Next step**:
- 重跑 /vla-audit 验证，pass 后 /sprint-contract --sign，然后起正式 run
```

## Failure modes

| 现象 | 处理 |
|---|---|
| Agent 偷懒省略 Risks 段 | 主动 self-check：「我有没有 5 段都写？没有 → 补」 |
| 段内超过 MAX_LINES | 拆 sub-bullet，但保持 5 顶级段 |
| 报告极短（一句话回应）| OK，"Conclusion-only" 模式允许（如简单 Q&A）|

## Composition

- 所有其他 skill 的 `Output` 段应 reference 本 skill
- `/double-check` 与本 skill 并用：先 5-段，再 confidence 0-5
- `/cross-review` 输出也走 5-段
