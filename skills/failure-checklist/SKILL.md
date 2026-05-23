---
name: failure-checklist
description: "AI Research 7 大 known failure mode checklist：data snoop / distribution mismatch / leakage / weak baseline / single-seed / pre-trained sanity / implementation diff。Stage 推进前必须逐项 ✓。Use when user says \"failure checklist\", \"7 种坑\", \"data snoop\", \"leakage check\", \"sanity check\", \"before submission check\"."
argument-hint: "[--run-id <id>] [--interactive]"
allowed-tools: Bash(*), Read, Write
---

# /failure-checklist — A5 7-Mode Blocking Gate

> 借鉴 ARS Failure-Mode Checklist + design.md Part V P1 A5。

## Overview

7 项逐项确认（agent + user 联手）：

| # | Failure mode | 怎么 verify |
|---|---|---|
| 1 | **Data snoop** | eval set 没在训练中用过（grep dataset split） |
| 2 | **Distribution mismatch** | train/eval domain 一致（mean/std 列表对比） |
| 3 | **Leakage** | features 不含 label 信息（如 timestamp leak） |
| 4 | **Weak baseline** | `/run-zero` 用的是 paper 原 config（git diff configs/paper.yaml 空） |
| 5 | **Single-seed** | ≥3 seed mean ± std |
| 6 | **Pre-trained sanity** | 未 fine-tune ckpt SR < 5%（防 "其实是 zero-shot ability"） |
| 7 | **Implementation diff** | commit clean / `/vla-audit` 通过 |

## Workflow

```bash
RUN=${RUN:-$(ls runs | tail -1)}
INTERACTIVE=${INTERACTIVE:-true}

for i in 1 2 3 4 5 6 7; do
  result=$(python3 tools/failure_check.py $i --run $RUN)
  if [ "$result" != "PASS" ] && [ "$INTERACTIVE" = "true" ]; then
    AskUserQuestion "$i: $result. mark anyway? [Y/n]"
  fi
done
# all pass → touch .auto-production/audit/a5_failure_checklist.passed
```

## Output

- `.auto-production/audit/a5_failure_checklist.passed`
- `.auto-production/audit/a5_failure_report.json`

## Composition

- RESULTS gate + FINAL gate 必检
- `/pivot` 决策 PROCEED 前必跑
