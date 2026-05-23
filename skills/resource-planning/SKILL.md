---
name: resource-planning
description: "下载 ckpt / dataset 前显式列：总大小 / 目标盘剩余空间 / 估计下载时间 / 是否需要 paywall / 是否要 import cookie。User 拍板再下。防 \"下到一半盘满\"。Use when user says \"resource planning\", \"下载前\", \"估空间\", \"plan download\", \"准备下数据\", \"check disk\"."
argument-hint: "[--items url1,url2,...] [--target-dir /data/foo]"
allowed-tools: Bash(*), Read, Write, WebFetch
---

# /resource-planning — Stage 3 Pre-Download Planning

> 借鉴 AutoResearchClaw stage 11 RESOURCE_PLANNING。

## Overview

下载前一张 table：

| 项 | URL | 大小估计 | 目标 path | paywall? | 预计时长 |
|---|---|---|---|---|---|
| ckpt-A | https://... | 12 GB | /data1/ckpts/a/ | no | ~20 min |
| dataset-B | https://... | 460 GB | /data2/raw/b/ | yes (need login) | ~3 h |

加上目标盘 `df -h` 输出，AskUserQuestion: 确认下吗？

## Workflow

1. For each URL: HEAD request 取 Content-Length（如服务器给）；或正则解析页面
2. `df -h` 目标 dir 看可用
3. 求和总下载量 + 比可用，警告 if > 80%
4. emit table + AskUserQuestion

## Output

- `docs/DEPLOYMENT.md` 追加 download 计划段
- 用 `/corpus-schema` 接续登记下载来源

## Composition

前置：Stage 3 开始
后置：`/corpus-schema` 写每条 entry
