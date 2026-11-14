"""Classify every delineated field in the county by rotation and write a light GeoJSON plus a map.

Usage:
    python3 pipelines/fields/county_rotations.py

Input:  data/raw/fields/candidates_<fips>.geojson (from delineate_fields.py)
Output: data/processed/county_fields.geojson  (one polygon per field: rotation, sequence, area_ha)
        data/processed/county_rotation_summary.json
        docs/img/county_rotations.png
"""
import collections, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from shapely.geometry import shape, mapping

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
FIPS = "20071"
STYLE = {  # rotation -> (label, colour)
    "W-F": ("Wheat - fallow (1 crop in 2 years)", "#d9a441"),
    "W-S-F": ("Wheat - sorghum - fallow", "#c0392b"),
    "W-C-F": ("Wheat - corn - fallow", "#2e86c1"),
    "W-F to 3-year": ("Moved from wheat - fallow to a 3-year rotation", "#8e44ad"),
    "no fallow": ("No fallow in 8 years", "#1e8449"),
    "other with fallow": ("Other sequences with fallow", "#bfc5c9"),
}

def cyclic(seq, pattern):
    return any(all(seq[i] == pattern[(i + k) % len(pattern)] for i in range(len(seq))) for k in range(len(pattern)))

def classify(seq):
    if cyclic(seq, "WF"): return "W-F"
    if cyclic(seq, "WSF"): return "W-S-F"
    if cyclic(seq, "WCF"): return "W-C-F"
    if "F" not in seq: return "no fallow"
    if cyclic(seq[:4], "WF") and any(cyclic(seq[i:], p) for i in (3, 4) for p in ("WSF", "WCF")): return "W-F to 3-year"
    return "other with fallow"

def main():
    src = json.load(open(os.path.join(ROOT, "data", "raw", "fields", f"candidates_{FIPS}.geojson")))
    demo = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson")))
    feats, count, area = [], collections.Counter(), collections.Counter()
    for f in src["features"]:
        p = f["properties"]; rot = classify(p["sequence"])
        geom = shape(f["geometry"]).simplify(0.0003)
        coords = json.loads(json.dumps(mapping(geom)), parse_float=lambda x: round(float(x), 5))
        feats.append({"type": "Feature", "geometry": coords,
                      "properties": {"rotation": rot, "sequence": p["sequence"], "area_ha": p["area_ha"]}})
        count[rot] += 1; area[rot] += p["area_ha"]
    json.dump({"type": "FeatureCollection", "features": feats},
              open(os.path.join(ROOT, "data", "processed", "county_fields.geojson"), "w"), separators=(",", ":"))
    total = sum(area.values())
    summary = dict(county_fips=FIPS, years=f"{src['features'][0]['properties']['first_year']}-{src['features'][0]['properties']['last_year']}",
                   note="Fields of at least 40 ha with the same CDL crop sequence in all pixels and cropland in every year. "
                        "This is a sample of clean fields, not all cropland in the county.",
                   fields=len(feats), area_ha=round(total),
                   rotations={k: dict(label=STYLE[k][0], fields=count[k], area_ha=round(area[k]), share_of_area=round(area[k] / total, 3)) for k in STYLE})
    json.dump(summary, open(os.path.join(ROOT, "data", "processed", "county_rotation_summary.json"), "w"), indent=1)
    for k, v in summary["rotations"].items(): print(f"{v['fields']:5d} fields {v['area_ha']:7d} ha {100 * v['share_of_area']:5.1f}%  {v['label']}")

    fig, ax = plt.subplots(figsize=(11, 9), dpi=160)
    for f in feats:
        g = shape(f["geometry"])
        for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            ax.fill(*poly.exterior.xy, color=STYLE[f["properties"]["rotation"]][1], linewidth=0)
    for f in demo["features"]:
        g = shape(f["geometry"]); c = g.centroid
        ax.plot(*g.exterior.xy, color="black", linewidth=1.2)
        ax.annotate(f["properties"]["field_id"][-3:], (c.x, c.y), xytext=(6, 6), textcoords="offset points", fontsize=8, weight="bold")
    ax.plot(-101.75, 38.47, marker="*", color="black", markersize=13)
    ax.annotate("K-State Tribune station", (-101.75, 38.47), xytext=(8, -12), textcoords="offset points", fontsize=8)
    ax.set_aspect(1 / 0.783); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_title(f"Greeley County, Kansas: crop rotation on {len(feats):,} fields, {summary['years']}\n(from USDA Cropland Data Layer sequences; demo fields outlined)", fontsize=11)
    ax.legend(handles=[Patch(color=c, label=f"{l} - {count[k]} fields, {100 * area[k] / total:.0f}% of area") for k, (l, c) in STYLE.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=2, fontsize=8, frameon=False)
    fig.savefig(os.path.join(ROOT, "docs", "img", "county_rotations.png"), bbox_inches="tight")
    print("saved map and", len(feats), "fields")

if __name__ == "__main__":
    main()
