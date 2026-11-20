#!/usr/bin/env python3
"""Who cannot pay all of this month's bills in full, by whether they could cover a $400 emergency. SHED 2025. Standard
library only.

    python3 -I sources/tools/shed_bills.py

Reads sources/raw/shed/SHED_public_use_data_2025_(CSV).zip (public2025.csv) and weights adults by weight_pop. EF5C is
taken to be "This month, will you be able to pay all of your bills in full?" (answered by everyone, Yes or No). EF8_a
is "Paid a bill late", one of the follow-ups (EF8_a-j) asked of those who answered No, or who said a $400 expense would
stop them paying their bills (EF5D). The codebook PDF's text could not be extracted, so the wording is inferred from the
answers and the question order (an estimate of the reading, not of the numbers). Writes sources/derived/shed_bills.csv.
Used to check the month run's retry queue (sim/evidence/month_targets.csv).
"""
import collections
import csv
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
ZIP = os.path.join(SOURCES, "raw", "shed", "SHED_public_use_data_2025_(CSV).zip")
OUT = os.path.join(SOURCES, "derived", "shed_bills.csv")


def main():
    g = collections.defaultdict(collections.Counter)
    with zipfile.ZipFile(ZIP) as z:
        for r in csv.DictReader(io.TextIOWrapper(z.open("public2025.csv"), encoding="latin-1", newline="")):
            w = float(r["weight_pop"] or 0)
            grp = "covers_400" if r["pay_casheqv"] == "Yes" else "cannot_cover_400"
            for k in ("all", grp):
                g[k]["adults"] += w
                g[k]["cannot_pay_all_bills"] += w * (r["EF5C"] == "No")
                g[k]["paid_a_bill_late"] += w * (r["EF8_a"] == "Paid a bill late")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["group", "share_of_adults", "cannot_pay_all_bills_in_full_this_month", "paid_a_bill_late"])
        for k in ("all", "covers_400", "cannot_cover_400"):
            c = g[k]
            wr.writerow([k, "%.4f" % (c["adults"] / g["all"]["adults"]), "%.4f" % (c["cannot_pay_all_bills"] / c["adults"]),
                         "%.4f" % (c["paid_a_bill_late"] / c["adults"])])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
