# pipelines/weather — workstream A

Daily weather and the "What has changed" numbers for each demo field.

## Run

```bash
pip install -r pipelines/weather/requirements.txt
earthengine authenticate            # once; in a Codespace use: earthengine authenticate --auth_mode=notebook
export EE_PROJECT=<your-earth-engine-project>

python3 pipelines/weather/run.py crosscheck   # step 1: precipitation cross-check table for the first field
python3 pipelines/weather/run.py all          # cross-check + weather CSV + climate JSON for every field
python3 pipelines/weather/test_compute.py     # offline tests on synthetic data (no Earth Engine, no network)
```

Options: `--field ks071-001` (one field), `--refresh` (ignore the raw cache in `data/raw/weather/`).

Fields are read from `data/processed/fields.geojson` (`field_id`, `lon`, `lat`). Until B delivers that file the
pipeline uses one point, lon −101.75, lat 38.47, as `ks071-001` (ASSUMPTION: rename if B picks another ID).

## Outputs

| File | Content |
| :--- | :--- |
| `data/processed/weather/<field_id>.csv` | `date, precip_mm, tmax_c, tmin_c, eto_mm, srad_mj_m2, wind_m_s`, daily from 1994-01-01 to the last gridMET day, no gaps |
| `data/processed/weather/sources.md` | Product behind each column and the number of days taken from each fallback |
| `data/processed/climate/<field_id>.json` | See keys below |
| `data/processed/climate/<field_id>_precip_crosscheck.md`, `.png` | Cross-check table and chart |

Keys of `climate/<field_id>.json`:

- `trends` — list of `indicator, label, unit, source, mean_first_half, mean_second_half, slope_per_decade, mk_p, reliable, n_years, first_year, last_year`. `reliable` is true when Mann-Kendall p < 0.05.
- `yearly` — year → indicator values behind the trends (for charts).
- `year_types` — year → `dry` / `normal` / `wet`; `year_type_method` holds the thresholds and the yearly values.
- `monthly_water_balance` — `period` and 12 × `month, precip_mm, eto_mm, balance_mm`.
- `grace` — `series` (`date, lwe_cm`), `trend_cm_per_year`, `total_change_cm`, `mk_p`, `note`.
- `smap` — `series` (`date, sm_rootzone`), `latest` (`date, value, percentile_for_calendar_date, window_days, n_values, n_years`), `note`.
- `precip_crosscheck` — summary rows and yearly totals per product, annual and April–September.
- `sources`, `caveats`.

## Method choices

- Precipitation, Tmax, Tmin and reference ET come from gridMET; radiation and wind from NASA POWER.
  Missing days fall back to the other product with unit conversion; the counts are in `sources.md`.
- Temperature indicators (GDD, frost dates, hot days) use NASA POWER, water indicators use gridMET, because NASA POWER rainfall disagrees with the other records here.
- Year types: terciles of April–September precipitation minus reference ET over all complete seasons since 1995.
- SMAP percentile: latest root-zone value against all values within ±7 days of the same calendar date, all years.
  One 3-hourly field per day (the first of each UTC day) keeps the request small; root-zone moisture changes slowly.
- Cross-check statistics use only the years every product covers completely; PRISM (station-based) is the reference.

## Earth Engine load

One point per request: gridMET one call per year (6 bands), SMAP one call per year, PRISM, IMERG and GRACE one call
each. Finished years are cached and never requested again. A first run for one field is about 50 small calls.

## Known limits

- gridMET is 4 km and NASA POWER about 50 km: the files describe the area around the field.
- PRISM is read from `OREGONSTATE/PRISM/ANm` (the older `AN81m` asset is deprecated and stops in 2020). The table states the years actually compared.
- Temperature indicators are identical for all five fields: they share one NASA POWER cell (about 50 km).
- The GRACE p-value ignores autocorrelation between months.

## OpenET (stretch)

```bash
python3 pipelines/weather/openet.py check   # coverage of two test years, 2 requests
python3 pipelines/weather/openet.py all     # 1999–2024, one request per year for all fields
```

Writes `data/processed/climate/<field_id>_openet.csv` (`month, et_mm, et_min_mm, et_max_mm, valid_pixel_share, precip_mm, eto_mm`)
and `data/processed/climate/openet_summary.json` (per field: yearly ET next to precipitation, reference ET and the CDL crop;
mean ET/P; April–October ET by crop). ET is the field mean of the OpenET ensemble at 30 m; `et_min_mm` / `et_max_mm` are the
range across the six models. The collection is tiled by UTM zone and a tile is masked outside its zone (a single-image point query can
return nothing, which is what the note in data-sources.md saw); the script mosaics the tiles first. Months where fewer than 90% of the field's pixels have a value are left empty.
Result for the five demo fields (1999–2024): mean annual OpenET is about 20% above gridMET precipitation on every field
(ET / P 1.19–1.21), dryland wheat–fallow included. Over 24 years that cannot be real for a rainfed field, so OpenET is biased
high here relative to gridMET precipitation. Use it for differences between years, crops and fields, not for absolute ET.

## Notes for the engine and the app

**To D (engine)**

- `data/processed/weather/ks071-001.csv` … `ks071-005.csv` are ready: daily, 1994-01-01 to the last gridMET day, no gaps, columns as listed under "Outputs". Units: mm, °C, mm, MJ/m²/day, m/s at 2 m.
- `precip_mm`, `tmax_c`, `tmin_c`, `eto_mm` are gridMET (4 km). `eto_mm` is grass reference ET (ASCE Penman-Monteith), the same variable the baseline script uses.
- `srad_mj_m2` and `wind_m_s` are NASA POWER (about 50 km); the most recent days fall back to gridMET. Counts per source are in `data/processed/weather/sources.md`.
- The last rows are only a few days old and gridMET revises recent days: re-run the pipeline before the final results.

**To E (app)**

- View 2 reads `data/processed/climate/<field_id>.json`; the keys are listed under "Outputs" above.
- Use `trends[].reliable` for the "reliable / not reliable" label and `trends[].label` / `unit` for display text (metric: convert for the farmer).
- Precipitation shows no reliable trend in any product except NASA POWER, whose drying trend the other three do not confirm. Do not write that rainfall is declining; `precip_crosscheck` and `<field_id>_precip_crosscheck.png` hold the evidence.
- GDD, hot days and frost dates are the same for all five fields (one NASA POWER cell). Present them as "the area", not "this field".
- `grace` is a regional value (~300 km) and `smap` a 9 km cell: show them with their `note`, never as a field measurement.

**To D (engine), OpenET**

- For validation level 4 compare modelled crop ET with `et_apr_oct_mm` per year in `openet_summary.json` (`yearly[]`, with the CDL crop of that year), or with the monthly values in `<field_id>_openet.csv`. Use `et_min` / `et_max` as the uncertainty band.
- Expect modelled ET to be about 20% below OpenET in absolute terms (see the result above): compare the year-to-year pattern (correlation, ranking of years), not the level.
- OpenET is itself a model ensemble driven by gridMET reference ET, so it is not fully independent of our weather input.

## County weather (transect map)

```bash
python3 pipelines/weather/run.py counties
```

Writes `data/processed/weather/counties/<county_id>.csv` (same columns as the field files) for every county in
`data/processed/counties.geojson`, at the county point (`lon`, `lat`), plus `counties/sources.md`.
gridMET is fetched in one request per year for all county points together; NASA POWER needs one HTTP request per county.
No climate JSON and no cross-check are produced at county level.

**To D:** a county file is the weather at one point (the county centroid), not a county mean, so treat county results
as indicative. Rainfall differs within a county by more than between neighbouring centroids in some years.
