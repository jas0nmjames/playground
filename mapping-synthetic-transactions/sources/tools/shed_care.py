#!/usr/bin/env python3
"""Who goes without care because of cost, by whether they could cover a $400 emergency. SHED 2025. Standard library only.

    python3 -I sources/tools/shed_care.py

Reads sources/raw/shed/SHED_public_use_data_2025_(CSV).zip (public2025.csv), weights adults by weight_pop, and splits
them by pay_casheqv (would cover a $400 emergency with cash or its equivalent). E1_a-E1_e: in the past 12 months, went
without prescription medicine, a doctor, mental health care, dental care, or follow-up care because of the cost.
Writes sources/derived/shed_care_by_fragility.csv. Used to put skipped care on the same households that are short of money.
"""
import collections
import csv
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
ZIP = os.path.join(SOURCES, "raw", "shed", "SHED_public_use_data_2025_(CSV).zip")
OUT = os.path.join(SOURCES, "derived", "shed_care_by_fragility.csv")
ITEMS = {"E1_a": "prescription", "E1_b": "doctor", "E1_c": "mental_health", "E1_d": "dental", "E1_e": "follow_up"}


def main():
    g = collections.defaultdict(collections.Counter)
    with zipfile.ZipFile(ZIP) as z:
        for r in csv.DictReader(io.TextIOWrapper(z.open("public2025.csv"), encoding="latin-1", newline="")):
            w = float(r["weight_pop"] or 0)
            grp = "covers_400" if r["pay_casheqv"] == "Yes" else "cannot_cover_400"
            for k in ("all", grp):
                g[k]["adults"] += w
                g[k]["any"] += w * any(r[c] == "Yes" for c in ITEMS)
                for c, name in ITEMS.items():
                    g[k][name] += w * (r[c] == "Yes")
    rows = []
    for k in ("all", "covers_400", "cannot_cover_400"):
        c = g[k]
        row = {"group": k, "share_of_adults": "%.4f" % (c["adults"] / g["all"]["adults"]),
               "went_without_any_care": "%.4f" % (c["any"] / c["adults"])}
        row.update({"went_without_" + n: "%.4f" % (c[n] / c["adults"]) for n in ITEMS.values()})
        rows.append(row)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("%-17s %s of adults; went without some care %s; prescription %s" % (r["group"], r["share_of_adults"],
                                                                              r["went_without_any_care"], r["went_without_prescription"]))
    print("wrote %s" % os.path.relpath(OUT, os.path.dirname(SOURCES)))


if __name__ == "__main__":
    main()
