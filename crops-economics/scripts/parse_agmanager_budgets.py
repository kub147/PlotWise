"""Parse K-State AgManager dryland cost-return budgets (Southwest / Western Kansas) into a flat table.

Input : PDFs downloaded from agmanager.info into data/raw/agmanager/ (file names start with the
        budget year, e.g. "2026__Wheat_(W-F)_Cost-Return_Budget_in_Southwest_KS__Nov-01-2025.pdf").
Output: data/raw/agmanager/budgets_parsed.csv  (one row per budget, middle / average yield level)

Only the first budget in each PDF is read: that is the middle ("average") yield level.
Requires `pdftotext` (poppler-utils).

Usage: python scripts/parse_agmanager_budgets.py
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

MONEY = r"-?\$?\s*-?[\d,]+\.\d\d"


def money(s: str) -> float:
    s = s.replace("$", "").replace(",", "").replace(" ", "")
    neg = s.count("-") % 2 == 1
    return -float(s.replace("-", "")) if neg else float(s.replace("-", ""))


def classify(name: str) -> tuple[str, str]:
    """Return (crop, rotation_context) from the file name."""
    n = name.lower()
    if "sunflower" in n:
        return "sunflower", "W-SF-F"
    if "sorghum" in n:
        return "sorghum", "W-S-F"
    if "corn" in n:
        return "corn", "W-C-F"
    if "wheat" in n:
        if "w-s_c-f" in n or "wsf" in n:
            return "wheat", "W-S/C-F"
        return "wheat", "W-F"
    raise ValueError(f"unknown crop in {name}")


def first(pattern: str, text: str, flags=0):
    m = re.search(pattern, text, flags)
    return m


def parse(pdf: Path) -> dict:
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True,
                          check=True).stdout

    start = text.find("INCOME")
    body = text[start:]

    crop, ctx = classify(pdf.name)
    budget_year = int(pdf.name[:4])
    date_m = first(r"Date:\s*([A-Za-z]{3}-\d{2}-\d{4})", text)

    prod = first(r"Product\s*\n\s+(.+?)\s{2,}(bu|cwt|lb)\s+\$([\d.]+)\s+([\d.]+)\s+\$([\d,.]+)", body)
    if not prod:
        raise ValueError(f"no product line in {pdf.name}")

    direct = first(r"--TOTAL DIRECT EXPENSES--\s+(" + MONEY + ")", body)
    fixed = first(r"--TOTAL FIXED EXPENSES--\s+(" + MONEY + ")", body)
    ins = first(r"Crop insurance[^\n$]*?(" + MONEY + r")\s", body)
    rent_detail = first(r"(?:All crops[^\n]*?|Cash rent \(ave\)[^\n]*?)\s+acre\s+\$([\d.]+)\s+([\d.]+)\s+\$([\d,.]+)",
                        text[start:])
    rent_abstract = first(r"Cash rent\s+-{5,}\s+(" + MONEY + ")", body)

    direct_v = money(direct.group(1))
    fixed_v = money(fixed.group(1)) if fixed else 0.0
    ins_v = money(ins.group(1)) if ins else 0.0
    if rent_detail:
        rent_rate, rent_qty, rent_amt = float(rent_detail.group(1)), float(rent_detail.group(2)), money(
            rent_detail.group(3))
    elif rent_abstract:
        rent_amt = money(rent_abstract.group(1))
        rent_rate, rent_qty = rent_amt, float("nan")
    else:
        raise ValueError(f"no cash rent in {pdf.name}")

    total_spec = first(r"--TOTAL SPECIFIED EXPENSES--\s+(" + MONEY + ")", body)
    total_v = money(total_spec.group(1)) if total_spec else direct_v + fixed_v
    if abs(total_v - (direct_v + fixed_v)) > 1.0:
        raise ValueError(f"totals do not add up in {pdf.name}: {direct_v} + {fixed_v} != {total_v}")

    return {
        "budget_year": budget_year,
        "budget_date": date_m.group(1) if date_m else "",
        "crop": crop,
        "rotation_context": ctx,
        "product": prod.group(1).strip(),
        "yield_unit": prod.group(2),
        "planning_price_usd_per_unit": float(prod.group(3)),
        "planning_yield": float(prod.group(4)),
        "direct_costs_usd_acre": round(direct_v, 2),
        "crop_insurance_usd_acre": round(ins_v, 2),
        "fixed_costs_usd_acre": round(fixed_v, 2),
        "cash_rent_rate_usd_acre_year": rent_rate,
        "cash_rent_acre_years_charged": rent_qty,
        "cash_rent_usd_acre": round(rent_amt, 2),
        "machinery_fixed_usd_acre": round(fixed_v - rent_amt, 2),
        "total_specified_usd_acre": round(total_v, 2),
        "source_file": pdf.name,
    }


def main(folder: str) -> None:
    folder_p = Path(folder)
    rows, errors = [], []
    for pdf in sorted(folder_p.glob("20*__*.pdf")):
        try:
            rows.append(parse(pdf))
        except Exception as e:  # report and continue: a missing budget must be visible, not silent
            errors.append(f"{pdf.name}: {e}")
    out = folder_p / "budgets_parsed.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} budgets)")
    for e in errors:
        print("ERROR", e)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "data/raw/agmanager"))
