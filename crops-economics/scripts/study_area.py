"""Read data/processed/counties.geojson (repo root) into {county code: {fips, name, lat, lon}}.

The county code, name and coordinates are found under common property names; without lat/lon
properties the centre of the geometry is used.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTIES = ROOT.parent / "data/processed/counties.geojson"

FIPS_KEYS = ("county_fips", "fips", "geoid", "fips_code", "countyfp", "county_code", "cntyfips")
NAME_KEYS = ("name", "county", "county_name", "namelsad")
LAT_KEYS = ("lat", "latitude", "y", "centroid_lat")
LON_KEYS = ("lon", "lng", "longitude", "x", "centroid_lon")


def _pick(props: dict, keys: tuple[str, ...]):
    low = {k.lower(): v for k, v in props.items()}
    for k in keys:
        if k in low and low[k] not in (None, ""):
            return low[k]
    return None


def _centre(geom: dict | None) -> tuple[float, float] | None:
    if not geom:
        return None
    if geom["type"] == "Point":
        return geom["coordinates"][0], geom["coordinates"][1]
    pts = []

    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c:
                walk(x)
    walk(geom["coordinates"])
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def load_counties(path: Path = COUNTIES) -> dict[str, dict]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    out = {}
    for f in data.get("features", []):
        p = f.get("properties", {})
        fips = _pick(p, FIPS_KEYS)
        if fips is None:
            raise KeyError(f"no county FIPS property in {path}; properties are {sorted(p)}")
        code = str(fips).strip().split(".")[0].zfill(3)
        code = code[-3:]
        lat, lon = _pick(p, LAT_KEYS), _pick(p, LON_KEYS)
        if lat is None or lon is None:
            c = _centre(f.get("geometry"))
            lon, lat = (c if c else (None, None))
        out[code] = {"fips": "20" + code, "name": str(_pick(p, NAME_KEYS) or "").title(),
                     "lat": float(lat) if lat is not None else None,
                     "lon": float(lon) if lon is not None else None}
    return out
