#!/usr/bin/env python3
"""tools/auto_version.py — snapshot a run dir to runs/_archive, emit 3-part
PROMPT.md (CONTINUATION / PRIOR PLAN / DELTA) for the next run.
"""
import argparse, json, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

def sh(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""

def archive(src):
    src = Path(src)
    if not src.exists(): sys.exit(f"❌ {src} not found")
    ts = datetime.now().strftime("%y%m%d_%H%M")
    dest = Path("runs/_archive") / f"{src.name}_{ts}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), dest)
    return dest

def emit_prompt(archived, label, delta_summary):
    cont, plan = "(see archived run logs)", "(see archived sprint_contract.yaml)"
    archive_contract = archived / "sprint_contract.yaml"
    if archive_contract.exists():
        plan = archive_contract.read_text()[:500]
    metric_summary = ""
    fm = archived / "final_metric.json"
    if fm.exists():
        try:
            metric_summary = json.dumps(json.load(open(fm)), indent=2)[:300]
        except Exception:
            pass
    body = (
        f"# Next-run prompt for {label}\n"
        f"Generated: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Predecessor: {archived}\n"
        f"Git: {sh('git', 'rev-parse', '--short', 'HEAD')}\n\n"
        f"# CONTINUATION\n{metric_summary or cont}\n\n"
        f"# PRIOR PLAN\n```\n{plan}\n```\n\n"
        f"# DELTA\n{delta_summary or '(fill in: what this run changes vs predecessor)'}\n"
    )
    out = Path("runs") / label / "PROMPT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-of", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--delta", default="")
    args = ap.parse_args()
    archived = archive(args.snapshot_of)
    prompt = emit_prompt(archived, args.label, args.delta)
    print(f"✅ archived → {archived}")
    print(f"✅ next-run prompt → {prompt}")

if __name__ == "__main__":
    main()
