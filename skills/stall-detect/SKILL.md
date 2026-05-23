---
name: stall-detect
description: "agent 超 N 分钟无 stdout 进展（既不 tool call 也不输出），自动 ping user / abort / 触发 /meta-optimize 自检。夜间 autonomous 模式必备——没这个醒来发现 agent 卡死 3 小时。Use when user says \"stall detect\", \"卡死\", \"agent 没动\", \"watchdog\", \"心跳\", or runs as background watcher during /sleep-research."
argument-hint: "[--watch <pid-or-session>] [--timeout 600] [--action ping|abort|meta]"
allowed-tools: Bash(*), Read, Write
---

# /stall-detect — Stall Watchdog

> 借鉴 claude-research 9-hook。横切机制 Part I §3 C2。

## Overview

后台 watcher 监控 agent process / claude session：

- 监 stdout file 的 mtime
- 监 `.auto-production/heartbeat` 文件 mtime
- 超 `TIMEOUT_S` 无变化 → 触发 `ACTION`

## When to Use

- `/sleep-research` 启动时自动起 watcher
- 长 training 跑时手动起
- pipeline 多 sub-agent 时

## Constants

- **TIMEOUT_S** = `600`（10 分钟无 stdout/heartbeat）
- **CHECK_INTERVAL_S** = `30`
- **ACTIONS** = `ping` (default), `abort`, `meta`（trigger `/meta-optimize`）
- **HEARTBEAT_FILE** = `.auto-production/heartbeat`

## Workflow

### Phase 0 — start watcher

```bash
TIMEOUT=${TIMEOUT_S:-600}
ACTION=${ACTION:-ping}
TARGET_PID=${PID:-$(pgrep -f "claude.*--session" | head -1)}

# 起后台 watcher，写自己的 pid 到 .auto-production/stall_watcher.pid
nohup bash tools/stall_watch.sh $TARGET_PID $TIMEOUT $ACTION \
  > .auto-production/stall_watch.log 2>&1 &
echo $! > .auto-production/stall_watcher.pid
```

### Phase 1 — heartbeat loop（agent 端）

agent 每次 tool call 前 / 完成段任务后写 heartbeat：

```bash
echo "$(date -Iseconds) $TURN" > .auto-production/heartbeat
```

可注册成 PreToolUse hook 自动化。

### Phase 2 — watcher 检测

```bash
# tools/stall_watch.sh
PID=$1; TIMEOUT=$2; ACTION=$3
while kill -0 $PID 2>/dev/null; do
  HB=$(stat -c %Y .auto-production/heartbeat 2>/dev/null || echo 0)
  NOW=$(date +%s)
  if [ $((NOW - HB)) -gt $TIMEOUT ]; then
    case $ACTION in
      ping)  python3 tools/notify.py "⚠️ Agent stall: no progress for ${TIMEOUT}s" ;;
      abort) kill -INT $PID; sleep 5; kill -KILL $PID 2>/dev/null ;;
      meta)  echo "STALL_AT $(date -Iseconds)" >> .auto-production/meta_opt/signals.jsonl ;;
    esac
    break
  fi
  sleep $CHECK_INTERVAL_S
done
```

### Phase 3 — stop watcher

```bash
# /stall-detect --stop
kill $(cat .auto-production/stall_watcher.pid) 2>/dev/null
rm -f .auto-production/stall_watcher.pid
```

`/sleep-research` 结束自动停。

## Output

- `.auto-production/stall_watcher.pid`（watcher 自己的 pid）
- `.auto-production/stall_watch.log`（trigger 历史）
- 视 ACTION：通知 / kill / append meta-opt signal

## Failure modes

| 现象 | 处理 |
|---|---|
| target pid 不存在 | watcher 立即 exit |
| heartbeat 文件不存在 | 当 0，等第一次心跳 |
| watcher 自己挂了 | `/sleep-research` 启动时跑 `/stall-detect --health` 重启 |
| 假阳性（agent 真在思考长时间）| 调大 TIMEOUT 到 1800s；或 agent 调用 think 工具时写一次 heartbeat |

## Composition

- `/sleep-research` 启动时自动起
- `/promise-check` reminder 触发时一起触发
- hook `hooks/pre_session_sync.sh` 启动检查 watcher 是否在
