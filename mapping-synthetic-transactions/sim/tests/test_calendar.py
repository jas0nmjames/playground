"""Tests for the holiday-aware calendar: federal holidays, benefit dates, paydays and ACH autopays."""
import csv
import datetime as dt
import os
from types import SimpleNamespace

from conftest import SIM_DIR
from halvern_sim.config import calendar, federal_holidays
from halvern_sim.day_a import due_today, paid_today

OPM_CSV = os.path.join(os.path.dirname(SIM_DIR), "sources", "derived", "federal_holidays_2027.csv")


def _days(year=2027):
    d = dt.date(year, 1, 1)
    while d.year == year:
        yield d
        d += dt.timedelta(days=1)


def test_holidays_match_opm_2027():
    with open(OPM_CSV, newline="", encoding="utf-8") as f:
        opm = {dt.date.fromisoformat(r["observed_date"]) for r in csv.DictReader(f) if r["observed_date"].startswith("2027")}
    assert set(federal_holidays(2027)) == opm


def test_ssi_dates_match_ssa_2027():
    # SSA's 2027 schedule (EN-05-10031): SSI on the 1st, or the business day before; January 2027's was paid 2026-12-31
    want = ["2027-02-01", "2027-03-01", "2027-04-01", "2027-04-30", "2027-06-01", "2027-07-01", "2027-07-30",
            "2027-09-01", "2027-10-01", "2027-11-01", "2027-12-01", "2027-12-30"]
    assert [d.isoformat() for d in _days() if calendar(d)["ssi_today"]] == want


def test_social_security_3rd_moves_to_business_day_before():
    thirds = [d for d in _days() if "3rd" in calendar(d)["ss_cohorts"]]
    assert dt.date(2027, 7, 2) in thirds and dt.date(2027, 7, 3) not in thirds   # July 3, 2027 is a Saturday
    assert all(calendar(d)["bank_day"] for d in thirds)


def test_no_payroll_or_autopay_on_a_holiday():
    hol, fri, tue = calendar(dt.date(2027, 7, 5)), calendar(dt.date(2027, 7, 2)), calendar(dt.date(2027, 7, 6))
    assert hol["holiday"] == "Independence Day" and not hol["bank_day"] and not hol["school_day"]
    monday_payer = SimpleNamespace(cadence="weekly", payday=(0,))
    assert not paid_today(monday_payer, hol)
    assert paid_today(monday_payer, fri)          # paid the business day before
    bill = ("electric_bill", None, 100.0, 5, "ach_auto", None, "M", None)   # due on the 5th
    assert not due_today(bill, hol)
    assert due_today(bill, tue)                   # posts the next business day
    card = ("electric_bill", None, 100.0, 5, "card_auto", None, "M", None)
    assert due_today(card, hol)                   # card autopays still charge


def test_schools_open_on_columbus_and_veterans_day():
    assert calendar(dt.date(2027, 10, 11))["school_day"]
    assert calendar(dt.date(2027, 11, 11))["school_day"]
    assert not calendar(dt.date(2027, 9, 6))["school_day"]
