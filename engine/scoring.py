"""Criterion scores (0-1) per rotation and a weight-sensitivity analysis.

Water and soil both reward more intensive cropping, so they are correlated. Scores use FIXED reference scales, so adding or removing a rotation never changes the score of another one.
The scales are value judgements, not measurements (ASSUMPTION; review with workstreams C and E):

    water            share of precipitation that passes through a crop instead of being lost   0.35 -> 0, 0.60 -> 1
    soil             cropping intensity: crops harvested per year (residue and roots returned)  0.5 -> 0, 1.0 -> 1
    income           mean net return before land rent, 2025 USD per acre per year              -50 -> 0, +20 -> 1
    dry_year_safety  mean net return before land rent in the dry years of the record           -100 -> 0,   0 -> 1

Money is scored BEFORE land rent: rent is nearly the same for every rotation of a region (within a few dollars) but differs between regions
(43-82 USD per acre), so the full net return would make every Hays rotation look worse than every Tribune one.

Weight sensitivity follows stochastic multicriteria acceptability analysis (SMAA; Lahdelma et al. 1998):
draw many weight sets uniformly from all possible weightings and count how often each rotation comes first.
"""
from __future__ import annotations

import numpy as np

CRITERIA = ("water", "soil", "income", "dry_year_safety")
SCALES = {"water": (0.35, 0.60), "soil": (0.5, 1.0), "income": (-50.0, 20.0), "dry_year_safety": (-100.0, 0.0)}
DEFAULT_WEIGHTS = {c: 0.25 for c in CRITERIA}


def _scale(x: float, lo: float, hi: float) -> float:
    return round(float(min(1.0, max(0.0, (x - lo) / (hi - lo)))), 2)


def scores_for(result: dict, dry_years: list[int]) -> tuple[dict, float]:
    """Scores of one replayed rotation; also returns its mean net return in the dry years."""
    rent = result["summary"].get("land_rent", 0.0)
    dry = [result["net_year"][y] for y in dry_years if y in result["net_year"]]
    dry_mean = float(np.mean(dry)) if dry else result["summary"]["mean_of_worst_fifth"]
    raw = {"water": result["indicators"]["crop_water_share"], "soil": result["indicators"]["crops_per_year"],
           "income": result["summary"]["mean"] + rent, "dry_year_safety": dry_mean + rent}
    return {c: _scale(raw[c], *SCALES[c]) for c in CRITERIA}, dry_mean


def rank(scores: dict[str, dict], weights: dict[str, float]) -> list[str]:
    total = {rid: sum(weights[c] * s[c] for c in CRITERIA) for rid, s in scores.items()}
    return sorted(total, key=total.get, reverse=True)


def weight_sensitivity(scores: dict[str, dict], n_sets: int = 5000, seed: int = 0) -> dict:
    """Share of random weight sets for which each rotation ranks first."""
    ids = list(scores)
    m = np.array([[scores[r][c] for c in CRITERIA] for r in ids])
    w = np.random.default_rng(seed).dirichlet(np.ones(len(CRITERIA)), size=n_sets)
    first = (w @ m.T).argmax(axis=1)
    share = {ids[i]: round(float((first == i).mean()), 2) for i in range(len(ids))}
    best = max(share, key=share.get)
    return dict(weight_sets_tested=n_sets, share_of_wins=share, most_often_first=best,
                stable=bool(share[best] >= 0.6),
                note="Share of all possible priority weightings under which each rotation ranks first. "
                     "Below about 0.6 for the leader, the ranking depends on the farmer's priorities.")
