---
name: gate
description: "Meta-gate-check skill：给定 gate 名 (NOVELTY / METHOD / RESOURCE / RESULTS / FINAL)，自动跑 checklist 检查，全 ✓ 才放行。代替 ad-hoc agent 自己判 \"我觉得过了\"。Use when user says \"gate check\", \"过 gate\", \"check NOVELTY\", \"check METHOD\", \"check RESULTS\", \"过 FINAL\", \"can I proceed\"."
argument-hint: "--name NOVELTY|METHOD|RESOURCE|RESULTS|FINAL"
allowed-tools: Bash(*), Read
---

# /gate — Named Stage Gate Auto-Check

> 借鉴 ARS Stage 2.5/4.5 integrity gate pattern + design.md Part III §A2。

## Overview

5 named gate auto-checker，逐项跑 `docs/GATES.md` 定义的 checklist：

| Gate | Stage transition |
|---|---|
| NOVELTY | 1 → 2 |
| METHOD | 2 → 4 |
| RESOURCE | 4 → 5 |
| RESULTS | 6 → 7 |
| FINAL | 8 → 9 |

任何 item 失败 → exit 1 + 列 missing。

## Workflow

```bash
NAME=${1?need --name}
case $NAME in
  NOVELTY)
    [ -s idea-stage/proposal.md ] \
      && [ -s idea-stage/novelty.json ] \
      && [ -s idea-stage/persona_questions.md ] \
      || { echo "❌ NOVELTY: missing"; exit 1; } ;;
  METHOD)
    HEAD=$(git rev-parse --short HEAD)
    [ "$HEAD" = "$(cat .auto-production/audit/vla_audit.passed 2>/dev/null)" ] \
      || { echo "❌ METHOD: VLA-audit not for current commit"; exit 1; } ;;
  RESOURCE)
    bash $AUTO_PRODUCTION_REPO/tools/gate_resource.sh ;;
  RESULTS)
    bash $AUTO_PRODUCTION_REPO/tools/gate_results.sh ;;
  FINAL)
    bash $AUTO_PRODUCTION_REPO/tools/gate_final.sh ;;
esac
```

## Composition

- `/research-pipeline` 每 stage 末调
- 失败 → block transition，回上 stage 修
