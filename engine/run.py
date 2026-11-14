"""Run the rotation replay for the demo fields and write data/processed/results/<field_id>.json.

    python -m engine.run                 # all fields in data/processed/fields.geojson
    python -m engine.run ks071-001       # one field
"""
from __future__ import annotations

import datetime as dt
import json
import sys

from . import inputs
from .replay import ROTATION_OF_LABEL, Economics, replay_field
from .scoring import MONEY_REFERENCE, CRITERIA, DEFAULT_WEIGHTS, SCALES, rank, scores_for, weight_sensitivity
from .counties import SCENARIOS
from .yields import load_params

ENGINE_GAPS = ["Stored soil water on this field is modelled from gridded weather, not measured",
               "Yields are long-run estimates; a single year can be far off, wheat more than sorghum (docs/engine-validation.md)"]


def dry_years_of(field_id: str) -> list[int]:
    path = inputs.CLIMATE_DIR / f"{field_id}.json"
    if not path.exists():
        return []
    return [int(y) for y, t in json.load(open(path, encoding="utf-8")).get("year_types", {}).items() if t == "dry"]


def field_context(field_id: str) -> tuple[str, dict | None, str, dict | None]:
    """Cost region, county yield factors (county average, well managed) of a field; county = field_id prefix."""
    from .counties import FACTORS_JSON, load_counties
    cid = field_id.split("-")[0]
    region = load_counties().get(cid, {}).get("budget_region", "SW")
    if FACTORS_JSON.exists():
        f = json.load(open(FACTORS_JSON, encoding="utf-8"))["counties"].get(cid)
        if f:
            return (region, {crop: v["factor"] for crop, v in f.items()}, cid,
                    {crop: v.get("factor_well_managed", v["factor"]) for crop, v in f.items()})
    print(f"WARNING: no county yield factors for {cid}: run `python -m engine.counties` first. "
          f"Using the Tribune trial-to-farm factors, which are too high away from Tribune.")
    return region, None, cid, None


def scenario_view(rep: dict, dry: list[int], current: str | None) -> dict:
    """Per-rotation numbers of one yield scenario, in the same keys as the main rotation records."""
    scores, rows = {}, []
    for rid, r in rep["rotations"].items():
        scores[rid], dry_mean = scores_for(r, dry, rep["rotations"].get(MONEY_REFERENCE))
        summary = dict(r["summary"], mean_in_dry_years=round(dry_mean, 1))
        if current in rep["rotations"]:
            cur = rep["rotations"][current]["net_year"]
            diff = [r["net_year"][y] - cur[y] for y in r["years"]]
            summary["mean_vs_current"] = round(sum(diff) / len(diff), 1)
            summary["share_of_years_better_than_current"] = round(sum(d > 0 for d in diff) / len(diff), 2) if rid != current else None
        rows.append(dict(id=rid, yields_kg_ha=r["yields"],
                         mean_yield_kg_ha={c: round(v) for c, v in r["crop_mean_kg_ha"].items()},
                         net_return_usd_acre=[[y, round(r["net_year"][y], 1)] for y in r["years"]],
                         summary=summary, indicators=r["indicators"], scores=scores[rid]))
    return dict(yield_factor=rep["yield_factor"], rotations=rows,
                default_ranking=rank(scores, DEFAULT_WEIGHTS), ranking_sensitivity=weight_sensitivity(scores))


