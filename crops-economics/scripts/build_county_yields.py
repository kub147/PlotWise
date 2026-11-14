"""Build reference/county_yields.csv from NASS county and district yields.

Keeps winter wheat, grain corn, grain sorghum and sunflower; adds yield in kg/ha, the NASS district
and in_study_area (county listed in data/processed/counties.geojson). Withheld values are dropped.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from units import bu_acre_to_kg_ha, lb_acre_to_kg_ha
from study_area import load_counties


ROOT = Path(__file__).resolve().parent.parent

RAW = [ROOT / "data/raw/nass/county_yields_ks.json", ROOT / "data/raw/nass/district_yields_ks.json"]
OUT = ROOT / "reference/county_yields.csv"
CROP = {"WHEAT": "winter_wheat", "SORGHUM": "grain_sorghum", "CORN": "corn", "SUNFLOWER": "sunflower"}
BUCROP = {"winter_wheat": "wheat", "grain_sorghum": "sorghum", "corn": "corn"}


def keep(r: dict) -> bool:
    sd = r["short_desc"]
    if r["commodity_desc"] == "WHEAT" and "WINTER" not in sd:
        return False
    if r["commodity_desc"] == "CORN" and "GRAIN" not in sd:
        return False
    if r["commodity_desc"] == "SORGHUM" and "GRAIN" not in sd:
        return False
    return r.get("reference_period_desc", "YEAR") == "YEAR"


def practice(sd: str) -> str:

    head = sd.split(" - ")[0]
    parts = [p.strip() for p in head.split(",")]
    rest = [p for p in parts[1:] if p not in ("WINTER", "GRAIN", "OIL TYPE")]
    return ", ".join(rest) if rest else "ALL PRODUCTION PRACTICES"


def main() -> None:
    study = load_counties()
    rows, withheld = [], Counter()
    for path in RAW:
        if not path.exists():
            sys.exit(f"{path} missing: run fetch_nass.py with NASS_API_KEY first.")
        for r in json.loads(path.read_text()):
            if not keep(r):
                continue
            crop = CROP[r["commodity_desc"]]
            unit = r["short_desc"].rsplit("MEASURED IN ", 1)[-1]
            level = "county" if r["agg_level_desc"] == "COUNTY" else "district"
            area = r["county_name"] if level == "county" else r["asd_desc"]
            try:
                v = float(r["Value"].replace(",", ""))
            except ValueError:
                withheld[(level, area, crop)] += 1
                continue
            if unit == "BU / ACRE":
                kg = bu_acre_to_kg_ha(v, BUCROP[crop])
            elif unit == "LB / ACRE":
                kg = lb_acre_to_kg_ha(v)
            else:
                continue
            rows.append({
                "level": level, "area": area.title(),
                "county_fips": f'20{r["county_ansi"]}' if level == "county" else "",
                "nass_district": r.get("asd_desc", "").title(),
                "in_study_area": (str(r["county_ansi"] in study).lower() if (level == "county" and study) else ""),
                "year": int(r["year"]), "crop": crop, "practice": practice(r["short_desc"]),
                "yield_value": v, "yield_unit": unit.lower().replace(" ", ""),
                "yield_kg_ha": round(kg, 1),
                "source": f'USDA NASS QuickStats survey: {r["short_desc"]}',
            })
    rows.sort(key=lambda x: (x["level"], x["area"], x["crop"], x["practice"], x["year"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    dry = [r for r in rows if r["practice"] == "NON-IRRIGATED"]
    for crop in sorted({r["crop"] for r in dry}):
        cs = [r for r in dry if r["crop"] == crop and r["level"] == "county"]
        sa = [r for r in cs if r["in_study_area"] == "true"]
        print(f"{crop}: non-irrigated county yields {len(cs)} county-years in {len({r['area'] for r in cs})} "
              f"counties; study area {len(sa)} county-years in {len({r['area'] for r in sa})} counties")
    print(f"withheld values dropped: {sum(withheld.values())}")
    if study:
        have = {r["county_fips"][2:] for r in dry if r["level"] == "county"}
        miss = sorted(study[c]["name"] for c in set(study) - have)
        if miss:
            print(f"study-area counties with no non-irrigated yields at all: {miss}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
