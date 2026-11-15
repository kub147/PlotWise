# Research evidence

What published field research tells us about dryland rotations in western Kansas, and how each finding is used.
None of us is an agronomist, so every agronomic statement in the product must point to a row in this file.

Status: **read** = we read the full report · **secondhand** = from an abstract or search summary; confirm before quoting it in the product.

## 1. Long-term rotation trials at Tribune, Kansas (K-State Southwest Research-Extension Center)

### 1.1 Four-year rotations, 1996–2020 — read
Schlegel, Holman, Burnett (2021), *Wheat and Grain Sorghum in Four-Year Rotations*, Kansas Agricultural Experiment Station Research Reports 7(7). Data transcribed to `reference/kstate_tribune_rotation_yields.csv`.

| Finding | Number | Use |
| :--- | :--- | :--- |
| Wheat after fallow, 24 years | mean 42 bu/acre; range 0–88; total failure in 2002 and 2013 | Validation target; shows the risk a farmer faces |
| Sorghum after wheat, 25 years | mean 88 bu/acre; range 0–147; total failure in 2002 and 2012 | Validation target |
| Second wheat crop in a row (recrop) | about 75% of the first | Rotation-effect multiplier |
| Continuous wheat | about 60% of wheat after fallow | Rotation-effect multiplier |
| Second sorghum crop in a row | about 65% of the first | Rotation-effect multiplier |
| Soil water at wheat planting after fallow | about 9 in; about 3 in (40%) less for recrop wheat | Check of modelled soil water |
| Soil water at sorghum planting | about 1.5 in less for the second sorghum | Check of modelled soil water |

### 1.2 Large-scale cropping systems, 2008–2015 — read
Schlegel, Haag, O'Brien (2016), *Large-Scale Dryland Cropping Systems*, KAES Research Reports 2(7). Table in `reference/kstate_tribune_soil_water.csv`.

| Finding | Number | Use |
| :--- | :--- | :--- |
| Most profitable rotation | Wheat–sorghum–fallow: the only one with a positive average net return (< $6/acre). Wheat–fallow −$18/acre; all others below −$35/acre. Crop insurance and government payments excluded | Benchmark for our economics; shows how thin margins are |
| Wheat yield vs rotation length | Little effect on average; ranking changes from year to year | Do not assume longer rotations hurt wheat |
| Sorghum and corn after wheat vs after a summer crop | Sorghum about twice as high after wheat; corn about 60% higher | Rotation-effect multiplier |
| Sorghum vs corn in the same rotation | Sorghum about twice the corn yield (about 65 bu/acre after wheat) | Explains why dryland corn is risky here; card text |
| Fallow efficiency | Wheat–fallow stores 28% of fallow precipitation; 3- and 4-year no-till rotations 15–19%; before sorghum or corn 14–22% | Calibrates the fallow part of the water balance |
| Available soil water at planting (8 ft) | Wheat: 9.4 in after a full fallow vs 5.8–6.1 in in longer rotations; sorghum 4.4–5.5 in; corn 4.0–5.2 in | Check of modelled soil water |
| Crop water use | Wheat 12.5–16.7 in; sorghum 11.7–12.8 in; corn 12.5–13.3 in | Check of modelled ET |
| Weather in the study period | Precipitation 96% of normal (17.9 in); one year at 42% of normal | Context |

### 1.3 Tillage in wheat–sorghum–fallow, 1991–2020 — read
Schlegel, Burnett (2021), *Tillage Intensity in a Long-Term Wheat-Sorghum-Fallow Rotation*, KAES Research Reports 7(7).

| Finding | Number | Use |
| :--- | :--- | :--- |
| Wheat, 20-year average | No-till 30 bu/acre vs conventional tillage 22 | Tillage switch in the engine; advice card |
| Sorghum, 20-year average | Long-term no-till 79 bu/acre vs short-term no-till 50; conventional tillage far lower (17 in 2020) | Same; no-till matters more for sorghum than for wheat |
| Soil water at planting | No-till and reduced till about 1 in (wheat) to 1.5 in (sorghum) more than conventional | Tillage effect on stored water |
| Reasons for poor wheat years | 11 of 20 years depressed: mostly drought, also winterkill (2015) and disease (2017) | Explains why a water model cannot explain all wheat years |

### 1.4 Earlier work — read
Gwin, Norwood, Lamm (1984), *Research on Wheat-Sorghum-Fallow in Western Kansas*: wheat–sorghum–fallow gives more total grain than wheat–fallow at Colby, Garden City and Tribune; the 11-month fallows of WSF store water more efficiently than the 14-month fallow of wheat–fallow. Use: the shift away from wheat–fallow is a forty-year, well-studied trend.

## 2. Yield as a function of water use — read
Stone, Schlegel, Khan, Klocke, Aiken (2006), *Water Supply: Yield Relationships Developed for Study of Water Management*, Table 1. In `reference/kstate_yield_vs_et.csv`.

