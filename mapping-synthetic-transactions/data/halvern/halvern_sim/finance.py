"""Household money: wallets (who pays from what) and recurring obligations."""
import math


class Wallet:
    __slots__ = ("wid", "hh", "owners", "bank", "savings", "cash", "cc_limit", "cc_bal", "revolver", "prepaid", "od",
                 "bank_org", "od_fee", "net_m", "start", "inflow", "outflow", "can400", "f", "g", "status", "ncc", "snap_start")

    def liquid(self):
        return (self.bank or 0.0) + self.cash + (self.prepaid or 0.0) - self.cc_bal

    def avail(self, m):
        if m in ("debit", "ach", "check", "p2p_app"):
            return self.bank if self.bank is not None else -1.0
        if m == "credit":
            return (self.cc_limit - self.cc_bal) if self.cc_limit else -1.0
        if m == "prepaid":
            return self.prepaid if self.prepaid is not None else -1.0
        if m in ("cash", "money_order"):
            return self.cash
        return -1.0

    def take(self, m, amt):
        if m in ("debit", "ach", "check", "p2p_app"):
            self.bank -= amt
        elif m == "credit":
            self.cc_bal += amt
        elif m == "prepaid":
            self.prepaid -= amt
        elif m in ("cash", "money_order"):
            self.cash -= amt
        self.outflow += amt

    def give(self, m, amt):
        if m == "savings":
            self.savings += amt
        elif m in ("bank", "ach", "debit", "check", "p2p_app") and self.bank is not None:
            self.bank += amt
        elif m == "prepaid" and self.prepaid is not None:
            self.prepaid += amt
        elif m == "prepaid":
            self.prepaid = amt
        else:
            self.cash += amt
        self.inflow += amt


# bill kind -> (job category, CEX group or None when the payment is debt service or saving)
BILL_CAT = {
    "rent": ("housing", "housing"), "mortgage": ("housing", "housing"), "hoa_dues": ("housing", "housing"),
    "renters_insurance": ("housing", "housing"), "home_insurance": ("housing", "housing"), "storage_unit": ("housing", "housing"),
    "lot_rent": ("housing", "housing"), "security_system": ("housing", "housing"), "cleaning_service": ("housing", "housing"),
    "electric_bill": ("utilities", "housing"), "gas_bill": ("utilities", "housing"), "water_bill": ("utilities", "housing"),
    "trash_bill": ("utilities", "housing"), "internet_bill": ("utilities", "housing"), "phone_bill": ("utilities", "housing"),
    "propane_budget_plan": ("utilities", "housing"),
    "car_payment": ("transportation", "transportation"), "auto_insurance": ("transportation", "transportation"),
    "bhph_car_payment": ("transportation", "transportation"), "toll_account": ("transportation", "transportation"),
    "health_premium": ("health", "healthcare"), "medigap_premium": ("health", "healthcare"), "medical_payment_plan": ("health", "healthcare"),
    "life_insurance": ("money_services", "insurance_pensions"),
    "streaming_subscription": ("discretionary", "entertainment"), "gym_membership": ("discretionary", "entertainment"),
    "other_subscription": ("discretionary", "entertainment"), "boat_payment": ("discretionary", "entertainment"),
    "country_club_bill": ("discretionary", "entertainment"), "pet_insurance": ("discretionary", "entertainment"),
    "child_care_payment": ("children_education", "housing"), "private_school_tuition": ("children_education", "education"),
    "college_payment_plan": ("children_education", "education"), "after_school_fee": ("children_education", "education"),
    "lessons_tuition": ("children_education", "education"),
    "credit_card_payment": ("money_services", None), "student_loan_payment": ("children_education", None),
    "bnpl_installment": ("money_services", None), "rent_to_own_payment": ("money_services", "housing"),
    "personal_loan_payment": ("money_services", None), "investment_contribution": ("discretionary", None),
    "college_savings_contribution": ("children_education", None), "recurring_donation": ("giving_faith", "contributions"),
    "recurring_tithe": ("giving_faith", "contributions"), "nursing_home_private_pay": ("health", "healthcare"),
    "assisted_living_fee": ("housing", "housing"),
}


