# Evidence register

Every crop, rotation, price and cost number in Field Shift points to an ID in this file.
Rotation cards (`rotations.json`, field `evidence`) list these IDs.

**Status**

| Status | Meaning |
| :--- | :--- |
| data | Downloaded from the source and processed by a script in `scripts/`. Reproducible with `run_all.py --refresh`. |
| read | Taken from a published report; the numbers were transcribed by the team (`docs/research-evidence.md`, `reference/kstate_*.csv`). |
| abstract | Only the published abstract was available. Used for direction, not for numbers. |
| secondhand | From a summary, not the original. Not used for any number in the tool. |
| assumption | Our choice where no source exists. Listed in `HANDOVER.md` (A1–A9). |

## Field trials at Tribune, Kansas (K-State Southwest Research-Extension Center)

Tribune is the validation site: the engine is calibrated and tested against these trials.

| ID | Finding | Source | Status |
| :--- | :--- | :--- | :--- |
| E01 | Wheat after fallow, 1996–2020: mean 42 bu/acre, range 0–88; total failure in 2002 and 2013 | Schlegel, Holman, Burnett (2021). *Wheat and Grain Sorghum in Four-Year Rotations.* KAES Research Reports 7(7). doi:10.4148/2378-5977.8102 | read |
| E02 | Sorghum after wheat: mean 88 bu/acre, range 0–147; total failure in 2002 and 2012 | as E01 | read |
| E03 | A second wheat crop in a row yields about 75% of the first | as E01 | read |
| E04 | Continuous wheat yields about 60% of wheat in the 4-year rotations | as E01 | read |
| E05 | A second sorghum crop in a row yields about 65% of the first | as E01 | read |
| E06 | Soil water at wheat planting about 9 in; about 3 in (40%) less before a second wheat; about 1.5 in less before a second sorghum | as E01 | read |
| E07 | 2008–2015: wheat–sorghum–fallow was the only rotation with a positive average net return (under $6/acre); wheat–fallow −$18/acre; all others below −$35/acre (no insurance or government payments). Rotation length had little effect on average wheat yield | Schlegel, Haag, O'Brien (2016). *Large-Scale Dryland Cropping Systems.* KAES Research Reports 2(7). doi:10.4148/2378-5977.1255 | read |
| E08 | Fallow stores 28% of its precipitation in wheat–fallow; 15–19% in 3- and 4-year no-till rotations; 14–22% before sorghum or corn | as E07 | read |
| E09 | Available soil water at planting (8 ft): wheat 9.4 in after a full fallow, 5.8–6.1 in in longer rotations; sorghum 4.4–5.5 in; corn 4.0–5.2 in | as E07 | read |
| E10 | Seasonal water use: wheat 12.5–16.7 in; sorghum 11.7–12.8 in; corn 12.5–13.3 in | as E07 | read |
| E11 | In the same rotation sorghum yielded about twice as much as corn (corn about 65 bu/acre after wheat) | as E07 | read |
| E12 | Sorghum and corn after wheat vs after a summer crop: the report abstract says "about 60% greater" for both; the 2021 edition (2008–2020) says about 50% | as E07 | sources disagree, so not used |
| E13 | Wheat–sorghum–fallow, 20-year averages: wheat 30 bu/acre no-till vs 22 conventional tillage; no-till stores about 1 in (wheat) to 1.5 in (sorghum) more water at planting | Schlegel, Burnett (2021). *Tillage Intensity in a Long-Term Wheat-Sorghum-Fallow Rotation.* KAES Research Reports 7(7) | read |
| E14 | Sorghum: long-term no-till 79 bu/acre vs short-term no-till 50; conventional tillage far lower (17 bu/acre in 2020) | as E13 | read |
| E15 | 11 of 20 wheat years were below normal: mostly drought, also winterkill (2015) and disease (2017) | as E13 | read |
| E16 | Wheat–sorghum–fallow gives more grain than wheat–fallow at Colby, Garden City and Tribune; its 11-month fallows store water more efficiently than the 14-month fallow of wheat–fallow | Gwin, Norwood, Lamm (1984). *Research on Wheat-Sorghum-Fallow in Western Kansas.* | read |

## Crop parameters

| ID | Finding | Source | Status |
| :--- | :--- | :--- | :--- |
| E17 | Yield vs seasonal water use. Wheat: no grain below 10.0 in of water use, then +6.0 bu/acre per extra inch (4.6 over the long term), no gain above 24 in. Sorghum: 6.9 in; +12.2 bu/acre per inch (9.4); 21 in. Corn: 10.9 in; +16.9 bu/acre per inch (13.3); 25 in. Sunflower: 5.4 in; +218 lb/acre per inch (150); 22 in | Stone, Schlegel, Khan, Klocke, Aiken (2006). *Water Supply: Yield Relationships Developed for Study of Water Management.* Table 1 | read |
| E18 | Water stress at flowering and early grain fill reduces yield more than seasonal totals suggest | as E17 | read |
| E23 | Crop coefficients Kc (initial, mid, end) | Allen, Pereira, Raes, Smith (1998). FAO Irrigation and Drainage Paper 56, Table 12. https://www.fao.org/4/x0490e/x0490e0b.htm | data |
| E24 | Lengths of crop development stages | FAO-56, Table 11 | data |
| E25 | How deep the roots reach and how far the soil can dry before the crop is stressed (rooting depth and depletion fraction p) | FAO-56, Table 22. https://www.fao.org/4/x0490e/x0490e0e.htm | data |
| E29 | Bushel weights: wheat 60 lb; corn and grain sorghum 56 lb | USDA standard bushel weights | data |

