"""Household day, part A: daily schedules, income and benefits arriving, recurring bills."""
import heapq
import itertools
from .config import DIST, INTRA, PART_B_PREMIUM, STATE_INCOME_TAX
from .engine import ANY, DAY, EVE, OFFICE, SHOP, LUNCH, MORN
from .finance import BILL_CAT
from .carry import bill_missed

_ctr = itertools.count()


def push(q, t, fn):
    heapq.heappush(q, (int(t), next(_ctr), fn))


def subtract(awake, busy):
    out = []
    for a0, a1 in awake:
        cur = [(a0, a1)]
        for b0, b1 in busy:
            nxt = []
            for s, e in cur:
                if b1 <= s or b0 >= e:
                    nxt.append((s, e))
                else:
                    if b0 - s >= 5:
                        nxt.append((s, b0))
                    if e - b1 >= 5:
                        nxt.append((b1, e))
            cur = nxt
        out.extend(cur)
    return [[s, e] for s, e in sorted(out) if e - s >= 5]


OFFICE_SCHED = ("day", "school", "early", "split")


def holiday_work(p, sk, cal):
    """Multiplier on the chance of working on a federal holiday. NCS March 2026: 81% of private-industry workers have paid
    holidays, 8 a year on average (so the six major ones plus about two more); state and local government workers 11.
    Shift, evening and gig schedules (hospitals, police, retail, food service) mostly work."""
    major = cal["holiday_major"]
    if sk == "school":
        return 1.0 if cal["school_day"] else .05
    if p.sector in ("gov", "fed"):
        return (.9 if major else 1.0) if sk not in OFFICE_SCHED else .05
    if p.sector == "fin" and sk in OFFICE_SCHED:
        return .08
    if sk in OFFICE_SCHED:
        return .15 if major else .75
    return .9 if major else 1.0


WORK_P = {"day": (.93, .62), "school": (.94, .7), "early": (.92, .6), "shift3": (.72, .55), "shift12": (.45, .35), "var": (.70, .52),
          "late": (.70, .5), "eve": (.80, .6), "night": (.72, .5), "split": (.93, .7), "gig": (.72, .5), "farm": (.88, .6)}


def skeleton(sim, H):
    rng, cal, wx = sim.rng, sim.cal, sim.wx
    weekday = cal["weekday"]
    school_on = cal["school_day"] and wx["school_open"]
    for p in H.members:
        a = p.age
        p.busy, p.works, p.wfh, p.absent, p.lunch, p.shift, p.cm, p.night = [], False, False, False, None, [], 0, False
        wake = int(rng.gauss(405, 40)) if a >= 18 else 400
        if p.emp == "retired":
            wake = int(rng.gauss(435, 50))
        bed = int(rng.gauss(1350, 45)) if a >= 16 else (1235 if a < 10 else 1300)
        if H.gq in ("jail", "nursing_home"):
            p.wake, p.bed, p.free = 390, 1290, [[420, 1260]]
            continue
        if H.gq == "nursing_home":
            continue
        working = p.emp in ("employed_full_time", "employed_part_time", "self_employed")
        if working:
            sk = p.sched
            pw = WORK_P[sk][0 if p.ft or p.emp == "self_employed" else 1]
            if not weekday and sk in ("day", "school", "early", "split"):
                pw *= .08
            if cal["holiday"]:
                pw *= holiday_work(p, sk, cal)
            if p.seasonal and not cal["growing"]:
                pw *= .62
            if sk in ("early", "farm") and p.sector in ("constr", "ag", "self"):
                pw *= (1.0 if wx["trips"] > .9 else .5)
            if rng.random() < pw:
                p.works = True
                ft = p.ft or p.emp == "self_employed"
                iv = []
                if sk == "day":
                    s = int(min(600, max(390, rng.gauss(495, 35))))
                    iv = [(s, s + (rng.randint(510, 570) if ft else rng.randint(240, 360)))]
                elif sk == "school":
                    s = rng.randint(425, 470)
                    iv = [(s, s + (rng.randint(480, 510) if ft else rng.randint(240, 330)))]
                elif sk in ("early", "farm"):
                    s = rng.randint(345, 420)
                    iv = [(s, s + (rng.randint(510, 630) if ft else rng.randint(240, 360)))]
                elif sk == "shift3":
                    iv = {1: [(360, 870)], 2: [(840, 1350)], 3: [(0, 390), (1320, 1440)]}[p.slot or 1]
                elif sk == "shift12":
                    iv = [(420, 1170)] if p.slot != 3 else [(0, 450), (1140, 1440)]
                elif sk == "var":
                    if ft and rng.random() < .75:
                        iv = [rng.choice([(360, 840), (600, 1080), (840, 1350), (480, 960)])]
                    else:
                        s = rng.randint(420, 1020)
                        iv = [(s, s + rng.randint(240, 360))]
                elif sk == "late":
                    iv = [(rng.randint(930, 1020), 1439)]
                elif sk == "eve":
                    s = rng.randint(870, 960)
                    iv = [(s, min(1410, s + (rng.randint(420, 480) if ft else rng.randint(180, 270))))]
                elif sk == "night":
                    iv = [(0, 360), (1320, 1440)]
                elif sk == "split":
                    iv = [(330, 545), (835, 1050)]
                elif sk == "gig":
                    iv = [(rng.randint(630, 680), rng.randint(800, 860)), (rng.randint(990, 1040), rng.randint(1200, 1290))]
                p.night = iv[0][0] == 0
                p.shift = iv
                if p.mode == "work_from_home" or (p.sector in ("prof", "fin", "info", "mgmt") and sk == "day" and rng.random() < .2):
                    p.wfh = True
                    cm = 0
                elif p.wd == "EXT" or p.wd not in INTRA:
                    cm = rng.randint(35, 60)
                else:
                    base = DIST[(H.district, p.wd)]
                    cm = int({"car": base * 2 + 6, "carpool": base * 2 + 14, "transit": base * 4.5 + 15, "walk": base * 18, "bike": base * 6 + 3,
                              "rideshare": base * 2 + 12}.get(p.mode, base * 2 + 6))
                    cm = min(cm, 85)
                p.cm = cm
                busy = []
                for (s, e) in iv:
                    if len(iv) == 1 and e - s >= 360 and sk not in ("gig",):
                        mid = (s + e) // 2 + rng.randint(-40, 40)
                        L = rng.randint(30, 45)
                        p.lunch = (mid, mid + L)
                        busy += [(max(0, s - cm), mid), (mid + L, min(1440, e + cm))]
                    else:
                        busy.append((max(0, s - cm) if s > 0 else 0, min(1440, e + cm) if e < 1440 else 1440))
                p.busy = busy
                if p.night:
                    end_m = busy[0][1]
                    st_e = busy[-1][0]
                    p.wake, p.bed = end_m, st_e
                    awake = [(end_m, min(end_m + rng.randint(60, 110), 600)), (rng.randint(860, 930), st_e)]
                    p.free = subtract(awake, [])
                    continue
                wake = min(wake, max(200, busy[0][0] - rng.randint(35, 70)))
                bed = max(bed, min(1439, busy[-1][1] + 25))
        if p.student in ("public_k12", "private_k12") and school_on:
            if rng.random() < .066:
                p.absent = True
            else:
                g = p.grade or 0
                s, e = (500, 900) if g <= 5 else (465, 905) if g <= 8 else (450, 880)
                p.busy.append((s - 25, e + 20))
                p.shift = [(s, e)]
        elif p.student in ("head_start", "public_prek", "child_care_center", "family_child_care") and weekday:
            p.busy.append((480, 930))
        p.wake, p.bed = wake, min(1439, bed)
        p.free = subtract([(wake + 15, p.bed - 10)], p.busy)


