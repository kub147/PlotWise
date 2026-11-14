"""Compare NASS county yields with the Tribune trial yields (research-evidence open question 4).

Inputs : reference/county_yields.csv (this folder, from build_county_yields.py)
         <repo root>/reference/kstate_tribune_rotation_yields.csv  (the team's transcribed K-State table;
         read only, never modified). Another path can be given as the first argument.
Output : reference/county_vs_trial.csv  (one row per crop and comparison area)

Pairs compared, same year, non-irrigated county yields:
  winter wheat : trial wheat after fallow  = mean of wheat_wssf and wheat_wwsf_first (those present)
  grain sorghum: trial sorghum after wheat = sorghum_wssf_first
Areas: Greeley County, the mean of all fetched counties for that year, and the West Central district.

Reported: number of common years, mean county and trial yields, ratio of means (county / trial),
median of yearly ratios (years with trial yield > 5 bu/acre), Pearson r of the yearly series.
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTY = ROOT / "reference/county_yields.csv"
TRIAL_DEFAULT = ROOT.parent / "reference/kstate_tribune_rotation_yields.csv"
OUT = ROOT / "reference/county_vs_trial.csv"

TRIAL_COLUMNS = {
    "winter_wheat": ["wheat_wssf", "wheat_wwsf_first"],
    "grain_sorghum": ["sorghum_wssf_first"],
}


def num(s: str | None) -> float | None:
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


def read_trial(path: Path) -> dict[str, dict[int, float]]:
    with path.open() as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    reader = csv.DictReader(lines)
    cols = reader.fieldnames or []
    year_col = next((c for c in cols if c.strip().lower() == "year"), None)
    if year_col is None:
        sys.exit(f"no 'year' column in {path}; columns are {cols}")
    for crop, want in TRIAL_COLUMNS.items():
        missing = [c for c in want if c not in cols]
        if missing:
            print(f"WARNING {crop}: columns {missing} not in the trial table; found {cols}")
    out: dict[str, dict[int, float]] = defaultdict(dict)
    for r in reader:
        y = num(r[year_col])
        if y is None:
            continue
        for crop, want in TRIAL_COLUMNS.items():
            vals = [v for c in want if c in r and (v := num(r[c])) is not None]
            if vals:
                out[crop][int(y)] = sum(vals) / len(vals)
    return out


def pearson(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3 or statistics.pstdev(a) == 0 or statistics.pstdev(b) == 0:
        return None
    return statistics.correlation(a, b)


def main() -> None:
    trial_path = Path(sys.argv[1]) if len(sys.argv) > 1 else TRIAL_DEFAULT
    if not trial_path.exists():
        sys.exit(f"trial table not found: {trial_path}")
    if not COUNTY.exists():
        sys.exit(f"{COUNTY} missing: run build_county_yields.py first")
    trial = read_trial(trial_path)

    areas: dict[tuple[str, str], dict[int, float]] = defaultdict(dict)
    all_counties: dict[tuple[str, int], list[float]] = defaultdict(list)
    with COUNTY.open() as f:
        for r in csv.DictReader(f):
            if r["practice"] != "NON-IRRIGATED" or r["crop"] not in TRIAL_COLUMNS:
                continue
            y, v = int(r["year"]), float(r["yield_value"])
            if r["level"] == "county":
                all_counties[(r["crop"], y)].append(v)
                if r["area"] == "Greeley":
                    areas[(r["crop"], "Greeley County")][y] = v
            else:
                areas[(r["crop"], f'{r["area"]} district')][y] = v
    for (crop, y), vals in all_counties.items():
        areas[(crop, "mean of fetched counties")][y] = sum(vals) / len(vals)

    rows = []
    for (crop, area), series in sorted(areas.items()):
        years = sorted(set(series) & set(trial.get(crop, {})))
        if not years:
            continue
        c = [series[y] for y in years]
        t = [trial[crop][y] for y in years]
        ratios = [series[y] / trial[crop][y] for y in years if trial[crop][y] > 5]
        r = pearson(c, t)
        rows.append({
            "crop": crop, "area": area, "trial_series": "+".join(TRIAL_COLUMNS[crop]),
            "years": len(years), "first_year": years[0], "last_year": years[-1],
            "mean_county_bu_acre": round(statistics.mean(c), 1),
            "mean_trial_bu_acre": round(statistics.mean(t), 1),
            "ratio_of_means": round(statistics.mean(c) / statistics.mean(t), 3),
            "median_yearly_ratio": round(statistics.median(ratios), 3) if ratios else "",
            "pearson_r": round(r, 3) if r is not None else "",
            "source": "NASS QuickStats non-irrigated yields (E27) vs Schlegel, Holman, Burnett 2021 Tables 1-2 (E01, E02)",
        })
    if not rows:
        sys.exit("no overlapping years between county and trial yields")
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f'{r["crop"]:<14} {r["area"]:<26} n={r["years"]:>2} ({r["first_year"]}-{r["last_year"]})  '
              f'county {r["mean_county_bu_acre"]:>5} vs trial {r["mean_trial_bu_acre"]:>5} bu/acre  '
              f'ratio {r["ratio_of_means"]}  median yearly {r["median_yearly_ratio"]}  r {r["pearson_r"]}')
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
