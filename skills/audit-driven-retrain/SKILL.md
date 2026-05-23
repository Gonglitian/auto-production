---
name: audit-driven-retrain
description: "标准化失败 retrain 循环：scancel → audit (sub-agent) → patch → 重起。这次 hf-jax 做了 v3/v4/v5/v6 4 次的模板化。Use when user says \"audit retrain\", \"重训\", \"训挂了\", \"scancel audit patch\", \"diagnose retrain\", \"为什么 SR 低\"."
argument-hint: "[--current-run <id>] [--hypothesis '...']"
allowed-tools: Bash(*), Read, Write, Edit, Agent, Skill
---

# /audit-driven-retrain — scancel → audit → patch → retry

> 借鉴 user 在 hf-jax v3→v6 实战 pattern。

## Overview

4 阶段闭环：

1. **scancel** 现 run（保留 ckpt + log）
2. **audit** sub-agent (`/spawn-task --type audit`)：读 log + 最后 ckpt metric + 用户给的 hypothesis，定位 root cause
3. **patch** 用 Edit 改文件（小 diff）+ commit
4. **retry** 走 `/smoke-test` → `/run-experiment`

每轮自动 `/auto-version` snapshot 旧 run dir。

## Workflow

```bash
RUN=${RUN:-$(/status --format json | jq -r '.runs[0].id')}
# Phase 1: scancel
ssh $HOST scancel <jobid>
# Phase 2: audit
Skill(/spawn-task --type audit --task "diagnose run $RUN, hypothesis: $HYP")
wait
# Phase 3: patch
# (user or agent reads audit result, makes Edit calls, commits)
# Phase 4: retry
Skill(/smoke-test)
Skill(/auto-version)
ssh $HOST sbatch <next.sbatch>
```

## Output

- `.auto-production/retrain/<round>/audit.md`
- `.auto-production/retrain/<round>/patch.diff`
- 自动 commit `fix(retrain-v<N>): <root-cause>`

## Composition

- 触发 conditions（自动）：训练 SR 卡住 / job 反复 FAILED / `/pivot` 决策 REFINE
- 后置 `/run-experiment` 起新 run
