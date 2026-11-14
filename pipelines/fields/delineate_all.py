"""Run delineate_fields.py for every county in data/processed/counties.geojson (skips counties already done).

Usage:
    EE_PROJECT=<your-ee-project> python3 pipelines/fields/delineate_all.py [--workers 3]
"""
import argparse, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")

def run(fips):
    out = os.path.join(ROOT, "data", "raw", "fields", f"candidates_{fips}.geojson")
    if os.path.exists(out):
        return fips, "already done"
    for attempt in range(2):
        r = subprocess.run([sys.executable, os.path.join(HERE, "delineate_fields.py"), "--fips", fips], capture_output=True, text=True)
        if r.returncode == 0:
            return fips, r.stdout.strip().splitlines()[-1].split(" -> ")[0]
    return fips, "FAILED: " + r.stderr.strip().splitlines()[-1][:200]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=3); a = ap.parse_args()
    counties = json.load(open(os.path.join(ROOT, "data", "processed", "counties.geojson")))["features"]
    fips = [c["properties"]["county_fips"] for c in counties]
    with ThreadPoolExecutor(a.workers) as ex:
        for f, msg in ex.map(run, fips):
            print(f, msg, flush=True)

if __name__ == "__main__":
    main()
