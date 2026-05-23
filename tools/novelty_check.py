#!/usr/bin/env python3
"""tools/novelty_check.py — query S2/OpenAlex/arXiv for similar work, emit
NOVEL/OVERLAP/DUPLICATE verdict by simple TF-IDF cosine over abstracts.

Pure stdlib + math. Output: idea-stage/novelty.json.
"""
import argparse, json, math, re, sys, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

S2 = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX = "https://api.openalex.org/works"
UA = "auto-production-novelty/0.1"

def http(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"⚠️  query failed: {e}", file=sys.stderr)
        return None

def s2_search(q, k=10):
    d = http(f"{S2}?{urllib.parse.urlencode({'query':q,'limit':k,'fields':'title,abstract,authors,year,venue,externalIds'})}")
    return (d or {}).get("data", []) or []

def openalex_search(q, k=10):
    d = http(f"{OPENALEX}?{urllib.parse.urlencode({'search':q,'per_page':k})}")
    rows = []
    for w in (d or {}).get("results", []):
        rows.append({
            "title":    w.get("title"),
            "abstract": _reconstruct_abstract(w.get("abstract_inverted_index") or {}),
            "year":     (w.get("publication_year")),
            "venue":    ((w.get("host_venue") or {}).get("display_name")),
            "externalIds": {"DOI": (w.get("doi") or "").replace("https://doi.org/", "")},
        })
    return rows

def _reconstruct_abstract(inv):
    if not inv: return ""
    positions = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions[:300])

def tokenize(s):
    return re.findall(r"[a-zA-Z]{3,}", (s or "").lower())

def tfidf_cosine(a, b):
    """Naive TF-IDF cosine over two short texts: treat both as the corpus."""
    ta, tb = Counter(tokenize(a)), Counter(tokenize(b))
    df = Counter()
    for tok in ta: df[tok] += 1
    for tok in tb: df[tok] += 1
    def weight(c):
        return {t: c[t] * math.log(2/df[t]+1) for t in c}
    wa, wb = weight(ta), weight(tb)
    common = set(wa) & set(wb)
    num = sum(wa[t]*wb[t] for t in common)
    den = math.sqrt(sum(v*v for v in wa.values())) * math.sqrt(sum(v*v for v in wb.values()))
    return (num/den) if den else 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idea")
    ap.add_argument("--threshold", type=float, default=0.60)
    ap.add_argument("--out", default="idea-stage/novelty.json")
    args = ap.parse_args()

    candidates = s2_search(args.idea) + openalex_search(args.idea)

    scored = []
    for c in candidates:
        s = tfidf_cosine(args.idea, c.get("abstract") or c.get("title") or "")
        scored.append({"title":c.get("title"), "year":c.get("year"),
                       "venue":c.get("venue"),
                       "arxiv":(c.get("externalIds") or {}).get("ArXiv"),
                       "doi":(c.get("externalIds") or {}).get("DOI"),
                       "sim": round(s, 3)})
    scored.sort(key=lambda x: -x["sim"])
    closest = scored[:10]
    max_sim = closest[0]["sim"] if closest else 0.0

    if max_sim >= 0.75:
        verdict = "DUPLICATE"
    elif max_sim >= args.threshold:
        verdict = "OVERLAP"
    else:
        verdict = "NOVEL"

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({
        "idea": args.idea, "verdict": verdict, "max_similarity": max_sim,
        "threshold": args.threshold, "closest": closest
    }, indent=2, ensure_ascii=False))
    print(f"verdict: {verdict}  (max_sim={max_sim:.2f})")
    for c in closest[:3]:
        print(f"  - sim={c['sim']:.2f}  {c['title'][:80]}")
    sys.exit(0 if verdict in {"NOVEL","OVERLAP"} else 1)

if __name__ == "__main__":
    main()
