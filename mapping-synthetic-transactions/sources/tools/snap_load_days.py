#!/usr/bin/env python3
"""The day of the month SNAP benefits load, as a national mix of the state rules compiled so far. Standard library only.

    python3 -I sources/tools/snap_load_days.py

Reads sources/derived/snap_issuance.csv (8 states' issuance rules) and weights each state by its SNAP households in the
FY2024 Quality Control file (sources/raw/snap_qc/qcfy2024_csv.zip, FYWGT). Within a state, every listed day is equally
likely. Two states state a range without the digit-to-day map: California (last digit d loads on day d; a 0 is taken as
the 10th) and Arkansas (4th-13th). Writes sources/derived/snap_load_days.csv: day, share, and the states that load that day.
"""
import collections
import csv
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
RULES = os.path.join(SOURCES, "derived", "snap_issuance.csv")
QC = os.path.join(SOURCES, "raw", "snap_qc", "qcfy2024_csv.zip")
OUT = os.path.join(SOURCES, "derived", "snap_load_days.csv")
NAMES = {"ND": "North Dakota", "MO": "Missouri", "IA": "Iowa", "GA": "Georgia", "MN": "Minnesota", "CA": "California",
         "IL": "Illinois", "AR": "Arkansas"}
RANGE_ONLY = {"CA": list(range(1, 11)), "AR": list(range(4, 14))}


def main():
    days = collections.defaultdict(list)
    with open(RULES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["state"] in RANGE_ONLY:
                days[r["state"]] = RANGE_ONLY[r["state"]]
            else:
                days[r["state"]].append(int(r["day_of_month"]))
    w = collections.Counter()
    with zipfile.ZipFile(QC) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv"))
        for r in csv.DictReader(io.TextIOWrapper(z.open(name), encoding="latin-1", newline="")):
            w[r["STATENAME"]] += float(r["FYWGT"] or 0)
    tot = sum(w[NAMES[s]] for s in days)
    share = collections.Counter()
    who = collections.defaultdict(set)
    for s, ds in days.items():
        for d in ds:
            share[d] += w[NAMES[s]] / tot / len(ds)
            who[d].add(s)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        out = csv.writer(f, lineterminator="\n")
        out.writerow(["day_of_month", "share", "states"])
        for d in sorted(share):
            out.writerow([d, "%.4f" % share[d], " ".join(sorted(who[d]))])
    for s in sorted(days, key=lambda s: -w[NAMES[s]]):
        print("%s %.3f of the 8 states' SNAP households; days %d-%d" % (s, w[NAMES[s]] / tot, min(days[s]), max(days[s])))
    print("by the 10th: %.1f%%; wrote %s" % (100 * sum(v for d, v in share.items() if d <= 10), os.path.relpath(OUT, os.path.dirname(SOURCES))))


if __name__ == "__main__":
    main()
