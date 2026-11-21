"""Group 3, change 6: hourly and gig workers' hours, and so their pay, change from week to week."""
import collections
import datetime as dt
import math
import os
import random
import statistics
from types import SimpleNamespace as NS

from conftest import read_csv
from medianville_sim import carry


def worker(pid, wsched="variable", emp="employed_part_time", gig=False):
    return NS(pid=pid, wsched=wsched, emp=emp, gig=gig)


def test_weekly_factor_is_deterministic_mean_one_and_correlated():
    c = carry.Carry(20270303, "2027-03-01")
    mon = dt.date(2027, 3, 1)
    xs, pairs = [], []
    for i in range(3000):
        p = worker("P%06d" % i)
        f = [carry.hours_factor(c, p, mon + dt.timedelta(days=7 * k)) for k in range(6)]
        assert f[0] == carry.hours_factor(carry.Carry(20270303, "2027-03-01"), p, mon + dt.timedelta(days=3))   # same week, same factor
        xs += f
        pairs += [(math.log(a), math.log(b)) for a, b in zip(f, f[1:])]
    assert abs(statistics.mean(xs) - 1) < .02
    assert abs(statistics.pstdev([math.log(x) for x in xs]) - carry.HOURS_SIGMA["variable"]) < .01
    a, b = zip(*pairs)
    r = statistics.correlation(a, b)
    assert abs(r - carry.HOURS_THETA / (1 + carry.HOURS_THETA ** 2)) < .05, r


def test_salaried_full_time_pay_does_not_move():
    c = carry.Carry(1, "2027-03-01")
    assert carry.hours_factor(c, worker("P1", wsched="fixed", emp="employed_full_time"), dt.date(2027, 3, 1)) == 1.0
    assert carry.hours_sigma(worker("P1", wsched="fixed", emp="employed_full_time", gig=True), gig=True) == carry.HOURS_SIGMA["gig"]


def test_variable_paychecks_swing_more_than_fixed_ones(carried10):
    per = {r["person_id"]: r for r in read_csv(os.path.join(carried10["days"][0][1], "persons.csv"))}
    pay = collections.defaultdict(list)
    for d, o in carried10["days"]:
        for r in read_csv(os.path.join(o, "records.csv")):
            if r["job_category"] == "income.paycheck_direct_deposit":
                pay[r["actor_person_id"]].append(float(r["amount_gross"]))
    chg = collections.defaultdict(list)
    for pid, v in pay.items():
        p = per[pid]
        if p["pay_cadence"] != "weekly" or len(v) < 2:
            continue
        g = "variable" if p["work_schedule"] == "variable" else "fixed_full" if p["employment_status"] == "employed_full_time" else "other"
        chg[g] += [abs(b - a) / ((a + b) / 2) for a, b in zip(v, v[1:])]
    assert len(chg["variable"]) > 100 and len(chg["fixed_full"]) > 100
    assert statistics.mean(chg["variable"]) > .10
    assert statistics.mean(chg["variable"]) > 4 * statistics.mean(chg["fixed_full"])
