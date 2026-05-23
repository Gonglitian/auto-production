---
name: double-check
description: "Agent 主动输出 confidence rating 0-5 + 列出可疑点。把 user 频繁说的 \"double check 一下\" 固化。Use when user says \"double check\", \"再确认\", \"你确定吗\", \"confidence\", \"自查\", \"reliability\"."
argument-hint: "[claim-or-output]"
allowed-tools: Read
---

# /double-check — Self-Confidence Audit

> 借鉴 user 11K 对话 "double check" 频次 + claude-research 自检 pattern。

## Overview

任何 agent 报告完，自查输出：

```
**Confidence: 4/5**

Suspicious points to verify:
1. Last GPU util reading may be stale (cache 30s)
2. Run v6-meta wandb URL was guessed from naming pattern, not fetched
3. Smoke gate passed but only with bs=2 — real bs=8192 might OOM
```

## Workflow

非可执行 skill——是 output style enforcement。可作为 PostToolUse hook 自动 append。

Agent 自我评：

```python
self.confidence = self.assess_confidence(
    sources_verified=True,
    fresh_data=True,
    edge_cases_covered=False,  # → -1
    has_speculation=True,       # → -1
    user_can_re_verify=True
)
# emit confidence X/5 + list each -1 reason
```

## Composition

- 配合 `/conclusion-first` 用：5-段报告之后 append confidence
- `/pivot` 推荐时强制 emit confidence
- `/cross-review` 判收敛时看每方 confidence
