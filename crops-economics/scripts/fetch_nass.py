"""Download the USDA NASS QuickStats series that workstream C needs, as raw JSON.

Needs a free API key (https://quickstats.nass.usda.gov/api) in the environment variable NASS_API_KEY.

    export NASS_API_KEY=...            # never commit the key
    python scripts/fetch_nass.py

Writes (raw, not committed):
    data/raw/nass/prices_ks.json         Kansas marketing-year prices received, 1990 ->
    data/raw/nass/county_yields_ks.json  County yields (all practices) for the validation counties, 1990 ->
    data/raw/nass/district_yields_ks.json  West Central district yields (fallback when a county is withheld)
    data/raw/nass/progress_ks.json       Kansas weekly crop progress (% planted / harvested), 1995 ->

Then run build_prices.py and build_county_yields.py (they work offline from these files).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

API = "https://quickstats.nass.usda.gov/api/api_GET/"
FIRST_YEAR = 1990
OUT = ROOT / "data/raw/nass"

# Greeley and nearby west-central Kansas counties (Kansas FIPS county codes).
COUNTIES = {
    "071": "GREELEY", "199": "WALLACE", "203": "WICHITA", "075": "HAMILTON",
    "093": "KEARNY", "171": "SCOTT", "109": "LOGAN",
}
COMMODITIES = ["WHEAT", "SORGHUM", "CORN", "SUNFLOWER"]


def get(params: dict, key: str) -> list[dict]:
    q = {"key": key, "format": "JSON", **params}
    url = API + "?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r).get("data", [])
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")
            if e.code == 400 and "no data" in body.lower():
                return []
            if attempt == 3:
                raise RuntimeError(f"QuickStats {e.code}: {body[:300]} for {params}") from e
        except urllib.error.URLError:
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)
    return []


def main() -> None:
    key = os.environ.get("NASS_API_KEY")
    if not key:
        sys.exit("Set NASS_API_KEY first (free key: https://quickstats.nass.usda.gov/api).")
    OUT.mkdir(parents=True, exist_ok=True)

    prices = []
    for c in COMMODITIES:
        rows = get({"source_desc": "SURVEY", "commodity_desc": c, "statisticcat_desc": "PRICE RECEIVED",
                    "agg_level_desc": "STATE", "state_alpha": "KS", "freq_desc": "ANNUAL",
                    "year__GE": FIRST_YEAR}, key)
        print(f"prices {c}: {len(rows)} rows")
        prices += rows
    (OUT / "prices_ks.json").write_text(json.dumps(prices, indent=0))

    county = []
    for c in COMMODITIES:
        for fips in COUNTIES:
            rows = get({"source_desc": "SURVEY", "commodity_desc": c, "statisticcat_desc": "YIELD",
                        "agg_level_desc": "COUNTY", "state_alpha": "KS", "county_ansi": fips,
                        "year__GE": FIRST_YEAR}, key)
            print(f"county yield {c} {COUNTIES[fips]}: {len(rows)} rows")
            county += rows
    (OUT / "county_yields_ks.json").write_text(json.dumps(county, indent=0))

    district = []
    for c in COMMODITIES:
        rows = get({"source_desc": "SURVEY", "commodity_desc": c, "statisticcat_desc": "YIELD",
                    "agg_level_desc": "AGRICULTURAL DISTRICT", "state_alpha": "KS",
                    "asd_desc": "WEST CENTRAL", "year__GE": FIRST_YEAR}, key)
        print(f"district yield {c}: {len(rows)} rows")
        district += rows
    (OUT / "district_yields_ks.json").write_text(json.dumps(district, indent=0))

    progress = []
    for c in COMMODITIES:
        rows = get({"source_desc": "SURVEY", "commodity_desc": c, "statisticcat_desc": "PROGRESS",
                    "agg_level_desc": "STATE", "state_alpha": "KS", "freq_desc": "WEEKLY",
                    "year__GE": 1995}, key)
        print(f"crop progress {c}: {len(rows)} rows")
        progress += rows
    (OUT / "progress_ks.json").write_text(json.dumps(progress, indent=0))
    found = sorted({f'{r["agg_level_desc"]} | {r["short_desc"]}' for r in prices + county + district + progress})
    (OUT / "series_found.txt").write_text("\n".join(found))
    print(f"{len(found)} distinct series listed in {OUT / 'series_found.txt'}")
    print("done; now run build_prices.py, build_county_yields.py, derive_crop_calendar.py, build_crops.py")


if __name__ == "__main__":
    main()
