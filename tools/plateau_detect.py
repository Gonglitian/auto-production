#!/usr/bin/env python3
"""tools/plateau_detect.py — detect metric plateau from decisions.jsonl,
suggest PIVOT if N consecutive REFINEs have <rel_tol delta.
"""
import argparse, json, sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default="decisions.jsonl")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--rel-tol", type=float, default=0.01)
    args = ap.parse_args()

    p = Path(args.ledger)
    if not p.exists():
        print("ℹ️  no decisions.jsonl yet"); sys.exit(0)

    lines = [l for l in p.read_text().splitlines() if l.strip()]
    hist = []
    for l in lines[-args.n:]:
        try:
            hist.append(json.loads(l))
        except Exception:
            pass

    if len(hist) < args.n:
        print(f"ℹ️  only {len(hist)} decisions, need {args.n} to detect plateau")
        sys.exit(0)

    metrics = [h.get("metric") for h in hist if h.get("metric") is not None]
    if len(metrics) < args.n:
        print("ℹ️  some decisions have no metric — cannot plateau-check")
        sys.exit(0)

    base = metrics[0] or 1e-9
    deltas = [(metrics[i+1] - metrics[i]) / abs(base) for i in range(len(metrics)-1)]
    all_refine = all(h.get("user_decision") == "REFINE" for h in hist)
    plateau = all(abs(d) < args.rel_tol for d in deltas)

    if plateau and all_refine:
        print("⚠️  PLATEAU detected:")
        for i, (h, d) in enumerate(zip(hist[1:], deltas), 1):
            print(f"   round {i}: metric={metrics[i]:.4f}  delta={d*100:+.2f}%  decision={h.get('user_decision')}")
        print(f"\n→ recommend PIVOT (last {args.n} REFINEs all < {args.rel_tol*100:.1f}% delta)")
        Path(".auto-production").mkdir(exist_ok=True)
        with open(".auto-production/plateau_alerts.jsonl", "a") as f:
            f.write(json.dumps({"detected_at": __import__("datetime").datetime.now().isoformat(),
                                "n": args.n, "deltas": deltas}) + "\n")
        sys.exit(2)   # special exit: plateau detected
    print(f"✓ no plateau (max |delta| = {max(abs(d) for d in deltas)*100:.2f}%)")

if __name__ == "__main__":
    main()
