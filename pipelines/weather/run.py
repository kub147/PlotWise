"""Workstream A pipeline: daily weather and climate summary per demo field.

Usage (from the repo root):
    export EE_PROJECT=<your-earth-engine-project>
    python3 pipelines/weather/run.py crosscheck      # step 1: precipitation cross-check table, nothing else
    python3 pipelines/weather/run.py all             # cross-check, then weather CSV and climate JSON for every field

    python3 pipelines/weather/run.py counties        # weather CSV only, for every county point in counties.geojson

Options: --field <field_id> (one field only), --refresh (ignore the raw cache).

Writes:
    data/processed/weather/<field_id>.csv            date, precip_mm, tmax_c, tmin_c, eto_mm, srad_mj_m2, wind_m_s
    data/processed/weather/sources.md                which product fills each column, and how many days were filled
    data/processed/climate/<field_id>.json           trends, year types, monthly water balance, GRACE, SMAP, cross-check
    data/processed/climate/<field_id>_precip_crosscheck.md / .png
    data/processed/weather/counties/<county_id>.csv  same columns, at the county point (lon, lat) of counties.geojson
Fields come from data/processed/fields.geojson; until that file exists a single point at Tribune is used.
"""
import argparse, csv, datetime as dt, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compute, fetch

PROCESSED = os.path.join(fetch.REPO, "data", "processed")
FALLBACK_FIELD = dict(field_id="ks071-001", lon=-101.75, lat=38.47)   # ASSUMPTION: field 1 = Tribune station point until B delivers fields.geojson


def load_fields(only=None):
    path = os.path.join(PROCESSED, "fields.geojson")
    if os.path.exists(path):
        with open(path) as f:
            features = json.load(f)["features"]
        fields = []
        for ft in features:
            p = ft["properties"]
            if p.get("lon") is None or p.get("lat") is None:
                raise SystemExit(f"field {p.get('field_id')} has no lon/lat properties (see work-plan.md)")
            fields.append(dict(field_id=p["field_id"], lon=float(p["lon"]), lat=float(p["lat"])))
    else:
        print("fields.geojson not found: using the Tribune point as field ks071-001")
        fields = [FALLBACK_FIELD]
    if only:
        fields = [f for f in fields if f["field_id"] == only]
        if not fields:
            raise SystemExit(f"field {only} not found")
    return fields


def crosscheck(field, refresh):
    lon, lat = field["lon"], field["lat"]
    print(f"[{field['field_id']}] precipitation cross-check at lon {lon}, lat {lat}")
    gridmet = fetch.gridmet_daily(lon, lat, refresh=refresh)
    power = fetch.power_daily(lon, lat, refresh=refresh)
    cc = compute.precip_crosscheck(gridmet, power, fetch.prism_monthly(lon, lat, refresh=refresh),
                                   fetch.imerg_monthly(lon, lat, refresh=refresh))
    table = compute.crosscheck_markdown(cc)
    out_dir = os.path.join(PROCESSED, "climate")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{field['field_id']}_precip_crosscheck.md"), "w") as f:
        f.write(f"# Precipitation cross-check — field {field['field_id']} (lon {lon}, lat {lat})\n\n"
                f"Generated {dt.date.today().isoformat()} by pipelines/weather/run.py.\n\n{table}\n")
    print("\n" + table + "\n")
    try:
        from chart import crosscheck_chart
        crosscheck_chart(cc, field["field_id"], os.path.join(out_dir, f"{field['field_id']}_precip_crosscheck.png"))
    except ImportError:
        print("   matplotlib not installed: chart skipped")
    return gridmet, power, cc


