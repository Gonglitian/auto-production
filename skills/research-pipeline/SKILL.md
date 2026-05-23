---
name: research-pipeline
description: "一句话拉起完整科研 pipeline：从 idea → 实验 → result → paper → submission。串联本仓所有 51 项 skill / hook / template，按 9-stage × 5-gate 节奏推进，每个 stage 强制经过 named gate 才放行。是本框架的最主要入口。Use when user says \"开始 research\", \"run pipeline\", \"全流程\", \"end-to-end\", \"从找 idea 到投稿\", \"start research on X\", \"做一篇 paper\", \"研究 X 这个方向\", \"/research X\", or wants the entire autonomous research lifecycle in one command."
argument-hint: "[research-direction] [— mode: full-auto|gate-only|co-pilot] [— venue: ICLR|NeurIPS|...] [— budget: 7d|14d]"
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent, Skill
---

# /research-pipeline — 完整科研流水线 ⭐

> 借鉴 ARIS `/research-pipeline`。这是 auto-production 框架的**主入口**。
> 一句话覆盖 Stage 1 → 9，按 design.md 的 5 个 named gate 强制节奏。

## Overview

```
/research-pipeline "factorized gap in discrete diffusion LMs"
```

把这条命令拉起：

```
[1 Idea] → NOVELTY → [2 Code] → METHOD+VLA-audit → [3 Data]
  → [4 ExpDesign] → RESOURCE → [5 Running] → [6 Result]
  → A1 PIVOT? → RESULTS → [7 Doc] → [8 Paper]
  → FINAL → [9 Promotion]
```

每个 stage 之间过 named gate。每个 gate fail → 退回上一 stage 不允许偷过。

## When to Use

- **主入口**：user 说「开始研究 X」/「做一篇 paper」/「end-to-end run」/「全流程」
- 第一次启动新 project
- 想从 idea 到投稿全自动走（适当 HITL）

## Constants

- **MODE** = `co-pilot`（默认）/ `full-auto` / `gate-only` / `checkpoint`
- **VENUE** = 不设定则不进 paper writing 阶段
- **BUDGET** = `7d`（总 wall-clock budget，到达 100% 强制 stop）
- **AUTO_PROCEED** = `false`（gate 默认问 user；`true` 让 agent 自己判 PROCEED/REFINE/PIVOT）
- **PROJECT_ROOT** = `$(pwd)`

## Workflow

### Phase 0 — bootstrap

```bash
# 1. ensure dir layout
mkdir -p .auto-production/{audit,cache/citations,meta_opt,baseline}

# 2. write CLAUDE.md if missing
[ -f CLAUDE.md ] || cp $AUTO_PRODUCTION_REPO/templates/CLAUDE.md ./CLAUDE.md

# 3. write hooks
[ -f .claude/settings.json ] || cp $AUTO_PRODUCTION_REPO/templates/settings.json ./.claude/settings.json

# 4. mark current stage
echo "1" > .auto-production/stage

# 5. record research direction
echo "$ARGUMENTS" > .auto-production/research_direction.md
```

### Stage 1 — Idea Generation

```
Skill(/idea-perspective)        # STORM 5-10 paper perspective
Skill(/idea-sim-convo)          # writer × expert role-play
Skill(/persona-probe)           # 8-stakeholder questions
Skill(/novelty-check)           # S2 / OpenAlex
```

Output: `proposal.md` + 8-persona Q list + novelty report → `idea-stage/`

**Gate NOVELTY**：检查 `idea-stage/proposal.md` + `novelty.json` + `persona_questions.md` 齐备。

### Stage 2 — Code Generation

```
Skill(/arch-plan)               # multi-file 改动前先画依赖图
Skill(/ast-validate)            # 写完 AST 静态扫
Skill(/vla-audit)               # ⭐ train ↔ eval 6 维度对齐
```

**Gate METHOD**：`.auto-production/audit/vla_audit.passed` + commit 匹配。

### Stage 3 — Data & Resource

```
Skill(/resource-planning)       # 列下载 size / 估时
Skill(/corpus-schema)           # literature_corpus_entry.schema.json 记录
Skill(/benchmark-agent)         # surveyor → selector → acquirer → validator
```

### Stage 4 — Experiment Design

```
Skill(/sprint-contract --init)  # ⭐ 5-tuple
Skill(/sprint-contract --verify)
Skill(/sprint-contract --sign)
Skill(/run-zero --seeds 3)      # ⭐ baseline lock
Skill(/smoke-test)              # 起正式前先 smoke
```

**Gate RESOURCE**：5-tuple signed + run_0 locked + smoke passed。

### Stage 5 — Tasks Running

