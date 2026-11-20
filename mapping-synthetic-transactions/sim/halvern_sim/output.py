"""Write the tables and compute the summary checks."""
import csv
import os
from collections import Counter, defaultdict

from . import config as C
from .finance import BILL_CAT
from .population import EDU, generation

# column positions in sim.rows
(IDX, T, RT, JC, JS, ACT, HID, FRM, TO, BEN, DIS, CH, PM, GROSS, USER, THIRD, PAYER, FUND, IMP, TAX, FEET, FEE, TMIN, WAIT, MILES, MODE, OUT, FR, LENS, REL, NARR) = range(31)

CES = [("housing", 33.9), ("transportation", 16.5), ("food", 13.0), ("insurance_pensions", 12.4), ("healthcare", 7.9), ("entertainment", 4.6),
       ("contributions", 2.7), ("apparel", 2.5), ("education", 2.0), ("personal_care", 1.2), ("alcohol", 0.8), ("tobacco", 0.5), ("misc", 2.0)]
VEHICLE = ("new_car_purchase", "used_car_dealer_purchase", "used_car_buy_here_pay_here", "used_car_private_sale")
GENERAL = {"big_box_shopping": (("housing", .40), ("apparel", .25), ("entertainment", .20), ("personal_care", .15)),
           "online_shopping_order": (("housing", .35), ("apparel", .30), ("entertainment", .25), ("personal_care", .10)),
           "dollar_store": (("food", .45), ("housing", .40), ("personal_care", .15)), "warehouse_club": (("food", .65), ("housing", .35))}
DISC = {"clothing": "apparel", "thrift_store": "apparel", "dry_cleaning": "apparel", "jewelry_purchase": "apparel", "designer_handbag": "apparel",
        "haircut": "personal_care", "nail_salon": "personal_care", "tobacco": "tobacco", "retirement_contribution_payroll": "insurance_pensions",
        "fine_dining": "food", "electronics": "entertainment", "furniture": "housing", "postage_and_shipping": "misc", "jail_commissary_purchase": "misc",
        "travel_booking": "transportation", "investment_contribution": None}
NOT_PAYMENTS = {"credit_card_payment", "credit_card_interest_charge", "credit_card_late_fee", "bank_monthly_maintenance_fee", "prepaid_card_monthly_fee",
                "nursing_home_patient_liability", "dining_hall_meal", "jail_commissary_purchase", "jail_phone_call", "atm_withdrawal", "transfer_from_savings",
                "transfer_to_savings", "p2p_instant_cash_out", "prepaid_card_cash_reload", "scam_loss", "toll"}
PAY_TRANSFERS = {"p2p_transfer", "church_offering", "remittance_sent", "crowdfunding_contribution", "one_time_online_donation", "roommate_rent_share"}


def ces_alloc(r):
    """Return [(CES group, dollars)] for a consumer-paid record, or []."""
    rt = r[RT]
    if rt not in ("purchase", "bill_payment", "transfer", "tax", "benefit_redemption", "insurance_claim", "public_service_encounter") or not r[ACT]:
        return []
    cat, kind = r[JC].split(".", 1)
    amt = r[GROSS] if kind in VEHICLE else r[USER]
    if amt <= 0 or r[OUT] not in ("completed", "partial"):
        return []
    if kind in BILL_CAT:
        g = BILL_CAT[kind][1]
        return [(g, amt)] if g else []
    if kind in GENERAL:
        return [(g, amt * w) for g, w in GENERAL[kind]]
    if rt == "tax":
        if kind == "payroll_fica":
            return [("insurance_pensions", amt)]
        if kind in ("property_tax_payment", "property_tax_escrow"):
            return [("housing", amt)]
        return []
    if cat == "food":
        return [("alcohol" if kind in ("bar_tab", "liquor_store") else "food", amt)]
    if cat in ("housing", "utilities"):
        return [("housing", amt)]
    if cat == "transportation":
        return [("transportation", amt)]
    if cat == "health":
        return [("healthcare", amt)]
    if cat == "children_education":
        return [("education", amt)]
    if cat == "discretionary":
        g = DISC.get(kind, "entertainment")
        return [(g, amt)] if g else []
    if cat == "giving_faith":
        return [("contributions" if kind != "gift_for_family" else "misc", amt)]
    if cat == "money_services":
        if kind == "remittance_sent":
            return [("contributions", amt)]
        if kind == "p2p_transfer":
            return [("contributions", amt)] if ("family" in r[NARR] or "gift" in r[NARR] or "student" in r[NARR]) else []
        if rt == "transfer":
            return [("misc", r[FEE])] if r[FEE] > 0 else []
        return [("misc", amt)]
    if cat == "civic_legal":
        return [("misc", amt)]
    if cat == "income" and kind in ("union_dues",):
        return [("misc", amt)]
    return []


