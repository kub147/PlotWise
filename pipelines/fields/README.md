# Workstream B — fields, soil and vegetation

Produces `data/processed/fields.geojson` (five demo fields in Greeley County, Kansas) and one NDVI series per field in `data/processed/ndvi/`.

## Run

```bash
export EE_PROJECT=<your-ee-project>
python3 pipelines/fields/delineate_fields.py     # candidate polygons for the county -> data/raw/fields/ (not committed)
python3 pipelines/fields/build_fields.py         # demo fields with all attributes -> data/processed/
python3 pipelines/fields/soil_sda.py             # smoke test of the soil lookup
```

Needs `earthengine-api` and `shapely`. Soil Data Access needs no key.

## What each field carries

| Property | Meaning | Source |
| :--- | :--- | :--- |
| `field_id`, `name`, `county_fips`, `area_ha`, `lon`, `lat` | Identity and centroid | — |
| `crop_history`, `crop_history_names` | CDL class per year, 2008 → 2025 (majority inside the field) | USDA CDL |
| `crop_sequence` | The same as letters: W wheat, F fallow, S sorghum, C corn, O other | CDL |
| `current_rotation`, `fallow_share` | Rotation label from the last six years; share of fallow years since 2008 | CDL |
| `awc_mm` | Plant-available water capacity to 150 cm | SSURGO |
| `texture`, `organic_matter_pct`, `kfactor`, `clay_pct`, `sand_pct` | Surface horizon | SSURGO |
| `hydrologic_group`, `soil_series`, `soil_map_unit`, `soil_map_unit_share` | Dominant map unit | SSURGO |
| `slope_pct` | Mean slope, SRTM smoothed over about 150 m | SRTM |
| `bare_days_per_year`, `bare_days_by_year` | Days with field-mean NDVI below 0.25 | Landsat 5/7/8/9 |
| `summer_peak_ndvi`, `probably_irrigated` | Mean June–August maximum NDVI of the last 8 years; irrigated if no fallow and peak ≥ 0.7 | Landsat |

## How the fields were found

The USDA Crop Sequence Boundaries archive (3.8 GB) refuses scripted downloads, so `delineate_fields.py` applies the same idea directly: neighbouring 30 m pixels with an identical 2018–2025 CDL crop sequence form one field. For Greeley County this gives 1,221 polygons of at least 40 ha that were cropland in every year: 148 in wheat–sorghum–fallow, 121 in wheat–fallow, 110 in wheat–corn–fallow, 51 that moved from wheat–fallow to a three-year rotation, 62 with no fallow, the rest mixed. The demo fields are compact polygons within 7 km of the K-State Tribune station, one per rotation type.

## Checks done

- **CDL vs NDVI.** In years CDL calls fallow, May–August NDVI has a median of 0.18 (90th percentile 0.26); in sorghum and corn years the summer mean is 0.4–0.55. The two independent sources agree on which years were fallow.
- **Slope.** Raw 30 m SRTM gave 3–5% on visibly flat fields because elevations are whole metres. After smoothing, slopes are 0.7–1.9%, in line with the SSURGO map-unit names ("0 to 1" and "1 to 3 percent slopes").
- **Soil.** All five fields are Ulysses or Richfield silt loam with 304–332 mm of available water to 150 cm. The engine baseline assumed 250 mm.

## Known limits

- Boundaries follow CDL pixels, not surveyed field edges; fields are shrunk by 30 m before statistics are taken.
- NDVI sees green cover only. Standing wheat stubble in no-till protects the soil but counts as "bare".
- Field `ks071-005` has no fallow and a summer peak NDVI of 0.65, below our 0.7 irrigation cut-off but above the dryland fields (0.46–0.52). Treat its irrigation status as uncertain.
- Field `ks071-002` shows rising NDVI in recent fallow summers (0.26–0.33 since 2021): weeds, a cover crop, or a CDL error. Worth a look on NAIP.
