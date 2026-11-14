"""Render preview images of the demo fields: a Sentinel-2 overview and one NAIP aerial chip per field.

Usage:
    EE_PROJECT=<your-ee-project> python3 pipelines/fields/render_preview.py

Output: docs/img/fields_overview_s2.png and docs/img/field_<field_id>_naip.png
"""
import datetime as dt, json, os, urllib.request
import ee

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def main():
    ee.Initialize(project=os.environ["EE_PROJECT"])
    fc = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson")))
    outlines = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"])) for f in fc["features"]])
    edge = lambda colour, width: ee.Image().byte().paint(outlines, 1, width).visualize(palette=[colour])
    box = outlines.geometry().bounds().buffer(2500).bounds()
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(box).filterDate("2025-07-01", "2025-08-15")
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10)).median())
    img = s2.visualize(bands=["B4", "B3", "B2"], min=300, max=3200, gamma=1.3).blend(edge("ffff00", 3))
    urllib.request.urlretrieve(img.getThumbURL({"region": box, "dimensions": 1600, "format": "png"}),
                               os.path.join(ROOT, "docs", "img", "fields_overview_s2.png"))
    print("saved overview (Sentinel-2 median, 1 Jul - 15 Aug 2025)")
    naip = ee.ImageCollection("USDA/NAIP/DOQQ").filterBounds(box)
    latest = dt.datetime.fromtimestamp(naip.aggregate_max("system:time_start").getInfo() / 1000, dt.timezone.utc).year
    mosaic = naip.filter(ee.Filter.calendarRange(latest, latest, "year")).mosaic()
    for f in fc["features"]:
        fid = f["properties"]["field_id"]
        region = ee.Geometry(f["geometry"]).bounds().buffer(250).bounds()
        chip = mosaic.visualize(bands=["R", "G", "B"], min=30, max=220).blend(edge("ffff00", 2))
        urllib.request.urlretrieve(chip.getThumbURL({"region": region, "dimensions": 900, "format": "png"}),
                                   os.path.join(ROOT, "docs", "img", f"field_{fid}_naip.png"))
        print("saved", fid, "NAIP", latest)

if __name__ == "__main__":
    main()
