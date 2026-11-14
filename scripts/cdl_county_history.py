"""Crop acreage history per county from the USDA Cropland Data Layer (CropScape API, no key needed).

Usage:
    python3 cdl_county_history.py --fips 20071 20203 --start 2008 --end 2024 [--out cdl_counties.json]

Prints wheat / fallow / sorghum / corn acreage (thousand acres), the fallow share of dryland cropland
and the ratio of summer crops (sorghum + corn) to wheat. County FIPS examples: 20071 Greeley KS (Tribune),
20203 Wichita KS, 20075 Hamilton KS, 20055 Finney KS (Garden City), 08121 Washington CO (Akron).
"""
import argparse, csv, io, json, re, urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLStat?year={y}&fips={f}&format=csv"
KEEP = {"Corn": "corn", "Sorghum": "sorghum", "Winter Wheat": "wheat", "Fallow/Idle Cropland": "fallow",
        "Millet": "millet", "Sunflowers": "sunflower", "Soybeans": "soybean", "Alfalfa": "alfalfa",
        "Triticale": "triticale", "Grass/Pasture": "grass"}

def fetch(job):
    f, y = job
    try:
        xml = urllib.request.urlopen(API.format(y=y, f=f), timeout=60).read().decode()
        url = re.search(r"<returnURL>(.*?)</returnURL>", xml).group(1)
        text = urllib.request.urlopen(url, timeout=60).read().decode()
        acres = {}
        for row in csv.reader(io.StringIO(text)):
            if len(row) >= 4 and row[1].strip() in KEEP:
                acres[KEEP[row[1].strip()]] = float(row[3])
        return f, y, acres
    except Exception:
        return f, y, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fips", nargs="+", required=True)
    ap.add_argument("--start", type=int, default=2008); ap.add_argument("--end", type=int, default=2024)
    ap.add_argument("--out", default="cdl_counties.json")
    a = ap.parse_args()
    jobs = [(f, y) for f in a.fips for y in range(a.start, a.end + 1)]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(fetch, jobs))
    out = {}
    for f, y, acres in res:
        if acres: out.setdefault(f, {})[y] = acres
    json.dump(out, open(a.out, "w"), indent=1)
    for f in a.fips:
        print(f"\ncounty {f} — thousand acres")
        print("year  wheat fallow sorghum  corn  fallow_share_%  summer_crops/wheat")
        for y in sorted(out.get(f, {})):
            g = lambda k: out[f][y].get(k, 0) / 1000
            total = sum(g(k) for k in ("wheat", "fallow", "sorghum", "corn", "millet", "sunflower"))
            print(f"{y} {g('wheat'):6.0f} {g('fallow'):6.0f} {g('sorghum'):7.0f} {g('corn'):5.0f} "
                  f"{100 * g('fallow') / total:10.1f} {(g('sorghum') + g('corn')) / max(g('wheat'), 1e-9):14.2f}")
    print("\nsaved", a.out)

if __name__ == "__main__":
    main()
