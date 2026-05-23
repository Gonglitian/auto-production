# QUICKSTART — 5 分钟上手

> 把 auto-production 装到一个真 project 上，跑一句 `/research-pipeline` 就完事。
> 全程中文。

---

## 0. 前置（30 秒）

确认你有：

- **Claude Code** CLI 装好（`claude --version` 能跑）
- **git** 在用
- 一个 Python project 目录（可以是空的；或者随便 `mkdir my-proj && cd my-proj && git init`）

可选（用到再装）：
- `NOTION_TOKEN` —— `/cross-host-sync` 同步多机用
- W&B API key —— `/auto-viz` 拉 metric 用
- MCP servers (codex / gemini) —— `/cross-review` 三家互审用

---

## 1. 装 auto-production（1 分钟）

```bash
git clone https://github.com/Gonglitian/auto-production.git ~/proj/auto-production
cd ~/proj/my-research-project        # 你的真 project
~/proj/auto-production/install.sh --mode both --target .
```

`--mode both` 同时装到：
- `~/.claude/skills/auto-production/` ← 全 project 都能用
- `<当前 project>/.claude/skills/` ← 当前 project 优先级更高（可 override）

装完会：
- 复制 `templates/CLAUDE.md` 到 project 根（agent 自动读）
- 复制 `templates/settings.json` 到 `.claude/`（注册 4 个 hook）
- `mkdir -p .auto-production/{audit,cache,meta_opt,baseline}` bootstrap state 目录
- 在你的 `~/.bashrc` 末尾加一行 `export AUTO_PRODUCTION_REPO=~/proj/auto-production`（让 hook 知道仓库在哪）

---

## 2. 第一次跑（3 分钟）

### 选 1：完整 9-stage 全流程（推荐）

打开 Claude Code 在 project 里，输入：

```
/research-pipeline "factorized gap in discrete diffusion LMs"
  — venue: NeurIPS, mode: co-pilot, budget: 14d
```

Agent 会：
1. 起 Stage 1（idea generation）—— 调 `/idea-perspective` + `/persona-probe` + `/novelty-check`
2. 跑到 NOVELTY gate 停下问你 PROCEED / REFINE / PIVOT
3. 你拍板 PROCEED → 进 Stage 2 ... 一路到 Stage 9

`mode: co-pilot` = 5 个 named gate 都问你；`mode: full-auto` = 一路不停只到 wake-on 条件触发。

### 选 2：夜间睡前模式

```
/sleep-research "训完 5 个 guidings + meta-distill，醒来给 PROCEED/REFINE/PIVOT 报告"
  — budget: 8h, wake-on: pivot|guard-fail|done
```

会自动起 `/stall-detect` watcher + heartbeat + cost cap。早上看 `wakeup_report.md`。

### 选 3：拆开手动用（debug / 学习）

```
/sprint-contract --init        # 写 5-tuple，Goal/Scope/Metric/Verify/Guard
# (编辑 sprint_contract.yaml)
/sprint-contract --verify
/sprint-contract --sign        # sha256 锁定，gate 用
/smoke-test                    # 跑极小 batch 验通路
/run-zero --seeds 3            # baseline 锁定
/vla-audit                     # train/eval pipeline 一致性
# 起正式训练
# 完了：
/auto-viz --wandb-run <id>     # 4 张图自动出
/pivot --run <id>              # PROCEED/REFINE/PIVOT 决策
```

---

## 3. 看进度 / 找东西

随时输入：

| 你想知道 | 输入 |
|---|---|
| 4 台机器现在跑啥 | `/status` |
| 最近的实验决策 | `cat decisions.jsonl \| tail -5` |
| 当前 sprint 合同 | `cat sprint_contract.yaml` |
| 所有 gate pass 状态 | `ls .auto-production/audit/` |
| Agent 答应了但没做的事 | `/promise-check --list-open` |
| Plateau 检测 | `/plateau-detect --n 3` |
| 浏览器开当前进度 | `python3 $AUTO_PRODUCTION_REPO/tools/html_homepage.py && open homepage.html` |

