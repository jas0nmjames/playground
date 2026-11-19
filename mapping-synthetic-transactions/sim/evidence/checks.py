#!/usr/bin/env python3
"""Evidence checks: measure simulated days against sim/evidence_targets.csv (plan, sections 2 and 4).

    python3 evidence/checks.py run OUT_DIR [--households N] [--keep] [--label TEXT]   simulate the typed-day set and report
    python3 evidence/checks.py measure RUN_DIR                         measure one existing output folder

`run` simulates every day in evidence/typed_days.py with the simulator in sim/, measures each day,
and writes to OUT_DIR:
    <date>/summary.md, <date>/metrics.json    per day (the large CSVs are deleted unless --keep)
    typed_day_metrics.csv                      one row per day and metric
    evidence_checks.md                         every target against the weighted year

The checks only read the simulator's output; they change nothing the simulator generates. They are
written to their own file rather than into summary.md so that v1 still reproduces byte for byte.
"""
import csv
import datetime as dt
import json
import os
import shutil
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(HERE)
for p in (SIM_DIR, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import typed_days  # noqa: E402

TARGETS = os.path.join(SIM_DIR, "evidence_targets.csv")

ABSENT_KINDS = {  # T14: jobs the plan lists as truly absent, matched by substring of job_category
    "car_disabled_by_lender": "car_disabled_by_lender",
    "direct_express_failure": "direct_express",
    "called_in_on_day_off": "called_in",
    "snap_interview_call": "snap_interview",
}


def kind(r):
    return r["job_category"].split(".", 1)[1]


def money(s):
    return float(s) if s else 0.0


def measure_rows(records, households, S=None):
    """Return {metric: value} for one simulated day. Counts are per day; shares carry numerator and denominator."""
    k = Counter(kind(r) for r in records)
    m = {}
    m["overdraft_fees"] = sum(1 for r in records if "overdraft_fee" in r["fee_type"])
    m["overdraft_fee_dollars"] = round(sum(money(r["fee_amount"]) for r in records if r["fee_type"] == "overdraft_fee"), 2)
    m["payday_loans_new"] = k["payday_loan_disbursed"]
    m["payday_rollovers"] = k["payday_loan_rollover"]
    m["payday_repayments"] = k["payday_loan_repayment"]
    m["title_loans_new"] = k["title_loan_disbursed"]
    m["title_loan_payments"] = sum(v for kk, v in k.items() if "title_loan_payment" in kk)
    m["title_repossessions"] = sum(v for kk, v in k.items() if "reposs" in kk)
    m["utility_disconnections"] = k["service_disconnected_for_nonpayment"]
    m["utility_shutoff_notices"] = k["shutoff_notice_received"]
    m["utility_reconnections"] = k["reconnection_payment"]
    m["care_delayed_by_debt"] = sum(v for kk, v in k.items() if "delayed" in kk and "debt" in kk)
    m["medical_payment_plans"] = k["medical_payment_plan"]
    m["caregiving_hours_home"] = round(sum(money(r["time_minutes"]) for r in records if kind(r) == "caregiving_at_home") / 60.0, 1)
    m["caregiving_hours_visits"] = round(sum(money(r["time_minutes"]) for r in records if kind(r) == "caregiving_visit") / 60.0, 1)
    m["caregiving_zero_dollar_records"] = sum(1 for r in records if r["job_category"].startswith("care_and_household.caregiving")
                                              and money(r["amount_paid_by_user"]) == 0)
    aide = [r for r in records if kind(r) == "personal_care_aide_visit"]
    missed = {r["record_id"] for r in aide if r["outcome"] != "completed"}
    linked = {r["related_record_id"] for r in records if r["related_record_id"] in missed}
    m["aide_visits"] = len(aide)
    m["aide_visits_missed"] = len(missed)
    m["aide_misses_with_linked_record"] = len(linked)
    m["scam_attempts"] = k["scam_attempt_handled"] + k["scam_loss"]
    m["scam_losses"] = k["scam_loss"]
    m["scam_loss_dollars"] = round(sum(money(r["amount_paid_by_user"]) for r in records if kind(r) == "scam_loss"), 2)
    m["scam_loss_max"] = max([money(r["amount_paid_by_user"]) for r in records if kind(r) == "scam_loss"] or [0.0])
    m["benefits_cliff_job"] = sum(v for kk, v in k.items() if "benefits_cliff" in kk)
    m["benefits_cliff_tagged"] = sum(1 for r in records if "benefits_cliff" in r["friction_tags"])
    m["paid_tax_prep"] = k["paid_tax_preparation"]
    m["free_tax_prep"] = k["free_tax_preparation"]
    m["pawn"] = k["pawn_loan"] + k["pawn_redemption"] + k["sold_item_to_pawn_shop"]
    m["check_cashing"] = k["check_cashing"]
    m["money_orders"] = k["money_order_purchase"]
    for name, pat in ABSENT_KINDS.items():
        m["absent_" + name] = sum(v for kk, v in k.items() if pat in kk)
    m["absent_h2a_households"] = sum(1 for h in households if "h2a" in h["household_type"].lower())
    if S is not None:
        share, n = S["cash_rural"]
        m["rural_payments"], m["rural_cash_payments"] = n, round(share * n)
    m["records"] = len(records)
    return m


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def measure_dir(run_dir, S=None):
    return measure_rows(read_csv(os.path.join(run_dir, "records.csv")), read_csv(os.path.join(run_dir, "households.csv")), S)


# --- combining the typed days into a year -----------------------------------------------------

def year_value(metric, days):
    """Weighted value for the year (per-day average, or a pooled share)."""
    W = sum(d["weight"] for d in days)
    if metric == "cash_share_rural":
        num = sum(d["weight"] * d["m"]["rural_cash_payments"] for d in days)
        den = sum(d["weight"] * d["m"]["rural_payments"] for d in days)
        return num / den if den else None
    if metric == "paid_prep_share":
        num = sum(d["weight"] * d["m"]["paid_tax_prep"] for d in days)
        den = num + sum(d["weight"] * d["m"]["free_tax_prep"] for d in days)
        return num / den if den else None
    if metric == "aide_visit_miss_share":
        num = sum(d["weight"] * d["m"]["aide_visits_missed"] for d in days)
        den = sum(d["weight"] * d["m"]["aide_visits"] for d in days)
        return num / den if den else None
    if metric == "scam_loss_share":
        num = sum(d["weight"] * d["m"]["scam_losses"] for d in days)
        den = sum(d["weight"] * d["m"]["scam_attempts"] for d in days)
        return num / den if den else None
    if metric == "fringe_services":
        return sum(d["weight"] * (d["m"]["pawn"] + d["m"]["check_cashing"] + d["m"]["money_orders"]) for d in days) / W
    if metric == "absent_jobs":
        return sum(d["weight"] * sum(v for kk, v in d["m"].items() if kk.startswith("absent_")) for d in days) / W
    return sum(d["weight"] * d["m"][metric] for d in days) / W


def verdict(t, v):
    if v is None:
        return "no data"
    lo = float(t["target_low"]) if t["target_low"] else None
    hi = float(t["target_high"]) if t["target_high"] else None
    c = t["check"]
    if c == "present":
        return "present" if v > 0 else "ABSENT"
    if c == "report":
        return "reported"
    if c == "range":
        return "in range" if lo <= v <= hi else ("LOW" if v < lo else "HIGH")
    if c == "range_tol":
        return "in range" if lo * .75 <= v <= hi * 1.25 else ("LOW" if v < lo else "HIGH")
    if c == "point_tol":
        return "in range" if abs(v - lo) <= .02 else ("LOW" if v < lo else "HIGH")
    return "?"


def fmt(metric, v):
    if v is None:
        return "-"
    if metric.endswith("_share") or metric == "cash_share_rural":
        return "%.1f%%" % (100 * v)
    return "{:,.1f}".format(v) if abs(v) < 1000 else "{:,.0f}".format(v)


def per_day_value(metric, d):
    return year_value(metric, [dict(d, weight=1.0)])


def write_report(out, days, baseline=None, label="v2 in progress (`sim/`)"):
    targets = read_csv(TARGETS)
    L = ["# Evidence checks: the typed-day set", "",
         "Simulator: %s. %d simulated days stand for 2027; each day's weight is the number of "
         "2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled "
         "shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence "
         "report's ids and grades are filled in." % (label, len(days)), "",
         "## Targets against the weighted year", "",
         "| Target | Item | Year (weighted) | Mar 3 | Target | Verdict | Status |", "|---|---|---|---|---|---|---|"]
    for t in targets:
        v = year_value(t["metric"], days)
        b = per_day_value(t["metric"], baseline) if baseline else None
        tgt = t["tolerance"] if t["check"] in ("present", "report") else "%s to %s %s" % (t["target_low"], t["target_high"], t["unit"])
        if t["check"] == "report" and t["target_high"]:
            tgt = "about %s %s (provisional)" % (t["target_high"], t["unit"])
        if t["check"] == "point_tol":
            tgt = "%.0f%% (%s)" % (100 * float(t["target_low"]), t["tolerance"])
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (t["target_id"], t["item"], fmt(t["metric"], v), fmt(t["metric"], b), tgt,
                                                       verdict(t, v), t["status"]))
    L += ["", "## Each day", ""]
    show = ["overdraft_fees", "payday_loans_new", "title_loans_new", "utility_shutoff_notices", "utility_disconnections",
            "caregiving_hours_home", "aide_visits_missed", "scam_losses", "paid_tax_prep", "free_tax_prep", "records"]
    L.append("| Date | Class | Weather | Weight | " + " | ".join(s.replace("_", " ") for s in show) + " |")
    L.append("|---|---|---|---|" + "---|" * len(show))
    for d in ([baseline] if baseline else []) + days:
        L.append("| %s | %s | %s | %.1f | " % (d["date"], d["cls"], d["weather"], d["weight"]) +
                 " | ".join("{:,}".format(d["m"][s]) if isinstance(d["m"][s], int) else "{:,.1f}".format(d["m"][s]) for s in show) + " |")
    L += ["", "## Supporting figures (weighted year, per day)", ""]
    for s in ("overdraft_fee_dollars", "payday_rollovers", "payday_repayments", "title_loans_new", "utility_shutoff_notices",
              "utility_reconnections", "medical_payment_plans", "caregiving_hours_visits", "caregiving_zero_dollar_records",
              "aide_visits", "aide_misses_with_linked_record", "scam_attempts", "scam_loss_dollars", "benefits_cliff_tagged",
              "pawn", "check_cashing", "money_orders") + tuple("absent_" + a for a in ABSENT_KINDS) + ("absent_h2a_households",):
        L.append("- %s: %s" % (s.replace("_", " "), fmt(s, year_value(s, days))))
    mx = max(d["m"]["scam_loss_max"] for d in days)
    L.append("- largest single scam loss on any typed day: ${:,.0f}".format(mx))
    L += ["", "## Limits", "",
          "- Each day is simulated from the same opening balances; nothing carries between days (option A). Chains such as "
          "notice to shutoff, and the concentration of overdraft fees, need the month run (option B).",
          "- Most classes are represented by October days. Heating-season (Nov-Mar) and cooling-season (Jun-Sep) effects are "
          "only in the days that fall in those months.",
          "- The simulator has no federal-holiday logic, so the holiday day runs as an ordinary weekday.",
          "- Storm and heat day counts (%d and %d) are placeholders until NOAA Storm Events data is downloaded." % (typed_days.STORM_DAYS, typed_days.HEAT_DAYS)]
    with open(os.path.join(out, "evidence_checks.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def run(out, households=None, keep=False, label="v2 in progress (`sim/`)"):
    import simulate
    from halvern_sim.config import PARAMS
    os.makedirs(out, exist_ok=True)
    days = []
    baseline = None
    ref = {"date": "2027-03-03", "class": "Mar 3 baseline (not weighted)", "weather": "ordinary", "weight": 0.0}
    for row in typed_days.day_set() + [ref]:
        cfg = dict(PARAMS)
        cfg["SIM_DATE"] = dt.date.fromisoformat(row["date"])
        cfg["WEATHER"] = row["weather"]
        if households:
            cfg["N_HOUSEHOLDS"] = households
        d_out = os.path.join(out, row["date"] + ("" if row["weather"] == "ordinary" else "_" + row["weather"]))
        sim, S = simulate.run_day(cfg, d_out, overrides=None, log=lambda *a: None)
        m = measure_dir(d_out, S)
        with open(os.path.join(d_out, "metrics.json"), "w") as f:
            json.dump(dict(row, metrics=m), f, indent=1)
        if not keep:
            for name in os.listdir(d_out):
                if name.endswith(".csv"):
                    os.remove(os.path.join(d_out, name))
        d = dict(date=row["date"], cls=row["class"], weather=row["weather"], weight=row["weight"], m=m)
        if row is ref:
            baseline = d
        else:
            days.append(d)
        print("%s %-26s %-8s %6d records  overdraft %4d  payday %3d  disconnections %3d" % (
            row["date"], row["class"], row["weather"], m["records"], m["overdraft_fees"], m["payday_loans_new"], m["utility_disconnections"]), flush=True)
    with open(os.path.join(out, "typed_day_metrics.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "class", "weather", "weight", "metric", "value"])
        for d in days:
            for k2, v in d["m"].items():
                w.writerow([d["date"], d["cls"], d["weather"], "%.4f" % d["weight"], k2, v])
    write_report(out, days, baseline, label)
    print("wrote", os.path.join(out, "evidence_checks.md"))


def main(argv):
    if argv[:1] == ["measure"]:
        print(json.dumps(measure_dir(argv[1]), indent=1))
    elif argv[:1] == ["run"]:
        hh = int(argv[argv.index("--households") + 1]) if "--households" in argv else None
        label = argv[argv.index("--label") + 1] if "--label" in argv else "v2 in progress (`sim/`)"
        run(argv[1], hh, "--keep" in argv, label)
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
