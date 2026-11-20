#!/usr/bin/env python3
"""H-2A guest workers on the job by day of the year, from DOL's FY2025 disclosure file. Standard library only.

    python3 -I sources/tools/h2a_season.py

Reads sources/raw/h2a_disclosure/H-2A_Disclosure_Data_FY2025_Q4.xlsx. For each certified case it counts the certified
H-2A workers as on the job every day from EMPLOYMENT_BEGIN_DATE to EMPLOYMENT_END_DATE, folds the dates onto one
calendar year (a fiscal year of certifications is one season). Certified positions are an upper bound on workers actually
present (some go unfilled). Writes sources/derived/h2a_on_the_job.csv: day of year (1-365), workers on the job in the
US and in Georgia, and per 1,000 residents. Also prints the certified-weighted median hourly wage offer.
"""
import csv
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx  # noqa: E402

SOURCES = os.path.dirname(HERE)
XLSX = os.path.join(SOURCES, "raw", "h2a_disclosure", "H-2A_Disclosure_Data_FY2025_Q4.xlsx")
OUT = os.path.join(SOURCES, "derived", "h2a_on_the_job.csv")
US_POP, GA_POP = 340_100_000, 11_200_000   # 2024-25 Census estimates, rounded (stated here, not downloaded)
EXCEL0 = dt.date(1899, 12, 30)


def main():
    it = xlsx.rows(XLSX)
    head = next(it)
    ix = {k: i for i, k in enumerate(head)}
    us = [0.0] * 366
    ga = [0.0] * 366
    wages = []
    for r in it:
        if not str(r[ix["CASE_STATUS"]] or "").startswith("Determination Issued - Certification"):
            continue
        n = r[ix["TOTAL_WORKERS_H2A_CERTIFIED"]] or 0
        b, e = r[ix["EMPLOYMENT_BEGIN_DATE"]], r[ix["EMPLOYMENT_END_DATE"]]
        if not n or not isinstance(b, float) or not isinstance(e, float) or e < b:
            continue
        d0, d1 = EXCEL0 + dt.timedelta(days=int(b)), EXCEL0 + dt.timedelta(days=int(e))
        state = r[ix["WORKSITE_STATE"]]
        w = r[ix["WAGE_OFFER"]]
        if isinstance(w, float) and 7 < w < 60:
            wages.append((w, n))
        d = d0
        while d <= d1:
            k = min(364, d.timetuple().tm_yday - 1)
            us[k] += n
            if state == "GA":
                ga[k] += n
            d += dt.timedelta(days=1)
    years = 1.0   # one fiscal year of certifications is one season; dates are folded onto a calendar year
    rows = [{"day_of_year": k + 1, "us_on_job": round(us[k] / years), "us_per_1000": "%.3f" % (us[k] / years / US_POP * 1000),
             "ga_on_job": round(ga[k] / years), "ga_per_1000": "%.3f" % (ga[k] / years / GA_POP * 1000)} for k in range(365)]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        wr.writeheader()
        wr.writerows(rows)
    wages.sort()
    tot, acc, med = sum(n for _, n in wages), 0, None
    for w, n in wages:
        acc += n
        if acc >= tot / 2:
            med = w
            break
    peak = max(rows, key=lambda r: r["us_on_job"])
    for m in (1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335):
        r = rows[m - 1]
        print("day %3d  US %7d (%s per 1,000)  GA %6d (%s per 1,000)" % (m, r["us_on_job"], r["us_per_1000"], r["ga_on_job"], r["ga_per_1000"]))
    print("peak day %d: US %d; median wage offer $%.2f an hour; wrote %s" % (peak["day_of_year"], peak["us_on_job"], med,
                                                                           os.path.relpath(OUT, os.path.dirname(SOURCES))))


if __name__ == "__main__":
    main()
