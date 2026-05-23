#!/usr/bin/env python3
"""tools/tree_viz.py — render runs/_archive/* DAG as ASCII + HTML.

Parent inferred from `Predecessor:` line in each run's PROMPT.md (written by
auto_version.py). Each node: label / metric / commit / status.
"""
import argparse, html, json, re, sys
from collections import defaultdict
from pathlib import Path

def parse_run(d):
    p = d / "PROMPT.md"
    pred = ""
    if p.exists():
        m = re.search(r"^Predecessor:\s*(.+)$", p.read_text(), re.MULTILINE)
        if m: pred = m.group(1).strip()
    metric = None
    fm = d / "final_metric.json"
    if fm.exists():
        try: metric = json.load(open(fm)).get("primary_metric")
        except Exception: pass
    return {"name": d.name, "path": str(d), "predecessor": pred, "metric": metric}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="runs/_archive/tree.html")
    ap.add_argument("--archive-root", default="runs/_archive")
    args = ap.parse_args()

    root = Path(args.archive_root)
    if not root.exists():
        print("(no archive yet)"); sys.exit(0)

    nodes = [parse_run(d) for d in sorted(root.iterdir()) if d.is_dir()]

    # build tree from predecessor → children
    children = defaultdict(list)
    by_path = {n["path"]: n for n in nodes}
    roots = []
    for n in nodes:
        if n["predecessor"] and n["predecessor"] in by_path:
            children[n["predecessor"]].append(n["path"])
        else:
            roots.append(n["path"])

    def fmt(p, indent=0):
        n = by_path[p]
        m = f"  metric={n['metric']:.3f}" if isinstance(n['metric'], (int,float)) else ""
        out = ["  " * indent + f"- {n['name']}{m}"]
        for c in children.get(p, []):
            out += fmt(c, indent+1)
        return out

    ascii_tree = []
    for r in roots:
        ascii_tree += fmt(r)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    body = "<html><head><meta charset=utf-8><title>run tree</title></head><body>"
    body += "<h1>Run tree</h1><pre>" + html.escape("\n".join(ascii_tree)) + "</pre>"
    body += "</body></html>"
    Path(args.output).write_text(body)
    print("\n".join(ascii_tree))
    print(f"\n→ {args.output}")

if __name__ == "__main__":
    main()
