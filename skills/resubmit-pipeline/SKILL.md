---
name: resubmit-pipeline
description: "Workflow 5: text-only resubmit across venues。port 已 polish paper 到新 venue (no new experiments / no bib edits / no framework changes)。5 阶段：物理隔离 → 5-layer 匿名性 → audits (--soft-only) → microedits → adversarial gate → final compile。Use when user says \"resubmit\", \"换 venue\", \"投另一个会\", \"重新投稿\", \"port to ICLR\", \"text-only resubmit\"."
argument-hint: "[source-paper-dir] [--from-venue NeurIPS] [--to-venue ICLR]"
allowed-tools: Bash(*), Read, Write, Edit, Skill
---

# /resubmit-pipeline — Cross-Venue Resubmit

> 借鉴 ARIS `/resubmit-pipeline`。

## Overview

```
phase 0: clone paper/ → paper-${to_venue}/  (物理隔离)
phase 1: 5-layer anonymity check (作者名 / acknowledgments / github URL / etc.)
phase 2: audits 全跑 --soft-only (bib 冻结)
phase 3: microedits via /auto-paper-improvement-loop --edit-whitelist (限制改动范围)
phase 4: /kill-argument adversarial gate
phase 5: final compile + /overleaf-sync push
```

Forbidden moves：`new_cite` / `new_theorem_env` / `numerical_claim` / `framework_change`。

## Workflow

```bash
SRC=${1?need source paper dir}
TO=${TO_VENUE:?need --to-venue}
NEW=paper-$TO
cp -r $SRC $NEW
# subsequent phases...
```

## Output

- `paper-<to_venue>/` 完整独立 dir
- `paper-<to_venue>/RESUBMIT_REPORT.json` 7-verdict ledger

## Composition

- 联动 `/citation-audit --soft-only`（text-rewrite 而非 bib edit）
- 联动 `/kill-argument`
- 不影响 source paper（物理隔离）
