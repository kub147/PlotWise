# crops-economics — workstream C: crops, rotations and economics

Self-contained folder of workstream C (work plan: "Crops, rotations and economics"). It depends on nothing
else in the repo: every script finds its files relative to this folder.

## What other workstreams use

| File | For | Notes |
| :--- | :--- | :--- |
| `reference/crops.csv` | D | one row per crop; spec columns plus `status`, `yield_per_mm_longterm_kg_ha`, `depletion_fraction_p` |
| `reference/rotations.json` | D, E | 8 rotations; card text (why, benefits, risks, gaps, check_locally, evidence) |
| `reference/costs.csv` | D | cost per acre per rotation phase, 2016–2027, nominal and 2025 USD |
| `reference/prices.csv` | D | Kansas marketing-year prices (built once the NASS key is set) |
| `reference/county_yields.csv` | D | validation level 3 (built once the NASS key is set) |
| `reference/county_vs_trial.csv` | D | how much lower county yields are than Tribune trial yields (open question 4) |
| `reference/calibration_targets.csv` | D | measured Tribune values to calibrate and check the engine |
| `reference/evidence.md` | E | evidence IDs used on the cards |
| `scripts/lookup.py` | D | `Economics().price_usd_per_kg(...)`, `.phase_cost_usd_per_acre(...)`, `.net_return_usd_per_acre(...)` |

Conventions (years, real dollars, fallow costs, multipliers): [reference/README.md](reference/README.md).
Assumptions and open items: [HANDOVER.md](HANDOVER.md).

Use from the engine:

```python
import sys; sys.path.insert(0, "crops-economics/scripts")
from lookup import Economics
eco = Economics()
eco.phase_cost_usd_per_acre(2012, "sorghum|W-S-F")   # 2025 USD; years before 2016 use the 2016-2026 mean
```

## Rebuild and test

Needs Python 3.10+ (standard library only) and `pdftotext` (poppler-utils) to rebuild costs from the K-State PDFs.

```bash
python crops-economics/run_all.py
```

With the NASS key (free, https://quickstats.nass.usda.gov/api) it also builds prices, county yields and the crop calendar:

```bash
export NASS_API_KEY=your_key     # Windows PowerShell: $env:NASS_API_KEY="your_key"
python crops-economics/run_all.py
```

`run_all.py` ends with the tests (`tests/test_reference.py`) and prints `ALL OK` or what failed.
Raw downloads go to `data/raw/` (git-ignored). Never commit keys.

## Scripts

| Script | Does |
| :--- | :--- |
| `fetch_nass.py` | downloads prices, county / district yields, crop progress from QuickStats (key) |
| `fetch_agmanager.py` | downloads the 57 K-State budget PDFs (no key) |
| `fetch_ams.py` | lists / downloads AMS Market News Kansas grain reports (key; optional) |
| `parse_agmanager_budgets.py` | PDF → `data/raw/agmanager/budgets_parsed.csv` |
| `build_costs.py` | → `reference/costs.csv` |
| `build_prices.py` | → `reference/prices.csv`, `reference/cpi_u_annual.csv` |
| `build_county_yields.py` | → `reference/county_yields.csv` |
| `compare_county_vs_trial.py` | → `reference/county_vs_trial.csv` (county vs Tribune yields; reads the repo's `reference/kstate_tribune_rotation_yields.csv`, read only) |
| `derive_crop_calendar.py` | → `reference/crop_calendar_ks.csv` |
| `build_crops.py` | → `reference/crops.csv` |
| `units.py`, `lookup.py` | shared conversions; lookups for the engine |
