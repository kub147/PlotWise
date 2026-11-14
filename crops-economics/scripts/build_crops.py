"""Build reference/crops.csv: one row per crop, every number with its source.

All conversions are done here (inches -> mm, bu/acre -> kg/ha) so they can be audited.
Units inside the pipeline are metric (work plan, "Files we exchange").

Sources (IDs refer to reference/evidence.md):
  E17  Stone, Schlegel, Khan, Klocke, Aiken (2006), Water supply: yield relationships..., Table 1
       (threshold ET, yield per inch of ET, long-term slope, maximum ET) - also reference/kstate_yield_vs_et.csv
  E23  FAO-56 (Allen et al. 1998) Table 12: Kc ini / mid / end
  E24  FAO-56 Table 11: lengths of crop development stages
  E25  FAO-56 Table 22: maximum effective rooting depth and depletion fraction p
  E29  USDA standard bushel weights

Crop calendar (plant_doy, stage lengths): FAO-56 gives generic stage lengths, not west-central Kansas.
Values below are marked ASSUMPTION until replaced by derive_crop_calendar.py (NASS Kansas crop progress)
and checked against field NDVI (workstream B).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from units import BUSHEL_KG, INCH_MM, LB_KG, bu_acre_to_kg_ha, lb_acre_to_kg_ha  

ROOT = Path(__file__).resolve().parent.parent

OUT = ROOT / "reference/crops.csv"
CALENDAR = ROOT / "reference/crop_calendar_ks.csv"  


STONE = {
    "winter_wheat": (10.0, 6.0, 4.6, 24.0, "bu"),
    "grain_sorghum": (6.9, 12.2, 9.4, 21.0, "bu"),
    "corn": (10.9, 16.9, 13.3, 25.0, "bu"),
    "sunflower": (5.4, 218.0, 150.0, 22.0, "lb"),
}
BUSHEL_CROP = {"winter_wheat": "wheat", "grain_sorghum": "sorghum", "corn": "corn"}


EXTRA_BUSHEL_LB = {"proso_millet": 50.0, "field_pea": 60.0}

CROPS = [
    dict(crop="winter_wheat", name="Winter wheat", plant_doy=268, stages=(171, 47, 40, 21),
         kc=(0.4, 1.15, 0.30), root=1.65, p=0.55, residue="high", fixes_n=False, status="modelled",
         cal_note="planted ~25 Sep, harvested ~1 Jul next year; initial stage includes winter dormancy "
                  "(FAO-56 Table 11 note 2); Kc ini 0.4 'with frozen soils', Kc end 0.30 within FAO range "
                  "0.25-0.4"),
    dict(crop="grain_sorghum", name="Grain sorghum", plant_doy=152, stages=(20, 35, 40, 30),
         kc=(0.3, 1.05, 0.55), root=1.5, p=0.55, residue="high", fixes_n=False, status="modelled",
         cal_note="planted ~1 Jun; stage lengths FAO-56 Table 11 'USA, May/June'; Kc mid 1.05 = middle of "
                  "FAO range 1.00-1.10; Kc ini 0.3 = FAO cereals"),
    dict(crop="corn", name="Corn (grain)", plant_doy=121, stages=(30, 40, 50, 30),
         kc=(0.3, 1.20, 0.35), root=1.35, p=0.55, residue="high", fixes_n=False, status="modelled",
         cal_note="planted ~1 May; stage lengths FAO-56 Table 11 'April, Spain/Calif.'; Kc end 0.35 for grain "
                  "dried in the field (FAO range 0.60-0.35)"),
    dict(crop="sunflower", name="Sunflower (oil)", plant_doy=161, stages=(25, 35, 45, 25),
         kc=(0.35, 1.05, 0.35), root=1.15, p=0.45, residue="low", fixes_n=False, status="modelled",
         cal_note="planted ~10 Jun; stage lengths FAO-56 Table 11 'April/May, Medit./California'; Kc mid "
                  "1.05 within FAO range 1.0-1.15; Kc ini 0.35 = FAO oil crops"),
    dict(crop="proso_millet", name="Proso millet", plant_doy=161, stages=(15, 25, 40, 25),
         kc=(0.3, 1.00, 0.30), root=1.5, p=0.55, residue="medium", fixes_n=False, status="not_modelled",
         cal_note="stage lengths FAO-56 Table 11 'June, Pakistan' (generic millet). No Kansas yield-water "
                  "function found: yield not modelled"),
    dict(crop="spring_triticale_forage", name="Spring triticale (forage)", plant_doy=74, stages=(20, 30, 35, 0),
         kc=(0.3, 1.15, 1.15), root=1.25, p=0.55, residue="low", fixes_n=False, status="ASSUMPTION",
         cal_note="planted ~15 Mar, cut for hay at heading ~8 Jun, so no late stage and Kc end = Kc mid "
                  "(water use stops at cutting). Kc from FAO-56 small grains; root depth = middle of FAO "
                  "spring small-grain range 1.0-1.5 m. Forage yield needs its own function (see gaps)"),
    dict(crop="field_pea", name="Field pea (dry)", plant_doy=79, stages=(35, 25, 30, 20),
         kc=(0.5, 1.15, 0.30), root=0.8, p=0.40, residue="low", fixes_n=True, status="not_modelled",
         cal_note="planted ~20 Mar; stage lengths FAO-56 Table 11 'April, Idaho USA'; Kc for dry/seed peas. "
                  "No Kansas yield-water function found: yield not modelled"),
]


def doy_add(doy: int, days: int) -> int:
    return (doy - 1 + days) % 365 + 1


def main() -> None:
    calendar = {}
    if CALENDAR.exists():
        for r in csv.DictReader(CALENDAR.open()):
            calendar[r["crop"]] = r

    rows = []
    for c in CROPS:
        crop = c["crop"]
        plant = c["plant_doy"]
        stages = list(c["stages"])
        harvest_obs = None
        cal_src = "ASSUMPTION: approximate west-central Kansas date, replace with NASS crop progress / NDVI"
        cal = calendar.get(crop, {})
        if cal.get("plant_doy_median"):
            plant = int(float(cal["plant_doy_median"]))
            cal_src = cal["source"]
        if cal.get("harvest_doy_median"):
            harvest_obs = int(float(cal["harvest_doy_median"]))
        if crop == "winter_wheat" and harvest_obs:
            season_obs = (harvest_obs - plant) % 365
            stages[0] = season_obs - sum(stages[1:])
        maturity = doy_add(plant, sum(stages))

        harvest = harvest_obs if harvest_obs else maturity
        row = {
            "crop": crop, "name": c["name"], "status": c["status"],
            "plant_doy": plant, "maturity_doy": maturity, "harvest_doy": harvest,
            "kc_ini": c["kc"][0], "kc_mid": c["kc"][1], "kc_end": c["kc"][2],
            "stage_lengths_days": "/".join(str(s) for s in stages),
            "season_days": sum(stages),
            "root_depth_m": c["root"], "depletion_fraction_p": c["p"],
            "threshold_et_mm": "", "yield_per_mm_kg_ha": "", "yield_per_mm_longterm_kg_ha": "",
            "max_et_mm": "", "max_yield_kg_ha": "",
            "bushel_kg": "", "residue_class": c["residue"], "fixes_nitrogen": str(c["fixes_n"]).lower(),
            "source": "",
        }
        if crop in BUSHEL_CROP:
            row["bushel_kg"] = round(BUSHEL_KG[BUSHEL_CROP[crop]], 4)
        elif crop in EXTRA_BUSHEL_LB:
            row["bushel_kg"] = round(EXTRA_BUSHEL_LB[crop] * LB_KG, 4)

        if crop in STONE:
            thr_in, slope, slope_lt, max_in, unit = STONE[crop]
            if unit == "bu":
                conv = lambda v: bu_acre_to_kg_ha(v, BUSHEL_CROP[crop])  # noqa: E731
            else:
                conv = lb_acre_to_kg_ha
            row["threshold_et_mm"] = round(thr_in * INCH_MM, 1)
            row["yield_per_mm_kg_ha"] = round(conv(slope) / INCH_MM, 3)
            row["yield_per_mm_longterm_kg_ha"] = round(conv(slope_lt) / INCH_MM, 3)
            row["max_et_mm"] = round(max_in * INCH_MM, 1)
            row["max_yield_kg_ha"] = round(conv(slope) / INCH_MM * (max_in - thr_in) * INCH_MM, 0)
            yld = (f"yield-ET: Stone et al. 2006 Table 1 (E17): threshold {thr_in} in, {slope} {unit}/acre per in "
                   f"(long-term {slope_lt}), max ET {max_in} in, converted to metric")
        else:
            yld = "yield-ET: none found for Kansas (gap)"

        if harvest_obs:
            cal_src += f"; harvest_doy = NASS median day 50% harvested ({harvest_obs})"
        else:
            cal_src += "; harvest_doy = maturity_doy (no harvest progress data)"
        row["source"] = (f"{yld}; Kc: FAO-56 Table 12 (E23); stages: FAO-56 Table 11 (E24), {c['cal_note']}; "
                         f"root depth and p: FAO-56 Table 22 (E25); calendar: {cal_src}; "
                         f"bushel weight: USDA standard (E29)")
        rows.append(row)

    rows.append({k: "" for k in rows[0]} | {
        "crop": "fallow", "name": "Fallow (no-till, chemical weed control)", "status": "modelled",
        "residue_class": "carries residue of previous crop", "fixes_nitrogen": "false",
        "source": "no crop transpiration; soil evaporation from the engine. Calibration targets for storage "
                  "efficiency in reference/calibration_targets.csv (E08)",
    })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f'{r["crop"]:<24} plant {str(r["plant_doy"]):>3} harvest {str(r["harvest_doy"]):>3} '
              f'thr {str(r["threshold_et_mm"]):>6} mm  slope {str(r["yield_per_mm_kg_ha"]):>7} kg/ha/mm  '
              f'max {str(r["max_yield_kg_ha"]):>6} kg/ha  [{r["status"]}]')
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
