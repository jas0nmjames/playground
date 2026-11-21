"""City-level events: person-to-person transfers, life events, civic counters and institutions."""
import math
from .engine import ANY, DAY, EVE, OFFICE, SHOP
from .day_a import push
from .day_b import errand, online, bus_ride
from .day_c import go, pois, rround, hand_pay
from .config import SALES_TAX

MARRIAGE_FEE = (66.0, 56.0)   # the county courthouse and the rural one; an estimate inside the $56-76 v1 drew from

P2P_PURPOSES = [
    ("splitting a dinner or bar tab", .19, (8, 55), "peer"), ("paying a friend back", .12, (10, 120), "peer"),
    ("sending money to family", .16, (25, 400), "family"), ("paying a babysitter", .07, (30, 90), "sitter"),
    ("paying for yard work, cleaning or a small repair", .10, (40, 220), "self"), ("buying a used item from a neighbor", .09, (15, 250), "peer"),
    ("a birthday or graduation gift", .08, (20, 100), "family"), ("a share of rent or utilities", .10, (60, 650), "peer"),
    ("paying a hairdresser or tutor", .05, (25, 90), "self"), ("money for a college student", .04, (20, 150), "student"),
]


def city_events(sim, q):
    p2p(sim, q)
    life_events(sim, q)
    civic(sim, q)
    institutions(sim, q)
    if sim.wx["power_outage"] > 0:
        power_outage(sim)


# ------------------------------------------------------------------------------------------ person to person
def p2p(sim, q):
    rng, X = sim.rng, sim.X
    emit = sim.emit
    adults = [p for p in sim.persons if p.age >= 18 and p.wallet is not None and not p.inpatient and p.hh.gq not in ("jail", "nursing_home")]
    send = [p for p in adults if p.wallet.bank is not None]
    if not send:
        return
    ws = [(2.2 if p.age < 35 else 1.5 if p.age < 50 else .7 if p.age < 65 else .35) * (.4 if p.hh.internet == "no" else 1.0) for p in send]
    selfemp = [p for p in adults if p.emp == "self_employed" and p.occ in ("landscaper", "house cleaner", "general contractor", "hair stylist", "music and tutoring teacher", "home child care provider")] or adults
    young = [p for p in adults if p.age < 26] or adults
    students = [p for p in adults if p.student == "college"] or young
    n = int(len(adults) * .0445)
    apps = [X["x_p2p1"], X["x_p2p2"]]
    senders = rng.choices(send, ws, k=n)
    pw = [x[1] for x in P2P_PURPOSES]
    for s in senders:
        why, _, (lo, hi), who = rng.choices(P2P_PURPOSES, pw)[0]
        H = s.hh
        if who == "sitter" and not any(k.age < 12 for k in H.kids):
            why, (lo, hi), who = "paying a friend back", (10, 120), "peer"
        amt = round(math.exp(rng.uniform(math.log(lo), math.log(hi))), 0 if rng.random() < .7 else 2)
        if who == "self":
            r = rng.choice(selfemp)
        elif who == "sitter":
            r = rng.choice(young)
        elif who == "student":
            r = rng.choice(students)
        elif who == "family" and rng.random() < .4:
            r = None
        else:
            r = rng.choice(adults)
        if r is s or (r is not None and r.hh is H and who != "student"):
            r = None if who == "family" else rng.choice(adults)
            if r is s:
                continue
        t = sim.slot_soft(s, 2, ((420, 540, .7), (690, 800, 1.0), (1020, 1380, 2.2)))
        app = rng.choice(apps)

        def run(t=t, s=s, r=r, amt=amt, why=why, app=app, H=H):
            W = s.wallet
            to = r if r is not None else X["x_outfam"]
            ctx = dict(why=why, amt="%.2f" % amt, org=app.name)
            if W.bank >= amt:
                W.take("p2p_app", amt)
                if r is not None:
                    sim.credit(r.wallet, amt, "bank")
                i = emit(t, "transfer", "money_services", "p2p_transfer", s, H, s, to, ben=r if r is not None else "", channel="app", method="p2p_app", gross=amt, user=amt,
                         tmin=2, lens=(("family_care",) if "family" in why or "student" in why or "babysitter" in why else ()) + (("small_business",) if "yard work" in why or "hairdresser" in why else ()),
                         ctx=ctx)
                # an instant cash-out goes to a bank debit card, so the unbanked can't make one (v2 phase 5: v1 wrote them with
                # the fee in the narrative and none charged)
                if r is not None and rng.random() < .13 and amt >= 20 and r.wallet.bank is not None:
                    fee = round(max(.25, amt * .0175), 2)
                    r.wallet.take("p2p_app", fee)
                    emit(min(1439, t + rng.randint(1, 30)), "transfer", "money_services", "p2p_instant_cash_out", r, r.hh, r, app, channel="app", method="p2p_app", gross=amt,
                         user=fee, fee_type="instant_transfer_fee", fee=fee, tmin=1, related=i,
                         ctx=dict(amt="%.2f" % amt, fee="%.2f" % fee, org=app.name))
            elif W.cc_limit - W.cc_bal >= amt * 1.03 and rng.random() < .35:
                fee = round(amt * .03, 2)
                W.take("credit", amt + fee)
                if r is not None:
                    sim.credit(r.wallet, amt, "bank")
                emit(t, "transfer", "money_services", "p2p_transfer", s, H, s, to, ben=r if r is not None else "", channel="app", method="credit", gross=amt, user=amt + fee,
                     fee_type="credit_card_funding_fee", fee=fee, tmin=2, fr=("insufficient_funds",), ctx=ctx)
            else:
                emit(t, "failed_attempt", "money_services", "p2p_transfer", s, H, s, to, channel="app", method="p2p_app", gross=amt, tmin=2, outcome="declined",
                     fr=("insufficient_funds",), ctx=dict(ctx, reason="the linked account did not have enough to cover it"))
        push(q, t, run)


