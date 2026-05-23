---
name: sprint-contract
description: "起任何实验/sprint 前必须填 Karpathy 5-tuple: Goal / Scope / Metric / Verify / Guard。不填拒绝起训练。Stage 4 → 5 之间 RESOURCE gate 的一部分。用户说 'contract' / '5-tuple' / '签合同' / 'sprint plan' 时调用。"
argument-hint: "[--file sprint_contract.yaml] [--check|--init]"
allowed-tools: Bash(*), Read, Write, Edit
---

# /sprint-contract — Karpathy 5-tuple Gate ⭐

来源 = B2 [uditgoenka/autoresearch + Karpathy]。

## The 5 Required Fields

| Field | Question | Example |
|---|---|---|
| **Goal** | 这个 sprint 回答什么 question | "stage 1 5 个 guiding policy 是否能各自达到 paper Table II 的 SR" |
| **Scope** | 不做什么（防 scope creep） | "不动 stage 2 KL distillation；不改 lidar config" |
| **Metric** | 量化判断成功的指标 + 阈值 | "5 个 guiding policy 全部达到 SR ≥ 0.7 @ 5M step" |
| **Verify** | 怎么知道结果可信 | "eval 跑 100 episode × 3 seed；vla-audit 通过" |
| **Guard** | 什么算不可接受的失败（trigger PIVOT） | "任何 guiding 5M step 后 SR < 0.4 → PIVOT 不再加 step" |

**Guard 字段尤其关键**——明确「OCR > 20% 就算失败」让 agent 主动报警，反 sunk-cost。

## Workflow

### Mode 1: `--init`

如果 `sprint_contract.yaml` 不存在，cp 一份 `templates/five_tuple.yaml` 到当前目录，用 user 拍板的 Goal 起手，剩下 4 项空着等 user 填。报告给 user 提示「filling required」。

### Mode 2: `--check`（默认）

读 `sprint_contract.yaml`，校验：

1. 5 字段都非空
2. Metric 字段有 numeric threshold（regex `\d+(\.\d+)?` 或 `<=`/`>=` 符号）
3. Guard 字段有 trigger 描述（含 `trigger:` 或 `if ...` 模式）
4. Verify 字段含 `seed` count

任一失败 → exit 1，阻断 stage 5 (Tasks Running)。

### Mode 3: post-sprint 自动复盘（被 `/pivot` 调）

跑完实验后 `/pivot` 自动调 `--reflect`：
- 对照 Goal 是否达到
- 对照 Metric 是否过阈值
- 对照 Guard 是否触发
- 对照 Scope 是否 creep

写复盘段到 `findings.md`。

## YAML Schema

见 [`templates/five_tuple.yaml`](../../templates/five_tuple.yaml)。

## Output (check mode)

```markdown
## Sprint Contract Check @ 2026-05-22

| Field | Status | Note |
|---|---|---|
| Goal | ✅ |
| Scope | ✅ |
| Metric | ⚠️ | 缺 threshold ("SR 高一点" 不是 metric) |
| Verify | ✅ | 100 ep × 3 seed |
| Guard | ❌ | 字段空 |

**Verdict**: ❌ FAIL — 2 fields incomplete. 起训练 BLOCKED.

请填：
  Metric:  改成 "SR ≥ 0.7 @ 5M step"
  Guard:   填 "if SR < 0.4 @ 5M then PIVOT"
```

## External-ref validation (NEW in v2)

> 实战由来：vla3d Sprint 2 contract 把 partition 写成 `raise@hpcc`——这是 stale
> 信息，真实 hpcc 现有 partition 是 `batch / epyc / gpu / highclock / highmem`。
> 如果 sign 时没 validate，到 sbatch 时才崩 + 损失几分钟到 hours。

`sprint_contract.yaml` 里任何引用「外部资源标识符」的字段都必须在 `--sign` 阶段
做 reachability check。常见：

| 字段类型 | 检查 | 实现 |
|---|---|---|
| **slurm partition** | `sinfo -p $PARTITION` 返回非空 | `verify_partition_exists()` |
| **conda env path** | 路径存在 + has python | `verify_conda_env_path()` |
| **dataset HF repo** | `huggingface_hub.repo_exists()` | `verify_hf_repo()` |
| **wandb project** | api.project() 不 404 | `verify_wandb_project()` |
| **lerobot version pin** | `import lerobot; lerobot.__version__ == X` | `verify_pkg_version()` |
| **arxiv ID 引用** | URL 200（cite-audit Layer 1 复用） | `verify_arxiv_id()` |

完整 helper 见 [`templates/verify_external_ref.py`](../../templates/verify_external_ref.py).

`--sign` workflow (v2)：

```bash
/sprint-contract --verify        # 5-tuple 字段 + threshold/seed check
/sprint-contract --check-refs    # NEW: 跑所有外部 ref validator
/sprint-contract --sign          # sha256 锁定 yaml + 写 audit trace
```

如 `--check-refs` 任何 fail → `--sign` 拒绝执行。

## Failure modes

- yaml 解析错 → 提示语法
- 用户硬要跑没合同 → 仍然 BLOCK，让 user 显式 `--force`（且 log 警告）
- 外部 ref 检查失败（如 partition 不存在）→ exit 2 + 列出失败 ref + 修复建议

## See also

- [`/pivot`](../pivot-decision/SKILL.md) — RESULTS gate 用 5-tuple 复盘
- [`/run-zero`](../run-zero/SKILL.md) — 同 gate 另一道
- [`/arch-plan`](../arch-plan/SKILL.md) — code-level external ref 守门（line# / API）
- [`templates/sprint_contract.yaml`](../../templates/sprint_contract.yaml) — v2 schema 含 differentiators / baselines / axes_changed
- [`templates/verify_external_ref.py`](../../templates/verify_external_ref.py) — runtime fail-loud helpers
