#!/usr/bin/env python3
"""tools/rebuttal.py — parse reviewer markdown into structured concern list,
emit a draft skeleton with safety-gate placeholders.
"""
import argparse, glob, json, re, sys
from pathlib import Path

CATEGORIES = ["factual-question", "request-for-experiment", "clarification", "subjective-criticism"]

def categorize(text):
    lower = text.lower()
    if any(k in lower for k in ["please add", "we'd like to see", "could you run", "missing"]):
        return "request-for-experiment"
    if any(k in lower for k in ["unclear", "confusing", "ambiguous", "please clarify"]):
        return "clarification"
    if any(k in lower for k in ["seems", "feels", "i suspect", "in my opinion"]):
        return "subjective-criticism"
    return "factual-question"

def parse_review(path):
    text = Path(path).read_text()
    concerns = []
    for i, para in enumerate(re.split(r"\n\s*\n", text)):
        para = para.strip()
        if len(para) < 30: continue
        concerns.append({
            "reviewer_file": str(path),
            "para_idx": i,
            "text": para[:600],
            "category": categorize(para),
        })
    return concerns

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse"); p.add_argument("files", nargs="+"); p.add_argument("--out", default="paper/reviews/parsed.json")
    d = sub.add_parser("draft"); d.add_argument("--char-limit", type=int, default=5000); d.add_argument("--venue", default="ICML")
    args = ap.parse_args()

    if args.cmd == "parse":
        all_concerns = []
        for f in args.files:
            all_concerns += parse_review(f)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(all_concerns, indent=2, ensure_ascii=False))
        print(f"✅ {len(all_concerns)} concern(s) → {args.out}")
        for c in all_concerns[:5]:
            print(f"  - [{c['category']}] {c['text'][:80]}…")

    elif args.cmd == "draft":
        parsed = json.loads(Path("paper/reviews/parsed.json").read_text())
        skel = [f"# Rebuttal draft (target ≤{args.char_limit} chars, venue={args.venue})\n"]
        skel.append("\n## Safety gates (must pass before PASTE_READY emit)")
        skel.append("- [ ] No fabrication: every claim links to paper / code / user-confirmed result")
        skel.append("- [ ] No overpromise: every 'we will add X' user-approved")
        skel.append("- [ ] Full coverage: every concern below has a response\n")
        for i, c in enumerate(parsed, 1):
            skel.append(f"### #{i} [{c['category']}] from {Path(c['reviewer_file']).name}")
            skel.append(f"> {c['text'][:200]}")
            skel.append("**Response**: TBD\n")
        out = Path("paper/rebuttal/draft.md")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(skel))
        print(f"✅ draft skeleton → {out}  ({len(parsed)} concerns)")

if __name__ == "__main__":
    main()
