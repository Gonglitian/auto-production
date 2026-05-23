# Example — From Idea to Paper in 14 Days

> 模拟一次用 `/research-pipeline` 走完 Stage 1 → 9 的会话。

## Day 0 — Setup

```bash
git clone https://github.com/<you>/auto-production.git ~/proj/auto-production
cd ~/proj/my-new-research
git init
~/proj/auto-production/install.sh --mode project --target .
```

## Day 1 — Kick off

```
User: /research-pipeline "factorized gap in discrete diffusion LMs"
  — venue: NeurIPS, mode: co-pilot, budget: 14d
```

Agent:

```
**Conclusion**: Pipeline started, Stage 1 entering. NOVELTY gate ~2h.

**What I changed**:
- created .auto-production/ structure
- wrote research_direction.md
- marked stage=1

**What I checked**:
- AUTO_PRODUCTION_REPO env ✓
- git initialized ✓
- conda env = my-research ✓

**Risks**:
- co-pilot mode means I'll wake you at each named gate (NOVELTY/METHOD/RESOURCE/RESULTS/FINAL)
- budget 14d will trigger stop even if mid-stage

**Next step**:
- run /idea-perspective + /persona-probe + /novelty-check in parallel
- ETA NOVELTY gate: 2h
```

## Day 1 (later) — NOVELTY gate

Agent stops and asks:

```
✅ NOVELTY gate ready:
   - proposal.md (5 sections, 320 lines)
   - novelty.json (3 closest prior works found, none identical)
   - persona_questions.md (8 stakeholders × 3 = 24 questions)

PROCEED to METHOD? [PROCEED / REFINE / PIVOT]
```

User: `PROCEED`

## Day 2-3 — Code Generation + METHOD gate

Stage 2 runs `/arch-plan` → `/ast-validate` → `/vla-audit`. VLA audit catches a `dtype` mismatch in eval. Agent:

```
❌ VLA-AUDIT FAILED:
   train: bf16, eval: fp32

Suggested patch:
  configs/eval.yaml:12  dtype: fp32 → bf16

Apply? [Y/n]
```

User Y. Re-runs audit. PASS.

```
✅ METHOD gate passed (commit 5a3f291)
   - vla_audit.passed ✓
   - ast_validate.passed ✓
```

## Day 3 — RESOURCE gate

Stage 4：

```
/sprint-contract --init
```

Agent writes draft 5-tuple, user fills/edits. Then:

```
/sprint-contract --verify   # ✓
/sprint-contract --sign     # sha256 locked
/run-zero --seeds 3         # 3 seeds × ~2h = 6h
/smoke-test                 # 50 step in 4 min
```

```
✅ RESOURCE gate:
   - contract signed: c8d1...
   - run_zero locked: 0.62 ± 0.04 SR
   - smoke passed: 5a3f291
```

## Day 4-11 — Stage 5 + 6 (full-auto night mode)

```
/sleep-research "训完 stage 1 (5 guidings × 40M) + stage 2 (50M meta-distill), 
                eval on MC10/MC20, 醒来 /pivot 报告"
```

User goes to sleep. Agent loops:

- `/slurm-hold --partition raise --days 7`
- 起 `/stall-detect` watcher
- 跑 train (heartbeat 每 5min 写)
- 完成第一个 guiding → `/auto-viz` → `/cross-host-sync` push → 起下一个
- 凌晨 3 点 GPU OOM → `/audit-driven-retrain` (scancel → audit → reduce bs → retry)
- 早 8 点全部完成 → `/pivot --auto-recommend`

User 起床:

```
$ cat wakeup_report.md

**Conclusion**: 5 guidings + meta-distill 完成. Stage 1 best SR 87% (>80% goal), 
                meta SR 91%. Recommend PROCEED to Stage 7.

**What I changed**: ... (8 commits across v6-meta-* runs)
**What I checked**: ... (gates / smoke / audit / cross-host-sync)
**Risks**: pref-3.0 SR only 73% (others all >85%); may need ablation
**Next step**: confirm PROCEED → Stage 7 + 8 (paper draft). I queued /paper-pipeline.
```

User: PROCEED.

## Day 12-13 — Stage 8 paper

```
/paper-pipeline --venue NeurIPS
  → outline (1h)
  → draft (overnight)
  → /cross-review --rounds 3   # Claude × GPT × Gemini 互审
  → revise (3 round)
  → /citation-audit            # 87 cite，82 verified，3 anchor_missing
  → user fix 3 missing anchors
  → re-audit ✓ PASS
  → /pubfig
  → compile paper.pdf
```

```
✅ FINAL gate:
   - cite_audit verdict=PASS
   - cross_review converged in 2 rounds
   - a5_failure_checklist all ✓
   - paper.pdf compiled (12 pages)

Submit to NeurIPS OpenReview? [Y/n]
```

User Y. Done. Day 14 buffer.

## Post-acceptance (3 months later)

```
/paper-talk
/paper-poster
/paper-slides
```

Reviewer feedback comes:

```
/rebuttal "paper/ + reviews" — venue: NeurIPS, character_limit: 5000
```

---

## 整体感受

- **co-pilot mode** 让 user 在 5 个 gate 处确认，其他时间 agent 自跑
- **full-auto mode**（夜间）让 agent 跑到 wake-on 条件触发才停
- 每次 `/pivot` 三选一记录到 `decisions.jsonl`，周末 `/meta-optimize` 复盘 agent 推荐 vs user 决策的差异，patch skill prompt
- `homepage.html` 60s 自刷，user 任何时间打开都能看
