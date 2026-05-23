---
name: citation-audit
description: "paper draft 里每句 'X et al. found Y' 必须带 3-layer anchor (quote/page/section/paragraph)。无 anchor 拒绝输出，强制 author 验证。Stage 8 → 9 强制 FINAL gate 一部分。用户说 'audit citations' / '查引用' / 'citation audit' / '防 hallucination' 时调用。"
argument-hint: "[paper-dir-or-tex] [--strict] [--cache .auto-production/cache/citations]"
allowed-tools: Bash(*), Read, Write, Grep, Glob, WebSearch, WebFetch, Agent
---

# /citation-audit — Paper Citation Faithfulness ⭐

来源 = F1 [ARS 3-layer anchor + claim audit 模式]。**desk-reject 第一杀手**——paper hallucination。

## What this catches

不是「明显假引用」(那些好 spot)，而是：

1. **存在但 attribution 错** — 引用了真 paper，但说成另一位 author
2. **存在但 year/venue 错** — 「Liu et al. 2024 ICLR」实际是 2023 NeurIPS
3. **存在但 context 不对** — 引用 paper 在 prove A，但你引来 support B（completely unrelated claim）
4. **fabricated quote** — 「as Liu et al. (2024) showed, X」但原文从未说过 X

## 3-layer Anchor Format

每个 `\cite{liu2024foo}` 在 markdown / tex source 必须**伴随**一个 HTML comment anchor：

```
\cite{liu2024foo} found that <claim>.
<!--anchor:quote="claim verbatim from paper":page=4:section=3.2:paragraph=2-->
```

- `quote=` ≤ 25 words 直接引文
- `page=`, `section=`, `paragraph=` 至少 2 个非空
- 缺 anchor → formatter 拒绝 emit

## Workflow

### Phase 1: Pre-search verification (fast filter)

调 `tools/verify_citations.py`：
- 抽 `.bib` 所有 entry
- 3-layer fallback: arXiv batch API (40 ids/req) → CrossRef DOI → Semantic Scholar fuzzy title (>= 0.6 word overlap)
- 每条产生 4-state: `verified` / `unverified` / `verify_pending` (5xx/timeout) / `error`
- 写 30-day TTL cache 到 `.auto-production/cache/citations.json`

### Phase 2: Anchor presence check

`grep -E '\\\\cite\\{[^}]+\\}'` 找所有 cite 位置 → 每个 cite 前后 3 行内必须有 `<!--anchor:...-->` block。

### Phase 3: Anchor validity check (per cite)

对 each anchor：
1. 用 WebSearch / arxiv fetch 拉原 paper（cache 一份）
2. spawn sub-agent 读原 paper + claim：
   - `quote=` 是否真在 paper 中（fuzzy match）
   - claim 是否被 paper 的 (page, section, paragraph) 段落支持
3. 输出 verdict `PASS` / `WARN` / `FAIL`

### Phase 4: Verdict aggregation

| Status | Count | Action |
|---|---|---|
| `verified` + anchor `PASS` | N1 | OK |
| `verified` + anchor `WARN` | N2 | flag for author review |
| `verified` + anchor `FAIL` | N3 | **BLOCK** submission |
| `verify_pending` | N4 | 不计入 hallucination rate，转 manual queue |
| `unverified` / `error` | N5 | **BLOCK** |

如果 N3 + N5 > 0 且非 `--strict=warn-only` → exit 1，阻断 `/paper-pipeline` 流水线。

### Phase 5: Report

写 `paper_audit_report.md`：

```markdown
## Citation Audit Report @ 2026-05-22

- Total citations: 87
- Verified + anchor passed: 78 (89.7%)
- Anchor missing: 4 ❌
- Anchor failed (wrong context): 2 ❌
- Verify pending (transient API): 3 ⚠️

### BLOCKED entries:
- liu2024foo (Sec 2.3) — anchor claim "robots prefer X" not found in original paper. Original talks about Y.
- ...
```

## Failure modes

- arXiv API down → tag `verify_pending`, exclude from rate, queue for retry
- 原 paper 是 paywall → 用 Open Access link / 提示用户提供 cookie / 跳过 anchor 验 (只验 metadata)
- `\cite` 形式不规范（natbib `\citep{}` 等）→ 扩 regex

## See also

- [`/cross-review`](../cross-review/SKILL.md) — sibling FINAL gate skill
- [`tools/verify_citations.py`](../../tools/verify_citations.py)
- ARS 3-layer anchor spec: `references/claude-code-skills/academic-research-skills/`
