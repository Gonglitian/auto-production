---
name: html-homepage
description: "为当前 project 生成 / 刷新一个静态 html homepage，实时反映: 当前 stage / 最近 run metrics / 未决决策 / next action / 资源用量。Co-STORM Mind Map 风格。用户说 'homepage' / '生成主页' / 'project status html' 时调用。"
argument-hint: "[--out homepage.html] [--theme dark|light]"
allowed-tools: Bash(*), Read, Write, Glob
---

# /html-homepage — Per-project Live Status HTML

来源 = E2。

## Sections (固定 6 块)

1. **Project header** — name, branch, commit, last update
2. **Current stage** (1-9) + which gate is next
3. **Latest run** — 4 张 auto-viz PNG (来自 `/auto-viz`) + 关键 metric
4. **Pending decisions** — `findings.md` 里 status=`pending` 的 PIVOT/REFINE
5. **Cross-host status** — `EXPERIMENT_STATUS.md` 转 html 表
6. **Next action** — 从 task list 取 in_progress + 下 3 个 pending

## Workflow

### Phase 0: Gather sources

| Source | Used for |
|---|---|
| `git rev-parse --short HEAD` + `git branch --show-current` | header |
| `sprint_contract.yaml` | current stage |
| `figures/*.png` (来自 /auto-viz) | latest run section |
| `findings.md` | pending decisions |
| `EXPERIMENT_STATUS.md` | cross-host table |
| `.tasks.json` (Claude Code TaskList) | next action |

### Phase 1: Render

用 Python stdlib `string.Template`（**不**用 jinja2，K1 规则）。模板放 `templates/homepage.html.tpl`，slot 占位 `${section_X}`。

### Phase 2: Auto-refresh hook

输出末尾插 `<script>setTimeout(()=>location.reload(), 60000)</script>` 让 page 1 min 自动刷新。

### Phase 3: Notify

输出 file:// URL 让 user 浏览器打开。如果有 `feishu` / `slack` MCP 集成，可推送。

## Output

`homepage.html`（单文件，无外链 CSS/JS 依赖）。

## Failure modes

- 缺 figures/ → 显示 "no auto-viz yet, run /auto-viz first" placeholder
- 缺 findings.md → 该 section 隐藏
- 缺 git → header 显示 "(not a git repo)"

## See also

- [`/auto-viz`](../auto-viz/SKILL.md) — 输入数据源
- [`/cross-host-sync`](../cross-host-sync/SKILL.md) — 提供 EXPERIMENT_STATUS.md
- [`templates/homepage.html.tpl`](../../templates/homepage.html.tpl)
