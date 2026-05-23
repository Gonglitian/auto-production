---
name: tree-viz
description: "把所有 v1/v2/v3/v6 run 画成树状图（含 branch 关系），每个分支 metric 一目了然，hover 看 hyperparam diff。替代爬不同 wandb run 人脑对比。Use when user says \"tree viz\", \"run 树\", \"对比 runs\", \"v1 v2 v3 v6 关系\", \"branch tree\", \"看祖宗\"."
argument-hint: "[--output runs/_archive/tree.html]"
allowed-tools: Bash(*), Read, Write
---

# /tree-viz — Unified Run Tree Visualizer

> 借鉴 AI-Scientist-v2 BFTS tree viz。

## Overview

读 `runs/_archive/*/PROMPT.md` 的 `# DELTA` 段定 parent-child 关系，emit HTML：

```
v1 ─┬─ v2 (delta: lr 5e-5 → 4e-5)
    └─ v3 (delta: bs 4096 → 8192)
            └─ v4 (delta: KL 0 → 0.01)
                    ├─ v5 (delta: env-fidelity patches)
                    └─ v6 (delta: 40M per guiding)
```

每节点：metric mean / commit / wall-clock / status (DONE/FAIL)。

## Workflow

1. Walk `runs/_archive/`
2. Parse `PROMPT.md` 的 DELTA → 算 parent
3. emit SVG tree（用 graphviz 如有，否则 ASCII）
4. wrap HTML + hover tooltip 显 hyperparam diff

## Output

- `runs/_archive/tree.html`
- 嵌入 `/html-homepage` 的 figures 区

## Composition

- `/auto-version` 每次后自动 trigger
- `/pivot` 决策前可看 tree 帮断
