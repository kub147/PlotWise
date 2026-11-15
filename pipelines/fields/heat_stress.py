"""Field-scale heat stress from ECOSTRESS land-surface temperature (70 m) on hot summer afternoons.

Usage:
    EE_PROJECT=<your-ee-project> python3 pipelines/fields/heat_stress.py [--site Colby Hays]

For a few clear, hot ECOSTRESS overpasses at each site (Tribune, Colby, Hays) it reports
  - mean land-surface temperature of each demo field of the site, with the crop CDL shows for that year
  - mean temperature by crop class over the surrounding area (about 25 x 20 km), to show how much cooler a
    transpiring crop is than fallow or stubble on the same afternoon
and renders a temperature map with the demo fields outlined (docs/img/ecostress_<date>.png for Tribune,
docs/img/ecostress_<site>_<date>.png for the other sites).

Output: data/processed/heat/ecostress_summary.json. Each scene carries its site and the bounds of its image
(west, south, east, north in degrees), so the app can lay the image over the map.
With --site only those sites are redrawn; the scenes of the other sites are kept as they are in the file.
"""
import argparse, datetime as dt, json, os, urllib.request
import ee

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
COLLECTION = "NASA/ECOSTRESS/L2T_LSTE/V2"
# Clear, hot afternoon overpasses per site, picked by hand from the scenes that cover the whole area without cloud.
# A scene is one or more tiles of the same overpass: the Hays area lies on the edge between two tiles.
SITES = {
    "Tribune": [["2023_07_30_200805_28721_006_14SKH"], ["2024_08_17_191142_34675_009_14SKH"], ["2022_06_16_211220_22371_009_14SKH"],
                ["2021_08_24_181434_17774_012_14SKH"]],
    "Colby": [["2025_08_18_180014_40359_006_14SLJ"], ["2022_08_13_215024_23273_012_14SLJ"], ["2022_08_05_183532_23146_006_14SLJ"],
              ["2021_08_24_181434_17774_012_14SLJ"]],
    "Hays": [["2025_08_18_180014_40359_006_14SMJ", "2025_08_18_180014_40359_006_14SMH"],
             ["2025_08_10_211534_40237_009_14SMJ", "2025_08_10_211534_40237_009_14SMH"],
             ["2023_08_03_183114_28782_006_14SMJ", "2023_08_03_183114_28782_006_14SMH"],
             ["2022_08_13_215024_23273_012_14SMJ", "2022_08_13_215024_23273_012_14SMH"]],
}
CLASSES = {24: "winter wheat (ripe in June, stubble from July)", 61: "fallow", 4: "sorghum", 1: "corn", 176: "grass/pasture"}
PALETTE = ["313695", "74add1", "e0f3f8", "fee090", "f46d43", "a50026"]

