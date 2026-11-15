"""Map of mean summer greenness around each site (Tribune, Colby, Hays), for the Greenness layer of the app's map.

Usage:
    EE_PROJECT=<your-ee-project> python3 pipelines/fields/greenness_map.py

Mean NDVI of all clear Landsat 8 and 9 passes in June-August of 2021-2025, over the same area as the ECOSTRESS
heat images (the demo fields of the site and 4 km around them). Land that carries a crop every summer is green;
wheat (harvested in June) and fallow stay brown.

Output: docs/img/greenness_<site>.png (Web Mercator, no outlines) and data/processed/ndvi/summer_map.json with
the bounds of each image (west, south, east, north in degrees) and the colour scale.
"""
import json, os, urllib.request
import ee

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
YEARS = (2021, 2025)
SCALE = (0.1, 0.6)
PALETTE = ["8c6d4f", "d9c9a3", "f3efd0", "b6d98a", "5fae5a", "1e7a3c", "0b4f2a"]

def main():
    ee.Initialize(project=os.environ["EE_PROJECT"])
    fc = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson"), encoding="utf-8"))
    def ndvi(img):
        clear = img.select("QA_PIXEL").bitwiseAnd(0b111110).eq(0)      # bits 1-5: dilated cloud, cirrus, cloud, shadow, snow
        sr = img.select(["SR_B5", "SR_B4"]).multiply(0.0000275).add(-0.2)
        return sr.normalizedDifference(["SR_B5", "SR_B4"]).rename("ndvi").updateMask(clear)
    sites = []
    for site in dict.fromkeys(f["properties"]["site"] for f in fc["features"]):
        outlines = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"])) for f in fc["features"] if f["properties"]["site"] == site])
        box = outlines.geometry().bounds().buffer(4000).bounds()
        ring = box.coordinates().getInfo()[0]
        bounds = [round(v, 5) for v in (min(x for x, _ in ring), min(y for _, y in ring), max(x for x, _ in ring), max(y for _, y in ring))]
        col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")).filterBounds(box)
               .filter(ee.Filter.calendarRange(YEARS[0], YEARS[1], "year")).filter(ee.Filter.calendarRange(6, 8, "month")))
        passes = col.size().getInfo()
        mean = col.map(ndvi).mean()
        url = mean.visualize(min=SCALE[0], max=SCALE[1], palette=PALETTE).getThumbURL(
            {"region": ee.Geometry.Rectangle(bounds, None, False), "crs": "EPSG:3857", "dimensions": 1400, "format": "png"})
        name = f"greenness_{site.lower()}.png"
        urllib.request.urlretrieve(url, os.path.join(ROOT, "docs", "img", name))
        sites.append(dict(site=site, image=f"docs/img/{name}", bounds=bounds, landsat_passes=passes))
        print("saved", name, "from", passes, "Landsat passes")
    path = os.path.join(ROOT, "data", "processed", "ndvi", "summer_map.json")
    json.dump(dict(source="Landsat 8 and 9 Collection 2 surface reflectance (30 m), cloud-masked",
                   note="Mean NDVI of all clear passes in June-August. Wheat is harvested in June, so wheat and fallow land stay low.",
                   years=list(YEARS), months=[6, 8], colour_scale_ndvi=list(SCALE), palette=PALETTE, sites=sites),
              open(path, "w", encoding="utf-8"), indent=1)
    print("saved", path)

if __name__ == "__main__":
    main()
