#!/usr/bin/env python3
"""Unpaid adult caregiving from the ATUS activity summary file. Standard library only.

    python3 -I sources/tools/atus_caregiving.py

Reads sources/raw/atus_microdata/atussum-0325.zip (2003-2025 multi-year activity summary) and writes
sources/derived/atus_caregiving.csv: for persons 15 and over, pooled 2023-2025 and weighted with TU20FWGT,
the average minutes per day spent on each kind of adult care as a primary activity, the share of people
who did any on the diary day, and the average among those who did. Also by age of the person giving care.

Activity codes (ATUS lexicon):
    0304  caring for household adults     (physical care, looking after, medical care)
    0305  helping household adults        (paperwork, household and vehicle help, picking up)
    0404  caring for non-household adults
    0405  helping non-household adults    (any adult outside the household: relatives, friends, neighbors)
Secondary care (care while doing something else) is not in these codes.
"""
import csv
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
ZIP = os.path.join(SOURCES, "raw", "atus_microdata", "atussum-0325.zip")
OUT = os.path.join(SOURCES, "derived", "atus_caregiving.csv")
YEARS = (2023, 2024, 2025)
WEIGHT = "TU20FWGT"   # final weight for 2020 and later years in the multi-year file
CODES = {"0304": "caring for household adults", "0305": "helping household adults",
         "0404": "caring for non-household adults", "0405": "helping non-household adults"}
GROUPS = {"0304": ("0304",), "0305": ("0305",), "0404": ("0404",), "0405": ("0405",),
          "0304+0305": ("0304", "0305"), "0404+0405": ("0404", "0405")}
BANDS = (("15-44", 15, 44), ("45-64", 45, 64), ("65+", 65, 200))


def band(age):
    return next(b for b, lo, hi in BANDS if lo <= age <= hi)


def main():
    with zipfile.ZipFile(ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith(".dat"))
        f = io.TextIOWrapper(z.open(name), encoding="utf-8", newline="")
        r = csv.reader(f)
        head = next(r)
        ix = {k: i for i, k in enumerate(head)}
        cols = {c: [i for k, i in ix.items() if k.startswith("t" + c)] for c in CODES}
        keys = [(g, b) for g in GROUPS for b in ("all",) + tuple(x[0] for x in BANDS)]
        W = {b: 0.0 for b in ("all",) + tuple(x[0] for x in BANDS)}
        mins = {k: 0.0 for k in keys}
        doers = {k: 0.0 for k in keys}
        n = 0
        for row in r:
            if int(row[ix["TUYEAR"]]) not in YEARS:
                continue
            n += 1
            w = float(row[ix[WEIGHT]])
            b = band(int(row[ix["TEAGE"]]))
            W["all"] += w
            W[b] += w
            per = {c: sum(float(row[i]) for i in cs) for c, cs in cols.items()}
            for g, cs in GROUPS.items():
                m = sum(per[c] for c in cs)
                for bb in ("all", b):
                    mins[(g, bb)] += w * m
                    doers[(g, bb)] += w * (m > 0)
    rows = []
    for g, bb in keys:
        mean = mins[(g, bb)] / W[bb]
        share = doers[(g, bb)] / W[bb]
        rows.append({"activity_codes": g, "activity": " + ".join(CODES[c] for c in GROUPS[g]), "age_of_carer": bb,
                     "years": "%d-%d" % (YEARS[0], YEARS[-1]), "respondents": n if bb == "all" else "",
                     "minutes_per_day_per_person": "%.3f" % mean, "share_doing_any": "%.4f" % share,
                     "minutes_per_day_among_doers": "%.1f" % (mins[(g, bb)] / doers[(g, bb)] if doers[(g, bb)] else 0),
                     "population_share": "%.4f" % (W[bb] / W["all"]),
                     "source_file": "atussum-0325.zip (BLS ATUS 2003-2025 multi-year activity summary)", "weight": WEIGHT})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for x in rows:
        if x["age_of_carer"] == "all":
            print("%-10s %6s min/day  %5.2f%% doing  %5s min among doers" % (x["activity_codes"], x["minutes_per_day_per_person"],
                                                                          100 * float(x["share_doing_any"]), x["minutes_per_day_among_doers"]))
    print("respondents %d; wrote %s" % (n, os.path.relpath(OUT, os.path.dirname(SOURCES))))


if __name__ == "__main__":
    main()
