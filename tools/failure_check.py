#!/usr/bin/env python3
"""tools/failure_check.py — A5 7-mode failure-mode checklist.

Each check is best-effort heuristic; ambiguous → returns NEEDS_USER_REVIEW
which /failure-checklist promotes to a user prompt in interactive mode.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

CHECKS = {
    1: ("data snoop",
        "eval split is disjoint from train split — grep 'split' in dataset code"),
    2: ("distribution mismatch",
        "train/eval domain stats overlap — check normalization params"),
    3: ("leakage",
        "features do not contain label-derived columns — manual"),
    4: ("weak baseline",
        "/run-zero used stock paper config (git diff configs/paper.yaml clean)"),
    5: ("single-seed",
        "≥3 seed mean ± std reported (grep 'seed' in eval log)"),
    6: ("pre-trained sanity",
        "untuned ckpt SR < 5% (compare baseline log)"),
    7: ("implementation diff",
        "git commit clean + /vla-audit passed for current HEAD"),
}

def sh(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""

def auto_check(n, run_dir):
    if n == 4:
        diff = sh("git", "diff", "--quiet", "configs/paper.yaml")
        rc = subprocess.run(["git", "diff", "--quiet", "configs/paper.yaml"]).returncode
        return "PASS" if rc == 0 else "FAIL"
    if n == 5:
        try:
            log = (Path(run_dir or ".") / "eval.log").read_text()
            return "PASS" if log.lower().count("seed") >= 3 else "NEEDS_USER_REVIEW"
        except Exception:
            return "NEEDS_USER_REVIEW"
    if n == 7:
        head = sh("git", "rev-parse", "--short", "HEAD")
        got = ""
        try:
            got = Path(".auto-production/audit/vla_audit.passed").read_text().strip()
        except Exception: pass
        return "PASS" if head == got and head else "FAIL"
    return "NEEDS_USER_REVIEW"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("n", type=int, choices=list(CHECKS))
    ap.add_argument("--run", default="")
    args = ap.parse_args()

    label, hint = CHECKS[args.n]
    verdict = auto_check(args.n, args.run)
    print(f"{args.n}. {label}: {verdict}  ({hint})")

if __name__ == "__main__":
    main()
