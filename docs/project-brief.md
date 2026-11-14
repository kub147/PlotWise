# Field Shift — project brief

NASA Space Apps 2026 · challenge "Field Shift: Adapting Farms with NASA Data" · working draft, 2026-11-14.
Submission closes **Sunday 15 November, 23:59 local time**.

Read with: [data-sources.md](data-sources.md) · [research-evidence.md](research-evidence.md) · [work-plan.md](work-plan.md)

## 1. Goal in one sentence

Let a dryland farmer **replay the last 30 years on their own field under different crop rotations** and see, for each one, the yield, the profit, the risk of a failed year and what happens to the soil — with every number traced to NASA data and to published field trials.

## 2. The question we answer

> "My field is in wheat–fallow (or wheat–sorghum–fallow). Should I change the rotation, to what, and what do I risk in a dry year?"

The challenge asks for exactly this: compare at least three rotation strategies including the existing one, and for each explain why it was suggested, what evidence supports it, what it may offer, where the gaps are and what needs local review. The tool supports the farmer's judgment; it does not replace it.

## 3. What we build

A web dashboard with four views. The first three are the minimum; the fourth is the differentiator.

| View | What the farmer sees | Data behind it |
| :--- | :--- | :--- |
| **1. My field** | Field outline, the rotation actually practised in recent years, soil, slope, how often the soil is bare | Crop Sequence Boundaries + CDL, SSURGO, SRTM, MODIS / Sentinel-2 NDVI |
| **2. What has changed** | 30-year trends with an honest "reliable / not reliable" label; regional water storage; how the county's rotations are shifting | NASA POWER, gridMET / PRISM, GPM IMERG, GRACE, CDL |
| **3. Rotation replay** | Each rotation simulated through every year since 1995: yield per crop, net return per acre, worst year, share of years with a loss, days of bare soil, water productivity. Farmer sets priorities with sliders; ranking shows whether the winner is robust or depends on the weights | Soil-water balance engine + K-State yield functions + prices and costs |
| **4. This season** | "Soil water today is in the Nth percentile for this date. If you plant sorghum now, the expected yield range is A–B; if you fallow, next year's wheat gains C." | SMAP root-zone soil moisture + the same engine run forward over all historical weather years |

Each rotation gets a card: **why it is suggested · evidence · benefits · information gaps · what to check locally**. Card text can be drafted by an LLM, but only from numbers produced by the engine.

## 4. Why western Kansas (Tribune, Greeley County)

We checked the choice with data instead of assuming it. All numbers below were computed on 2026-11-14; scripts are in `scripts/`.

**The problem is real and current**

| Evidence | Value | Source |
| :--- | :--- | :--- |
| Water is the limiting factor | Precipitation covers about 37% of reference ET (Ames, Iowa: 85%; Poznań, Poland: 80%) | NASA POWER 1995–2024, `power_indicators.py` |
| Rain varies enormously | April–September rain 161 mm (2012) to 552 mm (2016); CV 28% | gridMET 1995–2020 |
| Yields swing from zero to record | Wheat after fallow: mean 42 bu/acre, CV 58%, total failure in 2002 and 2013. Sorghum: mean 88 bu/acre, CV 42%, total failure in 2002 and 2012 | K-State Tribune trials 1996–2020 |
| The season is getting warmer | Growing degree days +78 per decade (Mann-Kendall p < 0.01) | NASA POWER |
| Regional water storage is falling | −0.8 cm/year of water equivalent, 2002–2024 (about −18 cm in total) | GRACE / GRACE-FO mascons |
| Margins are thin | In 2008–2015 only wheat–sorghum–fallow had a positive average net return (< $6/acre); wheat–fallow lost $18/acre | K-State, Schlegel et al. 2016 |

**Farmers there are in the middle of exactly this decision**

| Evidence | Value | Source |
| :--- | :--- | :--- |
| Fallow is still a third of cropland | Fallow share of dryland cropland in Greeley County: 42% (2008) → 29% (2024) | CDL, `cdl_county_history.py` |
| Rotations are intensifying | Sorghum + corn acreage relative to wheat: 0.52 (2008) → 1.26 (2024) | CDL |
| Wheat still depends on fallow | 82% of wheat is planted after fallow; 69% of cropland is fallowed about one year in three, 18% one year in two | CDL pixel sequences 2010–2024, n ≈ 9,800, `cdl_rotation_sequences.py` |
| After wheat, farmers split | Next year: 40% fallow, 28% sorghum, 17% corn, 12% wheat again | same |

**It is the best-documented place for this question**

- K-State's Southwest Research-Extension Center at Tribune has run dryland rotation trials for decades and publishes **year-by-year yields per rotation phase** (1996–2020), soil water at planting, crop water use and economics. That gives us something almost no other team will have: a way to **validate** the model against measured outcomes.
- Every US dataset on the challenge resource list works here (CDL, SSURGO, PRISM, NAIP, NASS, AMS, OpenET).

**A caution we found and will show**: NASA POWER precipitation at Tribune has a drying trend (−45 mm/decade, p = 0.03) that gridMET does not show (+3 mm/decade, p = 0.89). We therefore do **not** claim that rainfall is declining. We use POWER for temperature, radiation and GDD, and a station-anchored product for precipitation. Cross-checking products is part of the method.

### Alternatives considered