def _paid_on(p, c):
    cad, pd = p.cadence, p.payday
    if not pd:
        return False
    if cad == "weekly":
        return pd[0] == c["dow"]
    if cad == "biweekly":
        return pd[0] == c["dow"] and pd[1] == c["week_parity"]
    return c["dom"] in pd


def paid_today(p, cal):
    """Payroll lands only on bank days; a payday that falls on a weekend or holiday is paid the business day before."""
    if not cal["bank_day"]:
        return False
    return _paid_on(p, cal) or any(_paid_on(p, c) for c in cal["pay_ahead"])


def handle_check(sim, q, P, H, W, amt, t0, what):
    """A paper check has to be cashed or deposited before it is money."""
    rng = sim.rng
    if W.bank is None:
        org = sim.pick(("check_casher", "grocery_full", "supercenter"), H.district, 6.0)
        if org is None:
            sim.credit(W, amt, "cash")
            return
        fee = round(amt * rng.choice([.015, .019, .025, .03]), 2) if org.kind == "check_casher" else rng.choice([4.0, 6.0, 8.0])
        miles, mode, mins, fr = sim.trip(P, H, H.district, org.district)
        t = sim.slot(P, 18 + mins, SHOP, max(org.open, t0 + 10), org.close)
        if t is None:
            sim.emit(min(1380, t0 + 60), "non_monetary_job", "money_services", "check_not_cashed_yet", P, H, P, org, tmin=3,
                     outcome="rescheduled", fr=("hours_mismatch",), ctx=dict(org=org.name, amt="%.2f" % amt, what=what))
            return

        def run(t=t):
            sim.credit(W, amt - fee, "cash")
            sim.emit(t, "transfer", "money_services", "check_cashing", P, H, org, P, channel="in_person", method="check", gross=amt,
                     user=fee, fee_type="check_cashing_fee", fee=fee, tmin=18, wait=rng.randint(2, 14), miles=miles, mode=mode, fr=fr,
                     ctx=dict(org=org.name, amt="%.2f" % amt, what=what, fee="%.2f" % fee))
        push(q, t, run)
    elif rng.random() < .62 and H.internet != "no":
        t = sim.slot_soft(P, 4, ((max(t0 + 5, 400), 1320, 1),))
        avail = amt if amt <= 300 else 300.0

        def run(t=t):
            sim.credit(W, avail, "bank")
            if amt > avail:
                W.give("savings", amt - avail)
            sim.emit(t, "transfer", "money_services", "mobile_check_deposit", P, H, P, W.bank_org, channel="app", method="check", gross=amt,
                     tmin=4, fr=(("pending_hold",) if amt > avail else ()), ctx=dict(org=W.bank_org.name, amt="%.2f" % amt, what=what, avail="%.0f" % avail))
        push(q, t, run)
    else:
        key = "first" if "First" in W.bank_org.name else "corbel" if "Corbel" in W.bank_org.name else "cu"
        br = sim.branches.get(key) or sim.branches["first"]
        org = min(br, key=lambda o: DIST[(H.district, o.district)])
        miles, mode, mins, fr = sim.trip(P, H, H.district, org.district)
        t = sim.slot(P, 14 + mins, OFFICE, max(org.open, t0 + 5), org.close) if org.open is not None else None
        if t is None:
            sim.credit(W, 0, "bank")
            W.give("savings", amt)
            sim.emit(min(1380, t0 + 90), "non_monetary_job", "money_services", "check_not_cashed_yet", P, H, P, org, tmin=2,
                     outcome="rescheduled", fr=("hours_mismatch",), ctx=dict(org=org.name, amt="%.2f" % amt, what=what))
            return

        def run(t=t):
            sim.credit(W, amt, "bank")
            sim.emit(t, "transfer", "money_services", "branch_check_deposit", P, H, P, org, channel="in_person", method="check", gross=amt,
                     tmin=14, wait=rng.randint(1, 12), miles=miles, mode=mode, fr=fr, ctx=dict(org=org.name, amt="%.2f" % amt, what=what))
        push(q, t, run)


