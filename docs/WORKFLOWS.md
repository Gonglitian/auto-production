# WORKFLOWS.md — Named Composite Workflows

> 借鉴 ARIS W1-W6 命名 pipeline pattern。

## W1 — Full Research Pipeline

```
/research-pipeline "<topic>" — venue: <V>, budget: <T>
```

完整 Stage 1 → 9。最常用入口。

## W2 — Overnight Autonomous Mode

```
/sleep-research "<goal>" — budget: 8h, wake-on: pivot|guard-fail|done
```

W1 + stop-hook + heartbeat + cost cap。睡前一行。

## W3 — Targeted Improvement

```
/research-pipeline "improve X" — ref-paper: <url>, base-repo: <url>
```

读 ref paper 找弱点 → clone base repo → 针对性 idea → 跑 Stage 2-9。

## W4 — Rebuttal Sprint

```
/rebuttal "paper/ + reviews" — venue: ICML, character_limit: 5000
```

非 Stage 1 入口；只跑 Stage 8 rebuttal sub-pipeline。

## W5 — Resubmit Across Venues

```
/resubmit-pipeline "paper/" — from-venue: NeurIPS, to-venue: ICLR
```

text-only port，bib 冻结，5 阶段：anonymity → audits (--soft-only) → microedits → adversarial gate → compile + push。

## W6 — Status Snapshot

```
/status
```

跨机器一键看；可单独跑（非 pipeline 一部分）。

## Wiki — Persistent Memory

```
/learn-tag [LEARN:method] "..."
```

写入 MEMORY.md tier；下次 SessionStart 自动 load。

---

## Composition cheat sheet

| 目的 | 一行 |
|---|---|
| 从头开始一个 paper | `/research-pipeline "topic"` |
| 已有 idea，跑实验 | `/sprint-contract --init` → `/vla-audit` → `/smoke-test` → `/run-zero` → `/research-pipeline — start-stage: 5` |
| 已有 results，只写 paper | `/research-pipeline — start-stage: 8 — venue: NeurIPS` |
| 已收到 reviews | `/rebuttal "paper/" — venue: ICML` |
| 想换 venue 重投 | `/resubmit-pipeline "paper/" — to-venue: ICLR` |
| 想看现在状态 | `/status` |
| 想睡觉让它跑 | `/sleep-research "..."` |
| 周末复盘 | `/meta-optimize --since 7d` |
