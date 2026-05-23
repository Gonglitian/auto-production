# Auto-Production · ARIS-style skill-based research workflow

> Let agents do research while you sleep — skill-based pipeline portable across Claude Code / Codex CLI / Cursor / Trae.

中文版主 README → [`README.md`](README.md)

---

## What

Decompose "doing research" into **9 stages × 5 named gates × 51 composable skills/hooks/templates**, distilled from 16 community auto-research projects (ARIS / ARS / AI-Scientist-v2 / AutoResearchClaw / AgentLaboratory / STORM / etc.) + 11K personal-conversation logs.

Full design: [`../design.md`](../design.md).

## Why

- **Methodology, not platform** — every skill is a single `SKILL.md`, pure markdown + bash + Python stdlib. Zero dependencies, runs anywhere an LLM agent can read markdown.
- **Cross-model adversarial review** > single-model self-review.
- **Stage gates** force named checkpoints instead of ad-hoc human interruption.
- **Self-evolution** — `/meta-optimize` reviews failure log weekly and patches skill prompts.

## Install

```bash
git clone <repo> ~/.claude/skills/auto-production
```

See [`docs/INSTALL.md`](docs/INSTALL.md) for Codex / Cursor / Trae adaptations.

## Quick start

```
/sprint-contract   # fill Goal/Scope/Metric/Verify/Guard
/status            # what's running where
/vla-audit         # mandatory before training
/sleep-research "..." # overnight autonomous mode
```

See main [`README.md`](README.md) for the full skill catalog and architecture.

## License

MIT.
