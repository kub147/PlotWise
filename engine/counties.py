"""County layer: yield level per county, replay of every county, comparison with what farmers do.

    python -m engine.counties        # -> engine/county_yield_factors.json, data/processed/results/counties.json

Why a yield level per county
    The yield-vs-ET models are calibrated at the Tribune trial. Year to year they follow county yields well across
    western Kansas, but their LEVEL rises with rainfall much faster than real farm yields do (at Hays the model gives
    about 130 bu/acre of dryland corn, the county averages about 70). So each county and crop gets one factor:

        factor = mean USDA NASS non-irrigated county yield / mean modelled trial-level yield, same years (1996+)

    The model still decides how yields vary from year to year and how much water a rotation leaves for the next crop;
    the county's own farm yields decide the average level. Sunflower (WSfF) is replayed but never named best: it is
    optional in rotations.json and its yield function is not validated. Wheat is compared with wheat after fallow (WF), sorghum
    with sorghum in WSF, corn with corn in WCF, sunflower (all practices, NASS has no dryland split) with WSfF.
    A county with fewer than MIN_YEARS of data borrows the median factor of its cost region.

Two yield scenarios
    county_average  the factor above. Costs come from K-State budgets, which assume a well-managed field (planning
                    yields 15-45% above the county averages), so this scenario charges a good manager's costs for an
                    average farm's yields; that favours fallow, the cheapest phase.
    well_managed    factor_well_managed = K-State planning yield of the budget used for costs / mean modelled
                    trial-level yield over the budget years (2016 onward). Costs and yields then belong together.
    The farmer picks the one that describes the field. Neither is a forecast.

Inputs: data/processed/counties.geojson (B), data/processed/weather/counties/<county_id>.csv (A),
crops-economics/reference/county_yields.csv and county_budget_regions.csv (C),
data/processed/county_field_rotations.json (B, fields classified from CDL 2018-2025).
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

import numpy as np

from . import inputs
from .replay import Economics, replay_field
from .yields import KG_HA_PER_BU_ACRE, load_params, to_bu_acre

COUNTIES_GEOJSON = inputs.ROOT / "data" / "processed" / "counties.geojson"
COUNTY_WEATHER = inputs.WEATHER_DIR / "counties"
COUNTY_YIELDS = inputs.ROOT / "crops-economics" / "reference" / "county_yields.csv"
BUDGET_REGIONS = inputs.ROOT / "crops-economics" / "reference" / "county_budget_regions.csv"
FIELD_ROTATIONS = inputs.ROOT / "data" / "processed" / "county_field_rotations.json"
FACTORS_JSON = Path(__file__).resolve().parent / "county_yield_factors.json"
OUT_JSON = inputs.RESULTS_DIR / "counties.json"
REPORT_MD = inputs.ROOT / "docs" / "engine-counties.md"

MIN_AWC_MM = 200          # below this the centroid square missed the cropland (docs/transect.md)
FALLBACK_AWC_MM = 280     # median of the county layer, as agreed with B
MIN_YEARS = 5
FIRST_YEAR = 1996
REFERENCE = {"winter_wheat": ("WF", "NON-IRRIGATED"), "grain_sorghum": ("WSF", "NON-IRRIGATED"),
             "corn": ("WCF", "NON-IRRIGATED"), "sunflower": ("WSfF", "ALL PRODUCTION PRACTICES")}
EXTEND = ("winter_wheat", "grain_sorghum")
EXTEND_MIN_OVERLAP = 5
EXTENDED: dict = {}       # filled by nass_yields(): which series were extended, and the ratio used
COSTS_CSV = inputs.ROOT / "crops-economics" / "reference" / "costs.csv"
# Budget whose planning yield defines the "well-managed field" level of each crop (same rotation position as REFERENCE)
BUDGET_KEY = {"winter_wheat": "wheat|W-F", "grain_sorghum": "sorghum|W-S-F", "corn": "corn|W-C-F", "sunflower": "sunflower|W-SF-F"}
BUDGET_FIRST_YEAR = 2016                       # first K-State budget year in costs.csv
KG_HA_PER_CWT_ACRE = 100 * 0.45359237 / 0.40468564
SCENARIOS = {
    "county_average": "Average dryland yield of the county (USDA NASS): all farms, good and poor fields, every rotation position",
    "well_managed": "Planning yield of the K-State budget whose costs are used: a well-managed field. The costs then match the yields",
}
MAIN = ("WF", "WSF", "WCF", "WSSF", "WWSF")   # rotations that can be "best"; optional WSfF is reported, not ranked
PRACTICE_LABEL = {"WF": "W-F", "WSF": "W-S-F", "WCF": "W-C-F"}   # engine id -> label in county_field_rotations.json


def load_counties() -> dict[str, dict]:
    regions = {r["county_fips"]: r["budget_region"] for r in csv.DictReader(open(BUDGET_REGIONS, encoding="utf-8"))}
    out = {}
    for f in json.load(open(COUNTIES_GEOJSON, encoding="utf-8"))["features"]:
        p = dict(f["properties"])
        p["awc_mm_layer"] = p["awc_mm"]
        if p["awc_mm"] < MIN_AWC_MM:
            p["awc_mm"] = FALLBACK_AWC_MM
        region = regions.get(p["county_fips"], "SW")
        p["budget_region"] = region if region in ("SW", "NW", "NC", "SC") else "SW"
        out[p["county_id"]] = p
    return out


def county_id_of_field(field_id: str) -> str:
    return field_id.split("-")[0]


def nass_yields() -> dict[tuple[str, str], dict[int, float]]:
    """(county_id, crop) -> {year: kg/ha} for the practice in REFERENCE.

    NASS stopped publishing dryland county yields around 2007 (sorghum) to 2016 (wheat), before most of the recent
    yield gains. For wheat and sorghum the series is extended to 2025 with the all-practices yield times the
    county's own median dryland / all-practices ratio (needs EXTEND_MIN_OVERLAP common years; across the 46 counties
    the ratio varies within a county by about 3% for wheat and 9% for sorghum). Corn is not extended: its
    all-practices yield is mostly irrigated corn.
    """
    raw: dict[tuple[str, str, str], dict[int, float]] = {}
    for r in csv.DictReader(open(COUNTY_YIELDS, encoding="utf-8")):
        if r["crop"] in REFERENCE and r["yield_kg_ha"]:
            raw.setdefault(("ks" + r["county_fips"][2:], r["crop"], r["practice"]), {})[int(r["year"])] = float(r["yield_kg_ha"])
    out: dict[tuple[str, str], dict[int, float]] = {}
    for (cid, crop, practice), series in raw.items():
        if practice != REFERENCE[crop][1]:
            continue
        series = dict(series)
        allp = raw.get((cid, crop, "ALL PRODUCTION PRACTICES"), {})
        if crop in EXTEND and allp:
            common = [y for y in series if y in allp and allp[y] > 0]
            if len(common) >= EXTEND_MIN_OVERLAP:
                ratio = float(np.median([series[y] / allp[y] for y in common]))
                for y, v in allp.items():
                    if y not in series:
                        series[y] = v * ratio
                EXTENDED[(cid, crop)] = dict(ratio=round(ratio, 3), years_added=sorted(y for y in allp if y not in raw[(cid, crop, practice)]))
        out[(cid, crop)] = series
    return out


def compute_factors(counties, crops, rotations, params, eco) -> dict:
    """County yield factors (trial-level model -> county farm level) and the check behind each."""
    nass = nass_yields()
    rot = {rid: rotations[rid] for rid in {v[0] for v in REFERENCE.values()}}
    ones = {c: 1.0 for c in REFERENCE}
    raw = {}
    for cid, c in counties.items():
        wx = inputs.load_weather(COUNTY_WEATHER / f"{cid}.csv")
        rep = replay_field(c, wx, crops, rot, params, eco, first_year=FIRST_YEAR, yield_factor=ones)
        raw[cid] = {}
        for crop, (rid, _) in REFERENCE.items():
            model = dict((y, v) for y, v in rep["rotations"][rid]["yields"][crop])
            obs = nass.get((cid, crop), {})
            years = sorted(y for y in obs if y in model)
            entry = dict(n_years=len(years), model_trial_mean_kg_ha=round(float(np.mean(list(model.values())))))
            if len(years) >= MIN_YEARS:
                o, m = np.array([obs[y] for y in years]), np.array([model[y] for y in years])
                entry.update(years=[years[0], years[-1]], nass_mean_kg_ha=round(float(o.mean())),
                             model_mean_same_years_kg_ha=round(float(m.mean())),
                             factor=round(float(o.mean() / m.mean()), 3) if m.mean() > 0 else None,
                             r2_year_to_year=round(float(np.corrcoef(o, m)[0, 1] ** 2), 2) if o.std() > 0 and m.std() > 0 else None)
            budget = planning_yields().get((c["budget_region"], BUDGET_KEY[crop]))
            recent = [v for y, v in model.items() if y >= BUDGET_FIRST_YEAR]
            if budget and recent and np.mean(recent) > 0:
                entry.update(planning_yield_kg_ha=round(budget["kg_ha"]), planning_budget=budget["label"],
                             model_trial_mean_budget_years_kg_ha=round(float(np.mean(recent))),
                             factor_well_managed=round(float(budget["kg_ha"] / np.mean(recent)), 3))
            if (cid, crop) in EXTENDED:
                entry["extended_with_all_practices"] = dict(EXTENDED[(cid, crop)], years_added=len(EXTENDED[(cid, crop)]["years_added"]))
            raw[cid][crop] = entry
    # borrow the regional median where a county has too few years
    for crop in REFERENCE:
        by_region: dict[str, list] = {}
        for cid, c in counties.items():
            f = raw[cid][crop].get("factor")
            if f:
                by_region.setdefault(c["budget_region"], []).append(f)
        all_f = [f for v in by_region.values() for f in v]
        for cid, c in counties.items():
            e = raw[cid][crop]
            if not e.get("factor"):
                pool = by_region.get(c["budget_region"]) or all_f
                e["factor"] = round(float(np.median(pool)), 3)
                e["borrowed"] = f"median of region {c['budget_region']} ({len(pool)} counties)"
            if not e.get("factor_well_managed"):
                e["factor_well_managed"] = e["factor"]
                e["well_managed_note"] = "no K-State planning yield for this crop and region; county average used"
    return raw


_PLANNING: dict = {}


def planning_yields() -> dict:
    """(region, cost_key) -> mean K-State planning yield 2016-2025 in kg/ha, and whether the budget is a proxy."""
    if not _PLANNING:
        acc: dict = {}
        for r in csv.DictReader(open(COSTS_CSV, encoding="utf-8")):
            if r["planning_yield"] and int(r["year"]) <= 2025:
                acc.setdefault((r["region"], r["cost_key"]), []).append((float(r["planning_yield"]), r["yield_unit"], r["proxy"]))
        for k, v in acc.items():
            unit = v[0][1]
            mean = float(np.mean([x[0] for x in v]))
            crop = {"wheat": "winter_wheat", "sorghum": "grain_sorghum", "corn": "corn", "sunflower": "sunflower"}[k[1].split("|")[0]]
            kg = mean * KG_HA_PER_CWT_ACRE if unit == "cwt" else mean * KG_HA_PER_BU_ACRE.get(crop, 62.77)
            proxy = any(x[2] not in ("", "false", "False", "0") for x in v)
            _PLANNING[k] = dict(kg_ha=kg, label=f"{k[0]} {k[1]}: {mean:.0f} {unit}/acre" + (" (proxy budget)" if proxy else ""))
    return _PLANNING


def best_of(rotations_out: dict, ids) -> str:
    return max(ids, key=lambda r: rotations_out[r]["mean"])


def _rotation_table(rep: dict) -> dict:
    rots = {}
    for rid, r in rep["rotations"].items():
        vals = np.array(list(r["net_year"].values()))
        rots[rid] = dict(mean=round(float(vals.mean()), 1),
                         mean_before_land_rent=r["summary"]["mean_before_land_rent"],
                         share_of_years_with_profit=round(float((vals > 0).mean()), 2),
                         share_of_years_covering_costs_before_rent=r["summary"]["share_of_years_covering_costs_before_rent"],
                         mean_of_worst_fifth=r["summary"]["mean_of_worst_fifth"],
                         mean_yield_bu_acre={k: round(to_bu_acre(k, v), 1) if k != "sunflower" else None
                                             for k, v in r["crop_mean_kg_ha"].items()},
                         mean_yield_kg_ha={k: round(v) for k, v in r["crop_mean_kg_ha"].items()})
    return rots


def _scenario_summary(rots: dict) -> dict:
    return dict(best_rotation=best_of(rots, [r for r in MAIN if r in rots]),
                best_of_three=best_of(rots, ("WF", "WSF", "WCF")),
                gain_replacing_fallow_usd_acre=round(rots["WSF"]["mean"] - rots["WF"]["mean"], 1),
                best_three_year_vs_wf_usd_acre=round(max(rots["WSF"]["mean"], rots["WCF"]["mean"]) - rots["WF"]["mean"], 1))


def _practice(p: dict, best3: str) -> dict:
    shares = {rid: p["rotations"][lab]["share_of_area"] for rid, lab in PRACTICE_LABEL.items()}
    common = max(shares, key=shares.get)
    fallow_based = sum(shares.values())
    return dict(fields=p["fields"], share_of_area=shares,
                share_no_fallow=p["rotations"]["no fallow"]["share_of_area"],
                share_moved_wf_to_three_year=p["rotations"]["W-F to 3-year"]["share_of_area"],
                most_common_of_three=common if fallow_based > 0 else None,
                three_rotations_share=round(fallow_based, 3),
                model_best_is_most_common=(best3 == common) if fallow_based >= 0.05 else None,
                model_best_share=shares[best3])


def replay_counties(counties, crops, rotations, params, eco, factors) -> dict:
    """Top level of each county = county_average scenario (unchanged format); `well_managed` holds the second one."""
    practice = json.load(open(FIELD_ROTATIONS, encoding="utf-8"))
    practice = practice.get("counties", practice)
    out = {}
    for cid, c in counties.items():
        wx = inputs.load_weather(COUNTY_WEATHER / f"{cid}.csv")
        res = {}
        for scen, key in (("county_average", "factor"), ("well_managed", "factor_well_managed")):
            yf = {crop: factors[cid][crop][key] for crop in REFERENCE}
            rep = replay_field(c, wx, crops, rotations, params, eco, first_year=FIRST_YEAR,
                               region=c["budget_region"], yield_factor=yf)
            rots = _rotation_table(rep)
            res[scen] = dict(_scenario_summary(rots), rotations=rots, yield_factor=yf)
        avg, wm = res["county_average"], res["well_managed"]
        entry = dict(
            name=c["name"], lon=c["lon"], lat=c["lat"], budget_region=c["budget_region"],
            awc_mm=c["awc_mm"], awc_replaced=c["awc_mm"] != c["awc_mm_layer"],
            precip_mm_per_year=round(float(wx.precip.sum() / len(wx.dates) * 365.25)),
            period=[rep["first_year"], rep["last_year"]],
            land_rent_usd_acre=avg["rotations"]["WF"]["mean_before_land_rent"] - avg["rotations"]["WF"]["mean"],
            **{k: avg[k] for k in ("best_rotation", "best_of_three", "gain_replacing_fallow_usd_acre", "best_three_year_vs_wf_usd_acre")},
            rotations=avg["rotations"], yield_factor=avg["yield_factor"],
            yield_factor_borrowed=[k for k in REFERENCE if factors[cid][k].get("borrowed")],
            well_managed=wm)
        entry["land_rent_usd_acre"] = round(entry["land_rent_usd_acre"], 1)
        p = practice.get(cid)
        if p:
            entry["practice"] = _practice(p, avg["best_of_three"])
            wm["practice_match"] = _practice(p, wm["best_of_three"])["model_best_is_most_common"]
        out[cid] = entry
    return out


def agreement(out: dict) -> dict:
    rows = [v for v in out.values() if v.get("practice") and v["practice"]["model_best_is_most_common"] is not None]
    n = len(rows)
    hits = sum(v["practice"]["model_best_is_most_common"] for v in rows)
    # chance level: always picking the rotation that is most common across all counties
    tot = {rid: sum(v["practice"]["share_of_area"][rid] for v in rows) for rid in PRACTICE_LABEL}
    naive = max(tot, key=tot.get)
    naive_hits = sum(v["practice"]["most_common_of_three"] == naive for v in rows)
    bands = {}
    for lo, hi, label in ((-102.1, -101.0, "102-101 W"), (-101.0, -100.0, "101-100 W"), (-100.0, -99.0, "100-99 W"), (-99.0, -98.3, "99-98.3 W")):
        sel = [v for v in rows if lo <= v["lon"] < hi]
        bands[label] = dict(counties=len(sel), matches=sum(v["practice"]["model_best_is_most_common"] for v in sel))
    wm_hits = sum(bool(v["well_managed"].get("practice_match")) for v in rows)
    for lo, hi, label in ((-102.1, -101.0, "102-101 W"), (-101.0, -100.0, "101-100 W"), (-100.0, -99.0, "100-99 W"), (-99.0, -98.3, "99-98.3 W")):
        bands[label]["matches_well_managed"] = sum(bool(v["well_managed"].get("practice_match")) for v in rows if lo <= v["lon"] < hi)
    return dict(counties_compared=n, model_matches_most_common=hits, model_matches_most_common_well_managed=wm_hits,
                by_longitude=bands, share=round(hits / n, 2) if n else None,
                naive_rule=f"always {naive}", naive_matches=naive_hits,
                note="Counties where WF, WSF and WCF together cover at least 5% of the classified field area. "
                     "Most common = largest share of area among the three; model = highest mean net return among the three.")


def _spearman(x, y) -> float:
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def choice_checks(out: dict) -> dict:
    """Does the model's preference between two rotations follow the share of farmers choosing them?"""
    res = {}
    for label, a, b in (("sorghum instead of fallow (WSF vs WF)", "WSF", "WF"), ("corn instead of sorghum (WCF vs WSF)", "WCF", "WSF")):
        rows = [v for v in out.values() if v.get("practice")
                and v["practice"]["share_of_area"][a] + v["practice"]["share_of_area"][b] >= 0.05]
        gain = [v["rotations"][a]["mean"] - v["rotations"][b]["mean"] for v in rows]
        gain_wm = [v["well_managed"]["rotations"][a]["mean"] - v["well_managed"]["rotations"][b]["mean"] for v in rows]
        share = [v["practice"]["share_of_area"][a] / (v["practice"]["share_of_area"][a] + v["practice"]["share_of_area"][b]) for v in rows]
        res[label] = dict(counties=len(rows), spearman=round(_spearman(gain, share), 2),
                          spearman_well_managed=round(_spearman(gain_wm, share), 2),
                          note=f"rank correlation between the model's gain of {a} over {b} and farmers' share of {a} among {a}+{b}")
    # did farmers leave fallow where the model sees the largest gain from leaving it?
    layer = {f["properties"]["county_id"]: f["properties"] for f in json.load(open(COUNTIES_GEOJSON, encoding="utf-8"))["features"]}
    ids = [cid for cid in out if cid in layer]
    gain = [out[c]["gain_replacing_fallow_usd_acre"] for c in ids]
    gain_wm = [out[c]["well_managed"]["gain_replacing_fallow_usd_acre"] for c in ids]
    drop = [layer[c]["fallow_share_2008"] - layer[c]["fallow_share_latest"] for c in ids]
    moved = [out[c]["practice"]["share_moved_wf_to_three_year"] if out[c].get("practice") else 0.0 for c in ids]
    rel_ids = [i for i, c in enumerate(ids) if layer[c]["fallow_share_2008"] >= 0.05]
    rel = [drop[i] / layer[ids[i]]["fallow_share_2008"] for i in rel_ids]
    res["leaving fallow since 2008"] = dict(
        counties=len(ids), spearman_gain_vs_drop_in_fallow_share=round(_spearman(gain, drop), 2),
        spearman_gain_vs_share_moved_wf_to_three_year=round(_spearman(gain, moved), 2),
        counties_relative=len(rel_ids),
        spearman_gain_vs_relative_drop=round(_spearman([gain[i] for i in rel_ids], rel), 2),
        spearman_gain_well_managed_vs_relative_drop=round(_spearman([gain_wm[i] for i in rel_ids], rel), 2),
        spearman_fallow_share_2008_vs_relative_drop=round(_spearman([layer[ids[i]]["fallow_share_2008"] for i in rel_ids], rel), 2),
        note="Fallow share of dryland cropland 2008 -> latest CDL year (counties.geojson) and fields that moved from "
             "wheat-fallow to a three-year rotation (county_field_rotations.json). A positive value would mean farmers "
             "left fallow where the model sees the largest gain.")
    return res


def write_report(factors: dict, summary: dict, params: dict) -> None:
    out = summary["counties"]
    L = ["# Engine across 46 western Kansas counties", "",
         "Written by `python -m engine.counties`. One point per county (centroid weather from A, soil from B, cost region from C), "
         "replayed 1996 onward. County results are indicative; the field results are the product.", "",
         "## 1. Yield level: the model needed a correction outside Tribune", "",
         "Modelled yields at farm level (Tribune trial-to-farm factors) against USDA NASS non-irrigated county yields, same years. "
         "Ratio > 1 means the model is too high.", "",
         "| Longitude | Counties | Wheat ratio | Sorghum ratio | Corn ratio | Median year-to-year r² (wheat / sorghum / corn) |",
         "| :--- | ---: | ---: | ---: | ---: | :--- |"]
    ff = params["farm_factor"]
    for lo, hi, lab in ((-102.1, -101.0, "102-101 W"), (-101.0, -100.0, "101-100 W"), (-100.0, -99.0, "100-99 W"), (-99.0, -98.3, "99-98.3 W")):
        sel = [cid for cid, v in out.items() if lo <= v["lon"] < hi]
        cells, r2s = [], []
        for crop in ("winter_wheat", "grain_sorghum", "corn"):
            e = [factors[c][crop] for c in sel if factors[c][crop].get("nass_mean_kg_ha")]
            cells.append(f"{np.mean([x['model_mean_same_years_kg_ha'] * ff[crop] / x['nass_mean_kg_ha'] for x in e]):.2f}" if e else "-")
            r = [x["r2_year_to_year"] for x in e if x.get("r2_year_to_year") is not None]
            r2s.append(f"{np.median(r):.2f}" if r else "-")
        L.append(f"| {lab} | {len(sel)} | {' | '.join(cells)} | {' / '.join(r2s)} |")
    L += ["", "The year-to-year pattern transfers reasonably well, least so for wheat in the east, but the level does not: "
          "the yield-vs-ET relation calibrated at Tribune turns the extra rain of the east into far more grain than farms there harvest "
          "(dryland corn about 130 bu/acre modelled at Hays against about 70 in the county). Each county and crop therefore gets one factor "
          "(`engine/county_yield_factors.json`): the mean NASS dryland yield divided by the mean modelled yield over the same years. "
          "The model keeps the year-to-year variation and the water carried between crops; the county's own farms set the average.", "",
          "NASS stopped publishing dryland county yields around 2007 (sorghum) and 2016 (wheat). For wheat and sorghum the series is "
          "extended to 2025 with the all-practices yield times the county's own dryland share (stable within a county: about 3% for "
          "wheat, 9% for sorghum). Corn is not extended because its all-practices yield is mostly irrigated corn.", "",
          "Known bias: the county sorghum average includes sorghum after sorghum and continuous sorghum, while the county wheat average "
          "is mostly wheat after fallow in the west. Sorghum's factor is therefore likely too low relative to wheat's, which works against "
          "wheat-sorghum-fallow.", ""]
    a = summary["agreement_with_practice"]
    c = summary["choice_checks"]
    L += ["## 2. Best rotation along the transect", "",
          "| Longitude | Counties | Mean gain of WSF over WF, USD/acre/yr | Model's best: WF / WSF / WCF / other |", "| :--- | ---: | ---: | :--- |"]
    for lo, hi, lab in ((-102.1, -101.0, "102-101 W"), (-101.0, -100.0, "101-100 W"), (-100.0, -99.0, "100-99 W"), (-99.0, -98.3, "99-98.3 W")):
        sel = [v for v in out.values() if lo <= v["lon"] < hi]
        cnt = {r: sum(v["best_rotation"] == r for v in sel) for r in ("WF", "WSF", "WCF")}
        L.append(f"| {lab} | {len(sel)} | {np.mean([v['gain_replacing_fallow_usd_acre'] for v in sel]):+.0f} | "
                 f"{cnt['WF']} / {cnt['WSF']} / {cnt['WCF']} / {len(sel) - sum(cnt.values())} |")
    lon = [v["lon"] for v in out.values()]; g = [v["gain_replacing_fallow_usd_acre"] for v in out.values()]
    L += ["", f"The gain from replacing fallow with sorghum rises from west to east (correlation with longitude {np.corrcoef(lon, g)[0, 1]:.2f}). "
          "All numbers include land rent; `mean_before_land_rent` in `results/counties.json` adds it back.", "",
          "## 3. Two yield levels: county average and well-managed field", "",
          "Costs come from K-State budgets, which assume a well-managed field. Their planning yields are well above the county "
          "averages the main scenario uses (2016-2024, model at county level / budget planning yield):", "",
          "| Budget region | Wheat after fallow | Sorghum in WSF | Corn in WCF |", "| :--- | ---: | ---: | ---: |"]
    for reg in ("SW", "NW", "NC", "SC"):
        cells = []
        for crop in ("winter_wheat", "grain_sorghum", "corn"):
            e = [factors[c][crop] for c, v in out.items() if v["budget_region"] == reg and factors[c][crop].get("factor_well_managed")
                 and not factors[c][crop].get("well_managed_note")]
            cells.append(f"{np.mean([x['factor'] / x['factor_well_managed'] for x in e]):.2f}" if e else "-")
        L.append(f"| {reg} ({sum(v['budget_region'] == reg for v in out.values())} counties) | {' | '.join(cells)} |")
    wm_bands = []
    for lo, hi, lab in ((-102.1, -101.0, "102-101 W"), (-101.0, -100.0, "101-100 W"), (-100.0, -99.0, "100-99 W"), (-99.0, -98.3, "99-98.3 W")):
        sel = [v for v in out.values() if lo <= v["lon"] < hi]
        cnt = {r: sum(v["well_managed"]["best_rotation"] == r for v in sel) for r in ("WF", "WSF", "WCF")}
        wm_bands.append(f"| {lab} | {len(sel)} | {np.mean([v['gain_replacing_fallow_usd_acre'] for v in sel]):+.0f} | "
                        f"{np.mean([v['well_managed']['gain_replacing_fallow_usd_acre'] for v in sel]):+.0f} | "
                        f"{cnt['WF']} / {cnt['WSF']} / {cnt['WCF']} / {len(sel) - sum(cnt.values())} |")
    L += ["", "So the main scenario charges a good manager's costs for an average farm's yields, which favours fallow, the cheapest "
          "phase. The second scenario, `well_managed`, sets each crop's level to the planning yield of the budget whose costs are used "
          "(`factor_well_managed` in `engine/county_yield_factors.json`). The farmer picks the one that describes the field.", "",
          "| Longitude | Counties | Gain of WSF over WF, county average | Same, well managed | Model's best, well managed: WF / WSF / WCF / other |",
          "| :--- | ---: | ---: | ---: | :--- |"] + wm_bands + ["",
          "Caveat: the north-central and south-central budgets are proxies from wetter central Kansas without fallow (C's note A8); "
          "their sorghum and corn planning yields (about 115 bu/acre) are probably too high for Hays, so the well-managed numbers "
          "there are optimistic.", "",
          "## 4. Independent check: what farmers actually do", "",
          "Farmers' rotations come from the crop sequence 2018-2025 of 31,660 fields (workstream B), so they were not used to build the model.", "",
          f"- **Corn or sorghum after wheat:** the model's preference follows farmers' choice, Spearman ρ = {c['corn instead of sorghum (WCF vs WSF)']['spearman']:.2f} "
          f"over {c['corn instead of sorghum (WCF vs WSF)']['counties']} counties. Corn is favoured in the cooler north-west, sorghum in the south and centre, as on the map.",
          f"- **Sorghum or fallow:** weak, ρ = {c['sorghum instead of fallow (WSF vs WF)']['spearman']:.2f} over {c['sorghum instead of fallow (WSF vs WF)']['counties']} counties. "
          "Strict wheat-fallow is rare everywhere (about 4% of field area), so farmers' share hardly varies; the model prefers wheat-fallow west of 101° W, "
          "where most farmers have already moved to three-year rotations. Reasons outside the model: crop insurance and government payments, "
          "spreading work and risk, weed control, and the sorghum bias above.",
          f"- **Leaving fallow since 2008: the model disagrees with farmers.** Rank correlation between the model's gain from replacing fallow "
          f"and the drop in fallow share 2008 → latest: ρ = {c['leaving fallow since 2008']['spearman_gain_vs_drop_in_fallow_share']:+.2f}; with the share of fields "
          f"that moved from wheat-fallow to a three-year rotation: ρ = {c['leaving fallow since 2008']['spearman_gain_vs_share_moved_wf_to_three_year']:+.2f} "
          f"({c['leaving fallow since 2008']['counties']} counties). Part of this is arithmetic: the west had the most fallow to lose. Measured as a relative drop "
          f"(drop / 2008 share, {c['leaving fallow since 2008']['counties_relative']} counties with at least 5% fallow in 2008) it is weaker but still negative: "
          f"ρ = {c['leaving fallow since 2008']['spearman_gain_vs_relative_drop']:+.2f} (well managed {c['leaving fallow since 2008']['spearman_gain_well_managed_vs_relative_drop']:+.2f}). "
          "Farmers in the dry west cut their fallow by about 30%, those near Hays by under 10%; the model sees the opposite gradient. "
          "The east had little fallow to leave. Where the model sees a gain, fallow is lower today (17.5% against 22% of cropland), but that is "
          "explained by rainfall alone. Likely reasons the model misses: better water storage under modern no-till, the rise of sorghum yields "
          "since 2008 (one constant factor averages old and new years), insurance and payments, and the sorghum bias above.",
          f"- **Most common rotation of the three = model's best:** {a['model_matches_most_common']} of {a['counties_compared']} counties "
          f"with county-average yields, {a['model_matches_most_common_well_managed']} with well-managed yields "
          f"(always guessing WSF: {a['naive_matches']}). The well-managed scenario agrees more often mainly because it names WSF almost "
          "everywhere, which is what most farmers grow; it does not explain where farmers left fallow (point above). By longitude, county average: " + ", ".join(f"{k} {v['matches']}/{v['counties']}" for k, v in a["by_longitude"].items()) + ".", "",
          "Reading: the model agrees with farmers on where corn and where sorghum fits. Whether replacing fallow pays depends above all on how "
          "well the field yields: with county-average yields fallow wins in the west, with the yields the K-State budgets assume sorghum wins "
          "almost everywhere. Neither scenario explains why the far west has been leaving fallow fastest; that is where local knowledge "
          "(no-till water storage, insurance, workload) beats the model.", "",
          "## 5. Inputs and assumptions", "",
          f"- Soil: SSURGO at the centroid; where below {MIN_AWC_MM} mm (the 2 km square missed the cropland) {FALLBACK_AWC_MM} mm is used "
          f"({sum(v['awc_replaced'] for v in out.values())} counties).",
          "- Costs: K-State budgets of the county's region (`county_budget_regions.csv`; north-central and south-central budgets are proxies without fallow, C's A8).",
          "- Sunflower (WSfF) is replayed but never named best: optional rotation, yield function not validated.",
          "- Factors with fewer than 5 years of county data borrow the median of the cost region: " +
          ", ".join(f"{out[cid]['name']} ({', '.join(v['yield_factor_borrowed'])})" for cid, v in out.items() if v["yield_factor_borrowed"]) + "."]
    REPORT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    params, crops, rotations, eco = load_params(), inputs.load_crops(), inputs.load_rotations(), Economics()
    counties = load_counties()
    factors = compute_factors(counties, crops, rotations, params, eco)
    FACTORS_JSON.write_text(json.dumps(dict(
        _about="Written by python -m engine.counties. factor = mean NASS non-irrigated county yield / mean modelled "
               "trial-level yield over the same years. Multiply a trial-level yield by it to get the county farm level.",
        reference=REFERENCE, min_years=MIN_YEARS, counties=factors), indent=1), encoding="utf-8")
    out = replay_counties(counties, crops, rotations, params, eco, factors)
    summary = dict(
        generated=dt.date.today().isoformat(),
        units="net returns: 2025 USD per acre per year over the whole rotation, fallow acres included; K-State budget "
              "of the county's region with land rent; insurance and government payments excluded. mean_before_land_rent "
              "adds the region's rent back (nearly the same for every rotation of a county, within a few dollars)",
        yield_level="Model yields scaled per county and crop to the mean USDA NASS non-irrigated county yield (engine/county_yield_factors.json)",
        caution="The county center is not a field: weather and soil at one point stand for the whole county. Indicative only.",
        agreement_with_practice=agreement(out),
        choice_checks=choice_checks(out),
        counties=out)
    OUT_JSON.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    write_report(factors, summary, params)
    a = summary["agreement_with_practice"]
    print(f"model best of WF/WSF/WCF = most common in practice: {a['model_matches_most_common']}/{a['counties_compared']} "
          f"(naive '{a['naive_rule']}': {a['naive_matches']})")
    for cid, v in sorted(out.items(), key=lambda kv: kv[1]["lon"]):
        r = v["rotations"]
        pr = v.get("practice", {})
        print(f"{v['name'][:11]:11s} {v['lon']:7.2f} {v['budget_region']} P{v['precip_mm_per_year']:4d} "
              f"WF {r['WF']['mean']:+6.0f} WSF {r['WSF']['mean']:+6.0f} WCF {r['WCF']['mean']:+6.0f} WSSF {r['WSSF']['mean']:+6.0f} "
              f"best {v['best_rotation']:5s} best3 {v['best_of_three']:4s} | practice {pr.get('most_common_of_three')} "
              f"{pr.get('share_of_area')} match {pr.get('model_best_is_most_common')}")
    print("written", FACTORS_JSON, OUT_JSON, REPORT_MD)


if __name__ == "__main__":
    main()
