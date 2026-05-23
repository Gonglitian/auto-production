---
name: auto-version
description: "决策为 REFINE 或 PIVOT 时，自动 snapshot stage-N_v{K}/ 目录（保留旧版本），新 run 用 3-part prompt: CONTINUATION (上次进度) + PRIOR PLAN (上次方案) + DELTA (这次改动)。Use when user says \"auto version\", \"snapshot\", \"备份旧版本\", \"v3 v4 v5\", \"version run\", \"保留旧 run\"."
argument-hint: "[--snapshot-of <dir>] [--label v6-meta]"
allowed-tools: Bash(*), Read, Write
---

# /auto-version — Snapshot on PIVOT/REFINE

> 借鉴 AutoResearchClaw `--incremental-experiment` + ARIS W3 `--pivot`。

## Overview

防 v3 / v4 / v5 / v6 在同一 checkout 互相覆盖。

REFINE/PIVOT 决策出来后自动：

```
runs/stage-1_v6_meta/ → runs/_archive/stage-1_v6_meta_<ts>/
```

并写新 run 的 prompt 模板：

```markdown
# CONTINUATION
Previous run reached SR=87% at step 35M; loss plateaued from step 28M.

# PRIOR PLAN
KL-distillation against 5 guidings, lr=4e-5, KL_weight=0.01.

# DELTA
- bump KL_weight to 0.05 (per /pivot reasoning)
- new sprint_contract.yaml signed at <hash>
```

## Workflow

```bash
TS=$(date +%y%m%d_%H%M)
SRC=${1:-runs/$(ls runs | sort | tail -1)}
DEST=runs/_archive/$(basename $SRC)_$TS
mkdir -p runs/_archive
mv $SRC $DEST
# emit 3-part prompt to next-run.md
python3 tools/auto_version.py emit-prompt --archived $DEST --label $LABEL > runs/$LABEL/PROMPT.md
```

## Output

- `runs/_archive/<old>_<ts>/`
- `runs/<new-label>/PROMPT.md`

## Composition

- `/pivot` REFINE/PIVOT 后自动调
- `/audit-driven-retrain` 每轮先调
