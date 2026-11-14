# crops-economics

Workstream C: crop data, rotations, prices and costs for the Field Shift engine.
Every number has a source (see `reference/evidence.md`).

## Files

All results are in `reference/`:

| File | What it is |
| :--- | :--- |
| `crops.csv` | Crop parameters: planting and harvest dates, water use, root depth, yield per mm of water |
| `rotations.json` | 8 crop rotations with card text (why, risks, gaps, check locally) |
| `costs.csv` | Cost per acre for each crop and fallow, 2016–2027 (K-State budgets) |
| `prices.csv` | Kansas crop prices since 1990 (USDA NASS) |
| `county_yields.csv` | Real farm yields from counties around Tribune (USDA NASS) |
| `county_vs_trial.csv` | Farm yields vs Tribune trial yields |
| `calibration_targets.csv` | Measured values from Tribune to check the engine |
| `evidence.md` | All sources |

## Use in the engine

```python
import sys; sys.path.insert(0, "crops-economics/scripts")
from lookup import Economics
eco = Economics()
eco.net_return_usd_per_acre(2012, "grain_sorghum", "sorghum|W-S-F", yield_kg_ha=3000)
```

Values are in 2025 US dollars. Year = harvest year.

## Check that everything works

```bash
python crops-economics/run_all.py
```

It runs the tests and prints `ALL OK`. It downloads nothing.

To download fresh data (rarely needed): `python crops-economics/run_all.py --refresh`
(NASS data also needs `NASS_API_KEY` set in the terminal).

## More

- Conventions (years, dollars, fallow costs): `reference/README.md`
- Assumptions and open items: `HANDOVER.md`
