# Auto-Production · 自动科研工作流 (ARIS 风格 / Skill-based)

> 🧪 让 Claude Code / Codex CLI / Cursor / Trae 在你睡觉时帮你做研究——从 idea 到 paper，全链路 skill 编排，跨机器、跨模型、跨工具。
>
> 📜 **方法论先行，零依赖**：每个 skill 都是一份 `SKILL.md`，纯 markdown + bash + Python 标准库。任何能读懂 markdown 的 agent runtime 都能跑。
>
> 🔄 **基于 51 项精挑细选**：从 16 个社区 auto-research 项目（ARIS / ARS / AI-Scientist-v2 / AutoResearchClaw / AgentLaboratory / STORM 等）+ 11K 条自身对话日志中提炼。完整设计见 [`../design.md`](../design.md)。

[English](README_EN.md) ｜ 中文

---

## 🎯 这是什么

把"做科研"拆成 **9 个 stage** + **5 个 named gate** + **51 个可装可拆的 skill / hook / template**，让 agent 能：

1. **自主推进** — `/sleep-research` 起一个夜间 autonomous loop，醒来看 PROCEED/REFINE/PIVOT 三选一报告
2. **跨机器协调** — `/cross-host-sync` 把 4 台机器上正在跑的 run + ckpt 实时同步到 Notion
3. **强制防呆** — promise-checker / stall-detector / VLA-audit / citation-audit 全程把关
4. **可被监管** — html homepage + auto matplotlib + Notion mirror，你随时能看进度
5. **能学习** — `/meta-optimize` 每周复盘 failure log → 自动 patch skill prompt

---

## 🏗️ 仓库结构

```
auto-production/
├── README.md             # 你正在看的
├── README_EN.md          # English version (skeleton)
├── AGENT_GUIDE.md        # 写给 agent 看的入口 (而非给人浏览)
├── CONTRIBUTING.md       # 怎么贡献新 skill
├── LICENSE               # MIT
│
├── skills/               # 51 个 skill，每个 1 份 SKILL.md
│   ├── status/SKILL.md           # /status — 当前所有 background task + GPU + 最新 metric
│   ├── vla-audit/SKILL.md        # /vla-audit ⭐ — train/eval pipeline 一致性 (你 #1 zero-shot bug)
│   ├── cross-host-sync/SKILL.md  # /cross-host-sync — 4 机器 run/ckpt ↔ Notion DB
│   ├── slurm-hold/SKILL.md       # /slurm-hold — hpcc raise 7-day hold + tmux + srun --overlap
│   ├── auto-viz/SKILL.md         # /auto-viz — 实验完自动出 4 张图 PNG
│   ├── html-homepage/SKILL.md    # /html-homepage — per-project live status html
│   ├── citation-audit/SKILL.md   # /citation-audit ⭐ — 3-layer anchor 防 hallucination
│   ├── cross-review/SKILL.md     # /cross-review ⭐ — Claude × GPT × Gemini 互审
│   ├── meta-optimize/SKILL.md    # /meta-optimize — 周复盘 failure → patch prompt
│   ├── sprint-contract/SKILL.md  # /sprint-contract — Karpathy 5-tuple gate
│   ├── run-zero/SKILL.md         # /run-zero — baseline lock per machine
│   ├── pivot-decision/SKILL.md   # /pivot — PROCEED/REFINE/PIVOT 三选一
│   ├── smoke-test/SKILL.md       # /smoke — 起正式前先 smoke
│   ├── promise-check/SKILL.md    # /promise-check — agent 说了 "我会..." 自动追踪
│   ├── stall-detect/SKILL.md     # /stall-detect — N 分钟无 stdout 告警
│   └── conclusion-first/SKILL.md # /conclusion-first — 报告 5-段强制格式
│
├── tools/                # Python 标准库 + bash 助手 (零外部依赖)
│   ├── cross_host_sync.py        # Notion API + ssh 多机扫描
│   ├── promise_check.py          # parse agent 输出找 "我会..." 入 promise.json
│   ├── stall_detect.py           # heartbeat watcher
│   ├── auto_viz.py               # wandb API → 4 PNG
│   ├── status.sh                 # 各机器 GPU + tmux + slurm queue 汇总
│   ├── smoke_gate.sh             # stop-hook 默认条件
│   └── verify_citations.py       # citation-audit 后端
│
├── templates/            # 可填入的 markdown / YAML 模板
│   ├── five_tuple.yaml           # Karpathy Goal/Scope/Metric/Verify/Guard
│   ├── sprint_contract.yaml      # 入口必填
│   ├── RESEARCH_BRIEF.md         # /sleep-research 输入
│   ├── CLAUDE.md                 # 新 project 起手 CLAUDE.md
│   ├── conclusion_first.md       # 5-段报告格式范例
│   └── settings.json             # Claude Code hooks 配置
│
├── hooks/                # Pre/Post-tool-use hooks (bash 脚本)
│   ├── pre_promise_check.sh      # PostToolUse: 扫描输出 → promise.json
│   ├── pre_destructive_git.sh    # PreToolUse: 拦 rm -rf / push --force
│   ├── pre_session_sync.sh       # SessionStart: git pull skills/
│   └── stop_smoke_gate.sh        # Stop: 检查 smoke 是否过
│
├── docs/                 # 文档
│   ├── ARCHITECTURE.md           # 9-stage × 5-gate × 5 横切机制
│   ├── WORKFLOWS.md              # 命名 workflow (W1-W6 + Wiki)
│   ├── GATES.md                  # 5 个 named gate 的 checklist
│   ├── INSTALL.md                # 安装到 Claude Code / Codex
│   └── design/                   # ADR 决策记录
│
├── tests/                # 结构性测试 (frontmatter / 链接完整性)
│   └── test_skill_format.py
│
└── examples/             # 用法演示
    └── from_idea_to_paper.md
```

