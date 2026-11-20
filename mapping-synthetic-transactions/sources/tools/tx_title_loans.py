#!/usr/bin/env python3
"""Texas auto title lending in 2025, from the OCCC credit access business reports. Standard library only.

    python3 -I sources/tools/tx_title_loans.py

Reads sources/raw/payday_title_tx_occc/: the CY2025 annual state report (new title loans by size, refinances, consumers)
and the four 2025 quarterly state reports (vehicles surrendered or repossessed). Columns are single-payment and
installment title loans. Writes sources/derived/title_loans_tx_2025.csv with each figure, Texas's population, and the
rate per 1,000 residents a year, which the simulator scales to Halvern.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pdftext import text  # noqa: E402

SOURCES = os.path.dirname(HERE)
RAW = os.path.join(SOURCES, "raw", "payday_title_tx_occc")
OUT = os.path.join(SOURCES, "derived", "title_loans_tx_2025.csv")
TX_POP_2025 = 31_300_000   # Census Vintage 2025 estimate for Texas, rounded (stated here, not downloaded)
QUARTERS = ["q1_2025_state_formatted.pdf", "q2_2025_state_formatted.pdf", "Q3_2025_State_Formatted.pdf", "Q4_2025_State.pdf"]


def nums(s, n):
    return [int(x.replace(",", "")) for x in re.findall(r"\$?([\d,]+)", s)[:n]]


def main():
    a = text(os.path.join(RAW, "2025_Annual_State.pdf"))
    new = [0, 0]
    four = r" (\d[\d,]*) (\d[\d,]*) (\d[\d,]*) (\d[\d,]*)"
    for band in "ABCDEFGHIJK":
        lead = r"6 ?%s \$[\d,]+ ?- ?\$[\d,]+" % band if band != "K" else r"6K Over \$7,500"
        m = re.search(lead + four, a)
        v = [int(m.group(g).replace(",", "")) for g in (3, 4)]   # single-payment and installment title loans
        new = [new[0] + v[0], new[1] + v[1]]
    refi = nums(re.search(r"8 Total number of refinances on extensions of consumer credit originated in the report year\. ([\d, ]+)", a).group(1), 4)[2:]
    cons = nums(re.search(r"5 Number of consumers for whom the CAB obtained.*?report year\. ([\d, ]+)", a).group(1), 4)[2:]
    repo = [0, 0]
    for f in QUARTERS:
        q = text(os.path.join(RAW, f))
        v = nums(re.search(r"Number of vehicles surrendered or repossessed during the reporting period.*?obtaining\. ([\d, ]+)", q).group(1), 2)
        repo = [repo[0] + v[0], repo[1] + v[1]]
    rows = []
    for item, (s, i) in (("new title loans", new), ("refinances of title loans originated in 2025", refi),
                         ("consumers who got a title loan (counted by location)", cons), ("vehicles surrendered or repossessed", repo)):
        rows.append({"item": item, "single_payment": s, "installment": i, "total": s + i, "texas_population": TX_POP_2025,
                     "per_1000_residents": "%.3f" % ((s + i) / TX_POP_2025 * 1000), "year": 2025})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("%-55s %8s %8s %8s  %s per 1,000" % (r["item"], r["single_payment"], r["installment"], r["total"], r["per_1000_residents"]))
    print("wrote %s" % os.path.relpath(OUT, os.path.dirname(SOURCES)))


if __name__ == "__main__":
    main()
