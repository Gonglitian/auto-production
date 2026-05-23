---
name: datalake
description: "针对机器人 / VLA 领域建一个 datalake：数据集元数据 + 常用 API + 行话词典 + 已知坑。Biomni 模板。下次同领域 project 直接复用。Use when user says \"datalake\", \"know-how\", \"领域词典\", \"常用 dataset 库\", \"domain library\", \"avoid known pitfalls\"."
argument-hint: "[--domain robotics|nlp|cv] [--query 'foo']"
allowed-tools: Bash(*), Read, Write, Grep
---

# /datalake — Domain Datalake + Know-How Library

> 借鉴 Biomni (Stanford biomedical agent)。

## Overview

`datalake/<domain>/` 存：

```
datalake/robotics/
├── datasets.yaml       # LIBERO/RoboMimic/Bridge/... 元数据
├── apis.md             # OFT/π0/GR00T 常用 API 速查
├── glossary.md         # SR / EEF / TCP / waypoint / ... 词典
├── known_pitfalls.md   # 8-bit vs bf16 chunk, action norm 等坑
└── ref_papers.yaml     # 必读 papers
```

可被任何 skill grep 当词典用。

## Workflow

`--query 'foo'`：grep 整个 datalake 出现 foo 的段
`--add domain robotics --topic pitfall --content '...'`：写一段进 known_pitfalls.md
`--export`：打包成 tarball

## Composition

- Stage 1 `/idea-perspective` 起步时先 query datalake 看有无现成
- Stage 6 `/pivot` 新发现的坑 append to known_pitfalls.md
- `/meta-optimize` 周末把 patterns 提炼成新 entry
