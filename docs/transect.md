# Western Kansas transect — why and what each workstream does next

Decided on 2026-11-14 after the first full engine run. Tribune stays the validation site; the demo widens to three
sites along the rainfall gradient and to a county map of western Kansas.

## Why

At Tribune every rotation loses money on average and the five fields get almost the same numbers. That is a true
picture of the driest end of the region, but a demo with one site cannot show what the tool is for. A quick test of
the engine at K-State station towns (gridMET weather at the town, SSURGO soil at the point, south-west Kansas costs
everywhere, 1996–2025) shows that the answer changes over 250 km:

| Site | Rain mm/yr | Wheat–fallow | Wheat–sorghum–fallow | Wheat–corn–fallow | Reading |
| :--- | ---: | ---: | ---: | ---: | :--- |
| Akron, Colorado | 422 | −18 (31%) | −30 (28%) | −79 (31%) | fallow is the least bad |
| **Tribune** | 461 | −33 (17%) | −31 (24%) | −67 (28%) | nothing pays; fallow is survival |
| Garden City | 483 | −40 (28%) | −33 (24%) | −54 (34%) | same |
| **Colby** | 504 | −5 (44%) | **+8 (55%)** | 0 (55%) | replacing fallow turns a loss into a small profit |
| **Hays** | 611 | +10 (44%) | +41 (59%) | +73 (76%) | every rotation pays; intensifying pays more |
| Great Bend | 676 | +11 (48%) | +45 (62%) | +86 (76%) | same |

Mean net return in 2025 USD per acre per year; in brackets the share of years with a profit. This was a test, not a
result: see the cautions below. Further east (Belleville, Hutchinson) fallow is hardly used, so the question
disappears; the transect stops near 98.3° W.

## Cautions

- **The engine is calibrated at Tribune only.** Confidence drops with distance. Colby (140 km) is safer than Hays (230 km).
- **Corn is the weakest part.** It has no calibration of its own, and the modelled 122 bu/acre for dryland corn at Hays looks high.
  The crop history agrees with the doubt: around Hays 103 of 252 clean fields are in wheat–sorghum–fallow and almost none grow corn,
  while the model ranks wheat–corn–fallow first. Check against county corn yields before showing the Hays corn number.
- **Costs differ by region.** The test used south-west Kansas budgets everywhere; K-State publishes separate north-west and
  north-central budgets.
- **Bare-soil days use one NDVI threshold (0.25) everywhere.** In wetter Ellis County fallow fields are greener (weeds), so their
  bare-day counts are low and not comparable with Tribune.

## What exists now (workstream B)

- `data/processed/fields.geojson`: **11 fields at three sites** (new property `site`): Tribune `ks071-001…005`, Colby `ks193-001…003`,
  Hays `ks051-001…003`, with crop history, soil, slope and NDVI as before.
- `data/processed/counties.geojson`: **46 Kansas counties west of 98.3° W** with `county_id` (e.g. `ks071`), centroid `lon`/`lat`,
  `awc_mm` from SSURGO near the centroid, and CDL statistics for 2008 and the latest year (`fallow_share_*`, `summer_to_wheat_*`,
  crop hectares). County centroids are not fields; treat county results as indicative.

## Next steps per workstream

| | Task |
| :--- | :--- |
| **A** | Run the weather pipeline for the six new fields. For the county map: a weather CSV per `county_id` at the centroid in `counties.geojson` (same format, e.g. `data/processed/weather/counties/ks071.csv`); climate JSON is not needed for counties |
| **C** | Add north-west and north-central Kansas dryland budgets to `costs.csv` with a region key; tell D which counties use which. County yields for all 46 counties for validation |
| **D** | Replay the new fields; replay each county (`awc_mm` and weather from the county layer) and write one small file with best rotation, mean return per rotation and share of profitable years per county; compare modelled and NASS yields per county, corn first |
| **E** | Site switch (Tribune / Colby / Hays) in the field view; county map coloured by best rotation or by the gain from replacing fallow; the story "the answer depends on where you farm" |
| **B** | Done for now. On request: more fields per site, NDVI charts and previews for the new fields |
