# Field Shift

NASA Space Apps Challenge 2026 — [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)

A decision-support tool that turns NASA Earth observations into a field-level profile of changing conditions (heat, frost, rainfall, soil moisture, vegetation, water balance) and compares the farmer's current crop rotation with alternatives ranked by the farmer's own priorities. Every suggestion shows its evidence, its uncertainty and what needs local expert review.

## Status

Early stage — problem definition and an example walkthrough:
- [`docs/problem-and-solution.md`](docs/problem-and-solution.md) — problem statement, example for a field in western Kansas with real NASA POWER indicators, rotation strategies, team roles.
- [`scripts/power_indicators.py`](scripts/power_indicators.py) — climate indicators from NASA POWER daily data (GDD, frost dates, heat days, Hargreaves ET₀, monthly water balance, Mann-Kendall trends).

## Quick start

```bash
python3 scripts/power_indicators.py --lat 37.97 --lon -100.87 --start 1995 --end 2024 --out climate.json
```

No API key needed; standard library only.

## Data

NASA POWER, SMAP, GPM IMERG, MODIS / Landsat / Sentinel-2, SRTM, GRACE / GRACE-FO, USDA Cropland Data Layer, SSURGO / SoilGrids, FAO GAEZ.