---

## 4. 配置高级功能（可选，按需）

### Notion 多机同步（`/cross-host-sync`）

1. Notion 建一个 database，字段：run_name (Title) / host (Select) / partition / job_id / branch / commit / start_time (Date) / wandb_url (URL) / ckpt_path / conda_env / dataset_path / status (Select) / last_metric
2. share 给你的 Notion integration，拿到 token
3. `echo "export NOTION_TOKEN=secret_xxx" >> ~/.bashrc`
4. `mkdir -p ~/.auto-production && echo "database_id: <你的 db id>" > ~/.auto-production/notion.yaml`
5. `/cross-host-sync --direction push` 试一下

### 周末自演化（`/meta-optimize`）

```bash
# crontab -e 加
0 22 * * 0 cd ~/proj/my-research-project && claude --print "/meta-optimize" >> .auto-production/meta_opt/cron.log 2>&1
```

每周日 22:00 自动复盘上周 failure log，emit patch proposal 到 `.auto-production/meta_opt/<date>/`，你周一来看。

### 跨模型互审（`/cross-review`）

需要装 codex MCP + gemini MCP。装完后任何时候：

```
/cross-review paper/ --rounds 3
```

---

## 5. 改 prompt / 加 skill

```bash
cd ~/proj/auto-production
# 加新 skill
mkdir skills/my-skill && touch skills/my-skill/SKILL.md
# 改现有 skill
$EDITOR skills/pivot-decision/SKILL.md
# 测
python3 tests/test_skill_format.py
# 提交
git commit -am "feat: ..."
```

下次 SessionStart hook 自动 `git pull` 同步全机器。

---

## 6. 常见问题

| 问题 | 解决 |
|---|---|
| `command not found: /research-pipeline` | 确认 `.claude/skills/` 有符号链接：`ls .claude/skills/auto-production/skills/` |
| `AUTO_PRODUCTION_REPO not set` | `source ~/.bashrc` 或新开 terminal |
| `/vla-audit failed` 但你确信 train/eval 一致 | 给 project 写 `.auto-production/tools/vla_audit_loader.py` 自定 6 维度抽取（参考 `tools/vla_audit.py` 接口） |
| Stage 8 paper helper 跑出错 | `pubfig.py / paper_slides.py / poster_gen.py` 需要 matplotlib + LaTeX，按 `pip install matplotlib` 和 `apt install texlive-latex-extra` 装 |
| hook 没起作用 | `cat .claude/settings.json` 看 hooks 段是否在；`echo $AUTO_PRODUCTION_REPO` 看是否非空 |

---

## 7. 全 skill 速查

完整 54 个 skill 列表见 [`../README.md`](../README.md#🗂️-skill-目录速查) 或 [`ARCHITECTURE.md`](ARCHITECTURE.md)。

最常用 9 个：

```
/research-pipeline    # 主入口
/sleep-research       # 夜间 wrapper
/status               # 跨机现状
/sprint-contract      # 5-tuple
/smoke-test           # 起正式前必跑
/vla-audit            # METHOD gate 必跑
/auto-viz             # 出图
/pivot                # PROCEED/REFINE/PIVOT
/citation-audit       # paper 投前必跑
```

5-tuple 模板长这样（`templates/sprint_contract.yaml`）：

```yaml
goal: "验证 KL-distillation 比 hard-target supervision 收敛快"
scope: "不调 LR schedule，不换 backbone"
metric: "wall-clock to 80% SR on MC10, 5-seed mean"
verify: "5 seed bootstrap CI 不与 baseline CI 重叠"
guard: "若 SR<60% 或 loss 30 步不降，trigger PIVOT"
```

填好它 → `/smoke-test` → `/run-zero` → 起训 → `/pivot`。整套就这样。

---

🎉 玩得开心。有 bug 或建议提 issue。
