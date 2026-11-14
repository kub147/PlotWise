# Work plan

Five people, five workstreams, one deadline: **Sunday 15 November, 23:59 local time** (submission form closes).
We aim to submit a complete version by **Sunday 20:00** and use the rest for fixes.

Read first: [project-brief.md](project-brief.md) (what and why), [data-sources.md](data-sources.md) (where the data is), [research-evidence.md](research-evidence.md) (what the agronomy says).

## How we split

Three people prepare inputs, one builds the engine, one builds the app and the story. Nobody waits for anybody: the engine starts from a working baseline script, and the app starts from a sample results file.

```
A  Weather & water ─┐
B  Fields & soil ───┼──► D  Engine (replay, economics, scoring) ──► E  App & story
C  Crops & money ───┘            ▲ validation against K-State trials
```

| | Workstream | Owns | Folder |
| :--- | :--- | :--- | :--- |
| **A** | Weather and water | Daily weather per field, climate trends, GRACE, SMAP | `pipelines/weather/` |
| **B** | Fields, soil and vegetation | Demo fields, their crop history, soil, slope, NDVI | `pipelines/fields/` |
| **C** | Crops, rotations and economics | Crop table, rotation definitions, prices, costs, the evidence behind every claim | `reference/`, `pipelines/economics/` |
| **D** | Engine and validation | Soil-water balance, yields, net returns, indicators, scoring, validation plots | `engine/` |
| **E** | App and story | Dashboard, cards, demo video, slides, submission text | `app/`, `docs/submission/` |

Suggested: the repo owner takes **D**, because D is where everything meets. Whoever likes front-end most takes **E**; whoever reads papers fastest takes **C**.

## Timeline

Hours count from kickoff (T+0 = when all five have read this file).

| When | Milestone | What must exist |
| :--- | :--- | :--- |
| T+0 → T+1 | **Kickoff** | Workstreams assigned; API keys requested; everyone can run Earth Engine; field IDs and file formats below agreed; no changes to formats after this without telling D and E |
| T+1 → T+6 | **Sprint 1: one field, end to end** | A: weather CSV for field 1. B: `fields.geojson` with field 1. C: crop table and four rotations. D: replay for field 1 with those inputs. E: dashboard reading the sample results |
| T+6 | **Checkpoint 1** (30 min, everyone) | Real numbers for one field on screen. Decide what is cut |
| T+6 → Saturday night | **Sprint 2: make it true** | D: calibration and validation plot vs Tribune. C: prices and costs in. A: trends and GRACE. B: 3–5 fields, bare-soil days. E: cards, sliders, ranking |
| Sunday morning | **Checkpoint 2** | All must-haves done (brief, section 8). Pick stretch goals, at most one per person |
| Sunday → 14:00 | **Sprint 3: stretch and polish** | "This season" view with SMAP; weight sensitivity; second validation; extra fields |
| **Sunday 14:00** | **Feature freeze** | Only bug fixes after this |
| Sunday 14:00 → 20:00 | **Story** | Demo recording, slides, README, submission text, data and reference list |
| **Sunday 20:00** | **Submit** | Then review as a judge would and fix |
| Sunday 23:59 | Hard deadline | — |

If Sprint 1 slips, cut fields (keep one) before cutting rotations or validation.

## Files we exchange

Small, plain files in `data/processed/` (committed). Raw downloads go to `data/raw/` (ignored). Units are metric inside the pipeline; the app converts to bushels, acres and inches for display. Dates are ISO (`YYYY-MM-DD`).

**`data/processed/fields.geojson`** — owner B
One feature per demo field. Properties:
`field_id` (e.g. `ks071-001`), `name`, `county_fips`, `area_ha`, `lon`, `lat`, `crop_history` (object, year → CDL code, 2008–2025), `current_rotation` (e.g. `W-S-F`), `fallow_share`, `probably_irrigated` (true/false), `awc_mm` (plant-available water to 1.5 m), `texture`, `organic_matter_pct`, `kfactor`, `hydrologic_group`, `slope_pct`, `bare_days_per_year`.

**`data/processed/weather/<field_id>.csv`** — owner A
`date, precip_mm, tmax_c, tmin_c, eto_mm, srad_mj_m2, wind_m_s` — daily, 1994-01-01 to the latest available date, no gaps. One extra file `weather/sources.md` says which product fills each column.

**`data/processed/climate/<field_id>.json`** — owner A
Trend table (indicator, mean first half, mean second half, slope per decade, Mann-Kendall p), year types (year → dry / normal / wet), monthly water balance, GRACE series and trend, SMAP root-zone series with today's percentile for the calendar date.

**`reference/crops.csv`** — owner C
`crop, plant_doy, harvest_doy, kc_ini, kc_mid, kc_end, stage_lengths_days, root_depth_m, threshold_et_mm, yield_per_mm_kg_ha, max_et_mm, bushel_kg, residue_class, fixes_nitrogen, source` — one row per crop (winter wheat, grain sorghum, corn, sunflower, proso millet, spring forage triticale, field pea, fallow).

