# GATES.md — 5 Named Stage Gates

> 借鉴 ARS Stage 2.5 / 4.5 integrity gates + AutoResearchClaw 3-gate + design.md Part III §A2。

每个 gate = 「必须有 audit trace 文件存在 + commit 匹配，agent 才放行下一 stage」。

---

## Gate 1 — NOVELTY (Stage 1 → 2)

### Required artifacts

| 文件 | 内容 | 来源 |
|---|---|---|
| `idea-stage/proposal.md` | 至少 5 段：motivation / hypothesis / method sketch / expected contribution / experiment plan | `/idea-perspective` 或 user 写 |
| `idea-stage/novelty.json` | S2 / OpenAlex 搜索结果，含 closest prior work 列表 | `/novelty-check` |
| `idea-stage/persona_questions.md` | 8-persona × 3 questions = ≥24 questions | `/persona-probe` |

### Auto-check

```bash
[ -s idea-stage/proposal.md ] \
  && [ -s idea-stage/novelty.json ] \
  && [ -s idea-stage/persona_questions.md ] \
  && [ $(wc -l < idea-stage/persona_questions.md) -ge 24 ] \
  || exit 1
```

### Manual sign-off

如 `mode != full-auto`，agent 必须 AskUserQuestion：「proposal + novelty + 8-persona Q 齐备，PROCEED to METHOD?」user 拍 PROCEED 才进 Stage 2。

---

## Gate 2 — METHOD (Stage 2 → 4)

### Required artifacts

| 文件 | 内容 |
|---|---|
| `.auto-production/audit/vla_audit_<commit>.json` | `/vla-audit` 通过的 trace，包含 6-维 train/eval 一致性 |
| `.auto-production/audit/vla_audit.passed` | 一行 commit hash，必须等于 `git rev-parse --short HEAD` |
| `.auto-production/audit/ast_validate.passed`（可选）| `/ast-validate` 静态分析过 |

### Auto-check

```bash
HEAD=$(git rev-parse --short HEAD)
GOT=$(cat .auto-production/audit/vla_audit.passed 2>/dev/null)
[ "$HEAD" = "$GOT" ] || exit 1
```

### Why

VLA pipeline 不一致是 user 历史 #1 zero-shot bug class（OFT / GR00T / MemoryVLA / hf-jax 都中过）。强制 gate 不允许偷过。

---

## Gate 3 — RESOURCE (Stage 4 → 5)

### Required artifacts

| 文件 | 内容 |
|---|---|
| `sprint_contract.yaml` | 5-tuple 全填 + Guard 含可量化阈值 |
| `.auto-production/audit/contract_signed.json` | `{sha256: <hash>, signed_at: ...}`，hash 必须等于当前 sprint_contract.yaml |
| `.auto-production/baseline/run_zero_<host>_<commit>.json` | `/run-zero` 锁定的 baseline metric (mean ± std, ≥3 seeds) |
| `.auto-production/audit/smoke_passed.json` | `/smoke-test` 通过 + commit 匹配 |

### Auto-check

```bash
HEAD=$(git rev-parse --short HEAD)
HOST=$(hostname)
SHA=$(sha256sum sprint_contract.yaml | awk '{print $1}')
GOT_SHA=$(python3 -c "import json; print(json.load(open('.auto-production/audit/contract_signed.json'))['sha256'])" 2>/dev/null)
[ "$SHA" = "$GOT_SHA" ] || exit 1
ls .auto-production/baseline/run_zero_${HOST}_*.json >/dev/null 2>&1 || exit 1
GOT_SMOKE=$(python3 -c "import json; print(json.load(open('.auto-production/audit/smoke_passed.json'))['commit'])" 2>/dev/null)
[ "$GOT_SMOKE" = "$HEAD" ] || exit 1
```

---

## Gate 4 — RESULTS (Stage 6 → 7)

### Required artifacts

| 文件 | 内容 |
|---|---|
| `decisions.jsonl` | 最新一行 entry 含 `rec` ∈ {PROCEED, REFINE, PIVOT} 且 `user_decision` 字段非空 |
| `findings.md` | 包含本次决策段（手写或 `/pivot` 自动追加）|
| `figures/loss.png`, `reward.png`, `task_sr.png`, `pref_dist.png` | `/auto-viz` 出图 |
| `.auto-production/audit/a5_failure_checklist.passed` | 7 种 known failure mode 逐项 ✓ |

### Auto-check

```bash
LATEST=$(tail -1 decisions.jsonl 2>/dev/null)
python3 -c "
import json,sys
d=json.loads('$LATEST' or '{}')
assert d.get('rec') in {'PROCEED','REFINE','PIVOT'}
assert d.get('user_decision')
" || exit 1
```

### A5 failure-mode checklist (must ✓)

1. ❑ data snoop：eval set 没被训练用过
2. ❑ distribution mismatch：train / eval 分布对齐
3. ❑ leakage：features 不含 label-derived info
4. ❑ weak baseline：`/run-zero` 是 paper 原 config
5. ❑ multi-seed：≥3 seed mean ± std
6. ❑ pre-trained sanity：未 fine-tune 的 ckpt SR < 5%
7. ❑ implementation diff：commit clean / 跟 baseline 对比一致

---

## Gate 5 — FINAL (Stage 8 → 9)

### Required artifacts

| 文件 | 内容 |
|---|---|
| `.auto-production/cite_audit.json` | `verdict: PASS`（或 `WARN` 且无 BLOCKED）|
| `.auto-production/cross_review/round_N/converged.json` | 两个 critic 都 APPROVE / APPROVE_WITH_NITS |
| `.auto-production/audit/a5_failure_checklist.passed` | 同上 |
| `paper/paper.pdf` | compile 成功 |

### Auto-check

```bash
python3 -c "
import json
v = json.load(open('.auto-production/cite_audit.json'))['verdict']
assert v in {'PASS','WARN'}, f'cite audit verdict {v}'
" || exit 1
ls .auto-production/cross_review/round_*/converged.json >/dev/null 2>&1 || exit 1
```

### Manual sign-off (recommended)

即使 `mode == full-auto`，FINAL gate 默认要 user 确认（paper 投出去不可撤）。`--really-full-auto` 才跳过。
