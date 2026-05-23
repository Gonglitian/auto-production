---
name: remote-drive
description: "用一个 Claude (driver) 通过 tmux 远程控制另一个 Claude Code session (sub-agent CC) 走完 pipeline。把 sub-agent 当 worker 用：driver brief 任务 → send-keys 输入 → capture-pane 监听 → 处理 AskUserQuestion → 等下次 idle。Use when user says \"remote drive\", \"驱动另一个 cc\", \"sub-agent cc\", \"控制别的 claude\", \"tmux drive\", \"我已经开了 cc 你来控制\"."
argument-hint: "[--target tmux-session:window] [--brief brief.md]"
allowed-tools: Bash(*), Read, Write
---

# /remote-drive — 远程驱动一个 tmux 里的 sub-agent CC

> 实战经验：driver Claude 控制 vla3d project 里另一个 Claude Code，走完 Stage 1-4。
> 完整 transcript 在 [Auto-Production GitHub PR/issue history](https://github.com/Gonglitian/auto-production)。

## Overview

driver 通过 4 个 tmux 原子操作完成全程：

| 操作 | 何用 |
|---|---|
| `tmux capture-pane -p -t <target> -S -<N>` | 读 sub-agent 当前屏（含 askuser UI） |
| `tmux send-keys -t <target> "text" Enter` | 发消息 |
| `tmux send-keys -t <target> Escape` | 清 input 框（sub-agent 自动 suggest 文本不会真 submit） |
| `tmux send-keys -t <target> Enter` | 在 AskUserQuestion UI 里 select 当前 highlight option |

## When to Use

- 一个 Claude 跑长任务，另一个 driver Claude 盯着它（dual-monitor 模式）
- 测一个 skill bundle，driver 验完整路径而 sub-agent 实际执行
- 夜间 wrapper：driver = ScheduleWakeup poller，sub-agent = autonomous loop
- 多 sub-agent 编排（driver 控 N 个 cc 窗口分头跑实验）

## Critical patterns (实战发现)

### 1. CC UI 假"pending input"陷阱 ⚠️

Sub-agent 写完一段后**自动在 input 框 suggest 下一动作的文字**（如「进 Stage 2」「直接进 Stage 3」「等 datalake 完成再继续」）。看起来像 pending 输入但**按 Enter 不会 submit**。
**正确做法**：先 `Escape` 清 input，再 `send-keys "your message" Enter`。

```bash
tmux send-keys -t research:vla3d Escape
sleep 1
tmux send-keys -t research:vla3d "go Stage 5" Enter
```

### 2. AskUserQuestion UI 导航

Sub-agent 弹 multi-choice 时屏幕显示：
```
❯ 1. PROCEED ...
  2. REFINE ...
  3. PIVOT ...

Enter to select · Tab/Arrow keys to navigate · Esc to cancel
```

- 直接 `Enter` = 选当前 `❯` 高亮的（默认 option 1）
- 选别的：`Tab`（下） / `BSpace` 或 `Up` （上）N 次再 Enter
- multi-choice 后会再问「Submit answers?」，再发一次 Enter 才真提交

### 3. Wait-for-idle 检测

不要 `sleep 30` 后盲读——sub-agent 可能还在思考或刚开始新工具调用。用 polling：

```bash
# idle = pane content 不变 AND 末尾有 "^❯ $" 空 prompt AND 无 busy marker
prev=""; stable=0
while true; do
  pane=$(tmux capture-pane -p -t $TARGET)
  h=$(echo "$pane" | md5sum | awk '{print $1}')
  busy=$(echo "$pane" | tail -10 | grep -cE \
    "Jitterbugging|Twisting|Blanching|Churned|Spawning|Editing|Reading|Searching|esc to interrupt|✶|✻|Submit answers")
  empty=$(echo "$pane" | tail -8 | grep -c "^❯ *$")
  if [ "$h" = "$prev" ] && [ "$busy" -eq 0 ] && [ "$empty" -ge 1 ]; then
    stable=$((stable+1))
    [ $stable -ge 5 ] && { echo IDLE; break; }
  else
    stable=0; prev="$h"
  fi
  sleep 3
done
```

跑成 background task（`run_in_background: true`），不阻塞 driver 处理别的事。

### 4. 长 brief 用文件而非 send-keys

>200 字符的 brief 直接 send-keys 经常被 cc 截断或排版乱。**改成写文件**：

```bash
cat > .driver_brief.md <<EOF
# Brief for sub-agent
... 详细任务 ...
EOF
tmux send-keys -t $TARGET "读 .driver_brief.md 然后按里面要求走" Enter
```

### 5. 报告频率契约

Brief 里**强制要求** sub-agent 每段大动作 + stage 末尾用 `/conclusion-first` 5-段格式汇报，driver 读 capture-pane 拿摘要。否则 driver 要爬全屏 N 段才能拼出来。

## Workflow

### Phase 0 — pre-flight

```bash
# 验证 target tmux window 存在 & cc 在 prompt
tmux list-windows -t <session> | grep -q $WINDOW || exit 1
tmux capture-pane -p -t $TARGET | tail -8 | grep -q "^❯" || exit 1
```

### Phase 1 — 写 brief

把任务、约束、报告契约写进 `<project>/.driver_brief.md`。必含：

- 你是 sub-agent 角色定位
- 工作目录 + 已就绪的前置
- 目标任务（数字化、可验收）
- 约束（什么能做、什么不能）
- **报告频率** + 5-段格式要求
- 第一步立刻执行什么

### Phase 2 — kick off

```bash
tmux send-keys -t $TARGET "读 .driver_brief.md 然后按里面要求走" Enter
```

### Phase 3 — drive loop

```
loop:
  wait_for_idle (background)
  capture pane to see latest output
  if AskUserQuestion detected:
    decide option N
    send Enter (or Tab×N then Enter)
    submit confirmation Enter
  elif report 5-段 detected and task incomplete:
    Escape; send next-step prompt; Enter
  elif task complete (sub-agent says STOP or final report):
    break
```

### Phase 4 — handoff

Sub-agent 末尾汇报后：

- driver commit sub-agent 产物
- driver 写自己的 5-段汇报回给 user
- 可选：sub-agent 继续 standby 等 user 下一轮 brief

## Constants

- **CAPTURE_LINES** = `300`（足够看到 1-2 个 AskUserQuestion + 上下文）
- **IDLE_STABLE_SEC** = `15`（5 次 3-秒 stable 才算 idle，防 cc 工具调用间隙误判）
- **MAX_TURN_TIME** = `15min`（单个 turn 超时 → driver 介入 ping 一下「你还在吗」）

## Output

driver 产物：
- `<project>/.driver_brief.md` — 任务 brief
- `<project>/.driver_log.md` —（可选）driver 每次 send-keys + capture 的 timestamp log

## Failure modes

| 现象 | 处理 |
|---|---|
| send-keys 后 sub-agent 无响应 | 再发一次 Enter；或 Escape + 重新 type |
| sub-agent UI 假 pending input | Escape 清，重 type |
| sub-agent 卡在 spinner > 15min | tmux send-keys C-c 中断，重新 brief |
| AskUserQuestion 弹了 nested 2 个 question | 一个一个 Enter 答完，最后 submit |
| sub-agent 把 driver 当 user 反问 | driver 答案要简洁，跟 brief 风格一致 |
| pane 滚动出去看不到 history | `capture-pane -S -<N>` 拉更多行 |
| sub-agent 调 `/clear` 把 brief 丢了 | driver 立即 send-keys 重读 .driver_brief.md |

## Composition

- 跟 `/sleep-research` 互补：sleep-research = 自己 wrap 自己；remote-drive = 别人 wrap 你
- 跟 `/spawn-task` 区别：spawn-task = fork 一个 Agent sub-agent in-process；remote-drive = 跨 process / 跨 session 控制独立的 CC instance
- 跟 `/cross-host-sync` 联动：driver 调 cross-host-sync 知道 sub-agent 跑在哪台机器
- 跟 `/meta-optimize` 联动：driver-sub-agent 协作日志是 self-evolution 高质量数据

## Example session

```bash
# driver 这边
tmux new-window -t research -n sub-cc -c /path/to/project
tmux send-keys -t research:sub-cc "claude" Enter
sleep 10  # 等 cc 启动

cat > /path/to/project/.driver_brief.md <<EOF
你是 sub-agent。任务：跑通 /research-pipeline Stage 1-4，STOP 在 Stage 5。
报告：每 stage 末 5-段格式。
第一步：cat RESEARCH_BRIEF.md，告诉我你计划的 skill 调用顺序。
EOF
tmux send-keys -t research:sub-cc "读 .driver_brief.md 按要求走" Enter

# 后台 watcher
nohup bash -c 'while ...; do ...; done' &

# loop: wait → capture → decide → send
while true; do
  wait_for_idle
  pane=$(tmux capture-pane -p -t research:sub-cc -S -300)
  if echo "$pane" | grep -q "Enter to select"; then
    tmux send-keys -t research:sub-cc Enter  # accept default
  elif echo "$pane" | grep -q "STOP"; then
    break
  else
    tmux send-keys -t research:sub-cc Escape
    tmux send-keys -t research:sub-cc "继续下一阶段" Enter
  fi
done
```

完整实战见 `auto-production` repo 的 vla3d test session（commit `10459f1`）。
