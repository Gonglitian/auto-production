#!/usr/bin/env python3
"""tests/test_skill_format.py — minimal structural test for all SKILL.md.

Checks: every skills/*/SKILL.md has YAML frontmatter with required keys,
the body has expected sections, and slugs match dir name.

Run: python3 tests/test_skill_format.py
"""
import re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REQUIRED_FRONTMATTER = {"name", "description", "argument-hint", "allowed-tools"}
RECOMMENDED_BODY_SECTIONS = ["## Overview", "## When to Use", "## Workflow"]

def check_one(path):
    text = path.read_text()
    errors, warns = [], []

    fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not fm_match:
        errors.append("missing YAML frontmatter")
        return errors, warns
    fm_body = fm_match.group(1)
    keys = set(re.findall(r"^([a-z-]+)\s*:", fm_body, re.MULTILINE))
    missing = REQUIRED_FRONTMATTER - keys
    if missing:
        errors.append(f"missing frontmatter keys: {sorted(missing)}")

    name_m = re.search(r"^name:\s*(\S+)", fm_body, re.MULTILINE)
    if name_m and name_m.group(1) != path.parent.name:
        errors.append(f"name `{name_m.group(1)}` != dir name `{path.parent.name}`")

    for section in RECOMMENDED_BODY_SECTIONS:
        if section not in text:
            warns.append(f"missing recommended section: {section!r}")

    return errors, warns

def main():
    skill_files = sorted((REPO / "skills").glob("*/SKILL.md"))
    if not skill_files:
        print("❌ no skills/*/SKILL.md found"); sys.exit(2)

    fail = 0
    for f in skill_files:
        rel = f.relative_to(REPO)
        errors, warns = check_one(f)
        if errors:
            fail += 1
            print(f"❌ {rel}")
            for e in errors:
                print(f"   - {e}")
        elif warns:
            print(f"⚠️  {rel}")
            for w in warns:
                print(f"   - {w}")
        else:
            print(f"✓ {rel}")

    print(f"\n{len(skill_files)} skills checked; {fail} failed")
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
