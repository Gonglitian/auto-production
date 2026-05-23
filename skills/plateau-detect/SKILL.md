---
name: plateau-detect
description: "N 个连续 sprint metric 不动（如 SR 卡在 60% 不上不下），自动弹窗建议 PIVOT 而不是继续 REFINE。防 sunk cost 心理一直 \"再试试\"。Use when user says \"plateau\", \"卡住了\", \"metric 不涨\", \"sunk cost\", \"该不该继续\", \"是不是该 pivot\"."
argument-hint: "[--n 3] [--rel-tol 0.01]"
allowed-tools: Bash(*), Read, Write
---

# /plateau-detect — Auto-Suggest PIVOT on Plateau

> 借鉴 autoresearch `/evals` plateau-detection。

## Overview

读 `decisions.jsonl` 后 N 条 PROCEED/REFINE 决策的 metric。若：

- 连续 N 条 metric delta < `rel_tol` (默认 1%)
- 且决策都是 REFINE 而非 PROCEED

→ emit PIVOT 推荐 + 列每条 delta，AskUserQuestion 是否 PIVOT。

## Workflow

```python
hist = [json.loads(l) for l in open('decisions.jsonl')][-N:]
deltas = [hist[i+1]['metric'] - hist[i]['metric'] for i in range(N-1)]
if all(abs(d / hist[0]['metric']) < REL_TOL for d in deltas) \
   and all(h['user_decision'] == 'REFINE' for h in hist):
    suggest_pivot(hist, deltas)
```

## Output

- AskUserQuestion 弹窗 + 写一行 `.auto-production/plateau_alerts.jsonl`

## Composition

- `/pivot` 决策前先调本 skill 看是否 plateau
- `/meta-optimize` 收集 plateau 历史给 patch 提示
