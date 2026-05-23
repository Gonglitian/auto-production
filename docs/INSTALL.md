# INSTALL.md — 安装到各 agent runtime

## 一键安装（推荐）

```bash
git clone https://github.com/<you>/auto-production.git ~/proj/auto-production-skills
cd ~/proj/auto-production-skills
./install.sh --mode both --target /path/to/your/research-project
```

`--mode`：
- `user`：装到 `~/.claude/skills/auto-production`（全 project 可用）
- `project`：装到 `<target>/.claude/skills/`（per-project，更可控）
- `both`：两个都装

## 验证

```bash
cd /path/to/your/research-project
ls .claude/skills/    # 应见 16+ 个 skill 符号链接
cat .claude/settings.json | head -5    # hooks 配置
ls .auto-production/  # bootstrap 出来的 audit/cache/...
echo $AUTO_PRODUCTION_REPO   # 应该有值，指向仓库根
```

第一次跑：

```bash
/sprint-contract --init
# 编辑 sprint_contract.yaml 填 Goal/Scope/Metric/Verify/Guard
/sprint-contract --verify
/sprint-contract --sign
/smoke-test
/research-pipeline "your topic"
```

## 各 agent runtime 适配

### Claude Code

直接装 `.claude/skills/`，`.claude/settings.json` 自动加载 hooks。已默认支持。

### Codex CLI

skills 兼容（pure markdown），但 hooks 系统不同——参考 ARIS `skills/skills-codex/` 的 mirror pattern。简单做法：把 `~/.codex/skills/` symlink 到本仓库 `skills/`。

### Cursor

- 把 `templates/CLAUDE.md` 内容拷到 `.cursorrules` 或 `.cursor/rules/`
- Skill 调用：手动 `@` 引用 `skills/<name>/SKILL.md`
- Hook 系统不可用——`/promise-check` `/stall-detect` 退化为手动

### Trae / Antigravity / Copilot CLI

参考 ARIS 的各 runtime 适配 doc（`docs/TRAE_ARIS_RUNBOOK_EN.md` 等）。本仓沿用同样 pattern：skills 直接复用，hooks 视 runtime 支持降级。

## 环境变量

| 变量 | 作用 |
|---|---|
| `AUTO_PRODUCTION_REPO` | 仓库根路径，hooks 用它定位 tools/ |
| `NOTION_TOKEN` | `/cross-host-sync` 用 |
| `AUTO_PRODUCTION_NOTION_DB` | Notion DB ID (或写 `~/.auto-production/notion.yaml`) |
| `AUTO_PRODUCTION_NOTIFY_URL` | `/sleep-research` 完成通知 webhook（可选）|
| `AUTO_PRODUCTION_VERIFY_EMAIL` | citation 验证时 polite-pool 邮箱 |

## 卸载

```bash
./install.sh --uninstall   # （未实现；手动 rm -rf 安装目录 + 删 settings.json）
```

或手动：

```bash
rm -rf ~/.claude/skills/auto-production
rm /path/to/project/.claude/skills/<all-skill-symlinks>
mv /path/to/project/.claude/settings.json.bak /path/to/project/.claude/settings.json
```
