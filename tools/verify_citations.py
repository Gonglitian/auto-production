#!/usr/bin/env python3
"""tools/verify_citations.py — citation existence check (Layer 1).

Skeleton: takes a list of cite keys + .bib, queries arXiv / Crossref /
OpenAlex with urllib (stdlib), caches results 30d, emits per-key 4-state
verdict JSON for the citation-audit skill.
"""
import argparse, hashlib, json, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ARXIV_API = "http://export.arxiv.org/api/query"
CROSSREF_API = "https://api.crossref.org/works"
OPENALEX_API = "https://api.openalex.org/works"
TTL = timedelta(days=30)
UA = "auto-production-citation-audit/0.1 (mailto:%s)" % (
    __import__("os").environ.get("AUTO_PRODUCTION_VERIFY_EMAIL", "noreply@example.com"))

def cache_key(s): return hashlib.sha1(s.encode()).hexdigest()[:16]

def cached(cache_dir, k):
    p = Path(cache_dir) / f"{k}.json"
    if p.exists() and (datetime.now() - datetime.fromtimestamp(p.stat().st_mtime) < TTL):
        return json.loads(p.read_text())
    return None

def save_cache(cache_dir, k, data):
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    (Path(cache_dir) / f"{k}.json").write_text(json.dumps(data, ensure_ascii=False))

def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()

def parse_bib(bib_path):
    """Minimal bib parser — extracts @type{key, ...}. Not full BibTeX-correct."""
    out = {}
    if not Path(bib_path).exists():
        return out
    text = Path(bib_path).read_text()
    for m in re.finditer(r"@\w+\s*\{\s*([^,]+),(.*?)\n\}", text, re.DOTALL):
        key, body = m.group(1).strip(), m.group(2)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*[\{\"]([^\}\"]+)[\}\"]", body):
            fields[fm.group(1).lower()] = fm.group(2).strip()
        out[key] = fields
    return out

def verify_arxiv(arxiv_id):
    try:
        url = f"{ARXIV_API}?id_list={urllib.parse.quote(arxiv_id)}"
        text = http_get(url)
        return ("<entry>" in text, "arxiv")
    except Exception:
        return (None, "arxiv")

def verify_doi(doi):
    try:
        url = f"{CROSSREF_API}/{urllib.parse.quote(doi)}"
        text = http_get(url)
        d = json.loads(text)
        return (d.get("status") == "ok", "crossref")
    except Exception:
        return (None, "crossref")

def verify_title(title):
    try:
        url = f"{OPENALEX_API}?search={urllib.parse.quote(title)}&per_page=1"
        text = http_get(url)
        d = json.loads(text)
        return (bool(d.get("results")), "openalex")
    except Exception:
        return (None, "openalex")

def verify_one(key, fields, cache_dir):
    ck = cache_key(key + json.dumps(fields, sort_keys=True))
    hit = cached(cache_dir, ck)
    if hit:
        return hit
    res = {"key": key, "status": "unverified", "source": None, "checked_at": datetime.now().isoformat()}
    arxiv = fields.get("eprint") or fields.get("arxiv") or ""
    doi = fields.get("doi", "")
    title = fields.get("title", "")
    for fn, arg in [(verify_arxiv, arxiv), (verify_doi, doi), (verify_title, title)]:
        if not arg:
            continue
        ok, source = fn(arg)
        if ok:
            res["status"] = "verified"; res["source"] = source; break
        if ok is None:
            res["status"] = "verify_pending"; res["source"] = source
        time.sleep(0.3)
    save_cache(cache_dir, ck, res)
    return res

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("existence")
    e.add_argument("--keys", required=True)
    e.add_argument("--bib", required=True)
    e.add_argument("--cache-dir", default=".auto-production/cache/citations")
    e.add_argument("--out", default=".auto-production/cite_existence.json")
    args = ap.parse_args()

    if args.cmd == "existence":
        bib = parse_bib(args.bib)
        keys = [l.strip() for l in Path(args.keys).read_text().splitlines() if l.strip()]
        results = []
        for k in keys:
            fields = bib.get(k, {})
            if not fields:
                results.append({"key": k, "status": "error", "reason": "key not in bib"})
                continue
            results.append(verify_one(k, fields, args.cache_dir))

        counts = {"verified": 0, "unverified": 0, "verify_pending": 0, "error": 0}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        verdict = "PASS" if counts["unverified"] == 0 and counts["error"] == 0 else (
                  "WARN" if counts["unverified"] <= 2 else "BLOCKED")
        out = {"summary": counts, "verdict": verdict, "results": results}
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2))
        print(json.dumps(out["summary"], indent=2), file=sys.stderr)
        sys.exit(0 if verdict == "PASS" else (1 if verdict == "BLOCKED" else 0))

if __name__ == "__main__":
    main()