| Crop | Threshold ET (no grain below this) | Yield per extra inch of ET | Long-term slope (with hail, frost, pests) | Maximum ET |
| :--- | ---: | ---: | ---: | ---: |
| Winter wheat | 10.0 in | 6.0 bu/acre | 4.6 | 24 in |
| Grain sorghum | 6.9 in | 12.2 bu/acre | 9.4 | 21 in |
| Corn | 10.9 in | 16.9 bu/acre | 13.3 | 25 in |
| Sunflower | 5.4 in | 218 lb/acre | 150 | 22 in |
| Soybean | 7.8 in | 4.6 bu/acre | 3.8 | 24 in |

Use: the yield step of the engine. The thresholds also explain crop choice in plain words: sorghum starts making grain after about 7 in of water use, corn needs about 11 in. The same report notes that timing matters: stress at flowering and early grain fill costs more than the totals suggest, so a stress term for the critical stage is a sensible refinement.

## 3. Replacing fallow with a cover or forage crop (Garden City, Kansas)

### 3.1 Soil health — read
Simon, Obour, Holman et al. (2020), *Long-Term Cover Crop Management Effects on Soil Health in Semiarid Dryland Cropping Systems*, KAES Research Reports 6(5). Trial started 2007, wheat–sorghum–fallow with spring crops in place of fallow.

- No significant difference in soil organic carbon between cover crops and fallow in 2018–2019.
- Larger, more stable soil aggregates with cover crops than with fallow in 2018 (mean weight diameter 0.042–0.044 in vs 0.033 in); the difference was not significant after the 2019 wheat harvest.
- Haying the cover crop for forage did not reduce the soil benefit.
- Stated reason for slow adoption: cover crops use soil water and can cut the next cash crop's yield in dry years.

Use: honest card for the "replace fallow" strategy. The soil benefit is physical (aggregates, erosion), small and not guaranteed; harvesting it as forage keeps the benefit and adds income.

### 3.2 Yield and profit — secondhand
Holman et al. (Crop Science 2021, DOI 10.1002/csc2.20670, and earlier conference abstracts):

- Spring fallow replacement did not change average wheat or sorghum yield in the 2013–2020 study; spring triticale forage gave the highest net return.
- Earlier abstracts report wheat yield losses of 0–34% in wetter years and 40–70% in dry years after a cover crop, and that cover crops left standing were always less profitable than fallow, while forage crops can pay in wetter years.
- Rule of thumb from an abstract: each 125 kg/ha of cover-crop biomass costs about 1 mm of plant-available water; each mm is worth about 5.5 kg/ha of wheat.

Use: the "flexible fallow" strategy (plant a forage crop only when stored soil water is high). **Confirm the numbers in the full paper before they appear in the product.**

## 4. Soil water at planting and yield — secondhand
Nielsen and Vigil (USDA-ARS, Akron, Colorado): wheat yield rises by about 141 kg/ha for each extra cm of available soil water at planting; average 218 mm at planting after a 12–14 month fallow in no-till. Use: second site to check the engine; motivation for the "This season" view. **Confirm in the original papers.**

## 5. The aquifer — secondhand
Kansas Geological Survey: in Greeley, Wichita, Scott and northern Finney counties the original saturated thickness of the High Plains aquifer was often under 100 ft, so modest declines remove a large share of it; in parts of the Ogallala region less than 40% of the original thickness remains; western Kansas levels fell by almost 1 ft in 2024. Use: the story (irrigation is not the way out; dryland decisions matter). **Take exact figures from KGS Public Information Circular 18 and Technical Series 25 before quoting.**

## 6. Our own checks (computed 2026-11-14)

| Check | Result | Script |
| :--- | :--- | :--- |
| Do precipitation sums explain Tribune yields? | POWER: wheat R² 0.35, sorghum 0.25. gridMET: wheat 0.31, sorghum 0.61 | `water_balance_baseline.py` (gridMET part) |
| Does a simple soil-water bucket do better? | Seasonal ET alone: wheat R² 0.44 (leave-one-out 0.29), sorghum R² 0.63 (leave-one-out 0.56) | same |
| Is modelled stored water realistic? | 143 mm at sorghum planting vs 135 mm measured (2008–2015, 8 ft). Encouraging, but the model's starting water was a guess | same |
| Do precipitation products agree? | Annual totals POWER vs gridMET: r = 0.78; opposite trends | project brief, section 4 |

Reading: stored water plus in-season water explains most of the sorghum variation and under half of the wheat variation. The engine is worth building; wheat needs humility.

## 7. Open questions for the agronomy owner

1. Costs per acre for each crop and for fallow (herbicide passes) from the current AgManager western Kansas dryland budgets.
2. Planting and harvest windows for wheat, sorghum, corn, and for spring forage (triticale, oats, pea) in west-central Kansas.
3. Is there published guidance for "flex fallow" decisions based on soil water at planting (K-State or USDA-ARS)? If yes, use its threshold instead of inventing one.
4. County yields are well below trial yields. By how much? (NASS vs Tribune table.)
5. Crop insurance: one sentence on how it changes the picture, so the card can say what we left out.
