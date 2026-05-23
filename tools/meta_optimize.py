#!/usr/bin/env python3
"""tools/meta_optimize.py — failure-log → patch-proposal.

Skeleton: collect signals from multiple sources, naive cluster, emit patch
proposal markdown stubs. The deep root-cause analysis is intended to be
done by an LLM sub-agent reading these stubs; this script only prepares
the input bundle.
"""
import argparse, json, re, subprocess
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

USER_PUSHBACK_RE = re.compile(r"(?:不对|你又|stop|wrong|nope|no that's)", re.IGNORECASE)

def parse_since(s):
    if s.endswith("d"):
        return timedelta(days=int(s[:-1]))
    if s.endswith("h"):
        return timedelta(hours=int(s[:-1]))
    return timedelta(days=7)

def collect_pushbacks(since_dt):
    """Scan Claude Code project jsonl for user-pushback messages."""
    out = []
    base = Path.home() / ".claude" / "projects"
    if not base.exists():
        return out
    for jl in base.rglob("*.jsonl"):
        if jl.stat().st_mtime < since_dt.timestamp():
            continue
        try:
            for line in jl.read_text(errors="ignore").splitlines():
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("type") != "user":
                    continue
                msg = d.get("message", {})
                content = msg.get("content", "")
                text = content if isinstance(content, str) else "".join(
                    b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
                )
                if USER_PUSHBACK_RE.search(text):
                    out.append({"src": "jsonl", "file": str(jl), "ts": d.get("timestamp"), "text": text[:300]})
        except Exception:
            continue
    return out

def collect_promises(promise_json):
    p = Path(promise_json)
    if not p.exists():
        return []
    d = json.loads(p.read_text())
    return [{"src": "promise_unfulfilled", "text": x["text"]} for x in d.get("open", []) if "turn" in x]

def collect_audits(audit_dir):
    out = []
    d = Path(audit_dir)
    if not d.exists():
        return out
    for f in d.glob("*_diff.json"):
        out.append({"src": "audit_fail", "file": str(f), "diff": f.read_text()[:1000]})
    return out

def collect_git_reverts():
    try:
        log = subprocess.run(
            ["git", "log", "--since=14.days.ago", "--grep=Revert", "--oneline"],
            capture_output=True, text=True, timeout=10
        ).stdout
        return [{"src": "git_revert", "line": l} for l in log.splitlines() if l.strip()]
    except Exception:
        return []

def naive_cluster(signals):
    """Cluster by lowercased first 5 tokens — heuristic, good enough for v0."""
    buckets = {}
    for s in signals:
        text = (s.get("text") or s.get("diff") or s.get("line") or "").lower()
        key = " ".join(text.split()[:5]) or "(empty)"
        buckets.setdefault(key, []).append(s)
    return sorted(buckets.values(), key=len, reverse=True)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--since", default="7d")
    c.add_argument("--out", default=".auto-production/meta_opt")
    c.add_argument("--promise", default="promise.json")
    c.add_argument("--audit", default=".auto-production/audit")
    args = ap.parse_args()

    if args.cmd == "collect":
        since_dt = datetime.now() - parse_since(args.since)
        signals = []
        signals += collect_pushbacks(since_dt)
        signals += collect_promises(args.promise)
        signals += collect_audits(args.audit)
        signals += collect_git_reverts()

        clusters = naive_cluster(signals)
        big = [c for c in clusters if len(c) >= 3]

        out = Path(args.out) / datetime.now().strftime("%Y-%m-%d")
        out.mkdir(parents=True, exist_ok=True)
        (out / "signals.json").write_text(json.dumps(signals, ensure_ascii=False, indent=2, default=str))
        (out / "clusters.json").write_text(json.dumps(clusters, ensure_ascii=False, indent=2, default=str))

        for i, cl in enumerate(big, 1):
            stub = [
                f"# Patch proposal #{i}",
                f"\nFrequency: {len(cl)} signals in window",
                "\n## Examples\n",
            ] + [f"- ({s.get('src')}) {(s.get('text') or s.get('diff') or s.get('line') or '')[:200]}" for s in cl[:3]]
            stub += [
                "\n## Hypothesis\n",
                "(fill in via LLM sub-agent reading the cluster)\n",
                "\n## Proposed patch target\n",
                "skills/<which-skill>/SKILL.md @ <which-phase>\n",
            ]
            (out / f"patch_{i:02d}.md").write_text("\n".join(stub))
        print(f"✅ collected {len(signals)} signals → {len(big)} clusters ≥3 → {out}")

if __name__ == "__main__":
    main()
