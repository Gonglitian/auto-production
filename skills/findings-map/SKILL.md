---
name: findings-map
description: "所有 findings 一个 dict + 一个可视化 graph（谁影响谁，主线 vs 支线）。替代 findings.md 纯线性 append。Use when user says \"findings map\", \"研究地图\", \"finding graph\", \"主线支线\", \"insight network\", \"知识图\"."
argument-hint: "[--render | --add 'finding text' --depends-on id1,id2]"
allowed-tools: Bash(*), Read, Write
---

# /findings-map — Findings Memory + Research Map

> 借鉴 DeepScientist。

## Overview

`findings.yaml` 结构化版（替代 `findings.md` 平铺）：

```yaml
- id: f042
  date: 2026-05-23
  text: "KL_weight=0.01 太低，gradient signal 几乎为 0"
  source_run: v6-meta-distill
  evidence: ".auto-production/audit/v6_grad_norm.json"
  depends_on: [f038, f041]
  type: hypothesis | observation | conclusion
  status: open | confirmed | refuted
```

`--render` → SVG graph，节点按 type 上色，边按 depends_on 连。

## Workflow

`--add`：append 一条 entry
`--render`：emit `findings_map.svg` + embed homepage.html
`--query`：grep type/status

## Output

- `findings.yaml`（结构化）
- `findings_map.svg`
- legacy `findings.md` (auto-generated tail，向后兼容)

## Composition

- `/pivot` 决策完 `--add` 一条 conclusion entry
- `/html-homepage` 嵌 SVG
- `/meta-optimize` 周末读 graph 找未闭环 hypothesis
