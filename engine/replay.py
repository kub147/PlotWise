"""Rotation replay: run every phase of every rotation through every year of a field's weather record.

All phases of a rotation are present in every year (as on a farm that splits its land evenly between the
phases), so each rotation gets one whole-farm result per year instead of one lucky or unlucky sequence.
Yields are at farm level (trial level x farm factor); money is in 2025 US dollars per acre of the whole
rotation, fallow acres included; prices are the actual Kansas prices of each harvest year.
"""
from __future__ import annotations

import csv
import functools
import sys

import numpy as np

from . import inputs
from .rotation import build_schedule
from .waterbalance import WaterParams, fallow_periods, season_summaries, simulate
from .yields import trial_yield

sys.path.insert(0, str(inputs.ROOT / "crops-economics" / "scripts"))
from lookup import ACRE_HA, Economics  # noqa: E402

COSTS_CSV = inputs.ROOT / "crops-economics" / "reference" / "costs.csv"
SPIN_UP_YEARS = 2
FAILURE_SHARE = 0.25        # a harvest below this share of the crop's own mean counts as a failed crop
ROTATION_OF_LABEL = {"W-F": "WF", "W-S-F": "WSF", "W-C-F": "WCF"}   # fields.geojson current_rotation -> rotation id


@functools.lru_cache(maxsize=None)
def _rent_table() -> dict:
    """(region, cost_key) -> mean land rent of that budget, 2025 USD per acre-year (budget years to 2026)."""
    acc: dict = {}
    for r in csv.DictReader(open(COSTS_CSV, encoding="utf-8")):
        if r["land_rent_usd_acre_year"] and int(r["year"]) <= 2026:
            acc.setdefault((r["region"], r["cost_key"]), []).append(
                float(r["land_rent_usd_acre_year"]) * float(r["cpi_factor_to_2025"]))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def land_rent_usd_acre(region: str, cost_keys: list[str]) -> float:
    """Mean land rent per acre and year of a rotation: average over its phases of the rent inside each K-State
    budget. Rotations of one region differ by a few dollars at most (budgets assume slightly different rents)."""
    table = _rent_table()
    fallback = table.get((region, "fallow|any"), 0.0)
    return float(np.mean([table.get((region, k), fallback) for k in cost_keys]))


def modelled_rotations(rotations: dict, crops: dict) -> tuple[list[str], dict[str, str]]:
    """Rotations the engine can replay, and why the others are skipped."""
    ok, skipped = [], {}
    for rid, r in rotations.items():
        if r.get("status") == "validation_only":
            skipped[rid] = "used for validation only"
        elif any(c != "fallow" and not crops[c].has_yield_function for c in r["phases"]):
            skipped[rid] = "no yield function for one of its crops"
        else:
            ok.append(rid)
    return ok, skipped


