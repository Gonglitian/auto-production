#!/usr/bin/env python3
"""tools/html_homepage.py — render a project's live-status homepage.html.

Single-file HTML, no JS framework. Reads sprint_contract.yaml, promise.json,
findings.md tail, .auto-production/active_runs.json, and the audit/ pass
trace dir. Pure stdlib + string templating.
"""
import argparse, html, json, os, subprocess
from datetime import datetime
from pathlib import Path

CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  max-width:980px;margin:24px auto;padding:0 16px;color:#222;line-height:1.55}
h1{border-bottom:2px solid #1a4a8c;padding-bottom:6px}
h2{color:#1a4a8c;margin-top:32px;border-left:4px solid #1a4a8c;padding-left:10px}
table{border-collapse:collapse;width:100%;margin:10px 0}
th,td{border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:14px}
th{background:#f5f7fa}
code,pre{background:#f5f7fa;padding:2px 6px;border-radius:4px;font-size:13px}
pre{padding:10px;overflow:auto}
.ok{color:#0a7f29}.warn{color:#a86b00}.fail{color:#b00020}
small{color:#666}
.gates li{list-style:none;padding:4px 0}
"""

TEMPLATE = """<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">{auto_refresh}
<title>{project} — Stage {stage}</title>
<style>{css}</style>
</head><body>
<h1>{project} <small>branch=<code>{branch}</code> commit=<code>{commit}</code></small></h1>
<p><strong>Stage</strong>: {stage} &nbsp; · &nbsp; <strong>Updated</strong>: {now}</p>

<h2>1. Sprint Contract</h2>
{contract_block}

<h2>2. Active Runs</h2>
{runs_block}

<h2>3. Latest Figures</h2>
{figs_block}

<h2>4. Pending Promises</h2>
{promises_block}

<h2>5. Findings (latest)</h2>
{findings_block}

<h2>6. Stage Gates</h2>
<ul class="gates">{gates_block}</ul>

</body></html>
"""

def sh(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""

def render_contract(path):
    if not Path(path).exists():
        return '<p class="warn">⚠️ no sprint_contract.yaml — run <code>/sprint-contract --init</code></p>'
    return f"<pre>{html.escape(Path(path).read_text())}</pre>"

def render_runs(path):
    p = Path(path)
    if not p.exists():
        return '<p class="warn">no active runs — run <code>/cross-host-sync --direction pull</code></p>'
    try:
        runs = json.loads(p.read_text())
    except Exception:
        return '<p class="fail">malformed active_runs.json</p>'
    if not runs:
        return "<p>(no active runs)</p>"
    out = ["<table><tr><th>host</th><th>job_id</th><th>name</th><th>status</th><th>wandb</th></tr>"]
    for r in runs:
        out.append(
            f"<tr><td>{html.escape(r.get('host',''))}</td>"
            f"<td>{html.escape(str(r.get('job_id','')))}</td>"
            f"<td>{html.escape(r.get('run_name',''))}</td>"
            f"<td>{html.escape(r.get('status',''))}</td>"
            f"<td><a href=\"{html.escape(r.get('wandb_url',''))}\">wandb</a></td></tr>"
        )
    out.append("</table>")
    return "".join(out)

def render_figs(dir_):
    d = Path(dir_)
    pngs = sorted(d.glob("*.png")) if d.exists() else []
    if not pngs:
        return '<p class="warn">no figures — run <code>/auto-viz</code></p>'
    return "".join(f'<p><img src="{p}" alt="{p.name}" style="max-width:100%"></p>' for p in pngs)

def render_promises(path):
    p = Path(path)
    if not p.exists():
        return "<p>(no promise ledger)</p>"
    d = json.loads(p.read_text())
    if not d.get("open"):
        return '<p class="ok">✅ no pending promises</p>'
    out = ["<ul>"]
    for x in d["open"]:
        out.append(f"<li>⏳ <code>{x['id']}</code> — {html.escape(x['text'])}</li>")
    out.append("</ul>")
    return "".join(out)

def render_findings(path, n=20):
    p = Path(path)
    if not p.exists():
        return "<p>(no findings.md)</p>"
    lines = p.read_text().splitlines()[-n:]
    return f"<pre>{html.escape(chr(10).join(lines))}</pre>"

def render_gates(audit_dir):
    d = Path(audit_dir)
    if not d.exists():
        return '<li class="warn">⚠️ no audit/ — no gates passed yet</li>'
    items = []
    for f in sorted(d.glob("*")):
        items.append(f'<li class="ok">✅ {html.escape(f.name)}</li>')
    return "".join(items) or '<li>(no gate traces)</li>'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="homepage.html")
    ap.add_argument("--auto-refresh", type=int, default=0)
    ap.add_argument("--project", default=Path.cwd().name)
    ap.add_argument("--stage", default="?")
    args = ap.parse_args()

    refresh = f'<meta http-equiv="refresh" content="{args.auto_refresh}">' if args.auto_refresh else ""

    page = TEMPLATE.format(
        project=html.escape(args.project),
        stage=html.escape(args.stage),
        css=CSS,
        auto_refresh=refresh,
        branch=html.escape(sh("git", "branch", "--show-current") or "(not git)"),
        commit=html.escape(sh("git", "rev-parse", "--short", "HEAD") or ""),
        now=datetime.now().isoformat(timespec="seconds"),
        contract_block=render_contract("sprint_contract.yaml"),
        runs_block=render_runs(".auto-production/active_runs.json"),
        figs_block=render_figs("figures"),
        promises_block=render_promises("promise.json"),
        findings_block=render_findings("findings.md"),
        gates_block=render_gates(".auto-production/audit"),
    )

    tmp = Path(args.output + ".tmp")
    tmp.write_text(page)
    os.replace(tmp, args.output)
    print(f"✅ wrote {args.output}")

if __name__ == "__main__":
    main()
