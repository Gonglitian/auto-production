---
name: idea-perspective
description: "STORM-style Perspective-Guided Question Asking. 找 5-10 篇 similar-topic paper → 提取每篇独特视角 → 用这些视角驱动 question 自动生成。破单一视角盲点。Use when user says \"找视角\", \"perspective\", \"STORM idea\", \"广角调研\", \"找问题方向\", \"idea brainstorm\", \"换角度想\"."
argument-hint: "[topic] [--k-papers 8]"
allowed-tools: Bash(*), Read, Write, WebSearch, WebFetch, Agent
---

# /idea-perspective — STORM Perspective-Guided Question Asking

> 借鉴 STORM (Stanford OVAL)。Stage 1 主力 idea skill。

## Overview

```
topic → S2/arXiv search → 8 similar papers → extract each paper's
"angle" / "framing" / "unique problem they pose" → use as N
different lenses to generate questions about your topic
```

## When to Use

- Stage 1 入口
- 「我对 X 感兴趣但不知道从哪问起」
- 比 `/idea-creator` 更系统（后者是单一视角）

## Workflow

1. **Search**：S2 API search `topic` → top 30 by citation → sample diverse 8
2. **Extract angle**：每篇 paper Agent 读 abstract+intro，emit 单行 angle：
   - "frames as constraint-satisfaction"
   - "frames as bandit problem"
   - "frames as distillation"
   - ...
3. **Question gen**：用每个 angle 当 lens，对 `topic` 生 3 questions
4. **Dedupe & rank**：按 novelty score 排，emit top 15

## Output

- `idea-stage/perspectives.json` — 8 angle + source paper
- `idea-stage/perspective_questions.md` — 24 questions
- 用 `/idea-sim-convo` 接续深挖某条 question

## Composition

前置：none. 后置：`/idea-sim-convo` / `/novelty-check` / `/persona-probe` 平行跑。