## Replacing fallow with a forage or cover crop (Garden City, Kansas)

| ID | Finding | Source | Status |
| :--- | :--- | :--- | :--- |
| E19 | Cover crops vs fallow: no difference in soil organic carbon (2018–2019); larger, more stable soil aggregates in 2018; haying did not remove the benefit; cover crops use water and can lower the next yield in dry years | Simon, Obour, Holman et al. (2020). *Long-Term Cover Crop Management Effects on Soil Health in Semiarid Dryland Cropping Systems.* KAES Research Reports 6(5) | read |
| E20 | 2013–2020: spring crops in place of fallow did not significantly change wheat or sorghum yield; spring triticale forage gave the highest net return; less soil water at the next planting | Holman, Obour, Assefa (2021). *Crop Science.* doi:10.1002/csc2.20670 | abstract |

## Context only

| ID | Finding | Source | Status |
| :--- | :--- | :--- | :--- |
| E21 | Wheat yield about +5.3 bu/acre per extra inch of soil water at planting (141 kg/ha per cm; Akron, Colorado) | Nielsen and Vigil, USDA-ARS Akron | secondhand |
| E22 | High Plains aquifer: thin original saturated thickness in Greeley, Wichita, Scott and northern Finney counties; large declines in western Kansas | Kansas Geological Survey, Public Information Circular 18; Technical Series 25 | secondhand |

## Prices, costs and yields for the study area (46 counties)

| ID | Finding | Source | Status |
| :--- | :--- | :--- | :--- |
| E26 | Cost per acre, dryland, budget years 2016–2027, four regions. Southwest and Northwest Kansas: wheat (W-F), wheat (W-S/C-F), sorghum (W-S-F), corn (W-C-F), sunflower (W-SF-F). North Central and South Central Kansas: wheat in rotation, continuous wheat, sorghum, corn, dryland sunflower. 209 budgets | K-State AgManager farm management guides, non-irrigated crops. https://www.agmanager.info/farm-budgets | data |
| E27 | Kansas marketing-year prices received (1990–2025); non-irrigated county and district yields for all Kansas counties (1990–2025); weekly crop progress (1995–2025) | USDA NASS QuickStats. https://quickstats.nass.usda.gov | data |
| E28 | Inflation adjustment to 2025 dollars; October 2025 was not published and is interpolated | BLS CPI-U, FRED series CPIAUCSL | data |
| E30 | K-State charges fallow weed control to the crop after the fallow, and charges the fallow year's rent with a varying number of acre-years (1.0, 1.5 or 2.0) | AgManager budget PDFs (E26) | data |
| E31 | Crop insurance premiums in the budgets: about $8–34/acre | AgManager budget PDFs (E26) | data |
| E32 | Farm yields vs Tribune trial yields, same years. Wheat after fallow: ratio of means 0.85 (Greeley County, 14 years), 0.93 (West Central district, 20 years), 0.96 (mean of West Central counties, 18 years); correlation 0.80–0.94. Sorghum after wheat: 0.72 (Greeley, 7 years), 0.85 (district, 12 years), 0.82 (counties, 12 years); correlation 0.69–0.88 | Our comparison of USDA NASS county yields (E27) with the Tribune trials (E01, E02) | data |
| E33 | K-State budget region of each county: 46 study counties = 19 SW, 12 NW, 6 NC, 9 SC | Our assignment of counties to K-State budget regions | our assumption |

## Answers to the open questions (docs/research-evidence.md, section 7)

1. **Cost per acre for each crop and for fallow:** `costs.csv` (E26). There is no K-State fallow budget: fallow operations are inside the next crop's budget, and fallow has its own row with one year of rent (E30). In central Kansas a fallow weed-control allowance is added (A8).
2. **Planting and harvest windows:** `crops.csv`, from NASS crop progress for Kansas (E27). Winter wheat: planted around day 278 (5 Oct), harvested around day 178 (27 Jun). Sorghum planted around day 158, corn 124, sunflower 163.
3. **Published soil-water threshold for flexible fallow:** none found. The WS-forage rotation keeps `threshold_mm: null`; the engine shows a range instead of one value.
4. **County vs trial yields:** farm yields are about 0.85–0.96 of trial yields for wheat and 0.72–0.85 for sorghum, and follow the same good and bad years (E32). Calibrate on Tribune, scale to farm level with `calibration_targets.csv` T19–T20.
5. **Crop insurance, one sentence for the cards:** "Results leave out crop insurance: premiums (about $8–34/acre a year) would add a cost every year, and payouts in failed years such as 2002, 2012 and 2013 would reduce losses in those years."