# ------------------------------------------------------------------------------------------ births, deaths, hospital stays, moves
def life_events(sim, q):
    rng, X, sc = sim.rng, sim.X, sim.scale
    emit = sim.emit
    ev = sim.ev
    hosp = sim.by_kind["hospital"]
    main = hosp[0]
    private = ("employer", "marketplace", "other_private")
    # ---- births
    for p in ev["births"]:
        H = p.hh
        t = rng.randint(10, 1380)
        cov = p.cov
        if cov in ("medicaid", "medicare_medicaid_dual") or (cov == "uninsured" and rng.random() < .75):
            allowed, third, payer, fund, later = 8150.0, 8150.0, "Medicaid (pregnancy and newborn coverage)", "mixed", 0.0
        elif cov in private or cov == "military":
            allowed = round(rng.uniform(13800, 19500), 2)
            later = round(rng.uniform(1400, 4800), 2) if cov != "military" else 0.0
            third, payer, fund = allowed - later, ("TRICARE" if cov == "military" else "Commercial health insurance"), ("federal" if cov == "military" else "private")
        else:
            allowed, third, payer, fund, later = 11200.0, 0.0, "", "", 11200.0
        i = emit(t, "insurance_claim" if third else "purchase", "health", "childbirth_hospital_stay", p, H, main, p, ben=p, method="insurance" if third else "none",
                 gross=allowed, third=third, payer=payer, fund=fund, tmin=1440 - t, miles=round(sim.dist(H.district, main.district), 1), mode="car" if H.vehicles else "ride_from_family_or_friend",
                 outcome="partial" if later else "completed", lens=("health_cost", "family_care"), ctx=dict(org=main.name, later="%.0f" % later))
        par = next((a for a in H.adults if a is not p and a.rel in ("head", "spouse", "unmarried_partner") and not a.inpatient), None)
        if par is not None:
            unpaid = par.works and (par.wsched != "fixed" or par.wage < 45000)
            lost = round(8 * par.wage / 2080.0, 2) if unpaid else 0.0
            emit(t, "non_monetary_job", "care_and_household", "at_hospital_for_a_birth", par, H, par, main, ben=p, gross=lost, tmin=min(600, 1440 - t), miles=round(sim.dist(H.district, main.district), 1),
                 mode="car" if H.vehicles else "ride_from_family_or_friend", fr=("schedule_volatility",) if lost else (), lens=("family_care", "labor"), related=i,
                 ctx=dict(org=main.name, lost="%.2f" % lost))
        emit(min(1439, t + 30), "non_monetary_job", "civic_legal", "birth_registered", p, H, main, sim.one("county"), ben=p, channel="automatic", tmin=10, related=i, ctx=dict())
    # ---- hospital admissions
    for p in ev["admits"]:
        H = p.hh
        t = rng.randint(20, 1300)
        org = hosp[min(len(hosp) - 1, 1)] if (H.district in ("D1", "D2") and rng.random() < .55) else main
        cov = p.cov
        if cov in ("medicare", "medicare_advantage"):
            allowed = round(rng.uniform(11500, 21000), 2)
            later = 0.0 if p.medigap else (1790.0 if cov == "medicare" else float(rng.choice([900, 1400, 1750])))
            third, payer, fund = allowed - later, ("Medicare Part A" if cov == "medicare" else "Medicare Advantage plan"), "federal"
        elif cov == "medicare_medicaid_dual":
            allowed = round(rng.uniform(11500, 21000), 2)
            third, payer, fund, later = allowed, "Medicare Part A and Medicaid", "mixed", 0.0
        elif cov == "medicaid":
            allowed, later = round(rng.uniform(7200, 12500), 2), 0.0
            third, payer, fund = allowed, "Medicaid", "mixed"
        elif cov in private or cov in ("military", "va"):
            allowed = round(rng.uniform(19000, 38000), 2)
            later = round(rng.uniform(1800, 7200), 2) if cov in private else 0.0
            third, payer, fund = allowed - later, ("Commercial health insurance" if cov in private else "TRICARE" if cov == "military" else "VA community care"), ("private" if cov in private else "federal")
        else:
            allowed, third, payer, fund, later = round(rng.uniform(15000, 30000), 2), 0.0, "", "", 0.0
        ctx = dict(org=org.name, later="%.0f" % later, via=rng.choice(["through the emergency department", "through the emergency department", "as a scheduled surgery", "sent over from a clinic visit"]))
        if cov == "uninsured":
            cost = round(allowed * .42, 2)
            i = emit(t, "public_service_encounter", "health", "hospital_admission_uncompensated", p, H, org, p, ben=p, gross=allowed, third=cost,
                     payer="Uncompensated care (hospital charity care, Medicaid disproportionate-share funds)", fund="mixed", imputed=cost, tmin=1440 - t, outcome="partial",
                     lens=("health_cost",), ctx=dict(ctx, later="%.0f" % allowed))
        else:
            i = emit(t, "insurance_claim", "health", "hospital_admission", p, H, org, p, ben=p, method="insurance", gross=allowed, third=third, payer=payer, fund=fund,
                     tmin=1440 - t, outcome="partial" if later else "completed", lens=("health_cost",), ctx=ctx)
        kin = (p.cared_by[0] if p.cared_by else next((a for a in H.adults if a is not p and not a.inpatient), None))
        if kin is not None:
            emit(min(1400, t + rng.randint(20, 120)), "non_monetary_job", "care_and_household", "hospital_bedside_time", kin, kin.hh, kin, org, ben=p, tmin=rng.randint(90, 420),
                 miles=round(sim.dist(kin.hh.district, org.district), 1), mode="car" if kin.hh.vehicles else "ride_from_family_or_friend",
                 fr=("caregiving_conflict",) if kin.works else (), lens=("family_care",), related=i, ctx=dict(org=org.name, rel=p.rel))
    for p in ev["census"]:
        if rng.random() < .40:
            H = p.hh
            kin = (p.cared_by[0] if p.cared_by else next((a for a in H.adults if a is not p and not a.inpatient), None))
            if kin is None or kin.wallet is None:
                continue
            org = main

            def run(t, miles, mode, tfr, w, kin=kin, p=p, org=org):
                i = emit(t, "non_monetary_job", "care_and_household", "hospital_visit_to_relative", kin, kin.hh, kin, org, ben=p, tmin=rng.randint(45, 150), miles=miles, mode=mode,
                         fr=tfr, lens=("family_care",), ctx=dict(org=org.name, rel=p.rel))
                if mode == "car" and rng.random() < .7:
                    sim.pay(t, kin, kin.hh, kin.wallet, None, "transportation", "parking_fee", float(rng.choice([4, 5, 6, 8])), ctx=dict(org=org.name, where="the hospital garage"), tmin=2,
                            to=org, related=i, quiet_fail=1.0)
            go(sim, q, kin, kin.hh, org, 90, ((600, 1200, 1.0),), run)
    # ---- deaths
    fun = sim.by_kind["funeral"]
    cty = sim.one("county")
    for p in ev["deaths"]:
        H = p.hh
        t = rng.randint(5, 1300)
        where = "the nursing home" if H.gq == "nursing_home" else rng.choice(["the hospital", "home under hospice care", "home under hospice care", "the emergency department", "home"])
        if "hospice" in where and p.age >= 60:
            emit(max(0, t - 60), "insurance_claim", "health", "hospice_care_day", p, H, sim.one("hospice"), p, ben=p, method="insurance", gross=232.0, third=232.0,
                 payer="Medicare hospice benefit", fund="federal", tmin=120, lens=("family_care",), ctx=dict(org=sim.one("hospice").name))
        kin = (p.cared_by[0] if p.cared_by else next((a for a in H.adults if a is not p and not a.inpatient), None))
        emit(t, "non_monetary_job", "civic_legal", "death_recorded", kin if kin is not None else None, H if kin is None else kin.hh, cty, cty, ben=p, channel="automatic", tmin=0,
             district=H.district, ctx=dict(where=where, age=p.age))
        if kin is None or kin.wallet is None:
            continue
        org = rng.choice([o for o in fun if o.district == H.district] or fun)
        cremation = rng.random() < .62
        total = round(rng.uniform(1450, 3900) if cremation else rng.uniform(7400, 11800), 2)
        W = kin.wallet
        ins = rng.random() < .30
        t2 = min(1150, max(560, t + rng.randint(90, 400)))

        def run(t=t2, kin=kin, p=p, org=org, total=total, W=W, ins=ins, cremation=cremation):
            ctx = dict(org=org.name, kind="cremation" if cremation else "burial with a service", amt="%.0f" % total, rel=p.rel)
            if ins:
                emit(t, "purchase", "civic_legal", "funeral_arrangements", kin, kin.hh, kin, org, ben=p, method="insurance", gross=total, user=0.0, third=total,
                     payer="Life insurance assignment to the funeral home", fund="private", tmin=rng.randint(75, 150), miles=round(sim.dist(kin.hh.district, org.district) * 2, 1),
                     mode="car" if kin.hh.vehicles else "ride_from_family_or_friend", lens=("family_care",), ctx=ctx)
            else:
                room = W.liquid() + W.cc_bal + max(0, W.cc_limit - W.cc_bal) + W.savings
                dep = total if room >= total else round(max(200.0, min(total * .5, room * .8)), 2)
                if W.savings > 0 and (W.bank or 0) < dep:
                    mv = min(W.savings, dep)
                    W.savings -= mv
                    if W.bank is not None:
                        W.bank += mv
                    else:
                        W.cash += mv
                i, oc, m = sim.pay(t, kin, kin.hh, W, org, "civic_legal", "funeral_arrangements", total, ctx=ctx, tmin=rng.randint(75, 150),
                                   miles=round(sim.dist(kin.hh.district, org.district) * 2, 1), mode="car" if kin.hh.vehicles else "ride_from_family_or_friend",
                                   defer=round(total - dep, 2), ben=p, quiet_fail=0.0, lens=("family_care",))
                if total - dep > 500 and rng.random() < .6:
                    emit(min(1430, t + rng.randint(60, 300)), "non_monetary_job", "giving_faith", "crowdfunding_campaign_started", kin, kin.hh, kin, X["x_crowd"], channel="online",
                         gross=round(total - dep, 2), tmin=rng.randint(20, 50), related=i, fr=("insufficient_funds",), ctx=dict(amt="%.0f" % (total - dep), org=X["x_crowd"].name))
            n = rng.randint(4, 8)
            fee = 25.0 + 10.0 * (n - 1)
            sim.pay(t + 5, kin, kin.hh, W, None, "civic_legal", "death_certificates", fee, ctx=dict(n=n, org=cty.name), tmin=3, to=cty, ben=p, quiet_fail=1.0)
        push(q, t2, run)
    # ---- marriages and divorces
    # NCHS 2024 (sources/raw/nchs_vital): 6.3 marriages and 2.3 divorces per 1,000 people a year, so about 628 and 229
    # for Medianville; licenses and filings happen on the ~249 days the courthouse is open (v1: 1.25 and .66 a weekday).
    court = sim.cal["weekday"] and not sim.cal["holiday"]
    reg = [H for H in sim.households if not H.gq]
    cohab = [H for H in reg if any(m.rel == "unmarried_partner" for m in H.members)]
    married = [H for H in reg if any(m.rel == "spouse" for m in H.members)]
    courts = sim.by_kind["courthouse"]
    for H in rng.sample(cohab, min(len(cohab), rround(rng, 2.41 * sc * (1.0 if court else .1)))):
        P = H.head
        org = courts[0] if H.district != "D5" and H.district != "D6" else courts[-1]
        rng.choice((0, 1, 2, 3))                     # kept so the draws line up; v1 drew the fee here
        fee = MARRIAGE_FEE[0 if org is courts[0] else 1]   # one fee per county courthouse (v2 phase 5: v1 drew $56-76 each time)
        errand(sim, q, P, H, org, "civic_legal", "marriage_license", fee, rng.randint(20, 35), OFFICE, taxable=False, wait=(5, 40), ctx=dict(), quiet_fail=0.0,
               fee=("courthouse_ceremony_fee", 50.0) if rng.random() < .3 else None)
    for H in rng.sample(married, min(len(married), rround(rng, .92 * sc * (1.0 if court else 0)))):
        P = rng.choice([m for m in H.members if m.rel in ("head", "spouse")])
        org = courts[0]
        errand(sim, q, P, H, org, "civic_legal", "divorce_filing_fee", float(rng.choice([232, 268, 295, 310])), rng.randint(20, 40), OFFICE, taxable=False, wait=(5, 45), ctx=dict(),
               quiet_fail=0.0, W=P.wallet)
        if rng.random() < .6 and P.wallet is not None and sim.by_kind.get("law"):
            online(sim, q, P, H, rng.choice(sim.by_kind["law"]), "civic_legal", "attorney_retainer", float(rng.choice([1500, 2500, 3500, 5000])), taxable=False, ctx=dict(), W=P.wallet)
    # ---- moves
    renters = [H for H in reg if H.tenure == "renter" and H.landlord is not None]
    home_c = sim.by_kind["home_center"]
    for H in rng.sample(renters, min(len(renters), rround(rng, 9.0 * sc))):
        P = next((a for a in H.adults if not a.inpatient and a.wallet is not None), None)
        if P is None:
            continue
        W = H.wallets[0]
        ll = H.landlord
        rent = H.housing_cost
        dep = round(rent * rng.choice([.5, 1.0, 1.0, 1.5]), 0)
        org = rng.choice(home_c)
        errand(sim, q, P, H, org, "housing", "moving_truck_rental", round(rng.choice([19.95, 29.95, 39.95]) + rng.uniform(18, 95), 2), rng.randint(20, 35), ((420, 660, 1.0),),
               wait=(5, 30), ctx=dict(), W=W, fee=("damage_waiver_and_mileage", round(rng.uniform(14, 48), 2)), quiet_fail=.5)
        t = sim.slot_soft(P, 15, ((540, 960, 1.0),))

        def run(t=t, P=P, H=H, W=W, ll=ll, rent=rent, dep=dep):
            m = "money_order" if W.bank is None else rng.choice(["ach", "check", "money_order"])
            need = rent + dep
            ctx = dict(org=ll.name, amt="%.0f" % need, dep="%.0f" % dep)
            if W.avail(m) >= need:
                fee = 2.1 if m == "money_order" else 0.0
                W.take(m, need + fee)
                sim.emit(t, "bill_payment", "housing", "move_in_deposit_and_first_rent", P, H, P, ll, channel="in_person" if m != "ach" else "online", method=m, gross=need,
                         user=need + fee, fee_type="money_order_fee" if fee else "", fee=fee, tmin=20, ctx=ctx)
            else:
                have = max(W.avail(m), 0)
                part = round(have * .9, 0)
                if part > 100:
                    W.take(m, part)
                sim.emit(t, "bill_payment" if part > 100 else "failed_attempt", "housing", "move_in_deposit_and_first_rent", P, H, P, ll, method=m, gross=need,
                         user=part if part > 100 else 0.0, tmin=20, outcome="partial" if part > 100 else "abandoned", fr=("insufficient_funds",),
                         ctx=dict(ctx, short="%.0f" % (need - part), reason="the deposit and first month together were more than the account held"))
        push(q, t, run)
        el = next((b for b in H.bills if b[0] == "electric_bill"), None)
        if el is not None and H.alice != "above" and rng.random() < .5:
            online(sim, q, P, H, el[1], "utilities", "utility_connection_deposit", float(rng.choice([100, 150, 200, 250, 300])), taxable=False, ctx=dict(), W=W, channel="phone",
                   dur=(12, 30), rtype="bill_payment", fr=("paperwork",))
        t3 = sim.slot_soft(P, 8, EVE)
        sim.emit(t3, "non_monetary_job", "civic_legal", "change_of_address", P, H, P, sim.by_kind["post_office"][0], channel="online" if H.internet != "no" else "in_person",
                 gross=1.25 if H.internet != "no" else 0.0, user=0.0, tmin=rng.randint(6, 15), ctx=dict())
    for H in rng.sample(renters, min(len(renters), pois(rng, 14.0 * sc))):
        P = next((a for a in H.adults if not a.inpatient and a.wallet is not None), None)
        if P is None:
            continue
        ll = rng.choice(sim.by_kind["landlord"])
        online(sim, q, P, H, ll, "housing", "rental_application_fee", float(rng.choice([35, 45, 50, 60, 75])), taxable=False, ctx=dict(), W=H.wallets[0], dur=(20, 45),
               fr=("paperwork",), lens=("housing",))
    # ---- eviction filings and hearings
    strained = [H for H in renters if H.alice != "above" and not H.subsidized]
    for H in rng.sample(strained, min(len(strained), rround(rng, 4.4 * sc * (1.0 if court else 0)))):
        P = H.head
        ct = courts[0]
        fee = float(rng.choice([95, 110, 135, 160]))
        owed = round(H.housing_cost * rng.uniform(1.0, 2.6), 2)
        i = emit(rng.randint(540, 960), "b2b", "business", "eviction_filing_fee", None, None, H.landlord, ct, district=H.landlord.district, method="check", gross=fee, user=fee, tmin=20,
                 lens=("housing", "small_business"), ctx=dict(org=H.landlord.name, amt="%.0f" % fee))
        emit(rng.randint(960, 1140), "non_monetary_job", "housing", "eviction_notice_received", P, H, ct, P, tmin=rng.randint(5, 20), outcome="partial", fr=("insufficient_funds", "paperwork"),
             lens=("housing",), related=i, ctx=dict(org=H.landlord.name, amt="%.0f" % owed, days=7))
    for H in rng.sample(strained, min(len(strained), pois(rng, 4.0 * sc * (1.0 if court else 0)))):
        P = next((a for a in H.adults if not a.inpatient), None)
        if P is None:
            continue
        ct = courts[0]

        def run(t, miles, mode, tfr, w, P=P, H=H, ct=ct):
            r = rng.random()
            oc, why = ("partial", "a payment plan was signed in the hallway") if r < .5 else (("completed", "the case was dismissed after the back rent was paid") if r < .7 else ("failed", "the judge granted possession to the landlord in seven days"))
            emit(t, "non_monetary_job" if oc != "failed" else "failed_attempt", "housing", "eviction_hearing", P, H, P, ct, tmin=45 + w, wait=w, miles=miles, mode=mode, outcome=oc,
                 fr=tfr + ["paperwork"] + (["schedule_volatility"] if P.works else []), lens=("housing",), ctx=dict(org=ct.name, reason=why))
        if go(sim, q, P, H, ct, 45, ((540, 720, 1.0),), run, wait=(30, 140)) is None:
            emit(600, "failed_attempt", "housing", "eviction_hearing", P, H, P, ct, tmin=0, outcome="failed", fr=("schedule_volatility", "hours_mismatch"), lens=("housing", "labor"),
                 ctx=dict(org=ct.name, reason="the hearing was set for mid-morning on a workday and went ahead without the tenant"))


