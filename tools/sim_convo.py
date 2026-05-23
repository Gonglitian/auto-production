#!/usr/bin/env python3
"""tools/sim_convo.py — emit a writer×expert role-play prompt template.

This is a prompt-emitter: the actual conversation needs to be driven by an
LLM (e.g. via Claude Agent tool). Output goes to idea-stage/sim_convo_<ts>.md
as a template the agent fills in.
"""
import argparse, sys
from datetime import datetime
from pathlib import Path

TEMPLATE = """# Simulated Writer × Expert Conversation
Topic: {topic}
Rounds: {turns}
Started: {ts}

---

## Roles
- **Writer**: probes assumptions, asks follow-up trade-off questions, links answers back to the original topic.
- **Expert**: answers with specific examples + citations, points out flaws in writer's framing.

## Instructions for the agent
Run {turns} rounds. Each round:
1. Writer asks a sharper question than the previous round.
2. Expert answers with one specific example, one counter-consideration, one open question.
3. Agent records the exchange below verbatim.

After {turns} rounds, Writer writes a synthesis:
"From this conversation, candidate research ideas are: …" — 3-5 bullet points.

---

## Round 1
**Writer**: …

**Expert**: …

## Round 2
**Writer**: …

**Expert**: …

…

## Synthesis (candidate ideas)
- Candidate 1: …
- Candidate 2: …
- Candidate 3: …
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic")
    ap.add_argument("--turns", type=int, default=6)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ts = datetime.now().isoformat(timespec="seconds")
    out = args.out or f"idea-stage/sim_convo_{ts.replace(':','-')}.md"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(TEMPLATE.format(topic=args.topic, turns=args.turns, ts=ts))
    print(f"✅ template emitted → {out}")
    print("→ fill in the rounds via Claude Agent, then run /idea-perspective + /novelty-check on each candidate")

if __name__ == "__main__":
    main()
