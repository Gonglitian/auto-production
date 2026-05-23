---
name: paper-poster
description: "Paper 接收后生成 3'×4' A0 海报 PDF + editable PPTX + SVG。venue-specific 布局模板。Use when user says \"paper poster\", \"做 poster\", \"海报\", \"A0 poster\", \"会议海报\"."
argument-hint: "[paper-dir] [--size A0|A1] [--orientation portrait|landscape]"
allowed-tools: Bash(*), Read, Write, Edit, Agent
---

# /paper-poster — Conference Poster Pipeline

> 借鉴 ARIS `/paper-poster`。

## Overview

3 产物：

1. `paper/poster/poster.pdf` (A0 默认)
2. `paper/poster/poster.pptx` (editable)
3. `paper/poster/poster.svg` (source)

布局模板：5-section (problem / method / setup / results / discussion + bibtex 角落)，含 abstract block。

## Workflow

```bash
SIZE=${1:-A0}
ORIENT=${2:-portrait}
# 用 LaTeX beamerposter 或 tikz
python3 tools/poster_gen.py --paper paper/ --size $SIZE --orient $ORIENT
```

依赖 `/pubfig` 把 figures 转 vector PDF 嵌进 poster。

## Output

- `paper/poster/*`

## Composition

- 跟 `/paper-talk` + `/paper-slides` 同期跑
- 引用 `/pubfig` 出的 PDF
