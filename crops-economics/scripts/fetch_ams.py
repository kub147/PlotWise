"""Download USDA AMS Market News grain reports for Kansas to data/raw/ams/ (needs AMS_API_KEY).

    python fetch_ams.py            list Kansas grain reports
    python fetch_ams.py <slug_id>  save the latest issue of one report
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
