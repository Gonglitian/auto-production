#!/usr/bin/env python3
"""tools/task_notes_yaml.py — init/verify task_notes.yaml for a phase."""
import argparse, re, shutil, sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET = Path("task_notes.yaml")
TEMPLATE = REPO / "templates" / "task_notes.yaml"
REQUIRED_NONEMPTY = ["phase", "dataset_loader_code"]

def init():
    if TARGET.exists():
        print(f"⚠️  {TARGET} exists — not overwriting")
        return
    shutil.copy(TEMPLATE, TARGET)
    print(f"✅ wrote {TARGET} — edit before /task-notes-yaml --verify")

def verify():
    if not TARGET.exists():
        sys.exit("❌ task_notes.yaml not found — run --init first")
    text = TARGET.read_text()
    errors = []
    for k in REQUIRED_NONEMPTY:
        m = re.search(rf"^{k}\s*:\s*(.*)$", text, re.MULTILINE)
        if not m or not m.group(1).strip().strip('"').strip("'"):
            errors.append(f"empty: {k}")
    m = re.search(r"^deadline\s*:\s*(.+)$", text, re.MULTILINE)
    if m:
        try:
            d = datetime.fromisoformat(m.group(1).strip().strip('"').strip("'"))
            if d < datetime.now(d.tzinfo if d.tzinfo else None):
                errors.append("deadline is in the past")
        except Exception:
            errors.append("deadline not ISO-8601 parseable")
    if errors:
        print("❌ task_notes.yaml invalid:")
        for e in errors: print(f"   - {e}")
        sys.exit(1)
    print("✅ task_notes.yaml valid")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["init", "verify"])
    args = ap.parse_args()
    {"init": init, "verify": verify}[args.cmd]()

if __name__ == "__main__":
    main()
