"""Overview figure of the western Kansas transect: fallow share per county and the engine test per site.

Usage:
    python3 pipelines/fields/plot_transect.py

Input:  data/processed/counties.geojson, data/processed/fields.geojson, docs/transect_test.csv
Output: docs/img/transect_overview.png
"""
import csv, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from shapely.geometry import shape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def main():
    counties = json.load(open(os.path.join(ROOT, "data", "processed", "counties.geojson")))["features"]
    fields = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson")))["features"]
    test = [r for r in csv.DictReader(l for l in open(os.path.join(ROOT, "docs", "transect_test.csv")) if not l.startswith("#"))]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 6), dpi=160, gridspec_kw={"width_ratios": [1.25, 1]})
    norm = colors.Normalize(0, 0.36); cmap = cm.get_cmap("YlOrBr")
    for c in counties:
        g = shape(c["geometry"]); p = c["properties"]
        for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            ax.fill(*poly.exterior.xy, color=cmap(norm(p["fallow_share_latest"])), edgecolor="white", linewidth=0.6)
        ax.text(p["lon"], p["lat"], f"{100 * p['fallow_share_latest']:.0f}", ha="center", va="center", fontsize=6.5, color="#333333")
    sites = {}
    for f in fields:
        sites.setdefault(f["properties"]["site"], []).append((f["properties"]["lon"], f["properties"]["lat"]))
    for name, pts in sites.items():
        x = sum(p[0] for p in pts) / len(pts); y = sum(p[1] for p in pts) / len(pts)
        ax.plot(x, y, marker="*", color="black", markersize=16, markeredgecolor="white")
        ax.annotate(f"{name} ({len(pts)} fields)", (x, y), xytext=(8, 8), textcoords="offset points", fontsize=9, weight="bold")
    ax.set_aspect(1 / 0.78); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_title("Fallow share of dryland cropland, % (USDA Cropland Data Layer, latest year)\n46 Kansas counties west of 98.3° W; drier to the west", fontsize=10)
    fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, fraction=0.03, pad=0.02).set_label("fallow share")
    rows = [r for r in test if r["site"] in ("Tribune", "Colby", "Hays")]
    series = (("wf", "Wheat - fallow", "#d9a441"), ("wsf", "Wheat - sorghum - fallow", "#c0392b"), ("wcf", "Wheat - corn - fallow", "#2e86c1"))
    for i, (key, label, colour) in enumerate(series):
        xs = [j + (i - 1) * 0.27 for j in range(len(rows))]
        vals = [float(r[f"{key}_net"]) for r in rows]
        bx.bar(xs, vals, width=0.25, color=colour, label=label)
        for x, v, r in zip(xs, vals, rows):
            bx.text(x, v + (3 if v >= 0 else -9), f"{v:+.0f}\n{100 * float(r[f'{key}_profit']):.0f}%", ha="center", fontsize=7.5)
    bx.axhline(0, color="black", linewidth=0.8)
    bx.set_xticks(range(len(rows))); bx.set_xticklabels([f"{r['site']}\n{r['rain_mm']} mm rain/yr" for r in rows])
    bx.set_ylabel("mean net return, 2025 USD per acre per year"); bx.set_ylim(-95, 105)
    bx.set_title("Rotation replay 1996-2025, quick test at three sites\n(label: mean return and share of years with a profit; corn at Hays not yet checked)", fontsize=10)
    bx.legend(fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, "docs", "img", "transect_overview.png")); print("saved")

if __name__ == "__main__":
    main()
