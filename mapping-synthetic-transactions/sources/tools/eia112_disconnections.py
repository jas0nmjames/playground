#!/usr/bin/env python3
"""National residential final notices, disconnections and reconnections by month, 2024: Form EIA-112. Standard library only.

    python3 -I sources/tools/eia112_disconnections.py

Reads the two utility-level workbooks in sources/raw/utility_disconnections/ (electric and natural gas), sums the "State
Total" rows (which include EIA's adjustments for nonresponse) of the Final notices, Disconnections, Reconnections and
Number of customers sheets, and writes sources/derived/eia112_disconnections_2024.csv: one row per fuel and month, plus a
year row. Used for the month run's notice-to-shutoff chain: how many disconnections end in a reconnection, and how the
shutoff rate compares with the notices.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xlsx import rows  # noqa: E402

SOURCES = os.path.dirname(HERE)
RAW = os.path.join(SOURCES, "raw", "utility_disconnections")
OUT = os.path.join(SOURCES, "derived", "eia112_disconnections_2024.csv")
FILES = {"electric": "112 electric utility level data 2024.xlsx", "natural_gas": "112 natural gas utility level data 2024.xlsx"}
SHEETS = {"final_notices": "Final notices", "disconnections": "Disconnections", "reconnections": "Reconnections", "customers": "Number of customers"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def totals(path, sheet):
    out = [0.0] * 12
    for r in rows(path, sheet):
        if len(r) >= 14 and r[1] == "State Total":
            for i in range(12):
                out[i] += float(r[2 + i] or 0)
    return out


def main():
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fuel", "month", "final_notices", "disconnections", "reconnections", "customers", "disconnections_per_notice",
                    "reconnections_per_disconnection", "disconnections_per_customer"])
        for fuel, name in FILES.items():
            t = {k: totals(os.path.join(RAW, name), sh) for k, sh in SHEETS.items()}
            for i, m in enumerate(MONTHS + ["year"]):
                if m == "year":
                    n, d, r = sum(t["final_notices"]), sum(t["disconnections"]), sum(t["reconnections"])
                    c = sum(t["customers"]) / 12.0
                else:
                    n, d, r, c = t["final_notices"][i], t["disconnections"][i], t["reconnections"][i], t["customers"][i]
                w.writerow([fuel, m, "%.0f" % n, "%.0f" % d, "%.0f" % r, "%.0f" % c, "%.4f" % (d / n), "%.4f" % (r / d), "%.5f" % (d / c)])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
