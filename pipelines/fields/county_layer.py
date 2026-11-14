"""County layer for the western Kansas transect: one point, soil and cropping statistics per county.

Usage:
    EE_PROJECT=<your-ee-project> python3 pipelines/fields/county_layer.py

For every Kansas county west of 98.3 W (where fallow is still part of dryland rotations) it writes
  - a simplified outline and a centroid (`lon`, `lat`) for the weather pipeline
  - cropland statistics from the Cropland Data Layer, first (2008) and latest year: hectares of wheat, fallow,
    sorghum and corn, the fallow share and the ratio of summer crops to wheat
  - plant-available water capacity to 150 cm from SSURGO around the centroid (2 km square)

Output: data/processed/counties.geojson (id `county_id` = "ks" + 3-digit county code, e.g. ks071)
"""
import json, os
import ee
from shapely.geometry import shape, mapping
from soil_sda import field_soil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
WEST_OF = -98.3
CROPS = {24: "wheat", 61: "fallow", 4: "sorghum", 1: "corn"}

def main():
    ee.Initialize(project=os.environ["EE_PROJECT"])
    counties = ee.FeatureCollection("TIGER/2018/Counties").filter(ee.Filter.eq("STATEFP", "20"))
    counties = counties.map(lambda f: f.set("cx", f.geometry().centroid(100).coordinates().get(0),
                                            "cy", f.geometry().centroid(100).coordinates().get(1)))
    counties = counties.filter(ee.Filter.lt("cx", WEST_OF))
    cdl = ee.ImageCollection("USDA/NASS/CDL")
    last = ee.Date(cdl.aggregate_max("system:time_start")).get("year").getInfo()
    stats = {}
    for y in (2008, last):
        img = cdl.filter(ee.Filter.calendarRange(y, y, "year")).first().select("cropland")
        res = img.reduceRegions(counties.select(["GEOID"]), ee.Reducer.frequencyHistogram(), 90, tileScale=4).getInfo()["features"]
        for f in res:
            h = f["properties"]["histogram"]
            stats.setdefault(f["properties"]["GEOID"], {})[y] = {n: float(h.get(str(c), 0)) * 0.81 for c, n in CROPS.items()}   # 90 m pixel = 0.81 ha
    feats = []
    for f in counties.getInfo()["features"]:
        p = f["properties"]; fips = p["GEOID"]; lon, lat = p["cx"], p["cy"]
        geom = shape(f["geometry"]).simplify(0.005)
        d = 0.01
        try:
            soil = field_soil(f"POLYGON(({lon-d} {lat-d},{lon+d} {lat-d},{lon+d} {lat+d},{lon-d} {lat+d},{lon-d} {lat-d}))")
            awc, series = (soil["awc_mm"] if soil["awc_mm"] and soil["awc_mm"] >= 100 else None), soil["soil_series"]
        except Exception:
            awc, series = None, None
        out = dict(county_id="ks" + fips[2:], county_fips=fips, name=p["NAME"], lon=round(lon, 4), lat=round(lat, 4),
                   awc_mm=awc, soil_series=series, cdl_years=[2008, last])
        for y, tag in ((2008, "2008"), (last, "latest")):
            s = stats[fips][y]; total = sum(s.values())
            out[f"fallow_share_{tag}"] = round(s["fallow"] / total, 3) if total else None
            out[f"summer_to_wheat_{tag}"] = round((s["sorghum"] + s["corn"]) / s["wheat"], 2) if s["wheat"] else None
            if tag == "latest":
                out.update({f"{k}_ha": round(v) for k, v in s.items()})
        feats.append({"type": "Feature", "properties": out,
                      "geometry": json.loads(json.dumps(mapping(geom)), parse_float=lambda x: round(float(x), 4))})
    feats.sort(key=lambda f: f["properties"]["county_id"])
    json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(ROOT, "data", "processed", "counties.geojson"), "w"), separators=(",", ":"))
    print(len(feats), "counties; missing soil:", [f["properties"]["name"] for f in feats if f["properties"]["awc_mm"] is None])
    for f in sorted(feats, key=lambda f: f["properties"]["lon"])[::6]:
        p = f["properties"]; print(f"  {p['county_id']} {p['name']:10s} lon {p['lon']:8.2f}  fallow {p['fallow_share_2008']} -> {p['fallow_share_latest']}  awc {p['awc_mm']}")

if __name__ == "__main__":
    main()
