---
name: run-zero
description: "任何 iterative search 开始前先手动跑一遍 baseline (原 paper config 零修改) 把 metric 锁定。后续所有 iteration 必须超过 run_0 才算 agent 改善了。防 '训练 loss 在降但其实只是修复了 bug' 假阳性。用户说 'run zero' / 'baseline lock' / '锁基线' 时调用。"
argument-hint: "[--paper-config <file>] [--lock-file .auto-production/run_zero.json]"
allowed-tools: Bash(*), Read, Write
---

# /run-zero — Per-machine Baseline Lock

来源 = A6 [AI-Scientist / AI-Researcher Validation Phase]。

## Why

历史多次 false positive：「训练 loss 在降」其实只是修复了**实现 bug**，跟 idea 没关系。`run_0` 锁定一个**未修过的 paper-default baseline metric** → 后续 iteration 必须超过它才算「improvement」。

## Workflow

### Phase 0: 检测 run_0 是否已锁

```bash
[ -f .auto-production/run_zero.json ] && echo "already locked, exit" || continue
```

如果已锁 → 报告锁了的 metric + 提示「要重锁删 run_zero.json」。

### Phase 1: Pull paper default config

- 优先 `--paper-config configs/paper_default.yaml`
- 否则从 git history 找最早 commit 的 config (`git log --reverse configs/`)
- 否则报错：「请显式提供 paper-original config」

### Phase 2: Run baseline experiment

```bash
python scripts/train.py --config configs/paper_default.yaml \
                       --total-timesteps $PAPER_STEPS \
                       --seed 42 \
                       --wandb-tags run_zero baseline \
                       --output runs/run_zero
```

⚠️ **不**允许 agent 改 config 做 "small improvement"。原版就是原版。

### Phase 3: Extract & lock metrics

```python
import json
metrics = parse_wandb_summary("runs/run_zero/wandb-summary.json")
lock = {
  "machine": socket.gethostname(),
  "commit": git_sha(),
  "config_path": "configs/paper_default.yaml",
  "config_sha": file_sha("configs/paper_default.yaml"),
  "seed": 42,
  "metrics": {
    "loss/final": metrics["loss/total"],
    "reward/mean": metrics["reward/mean"],
    "sr/best": max(metrics["success_rate/task_*"].values()),
    ...
  },
  "wandb_run_id": metrics["run_id"],
  "locked_at": "2026-05-22T23:00:00",
}
json.dump(lock, open(".auto-production/run_zero.json", "w"), indent=2)
```

### Phase 4: 调 `/sprint-contract` 比对

后续 `/sprint-contract --check` 自动读 `run_zero.json`，校验 Metric 字段的阈值是否 > run_0 baseline。如果阈值 ≤ run_0 → warn「不算 improvement，确认要跑吗？」

### Phase 5: Cross-machine sanity

每台 machine 一份 `run_zero.json`（同样 paper config，不同硬件可能有 ±5% 浮动）。`/cross-host-sync` 把 run_zero.json 也带上 Notion。

## Output

`.auto-production/run_zero.json`（不要 commit，gitignored）+ 终端报告锁定的 metric。

## Failure modes

- paper config 找不到 → 提示用户提供 / 让 user 写一个 minimal default
- baseline 跑 OOM → 提示降 batch size + 重锁
- baseline 跑废（NaN/diverge）→ 不锁，报警

## See also

- [`/sprint-contract`](../sprint-contract/SKILL.md) — 比对 Metric vs run_0
- [`/pivot`](../pivot-decision/SKILL.md) — REFINE 判断是否真比 run_0 好
