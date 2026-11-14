"""Download K-State AgManager dryland cost-return budget PDFs (2016-2027) to data/raw/agmanager/.

Regions: Southwest, Northwest, North Central, South Central and Western Kansas.
Crops: wheat, grain sorghum, corn, oil-type sunflower. Files already on disk are not downloaded again.
"""
from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/raw/agmanager"
SITE = "https://www.agmanager.info"
PAGES = {
    **{y: f"{SITE}/farm-budgets/historical-farm-budget-projections/{y}-historical-budget-projections-non-irrigated"
       for y in range(2016, 2027)},
    2027: f"{SITE}/farm-budgets/2027-farm-management-guides-non-irrigated-crops",
}
WANT = re.compile(r"(southwest|northwest|north central|south central|western|^(SW|NW|NC|SC)_)", re.I)
CROP = re.compile(r"(wheat|sorghum|corn|sunflower|fallow)", re.I)
SKIP = re.compile(r"(durum|silage|confection|forage|hay|double|soybean|alfalfa|cotton|canola|irrigat)", re.I)
HEADERS = {"User-Agent": "field-shift-research-script"}


def fetch(url: str) -> bytes:
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    return b""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for year, page in PAGES.items():
        html = fetch(page).decode("utf-8", errors="ignore")
        links = sorted(set(re.findall(r'href="([^"]+\.pdf)"', html)))
        for link in links:
            name = urllib.parse.unquote(link.rsplit("/", 1)[-1])
            if not (WANT.search(name) and CROP.search(name)) or SKIP.search(name):
                continue

            path = re.sub(r"^https?://(www\.)?agmanager\.info", "", link)
            url = SITE + urllib.parse.quote(urllib.parse.unquote(path))
            target = OUT / f"{year}__{name.replace(' ', '_')}"
            if target.exists() and target.stat().st_size > 10_000:
                n += 1
                continue
            data = fetch(url)
            if not data.startswith(b"%PDF"):
                print(f"WARNING not a PDF: {url}")
                continue
            target.write_bytes(data)
            n += 1
            print(f"{year} {target.name}")
    print(f"{n} budget PDFs in {OUT}")


if __name__ == "__main__":
    main()
