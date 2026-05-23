---
name: paper-slides
description: "Paper 接收后生成 10 页 slides（Beamer + PPTX），含 speaker notes。可单独跑（不跟 /paper-talk 绑定）。Use when user says \"paper slides\", \"做 slides\", \"PPT\", \"Beamer slides\", \"15 页 ppt\", \"slides only\"."
argument-hint: "[paper-dir] [--from-script <md>] [--theme metropolis|default]"
allowed-tools: Bash(*), Read, Write, Edit
---

# /paper-slides — Stand-alone Slides Generator

> 借鉴 ARIS `/paper-slides` + `/slides-polish`。

## Overview

输入 paper or script → emit 10 页 slides：

| 页 | 内容 |
|---|---|
| 1 | Title + authors + venue |
| 2 | Problem motivation (1 figure) |
| 3 | Key question / hypothesis |
| 4 | Related work positioning (1 table) |
| 5 | Method overview (1 architecture figure) |
| 6 | Method detail (formulas) |
| 7 | Experiment setup (config table) |
| 8 | Main results (1 figure) |
| 9 | Ablation / discussion |
| 10 | Conclusion + future work |

Theme：Metropolis (推荐) / default / madrid。

## Workflow

```bash
python3 tools/paper_slides.py --paper paper/ --theme metropolis --out paper/slides/
# emit Beamer .tex + compile to PDF + libreoffice convert to .pptx
```

后处理：`/slides-polish` 每页 codex review（如 polished mode）。

## Output

- `paper/slides/slides.tex` + `.pdf` + `.pptx`
- `paper/slides/speaker_notes.md`

## Composition

- 被 `/paper-talk` 调
- 单独跑（如 invited talk 不写完整 script）
