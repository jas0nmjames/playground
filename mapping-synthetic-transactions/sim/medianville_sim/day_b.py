"""Household day, part B: food, shopping, getting around, health care."""
import math
from .config import SALES_TAX, TRANSIT_SERVED, PART_B_DEDUCTIBLE, PART_D_OOP_CAP
from .engine import ANY, DAY, EVE, GAS, OFFICE, SHOP, LUNCH, MORN, MEAL, AFT, NIGHT
from .day_a import push

# Bus and paratransit, set from NTD 2025 (sources/raw/ntd, Master sheet of the September 2026 monthly ridership file):
# agencies in urbanized areas of 50,000-400,000 people, trip-weighted. Bus: $8.74 operating cost and $0.79 in fares per
# unlinked trip; demand response (paratransit): $50.42 and $4.13. Costs carried to 2027 at 3% a year. v1 had $9.80 a bus
# ride, a $1.75 fare (riders paid $1.01 a ride on average) and $58 a paratransit ride.
TRANSIT_COST = 9.27
PARATRANSIT_COST = 53.50
BUS_FARE, BUS_FARE_REDUCED = 1.50, 0.75   # half fare for seniors and riders with disabilities (federal rule)


def bus_ride(sim, q, P, H, t, o_d, d_d, purpose="errand"):
    """One unlinked transit trip: the fare the rider pays plus the operating subsidy behind it."""
    rng, X = sim.rng, sim.X
    tr = sim.one("transit")
    W = P.wallet
    reduced = P.age >= 65 or P.dis not in ("none", None)
    fare = BUS_FARE_REDUCED if reduced else BUS_FARE
    if P.pid in sim.passholders or (P.age < 19 and rng.random() < .5):
        fare, how = 0.0, "prepaid"
    else:
        r = rng.random()
        how = "cash" if (r < .30 or W.bank is None) else "prepaid"
        if how == "cash" and W.cash < fare:
            how = "prepaid" if W.bank is not None else "cash"
    missed = rng.random() < .025 * sim.wx["missed_bus"] * (3.5 if sim.cfg["BUS_BREAKDOWN"][0] <= t <= sim.cfg["BUS_BREAKDOWN"][1] and o_d in ("D1", "D2") else 1)
    ride = int(8 + 3.2 * (sim.dist(o_d, d_d)))

    def run(t=t):
        rel, tt = None, t
        if missed:
            w = rng.randint(18, 48)
            late = purpose == "commute" and P.wsched != "none"
            rel = sim.emit(tt, "failed_attempt", "transportation", "missed_bus", P, H, P, tr, ben=P, method="none", tmin=0, wait=w, outcome="failed",
                           fr=("wait", "schedule_volatility") if late else ("wait",), lens=("land_use",) + (("labor",) if late else ()),
                           ctx=dict(wait=w, purpose=purpose, late="1" if late else ""))
            tt += w
        paid = fare
        if how == "cash":
            if W.cash >= fare:
                W.take("cash", fare)
            else:
                paid = 0.0
        elif fare and W.bank is not None and W.bank >= fare:
            W.take("debit", fare)
        elif fare and W.cash >= fare:
            W.take("cash", fare)
        elif fare:
            paid = 0.0
        sim.emit(tt, "public_service_encounter", "transportation", "transit_ride", P, H, tr, P, ben=P, method=(how if paid else "none"),
                 gross=TRANSIT_COST, user=paid, third=TRANSIT_COST - paid, payer="Medianville Area Transit operating subsidy (local sales tax, state aid, federal formula funds)",
                 fund="mixed", imputed=TRANSIT_COST, tmin=ride, wait=rng.randint(2, 14), miles=round(sim.dist(o_d, d_d), 1), mode="transit",
                 lens=("land_use",), related=rel, ctx=dict(purpose=purpose, fare="%.2f" % paid, reduced="1" if reduced and paid else "", free="1" if not fare else ""))
    push(q, t, run)


