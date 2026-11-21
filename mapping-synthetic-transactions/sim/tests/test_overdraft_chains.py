"""Group 3, change 3: one overdraft leads to more fees, and sometimes to a late rent payment."""
import collections
import datetime as dt
import os

from conftest import chains, read_csv
from medianville_sim.carry import EXTENDED_OD_DAYS, OD_DAILY_CAP, OD_LIMIT, RENT_WINDOW


def test_every_overdraft_fee_is_in_a_chain(carried10):
    n = 0
    for date, folder in carried10["days"]:
        links = collections.defaultdict(set)
        for l in read_csv(os.path.join(folder, "links.csv")):
            links[l["record_id"]].add((l["chain"], l["step"]))
        for r in read_csv(os.path.join(folder, "records.csv")):
            if "overdraft_fee" in r["fee_type"]:
                steps = {s for c, s in links[r["record_id"]] if c == "overdraft"}
                assert steps & {"first_overdraft", "more_fees", "extended_fee"}, r["record_id"]
                n += 1
    assert n > 50


def test_fee_cap_and_overdraft_limit(carried10):
    for date, folder in carried10["days"]:
        per = collections.Counter(l["account_id"] for l in read_csv(os.path.join(folder, "links.csv"))
                                  if l["chain"] == "overdraft" and l["step"] in ("first_overdraft", "more_fees"))
        assert max(per.values() or [0]) <= OD_DAILY_CAP, date
        for r in read_csv(os.path.join(folder, "household_ledger.csv")):
            # one item may go to the limit, then its fee and an extended fee on top, per account
            assert float(r["close_checking"]) >= -(OD_LIMIT + 120) * int(r["wallets"]), (date, r["household_id"])


def test_chains_grow_across_days(carried10):
    ch = chains(carried10, "overdraft")
    multi = 0
    for cid, steps in ch.items():
        assert steps[0][1]["step"] == "first_overdraft" and not steps[0][1]["earlier_record_id"]
        for (da, la, ra), (db, lb, rb) in zip(steps, steps[1:]):
            assert lb["earlier_record_id"] and (lb["earlier_date"], lb["earlier_record_id"]) <= (db, lb["record_id"])
        days = {d for d, l, r in steps}
        multi += len(days) > 1
        for d, l, r in steps:
            if l["step"] == "extended_fee":
                assert (dt.date.fromisoformat(d) - dt.date.fromisoformat(steps[0][0])).days >= EXTENDED_OD_DAYS
                assert r["fee_type"] == "extended_overdraft_fee"
    assert multi >= 10


def test_rent_joins_an_overdraft_chain_only_after_a_recent_fee(carried10):
    for steps in chains(carried10, "overdraft").values():
        fees = [dt.date.fromisoformat(d) for d, l, r in steps if l["step"] in ("first_overdraft", "more_fees")]
        for d, l, r in steps:
            if l["step"] == "rent_missed":
                day = dt.date.fromisoformat(d)
                assert r["job_category"] in ("housing.rent", "housing.lot_rent")
                assert any(0 <= (day - f).days <= RENT_WINDOW for f in fees)
