#!/usr/bin/env python3
"""tools/findings_render.py — manage findings.yaml + render SVG dependency graph.

Subcommands: add (append entry), render (SVG to findings_map.svg + sync findings.md tail).
"""
import argparse, sys, uuid
from datetime import datetime
from pathlib import Path

LEDGER = Path("findings.yaml")
LEGACY = Path("findings.md")
SVG_OUT = Path("findings_map.svg")

def parse_yaml_list(text):
    # minimal: each entry starts with "- id:"
    items, cur = [], None
    for line in text.splitlines():
        if line.startswith("- "):
            if cur: items.append(cur)
            cur = {}
            k, _, v = line[2:].partition(":")
            cur[k.strip()] = v.strip()
        elif ":" in line and cur is not None and line.startswith("  "):
            k, _, v = line.partition(":")
            cur[k.strip()] = v.strip()
    if cur: items.append(cur)
    return items

def serialize(items):
    out = []
    for e in items:
        out.append(f"- id: {e['id']}")
        for k in ("date","text","source_run","evidence","type","status"):
            if k in e:
                out.append(f"  {k}: {e[k]}")
        if e.get("depends_on"):
            out.append(f"  depends_on: {e['depends_on']}")
    return "\n".join(out) + "\n"

def add(text, depends_on, type_, source_run):
    entries = parse_yaml_list(LEDGER.read_text()) if LEDGER.exists() else []
    fid = f"f{len(entries)+1:03d}"
    entries.append({
        "id": fid, "date": datetime.now().strftime("%Y-%m-%d"),
        "text": text, "source_run": source_run or "",
        "depends_on": "[" + ",".join(depends_on) + "]" if depends_on else "",
        "type": type_, "status": "open",
    })
    LEDGER.write_text(serialize(entries))
    # append legacy markdown tail for backward-compat
    with open(LEGACY, "a") as f:
        f.write(f"\n## {entries[-1]['date']} [{fid}] ({type_})\n{text}\n")
    print(f"✅ added {fid}")

def render():
    if not LEDGER.exists(): sys.exit("no findings.yaml yet")
    entries = parse_yaml_list(LEDGER.read_text())
    # bare-minimum SVG (one row per entry, arrows = depends_on)
    H = 60; W = 800
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H*len(entries)+40}">',
           "<style>text{font:13px sans-serif} .obs{fill:#cfe} .hyp{fill:#fec} .con{fill:#cef}</style>"]
    pos = {}
    for i, e in enumerate(entries):
        y = 20 + i*H; pos[e["id"]] = (W/2, y+25)
        cls = {"observation":"obs","hypothesis":"hyp","conclusion":"con"}.get(e.get("type",""), "obs")
        svg.append(f'<rect x="20" y="{y}" width="{W-40}" height="40" class="{cls}" stroke="#888"/>')
        svg.append(f'<text x="30" y="{y+25}">{e["id"]}: {e.get("text","")[:80]}</text>')
    for e in entries:
        for dep in (e.get("depends_on") or "").strip("[]").split(","):
            dep = dep.strip()
            if dep in pos:
                x1, y1 = pos[dep]; x2, y2 = pos[e["id"]]
                svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2-12}" stroke="#888" marker-end="url(#a)"/>')
    svg.append("</svg>")
    SVG_OUT.write_text("\n".join(svg))
    print(f"✅ wrote {SVG_OUT}")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("text"); a.add_argument("--depends-on", default="")
    a.add_argument("--type", default="observation", choices=["observation","hypothesis","conclusion"])
    a.add_argument("--source-run", default="")
    sub.add_parser("render")
    args = ap.parse_args()
    if args.cmd == "add":
        deps = [d.strip() for d in args.depends_on.split(",") if d.strip()]
        add(args.text, deps, args.type, args.source_run)
    elif args.cmd == "render":
        render()

if __name__ == "__main__":
    main()
