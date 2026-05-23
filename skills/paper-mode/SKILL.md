---
name: paper-mode
description: "10-mode academic-paper writing skill：intro / related-work / method / experiment / discussion / abstract / conclusion / appendix / reviewer-defense / one-pager。一个 skill 多模式切换。Use when user says \"paper mode\", \"写 intro\", \"写 method\", \"写 abstract\", \"写 related work\", \"写 conclusion\", \"academic paper section\"."
argument-hint: "--mode intro|related-work|method|experiment|discussion|abstract|conclusion|appendix|reviewer-defense|one-pager [--venue NeurIPS]"
allowed-tools: Read, Write, Edit, Agent, WebSearch
---

# /paper-mode — 10-Mode Academic Paper Writer

> 借鉴 ARS `academic-paper` 10-mode skill。

## Overview

每 mode 一个 prompt + style guide：

| Mode | 输入 | 输出 |
|---|---|---|
| `outline` | proposal + results | `paper/OUTLINE.md`（每 section 一句）|
| `intro` | outline + key story | `paper/sections/intro.tex` |
| `related-work` | survey + novelty.json | `paper/sections/related.tex` |
| `method` | code + figures spec | `paper/sections/method.tex` |
| `experiment` | results + figures | `paper/sections/experiment.tex` |
| `discussion` | findings.yaml | `paper/sections/discussion.tex` |
| `abstract` | full draft | `paper/abstract.tex`（顶会风格 4-段）|
| `conclusion` | discussion + future work | `paper/sections/conclusion.tex` |
| `appendix` | extra ablations | `paper/sections/appendix.tex` |
| `reviewer-defense` | reviewer concerns | `paper/sections/reviewer_defense.tex`（rebuttal 内嵌）|
| `one-pager` | abstract + intro | `paper/onepager.md`（社交媒体用）|

每 mode 有 venue-specific style：NeurIPS / ICLR / CVPR / ACL / Nature 等。

## Workflow

```bash
MODE=${1?need --mode}
VENUE=${VENUE:-NeurIPS}
python3 tools/paper_mode.py emit-prompt --mode $MODE --venue $VENUE > /tmp/prompt.md
# Agent reads prompt + project state, writes output file
```

## Composition

- 被 `/paper-pipeline` 按 stage 调
- 单独跑：「重写一下 intro」→ `/paper-mode --mode intro`
