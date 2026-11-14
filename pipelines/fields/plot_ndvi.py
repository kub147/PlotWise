"""Plot the Landsat NDVI history of each demo field with the CDL crop of every year marked.

Usage:
    python3 pipelines/fields/plot_ndvi.py [--start 2012]

Output: docs/img/ndvi_<field_id>.png
"""
import argparse, csv, datetime as dt, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
COLOUR = {"F": "#e8d9b5", "W": "#f6e58d", "S": "#f5b7b1", "C": "#aed6f1", "O": "#e5e7e9"}
NAME = {"F": "fallow", "W": "winter wheat", "S": "sorghum", "C": "corn", "O": "other"}
LETTER = {24: "W", 61: "F", 4: "S", 1: "C"}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--start", type=int, default=2012); a = ap.parse_args()
    fields = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson")))["features"]
    for f in fields:
        p = f["properties"]; fid = p["field_id"]
        rows = [(dt.date.fromisoformat(r["date"]), float(r["ndvi"]))
                for r in csv.DictReader(open(os.path.join(ROOT, "data", "processed", "ndvi", f"{fid}.csv")))]
        rows = [r for r in rows if r[0].year >= a.start]
        fig, ax = plt.subplots(figsize=(13, 3.8), dpi=160)
        years = [int(y) for y in p["crop_history"] if int(y) >= a.start]
        for y in years:
            letter = LETTER.get(p["crop_history"][str(y)], "O")
            ax.axvspan(dt.date(y, 1, 1), dt.date(y + 1, 1, 1), color=COLOUR[letter], alpha=0.75, linewidth=0)
            ax.text(dt.date(y, 7, 1), 0.93, letter, ha="center", va="center", fontsize=11, weight="bold", color="#444444")
        ax.plot([r[0] for r in rows], [r[1] for r in rows], color="#1e8449", linewidth=1.1, marker="o", markersize=2.2)
        ax.axhline(p["ndvi_bare_threshold"], color="#7f8c8d", linestyle="--", linewidth=0.9)
        ax.text(rows[0][0], p["ndvi_bare_threshold"] + 0.012, " no green cover below this line", fontsize=7.5, color="#566573")
        ax.set_ylim(0, 1); ax.set_xlim(dt.date(a.start, 1, 1), dt.date(years[-1] + 1, 1, 1)); ax.set_ylabel("NDVI (field mean)")
        ax.set_title(f"{fid} - {p['name']}\nGreenness from Landsat (line) against the crop reported by the USDA Cropland Data Layer (background)", fontsize=10)
        ax.legend(handles=[Patch(color=COLOUR[k], label=f"{k} = {NAME[k]}") for k in "WFSCO"], loc="upper center",
                  bbox_to_anchor=(0.5, -0.1), ncol=5, fontsize=8, frameon=False)
        fig.savefig(os.path.join(ROOT, "docs", "img", f"ndvi_{fid}.png"), bbox_inches="tight"); plt.close(fig)
        print("saved", fid)

if __name__ == "__main__":
    main()
