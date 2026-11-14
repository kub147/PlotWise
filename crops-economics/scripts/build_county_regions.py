"""Build reference/county_budget_regions.csv: K-State budget region (SW, NW, NC, SC) of each county.

Rule by NASS agricultural district: Northwest -> NW, Southwest -> SW, North Central and Northeast -> NC,
South Central and Southeast -> SC; West Central, Central and East Central are split at 38.7 N
(north -> NW or NC, south -> SW or SC). Latitude comes from data/processed/counties.geojson.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study_area import COUNTIES, load_counties

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/nass/county_yields_ks.json"
OUT = ROOT / "reference/county_budget_regions.csv"
SPLIT_LAT = 38.7

FIXED = {"NORTHWEST": "NW", "SOUTHWEST": "SW", "NORTH CENTRAL": "NC", "SOUTH CENTRAL": "SC",
         "NORTHEAST": "NC", "SOUTHEAST": "SC"}
SPLIT = {"WEST CENTRAL": ("NW", "SW"), "CENTRAL": ("NC", "SC"), "EAST CENTRAL": ("NC", "SC")}


def main() -> None:
    if not RAW.exists():
        sys.exit(f"{RAW} missing: run fetch_nass.py (run_all.py --refresh with NASS_API_KEY)")
    study = load_counties()
    if not study:
        print(f"WARNING {COUNTIES} not found: latitude unknown, split districts get 'unknown'")
    districts = {}
    for r in json.loads(RAW.read_text()):
        code = (r.get("county_ansi") or "").zfill(3)
        if code and code != "000" and r.get("asd_desc"):
            districts[code] = (r["county_name"].title(), r["asd_desc"].upper())

    rows = []
    for code, (name, asd) in sorted(districts.items()):
        lat = study.get(code, {}).get("lat")
        if asd in FIXED:
            region, rule = FIXED[asd], f"NASS district {asd.title()}"
        elif asd in SPLIT and lat is not None:
            north, south = SPLIT[asd]
            region = north if lat >= SPLIT_LAT else south
            rule = f"NASS district {asd.title()}, latitude {lat:.2f} {'>=' if lat >= SPLIT_LAT else '<'} {SPLIT_LAT}"
        else:
            region, rule = "unknown", f"NASS district {asd.title()}, latitude unknown"
        rows.append({"county_fips": "20" + code, "county_name": name, "nass_district": asd.title(),
                     "lat": round(lat, 3) if lat is not None else "", "budget_region": region,
                     "in_study_area": str(code in study).lower(), "rule": rule + " (ASSUMPTION A9)"})
    missing = sorted(set(study) - set(districts))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    sa = [r for r in rows if r["in_study_area"] == "true"]
    print(f"wrote {OUT}: {len(rows)} counties, {len(sa)} in the study area")
    for reg in ("SW", "NW", "NC", "SC", "unknown"):
        names = [r["county_name"] for r in sa if r["budget_region"] == reg]
        if names:
            print(f"  {reg}: {len(names)} - {', '.join(names)}")
    if missing:
        print(f"WARNING study-area counties without NASS district: {missing}")


if __name__ == "__main__":
    main()
