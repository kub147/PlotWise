# Data and references

What PlotWise actually uses, for the "Space agency data" and "References" parts of the submission form.
Only datasets that feed a number or an image in the product are listed. Datasets we evaluated and did not use are in
[../data-sources.md](../data-sources.md). "GEE" is the Google Earth Engine asset ID used by the pipelines.

## NASA data

| Dataset | What we take from it | Where it shows in the app | Access |
| :--- | :--- | :--- | :--- |
| NASA POWER (daily, point) | Temperature, radiation, wind; growing degree days, frost dates, hot days | What has changed | https://power.larc.nasa.gov/api/temporal/daily/point |
| GPM IMERG monthly V07 | Precipitation, as one of four records in the rainfall cross-check | What has changed | GEE `NASA/GPM_L3/IMERG_MONTHLY_V07` |
| GRACE / GRACE-FO mascons | Monthly terrestrial water storage, 2002–2024 (regional) | What has changed | GEE `NASA/GRACE/MASS_GRIDS_V04/MASCON` |
| SMAP Level 4 (SPL4SMGP) | Root-zone soil moisture, 9 km, 2015 to today; percentile for the calendar date | This season | GEE `NASA/SMAP/SPL4SMGP/008` |
| Landsat 5, 7, 8, 9 Collection 2 Level 2 (NASA / USGS) | NDVI per field since 2008; bare-ground days; mean summer NDVI 2021–2025 around each site (map layer) | My field | GEE `LANDSAT/LT05/C02/T1_L2`, `LE07`, `LC08`, `LC09` |
| ECOSTRESS L2T LSTE V2 | Land surface temperature, 70 m, twelve scenes: four each around Tribune, Colby and Hays | My field, What has changed | GEE `NASA/ECOSTRESS/L2T_LSTE/V2` |
| SRTM 30 m | Slope per field | My field | GEE `USGS/SRTMGL1_003` |

## Partner space agency data

| Dataset | What we take from it | Where it shows | Access |
| :--- | :--- | :--- | :--- |
| Sentinel-2 surface reflectance (ESA / Copernicus) | Overview image of the demo fields | Documentation figure | GEE `COPERNICUS/S2_SR_HARMONIZED` |

## Other open data

| Dataset | What we take from it | Where it shows | Access |
| :--- | :--- | :--- | :--- |
| gridMET (University of Idaho) | Daily precipitation, temperature and reference evapotranspiration, 4 km, 1994 to today: the weather that drives the engine | Rotation replay, What has changed | GEE `IDAHO_EPSCOR/GRIDMET` |
| PRISM (Oregon State University) | Monthly precipitation: the reference in the rainfall cross-check | What has changed | GEE `OREGONSTATE/PRISM/ANm` |
| USDA NASS Cropland Data Layer | Crop per 30 m pixel and year, 2008–2025: field outlines, crop history, county rotations | My field, Region | GEE `USDA/NASS/CDL` |
| USDA NRCS SSURGO (Soil Data Access) | Soil map unit, texture, organic matter, plant-available water to 5 ft | My field, engine | https://sdmdataaccess.sc.egov.usda.gov |
| USDA NAIP | 1 m aerial photos of the 11 demo fields | My field | GEE `USDA/NAIP/DOQQ` |
| USDA NASS QuickStats | Kansas marketing-year prices; dryland county yields | Rotation replay, Region | https://quickstats.nass.usda.gov |
| K-State AgManager farm budgets | Dryland cost per acre by crop, rotation and region, 2016–2027 | Rotation replay | https://www.agmanager.info/farm-budgets |
| BLS CPI-U | Conversion to 2025 dollars | Rotation replay | FRED series CPIAUCSL |
| US Census TIGER counties | County outlines | Region | GEE `TIGER/2018/Counties` |
| Esri World Imagery | Aerial base map tiles | My field, Region | ArcGIS Online tile service |
| OpenET ensemble (monthly) | Field-scale evapotranspiration for five fields; computed and stored, not shown in the app | — | GEE `projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0` |

## Field research the model is built on and checked against

Evidence IDs (E01…) are the ones shown on the rotation cards; the full register is
[`crops-economics/reference/evidence.md`](../../crops-economics/reference/evidence.md).

1. Schlegel, Holman, Burnett (2021). *Wheat and Grain Sorghum in Four-Year Rotations.* Kansas Agricultural
   Experiment Station Research Reports 7(7). doi:10.4148/2378-5977.8102 — year-by-year yields 1996–2020; validation
   data (E01–E06).
2. Schlegel, Haag, O'Brien (2016). *Large-Scale Dryland Cropping Systems.* Kansas Agricultural Experiment
   Station Research Reports 2(7). doi:10.4148/2378-5977.1255 — net returns, fallow efficiency, soil water and crop
   water use 2008–2015 (E07–E12).
3. Schlegel, Burnett (2021). *Tillage Intensity in a Long-Term Wheat-Sorghum-Fallow Rotation.* Kansas
   Agricultural Experiment Station Research Reports 7(7) (E13–E15).
4. Gwin, Norwood, Lamm (1984). *Research on Wheat-Sorghum-Fallow in Western Kansas.* Kansas State
   University (E16).
5. Stone, Schlegel, Khan, Klocke, Aiken (2006). *Water Supply: Yield Relationships Developed for
   Study of Water Management.* Table 1 — yield as a function of seasonal water use (E17, E18).
6. Allen, Pereira, Raes, Smith (1998). *Crop Evapotranspiration.* FAO Irrigation and Drainage Paper 56
   — crop coefficients, stage lengths, rooting depth (E23–E25). https://www.fao.org/4/x0490e/x0490e00.htm
7. Simon, Obour, Holman, et al. (2020). *Long-Term Cover Crop Management Effects on Soil Health in Semiarid
   Dryland Cropping Systems.* Kansas Agricultural Experiment Station Research Reports 6(5) (E19).
8. Holman, Obour, Assefa (2021). *Crop Science.* doi:10.1002/csc2.20670 — abstract only; used for
   direction, not for numbers (E20).
9. Lahdelma, Hokkanen, Salminen (1998). *SMAA — Stochastic multiobjective acceptability analysis.*
   European Journal of Operational Research 106 — the method behind the "how often does each rotation win" test.

## Software

Python (NumPy, Matplotlib, Google Earth Engine API) for pipelines and the engine. The app: React, TypeScript, Vite,
Tailwind CSS, Leaflet and React Leaflet, Recharts, Radix UI, Lucide icons, Geologica typeface. All open source.

## Our own documents

- Validation of the engine against the Tribune trials: [../engine-validation.md](../engine-validation.md)
- The engine across 46 counties: [../engine-counties.md](../engine-counties.md)
- Why three sites along the rainfall gradient: [../transect.md](../transect.md)
- Published findings and how each is used: [../research-evidence.md](../research-evidence.md)
