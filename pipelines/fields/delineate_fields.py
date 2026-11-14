"""Delineate field polygons from crop sequences in the USDA Cropland Data Layer (Google Earth Engine).

Usage:
    EE_PROJECT=<your-ee-project> python3 delineate_fields.py --fips 20071 --start 2018 --end 2025 --min-ha 40

Same idea as the USDA NASS Crop Sequence Boundaries: neighbouring pixels that grew the same crop sequence over
eight years belong to the same field. Each year's CDL is simplified to six classes and smoothed with a 3x3 mode
filter, the years are packed into one integer per pixel, and connected regions with the same integer become polygons.
Polygons smaller than --min-ha or with a non-crop year are dropped.

Output: data/raw/fields/candidates_<fips>.geojson with properties sequence (e.g. "WFWSFWSF"), area_ha, lon, lat.
"""
import argparse, json, os, urllib.request
import ee

# CDL code -> simplified class: 1 wheat, 2 fallow, 3 sorghum, 4 corn, 5 other crop, 0 not cropland
CLASSES = {24: 1, 61: 2, 4: 3, 1: 4}
OTHER_CROPS = [5, 6, 21, 23, 25, 26, 27, 28, 29, 31, 36, 37, 42, 53, 205, 225, 226, 235, 236, 237, 238]
LETTER = "-WFSCO"
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fips", default="20071"); ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", type=int, default=2025); ap.add_argument("--min-ha", type=float, default=40)
    a = ap.parse_args()
    ee.Initialize(project=os.environ["EE_PROJECT"])
    county = ee.FeatureCollection("TIGER/2018/Counties").filter(ee.Filter.eq("GEOID", a.fips)).geometry()
    cdl = ee.ImageCollection("USDA/NASS/CDL")
    last = ee.Date(cdl.aggregate_max("system:time_start")).get("year").getInfo()
    end = min(a.end, last); years = list(range(end - (a.end - a.start), end + 1))
    print("CDL years used:", years[0], "-", years[-1])
    src = list(CLASSES) + OTHER_CROPS; dst = list(CLASSES.values()) + [5] * len(OTHER_CROPS)
    code = ee.Image(0)
    for i, y in enumerate(years):
        img = cdl.filter(ee.Filter.calendarRange(y, y, "year")).first().select("cropland").remap(src, dst, 0)
        img = img.focalMode(1, "square", "pixels")
        code = code.add(img.multiply(6 ** i))
    code = code.toInt().rename("code").clip(county)
    vectors = code.reduceToVectors(geometry=county, scale=30, geometryType="polygon", eightConnected=False,
                                   labelProperty="code", reducer=ee.Reducer.countEvery(), maxPixels=1e9, tileScale=4)
    min_px = a.min_ha * 10000 / 900
    vectors = vectors.filter(ee.Filter.gte("count", min_px))
    def describe(f):
        c = f.geometry().centroid(10).coordinates()
        return f.setGeometry(f.geometry().simplify(20)).set({"area_ha": f.geometry().area(10).divide(10000), "lon": c.get(0), "lat": c.get(1)})
    url = vectors.map(describe).getDownloadURL("geojson")
    fc = json.load(urllib.request.urlopen(url, timeout=600))
    keep = []
    for f in fc["features"]:
        n, seq = f["properties"]["code"], ""
        for _ in years:
            seq += LETTER[n % 6]; n //= 6
        if "-" in seq: continue
        p = f["properties"]
        f["properties"] = dict(sequence=seq, first_year=years[0], last_year=years[-1], area_ha=round(p["area_ha"], 1),
                               lon=round(p["lon"], 5), lat=round(p["lat"], 5))
        f.pop("id", None); keep.append(f)
    out = os.path.join(HERE, "..", "..", "data", "raw", "fields"); os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"candidates_{a.fips}.geojson")
    json.dump({"type": "FeatureCollection", "features": keep}, open(path, "w"))
    print(f"{len(fc['features'])} polygons >= {a.min_ha} ha, {len(keep)} cropland in every year -> {path}")

if __name__ == "__main__":
    main()
