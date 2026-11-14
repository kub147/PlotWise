"""USDA AMS Market News (MARS API): find Kansas grain bid reports and save the latest one.

Needs a free MARS API key (https://mymarketnews.ams.usda.gov/mymarketnews-api) in AMS_API_KEY.
The key is sent as the HTTP basic-auth user name with an empty password (MARS convention).

    export AMS_API_KEY=...
    python scripts/fetch_ams.py                 # list Kansas grain reports
    python scripts/fetch_ams.py <slug_id>       # save the latest issue of one report

Output (raw, not committed): data/raw/ams/reports_kansas_grain.json, data/raw/ams/<slug_id>_latest.json
Use: the "today" price scenario and the "is there a local market for this crop" check on the cards.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

API = "https://marsapi.ams.usda.gov/services/v1.2/reports"
OUT = ROOT / "data/raw/ams"


def get(url: str, key: str):
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{key}:".encode()).decode())
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main() -> None:
    key = os.environ.get("AMS_API_KEY")
    if not key:
        sys.exit("Set AMS_API_KEY first.")
    OUT.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) == 1:
        reports = get(API, key)
        hits = [r for r in reports if "kansas" in json.dumps(r).lower()
                and any(w in r.get("report_title", "").lower() for w in ("grain", "bid", "sorghum", "wheat"))]
        (OUT / "reports_kansas_grain.json").write_text(json.dumps(hits, indent=1))
        for r in hits:
            print(r.get("slug_id"), "|", r.get("report_title"), "|", r.get("published_date", ""))
        print(f"{len(hits)} reports; run again with a slug_id to download one")
    else:
        slug = sys.argv[1]
        data = get(f"{API}/{slug}?lastReports=1", key)
        (OUT / f"{slug}_latest.json").write_text(json.dumps(data, indent=1))
        print(f"saved {OUT / f'{slug}_latest.json'}")


if __name__ == "__main__":
    main()
