"""Criterion scores (0-1) per rotation and a weight-sensitivity analysis.

Scores use FIXED reference scales, so adding or removing a rotation never changes the score of another one.
The scales are value judgements, not measurements (ASSUMPTION; review with workstreams C and E):

    water            share of precipitation that passes through a crop instead of being lost   0.35 -> 0, 0.60 -> 1
    soil             cropping intensity: crops harvested per year (residue and roots returned)  0.5 -> 0, 1.0 -> 1
    income           mean net return MINUS that of wheat-fallow on the same field and scenario  -60 -> 0, +60 -> 1
    dry_year_safety  same, in the dry years of the record                                        -60 -> 0, +60 -> 1
                     (2025 USD per acre per year; wheat-fallow itself scores 0.5 on both)

Why money is scored against wheat-fallow: the level of the net return depends on land rent (43-82 USD per acre,
different per region) and on the yield scenario (county average or well managed, 30-60 USD apart), but neither
changes which rotation earns more on a given field. Differences between rotations on one field are 0-90 USD, so a
+-60 scale keeps money as decisive as water and soil. With an absolute scale wide enough for both scenarios, the two
correlated intensity criteria (water, soil) out-voted a loss of 35 USD per acre per year.

Weight sensitivity follows stochastic multicriteria acceptability analysis (SMAA; Lahdelma et al. 1998):
draw many weight sets uniformly from all possible weightings and count how often each rotation comes first.
"""
from __future__ import annotations

import numpy as np

CRITERIA = ("water", "soil", "income", "dry_year_safety")
SCALES = {"water": (0.35, 0.60), "soil": (0.5, 1.0), "income": (-60.0, 60.0), "dry_year_safety": (-60.0, 60.0)}
MONEY_REFERENCE = "WF"
DEFAULT_WEIGHTS = {c: 0.25 for c in CRITERIA}


def _scale(x: float, lo: float, hi: float) -> float:
    return round(float(min(1.0, max(0.0, (x - lo) / (hi - lo)))), 2)


def _dry_mean(result: dict, dry_years: list[int]) -> float:
    dry = [result["net_year"][y] for y in dry_years if y in result["net_year"]]
    return float(np.mean(dry)) if dry else result["summary"]["mean_of_worst_fifth"]


def scores_for(result: dict, dry_years: list[int], reference: dict | None = None) -> tuple[dict, float]:
    """Scores of one replayed rotation; also returns its mean net return in the dry years.
    reference: the replayed wheat-fallow of the same field and scenario (None: the rotation is the reference)."""
    ref = reference or result
    dry_mean = _dry_mean(result, dry_years)
    raw = {"water": result["indicators"]["crop_water_share"], "soil": result["indicators"]["crops_per_year"],
           "income": result["summary"]["mean"] - ref["summary"]["mean"],
           "dry_year_safety": dry_mean - _dry_mean(ref, dry_years)}
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
