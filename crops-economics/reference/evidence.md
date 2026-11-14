# Evidence register

Every agronomic or economic statement in Field Shift points to an ID here. Rotation cards list these IDs.
Owner: workstream C. Last update 2026-11-14.

Status: **read** = the team read the full report (research-evidence.md) · **data** = we downloaded and processed the data ourselves ·
**abstract** = confirmed from the published abstract only · **secondhand** = from a summary; do not quote numbers in the product until confirmed ·
**conflict** = two sources disagree; see note.

## Tribune field trials (K-State Southwest Research-Extension Center)

| ID | Claim | Source | Status |
| :--- | :--- | :--- | :--- |
| E01 | Wheat after fallow in 4-year rotations: mean 42 bu/acre, range 0–88, total failure 2002 and 2013 (1996–2020) | Schlegel, Holman, Burnett (2021), *Wheat and Grain Sorghum in Four-Year Rotations*, KAES Research Reports 7(7), doi:10.4148/2378-5977.8102, https://newprairiepress.org/kaesrr/vol7/iss7/3 | read |
| E02 | Sorghum after wheat: mean 88 bu/acre, range 0–147, total failure 2002 and 2012 | same as E01 | read |
| E03 | Recrop (second) wheat yields about 75% of the first wheat | same as E01 | read |
| E04 | Continuous wheat yields about 60% of wheat in the 4-year rotations | same as E01; the report abstract says "about 60% of the yield of wheat grown in a 4-year rotation following sorghum" | read |
| E05 | Second sorghum in WSSF yields about 65% of the first | same as E01 (also in the abstract) | read |
| E06 | Soil water at wheat planting about 9 in; about 3 in (40%) less for recrop wheat; about 1.5 in less for the second sorghum | same as E01 | read |
| E07 | 2008–2015: WSF the only rotation with a positive average net return (< $6/acre); WF −$18/acre; others below −$35/acre; insurance and government payments excluded. Rotation length had little effect on average wheat yield | Schlegel, Haag, O'Brien (2016), *Large-Scale Dryland Cropping Systems*, KAES Research Reports 2(7), doi:10.4148/2378-5977.1255 | read |
| E08 | Fallow storage efficiency: WF 28%; 3- and 4-year no-till rotations 15–19%; before sorghum or corn 17–22% | same as E07 | read |
| E09 | Available soil water at planting (8 ft): wheat 9.4 in after full fallow, 5.8–6.1 in in longer rotations; sorghum 4.4–5.5 in; corn 4.0–5.2 in | same as E07 | read |
| E10 | Crop water use: wheat 12.5–16.7 in; sorghum 11.7–12.8 in; corn 12.5–13.3 in | same as E07 | read |
| E11 | Sorghum yielded about twice as much as corn in the same rotation (corn about 65 bu/acre after wheat) | same as E07 | read |
| E12 | Sorghum and corn yield after wheat vs after a summer crop | research-evidence.md says "sorghum about twice as high after wheat; corn about 60% higher" (2016 report). The 2016 abstract says "corn and grain sorghum yields were about 60% greater when following wheat than when following corn or grain sorghum"; the 2021 edition (2008–2020) says about 50%. | **conflict**: check Table in the 2016 report before using. Our rotations do not need this number: WSSF uses E05, which is measured directly |
| E13 | WSF tillage, 20-year averages: wheat no-till 30 vs conventional 22 bu/acre; no-till and reduced till store about 1 in (wheat) to 1.5 in (sorghum) more soil water at planting | Schlegel, Burnett (2021), *Tillage Intensity in a Long-Term Wheat-Sorghum-Fallow Rotation*, KAES Research Reports 7(7) | read |
| E14 | Sorghum: long-term no-till 79 vs short-term no-till 50 bu/acre; conventional far lower (17 in 2020) | same as E13 | read |
| E15 | 11 of 20 wheat years depressed: mostly drought, also winterkill (2015) and disease (2017) | same as E13 | read |
| E16 | WSF gives more total grain than WF at Colby, Garden City and Tribune; the 11-month fallows of WSF store water more efficiently than the 14-month fallow of WF | Gwin, Norwood, Lamm (1984), *Research on Wheat-Sorghum-Fallow in Western Kansas* | read |

## Yield functions and crop parameters

| ID | Claim | Source | Status |
| :--- | :--- | :--- | :--- |
| E17 | Yield vs seasonal ET: threshold / slope / long-term slope / max ET — wheat 10.0 in, 6.0 bu/acre/in, 4.6, 24 in; sorghum 6.9, 12.2, 9.4, 21; corn 10.9, 16.9, 13.3, 25; sunflower 5.4 in, 218 lb/acre/in, 150, 22 | Stone, Schlegel, Khan, Klocke, Aiken (2006), *Water Supply: Yield Relationships Developed for Study of Water Management*, Table 1; `reference/kstate_yield_vs_et.csv` | read |
| E18 | Stress at flowering and early grain fill costs more yield than seasonal totals suggest | same as E17 | read |
| E23 | Crop coefficients Kc ini / mid / end | Allen, Pereira, Raes, Smith (1998), FAO Irrigation and Drainage Paper 56, Table 12, https://www.fao.org/4/x0490e/x0490e0b.htm | data (read from the table) |
| E24 | Lengths of crop development stages | FAO-56 Table 11 (same page) | data |
| E25 | Maximum effective rooting depth and depletion fraction p | FAO-56 Table 22, https://www.fao.org/4/x0490e/x0490e0e.htm | data |
| E29 | Standard bushel weights: wheat 60 lb, corn and grain sorghum 56 lb, field pea 60 lb, proso millet 50 lb | USDA standard weights per bushel | secondhand for pea and millet (not used in the engine: those crops are not modelled) |

