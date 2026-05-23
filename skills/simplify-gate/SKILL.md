---
name: simplify-gate
description: "任何单文件超 400 行触发提醒，超 800 行强制 refactor 才能继续。防代码膨胀失控。Use when user says \"simplify gate\", \"文件太大\", \"line limit\", \"refactor 提醒\", \"代码膨胀\"."
argument-hint: "[--scan src/] [--soft-limit 400] [--hard-limit 800]"
allowed-tools: Bash(*), Read, Glob
---

# /simplify-gate — File-Size Bloat Gate

> 借鉴 autoresearch。

## Overview

扫描所有 source 文件行数，若：

- `≥ soft-limit (400)` → emit warn，建议 refactor
- `≥ hard-limit (800)` → exit 1，强制 refactor 才允许 commit / Edit

可作 pre-commit hook 用。

## Workflow

```bash
SOFT=${SOFT:-400}; HARD=${HARD:-800}
WARN=0; FAIL=0
for f in $(git ls-files '*.py' '*.ts' '*.tsx' '*.go' '*.rs' 2>/dev/null); do
  N=$(wc -l < "$f")
  if [ $N -ge $HARD ]; then
    echo "❌ $f: $N lines (≥ $HARD)"; FAIL=1
  elif [ $N -ge $SOFT ]; then
    echo "⚠️  $f: $N lines (≥ $SOFT, consider split)"; WARN=$((WARN+1))
  fi
done
exit $FAIL
```

## Output

- stdout: warn + fail list
- exit 0 (clean) / 1 (any hard-limit fail)

## Composition

- 可注册成 PreCommit hook
- `/arch-plan` 大改动前调
