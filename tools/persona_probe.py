#!/usr/bin/env python3
"""tools/persona_probe.py — emit 8-persona × 3 question template for a topic.

Pure stdlib. Output goes to idea-stage/persona_questions.md.
"""
import argparse, sys
from pathlib import Path

PERSONAS = [
    ("Reviewer (top venue)",      "novelty / soundness / experiment rigor / related-work coverage"),
    ("PI / advisor",              "story / position in lab roadmap / why-now"),
    ("Same-field PhD student",    "reproducibility / hyperparam sensitivity / cost to retry"),
    ("Cross-disciplinary scholar","accessibility / abstraction / transferable insight"),
    ("Industry ML engineer",      "inference cost / deployment / latency / maintenance"),
    ("Policy maker / ethicist",   "bias / dual-use / safety / sustainability"),
    ("Chinese-community user",    "localization / Chinese-data adaptation / Chinese benchmark coverage"),
    ("Reproducer 3 years later",  "environment / data availability / ckpt / artifact decay"),
]

TEMPLATE = """# 8-Persona Probe for: {topic}

Run by /persona-probe. Each persona contributes the 3 most uncomfortable
questions about the proposal. Use these as the "ammunition" for later
AskUserQuestion / cross-review / rebuttal preparation.

---
"""

PERSONA_SECTION = """## {idx}. {name}
Focus: {focus}

1. (TBD)
2. (TBD)
3. (TBD)

"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic")
    ap.add_argument("--out", default="idea-stage/persona_questions.md")
    args = ap.parse_args()

    body = TEMPLATE.format(topic=args.topic)
    for i, (name, focus) in enumerate(PERSONAS, 1):
        body += PERSONA_SECTION.format(idx=i, name=name, focus=focus)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(body)
    print(f"✅ template emitted → {args.out}")
    print(f"→ {len(PERSONAS)} persona × 3 = {3*len(PERSONAS)} questions to fill in (≥24 required for NOVELTY gate)")

if __name__ == "__main__":
    main()
