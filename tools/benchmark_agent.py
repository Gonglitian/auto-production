#!/usr/bin/env python3
"""tools/benchmark_agent.py — orchestrator stub for the 4-stage benchmark
pipeline (Surveyor → Selector → Acquirer → Validator).

This emits 4 sub-agent prompt files; the actual LLM execution happens via
Claude's Agent tool. Output goes to benchmark-stage/.
"""
import argparse, json, sys
from pathlib import Path

OUT = Path("benchmark-stage")
STAGES = ["surveyor", "selector", "acquirer", "validator"]

PROMPTS = {
    "surveyor":  "Survey 10+ candidate benchmarks for task: {task}\n"
                 "Sources: papers-with-code, HuggingFace datasets, arxiv. "
                 "For each emit {{name, paper, license, size, n_episodes, "
                 "metric_type, why_relevant}}. Output to "
                 "benchmark-stage/candidates.json (JSON list).\n",
    "selector":  "Read benchmark-stage/candidates.json. Score each on: "
                 "relevance / community-usage / license / data-availability "
                 "(0-5 each). Pick top {top_k} and write to "
                 "benchmark-stage/selected.json with reasons.\n",
    "acquirer":  "For each entry in benchmark-stage/selected.json: emit a "
                 "download command (huggingface-cli/git/wget). Call /resource-planning "
                 "first to confirm disk. Then download to benchmark-stage/downloads/.\n",
    "validator": "For each downloaded benchmark: (a) verify file count vs "
                 "expected (b) load one sample via project's dataloader "
                 "(c) check schema match. Write benchmark-stage/validation.json "
                 "with PASS/FAIL per benchmark.\n",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--out", default="benchmark-stage")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    for stage in STAGES:
        prompt = PROMPTS[stage].format(task=args.task, top_k=args.top_k)
        (out / f"{stage}_prompt.md").write_text(f"# {stage.title()} sub-agent\n\n{prompt}")
    print(f"✅ 4 sub-agent prompts emitted → {out}/")
    print("→ run each via Claude Agent tool in order surveyor → selector → acquirer → validator")
    print("→ each stage's sub-agent writes its output back into benchmark-stage/")

if __name__ == "__main__":
    main()
