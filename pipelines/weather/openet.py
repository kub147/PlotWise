"""Workstream A, stretch: OpenET monthly evapotranspiration per demo field (independent check of modelled crop ET).

Usage (from the repo root, EE_PROJECT set):
    python3 pipelines/weather/openet.py check     # step 1: coverage of two test years (2012, 2024), 2 small requests
    python3 pipelines/weather/openet.py all       # 1999-2024, one request per year for all fields together

Reads   data/processed/fields.geojson (polygons) and data/processed/weather/<field_id>.csv (precipitation, reference ET).
Writes  data/processed/climate/<field_id>_openet.csv   month, et_mm, et_min_mm, et_max_mm, valid_pixel_share, precip_mm, eto_mm
        data/processed/climate/openet_summary.json     coverage, yearly ET next to precipitation and the CDL crop, ET/P ratio

OpenET ensemble: mean of six satellite ET models after outlier filtering, 30 m, monthly; et_min / et_max are the
range across the models. Each request reduces 12 monthly mosaics over the field polygons and returns a small table.
"""
import argparse, csv, json, os, sys
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch

OPENET = "projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0"
FIRST_YEAR, LAST_YEAR = 1999, 2024            # collection runs from 1999-10 to 2024-12
MIN_VALID_SHARE = 0.9                         # a month counts when at least 90% of the field's pixels have a value
SEASON = range(4, 11)                         # April-October
UTM_CRS = "EPSG:32614"                        # UTM zone 14N, the native grid of the tiles over Greeley County
PROCESSED = os.path.join(fetch.REPO, "data", "processed")
COLUMNS = ["month", "et_mm", "et_min_mm", "et_max_mm", "valid_pixel_share", "precip_mm", "eto_mm"]


def load_fields():
    path = os.path.join(PROCESSED, "fields.geojson")
    if not os.path.exists(path):
        raise SystemExit("data/processed/fields.geojson is needed: OpenET is reduced over the field polygons")
    with open(path) as f:
        return [dict(field_id=ft["properties"]["field_id"], geometry=ft["geometry"],
                     crops=ft["properties"].get("crop_history_names") or {}) for ft in json.load(f)["features"]]


def fetch_year(fields, year):
    """One Earth Engine request: field means for every month of `year`. Returns a list of plain dicts.

    The collection is stored as overlapping UTM-zone tiles (about 25 images per month) and a tile is masked outside
    its own zone, so the tiles that touch the fields are mosaicked per month before reducing."""
    ee = fetch.ee_api()
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]), {"field_id": f["field_id"]}) for f in fields])
    reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
    col = ee.ImageCollection(OPENET).filterBounds(fc.geometry())
    tables = []
    for m in range(10 if year == FIRST_YEAR else 1, 13):          # the collection starts in 1999-10
        start = ee.Date.fromYMD(year, m, 1)
        img = (col.filterDate(start, start.advance(1, "month"))
               .select(["et_ensemble_mad", "et_ensemble_mad_min", "et_ensemble_mad_max"], ["et", "et_min", "et_max"]).mosaic()
               .addBands(ee.Image.constant(1).rename("all")))
        stats = img.reduceRegions(collection=fc, reducer=reducer, scale=30, crs=UTM_CRS)
        month = f"{year}-{m:02d}"
        tables.append(stats.map(lambda ft, month=month: ee.Feature(None, ft.toDictionary()).set("month", month)))
    return [ft["properties"] for ft in ee.FeatureCollection(tables).flatten().getInfo()["features"]]


def get_year(fields, year, refresh=False):
    key = "openet_mosaic/" + "_".join(f["field_id"] for f in fields) + f"_{year}"
    return fetch._cached(key, lambda: fetch_year(fields, year), growing=False, refresh=refresh)


