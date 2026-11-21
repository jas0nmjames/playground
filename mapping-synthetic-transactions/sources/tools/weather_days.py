#!/usr/bin/env python3
"""Storm and heat weekdays a year for Medianville's places, 2015-2025. Standard library only.

    python3 -I sources/tools/weather_days.py

Medianville's people are national but its places are local (City Design v0.1): each district borrows from real places
within driving distance of Fayetteville, GA. Weather belongs to places, so the counts come from those counties.

Storm weekday: a Monday-Friday on which NOAA Storm Events logs a winter storm, ice storm, winter weather, heavy snow,
blizzard, tropical storm or hurricane in at least 2 of the Medianville counties below (multi-day events count every day).
That is the simulator's storm: schools closed, trips cut, power out for some households. Afternoon thunderstorms and
tornadoes are not counted; they cut power locally but do not close the city, and the simulator has no scenario for them.

Heat weekday: a Monday-Friday with a high of 95 F or more at Atlanta's airport (GHCN-Daily USW00013874, Clayton County).
Storm Events logs no heat events for these counties in 2015-2025, so it cannot give this count.

Writes sources/derived/weather_days.csv: one row per year with both counts and the dates, then a mean row.
"""
import csv
import datetime as dt
import glob
import gzip
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
STORM_GLOB = os.path.join(SOURCES, "raw", "noaa_storm_events", "StormEvents_details-ftp_v1.0_d*.csv.gz")
GHCN = os.path.join(SOURCES, "raw", "noaa_ghcn_daily", "USW00013874.csv")
OUT = os.path.join(SOURCES, "derived", "weather_days.csv")
YEARS = range(2015, 2026)
# Fulton (downtown), Clayton (inner suburbs), Fayette and Henry (outer suburbs), Spalding and Coweta (satellite city),
# Pike, Lamar, Meriwether and Upson (rural towns), Peach (orchards). Fulton is split into two forecast zones.
COUNTIES = {"FULTON", "NORTH FULTON", "SOUTH FULTON", "CLAYTON", "FAYETTE", "HENRY", "SPALDING", "COWETA",
            "PIKE", "LAMAR", "MERIWETHER", "UPSON", "PEACH"}
STORM_TYPES = {"Winter Storm", "Ice Storm", "Winter Weather", "Heavy Snow", "Blizzard", "Tropical Storm",
               "Hurricane", "Hurricane (Typhoon)"}
MIN_COUNTIES = 2
HEAT_F = 95.0


def _date(ym, day):
    return dt.date(int(ym[:4]), int(ym[4:]), int(day))


def storm_days():
    hits = {}
    for path in sorted(glob.glob(STORM_GLOB)):
        with gzip.open(path, "rt", encoding="latin-1", newline="") as f:
            for r in csv.DictReader(f):
                if r["STATE"] != "GEORGIA" or r["CZ_NAME"] not in COUNTIES or r["EVENT_TYPE"] not in STORM_TYPES:
                    continue
                d, end = _date(r["BEGIN_YEARMONTH"], r["BEGIN_DAY"]), _date(r["END_YEARMONTH"], r["END_DAY"])
                while d <= end:
                    hits.setdefault(d, set()).add(r["CZ_NAME"].replace("NORTH ", "").replace("SOUTH ", ""))
                    d += dt.timedelta(days=1)
    return sorted(d for d, c in hits.items() if len(c) >= MIN_COUNTIES and d.weekday() < 5 and d.year in YEARS)


def heat_days():
    out = []
    with open(GHCN, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = dt.date.fromisoformat(r["DATE"])
            if d.year in YEARS and d.weekday() < 5 and r["TMAX"].strip():
                if int(r["TMAX"]) / 10 * 9 / 5 + 32 >= HEAT_F - 0.05:   # TMAX is tenths of a degree C
                    out.append(d)
    return out


def main():
    storms, heat = storm_days(), heat_days()
    rows = []
    for y in YEARS:
        s = [d for d in storms if d.year == y]
        h = [d for d in heat if d.year == y]
        rows.append({"year": y, "storm_weekdays": len(s), "heat_weekdays": len(h),
                     "storm_dates": " ".join(d.isoformat() for d in s), "heat_dates": " ".join(d.isoformat() for d in h)})
    n = len(rows)
    rows.append({"year": "mean %d-%d" % (YEARS[0], YEARS[-1]), "storm_weekdays": "%.2f" % (len(storms) / n),
                 "heat_weekdays": "%.2f" % (len(heat) / n), "storm_dates": "", "heat_dates": ""})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("%-14s storm %5s  heat %5s" % (r["year"], r["storm_weekdays"], r["heat_weekdays"]))
    print("wrote %s" % os.path.relpath(OUT, os.path.dirname(SOURCES)))


if __name__ == "__main__":
    main()