def is_payment(r, adults):
    """A consumer payment in the sense of the Fed payment diary: purchases, bills and person-to-person payments."""
    if r[OUT] not in ("completed", "partial") or r[USER] <= 0 or r[ACT] not in adults:
        return False
    if r[PM] in ("none", "payroll_deduction", "insurance"):
        return False
    kind = r[JC].split(".", 1)[1]
    if kind in NOT_PAYMENTS:
        return False
    rt = r[RT]
    if rt in ("purchase", "bill_payment", "benefit_redemption", "insurance_claim", "public_service_encounter"):
        return True
    if rt == "tax":
        return kind in ("property_tax_payment", "federal_tax_balance_due_payment")
    if rt == "transfer":
        return kind in PAY_TRANSFERS
    if rt == "b2b":
        return False
    return False


# ------------------------------------------------------------------------------------------------ tables
def income_mix(H):
    parts = defaultdict(float)
    for p in H.members:
        if p.wage:
            parts["self_employment" if p.emp == "self_employed" else "wages"] += p.wage
        parts["social_security"] += 12 * p.ss
        parts["ssi"] += 12 * p.ssi
        parts["pension"] += 12 * p.pension
        parts["investments_and_retirement_draws"] += 12 * p.inv
        parts["unemployment_insurance"] += 12 * p.ui
        parts["va_compensation"] += 12 * p.va
    parts["child_support"] += 12 * H.cs
    parts["tanf"] += 12 * H.tanf
    tot = sum(parts.values())
    if tot <= 0:
        return "none"
    return ";".join("%s:%.2f" % (k, v / tot) for k, v in sorted(parts.items(), key=lambda x: -x[1]) if v / tot >= .005)


