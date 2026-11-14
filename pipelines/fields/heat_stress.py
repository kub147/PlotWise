"""Field-scale heat stress from ECOSTRESS land-surface temperature (70 m) on hot summer afternoons.

Usage:
    EE_PROJECT=<your-ee-project> python3 pipelines/fields/heat_stress.py

For a few clear, hot ECOSTRESS overpasses it reports
  - mean land-surface temperature of each demo field, with the crop CDL shows for that year
  - mean temperature by crop class over the surrounding area (about 25 x 20 km), to show how much cooler a
    transpiring crop is than fallow or stubble on the same afternoon
and renders a temperature map with the demo fields outlined (docs/img/ecostress_<date>.png).

Output: data/processed/heat/ecostress_summary.json
"""
import datetime as dt, json, os, urllib.request
import ee

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SCENES = ["2023_07_30_200805_28721_006_14SKH", "2024_08_17_191142_34675_009_14SKH", "2022_06_16_211220_22371_009_14SKH",
          "2021_08_24_181434_17774_012_14SKH"]
CLASSES = {24: "winter wheat (ripe in June, stubble from July)", 61: "fallow", 4: "sorghum", 1: "corn", 176: "grass/pasture"}

def main():
    ee.Initialize(project=os.environ["EE_PROJECT"])
    fc = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson")))
    fields = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]).buffer(-70), {"field_id": f["properties"]["field_id"]})
                                   for f in fc["features"]])
    outlines = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"])) for f in fc["features"]])
    box = outlines.geometry().bounds().buffer(4000).bounds()
    cdl = ee.ImageCollection("USDA/NASS/CDL")
    out = []
    for sid in SCENES:
        img = ee.Image(f"NASA/ECOSTRESS/L2T_LSTE/V2/{sid}")
        t = dt.datetime.fromtimestamp(img.get("system:time_start").getInfo() / 1000, dt.timezone.utc)
        lst = img.select("LST").updateMask(img.select("cloud").eq(0)).subtract(273.15).rename("lst_c")
        crops = cdl.filter(ee.Filter.calendarRange(t.year, t.year, "year")).first().select("cropland")
        per_field = {f["properties"]["field_id"]: f["properties"].get("mean")
                     for f in lst.reduceRegions(fields, ee.Reducer.mean(), 70).getInfo()["features"]}
        grouped = lst.addBands(crops).reduceRegion(ee.Reducer.mean().combine(ee.Reducer.count(), "", True).group(1, "cdl"),
                                                   box, 70, maxPixels=1e8).getInfo()["groups"]
        by_class = {CLASSES[g["cdl"]]: dict(mean_c=round(g["mean"], 1), pixels=g["count"]) for g in grouped if g["cdl"] in CLASSES}
        rec = dict(scene=sid, time_utc=t.strftime("%Y-%m-%d %H:%M"), local_solar_time=(t - dt.timedelta(hours=6.8)).strftime("%H:%M"),
                   fields={k: dict(lst_c=round(v, 1) if v is not None else None,
                                   crop=next(f["properties"]["crop_history_names"].get(str(t.year)) for f in fc["features"] if f["properties"]["field_id"] == k))
                           for k, v in sorted(per_field.items())},
                   by_crop_class=by_class)
        out.append(rec)
        print(rec["time_utc"], "UTC (about", rec["local_solar_time"], "local solar time)")
        for k, v in rec["fields"].items(): print("   ", k, v)
        for k, v in sorted(by_class.items(), key=lambda x: x[1]["mean_c"]): print("      %-42s %5.1f C  (%d px)" % (k, v["mean_c"], v["pixels"]))
        stats = lst.reduceRegion(ee.Reducer.percentile([2, 98]), box, 70, maxPixels=1e8).getInfo()
        vis = lst.visualize(min=stats["lst_c_p2"], max=stats["lst_c_p98"], palette=["313695", "74add1", "e0f3f8", "fee090", "f46d43", "a50026"])
        vis = vis.blend(ee.Image().byte().paint(outlines, 1, 3).visualize(palette=["000000"]))
        url = vis.getThumbURL({"region": box, "dimensions": 1400, "format": "png"})
        name = f"ecostress_{t.strftime('%Y-%m-%d')}.png"
        urllib.request.urlretrieve(url, os.path.join(ROOT, "docs", "img", name))
        rec["image"] = f"docs/img/{name}"; rec["colour_scale_c"] = [round(stats["lst_c_p2"], 1), round(stats["lst_c_p98"], 1)]
    path = os.path.join(ROOT, "data", "processed", "heat", "ecostress_summary.json")
    json.dump(dict(source="NASA ECOSTRESS L2T LSTE V2 (70 m), cloud-masked; crop classes from USDA CDL of the same year",
                   note="Surface temperature, not air temperature. One afternoon per scene; values depend on overpass time.",
                   scenes=out), open(path, "w"), indent=1)
    print("saved", path)

if __name__ == "__main__":
    main()
