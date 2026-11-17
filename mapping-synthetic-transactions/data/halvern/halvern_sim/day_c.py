"""Household day, part C: school, public services, money services, unpaid work, and things that go wrong."""
import math
from .engine import ANY, DAY, EVE, OFFICE, SHOP, MORN, AFT
from .day_a import push, subtract
from .day_b import errand, online, bus_ride, inc
from .config import SALES_TAX

SCHOOL_COST = [103.6, 97.9, 108.4]          # imputed cost per pupil per school day, by district (see assumptions)
LUNCH_COST, BFAST_COST = 4.95, 2.85
PAY_K12 = "%s general fund (state aid, local property tax, federal Title I and IDEA)"


def pois(rng, lam):
    if lam <= 0:
        return 0
    if lam > 40:
        return max(0, int(round(rng.gauss(lam, lam ** .5))))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def rround(rng, lam):
    """Expected count rounded at random: keeps rare citywide events close to their daily rate."""
    return int(lam) + (1 if rng.random() < lam - int(lam) else 0)


def go(sim, q, P, H, org, dur, prefs, fn, wait=(0, 0), chained=None, after=None, before=None, anchor=None, purpose="errand"):
    """Schedule an in-person visit. fn(t, miles, mode, travel_frictions, wait) runs when its time comes."""
    rng = sim.rng
    if org is None or org.open is None or not P.free:
        return None
    o_d = anchor or H.district
    miles, mode, mins, tfr = sim.trip(P, H, o_d, org.district if org.district != "EXT" else o_d, bool(chained))
    buf = min(mins, 45)
    w = rng.randint(*wait)
    op = max(org.open, after) if after else org.open
    cl = min(org.close, before) if before else org.close
    t = sim.slot(P, dur + w + buf, prefs, op, cl)
    if t is None:
        return None
    t += buf // 2
    if mode == "transit":
        bus_ride(sim, q, P, H, max(0, t - buf // 2 - 4), o_d, org.district, purpose)
    push(q, t, lambda: fn(t, miles, mode, tfr, w))
    return t


def hand_pay(sim, t, P, H, W, to, cat, kind, amt, methods, rtype="purchase", **kw):
    """Pay with the first of `methods` the wallet can cover; quietly skip if none can."""
    for m in methods:
        if W.avail(m) >= amt:
            W.take(m, amt)
            ctx = kw.pop("ctx", {})
            ctx.setdefault("org", to.name if hasattr(to, "name") else "")
            ctx.setdefault("amt", "%.2f" % amt)
            return sim.emit(t, rtype, cat, kind, P, H, P, to, method=m, gross=amt, user=amt, ctx=ctx, **kw)
    return None


def school_district(sim, sch):
    sd = sim.by_kind["school_district"]
    i = 0 if sch.district in ("D1", "D2", "D3") else (1 if sch.district == "D4" else 2)
    i = min(i, len(sd) - 1)
    return sd[i], i


# ------------------------------------------------------------------------------------------ before the day starts
def pre_day(sim):
    """Events that take people out of their ordinary day: births, deaths, hospital stays, a parent home with a sick child."""
    rng, sc = sim.rng, sim.scale
    PP = [p for p in sim.persons if p.hh.gq != "jail"]

    def draw(n, wf):
        out = []
        if n <= 0:
            return out
        ws = [wf(p) for p in PP]
        if sum(ws) <= 0:
            return out
        for p in rng.choices(PP, ws, k=n * 2 + 2):
            if not p.inpatient and p not in out and len(out) < n:
                out.append(p)
                p.inpatient = True
                p.free = []
                p.works, p.shift, p.busy, p.lunch = False, [], [], None
        return out

    def mort(p):
        a = p.age
        m = .00015 if a < 45 else .0009 if a < 55 else .0022 if a < 65 else .0055 if a < 75 else .015 if a < 85 else .05
        return m * (3 if p.hh.gq == "nursing_home" else 1) * (1.6 if p.dis != "none" else 1)

    def adm(p):
        a = p.age
        return (.5 if a < 18 else 1 if a < 45 else 2.2 if a < 65 else 5 if a < 75 else 9) * (1.6 if p.dis != "none" else 1)

    ev = sim.ev = {}
    ev["births"] = draw(rround(rng, 2.93 * sc), lambda p: (1.0 if 25 <= p.age <= 34 else .5) if (p.sex == "F" and 17 <= p.age <= 43 and not p.hh.gq) else 0.0)
    ev["deaths"] = draw(rround(rng, 2.52 * sc), mort)
    ev["admits"] = draw(pois(rng, 24 * sc), adm)
    ev["census"] = draw(pois(rng, 100 * sc), adm)
    if sim.cal["weekday"]:
        pool = [p for p in sim.persons if 18 <= p.age <= 75 and not p.hh.gq and not p.inpatient and p.wallet is not None]
        ev["jurors"] = rng.sample(pool, min(len(pool), pois(rng, 46 * sc)))
        for p in ev["jurors"]:
            seated = rng.random() < .3
            end = 990 if seated else rng.randint(690, 800)
            lost = round((end - 495) / 60.0 * p.wage / 2080.0, 2) if (p.works and (p.wsched != "fixed" or p.wage < 40000)) else 0.0
            p.works, p.shift, p.busy, p.lunch, p.night = False, [], [], None, False
            p.wake, p.bed = 380, 1340
            p.free = ([[720, 765]] if seated else []) + [[end + 35, 1320]]
            sim.jury = getattr(sim, "jury", {})
            sim.jury[p.pid] = (seated, end, lost)
    sim.stayhome = {}
    for H in sim.households:
        sick = [k for k in H.members if k.absent and k.age < 13]
        if not sick:
            continue
        ad = [a for a in H.adults if not a.inpatient and a.age >= 18]
        if not ad or any((not a.works) or a.wfh for a in ad):
            continue
        a = min(ad, key=lambda x: (x.ft, x.wage))
        unpaid = a.wsched != "fixed" or a.wage < 42000 or a.emp == "self_employed"
        hrs = min(10.0, sum(e - s for s, e in a.shift) / 60.0) if a.shift else 8.0
        lost = round(hrs * a.wage / 2080.0, 2) if (unpaid and rng.random() < .7) else 0.0
        sim.stayhome[a.pid] = (sick[0], hrs, lost)
        a.works, a.shift, a.busy, a.lunch, a.night = False, [], [], None, False
        a.wake, a.bed = 400, 1340
        a.free = [[430, 1320]]


# ------------------------------------------------------------------------------------------ school and child care
def gen_school(sim, H, q):
    rng, cal = sim.rng, sim.cal
    if H.gq:
        return
    emit = sim.emit
    for a in H.adults:
        if a.pid in sim.stayhome:
            kid, hrs, lost = sim.stayhome[a.pid]
            if lost:
                emit(450, "failed_attempt", "work", "missed_shift_for_sick_child", a, H, a, a.org if a.org is not None else "", ben=kid, gross=lost, tmin=int(hrs * 60),
                     outcome="failed", fr=("caregiving_conflict", "schedule_volatility"), lens=("family_care", "labor"), ctx=dict(lost="%.2f" % lost, hrs="%.1f" % hrs, age=kid.age))
            else:
                emit(450, "non_monetary_job", "care_and_household", "stayed_home_with_sick_child", a, H, a, "", ben=kid, tmin=int(hrs * 60), fr=("caregiving_conflict",),
                     lens=("family_care",), ctx=dict(age=kid.age))
    if not cal["school_day"]:
        return
    if not sim.wx["school_open"]:
        kids = [p for p in H.members if p.student in ("public_k12", "private_k12") and p.age < 13]
        ad = [a for a in H.adults if a.works and not a.wfh]
        if kids and ad and len(ad) == len([a for a in H.adults if a.age < 70]):
            a = ad[0]
            emit(rng.randint(330, 420), "non_monetary_job", "care_and_household", "school_closure_child_care_scramble", a, H, a, "", ben=kids[0], channel="phone",
                 tmin=rng.randint(15, 50), outcome=rng.choice(["completed", "completed", "abandoned"]), fr=("caregiving_conflict", "schedule_volatility"),
                 lens=("family_care", "labor"), ctx=dict(n=len(kids)))
        return
    d = H.district
    ad = [a for a in H.adults if not a.inpatient]
    car_kids = {}
    paid_kids = 0
    for p in H.members:
        st = p.student
        if st == "public_k12" and p.school is not None:
            sd, i = school_district(sim, p.school)
            cost = SCHOOL_COST[i] * (2.05 if p.dis != "none" else 1.0)
            g = p.grade or 0
            payer = PAY_K12 % sd.name
            if p.absent or p.inpatient:
                why, tag = rng.choices([("home sick", "other"), ("at a medical appointment", "other"), ("without a ride after missing the bus", "no_transit"),
                                        ("needed at home to help with family", "caregiving_conflict"), ("out for a family matter", "other")], [.55, .12, .08, .08, .17])[0]
                emit(470, "public_service_encounter", "children_education", "public_school_day", p, H, sd, p, ben=p, gross=cost, third=0.0, payer=payer, fund="mixed",
                     imputed=cost, outcome="failed", fr=(tag,), ctx=dict(school=p.school.name, grade=g, reason=why))
                continue
            if not p.shift:
                continue
            s, e = p.shift[0]
            pb = {"D1": .36, "D2": .50, "D3": .62, "D4": .50, "D5": .66, "D6": .84}.get(d, .5)
            r = rng.random()
            mode = "school_bus" if r < pb else ("car" if r < pb + (1 - pb) * .70 else "walk")
            if mode == "car" and H.vehicles == 0:
                mode = "walk" if d in ("D1", "D4", "D5") else "school_bus"
            miles = round(sim.dist(d, p.school.district) * rng.uniform(.5, 1.2), 1)
            if mode == "walk":
                miles = round(rng.uniform(.2, 1.1), 1)
            fr = ("distance",) if (mode == "school_bus" and miles > 14) else ()
            emit(s, "public_service_encounter", "children_education", "public_school_day", p, H, sd, p, ben=p, gross=cost, third=cost, payer=payer, fund="mixed",
                 imputed=cost, tmin=e - s, miles=miles, mode=mode, fr=fr, ctx=dict(school=p.school.name, grade=g, sped="1" if p.dis != "none" else "", bus="1" if mode == "school_bus" else ""))
            if mode == "car" and g <= 8:
                car_kids.setdefault(p.school.oid, [p.school, []])[1].append(p)
            # meals
            m = p.meal or "paid"
            sec = g > 5
            pl = {"free": .80, "reduced": .72, "paid": .42}[m]
            pbk = {"free": .42, "reduced": .25, "paid": .09}[m]
            if m == "paid":
                paid_kids += 1
            for (pr, kind, cst, price, tt) in ((pbk, "school_breakfast", BFAST_COST, {"free": 0, "reduced": .30, "paid": 2.10 if sec else 2.00}[m], s - rng.randint(5, 20)),
                                               (pl, "school_lunch", LUNCH_COST, {"free": 0, "reduced": .40, "paid": 3.50 if sec else 3.25}[m], rng.randint(650, 765))):
                if rng.random() >= pr:
                    continue
                if m == "free":
                    emit(tt, "public_service_encounter", "food", kind, p, H, sd, p, ben=p, gross=cst, third=cst, payer="USDA school meal programs (free meal reimbursement)",
                         fund="federal", imputed=cst, tmin=20, ctx=dict(tier="free", school=p.school.name))
                else:
                    debt = rng.random() < (.07 if m == "reduced" else .03)
                    emit(tt, "public_service_encounter", "food", kind, p, H, sd, p, ben=p, method="none" if debt else "prepaid", gross=cst, user=0.0 if debt else price,
                         third=cst - (0.0 if debt else price), payer="USDA school meal programs and district food service fund", fund="mixed", imputed=cst, tmin=20,
                         outcome="partial" if debt else "completed", fr=("insufficient_funds",) if debt else (),
                         ctx=dict(tier=m, price="%.2f" % price, debt="1" if debt else "", school=p.school.name))
        elif st in ("head_start", "public_prek"):
            if rng.random() < .08 or p.inpatient:
                continue
            if st == "head_start":
                org = sim.one("head_start")
                emit(480, "public_service_encounter", "children_education", "head_start_day", p, H, org, p, ben=p, gross=88.0, third=88.0,
                     payer="Head Start (U.S. Department of Health and Human Services grant)", fund="federal", imputed=88.0, tmin=390, ctx=dict(org=org.name))
            else:
                sd = sim.by_kind["school_district"]
                sdo = sd[0] if d in ("D1", "D2", "D3") else sd[min(len(sd) - 1, 1 if d == "D4" else 2)]
                emit(495, "public_service_encounter", "children_education", "public_prek_day", p, H, sdo, p, ben=p, gross=47.5, third=47.5,
                     payer="State pre-kindergarten program (lottery and general funds)", fund="state", imputed=47.5, tmin=390, ctx=dict(org=sdo.name))
    # drop-off and pick-up lines
    for sch, ks in car_kids.values():
        s, e = ks[0].shift[0]
        miles = round(sim.dist(d, sch.district) * rng.uniform(.5, 1.2) * 2, 1)
        for (lo, hi, kind) in ((s - 42, s + 6, "school_dropoff"), (e - 12, e + 48, "school_pickup")):
            done = False
            for a in sorted(ad, key=lambda x: (x.works, x.age)):
                dur = rng.randint(18, 36)
                t = sim.slot(a, dur, ((lo, hi, 1.0),), lo, hi)
                if t is not None:
                    emit(t, "non_monetary_job", "care_and_household", kind, a, H, a, sch, ben=ks[0], tmin=dur, wait=rng.randint(3, 16), miles=miles, mode="car",
                         lens=("family_care",), ctx=dict(n=len(ks), school=sch.name))
                    done = True
                    break
            if not done and kind == "school_pickup" and ad:
                a = ad[0]
                emit(max(300, e - rng.randint(40, 150)), "non_monetary_job", "care_and_household", "pickup_arranged_with_someone_else", a, H, a, sch, ben=ks[0],
                     channel="phone", tmin=rng.randint(4, 12), fr=("caregiving_conflict",), lens=("family_care", "labor"), ctx=dict(n=len(ks), school=sch.name))
    # small school money
    par = [a for a in ad if a.wallet is not None]
    if not par:
        return
    P = rng.choice(par)
    if paid_kids and rng.random() < .035:
        amt = float(rng.choice([20, 25, 30, 40, 50, 60]))
        online(sim, q, P, H, sim.X["x_mealpay"], "children_education", "school_meal_account_reload", amt, taxable=False, ctx=dict(),
               fee=("online_convenience_fee", rng.choice([2.60, 2.75, 3.25])), lens=("family_care",))
    for k in H.kids:
        if k.student not in ("public_k12", "private_k12"):
            continue
        r = rng.random()
        if r < .004:
            amt = float(rng.choice([6, 8, 10, 12, 15, 22]))
            if rng.random() < .5:
                online(sim, q, P, H, sim.X["x_mealpay"], "children_education", "field_trip_fee", amt, taxable=False, ctx=dict(), fee=("online_convenience_fee", 1.95), lens=("education",))
            else:
                t = sim.slot_soft(P, 3, MORN)
                push(q, t, lambda t=t, P=P, amt=amt, k=k: hand_pay(sim, t, P, H, P.wallet, k.school if k.school is not None else "", "children_education", "field_trip_fee", amt,
                                                                     ("cash", "check"), ctx=dict(envelope="1"), tmin=3, ben=k, lens=("education",)))
        elif r < .010 and 5 <= k.age <= 14:
            org = rng.choice(sim.by_kind["youth_sports"])
            fee = float(rng.choice([85, 95, 110, 125, 150, 185]))
            if H.alice != "above" and rng.random() < .30:
                P2 = P
                t = sim.slot_soft(P2, 12, EVE)
                push(q, t, lambda t=t, P2=P2, org=org, fee=fee, k=k: sim.emit(t, "purchase", "children_education", "youth_sports_registration", P2, H, P2, org, ben=k, channel="online",
                                                                               method="none", gross=fee, user=0.0, third=fee, payer="League scholarship fund (donations)", fund="philanthropic",
                                                                               tmin=12, fr=("paperwork",), lens=("family_care",), ctx=dict(org=org.name, waiver="1")))
            else:
                online(sim, q, P, H, org, "children_education", "youth_sports_registration", fee, taxable=False, ctx=dict(), fee=("online_processing_fee", round(fee * .035, 2)),
                       lens=("family_care",))
        elif r < .013 and k.age >= 14:
            online(sim, q, P, H, sim.X["x_mealpay"], "children_education", "school_activity_fee", float(rng.choice([15, 25, 40, 65, 95])), taxable=False, ctx=dict(),
                   fee=("online_convenience_fee", 2.5))
    if H.kids and rng.random() < .011:
        org = sim.pick(("supercenter", "dollar", "pharmacy"), d, 5.0)
        errand(sim, q, P, H, org, "children_education", "school_supplies", round(rng.uniform(5, 38), 2), rng.randint(10, 25), SHOP, ctx=dict(), allow_partial=True)
    for p in H.adults:
        if p.student == "college" and rng.random() < .004 and p.wallet is not None:
            online(sim, q, p, H, sim.X["x_market"], "children_education", "college_textbooks", round(rng.uniform(38, 190), 2), ctx=dict())


# ------------------------------------------------------------------------------------------ public services
LIB_PAYER = "Public library operating budget (city and county property tax, state aid)"


def gen_public(sim, H, q):
    rng, cal = sim.rng, sim.cal
    if H.gq in ("jail", "nursing_home"):
        return
    d = H.district
    ad = [a for a in H.adults if not a.inpatient]
    if not ad:
        return
    emit = sim.emit
    dm = {"D5": .8, "D6": .4}.get(d, 1.0) * sim.wx["trips"]
    for p in H.members:
        if p.inpatient:
            continue
        a = p.age
        # ---- library
        pr = .0050 * dm * (1.4 if 2 <= a <= 12 else 1.5 if a >= 65 else 1.0) * (3.0 if H.internet == "no" else 1.5 if H.internet == "mobile_only" else 1.0)
        pr *= 2.5 if p.emp == "unemployed" else (1.6 if p.student in ("college", "public_k12") and a >= 13 else 1.0)
        if rng.random() < pr:
            actor = p if a >= 13 else rng.choice(ad)
            org = sim.pick(("library",), d, 6.0)
            if org is not None and org.open is not None:
                r = rng.random()
                comp = H.internet != "yes" and r < .55 or r < .10
                story = a <= 5 and r < .5
                kind = "library_computer_session" if comp and a >= 13 else ("library_story_time" if story else "library_visit")
                cost = {"library_visit": 9.6, "library_computer_session": 13.4, "library_story_time": 11.8}[kind]
                dur = rng.randint(35, 80) if kind != "library_visit" else rng.randint(15, 50)
                n_items = rng.choice([0, 1, 2, 2, 3, 4, 6]) if kind != "library_computer_session" else 0
                prints = round(rng.choice([0, 0, .2, .5, 1.0, 1.5]), 2) if kind == "library_computer_session" else 0.0
                purpose = rng.choice(["a job application", "a benefits renewal form", "printing a tax form", "email and bill pay", "homework", "a résumé"]) if comp else ""
                early = org.open >= 700 and rng.random() < .22

                def run(t, miles, mode, tfr, w, p=p, actor=actor, org=org, kind=kind, cost=cost, dur=dur, n_items=n_items, prints=prints, purpose=purpose):
                    W = actor.wallet
                    paid = prints if (prints and W is not None and W.cash >= prints) else 0.0
                    if paid:
                        W.take("cash", paid)
                    emit(t, "public_service_encounter", "public_services", kind, actor, H, org, actor, ben=p, method="cash" if paid else "none", gross=cost + paid, user=paid,
                         third=cost, payer=LIB_PAYER, fund="local", imputed=cost + paid, fee_type="printing_fee" if paid else "", fee=paid, tmin=dur, wait=w, miles=miles,
                         mode=mode, fr=tfr, lens=(("digital_access",) if kind == "library_computer_session" else ()), ctx=dict(org=org.name, items=n_items, purpose=purpose, kid="1" if p is not actor else ""))
                if early and actor.free:
                    # arrives before a late-opening rural branch unlocks its doors
                    t0 = sim.slot(actor, 25, ((540, org.open - 15, 1.0),), 540, org.open - 5)
                    if t0 is not None:
                        i0 = emit(t0, "failed_attempt", "public_services", kind, actor, H, actor, org, ben=p, tmin=10, miles=round(sim.dist(d, org.district) * 2, 1),
                                  mode="car" if H.vehicles else "ride_from_family_or_friend", outcome="rescheduled", fr=("hours_mismatch", "repeat_trip"),
                                  ctx=dict(org=org.name, reason="the branch does not open until %d:%02d" % (org.open // 60, org.open % 60)))
                        if rng.random() < .55:
                            go(sim, q, actor, H, org, dur, AFT, lambda t, miles, mode, tfr, w, i0=i0, run=run: (run(t, miles, mode, tfr, w), sim.rows[-1].__setitem__(29, i0)),
                               wait=(0, 6))
                        continue
                go(sim, q, actor, H, org, dur, ((600, 1140, 1.0),) if a < 13 else ANY, run, wait=(0, 8) if comp else (0, 2))
        # ---- recreation programs
        if 6 <= a <= 14 and rng.random() < .012 * sim.wx["trips"] and d != "D6":
            org = sim.one("parks")
            par = rng.choice(ad)
            t = sim.slot(par, 85, ((1020, 1140, 1.0),), 1010, 1150)
            emit(t if t is not None else rng.randint(1030, 1060), "public_service_encounter", "public_services", "rec_league_practice", par if t is not None else p, H, org, p, ben=p,
                 gross=9.2, third=9.2, payer="Parks and recreation budget (city general fund, league fees)", fund="local", imputed=9.2, tmin=75 if t is not None else 60,
                 miles=round(sim.dist(d, d) * 2, 1), mode="car" if (t is not None and H.vehicles) else "carpool", lens=("family_care",),
                 fr=(() if t is not None else ("caregiving_conflict",)), ctx=dict(carpool="" if t is not None else "1"))
        elif a >= 62 and rng.random() < .0045 and d in ("D1", "D2", "D3", "D4"):
            org = sim.by_kind["after_school"][-1] if rng.random() < .5 else sim.one("parks")
            ma = p.cov == "medicare_advantage"

            def run(t, miles, mode, tfr, w, p=p, org=org, ma=ma):
                fee = 0.0 if ma else 3.0
                if fee and p.wallet.cash >= fee:
                    p.wallet.take("cash", fee)
                elif fee:
                    fee = 0.0
                emit(t, "public_service_encounter", "public_services", "senior_fitness_class", p, H, org, p, ben=p, method="cash" if fee else "none", gross=8.5,
                     user=fee, third=8.5 - fee, payer="Medicare Advantage fitness benefit" if ma else "Parks and recreation budget (city general fund)",
                     fund="federal" if ma else "local", imputed=8.5, tmin=55, miles=miles, mode=mode, fr=tfr, ctx=dict(org=org.name))
            go(sim, q, p, H, org, 55, ((540, 690, 1.0),), run)
        elif 6 <= a <= 14 and H.alice != "above" and d == "D1" and rng.random() < .03:
            org = sim.by_kind["after_school"][0]
            emit(rng.randint(905, 930), "public_service_encounter", "children_education", "after_school_club_day", p, H, org, p, ben=p, gross=23.0, third=23.0,
                 payer="United Fund of Greater Halvern and private donors", fund="philanthropic", imputed=23.0, tmin=180, mode="walk", lens=("family_care",), ctx=dict(org=org.name))
        # ---- public health clinic
        if rng.random() < (.0009 if a < 6 else .0005 if a < 40 else .0003) * (2.2 if p.cov in ("uninsured", "medicaid") else .5):
            org = sim.one("health_dept")
            actor = p if a >= 16 else rng.choice(ad)
            svc = rng.choice(["childhood immunizations", "a flu and COVID shot", "a TB test for work", "family planning", "STI testing"]) if a >= 16 else "childhood immunizations"
            fee = float(rng.choice([0, 0, 0, 10, 21.5, 25])) if p.cov == "uninsured" else 0.0

            def run(t, miles, mode, tfr, w, p=p, actor=actor, org=org, svc=svc, fee=fee):
                W = actor.wallet
                paid = fee if (fee and W is not None) else 0.0
                m = "none"
                if paid:
                    m = "cash" if W.cash >= paid else ("debit" if W.bank is not None and W.bank >= paid else "none")
                    if m == "none":
                        paid = 0.0
                    else:
                        W.take(m, paid)
                payer = "Medicaid" if p.cov in ("medicaid", "medicare_medicaid_dual") else "County health department (state and federal public health grants, Vaccines for Children)"
                emit(t, "public_service_encounter", "health", "public_health_clinic_visit", actor, H, org, actor, ben=p, method=m, gross=118.0, user=paid, third=118.0 - paid,
                     payer=payer, fund="mixed", imputed=118.0, tmin=40 + w, wait=w, miles=miles, mode=mode, fr=tfr + (["language"] if H.lep and rng.random() < .4 else []),
                     ctx=dict(org=org.name, svc=svc))
            go(sim, q, actor, H, org, 40, OFFICE, run, wait=(10, 70))
    P = rng.choice(ad)
    W = P.wallet
    # ---- WIC clinic appointment
    if H.wic and rng.random() < .012:
        org = sim.one("health_dept")
        kid = next((k for k in H.members if k.age < 5), None)

        def run(t, miles, mode, tfr, w):
            miss = rng.random() < .10
            emit(t, "public_service_encounter", "health", "wic_clinic_appointment", P, H, org, P, ben=kid or P, gross=48.0, third=48.0,
                 payer="WIC nutrition services and administration grant (USDA)", fund="federal", imputed=48.0, tmin=45 + w, wait=w, miles=miles, mode=mode,
                 outcome="rescheduled" if miss else "completed", fr=tfr + (["missing_document", "repeat_trip"] if miss else []), lens=("family_care",),
                 ctx=dict(org=org.name, reason="proof of income was missing from the folder" if miss else ""))
        go(sim, q, P, H, org, 45, OFFICE, run, wait=(5, 45))
    # ---- career center
    for p in ad:
        if p.emp == "unemployed" and rng.random() < .02:
            org = sim.one("workforce")
            go(sim, q, p, H, org, rng.randint(40, 90), OFFICE,
               lambda t, miles, mode, tfr, w, p=p, org=org: emit(t, "public_service_encounter", "work", "career_center_visit", p, H, org, p, ben=p, gross=66.0, third=66.0,
                                                                  payer="Workforce Innovation and Opportunity Act funds (federal, via state)", fund="federal", imputed=66.0,
                                                                  tmin=60 + w, wait=w, miles=miles, mode=mode, fr=tfr, lens=("labor",), ctx=dict(org=org.name)),
               wait=(5, 40))
    # ---- free tax help
    if cal["tax_season"] and H.income < 69000 and not H.gq and sim.by_kind.get("vita") and rng.random() < .0036:
        org = sim.pick(("vita",), d, 12.0)
        if org is not None:
            def run(t, miles, mode, tfr, w):
                miss = rng.random() < .13
                emit(t, "public_service_encounter", "money_services", "free_tax_preparation", P, H, org, P, ben=P, gross=245.0, third=245.0,
                     payer="Volunteer Income Tax Assistance (IRS grant, United Fund, volunteer time)", fund="philanthropic", imputed=245.0, tmin=75 + w, wait=w, miles=miles,
                     mode=mode, outcome="rescheduled" if miss else "completed", fr=tfr + (["missing_document", "repeat_trip"] if miss else []),
                     ctx=dict(org=org.name, reason=rng.choice(["a W-2 from a second job had not arrived", "the health insurance form 1095-A was missing", "a child's Social Security card was needed"]) if miss else ""))
            go(sim, q, P, H, org, 75, ANY, run, wait=(15, 90))
    # ---- legal aid and energy assistance
    if H.alice != "above" and rng.random() < .0004:
        org = sim.one("legal_aid")
        go(sim, q, P, H, org, 50, OFFICE,
           lambda t, miles, mode, tfr, w: emit(t, "public_service_encounter", "civic_legal", "legal_aid_consultation", P, H, org, P, ben=P, gross=315.0, third=315.0,
                                               payer="Legal Services Corporation grant and state bar foundation", fund="mixed", imputed=315.0, tmin=50 + w, wait=w, miles=miles,
                                               mode=mode, fr=tfr, ctx=dict(org=org.name, matter=rng.choice(["an eviction notice", "a denied benefits claim", "a debt collection lawsuit", "a custody question", "a wage theft complaint"]))),
           wait=(5, 40))
    if cal["heating"] and (H.liheap or (H.alice == "poverty" and not H.util_incl)) and rng.random() < (.012 if H.liheap else .0012):
        org = sim.one("community_action")
        util = next((b for b in H.bills if b[0] in ("electric_bill", "gas_bill")), None)
        if util is not None:
            def run(t, miles, mode, tfr, w):
                r = rng.random()
                if r < .62:
                    amt = float(rng.choice([250, 300, 350, 400, 500, 600]))
                    i = emit(t, "public_service_encounter", "utilities", "energy_assistance_application", P, H, org, P, ben=P, gross=42.0, third=42.0,
                             payer="Low Income Home Energy Assistance Program (federal block grant)", fund="federal", imputed=42.0, tmin=45 + w, wait=w, miles=miles, mode=mode,
                             fr=tfr + ["paperwork"], ctx=dict(org=org.name))
                    emit(t + 40, "benefit_issuance", "utilities", "energy_assistance_pledge", P, H, org, util[1], ben=P, channel="automatic", method="ach", gross=amt, third=amt,
                         payer="Low Income Home Energy Assistance Program (federal block grant)", fund="federal", related=i, ctx=dict(org=util[1].name, amt="%.0f" % amt))
                else:
                    why, tag = rng.choice([("a pay stub for everyone in the home was required", "missing_document"), ("this season's funds were already committed", "eligibility_confusion"),
                                           ("the shutoff notice had to be in the applicant's name", "paperwork")])
                    emit(t, "public_service_encounter", "utilities", "energy_assistance_application", P, H, org, P, ben=P, gross=42.0, third=42.0,
                         payer="Low Income Home Energy Assistance Program (federal block grant)", fund="federal", imputed=42.0, tmin=45 + w, wait=w, miles=miles, mode=mode,
                         outcome="rescheduled" if tag != "eligibility_confusion" else "failed", fr=tfr + [tag], ctx=dict(org=org.name, reason=why))
            go(sim, q, P, H, org, 45, OFFICE, run, wait=(20, 110))
    # ---- post office counter
    if rng.random() < .0065 * len(ad) and W is not None:
        org = sim.pick(("post_office", "ship_notary"), d, 5.0)
        errand(sim, q, P, H, org, "discretionary", "postage_and_shipping", round(rng.choice([7.3, 14.6, 5.25, 9.85, 11.4, 18.6, 27.5]) * rng.uniform(.9, 1.1), 2), rng.randint(6, 14), OFFICE,
               taxable=False, wait=(0, 14), ctx=dict())
    # ---- Social Security office or phone line
    if any(p.ss or p.ssi or p.age >= 61 for p in ad) and rng.random() < .0011:
        org = sim.one("ssa")
        p = next(p for p in ad if p.ss or p.ssi or p.age >= 61)
        if rng.random() < .35:
            go(sim, q, p, H, org, 35, OFFICE,
               lambda t, miles, mode, tfr, w, p=p: emit(t, "non_monetary_job", "civic_legal", "social_security_office_visit", p, H, p, org, tmin=35 + w, wait=w, miles=miles, mode=mode,
                                                         outcome=rng.choice(["completed", "completed", "rescheduled"]), fr=tfr, ctx=dict(org=org.name, matter=rng.choice(["a replacement card", "a benefit application", "an overpayment letter", "a change of direct deposit", "a Medicare enrollment question"]))),
               wait=(25, 150))
        else:
            hold(sim, p, H, org, "social_security_phone_call", (25, 95), "civic_legal", matter=rng.choice(["an overpayment letter", "a missing payment", "a change of address", "a benefit verification letter"]))


def hold(sim, P, H, org, kind, wr, cat="care_and_household", matter="", drop=.24, lens=(), ben=""):
    """Time on hold with an agency, insurer or company."""
    rng = sim.rng
    w = rng.randint(*wr)
    talk = rng.randint(4, 16)
    r = rng.random()
    oc = "abandoned" if r < drop else ("rescheduled" if r < drop + .14 else "completed")
    t = sim.slot_soft(P, w + talk, ((510, 1000, 1.0),))
    if oc == "abandoned":
        talk = 0
    sim.emit(t, "non_monetary_job" if oc == "completed" else "failed_attempt", cat, kind, P, H, P, org, ben=ben, channel="phone", tmin=w + talk, wait=w, outcome=oc,
             lens=lens, fr=(("language",) if (H.lep and rng.random() < .3) else ()), ctx=dict(org=org.name if hasattr(org, "name") else "", matter=matter,
                                                                                               reason={"abandoned": rng.choice(["the call dropped after the hold", "the hold outlasted the lunch break", "the line said to call back later and hung up"]),
                                                                                                       "rescheduled": rng.choice(["the agent needed a document uploaded first", "the right department was closed for the day", "a callback was promised within two days"]),
                                                                                                       "completed": ""}[oc]))
    return oc


# ------------------------------------------------------------------------------------------ money services
def gen_money(sim, H, q):
    rng, cal, X = sim.rng, sim.cal, sim.X
    if H.gq in ("jail", "nursing_home"):
        return
    d = H.district
    emit = sim.emit
    for W in H.wallets:
        own = [p for p in W.owners if p.age >= 18 and not p.inpatient]
        if not own:
            continue
        P = own[0] if len(own) == 1 else rng.choice(own)
        cp = P.cashpref
        low = W.status != "above" or W.revolver
        # ---- ATM cash
        if W.bank is not None and (rng.random() < .020 + .085 * cp or (W.cash < 12 and cp > .35 and rng.random() < .45)) and P.free:
            amt = float(rng.choice([20, 40, 40, 60, 60, 80, 100, 100, 140, 200, 300]))
            online_bank = "Nimbus" in W.bank_org.name
            oon = rng.random() < (.22 + (.25 if d in ("D5", "D6") else 0) + (.35 if online_bank else 0))
            fee = (rng.choice([3.0, 3.25, 3.5, 4.0]) + (0 if online_bank else rng.choice([2.5, 3.0]))) if oon else 0.0
            host = sim.pick(("gas", "grocery_full", "dollar"), d, 3.0) if oon else W.bank_org
            t = sim.slot(P, 6, ANY)
            if t is None:
                continue

            def run(t=t, P=P, W=W, amt=amt, fee=fee, host=host, oon=oon):
                rel = None
                f = fee
                if not oon and rng.random() < .016:
                    rel = emit(t, "failed_attempt", "money_services", "atm_withdrawal", P, H, P, W.bank_org, method="debit", gross=amt, tmin=4, outcome="failed",
                               fr=("outage",), ctx=dict(org=W.bank_org.name, reason="the machine was out of service", amt="%.0f" % amt))
                    f = rng.choice([3.0, 3.5]) + 2.5
                    t += rng.randint(6, 18)
                if W.bank >= amt + f:
                    W.take("debit", amt + f)
                    W.cash += amt
                    W.inflow += amt
                    emit(t, "transfer", "money_services", "atm_withdrawal", P, H, P, host if (oon or rel is not None) and host is not None else W.bank_org, method="debit",
                         gross=amt, user=f, fee_type="out_of_network_atm_fees" if f else "", fee=f, tmin=4, miles=round(rng.uniform(.2, 2.5), 1),
                         mode="car" if H.vehicles else "walk", related=rel, ctx=dict(org=(host.name if host is not None and f else W.bank_org.name), amt="%.0f" % amt))
                else:
                    emit(t, "failed_attempt", "money_services", "atm_withdrawal", P, H, P, W.bank_org, method="debit", gross=amt, tmin=3, outcome="declined",
                         fr=("insufficient_funds",), related=rel, ctx=dict(org=W.bank_org.name, reason="the balance was below the amount requested", amt="%.0f" % amt))
            push(q, t, run)
        # ---- moving money from savings when checking runs low
        if W.bank is not None and W.savings > 300 and W.bank < 150 and rng.random() < .30:
            amt = float(min(W.savings, rng.choice([100, 200, 300, 500])))
            t = sim.slot_soft(P, 3, ((400, 600, 1.0),))

            def run(t=t, P=P, W=W, amt=amt):
                W.savings -= amt
                W.bank += amt
                emit(t, "transfer", "money_services", "transfer_from_savings", P, H, P, W.bank_org, channel="app", method="ach", gross=amt, tmin=3,
                     ctx=dict(org=W.bank_org.name, amt="%.0f" % amt))
            push(q, t, run)
        elif W.bank is not None and W.status == "above" and W.bank > 3000 and rng.random() < .008:
            amt = float(rng.choice([100, 200, 250, 500, 1000]))
            t = sim.slot_soft(P, 3, EVE)

            def run(t=t, P=P, W=W, amt=amt):
                if W.bank > amt + 500:
                    W.bank -= amt
                    W.savings += amt
                    emit(t, "transfer", "money_services", "transfer_to_savings", P, H, P, W.bank_org, channel="app", method="ach", gross=amt, tmin=3,
                         ctx=dict(org=W.bank_org.name, amt="%.0f" % amt))
            push(q, t, run)
        # ---- prepaid cards
        if W.prepaid is not None and W.bank is None:
            if W.cash > 150 and W.prepaid < 45 and rng.random() < .25:
                amt = float(rng.choice([50, 100, 100, 150, 200, 300]))
                amt = min(amt, W.cash - 20)
                fee = rng.choice([3.95, 4.95, 5.95])
                org = sim.pick(("dollar", "pharmacy", "supercenter", "gas"), d, 4.0)

                def run(t, miles, mode, tfr, w, P=P, W=W, amt=amt, fee=fee, org=org):
                    if W.cash >= amt + fee:
                        W.take("cash", amt + fee)
                        W.give("prepaid", amt)
                        emit(t, "transfer", "money_services", "prepaid_card_cash_reload", P, H, P, org, method="cash", gross=amt, user=fee, fee_type="reload_fee", fee=fee,
                             tmin=8 + w, wait=w, miles=miles, mode=mode, fr=tfr, ctx=dict(org=org.name, amt="%.0f" % amt, fee="%.2f" % fee))
                go(sim, q, P, H, org, 8, SHOP, run, wait=(0, 10), chained=True)
            if rng.random() < 1 / 30.0 and W.prepaid > 12:
                fee = rng.choice([5.95, 7.95, 9.95])
                W.take("prepaid", fee)
                emit(rng.randint(60, 300), "bill_payment", "money_services", "prepaid_card_monthly_fee", P, H, P, X["x_prepaid"], channel="automatic", method="prepaid",
                     gross=fee, user=fee, fee_type="monthly_card_fee", fee=fee, ctx=dict(org=X["x_prepaid"].name))
        # ---- account and card charges
        if W.bank is not None and W.bank < 500 and W.od_fee and rng.random() < .45 / 30.0:
            fee = float(rng.choice([8, 10, 12, 12, 15]))
            t = rng.randint(30, 240)
            push(q, t, lambda t=t, P=P, W=W, fee=fee: (W.take("debit", fee), emit(t, "bill_payment", "money_services", "bank_monthly_maintenance_fee", P, H, P, W.bank_org,
                                                                                    channel="automatic", method="debit", gross=fee, user=fee, fee_type="monthly_maintenance_fee",
                                                                                    fee=fee, ctx=dict(org=W.bank_org.name))))
        if W.revolver and W.cc_bal > 50:
            if rng.random() < 1 / 30.4:
                apr = rng.choice([.2099, .2299, .2449, .2699, .2899, .2999])
                intr = round(W.cc_bal * apr / 12.0, 2)
                W.take("credit", intr)
                emit(rng.randint(10, 200), "bill_payment", "money_services", "credit_card_interest_charge", P, H, P, X["x_cc1"], channel="automatic", method="credit",
                     gross=intr, user=intr, fee_type="interest_charge", fee=intr, ctx=dict(amt="%.2f" % intr, apr="%.2f" % (apr * 100), bal="%.0f" % W.cc_bal))
            if rng.random() < .0022:
                fee = float(rng.choice([30, 32, 38, 41]))
                W.take("credit", fee)
                emit(rng.randint(10, 200), "bill_payment", "money_services", "credit_card_late_fee", P, H, P, X["x_cc2"], channel="automatic", method="credit", gross=fee,
                     user=fee, fee_type="late_fee", fee=fee, ctx=dict(amt="%.0f" % fee))
        earner = any(p.wage > 0 for p in own)
        # ---- small-dollar credit
        if low and earner and W.bank is not None:
            r = rng.random()
            if r < .00085:
                amt = float(rng.choice([200, 255, 300, 300, 350, 400, 500]))
                fee = round(amt * rng.choice([.15, .15, .175]), 2)
                if rng.random() < .58 and sim.by_kind.get("payday"):
                    org = sim.pick(("payday",), d, 8.0)

                    def run(t, miles, mode, tfr, w, P=P, W=W, amt=amt, fee=fee, org=org):
                        W.give("cash", amt)
                        emit(t, "transfer", "money_services", "payday_loan_disbursed", P, H, org, P, method="cash", gross=amt, fee_type="payday_finance_charge_due_at_payback",
                             fee=fee, tmin=25 + w, wait=w, miles=miles, mode=mode, fr=tfr, ctx=dict(org=org.name, amt="%.0f" % amt, fee="%.2f" % fee, due="%.2f" % (amt + fee)))
                    go(sim, q, P, H, org, 25, SHOP, run, wait=(0, 15))
                else:
                    t = sim.slot_soft(P, 14, EVE)
                    push(q, t, lambda t=t, P=P, W=W, amt=amt, fee=fee: (W.give("bank", amt), emit(t, "transfer", "money_services", "online_installment_loan_disbursed", P, H, X["x_cc2"], P,
                                                                                                       channel="online", method="ach", gross=amt, fee_type="finance_charge_due_at_payback",
                                                                                                       fee=round(fee * 1.6, 2), tmin=14, ctx=dict(amt="%.0f" % amt, fee="%.2f" % (fee * 1.6)))))
            elif r < .0017:
                due = float(rng.choice([230, 293.25, 345, 402.5, 460, 575]))
                feeonly = round(due - due / 1.15, 2)
                org = sim.pick(("payday",), d, 8.0)
                if org is not None:
                    t = rng.randint(200, 420)

                    def run(t=t, P=P, W=W, due=due, feeonly=feeonly, org=org):
                        if W.bank >= due:
                            W.take("ach", due)
                            emit(t, "bill_payment", "money_services", "payday_loan_repayment", P, H, P, org, channel="automatic", method="ach", gross=due, user=due,
                                 fee_type="payday_finance_charge", fee=feeonly, ctx=dict(org=org.name, amt="%.2f" % due, fee="%.2f" % feeonly))
                        elif W.bank >= feeonly or W.cash >= feeonly:
                            m = "ach" if W.bank >= feeonly else "cash"
                            W.take(m, feeonly)
                            emit(t if m == "ach" else rng.randint(600, 1000), "bill_payment", "money_services", "payday_loan_rollover", P, H, P, org,
                                 channel="automatic" if m == "ach" else "in_person", method=m, gross=due, user=feeonly, fee_type="rollover_fee", fee=feeonly, outcome="partial",
                                 fr=("insufficient_funds",), ctx=dict(org=org.name, amt="%.2f" % due, fee="%.2f" % feeonly))
                        else:
                            nsf = float(rng.choice([25, 30, 35]))
                            emit(t, "failed_attempt", "money_services", "payday_loan_repayment", P, H, P, org, channel="automatic", method="ach", gross=due,
                                 fee_type="returned_payment_fee", fee=nsf, outcome="failed", fr=("insufficient_funds",),
                                 ctx=dict(org=org.name, amt="%.2f" % due, reason="the lender's debit bounced"))
                    push(q, t, run)
            elif r < .0057 and any(p.wsched != "fixed" or p.wage < 45000 for p in own):
                amt = float(rng.choice([40, 50, 60, 75, 100, 150]))
                fee = rng.choice([2.99, 3.49, 4.99, 5.99])
                t = sim.slot_soft(P, 4, ANY)
                push(q, t, lambda t=t, P=P, W=W, amt=amt, fee=fee: (W.give("bank", amt - fee), emit(t, "transfer", "money_services", "earned_wage_advance", P, H, X["x_ewa"], P, channel="app",
                                                                                                        method="ach", gross=amt, user=fee, fee_type="instant_transfer_fee", fee=fee,
                                                                                                        tmin=4, lens=("labor",), ctx=dict(amt="%.0f" % amt, fee="%.2f" % fee))))
        if low and H.vehicles and rng.random() < .00013 and sim.by_kind.get("title_loan"):
            org = sim.pick(("title_loan",), d, 12.0)
            amt = float(rng.choice([400, 600, 800, 1000, 1500]))
            go(sim, q, P, H, org, 40, SHOP,
               lambda t, miles, mode, tfr, w, P=P, W=W, amt=amt, org=org: (W.give("cash", amt), emit(t, "transfer", "money_services", "title_loan_disbursed", P, H, org, P, method="cash",
                                                                                                      gross=amt, fee_type="monthly_finance_charge", fee=round(amt * .25, 2), tmin=40 + w,
                                                                                                      wait=w, miles=miles, mode=mode, fr=tfr, ctx=dict(org=org.name, amt="%.0f" % amt, fee="%.0f" % (amt * .25)))),
               wait=(0, 20))
        if W.status != "above" and rng.random() < .0011:
            org = sim.pick(("pawn",), d, 8.0)
            r = rng.random()
            item = rng.choice(["a cordless drill set", "a game console", "a gold chain", "a guitar", "a television", "a wedding band", "a laptop", "a chainsaw"])
            if r < .45:
                amt = float(rng.choice([35, 50, 60, 80, 100, 150, 220]))
                go(sim, q, P, H, org, 20, SHOP,
                   lambda t, miles, mode, tfr, w, P=P, W=W, amt=amt, org=org, item=item: (W.give("cash", amt), emit(t, "transfer", "money_services", "pawn_loan", P, H, org, P, method="cash",
                                                                                                                 gross=amt, fee_type="monthly_pawn_charge", fee=round(amt * .22, 2), tmin=20 + w,
                                                                                                                 wait=w, miles=miles, mode=mode, fr=tfr, ctx=dict(org=org.name, amt="%.0f" % amt, item=item))),
                   wait=(0, 12))
            elif r < .72:
                amt = float(rng.choice([20, 35, 50, 75, 120, 180]))
                go(sim, q, P, H, org, 15, SHOP,
                   lambda t, miles, mode, tfr, w, P=P, W=W, amt=amt, org=org, item=item: (W.give("cash", amt), emit(t, "income", "income", "sold_item_to_pawn_shop", P, H, org, P, method="cash",
                                                                                                                 gross=amt, tmin=15 + w, wait=w, miles=miles, mode=mode, fr=tfr,
                                                                                                                 ctx=dict(org=org.name, amt="%.0f" % amt, item=item))),
                   wait=(0, 12))
            else:
                amt = float(rng.choice([61, 97.6, 122, 183]))
                errand(sim, q, P, H, org, "money_services", "pawn_redemption", amt, 15, SHOP, taxable=False, ctx=dict(item=item), W=W, rtype="bill_payment", quiet_fail=0.0)
        # ---- remittances
        if H.immigrant and earner and rng.random() < (.030 if H.recent else .017):
            amt = float(rng.choice([80, 100, 100, 150, 200, 200, 250, 300, 400]))
            if W.bank is not None and H.internet != "no" and rng.random() < .45:
                fee = rng.choice([1.99, 2.99, 3.99, 4.99])
                online(sim, q, P, H, X["x_remit"], "money_services", "remittance_sent", amt, taxable=False, ctx=dict(), fee=("transfer_fee", fee), W=W, rtype="transfer", channel="app",
                       lens=("family_care",))
            else:
                fee = rng.choice([4.0, 5.0, 6.99, 8.0, 9.99])
                tax = round(amt * .01, 2)
                org = sim.pick(("grocery_indep", "check_casher", "supercenter"), d, 5.0)
                errand(sim, q, P, H, org, "money_services", "remittance_sent", amt, rng.randint(10, 20), SHOP, taxable=False, wait=(0, 15), ctx=dict(extax="%.2f" % tax), W=W,
                       rtype="transfer", fee=("transfer_fee+remittance_excise_tax", round(fee + tax, 2)), lens=("family_care",), quiet_fail=.5)
        elif H.immigrant and rng.random() < .0012:
            amt = float(rng.choice([100, 200, 300, 500]))
            t = sim.slot_soft(P, 5, DAY)
            push(q, t, lambda t=t, P=P, W=W, amt=amt: (sim.credit(W, amt, "bank"), emit(t, "transfer", "income", "remittance_received", P, H, X["x_abroad"], P, channel="app",
                                                                                         method="ach" if W.bank is not None else "cash", gross=amt, tmin=5, ctx=dict(amt="%.0f" % amt))))
        # ---- plasma
        if W.status != "above" and 18 <= P.age <= 50 and d in ("D1", "D2", "D4") and sim.by_kind.get("plasma") and rng.random() < .0052:
            org = sim.one("plasma")
            amt = float(rng.choice([40, 45, 50, 60, 70, 100]))
            go(sim, q, P, H, org, 85, ANY,
               lambda t, miles, mode, tfr, w, P=P, W=W, amt=amt, org=org: (W.give("prepaid", amt), emit(t, "income", "income", "plasma_donation_payment", P, H, org, P, method="prepaid",
                                                                                                         gross=amt, tmin=85 + w, wait=w, miles=miles, mode=mode, fr=tfr,
                                                                                                         ctx=dict(org=org.name, amt="%.0f" % amt))),
               wait=(10, 60))
    # ---- household-level: TANF cash withdrawal, tax preparation, tax payments
    W0, head = H.wallets[0], H.head
    if H.tanf and H.tanf_day == cal["dom"]:
        amt = float(int(H.tanf * rng.choice([.5, .75, 1.0, 1.0]) / 20) * 20)
        fee = rng.choice([0.0, 0.85, 2.5, 3.0, 3.5])
        t = sim.slot(head, 6, ((480, 900, 1.0),)) if not head.inpatient else None
        if t is not None and amt > 0:
            def run(t=t, amt=amt, fee=fee):
                W0.give("cash", amt - fee)
                rest = H.tanf - amt
                if rest > 0:
                    W0.give("prepaid", rest)
                emit(t, "benefit_redemption", "money_services", "ebt_cash_withdrawal", head, H, head, X["x_snap"], method="ebt_cash", gross=amt, user=fee, third=amt,
                     payer="TANF cash assistance", fund="mixed", fee_type="atm_surcharge" if fee else "", fee=fee, tmin=5, related=sim.tanf_idx.get(H.hid),
                     ctx=dict(amt="%.0f" % amt))
            push(q, t, run)
        else:
            push(q, 400, lambda: W0.give("prepaid", H.tanf))
    if cal["tax_season"] and not H.gq and any(p.wage > 0 or p.pension or p.inv for p in H.adults):
        r = rng.random()
        P = rng.choice([p for p in H.adults if not p.inpatient] or [head])
        if r < .0042 and sim.by_kind.get("tax_prep"):
            org = sim.pick(("tax_prep", "accounting"), d, 8.0)
            fee = round(rng.uniform(170, 430) if org.kind == "tax_prep" else rng.uniform(320, 780), 2)
            if H.alice != "above" and rng.random() < .45:
                def run(t, miles, mode, tfr, w, P=P, org=org, fee=fee):
                    rt = float(rng.choice([39.95, 49.95, 59.95]))
                    emit(t, "purchase", "money_services", "paid_tax_preparation", P, H, P, org, method="none", gross=fee + rt, user=0.0, fee_type="refund_transfer_fee", fee=rt,
                         tmin=70 + w, wait=w, miles=miles, mode=mode, outcome="partial", fr=tfr, ctx=dict(org=org.name, amt="%.2f" % fee, rt="%.2f" % rt, deduct="1"))
                go(sim, q, P, H, org, 70, ANY, run, wait=(5, 70))
            else:
                errand(sim, q, P, H, org, "money_services", "paid_tax_preparation", fee, rng.randint(55, 90), ANY, taxable=False, wait=(5, 60), ctx=dict(), W=W0, quiet_fail=0.0)
        elif r < .0084 and H.internet != "no":
            fed = float(rng.choice([0, 0, 0, 39, 59, 69, 89, 119]))
            st = float(rng.choice([0, 39, 49, 59, 64]))
            if fed + st > 0:
                online(sim, q, P, H, X["x_taxsoft"], "money_services", "tax_software_filing", fed + st, taxable=False, ctx=dict(), dur=(70, 160), W=W0, prefs=EVE,
                       fr=(("price_spike",) if fed >= 89 else ()))
            else:
                t = sim.slot_soft(P, 90, EVE)
                emit(t, "non_monetary_job", "money_services", "tax_return_filed_free", P, H, P, X["x_irs"], channel="online", tmin=rng.randint(60, 150),
                     fr=(("digital_barrier",) if H.internet == "mobile_only" else ()), ctx=dict())
        elif r < .0088 and H.alice == "above" and W0.bank is not None:
            amt = round(rng.uniform(250, 4600), 2)
            t = sim.slot_soft(P, 8, EVE)
            push(q, t, lambda t=t, P=P, amt=amt: (W0.take("ach", amt), emit(t, "tax", "money_services", "federal_tax_balance_due_payment", P, H, P, X["x_irs"], channel="online",
                                                                              method="ach", gross=amt, user=amt, tmin=8, ctx=dict(amt="%.2f" % amt))) if W0.bank >= amt else None)
    # ---- property tax paid directly
    if H.tenure in ("owner_free_and_clear",) or (H.mortgage and not H.escrow):
        if not H.mobile_home and rng.random() < (.0045 if cal["month"] in (3, 9) else .0008) and W0.bank is not None:
            amt = round(max(380, H.housing_cost * rng.uniform(1.6, 3.4) if H.tenure == "owner_free_and_clear" else H.housing_cost * rng.uniform(.9, 1.6)), 2)
            P = head
            cty = sim.pick(("county",), d, 14.0) or sim.by_kind["county"][0]
            r = rng.random()
            if r < .5 and H.internet != "no":
                fee = 1.0 if rng.random() < .6 else round(amt * .0235, 2)
                online(sim, q, P, H, cty, "housing", "property_tax_payment", amt, taxable=False, ctx=dict(), fee=("online_payment_fee", fee), W=W0, rtype="tax", lens=("public_finance",))
            elif r < .8:
                t = sim.slot_soft(P, 6, DAY)
                push(q, t, lambda t=t, P=P, amt=amt, cty=cty: (W0.take("check", amt + .78), emit(t, "tax", "housing", "property_tax_payment", P, H, P, cty, channel="mail", method="check",
                                                                                                    gross=amt, user=amt + .78, fee_type="postage", fee=.78, tmin=6,
                                                                                                    ctx=dict(org=cty.name, amt="%.2f" % amt))) if W0.bank >= amt + 1 else None)
            else:
                errand(sim, q, P, H, cty, "housing", "property_tax_payment", amt, 12, OFFICE, taxable=False, wait=(3, 45), ctx=dict(), W=W0, rtype="tax", quiet_fail=0.0,
                       lens=("public_finance",))


# ------------------------------------------------------------------------------------------ unpaid work and admin
def gen_care(sim, H, q):
    rng, cal, X = sim.rng, sim.cal, sim.X
    if H.gq in ("jail", "nursing_home", "assisted_living"):
        return
    d = H.district
    emit = sim.emit
    out = sim.cfg["BENEFITS_PORTAL_OUTAGE"]
    for p in H.members:
        if p.age < 16 or p.inpatient:
            continue
        a = p.age
        # ---- caregiving
        for c in p.care_for:
            if c.inpatient:
                continue
            same = c.hh is H
            if rng.random() > (.80 if same else .34):
                continue
            dur = rng.randint(50, 200) if same else rng.randint(40, 140)
            tasks = rng.choice(["meals and medications", "bathing and dressing", "a ride and an errand", "sorting pills and paying bills", "housework and laundry", "keeping company and supervising"])
            if same:
                t = sim.slot(p, dur, ((390, 560, 1.0), (1020, 1290, 1.5), (600, 1000, .6)))
                squeezed = t is None
                if t is None:
                    dur = rng.randint(25, 45)
                    t = sim.slot(p, dur, ((300, 1430, 1.0),))
                    if t is None:
                        continue
                emit(t, "non_monetary_job", "care_and_household", "caregiving_at_home", p, H, p, c, ben=c, tmin=dur, lens=("family_care",),
                     fr=(("caregiving_conflict",) if (squeezed or p.works) and rng.random() < .5 else ()), ctx=dict(tasks=tasks, rel=c.rel, age=c.age))
            else:
                cd = c.hh.district
                miles, mode, mins, tfr = sim.trip(p, H, d, cd)
                t = sim.slot(p, dur + min(mins, 50), ((1000, 1260, 1.5), (540, 1000, 1.0)))
                if t is None:
                    emit(rng.randint(720, 1200), "failed_attempt", "care_and_household", "caregiving_visit", p, H, p, c, ben=c, channel="phone", tmin=rng.randint(5, 15),
                         outcome="rescheduled", fr=("caregiving_conflict", "schedule_volatility") if p.works else ("caregiving_conflict",), lens=("family_care",),
                         ctx=dict(tasks=tasks, rel=c.rel, age=c.age, reason="work ran long and there was no time left to get there"))
                else:
                    fac = c.hh.gq in ("nursing_home", "assisted_living", "group_home")
                    emit(t + min(mins, 50) // 2, "non_monetary_job", "care_and_household", "caregiving_visit", p, H, p, c, ben=c, tmin=dur, miles=miles, mode=mode,
                         fr=tfr, lens=("family_care",), ctx=dict(tasks=("a visit and a talk with the staff" if fac else tasks), rel=c.rel, age=c.age, fac="1" if fac else ""))
        if a < 18:
            continue
        # ---- shift volatility
        if p.emp.startswith("employed") and p.wsched == "variable" and p.org is not None:
            if p.works and p.shift and rng.random() < .028:
                hrs = rng.choice([1, 1.5, 2, 2, 3])
                lost = round(hrs * p.wage / 2080.0, 2)
                emit(max(0, p.shift[-1][1] - int(hrs * 60)), "failed_attempt", "work", "sent_home_early", p, H, p, p.org, gross=lost, tmin=int(hrs * 60), outcome="partial",
                     fr=("schedule_volatility",), lens=("labor",), ctx=dict(org=p.org.name, hrs=hrs, lost="%.2f" % lost))
            elif not p.works and cal["weekday"] and rng.random() < .022:
                hrs = rng.choice([4, 5, 6, 8])
                lost = round(hrs * p.wage / 2080.0, 2)
                emit(rng.randint(330, 720), "failed_attempt", "work", "shift_cancelled_short_notice", p, H, p, p.org, channel="app", gross=lost, tmin=3, outcome="failed",
                     fr=("schedule_volatility",), lens=("labor",), ctx=dict(org=p.org.name, hrs=hrs, lost="%.2f" % lost, notice=rng.choice(["two hours", "the night before", "ninety minutes", "at clock-in"])))
        # ---- extra hours turned down to stay under a benefit limit
        if p.emp.startswith("employed") and p.wsched != "fixed" and p.org is not None and (H.snap or H.ccdf or H.subsidized or p.cov == "medicaid") and rng.random() < .0045:
            hrs = rng.choice([4, 6, 8, 10])
            extra = round(hrs * p.wage / 2080.0, 2)
            prog = "food benefits" if H.snap else "the child care subsidy" if H.ccdf else "the rent subsidy" if H.subsidized else "Medicaid"
            emit(sim.slot_soft(p, 3, DAY), "non_monetary_job", "work", "turned_down_extra_hours", p, H, p, p.org, gross=extra, tmin=3, outcome="abandoned", fr=("benefits_cliff",),
                 lens=("labor", "public_finance"), ctx=dict(org=p.org.name, hrs=hrs, extra="%.2f" % extra, prog=prog))
        # ---- a paid ride to the fields
        if p.works and p.occ in ("crop farmworker", "packing shed worker") and p.shift and (H.vehicles == 0 or rng.random() < .35) and p.wallet is not None:
            fare = float(rng.choice([8, 8, 10, 10, 12]))
            t0 = max(240, p.shift[0][0] - 35)
            push(q, t0, lambda t0=t0, p=p, fare=fare: hand_pay(sim, t0, p, H, p.wallet, X["x_customers"], "transportation", "ride_to_work_fee", fare, ("cash",), tmin=0,
                                                              miles=round(sim.dist(H.district, "D6") * 2, 1), mode="carpool", fr=("no_transit", "fee"), lens=("farmworker", "labor", "rural"),
                                                              ctx=dict(org=p.org.name if p.org is not None else "the farm")))
        # ---- looking for work
        if p.emp == "unemployed":
            if rng.random() < .42:
                n = rng.choice([1, 1, 2, 3, 4])
                dur = rng.randint(25, 45) * n
                if H.internet == "no":
                    emit(sim.slot_soft(p, 20, DAY), "non_monetary_job", "work", "job_search_in_person", p, H, p, "", tmin=rng.randint(60, 150), miles=round(rng.uniform(2, 14), 1),
                         mode="car" if H.vehicles else "walk", fr=("digital_barrier",) + (() if H.vehicles else ("no_transit",) if d not in ("D1", "D2") else ()), lens=("labor",), ctx=dict(n=n))
                else:
                    t = sim.slot_soft(p, dur, ((540, 1260, 1.0),))
                    emit(t, "non_monetary_job", "work", "job_applications_online", p, H, p, "", channel="online", tmin=dur,
                         fr=(("digital_barrier",) if H.internet == "mobile_only" else ()), lens=("labor",), ctx=dict(n=n))
            if rng.random() < .028:
                job_interview(sim, p, H, q)
            if p.ui and (int(p.pid[1:]) % 5) == (cal["dow"] + 3) % 5:
                r = rng.random()
                t = sim.slot_soft(p, 12, DAY)
                bad = out[0] <= t <= out[1] or r < .07
                i = emit(t, "failed_attempt" if bad else "non_monetary_job", "work", "weekly_unemployment_certification", p, H, p, X["x_ui"], channel="online" if H.internet != "no" else "phone",
                         tmin=rng.randint(8, 16) if not bad else rng.randint(10, 30), outcome="failed" if bad else "completed", fr=("outage", "digital_barrier") if bad else (),
                         lens=("labor",), ctx=dict(reason="the state claims site would not load" if bad else ""))
                if bad:
                    emit(min(1400, max(t + 120, out[1] + rng.randint(20, 240))), "non_monetary_job", "work", "weekly_unemployment_certification", p, H, p, X["x_ui"], channel="phone",
                         tmin=rng.randint(15, 40), wait=rng.randint(8, 30), related=i, lens=("labor",), ctx=dict(retry="phone"))
        elif p.emp.startswith("employed") and rng.random() < .0011:
            job_interview(sim, p, H, q)
        # ---- phone holds and paperwork
        if rng.random() < .0052:
            r = rng.random()
            if r < .28 and p.cov not in ("uninsured",):
                hold(sim, p, H, X["x_ins_a"] if p.cov in ("employer", "marketplace", "other_private") else X["x_cms"] if p.cov.startswith("medicare") else X["x_medicaid"],
                     "insurance_phone_call", (10, 48), "health", matter=rng.choice(["a denied claim", "a prior authorization", "a surprise bill", "finding an in-network doctor", "a wrong premium charge"]),
                     lens=("health_cost",))
            elif r < .46:
                b = next((b for b in H.bills if b[0] in ("electric_bill", "internet_bill", "phone_bill", "gas_bill", "water_bill")), None)
                if b is not None:
                    hold(sim, p, H, b[1], "utility_billing_phone_call", (4, 32), "utilities", matter=rng.choice(["a bill twice the usual size", "a payment arrangement", "a service outage", "a promotional rate that expired", "a late fee"]))
            elif r < .58 and p.wallet is not None and p.wallet.bank_org is not None:
                hold(sim, p, H, p.wallet.bank_org, "bank_phone_call", (3, 26), "money_services", matter=rng.choice(["a locked card", "an overdraft fee", "a charge that was not theirs", "a held deposit"]), drop=.12)
            elif r < .70 and cal["tax_season"]:
                hold(sim, p, H, X["x_irs"], "irs_phone_call", (22, 95), "civic_legal", matter=rng.choice(["a refund that has not arrived", "an identity verification letter", "a notice about last year's return"]), drop=.38)
            elif r < .84:
                org = sim.pick(("physician", "dental", "behavioral"), d, 8.0)
                if org is not None:
                    t = sim.slot_soft(p, 9, ((500, 990, 1.0),))
                    wk = rng.choice([1, 2, 3, 5, 8, 11])
                    emit(t, "non_monetary_job", "health", "appointment_scheduling_call", p, H, p, org, channel="phone", tmin=rng.randint(5, 14), wait=rng.randint(0, 12),
                         fr=(("wait",) if wk >= 5 else ()), ctx=dict(org=org.name, weeks=wk))
            else:
                ll = H.landlord
                if H.tenure == "renter" and ll is not None:
                    t = sim.slot_soft(p, 8, DAY)
                    oc = rng.choice(["completed", "completed", "rescheduled"])
                    emit(t, "non_monetary_job", "housing", "repair_request_to_landlord", p, H, p, ll, channel=rng.choice(["phone", "app", "phone"]), tmin=rng.randint(5, 15),
                         outcome=oc, ctx=dict(org=ll.name, reason="the office line went to voicemail" if oc != "completed" else "", issue=rng.choice(["no heat in the back bedroom", "a leaking kitchen faucet", "a broken dryer in the shared laundry", "mold in the bathroom", "mice", "a dead smoke detector"])))
        # ---- returns, disputes, scams, rides, civic forms
        r = rng.random()
        if r < .0034 and p.wallet is not None:
            org = sim.pick(("supercenter", "clothing", "home_center", "department", "electronics"), d, 8.0)
            amt = round(rng.uniform(9, 140), 2)

            def run(t, miles, mode, tfr, w, p=p, org=org, amt=amt):
                rr = rng.random()
                if rr < .14:
                    emit(t, "failed_attempt", "discretionary", "store_return", p, H, p, org, gross=amt, tmin=8 + w, wait=w, miles=miles, mode=mode, outcome="declined",
                         fr=tfr + ["missing_document"], ctx=dict(org=org.name, amt="%.2f" % amt, reason="there was no receipt and the return window had closed"))
                else:
                    how = "cash" if rr < .3 else "bank"
                    sim.credit(p.wallet, amt, how)
                    emit(t, "non_monetary_job", "discretionary", "store_return", p, H, org, p, method="cash" if how == "cash" else "debit", gross=amt, tmin=8 + w, wait=w,
                         miles=miles, mode=mode, fr=tfr, ctx=dict(org=org.name, amt="%.2f" % amt))
            go(sim, q, p, H, org, 10, SHOP, run, wait=(1, 18), chained=True)
        elif r < .0058 and H.internet != "no" and p.wallet is not None:
            org = sim.pick(("ship_notary", "post_office", "pharmacy"), d, 5.0)
            amt = round(rng.uniform(12, 120), 2)
            go(sim, q, p, H, org, 8, SHOP,
               lambda t, miles, mode, tfr, w, p=p, org=org, amt=amt: emit(t, "non_monetary_job", "discretionary", "online_order_return_dropoff", p, H, p, org, gross=amt, tmin=8 + w, wait=w,
                                                                          miles=miles, mode=mode, outcome="partial", fr=tfr + ["pending_hold"], ctx=dict(org=org.name, amt="%.2f" % amt)),
               wait=(0, 10), chained=True)
        elif r < .0064 and p.wallet is not None and (p.wallet.cc_limit or p.wallet.bank is not None):
            amt = round(rng.uniform(18, 420), 2)
            t = sim.slot_soft(p, 20, DAY)
            emit(t, "non_monetary_job", "money_services", "card_charge_dispute", p, H, p, X["x_cc1"], channel=rng.choice(["phone", "app"]), gross=amt, tmin=rng.randint(10, 35),
                 wait=rng.randint(0, 25), outcome="partial", fr=("pending_hold", "scam_attempt") if rng.random() < .5 else ("pending_hold",),
                 ctx=dict(amt="%.2f" % amt, what=rng.choice(["a subscription that was cancelled months ago", "a charge from a store never visited", "a double charge at a gas pump", "a package that never arrived"])))
        elif r < .0064 + .0042 * (1.6 if a >= 65 else 1.0):
            lost = rng.random() < .014
            t = sim.slot_soft(p, 4, ((540, 1200, 1.0),))
            how = rng.choice(["a text about an unpaid toll", "a call claiming to be the bank's fraud desk", "a call about a grandchild in jail", "a text about a package held for a fee",
                              "a call saying Social Security was suspending the number", "an email invoice for antivirus software", "a job offer that asked for a deposit"])
            if lost and p.wallet is not None and p.wallet.liquid() > 300:
                amt = float(rng.choice([200, 300, 500, 500, 1000, 1500]))
                W = p.wallet

                def run(t=t, p=p, W=W, amt=amt, how=how):
                    m = "debit" if (W.bank is not None and W.bank >= amt) else ("cash" if W.cash >= amt else None)
                    if m is None:
                        emit(t, "non_monetary_job", "money_services", "scam_attempt_handled", p, H, p, X["x_scam"], channel="phone", tmin=rng.randint(8, 40), fr=("scam_attempt",), ctx=dict(how=how))
                        return
                    W.take(m, amt)
                    emit(t, "transfer", "money_services", "scam_loss", p, H, p, X["x_scam"], channel="phone", method=m, gross=amt, user=amt, tmin=rng.randint(40, 120),
                         outcome="completed", fr=("scam_attempt",), ctx=dict(how=how, amt="%.0f" % amt, via=rng.choice(["gift cards read over the phone", "a wire from the bank branch", "a payment-app transfer", "a deposit into a crypto kiosk"])))
                push(q, t, run)
            else:
                emit(t, "non_monetary_job", "money_services", "scam_attempt_handled", p, H, p, X["x_scam"], channel=rng.choice(["phone", "phone", "online"]), tmin=rng.randint(1, 9),
                     fr=("scam_attempt",), ctx=dict(how=how))
        if (H.vehicles == 0 or a >= 82 or p.dis in ("vision", "multiple", "self_care")) and d in ("D3", "D4", "D5", "D6") and rng.random() < .014:
            t = sim.slot_soft(p, 15, ((480, 1080, 1.0),))
            rr = rng.random()
            rt = sim.one("rural_transit")
            where = rng.choice(["a clinic appointment", "the grocery store", "the pharmacy", "work", "the benefits office", "church"])
            if d in ("D5", "D6") and rr < .35:
                emit(t, "failed_attempt", "transportation", "ride_search", p, H, p, rt, channel="phone", tmin=rng.randint(8, 20), wait=rng.randint(2, 12), outcome="rescheduled",
                     fr=("no_transit", "hours_mismatch"), lens=("land_use", "rural"), ctx=dict(org=rt.name, where=where, reason="the county van needs a booking a full day ahead"))
            elif rr < .80:
                emit(t, "non_monetary_job", "transportation", "ride_search", p, H, p, "", channel="phone", tmin=rng.randint(6, 30), fr=("no_transit",), lens=("land_use",),
                     ctx=dict(where=where, got=rng.choice(["a neighbor", "a daughter on her lunch break", "a friend from church", "a coworker for gas money"])))
            else:
                emit(t, "failed_attempt", "transportation", "ride_search", p, H, p, "", channel="phone", tmin=rng.randint(15, 45), outcome="abandoned", fr=("no_transit",),
                     lens=("land_use",), ctx=dict(where=where, reason="nobody was free to drive"))
        if rng.random() < .00035:
            t = sim.slot_soft(p, 6, EVE)
            emit(t, "non_monetary_job", "civic_legal", "voter_registration_update", p, H, p, sim.one("county"), channel="online" if H.internet != "no" else "mail", tmin=rng.randint(4, 12),
                 ctx=dict(why=rng.choice(["a move across town", "a name change", "turning eighteen", "a new party preference"])))
    # ---- household benefit paperwork
    ad = [p for p in H.adults if not p.inpatient]
    if not ad:
        return
    P = ad[0] if len(ad) == 1 else rng.choice(ad)
    medicaid = any(p.cov in ("medicaid", "medicare_medicaid_dual") for p in H.members)
    if (H.snap or medicaid) and rng.random() < .0048:
        renewal(sim, P, H, q, "snap_recertification" if (H.snap and rng.random() < .5) else "medicaid_renewal")
    if (H.snap or medicaid) and rng.random() < .0011:
        org = sim.one("benefits_office")
        t = rng.randint(600, 1020)
        emit(t, "failed_attempt", "civic_legal", "benefits_renewal_returned", P, H, org, P, channel="mail", tmin=rng.randint(10, 25), outcome="failed",
             fr=("paperwork", "repeat_trip"), lens=("public_finance",), ctx=dict(org=org.name, reason=rng.choice(["one signature line was blank", "a second adult's signature was missing", "the form was an older version"])))
        renewal(sim, P, H, q, "renewal_resubmitted", after=t)
    for p in ad:
        if 19 <= p.age <= 64 and p.cov == "medicaid" and not p.ssi and p.dis == "none" and not any(k.age < 14 for k in H.kids) and rng.random() < 1 / 30.0:
            t = sim.slot_soft(p, 15, EVE)
            down = out[0] <= t <= out[1]
            r = rng.random()
            bad = down or r < .10
            i = emit(t, "failed_attempt" if bad else "non_monetary_job", "civic_legal", "medicaid_work_hours_report", p, H, p, X["x_medicaid"],
                     channel="online" if H.internet != "no" else "phone", tmin=rng.randint(10, 30), outcome=("failed" if down else "rescheduled") if bad else "completed",
                     fr=(("outage",) if down else ("paperwork", "eligibility_confusion")) if bad else (("digital_barrier",) if H.internet != "yes" else ()),
                     lens=("public_finance", "labor"), ctx=dict(reason=("the state portal was down" if down else rng.choice(["the pay stub upload was rejected as unreadable", "gig hours had no employer to verify them", "the form would not accept two part-time jobs"])) if bad else ""))
            if bad and rng.random() < .6:
                emit(min(1410, t + rng.randint(120, 420)), "non_monetary_job", "civic_legal", "medicaid_work_hours_report", p, H, p, X["x_medicaid"], channel="online",
                     tmin=rng.randint(10, 25), related=i, lens=("public_finance", "labor"), ctx=dict(retry="second try"))


def job_interview(sim, p, H, q):
    rng = sim.rng
    video = rng.random() < .35 and H.internet == "yes"
    if video:
        t = sim.slot(p, 45, ((540, 1020, 1.0),))
        if t is not None:
            sim.emit(t, "non_monetary_job", "work", "job_interview", p, H, p, "", channel="online", tmin=rng.randint(30, 55), lens=("labor",), ctx=dict(video="1"))
        return
    dd = rng.choice(["D1", "D2", "D3", "D4", H.district, H.district])
    miles, mode, mins, tfr = sim.trip(p, H, H.district, dd)
    t = sim.slot(p, 60 + min(mins, 50), ((540, 1020, 1.0),))
    if t is None:
        sim.emit(rng.randint(540, 900), "failed_attempt", "work", "job_interview", p, H, p, "", channel="phone", tmin=6, outcome="rescheduled",
                 fr=("schedule_volatility", "hours_mismatch"), lens=("labor",), ctx=dict(reason="the only slot offered overlapped a shift"))
        return
    if mode == "transit":
        bus_ride(sim, q, p, H, max(0, t - 5), H.district, dd, "job interview")
    sim.emit(t + min(mins, 50) // 2, "non_monetary_job", "work", "job_interview", p, H, p, "", tmin=rng.randint(35, 70), wait=rng.randint(0, 20), miles=miles, mode=mode,
             fr=tfr, lens=("labor",), ctx=dict(video=""))


def renewal(sim, P, H, q, kind, after=None):
    """A benefits renewal by portal, mail, phone or counter, including the day's portal outage."""
    rng, X = sim.rng, sim.X
    out = sim.cfg["BENEFITS_PORTAL_OUTAGE"]
    org = sim.pick(("benefits_office",), H.district, 14.0) or sim.by_kind["benefits_office"][0]
    r = rng.random()
    lens = ("public_finance",)
    if r < (.55 if H.internet == "yes" else .30 if H.internet == "mobile_only" else 0.0):
        dur = rng.randint(25, 70)
        t = sim.slot_soft(P, dur, ((480, 1320, 1.0),) if after is None else ((after + 20, 1380, 1.0),))
        fr = ["paperwork"] + (["digital_barrier"] if H.internet == "mobile_only" else []) + (["language"] if H.lep and rng.random() < .5 else [])
        if out[0] <= t <= out[1]:
            i = sim.emit(t, "failed_attempt", "civic_legal", kind, P, H, P, org, channel="online", tmin=rng.randint(12, 35), outcome="failed", fr=fr + ["outage"], lens=lens,
                         ctx=dict(org=org.name, reason="the state benefits portal was down from late morning into the afternoon"))
            sim.bump("portal_outage")
            if rng.random() < .7:
                t2 = min(1400, out[1] + rng.randint(30, 420))
                sim.emit(t2, "non_monetary_job", "civic_legal", kind, P, H, P, org, channel="online", tmin=dur, fr=fr, lens=lens, related=i, ctx=dict(org=org.name, retry="after the portal came back"))
            return
        miss = rng.random() < .18
        cut = ""
        if not miss and H.snap and any(p.wage > 0 for p in H.adults) and rng.random() < .22:
            cut = "%d" % rng.choice([23, 41, 58, 76, 112, 147])
            fr = fr + ["benefits_cliff"]
        elif not miss and rng.random() < .10:
            fr = fr + ["eligibility_confusion"]
        sim.emit(t, "non_monetary_job", "civic_legal", kind, P, H, P, org, channel="online", tmin=dur, outcome="partial" if miss else "completed",
                 fr=fr + (["missing_document"] if miss else []), lens=lens, ctx=dict(org=org.name, cut=cut, reason="a pay stub or lease still has to be uploaded" if miss else ""))
    elif r < .78:
        t = sim.slot_soft(P, 40, ((540, 1260, 1.0),))
        sim.emit(t, "non_monetary_job", "civic_legal", kind, P, H, P, org, channel="mail", tmin=rng.randint(30, 75), fee_type="postage", fee=.78, user=.78, gross=.78, method="cash",
                 fr=("paperwork",) + (("language",) if H.lep else ()), lens=lens, ctx=dict(org=org.name, mail="1"))
    else:
        def run(t, miles, mode, tfr, w):
            rr = rng.random()
            oc = "rescheduled" if rr < .20 else "completed"
            sim.emit(t, "non_monetary_job" if oc == "completed" else "failed_attempt", "civic_legal", kind, P, H, P, org, tmin=30 + w, wait=w, miles=miles, mode=mode, outcome=oc,
                     fr=tfr + ["paperwork"] + (["missing_document", "repeat_trip"] if oc != "completed" else []), lens=lens,
                     ctx=dict(org=org.name, reason=rng.choice(["proof of rent was missing", "an ID had expired", "the caseworker needed last month's pay stubs"]) if oc != "completed" else ""))
        if go(sim, q, P, H, org, 30, OFFICE, run, wait=(30, 150), after=after) is None:
            sim.emit(rng.randint(1000, 1200), "failed_attempt", "civic_legal", kind, P, H, P, org, tmin=3, outcome="rescheduled", fr=("hours_mismatch",), lens=lens,
                     ctx=dict(org=org.name, reason="the office closes at 4:30, before the workday ends"))


# ------------------------------------------------------------------------------------------ everything else at home
def gen_misc(sim, H, q):
    rng, cal, X = sim.rng, sim.cal, sim.X
    if H.gq:
        return
    d = H.district
    emit = sim.emit
    ad = [p for p in H.adults if not p.inpatient and p.wallet is not None]
    if not ad:
        return
    W0 = H.wallets[0]
    P = rng.choice(ad)
    # ---- midweek service offering
    if cal["dow"] in (2, 6) and rng.random() < (.018 if cal["dow"] == 2 else .17) * (1.4 if d in ("D5", "D6", "D4") else 1.0) * (1.5 if H.head.age >= 60 else 1.0):
        org = sim.pick(("church",), d, 4.0)
        amt = float(rng.choice([5, 10, 10, 20, 20, 25, 40, 50, 100]))
        if org is not None:
            miles, mode, mins, tfr = sim.trip(P, H, d, org.district)
            win = ((1080, 1230, 1.0),) if cal["dow"] == 2 else ((540, 750, 1.0),)
            t = sim.slot(P, 80 + min(mins, 30), win, win[0][0], win[0][1] + 60)
            if t is not None:
                m = ("cash", "check") if rng.random() < .6 else ("check", "cash")
                push(q, t, lambda t=t, P=P, org=org, amt=amt, m=m, miles=miles, mode=mode: hand_pay(sim, t, P, H, W0, org, "giving_faith", "church_offering", amt, m, rtype="transfer",
                                                                                                     tmin=80, miles=miles, mode=mode))
    # ---- online giving and crowdfunding
    if rng.random() < .0016 * len(ad) and W0.bank is not None:
        amt = float(rng.choice([10, 20, 25, 25, 50, 50, 100, 250]))
        tip = round(amt * rng.choice([0, 0, .1, .125, .15]), 2)
        online(sim, q, P, H, X["x_crowd"], "giving_faith", "crowdfunding_contribution", amt, taxable=False, fee=("optional_platform_tip", tip) if tip else None,
               ctx=dict(cause=rng.choice(["a coworker's medical bills", "a funeral for a neighbor's son", "a family burned out of their apartment", "a classmate's cancer treatment", "a youth team's travel costs", "a friend's rent after a layoff"])),
               rtype="transfer", W=W0)
    if rng.random() < .0009 * len(ad) and W0.bank is not None:
        online(sim, q, P, H, X["x_charity"], "giving_faith", "one_time_online_donation", float(rng.choice([15, 25, 50, 100, 250])), taxable=False, ctx=dict(), rtype="transfer", W=W0)
    # ---- home repair and services
    owner = H.tenure != "renter"
    if rng.random() < (.0030 if owner else .0004) * inc(H, .4, .8, 1.3):
        org = sim.pick(("construction", "repair_shop"), d, 12.0)
        job = rng.choice(["a water heater replacement", "a roof leak repair", "an HVAC service call", "a plumbing repair", "tree removal", "an electrical panel fix", "gutter repair", "an appliance repair"])
        amt = round(min(9500, max(120, rng.lognormvariate(math.log(520), .9))), 2)
        if org is not None:
            noshow = rng.random() < .13 * sim.wx["noshow"]
            win = rng.choice([(480, 720), (720, 960), (600, 840)])
            who = next((a for a in ad if (not a.works or a.wfh) and a.free), None)
            home = who is not None
            if home:
                who.free = subtract([tuple(f) for f in who.free], [win])
            else:
                who = P
            if home or rng.random() < .4:        # with nobody home on a workday, most jobs wait; outdoor work can go ahead
                def run(t=win[0], who=who, org=org, job=job, amt=amt, noshow=noshow, win=win, home=home):
                    if noshow:
                        emit(win[1], "failed_attempt", "housing", "home_repair_service", who, H, who, org, channel="in_person" if home else "phone", gross=amt, tmin=0,
                             wait=(win[1] - win[0]) if home else 0, outcome="rescheduled", fr=("wait", "schedule_volatility", "repeat_trip") if home else ("schedule_volatility", "repeat_trip"),
                             ctx=dict(org=org.name, job=job, reason="the contractor never showed during the four-hour window"))
                        sim.bump("contractor_no_show")
                        return
                    tp = win[0] + rng.randint(30, 200)
                    kw = dict(ctx=dict(job=job, org=org.name), tmin=rng.randint(45, 200) if home else 5, wait=rng.randint(10, 90) if home else 0,
                              channel="in_person" if home else "phone", quiet_fail=0.0)
                    if amt > 900 and rng.random() < .35:
                        dep = round(amt * .5, 2)
                        sim.pay(tp, who, H, W0, org, "housing", "home_repair_service", amt, defer=amt - dep,
                                force=("check", "credit", "debit") if W0.bank is not None and W0.bank > dep else None, **kw)
                    else:
                        sim.pay(tp, who, H, W0, org, "housing", "home_repair_service", amt, **kw)
                push(q, win[0], run)
    if rng.random() < .0011 * inc(H, .1, .5, 1.6) and owner:
        t = sim.slot_soft(P, 3, EVE)
        amt = float(rng.choice([45, 55, 60, 75, 90, 120]))
        push(q, t, lambda t=t, amt=amt: hand_pay(sim, t, P, H, W0, X["x_customers"], "housing", "lawn_or_yard_service", amt, ("p2p_app", "cash", "check"), channel="app", tmin=2))
    # ---- bike repair
    if H.vehicles == 0 and d in ("D1", "D2", "D4") and rng.random() < .0022:
        org = sim.pick(("bike_shop",), d, 6.0)
        errand(sim, q, P, H, org, "transportation", "bike_repair", round(rng.uniform(12, 95), 2), rng.randint(10, 25), SHOP, ctx=dict(), W=W0)
    # ---- shutoff notices, disconnections, reconnection
    if H.alice != "above" and not H.util_incl:
        r = rng.random()
        util = next((b for b in H.bills if b[0] in ("electric_bill", "gas_bill", "water_bill")), None)
        if util is not None and r < .0020:
            past = round(util[2] * rng.uniform(1.6, 3.2), 2)
            org = util[1]
            what = util[0].replace("_bill", "")
            if r < .0015:
                emit(rng.randint(660, 960), "non_monetary_job", "utilities", "shutoff_notice_received", P, H, org, P, channel="mail", tmin=rng.randint(4, 15),
                     outcome="partial", fr=("insufficient_funds",), lens=("housing",), ctx=dict(org=org.name, amt="%.2f" % past, what=what, days=rng.choice([5, 7, 10])))
            else:
                fee = float(rng.choice([35, 45, 50, 75]))
                t = sim.slot_soft(P, 15, ((480, 900, 1.0),))
                i0 = emit(max(300, t - rng.randint(30, 180)), "failed_attempt", "utilities", "service_disconnected_for_nonpayment", P, H, org, P, tmin=10, outcome="failed",
                          fr=("insufficient_funds",), lens=("housing",), ctx=dict(org=org.name, what=what, amt="%.2f" % past, reason="the past-due balance was not paid by the notice date"))

                def run(t=t, org=org, past=past, fee=fee, what=what, i0=i0):
                    need = round(past * rng.choice([.5, .5, 1.0]), 2)
                    i, oc, m = sim.pay(t, P, H, W0, None, "utilities", "reconnection_payment", need, channel="phone", ctx=dict(org=org.name, what=what), tmin=rng.randint(12, 30),
                                       wait=rng.randint(5, 25), rtype="bill_payment", fee=("reconnection_fee", fee), to=org, related=i0, quiet_fail=0.0, lens=("housing",))
                    if oc != "completed":
                        ca = sim.one("community_action")
                        emit(t + 45, "non_monetary_job", "utilities", "sought_emergency_utility_help", P, H, P, ca, channel="phone", tmin=rng.randint(15, 40), wait=rng.randint(5, 30),
                             outcome=rng.choice(["completed", "rescheduled", "abandoned"]), related=i0, fr=("insufficient_funds", "paperwork"), lens=("housing",), ctx=dict(org=ca.name, what=what))
                push(q, t, run)
    # prepaid phone ran out mid-month
    if W0.status != "above" and any(b[0] == "phone_bill" and b[7] == "prepaid" for b in H.bills) and rng.random() < .0035:
        org = sim.pick(("dollar", "phone_store", "gas"), d, 4.0)
        errand(sim, q, P, H, org, "utilities", "prepaid_phone_top_up", float(rng.choice([10, 15, 20, 25])), rng.randint(5, 12), SHOP, taxable=False, ctx=dict(), W=W0,
               fr=("digital_barrier",), allow_partial=False, quiet_fail=.3)
    # ---- notary and odd civic errands
    if rng.random() < .0006 * len(ad):
        org = sim.pick(("ship_notary", "bank", "credit_union"), d, 6.0)
        free = org is not None and org.kind in ("bank", "credit_union")
        if free:
            go(sim, q, P, H, org, 12, OFFICE,
               lambda t, miles, mode, tfr, w: emit(t, "non_monetary_job", "civic_legal", "notary_service", P, H, P, org, tmin=12 + w, wait=w, miles=miles, mode=mode, fr=tfr,
                                                   ctx=dict(org=org.name, doc=rng.choice(["a car title transfer", "a power of attorney", "a school residency affidavit", "a consent form for a child's passport"]), free="1")),
               wait=(0, 20))
        else:
            errand(sim, q, P, H, org, "civic_legal", "notary_service", float(rng.choice([5, 10, 10, 15, 20])), rng.randint(8, 15), OFFICE, taxable=False, wait=(0, 12),
                   ctx=dict(doc=rng.choice(["a car title transfer", "a power of attorney", "a school residency affidavit", "a consent form for a child's passport"])), W=W0)
    # ---- fishing and hunting licenses, pet licenses
    if d in ("D5", "D6", "D4", "D3") and rng.random() < .0006:
        online(sim, q, P, H, X["x_staterev"], "civic_legal", "fishing_or_hunting_license", float(rng.choice([15, 19, 28, 48])), taxable=False, ctx=dict(), fee=("online_convenience_fee", 2.0), W=W0)
    # ---- a new vehicle or a used one
    if rng.random() < .00085:
        car_purchase(sim, P, H, q)


def car_purchase(sim, P, H, q):
    rng, X = sim.rng, sim.X
    W0 = H.wallets[0]
    have = W0.liquid() + W0.cc_bal + W0.savings
    if have < 600:
        return
    d = H.district
    r = rng.random()
    emit = sim.emit
    if H.alice == "poverty" or (H.alice == "alice" and r < .45):
        if rng.random() < .45:
            price = float(rng.choice([1800, 2500, 3200, 4000, 5500]))
            t = sim.slot_soft(P, 40, ((600, 1200, 1.0),))

            def run(t=t, price=price):
                if W0.savings > 0 and W0.bank is not None and W0.cash + W0.bank < price:
                    mv = min(W0.savings, price)
                    W0.savings -= mv
                    W0.bank += mv
                if W0.cash + (W0.bank or 0) >= price:
                    take = min(W0.cash, price)
                    W0.take("cash", take)
                    if price > take:
                        W0.take("debit", price - take)
                    emit(t, "purchase", "transportation", "used_car_private_sale", P, H, P, X["x_customers"], method="cash", gross=price, user=price, tmin=rng.randint(60, 150),
                         miles=round(rng.uniform(3, 25), 1), mode="ride_from_family_or_friend", ctx=dict(amt="%.0f" % price))
            push(q, t, run)
        else:
            org = sim.pick(("bhph_dealer",), d, 14.0)
            price = float(rng.choice([8900, 10500, 11900, 13500]))
            down = float(min(rng.choice([500, 800, 1000, 1500, 2000]), max(300, int(have * .7 / 100) * 100)))
            errand(sim, q, P, H, org, "transportation", "used_car_buy_here_pay_here", price, rng.randint(90, 180), SHOP, taxable=True, wait=(5, 40),
                   ctx=dict(down="%.0f" % down, apr=rng.choice(["21.9", "24.9", "27.9"]), wk=rng.choice([85, 95, 110])), W=W0,
                   third=round(price * (1 + SALES_TAX) - down, 2), payer="Dealer financing (buy here, pay here)", fund="private", quiet_fail=0.0, fee=("documentation_fee", float(rng.choice([299, 399, 499]))))
    else:
        if W0.bank is not None and W0.savings > 0:
            mv = W0.savings * .6
            W0.savings -= mv
            W0.bank += mv
        new = H.alice == "above" and rng.random() < .40
        org = sim.pick(("car_dealer",), d, 16.0)
        price = round(rng.uniform(31000, 62000) if new else rng.uniform(13500, 32000), 0)
        down = round(min(price * rng.uniform(.05, .22), max(500.0, have * .6)), 0)
        lender = rng.choice([X["x_auto1"], X["x_auto2"]])
        errand(sim, q, P, H, org, "transportation", "new_car_purchase" if new else "used_car_dealer_purchase", price, rng.randint(120, 240), SHOP, taxable=True, wait=(5, 45),
               ctx=dict(down="%.0f" % down, apr=rng.choice(["5.9", "6.9", "7.4", "8.9", "11.5"]), term=rng.choice([60, 72, 72, 84])), W=W0,
               third=round(price * (1 + SALES_TAX) - down, 2), payer="%s (auto loan)" % lender.name, fund="private", quiet_fail=0.0, fee=("documentation_fee", float(rng.choice([399, 599, 699, 799]))))


HOUSEHOLD_GENS = [gen_school, gen_public, gen_money, gen_care, gen_misc]
