"""Build data/processed/fields.geojson: demo fields with crop history, soil, slope and bare-soil days.

Usage:
    EE_PROJECT=<your-ee-project> python3 build_fields.py

Steps
  1. take the demo fields listed in DEMO_FIELDS from the candidates made by delineate_fields.py
  2. crop history 2008 -> latest CDL year (majority class per field and year), rotation label, fallow share
  3. mean slope from SRTM
  4. Landsat NDVI time series per field (cloud-masked field mean) -> data/processed/ndvi/<field_id>.csv
  5. bare-soil days per year from the daily-interpolated NDVI series
  6. soil properties from SSURGO (soil_sda.py)
"""
import csv, datetime as dt, json, math, os
import ee
from shapely.geometry import shape
from soil_sda import field_soil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
NDVI_BARE = 0.25          # field-mean Landsat NDVI below this = no green cover. Fallow years, May-Aug: median 0.18, p90 0.26
FIRST_YEAR = 2008         # first CDL year for Kansas

# (field_id, county FIPS, site, name, lon, lat of the candidate polygon centroid)
# Three sites along the rainfall gradient of western Kansas, each next to a K-State research station.
DEMO_FIELDS = [
    ("ks071-001", "20071", "Tribune", "Wheat-sorghum-fallow field, about 1.5 miles north of the K-State research station at Tribune", -101.7572, 38.4912),
    ("ks071-002", "20071", "Tribune", "Wheat-fallow field, south-west of Tribune", -101.7751, 38.4131),
    ("ks071-003", "20071", "Tribune", "Wheat-corn-fallow field", -101.7947, 38.4329),
    ("ks071-004", "20071", "Tribune", "Field that moved from wheat-fallow to wheat-sorghum-fallow", -101.6736, 38.4766),
    ("ks071-005", "20071", "Tribune", "Continuously cropped field (no fallow since 2008), for comparison", -101.8164, 38.4711),
    ("ks193-001", "20193", "Colby", "Wheat-corn-fallow field near Colby", -101.0228, 39.4351),
    ("ks193-002", "20193", "Colby", "Wheat-sorghum-fallow field near Colby", -101.0126, 39.4341),
    ("ks193-003", "20193", "Colby", "Wheat-fallow field south of Colby", -101.0793, 39.2239),
    ("ks051-001", "20051", "Hays", "Wheat-sorghum-fallow field east of Hays", -99.2577, 38.8600),
    ("ks051-002", "20051", "Hays", "Wheat-fallow field in eastern Ellis County", -99.0728, 38.8165),
    ("ks051-003", "20051", "Hays", "Continuously cropped field (no fallow in 8 years) near Hays", -99.2215, 38.7948),
]
CDL_NAMES = {1: "corn", 4: "sorghum", 5: "soybean", 6: "sunflower", 24: "winter wheat", 28: "oats", 29: "millet",
             36: "alfalfa", 61: "fallow", 176: "grass/pasture", 205: "triticale", 236: "double crop wheat/sorghum"}
LETTER = {24: "W", 61: "F", 4: "S", 1: "C"}

def cyclic(seq, pattern):
    return any(all(seq[i] == pattern[(i + k) % len(pattern)] for i in range(len(seq))) for k in range(len(pattern)))

def rotation_label(seq):
    """Label from the last 6-8 years of W/F/S/C/O letters."""
    recent = seq[-6:]
    for pattern, label in (("WF", "W-F"), ("WSF", "W-S-F"), ("WCF", "W-C-F"), ("WSSF", "W-S-S-F"), ("WWSF", "W-W-S-F")):
        if cyclic(recent, pattern): return label
    if "F" not in seq[-8:]: return "continuous (no fallow)"
    return "mixed with fallow"

