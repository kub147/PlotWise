"""Shared pieces for calibration and validation against the K-State Tribune trials."""
from __future__ import annotations

import numpy as np

from .inputs import Crop, Weather
from .rotation import build_schedule
from .waterbalance import WaterParams, fallow_periods, season_summaries, simulate

AWC_TRIBUNE_MM = 320.0   # mean of the five demo fields (304-332 mm, Ulysses and Richfield silt loam, SSURGO)

PHASES = {
    "WF": ["winter_wheat", "fallow"],
    "WSF": ["winter_wheat", "grain_sorghum", "fallow"],
    "WCF": ["winter_wheat", "corn", "fallow"],
    "WSSF": ["winter_wheat", "grain_sorghum", "grain_sorghum", "fallow"],
    "WWSF": ["winter_wheat", "winter_wheat", "grain_sorghum", "fallow"],
    "WW": ["winter_wheat"],
}
# column of reference/kstate_tribune_rotation_yields.csv -> (rotation, phase index)
SERIES = {
    "wheat_wssf": ("WSSF", 0), "wheat_wwsf_first": ("WWSF", 0), "wheat_wwsf_recrop": ("WWSF", 1),
    "wheat_continuous": ("WW", 0), "sorghum_wssf_first": ("WSSF", 1), "sorghum_wssf_second": ("WSSF", 2),
    "sorghum_wwsf": ("WWSF", 2),
}
# Schlegel, Haag, O'Brien 2016, Table 1 (reference/kstate_tribune_soil_water.csv), 2008-2015, converted to mm:
# (crop, rotation) -> fallow efficiency %, fallow accumulation, available water at planting, crop water use
WATER_TARGETS = {
    ("winter_wheat", "WF"): (28, 164, 238, 424),
    ("winter_wheat", "WSF"): (19, 70, 155, 321),
    ("grain_sorghum", "WSF"): (14, 50, 135, 318),
    ("winter_wheat", "WCF"): (15, 57, 147, 318),
    ("corn", "WCF"): (16, 53, 133, 337),
}


def run_rotation(phases: list[str], wx: Weather, crops: dict[str, Crop], par: WaterParams):
    """Start every phase in every year: returns all crop seasons and all fallow periods."""
    seasons, fallows = [], []
    for offset in range(len(phases)):
        sched = build_schedule(phases, offset, crops, wx)
        sim = simulate(wx, sched, crops, par)
        seasons += season_summaries(wx, sched, sim)
        fallows += fallow_periods(wx, sched, sim)
    return seasons, fallows


def water_check(wx: Weather, crops: dict[str, Crop], par: WaterParams) -> dict:
    """Modelled counterparts of WATER_TARGETS for 2008-2015."""
    out = {}
    for rot in ("WF", "WSF", "WCF"):
        seasons, fallows = run_rotation(PHASES[rot], wx, crops, par)
        for (crop, r) in WATER_TARGETS:
            if r != rot:
                continue
            ss = [s for s in seasons if s["crop"] == crop and 2008 <= s["harvest_year"] <= 2015]
            ff = [f for f in fallows if f["before"] == crop and 2008 <= f["before_harvest_year"] <= 2015]
            out[(crop, r)] = (
                100 * sum(f["gain_mm"] for f in ff) / sum(f["precip_mm"] for f in ff),
                float(np.mean([f["gain_mm"] for f in ff])),
                float(np.mean([s["avail_at_planting"] for s in ss])),
                float(np.mean([s["water_use_mm"] for s in ss])))
    return out


def water_error(modelled: dict) -> float:
    """Mean squared relative error over efficiency, water at planting and water use."""
    err = []
    for key, target in WATER_TARGETS.items():
        m = modelled[key]
        err += [((m[0] - target[0]) / target[0]) ** 2, ((m[2] - target[2]) / target[2]) ** 2,
                ((m[3] - target[3]) / target[3]) ** 2]
    return float(np.mean(err))


def series_seasons(wx: Weather, crops: dict[str, Crop], par: WaterParams) -> dict[str, dict[int, dict]]:
    """Modelled season record for every measured yield series: series -> harvest year -> season."""
    cache, out = {}, {}
    for name, (rot, phase) in SERIES.items():
        if rot not in cache:
            cache[rot] = run_rotation(PHASES[rot], wx, crops, par)[0]
        out[name] = {s["harvest_year"]: s for s in cache[rot] if s["phase_index"] == phase}
    return out


def fit(columns: list, y) -> tuple[np.ndarray, float, float, np.ndarray]:
    """Least squares with intercept: coefficients, R2, leave-one-out R2, leave-one-out predictions."""
    x = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in columns])
    y = np.asarray(y, float)
    b, *_ = np.linalg.lstsq(x, y, rcond=None)
    sst = ((y - y.mean()) ** 2).sum()
    loo = np.empty(len(y))
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        bi, *_ = np.linalg.lstsq(x[m], y[m], rcond=None)
        loo[i] = x[i] @ bi
    return b, float(1 - ((y - x @ b) ** 2).sum() / sst), float(1 - ((y - loo) ** 2).sum() / sst), loo