**`reference/rotations.json`** — owner C
List of rotations: `id` (`WF`, `WSF`, `WCF`, `WSSF`, `WWSF`, `WS-forage`, …), `name`, `phases` (ordered list of crop IDs incl. `fallow`), `tillage`, `effects` (multipliers such as second sorghum 0.65, with source), `why` (one sentence), `check_locally` (list).

**`reference/prices.csv`**, **`reference/costs.csv`** — owner C
`year, crop, price_usd_per_bu, source` (marketing-year average, nominal, plus a CPI column) and `crop, cost_usd_per_acre, year, source` (incl. fallow).

**`data/processed/results/<field_id>.json`** — owner D
Per rotation: `yields` (crop → list of year, kg/ha), `net_return_usd_acre` (list per year), summary (`mean`, `p20`, `worst`, `share_of_years_with_loss`), `indicators` (`bare_days_per_year`, `storage_efficiency`, `water_productivity_kg_mm`, `failed_crop_years`), `scores` (0–1 per criterion), `evidence` (list of source IDs), `gaps` (list). A sample with made-up numbers is in `data/processed/results/sample.json` so that E can start immediately.

## Workstream briefs

Each brief ends with a prompt you can paste into Claude after opening the repo.

### A — Weather and water

**Goal:** trustworthy daily weather for each demo field and the "What has changed" numbers.

1. Daily series 1994 → today for each field centroid: precipitation, Tmax, Tmin, reference ET from gridMET (`IDAHO_EPSCOR/GRIDMET`); radiation and wind from NASA POWER. Write the weather CSV.
2. Cross-check precipitation: gridMET vs PRISM vs IMERG vs POWER, annual and April–September. One small table and one chart; keep the POWER-trend caveat.
3. Trends with Mann-Kendall p (extend `scripts/power_indicators.py`): GDD, frost dates, heat days, precipitation, ET₀, dry spells.
4. Year types (dry / normal / wet) from April–September precipitation minus ET₀.
5. GRACE series and trend for the region; SMAP root-zone series and the percentile of the latest value for this calendar date.
6. Stretch: OpenET monthly ET for the demo fields (check coverage first); CoCoRaHS gauge check.

**Done when:** D can run the engine on your CSV without touching it, and E can draw view 2 from `climate/<field_id>.json`.

> Prompt: "Read docs/project-brief.md, docs/data-sources.md and docs/work-plan.md. I own workstream A. Build pipelines/weather/ so that it writes data/processed/weather/<field_id>.csv and data/processed/climate/<field_id>.json exactly as specified in the work plan, for the fields in data/processed/fields.geojson (start with lon -101.75, lat 38.47 if that file is not there yet). Use Earth Engine with the project in $EE_PROJECT and the NASA POWER API. Keep Earth Engine requests small. Show me the precipitation cross-check table before anything else."

### B — Fields, soil and vegetation

**Goal:** 3–5 real dryland fields in Greeley County, each with its history and soil.

1. Download Crop Sequence Boundaries (2018–2025), clip to Greeley County (FIPS 20071). Pick fields ≥ 40 ha with clear histories: one wheat–fallow, one wheat–sorghum–fallow, one wheat–corn–fallow, one that changed rotation, and one with no fallow (probably irrigated) as a contrast. Field 1 should be close to the Tribune station (about 38.47°N, 101.75°W).
2. Crop history per field 2008–2025 from CDL (majority class per year); derive `current_rotation` and `fallow_share`.
3. Soil from SSURGO via Soil Data Access: dominant component, available water capacity to 1.5 m, texture, organic matter, K factor, hydrologic group.
4. Slope from SRTM.
5. NDVI series per field (MODIS 2000 →, HLS or Sentinel-2 2017 →); bare-soil days per year (NDVI below about 0.25–0.3, tune on a known fallow year); export the series for the chart in view 1.
6. Stretch: ECOSTRESS LST map of field 1 on a hot day; irrigation mask.

**Done when:** `fields.geojson` validates against the spec and the crop history of each field makes sense on a NAIP image.

> Prompt: "Read docs/project-brief.md, docs/data-sources.md and docs/work-plan.md. I own workstream B. Build pipelines/fields/ to produce data/processed/fields.geojson as specified: select demo fields in Greeley County, Kansas from the USDA Crop Sequence Boundaries, attach CDL crop history, SSURGO soil properties (Soil Data Access REST), SRTM slope and NDVI-based bare-soil days. Use Earth Engine with $EE_PROJECT. Start with one field near lon -101.75, lat 38.47 and show me its crop history before adding more."

### C — Crops, rotations and economics

**Goal:** every agronomic and economic number in the product has a source.

1. Get the NASS QuickStats and AMS Market News API keys (do this first).
2. `reference/crops.csv`: FAO-56 crop coefficients and stage lengths; planting and harvest dates for west-central Kansas; thresholds and slopes from `reference/kstate_yield_vs_et.csv` converted to metric.
3. `reference/rotations.json`: WF, WSF, WCF, WSSF, WWSF first; then a fallow-replacement rotation (spring forage). Effects and "why" from research-evidence.md.
4. Prices: Kansas marketing-year prices received for wheat, sorghum, corn since 1995 (QuickStats) plus CPI. Costs: K-State AgManager dryland budgets for western Kansas, including the cost of fallow.
5. County yields for Greeley and neighbouring counties since 1995 (QuickStats) for validation level 3.
6. Confirm the three "secondhand" items in research-evidence.md and answer its open questions.
7. Keep a short `reference/evidence.md`: ID, claim, source, link — the IDs go into rotation cards.

