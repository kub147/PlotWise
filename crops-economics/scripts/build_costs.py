"""Build reference/costs.csv from K-State AgManager dryland budgets (Southwest / Western Kansas).

Input : data/raw/agmanager/budgets_parsed.csv  (parse_agmanager_budgets.py)
        reference/cpi_u_annual.csv, data/raw/fred_CPIAUCSL.csv  (build_prices.py)
Output: reference/costs.csv

How K-State budgets treat fallow, and how we split it into rotation phases
------------------------------------------------------------------------
K-State does not publish a separate fallow budget. Fallow field operations (burndown herbicide,
tillage passes) are charged to the crop that follows the fallow, and since budget year 2018 the
land rent of the fallow year is charged to the crops as well: wheat in W-F is charged 2.0 acre-years
of rent, each crop of a 3-year W-S-F / W-C-F / W-SF-F rotation 1.5 acre-years. (Budget years 2016-2017
charge 1.0 acre-year to every crop, i.e. they leave out the rent of the fallow year.)

To make every rotation comparable we split each budget into phases:
    crop phase   = direct costs (excl. crop insurance) + machinery capital recovery + 1 year of rent
    fallow phase = 1 year of rent  (its field operations stay inside the following crop's direct costs)
For W-F:     wheat phase + fallow phase           = K-State total (2018+) minus crop insurance
For W-S-F:   wheat + sorghum + fallow phase        = K-State wheat + sorghum totals minus insurance
So the cost of a full rotation cycle equals the K-State budgets exactly (2018+), and 2016-2017
become consistent with later years. Crop insurance is reported but excluded from cost_usd_per_acre,
because the project's economics exclude insurance and its indemnities (project brief, section 9).

`year` = budget year = harvest year of the crop (the 2026 budget is dated Nov 2025, for crops
harvested in 2026).
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUDGETS = ROOT / "data/raw/agmanager/budgets_parsed.csv"
CPI = ROOT / "reference/cpi_u_annual.csv"
CPI_MONTHLY = ROOT / "data/raw/fred_CPIAUCSL.csv"
OUT = ROOT / "reference/costs.csv"
BASE_YEAR = 2025

PAGE = {
    **{y: f"https://www.agmanager.info/farm-budgets/historical-farm-budget-projections/"
          f"{y}-historical-budget-projections-non-irrigated" for y in range(2016, 2027)},
    2027: "https://www.agmanager.info/farm-budgets/2027-farm-management-guides-non-irrigated-crops",
}


def cpi_factors() -> tuple[dict[int, float], str]:
    f = {}
    with CPI.open() as fh:
        for r in csv.DictReader(fh):
            f[int(r["year"])] = float(r["factor_to_2025_usd"])
    with CPI_MONTHLY.open() as fh:
        vals = [float(r["CPIAUCSL"]) for r in csv.DictReader(fh) if r["CPIAUCSL"] not in ("", ".")]
    base = None
    with CPI.open() as fh:
        for r in csv.DictReader(fh):
            if int(r["year"]) == BASE_YEAR:
                base = float(r["cpi_u_annual_avg"])
    latest = base / (sum(vals[-12:]) / 12)
    return f, round(latest, 4)


def main() -> None:
    rows = list(csv.DictReader(BUDGETS.open()))
    factors, latest_factor = cpi_factors()
    out = []
    rent_by_year = defaultdict(dict)
    for r in rows:
        y = int(r["budget_year"])
        direct = float(r["direct_costs_usd_acre"])
        ins = float(r["crop_insurance_usd_acre"])
        mach = float(r["machinery_fixed_usd_acre"])
        rent = float(r["cash_rent_rate_usd_acre_year"])
        rent_by_year[y][f'{r["crop"]}|{r["rotation_context"]}'] = rent
        cost = direct - ins + mach + rent
        f = factors.get(y, latest_factor)
        out.append({
            "year": y,
            "crop": r["crop"],
            "rotation_context": r["rotation_context"],
            "cost_key": f'{r["crop"]}|{r["rotation_context"]}',
            "cost_usd_per_acre": round(cost, 2),
            "cost_real2025_usd_per_acre": round(cost * f, 2),
            "direct_excl_insurance_usd_acre": round(direct - ins, 2),
            "machinery_fixed_usd_acre": round(mach, 2),
            "land_rent_usd_acre_year": rent,
            "crop_insurance_usd_acre": ins,
            "kstate_total_usd_acre": r["total_specified_usd_acre"],
            "kstate_rent_acre_years": r["cash_rent_acre_years_charged"],
            "planning_yield": r["planning_yield"],
            "yield_unit": r["yield_unit"],
            "planning_price_usd_per_unit": r["planning_price_usd_per_unit"],
            "budget_date": r["budget_date"],
            "cpi_factor_to_2025": f,
            "source": f'K-State AgManager {y} cost-return budget "{r["product"]}" ({r["rotation_context"]}), '
                      f'middle yield; {PAGE[y]}',
            "notes": ("includes weed control of the preceding fallow (wheat) or of the period between "
                      "wheat harvest and planting (summer crops); 1 acre-year of rent"),
        })

    for y, rents in sorted(rent_by_year.items()):
        rent = rents.get("wheat|W-F") or rents.get("sorghum|W-S-F")
        src = "wheat|W-F" if "wheat|W-F" in rents else "sorghum|W-S-F"
        f = factors.get(y, latest_factor)
        out.append({
            "year": y, "crop": "fallow", "rotation_context": "any", "cost_key": "fallow|any",
            "cost_usd_per_acre": rent, "cost_real2025_usd_per_acre": round(rent * f, 2),
            "direct_excl_insurance_usd_acre": 0.0, "machinery_fixed_usd_acre": 0.0,
            "land_rent_usd_acre_year": rent, "crop_insurance_usd_acre": 0.0,
            "kstate_total_usd_acre": "", "kstate_rent_acre_years": "", "planning_yield": "",
            "yield_unit": "", "planning_price_usd_per_unit": "", "budget_date": "",
            "cpi_factor_to_2025": f,
            "source": f"K-State AgManager {y}: cash rent per acre-year from the {src} budget; {PAGE[y]}",
            "notes": "land rent only: K-State charges fallow herbicide and tillage to the following crop",
        })

    out.sort(key=lambda r: (r["year"], r["crop"], r["rotation_context"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {OUT}: {len(out)} rows, years {min(r['year'] for r in out)}-{max(r['year'] for r in out)}; "
          f"CPI factor for 2026-2027 (latest 12 months) = {latest_factor}")


if __name__ == "__main__":
    main()
