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

Default weights: water and soil both rise with cropping intensity. Across the 11 demo fields and both yield
scenarios the two indicators correlate 0.95, so with four equal weights intensity counted twice: wheat-fallow ranked
last on every field, and the first-ranked rotation was the one that earns most in 3 of 22 cases. By default the pair
therefore weighs as much as ONE money criterion: income 2, dry_year_safety 2, water 1, soil 1 (14 of 22 cases, and
wheat-fallow first or tied first where it earns most). The farmer can still set any weights in the app.

Weight sensitivity follows stochastic multicriteria acceptability analysis (SMAA; Lahdelma et al. 1998):
draw many weight sets from all possible weightings and count how often each rotation comes first. The draw treats
the water-soil pair the same way: three weights uniform on the simplex (income, dry_year_safety, the pair), and the
pair's weight split at random between water and soil.
"""
from __future__ import annotations

import numpy as np

CRITERIA = ("water", "soil", "income", "dry_year_safety")
SCALES = {"water": (0.35, 0.60), "soil": (0.5, 1.0), "income": (-60.0, 60.0), "dry_year_safety": (-60.0, 60.0)}
MONEY_REFERENCE = "WF"
INTENSITY_PAIR = ("water", "soil")        # correlated criteria that share one weight by default
DEFAULT_WEIGHTS = {"water": 1 / 6, "soil": 1 / 6, "income": 1 / 3, "dry_year_safety": 1 / 3}


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
    """Best first. Totals are compared to four decimals and ties keep the order of `scores`, as in the app
    (app/src/lib/results.ts rankRotations), so both always show the same order."""
    norm = sum(weights[c] for c in CRITERIA)
    total = {rid: round(sum(weights[c] * s[c] for c in CRITERIA) / norm, 4) for rid, s in scores.items()}
    return sorted(total, key=total.get, reverse=True)


def weight_sensitivity(scores: dict[str, dict], n_sets: int = 5000, seed: int = 0) -> dict:
    """Share of random weight sets for which each rotation ranks first."""
    ids = list(scores)
    m = np.array([[scores[r][c] for c in CRITERIA] for r in ids])
    rng = np.random.default_rng(seed)
    money = [c for c in CRITERIA if c not in INTENSITY_PAIR]
    base = rng.dirichlet(np.ones(len(money) + 1), size=n_sets)        # last column: the water-soil pair
    split = rng.random(n_sets)
    col = {c: base[:, i] for i, c in enumerate(money)}
    col[INTENSITY_PAIR[0]], col[INTENSITY_PAIR[1]] = base[:, -1] * split, base[:, -1] * (1 - split)
    w = np.column_stack([col[c] for c in CRITERIA])
    first = (w @ m.T).argmax(axis=1)
    share = {ids[i]: round(float((first == i).mean()), 2) for i in range(len(ids))}
    best = max(share, key=share.get)
    return dict(weight_sets_tested=n_sets, share_of_wins=share, most_often_first=best,
                stable=bool(share[best] >= 0.6),
                note="Share of all possible priority weightings under which each rotation ranks first; water and soil "
                     "share one weight in the draw because they measure nearly the same thing. "
                     "Below about 0.6 for the leader, the ranking depends on the farmer's priorities.")
