# engine — workstream D: rotation replay and validation

Takes a field (soil capacity), its daily weather and the rotations of workstream C, and replays every rotation
through every year since 1996: yields, net returns, risk, soil and water indicators, scores, and how much the
ranking depends on the farmer's priorities.

## Run

```bash
python -m engine.counties            # county yield factors + 46-county replay -> engine/county_yield_factors.json,
                                     #   data/processed/results/counties.json, docs/engine-counties.md (about 30 s). Run before engine.run
python -m engine.run                 # replay for every field -> data/processed/results/<field_id>.json
python -m engine.validate            # comparison with the K-State Tribune trials -> docs/engine-validation.md, docs/img/engine_validation.png
                                     #   and data/processed/results/validation.json (series and numbers for the app's "How we know" page)
python -m engine.test_engine         # offline tests (water conservation, schedules, scoring)
python -m engine.calibrate           # only after the model or its inputs change -> engine/params.json (about 30 s)
```

Needs Python 3.10+, `numpy`, and `matplotlib` for the validation figure. Run from the repository root.

## Inputs

| File | From | Used for |
| :--- | :--- | :--- |
| `data/processed/fields.geojson` | B | `awc_mm` (soil water capacity), `current_rotation` |
| `data/processed/weather/<field_id>.csv` | A | daily precipitation, reference ET, temperature |
| `data/processed/climate/<field_id>.json` | A | `year_types` (which years count as dry) |
| `crops-economics/reference/crops.csv`, `rotations.json` | C | crop calendar and coefficients, rotation phases, card text |
| `crops-economics/scripts/lookup.py` | C | every price and cost |
| `reference/kstate_tribune_rotation_yields.csv` | — | validation and yield calibration |
| `engine/validation/tribune_station_gridmet.csv` | D | gridMET weather of the K-State Tribune station, 1994-2020, written from the cache of `scripts/water_balance_baseline.py` |

## Three sites and 46 counties (transect, see docs/transect.md)

- **Cost region** of a field or county: `crops-economics/reference/county_budget_regions.csv` (Tribune SW, Colby NW, Hays NC).
- **Yield level**: the Tribune-calibrated model is far too high in the wetter east (dryland corn about 130 bu/acre at Hays
  against about 70 on farms). Every county and crop gets a factor = mean USDA NASS dryland county yield / mean modelled
  yield, same years (`county_yield_factors.json`). Fields use the factor of their county (field_id prefix, e.g. `ks051`).
  The model keeps the year-to-year variation and the water carried between crops; the county's farms set the average.
- **Two yield scenarios.** Main records: `county_average` (NASS county mean). `yield_scenarios.well_managed` in each field
  file (and `well_managed` per county in counties.json) repeats the per-rotation numbers at the planning yield of the K-State
  budget whose costs are used, 15-45% higher. Costs assume a well-managed field, so the county-average scenario favours fallow.
  The app should let the farmer pick; neither is a forecast. North-central budgets (Hays) are proxies from wetter central
  Kansas, so well-managed Hays is optimistic.
- **Money** is reported with land rent (`mean`) and without it (`mean_before_land_rent`): rent is nearly the same for every
  rotation of a region (43-82 USD/acre/yr), so it hardly affects a ranking, but it differs between regions. The money scores
  (`income`, `dry_year_safety`) are the difference to wheat-fallow on the same field and scenario (±60 USD/acre/yr → 0..1,
  WF = 0.5), so neither rent nor scenario level shifts them.
