#!/usr/bin/env python3
"""tools/storm_perspective.py — Search Semantic Scholar for K similar papers,
extract a one-line "angle" per paper to seed perspective-guided questions.

Pure stdlib. Outputs idea-stage/perspectives.json.
"""
import argparse, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"
UA = "auto-production-storm/0.1"

def search(query, k=8):
    url = f"{S2_API}?{urllib.parse.urlencode({'query':query,'limit':k*3,'fields':'title,abstract,year,citationCount,authors,externalIds'})}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"⚠️  S2 query failed: {e}", file=sys.stderr)
        return []
    # sort by citation count, dedupe by title
    seen, out = set(), []
    for p in sorted(data.get("data", []), key=lambda x: -(x.get("citationCount") or 0)):
        t = (p.get("title") or "").strip().lower()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(p)
        if len(out) >= k:
            break
    return out

ANGLE_HEURISTICS = [
    ("constraint",          "frames as constraint-satisfaction"),
    ("bandit",              "frames as bandit/online-learning"),
    ("distillation",        "frames as distillation"),
    ("RL",                  "frames as reinforcement learning"),
    ("transformer",         "frames as sequence modeling"),
    ("diffusion",           "frames as denoising/generative"),
    ("graph",               "frames as graph structure"),
    ("contrastive",         "frames as representation learning"),
    ("planning",            "frames as planning/search"),
    ("uncertainty",         "frames as uncertainty quantification"),
]

def heuristic_angle(abstract):
    a = (abstract or "").lower()
    for kw, label in ANGLE_HEURISTICS:
        if kw.lower() in a:
            return label
    return "frames as empirical study"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", help="research topic / direction")
    ap.add_argument("--k-papers", type=int, default=8)
    ap.add_argument("--out", default="idea-stage/perspectives.json")
    args = ap.parse_args()

    papers = search(args.topic, k=args.k_papers)
    if not papers:
        print("❌ no papers found"); sys.exit(1)

    perspectives = []
    for p in papers:
        perspectives.append({
            "title":       p.get("title"),
            "year":        p.get("year"),
            "citations":   p.get("citationCount"),
            "arxiv":       (p.get("externalIds") or {}).get("ArXiv"),
            "angle":       heuristic_angle(p.get("abstract")),
            "abstract_excerpt": (p.get("abstract") or "")[:300],
        })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"topic": args.topic, "perspectives": perspectives}, indent=2, ensure_ascii=False))
    print(f"✅ {len(perspectives)} perspectives → {args.out}")
    for p in perspectives:
        print(f"  - [{p['angle']}] {p['title'][:80]}")

if __name__ == "__main__":
    main()
