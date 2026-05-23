---
name: task-notes-yaml
description: "Phase 入口给 agent 一份 YAML: compute_budget / dataset_loader_code / eval_rules / deadline。Agent 必须读完才能动。固化资源分配。Use when user says \"task notes\", \"phase yaml\", \"资源声明\", \"agent 前置读\", \"compute budget\"."
argument-hint: "[--init | --verify]"
allowed-tools: Read, Write
---

# /task-notes-yaml — Per-Phase Task Notes

> 借鉴 AgentLaboratory phase YAML。RESOURCE gate 软前置。

## Overview

填 `task_notes.yaml`：

```yaml
phase: training
compute_budget:
  gpu_count: 4
  gpu_type: rtx-pro-6000
  wall_clock_hours: 48
  partition: raise@hpcc
dataset_loader_code: src/data/loader.py:CrowdFollowLoader
eval_rules:
  primary_metric: success_rate_mc10
  seeds: [41,43,47,53,59]
  baseline_run: .auto-production/baseline/run_zero_hpcc_5a3f.json
deadline: 2026-05-30T23:59:59+08:00
forbidden_moves:
  - change LR schedule
  - swap backbone
```

Agent 起任何 train.py 前必须 grep 该文件并 echo 读到的字段，否则 RESOURCE gate fail。

## Workflow

`--init`：从 templates/task_notes.yaml 拷一份
`--verify`：检查字段齐 + deadline 在未来

## Composition

前置：`/sprint-contract` 已签
后置：RESOURCE gate 检查 task_notes.yaml 存在