def run_site(site, features):
    fields = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]).buffer(-70), {"field_id": f["properties"]["field_id"]})
                                   for f in features])
    outlines = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"])) for f in features])
    box = outlines.geometry().bounds().buffer(4000).bounds()
    ring = box.coordinates().getInfo()[0]
    bounds = [round(v, 5) for v in (min(x for x, _ in ring), min(y for _, y in ring), max(x for x, _ in ring), max(y for _, y in ring))]
    # Hours between UTC and local solar time at the site (6.8 at Tribune).
    solar_offset = round(-(bounds[0] + bounds[2]) / 2 / 15, 1)
    cdl = ee.ImageCollection("USDA/NASS/CDL")
    out = []
    for ids in SITES[site]:
        tiles = [ee.Image(f"{COLLECTION}/{sid}") for sid in ids]
        t = dt.datetime.fromtimestamp(tiles[0].get("system:time_start").getInfo() / 1000, dt.timezone.utc)
        masked = [img.select("LST").updateMask(img.select("cloud").eq(0)) for img in tiles]
        lst = (masked[0] if len(masked) == 1 else ee.ImageCollection(masked).mosaic()).subtract(273.15).rename("lst_c")
        crops = cdl.filter(ee.Filter.calendarRange(t.year, t.year, "year")).first().select("cropland")
        per_field = {f["properties"]["field_id"]: f["properties"].get("mean")
                     for f in lst.reduceRegions(fields, ee.Reducer.mean(), 70).getInfo()["features"]}
        grouped = lst.addBands(crops).reduceRegion(ee.Reducer.mean().combine(ee.Reducer.count(), "", True).group(1, "cdl"),
                                                   box, 70, maxPixels=1e8).getInfo()["groups"]
        by_class = {CLASSES[g["cdl"]]: dict(mean_c=round(g["mean"], 1), pixels=g["count"]) for g in grouped if g["cdl"] in CLASSES}
        clear = lst.mask().reduceRegion(ee.Reducer.mean(), box, 70, maxPixels=1e8).getInfo()["lst_c"]
        rec = dict(scene="+".join(ids), site=site, time_utc=t.strftime("%Y-%m-%d %H:%M"),
                   local_solar_time=(t - dt.timedelta(hours=solar_offset)).strftime("%H:%M"),
                   fields={k: dict(lst_c=round(v, 1) if v is not None else None,
                                   crop=next(f["properties"]["crop_history_names"].get(str(t.year)) for f in features if f["properties"]["field_id"] == k))
                           for k, v in sorted(per_field.items())},
                   by_crop_class=by_class)
        out.append(rec)
        print(site, rec["time_utc"], "UTC (about", rec["local_solar_time"], "local solar time), clear over %.0f%% of the area" % (100 * clear))
        for k, v in rec["fields"].items(): print("   ", k, v)
        for k, v in sorted(by_class.items(), key=lambda x: x[1]["mean_c"]): print("      %-42s %5.1f C  (%d px)" % (k, v["mean_c"], v["pixels"]))
        stats = lst.reduceRegion(ee.Reducer.percentile([2, 98]), box, 70, maxPixels=1e8).getInfo()
        vis = lst.visualize(min=stats["lst_c_p2"], max=stats["lst_c_p98"], palette=PALETTE)
        vis = vis.blend(ee.Image().byte().paint(outlines, 1, 3).visualize(palette=["000000"]))
        # Web Mercator, the projection of the app's map, so the image can be laid over it as it is.
        url = vis.getThumbURL({"region": ee.Geometry.Rectangle(bounds, None, False), "crs": "EPSG:3857", "dimensions": 1400, "format": "png"})
        name = f"ecostress_{t.strftime('%Y-%m-%d')}.png" if site == "Tribune" else f"ecostress_{site.lower()}_{t.strftime('%Y-%m-%d')}.png"
        urllib.request.urlretrieve(url, os.path.join(ROOT, "docs", "img", name))
        rec["image"] = f"docs/img/{name}"; rec["colour_scale_c"] = [round(stats["lst_c_p2"], 1), round(stats["lst_c_p98"], 1)]
        rec["bounds"] = bounds
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", nargs="+", choices=list(SITES), default=list(SITES))
    args = parser.parse_args()
    ee.Initialize(project=os.environ["EE_PROJECT"])
    fc = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson"), encoding="utf-8"))
    path = os.path.join(ROOT, "data", "processed", "heat", "ecostress_summary.json")
    kept = json.load(open(path, encoding="utf-8"))["scenes"] if os.path.exists(path) else []
    scenes = []
    for site in SITES:
        if site in args.site:
            scenes += run_site(site, [f for f in fc["features"] if f["properties"]["site"] == site])
        else:
            # Scenes written before the file had sites are those of Tribune.
            scenes += [s for s in kept if s.get("site", "Tribune") == site]
    json.dump(dict(source="NASA ECOSTRESS L2T LSTE V2 (70 m), cloud-masked; crop classes from USDA CDL of the same year",
                   note="Surface temperature, not air temperature. One afternoon per scene; values depend on overpass time.",
                   scenes=scenes), open(path, "w", encoding="utf-8"), indent=1)
    print("saved", path)

if __name__ == "__main__":
    main()
