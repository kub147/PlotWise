"""Baseline: can gridded weather explain 24 years of K-State trial yields at Tribune, Kansas?

Usage:
    EE_PROJECT=<your-ee-project> python3 water_balance_baseline.py [--cache tribune_gridmet.json]

Pulls daily gridMET weather (precipitation, temperature, reference ET) for the Tribune station from Earth Engine,
runs a deliberately simple, uncalibrated single-layer soil-water bucket (FAO-56 style crop coefficients and a
water-stress coefficient) through each fallow + crop period, and compares the result with measured yields in
reference/kstate_tribune_rotation_yields.csv. It prints R2 and leave-one-out R2 for a few simple predictors.

This is the number to beat, not the final model. Known gaps: one soil layer, fixed planting dates, no residue or
tillage effect, no winterkill / disease / hail, soil water capacity assumed (250 mm).
"""
import argparse, csv, datetime as dt, json, os
import numpy as np

SITE = (-101.75, 38.47)   # K-State Southwest Research-Extension Center, Tribune unit (approximate)
CAPACITY_MM = 250.0       # plant-available water in the root zone — assumption, replace with SSURGO value
HERE = os.path.dirname(os.path.abspath(__file__))

def load_weather(cache):
    if os.path.exists(cache):
        raw = json.load(open(cache))
    else:
        import ee
        ee.Initialize(project=os.environ["EE_PROJECT"])
        pt, raw = ee.Geometry.Point(list(SITE)), {}
        for y in range(1994, 2021):
            col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate(f"{y}-01-01", f"{y + 1}-01-01").select(["pr", "tmmx", "tmmn", "eto"])
            rows = col.getRegion(pt, 4000).getInfo()
            i = {k: rows[0].index(k) for k in ("time", "pr", "tmmx", "tmmn", "eto")}
            for r in rows[1:]:
                raw[str(r[i["time"]])] = [r[i["pr"]], r[i["tmmx"]], r[i["tmmn"]], r[i["eto"]]]
        json.dump(raw, open(cache, "w"))
    out = {}
    for k, (pr, tx, tn, eto) in raw.items():
        t = dt.datetime.fromtimestamp(int(k) / 1000, dt.timezone.utc).date()
        out[t] = (pr or 0.0, eto or 0.0)
    return out

def load_yields():
    rows = [r for r in csv.DictReader(l for l in open(os.path.join(HERE, "..", "reference", "kstate_tribune_rotation_yields.csv")) if not l.startswith("#"))]
    wheat = {int(r["year"]): float(r["wheat_wssf"]) for r in rows if r["wheat_wssf"]}
    sorghum = {int(r["year"]): float(r["sorghum_wssf_first"]) for r in rows if r["sorghum_wssf_first"]}
    return wheat, sorghum

def kc_wheat(t, y):       # planted about 1 Oct (y-1), harvested about 30 Jun (y)
    if t < dt.date(y - 1, 10, 1) or t > dt.date(y, 6, 30): return None
    if t < dt.date(y - 1, 11, 15): return 0.4
    if t < dt.date(y, 3, 10): return 0.3
    if t < dt.date(y, 4, 25): return 0.3 + 0.85 * (t - dt.date(y, 3, 10)).days / 46
    if t < dt.date(y, 6, 5): return 1.15
    return 1.15 - 0.8 * (t - dt.date(y, 6, 5)).days / 25

def kc_sorghum(t, y):     # planted about 1 Jun, harvested about 10 Oct
    if t < dt.date(y, 6, 1) or t > dt.date(y, 10, 10): return None
    if t < dt.date(y, 6, 25): return 0.3
    if t < dt.date(y, 7, 25): return 0.3 + 0.75 * (t - dt.date(y, 6, 25)).days / 30
    if t < dt.date(y, 9, 5): return 1.05
    return 1.05 - 0.5 * (t - dt.date(y, 9, 5)).days / 35

