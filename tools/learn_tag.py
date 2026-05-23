#!/usr/bin/env python3
"""tools/learn_tag.py — route [LEARN:tier] tags from agent output into
MEMORY.md tier sections.

Hook mode: reads agent output on stdin, appends each `[LEARN:tier] text`
match to MEMORY.md under `## tier:` heading. Manual mode: --tier X --content Y.
"""
import argparse, re, sys
from datetime import datetime
from pathlib import Path

MEM = Path("MEMORY.md")
TIERS = ["method", "code", "notation", "tooling", "pitfall", "convention"]

def ensure_section(text, tier):
    h = f"## {tier}\n"
    if h not in text:
        text += f"\n{h}\n"
    return text

def append(tier, content):
    text = MEM.read_text() if MEM.exists() else "# MEMORY.md\n"
    text = ensure_section(text, tier)
    # split by tier sections, append to matching one
    parts = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    out = []
    appended = False
    for part in parts:
        if part.startswith(f"## {tier}\n") and not appended:
            part = part.rstrip() + f"\n- ({datetime.now().date()}) {content.strip()}\n"
            appended = True
        out.append(part)
    MEM.write_text("".join(out))
    print(f"✅ +1 entry to MEMORY.md/{tier}")

def scan(text):
    matches = re.findall(r"\[LEARN:(\w+)\]\s*(.+?)(?=\n\n|\n\[LEARN:|\Z)", text, re.DOTALL)
    n = 0
    for tier, content in matches:
        if tier.lower() in TIERS:
            append(tier.lower(), content)
            n += 1
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-input", action="store_true")
    ap.add_argument("--tier", choices=TIERS)
    ap.add_argument("--content")
    args = ap.parse_args()

    if args.scan_input:
        n = scan(sys.stdin.read())
        print(f"scanned: {n} tag(s) routed")
    elif args.tier and args.content:
        append(args.tier, args.content)
    else:
        sys.exit("usage: --scan-input  OR  --tier X --content 'Y'")

if __name__ == "__main__":
    main()
