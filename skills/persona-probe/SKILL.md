---
name: persona-probe
description: "Start project 时用 8 种 stakeholder 视角（reviewer / PI / 同领域学生 / 跨领域学者 / 工业界 / 政策制定者 / 中文用户 / 复现者）各提 3 个问题，作为后续 AskQuestion 的弹药库。Use when user says \"persona probe\", \"8 stakeholder\", \"reviewer 视角\", \"各角度问题\", \"stakeholder questions\", \"想问题\"."
argument-hint: "[topic-or-proposal-md]"
allowed-tools: Read, Write, Agent
---

# /persona-probe — 8-Persona Stakeholder Probe

> 借鉴 autoresearch (uditgoenka) `/probe`。NOVELTY gate 必备产物。

## Overview

8 个固定 persona × 3 question each = 24 question 弹药库。

| Persona | 关心点 |
|---|---|
| **Reviewer (顶会)** | novelty / soundness / experiment rigor |
| **PI (你导师)** | story / position in lab roadmap |
| **同领域 PhD** | reproducibility / hyperparam sensitivity |
| **跨领域学者** | accessibility / 跨场景 generalization |
| **工业界 ML engineer** | inference cost / deployment friction |
| **政策制定者 / ethicist** | bias / dual-use / safety |
| **中文社区用户** | localization / Chinese-data 适配 |
| **复现者 (3 年后)** | environment / data / ckpt 可获得性 |

## When to Use

- Stage 1 NOVELTY gate 前
- 任何重大决策（如换 baseline）前

## Workflow

1. Read input topic / proposal
2. 对每个 persona，prompt sub-agent: 「from $persona's POV, what are the 3 most uncomfortable questions you'd ask about $proposal?」
3. 汇总 → `idea-stage/persona_questions.md`
4. 每题给 placeholder answer (`TBD by user/agent in Stage 4 verify`)

## Output

- `idea-stage/persona_questions.md` — 8 sections × 3 questions

## Composition

- NOVELTY gate 检查本 skill 输出存在 + 行数 ≥ 24
- Stage 4 `/sprint-contract` verify 字段引用本 skill 输出
- Stage 8 `/rebuttal` 优先答 reviewer persona 的问题
