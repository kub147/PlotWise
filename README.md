# PlotWise

NASA Space Apps Challenge 2026 — [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)

**Live app: https://kub147.github.io/PlotWise/**

A decision-support tool that turns NASA Earth observations into a field-level profile of changing conditions (heat, frost, rainfall, soil moisture, vegetation, water balance) and compares the farmer's current crop rotation with alternatives ranked by the farmer's own priorities. Every suggestion shows its evidence, its uncertainty and what needs local expert review.

## Status

Hackathon weekend, 14–15 November 2026. The app, the engine and the data pipelines are in this repository; the app runs on eleven demo fields at three sites and on 46 counties of western Kansas.

Start here:
- [`docs/project-brief.md`](docs/project-brief.md) — goal, product, why Tribune (Kansas), the engine, validation, scope.
- [`docs/work-plan.md`](docs/work-plan.md) — five workstreams, timeline, file formats, a brief for each person.
- [`docs/transect.md`](docs/transect.md) — why the demo covers three sites and 46 counties, and what each workstream does next.
- [`docs/data-sources.md`](docs/data-sources.md) — every dataset on the challenge page: access, role, priority.
- [`docs/research-evidence.md`](docs/research-evidence.md) — what K-State field trials say and how we use it.
- [`docs/problem-and-solution.md`](docs/problem-and-solution.md) — first sketch of the problem and an example walkthrough.
- [`docs/engine-validation.md`](docs/engine-validation.md) — the engine against 24 years of K-State trial yields.
- [`docs/submission/`](docs/submission/) — submission text, data and reference list, demo storyboard, checklist.

First result: a simple, uncalibrated soil-water balance driven by gridded weather explains 63% of the year-to-year variation in sorghum yield and 44% in wheat yield measured in 24 years of K-State dryland trials at Tribune.

## The app

A static web app in [`app/`](app/) (React, TypeScript, Vite) with six pages: My field, What has changed, Rotation replay, This season, Region and How we know. It reads the processed files in `data/processed/` and the images in `docs/img/`; there is no backend.

```bash
cd app
npm install
npm run dev      # copies the data into app/static, then serves http://localhost:5173
npm run build    # production build in app/build
```

Tested with Node.js 24. The interface is in English and Polish. A push to `main` builds the app and publishes it to GitHub Pages at https://kub147.github.io/PlotWise/ (`.github/workflows/deploy-app.yml`).

What each page answers:

| Page | Question |
| :--- | :--- |
| My field | What is this field: crop history since 2008, soil, bare ground, greenness, surface heat |
| What has changed | Which weather trends at the field are reliable, and which are not |
| Rotation replay | How six rotations would have done here in each year 1996–2025, ranked by the farmer's priorities, at county-average or well-managed yields |
| This season | Where soil moisture stands today against the same dates in earlier years |
| Region | What farmers grow on 31,660 fields in 46 counties, and where the model agrees with them |
| How we know | The engine against 24 years of K-State field trials, the data sources, and what we do not claim |

## Repository layout

```
docs/             project brief, work plan, data and research notes, submission material
reference/        published tables transcribed with citations (K-State trials)
scripts/          exploratory scripts that reproduce the numbers in the docs
pipelines/        data extraction per source (weather, fields)
crops-economics/  crop table, rotations, prices, costs and the evidence register
engine/           soil-water balance, yields, economics, scoring
app/              the web app
data/             processed/ is committed, raw/ is not
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

## Limits

The replay is a comparison of rotations, not a profit forecast. It counts full costs including land rent and leaves out crop insurance and government payments, so most averages are below zero. County results stand on one point per county. Where the model and local practice disagree, the app says so; [`docs/engine-counties.md`](docs/engine-counties.md) has the details.

## Data

NASA POWER, SMAP, GPM IMERG, MODIS / Landsat / Sentinel-2, SRTM, GRACE / GRACE-FO, gridMET / PRISM, USDA Cropland Data Layer and Crop Sequence Boundaries, SSURGO, USDA NASS and AMS, K-State Research and Extension trial reports. Details in [`docs/data-sources.md`](docs/data-sources.md).

## License

Code: [MIT](LICENSE). The data in `data/processed/` and `reference/` is derived from public sources (NASA, USDA, K-State Research and Extension, gridMET, OpenET) that keep their own terms; cite the original source, listed in [`docs/data-sources.md`](docs/data-sources.md) and [`docs/submission/data-and-references.md`](docs/submission/data-and-references.md).