| Option | Why not the main demo |
| :--- | :--- |
| Garden City, Kansas (first draft) | Largely irrigated; Tribune has the dryland trials and CDL confirms wheat–fallow there |
| Nevada, irrigated alfalfa (the challenge page photo shows a Nevada alfalfa farmer) | A natural second showcase: OpenET covers it and the priorities listed in the challenge (forage value, nitrogen fixing, water use) fit alfalfa. We found no comparable open, year-by-year rotation trial data to validate against. **Stretch goal** if time allows |
| Poland | No CDL equivalent, no open field-scale soil survey, no open rotation trial data |

The engine is region-agnostic: weather, soil and a crop table go in. The demo region is where we can prove it works.

## 5. The engine

1. **Weather forcing** per field, daily since 1995: precipitation, temperature, reference ET.
2. **Daily soil-water balance** through the whole rotation, including fallow: storage capacity from SSURGO, crop coefficients from FAO-56, a water-stress coefficient, residue and tillage effects from K-State results.
3. **Yield** from seasonal water use with the K-State yield-vs-ET functions (threshold ET and slope per crop), adjusted by rotation effects measured at Tribune (e.g. second sorghum ≈ 65% of the first, recrop wheat ≈ 75%).
4. **Economics**: yield × price − cost, per acre and year. Prices from USDA (NASS prices received, AMS local bids), costs from K-State AgManager budgets.
5. **Soil indicators** per rotation: bare-soil days per year, share of time with residue cover, precipitation storage efficiency, water productivity.
6. **Scoring** with farmer weights, plus a sensitivity run over many weight sets to say whether the ranking is stable.

Every phase of every rotation is started in every year, so each rotation gets a full distribution of outcomes rather than one lucky or unlucky sequence.

### Validation ladder

| Level | Check | Status |
| :--- | :--- | :--- |
| 0 | Raw precipitation sums vs Tribune yields | done: wheat R² 0.31, sorghum R² 0.61 |
| 1 | Uncalibrated soil-water bucket vs Tribune yields | done: **wheat R² 0.44, sorghum R² 0.63** (leave-one-out 0.29 / 0.56); modelled soil water at sorghum planting 143 mm vs 135 mm measured — `water_balance_baseline.py` |
| 2 | Calibrated engine vs Tribune yields for all rotation phases | to do — this is the number to beat |
| 3 | Engine vs NASS county yields (Greeley and neighbours) | to do, needs a free QuickStats key |
| 4 | Modelled ET vs OpenET and MOD16 on real fields | stretch |
| 5 | Modelled soil water vs SMAP anomalies | stretch |

Wheat is harder than sorghum because winterkill (2015), disease (2017) and hail are not water effects. We say so in the tool.

### Where AI/ML is used

- Trend tests (Mann-Kendall) and year typing (dry / normal / wet).
- A second, data-driven yield model (gradient boosting on county-year yields with weather, SMAP and NDVI features) as an independent cross-check of the process model. Where the two disagree, the card shows wider uncertainty. **Stretch.**
- NDVI time-series rules to find bare-soil periods and confirm the crop calendar.
- An LLM turns engine output into plain-language cards.

## 6. Prices: scenarios, not forecasts

Forecasting grain prices is not something we can do credibly in a weekend, and a farmer would not trust it. Instead:

- **Historical replay**: each simulated year uses that year's actual price (inflation-adjusted), so the result reflects how weather and prices really moved together.
- **Scenario slider**: today's price, 5-year average, low and high percentile.
- **Break-even**: for each rotation, the price and the yield at which it stops paying.

This gives a distribution — "profitable in 19 of 30 years, worst year −$85/acre" — which is more useful and more honest than one predicted number.

## 7. What makes it competitive

| Award | Our angle |
| :--- | :--- |
| Best Use of Science | Model validated against 24 years of independent field-trial yields; published coefficients; trends reported with significance; a product disagreement found and disclosed |
| Best Use of Data | About a dozen datasets fused at field scale, each with a defined role (see data-sources.md); the current rotation read from satellite-derived crop history instead of typed in |
| Galactic / Local Impact | Dryland wheat–fallow covers large areas of the High Plains above a declining aquifer; the same engine applies to any water-limited region |
| Best Use of Storytelling | One farmer, one field, one question; "replay the last 30 years" is easy to grasp |

This is a strong position, not a guarantee. Judges also weigh presentation heavily, so the demo and the story get protected time.

## 8. Scope

| Tier | Content |
| :--- | :--- |
| **Must (by Saturday night)** | One real field end to end: profile, 4 rotations replayed (WF, WSF, WCF, WSSF), yields and net returns, ranking with sliders, Tribune validation plot |
| **Should (Sunday morning)** | 3–5 fields, bare-soil and soil indicators, weight sensitivity, cards with evidence and gaps, "This season" view with SMAP |
| **Stretch** | Fallow replacement with forage / cover crop, ML cross-check, OpenET validation, Nevada alfalfa field, scenario slider for warming |

## 9. Limits we state openly

- Reanalysis and satellite products are coarse (SMAP 9 km, POWER about 50 km, GRACE about 300 km); field-scale signal comes from soil data, CDL and NDVI.
- CDL is a classification; fallow and wheat can be confused.
- Trial plots are well managed; farm yields are usually lower. We calibrate the level with county statistics.
- Economics exclude crop insurance and government payments unless stated.
- No pest, disease, hail or market-access modelling: listed on each card as "check locally".