def bill_method(rng, H, W, kind):
    if kind in ("streaming_subscription", "other_subscription", "gym_membership", "pet_insurance", "bnpl_installment"):
        return "card_auto" if (W.bank is not None or W.cc_limit or W.prepaid is not None) else "none"
    if W.bank is None:
        if W.prepaid is not None and rng.random() < .35:
            return "card_auto"
        return "money_order" if kind in ("rent", "lot_rent", "car_payment", "auto_insurance") and rng.random() < .7 else "in_person"
    old = H.head.age >= 65
    r = rng.random()
    cp = H.head.cashpref
    if r < (.40 if old else .48):
        return "ach_auto"
    if r < (.50 if old else .63) and kind not in ("rent", "mortgage", "car_payment", "student_loan_payment", "credit_card_payment"):
        return "card_auto"
    if r < .86 - (.10 if old else 0) - (.08 if cp > .5 else 0):
        return "online"
    if r < .93 - (.02 if cp > .5 else 0):
        return "check_mail" if (old or rng.random() < .5) else "online"
    if r < .97:
        return "in_person"
    return "phone"


def build_finance(sim):
    rng, by_kind, cal = sim.rng, sim.by_kind, sim.cal
    banks = {"first": by_kind["bank"][0], "corbel": [o for o in by_kind["bank"] if "Corbel" in o.name][0],
             "cu": by_kind["credit_union"][0], "online": by_kind["x_onlinebank"][0]}
    first_branches = [o for o in by_kind["bank"] if "First Halvern" in o.name]
    corbel_branches = [o for o in by_kind["bank"] if "Corbel" in o.name]
    sim.branches = {"first": first_branches, "corbel": corbel_branches, "cu": by_kind["credit_union"]}
    wallets = []
    MU = {"poverty": math.log(.10), "alice": math.log(.20), "above": math.log(.80)}
    SV = {"poverty": math.log(.02), "alice": math.log(.10), "above": math.log(2.2)}
    for H in sim.households:
        joint = [p for p in H.members if p.rel in ("head", "spouse", "unmarried_partner", "resident") or p.age < 18]
        own = [p for p in H.members if p not in joint]
        groups = [joint] + [[p] for p in own]
        for gi, grp in enumerate(groups):
            ad = [p for p in grp if p.age >= 18] or grp[:1]
            W = Wallet()
            W.snap_start, W.ncc = 0.0, 0
            W.wid = "%s-W%d" % (H.hid, gi + 1)
            W.hh, W.owners = H, grp
            wages = sum(p.wage for p in grp)
            ben = sum(12 * (p.ss + p.ssi + p.pension + p.ui + p.va + p.inv) for p in grp)
            if gi == 0:
                ben += 12 * (H.cs + H.tanf)
            t = .10 + (.08 if wages > 60000 else 0) + (.07 if wages > 150000 else 0)
            W.net_m = (wages * (1 - t) + ben) / 12.0
            inc = wages + ben
            st = H.alice if gi == 0 else ("poverty" if inc < 17000 else "alice" if inc < 42000 else "above")
            W.status = st
            banked = H.banked != "unbanked" if gi == 0 else (rng.random() < (.94 if H.banked != "unbanked" else .5))
            if H.gq == "jail":
                banked = False
            W.f = math.exp(rng.gauss(MU[st], 1.05) + .30 * H.z)
            W.g = math.exp(rng.gauss(SV[st], 1.3) + .30 * H.z)
            W.bank = 0.0 if banked else None
            W.savings = 0.0
            a = max(p.age for p in ad)
            cp = max(p.cashpref for p in ad)
            W.cash = round(min(900, 30 * math.exp(rng.gauss(0, .8)) * (1 + 2.2 * cp)), 0)
            if not banked:
                W.cash = round(max(20, W.net_m * W.f * .9 + rng.uniform(10, 120)), 0)
            under = H.banked == "underbanked"
            W.prepaid = None
            if (not banked and rng.random() < .55) or (under and rng.random() < .22):
                W.prepaid = round(max(0, W.net_m * W.f * .5), 2)
            pcc = (.08 if not banked else {"poverty": .45, "alice": .72, "above": .93}[st]) - (.3 if a < 21 else 0)
            if H.gq in ("jail", "nursing_home", "shelter", "group_home", "residential_treatment"):
                pcc = .03
            if rng.random() < pcc:
                W.cc_limit = round(math.exp(rng.gauss(math.log({"poverty": 1400, "alice": 4800, "above": 14000}[st]), .7)) / 100) * 100 + 300
                W.revolver = rng.random() < {"poverty": .62, "alice": .58, "above": .34}[st]
                W.cc_bal = round(W.cc_limit * (rng.uniform(.30, .99) if W.revolver else rng.uniform(0, .22)), 2)
                if W.revolver:            # people carrying card balances hold much less cash (SHED: a third of middle-income adults lack $400 spare)
                    W.f *= .25
                    W.g *= .05
            else:
                W.cc_limit, W.revolver, W.cc_bal = 0.0, False, 0.0
            d = H.district
            if banked:
                if d in ("D5", "D6"):
                    k = rng.choices(["first", "online", "cu", "corbel"], [.6, .2, .1, .1])[0]
                else:
                    k = rng.choices(["first", "corbel", "cu", "online"], [.32, .30, .18, .20 if a < 45 else .08])[0]
                W.bank_org = banks[k]
                W.od_fee = {"first": 28, "corbel": 34, "cu": 25, "online": 0}[k]
                W.od = k != "online" and rng.random() < (.13 if st != "above" else .05)
            else:
                W.bank_org, W.od_fee, W.od = None, 0, False
            if H.gq in ("nursing_home", "assisted_living") and banked and grp[0].cov != "medicare_medicaid_dual":
                W.f, W.g = rng.uniform(4, 9), rng.uniform(8, 40)       # paying privately means there are still assets to spend down
            W.inflow = W.outflow = 0.0
            W.can400 = False
            for p in grp:
                p.wallet = W
            H.wallets.append(W)
            wallets.append(W)

    for W in wallets:
        if W.bank is not None:
            W.bank = round(W.net_m * W.f, 2)
            W.savings = round(W.net_m * W.g, 2)
    sim.wallets = wallets
    build_bills(sim)
    # People who put a bill on autopay mostly keep the money in the account for it; the exceptions become the day's overdrafts and bounces.
    from .day_a import due_today
    ready = {"poverty": .80, "alice": .90, "above": .97}
    for H in sim.households:
        need = {}
        for bl in H.bills:
            if bl[4] in ("ach_auto", "card_auto") and due_today(bl, cal):
                need[id(bl[5])] = need.get(id(bl[5]), 0.0) + bl[2]
        for W in H.wallets:
            due = need.get(id(W), 0.0)
            if due and W.bank is not None and W.bank < due * 1.02 and rng.random() < ready[W.status]:
                target = round(due * rng.uniform(1.03, 1.5) + rng.uniform(0, 40), 2)
                diff = target - W.bank
                W.savings = max(0.0, W.savings - diff)
                W.bank = target

    def spare(W, T):
        liq = (W.bank or 0) + W.savings + W.cash + (W.prepaid or 0)
        return bool(liq >= T or (W.cc_limit and not W.revolver and W.cc_limit - W.cc_bal >= 400))

    def share(T):
        ok = n = 0
        for W in wallets:
            na = sum(1 for p in W.owners if p.age >= 18)
            if na:
                ok += na * spare(W, T)
                n += na
        return ok / max(1, n)
    # SHED anchor: 63% of adults would cover a $400 emergency with cash or its equivalent. Many people with a few hundred dollars
    # on hand still would not, because that money is spoken for; solve the liquid-funds threshold that reproduces the 63%.
    lo, hi = 400.0, 60000.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if share(mid) > .63:
            lo = mid
        else:
            hi = mid
    T = (lo + hi) / 2
    sim.liq_mult = T
    sim.can400_share = share(T)
    for W in wallets:
        W.can400 = spare(W, T)
        W.start = (W.bank, W.cash, W.prepaid, W.cc_bal, W.savings)
    for H in sim.households:
        H.fragile = not H.wallets[0].can400
        if H.fragile:
            H.notes.append("could_not_cover_$400_from_cash_or_equivalent")
        # SNAP balance carried into the day
        if H.snap:
            dsince = cal["dom"] - H.snap_day
            if dsince < 0:
                frac = max(0.0, rng.uniform(-.05, .25))          # end of last month's cycle
            elif dsince == 0:
                frac = 0.0 + max(0.0, rng.uniform(-.1, .1))      # today's issuance not yet loaded
            else:
                frac = max(.15, 1 - .22 * dsince + rng.uniform(-.1, .1))
            H.snap_bal = round(H.snap * frac, 2)
        if H.wic:
            H.wic_bal = round(H.wic * rng.uniform(.2, 1.0), 2)
        H.wallets[0].snap_start = H.snap_bal
    sim.wallets = wallets


