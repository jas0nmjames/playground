#!/usr/bin/env python3
"""Evidence checks for a carried month (plan section 4, option B; phase 4).

    python3 evidence/month.py MONTH_DIR OUT_DIR [--label TEXT]

MONTH_DIR is what `simulate.py --date 2027-03-01 --days 31 --out MONTH_DIR` writes: one folder per day (records.csv,
links.csv, household_ledger.csv, ...) and a state file per day. Writes to OUT_DIR:
    evidence_checks.md      the month's targets (month_targets.csv), the chains, and the typed-day targets over the month
    summary.md              the month in figures, day by day
and to MONTH_DIR (it goes in the bundle, not the repo):
    month_day_metrics.csv   one row per day and metric

Read-only: nothing here changes what the simulator generates.
"""
import collections
import csv
import datetime as dt
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(HERE)
for p in (SIM_DIR, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import checks  # noqa: E402

TARGETS = os.path.join(HERE, "month_targets.csv")
FEE_STEPS = ("first_overdraft", "more_fees", "extended_fee")


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def kind(r):
    return r["job_category"].split(".", 1)[1]


def measure(month):
    days = sorted(d for d in os.listdir(month) if d[:4].isdigit() and os.path.isdir(os.path.join(month, d)))
    D = [dt.date.fromisoformat(d) for d in days]
    households = read_csv(os.path.join(month, days[0], "households.csv"))
    persons = {p["person_id"]: p for p in read_csv(os.path.join(month, days[0], "persons.csv"))}
    status = {h["household_id"]: h["alice_status"] for h in households}
    reg = {h["household_id"] for h in households if not h["household_type"].startswith("group_quarters")}
    snap_monthly = {}
    for h in households:
        for n in h["notes"].split(";"):
            if n.startswith("snap_monthly="):
                snap_monthly[h["household_id"]] = float(n.split("=")[1])
    M = dict(days=days)
    per_day = []
    chains = collections.defaultdict(list)          # chain_id -> [(day index, step, account)]
    od_fees = collections.Counter()
    by_type = collections.Counter()
    kinds = collections.Counter()
    snap_close = collections.defaultdict(dict)
    chk = collections.defaultdict(dict)
    snap_load, paydays = {}, collections.defaultdict(set)
    pay = collections.defaultdict(list)
    for k, d in enumerate(days):
        folder = os.path.join(month, d)
        recs = read_csv(os.path.join(folder, "records.csv"))
        m = checks.measure_rows(recs, households)
        kc = collections.Counter(kind(r) for r in recs)
        m["payday_rollovers_storefront"] = kc["payday_loan_rollover"]
        m["payday_loans_and_renewals"] = kc["payday_loan_disbursed"] + kc["payday_loan_rollover"]
        m["failed_attempts"] = sum(1 for r in recs if r["record_type"] == "failed_attempt")
        m["late_fees"] = sum(1 for r in recs if "late_fee" in r["fee_type"])
        m["reconnections"] = kc["service_reconnected"]
        m["extended_overdraft_fees"] = kc["extended_overdraft_fee"]
        for r in recs:
            by_type[r["record_type"]] += 1
            kinds[r["job_category"]] += 1
            kk = kind(r)
            if kk == "snap_issuance":
                snap_load[r["household_id"]] = k
            elif kk == "paycheck_direct_deposit":
                paydays[r["household_id"]].add(k)
            if kk.startswith("paycheck_"):
                pay[r["actor_person_id"]].append(float(r["amount_gross"]))
        links = read_csv(os.path.join(folder, "links.csv"))
        m["links"] = len(links)
        for l in links:
            chains[(l["chain"], l["chain_id"])].append((k, l["step"], l["account_id"]))
            if l["chain"] == "overdraft" and l["step"] in FEE_STEPS:
                od_fees[l["account_id"]] += 1
        for r in read_csv(os.path.join(folder, "household_ledger.csv")):
            h = r["household_id"]
            chk[h][k] = float(r["close_checking"])
            if h in snap_monthly:
                snap_close[h][k] = float(r["snap_close"])
            if r["reconciles"] != "yes":
                m["ledger_bad"] = m.get("ledger_bad", 0) + 1
        m.setdefault("ledger_bad", 0)
        per_day.append(m)
        print("%s %7d records  overdraft %4d  notices %3d  disconnections %3d  payday+renewals %3d" % (
            d, m["records"], m["overdraft_fees"], m["utility_shutoff_notices"], m["utility_disconnections"], m["payday_loans_and_renewals"]), flush=True)
    M["per_day"] = per_day
    M["by_type"], M["kinds"] = by_type, kinds
    n = len(days)

    def avg(key):
        return sum(m[key] for m in per_day) / n
    V = {}
    for key in ("overdraft_fees", "utility_disconnections", "utility_shutoff_notices", "payday_loans_and_renewals", "title_loan_payments"):
        V[key] = avg(key)
    # overdraft concentration
    st = json.load(open(os.path.join(month, "state_%s.json" % days[-1])))
    accounts = sum(1 for v in st["wallets"].values() if v[0] is not None)
    tot = sum(od_fees.values())
    srt = sorted(od_fees.values(), reverse=True)
    acc = k79 = 0
    for v in srt:
        acc += v
        k79 += 1
        if acc >= .79 * tot:
            break
    V["od_accounts_for_79"] = k79 / accounts
    M["od"] = dict(accounts=accounts, paying=len(od_fees), fees=tot, top9=sum(srt[:int(round(.09 * accounts))]) / max(1, tot),
                   per_account=collections.Counter(min(v, 10) for v in od_fees.values()))
    # chains
    od_chains = [v for (c, i), v in chains.items() if c == "overdraft"]
    late_rent = [v for v in od_chains if any(s == "rent_missed" for _, s, _ in v) and any(s in ("late_rent_paid", "late_rent_part") for _, s, _ in v)]
    V["od_late_rent_chains"] = len(late_rent)
    M["od_chains"] = dict(chains=len(od_chains), multi_day=sum(1 for v in od_chains if len({k for k, _, _ in v}) > 1),
                          with_more_fees=sum(1 for v in od_chains if any(s == "more_fees" for _, s, _ in v)),
                          extended=sum(1 for v in od_chains if any(s == "extended_fee" for _, s, _ in v)),
                          rent_missed=sum(1 for v in od_chains if any(s == "rent_missed" for _, s, _ in v)), late_rent=len(late_rent),
                          fees_per_chain=statistics.mean(sum(1 for _, s, _ in v if s in FEE_STEPS) for v in od_chains) if od_chains else 0)
    util = [v for (c, i), v in chains.items() if c == "utility_shutoff"]
    early = [v for v in util if v[0][1] == "notice" and v[0][0] < 20]
    V["notice_to_shutoff"] = sum(1 for v in early if any(s == "disconnected" for _, s, _ in v)) / max(1, len(early))
    disc = [v for v in util if any(s == "disconnected" and k < 24 for k, s, _ in v)]
    V["reconnected_share"] = sum(1 for v in disc if any(s == "reconnected" for _, s, _ in v)) / max(1, len(disc))
    off_days = []
    for v in disc:
        k0 = min(k for k, s, _ in v if s == "disconnected")
        ks = [k for k, s, _ in v if s == "reconnected"]
        if ks:
            off_days.append(min(ks) - k0)
    steps = collections.Counter(s for v in util for _, s, _ in v)
    M["util"] = dict(chains=len(util), early_notices=len(early), disconnected_early=len(disc), steps=steps,
                     days_off=collections.Counter(min(x, 8) for x in off_days), warm=sum(1 for v in util if v[0][1] != "notice"))
    pdl = [v for (c, i), v in chains.items() if c == "payday_loan"]
    ps = collections.Counter(s for v in pdl for _, s, _ in v)
    due = ps["renewed"] + ps["repaid"] + ps["bounced"]
    V["payday_renewed_share"] = ps["renewed"] / max(1, due)
    M["payday"] = dict(chains=len(pdl), steps=ps, due=due, open_end=sum(1 for L in st["carry"]["loans"] if L["status"] != "collections"),
                       collections=sum(1 for L in st["carry"]["loans"] if L["status"] == "collections"),
                       max_n=max([L["n"] for L in st["carry"]["loans"]] or [0]))
    tl = [v for (c, i), v in chains.items() if c == "title_loan"]
    M["title"] = dict(chains=len(tl), steps=collections.Counter(s for v in tl for _, s, _ in v), cars_lost=sum(st["carry"]["cars_lost"].values()))
    ub = [v for (c, i), v in chains.items() if c == "unpaid_bill"]
    M["unpaid"] = dict(chains=len(ub), steps=collections.Counter(s for v in ub for _, s, _ in v))
    open_h = {e["hid"] for e in st["carry"]["retries"]} & reg
    hh_of = {}
    for d in days:
        for l in read_csv(os.path.join(month, d, "links.csv")):
            if l["chain"] == "unpaid_bill" and not l["earlier_record_id"]:
                hh_of[l["household_id"]] = True
    entered = set(hh_of) & reg
    # SHED asks adults about their own bills, so the target is read per adult: adults whose own account (wallet) has a
    # bill still unpaid. Accounts follow finance.build_finance: the head, spouse or partner, other "resident" relatives and
    # all children share the first; every other adult has an account of their own, in household order.
    open_w = {e["wid"] for e in st["carry"]["retries"]}
    members = collections.defaultdict(list)
    for p in persons.values():
        members[p["household_id"]].append(p)
    ad = ad_open = 0
    for h in reg:
        own = 1
        for p in members[h]:
            joint = p["relationship_to_head"] in ("head", "spouse", "unmarried_partner", "resident") or int(p["age"]) < 18
            wid = "%s-W1" % h if joint else "%s-W%d" % (h, own + 1)
            if not joint:
                own += 1
            if int(p["age"]) >= 18:
                ad += 1
                ad_open += wid in open_w
    V["unpaid_at_month_end"] = ad_open / ad
    M["unpaid_households_end"] = len(open_h) / len(reg)
    grp = collections.defaultdict(lambda: [0, 0, 0])
    for h in reg:
        g = grp[status[h]]
        g[0] += 1
        g[1] += h in entered
        g[2] += h in open_h
    M["unpaid_by_group"] = dict(grp)
    M["unpaid_entered"] = len(entered) / len(reg)
    # SNAP path
    share = collections.defaultdict(list)
    for h, k0 in snap_load.items():
        amt = snap_monthly.get(h)
        if not amt:
            continue
        for k, b in snap_close[h].items():
            if k >= k0:
                share[k - k0].append(b / amt)
    M["snap"] = {k: statistics.mean(v) for k, v in sorted(share.items()) if len(v) >= 30}
    V["snap_left_day14"] = M["snap"].get(14)
    V["snap_left_day28"] = M["snap"].get(28)
    # checking path relative to the month mean, by days since the last direct-deposit paycheck
    rel = collections.defaultdict(list)
    for h, ks in paydays.items():
        mean = statistics.mean(chk[h].values())
        if mean <= 50:
            continue
        ks = sorted(ks)
        for k in range(n):
            prev = [x for x in ks if x <= k]
            if prev:
                rel[k - prev[-1]].append(chk[h][k] / mean)
    M["checking_path"] = {k: statistics.mean(v) for k, v in sorted(rel.items()) if k <= 14 and len(v) >= 30}
    later = [x for k in (10, 11, 12, 13) for x in rel.get(k, [])]
    V["payday_balance_ratio"] = M["checking_path"].get(0, 0) / statistics.mean(later) if later else None
    M["checking_by_group"] = {g: [statistics.median(chk[h][k] for h in reg if status[h] == g) for k in range(n)] for g in ("poverty", "alice", "above")}
    # weekly pay change
    wk = collections.defaultdict(list)
    for pid, v in pay.items():
        p = persons[pid]
        if p["pay_cadence"] != "weekly" or len(v) < 2:
            continue
        g = "variable" if p["work_schedule"] == "variable" else "part_time" if p["employment_status"] == "employed_part_time" else "full_time_fixed"
        wk[g].append(statistics.mean(abs(b - a) / ((a + b) / 2) for a, b in zip(v, v[1:]) if a + b > 0))
    M["weekly_pay"] = {g: (len(v), statistics.mean(v)) for g, v in wk.items()}
    V["weekly_pay_change_variable"] = M["weekly_pay"].get("variable", (0, None))[1]
    M["V"] = V
    M["records"] = sum(m["records"] for m in per_day)
    M["households"], M["reg"], M["persons"] = len(households), len(reg), len(persons)
    return M


def fmt(metric, v):
    if v is None:
        return "-"
    if metric in ("od_accounts_for_79", "notice_to_shutoff", "reconnected_share", "payday_renewed_share", "unpaid_at_month_end", "snap_left_day14",
                  "snap_left_day28", "weekly_pay_change_variable"):
        return "%.1f%%" % (100 * v)
    if metric == "payday_balance_ratio":
        return "%.2f" % v
    if metric == "od_late_rent_chains":
        return "%d" % v
    return "{:,.1f}".format(v)


def verdict(t, v):
    if t["check"] == "report":
        return "reported"
    if t["check"] == "present":
        return "present" if v and v > 0 else "ABSENT"
    lo, hi = float(t["target_low"]), float(t["target_high"])
    if t["check"] == "range_tol":
        lo, hi = lo * .75, hi * 1.25
    return "in range" if lo <= v <= hi else ("LOW" if v < lo else "HIGH")


def write(M, out, label, month):
    os.makedirs(out, exist_ok=True)
    days, V, n = M["days"], M["V"], len(M["days"])
    targets = read_csv(TARGETS)
    L = ["# Evidence checks: the March 2027 month", "",
         "Simulator: %s. %d days carried one into the next (%s to %s), full city, default seed: balances, the retry queue, "
         "shutoff notices, overdrafts, payday and title loans, SNAP balances and the weeks' hours all carry (`sim/medianville_sim/carry.py`). "
         "Chains across days are read from each day's `links.csv`. Targets are in `sim/evidence/month_targets.csv`; the typed-day targets "
         "(`sim/evidence_targets.csv`) are repeated below as monthly averages." % (label, n, days[0], days[-1]), "",
         "## Targets for the month", "", "| Target | Item | Month | Target | Verdict | Status |", "|---|---|---|---|---|---|"]
    for t in targets:
        v = V.get(t["metric"])
        if t["check"] in ("report", "present"):
            tgt = t["tolerance"] if t["check"] == "present" or not t["target_low"] else "%s (%s)" % (fmt(t["metric"], float(t["target_low"])), t["tolerance"])
        elif t["check"] == "range_tol":
            tgt = "%s to %s %s (within 25%%)" % (t["target_low"], t["target_high"], t["unit"])
        else:
            lo, hi = float(t["target_low"]), float(t["target_high"])
            tgt = ("%s to %s" % (fmt(t["metric"], lo), fmt(t["metric"], hi))) if t["metric"] in ("notice_to_shutoff", "reconnected_share", "payday_renewed_share",
                                                                                          "unpaid_at_month_end") else "%s to %s %s" % (t["target_low"], t["target_high"], t["unit"])
        vd = verdict(t, v)
        if t["metric"] == "od_accounts_for_79":
            vd = "more concentrated" if v < .09 else "less concentrated"
        L.append("| %s | %s | %s | %s | %s | %s |" % (t["target_id"], t["item"], fmt(t["metric"], v), tgt, vd, t["status"]))
    od, oc, u, pdl, tl = M["od"], M["od_chains"], M["util"], M["payday"], M["title"]
    L += ["", "## The chains", "",
          "**Notice to shutoff.** %d notice timers ran in the month (%d inherited from notices sent before March 1). Of the notices sent on days 1-20, "
          "%s ended in a disconnection. Of the %d households disconnected on days 1-24, %s were reconnected by March 31. Steps: %s. "
          "Days without service before reconnection: %s." % (
              u["chains"], u["warm"], fmt("notice_to_shutoff", V["notice_to_shutoff"]), u["disconnected_early"], fmt("reconnected_share", V["reconnected_share"]),
              ", ".join("%s %d" % kv for kv in u["steps"].most_common()), ", ".join("%s%s: %d" % (k, "+" if k == 8 else "", v) for k, v in sorted(u["days_off"].items()))),
          "",
          "**Overdraft to fee to late rent.** %d overdraft chains; %d ran across more than one day, %d drew more fees after the first and %d drew the "
          "extended fee after a week below zero (%.1f fees a chain on average). %d chains reached a missed rent payment within two weeks of a fee, "
          "and %d of those then show the late or part payment of that rent." % (
              oc["chains"], oc["multi_day"], oc["with_more_fees"], oc["extended"], oc["fees_per_chain"], oc["rent_missed"], oc["late_rent"]),
          "",
          "**Overdraft concentration.** %d of %d checking accounts (%.1f%%) paid at least one overdraft fee in the month; the 9%% of accounts that paid the "
          "most paid %.1f%% of the %d fees, and %s of accounts paid 79%% of them (CFPB: 9%% over a year). Fees per paying account: %s. Only accounts "
          "opted in to overdraft coverage can overdraw (about 6.6%% of accounts, `finance.OD_OPT_IN`), so no month or year here can spread fees as widely "
          "as the CFPB found; that is set by the one-day population, which phase 4 does not change." % (
              od["paying"], od["accounts"], 100.0 * od["paying"] / od["accounts"], 100 * od["top9"], od["fees"], fmt("od_accounts_for_79", V["od_accounts_for_79"]),
              ", ".join("%s%s: %d" % (k, "+" if k == 10 else "", v) for k, v in sorted(od["per_account"].items()))),
          "",
          "**Payday rollovers.** %d payday loan chains (storefront and online); of %d loans coming due, %s were renewed for the fee, %d repaid and %d bounced. "
          "Steps: %s. At month's end %d loans were open and %d with collectors; the longest sequence had reached loan %d." % (
              pdl["chains"], pdl["due"], fmt("payday_renewed_share", V["payday_renewed_share"]), pdl["steps"]["repaid"], pdl["steps"]["bounced"],
              ", ".join("%s %d" % kv for kv in pdl["steps"].most_common()), pdl["open_end"], pdl["collections"], pdl["max_n"]),
          "",
          "**Title loans.** Steps: %s. %d cars were repossessed and stayed gone for the rest of the month." % (
              ", ".join("%s %d" % kv for kv in tl["steps"].most_common()), tl["cars_lost"]),
          "",
          "**Unpaid bills.** %d bills entered the retry queue (%s of households had at least one); steps: %s. Households with a bill still unpaid on "
          "March 31: %s of adults, counting the bills on their own account (SHED 2025: 15.2%% of adults cannot pay all of this month's bills "
          "in full), and %s of households. Households by group: %s." % (
              M["unpaid"]["chains"], fmt("unpaid_at_month_end", M["unpaid_entered"]), ", ".join("%s %d" % kv for kv in M["unpaid"]["steps"].most_common()),
              fmt("unpaid_at_month_end", V["unpaid_at_month_end"]), fmt("unpaid_at_month_end", M["unpaid_households_end"]),
              ", ".join("%s %.1f%% entered, %.1f%% open at the end" % (g, 100.0 * e / c, 100.0 * o / c) for g, (c, e, o) in sorted(M["unpaid_by_group"].items()))),
          "",
          "**SNAP balances** (share of the month's benefit left, by days since it loaded): %s." % ", ".join(
              "day %d %.0f%%" % (k, 100 * v) for k, v in M["snap"].items() if k in (0, 1, 3, 7, 10, 14, 21, 28)),
          "",
          "**Checking and the pay calendar** (households paid by direct deposit; checking against the household's month mean, by days since payday): %s. "
          "Median checking at the start, middle and end of the month: %s." % (
              ", ".join("%d: %.2f" % kv for kv in M["checking_path"].items()),
              "; ".join("%s $%s, $%s, $%s" % (g, "{:,.0f}".format(v[0]), "{:,.0f}".format(v[len(v) // 2]), "{:,.0f}".format(v[-1])) for g, v in M["checking_by_group"].items())),
          "",
          "**Weekly pay** (mean change from one weekly paycheck to the next): %s." % ", ".join(
              "%s %.1f%% (%d workers)" % (g.replace("_", " "), 100 * v, k) for g, (k, v) in sorted(M["weekly_pay"].items())),
          "", "## Typed-day targets over the month", "",
          "Each target in `sim/evidence_targets.csv`, as a plain average over the 31 days (March, not a weighted year).", "",
          "| Target | Item | March average | Typed-day target | Verdict (as for the year) |", "|---|---|---|---|---|"]
    days_m = [dict(date=d, cls="", weather="ordinary", weight=1.0, m=m) for d, m in zip(days, M["per_day"])]
    for t in checks.read_csv(checks.TARGETS):
        v = checks.year_value(t["metric"], days_m) if t["metric"] != "cash_share_rural" else None
        tgt = t["tolerance"] if t["check"] in ("present", "report") else "%s to %s %s" % (t["target_low"], t["target_high"], t["unit"])
        vd = checks.verdict(t, v) if v is not None else "not measured"
        if t["target_id"] == "T02":
            vd += "; new sequences only in a carried run (with renewals, M08: %s a day)" % fmt("payday_loans_and_renewals", V["payday_loans_and_renewals"])
        L.append("| %s | %s | %s | %s | %s |" % (t["target_id"], t["item"], checks.fmt(t["metric"], v), tgt, vd))
    L += ["", "## Limits", "",
          "- One month, started cold on March 1 except for what is inherited: shutoff notices from the ten days before, the payday loans and title "
          "loans already out, and the tax season so far. The retry queue and the overdraft chains start empty, so the first days run a little light.",
          "- People, households, jobs and bills do not change during the month: a death, birth, move or new job drawn on one day does not carry to "
          "the next (that is option C, a year with the roster changing).",
          "- Rural cash share (T11) needs each day's payment summary, which this report does not reread; see the days' `summary.md`.",
          "- Overdraft fees can only fall on accounts opted in to coverage, so they stay more concentrated than the CFPB's 9% of accounts.",
          "- Week-to-week hours, SNAP spending pace and the move of surplus checking to savings are labeled estimates (see `carry.py`)."]
    with open(os.path.join(out, "evidence_checks.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    # summary
    S = ["# Medianville, March 2027: the month in figures", "",
         "%s. %d days, %s to %s, carried one into the next; seed 20270303, full city (%s households and group quarters, %s residents). "
         "%s records in all, %s a day on average (%s to %s)." % (
             label, n, days[0], days[-1], "{:,}".format(M["households"]), "{:,}".format(M["persons"]), "{:,}".format(M["records"]), "{:,.0f}".format(M["records"] / n),
             "{:,}".format(min(m["records"] for m in M["per_day"])), "{:,}".format(max(m["records"] for m in M["per_day"]))), "",
         "Every day's own `summary.md`, `assumptions.csv` and tables are in the bundle; this file adds the month together. The evidence checks are in "
         "`evidence_checks.md` beside it.", "",
         "## Records by type", "", "| Record type | Records | Per day |", "|---|---|---|"]
    for k, v in M["by_type"].most_common():
        S.append("| %s | {:,} | {:,.0f} |".format(v, v / n) % k)
    S += ["", "## Day by day", "",
          "| Date | Day | Records | Failed attempts | Late fees | Overdraft fees | Notices | Disconnections | Reconnections | Payday loans and renewals | Title payments | Chain links | Ledgers off |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for d, m in zip(days, M["per_day"]):
        S.append("| %s | %s | {:,} | {:,} | {:,} | {:,} | {:,} | {:,} | {:,} | {:,} | {:,} | {:,} | {:,} |".format(
            m["records"], m["failed_attempts"], m["late_fees"], m["overdraft_fees"], m["utility_shutoff_notices"], m["utility_disconnections"], m["reconnections"],
            m["payday_loans_and_renewals"], m["title_loan_payments"], m["links"], m["ledger_bad"]) % (d, dt.date.fromisoformat(d).strftime("%a")))
    S += ["", "## Most common jobs in the month", "", "| Job category | Records |", "|---|---|"]
    for k, v in M["kinds"].most_common(25):
        S.append("| %s | {:,} |".format(v) % k)
    S += ["", "Money reconciles for every household on every day when the Ledgers off column is all zeros (opening balance plus inflows "
          "minus outflows equals the close, `household_ledger.csv`). Wages carry v1's boost (decision 9.1: every worker paid 1.23 times the "
          "national pay for the occupation)."]
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(S) + "\n")
    with open(os.path.join(month, "month_day_metrics.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "metric", "value"])
        for d, m in zip(days, M["per_day"]):
            for k, v in m.items():
                w.writerow([d, k, v])
    print("wrote", os.path.join(out, "evidence_checks.md"), os.path.join(out, "summary.md"))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return
    label = argv[argv.index("--label") + 1] if "--label" in argv else "v2 phase 4 (`sim/`)"
    write(measure(argv[0]), argv[1], label, argv[0])


if __name__ == "__main__":
    main(sys.argv[1:])
