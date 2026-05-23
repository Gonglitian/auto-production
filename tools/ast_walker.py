#!/usr/bin/env python3
"""tools/ast_walker.py — minimal Python AST static checker for /ast-validate.

Checks: syntax, unresolved Names, signature/callsite arg count mismatch
(intra-file only — cross-file checks are heuristic and noisy).

Emits per-file diff lines to stdout; exit 0 if clean, 1 if any issue found.
"""
import argparse, ast, sys
from pathlib import Path

BUILTINS = set(dir(__builtins__))

class Walker(ast.NodeVisitor):
    def __init__(self, path):
        self.path = path
        self.defs = set()
        self.imports = set()
        self.uses = []
        self.func_sigs = {}      # name -> n_required_args
        self.calls = []          # (name, lineno, n_args)

    def visit_Import(self, node):
        for n in node.names:
            self.imports.add((n.asname or n.name).split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for n in node.names:
            self.imports.add(n.asname or n.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.defs.add(node.name)
        n_req = sum(1 for a in node.args.args) - len(node.args.defaults)
        self.func_sigs[node.name] = max(n_req, 0)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.defs.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        for t in node.targets:
            if isinstance(t, ast.Name):
                self.defs.add(t.id)
        self.generic_visit(node)

    def visit_For(self, node):
        if isinstance(node.target, ast.Name):
            self.defs.add(node.target.id)
        self.generic_visit(node)

    def visit_With(self, node):
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self.defs.add(item.optional_vars.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.uses.append((node.id, node.lineno))

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append((node.func.id, node.lineno, len(node.args)))
        self.generic_visit(node)

def check_file(path):
    issues = []
    src = Path(path).read_text(errors="ignore")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return [f"{path}:{e.lineno}: SyntaxError: {e.msg}"]
    w = Walker(path)
    w.visit(tree)
    known = w.defs | w.imports | BUILTINS | {"self", "cls"}
    seen = set()
    for name, lineno in w.uses:
        if name in known or name in seen:
            continue
        seen.add(name)
        issues.append(f"{path}:{lineno}: unresolved name `{name}`")
    for name, lineno, n_args in w.calls:
        sig = w.func_sigs.get(name)
        if sig is not None and n_args < sig:
            issues.append(f"{path}:{lineno}: call {name}({n_args} args) but def needs {sig}")
    return issues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    all_issues = []
    for f in args.files:
        all_issues += check_file(f)
    for line in all_issues:
        print(line)
    sys.exit(0 if not all_issues else 1)

if __name__ == "__main__":
    main()
