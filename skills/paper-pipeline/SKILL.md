---
name: paper-pipeline
description: "Paper 写作 6-stage 流水线：outline → draft → review → revise → format → cite-verify。每 stage 出 deliverable，不一气呵成。Use when user says \"paper pipeline\", \"写 paper\", \"投稿流水\", \"6-stage paper\", \"写论文\", \"start paper\"."
argument-hint: "[--venue NeurIPS|ICLR|...] [--start-stage 1] [--effort lite|polished|conference-ready]"
allowed-tools: Bash(*), Read, Write, Edit, Agent, Skill
---

# /paper-pipeline — 6-Stage Linear Paper Writing

> 借鉴 ARIS `/paper-writing`。FINAL gate 前的主入口。

## Overview

```
Stage 1: outline      → paper/OUTLINE.md
Stage 2: draft        → paper/sections/*.tex
Stage 3: review       → /cross-review N rounds
Stage 4: revise       → 改 draft
Stage 5: format       → /pubfig + bibtex tidy
Stage 6: cite-verify  → /citation-audit
```

每阶段产物 commit 一次，方便回滚。

## Workflow

```bash
VENUE=${1:-NeurIPS}
START=${2:-1}
EFFORT=${3:-polished}

for stage in 1 2 3 4 5 6; do
  [ $stage -lt $START ] && continue
  Skill(/paper-mode --stage $stage --venue $VENUE --effort $EFFORT)
  git add paper/; git commit -m "paper: stage $stage done"
done
```

每 stage 末调对应 atomic skill：

| Stage | Skill |
|---|---|
| 1 outline | `/paper-mode --mode outline` |
| 2 draft | `/paper-mode --mode draft` |
| 3 review | `/cross-review --rounds 3` |
| 4 revise | `/paper-mode --mode revise` |
| 5 format | `/pubfig` + format pass |
| 6 cite-verify | `/citation-audit` |

## Output

- `paper/` 目录完整
- `.auto-production/paper_pipeline_log.json` per-stage trace

## Composition

- 前置：Stage 6 RESULTS gate 已过（results 锁定）
- 后置：FINAL gate 检查 `cite_audit.json` + `cross_review converged`
