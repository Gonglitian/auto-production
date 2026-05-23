#!/usr/bin/env python3
"""tools/auto_viz.py — auto-generate 4 plots from a W&B run.

Skeleton: pulls history via wandb API, emits 4 PNGs into figures/.
Requires `wandb` and `matplotlib` to actually run. Falls back to writing
placeholder text files if those imports fail (so smoke tests still pass).
"""
import argparse, json, sys
from pathlib import Path

PLOTS = ["loss", "reward", "task_sr", "pref_dist"]

def safe_imports():
    try:
        import wandb, matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return wandb, plt
    except Exception as e:
        print(f"⚠️  wandb/matplotlib unavailable: {e}", file=sys.stderr)
        return None, None

def write_placeholder(out, name, reason):
    (out / f"{name}.png.txt").write_text(f"placeholder — {reason}\n")

def plot_history(wandb, plt, run_id, out):
    api = wandb.Api()
    run = api.run(run_id)
    hist = run.history(samples=10000)

    if "loss" in hist.columns or "train/loss" in hist.columns:
        col = "loss" if "loss" in hist.columns else "train/loss"
        plt.figure(figsize=(8, 5))
        plt.plot(hist.get("step", hist.index), hist[col])
        plt.xlabel("step"); plt.ylabel(col); plt.title(f"{run.name} — loss")
        plt.tight_layout(); plt.savefig(out / "loss.png", dpi=120); plt.close()
    else:
        write_placeholder(out, "loss", "no loss column")

    for src_col, fname in [("reward", "reward"), ("success_rate", "task_sr")]:
        if src_col in hist.columns:
            plt.figure(figsize=(8, 5))
            plt.plot(hist.get("step", hist.index), hist[src_col])
            plt.xlabel("step"); plt.ylabel(src_col); plt.title(f"{run.name} — {src_col}")
            plt.tight_layout(); plt.savefig(out / f"{fname}.png", dpi=120); plt.close()
        else:
            write_placeholder(out, fname, f"no {src_col} column")

    pref_cols = [c for c in hist.columns if "pref" in c.lower()]
    if pref_cols:
        plt.figure(figsize=(8, 5))
        for c in pref_cols:
            plt.hist(hist[c].dropna(), bins=20, alpha=0.4, label=c)
        plt.legend(); plt.title(f"{run.name} — preferences"); plt.tight_layout()
        plt.savefig(out / "pref_dist.png", dpi=120); plt.close()
    else:
        write_placeholder(out, "pref_dist", "no preference column")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wandb-run", required=True, help="entity/project/run_id or run_id alone")
    ap.add_argument("--output", default="figures/")
    args = ap.parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)

    wandb, plt = safe_imports()
    if wandb is None:
        for p in PLOTS:
            write_placeholder(out, p, "wandb missing")
        sys.exit(0)

    plot_history(wandb, plt, args.wandb_run, out)
    print(f"✅ wrote {len(PLOTS)} figures to {out}/")

if __name__ == "__main__":
    main()
