# CLAUDE.md — project context for agent

> 这是给 Claude Code / Codex / Cursor 自动读的项目级 prompt 增强。
> auto-production 框架的 default CLAUDE.md 模板。

## Project layout (auto-production conventions)

- `sprint_contract.yaml` — Karpathy 5-tuple，每实验入口必填
- `promise.json` — agent 承诺账本（PostToolUse hook 自动维护）
- `findings.md` — 每次 `/pivot` 决策追加一段
- `homepage.html` — `/html-homepage` 自动生成
- `figures/` — `/auto-viz` 自动出图
- `.auto-production/` — 私有 state（gitignored）
  - `audit/` — gate pass trace（VLA / smoke / contract / cite）
  - `baseline/` — `/run-zero` 锁定的 baseline metric
  - `cache/citations/` — citation 验证 30-day cache
  - `meta_opt/` — failure log + patch proposal

## Output format — MANDATORY

任何 user-facing report 必须用 `/conclusion-first` 5-段：

1. **Conclusion** — 一句话
2. **What I changed** — file:line 列出
3. **What I checked** — 验证记录
4. **Risks** — 已知未解决（即使「No known risks」也要写）
5. **Next step** — 下一步动作或问 user

## Always-on behaviors

- **Promise check**：你说 "我会..." → PostToolUse hook 自动登记 `promise.json`，N 步后没做会被 ping
- **Stall detect**：长任务时 `/stall-detect` 后台跑，>15min 无 heartbeat 自动 ping
- **Smoke gate**：任何 stop 前都查 `.auto-production/audit/smoke_passed.json`，commit 不匹配拒绝 stop
- **Destructive git block**：`rm -rf`, `git reset --hard`, `git push --force`, `git clean -fdx` PreToolUse 拦截

## 9-stage workflow & 5 named gates

Stage 1 (Idea) → **NOVELTY** → Stage 2 (Code) → **METHOD** (含 VLA-audit ⭐) → Stage 3 (Data)
→ Stage 4 (Exp Design) → **RESOURCE** (5-tuple + run_0) → Stage 5 (Running)
→ Stage 6 (Result) → **RESULTS** (含 `/pivot` ⭐⭐) → Stage 7 (Doc)
→ Stage 8 (Paper) → **FINAL** (含 citation-audit + cross-review) → Stage 9 (Promotion)

详见 `docs/ARCHITECTURE.md` + `docs/GATES.md` in auto-production repo。

## Main entry skills

- `/research-pipeline "<topic>"` —— 一句话拉起全流程
- `/sleep-research "<goal>"` —— 夜间 autonomous mode
- `/status` —— 跨机器当前状态
- `/pivot` —— PROCEED/REFINE/PIVOT 决策（每 result 必跑）
- `/sprint-contract --init` —— 起新实验

## Don'ts

- ❌ 不要默认「再加点 step 试试」——用 `/pivot` 三选一
- ❌ 不要 paper 写完不跑 `/citation-audit` 就投稿
- ❌ 不要跳 gate（agent 必须看到 `.auto-production/audit/<gate>.passed` 才放行）
- ❌ 不要 user 说「yes do it」就 yes-man——先 `/double-check` 或 `/concession-threshold`