---

## 🚀 快速上手

### 1. 安装到 Claude Code

```bash
# 克隆到你的 skills 目录
git clone <this-repo-url> ~/.claude/skills/auto-production

# 或者：复制到当前 project（让 skills 跟 project 走）
mkdir -p .claude/skills && cp -r skills/* .claude/skills/
```

### 2. 起一个新 project

```bash
# 在新 project 根目录
cp <repo>/templates/CLAUDE.md ./CLAUDE.md
cp <repo>/templates/sprint_contract.yaml ./sprint_contract.yaml
# 编辑 sprint_contract 填 Goal/Scope/Metric/Verify/Guard
```

### 3. 跑一个 skill

```
/sprint-contract   # 检查 5-tuple 填完
/status            # 看当前所有机器状态
/vla-audit         # 训练前必跑：train 和 eval pipeline 是否对齐
```

### 4. 起夜间 autonomous mode

```
/sleep-research "训完 stage 1 + 2 + eval，醒来给我 PROCEED/REFINE/PIVOT 报告"
```

详细安装见 [`docs/INSTALL.md`](docs/INSTALL.md)。

---

## 🧭 9-Stage Pipeline & 5 个 Named Gate

```
[1 Idea]        → NOVELTY gate   → [2 Code]    → METHOD gate +
                                                  VLA-audit ⭐
[3 Data]        → [4 Experiment Design] → RESOURCE gate
                                          (5-tuple + run-zero)
[5 Tasks Running]  ← 横切：promise-check + stall-detect 全程
[6 Result]         → A1 PROCEED/REFINE/PIVOT 决策 → RESULTS gate
[7 Doc] → [8 Paper] → FINAL gate (citation-audit + cross-review)
                    → [9 Promotion]
```

详见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) 和 [`docs/GATES.md`](docs/GATES.md)。

---

## ⭐ 重点 skill 速览

| Skill | 解决什么痛 | P |
|---|---|---|
| **`/vla-audit`** | train/eval pipeline 不一致（你 #1 zero-shot bug，OFT / GR00T / MemoryVLA / hf-jax 都中过） | P0 |
| **`/cross-host-sync`** | 4 台机器上「哪台跑了哪个 run」找半天，ckpt 路径靠脑记 | P0 |
| **`/citation-audit`** | paper 里编引用 → desk-reject 第一杀手 | P0 |
| **`/cross-review`** | 单模型 self-review 有 blind spot；Claude × GPT × Gemini 互审 | P0 |
| **`/pivot`** | 默认「再加点 step 试试」病；强制 PROCEED/REFINE/PIVOT 三选一 | P0 |
| **`/meta-optimize`** | agent 不会从错误学习；周复盘 failure log 自动 patch prompt | P0 |
| **`/sleep-research`** | 你 200+ 次手写 stop-hook + heartbeat，固化命名 skill | P0 |

完整 51 项见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#part-v-实现优先级)。

---

## 🧬 设计哲学（向 ARIS 学习）

1. **方法论 > 平台**：不锁定特定 runtime，纯 markdown skill 即可移植到 Codex / Cursor / Trae。
2. **跨模型对抗审 > 自审**：Claude 执笔，GPT/Gemini 找茬。Stochastic vs adversarial bandit——后者更难钻空子。
3. **3-layer resolver**：helper 查找顺序 `.auto-production/tools/` → `tools/` → `$REPO/tools/`。
4. **Stage gate 而非全自动**：5 个 named gate 是「必须有人或必须有 audit 通过才能继续」的硬卡点。
5. **Self-evolve**：失败 log 是金矿，`/meta-optimize` 周期把它们变成 skill 补丁。

---

## 📚 参考与致谢

- [ARIS (Auto-claude-code-research-in-sleep)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) — skill-based + cross-model review 范本
- [ARS (academic-research-skills)](https://github.com/Imbad0202/academic-research-skills) — Material Passport + citation anchor + sprint contract
- [AutoResearchClaw](https://github.com/) — PROCEED/REFINE/PIVOT decision node + cost guardrail
- [AI-Scientist-v2](https://github.com/SakanaAI/AI-Scientist-v2) — BFTS + run_0 baseline
- [STORM](https://github.com/stanford-oval/storm) — Perspective-Guided Question Asking + Co-STORM Mind Map
- 完整调研见 [`../references_survey.md`](../references_survey.md)

---

## 🔗 相关项目

- **设计文档 (上游)**：[`../design.md`](../design.md)
- **候选池 + 勾选状态**：[Notion 369539](https://www.notion.so/369539615a8a8081bf46d38509075d77)
- **本地 candidate menu**：[`../improvement_candidates.md`](../improvement_candidates.md)

---

## 📄 License

MIT · 2026 Litian Gong
