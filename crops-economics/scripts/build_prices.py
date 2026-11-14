"""Build reference/prices.csv: Kansas marketing-year prices received, nominal and in 2025 dollars.

Inputs
    data/raw/nass/prices_ks.json   (from fetch_nass.py; needs NASS_API_KEY once)
    data/raw/fred_CPIAUCSL.csv     (CPI-U, monthly, seasonally adjusted; downloaded here if missing)
Output
    reference/prices.csv
    reference/cpi_u_annual.csv

Conventions (see reference/README.md):
- `year` is the first calendar year of the marketing year = the harvest year of that crop
  (wheat MY Jun-May, corn / sorghum / sunflower MY Sep-Aug).
- Real prices use the calendar-year average CPI-U of `year`, rebased to 2025 = 1.
- NASS reports grain sorghum and sunflower in $/cwt; converted to $/bu (sorghum, 56 lb) and $/kg.
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from units import BUSHEL_KG, CWT_KG, LB_KG  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

BASE_YEAR = 2025
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
CPI_RAW = ROOT / "data/raw/fred_CPIAUCSL.csv"
NASS_RAW = ROOT / "data/raw/nass/prices_ks.json"
OUT = ROOT / "reference/prices.csv"
CPI_OUT = ROOT / "reference/cpi_u_annual.csv"

INTERPOLATED: list[str] = []

CROP_OF_COMMODITY = {"WHEAT": "wheat", "CORN": "corn", "SORGHUM": "sorghum", "SUNFLOWER": "sunflower"}

PREFERRED = {
    "wheat": ["WHEAT - PRICE RECEIVED, MEASURED IN $ / BU",
              "WHEAT, WINTER - PRICE RECEIVED, MEASURED IN $ / BU"],
    "corn": ["CORN, GRAIN - PRICE RECEIVED, MEASURED IN $ / BU"],
    "sorghum": ["SORGHUM, GRAIN - PRICE RECEIVED, MEASURED IN $ / CWT",
                "SORGHUM, GRAIN - PRICE RECEIVED, MEASURED IN $ / BU"],
    "sunflower": ["SUNFLOWER, OIL TYPE - PRICE RECEIVED, MEASURED IN $ / CWT",
                  "SUNFLOWER - PRICE RECEIVED, MEASURED IN $ / CWT"],
}


def annual_cpi() -> dict[int, float]:
    if not CPI_RAW.exists():
        CPI_RAW.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FRED_URL, CPI_RAW)
    with CPI_RAW.open() as f:
        obs = [(r["observation_date"][:7], r["CPIAUCSL"]) for r in csv.DictReader(f)]
    vals = [float(v) if v not in ("", ".") else None for _, v in obs]
    for i, v in enumerate(vals):
        if v is None and 0 < i < len(vals) - 1 and vals[i - 1] is not None and vals[i + 1] is not None:
            vals[i] = (vals[i - 1] + vals[i + 1]) / 2
            INTERPOLATED.append(obs[i][0])
    months = defaultdict(list)
    for (ym, _), v in zip(obs, vals):
        if v is not None:
            months[int(ym[:4])].append(v)

    return {y: sum(v) / 12 for y, v in months.items() if len(v) == 12}


def to_number(s: str) -> float | None:
    s = s.strip().replace(",", "")
    try:
        return float(s)
    except ValueError:  
        return None


def main() -> None:
    cpi = annual_cpi()
    CPI_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CPI_OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "cpi_u_annual_avg", "factor_to_2025_usd", "source"])
        for y in sorted(cpi):
            if y >= 1990:
                note = "".join(f"; {m} interpolated (not published)" for m in INTERPOLATED if m.startswith(str(y)))
                w.writerow([y, round(cpi[y], 3), round(cpi[BASE_YEAR] / cpi[y], 4),
                            "BLS CPI-U all items, SA (FRED series CPIAUCSL), mean of 12 months" + note])

    if not NASS_RAW.exists():
        print(f"CPI written to {CPI_OUT}. {NASS_RAW.name} not found: prices.csv NOT built "
              f"(run fetch_nass.py with NASS_API_KEY first).")
        return
    rows = json.loads(NASS_RAW.read_text())

    series = defaultdict(dict)  
    for r in rows:
        if r.get("reference_period_desc") != "MARKETING YEAR" or r.get("agg_level_desc") != "STATE":
            continue
        crop = CROP_OF_COMMODITY.get(r["commodity_desc"])
        v = to_number(r["Value"])
        if crop and v is not None:
            series[(crop, r["short_desc"])][int(r["year"])] = v

    out = []
    for crop, prefs in PREFERRED.items():
        years = sorted({y for (c, _), s in series.items() if c == crop for y in s})
        for y in years:
            for sd in prefs:
                if y in series.get((crop, sd), {}):
                    v = series[(crop, sd)][y]
                    unit = sd.rsplit("MEASURED IN ", 1)[1]
                    per_kg = v / (CWT_KG if unit == "$ / CWT" else BUSHEL_KG[crop])
                    per_bu = per_kg * BUSHEL_KG[crop] if crop in BUSHEL_KG else None
                    f = cpi[BASE_YEAR] / cpi[y] if y in cpi else None
                    out.append({
                        "year": y, "crop": crop,
                        "price_usd_per_bu": round(per_bu, 3) if per_bu is not None else "",
                        "price_usd_per_kg": round(per_kg, 5),
                        "price_usd_per_lb": round(per_kg * LB_KG, 5),
                        "nass_value": v, "nass_unit": unit,
                        "cpi_u": round(cpi[y], 3) if y in cpi else "",
                        "price_real2025_usd_per_bu": round(per_bu * f, 3) if (per_bu and f) else "",
                        "price_real2025_usd_per_kg": round(per_kg * f, 5) if f else "",
                        "source": f"USDA NASS QuickStats, Kansas, marketing year: {sd}",
                    })
                    break
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    for crop in PREFERRED:
        ys = [r["year"] for r in out if r["crop"] == crop]
        print(f"{crop}: {len(ys)} years" + (f" ({min(ys)}-{max(ys)})" if ys else " - NOT FOUND, check NASS series"))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