**Done when:** D has no hard-coded agronomy or prices left in the engine.

> Prompt: "Read docs/project-brief.md, docs/research-evidence.md and docs/work-plan.md. I own workstream C. Create reference/crops.csv, reference/rotations.json, reference/prices.csv and reference/costs.csv as specified. Use the K-State tables already in reference/, FAO-56 for crop coefficients, the USDA NASS QuickStats API (key in $NASS_API_KEY) for prices and county yields, and K-State AgManager budgets for costs. Every value needs a source column. Flag anything you could not verify instead of guessing."

### D — Engine and validation

**Goal:** the replay, and proof that it is believable.

1. Turn `scripts/water_balance_baseline.py` into `engine/`: a daily soil-water balance that runs any rotation from `rotations.json` on any weather CSV, with soil capacity from `fields.geojson` and crop parameters from `crops.csv`.
2. Replay: start every phase of every rotation in every year since 1995; collect yields per crop and year.
3. Yield step: K-State yield-vs-ET function; then add rotation effects and a stress term for the critical growth stage. Keep each addition only if it improves leave-one-out R² against the Tribune table.
4. **Validation plot**: modelled vs measured yield, wheat and sorghum, all rotation phases in `reference/kstate_tribune_rotation_yields.csv`. Baseline to beat: wheat R² 0.44, sorghum R² 0.63.
5. Economics: net return per acre and year from prices and costs; summary statistics.
6. Indicators: bare-soil days, storage efficiency, water productivity, failed-crop years.
7. Scoring: criteria scores 0–1, farmer weights, and a sensitivity run over a grid of weights that reports how often each rotation wins.
8. Stretch: "This season" forward run from today's soil water over all historical weather years; gradient-boosting cross-check on county yields.

**Done when:** `results/<field_id>.json` exists for every demo field and the validation plot is in `docs/`.

> Prompt: "Read docs/project-brief.md, docs/research-evidence.md and docs/work-plan.md. I own workstream D. Refactor scripts/water_balance_baseline.py into an engine/ package that reads reference/crops.csv, reference/rotations.json, data/processed/fields.geojson and data/processed/weather/<field_id>.csv and writes data/processed/results/<field_id>.json as specified. First reproduce the baseline R² values, then improve them step by step and keep a table of what each change did. Write tests for the water balance (mass conservation, no negative storage)."

### E — App and story

**Goal:** a judge understands the idea in 30 seconds and can click through it.

1. Hour one: build against `data/processed/results/sample.json` (made-up numbers, already in the repo; real files will have the same shape).
2. Dashboard: map with fields (Leaflet), view 1 "My field", view 2 "What has changed", view 3 "Rotation replay" with sliders and cards, view 4 "This season" if D delivers it. Flask or a static page with the JSON files; deploy somewhere public.
3. Rotation card: why · evidence · benefits · gaps · check locally. Plain words, units a US farmer uses.
4. The validation plot and the data-fusion diagram get their own "How we know" page.
5. Story: one farmer, one field, one question. Storyboard on Saturday; record on Sunday after the freeze.
6. Submission text, list of data and references (from data-sources.md and research-evidence.md), README.

**Done when:** someone outside the team can use it without explanation.

> Prompt: "Read docs/project-brief.md and docs/work-plan.md. I own workstream E. Build the dashboard in app/ with the four views described in the brief, reading data/processed/fields.geojson, data/processed/climate/*.json and data/processed/results/*.json. Start from data/processed/results/sample.json, which has made-up numbers in the final format. Keep it simple and readable for a farmer: plain language, US units, uncertainty visible."

## Working rules

- **English everywhere**: file names, code, comments, docs, commit messages (imperative: "Add weather pipeline").
- Each workstream commits only inside its own folders; `main` stays runnable; `git pull --rebase` before every push.
- Small processed files are committed; raw downloads are not.
- No number without a source. If something is a guess, mark it `ASSUMPTION` in the file and list it in the hand-over.
- Earth Engine: everyone uses their own project via `EE_PROJECT`; reduce over field polygons, export tables.
- At each checkpoint everyone says: done, blocked, cut.

## Submission checklist (owner E, everyone reviews)

- [ ] Team page: all members joined, challenge selected.
- [ ] Read the submission requirements on the Project tab **on Saturday** (we could not open the guide without logging in): required fields, demo format and length limits.
- [ ] If the form asks how AI tools were used, answer it accurately.
- [ ] Public repo link, live demo link, demo video or slides.
- [ ] Data and references listed: every dataset in data-sources.md that we actually used, every paper in research-evidence.md we cite.
- [ ] Limits stated (brief, section 9).
