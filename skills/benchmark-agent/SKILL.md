---
name: benchmark-agent
description: "Benchmark 选择自动化：Surveyor (调研) → Selector (筛选) → Acquirer (下载) → Validator (验证完整性) 4 阶段 sub-agent pipeline。Use when user says \"benchmark agent\", \"选 benchmark\", \"benchmark 调研\", \"surveyor selector\", \"找 dataset\", \"benchmark pipeline\"."
argument-hint: "[task-description] [--top-k 3]"
allowed-tools: Bash(*), Read, Write, WebSearch, Agent, Skill
---

# /benchmark-agent — Surveyor → Selector → Acquirer → Validator

> 借鉴 AutoResearchClaw BenchmarkAgent。

## Overview

4-stage sub-agent pipeline：

1. **Surveyor** — search arxiv/papers-with-code/HF datasets 列 10+ candidate benchmark
2. **Selector** — 按 task 相关度 / community usage / license 排序 → 选 top-K
3. **Acquirer** — 用 `/resource-planning` + 实际 download script
4. **Validator** — 检查文件数 / hash / dataset 加载一遍出 1 batch

## Workflow

每 stage 一个 sub-agent，prompt 模板在 `tools/benchmark_agent_prompts.md`（待填）。

输出：

```
benchmark-stage/
├── candidates.json (Surveyor)
├── selected.json   (Selector + user PROCEED)
├── downloads/      (Acquirer + manifest)
└── validation.json (Validator)
```

## Composition

- Stage 3 主力
- 联动 `/corpus-schema` 写下载 entry
- 联动 `/datalake` 缓存常用 dataset 元数据
