---
name: paper-talk
description: "Paper 接收后一行命令生成 12-min talk script + Beamer slides + speaker notes + Q&A prep。Use when user says \"paper talk\", \"做 talk\", \"会议 talk\", \"演讲稿\", \"presentation\", \"我要做 oral\"."
argument-hint: "[paper-dir] [--duration 12min] [--audience domain|general]"
allowed-tools: Bash(*), Read, Write, Edit, Agent, Skill
---

# /paper-talk — Conference Talk Pipeline

> 借鉴 ARIS `/paper-talk`。Stage 9 post-acceptance。

## Overview

4 产物：

1. `paper/talk/script.md` — 完整逐字稿，按 slide 切段
2. `paper/talk/slides.pdf` (Beamer) + `.pptx`
3. `paper/talk/speaker_notes.md` — 关键点 / 强调 / 节奏
4. `paper/talk/qa_prep.md` — 预测 reviewer 风格 questions + 答案

## Workflow

```bash
DUR=${1:-12min}
# 1. read paper/, extract narrative arc
Skill(/spawn-task --type research --task "extract 5-slide narrative arc from paper/")
# 2. emit script段, ~150 words per minute
# 3. /paper-slides 子调 Beamer
Skill(/paper-slides --from-script paper/talk/script.md --venue $VENUE)
# 4. Q&A from /persona-probe 8 personas (reviewer + cross-domain)
```

## Output

- `paper/talk/*`（4 file）

## Composition

- 调 `/paper-slides`
- 引用 `/persona-probe` 问题做 Q&A 准备
