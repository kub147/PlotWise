"""Calibrate the engine on the K-State Tribune trials and write engine/params.json.

    python -m engine.calibrate

Step 1  water parameters: grid search against measured fallow efficiency, soil water at planting and crop
        water use (Schlegel, Haag, O'Brien 2016, 2008-2015). Yields are not used in this step.
Step 2  yield models for wheat and sorghum: linear in modelled seasonal ET (wheat: plus days >= 34 C from
        flowering to maturity, after Tack, Barkley, Nalley 2015), fitted on the crop grown in its reference
        position (wheat after fallow, sorghum after wheat) in the four-year rotation trial 1996-2020.
Step 3  rotation residuals: what is left of the measured yield penalty of a second sorghum or wheat crop
        after the water effect the model already produces (see _double_counting_warning in rotations.json).
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

from . import inputs, tribune
from .waterbalance import WaterParams
from .yields import KG_HA_PER_BU_ACRE

PARAMS_JSON = Path(__file__).resolve().parent / "params.json"
GRID = dict(rain_eff=[0.8, 0.9, 1.0], rain_min_mm=[2.0, 5.0], fallow_evap=[0.15, 0.2, 0.25, 0.3, 0.4],
            wet_evap=[0.1, 0.3, 0.6], fallow_dry_frac=[0.3, 0.5, 0.7])
# Farm-level yield as a share of trial-level yield. Wheat and sorghum: calibration_targets.csv T19, T20
# (county / trial yields). Corn and sunflower: ASSUMPTION, same as sorghum (no trial series to compare with).
FARM_FACTOR = {"winter_wheat": 0.9, "grain_sorghum": 0.8, "corn": 0.8, "sunflower": 0.8}


def calibrate_water(wx, crops) -> tuple[WaterParams, float, int]:
    best, best_err, n = None, 1e9, 0
    for values in itertools.product(*GRID.values()):
        par = WaterParams(awc_mm=tribune.AWC_TRIBUNE_MM, **dict(zip(GRID, values)))
        err = tribune.water_error(tribune.water_check(wx, crops, par))
        n += 1
        if err < best_err:
            best, best_err = par, err
    return best, best_err, n


def mean_series(obs: dict, names: list[str]) -> dict[int, float]:
    years = sorted(set.intersection(*(set(obs[n]) for n in names)))
    return {y: float(np.mean([obs[n][y] for n in names])) for y in years}


def fit_yield_models(wx, crops, par) -> tuple[dict, dict]:
    obs = inputs.load_tribune_yields()
    seasons = tribune.series_seasons(wx, crops, par)
    models = {}
    # wheat after fallow: mean of the two measured series; modelled seasons are identical up to the rotation
    for crop, names, use_heat in (("winter_wheat", ["wheat_wssf", "wheat_wwsf_first"], True),
                                  ("grain_sorghum", ["sorghum_wssf_first", "sorghum_wwsf"], False)):
        y_obs = mean_series(obs, names)
        years = [y for y in y_obs if all(y in seasons[n] for n in names)]
        et = [np.mean([seasons[n][y]["et_mm"] for n in names]) for y in years]
        hot = [np.mean([seasons[n][y]["hot_days"] for n in names]) for y in years]
        target = [y_obs[y] * KG_HA_PER_BU_ACRE[crop] for y in years]
        cols = [et, hot] if use_heat else [et]
        b, r2, loo, _ = tribune.fit(cols, target)
        models[crop] = dict(intercept_kg_ha=round(float(b[0]), 1), per_mm_et_kg_ha=round(float(b[1]), 3),
                            per_hot_day_kg_ha=round(float(b[2]), 2) if use_heat else 0.0,
                            fitted_on=names, years=[years[0], years[-1]], n=len(years),
                            r2=round(r2, 3), r2_leave_one_out=round(loo, 3))
    # rotation residuals: measured ratio / modelled ratio, means over common years, never above 1
    residual = {}
    for label, crop, second, first in (("grain_sorghum after grain_sorghum", "grain_sorghum", "sorghum_wssf_second", "sorghum_wssf_first"),
                                       ("winter_wheat after winter_wheat", "winter_wheat", "wheat_wwsf_recrop", "wheat_wwsf_first")):
        years = [y for y in obs[second] if y in seasons[second] and y in obs[first] and y in seasons[first]]
        m = models[crop]
        pred = lambda s: max(0.0, m["intercept_kg_ha"] + m["per_mm_et_kg_ha"] * s["et_mm"] + m["per_hot_day_kg_ha"] * s["hot_days"])
        measured = np.mean([obs[second][y] for y in years]) / np.mean([obs[first][y] for y in years])
        modelled = np.mean([pred(seasons[second][y]) for y in years]) / np.mean([pred(seasons[first][y]) for y in years])
        residual[label] = dict(measured_ratio=round(float(measured), 3), modelled_ratio=round(float(modelled), 3),
                               residual_multiplier=round(float(min(1.0, measured / modelled)), 3))
    return models, residual


def main():
    wx = inputs.load_weather(inputs.TRIBUNE_WEATHER)
    crops = inputs.load_crops()
    par, err, n = calibrate_water(wx, crops)
    print(f"water parameters: best of {n} sets, mean squared relative error {err:.3f}")
    models, residual = fit_yield_models(wx, crops, par)
    out = {
        "_about": "Written by engine/calibrate.py. Do not edit by hand; rerun the script.",
        "calibration_weather": "engine/validation/tribune_station_gridmet.csv (gridMET pixel of the K-State Tribune station)",
        "water": {k: getattr(par, k) for k in GRID},
        "water_objective": round(err, 4),
        "water_grid": GRID,
        "awc_tribune_mm": tribune.AWC_TRIBUNE_MM,
        "yield_models": models,
        "rotation_residuals": residual,
        "farm_factor": {**FARM_FACTOR, "_source": "wheat, sorghum: calibration_targets.csv T19 and T20 (county / trial yields); corn, sunflower: ASSUMPTION, same as sorghum"},
    }
    PARAMS_JSON.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("water", "yield_models", "rotation_residuals")}, indent=1))
    print("written", PARAMS_JSON)


if __name__ == "__main__":
    main()
