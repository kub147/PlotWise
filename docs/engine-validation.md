# Engine validation

Written by `python -m engine.validate`. Weather: gridMET pixel of the K-State Tribune station, 1994-2020.
Measured values: K-State Southwest Research-Extension Center, Tribune (sources in `reference/` and
`crops-economics/reference/evidence.md`). 1 bu/acre = 67.25 kg/ha (wheat) or 62.77 kg/ha (sorghum, corn).

## 1. Water

The five water parameters were chosen on this table alone (270 combinations, `engine/calibrate.py`); yields were not used. Measured: Schlegel, Haag, O'Brien 2016, 2008-2015.

| Crop | Rotation | Fallow efficiency % (model / measured) | Water at planting mm | Crop water use mm |
| :--- | :--- | ---: | ---: | ---: |
| winter_wheat | WF | 17 / 28 | 146 / 238 | 331 / 424 |
| winter_wheat | WSF | 21 / 19 | 129 / 155 | 315 / 321 |
| grain_sorghum | WSF | 18 / 14 | 111 / 135 | 306 / 318 |
| winter_wheat | WCF | 22 / 15 | 130 / 147 | 316 / 318 |
| corn | WCF | 17 / 16 | 97 / 133 | 346 / 337 |

Chosen: rain_eff 1.0, rain_min_mm 2.0, fallow_evap 0.2, wet_evap 0.3, fallow_dry_frac 0.3; soil capacity 320 mm (SSURGO, mean of the demo fields).

Reading: crop water use is within 1-4% of the measurements for the three-year rotations and 22% low for wheat-fallow. The model cannot reproduce the high efficiency of the 14-month fallow of wheat-fallow (28% measured): it stores too little there, so **wheat-fallow is treated slightly unfairly** and wheat after a long fallow starts with less water than measured. Measured water is for an 8 ft profile, the model for 5 ft.

## 2. Yields, year by year

`published` = K-State yield-vs-ET function exactly as published, driven by modelled ET, nothing fitted to yields. `calibrated` = the model the replay uses (`engine/params.json`). R² here is 1 − SSE/SST of the prediction itself (it can be negative when the level is wrong); r² is the squared correlation.

| Series | n | Measured mean | Published: mean, bias, r² | Calibrated: mean, RMSE, R², r² |
| :--- | ---: | ---: | :--- | :--- |
| Wheat after fallow (WSSF) | 24 | 42 | 22, -20, 0.29 | 41, 18, 0.45, 0.45 |
| Wheat after fallow (WWSF) | 24 | 40 | 22, -18, 0.27 | 41, 18, 0.45, 0.46 |
| Wheat after wheat (WWSF) | 24 | 30 | 14, -16, 0.27 | 30, 16, 0.52, 0.53 |
| Continuous wheat | 24 | 24 | 14, -10, 0.38 | 30, 13, 0.50, 0.60 |
| Sorghum after wheat (WSSF) | 25 | 88 | 78, -10, 0.56 | 89, 23, 0.61, 0.61 |
| Sorghum after sorghum (WSSF) | 25 | 57 | 62, +5, 0.52 | 58, 23, 0.51, 0.55 |
| Sorghum after two wheats (WWSF) | 25 | 89 | 78, -11, 0.52 | 88, 24, 0.57, 0.57 |

Units: bu/acre. The calibrated models were fitted only on the two reference positions (wheat after fallow, sorghum after wheat), mean of the two series each:

| Crop | Model (kg/ha) | n | R² | Leave-one-out R² |
| :--- | :--- | ---: | ---: | ---: |
| winter_wheat | 773 + 8.34 × ET mm -95.6 × days ≥ 34 °C (flowering to maturity) | 24 | 0.46 | 0.14 |
| grain_sorghum | -268 + 17.42 × ET mm | 25 | 0.60 | 0.52 |

What the numbers say:

- **Sorghum is modelled usefully.** Modelled ET alone explains 61% of the measured variation of sorghum after wheat (leave-one-out 54%).
- **Sorghum yields rose over time for reasons the water model does not see.** Adding the calendar year lifts R² to 75% (leave-one-out 67%); measured sorghum after wheat rose from 73 bu/acre (1996-2007) to 101 (2008-2020), wheat did not. The replay uses the 1996-2020 average level, so it probably understates today's sorghum.
- **Wheat is modelled weakly.** ET explains 38% of wheat after fallow (leave-one-out 10%); with heat days 45% (leave-one-out 13%). A single wheat year from the replay is a rough estimate. Known causes outside the model: winterkill (2015), stripe rust and wheat streak mosaic (2015-2017), hail, late freeze.
- **The published function has the right pattern but the wrong level at this trial**: it is 10-20 bu/acre too low for wheat. That is why wheat and sorghum are calibrated.
- Two independent measured series of the same crop in the same position agree with r² = 0.95, so the unexplained part is model and input error, not plot noise. K-State's own regressions on measured soil water and on-site rain reach r² = 0.83 (no-till, Stone and Schlegel 2006).

