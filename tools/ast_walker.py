#!/usr/bin/env python3
"""tools/ast_walker.py — minimal Python AST static checker for /ast-validate.

Checks: syntax, unresolved Names, signature/callsite arg count mismatch
(intra-file only — cross-file checks are heuristic and noisy).

Emits per-file diff lines to stdout; exit 0 if clean, 1 if any issue found.

History: v2 fixes 4 false-positive classes found in vla3d Stage 5.4 test —
function params, comprehension targets, AnnAssign module consts, kwarg-only
calls (Call.keywords). v1 flagged 30+ FP on a clean stub file.
"""
import argparse, ast, sys
from pathlib import Path

BUILTINS = set(dir(__builtins__)) | {
    # typing-stdlib commonly used without explicit import in type annotations
    "Optional", "Union", "List", "Dict", "Tuple", "Set", "Any", "Callable",
    "Iterator", "Iterable", "Sequence", "Mapping", "Type", "ClassVar",
    "Annotated", "Literal", "Final", "TypeVar", "Generic", "Protocol",
}

class Walker(ast.NodeVisitor):
    def __init__(self, path):
        self.path = path
        self.defs = set()
        self.imports = set()
        self.uses = []                # (name, lineno) Load-context Names only
        self.func_sigs = {}           # name -> (n_required_positional, accepts_kwargs)
        self.calls = []               # (name, lineno, n_positional, n_keyword)
        self._param_names = []        # stack of param-name sets per nested scope
        self._wildcard_imports = []   # `from X import *` modules — disables unresolved check

    # -- imports -----------------------------------------------------------
    def visit_Import(self, node):
        for n in node.names:
            self.imports.add((n.asname or n.name).split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for n in node.names:
            if n.name == "*":
                # `from X import *` — wildcard; can't resolve names statically
                self._wildcard_imports.append(node.module or "?")
            else:
                self.imports.add(n.asname or n.name)
        self.generic_visit(node)

    # -- function / class defs ---------------------------------------------
    def visit_FunctionDef(self, node):
        self.defs.add(node.name)

        a = node.args
        n_pos = len(a.posonlyargs) + len(a.args)
        n_req = n_pos - len(a.defaults)
        accepts_kw = bool(a.vararg or a.kwonlyargs or a.kwarg)
        self.func_sigs[node.name] = (max(n_req, 0), accepts_kw)

        # Fix #1: track parameters as defs WITHIN the function scope.
        # We don't do real lexical scoping (too heavy); instead we add to
        # the global `defs` set for the duration of body traversal.
        param_names = set()
        for arg_list in (a.posonlyargs, a.args, a.kwonlyargs):
            for arg in arg_list:
                param_names.add(arg.arg)
        if a.vararg:
            param_names.add(a.vararg.arg)
        if a.kwarg:
            param_names.add(a.kwarg.arg)

        self._param_names.append(param_names)
        self.defs |= param_names
        try:
            self.generic_visit(node)
        finally:
            self._param_names.pop()
            # Note: we leave param names in self.defs — slight over-permission
            # is preferred over scope leak false positives (see Risks in docstring).

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        param_names = set()
        a = node.args
        for arg_list in (a.posonlyargs, a.args, a.kwonlyargs):
            for arg in arg_list:
                param_names.add(arg.arg)
        if a.vararg: param_names.add(a.vararg.arg)
        if a.kwarg:  param_names.add(a.kwarg.arg)
        self.defs |= param_names
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.defs.add(node.name)
        self.generic_visit(node)

    # -- assignments -------------------------------------------------------
    def visit_Assign(self, node):
        for t in node.targets:
            self._record_targets(t)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self._record_targets(node.target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        # Fix #3: type-annotated assignment (`X: int = 5` at module level was missed in v1)
        if isinstance(node.target, ast.Name):
            self.defs.add(node.target.id)
        self.generic_visit(node)

    def _record_targets(self, t):
        if isinstance(t, ast.Name):
            self.defs.add(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for sub in t.elts:
                self._record_targets(sub)
        elif isinstance(t, ast.Starred):
            self._record_targets(t.value)

    # -- loops / context managers / comprehensions -------------------------
    def visit_For(self, node):
        self._record_targets(node.target)
        self.generic_visit(node)

    visit_AsyncFor = visit_For

    def visit_With(self, node):
        for item in node.items:
            if item.optional_vars:
                self._record_targets(item.optional_vars)
        self.generic_visit(node)

    visit_AsyncWith = visit_With

    def _walk_comprehensions(self, generators):
        # Fix #2: comprehension targets (`[p for p in xs]` flagged `p` in v1)
        for g in generators:
            self._record_targets(g.target)

    def visit_ListComp(self, node):
        self._walk_comprehensions(node.generators)
        self.generic_visit(node)

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_ExceptHandler(self, node):
        if node.name:
            self.defs.add(node.name)
        self.generic_visit(node)

    def visit_Global(self, node):
        for name in node.names:
            self.defs.add(name)

    visit_Nonlocal = visit_Global

    def visit_NamedExpr(self, node):
        # Walrus operator: `(x := expr)` binds x in surrounding scope.
        if isinstance(node.target, ast.Name):
            self.defs.add(node.target.id)
        self.generic_visit(node)

    # -- match statement (Python 3.10+) -----------------------------------
    def visit_Match(self, node):
        for case in node.cases:
            self._collect_pattern_names(case.pattern)
        self.generic_visit(node)

    def _collect_pattern_names(self, pat):
        if pat is None:
            return
        # MatchAs: `case <pat> as x` or `case x` (== MatchAs(None, 'x'))
        if isinstance(pat, ast.MatchAs):
            if pat.name:
                self.defs.add(pat.name)
            self._collect_pattern_names(pat.pattern)
        elif isinstance(pat, ast.MatchStar):
            if pat.name:
                self.defs.add(pat.name)
        elif isinstance(pat, ast.MatchMapping):
            if pat.rest:
                self.defs.add(pat.rest)
            for p in pat.patterns:
                self._collect_pattern_names(p)
        elif isinstance(pat, ast.MatchSequence):
            for p in pat.patterns:
                self._collect_pattern_names(p)
        elif isinstance(pat, ast.MatchOr):
            for p in pat.patterns:
                self._collect_pattern_names(p)
        elif isinstance(pat, ast.MatchClass):
            for p in pat.patterns:
                self._collect_pattern_names(p)
            for p in pat.kwd_patterns:
                self._collect_pattern_names(p)

    # -- uses & calls ------------------------------------------------------
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.uses.append((node.id, node.lineno))

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            # Fix #4: count kwargs too. v1 reported `f(a=1, b=2)` as "0 args".
            n_pos = len(node.args)
            n_kw = len(node.keywords)
            self.calls.append((node.func.id, node.lineno, n_pos, n_kw))
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
    # `from X import *` makes static name-resolution unreliable — skip that
    # check but still do call-arity below.
    if not w._wildcard_imports:
        known = w.defs | w.imports | BUILTINS | {"self", "cls", "_"}
        seen = set()
        for name, lineno in w.uses:
            if name in known or name in seen:
                continue
            if name.startswith("__") and name.endswith("__"):
                continue
            seen.add(name)
            issues.append(f"{path}:{lineno}: unresolved name `{name}`")
    for name, lineno, n_pos, n_kw in w.calls:
        sig = w.func_sigs.get(name)
        if sig is None:
            continue
        n_req, accepts_kw = sig
        # If the def accepts kwargs/varargs we cannot statically check arity.
        if accepts_kw:
            continue
        if n_pos + n_kw < n_req:
            issues.append(
                f"{path}:{lineno}: call {name}({n_pos} pos + {n_kw} kw) but def needs {n_req}"
            )
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
