# Engine across 46 western Kansas counties

Written by `python -m engine.counties`. One point per county (centroid weather from A, soil from B, cost region from C), replayed 1996 onward. County results are indicative; the field results are the product.

## 1. Yield level: the model needed a correction outside Tribune

Modelled yields at farm level (Tribune trial-to-farm factors) against USDA NASS non-irrigated county yields, same years. Ratio > 1 means the model is too high.

| Longitude | Counties | Wheat ratio | Sorghum ratio | Corn ratio | Median year-to-year r² (wheat / sorghum / corn) |
| :--- | ---: | ---: | ---: | ---: | :--- |
| 102-101 W | 14 | 1.16 | 1.45 | 1.13 | 0.47 / 0.61 / 0.64 |
| 101-100 W | 10 | 1.21 | 1.36 | 1.47 | 0.54 / 0.71 / 0.74 |
| 100-99 W | 15 | 1.38 | 1.46 | 1.79 | 0.25 / 0.59 / 0.56 |
| 99-98.3 W | 7 | 1.38 | 1.51 | 2.04 | 0.09 / 0.61 / 0.53 |

The year-to-year pattern transfers reasonably well, least so for wheat in the east, but the level does not: the yield-vs-ET relation calibrated at Tribune turns the extra rain of the east into far more grain than farms there harvest (dryland corn about 130 bu/acre modelled at Hays against about 70 in the county). Each county and crop therefore gets one factor (`engine/county_yield_factors.json`): the mean NASS dryland yield divided by the mean modelled yield over the same years. The model keeps the year-to-year variation and the water carried between crops; the county's own farms set the average.

NASS stopped publishing dryland county yields around 2007 (sorghum) and 2016 (wheat). For wheat and sorghum the series is extended to 2025 with the all-practices yield times the county's own dryland share (stable within a county: about 3% for wheat, 9% for sorghum). Corn is not extended because its all-practices yield is mostly irrigated corn.

Known bias: the county sorghum average includes sorghum after sorghum and continuous sorghum, while the county wheat average is mostly wheat after fallow in the west. Sorghum's factor is therefore likely too low relative to wheat's, which works against wheat-sorghum-fallow.

## 2. Best rotation along the transect

| Longitude | Counties | Mean gain of WSF over WF, USD/acre/yr | Model's best: WF / WSF / WCF / other |
| :--- | ---: | ---: | :--- |
| 102-101 W | 14 | -17 | 12 / 1 / 1 / 0 |
| 101-100 W | 10 | -7 | 6 / 2 / 2 / 0 |
| 100-99 W | 15 | +5 | 4 / 10 / 1 / 0 |
| 99-98.3 W | 7 | +12 | 2 / 5 / 0 / 0 |

The gain from replacing fallow with sorghum rises from west to east (correlation with longitude 0.72). All numbers include land rent; `mean_before_land_rent` in `results/counties.json` adds it back.

## 3. Independent check: what farmers actually do

Farmers' rotations come from the crop sequence 2018-2025 of 31,660 fields (workstream B), so they were not used to build the model.

- **Corn or sorghum after wheat:** the model's preference follows farmers' choice, Spearman ρ = 0.53 over 38 counties. Corn is favoured in the cooler north-west, sorghum in the south and centre, as on the map.
- **Sorghum or fallow:** weak, ρ = 0.24 over 32 counties. Strict wheat-fallow is rare everywhere (about 4% of field area), so farmers' share hardly varies; the model prefers wheat-fallow west of 101° W, where most farmers have already moved to three-year rotations. Reasons outside the model: crop insurance and government payments, spreading work and risk, weed control, and the sorghum bias above.
- **Leaving fallow since 2008: the model disagrees with farmers.** Rank correlation between the model's gain from replacing fallow and the drop in fallow share 2008 → latest: ρ = -0.62; with the share of fields that moved from wheat-fallow to a three-year rotation: ρ = -0.62 (46 counties). Farmers left fallow mostly in the dry west, where the model says fallow still pays best; the east had little fallow to leave. Where the model sees a gain, fallow is lower today (17.5% against 22% of cropland), but that is explained by rainfall alone. Likely reasons the model misses: better water storage under modern no-till, the rise of sorghum yields since 2008 (one constant factor averages old and new years), insurance and payments, and the sorghum bias above.
- **Most common rotation of the three = model's best:** 15 of 39 counties (always guessing WSF: 25). By longitude: 102-101 W 3/14, 101-100 W 3/10, 100-99 W 8/14, 99-98.3 W 1/1.

Reading: the model agrees with farmers on where corn and where sorghum fits, and on WSF around Hays. It does not explain why farmers in the far west have been leaving fallow: there it is more pessimistic about sorghum than farmers are. Show the west with that caution; it is also an honest example of where local knowledge beats the model.

## 4. Inputs and assumptions

- Soil: SSURGO at the centroid; where below 200 mm (the 2 km square missed the cropland) 280 mm is used (9 counties).
- Costs: K-State budgets of the county's region (`county_budget_regions.csv`; north-central and south-central budgets are proxies without fallow, C's A8).
- Sunflower (WSfF) is replayed but never named best: optional rotation, yield function not validated.
- Factors with fewer than 5 years of county data borrow the median of the cost region: Barber (sunflower), Barton (sunflower), Clark (corn, sunflower), Comanche (sunflower), Edwards (sunflower), Ford (sunflower), Gove (sunflower), Graham (sunflower), Gray (sunflower), Hamilton (sunflower), Hodgeman (sunflower), Kearny (sunflower), Kiowa (sunflower), Lane (sunflower), Meade (sunflower), Norton (sunflower), Pawnee (sunflower), Pratt (sunflower), Rush (sunflower), Russell (sunflower), Seward (sunflower), Sheridan (sunflower), Stafford (sunflower), Trego (sunflower).
