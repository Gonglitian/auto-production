---
name: debate-judge
description: "重大决策时让 N 个 agent 用 N 种立场辩论，再用 blind judge 给结论。比 cross-review 更结构化（明确的 pro/con/judge 三方）。Use when user says \"debate\", \"辩论\", \"几个 agent 各执一词\", \"blind judge\", \"pro con\", \"重大决策\"."
argument-hint: "[question] [--n-debaters 3] [--rounds 2]"
allowed-tools: Read, Write, Agent
---

# /debate-judge — N-Position Debate + Blind Judge

> 借鉴 autoresearch `/reason`。

## Overview

3-role pattern：

| 角色 | 数量 | 任务 |
|---|---|---|
| Debater | N (默认 3) | 各自坚持一个立场，每轮反驳别人 |
| Judge | 1 | blind 看 transcript（不知谁说了什么），给胜出 + 理由 |
| Synthesizer | 1 | 把 judge 决策 + 最佳论点合成最终方案 |

## Workflow

1. Spawn N debater，prompt 各分一个立场（user 指定 or agent 划分）
2. R 轮（默认 2）：每 debater 答 + 反驳
3. blind 化 transcript（去掉 "Debater 1/2/3" 标签）
4. Judge sub-agent 看 → 判
5. Synthesizer 输出最终方案

## Output

- `.auto-production/debates/<ts>/transcript.md`
- `.auto-production/debates/<ts>/judge_verdict.md`
- `.auto-production/debates/<ts>/synthesis.md`

## Composition

- `/pivot` 决策 stuck 时调
- Stage 1 idea 选择 stuck 时调
- 比 `/cross-review` 更适合 "选 A 还是 B" 类二选一
