#!/usr/bin/env python3
"""tools/paper_slides.py — emit Beamer .tex + speaker_notes.md skeleton.

10-page outline (title/motivation/question/related/method-overview/method-detail/
setup/results/ablation/conclusion). LLM agent fills section text per /paper-mode.
"""
import argparse, sys
from pathlib import Path

OUTLINE = [
    ("Title",               "title + authors + venue"),
    ("Motivation",           "1 figure that hooks audience in 30s"),
    ("Question / Hypothesis","1 sentence + why-now"),
    ("Related Work",         "1 table positioning vs 3-5 baselines"),
    ("Method Overview",      "1 architecture figure"),
    ("Method Detail",        "key formula + 1 algorithm box"),
    ("Setup",                "config table: dataset / metric / hardware / seeds"),
    ("Main Results",         "1 figure: SR vs baseline"),
    ("Ablation",             "1 table or figure"),
    ("Conclusion",           "3 bullets + 3 future-work bullets"),
]

BEAMER_PREAMBLE = r"""\documentclass[aspectratio=169]{beamer}
\usetheme{metropolis}
\usepackage{graphicx}
\title{TBD}
\author{TBD}
\date{TBD}
\begin{document}
\frame{\titlepage}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="paper")
    ap.add_argument("--theme", default="metropolis")
    ap.add_argument("--out",   default="paper/slides")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    tex = [BEAMER_PREAMBLE.replace("metropolis", args.theme)]
    notes = ["# Speaker notes\n"]
    for i, (title, hint) in enumerate(OUTLINE, 1):
        tex.append(f"\\begin{{frame}}{{{title}}}\n  % hint: {hint}\n  TBD\n\\end{{frame}}\n")
        notes.append(f"## Slide {i}: {title}\n- hint: {hint}\n- talk-track: (~45s)\n- emphasize: \n")
    tex.append(r"\end{document}")
    (out / "slides.tex").write_text("\n".join(tex))
    (out / "speaker_notes.md").write_text("\n".join(notes))
    print(f"✅ {out}/slides.tex + speaker_notes.md (10 slides)")
    print("→ fill TBD via /paper-mode / Agent; compile with pdflatex")

if __name__ == "__main__":
    main()
