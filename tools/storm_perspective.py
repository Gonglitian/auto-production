#!/usr/bin/env python3
"""tools/storm_perspective.py — Search Semantic Scholar for K similar papers,
extract a one-line "angle" per paper to seed perspective-guided questions.

Pure stdlib. Outputs idea-stage/perspectives.json.
"""
import argparse, json, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX_API = "https://api.openalex.org/works"
UA = "auto-production-storm/0.1"
MAX_S2_RETRIES = 2          # exp backoff: 2s, 6s
S2_RETRY_DELAY_S = 2.0

def _http(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def _s2_search(query, k):
    url = f"{S2_API}?{urllib.parse.urlencode({'query':query,'limit':k*3,'fields':'title,abstract,year,citationCount,authors,externalIds'})}"
    delay = S2_RETRY_DELAY_S
    for attempt in range(MAX_S2_RETRIES + 1):
        try:
            d = _http(url)
            return d.get("data", []) or []
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_S2_RETRIES:
                print(f"⚠️  S2 429, retry in {delay:.0f}s (attempt {attempt+1}/{MAX_S2_RETRIES})", file=sys.stderr)
                time.sleep(delay)
                delay *= 3
                continue
            raise
    return []

def _openalex_search(query, k):
    """Fallback: OpenAlex has more lenient rate limits + similar coverage."""
    url = f"{OPENALEX_API}?{urllib.parse.urlencode({'search':query,'per_page':k*3,'select':'title,abstract_inverted_index,publication_year,cited_by_count,authorships,doi,ids'})}"
    try:
        d = _http(url)
    except Exception as e:
        print(f"⚠️  OpenAlex query failed: {e}", file=sys.stderr)
        return []
    out = []
    for w in d.get("results", []):
        out.append({
            "title": w.get("title"),
            "abstract": _reconstruct_abstract(w.get("abstract_inverted_index") or {}),
            "year": w.get("publication_year"),
            "citationCount": w.get("cited_by_count") or 0,
            "externalIds": {"DOI": (w.get("doi") or "").replace("https://doi.org/", "")},
        })
    return out

def _reconstruct_abstract(inv):
    if not inv: return ""
    positions = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions[:300])

def search(query, k=8):
    """S2 first; on 429/error fall back to OpenAlex (similar coverage, friendlier rate limit)."""
    try:
        rows = _s2_search(query, k)
        source = "S2"
    except Exception as e:
        print(f"⚠️  S2 hard-fail ({e}); falling back to OpenAlex", file=sys.stderr)
        rows = _openalex_search(query, k)
        source = "OpenAlex"
    if not rows:
        return []
    print(f"  source={source} candidates={len(rows)}", file=sys.stderr)
    # sort by citation count, dedupe by title
    seen, out = set(), []
    for p in sorted(rows, key=lambda x: -(x.get("citationCount") or 0)):
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
