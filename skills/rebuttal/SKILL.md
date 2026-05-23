---
name: rebuttal
description: "Reviewer 评论流水线：分类 → 找 supporting evidence → 写 rebuttal → cross-model review → submit。3 道 safety gate：no fabrication / no overpromise / full coverage。Use when user says \"rebuttal\", \"reviews\", \"reviewer 来了\", \"反驳\", \"答辩\", \"OpenReview comment\"."
argument-hint: "[paper-dir-with-reviews] [--venue ICML] [--char-limit 5000]"
allowed-tools: Bash(*), Read, Write, Edit, Agent, Skill, WebSearch
---

# /rebuttal — Reviewer-Comment Reply Pipeline

> 借鉴 ARIS `/rebuttal`。Stage 9 / acceptance loop。

## Overview

5 阶段：

0. **Parse reviews** → `paper/reviews/parsed.json`（per-reviewer concerns 列表）
1. **Categorize** 每条 concern：`factual-question` / `request-for-experiment` / `clarification` / `subjective-criticism`
2. **Evidence gather** 每条对应 paper/code/data 段
3. **Draft** rebuttal 文本（按 char limit）+ `/cross-review --rounds 2`
4. **Safety gate**：
   - 🔒 No fabrication — 每 claim 必须 link 到 paper/code/user-confirmed result
   - 🔒 No overpromise — 任何「we will add X」必须 user 批准
   - 🔒 Full coverage — 每 concern 都 addressed
5. **Emit**：`PASTE_READY.txt`（精确字符数）+ `REBUTTAL_DRAFT_rich.md`（rich text，留 manual edit）

## Workflow

```bash
VENUE=${VENUE:-ICML}
CHAR=${CHAR_LIMIT:-5000}
python3 tools/rebuttal.py parse paper/reviews/*.md > paper/reviews/parsed.json
# loop 5 stages...
```

## Output

- `paper/reviews/parsed.json`
- `paper/rebuttal/draft.md`
- `paper/rebuttal/PASTE_READY.txt`
- `paper/rebuttal/REBUTTAL_DRAFT_rich.md`

## Composition

- 联动 `/kill-argument` 准备反驳武器
- 联动 `/cross-review` 二审
- 如有新 experiment 需求 → `/experiment-bridge` (未实现，placeholder)
