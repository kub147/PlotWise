"""Unit conversion factors: bushel weights (wheat 60 lb, corn and sorghum 56 lb), lb, acre, inch, cwt."""
LB_KG = 0.45359237
ACRE_HA = 0.40468564224
INCH_MM = 25.4
CWT_KG = 100 * LB_KG

BUSHEL_LB = {"wheat": 60.0, "corn": 56.0, "sorghum": 56.0}
BUSHEL_KG = {crop: lb * LB_KG for crop, lb in BUSHEL_LB.items()}


def bu_acre_to_kg_ha(value: float, crop: str) -> float:
    return value * BUSHEL_KG[crop] / ACRE_HA


def lb_acre_to_kg_ha(value: float) -> float:
    return value * LB_KG / ACRE_HA


def per_acre_to_per_ha(value: float) -> float:
    return value / ACRE_HA
