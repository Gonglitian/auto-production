#!/bin/bash
# tools/gate_resource.sh — Stage 4 → 5 RESOURCE gate auto-check.
# See docs/GATES.md Gate 3.
set -u
fail=0
HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo "")
HOST=$(hostname)

if [ -z "$HEAD" ]; then
  echo "❌ RESOURCE gate: not in a git repo (or no commits yet)"; exit 1
fi

ck() { if eval "$2"; then echo "  ✓ $1"; else echo "  ✗ $1"; fail=1; fi; }

echo "== RESOURCE gate ($HOST @ $HEAD) =="
ck "sprint_contract.yaml present"     '[ -s sprint_contract.yaml ]'
ck "contract signed"                  '[ -f .auto-production/audit/contract_signed.json ]'
if [ -f sprint_contract.yaml ] && [ -f .auto-production/audit/contract_signed.json ]; then
  WANT=$(sha256sum sprint_contract.yaml | awk '{print $1}')
  GOT=$(python3 -c "import json; print(json.load(open('.auto-production/audit/contract_signed.json'))['sha256'])" 2>/dev/null)
  ck "contract hash matches"           "[ '$WANT' = '$GOT' ]"
fi
ck "run_zero baseline locked"         "ls .auto-production/baseline/run_zero_${HOST}_*.json >/dev/null 2>&1"
ck "smoke passed for current commit"  "[ \"\$(python3 -c \"import json;print(json.load(open('.auto-production/audit/smoke_passed.json'))['commit'])\" 2>/dev/null)\" = '$HEAD' ]"

[ $fail -eq 0 ] && { echo "✅ RESOURCE gate PASS"; touch .auto-production/audit/resource_gate.passed; exit 0; }
echo "❌ RESOURCE gate BLOCKED — fix the missing items above"
exit 1
