"""Build reference/crop_calendar_ks.csv from NASS weekly crop progress for Kansas.

For each year the day when 50% of the crop was planted or harvested is interpolated between weekly
reports; the file gives the median and the 10th and 90th percentiles over years.
"""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

RAW = ROOT / "data/raw/nass/progress_ks.json"
OUT = ROOT / "reference/crop_calendar_ks.csv"

SERIES = {
    "winter_wheat": ("WHEAT, WINTER - PROGRESS, MEASURED IN PCT PLANTED",
                     "WHEAT, WINTER - PROGRESS, MEASURED IN PCT HARVESTED"),
    "grain_sorghum": ("SORGHUM - PROGRESS, MEASURED IN PCT PLANTED",
                      "SORGHUM - PROGRESS, MEASURED IN PCT HARVESTED"),
    "corn": ("CORN - PROGRESS, MEASURED IN PCT PLANTED",
             "CORN, GRAIN - PROGRESS, MEASURED IN PCT HARVESTED"),
    "sunflower": ("SUNFLOWER - PROGRESS, MEASURED IN PCT PLANTED",
                  "SUNFLOWER - PROGRESS, MEASURED IN PCT HARVESTED"),
}


def doy_at_50(points: list[tuple[int, float]]) -> float | None:
    points.sort()
    for (d0, p0), (d1, p1) in zip(points, points[1:]):
        if p0 < 50 <= p1 and p1 > p0:
            return d0 + (50 - p0) * (d1 - d0) / (p1 - p0)
    return None


def pct(values: list[float], q: float) -> float:
    s = sorted(values)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> None:
    rows = json.loads(RAW.read_text())
    by = defaultdict(list)
    for r in rows:
        if not r.get("week_ending"):
            continue
        try:
            v = float(r["Value"].replace(",", ""))
        except ValueError:
            continue
        d = date.fromisoformat(r["week_ending"])
        by[(r["short_desc"], int(r["year"]))].append((d.timetuple().tm_yday, v))

    out = []
    for crop, (planted, harvested) in SERIES.items():
        res = {"crop": crop}
        for label, sd in (("plant", planted), ("harvest", harvested)):
            vals = [x for (s, y), pts in by.items() if s == sd and (x := doy_at_50(pts)) is not None]
            if len(vals) >= 5:
                res[f"{label}_doy_median"] = round(statistics.median(vals))
                res[f"{label}_doy_p10"] = round(pct(vals, 0.1))
                res[f"{label}_doy_p90"] = round(pct(vals, 0.9))
                res[f"{label}_years"] = len(vals)
            else:
                res |= {f"{label}_doy_median": "", f"{label}_doy_p10": "", f"{label}_doy_p90": "",
                        f"{label}_years": len(vals)}
        res["source"] = ("USDA NASS Crop Progress, Kansas statewide, day when 50% planted/harvested, "
                         "median over years (derive_crop_calendar.py)")
        out.append(res)
        print(res)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
