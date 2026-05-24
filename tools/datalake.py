#!/usr/bin/env python3
"""tools/datalake.py — domain know-how library query/add.

datalake/<domain>/ has 5 files (datasets.yaml, apis.md, glossary.md,
known_pitfalls.md, ref_papers.yaml). This tool greps across, appends, and
seeds from a repo-wide template if one exists.

If `templates/datalake/<domain>/` exists in the auto-production repo, /init
copies its content into your project's datalake/<domain>/ (preserving
existing files). Otherwise it writes empty stubs.
"""
import argparse, os, shutil, sys
from datetime import datetime
from pathlib import Path

ROOT = Path("datalake")
FILES = ["datasets.yaml", "apis.md", "glossary.md", "known_pitfalls.md", "ref_papers.yaml"]


def _find_template(domain):
    """Return path to templates/datalake/<domain>/ if it exists."""
    candidates = []
    repo = os.environ.get("AUTO_PRODUCTION_REPO")
    if repo:
        candidates.append(Path(repo) / "templates" / "datalake" / domain)
    # also check relative to this script (dev mode)
    candidates.append(Path(__file__).resolve().parent.parent / "templates" / "datalake" / domain)
    for c in candidates:
        if c.is_dir():
            return c
    return None


def init(domain):
    d = ROOT / domain
    d.mkdir(parents=True, exist_ok=True)
    template_dir = _find_template(domain)

    n_seeded = 0
    if template_dir:
        for src in template_dir.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(template_dir)
            dst = d / rel
            if dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            n_seeded += 1

    # ensure all 5 canonical files exist (write empty stubs for any missing)
    n_stubs = 0
    for f in FILES:
        p = d / f
        if not p.exists():
            p.write_text(f"# {domain} — {f}\n")
            n_stubs += 1

    msg = f"✅ datalake/{domain}/ ready"
    if template_dir:
        msg += f" (seeded {n_seeded} from {template_dir.relative_to(template_dir.parent.parent.parent)}, +{n_stubs} stubs)"
    else:
        msg += f" ({n_stubs} stubs; no template found for domain '{domain}')"
    print(msg)


def query(domain_or_all, term):
    paths = []
    if domain_or_all == "*":
        paths = list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.yaml"))
    else:
        paths = list((ROOT / domain_or_all).rglob("*"))
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


def list_domains():
    if not ROOT.exists():
        print("(no datalake/ in this project)"); return
    for d in sorted(ROOT.iterdir()):
        if d.is_dir():
            n = sum(1 for _ in d.rglob("*") if _.is_file())
            print(f"  {d.name:20s} {n} file(s)")
    print()
    # also list available templates
    repo = os.environ.get("AUTO_PRODUCTION_REPO") or str(Path(__file__).resolve().parent.parent)
    tmpl_root = Path(repo) / "templates" / "datalake"
    if tmpl_root.exists():
        print("Available domain templates:")
        for d in sorted(tmpl_root.iterdir()):
            if d.is_dir():
                print(f"  {d.name} (run /datalake init --domain {d.name} to seed)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").add_argument("--domain", required=True)
    q = sub.add_parser("query"); q.add_argument("term"); q.add_argument("--domain", default="*")
    a = sub.add_parser("add"); a.add_argument("--domain", required=True); a.add_argument("--topic", required=True); a.add_argument("--content", required=True)
    sub.add_parser("list")
    args = ap.parse_args()
    if args.cmd == "init":  init(args.domain)
    elif args.cmd == "query": query(args.domain, args.term)
    elif args.cmd == "add":   add(args.domain, args.topic, args.content)
    elif args.cmd == "list":  list_domains()


if __name__ == "__main__":
    main()
