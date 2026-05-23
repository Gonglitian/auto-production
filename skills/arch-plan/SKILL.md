---
name: arch-plan
description: "大改动 (>3 文件) 之前先画依赖图 + 改动计划，确认后再动手。防止 \"改一个文件牵动一堆，回头难收尾\"。Use when user says \"arch plan\", \"改动计划\", \"画依赖图\", \"重构前\", \"big change\", \"多文件改\", \"先规划\"."
argument-hint: "[--files file1,file2,...] [--goal '...']"
allowed-tools: Bash(*), Read, Write, Grep, Glob, Agent
---

# /arch-plan — Multi-File Architecture Plan

> 借鉴 AutoResearchClaw CodeAgent v2。METHOD gate 软前置。

## Overview

任何改动涉及 >3 文件，强制先：

1. 列待改文件 + 每个 file:line 计划改动
2. 画依赖图（who-calls-who，谁会被牵动）
3. emit Markdown 计划 → AskUserQuestion 是否 approve
4. approve 后才允许 Edit / Write

## Workflow

1. Glob/Grep 找待改文件 + 调用关系
2. Agent 出计划：
   ```
   File A:l.42 — modify signature foo(x) → foo(x, y)
     Affects: B (l.18), C (l.99), tests/test_A (l.30)
   File B:l.18 — update call site
   ...
   ```
3. AskUserQuestion: PROCEED / EDIT_PLAN / ABORT
4. PROCEED → 写 `.auto-production/arch_plan_<ts>.md` + 进入修改阶段

## Output

- `.auto-production/arch_plan_<timestamp>.md`
- `.auto-production/audit/arch_plan.approved`

## Composition

前置：none. 后置：METHOD gate 可选检查 arch_plan.approved。