# ------------------------------------------------------------------------------------------ counters and courts
def civic(sim, q):
    rng, X, sc, cal = sim.rng, sim.X, sim.scale, sim.cal
    emit = sim.emit
    if not cal["weekday"] or cal["holiday"]:   # counters and courts are closed on federal holidays
        return
    adults = [p for p in sim.persons if p.age >= 18 and p.wallet is not None and not p.inpatient and not p.hh.gq]
    if not adults:
        return
    urban = [p for p in adults if p.hh.district in ("D1", "D2", "D3", "D4")]
    rural = [p for p in adults if p.hh.district in ("D5", "D6")]
    lowinc = [p for p in adults if p.hh.alice != "above"] or adults
    dmv = sim.by_kind["dmv"]
    main_dmv = dmv[0]
    docs = ["a certified birth certificate", "two proofs of address", "the Social Security card", "a marriage certificate showing the name change", "proof of insurance"]

    def dmv_visit(P, org, rel=None, extra_fr=()):
        H = P.hh
        what, fee = rng.choice([("driver_license_renewal", 32.0), ("driver_license_renewal", 32.0), ("state_id_card", 12.0), ("real_id_upgrade", 32.0), ("first_driver_license", 42.0), ("title_transfer", 18.0)])
        if what == "first_driver_license" and not (P.age <= 24 or {"immigrant_household", "recent_immigrant_household"} & set(H.notes)):
            what, fee = "driver_license_renewal", 32.0   # a first license goes to the young and the newly arrived (v2 phase 5: v1 gave them at any age)

        def run(t, miles, mode, tfr, w, P=P, org=org, what=what, fee=fee, rel=rel):
            if rng.random() < .14:
                i = emit(t, "failed_attempt", "civic_legal", what, P, H, P, org, gross=fee, tmin=20 + w, wait=w, miles=miles, mode=mode, outcome="rescheduled",
                         fr=tfr + ["missing_document", "repeat_trip"] + list(extra_fr), related=rel, ctx=dict(org=org.name, reason="the clerk needed %s" % rng.choice(docs)))
                sim.bump("dmv_missing_doc")
                return
            sim.pay(t, P, H, P.wallet, org, "civic_legal", what, fee, ctx=dict(org=org.name), tmin=20 + w, wait=w, miles=miles, mode=mode, fr=tuple(tfr) + tuple(extra_fr),
                    related=rel, quiet_fail=0.0, fee=("card_convenience_fee", 1.5) if rng.random() < .5 else None)
        return go(sim, q, P, P.hh, org, 20, OFFICE, run, wait=(15, 115))

    for P in rng.sample(urban, min(len(urban), pois(rng, 52 * sc))):
        dmv_visit(P, main_dmv)
    if rural:
        local = dmv[-1]
        for P in rng.sample(rural, min(len(rural), pois(rng, 6 * sc))):
            if local is main_dmv or local.open is not None:
                dmv_visit(P, local)
            elif rng.random() < .55:
                t = sim.slot(P, 30, ((560, 900, 1.0),))
                if t is None:
                    continue
                i0 = emit(t, "failed_attempt", "civic_legal", "driver_license_renewal", P, P.hh, P, local, tmin=12, miles=round(sim.dist(P.hh.district, local.district) * 2, 1),
                          mode="car" if P.hh.vehicles else "ride_from_family_or_friend", outcome="rescheduled", fr=("hours_mismatch", "repeat_trip"), lens=("rural",),
                          ctx=dict(org=local.name, reason="the local office is open only two days a week and today is not one of them"))
                sim.bump("closed_office")
                if rng.random() < .35:
                    dmv_visit(P, main_dmv, rel=i0, extra_fr=("distance",))
            else:
                dmv_visit(P, main_dmv, extra_fr=("distance",))
    for P in rng.sample(adults, min(len(adults), pois(rng, 30 * sc))):
        if P.hh.internet != "no":
            online(sim, q, P, P.hh, main_dmv, "civic_legal", "driver_license_renewal", 32.0, taxable=False, ctx=dict(online="1"), fee=("online_convenience_fee", 2.0))
    # ---- fines and court dates
    muni = sim.by_kind["courthouse"][min(1, len(sim.by_kind["courthouse"]) - 1)]
    county_ct = sim.by_kind["courthouse"][0]
    for P in rng.sample(lowinc if rng.random() < .6 else adults, min(len(adults), pois(rng, 46 * sc))):
        H = P.hh
        fine = float(rng.choice([85, 110, 135, 165, 190, 240, 310]))
        r = rng.random()
        what = rng.choice(["a speeding ticket", "an expired tag", "a parking ticket that doubled", "no proof of insurance", "a seat belt citation", "a court-cost balance"])
        if r < .5 and H.internet != "no":
            online(sim, q, P, H, muni, "civic_legal", "court_fine_payment", fine, taxable=False, ctx=dict(what=what), fee=("online_payment_fee", round(1.5 + fine * .03, 2)))
        elif r < .8:
            errand(sim, q, P, H, muni, "civic_legal", "court_fine_payment", fine, rng.randint(10, 20), OFFICE, taxable=False, wait=(5, 50), ctx=dict(what=what), allow_partial=False, quiet_fail=0.0)
        else:
            errand(sim, q, P, H, muni, "civic_legal", "court_fine_payment_plan", float(rng.choice([25, 35, 50])), rng.randint(15, 30), OFFICE, taxable=False, wait=(10, 60),
                   ctx=dict(what=what, total="%.0f" % fine), fee=("payment_plan_setup_fee", float(rng.choice([15, 25, 30]))), defer=0.0, quiet_fail=0.0)
    for P in rng.sample(adults, min(len(adults), pois(rng, 58 * sc))):
        H = P.hh
        ct = county_ct if rng.random() < .6 else muni
        matter = rng.choice(["a traffic citation", "a small-claims case", "a child support review", "a custody hearing", "a misdemeanor arraignment", "a probation review", "a debt collection suit", "a name change petition"])

        def run(t, miles, mode, tfr, w, P=P, H=H, ct=ct, matter=matter):
            lost = round(min(4, (45 + w) / 60.0 + 1) * P.wage / 2080.0, 2) if (P.works and P.wsched != "fixed") else 0.0
            emit(t, "non_monetary_job", "civic_legal", "court_appearance", P, H, P, ct, gross=lost, tmin=45 + w, wait=w, miles=miles, mode=mode,
                 outcome=rng.choice(["completed", "completed", "rescheduled"]), fr=tfr + (["schedule_volatility"] if lost else []), ctx=dict(org=ct.name, matter=matter, lost="%.2f" % lost))
        go(sim, q, P, H, ct, 45, ((510, 720, 1.5), (780, 930, 1.0)), run, wait=(20, 160))
    for P in sim.ev.get("jurors", []):
        H = P.hh
        seated, end, lost = sim.jury[P.pid]
        miles = round(sim.dist(H.district, county_ct.district) * 2, 1)
        w = rng.randint(60, 170)
        i = emit(495, "non_monetary_job", "civic_legal", "jury_duty", P, H, P, county_ct, gross=lost, tmin=end - 495 - w, wait=w, miles=miles,
                 mode="car" if H.vehicles else "transit", fr=(("schedule_volatility",) if lost else ()) + (("distance",) if miles >= 40 else ()), lens=("labor",) if lost else (),
                 ctx=dict(org=county_ct.name, seated="1" if seated else "", lost="%.2f" % lost))
        emit(end, "income", "income", "juror_pay", P, H, county_ct, P, method="check", gross=30.0, lens=("public_finance",), related=i, ctx=dict(amt="30"))
    prob = sim.one("probation")
    for P in rng.sample(lowinc, min(len(lowinc), pois(rng, 8 * sc))):
        errand(sim, q, P, P.hh, prob, "civic_legal", "probation_supervision_fee", float(rng.choice([35, 40, 50, 55])), rng.randint(15, 35), OFFICE, taxable=False, wait=(10, 50), ctx=dict(),
               quiet_fail=0.0)
    jail = sim.one("jail")
    for P in rng.sample(lowinc, min(len(lowinc), pois(rng, 2.5 * sc))):
        bond = float(rng.choice([500, 750, 1000, 1500, 2500]))
        errand(sim, q, P, P.hh, jail, "civic_legal", "cash_bond_posted", bond, rng.randint(40, 90), ANY, taxable=False, wait=(20, 120), ctx=dict(), quiet_fail=0.0,
               fee=("kiosk_card_fee", round(bond * .07, 2)))
    # ---- permits and applications
    owners = [p for p in adults if p.hh.tenure != "renter" and p.rel == "head"] or adults
    city = sim.by_kind["city"]
    for P in rng.sample(owners, min(len(owners), pois(rng, 9 * sc))):
        H = P.hh
        org = city[0] if H.district in ("D1", "D2", "D3") else city[min(len(city) - 1, 1 if H.district == "D4" else 2)]
        fee = float(rng.choice([75, 110, 160, 240, 380, 650]))
        what = rng.choice(["a deck", "a fence", "a water heater swap", "a roof replacement", "a garage conversion", "a backyard shed"])
        if rng.random() < .5 and H.internet != "no":
            online(sim, q, P, H, org, "civic_legal", "building_permit", fee, taxable=False, ctx=dict(what=what), fee=("online_convenience_fee", round(fee * .025, 2)), dur=(25, 60), fr=("paperwork",))
        else:
            errand(sim, q, P, H, org, "civic_legal", "building_permit", fee, rng.randint(20, 45), OFFICE, taxable=False, wait=(5, 40), ctx=dict(what=what), fr=("paperwork",), quiet_fail=0.0)
    for P in rng.sample(adults, min(len(adults), pois(rng, 9 * sc))):
        H = P.hh
        org = city[0] if H.district in ("D1", "D2", "D3") else city[min(len(city) - 1, 1 if H.district == "D4" else 2)]
        kind, fee = rng.choice([("pet_license", 15.0), ("pet_license", 25.0), ("yard_sale_permit", 10.0), ("residential_parking_permit", 35.0), ("business_license_renewal", 85.0)])
        if H.internet != "no":
            online(sim, q, P, H, org, "civic_legal", kind, fee, taxable=False, ctx=dict(), fee=("online_convenience_fee", 1.5))
    po = sim.by_kind["post_office"]
    for P in rng.sample(adults, min(len(adults), pois(rng, 5 * sc))):
        H = P.hh
        org = sim.pick(("post_office",), H.district, 8.0) or po[0]

        def run(t, miles, mode, tfr, w, P=P, H=H, org=org):
            if rng.random() < .12:
                emit(t, "failed_attempt", "civic_legal", "passport_application", P, H, P, org, gross=200.0, tmin=15 + w, wait=w, miles=miles, mode=mode, outcome="rescheduled",
                     fr=tfr + ["missing_document", "repeat_trip"], ctx=dict(org=org.name, reason=rng.choice(["the photo was rejected for a shadow", "the birth certificate was a hospital keepsake, not the certified copy", "the appointment required both parents for a child's passport"])))
                return
            sim.pay(t, P, H, P.wallet, org, "civic_legal", "passport_application", 165.0, ctx=dict(org=org.name), tmin=20 + w, wait=w, miles=miles, mode=mode, fr=tfr,
                    fee=("execution_and_photo_fees", 51.95), quiet_fail=0.0, force=("check", "debit", "credit") if P.wallet.bank is not None else None)
        go(sim, q, P, H, org, 20, OFFICE, run, wait=(5, 35))
    imm = [p for p in adults if p.hh.immigrant] or adults
    for P in rng.sample(imm, min(len(imm), pois(rng, 3.2 * sc))):
        H = P.hh
        form, fee = rng.choice([("a naturalization application (N-400)", 710.0), ("a work permit renewal (I-765)", 470.0), ("a green card replacement (I-90)", 415.0),
                                ("a family petition (I-130)", 625.0), ("a work permit renewal (I-765)", 470.0)])
        if rng.random() < .65 and H.internet != "no":
            online(sim, q, P, H, X["x_uscis"], "civic_legal", "immigration_filing_fee", fee, taxable=False, ctx=dict(form=form), dur=(40, 110), fr=("paperwork",) + (("language",) if H.lep else ()))
        else:
            mo = sim.pick(("post_office", "grocery_full", "check_casher"), H.district, 6.0)
            errand(sim, q, P, H, mo, "civic_legal", "immigration_filing_fee", fee, rng.randint(15, 30), SHOP, taxable=False, wait=(0, 15), ctx=dict(form=form, mo="1"),
                   fee=("money_order_and_certified_mail", round(rng.choice([2.1, 2.55]) + 9.65, 2)), fr=("paperwork",) + (("language",) if H.lep else ()), quiet_fail=0.0)
        if rng.random() < .4 and sim.by_kind.get("law"):
            online(sim, q, P, H, rng.choice(sim.by_kind["law"]), "civic_legal", "immigration_attorney_consultation", float(rng.choice([100, 150, 250, 400])), taxable=False, ctx=dict(form=form))


