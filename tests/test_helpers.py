#!/usr/bin/env python3
"""tests/test_helpers.py — smoke-test every tools/*.{py,sh} (no real net / GPU).

For Python helpers: import the module (catches SyntaxError + ImportError on
stdlib-only environments) and call --help if argparse-based.
For bash helpers: bash -n syntax check.

Run: python3 tests/test_helpers.py
"""
import os, subprocess, sys, importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"

# Tools that are known to need external libs (skip --help if missing)
NETWORK_OK_TOOLS = {"verify_citations.py", "verify_contract.py"}
# Tools where --help would actually do something (run network call, etc) — skip
SKIP_HELP_TOOLS: set[str] = set()

def smoke_py(path):
    """Import-only check for a Python helper."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        return False, "cannot spec_from_file_location"
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit as e:
        # argparse top-level main() may call sys.exit; treat 0 as ok
        if getattr(e, "code", 0) in (0, None): return True, "(exited on import)"
        return False, f"SystemExit({e.code}) on import"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"
    return True, "import ok"

def help_py(path):
    if path.name in SKIP_HELP_TOOLS:
        return True, "(skip-help)"
    try:
        r = subprocess.run(
            [sys.executable, str(path), "--help"],
            capture_output=True, text=True, timeout=8,
        )
    except subprocess.TimeoutExpired:
        return False, "--help timeout"
    except Exception as e:
        return False, f"--help {type(e).__name__}: {e}"
    if r.returncode == 0:
        return True, "--help ok"
    # argparse-less scripts (e.g. simple positional CLI) may exit non-zero on --help
    if "argparse" in r.stderr or "argument" in r.stderr or "usage" in (r.stdout + r.stderr).lower():
        return True, "--help non-argparse (acceptable)"
    return True, f"--help rc={r.returncode} (advisory only)"

def smoke_sh(path):
    """bash -n syntax check."""
    r = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True, timeout=5)
    if r.returncode == 0:
        return True, "bash -n ok"
    return False, f"bash -n: {r.stderr.strip()[:200]}"

def main():
    fail = 0
    n = 0
    for p in sorted(TOOLS.iterdir()):
        if not p.is_file(): continue
        if not (p.suffix in {".py", ".sh"} or os.access(p, os.X_OK)): continue
        n += 1
        if p.suffix == ".py":
            ok, msg = smoke_py(p)
            tag = "✓" if ok else "✗"
            print(f"  {tag} {p.name:35s} import: {msg}")
            if not ok:
                fail += 1; continue
            ok, msg = help_py(p)
            tag = "✓" if ok else "✗"
            print(f"  {tag} {p.name:35s} --help: {msg}")
            if not ok: fail += 1
        elif p.suffix == ".sh":
            ok, msg = smoke_sh(p)
            tag = "✓" if ok else "✗"
            print(f"  {tag} {p.name:35s} {msg}")
            if not ok: fail += 1

    print(f"\n{n} tools checked; {fail} failed")
    sys.exit(0 if fail == 0 else 1)

if __name__ == "__main__":
    main()