def build_result(field: dict, wx, crops, rotations, params, eco) -> dict:
    region, yf, county, yf_wm = field_context(field["field_id"])
    rep = replay_field(field, wx, crops, rotations, params, eco, region=region, yield_factor=yf)
    rep_wm = replay_field(field, wx, crops, rotations, params, eco, region=region, yield_factor=yf_wm) if yf_wm else None
    dry = [y for y in dry_years_of(field["field_id"]) if rep["first_year"] <= y <= rep["last_year"]]
    current = ROTATION_OF_LABEL.get(field.get("current_rotation", ""))
    scores, dry_mean = {}, {}
    for rid, r in rep["rotations"].items():
        scores[rid], dry_mean[rid] = scores_for(r, dry, rep["rotations"].get(MONEY_REFERENCE))
    out_rot = []
    for rid, r in rep["rotations"].items():
        rot = rotations[rid]
        summary = dict(r["summary"], mean_in_dry_years=round(dry_mean[rid], 1))
        if current in rep["rotations"]:
            cur = rep["rotations"][current]["net_year"]
            diff = [r["net_year"][y] - cur[y] for y in r["years"]]
            summary["mean_vs_current"] = round(sum(diff) / len(diff), 1)
            summary["share_of_years_better_than_current"] = round(sum(d > 0 for d in diff) / len(diff), 2) if rid != current else None
        out_rot.append(dict(
            id=rid, name=rot["name"], phases=rot["phases"], status=rot.get("status", "main"),
            is_current=rid == current,
            yields_kg_ha=r["yields"],
            mean_yield_kg_ha={c: round(v) for c, v in r["crop_mean_kg_ha"].items()},
            yield_method=r["yield_methods"],
            net_return_usd_acre=[[y, round(r["net_year"][y], 1)] for y in r["years"]],
            summary=summary, indicators=r["indicators"], scores=scores[rid],
            why=rot["why"], benefits=rot.get("benefits", []), risks=rot.get("risks", []),
            evidence=rot.get("evidence", []), gaps=rot.get("gaps", []) + ENGINE_GAPS,
            check_locally=rot.get("check_locally", [])))
    return dict(
        field_id=field["field_id"], generated=dt.date.today().isoformat(),
        period=[rep["first_year"], rep["last_year"]],
        site=field.get("site"), county_id=county, cost_region=region,
        yield_factor=rep["yield_factor"],
        yield_factor_source="engine/county_yield_factors.json: model scaled to the mean USDA NASS dryland yield of the county" if yf
                            else "params.json farm_factor (Tribune trial to farm)",
        units={"yield": "kg/ha at farm level (trial-level model x county yield factor)",
               "net_return": "2025 USD per acre per year, averaged over the whole rotation, fallow acres included; "
                             "actual Kansas price of each harvest year; K-State budget of the field's cost region, land rent included; "
                             "crop insurance and government payments excluded. mean_before_land_rent adds the region's rent back "
                             "(nearly the same for every rotation of a region, within a few dollars)",
               "scores": "0-1 on fixed scales, see scoring_scales"},
        yield_scenario="county_average",
        yield_scenarios=dict(
            _about="The main rotation records above use county_average. well_managed repeats the per-rotation numbers "
                   "with the yield level of the K-State budgets whose costs are used; the app can swap them in. "
                   "Description of each: engine/counties.py SCENARIOS.",
            county_average=SCENARIOS["county_average"],
            well_managed=dict(scenario_view(rep_wm, dry, current), description=SCENARIOS["well_managed"]) if rep_wm else None),
        current_rotation=current,
        current_rotation_note=None if current else f"'{field.get('current_rotation')}' is not one of the fixed rotations the engine replays",
        soil=dict(awc_mm=field["awc_mm"], source="SSURGO, 0-150 cm (fields.geojson)"),
        dry_years=dry,
        dry_years_source="year_types in data/processed/climate/<field_id>.json (workstream A)",
        rotations=out_rot,
        rotations_not_modelled=rep["skipped"],
        default_weights=DEFAULT_WEIGHTS,
        default_ranking=rank(scores, DEFAULT_WEIGHTS),
        ranking_sensitivity=weight_sensitivity(scores),
        scoring_scales={c: dict(zero_at=SCALES[c][0], one_at=SCALES[c][1]) for c in CRITERIA},
        scoring_note="income and dry_year_safety: net return minus that of wheat-fallow (WF) on this field and scenario, USD/acre/yr",
        farm_factor=params["farm_factor"],
        assumptions=[
            "Every phase of a rotation is present every year (land split evenly between phases)",
            "Costs before 2016 equal the mean real 2016-2026 K-State budget cost (crops-economics/HANDOVER.md, A2)",
            "Average yield level of each crop = mean USDA NASS dryland yield of the county (1996 onward); the model supplies the year-to-year variation. "
            "Costs come from K-State budgets for a well-managed field, so this main scenario favours fallow; see yield_scenarios.well_managed",
            "Corn and sunflower have no trial calibration; their level comes only from county yields. Corn at Hays is the least certain number",
            "Sorghum at the 1996-2020 average yield level; measured trial yields rose by about 2 bu/acre per year, so today's sorghum is probably understated",
            "The model stores less water in a 14-month fallow than measured at Tribune, so wheat-fallow is probably somewhat better than shown",
            "Scores use fixed scales chosen by the team; they are value judgements",
            "Differences of a few dollars per acre between rotations are inside the model's error"],
        validation="docs/engine-validation.md")


def main(argv: list[str]) -> None:
    params, crops, rotations = load_params(), inputs.load_crops(), inputs.load_rotations()
    fields, eco = inputs.load_fields(), Economics()
    inputs.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for fid in (argv or list(fields)):
        wx = inputs.load_weather(inputs.WEATHER_DIR / f"{fid}.csv")
        res = build_result(fields[fid], wx, crops, rotations, params, eco)
        path = inputs.RESULTS_DIR / f"{fid}.json"
        path.write_text(json.dumps(res, indent=1), encoding="utf-8")
        top = res["ranking_sensitivity"]
        print(f"{fid}: current {res['current_rotation']}, default ranking {res['default_ranking']}, "
              f"first under random weights {top['share_of_wins']}")
        for r in res["rotations"]:
            s = r["summary"]
            print(f"   {r['id']:5s} mean {s['mean']:7.1f}  dry years {s['mean_in_dry_years']:7.1f}  worst {s['worst']:7.1f} ({s['worst_year']})  "
                  f"loss years {s['share_of_years_with_loss']:.2f}  scores {r['scores']}")


if __name__ == "__main__":
    main(sys.argv[1:])
