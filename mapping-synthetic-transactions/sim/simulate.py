#!/usr/bin/env python3
"""Generate one simulated day (or several) of transactions for Halvern, a synthetic American city.

    python simulate.py                                  # Wednesday, March 3, 2027, full city, seed 20270303
    python simulate.py --date 2027-03-05 --out out_fri  # another day, same residents
    python simulate.py --weather storm                  # shock scenario
    python simulate.py --days 5 --out week              # move the city forward day by day, carrying balances
    python simulate.py --households 4000                # 10% sample for quick runs (weights in households.csv)
"""
import argparse
import csv
import datetime as dt
import json
import os
import time

from halvern_sim import context, main, output
from halvern_sim.config import PARAMS

HERE = os.path.dirname(os.path.abspath(__file__))


def load_overrides(path):
    ov = {}
    if path and os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ov[r["record_id"]] = (r["job_category"], r["actor_person_id"], r["job_statement"], r["narrative"])
    return ov


def save_state(sim, path):
    st = {"date": sim.cal["iso"], "wallets": {W.wid: [W.bank, W.cash, W.prepaid, W.cc_bal, W.savings] for W in sim.wallets},
          "benefits": {H.hid: [H.snap_bal, H.wic_bal] for H in sim.households if H.snap or H.wic}}
    with open(path, "w") as f:
        json.dump(st, f)


def load_state(sim, path):
    with open(path) as f:
        st = json.load(f)
    for W in sim.wallets:
        v = st["wallets"].get(W.wid)
        if v:
            W.bank, W.cash, W.prepaid, W.cc_bal, W.savings = v
            W.start = (W.bank, W.cash, W.prepaid, W.cc_bal, W.savings)
    for H in sim.households:
        v = st["benefits"].get(H.hid)
        if v:
            H.snap_bal, H.wic_bal = v
            if H.wallets:
                H.wallets[0].snap_start = H.snap_bal
    return st["date"]


def run_day(cfg, out, state_in=None, state_out=None, overrides=None, log=print):
    t0 = time.time()
    log("Halvern %s (seed %s, %s households, weather %s)" % (cfg["SIM_DATE"], cfg["RANDOM_SEED"], cfg["N_HOUSEHOLDS"], cfg["WEATHER"]))
    sim = main.build(cfg, log=log)
    if state_in:
        log("  carried balances forward from %s" % load_state(sim, state_in))
    main.simulate(sim, log=log)
    os.makedirs(out, exist_ok=True)
    output.write_tables(sim, out)
    # hand-written text belongs to the baseline day only (same date, seed, size, weather and prices, no carried state)
    baseline = not state_in and all(cfg.get(k) == PARAMS.get(k) for k in PARAMS)
    ov = load_overrides(overrides) if baseline else {}
    n_ov = sim.write_records(os.path.join(out, "records.csv"), ov)
    S = output.summarize(sim)
    context.write_context(sim, os.path.join(out, "public_services_context.csv"))
    context.write_assumptions(sim, os.path.join(out, "assumptions.csv"), S)
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as f:
        f.write(output.write_summary(sim, S, None, n_ov))
    if state_out:
        save_state(sim, state_out)
    log("  wrote %d records to %s (%d with hand-written text) in %.0fs" % (len(sim.rows), out, n_ov, time.time() - t0))
    return sim, S


def cli():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=PARAMS["SIM_DATE"].isoformat(), help="simulation date, YYYY-MM-DD")
    ap.add_argument("--seed", type=int, default=PARAMS["RANDOM_SEED"])
    ap.add_argument("--households", type=int, default=PARAMS["N_HOUSEHOLDS"], help="41400 is the full city")
    ap.add_argument("--weather", default=PARAMS["WEATHER"], choices=["ordinary", "storm", "heat"])
    ap.add_argument("--out", default="out")
    ap.add_argument("--days", type=int, default=1, help="simulate this many consecutive days, carrying balances forward")
    ap.add_argument("--state-in", help="balances saved by an earlier run (state.json)")
    ap.add_argument("--state-out", help="where to save end-of-day balances")
    ap.add_argument("--gas-price", type=float, default=PARAMS["GAS_PRICE"])
    ap.add_argument("--grocery-price-mult", type=float, default=PARAMS["GROCERY_PRICE_MULT"])
    ap.add_argument("--portal-outage", default="640-805", help="state benefits portal outage as START-END minutes after midnight, or 'none'")
    ap.add_argument("--overrides", default=os.path.join(HERE, "detailed_overrides.csv"), help="hand-written text for sampled records")
    a = ap.parse_args()
    cfg = dict(PARAMS)
    cfg.update(RANDOM_SEED=a.seed, N_HOUSEHOLDS=a.households, WEATHER=a.weather, GAS_PRICE=a.gas_price, GROCERY_PRICE_MULT=a.grocery_price_mult)
    cfg["BENEFITS_PORTAL_OUTAGE"] = (-1, -1) if a.portal_outage == "none" else tuple(int(x) for x in a.portal_outage.split("-"))
    day = dt.date.fromisoformat(a.date)
    state = a.state_in
    for i in range(a.days):
        cfg["SIM_DATE"] = day + dt.timedelta(days=i)
        out = a.out if a.days == 1 else os.path.join(a.out, cfg["SIM_DATE"].isoformat())
        st_out = a.state_out if a.days == 1 else os.path.join(a.out, "state_%s.json" % cfg["SIM_DATE"].isoformat())
        if a.days > 1:
            os.makedirs(a.out, exist_ok=True)
        run_day(cfg, out, state_in=state, state_out=st_out, overrides=a.overrides)
        state = st_out


if __name__ == "__main__":
    cli()