# ------------------------------------------------------------------------------------------ institutions
def institutions(sim, q):
    rng, X, sc = sim.rng, sim.X, sim.scale
    emit = sim.emit
    jail = sim.one("jail")
    shelter = sim.one("shelter")
    adults = [p for p in sim.persons if p.age >= 18 and p.wallet is not None and p.wallet.bank is not None and not p.hh.gq]
    dining = sim.by_kind.get("college_private", [None])[0]
    for H in sim.households:
        g = H.gq
        if not g:
            continue
        p = H.head
        if g == "nursing_home":
            org = sim.by_name.get(H.facility) or sim.one("nursing_home")
            if p.inpatient:
                continue
            if p.cov == "medicare_medicaid_dual":
                emit(1, "insurance_claim", "health", "nursing_home_day", p, H, org, p, ben=p, method="insurance", gross=274.0, third=274.0, payer="Medicaid nursing facility benefit",
                     fund="mixed", tmin=1440, lens=("family_care",), ctx=dict(org=org.name))
            elif rng.random() < .30:
                emit(1, "insurance_claim", "health", "skilled_nursing_rehab_day", p, H, org, p, ben=p, method="insurance", gross=668.0, third=668.0 if rng.random() < .5 else 451.0,
                     payer="Medicare Part A skilled nursing benefit", fund="federal", tmin=1440, ctx=dict(org=org.name))
        elif g == "jail":
            emit(1, "public_service_encounter", "civic_legal", "jail_day", p, H, jail, p, ben=p, gross=124.0, third=124.0, payer="County sheriff's detention budget (county general fund)",
                 fund="local", imputed=124.0, tmin=1440, ctx=dict(org=jail.name))
            if rng.random() < .18:
                amt = round(rng.uniform(6, 44), 2)
                emit(rng.randint(600, 1080), "purchase", "discretionary", "jail_commissary_purchase", p, H, p, jail, method="prepaid", gross=amt, user=amt, tmin=5,
                     fr=("price_spike",) if rng.random() < .3 else (), ctx=dict(org=jail.name, amt="%.2f" % amt))
            if rng.random() < .22:
                mins = rng.randint(6, 15)
                amt = round(mins * .09 + .0, 2)
                emit(rng.randint(540, 1260), "purchase", "utilities", "jail_phone_call", p, H, p, X["x_jailpay"], channel="phone", method="prepaid", gross=amt, user=amt, tmin=mins,
                     ctx=dict(org=X["x_jailpay"].name, mins=mins, amt="%.2f" % amt))
            if rng.random() < .05 and adults:
                fam = rng.choice(adults)
                online(sim, q, fam, fam.hh, X["x_jailpay"], "civic_legal", "jail_account_deposit", float(rng.choice([20, 25, 40, 50, 100])), taxable=False, ctx=dict(),
                       fee=("deposit_service_fee", rng.choice([3.95, 5.95, 7.95, 8.95])), lens=("family_care",))
        elif g == "shelter":
            emit(rng.randint(1110, 1260), "public_service_encounter", "housing", "shelter_night", p, H, shelter, p, ben=p, gross=74.0, third=74.0,
                 payer="Emergency Solutions Grant, city general fund and private donations", fund="mixed", imputed=74.0, tmin=600, wait=rng.randint(10, 60), ctx=dict(org=shelter.name))
            if rng.random() < .12:
                emit(rng.randint(560, 900), "non_monetary_job", "housing", "housing_case_management_meeting", p, H, p, shelter, tmin=rng.randint(25, 60),
                     outcome=rng.choice(["completed", "partial", "rescheduled"]), fr=("paperwork", "missing_document") if rng.random() < .4 else ("paperwork",),
                     ctx=dict(org=shelter.name))
        elif g == "group_home":
            emit(1, "insurance_claim", "health", "group_home_residential_services", p, H, sim.one("community_action") if not sim.by_kind.get("behavioral") else sim.by_kind["behavioral"][0], p,
                 ben=p, method="insurance", gross=251.0, third=251.0, payer="Medicaid home and community-based services waiver", fund="mixed", tmin=1440, lens=("disability",), ctx=dict())
        elif g == "residential_treatment":
            emit(1, "insurance_claim", "health", "residential_treatment_day", p, H, sim.by_kind["behavioral"][0], p, ben=p, method="insurance", gross=322.0, third=322.0,
                 payer="Medicaid and state substance-use block grant", fund="mixed", tmin=1440, ctx=dict())
        elif g == "college_dorm" and dining is not None:
            for tt in ((rng.randint(430, 560), .55), (rng.randint(680, 800), .85), (rng.randint(1050, 1180), .8)):
                if rng.random() < tt[1]:
                    emit(tt[0], "purchase", "food", "dining_hall_meal", p, H, p, dining, method="prepaid", gross=9.85, user=9.85, tmin=rng.randint(15, 40), ctx=dict(org=dining.name))
    # ---- EMS responses that end without a trip to the hospital
    PP = [p for p in sim.persons if not p.inpatient and p.hh.gq != "jail"]
    ws = [(3.5 if p.age >= 75 else 1.6 if p.age >= 60 else 1.0) for p in PP]
    ems = sim.one("ems")
    for p in rng.choices(PP, ws, k=pois(rng, 8 * sc)):
        emit(rng.randint(0, 1430), "public_service_encounter", "health", "ems_response_no_transport", p, p.hh, ems, p, ben=p, channel="phone", gross=448.0, third=448.0,
             payer="County EMS levy", fund="local", imputed=448.0, tmin=rng.randint(20, 45), wait=rng.randint(5, 18),
             ctx=dict(why=rng.choice(["a fall with help getting up", "low blood sugar treated at home", "chest pain that eased; the ride was declined over the cost", "a panic attack", "a child's seizure that had stopped"])))


def power_outage(sim):
    rng = sim.rng
    pr = sim.wx["power_outage"]
    for H in sim.households:
        if H.gq:
            continue
        if rng.random() < pr * (2.5 if H.district in ("D5", "D6") else 1.0):
            P = H.head
            hrs = rng.choice([2, 3, 4, 6, 9, 14])
            el = next((b[1] for b in H.bills if b[0] == "electric_bill"), "")
            sim.emit(rng.randint(240, 900), "failed_attempt", "utilities", "power_outage", P, H, el, P, tmin=hrs * 60, outcome="failed", fr=("outage",),
                     ctx=dict(hrs=hrs, org=el.name if el else "the electric utility"))


def end_of_day(sim):
    """Apply today's card payments to the balances they pay down (posted overnight)."""
    pmap = {p.pid: p for p in sim.persons}
    for r in sim.rows:
        if r[3].endswith(".credit_card_payment") and r[2] == "bill_payment" and r[26] in ("completed", "partial"):
            p = pmap.get(r[5])
            if p is None or p.wallet is None:
                continue
            W = p.wallet
            x = min(W.cc_bal, max(0.0, r[14] - r[21]))
            W.cc_bal -= x
            W.inflow += x
