"""Render preview images of the demo fields: one NAIP aerial chip per field and, on request, a Sentinel-2 overview per site.

Usage:
    EE_PROJECT=<your-ee-project> python3 pipelines/fields/render_preview.py [--overview]

Output: docs/img/field_<field_id>_naip.png for every field in fields.geojson (Tribune, Colby and Hays).
With --overview also docs/img/fields_overview_s2.png (Tribune) and docs/img/fields_overview_s2_<site>.png (other sites).
"""
import argparse, datetime as dt, json, os, urllib.request
import ee

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overview", action="store_true", help="also draw the Sentinel-2 overview of each site")
    args = parser.parse_args()
    ee.Initialize(project=os.environ["EE_PROJECT"])
    fc = json.load(open(os.path.join(ROOT, "data", "processed", "fields.geojson"), encoding="utf-8"))
    edge = lambda outlines, colour, width: ee.Image().byte().paint(outlines, 1, width).visualize(palette=[colour])
    # The sites are more than 100 km apart, so every site gets its own outlines, overview and image mosaic.
    for site in dict.fromkeys(f["properties"]["site"] for f in fc["features"]):
        features = [f for f in fc["features"] if f["properties"]["site"] == site]
        outlines = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"])) for f in features])
        box = outlines.geometry().bounds().buffer(2500).bounds()
        if args.overview:
            s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(box).filterDate("2025-07-01", "2025-08-15")
                  .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10)).median())
            img = s2.visualize(bands=["B4", "B3", "B2"], min=300, max=3200, gamma=1.3).blend(edge(outlines, "ffff00", 3))
            name = "fields_overview_s2.png" if site == "Tribune" else f"fields_overview_s2_{site.lower()}.png"
            urllib.request.urlretrieve(img.getThumbURL({"region": box, "dimensions": 1600, "format": "png"}),
                                       os.path.join(ROOT, "docs", "img", name))
            print("saved", name, "(Sentinel-2 median, 1 Jul - 15 Aug 2025)")
        naip = ee.ImageCollection("USDA/NAIP/DOQQ").filterBounds(box)
        latest = dt.datetime.fromtimestamp(naip.aggregate_max("system:time_start").getInfo() / 1000, dt.timezone.utc).year
        mosaic = naip.filter(ee.Filter.calendarRange(latest, latest, "year")).mosaic()
        for f in features:
            fid = f["properties"]["field_id"]
            region = ee.Geometry(f["geometry"]).bounds().buffer(250).bounds()
            chip = mosaic.visualize(bands=["R", "G", "B"], min=30, max=220).blend(edge(outlines, "ffff00", 2))
            urllib.request.urlretrieve(chip.getThumbURL({"region": region, "dimensions": 900, "format": "png"}),
                                       os.path.join(ROOT, "docs", "img", f"field_{fid}_naip.png"))
            print("saved", fid, "NAIP", latest)

if __name__ == "__main__":
    main()
