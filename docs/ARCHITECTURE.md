# ARCHITECTURE.md

> 9 stages × 5 named gates × 5 横切机制 × **57 skills** (51 from design.md + 6 grown from real-test). 全部映射回 `../design.md` 的编号。

## 横切机制（always-on，每个 stage 都执行）

| 机制 | 主要 skill / hook |
|---|---|
| 透明性 (Transparency) | `/status`, `/auto-viz`, `/html-homepage`, `/conclusion-first` |
| HITL (Human-in-the-loop) | `/double-check`, `/concession-threshold` + `mode: full-auto/co-pilot` |
| Quality gate | `/promise-check`, `/stall-detect`, hooks `pre_destructive_git`, `stop_smoke_gate` |
| Multi-host & Autonomy | `/cross-host-sync`, `/slurm-hold`, `/sleep-research` |
| Self-evolution | `/meta-optimize` (weekly cron) |

## 9 Stages

| Stage | Skills | Gate at exit |
|---|---|---|
| 1 Idea | `/idea-perspective`, `/idea-sim-convo`, `/persona-probe`, `/novelty-check` | **NOVELTY** |
| 2 Code | `/arch-plan`, `/ast-validate`, **`/vla-audit`** ⭐ | **METHOD** |
| 3 Data | `/resource-planning`, `/corpus-schema`, `/benchmark-agent`, `/datalake` | (no formal gate) |
| 4 Exp Design | **`/sprint-contract`** ⭐, `/task-notes-yaml`, **`/run-zero`** ⭐ | **RESOURCE** |
| 5 Running | `/slurm-hold`, `/cross-host-sync`, `/sleep-research`, `/spawn-task`, `/audit-driven-retrain`, **`/smoke-test`** | (no exit gate, runs continuous) |
| 6 Result | `/auto-viz`, **`/pivot`** ⭐⭐, `/plateau-detect`, `/auto-version`, `/tree-viz`, `/findings-map` | **RESULTS** |
| 7 Doc | `/learn-tag` | — |
| 8 Paper | `/paper-pipeline`, `/paper-mode`, **`/citation-audit`** ⭐, **`/cross-review`** ⭐, `/pubfig`, `/paper-talk`, `/paper-poster`, `/paper-slides`, `/rebuttal`, `/kill-argument`, `/resubmit-pipeline` | **FINAL** |
| 9 Promotion | (project website, social) | — |

## 5 Named Gates

每个 gate = 「必须看到 checklist 全 ✓ 才能离开 stage」。Agent 检查 `.auto-production/audit/<gate>.passed` 是否存在 + commit 匹配。

| Gate | Stage transition | Checklist |
|---|---|---|
| **NOVELTY** | 1 → 2 | `idea-stage/proposal.md` + `novelty.json` (S2/OpenAlex) + `persona_questions.md` |
| **METHOD** | 2 → 4 | `.auto-production/audit/vla_audit.passed` 含当前 commit hash + AST validate clean |
| **RESOURCE** | 4 → 5 | `contract_signed.json` (sha256 of sprint_contract.yaml) + `baseline/run_zero_<host>_<commit>.json` + `smoke_passed.json` |
| **RESULTS** | 6 → 7 | `decisions.jsonl` 最新 entry (PROCEED/REFINE/PIVOT) + Guard 复盘 + A5 failure checklist |
| **FINAL** | 8 → 9 | `cite_audit.json` verdict=PASS + `cross_review_log.json` CONVERGED + 所有 5-tuple 字段 ✓ |

## Resolver chain

任何 skill 调 helper 时按 3 层 fallback：

1. `.auto-production/tools/<name>` —— project-local override
2. `tools/<name>` —— repo-local（最常见）
3. `$AUTO_PRODUCTION_REPO/tools/<name>` —— global install

便于不同 project 用不同变种（如各项目 `vla_audit_loader.py`）。

## 入口结构

```
/research-pipeline "<topic>"      # 主入口，9-stage 全跑
   └─ /sleep-research "<goal>"    # 夜间 wrapper（加 stop-hook + heartbeat）
       └─ /research-pipeline      # 内层一层

或者拆开手动：
/sprint-contract --init/sign      # Stage 4 入口
/vla-audit                         # Stage 2 出口
/pivot                             # Stage 6 决策
/citation-audit + /cross-review    # Stage 8 终审
```

## State files & write locations

| 文件 | 谁写 | 谁读 |
|---|---|---|
| `sprint_contract.yaml` | user (via `/sprint-contract --init`) | METHOD/RESOURCE gate, `/pivot` |
| `.auto-production/audit/*.passed` | gate skills | 下游 gate 检查 |
| `findings.md` | `/pivot` | `/html-homepage`, `/meta-optimize` |
| `promise.json` | `post_promise_check.sh` hook | `/status`, `/meta-optimize` |
| `decisions.jsonl` | `/pivot` | `/meta-optimize` |
| `.auto-production/active_runs.json` | `/cross-host-sync pull` | `/status`, `/html-homepage` |
| `homepage.html` | `/html-homepage` | user 浏览器 |

参见 `GATES.md` 各 gate 的具体 checklist，`WORKFLOWS.md` 命名 workflow。
