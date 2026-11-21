"""Group 3, change 4: payday and title loans roll over, with renewal fees, from one day to the next."""
import collections
import datetime as dt
import os
import re

from conftest import chains, read_csv
from medianville_sim.carry import PAYDAY_REPRESENT, PAYDAY_TERM_MIN
from medianville_sim.day_c import TITLE_SINGLE_FEE


def test_payday_chains_link_back_or_start_before_the_run(carried10):
    ch = chains(carried10, "payday_loan")
    assert len(ch) >= 20
    for cid, steps in ch.items():
        d0, l0, r0 = steps[0]
        assert l0["step"] == "borrowed" or l0["note"] == "loan taken before the run began", cid
        for (da, la, ra), (db, lb, rb) in zip(steps, steps[1:]):
            assert (lb["earlier_date"], lb["earlier_record_id"]) == (da, la["record_id"])
            assert db > da


def test_renewals_charge_the_fee_again_and_move_the_due_date(carried10):
    n = 0
    for steps in chains(carried10, "payday_loan").values():
        ren = [(dt.date.fromisoformat(d), r) for d, l, r in steps if l["step"] == "renewed"]
        nums = [int(re.search(r"Renewal number (\d+)", r["narrative"]).group(1)) for d, r in ren]
        assert nums == list(range(nums[0], nums[0] + len(nums))) if nums else True
        for (da, ra), (db, rb) in zip(ren, ren[1:]):
            assert (db - da).days >= PAYDAY_TERM_MIN
            assert ra["fee_amount"] == rb["fee_amount"] and float(ra["amount_paid_by_user"]) == float(ra["fee_amount"])
        for d, r in ren:
            principal = float(r["amount_gross"]) - float(r["fee_amount"])
            assert .15 * principal - .02 <= float(r["fee_amount"]) <= .175 * 1.6 * principal + .02
            n += 1
    assert n >= 10


def test_most_loans_due_are_renewed(carried10):
    c = collections.Counter(l["step"] for steps in chains(carried10, "payday_loan").values() for d, l, r in steps)
    due = c["renewed"] + c["repaid"] + c["bounced"]
    assert due >= 20 and .6 <= c["renewed"] / due <= .92       # CFPB 2014: over 80% renewed within 14 days


def test_bounced_loans_are_represented_twice_then_collected():
    """The lender's schedule after a bounce, on a stub city: re-presented 3 and then 5 business days later, then sold to
    a collector. (Bounces are rare enough that a 12-day 10% run may have none.)"""
    import random
    from types import SimpleNamespace as NS
    from medianville_sim import carry
    from test_retry_queue import bank_days_between
    c = carry.Carry(1, "2027-03-01")
    c.today, c.date, c._cal, c.crng, c.links, c.refs = dt.date(2027, 3, 1), "2027-03-01", {}, random.Random(1), [], []
    sim = NS(emit=lambda *a, **k: 0)
    H = NS(hid="H1")
    W = NS(wid="H1-W1", hh=H)
    L = dict(id="P1", status="open", tries=0, fee=45.0, last=None)
    prev = c.today
    for n, gap in enumerate(PAYDAY_REPRESENT):
        carry._payday_bounce(c, sim, L, H, W, NS(pid="P1"), 300, NS(name="lender"), 345.0, {}, "payday_loan_repayment")
        assert L["status"] == "default" and L["tries"] == n + 1
        due = dt.date.fromisoformat(L["due"])
        assert bank_days_between(prev, due) == gap
        prev = c.today = due
        c.date = due.isoformat()
    carry._payday_bounce(c, sim, L, H, W, NS(pid="P1"), 300, NS(name="lender"), 345.0, {}, "payday_loan_repayment")
    assert L["status"] == "collections"
    assert [l["step"] for l in c.links] == ["bounced"] * (len(PAYDAY_REPRESENT) + 1)


def test_loan_book_states(carried10):
    for st in carried10["states"]:
        for L in st["carry"]["loans"]:
            assert L["status"] in ("open", "default", "collections")
            assert (L["status"] == "open") == (L["tries"] == 0)
            assert L["status"] == "collections" or L["due"] > st["date"]


def test_title_rollovers_renew_the_fee_and_lost_cars_stay_lost(carried10):
    ch = chains(carried10, "title_loan")
    n = 0
    for steps in ch.values():
        for d, l, r in steps:
            if l["step"] == "rolled_over":
                m = re.search(r"\$([\d.]+) (?:in fees|rollover fee).*?\$(\d+)", r["narrative"])
                fee, owed = float(m.group(1)), float(m.group(2))
                assert abs(fee - TITLE_SINGLE_FEE * owed) <= 1.0, r["narrative"]
                n += 1
    assert n >= 1
    dates = [d for d, _ in carried10["days"]]
    veh = [{r["household_id"]: int(r["vehicles"]) for r in read_csv(os.path.join(o, "households.csv"))} for d, o in carried10["days"]]
    for steps in ch.values():
        for d, l, r in steps:
            if l["step"] == "repossessed":
                k = dates.index(d)
                hid = r["household_id"]
                assert all(v[hid] <= veh[k][hid] for v in veh[k + 1:]), hid
                assert all(st["carry"]["tloans"][hid] is None for st in carried10["states"][k:])
