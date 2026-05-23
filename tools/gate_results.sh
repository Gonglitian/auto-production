#!/bin/bash
# tools/gate_results.sh — Stage 6 → 7 RESULTS gate auto-check.
# See docs/GATES.md Gate 4.
set -u
fail=0

ck() { if eval "$2"; then echo "  ✓ $1"; else echo "  ✗ $1"; fail=1; fi; }

echo "== RESULTS gate =="
ck "decisions.jsonl has at least one entry"    '[ -s decisions.jsonl ]'
ck "latest decision is PROCEED/REFINE/PIVOT"   "tail -1 decisions.jsonl 2>/dev/null | python3 -c 'import json,sys; d=json.loads(sys.stdin.read() or \"{}\"); sys.exit(0 if d.get(\"rec\") in {\"PROCEED\",\"REFINE\",\"PIVOT\"} else 1)'"
ck "latest decision has user_decision set"     "tail -1 decisions.jsonl 2>/dev/null | python3 -c 'import json,sys; d=json.loads(sys.stdin.read() or \"{}\"); sys.exit(0 if d.get(\"user_decision\") else 1)'"
ck "findings.md updated"                       '[ -s findings.md ]'
ck "auto-viz figures present"                  '[ -f figures/loss.png ] || [ -f figures/reward.png ] || [ -f figures/task_sr.png ]'
ck "A5 failure checklist passed"               '[ -f .auto-production/audit/a5_failure_checklist.passed ]'

[ $fail -eq 0 ] && { echo "✅ RESULTS gate PASS"; touch .auto-production/audit/results_gate.passed; exit 0; }
echo "❌ RESULTS gate BLOCKED — run /pivot, /auto-viz, /failure-checklist"
exit 1
