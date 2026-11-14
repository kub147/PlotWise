"""Download NASS QuickStats data for Kansas to data/raw/nass/ as JSON.

Needs NASS_API_KEY. Downloads marketing-year prices, county and district yields (1990 onward,
all Kansas counties, in decade chunks) and weekly crop progress (1995 onward).
A query with no matching rows (HTTP 400) is stored as empty.
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


DECADES = [(1990, 1999), (2000, 2009), (2010, 2019), (2020, 2030)]
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
            if e.code == 400:


                print(f"  (no rows: {body[:80].strip()} for {params})")
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
        for y0, y1 in DECADES:
            rows = get({"source_desc": "SURVEY", "commodity_desc": c, "statisticcat_desc": "YIELD",
                        "agg_level_desc": "COUNTY", "state_alpha": "KS",
                        "year__GE": max(y0, FIRST_YEAR), "year__LE": y1}, key)
            print(f"county yield {c} {y0}-{y1}: {len(rows)} rows")
            county += rows
    (OUT / "county_yields_ks.json").write_text(json.dumps(county, indent=0))

    district = []
    for c in COMMODITIES:
        rows = get({"source_desc": "SURVEY", "commodity_desc": c, "statisticcat_desc": "YIELD",
                    "agg_level_desc": "AGRICULTURAL DISTRICT", "state_alpha": "KS",
                    "year__GE": FIRST_YEAR}, key)
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
    print("done; now run: python crops-economics/run_all.py")


if __name__ == "__main__":
    main()
