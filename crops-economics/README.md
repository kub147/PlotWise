# crops-economics

Workstream C of Field Shift: what each crop needs, which rotations we compare, what they cost and
what the harvest sells for. The engine (workstream D) turns weather and soil into yields; this folder
turns yields into money and gives every number a source.

Study area: 46 counties of western and central Kansas (Tribune → Colby → Hays).
Tribune is the validation site.

## What is in `reference/`

| File | Content | Used by |
| :--- | :--- | :--- |
| `crops.csv` | One row per crop: planting, maturity and harvest day; water use per growth stage (FAO-56 Kc); root depth; yield per mm of water (K-State) | engine |
| `rotations.json` | 8 rotations (WF, WSF, WCF, WSSF, WWSF, WSfF, WS-forage, WW): crop order, cost key of each phase, yield multipliers, card text (why, benefits, risks, gaps, check locally) | engine, app |
| `costs.csv` | Cost per acre of each crop and of fallow, 2016–2027, four K-State regions (SW, NW, NC, SC), nominal and 2025 USD | engine |
| `county_budget_regions.csv` | Which cost region each county uses | engine, app |
| `prices.csv` | Kansas crop prices received, 1990–2025, per bushel and per kg, nominal and 2025 USD | engine |
| `cpi_u_annual.csv` | Inflation factors to 2025 USD | engine |
| `county_yields.csv` | Non-irrigated yields of all Kansas counties, 1990–2025; `in_study_area` marks the 46 counties | validation |
| `county_vs_trial.csv` | Farm (county) yields vs Tribune trial yields | validation |
| `calibration_targets.csv` | Measured Tribune values to check the engine: fallow water storage, soil water at planting, water use, yields, net returns (T01–T20) | validation |
| `crop_calendar_ks.csv` | Planting and harvest days from NASS crop progress | `crops.csv` |
| `evidence.md` | Sources (E01–E33) and their status | app, submission |

## Using it in the engine

```python
import sys; sys.path.insert(0, "crops-economics/scripts")
from lookup import Economics

eco = Economics()
eco.price_usd_per_kg(2012, "grain_sorghum")
eco.phase_cost_usd_per_acre(2012, "sorghum|W-S-F", region="NW")
eco.net_return_usd_per_acre(2012, "grain_sorghum", "sorghum|W-S-F", yield_kg_ha=3000, region="NW")
```

- Region of a county: `county_budget_regions.csv` (Tribune SW, Colby NW, Hays NC). Default is SW.
- Values are in 2025 USD; `real=False` gives the dollars of that year.
- Reading `costs.csv` directly: filter by `region`, there is one row per year, region and cost key.

## Rules the numbers follow

- **Year** = harvest year of the crop.
- **Fallow:** K-State puts fallow weed control into the budget of the next crop. Each crop phase therefore
  carries its own operations plus one year of rent; the fallow phase carries one year of rent.
  Rotation cost per acre per year = sum of phase costs of one cycle / `cycle_years`.
- **Crop insurance is excluded** (kept in its own column).
- **Years before 2016** have no K-State budget: the mean real cost of 2016–2026 is used.
- **Yield multipliers** in `rotations.json` (0.75, 0.65, 0.60) already include the effect of less stored
  water. If the soil-water balance also models it, apply only the remainder (`_double_counting_warning`).
- **Farm vs trial yields:** farms reach about 0.9 (wheat) and 0.8 (sorghum) of Tribune trial yields (T19, T20).
- **Two dates per crop:** water use ends at `maturity_doy`; the field is harvested at `harvest_doy`.

Assumptions A1–A9 and open items: `HANDOVER.md`.

## Check and rebuild

```bash
python crops-economics/run_all.py
```

Runs the tests and prints `ALL OK`. Nothing is downloaded.

```bash
python crops-economics/run_all.py --refresh
```

Downloads the K-State budget PDFs and, if `NASS_API_KEY` is set in the terminal, the NASS data, then
rebuilds everything. Only needed when the sources publish new data. Needs `pdftotext` (poppler-utils).
Raw downloads go to `data/raw/` and are not committed.

## Scripts

| Script | Output |
| :--- | :--- |
| `fetch_nass.py` | NASS prices, county and district yields, crop progress → `data/raw/nass/` |
| `fetch_agmanager.py` | K-State budget PDFs → `data/raw/agmanager/` |
| `fetch_ams.py` | AMS Market News Kansas grain reports → `data/raw/ams/` (optional) |
| `parse_agmanager_budgets.py` | PDFs → `data/raw/agmanager/budgets_parsed.csv` |
| `build_costs.py` | `costs.csv` |
| `build_prices.py` | `prices.csv`, `cpi_u_annual.csv` |
| `build_county_yields.py` | `county_yields.csv` |
| `build_county_regions.py` | `county_budget_regions.csv` |
| `compare_county_vs_trial.py` | `county_vs_trial.csv` |
| `derive_crop_calendar.py` | `crop_calendar_ks.csv` |
| `build_crops.py` | `crops.csv` |
| `lookup.py`, `units.py`, `study_area.py` | shared code |