```
Skill(/slurm-hold --partition raise --days 7)    # 长期占位
Skill(/cross-host-sync --direction push)         # 登记到 Notion
# 起训
Bash: python train.py --config ... &
# 后台监督
Skill(/stall-detect --watch <pid> --timeout 600 --action ping)
Skill(/promise-check)            # PostToolUse hook 自动
```

如 `mode == full-auto` 自动跑 `/sleep-research` 起夜间 loop。

### Stage 6 — Result

```
Skill(/auto-viz --wandb-run <id>)               # ⭐ 4 张图
Skill(/html-homepage --auto-refresh 60)         # 主页刷
Skill(/pivot --run <id>)                        # ⭐⭐ PROCEED/REFINE/PIVOT
```

按决策分支：
- **PROCEED** → Stage 7
- **REFINE** → `/auto-version` + 新 `/sprint-contract --init` → 回 Stage 4
- **PIVOT** → snapshot + 回 Stage 1

**Gate RESULTS**：decisions.jsonl 新 entry + findings.md 复盘段。

### Stage 7 — Doc

```
Skill(/learn-tag)               # [LEARN:method] 入 MEMORY.md
# 更新 README / DEPLOYMENT / EXPERIMENT_STATUS / findings
```

### Stage 8 — Paper Writing（如 `--venue` 设定）

```
Skill(/paper-pipeline --venue ${VENUE})    # 6-stage linear: outline→draft→review→revise→format→cite-verify
Skill(/citation-audit)                      # ⭐ 3-layer anchor verify
Skill(/cross-review --rounds 3)             # ⭐ Claude × GPT × Gemini
Skill(/pubfig)                              # publication-ready figures
```

**Gate FINAL**：`/citation-audit` PASS + `/cross-review` CONVERGED + A5 failure checklist clean。

### Stage 9 — Promotion + Post-Acceptance

```
Skill(/paper-talk)              # 12 min script
Skill(/paper-poster)            # 3'×4'
Skill(/paper-slides)            # 10 页
# 落地 social：red book / X / bilibili
```

如 reviewer 给意见：

```
/rebuttal — venue: ${VENUE}, character_limit: 5000
/kill-argument  # 准备反驳武器
/resubmit-pipeline  # 换 venue
```

### Phase ∞ — Self-evolve（cron）

每周自动跑：

```
Skill(/meta-optimize --since 7d)
```

收集本周 failure log → patch skills/ prompt → commit。

## Output

按 stage 产出，最终一份 paper 可投稿。所有中间产物：

```
project/
├── proposal.md                 # Stage 1
├── idea-stage/
├── .auto-production/audit/     # 各 gate trace
├── runs/                       # ckpt / log
├── figures/                    # auto-viz PNG
├── homepage.html               # /html-homepage
├── findings.md                 # /pivot 决策史
├── sprint_contract.yaml        # 当前合同
├── promise.json                # agent 承诺账本
├── paper/                      # Stage 8 LaTeX
└── EXPERIMENT_STATUS.md        # cross-host runs table
```

## Failure modes / fallbacks

| 现象 | 处理 |
|---|---|
| 某 stage 卡 >1h | `/stall-detect` 自动 ping user |
| budget 用完 | 强制 stop，emit partial report |
| user 长时间不在 | switch 到 `co-pilot` 改 `gate-only`；继续推进 |
| reviewer 不可用 | fallback 单模型 self-review，warn user |
| 任何 gate 反复 fail | 强制 PIVOT 回 Stage 1 |

## Composition

本 skill **不**实现具体动作，全靠 `Skill()` 调用其他 atomic skill。
完整列表 → [`AGENT_GUIDE.md`](../../AGENT_GUIDE.md)。
变种入口：

- `/research-pipeline "topic" — ref-paper: <url>` → targeted mode，improve 给定 paper
- `/research-pipeline — rebuttal` → 跳到 `/rebuttal`
- `/sleep-research "X"` → 包一层 stop-hook + heartbeat 跑夜间版本

## Example

```
User: /research-pipeline "factorized gap in discrete diffusion LMs" — venue: NeurIPS, mode: full-auto, budget: 14d

Agent:
**Conclusion**: Pipeline started in full-auto mode, 14-day budget.
**What I changed**:
- created .auto-production/ structure
- copied CLAUDE.md + settings.json hooks
- recorded direction
**What I checked**:
- AUTO_PRODUCTION_REPO env set ✓
- git initialized ✓
- conda env detected: hf_jax ✓
**Risks**:
- full-auto skips NOVELTY/RESOURCE/RESULTS gate user confirmation (Guard 仍触发)
**Next step**:
- /idea-perspective + /novelty-check (Stage 1, ETA 2h)
- 我会每 stage 末 push 一次 /cross-host-sync 让你随时能 /status

[continues...]
```
