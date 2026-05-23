---
name: cross-review
description: "draft 出来后 Claude (执笔) × GPT (critic) × Gemini (second critic) 三家互审，收敛到 final draft。固化你已经在 sub-agent 模式手动干的事。用户说 'cross review' / '互审' / '三家审' / 'codex review' 时调用。"
argument-hint: "[draft-path] [--rounds 3] [--reviewer codex|gemini|both]"
allowed-tools: Bash(*), Read, Write, Edit, Agent
---

# /cross-review — Claude × GPT × Gemini 三家互审 ⭐

来源 = F2 [ARIS adversarial vs stochastic bandit 论证]。

## Why cross-model

单模型 self-review 是 **stochastic bandit**——同一模型 review 自己的输出，noise 是可预测的，blind spot 一致。

跨模型 = **adversarial bandit**——reviewer 主动探测 executor 没意识到的弱点，blind spot 互补。

> 2 model 是最小数（破 self-play 即可）；3+ 收益边际递减。

## Workflow

### Phase 0: Resolve reviewer backends

- GPT: 优先 `mcp__codex__codex` (Codex MCP, xhigh)；fallback `OPENAI_API_KEY` HTTP
- Gemini: 优先 `mcp__gemini-review__*` (Gemini MCP)；fallback `GEMINI_API_KEY` HTTP

至少需要 1 个 reviewer 可用，否则报错。

### Phase 1: Author draft (Claude, 你)

读 `<draft-path>` 文件作为初稿。

### Phase 2: Round 1 — Critic pass

并行：
- 给 Codex prompt: "你是 ML reviewer，找逻辑漏洞、未支持 claim、citation 错配、unclear writing。3 个最重要的问题。"
- 给 Gemini 同 prompt，但要求「不同于另一个 reviewer 的视角」

收集两份 review.md。

### Phase 3: Round 1 — Author respond

你（Claude）读两份 review：
- 同意的：修
- 不同意的：写反驳并说明
- 模棱两可的：列出来让 user 拍板

输出 `revised_draft.md` + `response_to_reviewers.md`。

### Phase 4: Round 2 — Stress test

第二轮 reviewer 拿到 revised draft + response，专门攻击：
- 反驳是否有理
- 修是否引入新问题
- 是否漏了某个 reviewer concern

### Phase 5: Round 3 (optional) — Converge

如果第 2 轮还有 BLOCK 级问题，第 3 轮。`--rounds N` 设上限。

### Phase 6: Verdict

```markdown
## Cross-review converged after $R rounds

- Codex final verdict: APPROVE / APPROVE WITH NITS / REQUEST CHANGES
- Gemini final verdict: ...
- Both APPROVE → ✅ ready for /citation-audit + FINAL gate
- 1 still REQUEST CHANGES → user 决定 ship or 继续
```

## Output

```
.auto-production/cross-review/<draft-stem>/
├── round_1_codex_review.md
├── round_1_gemini_review.md
├── round_1_revised_draft.md
├── round_1_response.md
├── round_2_...
└── final_verdict.md
```

## Failure modes

- 一个 reviewer 一直 REQUEST CHANGES → cap rounds + escalate user
- review 之间矛盾 → 输出双 reviewer diff 让 user 拍
- API rate limit → backoff，必要时降级到单 reviewer

## See also

- [`/citation-audit`](../citation-audit/SKILL.md) — 走完 cross-review 再跑 audit
- [`/kill-argument`](../kill-argument/SKILL.md) — 专门给 theory paper 的 two-thread adversarial
- ARIS reference: `references/claude-code-skills/Auto-claude-code-research-in-sleep/skills/auto-review-loop-llm`