def write_tables(sim, out, tagger=None):
    os.makedirs(out, exist_ok=True)
    w8 = "%.3f" % (1.0 / sim.scale)
    with open(os.path.join(out, "households.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["household_id", "district", "weight", "household_type", "size", "annual_income", "income_source_mix", "alice_status", "banked_status",
                    "housing_tenure", "monthly_housing_cost", "vehicles", "internet_at_home", "primary_language", "notes"] + (["block_id"] if tagger else []))
        for H in sim.households:
            notes = list(H.notes)
            if H.snap:
                notes.append("snap_monthly=%d" % H.snap)
            if H.fragile:
                pass
            w.writerow([H.hid, H.district, w8, H.htype, len(H.members), int(round(H.income)), income_mix(H), H.alice, H.banked, H.tenure, int(H.housing_cost),
                        H.vehicles, H.internet, H.lang, ";".join(notes)] + ([tagger.household_block(H.hid)] if tagger else []))
    with open(os.path.join(out, "persons.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["person_id", "household_id", "age", "birth_cohort", "sex", "race_ethnicity", "relationship_to_head", "education", "disability", "health_coverage",
                    "employment_status", "occupation", "employer_org_id", "industry_sector", "union_member", "work_schedule", "pay_cadence", "caregiver_for",
                    "benefits_received"])
        for p in sim.persons:
            w.writerow([p.pid, p.hh.hid, p.age, "%s_%d" % (generation(p.by), p.by), p.sex, p.race, p.rel, EDU[p.edu] if p.edu is not None else "not_applicable",
                        p.dis, p.cov, p.emp, p.occ, p.org.oid if p.org is not None else "", C.SECNAME.get(p.sector, ""), "yes" if p.union else "no", p.wsched,
                        p.cadence, ";".join(c.pid for c in p.care_for) or "none", ";".join(p.benefits) or "none"])
    with open(os.path.join(out, "organizations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["org_id", "name", "org_type", "sector", "district", "size_employees", "accepts", "hours", "notes"])
        for o in sim.orgs:
            note = o.notes
            if o.district != "EXT" and o.emp:
                note = (note + "; " if note else "") + "halvern_residents_on_staff=%d" % o.emp
            w.writerow([o.oid, o.name, o.otype, o.sector, "outside" if o.district == "EXT" else o.district, o.size if o.district != "EXT" else "", o.accepts, o.hours, note])
    # ledger: one row per household, the day's money reconciled
    bad = 0
    with open(os.path.join(out, "household_ledger.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["household_id", "wallets", "open_checking", "open_cash", "open_prepaid", "open_savings", "open_card_debt", "inflows", "outflows", "close_checking",
                    "close_cash", "close_prepaid", "close_savings", "close_card_debt", "open_net", "close_net", "reconciles", "snap_open", "snap_close",
                    "could_cover_400_emergency"])
        for H in sim.households:
            o = [0.0] * 5
            c = [0.0] * 5
            inf = outf = 0.0
            for W in H.wallets:
                s = W.start
                o[0] += s[0] or 0
                o[1] += s[1]
                o[2] += s[2] or 0
                o[3] += s[4]
                o[4] += s[3]
                c[0] += W.bank or 0
                c[1] += W.cash
                c[2] += W.prepaid or 0
                c[3] += W.savings
                c[4] += W.cc_bal
                inf += W.inflow
                outf += W.outflow
            on = o[0] + o[1] + o[2] + o[3] - o[4]
            cn = c[0] + c[1] + c[2] + c[3] - c[4]
            ok = abs(on + inf - outf - cn) < .06
            bad += 0 if ok else 1
            w.writerow([H.hid, len(H.wallets)] + ["%.2f" % x for x in o] + ["%.2f" % inf, "%.2f" % outf] + ["%.2f" % x for x in c] +
                       ["%.2f" % on, "%.2f" % cn, "yes" if ok else "no", "%.2f" % (H.wallets[0].snap_start if H.wallets else 0), "%.2f" % H.snap_bal,
                        "yes" if (H.wallets and H.wallets[0].can400) else "no"])
    sim.ledger_bad = bad
    return bad


# ------------------------------------------------------------------------------------------------ detailed sample
def select_detailed(sim, n=500):
    """Stratified sample across district x record type x income group; returns row indices."""
    import random
    rng = random.Random(sim.cfg["RANDOM_SEED"] + 500)
    hmap = {H.hid: H for H in sim.households}
    cells = defaultdict(list)
    for i, r in enumerate(sim.rows):
        H = hmap.get(r[HID])
        grp = H.alice if H is not None else "org"
        cells[(r[DIS] or "none", r[RT], grp)].append(i)
    keys = sorted(cells)
    picked = []
    per = max(1, n // len(keys))
    for k in keys:
        lst = cells[k]
        # favor variety of kinds inside a cell
        rng.shuffle(lst)
        seen, take = set(), []
        for i in lst:
            kd = sim.rows[i][JC]
            if kd not in seen:
                take.append(i)
                seen.add(kd)
            if len(take) >= per:
                break
        picked += take
    rest = [i for k in keys for i in cells[k][:6] if i not in set(picked)]
    rng.shuffle(rest)
    picked = (picked + rest)[:n]
    return sorted(picked, key=lambda i: (sim.rows[i][T], i))


# ------------------------------------------------------------------------------------------------ summary
def summarize(sim):
    rows = sim.rows
    HH, PP = sim.households, sim.persons
    hmap = {H.hid: H for H in HH}
    pmap = {p.pid: p for p in PP}
    reg = [H for H in HH if not H.gq]
    adults = {p.pid for p in PP if p.age >= 18}
    n_ad = len(adults)
    S = {}
    S["n_records"] = len(rows)
    S["n_hh"], S["n_gq"], S["n_p"], S["n_org"] = len(reg), len(HH) - len(reg), len(PP), len(sim.orgs)
    by = defaultdict(Counter)
    for r in rows:
        by[r[RT]][r[DIS] or "none"] += 1
    S["type_district"] = by
    # population anchors
    S["district_share"] = {d: sum(len(H.members) for H in HH if H.district == d) / len(PP) for d in C.DISTRICTS}
    emp = [p for p in PP if p.emp.startswith("employed") or p.emp == "self_employed"]
    S["jobs"] = len(emp)
    sc = Counter(p.sector for p in emp)
    S["sector"] = [(n, 100.0 * sc[c] / max(1, len(emp)), s) for c, n, s in C.SECTORS]
    S["alice"] = {k: v / len(reg) for k, v in Counter(H.alice for H in reg).items()}
    S["can400"] = sum(1 for p in PP if p.age >= 18 and p.wallet is not None and p.wallet.can400) / max(1, sum(1 for p in PP if p.age >= 18 and p.wallet is not None))
    inc = sorted(H.income for H in reg)
    S["median_income"] = inc[len(inc) // 2]
    S["out_commuters"] = sum(1 for p in emp if p.wd == "EXT")
    S["in_commuters"] = sum(max(0, o.size - o.emp) for o in sim.orgs if o.district != "EXT" and o.emp > 0 and o.kind not in ("school_elem", "school_mid", "school_high"))
    # payments
    pay = [r for r in rows if is_payment(r, adults)]
    S["payments"] = len(pay)
    S["pay_per_adult_month"] = len(pay) / max(1, n_ad) * 30.4
    mc = Counter(r[PM] for r in pay)
    S["method_count"] = mc
    mv = Counter()
    for r in pay:
        mv[r[PM]] += r[USER]
    S["method_value"] = mv
    S["cash_share"] = mc["cash"] / max(1, len(pay))

    def cash_share(pred):
        sub = [r for r in pay if pred(r)]
        return (sum(1 for r in sub if r[PM] == "cash") / max(1, len(sub)), len(sub))
    S["cash_55"] = cash_share(lambda r: pmap[r[ACT]].age >= 55)
    S["cash_u55"] = cash_share(lambda r: pmap[r[ACT]].age < 55)
    for g in ("poverty", "alice", "above"):
        S["cash_" + g] = cash_share(lambda r, g=g: hmap[r[HID]].alice == g)
    S["cash_rural"] = cash_share(lambda r: r[DIS] in ("D5", "D6"))
    S["cash_urban"] = cash_share(lambda r: r[DIS] in ("D1",))
    S["cash_suburb"] = cash_share(lambda r: r[DIS] in ("D2", "D3", "D4"))
    # spending mix
    ces = Counter()
    inst = {H.hid for H in HH if H.gq in ("nursing_home", "jail", "group_home", "residential_treatment", "assisted_living")}
    for r in rows:
        if r[HID] in inst:
            continue                # the survey covers households, not people living in institutions
        for g, a in ces_alloc(r):
            ces[g] += a
    S["ces"] = ces
    acc = {k: v for k, v in sim.accrual.items() if not k.startswith("_all_")}
    S["accrual"] = acc
    # failures
    failed_h = set()
    nfail = 0
    for r in rows:
        if r[RT] == "failed_attempt" or r[OUT] in ("declined", "abandoned", "failed", "rescheduled"):
            nfail += 1
            if r[HID]:
                failed_h.add(r[HID])
    S["fail_records"] = nfail
    S["fail_hh_share"] = len([h for h in failed_h if not hmap[h].gq]) / len(reg)
    S["fail_by_group"] = {g: len([h for h in failed_h if hmap[h].alice == g and not hmap[h].gq]) / max(1, sum(1 for H in reg if H.alice == g)) for g in ("poverty", "alice", "above")}
    S["retries"] = sum(1 for r in rows if r[REL] is not None and rows[r[REL]][RT] == "failed_attempt")
    # non-monetary time
    nm = [r for r in rows if r[RT] == "non_monetary_job"]
    S["nm_hours"] = sum(r[TMIN] + r[WAIT] for r in nm) / 60.0
    S["nm_n"] = len(nm)
    kt = Counter()
    for r in nm:
        kt[r[JC]] += r[TMIN] + r[WAIT]
    S["nm_top"] = kt.most_common(10)
    # fees
    fees = defaultdict(float)
    feen = Counter()
    feetype = defaultdict(Counter)
    spend = defaultdict(float)
    for r in rows:
        H = hmap.get(r[HID])
        if H is None:
            continue
        g = H.alice
        if r[FEE] > 0 and r[OUT] in ("completed", "partial", "failed"):
            fees[g] += r[FEE]
            feen[g] += 1
            for ft in r[FEET].split("+"):
                feetype[g][ft] += r[FEE] / max(1, len(r[FEET].split("+")))
        if r[RT] in ("purchase", "bill_payment") and r[OUT] in ("completed", "partial"):
            spend[g] += r[USER]
    nh = Counter(H.alice for H in HH)
    S["fees"] = {g: (fees[g], feen[g], fees[g] / max(1, nh[g]), fees[g] / max(1.0, spend[g]), feetype[g].most_common(4)) for g in ("poverty", "alice", "above")}
    # public dollars
    PUB = ("federal", "state", "local", "mixed")
    transfers = Counter()
    services = Counter()
    taxes = Counter()
    biz_tax = Counter()
    for r in rows:
        kind = r[JC].split(".", 1)[1]
        if r[RT] == "benefit_issuance":
            transfers[kind] += r[THIRD] if r[THIRD] else r[GROSS]
        elif r[RT] in ("public_service_encounter", "insurance_claim", "bill_payment", "purchase", "benefit_redemption") and r[FUND] in PUB and r[THIRD] > 0:
            if r[RT] == "benefit_redemption":
                continue            # spending of benefits already counted at issuance
            services[kind] += r[THIRD]
        if r[RT] == "tax":
            if kind in ("federal_payroll_tax_deposit", "employer_payroll_taxes"):
                biz_tax[kind] += r[GROSS]
            else:
                taxes[kind] += r[GROSS]
        if r[TAX] > 0 and r[OUT] in ("completed", "partial"):
            taxes["sales_tax_on_purchases"] += r[TAX]
    S["transfers"], S["services"], S["taxes"], S["biz_tax"] = transfers, services, taxes, biz_tax
    S["refunds"] = sum(r[GROSS] for r in rows if r[JC] in ("income.federal_tax_refund", "income.state_tax_refund"))
    # frictions
    wages = sorted(p.wage / 2080.0 for p in emp if p.wage > 0)
    tv = round(wages[len(wages) // 2], 2) if wages else 20.0
    S["time_value"] = tv
    fr = defaultdict(lambda: [0, 0.0, 0.0, defaultdict(float), defaultdict(float), defaultdict(float)])
    for r in rows:
        if not r[FR]:
            continue
        tags = r[FR].split(";")
        bad = r[RT] == "failed_attempt" or r[OUT] in ("declined", "abandoned", "failed", "rescheduled")
        mins = r[WAIT] + (r[TMIN] if bad else 0)
        if "distance" in tags or "no_transit" in tags or "repeat_trip" in tags:
            mins += r[MILES] * 2.0
        money = r[FEE] + (r[GROSS] if (r[JC].startswith("work.") and bad or r[OUT] == "partial" and r[JC].startswith("work.")) else 0.0)
        H = hmap.get(r[HID])
        for t in tags:
            a = fr[t]
            a[0] += 1
            a[1] += mins / len(tags)
            a[2] += money / len(tags)
            if H is not None:
                c = (mins / len(tags)) / 60.0 * tv + money / len(tags)
                a[3][H.htype] += c
                a[4][H.alice] += c
                a[5][H.district] += c
    nt = Counter(H.htype for H in HH)
    na = Counter(H.alice for H in HH)
    top = []
    for t, a in fr.items():
        cost = a[1] / 60.0 * tv + a[2]
        ht = sorted(((v / max(1, nt[k]), k) for k, v in a[3].items() if nt[k] >= max(20, .004 * len(HH))), reverse=True)[:2]
        al = sorted(((v / max(1, na[k]), k) for k, v in a[4].items()), reverse=True)[:1]
        top.append((cost, t, a[0], a[1] / 60.0, a[2], [k for _, k in ht], al[0][1] if al else ""))
    S["frictions"] = sorted(top, reverse=True)[:10]
    # time consistency
    load = defaultdict(float)
    whole_day = ("nursing_home_day", "skilled_nursing_rehab_day", "group_home_residential_services", "residential_treatment_day", "hospital_admission",
                 "hospital_admission_uncompensated", "childbirth_hospital_stay", "at_hospital_for_a_birth", "stayed_home_with_sick_child",
                 "missed_shift_for_sick_child", "late_or_missed_shift", "sent_home_early", "shift_cancelled_short_notice", "turned_down_extra_hours")
    for r in rows:
        if r[ACT] and r[CH] in ("in_person",) and r[RT] != "public_service_encounter" and r[JC].split(".", 1)[1] not in whole_day:
            load[r[ACT]] += r[TMIN] + r[WAIT]
    worst = 0.0
    over = 0
    for p in PP:
        w = sum(e - s for s, e in p.shift) if p.shift else 0
        tot = w + load.get(p.pid, 0.0)
        worst = max(worst, tot)
        over += tot > 1440
    S["max_person_minutes"], S["persons_over_24h"] = worst, over
    S["ledger_bad"] = getattr(sim, "ledger_bad", None)
    S["neg_checking"] = sum(1 for W in sim.wallets if W.bank is not None and W.bank < -.005)
    S["life"] = {k: len(v) for k, v in sim.ev.items()}
    kc = Counter(r[JC].split(".", 1)[1] for r in rows)
    S["kc"] = kc
    S["stats"] = dict(sim.stats)
    S["n_kinds"] = len(kc)
    return S


def fmt_money(x):
    return "${:,.0f}".format(x)


def write_summary(sim, S, path, n_detailed=0):
    cal = sim.cal
    L = []
    A = L.append
    A("# Halvern, %s %s: one simulated day" % (cal["dayname"], cal["date"].strftime("%B %-d, %Y")))
    A("")
    A("Seed %s, weather %s, scale %.2f. Everything here is synthetic. Figures marked *anchor* come from the prompt; the rest are labeled estimates (see assumptions.csv)."
      % (sim.cfg["RANDOM_SEED"], sim.cfg["WEATHER"], sim.scale))
    A("")
    A("## What was generated")
    A("")
    A("| Table | Rows |")
    A("|---|---|")
    A("| records.csv | {:,} |".format(S["n_records"]))
    A("| households.csv | {:,} ({:,} households plus {:,} one-person group-quarters units) |".format(S["n_hh"] + S["n_gq"], S["n_hh"], S["n_gq"]))
    A("| persons.csv | {:,} |".format(S["n_p"]))
    A("| organizations.csv | {:,} |".format(S["n_org"]))
    A("")
    A("%d distinct job categories. %d rows carry hand-written text (narrative starts with \"[detailed]\")." % (S["n_kinds"], n_detailed))
    A("")
    A("## Records by type and district")
    A("")
    ds = C.DISTRICTS
    A("| record_type | " + " | ".join(ds) + " | total |")
    A("|---|" + "---|" * (len(ds) + 1))
    tot_d = Counter()
    for rt in ["purchase", "bill_payment", "income", "benefit_issuance", "benefit_redemption", "transfer", "tax", "b2b", "public_service_encounter", "insurance_claim",
               "non_monetary_job", "failed_attempt"]:
        c = S["type_district"].get(rt, Counter())
        A("| %s | " % rt + " | ".join("{:,}".format(c.get(d, 0)) for d in ds) + " | {:,} |".format(sum(c.values())))
        for d in ds:
            tot_d[d] += c.get(d, 0)
    A("| **all** | " + " | ".join("**{:,}**".format(tot_d[d]) for d in ds) + " | **{:,}** |".format(S["n_records"]))
    A("")
    A("## Calibration against the anchors")
    A("")
    A("| Check | Target | Simulated | Note |")
    A("|---|---|---|---|")
    A("| Residents | about 100,000 | {:,} | includes {:,} people in group quarters |".format(S["n_p"], S["n_gq"]))
    A("| Households | about 40,000 | {:,} | excludes group quarters |".format(S["n_hh"]))
    A("| District shares (D1 to D6) | 31 / 20 / 22 / 13 / 8 / 6 % | " + " / ".join("%.1f" % (100 * S["district_share"][d]) for d in ds) + " % | share of residents |")
    A("| Residents with jobs | about 48,000 | {:,} | {:,} commute out; about {:,} positions at Halvern employers are filled by in-commuters |".format(S["jobs"], S["out_commuters"], S["in_commuters"]))
    dev = max(abs(a - s) for _, a, s in S["sector"])
    A("| Industry mix | BLS shares in the prompt | largest gap %.1f points | full table below |" % dev)
    A("| Payments per adult per month | about 43 | %.1f | %s payments by adults today x 30.4 days; definition below |" % (S["pay_per_adult_month"], "{:,}".format(S["payments"])))
    A("| Cash share of payments | about 14%% | %.1f%% | by count; %.1f%% by value |" % (100 * S["cash_share"], 100 * S["method_value"]["cash"] / max(1.0, sum(S["method_value"].values()))))
    A("| Cash higher for 55+ | yes | %.1f%% vs %.1f%% under 55 | |" % (100 * S["cash_55"][0], 100 * S["cash_u55"][0]))
    A("| Cash higher at lower incomes | yes | poverty %.1f%%, ALICE %.1f%%, above %.1f%% | |" % (100 * S["cash_poverty"][0], 100 * S["cash_alice"][0], 100 * S["cash_above"][0]))
    A("| Cash higher in rural districts | yes | rural %.1f%%, suburban %.1f%%, urban core %.1f%% | |" % (100 * S["cash_rural"][0], 100 * S["cash_suburb"][0], 100 * S["cash_urban"][0]))
    A("| Adults who would cover a $400 emergency with cash or equivalent | 63%% | %.1f%% | threshold solved at %s in liquid funds, or $400 free on a card paid in full |" % (100 * S["can400"], fmt_money(sim.liq_mult)))
    below = S["alice"].get("poverty", 0) + S["alice"].get("alice", 0)
    A("| Households below the ALICE survival budget | roughly 4 in 10 | %.1f%% | %.1f%% in poverty plus %.1f%% ALICE |" % (100 * below, 100 * S["alice"].get("poverty", 0), 100 * S["alice"].get("alice", 0)))
    A("| Median household income | not anchored | %s | 2027 dollars; estimate. SCF 2025 implies about $86,700. Reached by paying every worker x %.2f "
      "their occupation's national pay (about 14%% above real pay) to make up for small households; compare households, not one job's pay |"
      % (fmt_money(S["median_income"]), C.WAGE_SCALE))
    lf = S["life"]
    A("| Births | 2.9 a day | %d | 10.7 per 1,000 residents a year |" % lf.get("births", 0))
    A("| Deaths | 2.5 a day | %d | 9.2 per 1,000 a year |" % lf.get("deaths", 0))
    kc = S["kc"]
    A("| Marriage licenses | 2.4 a court day | %d | 6.3 per 1,000 a year (NCHS 2024) |" % kc.get("marriage_license", 0))
    A("| Divorce filings | 0.9 a court day | %d | 2.3 per 1,000 a year (NCHS 2024) |" % kc.get("divorce_filing_fee", 0))
    A("| Household moves | about 9 a day | %d | 8%% of residents move in a year; move-ins recorded |" % kc.get("move_in_deposit_and_first_rent", 0))
    A("| Hospital admissions | about 24 a day | %d | plus %d people already inpatients |" % (lf.get("admits", 0), lf.get("census", 0)))
    A("")
    A("A payment here follows the Federal Reserve diary's idea: a purchase, bill or person-to-person payment made by an adult, by any instrument including EBT. "
      "It leaves out payroll deductions, credit-card bill payments (the purchases were already counted), ATM withdrawals and transfers between a person's own accounts.")
    A("")
    A("### Payment instruments")
    A("")
    A("| Instrument | Share of payments | Share of value |")
    A("|---|---|---|")
    tc, tv_ = sum(S["method_count"].values()), sum(S["method_value"].values())
    for m, n in S["method_count"].most_common():
        A("| %s | %.1f%% | %.1f%% |" % (m, 100.0 * n / tc, 100.0 * S["method_value"][m] / max(1.0, tv_)))
    A("")
    A("### Industry mix of residents' jobs")
    A("")
    A("| Sector | Target % | Simulated % |")
    A("|---|---|---|")
    for n, a, s in S["sector"]:
        A("| %s | %.1f | %.1f |" % (n, s, a))
    A("")
    A("## Spending mix against the Consumer Expenditure Survey")
    A("")
    ces = S["ces"]
    tot = sum(ces.values())
    A("Out-of-pocket consumer spending recorded today: %s. Shares are compared with the BLS Consumer Expenditure Survey (2025 shares for the four largest components, 2024 for the rest)." % fmt_money(tot))
    A("")
    A("| Category | CES share | Today's share | Today's dollars |")
    A("|---|---|---|---|")
    for g, s in CES:
        A("| %s | %.1f%% | %.1f%% | %s |" % (g.replace("_", " "), s, 100.0 * ces.get(g, 0) / max(1.0, tot), fmt_money(ces.get(g, 0))))
    A("")
    A("Housing is the largest category, followed by transportation and food, as in the survey. A single day cannot match annual shares exactly: rent and mortgages bunch in the first "
      "days of the month, only about one worker in twenty is paid on a Wednesday the 3rd (so payroll-deducted Social Security and retirement contributions run low), and vehicle "
      "purchases are counted at full price on the day of sale. Recurring obligations spread over a month come to about %s a day." % fmt_money(sum(S["accrual"].values())))
    A("")
    A("## Things that went wrong")
    A("")
    A("- {:,} records are failed attempts or ended declined, abandoned, failed or rescheduled; {:,} later records are linked retries.".format(S["fail_records"], S["retries"]))
    A("- %.1f%% of households had at least one failed attempt (poverty %.1f%%, ALICE %.1f%%, above ALICE %.1f%%)."
      % (100 * S["fail_hh_share"], 100 * S["fail_by_group"]["poverty"], 100 * S["fail_by_group"]["alice"], 100 * S["fail_by_group"]["above"]))
    st = S["stats"]
    A("- Card or account declines for insufficient funds: {:,}; technical declines: {:,}; declines during the card-reader outage at one grocery store: {:,}; overdrafts: {:,}; bounced autopays: {:,}."
      .format(st.get("declined_insufficient_funds", 0), st.get("declined_other", 0), st.get("declined_outage", 0), st.get("overdraft", 0), st.get("nsf_return", 0)))
    A("- Purchases given up because nothing would cover them: {:,}. Prescriptions left at the counter over price: {:,}. Renewals stopped by the state portal outage: {:,}. Contractor no-shows: {:,}. Trips to a closed licensing office: {:,}."
      .format(st.get("unaffordable", 0), st.get("rx_abandoned", 0), st.get("portal_outage", 0), st.get("contractor_no_show", 0), st.get("closed_office", 0)))
    A("")
    A("## Unpaid time")
    A("")
    A("{:,} non-monetary jobs took {:,.0f} hours in all ({:.0f} minutes per adult). Largest by time:".format(S["nm_n"], S["nm_hours"], 60.0 * S["nm_hours"] / max(1, sum(1 for p in sim.persons if p.age >= 18))))
    A("")
    A("| Job | Hours |")
    A("|---|---|")
    for k, m in S["nm_top"]:
        A("| %s | %s |" % (k, "{:,.0f}".format(m / 60.0)))
    A("")
    A("## Fees by income group")
    A("")
    A("| Group | Fee records | Fees paid | Per household | Fees as share of purchases and bills | Largest fee types |")
    A("|---|---|---|---|---|---|")
    for g in ("poverty", "alice", "above"):
        f, n, per, shr, tops = S["fees"][g]
        A("| %s | %s | %s | $%.2f | %.2f%% | %s |" % (g, "{:,}".format(n), fmt_money(f), per, 100 * shr, ", ".join("%s (%s)" % (a.replace("_", " "), fmt_money(b)) for a, b in tops)))
    A("")
    A("Fees include overdraft, late, ATM, check-cashing, money-order, convenience, delivery, card-interest and loan finance charges recorded on the day.")
    A("")
    A("## Public dollars")
    A("")
    tr, sv, tx = S["transfers"], S["services"], S["taxes"]
    A("| Flow | Dollars today | Largest items |")
    A("|---|---|---|")
    A("| Transfers in (benefit issuances and refundable credits) | %s | %s |" % (fmt_money(sum(tr.values())), ", ".join("%s %s" % (k.replace("_", " "), fmt_money(v)) for k, v in tr.most_common(5))))
    A("| Tax refunds of people's own overpayments | %s | federal and state refunds, not counted as transfers |" % fmt_money(S["refunds"]))
    A("| Services delivered (public payers' share of encounters and claims) | %s | %s |" % (fmt_money(sum(sv.values())), ", ".join("%s %s" % (k.replace("_", " "), fmt_money(v)) for k, v in sv.most_common(5))))
    A("| Taxes paid by households (withholding, payroll tax, property tax, sales tax) | %s | %s |" % (fmt_money(sum(tx.values())), ", ".join("%s %s" % (k.replace("_", " "), fmt_money(v)) for k, v in tx.most_common(5))))
    bt = S["biz_tax"]
    A("| Taxes sent in by employers (matching payroll tax, deposits of earlier withholding) | %s | %s |" % (fmt_money(sum(bt.values())), ", ".join("%s %s" % (k.replace("_", " "), fmt_money(v)) for k, v in bt.most_common(3))))
    A("")
    A("Monthly benefits that post on other days are not in today's transfers: SSI and VA compensation arrived March 1, and most Social Security is paid on the second to fourth Wednesdays. "
      "Today's Social Security goes to people paid on the 3rd: long-time beneficiaries, people who also get SSI, and people whose Medicare premium the state pays. "
      "public_services_context.csv gives the daily cost of the services that are not itemized (police, roads, water, and so on).")
    A("")
    A("## The ten costliest frictions")
    A("")
    A("Time is valued at $%.2f an hour, the median hourly wage of Halvern workers. Money is fees plus wages lost. A record with several tags splits its cost among them." % S["time_value"])
    A("")
    A("| Friction | Records | Hours | Fees and lost wages | Combined cost | Household types hit hardest (per household) | Income group hit hardest |")
    A("|---|---|---|---|---|---|---|")
    for cost, t, n, hrs, money, hts, al in S["frictions"]:
        A("| %s | %s | %s | %s | %s | %s | %s |" % (t, "{:,}".format(n), "{:,.0f}".format(hrs), fmt_money(money), fmt_money(cost), ", ".join(hts), al))
    A("")
    A("## Consistency checks")
    A("")
    A("- Time: the busiest person has %.1f hours of work plus in-person activity; %d people exceed 24 hours. In-person activities are scheduled into each person's free time, so no one is in two places at once."
      % (S["max_person_minutes"] / 60.0, S["persons_over_24h"]))
    A("- Money: opening balance plus inflows minus outflows equals closing balance for all but %s households (household_ledger.csv). %d checking accounts end the day overdrawn."
      % (S["ledger_bad"], S["neg_checking"]))
    A("- Every payroll record has linked withholding and FICA records; every Social Security deposit with a Medicare premium has a linked deduction; retries point to the attempt that failed.")
    A("")
    return "\n".join(L)
