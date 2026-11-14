"""Build reference/costs.csv: cost per acre for each (year, region, cost_key).

Regions SW, NW, NC, SC. Each K-State budget is split into rotation phases:
    crop phase   = direct costs - crop insurance + machinery fixed costs + 1 year of rent
    fallow phase = 1 year of rent, plus in NC and SC the herbicide cost of the same year's NW wheat (W-F) budget
In NC and SC the budgets of rotations without fallow are used as proxies (column proxy = true).
Costs are given in nominal USD and in 2025 USD (CPI-U).
"""
from __future__ import annotations

import csv
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
REGION_NAME = {"SW": "Southwest KS", "NW": "Northwest KS", "NC": "North Central KS", "SC": "South Central KS",
               "W": "Western KS"}


WEST = {
    "wheat|W-F": ("wheat|W-F", None),
    "wheat|W-S/C-F": ("wheat|W-S/C-F", None),
    "sorghum|W-S-F": ("sorghum|W-S-F", None),
    "corn|W-C-F": ("corn|W-C-F", None),
    "sunflower|W-SF-F": ("sunflower|W-SF-F", "W"),
}
CENTRAL = {
    "wheat|W-F": ("wheat|rotation", None),
    "wheat|W-S/C-F": ("wheat|rotation", None),
    "wheat|continuous": ("wheat|continuous", None),
    "sorghum|W-S-F": ("sorghum|rotation", None),
    "corn|W-C-F": ("corn|rotation", None),
    "sunflower|W-SF-F": ("sunflower|dryland", "NC"),
}
MAPPING = {"SW": WEST, "NW": WEST, "NC": CENTRAL, "SC": CENTRAL}


def read(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def cpi_factors() -> tuple[dict[int, float], float]:
    f, base = {}, None
    for r in read(CPI):
        f[int(r["year"])] = float(r["factor_to_2025_usd"])
        if int(r["year"]) == BASE_YEAR:
            base = float(r["cpi_u_annual_avg"])

    vals = [float(r["CPIAUCSL"]) for r in read(CPI_MONTHLY) if r["CPIAUCSL"] not in ("", ".")]
    return f, round(base / (sum(vals[-12:]) / 12), 4)


def main() -> None:
    budgets = {}
    for r in read(BUDGETS):
        budgets[(int(r["budget_year"]), r["region"], f'{r["crop"]}|{r["rotation_context"]}')] = r
    factors, latest = cpi_factors()
    years = sorted({k[0] for k in budgets})
    out = []

    for y in years:
        f = factors.get(y, latest)
        for region, mapping in MAPPING.items():
            for cost_key, (budget_key, budget_region) in mapping.items():
                b = budgets.get((y, budget_region or region, budget_key))
                if b is None:
                    continue
                direct, ins = float(b["direct_costs_usd_acre"]), float(b["crop_insurance_usd_acre"])
                mach, rent = float(b["machinery_fixed_usd_acre"]), float(b["cash_rent_rate_usd_acre_year"])
                cost = direct - ins + mach + rent
                proxy = region in ("NC", "SC") or (budget_region not in (None, region))
                out.append({
                    "year": y, "region": region, "crop": cost_key.split("|")[0],
                    "rotation_context": cost_key.split("|")[1], "cost_key": cost_key,
                    "cost_usd_per_acre": round(cost, 2), "cost_real2025_usd_per_acre": round(cost * f, 2),
                    "direct_excl_insurance_usd_acre": round(direct - ins, 2),
                    "machinery_fixed_usd_acre": round(mach, 2), "land_rent_usd_acre_year": rent,
                    "crop_insurance_usd_acre": ins, "fallow_weed_control_usd_acre": 0.0,
                    "kstate_budget": f'{REGION_NAME[budget_region or region]} {budget_key}',
                    "proxy": str(proxy).lower(),
                    "kstate_total_usd_acre": b["total_specified_usd_acre"],
                    "kstate_rent_acre_years": b["cash_rent_acre_years_charged"],
                    "planning_yield": b["planning_yield"], "yield_unit": b["yield_unit"],
                    "planning_price_usd_per_unit": b["planning_price_usd_per_unit"],
                    "budget_date": b["budget_date"], "cpi_factor_to_2025": f,
                    "source": f'K-State AgManager {y} cost-return budget "{b["product"]}" '
                              f'({REGION_NAME[budget_region or region]}, {budget_key}), middle yield; {PAGE[y]}',
                    "notes": ("PROXY: K-State budget for a rotation without fallow; " if region in ("NC", "SC") else
                              "includes weed control of the preceding fallow or non-crop period; ")
                             + "1 acre-year of rent",
                })

            rent_src = (budgets.get((y, region, "wheat|W-F")) or budgets.get((y, region, "sorghum|W-S-F"))
                        or budgets.get((y, region, "wheat|rotation")) or budgets.get((y, region, "sorghum|rotation")))
            if rent_src is None:
                continue
            rent = float(rent_src["cash_rent_rate_usd_acre_year"])
            weed, note = 0.0, "land rent only: fallow weed control is inside the following crop's budget"
            if region in ("NC", "SC"):
                nw = budgets.get((y, "NW", "wheat|W-F"))
                if nw is None:
                    continue
                weed = float(nw["herbicides_usd_acre"])
                note = ("land rent + ASSUMPTION A8: fallow weed-control allowance = herbicides of the same "
                        "year's NW wheat (W-F) budget, because central-Kansas budgets have no fallow")
            cost = rent + weed
            out.append({
                "year": y, "region": region, "crop": "fallow", "rotation_context": "any", "cost_key": "fallow|any",
                "cost_usd_per_acre": round(cost, 2), "cost_real2025_usd_per_acre": round(cost * f, 2),
                "direct_excl_insurance_usd_acre": round(weed, 2), "machinery_fixed_usd_acre": 0.0,
                "land_rent_usd_acre_year": rent, "crop_insurance_usd_acre": 0.0,
                "fallow_weed_control_usd_acre": round(weed, 2),
                "kstate_budget": f'{REGION_NAME[region]} cash rent', "proxy": str(region in ("NC", "SC")).lower(),
                "kstate_total_usd_acre": "", "kstate_rent_acre_years": "", "planning_yield": "", "yield_unit": "",
                "planning_price_usd_per_unit": "", "budget_date": "", "cpi_factor_to_2025": f,
                "source": f"K-State AgManager {y}: cash rent per acre-year, {REGION_NAME[region]}; {PAGE[y]}",
                "notes": note,
            })

    out.sort(key=lambda r: (r["year"], r["region"], r["crop"], r["rotation_context"]))
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {OUT}: {len(out)} rows, years {years[0]}-{years[-1]}, regions {sorted(MAPPING)}; "
          f"CPI factor for 2026-2027 (latest 12 months) = {latest}")


if __name__ == "__main__":
    main()
