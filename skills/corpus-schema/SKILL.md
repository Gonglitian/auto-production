---
name: corpus-schema
description: "每个下载的 ckpt / dataset / paper 记录 obtained_via (URL/script) + obtained_at (timestamp) + sha256 + license + 来源 paper。重现 run 时知道每个 dependency 精确版本。Use when user says \"corpus schema\", \"登记下载\", \"literature corpus\", \"sha256\", \"download manifest\", \"reproducibility\"."
argument-hint: "[--add <path> --url <url>] [--list] [--verify]"
allowed-tools: Bash(*), Read, Write
---

# /corpus-schema — Literature Corpus Entry Schema

> 借鉴 ARS `literature_corpus_entry.schema.json`。

## Overview

每条 entry schema：

```yaml
- id: ckpt-pi0-v1
  type: checkpoint | dataset | paper | code
  obtained_via: "hf download lerobot/pi0 --revision <hash>"
  obtained_at: 2026-05-23T10:11:12+08:00
  local_path: /data1/ckpts/pi0/
  size_bytes: 12884901888
  sha256: <hex>
  license: Apache-2.0
  source_paper: "arxiv:2410.24164"
  notes: ""
```

写入 `corpus/literature_corpus.yaml`。

## Workflow

`--add`：用户指定 path + url，自动算 sha256 + size，写一行
`--list`：tabular 打印
`--verify`：复算 sha256 跟 manifest 对，diff 报 corruption

## Output

- `corpus/literature_corpus.yaml`
- `corpus/sha256_audit.log`（verify 历史）

## Composition

- `/resource-planning` 完后每条下载完跑 `--add`
- Stage 5/6 run 元数据引用 entry id
