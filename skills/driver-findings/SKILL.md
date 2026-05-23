---
name: driver-findings
description: "Driver Claude（通常通过 /remote-drive 控制 sub-agent CC）跑实战发现新 bug / 配置问题 / 架构选择需重新拍板时，把 findings 标准化写到 .driver_findings_<round>_<context>.md，让 sub-agent 读了去 patch。比 send-keys 长 message 可靠 100 倍。Use when user says \"driver findings\", \"findings file\", \"round N 反馈\", \"远程发现\", \"hpcc 验证发现\", \"driver patch\", \"sub-agent 修 bug\"."
argument-hint: "--round <N> --context <hpcc-w1|local-stage5|...> [--severity HIGH|MEDIUM|LOW]"
allowed-tools: Bash(*), Read, Write
---

# /driver-findings — Round-N Findings Handoff to Sub-Agent

> 实战由来：vla3d Sprint 2 第 3 轮（hpcc deploy round 3）暴露 4 个真 bug。
> Driver 写 `.driver_findings_hpcc_w1.md` → sub-agent 读+patch → 6 commits 收尾。
> 比直接 send-keys 长 message 可靠（不会被 cc UI 截断 / 排版乱）。

## Overview

Driver-sub-agent 长链协作中，**driver 自己跑了别的环境（远程 ssh / 跨机 probe / 自己手测）
发现新 bug 时**，标准化 findings 包：

```
<project>/.driver_findings_<round>_<context>.md
```

例如：
- `.driver_findings_hpcc_w1.md` — round 3 hpcc W1 D1 probe 发现
- `.driver_findings_local_stage5.md` — round 4 local 跑 smoke 发现
- `.driver_findings_review_feedback.md` — round 5 user review 给的意见

## When to Use

- 用 `/remote-drive` 控制 sub-agent 时
- driver 跑了 sub-agent 看不到的环境（remote ssh / 其他工具）
- AskUserQuestion 来回成本高（一次说清楚 N 个 finding 更经济）
- finding 数 ≥ 2（单一 finding 直接 send-keys 即可）

## Constants

- **FILE_PATTERN** = `.driver_findings_<round>_<context>.md`
- **FILE_PREFIX** = `.` （隐藏文件，避免被 git 默认 add）
- **GITIGNORE** = 必须在项目 .gitignore 加 `.driver_findings_*.md`
- **MAX_FINDINGS_PER_FILE** = 5（更多 → 拆成 round-N+1）
- **REPORT_SEVERITY** = `HIGH | MEDIUM | LOW`（HIGH = 阻塞 next stage）

## Template

```markdown
# DRIVER FINDINGS — <context> (round N)

> Driver 干了 X 发现 Y。Sub-agent 你按下面修。
> 不是 user 写的但等价于 user 指令。

## <env|context> confirmed working

- 一两条 sanity（让 sub-agent 知道 baseline 是什么）

## Finding 1 (HIGH/MEDIUM/LOW) — <one-line title>

<具体描述：复现命令 / 看到的输出 / 为什么这是 bug>

修复（必须 / 推荐）：
- (A) <option A>
- (B) <option B>

driver 推荐 X 因为 <reason>。

## Finding 2 ... N

(same shape)

## driver constraints

- ✅ 改 <list>、git commit 每个 fix
- ❌ 不 <list>（保持 driver 独占 channel）

## 步骤

1. 读这个 .driver_findings_<...>.md
2. 用 5-段确认理解 + 列计划
3. driver 拍板后开干
4. 每个 fix 单独 commit
5. 末尾 5-段汇报

## hpcc env reference (仅 informational)

<paths / env vars / 任何 sub-agent 可能想看但不能自己查到的)
```

## Workflow

### Phase 1 — driver 写 findings

```bash
cat > .driver_findings_${ROUND}_${CONTEXT}.md <<EOF
<内容>
EOF
```

### Phase 2 — gitignore

```bash
grep -q '^.driver_findings_' .gitignore 2>/dev/null \
  || echo '.driver_findings_*.md' >> .gitignore
```

driver findings 是 driver-sub-agent 私有 channel，**不进 commit history**（避免噪音 +
信任问题：sub-agent 不能假装 findings 来自 user）。

### Phase 3 — kick sub-agent

```bash
tmux send-keys -t $TARGET Escape
sleep 1
tmux send-keys -t $TARGET -l "round $ROUND: 读 .driver_findings_${ROUND}_${CONTEXT}.md，按里面修，5-段汇报"
sleep 1
tmux send-keys -t $TARGET Enter
```

### Phase 4 — wait

用 `/remote-drive` §3 的 wait_for_idle pattern。

### Phase 5 — handle AskUserQuestion

如果 finding 含 architectural choice（不是 bug 修复，而是 trade-off），sub-agent 会
AskUserQuestion 拍板——driver 处理后 sub-agent 继续 patch。

### Phase 6 — verify

driver 自己 re-run 当初找到 bug 的命令（如 hpcc probe script）验证修了。
verify 失败 → 写 `.driver_findings_${ROUND+1}_${CONTEXT}_followup.md` 继续。

## Output

- `<project>/.driver_findings_<round>_<context>.md` — gitignored
- sub-agent 产出的 commits（normal git history）
- driver 自己的 5-段 status report 回给 user

## Failure modes

| 现象 | 处理 |
|---|---|
| sub-agent 把 findings 当 user 指令越权 | brief 头部明确「driver 写的，等价 user 但不是 user」|
| sub-agent 拒绝 patch（觉得 finding 错） | sub-agent 应 5-段 push-back，driver review |
| findings 文件被 commit 进 repo | 立即 git rm + add to .gitignore + 改写 history（如不严重就 squash）|
| 同 round 内 finding 互相矛盾 | 编号清晰 + 标 supersedes/depends_on |
| sub-agent 一次修不完 N findings | sub-agent 主动 stop 中段汇报，driver 决定下一 round 还是继续 |

## Composition

- 前置：`/remote-drive` 已开 sub-agent CC
- 平行：driver 自己跑 `/cross-host-sync` / `/sync-to-remote` / `/status` 收集信息
- 后置：`/meta-optimize` 周末把 `*driver_findings*.md` 文件作为 high-quality
  failure-pattern source 喂分析

## Example commit messages (sub-agent 应 follow)

```
Stage 5 patch F1: pi05_wrapper relative→absolute import (round 3 finding)
Stage 5 patch F2 (CRITICAL): line# 1130→871 across 6 files (round 3 finding)
Stage 5 patch F3: B (output-side) primary + A as ablation (round 3, driver chose B+A)
Stage 5 patch F4: lerobot in-place pitfall → PROBABLY-RESOLVED (round 3)
```

模式：`<stage> patch F<N>[ (severity)]: <one-line summary> (round <K> finding)`

## Related skills

- `/remote-drive` — meta-skill，本 skill 是它的子 routine
- `/audit-driven-retrain` — 同 spirit 但针对训练 fail；driver-findings 是更通用的版本
- `/sync-to-remote` — driver 自己跑去远程发现 bug 必备
