# Contributing to Auto-Production

## 加新 skill 的 5 步

1. `mkdir skills/<your-skill>/` + `touch skills/<your-skill>/SKILL.md`
2. 顶部必须有 frontmatter（YAML，3-dash 围起来）：

   ```yaml
   ---
   name: your-skill
   description: "一句话什么时候用——必须含触发关键词（中英文）。"
   argument-hint: "[arg1] [--flag]"
   allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, Agent
   ---
   ```

3. body 至少包含：
   - `## Overview`
   - `## When to Use This Skill`
   - `## Workflow`（Phase 0 / 1 / 2 ...）
   - `## Output`
   - `## Failure modes`

4. 任何 helper 脚本放 `tools/`，纯 Python 标准库 + bash。**不允许** pip install。
5. 跑 `python tests/test_skill_format.py` 验证 frontmatter / 链接完整性。

## 加新 hook

放 `hooks/<name>.sh`，bash 写。注册到 `templates/settings.json` 的 `hooks` 段。

## Commit message

`feat(skill): add /your-skill — one-line` 或 `fix(hook): ...` 或 `docs: ...`。

## 改 design

design.md 是上游设计文档（在仓库**外** `../design.md`）。改 design 前先在 Notion 候选池 [369539](https://www.notion.so/369539615a8a8081bf46d38509075d77) 加候选 → 走勾选流程 → 才能改 design.md。
