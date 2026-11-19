#!/usr/bin/env python3
"""Compile sources/derived/federal_holidays_2027.csv from OPM's iCalendar file.

    python3 -I sources/tools/compile_holidays.py

Reads sources/raw/federal_holidays_2027/holidays.ics (downloaded from OPM). `observed_date` is the
date OPM lists (the day federal offices close); `actual_date` is the holiday's calendar date where
the two differ (a Saturday holiday is observed the Friday before, a Sunday holiday the Monday after).
"""
import csv
import datetime as dt
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
ICS = os.path.join(SOURCES, "raw", "federal_holidays_2027", "holidays.ics")
OUT = os.path.join(SOURCES, "derived", "federal_holidays_2027.csv")
ICS_URL = "https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/holidays.ics"
PAGE_URL = "https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/tabs/2027/"

# Calendar dates for the fixed-date holidays, to show when the observed day moved.
FIXED = {"New Year’s Day": (1, 1), "Juneteenth National Independence Day": (6, 19), "Independence Day": (7, 4),
         "Veterans Day": (11, 11), "Christmas Day": (12, 25)}


def main():
    text = open(ICS, encoding="utf-8").read().replace("\r\n ", "").replace("\n ", "")
    rows = []
    for ev in text.split("BEGIN:VEVENT")[1:]:
        d = dt.datetime.strptime(re.search(r"DTSTART;VALUE=DATE:(\d{8})", ev).group(1), "%Y%m%d").date()
        if d.year != 2027:
            continue
        name = re.search(r"SUMMARY:(.*)", ev).group(1).strip().replace("\\,", ",")
        actual = ""
        if name in FIXED:
            m, day = FIXED[name]
            year = 2028 if (name == "New Year’s Day" and d.month == 12) else 2027
            a = dt.date(year, m, day)
            if a != d:
                actual = a.isoformat()
        rows.append({"observed_date": d.isoformat(), "weekday": d.strftime("%A"), "holiday": name, "actual_date": actual,
                     "note": ("New Year's Day 2028 falls on a Saturday; observed in 2027" if actual.startswith("2028") else
                              "falls on a %s; observed %s" % (dt.date.fromisoformat(actual).strftime("%A"), d.strftime("%A")) if actual else ""),
                     "source_url": PAGE_URL, "source_file": ICS_URL})
    rows.sort(key=lambda r: r["observed_date"])
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote %d holidays to %s" % (len(rows), OUT))


if __name__ == "__main__":
    main()
