#!/usr/bin/env python3
"""National child care prices from the National Database of Childcare Prices (DOL Women's Bureau). Standard library only.

    python3 -I sources/tools/ndcp_prices.py

Reads sources/raw/ndcp/NDCP2022.xlsx (county file, 2008-2022) and takes, for each county, its latest study year with a
reported median weekly price. The national figure for each age and care type is the population-weighted median of the
county medians (weight TOTALPOP), so it describes what the typical American family faces where it lives.
Writes sources/derived/ndcp_weekly_prices.csv. Prices are in the study year's dollars (mostly 2022).
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx  # noqa: E402

SOURCES = os.path.dirname(HERE)
XLSX = os.path.join(SOURCES, "raw", "ndcp", "NDCP2022.xlsx")
OUT = os.path.join(SOURCES, "derived", "ndcp_weekly_prices.csv")
COLS = {("center", "infant"): "MCINFANT", ("center", "toddler"): "MCTODDLER", ("center", "preschool"): "MCPRESCHOOL",
        ("center", "school_age"): "MCSA", ("family", "infant"): "MFCCINFANT", ("family", "toddler"): "MFCCTODDLER",
        ("family", "preschool"): "MFCCPRESCHOOL", ("family", "school_age"): "MFCCSA"}


def wmedian(pairs):
    pairs = sorted(pairs)
    tot = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= tot / 2:
            return v


def main():
    it = xlsx.rows(XLSX)
    head = next(it)
    ix = {k: i for i, k in enumerate(head) if k}
    latest = {}
    for r in it:
        fips, year = r[ix["COUNTY_FIPS_CODE"]], r[ix["STUDYYEAR"]]
        if fips is None or year is None:
            continue
        for key, col in COLS.items():
            v = r[ix[col]]
            if isinstance(v, float) and v > 0:
                pop = r[ix["TOTALPOP"]] or 0
                old = latest.get((fips, key))
                if old is None or year > old[0]:
                    latest[(fips, key)] = (year, v, pop)
    rows = []
    for key, col in COLS.items():
        vals = [(v, pop) for (f, k), (y, v, pop) in latest.items() if k == key and pop]
        years = sorted(y for (f, k), (y, v, pop) in latest.items() if k == key)
        rows.append({"care_type": key[0], "age_group": key[1], "median_weekly_price": "%.2f" % wmedian(vals),
                     "counties": len(vals), "study_years": "%d-%d" % (years[0], years[-1]),
                     "share_from_2022": "%.2f" % (sum(1 for y in years if y == 2022) / len(years)), "ndcp_column": col})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("%-7s %-11s $%7s a week  (%s counties, %s, %s from 2022)" % (r["care_type"], r["age_group"], r["median_weekly_price"],
                                                                          r["counties"], r["study_years"], r["share_from_2022"]))
    print("wrote %s" % os.path.relpath(OUT, os.path.dirname(SOURCES)))


if __name__ == "__main__":
    main()
