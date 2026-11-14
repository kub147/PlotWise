"""Price and cost lookups for the engine, with the fallback rules written down once.

    import sys; sys.path.insert(0, "crops-economics/scripts")   # path to this folder
    from lookup import Economics
    eco = Economics()                                          # reads crops-economics/reference/
    eco.price_usd_per_kg(2012, "grain_sorghum")             # real 2025 USD by default
    eco.phase_cost_usd_per_acre(2012, "sorghum|W-S-F")      # real 2025 USD
    eco.net_return_usd_per_acre(2012, "grain_sorghum", "sorghum|W-S-F", yield_kg_ha=3000)

Rules (also in reference/README.md):
- Costs: K-State budgets exist for 2016-2027. For a year outside that range, or a key missing in a
  year (no SW wheat budget in 2027), the cost is the MEAN OF THE REAL (2025 USD) COSTS of all budget
  years 2016-2026 for that key. ASSUMPTION: real input costs before 2016 were similar to 2016-2026.
- Prices: the actual Kansas marketing-year price of that year (historical replay). No fallback: a
  missing price raises an error, so a gap is never filled silently.
- real=True (default) returns 2025 dollars; real=False returns the nominal dollars of that year.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

# Folder root (crops-economics/): every path is relative to it, so scripts run from anywhere.
ROOT = Path(__file__).resolve().parent.parent

ACRE_HA = 0.40468564224
PRICE_CROP = {"winter_wheat": "wheat", "grain_sorghum": "sorghum", "corn": "corn", "sunflower": "sunflower"}


def _read(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


class Economics:
    def __init__(self, reference_dir: str | Path | None = None):
        ref = Path(reference_dir) if reference_dir else ROOT / "reference"
        self.cpi_factor = {int(r["year"]): float(r["factor_to_2025_usd"])
                           for r in _read(ref / "cpi_u_annual.csv")}
        self.costs: dict[str, dict[int, tuple[float, float]]] = defaultdict(dict)
        for r in _read(ref / "costs.csv"):
            self.costs[r["cost_key"]][int(r["year"])] = (float(r["cost_usd_per_acre"]),
                                                         float(r["cost_real2025_usd_per_acre"]))
        self.mean_real_cost = {k: sum(v[1] for y, v in ys.items() if y <= 2026) /
                               len([y for y in ys if y <= 2026]) for k, ys in self.costs.items()}
        self.prices: dict[str, dict[int, tuple[float, float]]] = defaultdict(dict)
        p = ref / "prices.csv"
        if p.exists():
            for r in _read(p):
                if r["price_real2025_usd_per_kg"]:
                    self.prices[r["crop"]][int(r["year"])] = (float(r["price_usd_per_kg"]),
                                                              float(r["price_real2025_usd_per_kg"]))

    def _deflate(self, real_value: float, year: int) -> float:
        if year not in self.cpi_factor:
            raise KeyError(f"no CPI for {year}")
        return real_value / self.cpi_factor[year]

    def phase_cost_usd_per_acre(self, year: int, cost_key: str, real: bool = True) -> float:
        if cost_key not in self.costs:
            raise KeyError(f"unknown cost_key {cost_key!r}; see reference/costs.csv")
        if year in self.costs[cost_key]:
            nominal, real_v = self.costs[cost_key][year]
            return real_v if real else nominal
        real_v = self.mean_real_cost[cost_key]
        return real_v if real else self._deflate(real_v, year)

    def price_usd_per_kg(self, year: int, crop: str, real: bool = True) -> float:
        pc = PRICE_CROP.get(crop)
        if pc is None:
            raise KeyError(f"no price series for crop {crop!r}")
        if year not in self.prices[pc]:
            raise KeyError(f"no {pc} price for {year}: run fetch_nass.py and build_prices.py")
        nominal, real_v = self.prices[pc][year]
        return real_v if real else nominal

    def net_return_usd_per_acre(self, year: int, crop: str, cost_key: str, yield_kg_ha: float,
                                real: bool = True) -> float:
        revenue = yield_kg_ha * ACRE_HA * self.price_usd_per_kg(year, crop, real)
        return revenue - self.phase_cost_usd_per_acre(year, cost_key, real)
