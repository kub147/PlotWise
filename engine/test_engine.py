"""Tests that need no network and no calibration files.   python -m engine.test_engine"""
from __future__ import annotations

import datetime as dt

import numpy as np

from . import inputs
from .inputs import Crop, Weather
from .rotation import build_schedule, kc_curve
from .scoring import DEFAULT_WEIGHTS, rank, scores_for, weight_sensitivity
from .waterbalance import WaterParams, fallow_periods, season_summaries, simulate
from .yields import kstate_yield


def synthetic_weather(years: int = 8, seed: int = 1) -> Weather:
    rng = np.random.default_rng(seed)
    dates = [dt.date(2000, 1, 1) + dt.timedelta(days=i) for i in range(365 * years + 2)]
    doy = np.array([d.timetuple().tm_yday for d in dates])
    precip = np.where(rng.random(len(dates)) < 0.15, rng.exponential(8.0, len(dates)), 0.0)
    eto = 4.0 - 3.0 * np.cos(2 * np.pi * (doy - 15) / 365)
    tmax = 18 - 14 * np.cos(2 * np.pi * (doy - 15) / 365)
    return Weather(dates, precip, eto, tmax, tmax - 14)


def test_mass_balance_and_bounds(crops):
    wx = synthetic_weather()
    for phases in (["winter_wheat", "fallow"], ["winter_wheat", "grain_sorghum", "fallow"], ["winter_wheat"],
                   ["winter_wheat", "corn", "fallow"]):
        for offset in range(len(phases)):
            for par in (WaterParams(awc_mm=300), WaterParams(awc_mm=120, rain_eff=1.0, wet_evap=0.6, fallow_dry_frac=0.3)):
                sim = simulate(wx, build_schedule(phases, offset, crops, wx), crops, par)
                out = sim["lost_rain"].sum() + sim["evap"].sum() + sim["crop_et"].sum() + sim["drain"].sum()
                change = sim["avail"][-1] - sim["initial"]
                assert abs(wx.precip.sum() - out - change) < 1e-6, "water is not conserved"
                assert sim["avail"].min() >= -1e-9 and sim["avail"].max() <= par.awc_mm + 1e-9, "storage out of bounds"
                assert (sim["crop_et"] <= sim["crop_et_pot"] + 1e-9).all(), "crop ET above demand"
                assert min(sim[k].min() for k in ("evap", "crop_et", "drain", "lost_rain")) >= 0, "negative flux"


def test_schedule(crops):
    wx = synthetic_weather()
    sched = build_schedule(["winter_wheat", "grain_sorghum", "fallow"], 0, crops, wx)
    wheat = [s for s in sched.seasons if s.crop == "winter_wheat"]
    assert wheat and all(wx.dates[s.start].year == s.harvest_year - 1 for s in wheat), "wheat is planted the autumn before"
    assert all(wx.dates[s.end].year == s.harvest_year for s in sched.seasons)
    assert all(a.end < b.start for a, b in zip(sched.seasons, sched.seasons[1:])), "seasons overlap"
    years = sorted({s.harvest_year for s in sched.seasons if s.crop == "grain_sorghum"})
    assert all(b - a == 3 for a, b in zip(years, years[1:])), "one sorghum every three years"
    kc = kc_curve(crops["grain_sorghum"])
    assert len(kc) == crops["grain_sorghum"].season_days and abs(kc.max() - crops["grain_sorghum"].kc_mid) < 1e-9
    try:                                   # sorghum is still in the field when wheat should be planted
        build_schedule(["grain_sorghum", "winter_wheat"], 0, crops, wx)
        raise AssertionError("an infeasible rotation was accepted")
    except ValueError:
        pass


def test_more_water_more_yield(crops):
    wx = synthetic_weather()
    wet = Weather(wx.dates, wx.precip * 1.5, wx.eto, wx.tmax, wx.tmin)
    et = []
    for w in (wx, wet):
        sched = build_schedule(["winter_wheat", "grain_sorghum", "fallow"], 0, crops, w)
        sim = simulate(w, sched, crops, WaterParams(awc_mm=300))
        et.append(sum(s["et_mm"] for s in season_summaries(w, sched, sim)))
        assert all(f["days"] > 200 for f in fallow_periods(w, sched, sim))
    assert et[1] > et[0], "more rain must give more crop water use"
    c = crops["grain_sorghum"]
    assert kstate_yield(c, c.threshold_et_mm - 1) == 0 and kstate_yield(c, 400) > kstate_yield(c, 300) > 0
    assert kstate_yield(c, 5000) == c.max_yield_kg_ha


def test_weight_sensitivity():
    scores = {"A": dict(water=1, soil=1, income=1, dry_year_safety=1), "B": dict(water=0, soil=0, income=0, dry_year_safety=0)}
    assert weight_sensitivity(scores, 500)["share_of_wins"]["A"] == 1.0
    scores = {"A": dict(water=1, soil=0, income=0, dry_year_safety=0), "B": dict(water=0, soil=1, income=0, dry_year_safety=0)}
    share = weight_sensitivity(scores, 4000)["share_of_wins"]
    assert abs(share["A"] - 0.5) < 0.05 and abs(share["A"] + share["B"] - 1) < 1e-9
    # water and soil share one weight: a rotation that wins only on that pair comes first in about a third of the draws
    scores = {"A": dict(water=1, soil=1, income=0, dry_year_safety=0), "B": dict(water=0, soil=0, income=1, dry_year_safety=0),
              "C": dict(water=0, soil=0, income=0, dry_year_safety=1)}
    share = weight_sensitivity(scores, 6000)["share_of_wins"]
    assert all(abs(v - 1 / 3) < 0.04 for v in share.values()), share
    assert abs(sum(DEFAULT_WEIGHTS.values()) - 1) < 1e-9
    assert abs(DEFAULT_WEIGHTS["water"] + DEFAULT_WEIGHTS["soil"] - DEFAULT_WEIGHTS["income"]) < 1e-9
    # equal totals keep the order of the file: (0.5 + 0.5) / 3 + 0.2 / 6 == (0.37 + 0.28) / 3 + (0.56 + 0.34) / 6
    tie = {"WF": dict(water=0.2, soil=0.0, income=0.5, dry_year_safety=0.5),
           "WSF": dict(water=0.56, soil=0.34, income=0.37, dry_year_safety=0.28)}
    assert rank(tie, DEFAULT_WEIGHTS) == ["WF", "WSF"] and rank(dict(reversed(tie.items())), DEFAULT_WEIGHTS) == ["WSF", "WF"]
    wf = {"summary": {"mean": -50.0, "mean_of_worst_fifth": -90.0}, "net_year": {2001: -80.0, 2002: -20.0},
          "indicators": {"crop_water_share": 0.4, "crops_per_year": 0.5}}
    s, dry = scores_for(wf, [2001], wf)
    assert s["income"] == 0.5 and s["dry_year_safety"] == 0.5 and dry == -80.0, "wheat-fallow is the money reference"


def main():
    crops = inputs.load_crops()
    for test in (test_mass_balance_and_bounds, test_schedule, test_more_water_more_yield):
        test(crops); print("ok", test.__name__)
    test_weight_sensitivity(); print("ok test_weight_sensitivity")
    print("ALL OK")


if __name__ == "__main__":
    main()
