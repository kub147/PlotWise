"""Consistency tests for the workstream C reference files. Run: python -m unittest discover -s tests -v"""
from __future__ import annotations

import csv
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
sys.path.insert(0, str(ROOT / "scripts"))

from lookup import Economics 
from units import bu_acre_to_kg_ha  


def rows(name: str) -> list[dict]:
    with (REF / name).open() as f:
        return list(csv.DictReader(f))


SPEC_CROP_COLUMNS = ["crop", "plant_doy", "harvest_doy", "kc_ini", "kc_mid", "kc_end", "stage_lengths_days",
                     "root_depth_m", "threshold_et_mm", "yield_per_mm_kg_ha", "max_et_mm", "bushel_kg",
                     "residue_class", "fixes_nitrogen", "source"]


class TestCrops(unittest.TestCase):
    def test_spec_columns(self):
        cols = rows("crops.csv")[0].keys()
        for c in SPEC_CROP_COLUMNS:
            self.assertIn(c, cols)

    def test_every_row_has_source(self):
        for r in rows("crops.csv"):
            self.assertTrue(r["source"].strip(), r["crop"])

    def test_metric_conversion(self):
        w = {r["crop"]: r for r in rows("crops.csv")}["winter_wheat"]
        self.assertAlmostEqual(float(w["threshold_et_mm"]), 254.0, places=1)
        # 6.0 bu/acre per inch, 60 lb/bu
        self.assertAlmostEqual(float(w["yield_per_mm_kg_ha"]), bu_acre_to_kg_ha(6.0, "wheat") / 25.4, places=2)

    def test_stage_lengths_match_season(self):
        for r in rows("crops.csv"):
            if r["stage_lengths_days"]:
                total = sum(int(x) for x in r["stage_lengths_days"].split("/"))
                self.assertEqual(total, int(r["season_days"]), r["crop"])
                self.assertEqual((int(r["plant_doy"]) - 1 + total) % 365 + 1, int(r["maturity_doy"]), r["crop"])
                gap = (int(r["harvest_doy"]) - int(r["maturity_doy"])) % 365
                self.assertLessEqual(gap, 60, r["crop"])
                stages = [int(x) for x in r["stage_lengths_days"].split("/")]
                self.assertTrue(all(x >= 0 for x in stages) and stages[0] > 0, r["crop"])

    def test_kc_ranges(self):
        for r in rows("crops.csv"):
            for k in ("kc_ini", "kc_mid", "kc_end"):
                if r[k]:
                    self.assertTrue(0.1 <= float(r[k]) <= 1.3, (r["crop"], k))


class TestRotations(unittest.TestCase):
    def setUp(self):
        self.rot = json.loads((REF / "rotations.json").read_text())["rotations"]
        self.crops = {r["crop"] for r in rows("crops.csv")}
        self.cost_keys = {r["cost_key"] for r in rows("costs.csv")}
        self.evidence = set(re.findall(r"\| (E\d\d) \|", (REF / "evidence.md").read_text()))

    def test_required_rotations(self):
        ids = {r["id"] for r in self.rot}
        for need in ("WF", "WSF", "WCF", "WSSF", "WWSF"):
            self.assertIn(need, ids)

    def test_phases(self):
        for r in self.rot:
            self.assertEqual(len(r["phases"]), r["cycle_years"], r["id"])
            self.assertEqual([p["crop"] for p in r["phase_details"]], r["phases"], r["id"])
            for c in r["phases"]:
                self.assertIn(c, self.crops, r["id"])

    def test_cost_keys_exist(self):
        for r in self.rot:
            for p in r["phase_details"]:
                if not p["cost_key"].startswith("MISSING"):
                    self.assertIn(p["cost_key"], self.cost_keys, r["id"])

    def test_evidence_ids_exist(self):
        for r in self.rot:
            for e in r.get("evidence", []):
                self.assertIn(e, self.evidence, r["id"])

    def test_card_fields(self):
        for r in self.rot:
            for f in ("why", "evidence", "gaps", "check_locally"):
                self.assertIn(f, r, r["id"])


