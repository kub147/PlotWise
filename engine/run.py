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
from .scoring import CRITERIA, DEFAULT_WEIGHTS, SCALES, rank, scores_for, weight_sensitivity
from .yields import load_params

ENGINE_GAPS = ["Stored soil water on this field is modelled from gridded weather, not measured",
               "Yields are long-run estimates; a single year can be far off, wheat more than sorghum (docs/engine-validation.md)"]


def dry_years_of(field_id: str) -> list[int]:
    path = inputs.CLIMATE_DIR / f"{field_id}.json"
    if not path.exists():
        return []
    return [int(y) for y, t in json.load(open(path)).get("year_types", {}).items() if t == "dry"]


def build_result(field: dict, wx, crops, rotations, params, eco) -> dict:
    rep = replay_field(field, wx, crops, rotations, params, eco)
    dry = [y for y in dry_years_of(field["field_id"]) if rep["first_year"] <= y <= rep["last_year"]]
    current = ROTATION_OF_LABEL.get(field.get("current_rotation", ""))
    scores, dry_mean = {}, {}
    for rid, r in rep["rotations"].items():
        scores[rid], dry_mean[rid] = scores_for(r, dry)
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
        units={"yield": "kg/ha at farm level (trial level x farm factor)",
               "net_return": "2025 USD per acre per year, averaged over the whole rotation, fallow acres included; "
                             "actual Kansas price of each harvest year; crop insurance and government payments excluded",
               "scores": "0-1 on fixed scales, see scoring_scales"},
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
        farm_factor=params["farm_factor"],
        assumptions=[
            "Every phase of a rotation is present every year (land split evenly between phases)",
            "Costs before 2016 equal the mean real 2016-2026 K-State budget cost (crops-economics/HANDOVER.md, A2)",
            "Corn and sunflower: K-State yield function as published, farm factor assumed equal to sorghum; not validated year by year",
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
        path.write_text(json.dumps(res, indent=1))
        top = res["ranking_sensitivity"]
        print(f"{fid}: current {res['current_rotation']}, default ranking {res['default_ranking']}, "
              f"first under random weights {top['share_of_wins']}")
        for r in res["rotations"]:
            s = r["summary"]
            print(f"   {r['id']:5s} mean {s['mean']:7.1f}  dry years {s['mean_in_dry_years']:7.1f}  worst {s['worst']:7.1f} ({s['worst_year']})  "
                  f"loss years {s['share_of_years_with_loss']:.2f}  scores {r['scores']}")


if __name__ == "__main__":
    main(sys.argv[1:])
