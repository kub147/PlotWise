"""Rebuild every workstream C file, in order, then run the tests.

    python crops-economics/run_all.py              # from the repo root (or from inside crops-economics/)

Steps that need a key (NASS_API_KEY, AMS_API_KEY) are skipped with a message when the key is not set
and their raw files are not there yet. Everything else needs only Python 3.10+ and `pdftotext`
(poppler-utils) for the K-State PDFs.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
S = ROOT / "scripts"
RAW = ROOT / "data/raw"


def run(script: str, *args: str) -> bool:
    print(f"\n=== {script} {' '.join(args)}")
    r = subprocess.run([sys.executable, str(S / script), *args], cwd=ROOT)
    if r.returncode != 0:
        print(f"!!! {script} failed (exit {r.returncode})")
    return r.returncode == 0


def main() -> int:
    ok = True
    have_nass = bool(os.environ.get("NASS_API_KEY"))

    # 1. NASS raw data (prices, county yields, crop progress)
    if have_nass:
        ok &= run("fetch_nass.py")
    elif not (RAW / "nass/prices_ks.json").exists():
        print("\n--- NASS_API_KEY not set and no raw NASS files: skipping prices, county yields, crop calendar")

    nass_ready = (RAW / "nass/prices_ks.json").exists()
    if nass_ready and (RAW / "nass/progress_ks.json").exists():
        ok &= run("derive_crop_calendar.py")

    # 2. CPI (+ prices when NASS data exist). build_prices writes the CPI table in any case.
    r = run("build_prices.py")
    ok &= r or not nass_ready
    if nass_ready:
        ok &= run("build_county_yields.py")
        if (ROOT.parent / "reference/kstate_tribune_rotation_yields.csv").exists():
            ok &= run("compare_county_vs_trial.py")
        else:
            print("\n--- repo reference/kstate_tribune_rotation_yields.csv not found: skipping county vs trial")

    # 3. Crops (uses the crop calendar if present)
    ok &= run("build_crops.py")

    # 4. Costs from the K-State PDFs
    if shutil.which("pdftotext") is None:
        print("\n--- pdftotext not found: keeping the committed reference/costs.csv "
              "(install poppler-utils to rebuild it)")
    else:
        ok &= run("fetch_agmanager.py")
        ok &= run("parse_agmanager_budgets.py")
        ok &= run("build_costs.py")

    # 5. Tests
    print("\n=== tests")
    t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"], cwd=ROOT)
    ok &= t.returncode == 0

    print("\nALL OK" if ok else "\nSOME STEPS FAILED - read the messages above")
    if not nass_ready:
        print("Still missing: reference/prices.csv, county_yields.csv, crop_calendar_ks.csv (set NASS_API_KEY and rerun)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