def landsat_ndvi(fields, year):
    """Field-mean NDVI for every clear Landsat scene of one year. Returns rows (field_id, date, ndvi, sensor)."""
    def prep(nir, red):
        def f(img):
            qa = img.select("QA_PIXEL")
            clear = qa.bitwiseAnd(0b111110).eq(0)      # fill excluded by mask; bits 1-5: dilated cloud, cirrus, cloud, shadow, snow
            sr = img.select([nir, red]).multiply(0.0000275).add(-0.2)
            ndvi = sr.normalizedDifference([nir, red]).rename("ndvi").updateMask(clear)
            return ndvi.addBands(clear.rename("clear").unmask(0)).copyProperties(img, ["system:time_start", "SPACECRAFT_ID"])
        return f
    cols = []
    for cid, nir, red in (("LANDSAT/LT05/C02/T1_L2", "SR_B4", "SR_B3"), ("LANDSAT/LE07/C02/T1_L2", "SR_B4", "SR_B3"),
                          ("LANDSAT/LC08/C02/T1_L2", "SR_B5", "SR_B4"), ("LANDSAT/LC09/C02/T1_L2", "SR_B5", "SR_B4")):
        cols.append(ee.ImageCollection(cid).filterBounds(fields.geometry()).filterDate(f"{year}-01-01", f"{year + 1}-01-01")
                    .filter(ee.Filter.lt("CLOUD_COVER", 70)).map(prep(nir, red)))
    col = cols[0].merge(cols[1]).merge(cols[2]).merge(cols[3])
    def per_image(img):
        stats = img.reduceRegions(fields, ee.Reducer.mean(), 30)
        return stats.map(lambda f: ee.Feature(None, {"field_id": f.get("field_id"), "ndvi": f.get("ndvi"), "clear": f.get("clear"),
                                                    "t": img.get("system:time_start"), "sensor": img.get("SPACECRAFT_ID")}))
    feats = col.map(per_image).flatten().filter(ee.Filter.notNull(["ndvi"])).filter(ee.Filter.gte("clear", 0.6)).getInfo()["features"]
    rows = {}
    for f in feats:
        p = f["properties"]
        d = dt.datetime.fromtimestamp(p["t"] / 1000, dt.timezone.utc).date()
        rows[(p["field_id"], d)] = (round(p["ndvi"], 4), p["sensor"])      # one value per field and day
    return [(k[0], k[1], v[0], v[1]) for k, v in rows.items()]

def bare_days(series, threshold=NDVI_BARE):
    """Days per calendar year with daily-interpolated NDVI below the threshold. series: sorted [(date, ndvi)]."""
    out = {}
    for (d0, v0), (d1, v1) in zip(series, series[1:]):
        span = (d1 - d0).days
        if span > 64: continue                           # do not interpolate across long gaps
        for i in range(span):
            v = v0 + (v1 - v0) * i / span
            day = d0 + dt.timedelta(i)
            c = out.setdefault(day.year, [0, 0]); c[1] += 1
            if v < threshold: c[0] += 1
    return {y: round(365 * b / n) for y, (b, n) in out.items() if n >= 300}

