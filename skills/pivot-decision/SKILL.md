---
name: pivot-decision
description: "每个实验跑完，agent 强制输出 PROCEED/REFINE/PIVOT 三选一建议 + 理由 + AskUserQuestion 让 user 拍板。不允许默认 '再加点 step 试试' 这种隐式 PROCEED。Stage 6 → 7 之间 RESULTS gate 的关键。用户说 'pivot' / '决策' / 'what next' / '下一步' / 'PROCEED REFINE PIVOT' 时调用。"
argument-hint: "[--run <wandb-run>] [--auto-suggest|--ask-user]"
allowed-tools: Bash(*), Read, Write, Edit, Agent
---

# /pivot — PROCEED / REFINE / PIVOT 决策节点 ⭐⭐

来源 = A1 [AutoResearchClaw stage-15 / ARIS / AI-Scientist-v2 BFTS]。

**最重要的 skill**。防默认 "再加点 step 试试" 的隐式 PROCEED 病。

## The Three Options

| Decision | When | Action |
|---|---|---|
| **PROCEED** | Metric ≥ Sprint Contract threshold AND Guard 未触发 AND 结果可信（vla-audit 过 / seed > 3 / variance OK） | 进下一个 stage / sprint |
| **REFINE** | 思路对（看 trend 在涨）但参数/数据/超参没调到位 | 列出待调超参 diff，重起一次 sprint（A7 auto-version snapshot） |
| **PIVOT** | Guard 触发 OR Metric << threshold OR vla-audit 反复 FAIL OR plateau detector 触发 | 回 Stage 1 重新设计；snapshot 当前 → `stage-N_v{K}/` |

## Workflow

### Phase 1: Pull current state

- 读 `sprint_contract.yaml` 5-tuple
- 读 `runs/<latest>/wandb-summary.json`
- 读 `.auto-production/run_zero.json`
- 读 `findings.md`（看过去 N 个 sprint 决策）

### Phase 2: Auto-suggest

调一个 sub-agent 用以下 prompt 评估：

```
你是 ML 决策辅助。读：
1. Sprint Contract (5-tuple)
2. Latest run metrics
3. run_0 baseline
4. Past sprint findings (是否 plateau)

输出 JSON:
{
  "suggestion": "PROCEED" | "REFINE" | "PIVOT",
  "rationale": "1-3 sentences with numbers",
  "metric_vs_threshold": {...},
  "metric_vs_run_0": {...},
  "guard_triggered": bool,
  "plateau_detected": bool,  // 看是否连续 ≥ 3 sprint metric 不动
  "refine_proposal": null | {"params_to_change": [...], "rationale": "..."},
  "pivot_proposal": null | {"new_direction": "...", "rationale": "..."},
}
```

### Phase 3: Ask user (AskUserQuestion)

强制 3-选项 question：

```python
AskUserQuestion(
  question="Latest run: SR=0.62 (target 0.70, run_0=0.55). Suggestion: REFINE.",
  options=[
    {"label": "PROCEED (推荐如果 ...)", "description": "..."},
    {"label": "REFINE (推荐如果 ...)", "description": "..."},
    {"label": "PIVOT (推荐如果 ...)", "description": "..."},
  ]
)
```

`--auto-suggest` 模式：只输出建议不问 user（autonomous 模式用，但仍写到 findings.md 让 user 醒来看）。

### Phase 4: 执行选定路径

- **PROCEED**：清 `sprint_contract.yaml`，提示 `/sprint-contract --init` 起下一个
- **REFINE**：调 `/auto-version` snapshot 当前 → `<stage>_v{N+1}/` + 应用 refine_proposal.params_to_change → 重起
- **PIVOT**：调 `/auto-version` snapshot + 回 Stage 1 (`/idea-perspective` 或 `/idea-creator`)

### Phase 5: 写 findings.md

每次 decision 一条：

```markdown
## 2026-05-22 — sprint v6 stage 1

- Goal: 5 guiding @ 40M step → SR ≥ 0.7
- Result: best 0.71, worst 0.52 (4/5 达标)
- Decision: **REFINE** for guiding-#3 only (lr 4e-5 → 2e-5), PROCEED for stage 2 of others
- Reason: guiding-#3 reward variance 高，怀疑 lr 大；其他 4 个 metric 稳定。
- Sprint contract Guard: 未触发（worst 0.52 > 0.4 threshold）
```

## Output

终端三选一 prompt + `findings.md` append + sub-agent 写的 JSON 报告留底 `.auto-production/pivot/<date>.json`。

## Failure modes

- Plateau 触发但 user 仍选 REFINE → warn 一次后允许（user 知道自己在干嘛）
- Metric 缺失 → 强制 PIVOT (无 metric 等于无证据)
- 没 sprint_contract.yaml → 报错让 user 先 `/sprint-contract --init`

## See also

- [`/sprint-contract`](../sprint-contract/SKILL.md) — 5-tuple 入口
- [`/run-zero`](../run-zero/SKILL.md) — baseline 比对
- [`/auto-version`](../auto-version/SKILL.md) — snapshot on REFINE/PIVOT
- [`/plateau-detect`](../plateau-detect/SKILL.md) — 多 sprint 趋势检测
