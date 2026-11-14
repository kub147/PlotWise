# Weather files: sources

Generated 2026-11-14 by `pipelines/weather/run.py`. One CSV per field, daily, no gaps.

| Column | Primary source | Fallback when the primary has no value |
| :--- | :--- | :--- |
| `precip_mm` | gridMET `pr` (mm/day) | NASA POWER `PRECTOTCORR` |
| `tmax_c` | gridMET `tmmx` (K − 273.15) | NASA POWER `T2M_MAX` |
| `tmin_c` | gridMET `tmmn` (K − 273.15) | NASA POWER `T2M_MIN` |
| `eto_mm` | gridMET `eto` (grass reference ET, ASCE Penman-Monteith, mm/day) | Hargreaves (FAO-56 eq. 52) from the temperature columns |
| `srad_mj_m2` | NASA POWER `ALLSKY_SFC_SW_DWN` (MJ/m²/day) | gridMET `srad` × 0.0864 (W/m² → MJ/m²/day) |
| `wind_m_s` | NASA POWER `WS2M` (m/s at 2 m) | gridMET `vs` × 0.748 (10 m → 2 m, FAO-56 eq. 47) |

- gridMET: Earth Engine `IDAHO_EPSCOR/GRIDMET`, 4 km, pixel under the field centroid (`lon`, `lat` in fields.geojson). A gridMET day runs to 06:00 UTC of the following day.
- NASA POWER: `https://power.larc.nasa.gov/api/temporal/daily/point`, community AG, about 0.5° × 0.625°. Its recent days are often missing for radiation and wind; those days use the gridMET fallback.
- The series ends on the last day gridMET has published.
- Last resort (should be 0 days): mean of the nearest valid days, 0 for precipitation; marked ASSUMPTION below.

## Days per source

### ks071-001 (lon -101.75721, lat 38.49117; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks071-002 (lon -101.7751, lat 38.41306; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks071-003 (lon -101.79468, lat 38.43289; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks071-004 (lon -101.67359, lat 38.47657; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks071-005 (lon -101.81636, lat 38.47114; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks193-001 (lon -101.02282, lat 39.43511; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks193-002 (lon -101.01258, lat 39.43411; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks193-003 (lon -101.0793, lat 39.22393; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks051-001 (lon -99.2577, lat 38.86002; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks051-002 (lon -99.07284, lat 38.81649; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks051-003 (lon -99.22152, lat 38.79478; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |
