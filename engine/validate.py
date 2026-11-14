"""Validate the engine against the K-State Tribune trials and write docs/engine-validation.md.

    python -m engine.validate            # needs engine/params.json (python -m engine.calibrate)

Checks
    1  water: fallow efficiency, soil water at planting, crop water use vs Schlegel, Haag, O'Brien 2016
    2  yields, year by year, seven series of the four-year rotation trial 1996-2020
       a  K-State yield function as published (nothing fitted to yields)
       b  calibrated wheat and sorghum models, with leave-one-out error
    3  crop failures: does the model put the measured zero-yield years among its worst years
    4  rotation effects: second sorghum, recrop wheat, continuous wheat relative to the first crop
    5  level against USDA NASS county non-irrigated yields (Greeley County) and K-State budget planning yields
    6  economics: average net return 2008-2015 by rotation vs the K-State large-scale study
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from . import inputs, tribune
from .waterbalance import WaterParams
from .yields import KG_HA_PER_BU_ACRE, kstate_yield, load_params, to_bu_acre, trial_yield

DOC = inputs.ROOT / "docs" / "engine-validation.md"
FIG = inputs.ROOT / "docs" / "img" / "engine_validation.png"
COUNTY = inputs.ROOT / "crops-economics" / "reference" / "county_yields.csv"
LABEL = {"wheat_wssf": "Wheat after fallow (WSSF)", "wheat_wwsf_first": "Wheat after fallow (WWSF)",
         "wheat_wwsf_recrop": "Wheat after wheat (WWSF)", "wheat_continuous": "Continuous wheat",
         "sorghum_wssf_first": "Sorghum after wheat (WSSF)", "sorghum_wssf_second": "Sorghum after sorghum (WSSF)",
         "sorghum_wwsf": "Sorghum after two wheats (WWSF)"}
RESIDUAL_KEY = {"wheat_wwsf_recrop": "winter_wheat after winter_wheat", "wheat_continuous": "winter_wheat after winter_wheat",
                "sorghum_wssf_second": "grain_sorghum after grain_sorghum"}


def r2_of(obs, pred) -> float:
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    return float(1 - ((obs - pred) ** 2).sum() / ((obs - obs.mean()) ** 2).sum())


def collect(wx, crops, par, params):
    """Per series: years, measured, K-State-as-published and calibrated predictions (bu/acre)."""
    obs = inputs.load_tribune_yields()
    seasons = tribune.series_seasons(wx, crops, par)
    out = {}
    for name in tribune.SERIES:
        years = [y for y in sorted(obs[name]) if y in seasons[name]]
        crop = crops[seasons[name][years[0]]["crop"]]
        res = params["rotation_residuals"].get(RESIDUAL_KEY.get(name, ""), {}).get("residual_multiplier", 1.0)
        out[name] = dict(
            crop=crop.id, years=years, obs=[obs[name][y] for y in years],
            published=[to_bu_acre(crop.id, kstate_yield(crop, seasons[name][y]["et_mm"])) for y in years],
            calibrated=[to_bu_acre(crop.id, trial_yield(params, crop, seasons[name][y])[0] * res) for y in years],
            et=[seasons[name][y]["et_mm"] for y in years], hot=[seasons[name][y]["hot_days"] for y in years],
            residual=res)
    return out


def county_check(wx, crops, par, params):
    rows = list(csv.DictReader(open(COUNTY)))
    out = []
    for crop_id, rot in (("winter_wheat", "WF"), ("grain_sorghum", "WSF"), ("corn", "WCF")):
        county = {int(r["year"]): float(r["yield_value"]) for r in rows
                  if r["area"] == "Greeley" and r["crop"] == crop_id and r["practice"] == "NON-IRRIGATED"}
        seasons, _ = tribune.run_rotation(tribune.PHASES[rot], wx, crops, par)
        factor = params["farm_factor"].get(crop_id, 1.0)
        model = {s["harvest_year"]: to_bu_acre(crop_id, trial_yield(params, crops[crop_id], s)[0] * factor)
                 for s in seasons if s["crop"] == crop_id}
        years = [y for y in sorted(county) if y in model and y >= 1996]
        o, m = [county[y] for y in years], [model[y] for y in years]
        out.append(dict(crop=crop_id, rotation=rot, n=len(years), first=years[0], last=years[-1], factor=factor,
                        county=float(np.mean(o)), model=float(np.mean(m)), r2=float(np.corrcoef(o, m)[0, 1] ** 2)))
    return out


def economics_check(wx, crops, params):
    """Replay at the station: 2008-2015 net returns (K-State benchmark) and long-run farm-level yields."""
    from .replay import Economics, replay_field
    rotations = inputs.load_rotations()
    field = {"awc_mm": params["awc_tribune_mm"]}
    bench = replay_field(field, wx, crops, rotations, params, Economics(), first_year=2008, last_year=2015)
    longrun = replay_field(field, wx, crops, rotations, params, Economics(), first_year=1996, last_year=2020)
    planning = {}
    for r in csv.DictReader(open(inputs.ROOT / "crops-economics" / "reference" / "costs.csv")):
        if r["planning_yield"] and r["yield_unit"] == "bu":
            planning.setdefault(r["cost_key"], []).append(float(r["planning_yield"]))
    return bench, longrun, planning


def write_report(wx, crops, par, params, data, county, eco):
    L = []
    L += ["# Engine validation", "",
          "Written by `python -m engine.validate`. Weather: gridMET pixel of the K-State Tribune station, 1994-2020.",
          "Measured values: K-State Southwest Research-Extension Center, Tribune (sources in `reference/` and",
          "`crops-economics/reference/evidence.md`). 1 bu/acre = 67.25 kg/ha (wheat) or 62.77 kg/ha (sorghum, corn).", ""]

    L += ["## 1. Water", "",
          "The five water parameters were chosen on this table alone (270 combinations, `engine/calibrate.py`); "
          "yields were not used. Measured: Schlegel, Haag, O'Brien 2016, 2008-2015.", "",
          "| Crop | Rotation | Fallow efficiency % (model / measured) | Water at planting mm | Crop water use mm |",
          "| :--- | :--- | ---: | ---: | ---: |"]
    mod = tribune.water_check(wx, crops, par)
    for (crop, rot), t in tribune.WATER_TARGETS.items():
        m = mod[(crop, rot)]
        L.append(f"| {crop} | {rot} | {m[0]:.0f} / {t[0]} | {m[2]:.0f} / {t[2]} | {m[3]:.0f} / {t[3]} |")
    w = params["water"]
    L += ["", f"Chosen: rain_eff {w['rain_eff']}, rain_min_mm {w['rain_min_mm']}, fallow_evap {w['fallow_evap']}, "
          f"wet_evap {w['wet_evap']}, fallow_dry_frac {w['fallow_dry_frac']}; soil capacity {par.awc_mm:.0f} mm (SSURGO, mean of the demo fields).", "",
          "Reading: crop water use is within 1-4% of the measurements for the three-year rotations and 22% low for wheat-fallow. "
          "The model cannot reproduce the high efficiency of the 14-month fallow of wheat-fallow (28% measured): "
          "it stores too little there, so **wheat-fallow is treated slightly unfairly** and wheat after a long fallow "
          "starts with less water than measured. Measured water is for an 8 ft profile, the model for 5 ft.", ""]

    L += ["## 2. Yields, year by year", "",
          "`published` = K-State yield-vs-ET function exactly as published, driven by modelled ET, nothing fitted to yields. "
          "`calibrated` = the model the replay uses (`engine/params.json`). R² here is 1 − SSE/SST of the prediction itself "
          "(it can be negative when the level is wrong); r² is the squared correlation.", "",
          "| Series | n | Measured mean | Published: mean, bias, r² | Calibrated: mean, RMSE, R², r² |",
          "| :--- | ---: | ---: | :--- | :--- |"]
    for name, d in data.items():
        o, p, c = np.array(d["obs"]), np.array(d["published"]), np.array(d["calibrated"])
        L.append(f"| {LABEL[name]} | {len(o)} | {o.mean():.0f} | {p.mean():.0f}, {p.mean() - o.mean():+.0f}, {np.corrcoef(o, p)[0, 1] ** 2:.2f} "
                 f"| {c.mean():.0f}, {np.sqrt(((c - o) ** 2).mean()):.0f}, {r2_of(o, c):.2f}, {np.corrcoef(o, c)[0, 1] ** 2:.2f} |")
    ym = params["yield_models"]
    L += ["", "Units: bu/acre. The calibrated models were fitted only on the two reference positions (wheat after fallow, "
          "sorghum after wheat), mean of the two series each:", "",
          "| Crop | Model (kg/ha) | n | R² | Leave-one-out R² |", "| :--- | :--- | ---: | ---: | ---: |"]
    for crop_id, m in ym.items():
        heat = f" {m['per_hot_day_kg_ha']:+.1f} × days ≥ 34 °C (flowering to maturity)" if m["per_hot_day_kg_ha"] else ""
        L.append(f"| {crop_id} | {m['intercept_kg_ha']:.0f} + {m['per_mm_et_kg_ha']:.2f} × ET mm{heat} | {m['n']} | {m['r2']:.2f} | {m['r2_leave_one_out']:.2f} |")
    # extra regressions, information only
    s = data["sorghum_wssf_first"]; w_ = data["wheat_wssf"]
    _, r_et, loo_et, _ = tribune.fit([s["et"]], s["obs"]); _, r_ty, loo_ty, _ = tribune.fit([s["et"], s["years"]], s["obs"])
    _, w_et, wloo_et, _ = tribune.fit([w_["et"]], w_["obs"]); _, w_h, wloo_h, _ = tribune.fit([w_["et"], w_["hot"]], w_["obs"])
    L += ["", "What the numbers say:", "",
          f"- **Sorghum is modelled usefully.** Modelled ET alone explains {r_et:.0%} of the measured variation of sorghum after wheat "
          f"(leave-one-out {loo_et:.0%}).",
          f"- **Sorghum yields rose over time for reasons the water model does not see.** Adding the calendar year lifts R² to {r_ty:.0%} "
          f"(leave-one-out {loo_ty:.0%}); measured sorghum after wheat rose from 73 bu/acre (1996-2007) to 101 (2008-2020), wheat did not. "
          "The replay uses the 1996-2020 average level, so it probably understates today's sorghum.",
          f"- **Wheat is modelled weakly.** ET explains {w_et:.0%} of wheat after fallow (leave-one-out {wloo_et:.0%}); "
          f"with heat days {w_h:.0%} (leave-one-out {wloo_h:.0%}). A single wheat year from the replay is a rough estimate. "
          "Known causes outside the model: winterkill (2015), stripe rust and wheat streak mosaic (2015-2017), hail, late freeze.",
          "- **The published function has the right pattern but the wrong level at this trial**: it is 10-20 bu/acre too low for wheat. "
          "That is why wheat and sorghum are calibrated.",
          "- Two independent measured series of the same crop in the same position agree with r² = 0.95, so the unexplained part is model "
          "and input error, not plot noise. K-State's own regressions on measured soil water and on-site rain reach r² = 0.83 (no-till, Stone and Schlegel 2006).", ""]

    L += ["## 3. Crop failures", "",
          "| Crop | Measured zero-yield years | Model's three lowest years (calibrated, bu/acre) |", "| :--- | :--- | :--- |"]
    for name in ("wheat_wssf", "sorghum_wssf_first"):
        d = data[name]
        zeros = [y for y, v in zip(d["years"], d["obs"]) if v == 0]
        low = sorted(zip(d["calibrated"], d["years"]))[:3]
        L.append(f"| {LABEL[name]} | {', '.join(map(str, zeros))} | {', '.join(f'{y} ({v:.0f})' for v, y in low)} |")
    L += [""]

    L += ["## 4. Rotation effects", "",
          "Does the water balance alone explain why a second crop yields less? Ratio of mean yields, common years.", "",
          "| Effect | Measured | From modelled water alone | Residual applied in the replay |", "| :--- | ---: | ---: | ---: |"]
    for key, v in params["rotation_residuals"].items():
        L.append(f"| {key} | {v['measured_ratio']:.2f} | {v['modelled_ratio']:.2f} | {v['residual_multiplier']:.2f} |")
    L += ["", "Less stored water explains about a third of the penalty of a second sorghum crop and about half of that of recrop wheat. "
          "The rest (weeds, disease, nitrogen, stand) is applied as a residual multiplier, so the water effect is not counted twice "
          "(`_double_counting_warning` in rotations.json).", ""]

    L += ["## 5. Level against county yields", "",
          "USDA NASS, Greeley County, non-irrigated, years with data since 1996. Model = replay yield at farm level "
          "(trial level × farm factor) with the station weather.", "",
          "| Crop | Years | County mean bu/acre | Model mean bu/acre | Farm factor | r² |", "| :--- | :--- | ---: | ---: | ---: | ---: |"]
    for c in county:
        L.append(f"| {c['crop']} ({c['rotation']}) | {c['first']}-{c['last']}, n={c['n']} | {c['county']:.0f} | {c['model']:.0f} | {c['factor']} | {c['r2']:.2f} |")
    L += ["", "Corn has no year-by-year trial series in `reference/`, so it uses the published K-State function without calibration, "
          "with the farm factor of sorghum (ASSUMPTION); the row above is its only check. Sunflower is not validated at all. "
          "County sorghum data end in 2005, before most of the yield rise at the trial, which explains part of the gap in that row.", ""]

    bench, longrun, planning = eco
    L += ["K-State farm budgets give a second, more recent anchor: their planning yields for south-west Kansas dryland, 2016-2027 "
          "(`costs.csv`), against the replay's farm-level mean at the station, 1996-2020.", "",
          "| Crop in rotation | K-State planning yield bu/acre | Replay mean bu/acre |", "| :--- | ---: | ---: |"]
    for label, key, rid, crop_id in (("Wheat in wheat-fallow", "wheat|W-F", "WF", "winter_wheat"),
                                     ("Wheat in three-year rotations", "wheat|W-S/C-F", "WSF", "winter_wheat"),
                                     ("Sorghum in wheat-sorghum-fallow", "sorghum|W-S-F", "WSF", "grain_sorghum"),
                                     ("Corn in wheat-corn-fallow", "corn|W-C-F", "WCF", "corn")):
        v = planning[key]
        L.append(f"| {label} | {min(v):.0f}-{max(v):.0f} | {to_bu_acre(crop_id, longrun['rotations'][rid]['crop_mean_kg_ha'][crop_id]):.0f} |")
    L += ["", "The replay sits between the two anchors: above the county averages of 1996-2018, at or below what K-State budgets "
          "plan for today.", ""]

    L += ["## 6. Economics benchmark", "",
          "Average net return 2008-2015 at the station, 2025 USD per acre per year, against the K-State large-scale study "
          "(Schlegel, Haag, O'Brien 2016; nominal dollars of its time, its own prices and costs, trial yields). "
          "Expect the order and the sign of the differences to match, not the dollars.", "",
          "| Rotation | Replay | K-State study |", "| :--- | ---: | :--- |"]
    kstate = {"WSF": "positive, below +6", "WF": "-18", "WCF": "below -35", "WSSF": "not in the study", "WWSF": "not in the study"}
    for rid in ("WSF", "WF", "WSSF", "WWSF", "WCF"):
        L.append(f"| {rid} | {bench['rotations'][rid]['summary']['mean']:+.0f} | {kstate[rid]} |")
    L += ["", "The order matches (wheat-sorghum-fallow first, wheat-fallow second, wheat-corn-fallow last). For the two rotations with a "
          "published number the replay is 10-20 USD/acre lower; it uses farm-level instead of trial yields and today's real costs for every year.", ""]

    L += ["## 7. Model variants tried", "",
          "| Variant | r² wheat after fallow | r² sorghum after wheat | Note |", "| :--- | ---: | ---: | :--- |",
          "| `scripts/water_balance_baseline.py` (each crop period separate, starting water guessed) | 0.44 | 0.63 | regression fitted to yields; two series only |",
          "| Single layer, continuous through the rotation, published yield function (this engine, water-calibrated) | "
          f"{np.corrcoef(data['wheat_wssf']['obs'], data['wheat_wssf']['published'])[0, 1] ** 2:.2f} | "
          f"{np.corrcoef(data['sorghum_wssf_first']['obs'], data['sorghum_wssf_first']['published'])[0, 1] ** 2:.2f} | seven series, nothing fitted to yields |",
          "| Two layers (FAO-56 dual coefficient, surface evaporation layer, curve-number runoff, snow), water-calibrated | 0.39 | 0.49 | "
          "better fallow efficiency, worse water at planting; not kept |", "",
          "Running the rotation continuously costs a little skill compared with the baseline, which restarted every crop from the same guessed "
          "soil water. We keep the continuous run because the replay needs the carry-over between crops: that is what makes rotations differ.", ""]

    L += ["## 8. What this means for the product", "",
          "- Trust the **comparison between rotations over many years** more than any single year.",
          "- Sorghum results are firmer than wheat results; corn and sunflower are the least certain.",
          "- Wheat-fallow is probably a little better than shown (section 1).",
          "- Not modelled: hail, disease, winterkill, weeds, nitrogen, planting failures, crop insurance.", ""]
    DOC.write_text("\n".join(L))


def write_figure(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, name, color in ((axes[0], "wheat_wssf", "#b8860b"), (axes[1], "sorghum_wssf_first", "#a0522d")):
        d = data[name]
        ax.plot(d["years"], d["obs"], "o-", color="#222222", lw=1.5, ms=4, label="Measured (K-State Tribune trial)")
        ax.plot(d["years"], d["calibrated"], "s--", color=color, lw=1.5, ms=4, label="Engine")
        r2 = np.corrcoef(d["obs"], d["calibrated"])[0, 1] ** 2
        ax.set_title(f"{LABEL[name].split(' (')[0]}: r² = {r2:.2f}", loc="left", fontsize=11)
        ax.set_ylabel("Yield, bu/acre"); ax.set_ylim(bottom=0); ax.grid(alpha=0.25)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Engine driven by gridded weather vs measured dryland yields, Tribune, Kansas", fontsize=12, x=0.01, ha="left")
    fig.tight_layout()
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, dpi=150)


def main():
    params = load_params()
    wx = inputs.load_weather(inputs.TRIBUNE_WEATHER)
    crops = inputs.load_crops()
    par = WaterParams(awc_mm=params["awc_tribune_mm"], **params["water"])
    data = collect(wx, crops, par, params)
    county = county_check(wx, crops, par, params)
    write_report(wx, crops, par, params, data, county, economics_check(wx, crops, params))
    write_figure(data)
    print(DOC.read_text())


if __name__ == "__main__":
    main()
