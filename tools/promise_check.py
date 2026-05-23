#!/usr/bin/env python3
"""tools/promise_check.py — Agent promise ledger.

Scan agent stdout for promise-class phrases, write to promise.json. List open,
close by id, send reminders for overdue promises. Pure stdlib only.
"""
import argparse, json, re, sys, uuid
from datetime import datetime
from pathlib import Path

PROMISE_PATTERNS = [
    r"我会(在.+?)?(?:立即|稍后|接下来|完成.{0,8}?后)?(?:做|跑|改|写|加|检查|修)",
    r"下一步.{0,20}?(做|跑|改|写|加|检查|修)",
    r"先.{0,15}?再.{0,15}?",
    r"等.{0,15}?(完|完成|结束).{0,5}?我会",
    r"I('?ll| will)\s+(do|run|fix|write|check|add|update|patch|verify)",
    r"next step (is|will be|:)",
    r"after.+?I('?ll| will)",
    r"let me .+?(then|after)",
]
AUTO_CLOSE_KEYWORDS = ["完成", "已搞定", "已修", "done", "fixed", "完成了", "patched", "verified"]
REMINDER_AFTER_TURNS = 5

def now():
    return datetime.now().isoformat(timespec="seconds")

def load_ledger(path):
    p = Path(path)
    if not p.exists():
        return {"open": [], "closed": []}
    return json.loads(p.read_text())

def save_ledger(path, ledger):
    Path(path).write_text(json.dumps(ledger, ensure_ascii=False, indent=2))

def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[。.!?！？\n])\s*", text) if s.strip()]

def scan(text, ledger, turn):
    added = 0
    for sent in split_sentences(text):
        for pat in PROMISE_PATTERNS:
            if re.search(pat, sent, re.IGNORECASE):
                if any(p["text"] == sent for p in ledger["open"]):
                    break
                ledger["open"].append({
                    "id": uuid.uuid4().hex[:8],
                    "text": sent[:200],
                    "said_at": now(),
                    "turn": turn,
                    "pattern_matched": pat,
                })
                added += 1
                break
        for kw in AUTO_CLOSE_KEYWORDS:
            if kw in sent.lower():
                close_matching(ledger, hint=sent, turn=turn)
                break
    return added

def close_matching(ledger, hint=None, idx=None, turn=0):
    if idx:
        keep = [p for p in ledger["open"] if p["id"] != idx]
        moved = [p for p in ledger["open"] if p["id"] == idx]
    else:
        keep, moved = [], []
        for p in ledger["open"]:
            kw_in_hint = any(k in (hint or "") for k in p["text"].split()[:3])
            if kw_in_hint:
                moved.append(p)
            else:
                keep.append(p)
    for m in moved:
        m["closed_at"] = now()
        m["fulfilled_by_turn"] = turn
        ledger["closed"].append(m)
    ledger["open"] = keep

def list_open(ledger, current_turn):
    if not ledger["open"]:
        print("✅ no open promises")
        return
    for p in ledger["open"]:
        age = current_turn - p.get("turn", 0)
        flag = " 🔔OVERDUE" if age >= REMINDER_AFTER_TURNS else ""
        print(f"⏳ {p['id']}: \"{p['text'][:80]}\"  ({age} turns ago{flag})")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan"); s.add_argument("--ledger", default="promise.json"); s.add_argument("--turn", type=int, default=0)
    l = sub.add_parser("list-open"); l.add_argument("--ledger", default="promise.json"); l.add_argument("--turn", type=int, default=999999)
    c = sub.add_parser("close"); c.add_argument("--ledger", default="promise.json"); c.add_argument("--id", required=True); c.add_argument("--turn", type=int, default=0)

    args = ap.parse_args()
    ledger = load_ledger(args.ledger)

    if args.cmd == "scan":
        text = sys.stdin.read()
        added = scan(text, ledger, args.turn)
        save_ledger(args.ledger, ledger)
        print(f"+{added} promise(s) tracked")
    elif args.cmd == "list-open":
        list_open(ledger, args.turn)
    elif args.cmd == "close":
        close_matching(ledger, idx=args.id, turn=args.turn)
        save_ledger(args.ledger, ledger)
        print(f"closed {args.id}")

if __name__ == "__main__":
    main()
