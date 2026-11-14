"""Observed crop rotations from per-pixel CDL history (Google Earth Engine).

Usage:
    EE_PROJECT=<your-ee-project> python3 cdl_rotation_sequences.py --fips 20071 --start 2010 --end 2024 [--out sequences.json]

Samples random 30 m pixels in a county, keeps those that were cropland or fallow in almost every year and reports:
transition probabilities between crops, how often a field is fallowed, the most common 3-year sequences
and what wheat is planted after. Letters: W winter wheat, F fallow, S sorghum, C corn, M millet, U sunflower.
Caveat: CDL is a classification, not ground truth; fallow and winter wheat are sometimes confused.
"""
import argparse, collections, json, os
import ee

LETTER = {24: "W", 61: "F", 4: "S", 1: "C", 29: "M", 6: "U", 205: "T", 5: "B", 236: "D", 225: "D", 26: "D",
          176: "g", 36: "A"}
CROPLAND = set("WFSCMUTBD")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fips", required=True); ap.add_argument("--start", type=int, default=2010)
    ap.add_argument("--end", type=int, default=2024); ap.add_argument("--out", default="sequences.json")
    a = ap.parse_args()
    ee.Initialize(project=os.environ["EE_PROJECT"])
    county = ee.FeatureCollection("TIGER/2018/Counties").filter(ee.Filter.eq("GEOID", a.fips)).geometry()
    years = list(range(a.start, a.end + 1))
    cdl = ee.ImageCollection("USDA/NASS/CDL")
    stack = ee.Image.cat([cdl.filter(ee.Filter.calendarRange(y, y, "year")).first().select("cropland").rename(f"y{y}")
                          for y in years])
    rows = []
    for seed in (1, 2, 3):  # getInfo returns at most 5000 features per call
        rows += stack.sample(region=county, scale=30, numPixels=4500, seed=seed, tileScale=4).getInfo()["features"]
    seqs = []
    for f in rows:
        s = "".join(LETTER.get(f["properties"][f"y{y}"], "o") for y in years)
        if sum(c in CROPLAND for c in s) >= len(years) - 2:
            seqs.append(s)
    print(f"sampled {len(rows)} pixels, {len(seqs)} are cropland in at least {len(years) - 2} of {len(years)} years")
    trans, total = collections.Counter(), collections.Counter()
    for s in seqs:
        for x, y in zip(s, s[1:]):
            trans[(x, y)] += 1; total[x] += 1
    print("\ntransition probabilities in % (row = this year, column = next year)")
    print("       W      F      S      C  other      n")
    for x in "WFSC":
        cells = " ".join(f"{100 * trans[(x, y)] / total[x]:6.1f}" for y in "WFSC")
        print(x, cells, f"{100 * (1 - sum(trans[(x, y)] for y in 'WFSC') / total[x]):6.1f} {total[x]:6d}")
    classes = collections.Counter()
    for s in seqs:
        r = s.count("F") / len(s)
        classes["no fallow (<10% of years)" if r < .10 else "occasional fallow (10-25%)" if r < .25
                else "fallow about 1 year in 3 (25-42%)" if r < .42 else "fallow about 1 year in 2 (>=42%)"] += 1
    print("\nfallow frequency")
    for k, v in classes.most_common(): print(f"{100 * v / len(seqs):5.1f}%  {k}")
    tri = collections.Counter(s[i:i + 3] for s in seqs for i in range(len(s) - 2))
    n = sum(tri.values())
    print("\nmost common 3-year sequences")
    for k, v in tri.most_common(12): print(f"{100 * v / n:5.1f}%  {k}")
    before_wheat = collections.Counter()
    for (x, y), v in trans.items():
        if y == "W": before_wheat[x] += v
    print("\nwheat is planted after:", {k: round(100 * v / sum(before_wheat.values()), 1) for k, v in before_wheat.most_common(5)})
    json.dump(seqs, open(a.out, "w"))
    print("saved", a.out)

if __name__ == "__main__":
    main()
