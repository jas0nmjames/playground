"""Group 3, change 2: a shutoff notice starts a timer: notice, grace, disconnection, reconnection fee and reconnection."""
import datetime as dt
import os
import re

from conftest import chains, read_csv
from medianville_sim.carry import CREW_DAYS
from medianville_sim.config import calendar


def test_disconnections_come_only_from_timers(carried10):
    n = 0
    for date, folder in carried10["days"]:
        recs = read_csv(os.path.join(folder, "records.csv"))
        links = {l["record_id"]: l for l in read_csv(os.path.join(folder, "links.csv"))}
        for r in recs:
            if r["job_category"] == "utilities.service_disconnected_for_nonpayment":
                assert links[r["record_id"]]["step"] == "disconnected"
                n += 1
    assert n >= 5


def test_shutoff_waits_for_the_notice_date_and_a_crew_day(carried10):
    for steps in chains(carried10, "utility_shutoff").values():
        notice = next((s for s in steps if s[1]["step"] == "notice"), None)
        for d, l, r in steps:
            if l["step"] != "disconnected":
                continue
            day = dt.date.fromisoformat(d)
            assert calendar(day)["bank_day"] and day.weekday() in CREW_DAYS
            if notice is not None:
                days = int(re.search(r"disconnection in (\d+) days", notice[2]["narrative"]).group(1))
                assert day >= dt.date.fromisoformat(notice[0]) + dt.timedelta(days=days)
            else:
                assert l["note"] == "notice sent before the run began" or l["earlier_record_id"]


def test_reconnection_costs_a_fee_time_and_a_day(carried10):
    paid = back = 0
    for steps in chains(carried10, "utility_shutoff").values():
        seen = {}
        for d, l, r in steps:
            seen.setdefault(l["step"], d)
            if l["step"] == "reconnection_paid":
                assert "reconnection_fee" in r["fee_type"] and float(r["fee_amount"]) >= 35
                assert int(r["time_minutes"]) >= 12 and (r["channel"] == "phone" or float(r["travel_miles"]) > 0)
                assert seen["disconnected"] <= d
                paid += 1
            if l["step"] == "reconnected":
                assert "reconnection_paid" in seen or "assistance_pledged" in seen
                assert d > seen.get("reconnection_paid", seen.get("assistance_pledged"))
                assert calendar(dt.date.fromisoformat(d))["bank_day"]
                back += 1
    assert paid >= 3 and back >= 3


def test_notices_mostly_end_before_a_shutoff(carried10):
    notices = shut = 0
    for steps in chains(carried10, "utility_shutoff").values():
        if steps[0][1]["step"] == "notice":
            notices += 1
            shut += any(s[1]["step"] == "disconnected" for s in steps)
    assert notices >= 30 and shut / notices < .5


def test_timers_carry_in_the_state(carried10):
    for st in carried10["states"]:
        for hid, T in st["carry"]["util"].items():
            assert T["hid"] == hid and T["state"] in ("notice", "off")
            assert T["state"] != "off" or T["off"] <= st["date"]
