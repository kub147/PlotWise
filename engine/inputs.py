"""Loaders. Every path is relative to the repository root, so the engine runs from anywhere."""
from __future__ import annotations

import csv
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CROPS_CSV = ROOT / "crops-economics" / "reference" / "crops.csv"
ROTATIONS_JSON = ROOT / "crops-economics" / "reference" / "rotations.json"
TARGETS_CSV = ROOT / "crops-economics" / "reference" / "calibration_targets.csv"
FIELDS_GEOJSON = ROOT / "data" / "processed" / "fields.geojson"
WEATHER_DIR = ROOT / "data" / "processed" / "weather"
CLIMATE_DIR = ROOT / "data" / "processed" / "climate"
RESULTS_DIR = ROOT / "data" / "processed" / "results"
TRIBUNE_YIELDS = ROOT / "reference" / "kstate_tribune_rotation_yields.csv"
TRIBUNE_WEATHER = ROOT / "engine" / "validation" / "tribune_station_gridmet.csv"


@dataclass
class Weather:
    dates: list            # datetime.date, daily, no gaps
    precip: np.ndarray     # mm
    eto: np.ndarray        # mm, grass reference ET
    tmax: np.ndarray       # deg C
    tmin: np.ndarray       # deg C

    def index(self, d: dt.date) -> int:
        return (d - self.dates[0]).days

    @property
    def first_year(self) -> int:
        return self.dates[0].year

    @property
    def last_date(self) -> dt.date:
        return self.dates[-1]


def load_weather(path: str | Path) -> Weather:
    """Read a weather CSV in the work-plan format (date, precip_mm, tmax_c, tmin_c, eto_mm, ...)."""
    dates, p, e, tx, tn = [], [], [], [], []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            dates.append(dt.date.fromisoformat(r["date"]))
            p.append(float(r["precip_mm"])); e.append(float(r["eto_mm"]))
            tx.append(float(r["tmax_c"])); tn.append(float(r["tmin_c"]))
    gaps = [i for i in range(1, len(dates)) if (dates[i] - dates[i - 1]).days != 1]
    if gaps:
        raise ValueError(f"{path}: weather has gaps, first at {dates[gaps[0]]}")
    return Weather(dates, np.array(p), np.array(e), np.array(tx), np.array(tn))


def gridmet_cache_to_csv(cache_json: str | Path, out_csv: str | Path) -> None:
    """Convert the cache written by scripts/water_balance_baseline.py into the work-plan CSV format."""
    raw = json.load(open(cache_json, encoding="utf-8"))
    rows = []
    for k, (pr, tx, tn, eto) in raw.items():
        d = dt.datetime.fromtimestamp(int(k) / 1000, dt.timezone.utc).date()
        rows.append((d, pr or 0.0, (tx or 273.15) - 273.15, (tn or 273.15) - 273.15, eto or 0.0))
    rows.sort()
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "precip_mm", "tmax_c", "tmin_c", "eto_mm"])
        for d, pr, tx, tn, eto in rows:
            w.writerow([d.isoformat(), round(pr, 2), round(tx, 2), round(tn, 2), round(eto, 2)])


@dataclass
class Crop:
    id: str
    name: str
    status: str
    plant_doy: int
    harvest_doy: int
    stages: tuple            # (initial, development, mid, late) days
    kc_ini: float
    kc_mid: float
    kc_end: float
    root_depth_m: float
    p: float                 # depletion fraction before stress (FAO-56 Table 22)
    threshold_et_mm: float | None
    slope_kg_ha_mm: float | None
    slope_longterm_kg_ha_mm: float | None
    max_et_mm: float | None
    max_yield_kg_ha: float | None
    bushel_kg: float | None
    residue_class: str

    @property
    def season_days(self) -> int:
        return sum(self.stages)

    @property
    def has_yield_function(self) -> bool:
        return self.threshold_et_mm is not None and self.slope_kg_ha_mm is not None


def _f(x):
    return float(x) if x not in ("", None) else None


def load_crops(path: str | Path = CROPS_CSV) -> dict[str, Crop]:
    out = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["crop"] == "fallow":
                continue
            out[r["crop"]] = Crop(
                id=r["crop"], name=r["name"], status=r["status"],
                plant_doy=int(r["plant_doy"]), harvest_doy=int(r["harvest_doy"]),
                stages=tuple(int(x) for x in r["stage_lengths_days"].split("/")),
                kc_ini=float(r["kc_ini"]), kc_mid=float(r["kc_mid"]), kc_end=float(r["kc_end"]),
                root_depth_m=float(r["root_depth_m"]), p=float(r["depletion_fraction_p"]),
                threshold_et_mm=_f(r["threshold_et_mm"]), slope_kg_ha_mm=_f(r["yield_per_mm_kg_ha"]),
                slope_longterm_kg_ha_mm=_f(r["yield_per_mm_longterm_kg_ha"]),
                max_et_mm=_f(r["max_et_mm"]), max_yield_kg_ha=_f(r["max_yield_kg_ha"]),
                bushel_kg=_f(r["bushel_kg"]), residue_class=r["residue_class"])
    return out


def load_rotations(path: str | Path = ROTATIONS_JSON) -> dict[str, dict]:
    return {r["id"]: r for r in json.load(open(path, encoding="utf-8"))["rotations"]}


def load_fields(path: str | Path = FIELDS_GEOJSON) -> dict[str, dict]:
    return {f["properties"]["field_id"]: f["properties"] for f in json.load(open(path, encoding="utf-8"))["features"]}


def load_tribune_yields(path: str | Path = TRIBUNE_YIELDS) -> dict[str, dict[int, float]]:
    """Measured yields, bu/acre: series name -> {harvest year: yield}."""
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(l for l in f if not l.startswith("#")))
    out: dict[str, dict[int, float]] = {}
    for r in rows:
        for k, v in r.items():
            if k != "year" and v != "":
                out.setdefault(k, {})[int(r["year"])] = float(v)
    return out
