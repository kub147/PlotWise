"""Daily single-layer soil-water budget, run continuously through a whole rotation.

Same family as the Kansas Water Budget of K-State (Stone et al. 1995; Khan et al. 1996): reference ET times a
crop coefficient gives the crop's demand, a soil-water coefficient cuts it when the profile dries, and the
seasonal ET goes into a yield-vs-ET function (yields.py).

State: plant-available water in the profile, 0 .. awc_mm (SSURGO value from fields.geojson, 0-150 cm).

Each day
    effective rain   rain_eff * precipitation on days above rain_min_mm; smaller showers are lost to evaporation
    crop growing     ET = Ks * Kc * ETo,  Ks = min(1, water / ((1 - p) * awc)),  Kc and p from crops.csv (FAO-56)
    no crop          evaporation = fallow_evap * ETo * min(1, water / (fallow_dry_frac * awc))
                                   + wet_evap * ETo on days with effective rain
    water above awc_mm leaves the profile as drainage

Mass balance: precipitation = lost rain + evaporation + crop ET + drainage + change in storage
(test_engine.py checks it to rounding error).

The water parameters (rain_eff, rain_min_mm, fallow_evap, wet_evap, fallow_dry_frac) are calibrated on measured
soil water and crop water use at Tribune, never on yields (calibrate.py). A more detailed two-layer version
(FAO-56 dual coefficient with a surface evaporation layer, curve-number runoff and snow) was tried and not
kept: it did no better overall (see docs/engine-validation.md), so the simpler model stays.

Not modelled: snow drift, frozen soil, runoff as a separate term (it is inside rain_eff), root growth, weeds.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .inputs import Crop, Weather
from .rotation import Schedule


@dataclass
class WaterParams:
    awc_mm: float = 320.0            # plant-available water capacity of the profile (fields.geojson, SSURGO)
    rain_eff: float = 0.9            # share of a rain day's precipitation that enters the profile (calibrated)
    rain_min_mm: float = 2.0         # showers up to this size are lost (calibrated)
    fallow_evap: float = 0.20        # evaporation without a crop as a share of ETo, wet profile (calibrated)
    wet_evap: float = 0.10           # extra evaporation on rain days without a crop, share of ETo (calibrated)
    fallow_dry_frac: float = 0.5     # fallow evaporation slows below this share of awc (calibrated)
    initial_fraction: float = 0.5    # water on the first day as a share of awc; two spin-up years remove its effect


def simulate(wx: Weather, sched: Schedule, crops: dict[str, Crop], par: WaterParams) -> dict:
    n = len(wx.dates)
    cap = par.awc_mm
    s = par.initial_fraction * cap
    out = {k: np.zeros(n) for k in ("avail", "evap", "crop_et", "crop_et_pot", "lost_rain", "drain")}
    precip, eto, kc_arr, crop_of_day = wx.precip, wx.eto, sched.kc, sched.crop_of_day
    stress_at = {c.id: (1 - c.p) * cap for c in crops.values()}
    fallow_at = par.fallow_dry_frac * cap
    for i in range(n):
        p = precip[i]
        eff = par.rain_eff * p if p > par.rain_min_mm else 0.0
        kc = kc_arr[i]
        e = et = etp = 0.0
        if kc > 0:
            etp = kc * eto[i]
            et = min(min(1.0, s / stress_at[crop_of_day[i]]) * etp, s + eff)
        else:
            e = par.fallow_evap * eto[i] * min(1.0, s / fallow_at)
            if eff > 0:
                e += par.wet_evap * eto[i]
            e = min(e, s + eff)
        s = s + eff - et - e
        dr = 0.0
        if s > cap:
            dr = s - cap
            s = cap
        out["avail"][i] = s
        out["evap"][i] = e; out["crop_et"][i] = et; out["crop_et_pot"][i] = etp
        out["lost_rain"][i] = p - eff; out["drain"][i] = dr
    out["initial"] = par.initial_fraction * cap
    return out


def season_summaries(wx: Weather, sched: Schedule, sim: dict) -> list[dict]:
    """One record per crop season: water at planting, water use, relative ET by growth period."""
    rows = []
    for s in sched.seasons:
        a, b = s.start, s.end + 1
        b1, b2, b3, _ = s.stage_bounds
        half_mid = b2 + (b3 - b2) // 2
        # Growth periods of the Kansas Water Budget mapped on FAO-56 stages (ASSUMPTION):
        # vegetative = initial + development, flowering = first half of mid-season,
        # yield formation = second half of mid-season, ripening = late season.
        periods = {"vegetative": (a, a + b2), "flowering": (a + b2, a + half_mid),
                   "yield_formation": (a + half_mid, a + b3), "ripening": (a + b3, b)}
        rel = {}
        for name, (i0, i1) in periods.items():
            pot = sim["crop_et_pot"][i0:i1].sum()
            rel[name] = float(sim["crop_et"][i0:i1].sum() / pot) if pot > 0 else 1.0
        before = float(sim["avail"][a - 1]) if a > 0 else float("nan")
        rows.append(dict(
            crop=s.crop, harvest_year=s.harvest_year, phase_index=s.phase_index,
            plant_date=wx.dates[a], harvest_date=wx.dates[s.end],
            avail_at_planting=before, avail_at_harvest=float(sim["avail"][s.end]),
            et_mm=float(sim["crop_et"][a:b].sum()), precip_mm=float(wx.precip[a:b].sum()),
            water_use_mm=before - float(sim["avail"][s.end]) + float(wx.precip[a:b].sum()),
            relative_et=rel, start=a, end=s.end,
            hot_days=int((wx.tmax[a + b2:b] >= 34.0).sum()),           # days >= 34 C from flowering to maturity
            min_tmin_spring=float(wx.tmin[a + b1:a + b3].min())))      # coldest night from stem extension to grain fill
    return rows


def fallow_periods(wx: Weather, sched: Schedule, sim: dict) -> list[dict]:
    """Non-crop periods between two crops: precipitation, water gained, storage efficiency."""
    rows, seasons = [], sched.seasons
    for prev, nxt in zip(seasons, seasons[1:]):
        a, b = prev.end + 1, nxt.start                # first day without a crop .. planting day (exclusive)
        if b - a < 30:
            continue
        pr = float(wx.precip[a:b].sum())
        gain = float(sim["avail"][b - 1] - sim["avail"][a - 1])
        rows.append(dict(after=prev.crop, before=nxt.crop, before_harvest_year=nxt.harvest_year,
                         days=b - a, precip_mm=pr, gain_mm=gain,
                         efficiency=gain / pr if pr > 0 else float("nan")))
    return rows
