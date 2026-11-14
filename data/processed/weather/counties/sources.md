# Weather files: sources

Generated 2026-11-14 by `pipelines/weather/run.py`. One CSV per field, daily, no gaps.

County files: one point per county (`lon`, `lat` in counties.geojson, the county centroid), not a county mean. Treat them as indicative, as docs/transect.md says for all county results.

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

### ks007 (lon -98.6847, lat 37.2287; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks009 (lon -98.7565, lat 38.4789; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks023 (lon -101.7311, lat 39.7858; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks025 (lon -99.8203, lat 37.2354; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks033 (lon -99.2719, lat 37.1912; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks039 (lon -100.4599, lat 39.7846; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks047 (lon -99.3121, lat 37.8876; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks051 (lon -99.3172, lat 38.9146; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks055 (lon -100.7373, lat 38.0443; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks057 (lon -99.8879, lat 37.6916; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks063 (lon -100.4829, lat 38.916; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks065 (lon -99.8833, lat 39.3496; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks067 (lon -101.308, lat 37.5621; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks069 (lon -100.4378, lat 37.738; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks071 (lon -101.806, lat 38.4804; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks075 (lon -101.7912, lat 37.9989; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks081 (lon -100.8712, lat 37.5622; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks083 (lon -99.8979, lat 38.0875; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks093 (lon -101.3198, lat 38.0; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks097 (lon -99.286, lat 37.5582; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks101 (lon -100.4664, lat 38.4812; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks109 (lon -101.1484, lat 38.9173; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks119 (lon -100.3662, lat 37.2381; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks129 (lon -101.7992, lat 37.1913; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks135 (lon -99.9162, lat 38.4794; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks137 (lon -99.9035, lat 39.7843; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks141 (lon -98.768, lat 39.3502; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks145 (lon -99.2366, lat 38.1813; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks147 (lon -99.347, lat 39.7845; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks151 (lon -98.7396, lat 37.6477; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks153 (lon -101.0757, lat 39.7852; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks163 (lon -99.3251, lat 39.3501; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks165 (lon -99.3092, lat 38.5231; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks167 (lon -98.7624, lat 38.9147; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks171 (lon -100.9069, lat 38.482; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks175 (lon -100.8513, lat 37.1932; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks179 (lon -100.4418, lat 39.3502; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks181 (lon -101.72, lat 39.3514; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks183 (lon -98.7855, lat 39.785; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks185 (lon -98.7175, lat 38.0309; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks187 (lon -101.7842, lat 37.563; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks189 (lon -101.312, lat 37.1922; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks193 (lon -101.0555, lat 39.3509; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks195 (lon -99.8727, lat 38.9142; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks199 (lon -101.7636, lat 38.9166; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |

### ks203 (lon -101.3474, lat 38.4819; 1994-01-01 to 2026-11-11)

| Column | Source | Days |
| :--- | :--- | ---: |
| `precip_mm` | gridMET | 12003 |
| `tmax_c` | gridMET | 12003 |
| `tmin_c` | gridMET | 12003 |
| `eto_mm` | gridMET | 12003 |
| `srad_mj_m2` | NASA POWER | 12000 |
| `srad_mj_m2` | gridMET | 3 |
| `wind_m_s` | NASA POWER | 12003 |
