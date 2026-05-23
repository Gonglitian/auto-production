#!/usr/bin/env python3
"""tools/cross_host_sync.py — sync active runs to a Notion database.

push: read records from stdin, upsert into Notion DB (by host:job_id key).
pull: query Notion DB, render markdown table to stdout.

Notion API via stdlib urllib (no requests dep). Token from env NOTION_TOKEN.
"""
import argparse, json, os, sys, urllib.request, urllib.error
from datetime import datetime

NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"

def http(method, path, body=None):
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        sys.exit("❌ NOTION_TOKEN env not set")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        data=(json.dumps(body).encode() if body else None),
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code}: {e.read().decode()[:500]}\n"); raise

def query_db(db_id, key, value):
    body = {"filter": {"property": key, "rich_text": {"equals": value}}}
    return http("POST", f"/databases/{db_id}/query", body).get("results", [])

def make_props(rec):
    """Map a record dict to Notion property shape. Adjust to your schema."""
    def rt(v): return {"rich_text": [{"text": {"content": str(v or "")[:1900]}}]}
    def title(v): return {"title": [{"text": {"content": str(v or "")[:200]}}]}
    def sel(v): return {"select": {"name": str(v)[:100]}} if v else {"select": None}
    def date(v): return {"date": {"start": v}} if v else {"date": None}
    def url(v): return {"url": v or None}
    return {
        "run_name": title(rec.get("run_name") or rec.get("job_id")),
        "host": sel(rec.get("host")),
        "partition": rt(rec.get("partition")),
        "job_id": rt(rec.get("job_id")),
        "branch": rt(rec.get("branch")),
        "commit": rt(rec.get("commit")),
        "start_time": date(rec.get("start_time")),
        "wandb_url": url(rec.get("wandb_url")),
        "ckpt_path": rt(rec.get("ckpt_path")),
        "conda_env": rt(rec.get("conda_env")),
        "dataset_path": rt(rec.get("dataset_path")),
        "status": sel(rec.get("status") or "RUNNING"),
        "last_metric": rt(rec.get("last_metric")),
    }

def push(db_id, records, host):
    for rec in records:
        rec["host"] = host
        key = f"{host}:{rec.get('job_id')}"
        existing = query_db(db_id, "job_id", str(rec.get("job_id") or ""))
        existing = [e for e in existing if (host_prop := e["properties"].get("host", {}).get("select")) and host_prop.get("name") == host]
        props = make_props(rec)
        if existing:
            http("PATCH", f"/pages/{existing[0]['id']}", {"properties": props})
            print(f"↻ updated {key}")
        else:
            http("POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
            print(f"+ created {key}")

def pull(db_id):
    rows = http("POST", f"/databases/{db_id}/query", {"page_size": 100}).get("results", [])
    print("| run | host | status | branch@commit | wandb |")
    print("|---|---|---|---|---|")
    for r in rows:
        p = r["properties"]
        def gtitle(k): return "".join(t.get("plain_text","") for t in p.get(k, {}).get("title", []))
        def grt(k): return "".join(t.get("plain_text","") for t in p.get(k, {}).get("rich_text", []))
        def gsel(k): return (p.get(k, {}).get("select") or {}).get("name","")
        def gurl(k): return p.get(k, {}).get("url") or ""
        print(f"| {gtitle('run_name')} | {gsel('host')} | {gsel('status')} | {grt('branch')}@{grt('commit')} | {gurl('wandb_url')} |")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pu = sub.add_parser("push"); pu.add_argument("--database", required=True); pu.add_argument("--host", required=True); pu.add_argument("--records", default="-")
    pl = sub.add_parser("pull"); pl.add_argument("--database", required=True)
    a = ap.parse_args()
    if a.cmd == "push":
        src = sys.stdin if a.records == "-" else open(a.records)
        recs = [json.loads(l) for l in src if l.strip()]
        push(a.database, recs, a.host)
    elif a.cmd == "pull":
        pull(a.database)

if __name__ == "__main__":
    main()
