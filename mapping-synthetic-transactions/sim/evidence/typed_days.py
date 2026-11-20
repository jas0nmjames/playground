"""The typed-day set: a dozen-odd simulated days that stand for a year (plan, section 4, option A).

Every day of 2027 is put into exactly one class by `classify()`, using the simulator's own calendar
(Social Security cohorts, SSI day, tax season, EITC refund wave) and OPM's observed federal holidays.
Each class is represented by one or two simulated days; a representative's weight is the number of
2027 days in its class divided by the number of representatives. Storm and heat days are carved out
of the ordinary weekdays at the 2015-2025 average for Halvern's counties (sources/derived/weather_days.csv,
built by sources/tools/weather_days.py from NOAA Storm Events and Atlanta airport daily highs).
"""
import csv
import datetime as dt
import os
import sys

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SIM_DIR not in sys.path:
    sys.path.insert(0, SIM_DIR)
from halvern_sim.config import MAJOR_HOLIDAYS, calendar, federal_holidays  # noqa: E402

YEAR = 2027
HOLIDAYS_CSV = os.path.join(os.path.dirname(SIM_DIR), "sources", "derived", "federal_holidays_2027.csv")
WEATHER_CSV = os.path.join(os.path.dirname(SIM_DIR), "sources", "derived", "weather_days.csv")


def weather_counts():
    """Average storm and heat weekdays a year, 2015-2025 (the file's mean row)."""
    with open(WEATHER_CSV, newline="", encoding="utf-8") as f:
        mean = next(r for r in csv.DictReader(f) if r["year"].startswith("mean"))
    return float(mean["storm_weekdays"]), float(mean["heat_weekdays"])


STORM_DAYS, HEAT_DAYS = weather_counts()   # about 1.4 and 8.3

# class -> (representative days, weather, what the class covers)
CLASSES = {
    "holiday_major": ([dt.date(2027, 7, 5)], "ordinary", "New Year's, Memorial, Independence, Labor, Thanksgiving and Christmas Days (observed): banks, government and most offices closed"),
    "holiday_minor": ([dt.date(2027, 10, 11)], "ordinary", "MLK Day, Washington's Birthday, Juneteenth, Columbus and Veterans Days: banks and government closed, most private employers open"),
    "saturday": ([dt.date(2027, 10, 9)], "ordinary", "Saturdays"),
    "sunday": ([dt.date(2027, 10, 10)], "ordinary", "Sundays"),
    "eitc_wave": ([dt.date(2027, 3, 2)], "ordinary", "weekdays Feb 26-Mar 5 when EITC/ACTC refunds land (PATH Act hold)"),
    "ssi_first": ([dt.date(2027, 9, 1)], "ordinary", "first business day of the month: SSI paid"),
    "ss_third": ([dt.date(2027, 11, 3)], "ordinary", "the 3rd (or the business day before): Social Security for pre-1997 and SSI-linked recipients"),
    "ss_wednesday": ([dt.date(2027, 10, 13), dt.date(2027, 10, 20), dt.date(2027, 10, 27)], "ordinary", "2nd, 3rd and 4th Wednesdays: Social Security cohorts by birth date"),
    "friday": ([dt.date(2027, 10, 8), dt.date(2027, 10, 15)], "ordinary", "other Fridays, the main payday; two Fridays so both biweekly pay weeks are in"),
    "tax_season_weekday": ([dt.date(2027, 3, 16)], "ordinary", "other weekdays Jan 25-Apr 20 (tax season)"),
    "weekday_early": ([dt.date(2027, 10, 5)], "ordinary", "other weekdays, days 2-10 of the month (SNAP issuance window, rent)"),
    "weekday_mid": ([dt.date(2027, 10, 14)], "ordinary", "other weekdays, days 11-20"),
    "weekday_late": ([dt.date(2027, 10, 26)], "ordinary", "other weekdays, days 21-31"),
    "storm": ([dt.date(2027, 1, 19)], "storm", "winter or tropical storm weekdays that close schools (%.2f a year, NOAA 2015-25)" % STORM_DAYS),
    "heat": ([dt.date(2027, 7, 22)], "heat", "weekdays with a high of 95 F or more (%.2f a year, Atlanta airport 2015-25)" % HEAT_DAYS),
}


def holidays():
    with open(HOLIDAYS_CSV, newline="", encoding="utf-8") as f:
        return {dt.date.fromisoformat(r["observed_date"]) for r in csv.DictReader(f) if r["observed_date"].startswith(str(YEAR))}


def classify(d, hol):
    c = calendar(d)
    if d in hol:
        return "holiday_major" if federal_holidays(d.year).get(d) in MAJOR_HOLIDAYS else "holiday_minor"
    if c["dow"] == 5:
        return "saturday"
    if c["dow"] == 6:
        return "sunday"
    if c["eitc_wave"]:
        return "eitc_wave"
    if c["ssi_today"]:
        return "ssi_first"
    if "3rd" in c["ss_cohorts"]:
        return "ss_third"
    if c["ss_cohorts"]:
        return "ss_wednesday"
    if c["dow"] == 4:
        return "friday"
    if c["tax_season"]:
        return "tax_season_weekday"
    if c["dom"] <= 10:
        return "weekday_early"
    if c["dom"] <= 20:
        return "weekday_mid"
    return "weekday_late"


def day_set():
    """Rows of (date, class, weather, weight, covers); weights sum to the days in the year."""
    hol = holidays()
    counts = {}
    d = dt.date(YEAR, 1, 1)
    while d.year == YEAR:
        k = classify(d, hol)
        counts[k] = counts.get(k, 0) + 1
        d += dt.timedelta(days=1)
    counts["storm"], counts["heat"] = STORM_DAYS, HEAT_DAYS
    # storm and heat days replace ordinary weekdays, taken evenly from early, mid and late
    for k in ("weekday_early", "weekday_mid", "weekday_late"):
        counts[k] -= (STORM_DAYS + HEAT_DAYS) / 3.0
    rows = []
    for k, (days, weather, covers) in CLASSES.items():
        for day in days:
            if weather == "ordinary" and classify(day, hol) != k:
                raise ValueError("%s is not a %s day" % (day, k))
            rows.append({"date": day.isoformat(), "class": k, "weather": weather, "weight": counts[k] / len(days),
                         "class_days_2027": counts[k], "covers": covers})
    return rows


if __name__ == "__main__":
    rows = day_set()
    for r in rows:
        print("%s  %-19s %-8s weight %6.2f  (%g days)" % (r["date"], r["class"], r["weather"], r["weight"], r["class_days_2027"]))
    print("total weight %.2f over %d simulated days" % (sum(r["weight"] for r in rows), len(rows)))
