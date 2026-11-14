"""Grain yield from modelled seasonal crop ET.

Two levels:

kstate_yield      the K-State yield-vs-ET function as published (Stone et al. 2006, Table 1), metric values
                  from crops-economics/reference/crops.csv:
                  yield = slope * (ET - threshold), zero below the threshold, capped at the published maximum.
                  Used as published for corn and sunflower, for which we have no year-by-year trial yields.

calibrated_yield  wheat and sorghum: linear in modelled ET (wheat also loses yield per day >= 34 C between
                  flowering and maturity), fitted on the Tribune four-year rotation trial by calibrate.py and
                  stored in params.json. Trial level; multiply by the farm factor for a farmer's field.
"""
from __future__ import annotations

import json
from pathlib import Path

from .inputs import Crop

KG_HA_PER_BU_ACRE = {"winter_wheat": 67.25, "grain_sorghum": 62.77, "corn": 62.77}
PARAMS_JSON = Path(__file__).resolve().parent / "params.json"


def load_params(path: str | Path = PARAMS_JSON) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def kstate_yield(crop: Crop, et_mm: float, longterm: bool = False) -> float:
    """Yield in kg/ha for a seasonal crop ET in mm, K-State function as published."""
    if not crop.has_yield_function:
        raise ValueError(f"no yield function for {crop.id}")
    slope = crop.slope_longterm_kg_ha_mm if longterm else crop.slope_kg_ha_mm
    y = slope * (et_mm - crop.threshold_et_mm)
    if y <= 0:
        return 0.0
    return min(y, crop.max_yield_kg_ha) if crop.max_yield_kg_ha else y


def calibrated_yield(model: dict, crop: Crop, et_mm: float, hot_days: float) -> float:
    """Trial-level yield in kg/ha from a model in params.json["yield_models"]."""
    y = model["intercept_kg_ha"] + model["per_mm_et_kg_ha"] * et_mm + model["per_hot_day_kg_ha"] * hot_days
    if y <= 0:
        return 0.0
    return min(y, crop.max_yield_kg_ha) if crop.max_yield_kg_ha else y


def trial_yield(params: dict, crop: Crop, season: dict) -> tuple[float, str]:
    """Trial-level yield in kg/ha for one modelled season, and which method produced it."""
    model = params["yield_models"].get(crop.id)
    if model:
        return calibrated_yield(model, crop, season["et_mm"], season["hot_days"]), "calibrated on Tribune trial"
    return kstate_yield(crop, season["et_mm"]), "K-State function as published"


def to_bu_acre(crop_id: str, kg_ha: float) -> float:
    return kg_ha / KG_HA_PER_BU_ACRE[crop_id]
