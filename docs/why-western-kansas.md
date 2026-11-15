# Why western Kansas

PlotWise answers one question for a dryland farmer:

> "My field is in wheat–fallow (or wheat–sorghum–fallow). Should I change the rotation, to what, and what do I risk in a dry year?"

This note records why the demo is set in Tribune, Greeley County, Kansas, and later extended east to Colby and Hays
([transect.md](transect.md)). The engine itself is described in [`engine/README.md`](../engine/README.md), its
validation in [engine-validation.md](engine-validation.md), and the datasets in [data-sources.md](data-sources.md).

## The evidence

We checked the choice with data instead of assuming it. All numbers below were computed on 2026-11-14 with the scripts in `scripts/`.

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

- K-State's Southwest Research-Extension Center at Tribune has run dryland rotation trials for decades and publishes **year-by-year yields per rotation phase** (1996–2020), soil water at planting, crop water use and economics. That gives a way to **validate** the model against measured outcomes.
- Every US dataset on the challenge resource list works here (CDL, SSURGO, PRISM, NAIP, NASS, AMS, OpenET).

**A caution we found and show in the app**: NASA POWER precipitation at Tribune has a drying trend (−45 mm/decade, p = 0.03) that gridMET does not show (+3 mm/decade, p = 0.89). We therefore do **not** claim that rainfall is declining. We use POWER for temperature, radiation and GDD, and a station-anchored product for precipitation. Cross-checking products is part of the method.

## Alternatives considered

| Option | Why not the main demo |
| :--- | :--- |
| Garden City, Kansas (first draft) | Largely irrigated; Tribune has the dryland trials and CDL confirms wheat–fallow there |
| Nevada, irrigated alfalfa (the challenge page photo shows a Nevada alfalfa farmer) | A natural second showcase: OpenET covers it and the priorities listed in the challenge (forage value, nitrogen fixing, water use) fit alfalfa. We found no comparable open, year-by-year rotation trial data to validate against |
| Poland | No CDL equivalent, no open field-scale soil survey, no open rotation trial data |

The engine is region-agnostic: weather, soil and a crop table go in. The demo region is where we can prove it works.

## Limits we state openly

- Reanalysis and satellite products are coarse (SMAP 9 km, POWER about 50 km, GRACE about 300 km); field-scale signal comes from soil data, CDL and NDVI.
- CDL is a classification; fallow and wheat can be confused.
- Trial plots are well managed; farm yields are usually lower. We calibrate the level with county statistics.
- Economics exclude crop insurance and government payments unless stated.
- No pest, disease, hail or market-access modelling: listed on each card as "check locally".
