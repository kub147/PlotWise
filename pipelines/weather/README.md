# Weather and water pipeline

Builds the daily weather that drives the rotation replay and the climate summary behind the "What has changed" and
"This season" pages. It covers the eleven demo fields and one point in each of the 46 counties.

| Output | Used by |
| :--- | :--- |
| Daily weather since 1994 for every field and county | The engine (soil-water balance, yields) |
| 30-year trends with a reliability label, year types, monthly water balance | "What has changed" |
| Regional water storage (GRACE) and root-zone soil moisture (SMAP) | "What has changed", "This season" |
| Rainfall cross-check of four products | "What has changed" |
| Monthly field evapotranspiration (OpenET) | Stored as an independent check; not shown in the app |

## Run

```bash
pip install -r pipelines/weather/requirements.txt
earthengine authenticate            # once; in a Codespace: earthengine authenticate --auth_mode=notebook
export EE_PROJECT=<your-earth-engine-project>

python3 pipelines/weather/run.py crosscheck   # rainfall cross-check table for the first field
python3 pipelines/weather/run.py all          # cross-check, weather CSV and climate JSON for every field
python3 pipelines/weather/run.py counties     # weather CSV for every county point
python3 pipelines/weather/openet.py all       # monthly OpenET for the fields, 1999–2024
python3 pipelines/weather/test_compute.py     # offline tests on synthetic data (no Earth Engine, no network)
```

Options: `--field ks071-001` (one field), `--refresh` (ignore the raw cache in `data/raw/weather/`).
Fields are read from `data/processed/fields.geojson` and counties from `data/processed/counties.geojson`.

## Data sources

| Product | What is taken | Grid |
| :--- | :--- | :--- |
| gridMET | Precipitation, daily maximum and minimum temperature, grass reference evapotranspiration | 4 km |
| NASA POWER | Solar radiation and wind; temperature for growing degree days, frost dates and hot days | about 50 km |
| PRISM | Monthly precipitation, the station-based reference in the cross-check | 4 km |
| NASA GPM IMERG | Monthly precipitation in the cross-check | about 11 km |
| NASA GRACE / GRACE-FO | Terrestrial water storage, 2002–2024 | about 300 km |
| NASA SMAP Level 4 | Root-zone soil moisture since 2015 | 9 km |
| OpenET ensemble | Monthly evapotranspiration, averaged over each field outline | 30 m |

All Earth Engine requests are small: one point or field per request and one year at a time. Finished years are cached
and never requested again. County weather is fetched for all 46 points in one request per year.

## Outputs

| File | Content |
| :--- | :--- |
| `data/processed/weather/<field_id>.csv` | `date, precip_mm, tmax_c, tmin_c, eto_mm, srad_mj_m2, wind_m_s`; daily from 1994-01-01 to the last gridMET day, no gaps |
| `data/processed/weather/counties/<county_id>.csv` | The same columns at the county point (`lon`, `lat` in `counties.geojson`) |
| `data/processed/weather/sources.md`, `counties/sources.md` | The product behind each column and the number of days filled from a fallback |
| `data/processed/climate/<field_id>.json` | Trends, year types, monthly water balance, GRACE, SMAP, cross-check (keys below) |
| `data/processed/climate/<field_id>_precip_crosscheck.md`, `.png` | Cross-check table and chart |
| `data/processed/climate/<field_id>_openet.csv`, `openet_summary.json` | Monthly OpenET next to precipitation and reference ET; yearly totals with the crop of that year |

Units in the weather files: mm, °C, mm, MJ/m²/day, m/s at 2 m.

Keys of `climate/<field_id>.json`:

- `trends`: one entry per indicator with `label`, `unit`, `source`, `mean_first_half`, `mean_second_half`,
  `slope_per_decade`, `mk_p`, `reliable`, `n_years`, `first_year`, `last_year`.
- `yearly`: the indicator values per year behind the trends.
- `year_types`: year → `dry`, `normal` or `wet`; `year_type_method` holds the thresholds.
- `monthly_water_balance`: 12 months of mean precipitation, reference ET and their difference.
- `grace`: monthly series, `trend_cm_per_year`, `total_change_cm`, `mk_p`, `note`.
- `smap`: daily series and `latest` (`date`, `value`, `percentile_for_calendar_date`, `n_years`), `note`.
- `precip_crosscheck`: summary rows and yearly totals per product, annual and April–September.
- `sources`, `caveats`.

## Method

- **One source per variable, with a stated fallback.** Precipitation, temperature and reference ET come from gridMET;
  radiation and wind from NASA POWER. A missing day is filled from the other product after unit conversion, and
  `sources.md` counts every filled day.
- **Trends carry a label.** Slopes are ordinary least squares per decade. A trend is called reliable only when the
  Mann-Kendall test gives p < 0.05.
- **Temperature from POWER, water from gridMET.** NASA POWER rainfall disagrees with the other three records at
  Tribune (see below), so it is not used for rainfall indicators.
- **Year types.** Terciles of April–September precipitation minus reference ET over all complete seasons since 1995.
- **Soil moisture percentile.** The latest SMAP root-zone value against all values within ±7 days of the same
  calendar date in every year of the record.
- **Rainfall cross-check.** Annual and April–September totals of the four products are compared over the years all
  of them cover completely, with PRISM as the reference.

## What the checks showed

Mean annual precipitation rises from west to east along the transect, and gridMET agrees with station-based PRISM:

| Site | gridMET, mm/year | PRISM, mm/year | Difference | Correlation of annual totals |
| :--- | ---: | ---: | ---: | ---: |
| Tribune (five fields) | 445–450 | 452–488 | 1–8% | 0.89–0.96 |
| Colby (three fields) | 507–508 | 497–504 | up to 2% | 0.96–0.98 |
| Hays (three fields) | 607–636 | 610–639 | up to 2% | 0.96–0.98 |

- **Rain has no reliable trend.** At Tribune NASA POWER alone shows drying (−34 mm per decade, p = 0.03, 1995–2025);
  gridMET, PRISM and IMERG do not. At Colby and Hays no product shows a reliable trend. The app therefore does not
  say that rain is declining.
- **The season is warmer.** Growing degree days rise by 62 to 76 °C·days per decade at the three sites, reliably.
- **The air is thirstier.** Annual reference ET rises by about 35 mm per decade at Tribune and 47 to 58 mm at Colby
  and Hays.
- **The region is losing stored water.** GRACE shows −0.81 cm of water per year, about −18 cm from 2002 to 2024.
- **OpenET runs high here.** On the five Tribune fields mean annual OpenET is about 20% above gridMET precipitation
  (ET / P 1.19–1.21), dryland wheat–fallow included. A rainfed field cannot evaporate more than it receives over 24
  years, so OpenET is useful for differences between years, crops and fields, not for the absolute level.

## Limits

- Gridded weather describes the area around a field, not the field: gridMET is 4 km, NASA POWER about 50 km. Fields
  at one site share a POWER cell, so their temperature indicators are identical.
- A county file is the weather at one point (the county centroid), not a county mean.
- GRACE is a regional value and SMAP a 9 km model-assimilated cell with 12 years of record. Neither is a field
  measurement.
- The GRACE trend test ignores month-to-month autocorrelation, so its p-value is optimistic.
- OpenET models use gridMET reference ET, so OpenET is not fully independent of the weather files.
- gridMET revises its most recent days; re-run the pipeline before relying on the last rows.