def tidy(rows):
    """{field_id: {month: record}} with the valid-pixel share; months below MIN_VALID_SHARE keep et_mm = None."""
    out = {}
    for r in rows:
        total = r.get("all_count") or 0
        share = (r.get("et_count") or 0) / total if total else 0.0
        ok = share >= MIN_VALID_SHARE and r.get("et_mean") is not None
        out.setdefault(r["field_id"], {})[r["month"]] = dict(
            et_mm=round(r["et_mean"], 1) if ok else None,
            et_min_mm=round(r["et_min_mean"], 1) if ok and r.get("et_min_mean") is not None else None,
            et_max_mm=round(r["et_max_mean"], 1) if ok and r.get("et_max_mean") is not None else None,
            valid_pixel_share=round(share, 3))
    return out


def monthly_weather(field_id):
    """{month: (precip_mm, eto_mm)} from the weather CSV, complete months only."""
    path = os.path.join(PROCESSED, "weather", f"{field_id}.csv")
    if not os.path.exists(path):
        return {}
    sums = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            s = sums.setdefault(r["date"][:7], [0.0, 0.0, 0])
            s[0] += float(r["precip_mm"]); s[1] += float(r["eto_mm"]); s[2] += 1
    return {m: (round(p, 1), round(e, 1)) for m, (p, e, n) in sums.items() if n >= 28}


def coverage_table(data, years):
    """Markdown: valid months per field and year, and which calendar months are missing."""
    lines = ["| Field | Year | Months with ET | Missing or masked months |", "| :--- | ---: | ---: | :--- |"]
    for fid in sorted(data):
        for y in years:
            months = [f"{y}-{m:02d}" for m in range(1, 13)]
            bad = [m[5:] for m in months if data[fid].get(m, {}).get("et_mm") is None]
            lines.append(f"| {fid} | {y} | {12 - len(bad)} / 12 | {', '.join(bad) if bad else '–'} |")
    return "\n".join(lines)


def summarise(field, months, weather):
    """Yearly ET next to precipitation, reference ET and the CDL crop; long-term ET/P ratio."""
    yearly = []
    for y in range(FIRST_YEAR, LAST_YEAR + 1):
        def total(key, sel):
            if key in ("precip", "eto"):
                vals = [(weather.get(f"{y}-{m:02d}") or (None, None))[key == "eto"] for m in sel]
            else:
                vals = [(months.get(f"{y}-{m:02d}") or {}).get(key) for m in sel]
            return None if any(v is None for v in vals) else round(sum(vals), 1)
        rec = dict(year=y, crop=field["crops"].get(str(y)),
                   et_mm=total("et_mm", range(1, 13)), precip_mm=total("precip", range(1, 13)),
                   et_apr_oct_mm=total("et_mm", SEASON), et_min_apr_oct_mm=total("et_min_mm", SEASON),
                   et_max_apr_oct_mm=total("et_max_mm", SEASON),
                   precip_apr_oct_mm=total("precip", SEASON), eto_apr_oct_mm=total("eto", SEASON))
        if rec["et_mm"] is not None or rec["et_apr_oct_mm"] is not None:
            yearly.append(rec)
    full = [r for r in yearly if r["et_mm"] is not None and r["precip_mm"] is not None]
    season = [r for r in yearly if r["et_apr_oct_mm"] is not None and r["eto_apr_oct_mm"]]
    out = dict(field_id=field["field_id"],
               months_with_et=sum(1 for v in months.values() if v["et_mm"] is not None), months_in_collection=len(months),
               n_complete_years=len(full), yearly=yearly)
    if full:
        et, p = mean(r["et_mm"] for r in full), mean(r["precip_mm"] for r in full)
        out.update(mean_annual_et_mm=round(et), mean_annual_precip_mm=round(p), et_to_precip_ratio=round(et / p, 2))
    if season:
        out.update(mean_apr_oct_et_mm=round(mean(r["et_apr_oct_mm"] for r in season)),
                   mean_apr_oct_et_to_eto=round(mean(r["et_apr_oct_mm"] / r["eto_apr_oct_mm"] for r in season), 2))
    by_crop = {}
    for r in season:
        if r["crop"]:
            by_crop.setdefault(r["crop"], []).append(r["et_apr_oct_mm"])
    out["apr_oct_et_by_cdl_crop"] = {c: dict(n_years=len(v), mean_mm=round(mean(v)), min_mm=round(min(v)), max_mm=round(max(v)))
                                     for c, v in sorted(by_crop.items())}
    return out


