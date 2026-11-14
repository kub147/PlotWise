"""Turn a rotation (ordered list of phases, one per harvest year) into a day-by-day crop schedule.

Convention (same as crops-economics/reference/README.md): a phase belongs to the HARVEST year of its crop.
A summer crop of year y grows from plant_doy to harvest in year y. Winter wheat of year y is planted in the
autumn of year y-1. A fallow phase has no crop; the land simply waits for the next planting.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np

from .inputs import Crop, Weather



@dataclass
class Season:
    crop: str
    harvest_year: int
    phase_index: int
    start: int                 # day index of planting
    end: int                   # day index of the last growing day (inclusive)
    stage_bounds: tuple        # day offsets where development, mid, late start; and season length


@dataclass
class Schedule:
    kc: np.ndarray             # crop coefficient per day (FAO-56 single coefficient), 0 when no crop grows
    crop_of_day: list          # crop id or None
    season_of_day: np.ndarray  # index into seasons, -1 when no crop grows
    seasons: list
    phase_of_year: dict        # year -> (phase index, crop id or "fallow")


def kc_curve(crop: Crop) -> np.ndarray:
    """Daily crop coefficient from planting to harvest: FAO-56 four-stage curve."""
    l1, l2, l3, l4 = crop.stages
    out = np.empty(l1 + l2 + l3 + l4)
    out[:l1] = crop.kc_ini
    out[l1:l1 + l2] = np.linspace(crop.kc_ini, crop.kc_mid, l2, endpoint=False)
    out[l1 + l2:l1 + l2 + l3] = crop.kc_mid
    if l4:
        out[l1 + l2 + l3:] = np.linspace(crop.kc_mid, crop.kc_end, l4)
    return out


def _doy_date(year: int, doy: int) -> dt.date:
    return dt.date(year, 1, 1) + dt.timedelta(days=doy - 1)


def build_schedule(phases: list[str], offset: int, crops: dict[str, Crop], wx: Weather) -> Schedule:
    """Schedule for one rotation with phases[(year - offset) % n] harvested in each calendar year."""
    n_days, n = len(wx.dates), len(phases)
    kc = np.zeros(n_days)
    crop_of_day: list = [None] * n_days
    season_of_day = np.full(n_days, -1, dtype=int)
    seasons, phase_of_year = [], {}
    for year in range(wx.first_year, wx.last_date.year + 2):
        k = (year - offset) % n
        cid = phases[k]
        phase_of_year[year] = (k, cid)
        if cid == "fallow":
            continue
        crop = crops[cid]
        winter = crop.plant_doy > crop.harvest_doy          # planted the autumn before the harvest year
        plant = _doy_date(year - 1 if winter else year, crop.plant_doy)
        start = wx.index(plant)
        end = start + crop.season_days - 1
        if start < 0 or end >= n_days:
            continue                                         # season not fully inside the weather record
        if (season_of_day[start:end + 1] >= 0).any():
            raise ValueError(f"{cid} harvested {year} overlaps the previous crop: rotation {phases} is not feasible")
        l1, l2, l3, l4 = crop.stages
        seasons.append(Season(cid, year, k, start, end, (l1, l1 + l2, l1 + l2 + l3, crop.season_days)))
        kc[start:end + 1] = kc_curve(crop)
        season_of_day[start:end + 1] = len(seasons) - 1
        for i in range(start, end + 1):
            crop_of_day[i] = cid
    return Schedule(kc, crop_of_day, season_of_day, seasons, phase_of_year)
