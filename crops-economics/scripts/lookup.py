"""Prices and costs for the engine.

    eco = Economics()
    eco.price_usd_per_kg(year, crop)
    eco.phase_cost_usd_per_acre(year, cost_key, region="SW")
    eco.net_return_usd_per_acre(year, crop, cost_key, yield_kg_ha, region="SW")

Values are in 2025 USD (real=False gives nominal). For a year without a budget the cost is the mean
real cost of 2016-2026 for that region and cost_key. A missing price raises KeyError.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


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
        self.costs: dict[tuple[str, str], dict[int, tuple[float, float]]] = defaultdict(dict)
        for r in _read(ref / "costs.csv"):
            key = (r.get("region") or "SW", r["cost_key"])
            self.costs[key][int(r["year"])] = (float(r["cost_usd_per_acre"]),
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

    def phase_cost_usd_per_acre(self, year: int, cost_key: str, real: bool = True, region: str = "SW") -> float:
        """Cost per acre of one rotation phase; region is SW, NW, NC or SC."""
        key = (region, cost_key)
        if key not in self.costs:
            raise KeyError(f"no cost for {cost_key!r} in region {region!r}; see reference/costs.csv")
        if year in self.costs[key]:
            nominal, real_v = self.costs[key][year]
            return real_v if real else nominal
        real_v = self.mean_real_cost[key]
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
                                real: bool = True, region: str = "SW") -> float:
        revenue = yield_kg_ha * ACRE_HA * self.price_usd_per_kg(year, crop, real)
        return revenue - self.phase_cost_usd_per_acre(year, cost_key, real, region)
