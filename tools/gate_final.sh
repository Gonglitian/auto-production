#!/bin/bash
# tools/gate_final.sh — Stage 8 → 9 FINAL gate auto-check.
# See docs/GATES.md Gate 5.
set -u
fail=0

ck() { if eval "$2"; then echo "  ✓ $1"; else echo "  ✗ $1"; fail=1; fi; }

echo "== FINAL gate =="
ck "citation audit verdict PASS or WARN" \
   "python3 -c 'import json;v=json.load(open(\".auto-production/cite_audit.json\"))[\"verdict\"];import sys;sys.exit(0 if v in {\"PASS\",\"WARN\"} else 1)' 2>/dev/null"
ck "cross-review converged"                "ls .auto-production/cross_review/round_*/converged.json >/dev/null 2>&1"
ck "A5 failure checklist passed"           '[ -f .auto-production/audit/a5_failure_checklist.passed ]'
ck "paper compiled to PDF"                 '[ -f paper/paper.pdf ] || [ -f paper/main.pdf ]'

[ $fail -eq 0 ] && { echo "✅ FINAL gate PASS — paper is ready to submit"; touch .auto-production/audit/final_gate.passed; exit 0; }
echo "❌ FINAL gate BLOCKED — run /citation-audit + /cross-review + /failure-checklist + paper-compile"
exit 1
