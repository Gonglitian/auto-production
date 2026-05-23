# AGENT_GUIDE.md — 给 LLM 看的入口

> ⚠️ 这份文件是**给 agent 读的**，不是给人浏览。结构化、紧凑、操作向。
> 人类请读 [`README.md`](README.md)。

## What this repo is

A skill bundle for autonomous research, ARIS-style. 9 stages × 5 gates × **57 skills** (2 entry + 10 cross-cutting + 39 stage-specific + 3 gate/quality + 3 driver/dev).

## Your job as agent reading this

1. **Identify the stage** the user is at (1-9, see ARCHITECTURE.md).
2. **Identify the gate** required to leave that stage (NOVELTY / METHOD / RESOURCE / RESULTS / FINAL, see GATES.md).
3. **Invoke skills in order** — do NOT skip gates.

## Skill catalog (by stage)

| Stage | Skill (slash command) | Mandatory? |
|---|---|---|
| 1 Idea | `/idea-perspective`, `/idea-sim-convo`, `/novelty-check`, `/persona-probe` | `/novelty-check` mandatory before NOVELTY gate |
| 2 Code | `/vla-audit` ⭐, `/arch-plan`, `/ast-validate` | `/vla-audit` MANDATORY before METHOD gate |
| 3 Data | `/resource-planning`, `/corpus-schema`, `/benchmark-agent`, `/datalake` | `/resource-planning` MANDATORY |
| 4 Exp Design | `/sprint-contract` ⭐ (5-tuple), `/task-notes-yaml`, `/run-zero` ⭐ | All 3 MANDATORY before RESOURCE gate |
| 5 Running | `/cross-host-sync`, `/slurm-hold`, `/spawn-task`, `/sleep-research`, `/audit-driven-retrain`, `/smoke-test` | `/smoke-test` MANDATORY (stop-hook default) |
| 6 Result | `/auto-viz`, `/pivot` ⭐, `/plateau-detect`, `/auto-version`, `/tree-viz`, `/findings-map` | `/pivot` MANDATORY before RESULTS gate |
| 7 Doc | `/learn-tag` | — |
| 8 Paper | `/paper-pipeline`, `/paper-mode`, `/citation-audit` ⭐, `/cross-review` ⭐, `/pubfig`, `/paper-talk`, `/paper-poster`, `/paper-slides`, `/rebuttal`, `/kill-argument`, `/resubmit-pipeline` | `/citation-audit` + `/cross-review` MANDATORY before FINAL gate |
| 9 Promotion | — | — |

## Driver / dev / deploy skills (only when YOU are a driver-Claude controlling another CC)

- `/remote-drive` — full meta-skill for tmux send-keys control of another Claude Code session
- `/driver-findings` — round-N findings file pattern for driver→sub-agent handoff
- `/sync-to-remote` — rsync project + bootstrap auto-production on remote compute host; pairs with `/cross-host-sync`

These are NOT for normal task execution — invoke them only when you're orchestrating another CC instance.

## Cross-cutting always-on (run as hooks, not by you)

These live in `hooks/` and trigger automatically:

- `pre_promise_check.sh` — PostToolUse: scan agent stdout for "我会..." → `promise.json`
- `pre_destructive_git.sh` — PreToolUse: intercept `rm -rf`, `git reset --hard`, `git push --force`, `git clean -fdx`
- `pre_session_sync.sh` — SessionStart: `git pull` skills/
- `stop_smoke_gate.sh` — Stop: refuse stop if smoke-test didn't pass

Plus you (agent) should:
- Output report format = `/conclusion-first` 5 sections: **Conclusion / What I changed / What I checked / Risks / Next step**
- Apply `/double-check` before any user-visible claim (confidence 0-5 + suspicious points)
- Apply `/concession-threshold` before agreeing with user proposal (evaluate trade-offs, alternatives, Guard violations)
- Use `/gate --name <NAME>` to verify a stage transition rather than judging "I think it's good"
- Run `/failure-checklist` before RESULTS and FINAL gates
- For stuck decisions, escalate to `/debate-judge` (N-position debate) or `/six-agent-team` (route to PI/postdoc/reviewer)

## Helper resolver chain (3 layers)

When a SKILL.md calls a Python helper, resolve in this order:

1. `.auto-production/tools/<name>` (project-local override)
2. `tools/<name>` (repo-local — most common)
3. `$AUTO_PRODUCTION_REPO/tools/<name>` (global install)

Documented in `docs/RESOLVER.md`.

## When in doubt

1. Read the user's last message; identify stage from keywords.
2. If unsure between PROCEED / REFINE / PIVOT, **always** invoke `/pivot` skill.
3. If you said "我会..." 3 steps ago and haven't done it, do it now.
4. If you've been silent for >5 min with no tool call, abort or escalate.
5. If a memory says X exists, **verify first** before recommending (grep / ls).

## State files agent should write/read

- `findings.md` — per-sprint conclusions, updated by you after `/pivot`
- `sprint_contract.yaml` — 5-tuple, read-only after gate passes
- `promise.json` — tracked by `pre_promise_check.sh`
- `.auto-production/cache/` — verify_citations cache (30-day TTL)
- `EXPERIMENT_STATUS.md` — cross-host run table (auto-updated by `/cross-host-sync`)

## DO NOT

- DO NOT skip gates.
- DO NOT default to "再加点 step 试试" — that's an implicit PROCEED. Use `/pivot`.
- DO NOT write paper claims without `/citation-audit` anchors.
- DO NOT push to git without `/promise-check` clean.
- DO NOT trust user's "yes do it" without `/concession-threshold` review.
