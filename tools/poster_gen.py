#!/usr/bin/env python3
"""tools/poster_gen.py — emit beamerposter .tex skeleton for A0/A1 poster.

5 sections: Problem / Method / Setup / Results / Discussion + abstract block +
bibtex corner. Agent fills TBD via /paper-mode.
"""
import argparse, sys
from pathlib import Path

SIZES = {
    "A0": ("84.1cm", "118.9cm"),
    "A1": ("59.4cm", "84.1cm"),
}

TEMPLATE = r"""\documentclass[final,t,xcolor=table]{beamer}
\usepackage[size=custom,width=%(w)s,height=%(h)s,scale=1.0,orientation=%(o)s]{beamerposter}
\usepackage{multicol}
\usetheme{Madrid}
\title{TBD}
\author{TBD}
\institute{TBD}
\date{}
\begin{document}
\begin{frame}{}
  \maketitle
  \begin{columns}[t]
    \column{0.48\linewidth}
      \begin{block}{Problem}TBD\end{block}
      \begin{block}{Method}TBD\end{block}
      \begin{block}{Setup}TBD\end{block}
    \column{0.48\linewidth}
      \begin{block}{Results}TBD\end{block}
      \begin{block}{Discussion}TBD\end{block}
      \begin{block}{References}\scriptsize\bibliographystyle{plain}\bibliography{references}\end{block}
  \end{columns}
\end{frame}
\end{document}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="paper")
    ap.add_argument("--size", default="A0", choices=list(SIZES))
    ap.add_argument("--orient", default="portrait", choices=["portrait", "landscape"])
    ap.add_argument("--out", default="paper/poster")
    args = ap.parse_args()

    w, h = SIZES[args.size]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "poster.tex").write_text(TEMPLATE % {"w": w, "h": h, "o": args.orient})
    print(f"✅ {out}/poster.tex (size={args.size}, orient={args.orient})")
    print("→ fill TBD via Agent; compile: pdflatex poster.tex")

if __name__ == "__main__":
    main()