## 3. Crop failures

| Crop | Measured zero-yield years | Model's three lowest years (calibrated, bu/acre) |
| :--- | :--- | :--- |
| Wheat after fallow (WSSF) | 2002, 2013 | 2013 (5), 2002 (10), 2006 (18) |
| Sorghum after wheat (WSSF) | 2002, 2012 | 2002 (28), 2012 (38), 2000 (47) |

## 4. Rotation effects

Does the water balance alone explain why a second crop yields less? Ratio of mean yields, common years.

| Effect | Measured | From modelled water alone | Residual applied in the replay |
| :--- | ---: | ---: | ---: |
| grain_sorghum after grain_sorghum | 0.65 | 0.89 | 0.73 |
| winter_wheat after winter_wheat | 0.74 | 0.86 | 0.86 |

Less stored water explains about a third of the penalty of a second sorghum crop and about half of that of recrop wheat. The rest (weeds, disease, nitrogen, stand) is applied as a residual multiplier, so the water effect is not counted twice (`_double_counting_warning` in rotations.json).

## 5. Level against county yields

USDA NASS, Greeley County, non-irrigated, years with data since 1996. Model = replay yield at farm level (trial level × farm factor) with the station weather.

| Crop | Years | County mean bu/acre | Model mean bu/acre | Farm factor | r² |
| :--- | :--- | ---: | ---: | ---: | ---: |
| winter_wheat (WF) | 1996-2013, n=15 | 31 | 38 | 0.9 | 0.60 |
| grain_sorghum (WSF) | 1996-2005, n=7 | 61 | 80 | 0.8 | 0.57 |
| corn (WCF) | 1996-2018, n=16 | 61 | 66 | 0.8 | 0.43 |

Corn has no year-by-year trial series in `reference/`, so it uses the published K-State function without calibration, with the farm factor of sorghum (ASSUMPTION); the row above is its only check. Sunflower is not validated at all. County sorghum data end in 2005, before most of the yield rise at the trial, which explains part of the gap in that row.

K-State farm budgets give a second, more recent anchor: their planning yields for south-west Kansas dryland, 2016-2027 (`costs.csv`), against the replay's farm-level mean at the station, 1996-2020.

| Crop in rotation | K-State planning yield bu/acre | Replay mean bu/acre |
| :--- | ---: | ---: |
| Wheat in wheat-fallow | 42-54 | 40 |
| Wheat in three-year rotations | 39-54 | 37 |
| Sorghum in wheat-sorghum-fallow | 76-85 | 71 |
| Corn in wheat-corn-fallow | 66-82 | 59 |

The replay sits between the two anchors: above the county averages of 1996-2018, at or below what K-State budgets plan for today.

## 6. Economics benchmark

Average net return 2008-2015 at the station, 2025 USD per acre per year, against the K-State large-scale study (Schlegel, Haag, O'Brien 2016; nominal dollars of its time, its own prices and costs, trial yields). Expect the order and the sign of the differences to match, not the dollars.

| Rotation | Replay | K-State study |
| :--- | ---: | :--- |
| WSF | -15 | positive, below +6 |
| WF | -30 | -18 |
| WSSF | -29 | not in the study |
| WWSF | -42 | not in the study |
| WCF | -83 | below -35 |

The order matches (wheat-sorghum-fallow first, wheat-fallow second, wheat-corn-fallow last). For the two rotations with a published number the replay is 10-20 USD/acre lower; it uses farm-level instead of trial yields and today's real costs for every year.

## 7. Model variants tried

| Variant | r² wheat after fallow | r² sorghum after wheat | Note |
| :--- | ---: | ---: | :--- |
| `scripts/water_balance_baseline.py` (each crop period separate, starting water guessed) | 0.44 | 0.63 | regression fitted to yields; two series only |
| Single layer, continuous through the rotation, published yield function (this engine, water-calibrated) | 0.29 | 0.56 | seven series, nothing fitted to yields |
| Two layers (FAO-56 dual coefficient, surface evaporation layer, curve-number runoff, snow), water-calibrated | 0.39 | 0.49 | better fallow efficiency, worse water at planting; not kept |

Running the rotation continuously costs a little skill compared with the baseline, which restarted every crop from the same guessed soil water. We keep the continuous run because the replay needs the carry-over between crops: that is what makes rotations differ.

## 8. What this means for the product

- Trust the **comparison between rotations over many years** more than any single year.
- Sorghum results are firmer than wheat results; corn and sunflower are the least certain.
- Wheat-fallow is probably a little better than shown (section 1).
- Not modelled: hail, disease, winterkill, weeds, nitrogen, planting failures, crop insurance.
