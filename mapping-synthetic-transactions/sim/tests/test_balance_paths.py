"""Group 3, change 5: SNAP balances run down from the load day, and checking follows the pay calendar."""
import collections
import datetime as dt
import os
import statistics

from conftest import read_csv


def per_day(carried, name):
    return [(d, read_csv(os.path.join(o, name))) for d, o in carried["days"]]


def test_snap_runs_down_from_the_load_day(carried10):
    days = [d for d, _ in carried10["days"]]
    led = {d: {r["household_id"]: float(r["snap_close"]) for r in rows} for d, rows in per_day(carried10, "household_ledger.csv")}
    loads = {}
    for d, recs in per_day(carried10, "records.csv"):
        for r in recs:
            if r["job_category"] == "income.snap_issuance":
                loads[r["household_id"]] = (d, float(r["amount_gross"]))
    share = collections.defaultdict(list)
    for h, (d0, amt) in loads.items():
        k0 = days.index(d0)
        for k in range(k0, len(days)):
            share[k - k0].append(led[days[k]][h] / amt)
    assert len(loads) > 300
    mean = {k: statistics.mean(v) for k, v in share.items() if len(v) >= 50}
    assert mean[0] > .85 and mean[7] < .55, mean
    ks = sorted(mean)
    assert all(mean[a] >= mean[b] - .02 for a, b in zip(ks, ks[1:])), mean


def test_checking_rises_on_payday_and_falls_between(carried10):
    days = [d for d, _ in carried10["days"]]
    chk = {d: {r["household_id"]: float(r["close_checking"]) for r in rows} for d, rows in per_day(carried10, "household_ledger.csv")}
    pay = collections.defaultdict(set)
    for d, recs in per_day(carried10, "records.csv"):
        for r in recs:
            if r["job_category"] == "income.paycheck_direct_deposit":
                pay[r["household_id"]].add(d)
    up = down = 0
    for h, ds in pay.items():
        for d in ds:
            k = days.index(d)
            if k == 0:
                continue
            up += chk[d][h] > chk[days[k - 1]][h]
            down += chk[d][h] < chk[days[k - 1]][h]
    assert up > 3 * down and up > 500


def test_one_refund_and_one_return_a_season(carried10):
    refunds, returns = collections.Counter(), collections.Counter()
    for d, recs in per_day(carried10, "records.csv"):
        for r in recs:
            k = r["job_category"].split(".")[1]
            if k == "federal_tax_refund":
                refunds[r["actor_person_id"]] += 1
            if k in ("paid_tax_preparation", "tax_software_filing", "tax_return_filed_free", "free_tax_preparation") and r["outcome"] in ("completed", "partial"):
                returns[r["household_id"]] += 1
    assert refunds and max(refunds.values()) == 1
    assert returns and max(returns.values()) == 1
    st = carried10["states"][-1]["carry"]
    assert len(st["refunded"]) > len(refunds) and len(st["filed"]) > len(returns)   # the season before the run counts too


def test_surplus_moves_to_savings_on_money_days(carried10):
    n = 0
    for d, recs in per_day(carried10, "records.csv"):
        for r in recs:
            if r["job_category"] == "money_services.transfer_to_savings" and r["timestamp_local"][11:13] >= "20":
                n += 1
    assert n > 20
