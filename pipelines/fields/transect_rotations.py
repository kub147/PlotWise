"""Classify every delineated field of the transect by rotation: statistics per county and a map.

Usage:
    python3 pipelines/fields/transect_rotations.py

Input:  data/raw/fields/candidates_<fips>.geojson for the counties in data/processed/counties.geojson
Output: data/processed/county_field_rotations.json   per county: fields, area and share of area per rotation class
        data/processed/county_fields.geojson          light polygons for the three demo counties only (app map)
        docs/img/transect_fields.png                  all fields coloured by rotation
"""
import collections, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from shapely.geometry import shape, mapping
from county_rotations import STYLE, classify

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DEMO_COUNTIES = ("20071", "20193", "20051")

def main():
    counties = json.load(open(os.path.join(ROOT, "data", "processed", "counties.geojson")))["features"]
    demo = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson")))["features"]
    fig, ax = plt.subplots(figsize=(13, 10.5), dpi=200)
    out, light, total_fields, total_area, missing = {}, [], 0, 0.0, []
    overall = collections.Counter()
    for c in counties:
        p = c["properties"]; fips = p["county_fips"]
        g = shape(c["geometry"])
        for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            ax.plot(*poly.exterior.xy, color="#999999", linewidth=0.4)
        path = os.path.join(ROOT, "data", "raw", "fields", f"candidates_{fips}.geojson")
        if not os.path.exists(path):
            missing.append(p["name"]); continue
        feats = json.load(open(path))["features"]
        count, area = collections.Counter(), collections.Counter()
        for f in feats:
            q = f["properties"]; rot = classify(q["sequence"]); count[rot] += 1; area[rot] += q["area_ha"]
            geom = shape(f["geometry"])
            for poly in (geom.geoms if geom.geom_type == "MultiPolygon" else [geom]):
                ax.fill(*poly.exterior.xy, color=STYLE[rot][1], linewidth=0)
            if fips in DEMO_COUNTIES:
                light.append({"type": "Feature", "geometry": json.loads(json.dumps(mapping(geom.simplify(0.0003))), parse_float=lambda x: round(float(x), 5)),
                              "properties": {"county_id": p["county_id"], "rotation": rot, "sequence": q["sequence"], "area_ha": q["area_ha"]}})
        tot = sum(area.values()) or 1.0
        out[p["county_id"]] = dict(name=p["name"], lon=p["lon"], fields=len(feats), area_ha=round(sum(area.values())),
                                   rotations={k: dict(fields=count[k], share_of_area=round(area[k] / tot, 3)) for k in STYLE},
                                   fallow_based_share=round(1 - area["no fallow"] / tot, 3),
                                   three_year_share=round((area["W-S-F"] + area["W-C-F"] + area["W-F to 3-year"]) / tot, 3))
        total_fields += len(feats); total_area += sum(area.values()); overall.update(area)
    for f in demo:
        ax.plot(f["properties"]["lon"], f["properties"]["lat"], marker="o", color="black", markersize=3)
    for site in sorted({f["properties"]["site"] for f in demo}):
        pts = [(f["properties"]["lon"], f["properties"]["lat"]) for f in demo if f["properties"]["site"] == site]
        ax.annotate(site, (sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)), xytext=(8, 8),
                    textcoords="offset points", fontsize=10, weight="bold", bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1))
    ax.set_aspect(1 / 0.78); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    years = "2018-2025"
    ax.set_title(f"Western Kansas: crop rotation on {total_fields:,} fields ({total_area / 1e6:.2f} million ha), {years}\n"
                 "fields of at least 40 ha with one crop sequence, from the USDA Cropland Data Layer", fontsize=11)
    ax.legend(handles=[Patch(color=c, label=f"{l} - {100 * overall[k] / total_area:.0f}% of area") for k, (l, c) in STYLE.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=3, fontsize=8, frameon=False)
    fig.savefig(os.path.join(ROOT, "docs", "img", "transect_fields.png"), bbox_inches="tight")
    json.dump(dict(years=years, note="Fields of at least 40 ha with an identical CDL crop sequence in all pixels and cropland in every year; a sample of clean fields, not all cropland.",
                   fields=total_fields, area_ha=round(total_area),
                   share_of_area={k: round(overall[k] / total_area, 3) for k in STYLE}, counties=out),
              open(os.path.join(ROOT, "data", "processed", "county_field_rotations.json"), "w"), indent=1)
    json.dump({"type": "FeatureCollection", "features": light}, open(os.path.join(ROOT, "data", "processed", "county_fields.geojson"), "w"), separators=(",", ":"))
    print(f"{total_fields} fields, {total_area / 1e6:.2f} Mha in {len(out)} counties; missing: {missing}")
    for k in STYLE: print(f"  {100 * overall[k] / total_area:5.1f}%  {STYLE[k][0]}")
    print("west to east (share of field area):")
    for lo, hi in ((-102.1, -101), (-101, -100), (-100, -99), (-99, -98.3)):
        cs = [v for v in out.values() if lo <= v["lon"] < hi]; a = sum(v["area_ha"] for v in cs) or 1
        w = lambda key: sum(v["rotations"][key]["share_of_area"] * v["area_ha"] for v in cs) / a
        print(f"  lon {lo:.0f}..{hi:.1f}: {len(cs):2d} counties, {sum(v['fields'] for v in cs):6d} fields | W-F {100*w('W-F'):4.1f}% | W-S-F {100*w('W-S-F'):4.1f}% | W-C-F {100*w('W-C-F'):4.1f}% | no fallow {100*w('no fallow'):4.1f}%")

if __name__ == "__main__":
    main()
