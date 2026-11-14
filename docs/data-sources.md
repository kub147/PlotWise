# Data sources

Every resource listed on the challenge page, plus the extras we add. Access was tested on 2026-11-14 from a laptop
(Earth Engine Python API and plain HTTP). "GEE" = Google Earth Engine asset ID, confirmed to exist.

Priority: **core** = needed for the minimum product · **support** = improves or validates · **skip** = considered, not used, with the reason.
Owner = workstream in [work-plan.md](work-plan.md).

## NASA resources from the challenge page

| Dataset | What it gives us | Access (tested) | Role in PlotWise | Priority | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SMAP** | Surface and root-zone soil moisture, 9 km, every 3 h, 2015 → today | GEE `NASA/SMAP/SPL4SMGP/008` (latest image 2026-11-10; root zone at Tribune 0.29 m³/m³), `NASA/SMAP/SPL3SMP_E/006` | "This season" view: today's soil-water percentile for the date; check of modelled soil water (anomalies, not absolute values) | core for view 4 | A |
| **GPM IMERG** | Precipitation, 0.1°, half-hourly and monthly, 2000 → today | GEE `NASA/GPM_L3/IMERG_V07`, `NASA/GPM_L3/IMERG_MONTHLY_V07` | Second precipitation product for cross-checking; heavy-rain days (erosion risk); global coverage for other regions | support | A |
| **Landsat** | 30 m reflectance, NDVI, since 1984 | GEE `LANDSAT/LC08/C02/T1_L2` (and LC09, LE07, LT05); harmonised with Sentinel-2 in `NASA/HLS/HLSL30/v002`, `NASA/HLS/HLSS30/v002` | Field-scale NDVI history: bare-soil periods, crop calendar per field | core | B |
| **MODIS / VIIRS** | 250 m NDVI every 16 days since 2000; ET (MOD16); LST | GEE `MODIS/061/MOD13Q1`, `MODIS/061/MOD16A2GF`, `MODIS/061/MOD11A2`, `NASA/VIIRS/002/VNP13A1` | Long, gap-free NDVI series for large fields; MOD16 as an ET cross-check | support | B |
| **NASA POWER** | Daily temperature, radiation, humidity, wind, precipitation since 1981, about 0.5° | REST API, no key (`scripts/power_indicators.py`). Not in GEE | Temperature, GDD, frost dates, heat days, radiation for ET. **Do not use its precipitation for trends** (see project brief) | core | A |
| **SRTM** | 30 m elevation | GEE `USGS/SRTMGL1_003` | Slope per field → water-erosion and runoff flag | core (cheap) | B |
| **ECOSTRESS** | 70 m land-surface temperature, irregular overpasses, 2018 → | GEE `NASA/ECOSTRESS/L2T_LSTE/V2` | Within-field heat-stress map for the demo field on a hot day | stretch | B |
| **GRACE / GRACE-FO** (named in the objectives) | Monthly terrestrial water storage, about 300 km, 2002 → 2024 | GEE `NASA/GRACE/MASS_GRIDS_V04/MASCON` (trend at Tribune −0.81 cm/yr) | Regional water-storage trend in "What has changed". Regional only: never present it as a field value | support | A |
| **NLDAS / GLDAS** | Hourly forcing since 1979 (NLDAS, 1/8°); modelled soil moisture since 2000 (GLDAS) | GEE `NASA/NLDAS/FORA0125_H002`, `NASA/GLDAS/V021/NOAH/G025/T3H` | Soil-moisture context before SMAP (2000–2015); alternative forcing | support | A |
| **GEDI** | Forest canopy height and biomass | GEE `LARSE/GEDI/GEDI04_A_002_MONTHLY` | **Skip.** Built for tall vegetation; no usable signal for annual crops on treeless plains. We say so rather than force it in | skip | — |

## Other resources from the challenge page