def gen_income(sim, H, q):
    rng, cal, X = sim.rng, sim.cal, sim.X
    dom = cal["dom"]
    for p in H.members:
        W = p.wallet
        # ---------------- payroll
        if p.emp in ("employed_full_time", "employed_part_time") and p.org is not None and paid_today(p, cal):
            per = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12}[p.cadence]
            gross = p.wage / per * (rng.uniform(.80, 1.16) if p.wsched == "variable" else rng.uniform(.98, 1.03))
            if p.tipped:
                gross *= 1.12
            gross = round(gross, 2)
            kids = len(H.kids)
            fed = round(gross * max(0.0, .035 + .125 * min(1.0, p.wage / 130000.0) - .018 * kids), 2)
            st = round(gross * STATE_INCOME_TAX * .9, 2)
            fica = round(gross * .0765, 2)
            prem = 0.0
            if p.cov == "employer" and (p.rel in ("head", "resident") or rng.random() < .35):
                fam = len([m for m in H.members if m.cov == "employer"]) > 1
                prem = round((6900 if fam else 1650) * rng.uniform(.8, 1.25) / per, 2)
            k401 = round(gross * p.k401, 2)
            dues = round(gross * .013, 2) if p.union else 0.0
            garn = round((gross - fed - st - fica) * rng.choice([.15, .15, .25]), 2) if p.garnish else 0.0
            net = round(gross - fed - st - fica - prem - k401 - dues - garn, 2)
            small = p.org.size < 20
            if W.bank is None:
                how = "paycard" if (not small and rng.random() < .7) else "check"
            else:
                how = "check" if (small and rng.random() < .10) else ("paycard" if (p.sector in ("admin", "food", "retail") and rng.random() < .05) else "ach")
            t = rng.randint(5, 380) if how != "check" else (p.shift[-1][1] if p.works and p.shift else rng.randint(600, 900))
            org = p.org
            sim.payroll[org.oid] = sim.payroll.get(org.oid, (0, 0.0))
            sim.payroll[org.oid] = (sim.payroll[org.oid][0] + 1, sim.payroll[org.oid][1] + gross)

            def run(t=t, p=p, W=W, gross=gross, fed=fed, st=st, fica=fica, prem=prem, k401=k401, dues=dues, garn=garn, net=net, how=how, org=org):
                kind = {"ach": "paycheck_direct_deposit", "paycard": "paycheck_paycard", "check": "paycheck_paper_check"}[how]
                ctx = dict(org=org.name, occ=p.occ, net="%.2f" % net, gross="%.2f" % gross, cadence=p.cadence)
                i = sim.emit(t, "income", "income", kind, p, H, org, p, channel=("automatic" if how != "check" else "in_person"),
                             method=("check" if how == "check" else how), gross=gross, lens=("labor",), ctx=ctx)
                sim.emit(t, "tax", "income", "payroll_income_tax_withholding", p, H, p, X["x_irs"], channel="automatic", method="payroll_deduction",
                         gross=fed + st, user=fed + st, lens=("labor",), related=i, ctx=dict(org=org.name, fed="%.2f" % fed, st="%.2f" % st))
                sim.emit(t, "tax", "income", "payroll_fica", p, H, p, X["x_irs"], channel="automatic", method="payroll_deduction",
                         gross=fica, user=fica, lens=("labor",), related=i, ctx=dict(org=org.name, amt="%.2f" % fica))
                if prem:
                    sim.emit(t, "bill_payment", "health", "health_premium_payroll", p, H, p, X["x_ins_a"], channel="automatic", method="payroll_deduction",
                             gross=prem, user=prem, lens=("labor",), related=i, ctx=dict(org=org.name, amt="%.2f" % prem))
                if k401:
                    sim.emit(t, "transfer", "discretionary", "retirement_contribution_payroll", p, H, p, X["x_broker"], channel="automatic",
                             method="payroll_deduction", gross=k401, user=k401, lens=("labor",), related=i, ctx=dict(org=org.name, amt="%.2f" % k401))
                if dues:
                    sim.emit(t, "bill_payment", "income", "union_dues", p, H, p, X["x_union_ed" if org.sector == "education" else ("x_union_pub" if org.otype == "government" else "x_union_trades")], channel="automatic", method="payroll_deduction",
                             gross=dues, user=dues, lens=("labor",), related=i, ctx=dict(amt="%.2f" % dues))
                if garn:
                    sim.emit(t, "bill_payment", "money_services", "wage_garnishment", p, H, p, X["x_ed"] if rng.random() < .5 else X["x_csdu"],
                             channel="automatic", method="payroll_deduction", gross=garn, user=garn, lens=("labor", "consumer_finance"),
                             related=i, ctx=dict(amt="%.2f" % garn))
                if how == "ach":
                    sim.credit(W, net, "bank")
                elif how == "paycard":
                    sim.credit(W, net, "prepaid")
                else:
                    handle_check(sim, q, p, H, W, net, t, "paycheck")
            push(q, t, run)
        # ---------------- tips
        if p.tipped and p.works and p.shift:
            amt = round(rng.uniform(40, 165) if p.occ in ("server", "bartender") else rng.uniform(8, 70), 0)
            t = min(1435, p.shift[-1][1])

            def run(t=t, p=p, W=W, amt=amt):
                sim.credit(W, amt, "cash")
                sim.emit(t, "income", "income", "cash_tips", p, H, X["x_customers"], p, method="cash", gross=amt, lens=("labor",),
                         ctx=dict(amt="%.0f" % amt, occ=p.occ, org=p.org.name if p.org else "the shop"))
            push(q, t, run)
        # ---------------- gig payouts
        if p.gig and (p.works if p.sched == "gig" else rng.random() < .30):
            main = p.sched == "gig"
            tstart = None
            if not main:
                tstart = sim.slot(p, rng.randint(120, 210), EVE)
                if tstart is None:
                    continue
            earn = round(rng.uniform(55, 195) if main else rng.uniform(22, 88), 2)
            instant = rng.random() < .55
            fee = (rng.choice([.85, 1.49, 1.99]) if instant else 0.0)
            weekly = (not instant) and cal["dow"] in (1, 2) and rng.random() < .6
            amt = round(earn * rng.uniform(3.5, 5.5), 2) if weekly else earn
            t = min(1438, (p.shift[-1][1] if main and p.shift else tstart + 200) + 5)
            if instant or weekly:
                def run(t=t, p=p, W=W, amt=amt, fee=fee, instant=instant):
                    sim.credit(W, amt - fee, "bank")
                    sim.emit(t if instant else rng.randint(300, 480), "income", "income", "gig_payout_instant" if instant else "gig_payout_weekly", p, H,
                             X[rng.choice(["x_ride1", "x_deliv1", "x_deliv2", "x_ride2"])], p, channel="app", method="ach" if W.bank is not None else "prepaid",
                             gross=amt, fee_type="instant_cashout_fee" if fee else "", fee=fee, user=fee, lens=("labor",),
                             ctx=dict(amt="%.2f" % amt, fee="%.2f" % fee))
                push(q, t if instant else 400, run)
        # ---------------- self-employment receipts
        if p.emp == "self_employed" and p.sched != "gig" and p.works and rng.random() < .55:
            occ = p.occ
            lo, hi, mix = {"general contractor": (350, 4800, "check"), "landscaper": (60, 420, "mixed"), "hair stylist": (120, 430, "mixed"),
                           "home child care provider": (180, 900, "mixed"), "freelance designer": (400, 3200, "ach"),
                           "independent consultant": (900, 7500, "ach"), "farmer": (300, 6000, "check"), "truck owner-operator": (900, 2600, "ach"),
                           "house cleaner": (90, 280, "mixed"), "real estate agent": (0, 0, "ach"), "food vendor": (220, 900, "mixed"),
                           "music and tutoring teacher": (40, 170, "mixed"), "shop owner": (350, 2400, "card"), "solo practitioner": (700, 4500, "card")}.get(occ, (100, 800, "mixed"))
            if hi == 0 or (occ in ("freelance designer", "independent consultant") and rng.random() < .7):
                continue
            amt = round(rng.uniform(lo, hi), 2)
            how = mix if mix != "mixed" else rng.choices(["cash", "p2p_app", "card", "check"], [.38, .30, .22, .10])[0]
            fee = round(amt * .029 + .30, 2) if how == "card" else 0.0
            if occ == "truck owner-operator":
                fee = round(amt * .03, 2)
            t = min(1430, (p.shift[-1][1] if p.shift else 1020) + rng.randint(-60, 30))

            def run(t=t, p=p, W=W, amt=amt, how=how, fee=fee, occ=occ):
                ctx = dict(amt="%.2f" % amt, occ=occ, fee="%.2f" % fee)
                i = sim.emit(t, "income", "income", "self_employment_receipts", p, H, X["x_customers"], p,
                             method={"card": "credit", "cash": "cash", "check": "check", "ach": "ach", "p2p_app": "p2p_app"}[how], gross=amt,
                             user=fee, fee_type=("card_processing_fee" if how == "card" else "factoring_fee" if fee else ""), fee=fee,
                             lens=("small_business", "labor"), ctx=ctx)
                if how == "cash":
                    sim.credit(W, amt, "cash")
                elif how == "check":
                    handle_check(sim, q, p, H, W, amt, t, "customer check")
                else:
                    sim.credit(W, amt - fee, "bank")
            push(q, t, run)
        # ---------------- Social Security
        if p.ss > 0 and p.ss_cohort in cal["ss_cohorts"]:
            gross = round(p.ss, 2)
            t = rng.randint(1, 300)
            partb = PART_B_PREMIUM if (p.cov in ("medicare", "medicare_advantage") and gross > PART_B_PREMIUM + 50) else 0.0
            buyin = p.cov == "medicare_medicaid_dual"
            partd = rng.choice([0, 0, 0, 17.4, 34.5, 46.2, 58.0]) if partb else 0.0
            nh = H.gq == "nursing_home" and p.cov == "medicare_medicaid_dual"
            net = round(gross - partb - partd, 2)

            def run(t=t, p=p, W=W, gross=gross, partb=partb, partd=partd, net=net, buyin=buyin, nh=nh):
                how = "ach" if W.bank is not None else "prepaid"
                ctx = dict(gross="%.2f" % gross, net="%.2f" % net, partb="%.2f" % partb, kind=p.ss_type.replace("_", " "))
                i = sim.emit(t, "benefit_issuance", "income", "social_security_deposit", p, H, X["x_treasury"], p, channel="automatic", method=how,
                             gross=gross, third=gross, payer="Social Security (%s)" % ("OASI" if p.ss_type != "ssdi" else "Disability Insurance"),
                             fund="federal", ctx=ctx)
                if partb:
                    sim.emit(t, "bill_payment", "health", "medicare_part_b_premium", p, H, p, X["x_cms"], channel="automatic", method="payroll_deduction",
                             gross=partb, user=partb, related=i, ctx=dict(amt="%.2f" % partb, gross="%.2f" % gross, net="%.2f" % net))
                if partd:
                    sim.emit(t, "bill_payment", "health", "medicare_drug_plan_premium", p, H, p, X["x_ins_b"], channel="automatic", method="payroll_deduction",
                             gross=partd, user=partd, related=i, ctx=dict(amt="%.2f" % partd))
                if buyin:
                    sim.emit(t, "bill_payment", "health", "medicare_part_b_state_buy_in", p, H, X["x_medicaid"], X["x_cms"], ben=p, channel="automatic",
                             method="none", gross=PART_B_PREMIUM, third=PART_B_PREMIUM, payer="State Medicaid (Medicare Savings Program)", fund="mixed",
                             related=i, ctx=dict(amt="%.2f" % PART_B_PREMIUM))
                if nh:
                    keep = 50.0
                    sim.emit(t + 1, "bill_payment", "health", "nursing_home_patient_liability", p, H, p, sim.by_name.get(H.facility, sim.one("nursing_home")),
                             channel="automatic", method="ach", gross=net - keep, user=net - keep, related=i,
                             ctx=dict(amt="%.2f" % (net - keep), keep="%.0f" % keep, org=H.facility))
                    W.inflow += net
                    W.outflow += net - keep
                    W.cash += keep
                else:
                    sim.credit(W, net, "bank")
            push(q, t, run)
        # Federal benefits on the Direct Express prepaid card (v2; estimate): about one call to its call center a year and a
        # half per cardholder, and about four calls in ten end without help (long holds, dropped calls, a locked card).
        if (p.ss > 0 or p.ssi > 0) and W is not None and W.bank is None and rng.random() < 1 / 550.0:
            def rund(p=p):
                bad = rng.random() < .4
                why = rng.choice(["the hold ran past an hour and the call dropped", "the card was locked after a fraud flag and the line could not unlock it",
                                  "the automated line did not recognize the card number"])
                sim.emit(rng.randint(540, 1020), "failed_attempt" if bad else "non_monetary_job", "money_services", "direct_express_call", p, H, p, X["x_treasury"],
                         channel="phone", tmin=rng.randint(45, 110) if bad else rng.randint(15, 40), outcome="failed" if bad else "completed",
                         fr=(("wait", "outage") if bad else ("wait",)), lens=("aging", "public_finance"), ctx=dict(reason=why if bad else ""))
            push(q, 200, rund)
        if p.ssi > 0 and cal["ssi_today"]:
            def run(p=p, W=W):
                sim.credit(W, p.ssi, "bank")
                sim.emit(rng.randint(1, 300), "benefit_issuance", "income", "ssi_deposit", p, H, X["x_treasury"], p, channel="automatic",
                         method="ach" if W.bank is not None else "prepaid", gross=p.ssi, third=p.ssi, payer="Supplemental Security Income", fund="federal",
                         ctx=dict(amt="%.2f" % p.ssi))
            push(q, 5, run)
        if p.pension and rng.random() < (.035 if dom == 3 else .45 if dom == 1 else .01):
            def run(p=p, W=W):
                net = round(p.pension * .9, 2)
                sim.credit(W, net, "bank")
                sim.emit(rng.randint(1, 360), "income", "income", "pension_payment", p, H, X["x_pension"], p, channel="automatic",
                         method="ach" if W.bank is not None else "check", gross=p.pension, lens=("aging",), ctx=dict(amt="%.2f" % p.pension, net="%.2f" % net))
            push(q, 6, run)
        if p.va and cal["ssi_today"]:   # VA compensation follows the same 1st-or-business-day-before rule as SSI
            def run(p=p, W=W):
                sim.credit(W, p.va, "bank")
                sim.emit(rng.randint(1, 300), "benefit_issuance", "income", "va_compensation_deposit", p, H, X["x_va"], p, channel="automatic", method="ach",
                         gross=p.va, third=p.va, payer="VA disability compensation", fund="federal", ctx=dict(amt="%.2f" % p.va))
            push(q, 5, run)
        if p.ui and cal["bank_day"] and (int(p.pid[1:]) % 5) == cal["dow"]:   # weekday deposits only (v1 also paid one group on Saturdays)
            amt = round(p.ui / 4.33, 2)

            def run(p=p, W=W, amt=amt):
                card = W.bank is None or rng.random() < .3
                sim.credit(W, amt, "prepaid" if card else "bank")
                sim.emit(rng.randint(120, 420), "benefit_issuance", "income", "unemployment_benefit", p, H, X["x_ui"], p, channel="automatic",
                         method="prepaid" if card else "ach", gross=amt, third=amt, payer="Unemployment Insurance", fund="state", lens=("labor",),
                         ctx=dict(amt="%.2f" % amt))
            push(q, 120, run)
    # ---------------- household-level benefits
    W0, head = H.wallets[0], H.head
    if H.snap and H.snap_day == dom:
        def run():
            H.snap_bal += H.snap
            sim.emit(rng.randint(1, 360), "benefit_issuance", "income", "snap_issuance", head, H, X["x_snap"], head, channel="automatic", method="ebt_snap",
                     gross=H.snap, third=H.snap, payer="SNAP (USDA Food and Nutrition Service)", fund="federal",
                     ctx=dict(amt="%.0f" % H.snap, n=len(H.members)))
        push(q, 2, run)
    if H.wic and H.wic_day == dom:
        def run():
            H.wic_bal = H.wic
            sim.emit(rng.randint(1, 360), "benefit_issuance", "income", "wic_benefit_load", head, H, X["x_snap"], head, channel="automatic", method="wic",
                     gross=H.wic, third=H.wic, payer="WIC (USDA)", fund="federal", lens=("family_care",), ctx=dict(amt="%.0f" % H.wic))
        push(q, 2, run)
    if H.tanf and H.tanf_day == dom:
        def run():
            i = sim.emit(rng.randint(1, 360), "benefit_issuance", "income", "tanf_cash_issuance", head, H, X["x_snap"], head, channel="automatic",
                         method="ebt_cash", gross=H.tanf, third=H.tanf, payer="TANF cash assistance", fund="mixed", ctx=dict(amt="%.0f" % H.tanf))
            H.flags.add("tanf_today")
            sim.tanf_idx[H.hid] = i
        push(q, 2, run)
    if H.cs and rng.random() < .11:
        amt = round(H.cs * 12 / 26.0, 2)

        def run(amt=amt):
            sim.credit(W0, amt, "bank")
            sim.emit(rng.randint(60, 420), "transfer", "income", "child_support_received", head, H, X["x_csdu"], head, channel="automatic",
                     method="ach" if W0.bank is not None else "prepaid", gross=amt, lens=("family_care",), ctx=dict(amt="%.2f" % amt))
        push(q, 60, run)
    # ---------------- tax refunds (tax season)
    if cal["tax_season"] and not H.gq:
        for W in H.wallets:
            earners = [p for p in W.owners if p.wage > 0]
            ad = [p for p in W.owners if p.age >= 18]
            if not ad:
                continue
            wages = sum(p.wage for p in earners)
            kids = len(H.kids) if W is W0 else 0
            eitc = bool(earners) and wages < (22000 if not kids else 52000 + 6000 * min(kids, 3)) and (kids or 25 <= ad[0].age < 65)
            pr = (.17 if cal["eitc_wave"] else .012) if (eitc and kids) else .0105
            if not earners and not any(p.pension or p.inv for p in ad):
                pr = .002
            if rng.random() < pr:
                if eitc and kids:
                    credit = round(min(8200, max(600, rng.gauss(3400 + 1300 * min(kids, 3), 1100))), 2)
                    refund = round(max(0, rng.gauss(900, 500)), 2)
                elif eitc:
                    credit, refund = round(rng.uniform(120, 660), 2), round(max(50, rng.gauss(650, 300)), 2)
                else:
                    credit, refund = 0.0, round(max(60, rng.lognormvariate(7.75, .65)), 2)
                p = ad[0]
                r = rng.random()
                via = "refund_transfer" if (eitc and r < .24) or r < .05 else ("prepaid" if (W.bank is None or r < .10) else "ach")
                fees = round(rng.uniform(190, 420) + rng.choice([45, 55, 65]), 2) if via == "refund_transfer" else 0.0

                def run(p=p, W=W, credit=credit, refund=refund, via=via, fees=fees):
                    t = rng.randint(1, 400)
                    total = credit + refund
                    how = "prepaid" if via in ("prepaid", "refund_transfer") and W.bank is None else ("ach" if via != "prepaid" else "prepaid")
                    ctx = dict(amt="%.2f" % total, credit="%.2f" % credit, refund="%.2f" % refund, fee="%.2f" % fees, via=via.replace("_", " "))
                    i = sim.emit(t, "income", "income", "federal_tax_refund", p, H, X["x_treasury"], p, channel="automatic", method=how, gross=refund,
                                 user=fees, fee_type="tax_prep_and_refund_transfer_fees" if fees else "", fee=fees,
                                 lens=("public_finance",) + (("consumer_finance",) if fees else ()), ctx=ctx)
                    if credit:
                        sim.emit(t, "benefit_issuance", "income", "refundable_tax_credit", p, H, X["x_treasury"], p, channel="automatic", method=how,
                                 gross=credit, third=credit, payer="Earned Income Tax Credit and refundable Child Tax Credit", fund="federal",
                                 lens=("labor", "family_care"), related=i, ctx=ctx)
                    sim.credit(W, total - fees, "prepaid" if how == "prepaid" else "bank")
                    H.flags.add("refund_today")
                push(q, 3, run)
            elif rng.random() < .006:
                amt = round(rng.uniform(60, 880), 2)

                def run(p=ad[0], W=W, amt=amt):
                    sim.credit(W, amt, "bank")
                    sim.emit(rng.randint(1, 400), "income", "income", "state_tax_refund", p, H, X["x_staterev"], p, channel="automatic",
                             method="ach" if W.bank is not None else "check", gross=amt, lens=("public_finance",), ctx=dict(amt="%.2f" % amt))
                push(q, 4, run)


