# Workstream B — fields, soil and vegetation

Produces `data/processed/fields.geojson` (11 demo fields at three sites: Tribune, Colby and Hays, Kansas), one NDVI series per field in `data/processed/ndvi/`, and a county layer for the western Kansas transect (`data/processed/counties.geojson`, see `docs/transect.md`).

## Run

```bash
export EE_PROJECT=<your-ee-project>
python3 pipelines/fields/delineate_fields.py --fips 20071   # candidate polygons per county (also 20193, 20051) -> data/raw/fields/ (not committed)
python3 pipelines/fields/build_fields.py         # demo fields with all attributes -> data/processed/
python3 pipelines/fields/soil_sda.py             # smoke test of the soil lookup
python3 pipelines/fields/county_layer.py         # 46 western Kansas counties -> data/processed/counties.geojson
python3 pipelines/fields/delineate_all.py        # candidate polygons for all 46 counties (about 10 minutes)
python3 pipelines/fields/transect_rotations.py   # rotation of 31,660 fields -> county_field_rotations.json, county_fields.geojson, docs/img/transect_fields.png
```

Needs `earthengine-api` and `shapely`. Soil Data Access needs no key.

Extras:

```bash
python3 pipelines/fields/heat_stress.py          # ECOSTRESS surface temperature per field and crop class -> data/processed/heat/, docs/img/
python3 pipelines/fields/render_preview.py       # Sentinel-2 overview and NAIP chip per field -> docs/img/
```

```bash
python3 pipelines/fields/county_rotations.py     # all delineated fields classified by rotation -> data/processed/county_fields.geojson, map
python3 pipelines/fields/plot_ndvi.py            # NDVI history chart per demo field -> docs/img/ndvi_<field_id>.png
```

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

## The whole county

`data/processed/county_fields.geojson` (2 MB, for the map in the app) now holds the fields of the three demo counties (written by `transect_rotations.py`; see `docs/transect.md` for the 46-county map). For Greeley County alone: 1,221 delineated fields with `rotation`, `sequence` and `area_ha`; totals are in `data/processed/county_rotation_summary.json`; the picture is `docs/img/county_rotations.png`.

| Rotation 2018–2025 | Fields | Share of area |
| :--- | ---: | ---: |
| Wheat – fallow | 121 | 11% |
| Wheat – sorghum – fallow | 148 | 13% |
| Wheat – corn – fallow | 110 | 9% |
| Moved from wheat – fallow to a 3-year rotation | 51 | 4% |
| No fallow in 8 years | 62 | 4% |
| Other sequences with fallow | 729 | 59% |

These are clean fields of at least 40 ha (about 90,000 ha in total), not all cropland in the county. The large "other" group is itself a finding: most fields do not follow a fixed textbook rotation, so farmers adjust from year to year. The round green fields in the north of the map are irrigated pivots.

## NDVI charts

`docs/img/ndvi_<field_id>.png` shows Landsat greenness since 2012 against the CDL crop of each year. On `ks071-004` the wheat peaks in spring, the flat fallow years and the tall late-summer sorghum peaks of 2022 and 2025 are all visible, so the chart shows the change of rotation without any model.

## Heat stress from ECOSTRESS

Land-surface temperature at 70 m on four clear, hot afternoons (`data/processed/heat/ecostress_summary.json`, maps in `docs/img/ecostress_*.png`).
Crop classes come from the CDL of the same year; class means cover about 25 x 20 km around the demo fields.

| Overpass (UTC) | Growing sorghum | Growing corn | Fallow | Wheat (ripe or stubble) | Coolest vs hottest demo field |
| :--- | ---: | ---: | ---: | ---: | :--- |
| 2023-07-30 20:08 | 45.5 °C | 44.4 °C | 50.5 °C | 49.2 °C | sorghum field 42.3 °C vs fallow field 53.3 °C |
| 2024-08-17 19:11 | 44.6 °C | 46.8 °C | 49.3 °C | 49.4 °C | corn field 42.8 °C vs fallow field 50.6 °C |
| 2021-08-24 18:14 | 47.2 °C | 47.1 °C | 52.8 °C | 52.4 °C | corn field 45.9 °C vs fallow field 53.6 °C |
| 2022-06-16 21:12 | 50.7 °C | 50.5 °C | 50.7 °C | 50.7 °C | no difference: summer crops had just emerged |

Reading: in late July and August a transpiring crop keeps the surface about 5 °C cooler than fallow or stubble across the area, and 8–11 °C cooler on the demo fields. In mid-June there is no difference yet. This is surface temperature on single afternoons, not air temperature and not a seasonal average; the size of the gap depends on overpass time and on how much water the crop has. Use it as a picture of what ground cover does on a hot day, and as a check that the CDL crop labels are right. The circles that stay cold in the maps are irrigated pivots.

## Preview images

- `docs/img/fields_overview_s2.png` — Sentinel-2 true colour, median of 1 July – 15 August 2025, demo fields in yellow.
- `docs/img/field_<field_id>_naip.png` — NAIP aerial image (2023) of each field.

What the NAIP chips show: `ks071-002` (fallow in 2023) is brown with scattered green patches, which explains its rising fallow-year NDVI: weeds, not a crop. `ks071-005` is a strip inside a larger uniformly green field with no pivot circle, so it is most likely dryland continuous cropping rather than irrigated; its polygon covers only part of the real field.

## Known limits

- Boundaries follow CDL pixels, not surveyed field edges; fields are shrunk by 30 m before statistics are taken.
- NDVI sees green cover only. Standing wheat stubble in no-till protects the soil but counts as "bare".
- Field `ks071-005` has no fallow and a summer peak NDVI of 0.65, below our 0.7 irrigation cut-off but above the dryland fields (0.46–0.52). The 2023 aerial image shows no pivot, so it is probably dryland, but this is not confirmed.
- Field `ks071-002` shows rising NDVI in recent fallow summers (0.26–0.33 since 2021): the 2023 aerial image points to weeds.
