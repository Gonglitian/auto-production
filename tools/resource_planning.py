#!/usr/bin/env python3
"""tools/resource_planning.py — pre-download resource planning table.

For each URL, HEAD-fetch Content-Length (best effort), check df -h on target,
emit a markdown table for user confirmation.
"""
import argparse, json, shutil, subprocess, sys, urllib.request
from pathlib import Path

def head_size(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as r:
            return int(r.headers.get("Content-Length", 0))
    except Exception:
        return None

def disk_free(path):
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    u = shutil.disk_usage(p)
    return u.free, u.total

def human(n):
    if n is None: return "?"
    for u in ("B","KB","MB","GB","TB"):
        if n < 1024: return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True, help="comma-separated URLs")
    ap.add_argument("--target-dir", default="/data")
    ap.add_argument("--out", default="docs/DEPLOYMENT.md")
    args = ap.parse_args()

    free, total = disk_free(args.target_dir)
    print(f"target: {args.target_dir}  free: {human(free)} / {human(total)}\n")

    plans = []
    total_size = 0
    for url in [u.strip() for u in args.items.split(",") if u.strip()]:
        sz = head_size(url)
        if sz: total_size += sz
        plans.append({"url": url, "size": sz})

    print("| # | URL | Size | ETA (100 MB/s) |")
    print("|---|-----|------|----------------|")
    for i, p in enumerate(plans, 1):
        eta = (p["size"] / (100*1024*1024) / 60) if p["size"] else None
        print(f"| {i} | {p['url'][:60]} | {human(p['size'])} | {f'{eta:.1f} min' if eta else '?'} |")
    print(f"\n**Total**: {human(total_size)}  vs free {human(free)}")
    if total_size > 0.8 * free:
        print("⚠️  WARNING: download exceeds 80% of free space.")

    # append to DEPLOYMENT.md
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "a") as f:
        f.write(f"\n## Download plan ({args.target_dir})\n")
        f.write(f"Total {human(total_size)} / free {human(free)}\n\n")
        for p in plans:
            f.write(f"- {p['url']}  ({human(p['size'])})\n")
    print(f"\n→ appended plan to {args.out}")

if __name__ == "__main__":
    main()
