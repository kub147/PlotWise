# PlotWise

NASA Space Apps Challenge 2026 — [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)

A decision-support tool that turns NASA Earth observations into a field-level profile of changing conditions (heat, frost, rainfall, soil moisture, vegetation, water balance) and compares the farmer's current crop rotation with alternatives ranked by the farmer's own priorities. Every suggestion shows its evidence, its uncertainty and what needs local expert review.

## Status

Hackathon weekend, 14–15 November 2026. The direction is set; the engine has a validated baseline.

Start here:
- [`docs/project-brief.md`](docs/project-brief.md) — goal, product, why Tribune (Kansas), the engine, validation, scope.
- [`docs/work-plan.md`](docs/work-plan.md) — five workstreams, timeline, file formats, a brief for each person.
- [`docs/data-sources.md`](docs/data-sources.md) — every dataset on the challenge page: access, role, priority.
- [`docs/research-evidence.md`](docs/research-evidence.md) — what K-State field trials say and how we use it.
- [`docs/problem-and-solution.md`](docs/problem-and-solution.md) — first sketch of the problem and an example walkthrough.

First result: a simple, uncalibrated soil-water balance driven by gridded weather explains 63% of the year-to-year variation in sorghum yield and 44% in wheat yield measured in 24 years of K-State dryland trials at Tribune.

## Repository layout

```
docs/        project brief, work plan, data and research notes
reference/   published tables transcribed with citations (K-State trials)
scripts/     exploratory scripts that reproduce the numbers in the docs
pipelines/   data extraction per source (weather, fields, economics)
engine/      soil-water balance, yields, economics, scoring
app/         dashboard
data/        processed/ is committed, raw/ is not
```

## Quick start

```bash
# climate indicators and trends for any point (no key needed)
python3 scripts/power_indicators.py --lat 38.47 --lon -101.75 --out climate.json

# crop acreage history for a county from the Cropland Data Layer (no key needed)
python3 scripts/cdl_county_history.py --fips 20071

# observed rotations from CDL pixel history (needs Earth Engine)
EE_PROJECT=<your-ee-project> python3 scripts/cdl_rotation_sequences.py --fips 20071

# baseline: weather + soil-water balance vs measured trial yields (needs Earth Engine, numpy)
EE_PROJECT=<your-ee-project> python3 scripts/water_balance_baseline.py
```

## Data

NASA POWER, SMAP, GPM IMERG, MODIS / Landsat / Sentinel-2, SRTM, GRACE / GRACE-FO, gridMET / PRISM, USDA Cropland Data Layer and Crop Sequence Boundaries, SSURGO, USDA NASS and AMS, K-State Research and Extension trial reports. Details in [`docs/data-sources.md`](docs/data-sources.md).
