# Workstream C hand-over

State on 2026-11-14. What is done, what is assumed, what still needs a person.

## For D (engine)

- Read `crops-economics/reference/README.md` first: year convention, real dollars, fallow costs, the multiplier warning.
- Use `crops-economics/scripts/lookup.py` for every price and cost (`Economics()`). No price or cost should be typed into the engine.
- Calibration and validation targets with evidence IDs: `crops-economics/reference/calibration_targets.csv` (storage efficiency, soil water at planting, crop water use, mean yields, 2008–2015 net returns).
- Benchmark to reproduce: Tribune 2008–2015 average net return WSF > 0 (< $6/acre), WF −$18/acre (T16, T17). The K-State study used its own prices and costs, so expect the sign and order to match, not the exact dollars.

## For E (app)

- Card text: `why`, `benefits`, `risks`, `gaps`, `check_locally`, `evidence` in `crops-economics/reference/rotations.json`.
- Insurance sentence for every card: evidence.md, answer 5.
- Rotation `status`: `optional` (WSfF), `stretch` (WS-forage), `validation_only` (WW, do not show as advice).

## ASSUMPTIONS (all listed here; each is also marked in its file)

| # | Where | Assumption | How to remove it |
| :--- | :--- | :--- | :--- |
| A1 | crops.csv `plant_doy`, stage lengths | Approximate west-central Kansas dates; FAO-56 generic stage lengths; winter-wheat stages built by hand around dormancy | Run `derive_crop_calendar.py` (NASS crop progress); B checks against NDVI |
| A2 | costs before 2016 | Equal to the mean real 2016–2026 cost of the same cost key | NASS prices-paid indices, if time |
| A3 | WSSF second sorghum, WWSF recrop wheat, WW | Same cost as the first crop in a 3-year rotation (no K-State budget) | None available in SW Kansas budgets |
| A4 | WS-forage | Triticale forage: no yield function, no cost budget, no soil-water threshold | Holman et al. 2021 full text; K-State cover-crop budget tool |
| A5 | 2026–2027 real dollars | CPI factor from the latest 12 published months | Rebuild in 2027 |
| A6 | residue_class | Qualitative (high / medium / low) | K-State residue data, if a soil indicator needs numbers |
| A8 | costs.csv, regions NC and SC | Central-Kansas K-State budgets have no fallow: they are used as proxies for the fallow-based rotations, and the fallow phase gets a weed-control allowance = herbicides of the same year's NW wheat (W-F) budget | A K-State fallow budget for central Kansas (none published) |
| A9 | county_budget_regions.csv | K-State gives no county list for its budget regions: counties are assigned by NASS agricultural district; West Central and Central districts are split at 38.7 N | Ask K-State (AgManager) or the team's agronomy contact |
| A7 | fallow cost | Land rent only; fallow operations are inside the next crop (K-State practice, E30) | — (this is a convention, not a guess) |

## Not done, and why

- `prices.csv`, `county_yields.csv`, `crop_calendar_ks.csv`: the scripts are written and tested on sample data, but need `NASS_API_KEY` to download.
- AMS local bids: `fetch_ams.py` written, needs `AMS_API_KEY`; not run.
- Holman et al. 2021 (Crop Science) full text: paywalled; only the abstract is confirmed (E20).
- Nielsen and Vigil (E21) and KGS aquifer figures (E22): still secondhand.
- E12: two versions of the "sorghum after wheat vs after a summer crop" number; not used by any rotation.
- FAO GAEZ and Ag Data Commons (stretch): not started.
