"""Group 3, change 1: unpaid bills are retried on a schedule and pick up the late fee from the bill's terms."""
import datetime as dt

from conftest import chains
from medianville_sim.carry import CARD_GAPS, CARD_ONLY, GRACE, REPRESENT, REPRESENT_GAPS
from medianville_sim.config import calendar
from medianville_sim.day_a import LATE_FEE


def bank_days_between(a, b):
    d, n = a, 0
    while d < b:
        d += dt.timedelta(days=1)
        n += calendar(d)["bank_day"]
    return n


def test_each_chain_starts_with_a_missed_bill_and_links_back(carried10):
    ch = chains(carried10, "unpaid_bill")
    assert len(ch) > 300
    for cid, steps in ch.items():
        d0, l0, r0 = steps[0]
        assert l0["step"] in ("returned", "declined", "missed", "partial", "no_time") and not l0["earlier_record_id"], cid
        assert r0["record_type"] == "failed_attempt" or r0["outcome"] == "partial", cid
        for (da, la, ra), (db, lb, rb) in zip(steps, steps[1:]):
            assert (lb["earlier_date"], lb["earlier_record_id"]) == (da, la["record_id"]), cid
            assert db > da and rb["job_category"] == r0["job_category"], cid


def test_some_bills_are_paid_late_with_the_late_fee(carried10):
    # A late fee is charged once the grace period has run out. The one-day simulator already treats a few hand-made
    # payments as late (day_a.gen_bills, 4.5%); a retry of one of those carries the fee from the start.
    late = early = 0
    for steps in chains(carried10, "unpaid_bill").values():
        kind = steps[0][2]["job_category"].split(".")[1]
        due = dt.date.fromisoformat(steps[0][0])
        for d, l, r in steps[1:]:
            if r["record_type"] != "bill_payment":
                continue
            days = (dt.date.fromisoformat(d) - due).days
            g = GRACE.get(kind)
            past = g is not None and ((g == "5th" and dt.date.fromisoformat(d).day > 5) or (g != "5th" and days > g))
            if past and kind in LATE_FEE and "late_fee" in r["fee_type"]:
                lo, hi = LATE_FEE[kind]
                assert lo <= float(r["fee_amount"]) <= hi + 35 * 3, (kind, r["fee_amount"])   # the late fee, plus any returned-payment fees
                late += 1
            if "late_fee" in r["fee_type"] and not past:
                assert steps[0][1]["step"] in ("missed", "partial", "no_time"), (kind, d, steps[0][0])
                early += 1
    assert late > 20 and early < late / 4


def test_billers_represent_on_bank_days_twice_at_most(carried10):
    n = 0
    for steps in chains(carried10, "unpaid_bill").values():
        if steps[0][1]["step"] != "returned" or steps[0][2]["job_category"].split(".")[1] not in REPRESENT:
            continue
        rep = [s for s in steps[1:] if "sent the payment again" in s[2]["narrative"] or "re-sent payment bounced again" in s[2]["narrative"]]
        assert len(rep) <= len(REPRESENT_GAPS)
        prev = dt.date.fromisoformat(steps[0][0])
        for k, (d, l, r) in enumerate(rep):
            day = dt.date.fromisoformat(d)
            assert calendar(day)["bank_day"]
            assert bank_days_between(prev, day) == REPRESENT_GAPS[k], (d, k)
            prev = day
            n += 1
    assert n > 20


def test_card_retries_follow_the_dunning_schedule(carried10):
    n = 0
    for steps in chains(carried10, "unpaid_bill").values():
        if steps[0][1]["step"] != "declined" or steps[0][2]["job_category"].split(".")[1] not in CARD_ONLY or len(steps) < 2:
            continue
        gaps = [(dt.date.fromisoformat(b[0]) - dt.date.fromisoformat(a[0])).days for a, b in zip(steps, steps[1:])]
        assert gaps == list(CARD_GAPS[:len(gaps)]), gaps
        n += 1
    assert n > 10


def test_queue_is_carried_in_the_state(carried10):
    for st in carried10["states"]:
        q = st["carry"]["retries"]
        assert all(e["next"] is None or e["next"] > st["date"] for e in q)
        assert len({e["id"] for e in q}) == len(q)
