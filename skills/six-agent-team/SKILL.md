---
name: six-agent-team
description: "固定 6 角色 self-evolving team：PI / postdoc / phd-student / engineer / reviewer / writer。每周 team review 一次，相互调整 prompt。仿真一个真实科研小组。Use when user says \"six agent\", \"6 角色\", \"team review\", \"虚拟 lab\", \"PI postdoc\", \"role play team\"."
argument-hint: "[--weekly-review | --route 'topic' --to phd|postdoc|reviewer]"
allowed-tools: Read, Write, Agent, Skill
---

# /six-agent-team — Self-Evolving 6-Agent Team

> 借鉴 EvoScientist。

## Overview

6 个 persistent persona（每个有自己的 prompt + memory）：

| Role | Style |
|---|---|
| **PI** | 战略 / 选题 / 资源批准 |
| **Postdoc** | 方法设计 / 拍方向 |
| **PhD student** | 跑实验 / 写代码 / 写 draft |
| **Engineer** | infra / scale / debug |
| **Reviewer** | 找漏洞 / 跟 cross-review 同源 |
| **Writer** | 把 finding 转 paper / talk / blog |

每周一次 team review：

1. 每 role 写一段「本周我做了 / 我看到的问题 / 下周建议」
2. 互相 critique
3. emit 5-行 team meeting note

可路由：「这个 idea 给 PI 看」/「这个 bug 给 engineer」/「写 abstract 给 writer」。

## Workflow

`--weekly-review` 调 6 sub-agent + 写 weekly_meeting.md
`--route X --to role` 单 role 路由：spawn 1 sub-agent with that role's persona

## Output

- `team/personas/<role>.md` (每 role 的 prompt + memory)
- `team/meetings/<date>.md` (每周复盘)

## Composition

- `/meta-optimize` 周末 + `/six-agent-team --weekly-review` 同期跑
- `/cross-review` 可路由到 reviewer + writer
