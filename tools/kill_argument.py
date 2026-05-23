#!/usr/bin/env python3
"""tools/kill_argument.py — emit adversarial-defense skeleton for a claim.

5 default attack angles: stat-significance / weak-baseline / generalization /
ablation-missing / theoretical-soundness. Agent fills the per-angle defense.
"""
import argparse, re, sys
from pathlib import Path

ATTACK_ANGLES = [
    ("Statistical significance",
     "Is the improvement larger than seed-variance? Bootstrap CI overlap?"),
    ("Weak baseline",
     "Is the comparison fair? Newer SOTA exists? Same compute budget?"),
    ("Generalization",
     "Does it hold beyond the tested benchmarks/domains? Cherry-picking?"),
    ("Ablation gaps",
     "What component drives the gain? Are all design choices ablated?"),
    ("Theoretical soundness",
     "Does the proof hold under the stated assumptions? Edge cases?"),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("claim", help="claim text or path to .md/.tex file")
    ap.add_argument("--threats", type=int, default=5)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    claim = Path(args.claim).read_text() if Path(args.claim).exists() else args.claim
    safe_id = re.sub(r"\W+", "_", claim[:40]).strip("_") or "claim"
    out = Path(args.out or f"paper/defenses/{safe_id}.md")

    body = [f"# Adversarial defense for claim", f"```\n{claim.strip()[:500]}\n```\n"]
    body.append(f"## {args.threats} attack angles\n")
    for i, (angle, hint) in enumerate(ATTACK_ANGLES[:args.threats], 1):
        body.append(f"### {i}. {angle}")
        body.append(f"_Hint: {hint}_")
        body.append("**Attack**: TBD")
        body.append("**Defense**: TBD")
        body.append("**Evidence pointer**: TBD (paper section / code path / data row)\n")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(body))
    print(f"✅ defense skeleton → {out}")
    print("→ fill Attack/Defense/Evidence; feed to /rebuttal as ammunition")

if __name__ == "__main__":
    main()