# ---------------------------------------------------------------------------------------------- bills
def _due_on(b, c):
    kind, org, amt, dom, method, W, freq, meta = b
    if freq == "M":
        return dom == c["dom"]
    if freq == "W":
        return dom == c["dow"]
    return dom[0] == c["dow"] and dom[1] == c["week_parity"]


def due_today(b, cal):
    """ACH autopays post only on bank days; one due on a weekend or holiday posts the next business day."""
    if b[4] == "ach_auto":
        if not cal["bank_day"]:
            return False
        return _due_on(b, cal) or any(_due_on(b, c) for c in cal["ach_catchup"])
    return _due_on(b, cal)


LATE_FEE = {"rent": (50, 100), "electric_bill": (5, 18), "gas_bill": (5, 15), "water_bill": (5, 12), "internet_bill": (10, 15),
            "phone_bill": (5, 10), "car_payment": (25, 39), "credit_card_payment": (30, 41), "auto_insurance": (10, 25), "mortgage": (45, 110)}


def gen_bills(sim, H, q):
    rng, cal, X = sim.rng, sim.cal, sim.X
    head = H.head
    adult = [p for p in H.adults if p.wallet is H.wallets[0]] or [head]
    for bi, b in enumerate(H.bills):
        if not due_today(b, cal):
            continue
        kind, org, amt, dom, method, W, freq, meta = b
        cat = BILL_CAT[kind][0]
        P = rng.choice([p for p in W.owners if p.age >= 18] or adult)
        ctx = dict(org=org.name, amt="%.2f" % amt, bill=kind.replace("_", " "))
        fr, third, payer, fund, rel = [], 0.0, "", "", None
        lens = []
        if kind == "child_care_payment" and meta and meta[0] == "ccdf":
            third, payer, fund = meta[1], "State child care assistance (CCDF)", "mixed"
            ctx["subsidy"] = "%.2f" % third
            lens.append("family_care")
        if kind in ("child_care_payment", "after_school_fee"):
            lens.append("family_care")
        if kind == "streaming_subscription" and rng.random() < .04:
            fr.append("price_spike")
            ctx["hike"] = "1"
        if kind == "electric_bill" and not H.gasheat and rng.random() < .10:
            fr.append("price_spike")
            ctx["hike"] = "1"
        if kind == "health_premium" and rng.random() < .30:
            fr.append("price_spike")
            ctx["hike"] = "1"
        if kind == "rent":
            # roommates send their share first
            others = [w for w in H.wallets[1:] if any(o.rel in ("roommate", "sibling", "other_relative", "adult_child") for o in w.owners)]
            if others and H.htype in ("roommates", "other_family"):
                sh = round(amt / (len(others) + 1), 2)
                for w in others:
                    o = w.owners[0]
                    t0 = sim.slot_soft(o, 2, ((420, 720, 1),))

                    def rs(t0=t0, w=w, o=o, sh=sh, W=W):
                        if w.avail("p2p_app") >= sh:
                            w.take("p2p_app", sh)
                            W.give("bank", sh)
                            sim.emit(t0, "transfer", "housing", "roommate_rent_share", o, H, o, head, channel="app", method="p2p_app", gross=sh, user=sh,
                                     tmin=2, ctx=dict(amt="%.2f" % sh))
                        elif w.cash >= sh:
                            w.take("cash", sh)
                            W.give("cash", sh)
                            sim.emit(t0, "transfer", "housing", "roommate_rent_share", o, H, o, head, channel="in_person", method="cash", gross=sh, user=sh,
                                     tmin=2, ctx=dict(amt="%.2f" % sh))
                        else:
                            sim.emit(t0, "failed_attempt", "housing", "roommate_rent_share", o, H, o, head, channel="app", method="p2p_app", gross=sh,
                                     tmin=3, outcome="failed", fr=("insufficient_funds",), ctx=dict(amt="%.2f" % sh, reason="the roommate was short this month"))
                    push(q, t0, rs)
            if dom > 5:
                lf = round(rng.uniform(*LATE_FEE["rent"]), 0)
                ctx["late"] = "%.0f" % lf
        fee = None
        if method in ("online", "phone", "in_person", "check_mail") and kind in LATE_FEE and rng.random() < .045 and kind != "rent":
            fee = ("late_fee", float(rng.randint(*LATE_FEE[kind])))
            ctx["late"] = "%.0f" % fee[1]
        if kind == "rent" and dom > 5:
            fee = ("late_fee", float(ctx["late"]))

        if method == "ach_auto":
            t = rng.randint(90, 420)

            def run(t=t, W=W, P=P, kind=kind, cat=cat, org=org, amt=amt, ctx=ctx, fr=fr, third=third, payer=payer, fund=fund, lens=lens, bi=bi):
                have = W.bank if W.bank is not None else -1
                if have >= amt:
                    W.take("ach", amt)
                    i = sim.emit(t, "bill_payment", cat, kind, P, H, P, org, channel="automatic", method="ach", gross=amt + third, user=amt, third=third,
                                 payer=payer, fund=fund, fr=fr, lens=lens, ctx=ctx)
                elif W.od and amt - max(have, 0) < 900 and rng.random() < .6:
                    W.take("ach", amt + W.od_fee)
                    sim.bump("overdraft")
                    i = sim.emit(t, "bill_payment", cat, kind, P, H, P, org, channel="automatic", method="ach", gross=amt + third, user=amt + W.od_fee,
                                 third=third, payer=payer, fund=fund, fee_type="overdraft_fee", fee=W.od_fee, fr=fr + ["insufficient_funds"], lens=lens, ctx=ctx)
                else:
                    rf = float(rng.choice([15, 20, 25, 25, 30, 35]))
                    ctx2 = dict(ctx)
                    ctx2["reason"] = "the autopay bounced for insufficient funds"
                    sim.bump("nsf_return")
                    i = sim.emit(t, "failed_attempt", cat, kind, P, H, P, org, channel="automatic", method="ach", gross=amt + third, user=0,
                                 fee_type="returned_payment_fee", fee=rf, outcome="failed", fr=fr + ["insufficient_funds"], lens=lens, ctx=ctx2)
                    H.flags.add("nsf_today")
                    if sim.carry is not None:
                        bill_missed(sim.carry, sim, H, bi, W, P, i, amt, fees=rf, how="returned")
                if kind == "mortgage" and H.escrow and i is not None and sim.rows[i][2] == "bill_payment":
                    tx = round(amt * rng.uniform(.16, .24), 2)
                    sim.emit(t, "tax", "housing", "property_tax_escrow", P, H, P, sim.one("county"), channel="automatic", method="ach", gross=tx, user=0,
                             related=i, ctx=dict(amt="%.2f" % tx, ins="%.2f" % (amt * .07)))
            push(q, t, run)
        elif method == "card_auto":
            t = rng.randint(30, 430)

            def run(t=t, W=W, P=P, kind=kind, cat=cat, org=org, amt=amt, ctx=ctx, fr=fr, lens=lens, bi=bi):
                i, oc, m = sim.pay(t, P, H, W, None, cat, kind, amt, taxable=(kind in ("streaming_subscription", "other_subscription")), channel="automatic",
                                   ctx=ctx, fr=fr, lens=lens, rtype="bill_payment", quiet_fail=0.0, to=org)
                if sim.carry is not None and oc not in ("completed", "partial"):
                    bill_missed(sim.carry, sim, H, bi, W, P, i, amt, how="declined")
            push(q, t, run)
        elif method in ("online", "phone"):
            dur = rng.randint(3, 9) if method == "online" else rng.randint(7, 16)
            t = sim.slot_soft(P, dur, ((420, 540, 1), (690, 780, 1), (1020, 1320, 2)))
            cf = None
            if method == "phone":
                cf = ("phone_payment_fee", rng.choice([2.5, 2.95, 3.95, 5.95]))
            elif kind in ("rent", "lot_rent") and rng.random() < .35:
                cf = ("card_convenience_fee", round(amt * .0295, 2))
            elif kind in ("electric_bill", "gas_bill", "water_bill") and rng.random() < .30:
                cf = ("card_convenience_fee", rng.choice([1.95, 2.25, 2.95, 3.95]))
            if fee and cf:
                cf = (cf[0] + "+late_fee", cf[1] + fee[1])
            elif fee:
                cf = fee
            usecard = bool(cf and "card" in cf[0]) or method == "phone" or kind in ("phone_bill", "internet_bill", "auto_insurance") and rng.random() < .5
            frx = list(fr)
            if H.internet == "no" and method == "online":
                frx.append("digital_barrier")

            def run(t=t, W=W, P=P, kind=kind, cat=cat, org=org, amt=amt, ctx=ctx, cf=cf, usecard=usecard, dur=dur, method=method, frx=frx, third=third, payer=payer, fund=fund, lens=lens,
                    bi=bi, lfee=(fee[1] if fee else 0.0)):
                if usecard or W.bank is None:
                    i, oc, m = sim.pay(t, P, H, W, None, cat, kind, amt, channel=method, ctx=ctx, tmin=dur, fr=frx, lens=lens, rtype="bill_payment",
                                       fee=cf, quiet_fail=0.0, to=org, third=0.0)
                    if sim.carry is not None and oc not in ("completed", "partial"):
                        bill_missed(sim.carry, sim, H, bi, W, P, i, amt, late=lfee)
                else:
                    f = cf[1] if cf else 0.0
                    if W.bank >= amt + f or W.od:
                        odf = W.od_fee if W.bank < amt + f else 0
                        W.take("ach", amt + f + odf)
                        if odf:
                            sim.bump("overdraft")
                        i = sim.emit(t, "bill_payment", cat, kind, P, H, P, org, channel=method, method="ach", gross=amt + third, user=amt + f + odf, third=third,
                                     payer=payer, fund=fund, fee_type=((cf[0] if cf else "") + ("+overdraft_fee" if odf and cf else "overdraft_fee" if odf else "")),
                                     fee=f + odf, tmin=dur, fr=frx + (["insufficient_funds"] if odf else []), lens=lens, ctx=ctx)
                    else:
                        part = round(max(0, W.bank) * rng.uniform(.6, .95), 2)
                        if kind in ("rent", "electric_bill", "gas_bill", "water_bill", "credit_card_payment", "car_payment") and part > 20:
                            W.take("ach", part)
                            ctx2 = dict(ctx)
                            ctx2["short"] = "%.2f" % (amt - part)
                            i = sim.emit(t, "bill_payment", cat, kind, P, H, P, org, channel=method, method="ach", gross=amt, user=part, tmin=dur,
                                         outcome="partial", fr=frx + ["insufficient_funds"], lens=lens, ctx=ctx2)
                            if sim.carry is not None:
                                bill_missed(sim.carry, sim, H, bi, W, P, i, amt - part, late=lfee, how="partial")
                        else:
                            ctx2 = dict(ctx)
                            ctx2["reason"] = "the account could not cover it today"
                            i = sim.emit(t, "failed_attempt", cat, kind, P, H, P, org, channel=method, method="ach", gross=amt, tmin=dur, outcome="abandoned",
                                         fr=frx + ["insufficient_funds"], lens=lens, ctx=ctx2)
                            if sim.carry is not None:
                                bill_missed(sim.carry, sim, H, bi, W, P, i, amt, late=lfee)
                if kind == "mortgage" and H.escrow and i is not None and sim.rows[i][2] == "bill_payment":
                    tx = round(amt * rng.uniform(.16, .24), 2)
                    sim.emit(t, "tax", "housing", "property_tax_escrow", P, H, P, sim.one("county"), channel="automatic", method="ach", gross=tx, user=0,
                             related=i, ctx=dict(amt="%.2f" % tx, ins="%.2f" % (amt * .07)))
            push(q, t, run)
        elif method == "check_mail":
            t = sim.slot_soft(P, 6, ((480, 720, 1), (1020, 1260, 1)))

            def run(t=t, W=W, P=P, kind=kind, cat=cat, org=org, amt=amt, ctx=ctx, fee=fee, fr=fr, lens=lens, bi=bi):
                f = fee[1] if fee else 0.0
                if W.bank is not None and W.bank >= amt + f:
                    W.take("check", amt + f + .78)
                    sim.emit(t, "bill_payment", cat, kind, P, H, P, org, channel="mail", method="check", gross=amt, user=amt + f + .78,
                             fee_type=(fee[0] + "+postage") if fee else "postage", fee=f + .78, tmin=6, fr=fr, lens=lens, ctx=ctx)
                else:
                    ctx2 = dict(ctx)
                    ctx2["reason"] = "the checkbook balance would not cover it, so the envelope stayed on the counter"
                    i = sim.emit(t, "failed_attempt", cat, kind, P, H, P, org, channel="mail", method="check", gross=amt, tmin=4, outcome="abandoned",
                                 fr=fr + ["insufficient_funds"], lens=lens, ctx=ctx2)
                    if sim.carry is not None:
                        bill_missed(sim.carry, sim, H, bi, W, P, i, amt, late=f)
            push(q, t, run)
        elif method in ("in_person", "money_order"):
            # where the payment is physically made
            if kind in ("rent", "lot_rent"):
                dest = org
            elif kind in ("electric_bill", "gas_bill", "water_bill", "internet_bill") and org.district == H.district and org.open is not None:
                dest = org
            elif kind == "phone_bill":
                dest = sim.pick(("phone_store", "dollar", "check_casher"), H.district, 5.0) or org
            elif kind in ("bhph_car_payment", "rent_to_own_payment"):
                dest = org
            else:
                dest = sim.pick(("check_casher", "grocery_full", "supercenter", "post_office"), H.district, 6.0) or org
            agent = dest is not org
            miles, mode, mins, tfr = sim.trip(P, H, H.district, dest.district if dest.district != "EXT" else H.district)
            o, c = (dest.open, dest.close) if dest.open is not None else (540, 1020)
            t = sim.slot(P, 12 + min(mins, 40), SHOP, o, c)
            if t is None:
                ctx2 = dict(ctx)
                ctx2["reason"] = "the office hours ended before anyone in the household was free"
                i = sim.emit(rng.randint(1020, 1200), "failed_attempt", cat, kind, P, H, P, org, channel="in_person", method="cash", gross=amt, tmin=2,
                             outcome="rescheduled", fr=fr + ["hours_mismatch"] + tfr, lens=lens, ctx=ctx2)
                if sim.carry is not None:
                    bill_missed(sim.carry, sim, H, bi, W, P, i, amt, how="no_time")
                continue
            mo = method == "money_order" or (agent and kind in ("rent", "car_payment", "auto_insurance"))

            def run(t=t, W=W, P=P, kind=kind, cat=cat, org=org, dest=dest, amt=amt, ctx=ctx, fee=fee, fr=fr, mo=mo, agent=agent, miles=miles, mode=mode, tfr=tfr, lens=lens, bi=bi):
                f = fee[1] if fee else 0.0
                ft = fee[0] if fee else ""
                rel = None
                if mo:
                    mf = rng.choice([1.25, 1.75, 2.10, 2.55])
                    src = sim.pick(("post_office", "grocery_full", "check_casher", "gas"), H.district, 5.0) or dest
                    if W.cash >= amt + f + mf:
                        W.take("cash", mf)
                        rel = sim.emit(t - 12 if t > 12 else t, "purchase", "money_services", "money_order_purchase", P, H, P, src, method="cash",
                                       gross=amt, user=mf, fee_type="money_order_fee", fee=mf, tmin=9, wait=rng.randint(1, 9), miles=miles, mode=mode,
                                       fr=tfr, lens=lens, ctx=dict(org=src.name, amt="%.2f" % amt, fee="%.2f" % mf, bill=ctx["bill"]))
                        meth = "money_order"
                    else:
                        meth = "cash"
                else:
                    meth = "cash"
                    if agent:
                        f += 1.5
                        ft = (ft + "+" if ft else "") + "walk_in_bill_pay_fee"
                have = W.cash
                ctx["org"] = org.name
                ctx["at"] = dest.name
                if have >= amt + f:
                    W.take("cash", amt + f)
                    sim.emit(t, "bill_payment", cat, kind, P, H, P, org, method=meth, gross=amt, user=amt + f, fee_type=ft, fee=f, tmin=12,
                             wait=rng.randint(0, 15), miles=(0 if rel is not None else miles), mode=mode, fr=fr + (tfr if rel is None else []),
                             lens=lens, related=rel, ctx=ctx)
                elif W.bank is not None and W.bank >= amt + f and "debit" in dest.acc:
                    W.take("debit", amt + f)
                    sim.emit(t, "bill_payment", cat, kind, P, H, P, org, method="debit", gross=amt, user=amt + f, fee_type=ft, fee=f, tmin=12,
                             wait=rng.randint(0, 15), miles=miles, mode=mode, fr=fr + tfr, lens=lens, ctx=ctx)
                elif have > 25 and kind in ("rent", "lot_rent", "electric_bill", "gas_bill", "water_bill", "bhph_car_payment", "phone_bill"):
                    part = round(have * rng.uniform(.7, .95), 0)
                    W.take("cash", part)
                    ctx["short"] = "%.2f" % (amt - part)
                    i = sim.emit(t, "bill_payment", cat, kind, P, H, P, org, method="cash", gross=amt, user=part, tmin=14, wait=rng.randint(0, 15),
                                 miles=miles, mode=mode, outcome="partial", fr=fr + tfr + ["insufficient_funds"], lens=lens, ctx=ctx)
                    if sim.carry is not None:
                        bill_missed(sim.carry, sim, H, bi, W, P, i, amt - part, late=(fee[1] if fee else 0.0), how="partial")
                else:
                    ctx["reason"] = "there was not enough cash to cover the bill"
                    i = sim.emit(t, "failed_attempt", cat, kind, P, H, P, org, method="cash", gross=amt, tmin=4, miles=0, mode=mode, outcome="abandoned",
                                 fr=fr + ["insufficient_funds"], lens=lens, ctx=ctx)
                    if sim.carry is not None:
                        bill_missed(sim.carry, sim, H, bi, W, P, i, amt, late=(fee[1] if fee else 0.0))
            push(q, t, run)
        elif method in ("p2p", "check_hand", "cash_hand"):
            t = sim.slot_soft(P, 2, ((600, 1080, 1),))

            def run(t=t, W=W, P=P, kind=kind, cat=cat, org=org, amt=amt, ctx=ctx, method=method, lens=lens):
                m = {"p2p": "p2p_app", "check_hand": "check", "cash_hand": "cash"}[method]
                if W.avail(m) >= amt:
                    W.take(m, amt)
                    sim.emit(t, "bill_payment", cat, kind, P, H, P, org, channel=("app" if m == "p2p_app" else "in_person"), method=m, gross=amt, user=amt,
                             tmin=2, lens=lens, ctx=ctx)
            push(q, t, run)
