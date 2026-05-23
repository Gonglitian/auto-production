---
name: idea-sim-convo
description: "Simulated Conversation (writer × expert)。Agent 扮演 writer 和 expert 两个角色互相 role-play 深挖一个 topic。比单一 monologue 出来的 idea 更扎实。Use when user says \"sim conversation\", \"对话深挖\", \"扮演专家\", \"两个 agent 聊\", \"role-play idea\", \"思辨\"."
argument-hint: "[topic-or-question] [--turns 6]"
allowed-tools: Read, Write, Agent
---

# /idea-sim-convo — Simulated Writer × Expert Dialogue

> 借鉴 STORM。Stage 1 deep-dive skill。

## Overview

2 角色：

| 角色 | 任务 |
|---|---|
| **Writer** | 提问 / 追问 / 把答案 link 回 idea 范畴 |
| **Expert** | 拿 specific 实例和文献回答 / 指出 writer 的假设漏洞 |

固定 N 轮（默认 6）→ emit transcript + 提炼出 K 个 candidate ideas。

## When to Use

- 已有 `/idea-perspective` 出的 question，想深挖其中 1-2 条
- 或 user 直接给一个 question 想看 trade-off

## Workflow

1. Agent fork 2 sub-agent：writer + expert
2. Writer 首问：「Q: $TOPIC」
3. Expert 答：基于知识 + WebSearch（如有）
4. Writer 追问 trade-off / weakness
5. 重复 N 轮
6. 最后 Writer 收尾：「我们这次得出了哪 K 个 candidate idea?」
7. 写 transcript + candidates 到 `idea-stage/sim_convo_$TS.md`

## Output

- `idea-stage/sim_convo_<timestamp>.md` (transcript + 3-5 candidate ideas)

## Composition

后置：用 `/novelty-check` 跑每个 candidate idea；user 拍板进 Stage 2。