| Dataset | What it gives us | Access (tested) | Role in PlotWise | Priority | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cropland Data Layer (CDL)** | Crop type per 30 m pixel, every year since 2008 (Kansas) | GEE `USDA/NASS/CDL`; CropScape statistics API, no key (`scripts/cdl_county_history.py`) | The rotation actually practised on each field; county trends; fallow frequency | core | B |
| **SSURGO / STATSGO2, Web Soil Survey** | Soil map units with texture, organic matter, available water capacity, erodibility, hydrologic group | Soil Data Access REST, no key: `POST https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest` (SQL in, JSON out). Web Soil Survey is the same data with a UI | Root-zone water capacity for the engine (replaces the 250 mm assumption); erodibility for soil indicators | core | B |
| **PRISM** | Daily and monthly precipitation and temperature, 4 km, station-based, since 1981 | GEE `OREGONSTATE/PRISM/AN81d`, `AN81m`; web service tested (`services.nacse.org/prism/data/get/us/4km/ppt/<yyyymm>`) | Precipitation forcing (or gridMET, which blends PRISM with NLDAS); the reference when products disagree | core | A |
| **USDA NASS QuickStats** | County yields and acreage; state monthly prices received, decades back | API needs a free key (401 without one): https://quickstats.nass.usda.gov/api | Validation level 3 (county yields); price history for economics | core | C |
| **USDA AMS Market News** | Daily local cash bids and basis | MARS API needs a free account and key (403 without one) | Local price for "today" scenario; shows whether a crop has a local market | support | C |
| **OpenET** | Monthly field-scale ET, 30 m, 1999 → 2024 | GEE `projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0` (the `OpenET/ENSEMBLE/...` ID is deprecated). A test pixel at Tribune returned no value for December 2024: **check coverage of growing-season months first** | Independent check of modelled crop ET on real fields | stretch | A |
| **NAIP** | 1 m aerial imagery | GEE `USDA/NAIP/DOQQ` | Background image of the demo fields; visual check of field outlines | support | E |
| **NLCD** | 30 m land cover | GEE `USGS/NLCD_RELEASES/2021_REL/NLCD` | Mask non-cropland around fields | support | B |
| **FAO GAEZ** | Global crop suitability and attainable yield | Portal reachable (gaez.fao.org); not in GEE | Sanity check for alternative crops; the argument that the method transfers to other countries | stretch | C |
| **CoCoRaHS** | Volunteer daily rain gauges | CSV export endpoint responds; station query needs tuning | Ground check of gridded precipitation near the demo field | stretch | A |
| **USGS NWIS** | Groundwater levels, streamflow | Legacy endpoint returned HTTP 403 today. Kansas well records are better served by the Kansas Geological Survey (WIZARD) | Aquifer decline for the story; GRACE already covers the regional signal | skip unless time | A |
| **USDA Ag Data Commons** | Research datasets from USDA labs | Portal only; one API search returned nothing useful | Possible source of ARS Akron (Colorado) dryland trial data as a second validation site | stretch | C |
| **LANDFIRE** | Vegetation type and fuels | GEE `LANDFIRE/Vegetation/EVT/v1_4_0` | **Skip.** Describes natural vegetation and fire fuels, not annual cropland | skip | — |

## Partner resources from the challenge page

| Dataset | What it gives us | Access (tested) | Role in PlotWise | Priority | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sentinel-2** (ESA) | 10–20 m reflectance every 5 days, 2017 → (surface reflectance) | GEE `COPERNICUS/S2_SR_HARMONIZED`; also in HLS | Sharpest view of bare soil and crop cover on the demo fields | core for visuals | B |
| **ERA5** (ECMWF) | Hourly reanalysis since 1950; ERA5-Land 9 km | GEE `ECMWF/ERA5_LAND/DAILY_AGGR` | Wind speed for a wind-erosion flag; fallback forcing outside the US | support | A |

## Extras we add

| Dataset | Why | Access |
| :--- | :--- | :--- |
| **gridMET** | Daily 4 km weather with reference ET already computed, 1979 → today; used in our baseline | GEE `IDAHO_EPSCOR/GRIDMET`; drought indices in `GRIDMET/DROUGHT` |
| **Crop Sequence Boundaries (USDA NASS)** | Field polygons for the whole US, each with its 8-year crop sequence. Gives us real field outlines and the "current rotation" in one file | `NationalCSB_2018-2025_rev23.zip` (3.8 GB) on the NASS CSB page; the server refuses scripted downloads, so get it in a browser if needed. Not in GEE. Workstream B derives equivalent polygons from CDL sequences instead (`pipelines/fields/delineate_fields.py`) |
| **POLARIS / SoilGrids** | Gridded soil properties when a raster is easier than SSURGO polygons | GEE `projects/sat-io/open-datasets/polaris/*`, `projects/soilgrids-isric/*` |
| **K-State Tribune trial tables** | Measured yields, soil water and economics by rotation — our validation data | `reference/*.csv` (transcribed from the open reports, with citations) |
| **K-State AgManager budgets** | Cost per acre for dryland wheat, sorghum, corn in western Kansas | agmanager.info → Farm Management Guides, non-irrigated crops |
| **TIGER counties** | County outlines | GEE `TIGER/2018/Counties` |

An irrigation mask is still missing: `UMT/Climate/IrrMapper_RF/v1_2` exists in GEE but does not cover Kansas. Until we find one, treat fields with no fallow in the CDL history as "probably irrigated" and exclude them from the dryland analysis.

## Keys and accounts to get first (5 minutes each, free)

1. **NASS QuickStats API key** — owner C.
2. **AMS Market News (MARS) API key** — owner C.
3. **Earth Engine project** (non-commercial) for everyone who runs GEE; set `EE_PROJECT` in your shell. Keep requests small: reduce over field polygons and export tables, not rasters.
4. **NASA Earthdata login** — only if we go beyond GEE (e.g. raw ECOSTRESS).