def build(field, gridmet, power, cc, refresh):
    lon, lat, fid = field["lon"], field["lat"], field["field_id"]
    rows, counts = compute.build_daily(gridmet, power, lat)
    compute.check_daily(rows)
    os.makedirs(os.path.join(PROCESSED, "weather"), exist_ok=True)
    path = os.path.join(PROCESSED, "weather", f"{fid}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(compute.COLUMNS)
        for r in rows:
            w.writerow([r["date"].isoformat()] + [r[c] for c in compute.COLUMNS[1:]])
    print(f"[{fid}] wrote {os.path.relpath(path, fetch.REPO)}: {len(rows)} days, {rows[0]['date']} to {rows[-1]['date']}")

    yearly = compute.yearly_indicators(rows, power)
    types, method = compute.year_types(yearly)
    climate = dict(
        field_id=fid, lon=lon, lat=lat, generated=dt.date.today().isoformat(),
        weather_period=[rows[0]["date"].isoformat(), rows[-1]["date"].isoformat()],
        trend_rule=f"reliable = Mann-Kendall p < {compute.RELIABLE_P}; slope is ordinary least squares per decade",
        trends=compute.trend_table(yearly),
        yearly={str(y): rec for y, rec in yearly.items()},
        year_types=types, year_type_method=method,
        monthly_water_balance=compute.monthly_water_balance(rows),
        precip_crosscheck=cc,
        grace=compute.grace_summary(fetch.grace_monthly(lon, lat, refresh=refresh)),
        smap=compute.smap_summary(fetch.smap_daily(lon, lat, refresh=refresh)),
        sources={"gridMET": fetch.GRIDMET, "PRISM": fetch.PRISM_MONTHLY, "GPM IMERG": fetch.IMERG_MONTHLY,
                 "GRACE / GRACE-FO": fetch.GRACE, "SMAP L4": fetch.SMAP, "NASA POWER": fetch.POWER_URL},
        caveats=["Gridded weather is 4 km (gridMET) to about 50 km (NASA POWER): it describes the area, not the field.",
                 "NASA POWER precipitation is not used for trends; see precip_crosscheck.",
                 "GRACE is a regional value (~300 km). SMAP is a 9 km model-assimilated product."])
    os.makedirs(os.path.join(PROCESSED, "climate"), exist_ok=True)
    path = os.path.join(PROCESSED, "climate", f"{fid}.json")
    with open(path, "w") as f:
        json.dump(climate, f, indent=1, ensure_ascii=False)
    print(f"[{fid}] wrote {os.path.relpath(path, fetch.REPO)}")
    for t in climate["trends"]:
        print(f"   {t['indicator']:<28} {t['mean_first_half']:>8} -> {t['mean_second_half']:>8}  "
              f"{t['slope_per_decade']:+7.1f}/decade  p={t['mk_p']:.2f}  {'reliable' if t['reliable'] else 'not reliable'}")
    return dict(field_id=fid, lon=lon, lat=lat, first=rows[0]["date"], last=rows[-1]["date"], counts=counts)


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(compute.COLUMNS)
        for r in rows:
            w.writerow([r["date"].isoformat()] + [r[c] for c in compute.COLUMNS[1:]])


def counties(refresh):
    """Weather CSV for every county point. gridMET comes in one request per year for all counties together;
    NASA POWER needs one HTTP request per county. No climate summary and no cross-check at this level."""
    path = os.path.join(PROCESSED, "counties.geojson")
    if not os.path.exists(path):
        raise SystemExit("data/processed/counties.geojson not found (owner: B)")
    with open(path) as f:
        points = [(ft["properties"]["county_id"], float(ft["properties"]["lon"]), float(ft["properties"]["lat"]))
                  for ft in json.load(f)["features"]]
    print(f"{len(points)} county points; gridMET in one request per year for all of them")
    gridmet = fetch.gridmet_daily_points(points, refresh=refresh)
    summaries = []
    for n, (cid, lon, lat) in enumerate(points, 1):
        power = fetch.power_daily(lon, lat, refresh=refresh)
        rows, counts = compute.build_daily(gridmet[cid], power, lat)
        compute.check_daily(rows)
        write_csv(os.path.join(PROCESSED, "weather", "counties", f"{cid}.csv"), rows)
        print(f"[{n}/{len(points)}] {cid}: {len(rows)} days, {rows[0]['date']} to {rows[-1]['date']}", flush=True)
        summaries.append(dict(field_id=cid, lon=lon, lat=lat, first=rows[0]["date"], last=rows[-1]["date"], counts=counts))
    ends = {s["last"] for s in summaries}
    if len(ends) > 1:
        print(f"   note: county files end on different days: {sorted(str(e) for e in ends)}")
    write_sources(summaries, os.path.join("counties", "sources.md"),
                  "County files: one point per county (`lon`, `lat` in counties.geojson, the county centroid), not a county mean. "
                  "Treat them as indicative, as docs/transect.md says for all county results.")


def write_sources(summaries, file_name="sources.md", extra=None):
    primary = dict(precip_mm="gridMET `pr` (mm/day)", tmax_c="gridMET `tmmx` (K − 273.15)", tmin_c="gridMET `tmmn` (K − 273.15)",
                   eto_mm="gridMET `eto` (grass reference ET, ASCE Penman-Monteith, mm/day)",
                   srad_mj_m2="NASA POWER `ALLSKY_SFC_SW_DWN` (MJ/m²/day)", wind_m_s="NASA POWER `WS2M` (m/s at 2 m)")
    fallback = dict(precip_mm="NASA POWER `PRECTOTCORR`", tmax_c="NASA POWER `T2M_MAX`", tmin_c="NASA POWER `T2M_MIN`",
                    eto_mm="Hargreaves (FAO-56 eq. 52) from the temperature columns",
                    srad_mj_m2="gridMET `srad` × 0.0864 (W/m² → MJ/m²/day)",
                    wind_m_s="gridMET `vs` × 0.748 (10 m → 2 m, FAO-56 eq. 47)")
    lines = ["# Weather files: sources", "",
             f"Generated {dt.date.today().isoformat()} by `pipelines/weather/run.py`. One CSV per field, daily, no gaps.", ""]
    lines += [extra, ""] if extra else []
    lines += [
             "| Column | Primary source | Fallback when the primary has no value |", "| :--- | :--- | :--- |"]
    lines += [f"| `{c}` | {primary[c]} | {fallback[c]} |" for c in compute.COLUMNS[1:]]
    lines += ["",
              f"- gridMET: Earth Engine `{fetch.GRIDMET}`, 4 km, pixel under the field centroid (`lon`, `lat` in fields.geojson). "
              "A gridMET day runs to 06:00 UTC of the following day.",
              f"- NASA POWER: `{fetch.POWER_URL}`, community AG, about 0.5° × 0.625°. Its recent days are often missing "
              "for radiation and wind; those days use the gridMET fallback.",
              "- The series ends on the last day gridMET has published.",
              "- Last resort (should be 0 days): mean of the nearest valid days, 0 for precipitation; marked ASSUMPTION below.",
              "", "## Days per source", ""]
    for s in summaries:
        lines += [f"### {s['field_id']} (lon {s['lon']}, lat {s['lat']}; {s['first']} to {s['last']})", "",
                  "| Column | Source | Days |", "| :--- | :--- | ---: |"]
        for c in compute.COLUMNS[1:]:
            lines += [f"| `{c}` | {src} | {n} |" for src, n in s["counts"][c].items()]
        lines.append("")
    with open(os.path.join(PROCESSED, "weather", file_name), "w") as f:
        f.write("\n".join(lines))
    print(f"wrote data/processed/weather/{file_name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=["crosscheck", "all", "counties"])
    ap.add_argument("--field"); ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    if a.step == "counties":
        return counties(a.refresh)
    fields = load_fields(a.field)
    if a.step == "crosscheck":
        fields = fields[:1] if not a.field else fields       # one field is enough to compare products
    summaries = []
    for field in fields:
        gridmet, power, cc = crosscheck(field, a.refresh)
        if a.step == "all":
            summaries.append(build(field, gridmet, power, cc, a.refresh))
    if summaries:
        write_sources(summaries)


if __name__ == "__main__":
    main()
