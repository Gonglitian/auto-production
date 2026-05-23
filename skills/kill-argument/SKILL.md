---
name: kill-argument
description: "为 reviewer 找茬准备反驳武器库。给一个 claim，agent 列出 5 种最可能的攻击角度 + 每个怎么反驳，附 evidence 链接。Use when user says \"kill argument\", \"反驳武器\", \"reviewer 会怎么挑\", \"adversarial defense\", \"theory paper 防御\"."
argument-hint: "[claim-text-or-paper] [--threats 5]"
allowed-tools: Read, Write, Agent, WebSearch
---

# /kill-argument — Adversarial Defense Toolkit

> 借鉴 ARIS `/kill-argument`。Theory paper 必备。

## Overview

输入一个 paper claim，对每个 claim emit：

```
Claim: "Our method achieves SR 87% on MC10, beating SOTA by 5%."

5 potential attacks:
1. "How do you control for seed variance? +5% can be 1σ"
   → defense: 5 seeds, 95% CI [82, 92], baseline CI [76, 80] — non-overlapping
   → evidence: paper Tab 3
2. "Baseline is a weak comparison — newer SOTA exists"
   → defense: ...
3. ...
```

## Workflow

1. Read claim
2. Spawn 5 adversarial sub-agents (each 1 angle)
3. Each emit attack + defense + evidence pointer
4. Merge → `paper/defenses/<claim_id>.md`

## Output

- `paper/defenses/<claim>.md`
- 喂给 `/rebuttal` 当 ammunition

## Composition

- `/rebuttal` 调本 skill 准备 reviewer 还没问的潜在追问
- Stage 8 paper drafting 时也可调，主动消除弱点
