#!/usr/bin/env python3
"""tools/corpus_schema.py — manage corpus/literature_corpus.yaml.

Subcommands: add (compute sha256+size, append entry), list (tabular), verify
(recompute sha256, diff with manifest).
"""
import argparse, hashlib, json, os, subprocess, sys
from datetime import datetime
from pathlib import Path

LEDGER = Path("corpus/literature_corpus.yaml")

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def load_ledger():
    if not LEDGER.exists(): return []
    text = LEDGER.read_text()
    # naive YAML list parser (matches templates/sprint_contract.yaml style)
    entries, cur = [], None
    for line in text.splitlines():
        if line.startswith("- "):
            if cur: entries.append(cur)
            cur = {}
            k, _, v = line[2:].partition(":")
            cur[k.strip()] = v.strip()
        elif ":" in line and cur is not None and line.startswith("  "):
            k, _, v = line.partition(":")
            cur[k.strip()] = v.strip()
    if cur: entries.append(cur)
    return entries

def save_ledger(entries):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for e in entries:
        out.append(f"- id: {e.get('id')}")
        for k, v in e.items():
            if k == "id": continue
            out.append(f"  {k}: {v}")
    LEDGER.write_text("\n".join(out) + "\n")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("path"); a.add_argument("--id", required=True)
    a.add_argument("--type", default="dataset"); a.add_argument("--url", required=True)
    a.add_argument("--license", default="unknown"); a.add_argument("--source-paper", default="")
    sub.add_parser("list")
    sub.add_parser("verify")
    args = ap.parse_args()

    entries = load_ledger()

    if args.cmd == "add":
        path = Path(args.path)
        if not path.exists(): sys.exit(f"❌ {path} not found")
        sz = path.stat().st_size
        sha = sha256_of(path) if path.is_file() else "(dir)"
        entries.append({
            "id": args.id, "type": args.type,
            "obtained_via": args.url,
            "obtained_at": datetime.now().isoformat(timespec="seconds"),
            "local_path": str(path),
            "size_bytes": str(sz), "sha256": sha,
            "license": args.license,
            "source_paper": args.source_paper or "",
        })
        save_ledger(entries)
        print(f"✅ added {args.id} (sha256={sha[:12]}…)")

    elif args.cmd == "list":
        print(f"{'id':20s} {'type':12s} {'size':>10s} {'sha':14s} path")
        for e in entries:
            sz = int(e.get("size_bytes") or 0)
            print(f"{e.get('id',''):20s} {e.get('type',''):12s} {sz:>10d} {(e.get('sha256') or '')[:12]:14s} {e.get('local_path','')}")

    elif args.cmd == "verify":
        fail = 0
        for e in entries:
            p = Path(e.get("local_path") or "")
            if not p.exists():
                print(f"❌ missing: {e['id']}  {p}"); fail += 1; continue
            if p.is_file():
                cur = sha256_of(p)
                if cur != e.get("sha256"):
                    print(f"❌ corrupt: {e['id']}  expected {e['sha256'][:12]} got {cur[:12]}"); fail += 1
                else:
                    print(f"✓ {e['id']}")
        sys.exit(0 if not fail else 1)

if __name__ == "__main__":
    main()
