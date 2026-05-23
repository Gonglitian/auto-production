#!/usr/bin/env python3
"""tools/datalake.py — domain know-how library query/add.

datalake/<domain>/ has 5 files (datasets.yaml, apis.md, glossary.md,
known_pitfalls.md, ref_papers.yaml). This tool greps across or appends.
"""
import argparse, sys
from datetime import datetime
from pathlib import Path

ROOT = Path("datalake")
FILES = ["datasets.yaml", "apis.md", "glossary.md", "known_pitfalls.md", "ref_papers.yaml"]

def init(domain):
    d = ROOT / domain
    d.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        p = d / f
        if not p.exists():
            p.write_text(f"# {domain} — {f}\n")
    print(f"✅ datalake/{domain}/ ready ({len(FILES)} files)")

def query(domain_or_all, term):
    paths = []
    if domain_or_all == "*":
        paths = list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.yaml"))
    else:
        paths = list((ROOT / domain_or_all).glob("*"))
    hits = 0
    for p in paths:
        if not p.is_file(): continue
        for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            if term.lower() in line.lower():
                print(f"{p}:{i}: {line.strip()[:200]}")
                hits += 1
    print(f"\n{hits} hit(s) for '{term}'", file=sys.stderr)

def add(domain, topic, content):
    d = ROOT / domain
    d.mkdir(parents=True, exist_ok=True)
    target = d / ("known_pitfalls.md" if topic == "pitfall" else "glossary.md")
    with open(target, "a") as f:
        f.write(f"\n## {datetime.now().date()} {topic}\n{content}\n")
    print(f"✅ appended to {target}")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").add_argument("--domain", required=True)
    q = sub.add_parser("query"); q.add_argument("term"); q.add_argument("--domain", default="*")
    a = sub.add_parser("add"); a.add_argument("--domain", required=True); a.add_argument("--topic", required=True); a.add_argument("--content", required=True)
    args = ap.parse_args()
    if args.cmd == "init":  init(args.domain)
    elif args.cmd == "query": query(args.domain, args.term)
    elif args.cmd == "add":   add(args.domain, args.topic, args.content)

if __name__ == "__main__":
    main()
