#!/usr/bin/env python3
"""When in the day people start errands and care, from the ATUS 2023-2025 activity files. Standard library only.

    python3 -I sources/tools/atus_hours.py

Reads sources/raw/atus_microdata/atusresp-0325.zip and atusact-0325.zip (2003-2025 multi-year files), keeps diary days
in 2023-2025, and weights each episode by the respondent's TU20FWGT. Weekday is a Monday-Friday diary day; weekend is
Saturday or Sunday (ATUS diary days that fall on holidays are coded to their weekday and are not separated here).
Writes sources/derived/atus_start_hours.csv: activity, day type, hour (0-23), the share of that activity's episodes
starting in that hour, and the number of episodes behind the profile.
"""
import collections
import csv
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
RAW = os.path.join(SOURCES, "raw", "atus_microdata")
OUT = os.path.join(SOURCES, "derived", "atus_start_hours.csv")
YEARS = {"2023", "2024", "2025"}
CODES = {"070101": "grocery_shopping", "070102": "purchasing_food_not_groceries", "070103": "purchasing_gas",
         "070104": "shopping_except_groceries_food_gas", "030112": "picking_up_dropping_off_household_children",
         "080101": "using_banking_services", "080401": "using_health_and_care_services",
         "030401": "physical_care_household_adults", "040401": "physical_care_nonhousehold_adults"}


def _reader(name):
    z = zipfile.ZipFile(os.path.join(RAW, name))
    inner = next(n for n in z.namelist() if n.endswith(".dat"))
    return csv.DictReader(io.TextIOWrapper(z.open(inner), encoding="utf-8", newline=""))


def main():
    resp = {}
    for r in _reader("atusresp-0325.zip"):
        if r["TUYEAR"] in YEARS:
            resp[r["TUCASEID"]] = (float(r["TU20FWGT"]), "weekend" if r["TUDIARYDAY"] in ("1", "7") else "weekday")
    w = collections.defaultdict(collections.Counter)
    n = collections.Counter()
    for r in _reader("atusact-0325.zip"):
        c = CODES.get(r["TRCODEP"])
        if c is None or r["TUCASEID"] not in resp:
            continue
        wt, day = resp[r["TUCASEID"]]
        w[(c, day)][int(r["TUSTARTTIM"][:2])] += wt
        n[(c, day)] += 1
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        out = csv.writer(f, lineterminator="\n")
        out.writerow(["activity", "day_type", "hour", "share", "episodes", "years", "weight"])
        for (c, day) in sorted(w):
            tot = sum(w[(c, day)].values())
            for h in range(24):
                out.writerow([c, day, h, "%.4f" % (w[(c, day)][h] / tot), n[(c, day)], "2023-2025", "TU20FWGT"])
    for k in sorted(n):
        print("%-45s %-8s %6d episodes" % (k[0], k[1], n[k]))
    print("respondents %d; wrote %s" % (len(resp), os.path.relpath(OUT, os.path.dirname(SOURCES))))


if __name__ == "__main__":
    main()
