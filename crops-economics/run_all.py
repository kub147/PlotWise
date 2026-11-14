"""Rebuild crops-economics/reference/ and run the tests.

    python crops-economics/run_all.py            uses local raw files only, no downloads
    python crops-economics/run_all.py --refresh  downloads K-State PDFs and, with NASS_API_KEY set, NASS data

A step whose raw input is missing is skipped and the committed result in reference/ is kept.
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
    refresh = "--refresh" in sys.argv


    if refresh and os.environ.get("NASS_API_KEY"):
        ok &= run("fetch_nass.py")
    elif refresh:
        print("\n--- --refresh without NASS_API_KEY: NASS data not downloaded")
    if not (RAW / "nass/prices_ks.json").exists():
        print("\n--- no raw NASS files here: keeping committed prices.csv, county_yields.csv, "
              "crop_calendar_ks.csv, county_vs_trial.csv")

    nass_ready = (RAW / "nass/prices_ks.json").exists()
    if nass_ready and (RAW / "nass/progress_ks.json").exists():
        ok &= run("derive_crop_calendar.py")


    r = run("build_prices.py")
    ok &= r or not nass_ready
    if nass_ready:
        ok &= run("build_county_yields.py")
        ok &= run("build_county_regions.py")
        if (ROOT.parent / "reference/kstate_tribune_rotation_yields.csv").exists():
            ok &= run("compare_county_vs_trial.py")
        else:
            print("\n--- repo reference/kstate_tribune_rotation_yields.csv not found: skipping county vs trial")


    ok &= run("build_crops.py")


    if shutil.which("pdftotext") is None:
        print("\n--- pdftotext not found: keeping the committed reference/costs.csv "
              "(install poppler-utils to rebuild it)")
    else:
        if refresh:
            ok &= run("fetch_agmanager.py")
        if list((RAW / "agmanager").glob("20*__*.pdf")) if (RAW / "agmanager").exists() else []:
            ok &= run("parse_agmanager_budgets.py")
            ok &= run("build_costs.py")
        else:
            print("\n--- no K-State PDFs here: keeping committed reference/costs.csv (use --refresh to download)")


    print("\n=== tests")
    t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"], cwd=ROOT)
    ok &= t.returncode == 0

    print("\nALL OK" if ok else "\nSOME STEPS FAILED - read the messages above")
    for f in ("prices.csv", "county_yields.csv", "crop_calendar_ks.csv"):
        if not (ROOT / "reference" / f).exists():
            print(f"Missing reference/{f}: run with --refresh and NASS_API_KEY set")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
