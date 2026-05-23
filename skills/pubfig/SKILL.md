---
name: pubfig
description: "Publication-ready figure + LaTeX↔Excel table 切换。NeurIPS / CoRL / ICLR 模板内置。把 /auto-viz 的 PNG 升级成投稿质量的 PDF/SVG。Use when user says \"pubfig\", \"publication figure\", \"投稿质量图\", \"latex table\", \"美化图\", \"出 PDF figure\"."
argument-hint: "[--venue NeurIPS|CoRL|ICLR] [--input figures/loss.png] [--output paper/figures/loss.pdf]"
allowed-tools: Bash(*), Read, Write
---

# /pubfig — Publication-Ready Figures + Tables

> 借鉴 claude-scholar pubfig + pubtab。

## Overview

- **Figure**：matplotlib 用 venue-specific rcParams 重画（字体 / DPI / colorbar / linewidth）→ vector PDF
- **Table**：CSV/Markdown ↔ LaTeX (booktabs)

Venue presets：

| Venue | font | DPI | column width |
|---|---|---|---|
| NeurIPS | Times New Roman | 300 | 5.5 in (single) / 3.25 in (col) |
| CoRL | Times New Roman | 300 | 6 in / 3 in |
| ICLR | Computer Modern | 300 | 5.5 in |
| Nature | Helvetica | 600 | 89 mm / 183 mm |

## Workflow

```bash
python3 tools/pubfig.py --venue $VENUE \
  --input figures/loss.png \
  --output paper/figures/loss.pdf
```

读 raw data 而非 PNG 重画（要求 figures/ 同名 `.json` data 文件由 `/auto-viz` 生成）。

## Output

- `paper/figures/*.pdf` vector
- `paper/tables/*.tex` LaTeX

## Composition

- 被 `/paper-pipeline` Stage 5 调
- 单独：「把 task_sr.png 出成 NeurIPS PDF」