def build_bills(sim):
    rng, by_kind, cal = sim.rng, sim.by_kind, sim.cal
    K = by_kind
    one = lambda k: K[k][0]
    dom_today = cal["dom"]
    electric, coop, gasu, trash, propane = one("electric"), one("electric_coop"), one("gas_util"), one("trash"), one("propane")
    water = {"D1": K["water"][0], "D2": K["water"][0], "D3": K["water"][0], "D4": K["water"][1], "D5": K["water"][2]}
    isp_c, isp_p, sat = K["isp"][0], K["isp"][1], one("x_sat")
    streams = [one("x_stream1"), one("x_stream2"), one("x_stream3"), one("x_stream4"), one("x_cloud")]
    gyms = K["gym"] + [o for o in K["after_school"] if "Rec Association" in o.name]
    morts = [one("x_mort1"), one("x_mort2"), by_kind["bank_hq"][0], K["credit_union"][0]]
    autol = [one("x_auto1"), one("x_auto2"), K["credit_union"][0], by_kind["bank_hq"][0]]
    cards = [one("x_cc1"), one("x_cc2")]
    accr = sim.accrual
    nbills = 0
    for H in sim.households:
        W0 = H.wallets[0]
        d, n, st = H.district, len(H.members), H.alice
        B = H.bills

        def add(kind, org, amt, dom=None, method=None, W=None, freq="M", meta=None):
            W = W or W0
            amt = round(amt, 2)
            if dom is None:
                dom = rng.randint(1, 28)
            if method is None:
                method = bill_method(rng, H, W, kind)
            if method == "none":
                return
            B.append((kind, org, amt, dom, method, W, freq, meta))
            g = BILL_CAT[kind][1]
            mult = 4.33 if freq == "W" else 2.17 if freq == "B" else 1.0
            if g:
                accr[g] = accr.get(g, 0.0) + amt * mult / 30.4
            accr["_all_" + kind] = accr.get("_all_" + kind, 0.0) + amt * mult / 30.4

        if H.gq:
            p = H.head
            if H.gq == "college_dorm":
                add("phone_bill", one("x_mobile1"), rng.uniform(25, 55))
                for o in rng.sample(streams, rng.choice([1, 1, 2])):
                    add("streaming_subscription", o, rng.choice([6.99, 9.99, 11.99, 15.49]))
                if rng.random() < .5:
                    add("college_payment_plan", one("x_tuition"), rng.choice([850, 1200, 1650, 2100]), dom=rng.choice([1, 5, 15, 20]), meta=one("college_private"))
            elif H.gq == "assisted_living":
                add("assisted_living_fee", K["assisted_living"][0], rng.uniform(4800, 7200), dom=rng.choice([1, 1, 1, 3, 5]), method=rng.choice(["ach_auto", "check_mail", "online"]))
            elif H.gq == "nursing_home" and p.cov != "medicare_medicaid_dual" and rng.random() < .65:
                add("nursing_home_private_pay", rng.choice(K["nursing_home"]), rng.uniform(8600, 10400), dom=rng.choice([1, 1, 3, 5, 10]), method="check_mail")
            elif H.gq in ("shelter", "group_home", "residential_treatment") and rng.random() < .6:
                add("phone_bill", one("x_mobile3"), rng.choice([25, 30, 35, 40]), method="in_person")
            nbills += len(B)
            continue
        # ---- housing
        if H.tenure == "renter":
            r = rng.random()
            ontime = {"poverty": .42, "alice": .52, "above": .68}[st]
            if any(p.ss_cohort == "3rd" for p in H.members) and rng.random() < .6:
                rd = 3
            elif r < ontime:
                rd = 1
            else:
                rd = rng.choices([2, 3, 4, 5, 6, 8, 10, 15, 20], [.13, .16, .12, .15, .08, .08, .08, .1, .1])[0]
            H.rent_day = rd
            H.late_rent = st != "above" and rng.random() < .035
            add("rent", H.landlord, H.housing_cost, dom=rd)
            if rng.random() < .42:
                add("renters_insurance", one("x_autoins"), rng.uniform(13, 27))
        elif H.mortgage:
            rd = 1 if rng.random() < .55 else rng.randint(2, 15)
            add("mortgage", rng.choice(morts), H.housing_cost, dom=rd, method=("ach_auto" if rng.random() < .62 and W0.bank is not None else None))
        else:
            if H.mobile_home:
                add("lot_rent", H.landlord or rng.choice(K["landlord"]), H.housing_cost, dom=rng.choice([1, 1, 3, 5]))
            elif rng.random() < .45:
                add("home_insurance", one("x_farmins") if d in ("D5", "D6") else one("x_autoins"), rng.uniform(150, 310))
        if H.hoa:
            add("hoa_dues", one("hoa_mgmt"), H.hoa, dom=rng.choice([1, 1, 3, 5, 10, 15]))
        # ---- utilities
        if not H.util_incl:
            e = (70 + 26 * min(n, 5)) * (1.45 if not H.gasheat else 1.0) * (1.1 if d in ("D5", "D6") else 1.0) * math.exp(rng.gauss(0, .22))
            add("electric_bill", coop if d in ("D5", "D6") else electric, e)
            if H.gasheat:
                add("gas_bill", gasu, (48 + 18 * min(n, 5)) * 1.5 * math.exp(rng.gauss(0, .25)))
            elif d in ("D5", "D6") and rng.random() < .5:
                H.flags.add("propane")
                if rng.random() < .4:
                    add("propane_budget_plan", propane, rng.uniform(110, 190))
        if H.tenure != "renter" or (not H.util_incl and rng.random() < .35):
            if d == "D6":
                if rng.random() < .7:
                    add("trash_bill", trash, rng.uniform(30, 38))
            else:
                add("water_bill", water[d], (52 + 14 * min(n, 5)) * math.exp(rng.gauss(0, .2)))
                if d in ("D3", "D4", "D5"):
                    add("trash_bill", trash, rng.uniform(27, 35))
        if H.internet == "yes":
            if d in ("D5", "D6"):
                o = isp_p if (d == "D5" or rng.random() < .45) else sat
                amt = rng.uniform(65, 80) if o is isp_p else rng.uniform(99, 125)
            else:
                o = isp_c
                amt = 30.0 if (st != "above" and rng.random() < .22) else rng.choice([55, 65, 75, 85, 95, 110])
            add("internet_bill", o, amt)
        for W in H.wallets:
            lines = sum(1 for p in W.owners if p.age >= 13) or 1
            prepaidphone = W.bank is None or (W.status != "above" and rng.random() < .5)
            if prepaidphone:
                add("phone_bill", one("x_mobile3"), lines * rng.choice([25, 30, 35, 40, 45]), W=W,
                    method=("in_person" if (W.bank is None or rng.random() < .35) else "card_auto"), meta="prepaid")
            else:
                add("phone_bill", one("x_mobile2") if (d in ("D5", "D6") and rng.random() < .6) else one("x_mobile1"),
                    lines * rng.uniform(36, 52) + rng.uniform(5, 35), W=W)
            a = max(p.age for p in W.owners)
            lam = {"poverty": 1.1, "alice": 1.9, "above": 3.0}[W.status] * (.6 if a >= 70 else 1.0)
            if H.internet == "no":
                lam *= .3
            k = min(5, int(sim.nrg.poisson(lam)))
            for o in rng.sample(streams, k):
                add("streaming_subscription", o, rng.choice([2.99, 7.99, 9.99, 11.99, 15.49, 17.99, 22.99]), W=W)
            if rng.random() < {"poverty": .05, "alice": .12, "above": .22}[W.status] and a < 75:
                g = rng.choice(gyms)
                add("gym_membership", g, rng.choice([10, 15, 24.99, 29.99, 45, 62]), W=W, dom=rng.choice([1, 1, 5, 15, 17, 20, 3]))
            for _ in range(int(sim.nrg.poisson({"poverty": .3, "alice": .7, "above": 1.5}[W.status]))):
                add("other_subscription", rng.choice([one("x_market"), one("x_stream4"), one("x_cloud"), one("newspaper"), one("x_shop4")]),
                    rng.choice([2.99, 4.99, 9.99, 12.99, 14.99, 16.99, 19.99, 39.0]), W=W)
            if W.cc_limit and W.cc_bal > 20:
                if W.revolver:
                    pay = max(35.0, .025 * W.cc_bal) * (1 if rng.random() < .6 else rng.uniform(1.5, 4))
                else:
                    pay = W.cc_bal
                add("credit_card_payment", rng.choice(cards), min(pay, W.cc_bal), W=W, method=("ach_auto" if rng.random() < .55 and W.bank is not None else "online" if W.bank is not None else "in_person"))
            for p in W.owners:
                if p.sloan:
                    add("student_loan_payment", one("x_ed"), p.sloan, W=W, meta=p)
                if p.bnpl:
                    for _ in range(rng.choice([1, 1, 2, 3])):
                        add("bnpl_installment", one(rng.choice(["x_bnpl1", "x_bnpl2"])), rng.choice([11.25, 18.75, 24.5, 32.0, 47.25, 62.5, 89.75]), W=W,
                            dom=(rng.randint(0, 6), rng.randint(0, 1)), freq="B", meta=p)
                if p.cov == "marketplace" and p.age >= 19:
                    add("health_premium", one(rng.choice(["x_ins_a", "x_ins_b"])), max(0, rng.gauss(210 if H.pov_ratio < 2.5 else 520, 140)) + 1,
                        W=W, dom=rng.choice([1, 1, 1, 2, 3, 5, 10, 15, 25]), meta=p)
                if p.cov == "medicare" and p.medigap:
                    add("medigap_premium", one("x_ins_a"), rng.uniform(125, 265), W=W, meta=p)
        # ---- vehicles
        if H.vehicles:
            pins = {"poverty": .76, "alice": .90, "above": .97}[st]
            if rng.random() < pins:
                young = any(16 <= p.age < 25 for p in H.members)
                prem = H.vehicles * rng.uniform(88, 190) * (1.4 if young else 1.0)
                if rng.random() < .78:
                    add("auto_insurance", one("x_farmins") if d in ("D5", "D6") and rng.random() < .5 else one("x_autoins"), prem)
                else:
                    H.flags.add("auto_ins_6mo")
            else:
                H.flags.add("uninsured_driver")
            for v in range(H.vehicles):
                if rng.random() < {"poverty": .25, "alice": .40, "above": .42}[st]:
                    if st == "poverty" and rng.random() < .35 and K.get("bhph_dealer"):
                        add("bhph_car_payment", rng.choice(K["bhph_dealer"]), rng.choice([75, 85, 95, 110]), dom=rng.randint(0, 5), freq="W",
                            method="in_person")
                    else:
                        lo_, hi_ = {"poverty": (280, 480), "alice": (330, 640), "above": (460, 940)}[st]
                        add("car_payment", rng.choice(autol), rng.uniform(lo_, hi_))
            if d == "D3" and rng.random() < .25:
                H.flags.add("toll_user")
        # ---- insurance, children, extras
        if rng.random() < .36:
            add("life_insurance", one("x_life"), rng.choice([18, 24, 31, 42, 58, 75, 96, 140]))
        cc_kids = [p for p in H.members if p.student in ("child_care_center", "family_child_care")]
        if cc_kids:
            wk = 0.0
            for p in cc_kids:
                base = 290 if p.age < 1 else 255 if p.age < 3 else 215
                base *= (.8 if p.student == "family_child_care" else 1.0) * {"D3": 1.1, "D5": .8, "D6": .8}.get(d, 1.0)
                wk += base
            if len(cc_kids) > 1:
                wk *= .93
            provider = rng.choice([o for o in K["child_care"] if o.district == d] or K["child_care"])
            if H.ccdf:
                copay = max(8.0, .07 * H.income / 52.0)
                add("child_care_payment", provider, copay, dom=rng.choice([0, 0, 2, 4, 4]), freq="W", meta=("ccdf", round(wk - copay, 2), cc_kids))
            elif rng.random() < .6:
                add("child_care_payment", provider, wk, dom=rng.choice([0, 0, 2, 4, 4]), freq="W", meta=("full", 0, cc_kids))
            else:
                add("child_care_payment", provider, wk * 4.33, dom=rng.choice([1, 1, 3, 5, 15]), meta=("full", 0, cc_kids))
        for p in H.members:
            if p.student == "private_k12":
                t = 620 if "Anselm" in p.school.name else 860 if "Christian" in p.school.name else 2350 if "Briarwood" in p.school.name else 980
                add("private_school_tuition", one("x_tuition"), t * rng.uniform(.75, 1.0), dom=rng.choice([1, 1, 5, 5, 15, 3]), meta=p)
            elif p.student == "college" and not H.gq and rng.random() < .45:
                add("college_payment_plan", one("x_tuition"), rng.choice([310, 420, 560, 690, 950]), dom=rng.choice([1, 5, 15, 20, 3]),
                    W=p.wallet, meta=one("community_college"))
            elif p.student == "public_k12" and p.age <= 12 and rng.random() < .10 and st == "above":
                add("after_school_fee", rng.choice(K["after_school"]), rng.choice([180, 240, 310, 365]), dom=rng.choice([1, 1, 5, 3]), meta=p)
            if 5 <= p.age <= 15 and rng.random() < ({"poverty": .03, "alice": .08, "above": .22}[st]):
                add("lessons_tuition", rng.choice(K["studio"]), rng.choice([65, 80, 95, 120, 160]), meta=p)
        if rng.random() < .09:
            add("medical_payment_plan", one("x_collect") if rng.random() < .35 else one("hospital"), rng.choice([25, 40, 50, 75, 100, 150]))
        if st != "above" and rng.random() < .028:
            add("rent_to_own_payment", rng.choice(K["rent_to_own"]), rng.choice([21.99, 27.99, 34.99, 44.99]), dom=rng.randint(0, 5), freq="W",
                method=("in_person" if rng.random() < .6 else "card_auto"))
        if st != "above" and rng.random() < .05:
            add("personal_loan_payment", K["credit_union"][0] if rng.random() < .3 else one("x_cc2"), rng.choice([62, 88, 115, 140, 186]))
        if rng.random() < .05:
            add("storage_unit", one("storage"), rng.choice([69, 89, 119, 149, 179]))
        if H.pets and st == "above" and rng.random() < .09:
            add("pet_insurance", one("x_shop4"), rng.choice([28, 39, 47, 62]))
        if st == "above":
            z = H.z
            if rng.random() < .16 + .06 * z:
                add("investment_contribution", one("x_broker"), rng.choice([100, 200, 250, 500, 750, 1000, 1500, 2500]), dom=rng.choice([1, 15, 3, 5, 10, 20, 25]), method="ach_auto" if W0.bank is not None else "none")
            if H.kids and rng.random() < .07 + .04 * z:
                add("college_savings_contribution", one("x_529"), rng.choice([50, 100, 150, 250, 500]), method="ach_auto" if W0.bank is not None else "none")
            if H.tenure != "renter" and rng.random() < .07 + .03 * z:
                add("security_system", sim.X["x_alarm"], rng.choice([29.99, 39.99, 49.99, 59.99]))
            if rng.random() < .055 + .03 * z:
                add("cleaning_service", one("x_customers"), rng.choice([120, 140, 160, 190]), dom=(rng.randint(0, 4), rng.randint(0, 1)), freq="B",
                    method=rng.choice(["p2p", "check_hand", "cash_hand"]))
            if d in ("D3", "D5", "D6") and rng.random() < .028:
                add("boat_payment", rng.choice(autol[1:]), rng.choice([265, 318, 392, 455, 540, 635]))
            if H.income > 190000 and d in ("D3", "D1") and rng.random() < .12:
                add("country_club_bill", one("country_club"), rng.choice([520, 610, 695, 780, 880]) + rng.uniform(40, 420), dom=rng.choice([1, 3, 5, 8, 10]))
        if rng.random() < {"poverty": .04, "alice": .09, "above": .19}[st]:
            add("recurring_donation", rng.choice([one("x_charity"), one("x_charity"), one("food_bank"), rng.choice(K["nonprofit"])]),
                rng.choice([5, 10, 15, 20, 25, 35, 50, 100]), method="card_auto")
        if rng.random() < .055:
            add("recurring_tithe", rng.choice([o for o in K["church"] if o.district == d] or K["church"]), max(20, round(H.income * rng.uniform(.01, .08) / 12, -1)),
                dom=rng.choice([1, 1, 15, 3, 5]), method="ach_auto" if W0.bank is not None else "in_person")
        nbills += len(B)
    sim.n_bills = nbills
