#!/usr/bin/env python3
"""What owners pay for housing each month, by mortgage status and household income. AHS 2023. Standard library only.

    python3 -I sources/tools/ahs_owner_costs.py

Reads sources/raw/ahs/AHS 2023 National PUF v1.1 CSV.zip (household.csv) and weights households by WEIGHT. Owners are
TENURE 1; an owner with a mortgage has MORTAMT above 0. Housing cost is TOTHCAMT less UTILAMT (mortgage, property tax,
insurance and fees; utilities are separate bills in Medianville), and income is HINCP, both in 2023 dollars. Writes
sources/derived/ahs_owner_costs.csv: for each mortgage status and income band, the weighted quantiles of monthly cost,
then the burden figures (cost over income) for the whole group. Used by population.reshape_owner_costs (decision in the
v2 close reading, reference/medianville-v2-close-reading.md).
"""
import csv
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
ZIP = os.path.join(SOURCES, "raw", "ahs", "AHS 2023 National PUF v1.1 CSV.zip")
OUT = os.path.join(SOURCES, "derived", "ahs_owner_costs.csv")
BANDS = ((0, 25000), (25000, 50000), (50000, 100000), (100000, 200000), (200000, None))
QS = (.01, .05, .10, .20, .30, .40, .50, .60, .70, .80, .90, .95, .99)


def num(v):
    try:
        return float(v.strip("'"))
    except ValueError:
        return None


def wquant(pairs, q):
    pairs = sorted(pairs)
    tot = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= q * tot:
            return v
    return pairs[-1][0]


def main():
    groups = {"free_and_clear": [], "with_mortgage": []}
    with zipfile.ZipFile(ZIP) as z:
        r = csv.reader(io.TextIOWrapper(z.open("household.csv"), encoding="utf-8", newline=""))
        head = next(r)
        ix = {k: i for i, k in enumerate(head)}
        for row in r:
            if row[ix["TENURE"]].strip("'") != "1":
                continue
            tot, util, inc, w, mort = (num(row[ix[k]]) for k in ("TOTHCAMT", "UTILAMT", "HINCP", "WEIGHT", "MORTAMT"))
            if tot is None or util is None or inc is None or w is None or tot < 0 or util < 0:
                continue
            groups["with_mortgage" if (mort or 0) > 0 else "free_and_clear"].append((max(0.0, tot - util), inc, w))
    rows = []
    for g, hh in groups.items():
        for lo, hi in BANDS:
            band = [(c, w) for c, inc, w in hh if inc >= lo and (hi is None or inc < hi)]
            rows.append([g, lo, "" if hi is None else hi, len(band)] + ["%.0f" % wquant(band, q) for q in QS])
        b = [(12 * c / inc, w) for c, inc, w in hh if inc > 0]
        tw = sum(w for _, w in b)
        print("%-15s %6d owners  burden median %.3f  over 30%% %.3f  over half %.3f  over all of income %.3f" % (
            g, len(hh), wquant(b, .5), sum(w for x, w in b if x > .3) / tw, sum(w for x, w in b if x > .5) / tw,
            sum(w for x, w in b if x > 1) / tw))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["mortgage_status", "income_from", "income_to", "households"] + ["p%02d" % round(q * 100) for q in QS])
        w.writerows(rows)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