def errand(sim, q, P, H, org, cat, kind, amt, dur, prefs, taxable=True, wait=(0, 6), ctx=None, W=None, fr=(), lens=(), allow_partial=False,
           fee=None, anchor=None, chained=None, rtype="purchase", third=0.0, payer="", fund="", defer=0.0, zero="none", ben="", after=None,
           before=None, quiet_fail=.65, imputed=0.0, pre=None):
    rng = sim.rng
    if org is None or org.open is None:
        return None
    o_d = anchor or H.district
    ch = (rng.random() < .5) if chained is None else chained
    miles, mode, mins, tfr = sim.trip(P, H, o_d, org.district, ch)
    op, cl = org.open, org.close
    if after:
        op = max(op, after)
    if before:
        cl = min(cl, before)
    buf = min(mins, 45)
    t = sim.slot(P, dur + buf, prefs, op, cl)
    if t is None:
        return None
    t += buf // 2
    w = rng.randint(*wait)
    if mode == "transit":
        bus_ride(sim, q, P, H, max(0, t - buf // 2 - 4), o_d, org.district, "errand")
    WW = W or P.wallet

    def run(t=t):
        rel = pre(t) if pre else None
        sim.pay(t, P, H, WW, org, cat, kind, amt, taxable=taxable, ctx=ctx, tmin=dur, wait=w, miles=miles, mode=mode, fr=tuple(fr) + tuple(tfr),
                lens=lens, allow_partial=allow_partial, fee=fee, rtype=rtype, third=third, payer=payer, fund=fund, defer=defer, zero=zero, ben=ben,
                quiet_fail=quiet_fail, imputed=imputed, related=rel)
    push(q, t, run)
    return t


def online(sim, q, P, H, org, cat, kind, amt, taxable=True, ctx=None, dur=(3, 9), prefs=ANY, fee=None, W=None, lens=(), fr=(), rtype="purchase",
           channel="online", bnpl=False):
    rng = sim.rng
    WW = W or P.wallet
    if WW.bank is None and not WW.cc_limit and WW.prepaid is None:
        return None
    d = rng.randint(*dur)
    t = sim.slot_soft(P, d, prefs)
    F = list(fr)
    if H.internet == "no":
        F.append("digital_barrier")

    def run(t=t):
        if bnpl:
            tax = round(amt * SALES_TAX, 2) if taxable else 0.0
            tot = amt + tax
            first = round(tot / 4, 2)
            m = "debit" if WW.bank is not None else "prepaid"
            if WW.avail(m) >= first:
                WW.take(m, first)
                c = dict(ctx or {})
                c.update(org=org.name, amt="%.2f" % tot, first="%.2f" % first)
                sim.emit(t, rtype, cat, kind, P, H, P, org, channel=channel, method="bnpl", gross=tot, user=first, third=tot - first,
                         payer="%s (buy-now-pay-later advance, repaid in 3 more installments)" % sim.X["x_bnpl1"].name, fund="private", tax=tax, tmin=d,
                         fr=F, lens=tuple(lens) + ("consumer_finance",), ctx=c)
                return
        sim.pay(t, P, H, WW, None, cat, kind, amt, taxable=taxable, channel=channel, ctx=dict(ctx or {}, org=org.name), tmin=d, fr=F, lens=lens,
                fee=fee, rtype=rtype, to=org)
    push(q, t, run)
    return t


def inc(H, pov, ali, abv):
    return pov if H.alice == "poverty" else ali if H.alice == "alice" else abv


def ln(rng, med, sig, lo, hi):
    return min(hi, max(lo, rng.lognormvariate(math.log(med), sig)))


# kind, category, daily rate per adult, multiplier(P,H), org kinds, amount(rng,P,H), taxable, duration, wait, time prefs, distance scale, P(start from work)
SIMPLE = [
    ("coffee", "food", .070, lambda P, H: (1.5 if P.works else 1) * inc(H, .35, .8, 1.35) * (.5 if H.district in ("D5", "D6") else 1) * (.5 if P.age >= 70 else 1),
     ("coffee", "coffee", "coffee", "gas"), lambda r, P, H: r.uniform(3.25, 9.5), True, (4, 10), (1, 9), MORN + ((810, 960, .3),), 4.0, .5),
    ("fast_food", "food", .19, lambda P, H: (1.25 if P.works else 1) * (1.15 if H.kids else 1) * (.55 if P.age >= 70 else 1) * (.5 if H.district == "D6" else 1) * inc(H, .85, 1.05, 1.0),
     ("fastfood", "fastfood", "food_truck"), lambda r, P, H: r.uniform(18, 44) if (H.kids and r.random() < .35) else r.uniform(7.5, 16.5), True, (8, 22), (2, 12), MEAL, 4.5, .55),
    ("sit_down_restaurant", "food", .050, lambda P, H: inc(H, .3, .7, 1.35) * (1.1 if P.age >= 65 else 1),
     ("restaurant",), lambda r, P, H: r.uniform(15, 31) * r.choice([1, 1, 2, 2, 3]) * 1.19, True, (45, 85), (0, 25), ((690, 810, 1), (1050, 1230, 2)), 6.0, .3),
    ("fine_dining", "discretionary", .0018, lambda P, H: (6 if H.income > 150000 else 1 if H.alice == "above" else .05),
     ("fine_dining",), lambda r, P, H: r.uniform(140, 430), True, (90, 140), (0, 15), ((1050, 1200, 1),), 12.0, 0),
    ("bar_tab", "food", .011, lambda P, H: 0 if P.age < 21 else (1.5 if P.age < 50 else .6),
     ("bar",), lambda r, P, H: r.uniform(12, 52), True, (50, 130), (0, 5), ((1020, 1380, 1),), 5.0, .3),
    ("convenience_store", "food", .045, lambda P, H: 1.0,
     ("gas", "gas", "dollar", "grocery_indep"), lambda r, P, H: r.uniform(2.5, 17), True, (4, 9), (0, 5), ANY, 3.0, .4),
    ("tobacco", "discretionary", .33, lambda P, H: 1.0 if P.smoker else 0,
     ("gas", "tobacco", "dollar"), lambda r, P, H: r.uniform(60, 78) if r.random() < .08 else r.uniform(8.5, 11.5), True, (3, 7), (0, 4), ANY, 3.0, .4),
    ("lottery_ticket", "discretionary", .020, lambda P, H: inc(H, 1.3, 1.2, .8),
     ("gas", "grocery_indep"), lambda r, P, H: float(r.choice([2, 2, 5, 5, 10, 20])), False, (3, 6), (0, 4), ANY, 3.0, .4),
    ("dollar_store", "food", .024, lambda P, H: inc(H, 2.0, 1.5, .5) * (2 if H.district == "D5" else 1),
     ("dollar",), lambda r, P, H: r.uniform(5, 34), True, (10, 25), (0, 8), SHOP, 3.5, .2),
    ("big_box_shopping", "discretionary", .042, lambda P, H: 1.0,
     ("supercenter",), lambda r, P, H: ln(r, 48, .7, 9, 420), True, (20, 50), (1, 12), SHOP, 8.0, .2),
    ("warehouse_club", "food", .007, lambda P, H: inc(H, .1, .5, 1.6),
     ("warehouse_club",), lambda r, P, H: r.uniform(85, 340), True, (35, 65), (2, 15), SHOP, 12.0, .1),
    ("clothing", "discretionary", .013, lambda P, H: inc(H, .5, .9, 1.2),
     ("clothing", "department", "thrift", "supercenter"), lambda r, P, H: r.uniform(18, 170), True, (20, 50), (0, 8), SHOP, 8.0, .2),
    ("electronics", "discretionary", .0035, lambda P, H: inc(H, .5, .9, 1.2),
     ("electronics", "supercenter", "phone_store"), lambda r, P, H: ln(r, 180, .9, 25, 1900), True, (20, 45), (0, 10), SHOP, 10.0, .2),
    ("home_improvement", "housing", .011, lambda P, H: (1.8 if H.tenure != "renter" else .5),
     ("home_center", "hardware", "farm_supply"), lambda r, P, H: ln(r, 42, .9, 6, 800), True, (15, 45), (0, 10), SHOP, 8.0, .2),
    ("furniture", "discretionary", .0013, lambda P, H: inc(H, .5, 1, 1.2),
     ("furniture", "rent_to_own"), lambda r, P, H: r.uniform(280, 2600), True, (35, 70), (0, 10), SHOP, 10.0, .1),
    ("haircut", "discretionary", .010, lambda P, H: inc(H, .6, .9, 1.15),
     ("salon",), lambda r, P, H: r.uniform(18, 95) * 1.18, False, (30, 75), (0, 20), SHOP, 4.5, .3),
    ("nail_salon", "discretionary", .0035, lambda P, H: (1.8 if P.sex == "F" else .2) * inc(H, .5, .9, 1.2),
     ("nail",), lambda r, P, H: r.uniform(30, 85) * 1.18, False, (40, 80), (0, 20), SHOP, 5.0, .2),
    ("entertainment", "discretionary", .007, lambda P, H: inc(H, .5, .9, 1.2) * (1.4 if H.kids else 1),
     ("cinema", "bowling", "trampoline", "museum", "theater"), lambda r, P, H: r.uniform(11, 70), True, (90, 150), (0, 10), ((960, 1260, 1),), 9.0, 0),
    ("hobby_and_gifts", "discretionary", .007, lambda P, H: inc(H, .5, .9, 1.25),
     ("sporting", "bookstore", "bike_shop", "florist"), lambda r, P, H: r.uniform(9, 130), True, (12, 35), (0, 6), SHOP, 8.0, .2),
    ("pet_supplies", "discretionary", .012, lambda P, H: 1.0 if H.pets else 0,
     ("pet_store", "supercenter", "farm_supply"), lambda r, P, H: r.uniform(14, 95), True, (10, 25), (0, 6), SHOP, 7.0, .2),
    ("vet_visit", "discretionary", .0028, lambda P, H: (1.0 if H.pets else 0) * inc(H, .5, .9, 1.2),
     ("vet",), lambda r, P, H: ln(r, 140, .7, 62, 1400), False, (35, 70), (2, 25), OFFICE, 8.0, 0),
    ("liquor_store", "food", .013, lambda P, H: 0 if P.age < 21 else 1,
     ("liquor", "grocery_full"), lambda r, P, H: r.uniform(11, 52), True, (5, 12), (0, 5), ((720, 1290, 1),), 4.0, .3),
    ("car_wash", "transportation", .006, lambda P, H: 1.0 if H.vehicles else 0,
     ("car_wash",), lambda r, P, H: r.uniform(9, 24), False, (10, 20), (0, 10), SHOP, 6.0, .3),
    ("auto_parts", "transportation", .004, lambda P, H: (1.0 if H.vehicles else 0) * inc(H, 1.3, 1.2, .8),
     ("auto_parts",), lambda r, P, H: r.uniform(9, 140), True, (10, 20), (0, 6), SHOP, 6.0, .2),
    ("thrift_store", "discretionary", .005, lambda P, H: inc(H, 1.5, 1.2, .8),
     ("thrift",), lambda r, P, H: r.uniform(4, 38), True, (15, 40), (0, 5), SHOP, 6.0, .2),
    ("over_the_counter_medicine", "health", .011, lambda P, H: 1.0,
     ("pharmacy", "supercenter", "dollar", "grocery_full"), lambda r, P, H: r.uniform(5, 29), True, (6, 15), (0, 6), SHOP, 4.5, .3),
    ("dry_cleaning", "discretionary", .0022, lambda P, H: inc(H, .05, .4, 1.4),
     ("dry_cleaner",), lambda r, P, H: r.uniform(9, 48), False, (4, 9), (0, 4), SHOP, 5.0, .5),
    ("gift_for_family", "giving_faith", .006, lambda P, H: 1.0,
     ("florist", "department", "supercenter", "bookstore", "pharmacy"), lambda r, P, H: r.uniform(15, 120), True, (12, 30), (0, 6), SHOP, 7.0, .3),
    ("jewelry_purchase", "discretionary", .00018, lambda P, H: inc(H, .2, .6, 1.6),
     ("jewelry",), lambda r, P, H: ln(r, 420, 1.0, 90, 6500), True, (25, 55), (0, 5), SHOP, 12.0, 0),
    ("designer_handbag", "discretionary", .00012, lambda P, H: (6 if H.income > 200000 else 1 if H.alice == "above" else 0),
     ("luxury_boutique",), lambda r, P, H: r.uniform(1450, 3900), True, (25, 50), (0, 3), SHOP, 20.0, 0),
    ("golf_round", "discretionary", .0009, lambda P, H: inc(H, 0, .4, 1.5) * (1.6 if P.emp == "retired" else .7),
     ("golf",), lambda r, P, H: r.uniform(34, 62), True, (200, 250), (0, 10), ((480, 780, 1),), 14.0, 0),
]
ONLINE = [
    ("online_shopping_order", "discretionary", .085, lambda P, H: inc(H, .45, .9, 1.25) * (.12 if H.internet == "no" else .75 if H.internet == "mobile_only" else 1) * (.5 if P.age >= 70 else 1),
     ("x_market", "x_market", "x_market", "x_shop2", "x_shop3", "x_shop4"), lambda r, P, H: ln(r, 31, .9, 6, 900), True),
    ("app_or_game_purchase", "discretionary", .028, lambda P, H: (1.4 if P.age < 45 else .5) * (.3 if H.internet == "no" else 1),
     ("x_stream4",), lambda r, P, H: r.choice([.99, 1.99, 2.99, 4.99, 4.99, 9.99, 19.99]), True),
    ("travel_booking", "discretionary", .0016, lambda P, H: inc(H, .2, .7, 1.5),
     ("x_travel", "x_air"), lambda r, P, H: ln(r, 420, .7, 110, 3200), False),
    ("online_wagering_deposit", "discretionary", .006, lambda P, H: (0 if P.age < 21 or P.age > 60 else 1) * (2 if P.sex == "M" else .5),
     ("x_bet",), lambda r, P, H: float(r.choice([10, 20, 25, 50, 100, 200])), False),
]


def gen_shopping(sim, H, q):
    rng, wx = sim.rng, sim.wx
    if H.gq in ("jail", "nursing_home"):
        return
    tm = wx["trips"]
    for P in H.adults:
        W = P.wallet
        if P.inpatient or W is None:
            continue
        gqm = .5 if H.gq else 1.0
        work_d = P.wd if (P.works and not P.wfh and P.wd in TRANSIT_SERVED) else None
        for (kind, cat, rate, mult, kinds, amtf, taxable, dur, wait, prefs, scale, pwork) in SIMPLE:
            pr = rate * tm * gqm * sim.cfg.get("PURCHASE_FREQ", 1.0) * sim.dow_mult
            if rng.random() >= pr * 2.5:
                continue
            if rng.random() >= mult(P, H) / 2.5:
                continue
            anchor = work_d if (work_d and rng.random() < pwork) else None
            org = sim.pick(kinds, anchor or H.district, scale * (1.8 if H.district == "D6" else 1.0))
            if org is None:
                continue
            amt = round(amtf(rng, P, H), 2)
            pf = prefs
            if anchor and P.lunch:
                pf = ((P.lunch[0], P.lunch[1] + 1, 3.0), (P.shift[-1][1], P.shift[-1][1] + 100, 1.5), (max(300, P.shift[0][0] - 50), P.shift[0][0], 1.0))
            d = rng.randint(*dur)
            if anchor and P.lunch and d > 25:
                pf = ((P.shift[-1][1], P.shift[-1][1] + 150, 1.0),)
            ctx = dict(n=len(H.members))
            fee = None
            if kind == "furniture" and org.kind == "rent_to_own":
                continue
            errand(sim, q, P, H, org, cat, kind, amt, d, pf, taxable=taxable, wait=wait, ctx=ctx, anchor=anchor, chained=bool(anchor) or None,
                   allow_partial=kind in ("dollar_store", "convenience_store"), fee=fee)
        # workplace cafeteria / vending
        if P.works and not P.wfh and P.lunch and P.org is not None and P.org.district != "EXT" and rng.random() < .045:
            amt = round(rng.uniform(1.75, 11), 2)
            t = P.lunch[0] + rng.randint(1, 10)
            push(q, t, lambda t=t, P=P, W=W, amt=amt: sim.pay(t, P, H, W, None, "food", "workplace_cafeteria_or_vending", amt, taxable=True,
                                                               ctx=dict(org=P.org.name), tmin=6, to=P.org))
        for (kind, cat, rate, mult, kinds, amtf, taxable) in ONLINE:
            pr = rate * (1.15 if tm < .9 else 1.0) * sim.cfg.get("PURCHASE_FREQ", 1.0) * sim.dow_mult
            if rng.random() >= pr * 2.5 or rng.random() >= mult(P, H) / 2.5:
                continue
            org = sim.X[rng.choice(kinds)]
            amt = round(amtf(rng, P, H), 2)
            use_bnpl = kind == "online_shopping_order" and amt > 60 and P.bnpl and rng.random() < .45
            online(sim, q, P, H, org, cat, kind, amt, taxable=taxable, ctx=dict(), bnpl=use_bnpl,
                   prefs=((420, 540, .6), (690, 790, 1), (1140, 1380, 2.5)))
        # event tickets with service fees
        if rng.random() < .0012 * inc(H, .3, .8, 1.4):
            amt = round(rng.uniform(38, 240), 2)
            online(sim, q, P, H, sim.X["x_tix"], "discretionary", "event_tickets", amt, taxable=False, ctx=dict(),
                   fee=("ticketing_service_fee", round(amt * rng.uniform(.18, .27), 2)))
        # restaurant delivery app
        dl = {"D1": 1, "D2": 1, "D3": 1, "D4": .5}.get(H.district, .04)
        if rng.random() < .019 * dl * wx["delivery"] * (1.6 if P.age < 45 else .6) * inc(H, .5, .9, 1.2) and H.internet != "no":
            sub = round(rng.uniform(16, 44), 2)
            tip = rng.choice([3, 4, 5, 6, 8])
            fees = round(rng.choice([2.99, 3.99, 4.99, 5.99]) + sub * .15, 2)
            org = sim.X[rng.choice(["x_deliv1", "x_deliv2"])]
            rest = sim.pick(("restaurant", "fastfood"), H.district, 4.0)
            sim.delivery_orders.append((rest, sub))
            online(sim, q, P, H, org, "food", "restaurant_delivery_order", sub + tip, taxable=True, ctx=dict(rest=rest.name if rest else "a restaurant", tip=tip),
                   fee=("delivery_and_service_fees", fees), channel="app", prefs=((690, 800, 1), (1050, 1260, 2.5)))
        # ride-hailing
        rs = {"D1": 1.5, "D2": 1.2, "D3": .8, "D4": .5}.get(H.district, .04)
        if rng.random() < .011 * rs * (3 if H.vehicles == 0 else 1) * (1.5 if P.age < 40 else .7):
            amt = round(rng.uniform(11, 36), 2)
            online(sim, q, P, H, sim.X[rng.choice(["x_ride1", "x_ride2"])], "transportation", "ride_hail_trip", amt * 1.15, taxable=False,
                   ctx=dict(), channel="app", dur=(14, 30), prefs=((420, 600, 1), (960, 1410, 2)))


# Rural grocery trips. USDA's Food Access Research Atlas (2019; sources/raw/food_access_atlas): 7.1% of rural residents
# live more than 10 miles from a supermarket and 0.7% more than 20. v1 sent about 30% of rural grocery trips more than 20
# miles, because the rural districts have no supercenter or discount grocer and every household that drew one drove to
# the suburbs and far stores outweighed the one local one. Now, when the kind drawn has no outlet in the household's
# district, 70% shop at a local grocery instead and 30% still make the long stock-up run, and distance counts for more
# (estimates: trips can bypass the nearest store, so they run longer than the atlas's nearest-store distances).
RURAL_GROCERY_SCALE = {"D6": .9, "D5": .5}   # distance multipliers in pick() (v1: 2.2 and 1.3); with them about 5% of
                                             # rural-town and 10% of open-country trips run over 20 miles one way
RURAL_LOCAL_SUB = .7


def gen_food(sim, H, q):
    rng, cal, X, wx = sim.rng, sim.cal, sim.X, sim.wx
    if H.gq:
        if H.gq == "h2a_worker_housing" and cal["dow"] == 5:
            # the grower's van runs crews to a supercenter on Saturday afternoon (H-2A employers must provide transport)
            P = H.head
            org = sim.pick(("supercenter", "grocery_discount", "grocery_indep"), "D5", 4.0)
            errand(sim, q, P, H, org, "food", "grocery_main_trip", round(rng.uniform(45, 115), 2), rng.randint(30, 50), ((840, 1080, 1.0),), taxable=False,
                   ctx=dict(n=1, org=org.name if org else ""), fr=("no_transit",), quiet_fail=.2)
            return
        if H.gq == "college_dorm" and rng.random() < .10:
            P = H.head
            org = sim.pick(("grocery_full", "supercenter", "dollar"), H.district, 4.0)
            errand(sim, q, P, H, org, "food", "grocery_fill_in", round(rng.uniform(6, 34), 2), rng.randint(10, 25), SHOP, taxable=False, ctx=dict(n=1))
        return
    n = len(H.members)
    ad = [p for p in H.adults if not p.inpatient]
    if not ad:
        return
    W0 = H.wallets[0]
    dsince = (cal["dom"] - H.snap_day) if H.snap else 99
    pm = .20 * wx["trips"] * (1.2 if n >= 4 else .75 if n == 1 else 1.0) * sim.dow_mult
    if 0 <= dsince <= 2:
        pm *= 2.1
    if any(p.ss_cohort in cal["ss_cohorts"] for p in H.members if p.ss):
        pm *= 1.5
    if sim.carry is not None and H.snap:
        pm *= sim.carry.snap_pace(H)       # carried runs: SNAP balances run down from the load day (carry.py)
    kindw = {"above": (("grocery_full", .55), ("supercenter", .20), ("warehouse_club", .10), ("grocery_indep", .09), ("grocery_discount", .06)),
             "alice": (("grocery_full", .36), ("supercenter", .25), ("grocery_discount", .20), ("grocery_indep", .12), ("dollar", .05), ("warehouse_club", .02)),
             "poverty": (("grocery_discount", .28), ("supercenter", .25), ("grocery_full", .20), ("grocery_indep", .15), ("dollar", .12))}[H.alice]

    def shopper():
        return rng.choices(ad, [1.5 if not p.works else 1.0 for p in ad])[0]

    def store(scale=6.0):
        k = rng.choices([x[0] for x in kindw], [x[1] for x in kindw])[0]
        if H.district in RURAL_GROCERY_SCALE and not sim.by_kd.get((k, H.district)) and rng.random() < RURAL_LOCAL_SUB:
            k = next((kk for kk in ("grocery_full", "grocery_indep", "grocery_discount", "dollar") if sim.by_kd.get((kk, H.district))), k)
        sc = scale * RURAL_GROCERY_SCALE.get(H.district, 1.0)
        return sim.pick((k,), H.district, sc) or sim.pick(("grocery_full", "supercenter", "grocery_indep", "dollar"), H.district, sc)

    eq = 1 + .6 * (len(H.adults) - 1) + .45 * len(H.kids)
    if rng.random() < pm:
        P = shopper()
        amt = round((40 + 28 * eq) * math.exp(rng.gauss(0, .33)) * inc(H, .78, .95, 1.15) * sim.cfg["GROCERY_PRICE_MULT"], 2)
        r = rng.random()
        if r < .09 * inc(H, .2, .7, 1.4) and H.internet != "no" and (W0.bank is not None or W0.cc_limit):
            org = sim.pick(("grocery_full", "supercenter"), H.district, 6.0)
            t = sim.slot(P, 14, ((960, 1200, 2), (600, 900, 1)), org.open, org.close)
            if t is not None:
                sub = rng.random() < .22

                def run(t=t, P=P, org=org, amt=amt, sub=sub):
                    i, oc, m = sim.pay(t, P, H, W0, org, "food", "grocery_pickup_order", amt, channel="app", ctx=dict(n=n, sub="1" if sub else ""),
                                       tmin=14, wait=rng.randint(2, 12), miles=round(sim.dist(H.district, org.district) * 1.2, 1), mode="car",
                                       fr=(("out_of_stock",) if sub else ()))
                push(q, t, run)
        elif r < .09 * inc(H, .2, .7, 1.4) + .04 and H.district in ("D1", "D2", "D3") and H.internet != "no":
            fee = ("delivery_and_service_fees", round(rng.choice([5.99, 7.99, 9.99]) + amt * .05, 2))
            online(sim, q, P, H, X["x_deliv2"], "food", "grocery_delivery_order", amt + rng.choice([4, 5, 7, 10]), taxable=False, ctx=dict(n=n), fee=fee,
                   channel="app", W=W0, lens=(("disability",) if P.dis != "none" else ()))
        else:
            org = store()
            if org is not None:
                miles, mode, mins, tfr = sim.trip(P, H, H.district, org.district, rng.random() < .35)
                dur = rng.randint(28, 58)
                buf = min(mins, 45)
                t = sim.slot(P, dur + buf, SHOP, org.open, org.close)
                if t is not None:
                    t += buf // 2
                    if mode == "transit":
                        bus_ride(sim, q, P, H, max(0, t - buf // 2 - 4), H.district, org.district, "groceries")
                        bus_ride(sim, q, P, H, min(1430, t + dur + 6), org.district, H.district, "groceries")

                    def run(t=t, P=P, org=org, amt=amt, miles=miles, mode=mode, tfr=tfr, dur=dur):
                        w = rng.randint(1, 14)
                        rel = None
                        ctx = dict(n=n, org=org.name)
                        if H.hid in sim.skimmed and "ebt_snap" in org.acc:
                            rel = sim.emit(t, "failed_attempt", "food", "snap_benefits_stolen", P, H, P, org, method="ebt_snap", gross=amt, tmin=6,
                                           outcome="failed", fr=("scam_attempt", "insufficient_funds"), lens=("consumer_finance", "public_finance"),
                                           ctx=dict(org=org.name, amt="%.0f" % H.snap))
                            sim.skimmed.discard(H.hid)
                            H.snap_bal = 0.0
                        elif rng.random() < .028:
                            item = rng.choice(["eggs", "the store-brand formula", "children's fever reducer", "the sale-price chicken thighs", "whole milk gallons", "the WIC-size cereal", "masa harina", "lactose-free milk"])
                            rel = sim.emit(t, "failed_attempt", "food", "grocery_item_out_of_stock", P, H, P, org, method="none", tmin=4, outcome="failed",
                                           fr=("out_of_stock",), ctx=dict(org=org.name, item=item))
                        snap_part = 0.0
                        if H.snap_bal > 5 and "ebt_snap" in org.acc:
                            snap_part = round(min(H.snap_bal, amt * rng.uniform(.82, .97)), 2)
                            H.snap_bal -= snap_part
                            rel = sim.emit(t, "benefit_redemption", "food", "grocery_snap_purchase", P, H, P, org, method="ebt_snap", gross=snap_part,
                                           third=snap_part, payer="SNAP EBT balance (issued earlier)", fund="federal", tmin=dur, wait=w, miles=miles, mode=mode,
                                           fr=tfr, related=rel, ctx=dict(n=n, org=org.name, bal="%.2f" % H.snap_bal))
                            org.rev += snap_part
                            rest = round(amt - snap_part, 2)
                            if rest > 1.5:
                                sim.pay(t + 1, P, H, W0, org, "food", "grocery_main_trip", rest, ctx=dict(ctx, split="1"), allow_partial=True, related=rel,
                                        quiet_fail=0.0)
                        else:
                            sim.pay(t, P, H, W0, org, "food", "grocery_main_trip", amt, ctx=ctx, tmin=dur, wait=w, miles=miles, mode=mode, fr=tfr,
                                    allow_partial=True, related=rel, quiet_fail=.3)
                    push(q, t, run)
    if rng.random() < .09 * wx["trips"]:
        P = shopper()
        org = sim.pick(("grocery_full", "grocery_indep", "dollar", "supercenter", "gas", "grocery_discount"), H.district, 3.5 * (2 if H.district == "D6" else 1))
        amt = round(rng.uniform(6, 38), 2)
        if H.snap_bal > amt and org is not None and "ebt_snap" in org.acc and rng.random() < .7:
            miles, mode, mins, tfr = sim.trip(P, H, H.district, org.district, True)
            t = sim.slot(P, 14 + min(mins, 30), SHOP, org.open, org.close)
            if t is not None:
                def run(t=t, P=P, org=org, amt=amt, miles=miles, mode=mode, tfr=tfr):
                    H.snap_bal -= amt
                    org.rev += amt
                    sim.emit(t, "benefit_redemption", "food", "grocery_snap_purchase", P, H, P, org, method="ebt_snap", gross=amt, third=amt,
                             payer="SNAP EBT balance (issued earlier)", fund="federal", tmin=14, wait=rng.randint(0, 8), miles=miles, mode=mode, fr=tfr,
                             ctx=dict(n=n, org=org.name, bal="%.2f" % H.snap_bal))
                push(q, t, run)
        else:
            errand(sim, q, P, H, org, "food", "grocery_fill_in", amt, rng.randint(9, 22), SHOP, taxable=False, wait=(0, 8), ctx=dict(n=n), W=W0,
                   chained=True, allow_partial=True)
    # WIC
    if H.wic and H.wic_bal > 10 and rng.random() < (.30 if H.wic_day == cal["dom"] else .11):
        P = shopper()
        org = sim.pick(("grocery_full", "supercenter", "grocery_indep"), H.district, 5.0)
        if org is not None and "wic" in org.acc:
            amt = round(min(H.wic_bal, rng.uniform(14, 52)), 2)
            miles, mode, mins, tfr = sim.trip(P, H, H.district, org.district, True)
            t = sim.slot(P, 25 + min(mins, 30), SHOP, org.open, org.close)
            if t is not None:
                def run(t=t, P=P, org=org, amt=amt, miles=miles, mode=mode, tfr=tfr):
                    r = rng.random()
                    rel = None
                    if r < .09:
                        rel = sim.emit(t, "failed_attempt", "food", "wic_item_rejected_at_register", P, H, P, org, method="wic", gross=amt, tmin=7,
                                       wait=rng.randint(3, 10), outcome="failed", fr=("eligibility_confusion",) if r < .06 else ("out_of_stock",),
                                       lens=("family_care", "public_finance"),
                                       ctx=dict(org=org.name, item=rng.choice(["the 12.4-oz formula can", "a 16-oz bread loaf", "the organic milk", "a cereal box one ounce too big", "the only yogurt size on the shelf"])))
                    H.wic_bal -= amt
                    org.rev += amt
                    sim.emit(t + (5 if rel is not None else 0), "benefit_redemption", "food", "grocery_wic_purchase", P, H, P, org, method="wic", gross=amt,
                             third=amt, payer="WIC (USDA)", fund="federal", tmin=25, wait=rng.randint(1, 10), miles=miles, mode=mode, fr=tfr,
                             lens=("family_care",), related=rel, ctx=dict(org=org.name))
                push(q, t, run)
    # Wednesday farmers market (in season indoors)
    fm = sim.by_kind.get("farmers_market")
    if fm and fm[0].open is not None and H.district in ("D1", "D2", "D3") and rng.random() < .0045 * inc(H, .6, .9, 1.2):
        P = shopper()
        org = fm[0]
        amt = round(rng.uniform(11, 46), 2)
        if H.snap_bal > 10 and rng.random() < .8:
            use = min(20.0, H.snap_bal)
            miles, mode, mins, tfr = sim.trip(P, H, H.district, org.district)
            t = sim.slot(P, 35 + min(mins, 30), ((840, 1080, 1),), org.open, org.close)
            if t is not None:
                def run(t=t, P=P, use=use, miles=miles, mode=mode, tfr=tfr):
                    H.snap_bal -= use
                    i = sim.emit(t, "benefit_redemption", "food", "farmers_market_snap_tokens", P, H, P, org, method="ebt_snap", gross=use, third=use,
                                 payer="SNAP EBT balance (issued earlier)", fund="federal", tmin=35, wait=rng.randint(2, 9), miles=miles, mode=mode, fr=tfr,
                                 ctx=dict(amt="%.0f" % use))
                    sim.emit(t + 1, "benefit_redemption", "food", "farmers_market_match", P, H, sim.one("nonprofit"), org, ben=P, method="none", gross=use,
                             third=use, payer="Market match program (United Fund grant)", fund="philanthropic", related=i, ctx=dict(amt="%.0f" % use))
                push(q, t, run)
        else:
            errand(sim, q, P, H, org, "food", "farmers_market_purchase", amt, rng.randint(25, 45), ((840, 1080, 1),), taxable=False, wait=(0, 6), ctx=dict(), W=W0)
    # food pantry (Wednesday distribution)
    pp = inc(H, .034, .011, .0008) * (1.6 if H.fragile else .7)
    if rng.random() < pp:
        P = shopper()
        org = sim.pick(("food_pantry",), H.district, 9.0)
        if org is not None:
            miles, mode, mins, tfr = sim.trip(P, H, H.district, org.district)
            w = rng.randint(20, 75)
            t = sim.slot(P, w + 15 + min(mins, 40), DAY, org.open, org.close)
            if t is not None:
                val = round(rng.uniform(48, 92), 2)

                def run(t=t, P=P, org=org, miles=miles, mode=mode, tfr=tfr, w=w, val=val):
                    sim.emit(t, "public_service_encounter", "food", "food_pantry_visit", P, H, org, P, ben=P, method="none", gross=val, third=val,
                             payer="Donated and federal commodity food (Three Rivers Food Bank, TEFAP)", fund="philanthropic", imputed=val, tmin=w + 15, wait=w,
                             miles=miles, mode=mode, fr=tfr, ctx=dict(org=org.name, n=n, wait=w))
                push(q, t, run)
    # laundromat for homes without a washer
    if not H.washer and rng.random() < .13:
        P = shopper()
        org = sim.pick(("laundromat",), H.district, 3.0)
        errand(sim, q, P, H, org, "housing", "laundromat", round(rng.uniform(6, 19), 2), rng.randint(95, 140), ((420, 1260, 1),), taxable=False,
               wait=(0, 15), ctx=dict(n=n), W=W0)
    # senior meals
    for p in H.members:
        if p.age >= 62 and not p.inpatient:
            homebound = p.dis in ("ambulatory", "self_care", "independent_living", "multiple") and p.age >= 68
            sc = sim.one("senior_center")
            if homebound and rng.random() < .11:
                t = rng.randint(630, 760)
                don = rng.choice([0, 0, 0, 1, 2, 3])
                push(q, t, lambda t=t, p=p, don=don: (p.wallet.take("cash", don) if p.wallet.cash >= don else None,
                                                      sim.emit(t, "public_service_encounter", "food", "home_delivered_meal", p, H, sc, p, ben=p, method="cash" if don and p.wallet.cash >= 0 else "none",
                                                               gross=14.2, user=don, third=14.2 - don, payer="Older Americans Act nutrition program and county funds", fund="mixed",
                                                               imputed=14.2, tmin=3, ctx=dict(don=don))))
            elif not homebound and rng.random() < .006 and H.district in ("D1", "D4", "D5"):
                t = sim.slot(p, 75, ((660, 780, 1),))
                if t is not None:
                    don = rng.choice([0, 1, 2, 3, 3])
                    push(q, t, lambda t=t, p=p, don=don: (p.wallet.take("cash", don) if p.wallet.cash >= don else None,
                                                          sim.emit(t, "public_service_encounter", "food", "senior_center_meal", p, H, sc, p, ben=p, method="cash" if don else "none",
                                                                   gross=12.6, user=don, third=12.6 - don, payer="Older Americans Act nutrition program and county funds", fund="mixed",
                                                                   imputed=12.6, tmin=75, miles=round(sim.dist(H.district, H.district) * 2, 1), mode="car" if H.vehicles else "ride_from_family_or_friend", ctx=dict(don=don))))


def gen_transport(sim, H, q):
    rng, cal, X, wx = sim.rng, sim.cal, sim.X, sim.wx
    if H.gq in ("jail", "nursing_home", "assisted_living"):
        return
    # commute rides for transit commuters
    for p in H.members:
        if p.works and p.mode == "transit" and p.shift and not p.wfh and p.wd in TRANSIT_SERVED:
            bus_ride(sim, q, p, H, max(0, p.shift[0][0] - p.cm), H.district, p.wd, "commute")
            bus_ride(sim, q, p, H, min(1436, p.shift[-1][1] + 4), p.wd, H.district, "commute")
            if p.pid not in sim.passholders and cal["early_month"] and rng.random() < .05:
                amt = 28.0 if (p.age >= 65 or p.dis != "none") else 56.0
                online(sim, q, p, H, sim.one("transit"), "transportation", "transit_pass_purchase", amt, taxable=False, ctx=dict(), channel="app")
        elif p.student == "college" and H.vehicles == 0 and H.district in ("D1", "D2") and rng.random() < .5 and p.free:
            bus_ride(sim, q, p, H, rng.randint(450, 600), H.district, "D2", "class")
            bus_ride(sim, q, p, H, rng.randint(840, 1080), "D2", H.district, "class")
        # parking downtown
        if p.works and p.wd == "D1" and p.mode == "car" and not p.wfh and p.shift and rng.random() < .10:
            amt = round(rng.choice([7, 8, 9, 11, 13]) if rng.random() < .6 else rng.uniform(1.5, 4.5), 2)
            t = max(0, p.shift[0][0] - 6)
            push(q, t, lambda t=t, p=p, amt=amt: sim.pay(t, p, H, p.wallet, sim.one("parking"), "transportation", "parking_fee", amt, ctx=dict(), tmin=3,
                                                          channel="app" if rng.random() < .4 else "in_person"))
    if not H.vehicles:
        return
    drivers = [p for p in H.members if p.age >= 16 and not p.inpatient and not (p.age >= 86 and p.dis != "none")]
    if not drivers:
        return
    W0 = H.wallets[0]
    for v in range(H.vehicles):
        P = rng.choice(drivers)
        W = P.wallet
        if v < H.ev:
            if rng.random() < .03:
                online(sim, q, P, H, sim.one("ev_charging"), "transportation", "ev_public_charging", round(rng.uniform(9, 29), 2), taxable=False, ctx=dict(),
                       channel="app", dur=(18, 40), prefs=SHOP)
            continue
        if rng.random() < .115 * (1.0 if wx["trips"] > .9 else .8):
            price = sim.cfg["GAS_PRICE"] + rng.uniform(-.06, .12)
            gal = rng.uniform(7, 15.5)
            tight = W.liquid() < 70 or (W.bank is None)
            amt = round(gal * price, 2) if not tight else float(rng.choice([10, 15, 20, 20, 25]))
            org = sim.pick(("gas",), P.wd if (P.works and P.wd in TRANSIT_SERVED and rng.random() < .4) else H.district, 3.5)
            if org is None:
                continue
            t = sim.slot(P, 8, GAS, org.open, org.close)
            if t is None:
                continue

            def run(t=t, P=P, W=W, org=org, amt=amt, price=price, tight=tight):
                ctx = dict(org=org.name, gal="%.1f" % (amt / price), price="%.2f" % price)
                if tight and W.cash >= amt:
                    W.take("cash", amt)
                    org.rev += amt
                    org.csh += amt
                    org.ntx += 1
                    sim.emit(t, "purchase", "transportation", "gas_fill_up", P, H, P, org, method="cash", gross=amt, user=amt, tmin=9, wait=rng.randint(0, 5),
                             miles=round(rng.uniform(.3, 2.5), 1), mode="car", ctx=dict(ctx, inside="1"))
                    return
                if W.bank is not None and not W.cc_limit and W.bank < 125 and W.bank >= amt and rng.random() < .5:
                    i = sim.emit(t, "failed_attempt", "transportation", "gas_fill_up", P, H, P, org, method="debit", gross=amt, tmin=3, outcome="declined",
                                 fr=("pending_hold",), ctx=dict(ctx, reason="the pump wanted a $125 hold the account could not cover", method="debit"))
                    W.take("debit", amt)
                    org.rev += amt
                    org.dc += amt
                    sim.emit(t + 3, "purchase", "transportation", "gas_fill_up", P, H, P, org, method="debit", gross=amt, user=amt, tmin=8, wait=rng.randint(1, 6),
                             mode="car", related=i, ctx=dict(ctx, inside="1", retry="debit"))
                    return
                sim.pay(t, P, H, W, org, "transportation", "gas_fill_up", amt, ctx=ctx, tmin=6, miles=round(rng.uniform(.3, 2.5), 1), mode="car",
                        allow_partial=True, quiet_fail=.2)
            push(q, t, run)
        # repairs and upkeep
        r = rng.random()
        if r < .0035:
            org = sim.pick(("auto_repair",), H.district, 6.0)
            amt = round(min(3200, max(140, rng.lognormvariate(math.log(430), .75))), 2)
            cant = W.liquid() + (W.cc_limit - W.cc_bal) < amt

            def pre(t, P=P, org=org, amt=amt, cant=cant):
                if cant:
                    return sim.emit(t, "non_monetary_job", "transportation", "repair_estimate_too_high", P, H, P, org, tmin=10, outcome="partial",
                                    fr=("insufficient_funds",), lens=("consumer_finance",), ctx=dict(org=org.name, amt="%.0f" % amt))
                return None
            errand(sim, q, P, H, org, "transportation", "car_repair", amt if not cant else round(rng.uniform(85, 160), 2), rng.randint(15, 30), OFFICE,
                   taxable=False, wait=(0, 20), ctx=dict(est="%.0f" % amt, cant="1" if cant else ""), W=W, pre=pre, quiet_fail=0.0)
        elif r < .0065:
            errand(sim, q, P, H, sim.pick(("oil_change", "auto_repair"), H.district, 6.0), "transportation", "oil_change", round(rng.uniform(62, 118), 2),
                   rng.randint(25, 50), SHOP, taxable=False, wait=(0, 25), ctx=dict(), W=W)
        elif r < .0074:
            low = H.alice != "above" and rng.random() < .5
            amt = round(rng.uniform(55, 95) * rng.choice([1, 2]), 2) if low else round(rng.uniform(420, 980), 2)
            fee = ("lease_to_own_financing_fee", round(amt * .18, 2)) if (not low and H.alice != "above" and rng.random() < .3) else None
            errand(sim, q, P, H, sim.pick(("tire",), H.district, 8.0), "transportation", "tires", amt, rng.randint(45, 90), SHOP, taxable=True, wait=(5, 40),
                   ctx=dict(used="1" if low else ""), W=W, fee=fee)
        elif r < .0074 + 1 / 365.0:
            fee_amt = float(rng.choice([48, 62, 85, 85, 110, 135]))
            if H.internet != "no" and rng.random() < .62 and (W.bank is not None or W.cc_limit):
                online(sim, q, P, H, sim.one("county"), "civic_legal", "vehicle_registration_renewal", fee_amt, taxable=False, ctx=dict(), fee=("online_convenience_fee", 3.0), W=W)
            else:
                org = sim.pick(("county",), H.district, 14.0)
                errand(sim, q, P, H, org, "civic_legal", "vehicle_registration_renewal", fee_amt, rng.randint(12, 25), OFFICE, taxable=False, wait=(5, 55),
                       ctx=dict(), W=W)
        if rng.random() < .00034 * wx["car_fail"]:
            sim.car_fail(H, P, q)
    if "toll_user" in H.flags:
        for p in H.members:
            if p.works and p.mode == "car" and p.wd in ("D1", "D2") and not p.wfh and p.shift and rng.random() < .55:
                toll = rng.choice([1.75, 2.25, 2.75, 3.5])
                plate = rng.random() < .18
                for tt in (max(0, p.shift[0][0] - p.cm // 2), min(1438, p.shift[-1][1] + p.cm // 2)):
                    def run(t=tt, p=p, toll=toll, plate=plate):
                        W = p.wallet
                        f = 2.0 if plate else 0.0
                        if plate:
                            sim.emit(t, "bill_payment", "transportation", "toll", p, H, p, sim.one("tollway"), channel="automatic", method="none", gross=toll,
                                     user=0, fee_type="pay_by_plate_admin_fee", fee=f, outcome="partial", ctx=dict(amt="%.2f" % toll, plate="1"))
                        else:
                            sim.emit(t, "bill_payment", "transportation", "toll", p, H, p, sim.one("tollway"), channel="automatic", method="prepaid", gross=toll,
                                     user=toll, ctx=dict(amt="%.2f" % toll))
                            sim.toll_draw[W] = sim.toll_draw.get(W, 0) + toll
                    push(q, tt, run)
                if not plate and rng.random() < .09:
                    online(sim, q, p, H, sim.one("tollway"), "transportation", "toll_account_reload", 25.0, taxable=False, ctx=dict(), channel="automatic", dur=(0, 0))


# ------------------------------------------------------------------------------------------------- health
PAYF = {"medicare": .80, "medicare_advantage": .82, "medicare_medicaid_dual": .78, "medicaid": .60, "uninsured": 1.25, "va": .85, "military": .85}
PRIV_CP = {"primary": 30, "specialist": 60, "urgent": 70, "ed": 300, "therapy": 30, "pt": 40, "lab": 0, "telehealth": 20, "vision": 15, "dialysis": 0, "home": 0}
MA_CP = {"primary": 5, "specialist": 40, "urgent": 45, "ed": 125, "therapy": 30, "pt": 30, "lab": 0, "telehealth": 0, "vision": 10, "dialysis": 0, "home": 0}


def cover(sim, P, allowed, svc):
    """Split an allowed amount into (paid now by patient, third-party payment, payer, funding level, billed to patient later)."""
    rng, cov = sim.rng, P.cov
    if cov == "medicare_medicaid_dual":
        return 0.0, allowed, "Medicare and Medicaid (dual eligible)", "mixed", 0.0
    if cov == "medicaid":
        cp = float(rng.choice([0, 0, 0, 1, 3, 4])) if (P.age >= 21 and svc in ("primary", "specialist", "urgent")) else 0.0
        return cp, allowed - cp, "Medicaid (Arbor Community Care)", "mixed", 0.0
    if cov == "medicare":
        if svc == "home":
            return 0.0, allowed, "Medicare (home health benefit)", "federal", 0.0
        resp = .2 * allowed
        if rng.random() < .35:
            resp = min(allowed, rng.uniform(40, PART_B_DEDUCTIBLE) + .2 * max(0, allowed - 150))
        if P.medigap:
            return 0.0, allowed, "Medicare Part B plus Medigap", "federal", 0.0
        return 0.0, allowed - resp, "Medicare Part B", "federal", round(resp, 2)
    if cov == "medicare_advantage":
        cp = MA_CP.get(svc, 20)
        if svc == "dialysis":
            cp = .2 * allowed
        cp = min(cp, allowed)
        return float(cp), allowed - cp, "Medicare Advantage (Arbor Health Plan)", "federal", 0.0
    if cov in ("employer", "marketplace", "other_private"):
        payer = "Northlight Health Insurance" if (int(P.hh.hid[1:]) % 2) else "Arbor Health Plan"
        if P.plan == "hdhp" and rng.random() < .8:
            if rng.random() < .55:
                return allowed, 0.0, payer + " (deductible not met)", "private", 0.0
            return 0.0, 0.0, payer + " (deductible not met)", "private", allowed
        cp = min(float(PRIV_CP.get(svc, 30)), allowed)
        if svc in ("lab", "dialysis"):
            cp = round(.2 * allowed, 2)
        return cp, allowed - cp, payer, "private", 0.0
    if cov == "military":
        cp = min(float(rng.choice([0, 0, 26, 38])), allowed)
        return cp, allowed - cp, "TRICARE", "federal", 0.0
    if cov == "va":
        return 0.0, allowed, "VA health care", "federal", 0.0
    now = min(allowed, float(rng.choice([40, 60, 80, 100, 150]))) if svc != "ed" else 0.0
    return now, 0.0, "", "", round(allowed - now, 2)


def visit(sim, q, P, H, kinds, svc, kind, base, dur, wait, prefs=OFFICE, tele=False, scale=9.0, ctx=None, org=None, lens=()):
    rng = sim.rng
    cov = P.cov
    if org is None:
        if svc in ("primary", "specialist") and cov == "va":
            org = sim.one("va_clinic")
            kind = "va_clinic_visit"
        elif svc == "primary" and rng.random() < {"uninsured": .5, "medicaid": .32, "medicare_medicaid_dual": .2}.get(cov, .04):
            org = sim.pick(("fqhc",), H.district, 12.0)
            kind = "community_health_center_visit"
        else:
            org = sim.pick(kinds, H.district, scale * (1.6 if H.district in ("D5", "D6") else 1.0),
                           who="child" if P.age < 18 else ("adult_f" if P.sex == "F" else "adult_m"))
    if org is None or org.open is None:
        return
    if svc in ("primary", "specialist"):
        # MEPS 2024 office-based visits (sources/raw/meps/h254g): median $146, mean $308, so a long tail of visits with
        # tests and procedures; lognormal with sigma 1.2 keeps v1's median and gives about twice it as the mean
        allowed = round(base * PAYF.get(cov, 1.15) * min(25.0, max(.45, rng.lognormvariate(0.0, 1.2))), 2)
    else:
        allowed = round(base * PAYF.get(cov, 1.15) * rng.uniform(.85, 1.2), 2)
    now, third, payer, fund, later = cover(sim, P, allowed, svc)
    why_later = "the Part B deductible and 20% coinsurance" if (later and payer == "Medicare Part B") else ""
    if org.kind == "fqhc" and cov == "uninsured":
        now = float(rng.choice([25, 30, 40, 45]))
        third, payer, fund, later = allowed - now, "Health center sliding-fee subsidy (federal health center grant)", "federal", 0.0
    # who has to be there
    comp = None
    if P.age < 16 or (P.cared_by and P.dis in ("self_care", "multiple", "cognitive", "independent_living")):
        cands = [c for c in (P.cared_by or []) if c.hh is H or True] or [a for a in H.adults if a is not P]
        cands = cands or [a for a in H.adults if a is not P]
        comp = cands[0] if cands else None
        if P.age < 16 and comp is None:
            return
    actor = comp if (comp is not None and P.age < 16) else P
    sched = comp if comp is not None else P
    c = dict(ctx or {})
    c.update(org=org.name, who=("my child" if P.age < 16 else "me"), age=P.age, later_why=why_later)
    payee_w = (comp.wallet if comp is not None and P.age < 16 else P.wallet)
    if tele:
        t = sim.slot(sched, dur, ((480, 1140, 1),))
        if t is None:
            return
        push(q, t, lambda t=t: sim.pay(t, actor, H, payee_w, org, "health", kind, allowed, channel="app", ctx=c, tmin=dur, wait=rng.randint(0, 12),
                                        rtype="insurance_claim" if payer else "purchase", third=third, payer=payer, fund=fund, defer=later, zero="insurance",
                                        ben=P, fr=(("digital_barrier",) if H.internet != "yes" else ()), lens=lens, quiet_fail=0.0))
        return
    miles, mode, mins, tfr = sim.trip(sched, H, H.district, org.district)
    buf = min(mins, 50)
    w = rng.randint(*wait)
    t = sim.slot(sched, dur + w + buf, prefs, org.open, org.close)
    if t is None:
        if rng.random() < .3:
            sim.emit(rng.randint(480, 1000), "non_monetary_job", "health", "appointment_rescheduled_no_free_time", actor, H, actor, org, ben=P, channel="phone",
                     tmin=rng.randint(6, 18), wait=rng.randint(2, 12), outcome="rescheduled",
                     fr=("hours_mismatch", "caregiving_conflict") if comp is not None else ("hours_mismatch", "schedule_volatility"), lens=lens, ctx=c)
        return
    t += buf // 2
    F = list(tfr)
    if H.lep and rng.random() < .35:
        F.append("language")
    if P.dis in ("ambulatory", "multiple") and rng.random() < .12:
        F.append("disability_access")
    if mode == "transit":
        bus_ride(sim, q, sched, H, max(0, t - buf // 2 - 4), H.district, org.district, "medical appointment")

    def run(t=t):
        i, oc, m = sim.pay(t, actor, H, payee_w, org, "health", kind, allowed, ctx=c, tmin=dur + w, wait=w, miles=miles, mode=mode, fr=F,
                           rtype="insurance_claim" if payer else "purchase", third=third, payer=payer, fund=fund, defer=later, zero="insurance", ben=P,
                           lens=lens, quiet_fail=0.0)
        if comp is not None and comp is not actor and i is not None:
            sim.emit(t, "non_monetary_job", "care_and_household", "escort_to_appointment", comp, comp.hh, comp, P, ben=P, tmin=dur + w + 2 * buf, wait=w,
                     miles=miles, mode=mode, lens=("family_care",), related=i, ctx=dict(org=org.name, rel=P.rel))
    push(q, t, run)


def rx_pickup(sim, q, P, H, nfill=None, after=None):
    rng, X = sim.rng, sim.X
    cov = P.cov
    nfill = nfill or rng.choices([1, 2, 3], [.6, .28, .12])[0]
    actor = P
    if P.age < 16 or (P.dis in ("self_care", "multiple") and P.cared_by):
        actor = (P.cared_by[0] if P.cared_by else None) or next((a for a in H.adults if a is not P), None)
        if actor is None:
            return
    mail = rng.random() < (.20 if P.age >= 65 else .10) and after is None
    org = X["x_rxmail"] if mail else sim.pick(("pharmacy",), H.district, 5.0 * (2.2 if H.district == "D6" else 1))
    if org is None or org.open is None:
        return
    fills = []
    for _ in range(nfill):
        # MEPS 2024 prescribed medicines (h254a): median payment per fill $15, mean $233, so a few very costly fills.
        # 2% specialty (median $5,000), 10% other brand, 88% generic; v1 had 12% brand capped at $1,600 and no specialty.
        r = rng.random()
        specialty, brand = r < .02, r < .12
        if specialty:
            cash = round(min(40000, max(900, rng.lognormvariate(math.log(5000), .9))), 2)
        else:
            cash = round(min(5000 if brand else 400, max(4, rng.lognormvariate(math.log(520 if brand else 20), .8))), 2)
        neg = cash * (.82 if brand else .45)
        if cov in ("medicaid",):
            cp = float(rng.choice([0, 0, 1, 3]))
            third, payer, fund = neg - cp, "Medicaid pharmacy benefit", "mixed"
        elif cov == "medicare_medicaid_dual":
            cp = float(rng.choice([0, 1.6, 5.1, 5.1, 12.65])) if brand else float(rng.choice([0, 1.6, 1.6, 5.1]))
            third, payer, fund = neg - cp, "Medicare Part D with low-income subsidy", "federal"
        elif cov in ("medicare", "medicare_advantage"):
            cp = round(.25 * neg, 2) if brand else float(rng.choice([0, 0, 2, 5, 8, 12]))
            if brand and rng.random() < .15:
                cp = 35.0
            if specialty:   # coinsurance runs into the Part D out-of-pocket cap within a fill or two
                cp = round(min(cp, rng.uniform(150, PART_D_OOP_CAP)), 2)
            third, payer, fund = neg - cp, "Medicare Part D plan", "federal"
        elif cov in ("employer", "marketplace", "other_private", "military"):
            # High-deductible plans: the full price until the deductible is met (capped at what is left of it). v1 charged full
            # price on 75% of fills; 45% brings fills with over $250 to pay near MEPS 2024 (0.84% of purchased fills).
            if P.plan == "hdhp" and rng.random() < .45:
                cp = round(min(neg, rng.uniform(100, 2500)), 2)
            elif specialty:   # specialty-tier coinsurance with a per-fill cap; most commercial patients use a manufacturer copay card
                cp = float(rng.choice([0, 5, 10])) if rng.random() < .55 else round(min(.25 * neg, rng.uniform(150, 1000)), 2)
            else:
                cp = float(rng.choice([40, 50, 60, 90])) if brand else float(rng.choice([0, 5, 10, 10, 15]))
            cp = min(cp, neg)
            third, payer, fund = neg - cp, ("TRICARE pharmacy" if cov == "military" else "Commercial pharmacy benefit"), ("federal" if cov == "military" else "private")
        elif cov == "va":
            cp = float(rng.choice([0, 5, 8, 11]))
            third, payer, fund = neg - cp, "VA pharmacy", "federal"
        else:
            disc = rng.random() < (.4 if brand else .55)   # v1 gave brand drugs no discount; manufacturer and discount-card programs
            cp = round(cash * ((.5 if brand else .38) if disc else 1.0), 2)
            third, payer, fund = 0.0, ("pharmacy discount card (no payer)" if disc else ""), ""
        fills.append((brand, cash, round(max(cp, 0), 2), round(max(third, 0), 2), payer, fund))

    # v2 phase 5: the record's gross is what the fill was charged (the plan's price, or what an uninsured buyer paid), so
    # gross = plan + patient on every claim; the cash price is named in the narrative. v1 showed the cash price as gross.
    def priced(cp, third, payer):
        if third:
            return "the plan's price was $%.2f and the copay $%.2f" % (cp + third, cp)
        if payer:
            return "a discount card brought it down to $%.2f" % cp
        return "paid the cash price"
    W = actor.wallet
    if mail:
        t = rng.randint(120, 480)

        def runm(t=t):
            for brand, cash, cp, third, payer, fund in fills:
                i, oc, m = sim.pay(t, actor, H, W, None, "health", "prescription_mail_order", cp + third, channel="automatic",
                                   ctx=dict(org=org.name, cash="%.2f" % cash, cp="%.2f" % cp, brand="brand" if brand else "generic",
                                            priced=priced(cp, third, payer)),
                                   rtype="insurance_claim" if third else "purchase", third=third, payer=payer, fund=fund, zero="insurance",
                                   ben=P, to=org, quiet_fail=0.0)
        push(q, t, runm)
        return
    miles, mode, mins, tfr = sim.trip(actor, H, H.district, org.district, rng.random() < .5)
    lunchgap = "closes 13:00" in org.notes
    t = sim.slot(actor, 12 + min(mins, 40), SHOP if after is None else ((after, 1260, 1),), org.open, org.close)
    if t is None:
        return
    t += min(mins, 40) // 2

    def run(t=t):
        w = rng.randint(0, 22)
        F = list(tfr)
        if lunchgap and 780 <= t <= 810:
            i = sim.emit(t, "failed_attempt", "health", "prescription_pickup", actor, H, actor, org, ben=P, tmin=4, miles=miles, mode=mode, outcome="rescheduled",
                         fr=F + ["hours_mismatch", "repeat_trip"], ctx=dict(org=org.name, reason="the pharmacy counter was closed for lunch"))
            return
        prev = None
        for k, (brand, cash, cp, third, payer, fund) in enumerate(fills):
            c = dict(org=org.name, cash="%.2f" % cash, cp="%.2f" % cp, brand="brand" if brand else "generic", who=("my child's" if P.age < 16 else "my"),
                     priced=priced(cp, third, payer))
            r = rng.random()
            if r < .055:
                why = rng.choice(["it was not ready yet", "it was not ready yet", "the refill needed the doctor's approval", "the insurer wanted a prior authorization"]) if not brand or r < .03 else "the insurer wanted a prior authorization"
                tag = "wait" if "ready" in why else "paperwork"
                prev = sim.emit(t, "failed_attempt", "health", "prescription_pickup", actor, H, actor, org, ben=P, gross=cash, tmin=8, wait=w, miles=miles if k == 0 else 0,
                                mode=mode, outcome="rescheduled", fr=F + [tag, "repeat_trip"], lens=("health_cost",), ctx=dict(c, reason=why))
                continue
            if r < .078:
                prev = sim.emit(t, "failed_attempt", "health", "prescription_pickup", actor, H, actor, org, ben=P, gross=cash, tmin=8, wait=w, miles=miles if k == 0 else 0,
                                mode=mode, outcome="failed", fr=F + ["out_of_stock", "repeat_trip"], lens=("health_cost",), ctx=dict(c, reason="the drug was on back order"))
                continue
            if cp > 250 and rng.random() < (.6 if H.fragile else .35):
                # Fills costing over $250 at the counter: pharmacy-industry reports put abandonment near half (estimate;
                # not in the downloaded sources), more often where the household could not cover a $400 emergency (SHED).
                prev = sim.emit(t, "failed_attempt", "health", "prescription_abandoned_over_cost", actor, H, actor, org, ben=P, gross=cp, tmin=7, wait=w,
                                miles=miles if k == 0 else 0, mode=mode, outcome="abandoned", fr=F + ["insufficient_funds"], lens=("health_cost",),
                                ctx=dict(c, reason="the share to pay at the counter was $%.2f" % cp))
                sim.bump("rx_abandoned")
                continue
            if cp > 55 and rng.random() < (.42 if not third else .2):
                prev = sim.emit(t, "failed_attempt", "health", "prescription_pickup", actor, H, actor, org, ben=P, gross=cash, tmin=7, wait=w, miles=miles if k == 0 else 0,
                                mode=mode, outcome="abandoned", fr=F + ["price_spike"], lens=("health_cost",),
                                ctx=dict(c, reason="the price at the counter was $%.2f, more than expected" % cp))
                sim.bump("rx_abandoned")
                continue
            i, oc, m = sim.pay(t + k, actor, H, W, org, "health", "prescription_pickup", cp + third, ctx=c, tmin=10 if k == 0 else 1, wait=w if k == 0 else 0,
                               miles=miles if k == 0 else 0, mode=mode, fr=F if k == 0 else (), rtype="insurance_claim" if third else "purchase", third=third,
                               payer=payer, fund=fund, defer=0.0, zero="insurance", ben=P, quiet_fail=0.0, related=prev)
    push(q, t, run)


def gen_health(sim, H, q):
    rng, cal, X, wx = sim.rng, sim.cal, sim.X, sim.wx
    wk = cal["weekday"]
    for P in H.members:
        a, cov = P.age, P.cov
        if H.gq == "jail":
            continue
        if P.inpatient:
            continue
        nh = H.gq == "nursing_home"
        unins = .45 if cov == "uninsured" else (.9 if cov == "medicaid" else 1.0)
        dis = 1.6 if P.dis != "none" else 1.0
        if wk and not nh:
            v = (4.5 if a < 5 else 1.8 if a < 18 else 2.0 if a < 45 else 3.5 if a < 65 else 6.0 if a < 75 else 7.5) / 250.0 * unins * dis
            if rng.random() < v:
                r = rng.random()
                if r < .09 and H.internet != "no":
                    visit(sim, q, P, H, ("physician",), "telehealth", "telehealth_visit", 98, rng.randint(15, 25), (0, 10), tele=True)
                elif r < .50 or a < 18:
                    visit(sim, q, P, H, ("physician",), "primary", "doctor_visit", 138, rng.randint(25, 45), (5, 40))
                elif r < .80:
                    visit(sim, q, P, H, ("physician", "hospital"), "specialist", "specialist_visit", 215, rng.randint(25, 50), (5, 45), scale=14.0)
                else:
                    visit(sim, q, P, H, ("hospital",), "lab", "lab_or_imaging", rng.choice([55, 90, 160, 320, 620, 1150]), rng.randint(20, 50), (5, 35), scale=14.0)
            if rng.random() < .0011 * unins:
                visit(sim, q, P, H, ("urgent_care",), "urgent", "urgent_care_visit", 188, rng.randint(30, 60), (10, 75), prefs=((480, 1200, 1),), scale=10.0)
            dv = ((1.7 if a < 19 else 1.6) if P.dental else .45) / 250.0
            if a >= 2 and rng.random() < dv:
                r = rng.random()
                svc, base = ("cleaning and exam", 168) if r < .66 else ("filling", 258) if r < .84 else ("crown or root canal", 1340) if r < .92 else ("extraction", 262)
                org = sim.pick(("dental", "fqhc") if cov in ("medicaid", "uninsured") else ("dental",), H.district, 9.0)
                dental(sim, q, P, H, org, svc, base)
            if a >= 4 and rng.random() < .0011:
                visit(sim, q, P, H, ("vision",), "vision", "vision_exam_and_glasses", rng.choice([95, 180, 320, 420]), rng.randint(30, 55), (0, 25))
            if a >= 12 and rng.random() < (.0038 if a >= 18 else .003) * (1.5 if P.dis == "cognitive" else 1):
                tele = rng.random() < .45 and H.internet != "no"
                selfpay = cov not in ("medicaid", "medicare_medicaid_dual") and rng.random() < .22
                if selfpay:
                    org = sim.pick(("behavioral",), H.district, 9.0)
                    amt = float(rng.choice([110, 125, 140, 160]))
                    if tele:
                        online(sim, q, P if a >= 18 else H.head, H, org, "health", "therapy_session_self_pay", amt, taxable=False, ctx=dict(), dur=(50, 55), channel="app",
                               prefs=((480, 1200, 1),))
                    else:
                        errand(sim, q, P if a >= 18 else H.head, H, org, "health", "therapy_session_self_pay", amt, 55, ((480, 1200, 1),), taxable=False, ctx=dict(), ben=P)
                else:
                    visit(sim, q, P, H, ("behavioral",), "therapy", "therapy_session", 126, 55, (0, 10), prefs=((480, 1200, 1),), tele=tele)
            if a >= 16 and rng.random() < .0025 * (1.8 if a >= 60 else 1):
                visit(sim, q, P, H, ("pt_clinic",), "pt", "physical_therapy_visit", 116, rng.randint(40, 60), (0, 15), prefs=((420, 1140, 1),))
        # prescriptions
        if P.nrx and rng.random() < P.nrx * .0156 and not nh:
            rx_pickup(sim, q, P, H)
        # emergency department and EMS
        pe = .00115 * wx["ed"] * (1.6 if a < 5 else 1.9 if a >= 75 else 1.0) * (1.15 if cov == "uninsured" else 1.7 if cov in ("medicaid", "medicare_medicaid_dual") else 1.0)
        if rng.random() < pe:
            ed_visit(sim, q, P, H)
        # dialysis (Mon/Wed/Fri or Tue/Thu/Sat groups)
        if P.esrd and not nh:
            grp = (int(P.pid[1:]) * 7919) % 100
            if grp < 12:
                continue
            mwf = grp < 60
            if (mwf and cal["dow"] in (0, 2, 4)) or (not mwf and cal["dow"] in (1, 3, 5)):
                dialysis(sim, q, P, H)
        # home care visits
        if P.home_care and wk and rng.random() < (.62 if P.home_care == "medicaid" else .42):
            home_visit(sim, q, P, H)


def dental(sim, q, P, H, org, svc, base):
    rng = sim.rng
    if org is None or org.open is None:
        return
    allowed = round(base * rng.uniform(.85, 1.2), 2)
    cov = P.cov
    actor = P if P.age >= 16 else next((x for x in H.adults), None)
    if actor is None:
        return
    W = actor.wallet
    major = svc not in ("cleaning and exam",)
    if P.dental:
        share = (0.0 if not major else .2 if svc == "filling" else .5 if "crown" in svc else .2)
        if cov in ("medicaid", "medicare_medicaid_dual"):
            share = 0.0
            allowed = round(allowed * .55, 2)
            payer, fund = "Medicaid dental benefit", "mixed"
        else:
            payer, fund = ("Medicare Advantage dental allowance" if cov == "medicare_advantage" else "Dental insurance plan"), ("federal" if cov == "medicare_advantage" else "private")
        now, third = round(allowed * share, 2), round(allowed * (1 - share), 2)
    else:
        now, third, payer, fund = allowed, 0.0, "", ""
    c = dict(org=org.name, svc=svc, who=("my child" if P.age < 16 else "me"))
    miles, mode, mins, tfr = sim.trip(actor, H, H.district, org.district)
    dur = 45 if not major else 75
    t = sim.slot(actor, dur + min(mins, 45), OFFICE, org.open, org.close)
    if t is None:
        return
    t += min(mins, 45) // 2

    def run(t=t):
        if now > 250 and W.liquid() + max(0, W.cc_limit - W.cc_bal) < now:
            sim.emit(t, "failed_attempt", "health", "dental_visit", actor, H, actor, org, ben=P, gross=allowed, tmin=30, wait=rng.randint(0, 15), miles=miles, mode=mode,
                     outcome="abandoned", fr=list(tfr) + ["insufficient_funds"], lens=("health_cost",),
                     ctx=dict(c, reason="the estimate was $%.0f out of pocket, so only the exam was done" % now))
            return
        if now > 400 and rng.random() < .35:
            fin = sim.X["x_medcard"]
            sim.emit(t, "purchase", "health", "dental_visit", actor, H, actor, org, ben=P, method="credit", gross=allowed, user=0.0, third=allowed,
                     payer="%s (patient financing, deferred interest)" % fin.name, fund="private", tmin=dur, wait=rng.randint(0, 15), miles=miles, mode=mode,
                     fr=tfr, lens=("health_cost", "consumer_finance"), ctx=dict(c, financed="1"))
            return
        sim.pay(t, actor, H, W, org, "health", "dental_visit", allowed, ctx=c, tmin=dur, wait=rng.randint(0, 15), miles=miles, mode=mode, fr=tfr,
                rtype="insurance_claim" if third else "purchase", third=third, payer=payer, fund=fund, zero="insurance", ben=P, quiet_fail=0.0)
    push(q, t, run)


def ed_visit(sim, q, P, H):
    rng, X = sim.rng, sim.X
    hosp = sim.by_kind["hospital"]
    org = hosp[1] if (H.district in ("D1", "D2") and rng.random() < .7) or (H.district == "D3" and rng.random() < .5) else hosp[0]
    cov = P.cov
    # MEPS 2024 emergency room visits (h254e, facility plus doctor): median $674, mean $1,405; about $741 and $1,545 in 2027.
    # v1 drew a median near $1,280 with a short tail. v2 phase 5: draws under $600 are pressed into $300-600 (an estimate;
    # a visit lasting hours carries a facility fee, and the v2 close reading found an uninsured 6.9-hour stay billed
    # $181.59 in all), smoothly, so no amount piles up; v1's floor was $150.
    x = rng.lognormvariate(math.log(950), 1.2)
    allowed = round(min(40000, max(x, 300 + .5 * x)) * (PAYF.get(cov, 1.15) if cov != "uninsured" else 1.0), 2)
    dur = rng.randint(150, 420)
    w = rng.randint(12, 190)
    t = sim.slot(P, 60, ((0, 1320, 1),))
    if t is None:
        t = rng.randint(30, 1200)
    P.free = [f for f in P.free if f[1] <= t]            # the rest of the day is gone
    ems = rng.random() < .26
    comp = (P.cared_by[0] if P.cared_by else next((x for x in H.adults if x is not P), None)) if (P.age < 18 or P.age >= 75) else None
    actor = comp if (P.age < 16 and comp is not None) else P
    miles = round(sim.dist(H.district, org.district) * 1.0, 1)

    def run(t=t):
        rel = None
        if ems:
            cost = 1250.0
            if cov in ("medicare", "medicare_advantage", "medicare_medicaid_dual"):
                third, payer, fund, later = 520.0, "Medicare Part B (ambulance)", "federal", (0.0 if cov == "medicare_medicaid_dual" or P.medigap else 104.0)
            elif cov == "medicaid":
                third, payer, fund, later = 285.0, "Medicaid", "mixed", 0.0
            elif cov == "uninsured":
                third, payer, fund, later = 0.0, "", "", 1250.0
            else:
                third, payer, fund, later = 880.0, "Commercial health insurance", "private", float(rng.choice([150, 250, 370, 450]))
            gap = max(0.0, cost - third - (later if cov != "uninsured" else 0))
            rel = sim.emit(t - min(t, 25), "public_service_encounter", "health", "ems_ambulance_transport", actor, H, sim.one("ems"), P, ben=P, channel="phone",
                           method="insurance" if third else "none", gross=cost, user=0.0, third=third + gap,
                           payer=(payer + " plus county EMS levy") if payer else "County EMS levy (bill likely uncollected)", fund="mixed" if payer else "local",
                           imputed=cost, tmin=38, wait=rng.randint(6, 19), miles=miles, mode="ambulance", outcome="partial" if later else "completed",
                           lens=("health_cost",), ctx=dict(org=org.name, later="%.0f" % later, who=("my child" if P.age < 16 else "me")))
        c = dict(org=org.name, who=("my child" if P.age < 16 else "me"), hrs="%.1f" % (dur / 60.0))
        if cov == "uninsured":
            cost = round(allowed * .45, 2)
            i = sim.emit(t, "public_service_encounter", "health", "emergency_visit_uncompensated", actor, H, org, P, ben=P, method="none", gross=allowed, user=0.0,
                         third=cost, payer="Uncompensated care (hospital charity care, Medicaid disproportionate-share funds)", fund="mixed", imputed=cost,
                         tmin=min(dur, 1439 - int(t)), wait=min(w, max(0, 1439 - int(t))), miles=miles, mode="ambulance" if ems else ("car" if H.vehicles else "ride_from_family_or_friend"), outcome="partial",
                         fr=("wait",), lens=("health_cost",), related=rel, ctx=dict(c, bill="%.0f" % allowed, cost="%.0f" % cost))
        else:
            now, third, payer, fund, later = cover(sim, P, allowed, "ed")
            if now > 0 and rng.random() < .6:
                later, now = later + now, 0.0             # most emergency copays are billed afterward
            i = sim.emit(t, "insurance_claim", "health", "emergency_department_visit", actor, H, org, P, ben=P, method="insurance", gross=allowed, user=now,
                         third=third, payer=payer, fund=fund, tmin=min(dur, 1439 - int(t)), wait=min(w, max(0, 1439 - int(t))), miles=miles,
                         mode="ambulance" if ems else ("car" if H.vehicles else "ride_from_family_or_friend"), outcome="partial" if later else "completed",
                         lens=("health_cost",), related=rel, ctx=dict(c, later="%.0f" % later))
        if comp is not None and comp is not actor:
            sim.emit(t, "non_monetary_job", "care_and_household", "escort_to_appointment", comp, comp.hh, comp, P, ben=P, tmin=min(dur, 1439 - int(t)), wait=0, miles=miles,
                     mode="car", fr=("caregiving_conflict",) if comp.works else (), lens=("family_care",), related=i, ctx=dict(org=org.name, rel=P.rel, ed="1"))
            comp.free = [f for f in comp.free if f[1] <= t]
        if rng.random() < .5:
            rx_pickup(sim, q, P, H, nfill=1, after=min(1250, t + dur + 10))
    push(q, t, run)


def dialysis(sim, q, P, H):
    rng = sim.rng
    org = min(sim.by_kind["dialysis"], key=lambda o: sim.dist(H.district, o.district))
    cov = P.cov
    allowed = round(305 * rng.uniform(.97, 1.05), 2)
    private = cov in ("employer", "marketplace", "other_private")
    if private:
        allowed = round(allowed * 3.2, 2)
        now, third, payer, fund, later = 0.0, allowed * .8, "Commercial plan (first 30 months of dialysis)", "private", allowed * .2
    elif cov == "medicare_medicaid_dual" or cov == "medicaid":
        now, third, payer, fund, later = 0.0, allowed, "Medicare (ESRD) and Medicaid", "mixed", 0.0
    elif cov == "medicare_advantage" or P.medigap:
        now, third, payer, fund, later = 0.0, allowed, "Medicare (ESRD) with supplemental coverage", "federal", 0.0
    else:
        now, third, payer, fund, later = 0.0, allowed * .8, "Medicare (ESRD)", "federal", allowed * .2
    start = rng.choice([345, 360, 600, 615, 840])
    P.free = [f for f in P.free if f[0] >= start + 300 or f[1] <= start - 60]
    miles = round(sim.dist(H.district, org.district) * 2, 1)
    car = H.vehicles > 0 and P.age < 80
    helper = P.cared_by[0] if (P.cared_by and not car) else None

    def run(t=start):
        mode = "car" if car else ("ride_from_family_or_friend" if helper else "paratransit")
        i = sim.emit(t, "insurance_claim", "health", "dialysis_treatment", P, H, org, P, ben=P, method="insurance", gross=allowed, user=now, third=third, payer=payer,
                     fund=fund, tmin=245, wait=rng.randint(0, 20), miles=miles, mode=mode, outcome="partial" if later else "completed",
                     fr=("distance",) if miles > 24 else (), lens=("health_cost",), ctx=dict(org=org.name, later="%.2f" % later))
        if helper:
            sim.emit(t - 30, "non_monetary_job", "care_and_household", "escort_to_appointment", helper, helper.hh, helper, P, ben=P, tmin=90, miles=miles * 2,
                     mode="car", fr=("caregiving_conflict",) if helper.works else (), lens=("family_care",), related=i, ctx=dict(org=org.name, rel=P.rel, dialysis="1"))
        elif not car:
            for tt in (t - 40, t + 255):
                sim.emit(tt, "public_service_encounter", "transportation", "paratransit_ride", P, H, sim.one("paratransit"), P, ben=P, method="none", gross=PARATRANSIT_COST,
                         user=0.0, third=PARATRANSIT_COST, payer="Medicaid non-emergency medical transportation" if cov in ("medicaid", "medicare_medicaid_dual") else "HAT Access paratransit subsidy",
                         fund="mixed", imputed=PARATRANSIT_COST, tmin=40, wait=rng.randint(5, 35), miles=miles / 2, mode="paratransit", lens=("disability", "land_use"),
                         related=i, ctx=dict(org=org.name))
    push(q, start, run)


def home_visit(sim, q, P, H):
    rng = sim.rng
    org = sim.pick(("home_health",), H.district, 14.0)
    if org is None:
        return
    hc = P.home_care
    hrs = rng.choice([2, 3, 3, 4])
    t = rng.choice([480, 540, 600, 780, 840])
    if hc == "medicaid":
        allowed, third, payer, fund, now = 27.5 * hrs, 27.5 * hrs, "Medicaid home and community-based services", "mixed", 0.0
        kind = "personal_care_aide_visit"
    elif hc == "medicare":
        allowed, third, payer, fund, now = 172.0, 172.0, "Medicare (home health benefit)", "federal", 0.0
        kind, hrs = "home_health_nurse_visit", 1
    else:
        allowed, third, payer, fund, now = 34.0 * hrs, 0.0, "", "", 34.0 * hrs
        kind = "personal_care_aide_visit"
    noshow = rng.random() < .045 * sim.wx["noshow"]

    def run(t=t):
        if noshow:
            i = sim.emit(t, "failed_attempt", "health", kind, P, H, org, P, ben=P, gross=allowed, tmin=hrs * 60, wait=rng.randint(40, 120), outcome="failed",
                         fr=("wait", "caregiving_conflict"), lens=("family_care", "labor"), ctx=dict(org=org.name, reason="the aide's shift went unfilled"))
            # who covers (v2): the family caregiver, or another adult at home. A working caregiver leaves work or goes without.
            cover = next((c for c in (P.cared_by or []) if c.age >= 18 and not c.inpatient), None) or next((a for a in H.adults if a is not P and not a.inpatient), None)
            if cover is None:
                return
            at_work = cover.works and any(s <= t <= e for s, e in (cover.shift or []))
            if at_work and rng.random() < .6:
                lost = round(hrs * cover.wage / 2080.0, 2)
                sim.emit(t + rng.randint(20, 60), "failed_attempt", "work", "left_work_aide_no_show", cover, cover.hh, cover, cover.org or "", ben=P, gross=lost,
                         tmin=hrs * 60, outcome="partial", fr=("caregiving_conflict", "schedule_volatility"), lens=("family_care", "labor"), related=i,
                         ctx=dict(org=org.name, lost="%.2f" % lost, hrs=hrs, rel=P.rel, age=P.age))
            elif not at_work:
                sim.emit(t + rng.randint(10, 40), "non_monetary_job", "care_and_household", "covered_missed_aide_shift", cover, cover.hh, cover, P, ben=P,
                         tmin=hrs * 60, fr=("caregiving_conflict",), lens=("family_care",), related=i, ctx=dict(org=org.name, hrs=hrs, rel=P.rel, age=P.age))
            return
        if now:
            W = P.wallet
            payer_p = P.cared_by[0] if (P.cared_by and rng.random() < .5) else P
            sim.pay(t, payer_p, payer_p.hh, payer_p.wallet, org, "health", kind, allowed, channel="automatic", ctx=dict(org=org.name, hrs=hrs), tmin=0,
                    ben=P, quiet_fail=0.0, lens=("family_care",))
        else:
            sim.emit(t, "insurance_claim", "health", kind, P, H, org, P, ben=P, method="insurance", gross=allowed, third=third, payer=payer, fund=fund,
                     tmin=hrs * 60, lens=("family_care",), ctx=dict(org=org.name, hrs=hrs))
    push(q, t, run)


# Care put off because of cost. SHED 2025 (sources/derived/shed_care_by_fragility.csv): in the past year 27.9% of adults
# who could not cover a $400 emergency went without a doctor because of the cost, against 7.0% of those who could; for
# dental care 33.0% and 8.6%. Taken as one such decision a year per adult who reports it, spread over the days.
SKIP_CARE = {"doctor": (.279, .070), "dental": (.330, .086)}


def gen_skipped_care(sim, H, q):
    if H.gq:
        return
    rng = sim.rng
    debt = next((b for b in H.bills if b[0] == "medical_payment_plan"), None)
    for P in H.adults:
        if P.inpatient:
            continue
        for what, (frag, ok) in SKIP_CARE.items():
            if rng.random() >= (frag if H.fragile else ok) / 365.0:
                continue
            t = sim.slot_soft(P, 10, EVE)
            if what == "dental":
                kind, cost = "dental_care_put_off_over_cost", float(rng.choice([180, 240, 320, 650, 1100]))
                why = "a filling or crown would cost about $%.0f" % cost
            elif debt is not None:
                kind, cost = "care_delayed_by_medical_debt", 160.0
                why = "the last medical bill is still being paid off at $%.0f a month" % debt[2]
            else:
                kind, cost = "care_delayed_by_cost", 160.0
                why = "a visit would cost more than there was to spare"
            sim.emit(t, "failed_attempt", "health", kind, P, H, P, "", ben=P, gross=cost, tmin=5, outcome="abandoned",
                     fr=("insufficient_funds",), lens=("health_cost",), ctx=dict(reason=why, debt="%.0f" % (debt[2] if debt else 0)))
