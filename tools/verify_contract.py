#!/usr/bin/env python3
"""tools/verify_contract.py — validate sprint_contract.yaml.

Checks: 5 required fields present, each ≥ MIN_CHARS, Guard contains a
quantified threshold, Verify mentions seed/baseline. Pure stdlib.
"""
import re, sys
from pathlib import Path

REQUIRED = ["goal", "scope", "metric", "verify", "guard"]
MIN_CHARS = 30
THRESHOLD_RE = re.compile(r"[<>≤≥]=?\s*\d|\d+\s*%|\d+\.\d+")
SEED_RE = re.compile(r"seed|baseline|run_0|run-0|run zero", re.IGNORECASE)

def parse_simple_yaml(text):
    """Minimal flat key: |multiline parser (avoid PyYAML dep)."""
    out, key, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^([a-z_]+)\s*:\s*(.*)$", line)
        if m and not line.startswith(" "):
            if key is not None:
                out[key] = "\n".join(buf).strip()
            key = m.group(1)
            val = m.group(2).strip()
            buf = [val] if val and val != "|" else []
        else:
            if key is not None:
                buf.append(line.rstrip())
    if key is not None:
        out[key] = "\n".join(buf).strip()
    return out

def main():
    if len(sys.argv) != 2:
        print("usage: verify_contract.py <path>"); sys.exit(2)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ {path} not found"); sys.exit(2)

    data = parse_simple_yaml(path.read_text())
    errors, warns = [], []

    for field in REQUIRED:
        if field not in data or not data[field]:
            errors.append(f"missing field: {field}")
            continue
        if len(data[field]) < MIN_CHARS:
            errors.append(f"{field}: too short ({len(data[field])} < {MIN_CHARS})")

    if "guard" in data and not THRESHOLD_RE.search(data["guard"]):
        errors.append("guard: must contain a measurable threshold (e.g., 'SR<60%', 'loss>2.0')")

    if "verify" in data and not SEED_RE.search(data["verify"]):
        warns.append("verify: consider multi-seed verification (mention 'seed' or 'baseline')")

    for w in warns:
        print(f"⚠️  {w}")
    if errors:
        print("❌ CONTRACT INVALID:")
        for e in errors:
            print(f"   - {e}")
        sys.exit(1)
    print("✅ contract valid")

if __name__ == "__main__":
    main()