def main():
    ee.Initialize(project=os.environ["EE_PROJECT"])
    cands, chosen, meta = {}, [], {}
    for fid, fips, site, name, lon, lat in DEMO_FIELDS:
        if fips not in cands:
            cands[fips] = json.load(open(os.path.join(ROOT, "data", "raw", "fields", f"candidates_{fips}.geojson")))["features"]
        f = min(cands[fips], key=lambda c: math.hypot(c["properties"]["lon"] - lon, c["properties"]["lat"] - lat))
        assert math.hypot(f["properties"]["lon"] - lon, f["properties"]["lat"] - lat) < 0.002, fid
        chosen.append((fid, name, f)); meta[fid] = (fips, site)
    fields = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]).buffer(-30), {"field_id": fid}) for fid, _, f in chosen])

    # crop history and slope
    cdl = ee.ImageCollection("USDA/NASS/CDL")
    last = ee.Date(cdl.aggregate_max("system:time_start")).get("year").getInfo()
    years = list(range(FIRST_YEAR, last + 1))
    stack = ee.Image.cat([cdl.filter(ee.Filter.calendarRange(y, y, "year")).first().select("cropland").rename(f"y{y}") for y in years])
    hist = {f["properties"]["field_id"]: f["properties"] for f in stack.reduceRegions(fields, ee.Reducer.mode(), 30).getInfo()["features"]}
    # SRTM stores whole metres, which fakes ~3% slopes on flat land at 30 m; smooth over ~150 m first
    dem = ee.Image("USGS/SRTMGL1_003").toFloat().focalMean(5, "circle", "pixels")
    slope_pct = ee.Terrain.slope(dem).multiply(math.pi / 180).tan().multiply(100).rename("slope")
    slope = {f["properties"]["field_id"]: f["properties"]["mean"] for f in slope_pct.reduceRegions(fields, ee.Reducer.mean(), 30).getInfo()["features"]}

    # NDVI
    rows = []
    for site in sorted({m[1] for m in meta.values()}):       # one site at a time keeps each request small
        part = fields.filter(ee.Filter.inList("field_id", [fid for fid, m in meta.items() if m[1] == site]))
        for y in range(FIRST_YEAR, dt.date.today().year + 1):
            rows += landsat_ndvi(part, y)
    os.makedirs(os.path.join(ROOT, "data", "processed", "ndvi"), exist_ok=True)
    series = {}
    for fid, d, v, s in sorted(rows):
        series.setdefault(fid, []).append((d, v, s))
    for fid, rs in series.items():
        with open(os.path.join(ROOT, "data", "processed", "ndvi", f"{fid}.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["date", "ndvi", "sensor"]); w.writerows((d.isoformat(), v, s) for d, v, s in rs)

    features = []
    for fid, name, f in chosen:
        h = hist[fid]
        history = {str(y): int(h[f"y{y}"]) for y in years if h.get(f"y{y}") is not None}
        letters = "".join(LETTER.get(history[str(y)], "O") for y in years if str(y) in history)
        bare = bare_days([(d, v) for d, v, _ in series.get(fid, [])])
        recent = [bare[y] for y in bare if y >= years[-1] - 7]
        summer = {}
        for d, v, _ in series.get(fid, []):
            if 6 <= d.month <= 8 and d.year >= years[-1] - 7: summer[d.year] = max(summer.get(d.year, 0), v)
        peak = round(sum(summer.values()) / len(summer), 2) if summer else None
        geom = shape(f["geometry"])
        soil = field_soil(geom.simplify(0.0002).wkt)
        props = dict(field_id=fid, name=name, site=meta[fid][1], county_fips=meta[fid][0], area_ha=f["properties"]["area_ha"],
                     lon=f["properties"]["lon"], lat=f["properties"]["lat"],
                     crop_history=history, crop_history_names={y: CDL_NAMES.get(c, f"CDL {c}") for y, c in history.items()},
                     crop_sequence=letters, crop_sequence_first_year=years[0],
                     current_rotation=rotation_label(letters), fallow_share=round(letters.count("F") / len(letters), 2),
                     summer_peak_ndvi=peak,
                     # irrigated summer crops reach field-mean NDVI of 0.7+; dryland crops here stay near 0.4-0.6
                     probably_irrigated=bool(letters[-8:].count("F") == 0 and peak is not None and peak >= 0.7),
                     slope_pct=round(slope[fid], 2),
                     bare_days_per_year=round(sum(recent) / len(recent)) if recent else None, bare_days_by_year=bare,
                     bare_days_note="Days per year with field-mean Landsat NDVI below the threshold, mean of the last 8 years. "
                                    "No green cover; standing stubble in no-till still protects the soil and is not detected.",
                     ndvi_bare_threshold=NDVI_BARE, ndvi_observations=len(series.get(fid, [])),
                     boundary_source="Connected regions of identical 2018-2025 CDL crop sequences (delineate_fields.py); not a surveyed boundary",
                     **soil)
        features.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
        print(fid, props["site"], props["current_rotation"], letters, "| fallow", props["fallow_share"], "| slope %", props["slope_pct"],
              "| AWC", props["awc_mm"], props["soil_series"], "| bare d/yr", props["bare_days_per_year"], "| peak NDVI", peak, "| irrigated?", props["probably_irrigated"], "| NDVI obs", props["ndvi_observations"])
    out = os.path.join(ROOT, "data", "processed", "fields.geojson")
    json.dump({"type": "FeatureCollection", "features": features}, open(out, "w"), indent=1)
    print("saved", out)

if __name__ == "__main__":
    main()
