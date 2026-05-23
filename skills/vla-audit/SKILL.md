---
name: vla-audit
description: "训练前必跑：自动 diff train 端和 eval 端的 input normalization 公式 / dim / dtype / batching / action space 范围 / image preprocessing。任何不一致拒绝训练并列出 diff。用户 #1 zero-shot bug class（OFT / GR00T-N1.6 / MemoryVLA / hf-jax 都中过）。用户说 'audit pipeline' / '对齐 train eval' / 'vla audit' / '查 normalization' 时调用。"
argument-hint: "[--train <path>] [--eval <path>] [--strict]"
allowed-tools: Bash(*), Read, Grep, Glob, Edit, Agent
---

# /vla-audit — Train ↔ Eval Pipeline 一致性审计 ⭐

来源 = C8 [hf-jax env-fidelity audit 实战模式抽象]。是 **Stage 2 → 4 之间的强制 gate**。

## When to Use

**MANDATORY** in：
- 任何 VLA / robot learning project 起训练前
- ckpt 换了新 backbone 后
- dataset preprocessing 改过后

## What this catches

| 类型 | 例子 | 后果 |
|---|---|---|
| Image normalization 公式 | train `(x-127.5)/127.5`, eval `x/255.0 - 0.485 / 0.229` | zero-shot 完全失败 |
| Action space 范围 | train `[-1, 1]`, eval `[0, 2π]` | gripper 反向 |
| Dim mismatch | train 7-dim action, eval 6-dim | shape error 或 silent truncate |
| Dtype | train fp32, eval bf16 | 数值漂移 |
| Batching | train `(B, T, C, H, W)`, eval `(T, C, H, W)` 漏 batch dim | 单 sample 跑通但 batched 错 |
| Image preprocess order | train resize→crop→norm, eval crop→resize→norm | 微小 shift |

## Workflow

### Phase 1: Locate pipeline files

自动 glob：
- Train: `train.py`, `dataset.py`, `data_loader.py`, `transforms.py`
- Eval: `eval.py`, `evaluate.py`, `inference.py`, `deploy.py`

用户可显式 `--train scripts/train.py --eval scripts/eval.py` override。

### Phase 2: Extract normalization signatures

用 grep + AST 解析提取每个 pipeline 端的：

1. **Image transform chain** — 找 `transforms.Compose([...])` / `tf.image.*` / `cv2.*` / 手写 op
2. **Numerical normalize** — 找 `mean=` `std=` 常数 + `/255` `*255` `-127.5` 模式
3. **Action transform** — 找 action `normalize` / `unnormalize` / `clip` / `scale`
4. **Dim / dtype** — 找 `.reshape(` / `.astype(` / `dtype=`

写成 JSON：
```json
{
  "train": {
    "image_norm": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
    "action_range": [-1, 1],
    "action_dim": 7,
    "dtype": "fp32"
  },
  "eval": {...}
}
```

### Phase 3: Diff

对每 key 严格比较。**Tolerance: 0**（normalization 公式不允许 round-off mismatch）。

### Phase 4: Verdict

- 完全一致 → `PASS` + 写入 `.auto-production/cache/vla-audit-pass-<sha>.json` + 允许起训练
- 有 diff → `FAIL` + 输出 diff 表 + 阻断（exit 1）

`--strict` 模式：还要查 image preprocessing **顺序**（resize/crop/normalize 三者顺序敏感）。

### Phase 5 (optional): Auto-fix proposal

如果 diff 简单（如 mean/std 常数差异），spawn 一个 sub-agent 提议 patch (Edit 形式)，让 user 拍板。

## Output

```markdown
## VLA Pipeline Audit @ 2026-05-22

| Field | Train | Eval | Match? |
|---|---|---|---|
| image_mean | [0.485, 0.456, 0.406] | [0.5, 0.5, 0.5] | ❌ |
| image_std | [0.229, ...] | [0.5, ...] | ❌ |
| action_range | [-1, 1] | [-1, 1] | ✅ |
| action_dim | 7 | 7 | ✅ |
| dtype | fp32 | bf16 | ⚠️ (numerical drift OK?) |

**Verdict**: ❌ FAIL — 2 hard mismatches in image normalization.

**Action**: training BLOCKED. Fix in:
  - `scripts/eval.py:42` — change mean/std to match train.
  - Or: change `dataset.py:88` to use [0.5, 0.5, 0.5] for both.

User 拍板后 re-run `/vla-audit`.
```

## Failure modes (skill 自己的)

- 找不到 train/eval 文件 → 报错，让用户 `--train --eval` 显式指定
- pipeline 用了动态加载（registry pattern）→ 静态 AST 抓不到 → spawn sub-agent 用 LLM 读源代码
- 多种 normalization 路径（如 simulation vs real-world）→ 列出所有路径让 user 选要审哪条

## See also

- [`docs/GATES.md`](../../docs/GATES.md#method-gate) — METHOD gate 入口
- [`/ast-validate`](../ast-validate/SKILL.md) — 通用代码静态检查（不止 normalization）
- Reference: `hf-jax env-fidelity audit` (12 HIGH + 8 MEDIUM gaps found 2026-05-15)
