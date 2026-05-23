#!/usr/bin/env python3
"""tools/paper_mode.py — emit prompt template per (mode, venue) pair.

The actual section text is written by an LLM agent reading the prompt +
the project's findings/results. This tool just produces the brief.
"""
import argparse, sys
from pathlib import Path

VENUE_STYLE = {
    "NeurIPS":  "9-page double-column NeurIPS 2026, formal but accessible, claims grounded in 5-seed CI",
    "ICLR":     "9-page single-column ICLR, openreview-friendly, story-driven",
    "ICML":     "8-page double-column ICML, theory + empirical balance",
    "CVPR":     "8-page double-column CVPR, heavy on visual figures",
    "CoRL":     "8-page CoRL, robotics applied focus, real-robot results",
    "ACL":      "9-page ACL, linguistics-aware, fair eval, low compute",
    "Nature":   "Nature single-column, broad-audience accessible, methods in supp",
}

MODE_TEMPLATES = {
    "outline":          "Write paper/OUTLINE.md: 1 sentence per section "
                        "for {n_sections} sections (intro/related/method/setup/results/discussion/conclusion).",
    "intro":            "Write paper/sections/intro.tex (~1 page): 5-paragraph "
                        "Black-Mad-Libs structure (hook/gap/idea/result/contribution).",
    "related-work":     "Write paper/sections/related.tex: 3-5 thematic groups, "
                        "each ending in 'unlike these we …'.",
    "method":           "Write paper/sections/method.tex: notation up-front, then "
                        "Algorithm 1 + 1 figure + per-step justification.",
    "experiment":       "Write paper/sections/experiment.tex: setup → main "
                        "table → ablation → qualitative (figure).",
    "discussion":       "Write paper/sections/discussion.tex: 3-4 paragraphs, "
                        "each opening with a contrarian observation.",
    "abstract":         "Write paper/abstract.tex: 4-sentence top-venue format "
                        "(context / gap / method / result).",
    "conclusion":       "Write paper/sections/conclusion.tex (1 paragraph) + "
                        "Future Work (3 bullets).",
    "appendix":         "Write paper/sections/appendix.tex: extra ablations + hyperparams.",
    "reviewer-defense": "Write paper/sections/reviewer_defense.tex: anticipate "
                        "top 5 reviewer concerns + 1-paragraph response each. "
                        "Pull questions from idea-stage/persona_questions.md.",
    "one-pager":        "Write paper/onepager.md: 1-page social-media abstract + "
                        "1 hero figure caption, plain English.",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=list(MODE_TEMPLATES))
    ap.add_argument("--venue", default="NeurIPS")
    ap.add_argument("--n-sections", type=int, default=7)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    style = VENUE_STYLE.get(args.venue, f"({args.venue}) — generic top-venue style")
    body = MODE_TEMPLATES[args.mode].format(n_sections=args.n_sections)
    prompt = (
        f"# /paper-mode --mode {args.mode} --venue {args.venue}\n\n"
        f"Style: {style}\n\n"
        f"Task: {body}\n\n"
        f"Constraints:\n"
        f"- No fabricated numbers (use <!-- DATA_NEEDED --> placeholder instead)\n"
        f"- No fabricated citations (every `\\cite{{}}` must exist in references.bib)\n"
        f"- 3-layer anchor on factual claims (see /citation-audit)\n"
        f"- Conclusion-first 5-section internal-thinking before drafting\n"
    )

    out = args.out or f".auto-production/paper_prompts/{args.mode}.md"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(prompt)
    print(prompt)
    print(f"\n→ saved to {out}  (feed to Claude Agent to write the section)")

if __name__ == "__main__":
    main()
