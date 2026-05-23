#!/usr/bin/env python3
"""tools/vla_audit.py — train/eval pipeline alignment audit.

Loads train_cfg and eval_cfg, extracts 6 dimensions, diffs them, emits verdict.
SKELETON — the actual loader code is project-specific. Each project should
register a loader hook at `.auto-production/vla_audit_loader.py` that exposes
two functions: `extract_train(cfg) -> dict` and `extract_eval(cfg) -> dict`.

Pure stdlib + optional torch/numpy if available.
"""
import argparse, importlib.util, json, math, sys
from pathlib import Path

DIMENSIONS = ["normalization", "shape", "dtype", "collate_src", "action_range", "image_pipeline"]
TOL_NUMERIC = 1e-6
TOL_PIXEL = 1e-4

def approx_eq(a, b, tol=TOL_NUMERIC):
    if a == b:
        return True
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, abs_tol=tol)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        return all(approx_eq(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
        return all(approx_eq(a[k], b[k], tol) for k in a)
    return False

def load_loader(path):
    if not Path(path).exists():
        sys.exit(f"❌ no loader at {path} — see SKILL.md Phase 0")
    spec = importlib.util.spec_from_file_location("loader", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def diff(train, eval_):
    out = {}
    for dim in DIMENSIONS:
        if dim not in train or dim not in eval_:
            out[dim] = {"missing": [d for d, x in [("train", train), ("eval", eval_)] if dim not in x]}
            continue
        if not approx_eq(train[dim], eval_[dim]):
            out[dim] = {"train": train[dim], "eval": eval_[dim]}
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loader", default=".auto-production/vla_audit_loader.py")
    ap.add_argument("--train-config", required=True)
    ap.add_argument("--eval-config", required=True)
    ap.add_argument("--out-dir", default=".auto-production/audit")
    args = ap.parse_args()

    loader = load_loader(args.loader)
    train = loader.extract_train(args.train_config)
    eval_ = loader.extract_eval(args.eval_config)

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "vla_audit_train.json").write_text(json.dumps(train, indent=2, default=str))
    (out / "vla_audit_eval.json").write_text(json.dumps(eval_, indent=2, default=str))

    d = diff(train, eval_)
    if d:
        (out / "vla_audit_diff.json").write_text(json.dumps(d, indent=2, default=str))
        print("❌ VLA-AUDIT FAILED — refusing to start training")
        print(json.dumps(d, indent=2, default=str))
        print("\nFix train ↔ eval mismatch then re-run.")
        sys.exit(1)

    import subprocess
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    (out / f"vla_audit_{sha or 'no-git'}.json").write_text(json.dumps({
        "passed_commit": sha, "train": train, "eval": eval_,
    }, indent=2, default=str))
    (out / "vla_audit.passed").write_text(sha or "no-git")
    print("✅ VLA-AUDIT PASSED")

if __name__ == "__main__":
    main()
