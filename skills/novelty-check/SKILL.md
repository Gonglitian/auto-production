---
name: novelty-check
description: "Idea 拍下来后自动去 Semantic Scholar / OpenAlex 搜，看是否已有 paper 做过。防 \"想了 3 周才发现 ICLR'25 有人做过\"。Use when user says \"novelty check\", \"查重\", \"有人做过吗\", \"prior art\", \"是否新\", \"是不是 novel\", \"重复了没\"."
argument-hint: "[idea-md-or-title] [--threshold 0.6]"
allowed-tools: Bash(*), Read, Write, WebSearch, WebFetch
---

# /novelty-check — Idea Novelty Audit (S2 + OpenAlex)

> 借鉴 AI-Scientist novelty check。NOVELTY gate 必备产物。

## Overview

输入 idea 标题 / 一段描述，查 3 个源：

| 源 | API |
|---|---|
| Semantic Scholar | `api.semanticscholar.org/graph/v1/paper/search` |
| OpenAlex | `api.openalex.org/works?search=` |
| arXiv | `export.arxiv.org/api/query?search_query=` |

emit `closest prior work` 列表 + 相似度评分 + verdict `NOVEL / OVERLAP / DUPLICATE`。

## Workflow

1. Extract 5 key noun phrases from idea
2. Query each source with top phrase combinations
3. Dedupe by arxiv/DOI, sort by citation count
4. Fetch top 10 abstracts via WebFetch
5. Embed-similarity vs idea (用 tools 里 simple TF-IDF cosine，不依赖外部 embed)
6. Verdict:
   - max_sim < 0.5 → NOVEL
   - 0.5 ≤ max_sim < 0.75 → OVERLAP（user 看 closest 3 篇判断）
   - ≥ 0.75 → DUPLICATE（refuse PROCEED to NOVELTY gate）

## Output

```
idea-stage/novelty.json
{
  "verdict": "NOVEL|OVERLAP|DUPLICATE",
  "max_similarity": 0.43,
  "closest": [
    {"title":"...","authors":[...],"venue":"ICLR 2024","arxiv":"...","sim":0.43}
  ]
}
```

## Composition

- NOVELTY gate 检查 verdict ∈ {NOVEL, OVERLAP}
- `/idea-perspective` 完后立即跑本 skill