class TestCosts(unittest.TestCase):
    def test_positive_and_sourced(self):
        for r in rows("costs.csv"):
            self.assertGreater(float(r["cost_usd_per_acre"]), 0, r)
            self.assertIn("agmanager.info", r["source"])

    def test_cycle_equals_kstate_budget(self):
        # SW W-F 2018-2026: wheat phase + fallow phase == K-State wheat W-F total minus crop insurance
        c = {(int(r["year"]), r.get("region", "SW"), r["cost_key"]): r for r in rows("costs.csv")}
        for y in range(2018, 2027):
            w = c[(y, "SW", "wheat|W-F")]
            f = c[(y, "SW", "fallow|any")]
            expected = float(w["kstate_total_usd_acre"]) - float(w["crop_insurance_usd_acre"])
            self.assertAlmostEqual(float(w["cost_usd_per_acre"]) + float(f["cost_usd_per_acre"]), expected,
                                   delta=0.05, msg=y)

    def test_unique_and_regions(self):
        keys = [(r["year"], r["region"], r["cost_key"]) for r in rows("costs.csv")]
        self.assertEqual(len(keys), len(set(keys)), "duplicate (year, region, cost_key)")
        self.assertEqual({r["region"] for r in rows("costs.csv")}, {"SW", "NW", "NC", "SC"})

    def test_every_rotation_has_cost_in_every_region(self):
        rot = json.loads((REF / "rotations.json").read_text())["rotations"]
        have = {(r["region"], r["cost_key"]) for r in rows("costs.csv")}
        for reg in ("SW", "NW", "NC", "SC"):
            for r in rot:
                if r.get("status") in ("stretch", "validation_only"):
                    continue
                for p in r["phase_details"]:
                    self.assertIn((reg, p["cost_key"]), have, (reg, r["id"]))

    def test_lookup_fallback(self):
        e = Economics()
        mean = e.mean_real_cost[("SW", "sorghum|W-S-F")]
        self.assertAlmostEqual(e.phase_cost_usd_per_acre(2005, "sorghum|W-S-F"), mean)
        self.assertLess(e.phase_cost_usd_per_acre(2005, "sorghum|W-S-F", real=False), mean)


class TestCpi(unittest.TestCase):
    def test_base_year(self):
        f = {int(r["year"]): float(r["factor_to_2025_usd"]) for r in rows("cpi_u_annual.csv")}
        self.assertEqual(f[2025], 1.0)
        self.assertGreater(f[1995], 1.5)


@unittest.skipUnless((REF / "prices.csv").exists(), "prices.csv not built yet (needs NASS_API_KEY)")
class TestPrices(unittest.TestCase):
    def test_coverage(self):
        p = rows("prices.csv")
        for crop in ("wheat", "sorghum", "corn"):
            years = {int(r["year"]) for r in p if r["crop"] == crop}
            missing = set(range(1995, 2025)) - years
            self.assertFalse(missing, f"{crop} missing years {sorted(missing)}")

    def test_cwt_conversion(self):
        for r in rows("prices.csv"):
            if r["crop"] == "sorghum" and r["nass_unit"] == "$ / CWT":
                self.assertAlmostEqual(float(r["price_usd_per_bu"]), float(r["nass_value"]) * 0.56, places=2)

    def test_plausible(self):
        for r in rows("prices.csv"):
            if r["price_usd_per_bu"]:
                self.assertTrue(1.0 < float(r["price_usd_per_bu"]) < 15.0, r)


@unittest.skipUnless((REF / "county_yields.csv").exists(), "county_yields.csv not built yet (needs NASS_API_KEY)")
class TestCountyYields(unittest.TestCase):
    def test_greeley_dryland_wheat(self):
        y = [r for r in rows("county_yields.csv")
             if r["area"] == "Greeley" and r["crop"] == "winter_wheat" and r["practice"] == "NON-IRRIGATED"]
        self.assertGreater(len(y), 5, "expected several years of Greeley non-irrigated wheat")
        for r in y:
            self.assertTrue(0 <= float(r["yield_value"]) < 100, r)



@unittest.skipUnless((REF / "county_vs_trial.csv").exists(), "county_vs_trial.csv not built yet")
class TestCountyVsTrial(unittest.TestCase):
    def test_ratios_plausible(self):
        for r in rows("county_vs_trial.csv"):
            self.assertTrue(0.2 < float(r["ratio_of_means"]) < 1.5, r)
            self.assertGreater(int(r["years"]), 0)



@unittest.skipUnless((REF / "county_budget_regions.csv").exists(), "county_budget_regions.csv not built yet")
class TestCountyRegions(unittest.TestCase):
    def test_regions_valid(self):
        for r in rows("county_budget_regions.csv"):
            self.assertIn(r["budget_region"], {"SW", "NW", "NC", "SC", "unknown"})
            if r["in_study_area"] == "true":
                self.assertNotEqual(r["budget_region"], "unknown", r)

    def test_every_study_county_has_region(self):
        from study_area import load_counties
        study = load_counties()
        if not study:
            self.skipTest("team counties.geojson not found")
        have = {r["county_fips"][2:] for r in rows("county_budget_regions.csv")}
        missing = sorted(set(study) - have)
        self.assertFalse(missing, f"study-area counties without a budget region (rerun fetch): {missing}")

    def test_demo_counties(self):
        reg = {r["county_name"]: r["budget_region"] for r in rows("county_budget_regions.csv")}
        for name, want in (("Greeley", "SW"), ("Thomas", "NW"), ("Ellis", "NC")):
            if name in reg:
                self.assertEqual(reg[name], want, name)


if __name__ == "__main__":
    unittest.main()