- **County results** (`results/counties.json`, about 140 kB): per county `best_rotation` (of WF, WSF, WCF, WSSF, WWSF),
  `gain_replacing_fallow_usd_acre` (WSF − WF), per rotation `mean`, `mean_before_land_rent`, `share_of_years_with_profit`,
  `share_of_years_covering_costs_before_rent`, mean yields, and `practice` (what farmers grow, from B's field classification).
  Top level: `agreement_with_practice`, `choice_checks`. Report: `docs/engine-counties.md`.

## How it works

1. **Schedule** (`rotation.py`). A rotation is a list of phases, one per harvest year. Every phase is started in every
   year, so each year has the whole rotation on the land at once.
2. **Water** (`waterbalance.py`). One store of plant-available water, daily, continuous through crops and fallows.
   Crop ET = Kc × reference ET × a soil-water coefficient (FAO-56). Five water parameters, calibrated on measured
   soil water and crop water use at Tribune, not on yields.
3. **Yield** (`yields.py`). Wheat and sorghum: linear in modelled seasonal ET (wheat also loses yield per day ≥ 34 °C
   from flowering to maturity), fitted on the Tribune four-year rotation trial. Corn and sunflower: the K-State
   yield-vs-ET function as published. A second crop of the same kind gets a residual multiplier for what water does
   not explain. Farm level = trial level × farm factor.
4. **Money** (`replay.py`). Yield × the actual Kansas price of that year − the K-State budget cost of the phase,
   2025 USD per acre of the whole rotation, fallow included.
5. **Scores and sensitivity** (`scoring.py`). Four criteria on fixed 0-1 scales; 5,000 random weightings show how often
   each rotation comes first. Default weights are income 2, dry_year_safety 2, water 1, soil 1: water and soil both
   measure cropping intensity (indicators correlate 0.95), so together they weigh as much as one money criterion.

## Output: `data/processed/results/<field_id>.json`

Same shape as `results/sample.json`, with more keys.

- Top level: `field_id`, `period`, `units`, `current_rotation`, `dry_years`, `rotations`, `rotations_not_modelled`,
  `default_weights`, `default_ranking`, `ranking_sensitivity` (`share_of_wins`, `most_often_first`, `stable`),
  `scoring_scales`, `farm_factor`, `assumptions`, `validation`.
- Per rotation: `id`, `name`, `phases`, `status`, `is_current`, `yields_kg_ha` (crop → `[year, kg/ha]`),
  `mean_yield_kg_ha`, `yield_method`, `net_return_usd_acre` (`[year, USD]`), `summary` (`mean`, `p20`, `worst`,
  `worst_year`, `share_of_years_with_loss`, `mean_of_worst_fifth`, `mean_in_dry_years`, `mean_vs_current`,
  `share_of_years_better_than_current`), `indicators` (`bare_days_per_year`, `storage_efficiency`,
  `water_productivity_kg_mm`, `crop_water_share`, `growing_share_of_year`, `crops_per_year`, `failed_crop_years`,
  `failed_harvest_share`), `scores`, and the card text from rotations.json (`why`, `benefits`, `risks`, `evidence`,
  `gaps`, `check_locally`).

To rank with the farmer's own weights in the app: total = Σ weight × score over `water`, `soil`, `income`,
`dry_year_safety`; no engine run is needed.

## What to tell the user (short form of docs/engine-validation.md)

- The model puts the measured crop failures (wheat 2002 and 2013, sorghum 2002 and 2012) among its worst years.
- Sorghum: modelled water use explains about 60% of measured year-to-year yield variation. Wheat: about 45%, and much
  less out of sample. One wheat year is a rough estimate.
- All rotations lose money on average once land rent is paid (full K-State costs, county-average yields, no insurance,
  no government payments). Before rent the best rotations are near break-even. Compare rotations with each other.
- Fields of one site get almost the same numbers: they share the weather of a few 4 km cells and similar soils.
- Along the transect the gain from replacing fallow with sorghum rises from about −17 USD/acre/yr in the far west to
  +12 in the east; the corn-or-sorghum preference follows farmers' choices (docs/engine-counties.md).

## ASSUMPTIONS and open items

| # | Where | Assumption | How to remove it |
| :--- | :--- | :--- | :--- |
| D1 | `county_yield_factors.json` | One constant yield factor per county and crop (no technology trend); corn only from NASS dryland years to 2018; sunflower from all-practices yields | Year-specific factors if NASS county data were complete |
| D8 | `counties.py` | County sorghum average mixes sorghum after wheat with sorghum after sorghum, so WSF is probably undervalued relative to WF | Sorghum yields by previous crop (not in NASS) |
| D9 | `counties.py` | County soil below 200 mm replaced by 280 mm (9 counties) | Cropland-weighted SSURGO from B |
| D2 | `scoring.py` SCALES | Reference scales of the four scores | Review with C and E; they are value judgements |
| D3 | `waterbalance.py` | Growth periods of the Kansas Water Budget mapped on FAO-56 stages (only used for diagnostics) | — |
| D4 | `replay.py` | Land split evenly between the phases of a rotation | — (a convention) |
| D5 | sorghum level | 1996-2020 average; the trial shows a rise of about 2 bu/acre per year that the water model cannot see | Add a technology trend once C confirms the cause |
| D6 | wheat-fallow | Modelled 14-month fallow stores 17% of precipitation, measured 28% | Better fallow physics (residue, snow catch); see validation, section 1 |
| D7 | soil score | Cropping intensity (crops per year) stands in for soil benefit; it correlates 0.95 with the water indicator, so by default the two share one weight (`scoring.py`); residue amounts per crop are not counted | Residue amounts per crop from C, which would make soil an independent criterion |

Not done: the "This season" forward run from today's soil water (stretch), validation against OpenET and SMAP.