def simulate(weather, days, kc_fn, year, start, initial_fraction):
    """Return (soil water at planting, seasonal actual ET, list of (date, stress coefficient))."""
    s, eta_sum, at_planting, stress = initial_fraction * CAPACITY_MM, 0.0, None, []
    for t in days:
        if t < start: continue
        if t > dt.date(year, 10, 15): break
        pr, eto = weather[t]
        effective = pr * 0.9 if pr > 2 else 0.0             # small events are lost to evaporation
        kc = kc_fn(t, year)
        if kc is None:                                      # fallow: soil evaporation slows as the profile dries
            loss = 0.20 * eto * min(1, s / (0.5 * CAPACITY_MM)) + (0.10 * eto if pr > 2 else 0)
            s = min(CAPACITY_MM, max(0, s + effective - loss))
        else:
            if at_planting is None: at_planting = s
            ks = min(1, s / (0.5 * CAPACITY_MM))
            eta = kc * eto * ks
            s = min(CAPACITY_MM, max(0, s + effective - eta)); eta_sum += eta
            stress.append((t, ks))
    return at_planting, eta_sum, stress

def report(name, predictors, y):
    x = np.column_stack([np.ones(len(y))] + [np.array(p, float) for p in predictors])
    b, *_ = np.linalg.lstsq(x, y, rcond=None)
    r2 = 1 - ((y - x @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    loo = []
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        bi, *_ = np.linalg.lstsq(x[m], y[m], rcond=None); loo.append(x[i] @ bi)
    loo = np.array(loo)
    q2 = 1 - ((y - loo) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    print(f"   {name:<42} R2={r2:.2f}  LOO-R2={q2:.2f}  LOO-RMSE={np.sqrt(((y - loo) ** 2).mean()):.1f} bu/acre")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cache", default="tribune_gridmet.json"); a = ap.parse_args()
    weather = load_weather(a.cache); days = sorted(weather)
    psum = lambda d0, d1: sum(weather[t][0] for t in days if d0 <= t <= d1)
    wheat, sorghum = load_yields()

    ys = sorted(wheat); y = np.array([wheat[k] for k in ys])
    print(f"WHEAT after fallow, n={len(ys)}, mean {y.mean():.0f} bu/acre, CV {100 * y.std() / y.mean():.0f}%")
    fallow_p = [psum(dt.date(k - 2, 11, 1), dt.date(k - 1, 9, 30)) for k in ys]
    season_p = [psum(dt.date(k - 1, 10, 1), dt.date(k, 6, 30)) for k in ys]
    sims = [simulate(weather, days, kc_wheat, k, dt.date(k - 2, 11, 1), 0.35) for k in ys]
    report("fallow precipitation + season precipitation", [fallow_p, season_p], y)
    report("modelled seasonal ET", [[s[1] for s in sims]], y)
    report("modelled soil water at planting + season P", [[s[0] for s in sims], season_p], y)

    ys = sorted(sorghum); y = np.array([sorghum[k] for k in ys])
    print(f"SORGHUM after wheat, n={len(ys)}, mean {y.mean():.0f} bu/acre, CV {100 * y.std() / y.mean():.0f}%")
    fallow_p = [psum(dt.date(k - 1, 7, 1), dt.date(k, 5, 31)) for k in ys]
    season_p = [psum(dt.date(k, 6, 1), dt.date(k, 9, 15)) for k in ys]
    sims = [simulate(weather, days, kc_sorghum, k, dt.date(k - 1, 7, 1), 0.15) for k in ys]
    report("fallow precipitation + season precipitation", [fallow_p, season_p], y)
    report("modelled seasonal ET", [[s[1] for s in sims]], y)
    report("modelled soil water at planting + season P", [[s[0] for s in sims], season_p], y)
    print(f"   modelled soil water at sorghum planting: mean {np.mean([s[0] for s in sims]):.0f} mm "
          f"(measured at Tribune 2008-2015: 5.33 in = 135 mm in an 8 ft profile)")

if __name__ == "__main__":
    main()
