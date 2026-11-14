# reference/ — crops, rotations, prices, costs (workstream C)

Every number here has a source column or an evidence ID ([evidence.md](evidence.md)). Values that are
guesses are marked `ASSUMPTION`. Units are metric unless the column name says otherwise.

| File | What | Built by | Status |
| :--- | :--- | :--- | :--- |
| `crops.csv` | Crop parameters: calendar, FAO-56 Kc and stage lengths, root depth, K-State yield–ET function (metric), bushel weight | `scripts/build_crops.py` | done; planting dates ASSUMPTION until crop progress is fetched |
| `rotations.json` | 8 rotations (WF, WSF, WCF, WSSF, WWSF, WSfF, WS-forage, WW): phases, cost keys, yield multipliers, why / benefits / risks / gaps / check locally, evidence IDs | hand-written, validated against crops.csv and costs.csv | done |
| `costs.csv` | Cost per acre and rotation phase, budget years 2016–2027, nominal and 2025 USD | `parse_agmanager_budgets.py` → `build_costs.py` | done |
| `cpi_u_annual.csv` | CPI-U annual averages and the factor to 2025 dollars | `build_prices.py` | done |
| `prices.csv` | Kansas marketing-year prices received, $/bu and $/kg, nominal and 2025 USD | `fetch_nass.py` → `build_prices.py` | **needs the NASS key** |
| `county_yields.csv` | NASS county and West Central district yields (validation level 3) | `fetch_nass.py` → `build_county_yields.py` | **needs the NASS key** |
| `crop_calendar_ks.csv` | Median planting / harvest day from NASS crop progress | `fetch_nass.py` → `derive_crop_calendar.py` | **needs the NASS key** |
| `calibration_targets.csv` | Measured Tribune values for calibrating and checking the engine (storage efficiency, soil water at planting, water use, yields, net returns) | hand-written from E01–E10 | done |
| `evidence.md` | Evidence register and answers to the open questions | hand-written | done |

## Conventions the engine must follow

- **Year** = harvest year of the crop. For prices it is the first year of the marketing year (wheat Jun–May; corn, sorghum, sunflower Sep–Aug), which is the same thing.
- **Real dollars** = 2025 USD, deflated with the calendar-year CPI-U of the harvest year.
- **Crop insurance is excluded** from `cost_usd_per_acre` (it is kept in its own column), because the project leaves out premiums and payouts alike.
- **Fallow costs**: K-State charges the weed control of a fallow to the crop that follows it. So in `costs.csv` each crop phase carries its own operations plus the preceding fallow's operations plus one year of land rent, and a `fallow|any` row carries one year of land rent. Summed over a rotation cycle this reproduces the K-State budgets exactly (checked for WF and WSF 2020).
- **Rotation cost per acre per year** = sum of the phase costs of one cycle / `cycle_years`.
- **Years without a budget** (before 2016): use the mean real 2016–2026 cost of that cost key (ASSUMPTION). `scripts/lookup.py` implements this, so the engine never hard-codes a cost or a price.
- **Yield–ET slopes**: `yield_per_mm_kg_ha` is the experimental slope; `yield_per_mm_longterm_kg_ha` includes hail, frost and pests (Stone et al. 2006). Which one to use is a calibration choice for D; say which one in the results.
- **Yield multipliers** in `rotations.json` already include the effect of less stored water. Read `_double_counting_warning` before applying them.

## Rebuild everything

From the repo root: `python crops-economics/run_all.py` (see `crops-economics/README.md`).