## Fallow replacement (Garden City)

| ID | Claim | Source | Status |
| :--- | :--- | :--- | :--- |
| E19 | No significant difference in soil organic carbon between cover crops and fallow (2018–2019); larger, more stable aggregates with cover crops in 2018; haying did not reduce the benefit; cover crops use water and can cut the next yield in dry years | Simon, Obour, Holman et al. (2020), *Long-Term Cover Crop Management Effects on Soil Health in Semiarid Dryland Cropping Systems*, KAES Research Reports 6(5) | read |
| E20 | 2013–2020, WSF near Garden City: spring fallow-replacement crops had no significant effect on wheat or sorghum yield; spring triticale forage gave the highest net return (forage productivity, low seed cost); fallow replacement left less soil water at planting | Holman, Obour, Assefa (2021), Crop Science, doi:10.1002/csc2.20670 | **abstract**. The numbers "wheat yield losses 0–34% in wet and 40–70% in dry years after cover crops" and "125 kg/ha biomass ≈ 1 mm water ≈ 5.5 kg/ha wheat" come from earlier conference abstracts: still **secondhand**, not used in the product |

## Second site and aquifer

| ID | Claim | Source | Status |
| :--- | :--- | :--- | :--- |
| E21 | Wheat yield +141 kg/ha per extra cm of available soil water at planting; 218 mm at planting after a 12–14 month no-till fallow (Akron, Colorado) | Nielsen and Vigil (USDA-ARS Akron) | **secondhand**: original paper not retrieved. Use only as a cross-check, never on a card |
| E22 | High Plains aquifer in Greeley, Wichita, Scott and northern Finney counties: original saturated thickness often under 100 ft; parts of the Ogallala region under 40% of the original thickness; western Kansas levels fell almost 1 ft in 2024 | Kansas Geological Survey, Public Information Circular 18 and Technical Series 25 | **secondhand**: story only; take exact figures from KGS before quoting |

## Economics

| ID | Claim | Source | Status |
| :--- | :--- | :--- | :--- |
| E26 | Cost per acre by crop and rotation, southwest / western Kansas dryland, budget years 2016–2027 (wheat W-F, wheat W-S/C-F, sorghum W-S-F, corn W-C-F, oil sunflower W-SF-F) | K-State AgManager farm management guides, non-irrigated crops, https://www.agmanager.info/farm-budgets (historical projections 2016–2026 and 2027 guides); parsed by `scripts/parse_agmanager_budgets.py` | data |
| E27 | Kansas marketing-year prices received; county and district yields; crop progress | USDA NASS QuickStats, https://quickstats.nass.usda.gov | data (after `fetch_nass.py` is run with a key) |
| E28 | Consumer price index for inflation adjustment (2025 dollars) | BLS CPI-U all items, seasonally adjusted, via FRED series CPIAUCSL; October 2025 not published (federal shutdown), interpolated | data |
| E30 | K-State budgets charge fallow weed control to the following crop and, since 2018, the fallow year's land rent too (2.0 acre-years for W-F wheat, 1.5 for each crop of a 3-year rotation) | AgManager budget PDFs, cash rent line "All crops_SW_Dry … acre … 2.00" | data |
| E32 | NASS non-irrigated county yields vs Tribune trial yields, same years: wheat after fallow — county / trial ratio of means 0.85 (Greeley, n = 14), 0.93 (West Central district, n = 20), 0.93 (mean of 7 counties, n = 19); median yearly ratio 0.77–0.88; correlation r 0.80–0.94. Sorghum after wheat — ratio of means 0.72 (Greeley, n = 7), 0.85 (district, n = 12), 0.81 (counties, n = 12); median yearly ratio 0.69–0.85; r 0.69–0.88 | `scripts/compare_county_vs_trial.py` → `reference/county_vs_trial.csv` (NASS E27 vs E01, E02) | data |
| E31 | Crop insurance premiums in the budgets: about $8–34/acre depending on crop and year | AgManager budgets (E26) | data. Excluded from our costs, like indemnities: see README |

## Answers to the open questions in research-evidence.md

1. **Costs per acre for each crop and for fallow** — done: `reference/costs.csv`, budget years 2016–2027, nominal and 2025 dollars (E26, E30). Fallow has no separate K-State budget: its operations sit in the next crop's budget, its land rent is a separate row.
2. **Planting and harvest windows** — provisional values in `crops.csv` (marked ASSUMPTION). `derive_crop_calendar.py` replaces them with NASS Kansas crop-progress medians once `fetch_nass.py` has run. Workstream B should check them against field NDVI.
3. **Published flex-fallow threshold** — not found. The WS-forage rotation keeps `threshold_mm: null` and asks D to show a sensitivity range instead of inventing a value.
4. **County vs trial yields** — answered (E32). Farm (county) yields are about **85–93% of the trial yields for wheat** and **72–85% for sorghum** in the same years, and they rise and fall with the trial from year to year (r 0.80–0.94 for wheat, 0.69–0.88 for sorghum). So an engine validated on Tribune reproduces the *pattern* of farm yields; for the *level*, multiply by a county factor (calibration_targets T19–T20). Caveats: NASS county estimates in these counties stop after 2005–2016 (withheld or discontinued), so the overlap is 7–20 years; county yields mix all rotations and management levels, the trial values are wheat after fallow and sorghum after wheat only.
5. **Crop insurance** — one sentence for the cards: *"Results exclude crop insurance: premiums (about $8–34/acre in the K-State budgets) and payouts in failed years such as 2002, 2012 and 2013 would narrow the losses in bad years but not change which rotation stores more water."*