def summary_table(summaries):
    f = lambda v, spec="": "–" if v is None else format(v, spec)
    lines = ["| Field | Complete years | Mean ET mm/yr | Mean P mm/yr | ET / P | Apr–Oct ET mm | Apr–Oct ET / ETo |",
             "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for s in summaries:
        lines.append(f"| {s['field_id']} | {s['n_complete_years']} | {f(s.get('mean_annual_et_mm'))} | {f(s.get('mean_annual_precip_mm'))} | "
                     f"{f(s.get('et_to_precip_ratio'), '.2f')} | {f(s.get('mean_apr_oct_et_mm'))} | {f(s.get('mean_apr_oct_et_to_eto'), '.2f')} |")
    return "\n".join(lines)


def write_outputs(fields, data):
    out_dir = os.path.join(PROCESSED, "climate")
    os.makedirs(out_dir, exist_ok=True)
    summaries = []
    for field in fields:
        fid, months, weather = field["field_id"], data.get(field["field_id"], {}), monthly_weather(field["field_id"])
        if not weather:
            print(f"   note: no weather CSV for {fid}; precipitation and reference ET columns stay empty")
        with open(os.path.join(out_dir, f"{fid}_openet.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(COLUMNS)
            for m in sorted(months):
                p, e = weather.get(m, ("", ""))
                rec = months[m]
                w.writerow([m] + ["" if rec[c] is None else rec[c] for c in COLUMNS[1:5]] + [p, e])
        summaries.append(summarise(field, months, weather))
        print(f"[{fid}] wrote data/processed/climate/{fid}_openet.csv ({summaries[-1]['months_with_et']} months with ET)")
    with open(os.path.join(out_dir, "openet_summary.json"), "w") as f:
        json.dump(dict(source=OPENET, unit="mm", period=[FIRST_YEAR, LAST_YEAR],
                       method=f"Field mean of the OpenET ensemble at 30 m; a month counts when at least {MIN_VALID_SHARE:.0%} of the "
                              "field's pixels have a value. et_min / et_max are the range across the ensemble models. "
                              "Precipitation and reference ET are gridMET, from the weather CSV. Crop is the CDL majority class.",
                       caveats=["On all five fields, including plain wheat-fallow, mean annual OpenET is about 20% above gridMET "
                                "precipitation (ET / P 1.19-1.21). A dryland field cannot evaporate more than it receives over 24 years, "
                                "so OpenET is biased high here relative to gridMET precipitation (or precipitation is biased low). "
                                "Use OpenET for differences between years, crops and fields, not for the absolute level.",
                                "Because the ratio is the same on every field, ET / P does not separate irrigated from dryland fields here.",
                                "OpenET models use gridMET reference ET, so OpenET is not fully independent of the weather files."],
                       fields=summaries), f, indent=1, ensure_ascii=False)
    print("wrote data/processed/climate/openet_summary.json\n")
    print(summary_table(summaries))
    return summaries


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=["check", "all"]); ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    fields = load_fields()
    years = [2012, 2024] if a.step == "check" else list(range(FIRST_YEAR, LAST_YEAR + 1))
    rows = []
    for y in years:
        rows += get_year(fields, y, a.refresh)
        print(f"   {y}: done", flush=True)
    data = tidy(rows)
    if not data:
        raise SystemExit("OpenET returned no rows: check access to the asset " + OPENET)
    if a.step == "check":
        print("\nOpenET coverage for two test years (a month counts when ≥ 90% of the field's pixels have a value)\n")
        print(coverage_table(data, years))
        print("\nGrowing-season ET of the test years, mm (April–October):")
        for fid in sorted(data):
            parts = []
            for y in years:
                v = [data[fid].get(f"{y}-{m:02d}", {}).get("et_mm") for m in SEASON]
                parts.append(f"{y}: " + ("incomplete" if any(x is None for x in v) else f"{sum(v):.0f}"))
            print(f"   {fid}  " + "   ".join(parts))
    else:
        write_outputs(fields, data)


if __name__ == "__main__":
    main()
