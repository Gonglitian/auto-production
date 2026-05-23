#!/usr/bin/env python3
"""tools/spawn_task.py — emit a sub-agent prompt template for /spawn-task.

The actual fork is done by the calling skill via Claude's Agent tool;
this script just produces a structured prompt + completion-signal contract.
"""
import argparse, json, uuid
from datetime import datetime
from pathlib import Path

TEMPLATES = {
    "research":  "Survey '{task}' across web/papers. Output sections: \n"
                 "  - Background (5 bullets)\n  - Top 5 references with URL\n  - Open questions\n"
                 "Write result to .auto-production/spawn/{id}/result.md, then "
                 "touch .auto-production/spawn/{id}/.done.\n"
                 "Constraint: ≤10 tool calls, no Bash beyond grep/find.",
    "review":    "Review the code in {task}. Identify: bugs (file:line), "
                 "design smells, missing tests. Output structured 5-section "
                 "report to .auto-production/spawn/{id}/result.md.",
    "code":      "Implement: {task}. Write code to the file path specified. "
                 "Run /smoke-test after. Touch .done when both code + smoke pass.",
    "audit":     "Audit / fact-check / cite-verify: {task}. Use WebSearch + "
                 "verify_citations.py. Emit PASS/WARN/FAIL with evidence to "
                 ".auto-production/spawn/{id}/result.md.",
    "freeform":  "{task}",
}

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("--type", default="freeform", choices=list(TEMPLATES))
    p.add_argument("--task", required=True)
    p.add_argument("--id", default=None)
    p.add_argument("--timeout", default="30m")
    args = ap.parse_args()

    if args.cmd == "prompt":
        sid = args.id or uuid.uuid4().hex[:8]
        d = Path(".auto-production/spawn") / sid
        d.mkdir(parents=True, exist_ok=True)
        prompt = (
            f"# Sub-agent task {sid} (type={args.type}, timeout={args.timeout})\n"
            f"Started: {datetime.now().isoformat(timespec='seconds')}\n\n"
            f"{TEMPLATES[args.type].format(task=args.task, id=sid)}\n\n"
            f"## Completion contract\n"
            f"- Write your final output to `.auto-production/spawn/{sid}/result.md`\n"
            f"- Touch `.auto-production/spawn/{sid}/.done` when finished\n"
            f"- Reply in /conclusion-first 5-section format\n"
        )
        (d / "prompt.md").write_text(prompt)
        meta = {"id": sid, "type": args.type, "task": args.task, "timeout": args.timeout,
                "started_at": datetime.now().isoformat(timespec="seconds")}
        (d / "meta.json").write_text(json.dumps(meta, indent=2))
        print(prompt)
        print(f"\n→ spawn id: {sid}  (forward this prompt to Agent tool)", flush=True)

if __name__ == "__main__":
    main()
