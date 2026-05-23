#!/usr/bin/env python3
"""tools/arch_plan.py — extract a rough dependency graph of given files.

Build "who-imports-whom" + "who-calls-which-function" maps, emit a
markdown plan stub the user/agent can fill in for /arch-plan.

Pure stdlib (ast + Path).
"""
import argparse, ast, json, re, sys
from collections import defaultdict
from pathlib import Path

def module_path(p):
    return str(Path(p).with_suffix("")).replace("/", ".")

def imports_in(path):
    try:
        tree = ast.parse(Path(path).read_text(errors="ignore"))
    except Exception:
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names: out.add(a.name)
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module)
    return out

def defs_in(path):
    try:
        tree = ast.parse(Path(path).read_text(errors="ignore"))
    except Exception:
        return set()
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", required=True, help="comma-separated paths or glob")
    ap.add_argument("--goal", default="")
    ap.add_argument("--out", default=".auto-production/arch_plan.md")
    args = ap.parse_args()

    files = []
    for spec in args.files.split(","):
        spec = spec.strip()
        if "*" in spec:
            files += [str(p) for p in Path(".").rglob(spec)]
        elif Path(spec).is_file():
            files.append(spec)

    mods = {f: module_path(f) for f in files}
    file_imports = {f: imports_in(f) for f in files}
    file_defs = {f: defs_in(f) for f in files}

    # who-imports-whom intra-set
    edges = []
    for f, imps in file_imports.items():
        for other in files:
            if other == f: continue
            if mods[other] in imps or any(mods[other].endswith("." + i) for i in imps):
                edges.append((f, other))

    out = [f"# Arch plan: {args.goal or 'unnamed'}\n",
           f"Files in scope ({len(files)}):\n"]
    for f in files:
        out.append(f"- `{f}` — defs: {sorted(file_defs[f])[:5]}…")
    out.append("\n## Dependency edges (intra-set imports)\n")
    if edges:
        for a, b in edges:
            out.append(f"- `{a}` → `{b}`")
    else:
        out.append("- (none)")
    out.append("""
## Planned changes (fill before editing)

For each file, list:
- File: <path>:<line>
- Change: <what>
- Affected callers: <list>

## Verify after change
- [ ] /ast-validate clean
- [ ] /smoke-test pass
- [ ] no new files exceed /simplify-gate soft limit
""")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(out))
    print(f"✅ arch plan stub → {args.out}")
    print(f"   files: {len(files)}, edges: {len(edges)}")

if __name__ == "__main__":
    main()