def replay_rotation(rot: dict, wx, crops: dict, par: WaterParams, params: dict, eco: Economics,
                    first_year: int, last_year: int, region: str = "SW", yield_factor: dict | None = None) -> dict:
    """region: K-State cost region (SW, NW, NC, SC). yield_factor: crop -> trial-to-farm factor;
    defaults to params["farm_factor"] (Tribune); engine/county_yield_factors.json has one per county."""
    factor = yield_factor or params["farm_factor"]
    phases, details = rot["phases"], rot["phase_details"]
    rent = land_rent_usd_acre(region, [d["cost_key"] for d in details])
    n = len(phases)
    years = list(range(first_year, last_year + 1))
    net = {y: [] for y in years}                    # per-acre net return of each phase present in year y
    harvests = []                                   # one record per crop harvest
    gain = precip_fallow = crop_et = 0.0
    growing_days = 0
    i0, i1 = wx.index(wx.dates[0].replace(year=first_year, month=1, day=1)), wx.index(wx.dates[0].replace(year=last_year, month=12, day=31)) + 1
    for offset in range(n):
        sched = build_schedule(phases, offset, crops, wx)
        sim = simulate(wx, sched, crops, par)
        by_year = {s["harvest_year"]: s for s in season_summaries(wx, sched, sim)}
        for y in years:
            k, cid = sched.phase_of_year[y]
            cost = eco.phase_cost_usd_per_acre(y, details[k]["cost_key"], region=region)
            if cid == "fallow":
                net[y].append(-cost)
                continue
            s = by_year[y]
            y_trial, method = trial_yield(params, crops[cid], s)
            residual = 1.0
            if details[k].get("follows") == cid:
                residual = params["rotation_residuals"].get(f"{cid} after {cid}", {}).get("residual_multiplier", 1.0)
            y_farm = y_trial * residual * factor[cid]
            revenue = y_farm * ACRE_HA * eco.price_usd_per_kg(y, cid)
            net[y].append(revenue - cost)
            harvests.append(dict(year=y, crop=cid, phase=k, yield_kg_ha=y_farm, et_mm=s["et_mm"],
                                 avail_at_planting=s["avail_at_planting"], method=method))
        for f in fallow_periods(wx, sched, sim):
            if first_year <= f["before_harvest_year"] <= last_year:
                gain += f["gain_mm"]; precip_fallow += f["precip_mm"]
        crop_et += float(sim["crop_et"][i0:i1].sum())
        growing_days += int((sched.kc[i0:i1] > 0).sum())

    n_years = len(years)
    total_precip = float(wx.precip[i0:i1].sum())
    net_year = {y: float(np.mean(v)) for y, v in net.items()}
    crops_in = [c for c in dict.fromkeys(phases) if c != "fallow"]
    yields = {c: [[y, round(float(np.mean([h["yield_kg_ha"] for h in harvests if h["crop"] == c and h["year"] == y])))]
                  for y in years] for c in crops_in}
    crop_mean = {c: float(np.mean([h["yield_kg_ha"] for h in harvests if h["crop"] == c])) for c in crops_in}
    failed = [h for h in harvests if h["yield_kg_ha"] < FAILURE_SHARE * crop_mean[h["crop"]]]
    grain = sum(h["yield_kg_ha"] for h in harvests) / n          # kg per hectare of rotation, all years
    vals = np.array([net_year[y] for y in years])
    return dict(
        years=years, net_year=net_year, yields=yields, crop_mean_kg_ha=crop_mean,
        summary=dict(mean=round(float(vals.mean()), 1), p20=round(float(np.percentile(vals, 20)), 1),
                     worst=round(float(vals.min()), 1), worst_year=int(years[int(vals.argmin())]),
                     share_of_years_with_loss=round(float((vals < 0).mean()), 2),
                     mean_of_worst_fifth=round(float(np.sort(vals)[:max(1, n_years // 5)].mean()), 1),
                     land_rent=round(rent, 1),
                     mean_before_land_rent=round(float(vals.mean()) + rent, 1),
                     share_of_years_with_profit=round(float((vals > 0).mean()), 2),
                     share_of_years_covering_costs_before_rent=round(float((vals + rent > 0).mean()), 2)),
        indicators=dict(
            bare_days_per_year=round(365.25 - growing_days / (n * n_years)),
            storage_efficiency=round(gain / precip_fallow, 2) if precip_fallow else None,
            water_productivity_kg_mm=round(grain / total_precip, 2),
            crop_water_share=round(crop_et / (n * total_precip), 2),
            growing_share_of_year=round(growing_days / (n * n_years * 365.25), 2),
            crops_per_year=round(sum(c != "fallow" for c in phases) / n, 2),
            failed_crop_years=len({h["year"] for h in failed}),
            failed_harvest_share=round(len(failed) / len(harvests), 2)),
        yield_methods={c: next(h["method"] for h in harvests if h["crop"] == c) for c in crops_in})


def replay_field(field: dict, wx, crops: dict, rotations: dict, params: dict, eco: Economics | None = None,
                 first_year: int | None = None, last_year: int | None = None, region: str = "SW",
                 yield_factor: dict | None = None) -> dict:
    eco = eco or Economics()
    par = WaterParams(awc_mm=float(field["awc_mm"]), **params["water"])
    first_year = first_year or wx.first_year + SPIN_UP_YEARS
    last_price_year = min(max(eco.prices[c]) for c in ("wheat", "sorghum", "corn"))
    last_year = last_year or min(last_price_year, wx.last_date.year - 1)
    ids, skipped = modelled_rotations(rotations, crops)
    return dict(par=par, first_year=first_year, last_year=last_year, skipped=skipped, region=region,
                yield_factor=yield_factor or params["farm_factor"],
                rotations={rid: replay_rotation(rotations[rid], wx, crops, par, params, eco, first_year, last_year,
                                                region, yield_factor)
                           for rid in ids})
