---
name: auto-viz
description: "实验跑完自动出 4 张 PNG: loss curve / reward curve / per-task SR breakdown / per-preference 分布，嵌进 html homepage + Notion run 页。替代纯 wandb 截图手工流程。用户说 '出图' / 'plot' / 'viz' / '画一下' / 'auto viz' 时调用。"
argument-hint: "[--wandb-run <id>] [--out figures/] [--include all|loss|reward|sr|pref]"
allowed-tools: Bash(*), Read, Write
---

# /auto-viz — 自动可视化 (matplotlib + wandb API)

来源 = E1。

## Why

`wandb.ai` 网页费眼睛 + 截图发 Notion 是手动。这个 skill 拉数据 → matplotlib → PNG → 自动嵌 html。

## Workflow

### Phase 0: Locate run

- `--wandb-run <id>` 显式给
- 否则读 `wandb/latest-run/files/wandb-metadata.json` 拿 run id
- 否则报错

### Phase 1: Pull metrics

```python
import wandb
api = wandb.Api()
run = api.run(f"{ENTITY}/{PROJECT}/{RUN_ID}")
hist = run.history()  # pd.DataFrame
```

（注意：wandb 不在 stdlib，按 K1 规则该 skill 是**条件可用**——要求用户已 `pip install wandb`，否则降级为「不画图，输出 instructions」。）

### Phase 2: 4 张图

| Figure | data column | style |
|---|---|---|
| `loss.png` | `loss/total`, `loss/policy`, `loss/value` | log-y, multi-line |
| `reward.png` | `reward/mean`, `reward/std` band | mean ± std fill |
| `sr_per_task.png` | `success_rate/task_*` | bar chart, sorted desc |
| `pref_distribution.png` | `preference_used/*` | stacked bar across chunk |

### Phase 3: HTML embed

写入 / 更新 `homepage.html` 的 `<section id="latest-run">`：

```html
<img src="figures/loss.png" />
<img src="figures/reward.png" />
...
```

### Phase 4 (optional): Notion mirror

调 `tools/cross_host_sync.py --update-figures <run_id>`，把 PNG 上传到 Notion run 页。

## Output

```
figures/
├── loss.png
├── reward.png
├── sr_per_task.png
└── pref_distribution.png
homepage.html  (updated)
```

加一行 markdown 摘要：

```markdown
## Auto-viz @ 2026-05-22
- Loss: final 0.34 (down from 1.2 at step 0)
- Reward: 78.5 ± 4.2
- SR (best task): 0.91 / SR (worst): 0.42
- Pref 1.5m used 22%, 2.25m 38%, 3.0m 40%
```

## Failure modes

- wandb 不可达 → 报错
- run 还在跑 → 用 partial history，标 `[in-progress]`
- 缺 metric → 跳过那张图，不阻塞

## See also

- [`/html-homepage`](../html-homepage/SKILL.md) — 接收并 render
- [`tools/auto_viz.py`](../../tools/auto_viz.py)
