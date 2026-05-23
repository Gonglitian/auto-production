---
name: smoke-test
description: "起正式训练前先跑 1-2 min 的 smoke test (微缩 batch / step) 把 pipeline 走完，不崩才放行正式。stop-hook 默认条件之一。用户说 'smoke' / 'smoke test' / '小跑一下' / 'sanity' 时调用。"
argument-hint: "[--script train.py] [--steps 50] [--batch 4]"
allowed-tools: Bash(*), Read, Edit
---

# /smoke-test — Sanity 跑通再起正式 Gate

来源 = M5 [user 每 project 必干一次]。

## Why

历史 N 次：起 100M step 训练 → 跑 30 秒崩 ImportError / OOM / dataset 路径不对。Smoke = 1-2 min 微缩跑过整个 pipeline → 不崩才让起正式。

## Workflow

### Phase 1: 找训练脚本

`--script` 显式给；否则 glob `scripts/train.py` / `train.py` / `main.py`。

### Phase 2: 缩参数

强制：
- `--total-timesteps`（或类似）→ `--steps 50`
- `--num-envs` → 缩到 `8` 以内
- `--batch-size` → 缩到 `4`
- 关掉 wandb online（用 `--wandb-mode offline`）
- 关掉 ckpt 写盘（环境变量 `SMOKE=1`，让 script 内部短路）

### Phase 3: 跑

```bash
SMOKE=1 timeout 120s python <script> <smoke-args> 2>&1 | tee /tmp/smoke.log
```

### Phase 4: Verdict

| Verdict | 条件 |
|---|---|
| ✅ PASS | exit 0 AND log 里至少有 1 个 step 完成 (grep "step 1" 或 wandb log line) |
| ⚠️ WARN | exit 0 但 step 数 < 5 (没真跑) |
| ❌ FAIL | 任何 exit code != 0 或 timeout |

写 `.auto-production/smoke_<sha>.json`：

```json
{"verdict": "PASS", "script": "scripts/train.py", "commit": "abc123", "ts": "..."}
```

### Phase 5: Stop-hook 联动

`hooks/stop_smoke_gate.sh` 在 `Stop` 事件触发时检查最近一次 smoke 是否 PASS（≤ 当前 commit 1 个之内）。如果不是 → 阻止 stop 并提示「跑 /smoke-test 先」。

## Output

```
✅ Smoke PASS @ 2026-05-22 23:45 (1m 14s, 50 steps, commit abc123)
Ready to launch full training.
```

或 FAIL 时：

```
❌ Smoke FAIL
Error: ImportError: cannot import 'foo' from 'bar' (scripts/train.py:42)
Fix and re-run /smoke-test.
```

## Failure modes

- 找不到 script → 让 user 显式指定
- script 不接受 `--steps` 这种 flag → 文档化「请支持 SMOKE=1 env 短路或 --steps」
- timeout 120s 不够 (大模型 init 慢) → `--timeout` 可调

## See also

- [`hooks/stop_smoke_gate.sh`](../../hooks/stop_smoke_gate.sh)
- [`templates/settings.json`](../../templates/settings.json) — stop hook 注册
