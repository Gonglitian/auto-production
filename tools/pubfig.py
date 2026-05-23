#!/usr/bin/env python3
"""tools/pubfig.py — convert PNG figures to publication-ready PDF/SVG.

If raw data JSON exists next to the PNG (figures/<name>.json), repickle the
plot in venue-specific rcParams. Otherwise fall back to high-DPI rasterize.

Requires matplotlib at runtime; skips gracefully if missing.
"""
import argparse, json, shutil, sys
from pathlib import Path

VENUE_RC = {
    "NeurIPS":  {"font.family": "serif", "font.size": 9,  "savefig.dpi": 300,
                 "axes.linewidth": 0.8,  "axes.labelsize": 9, "legend.fontsize": 8},
    "CoRL":     {"font.family": "serif", "font.size": 9,  "savefig.dpi": 300},
    "ICLR":     {"font.family": "serif", "font.size": 10, "savefig.dpi": 300},
    "Nature":   {"font.family": "sans-serif", "font.size": 7, "savefig.dpi": 600},
}

def safe_imports():
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return matplotlib, plt
    except Exception:
        return None, None

def convert_one(input_png, venue, output_pdf):
    mpl, plt = safe_imports()
    if mpl is None:
        shutil.copy(input_png, output_pdf.with_suffix(".png"))
        print(f"⚠️  matplotlib unavailable; copied PNG → {output_pdf.with_suffix('.png')}")
        return

    mpl.rcParams.update(VENUE_RC.get(venue, VENUE_RC["NeurIPS"]))

    raw = Path(str(input_png).replace(".png", ".json"))
    if raw.exists():
        d = json.loads(raw.read_text())
        plt.figure(figsize=tuple(d.get("figsize", [5.5, 3.4])))
        for s in d.get("series", []):
            plt.plot(s["x"], s["y"], label=s.get("label", ""))
        plt.xlabel(d.get("xlabel", "")); plt.ylabel(d.get("ylabel", ""))
        plt.title(d.get("title", "")); plt.legend()
    else:
        img = plt.imread(input_png)
        plt.figure(figsize=(5.5, 3.4))
        plt.imshow(img); plt.axis("off")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_pdf, format="pdf")
    plt.close()
    print(f"✅ {input_png} → {output_pdf}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="NeurIPS")
    ap.add_argument("--input", help="single PNG")
    ap.add_argument("--output", help="output PDF path")
    ap.add_argument("--batch", action="store_true", help="convert all figures/*.png to paper/figures/*.pdf")
    args = ap.parse_args()

    if args.batch:
        for png in Path("figures").glob("*.png"):
            out = Path("paper/figures") / (png.stem + ".pdf")
            convert_one(png, args.venue, out)
    else:
        if not (args.input and args.output): sys.exit("--input + --output  OR  --batch")
        convert_one(Path(args.input), args.venue, Path(args.output))

if __name__ == "__main__":
    main()
