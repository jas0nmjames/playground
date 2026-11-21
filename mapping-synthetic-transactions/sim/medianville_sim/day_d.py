"""Business-to-business activity implied by the day: settlements, supply runs, payroll, overhead, farm sales."""
import math
from .day_c import pois


def business_day(sim):
    rng, X, sc, cal = sim.rng, sim.X, sim.scale, sim.cal
    K = sim.by_kind
    weekday = cal["weekday"]
    local = [o for o in sim.orgs if o.district != "EXT"]

    def dist_of(a, b):
        for o in (a, b):
            d = getattr(o, "district", None)
            if d and d != "EXT":
                return d
        return ""

    def b2b(t, kind, frm, to, gross, user=None, rtype="b2b", P=None, H=None, **kw):
        lens = list(kw.pop("lens", ()))
        small = any(getattr(o, "size", 999) < 20 and getattr(o, "otype", "") == "business" and getattr(o, "district", "EXT") != "EXT" for o in (frm, to))
        if (small or P is not None) and "small_business" not in lens:
            lens.append("small_business")
        return sim.emit(t, rtype, "business", kind, P, H, frm, to, district=(H.district if H is not None else dist_of(frm, to)), gross=gross,
                        user=gross if user is None else user, lens=lens, **kw)

    def named(kind, *words):
        return [o for o in K.get(kind, []) if any(w in o.name for w in words)]

    food_ws = named("wholesaler", "Foodservice", "Produce", "Import Foods", "Beverage", "Restaurant Supply") or K["wholesaler"]
    build_ws = named("wholesaler", "Building Supply", "Plumbing Supply", "Electrical Supply") + K.get("home_center", [])
    auto_ws = named("wholesaler", "Auto Parts") or K["wholesaler"]
    jan_ws = named("wholesaler", "Janitorial") or K["wholesaler"]
    ag_ws = named("wholesaler", "Ag Supply", "Cooperative") or K["wholesaler"]
    med_ws = named("wholesaler", "Medical") or K["wholesaler"]
    bank_ops = K["bank_hq"][0]
    acq = X["x_acq"]
    sup = X["x_suppliers"]

    # ---- 1. card settlement and cash drops
    for o in local:
        card = o.cc + o.dc
        if card > 0.5:
            ncard = max(1, int(round(o.ntx * card / max(o.rev, card))))
            fee = round(o.cc * rng.uniform(.024, .031) + o.dc * rng.uniform(.007, .012) + .10 * ncard, 2)
            b2b(rng.randint(1385, 1435), "card_settlement_batch", acq, o, round(card, 2), user=fee, channel="automatic", method="ach", fee_type="card_processing_fees", fee=fee,
                ctx=dict(org=o.name, n=ncard, net="%.2f" % (card - fee), pct="%.1f" % (100 * fee / card)))
        if o.csh > 220 and o.otype == "business":
            big = o.size >= 100
            fee = round(18 + o.csh * .0035, 2) if big else 0.0
            b2b(rng.randint(1260, 1420), "cash_deposit", o, bank_ops if big else rng.choice(K["bank"]), round(o.csh, 2), user=fee, channel="in_person", method="cash",
                fee_type="armored_pickup_fee" if fee else "", fee=fee, tmin=0 if big else rng.randint(8, 20), ctx=dict(org=o.name, armored="1" if big else ""))
        if o.kind in ("restaurant", "fastfood", "food_truck", "salon", "auto_repair", "bar", "nail") and o.size < 25 and card > 150 and rng.random() < .03:
            amt = round(card * rng.choice([.10, .12, .15, .18]), 2)
            b2b(rng.randint(1390, 1435), "merchant_cash_advance_daily_remittance", o, acq, amt, channel="automatic", method="ach", fr=("fee",), lens=("consumer_finance",),
                ctx=dict(org=o.name, pct="%.0f" % (100 * amt / card)))
    # ---- 2. delivery platform payouts
    agg = {}
    for rest, subt in sim.delivery_orders:
        if rest is not None:
            agg.setdefault(rest.oid, [rest, 0.0, 0])
            agg[rest.oid][1] += subt
            agg[rest.oid][2] += 1
    for rest, tot, n in agg.values():
        fee = round(tot * rng.choice([.15, .20, .25, .30]) + .30 * n, 2)
        b2b(rng.randint(1390, 1435), "delivery_platform_payout", X[rng.choice(["x_deliv1", "x_deliv2"])], rest, round(tot, 2), user=fee, channel="automatic", method="ach",
            fee_type="platform_commission", fee=fee, ctx=dict(org=rest.name, n=n, pct="%.0f" % (100 * fee / tot)))
    # ---- 3. payroll runs and employer taxes
    wages = {}
    for p in sim.persons:
        if p.org is not None and p.wage > 0:
            wages[p.org.oid] = wages.get(p.org.oid, 0.0) + p.wage
    by_oid = {o.oid: o for o in sim.orgs}
    for oid, (n, gross) in sim.payroll.items():
        o = by_oid[oid]
        if o.district == "EXT":
            continue
        k = min(3.0, max(1.0, o.size / max(1, o.emp)))
        tot = round(gross * k, 2)
        nn = int(round(n * k))
        fee = round(42 + 2.35 * nn, 2) if o.size < 100 else round(1.1 * nn, 2)
        t = rng.randint(20, 300)
        i = b2b(t, "payroll_run", o, bank_ops, tot, user=tot + fee, channel="automatic", method="ach", fee_type="payroll_service_fee", fee=fee, lens=("labor",),
                ctx=dict(org=o.name, n=nn, residents=n))
        etax = round(tot * (.0765 + .011), 2)
        b2b(t, "employer_payroll_taxes", o, X["x_irs"], etax, rtype="tax", channel="automatic", method="ach", related=i, lens=("labor", "public_finance"), ctx=dict(org=o.name))
    if weekday and cal["dow"] in (2, 4):
        for o in local:
            if o.size >= 30 and o.otype in ("business", "nonprofit") and rng.random() < (.36 if cal["dow"] == 2 else .20):
                per = wages.get(o.oid, o.size * 52000.0) * min(3.0, max(1.0, o.size / max(1, o.emp))) / rng.choice([26, 26, 52])
                amt = round(per * rng.uniform(.24, .30), 2)
                b2b(rng.randint(480, 1020), "federal_payroll_tax_deposit", o, X["x_irs"], amt, rtype="tax", channel="online", method="ach", lens=("public_finance", "labor"),
                    ctx=dict(org=o.name, rule="semiweekly"))
    # ---- 4. supply runs
    if weekday:
        for o in local:
            k = o.kind
            if k in ("restaurant", "fastfood", "coffee", "bar", "fine_dining", "caterer", "food_truck") and rng.random() < .40:
                amt = round(o.size * math.exp(rng.gauss(math.log(215), .5)), 2)
                ws = rng.choice(food_ws)
                r = rng.random()
                terms = "cod" if (o.size < 12 and r < .45) else ("ach" if r < .65 else "net")
                b2b(rng.randint(300, 660), "foodservice_delivery", o, ws, amt, user=amt if terms != "net" else 0.0, method={"cod": "check", "ach": "ach", "net": "none"}[terms],
                    outcome="partial" if terms == "net" else "completed", fr=(("out_of_stock",) if rng.random() < .08 else ()), tmin=rng.randint(10, 30),
                    ctx=dict(org=ws.name, buyer=o.name, terms=terms, short=rng.choice(["eggs", "fryer oil", "chicken wings", "to-go containers", "romaine"])))
            elif k in ("grocery_full", "grocery_discount", "supercenter", "warehouse_club", "dollar", "grocery_indep", "home_center", "department"):
                base = o.rev if o.rev > 0 else o.size * 900.0
                amt = round(base * rng.uniform(.62, .80) * (1.0 if k != "grocery_indep" else .9), 2)
                if amt > 150 and rng.random() < (.9 if o.size >= 60 else .45):
                    b2b(rng.randint(180, 420), "store_replenishment_delivery", o, sup, amt, user=0.0, method="none", outcome="partial", tmin=rng.randint(30, 120),
                        fr=(("out_of_stock",) if rng.random() < .12 else ()), ctx=dict(org=o.name, terms="net"))
            elif k == "pharmacy":
                amt = round(max(900.0, o.rev * 3.2) * rng.uniform(.7, 1.1), 2)
                b2b(rng.randint(360, 540), "pharmacy_wholesaler_order", o, sup, amt, user=0.0, method="none", outcome="partial", fr=(("out_of_stock",) if rng.random() < .25 else ()),
                    ctx=dict(org=o.name, terms="net"))
            elif k == "gas" and rng.random() < .30:
                gal = rng.randint(6800, 8800)
                rack = sim.cfg["GAS_PRICE"] - rng.uniform(.52, .68)
                b2b(rng.randint(120, 420), "fuel_delivery", o, sup, round(gal * rack, 2), channel="automatic", method="ach", ctx=dict(org=o.name, gal=gal, rack="%.2f" % rack))
            elif k == "construction" and rng.random() < .38:
                ws = rng.choice(build_ws)
                amt = round(min(18000, math.exp(rng.gauss(math.log(420), 1.0))), 2)
                r = rng.random()
                m = "none" if r < .45 else ("credit" if r < .85 else "check")
                b2b(rng.randint(375, 600), "contractor_materials_purchase", o, ws, amt, user=0.0 if m == "none" else amt, method=m, outcome="partial" if m == "none" else "completed",
                    tmin=rng.randint(15, 50), wait=rng.randint(0, 25), fr=(("out_of_stock", "repeat_trip") if rng.random() < .07 else ()), ctx=dict(org=ws.name, buyer=o.name, terms="account" if m == "none" else m))
            elif k in ("auto_repair", "tire", "oil_change") and rng.random() < .6:
                ws = rng.choice(auto_ws)
                amt = round(math.exp(rng.gauss(math.log(260), .8)), 2)
                b2b(rng.randint(480, 960), "shop_parts_order", o, ws, amt, user=0.0, method="none", outcome="partial", fr=(("wait",) if rng.random() < .15 else ()),
                    ctx=dict(org=ws.name, buyer=o.name))
            elif k == "manufacturer":
                big = o.size >= 100
                if rng.random() < (.8 if big else .25):
                    amt = round(o.size * rng.uniform(140, 520), 2)
                    b2b(rng.randint(300, 900), "raw_materials_delivery", o, sup, amt, user=0.0, method="none", outcome="partial", ctx=dict(org=o.name, terms="net 45"))
                if rng.random() < (.85 if big else .30):
                    amt = round(o.size * rng.uniform(380, 1100), 2)
                    b2b(rng.randint(420, 1020), "customer_shipment_invoiced", X.get("x_buyers", X["x_customers"]), o, amt, user=0.0, method="none", outcome="partial", ctx=dict(org=o.name, terms="net 45"))
            elif k == "hospital":
                ws = rng.choice(med_ws)
                b2b(rng.randint(300, 480), "medical_supply_delivery", o, ws, round(o.size * rng.uniform(18, 46), 2), user=0.0, method="none", outcome="partial", ctx=dict(org=ws.name, buyer=o.name))
            elif k == "school_district" and cal["school_day"]:
                ws = food_ws[0]
                b2b(rng.randint(300, 420), "school_food_service_delivery", o, ws, round(o.size * rng.uniform(5.5, 11), 2), user=0.0, method="none", outcome="partial",
                    lens=("public_finance", "education"), ctx=dict(org=ws.name, buyer=o.name))
            elif k in ("salon", "nail", "laundromat", "dry_cleaner", "child_care") and rng.random() < .07:
                ws = rng.choice(jan_ws)
                amt = round(rng.uniform(40, 420), 2)
                b2b(rng.randint(540, 1000), "shop_supplies_order", o, ws, amt, method="credit", ctx=dict(org=ws.name, buyer=o.name))
    # ---- 5. farms
    farms = K.get("farm", [])
    packer = K["packing"][0] if K.get("packing") else None
    barn = K["sale_barn"][0] if K.get("sale_barn") else None
    farmers = [p for p in sim.persons if p.occ == "farmer" and p.emp == "self_employed"]
    for o in farms:
        note = o.notes
        if "dairy" in note:
            lb = rng.randint(24000, 28500)
            b2b(rng.randint(300, 420), "milk_pickup", X["x_customers"], o, round(lb * rng.uniform(.185, .215), 2), user=0.0, method="none", outcome="partial", lens=("rural",),
                ctx=dict(org=o.name, lb=lb))
        elif ("vegetable" in note or "mushroom" in note or "egg" in note or "apples" in note or "CSA" in note) and packer is not None and weekday and rng.random() < .55:
            amt = round(math.exp(rng.gauss(math.log(4200), .7)), 2)
            b2b(rng.randint(390, 840), "farm_load_delivered_to_packer", packer, o, amt, user=0.0, method="none", outcome="partial", tmin=rng.randint(30, 90), wait=rng.randint(10, 70),
                lens=("rural", "farmworker"), ctx=dict(org=packer.name, farm=o.name, terms="settlement in 21 days"))
            if rng.random() < .35:
                g2 = round(amt * rng.uniform(.6, 1.4), 2)
                fee = round(g2 * rng.uniform(.14, .22), 2)
                b2b(rng.randint(600, 960), "packer_settlement_check", packer, o, g2, user=fee, method="check", fee_type="packing_cooling_and_commission_charges", fee=fee, lens=("rural",),
                    ctx=dict(org=packer.name, farm=o.name, net="%.2f" % (g2 - fee)))
        elif "corn" in note and weekday and rng.random() < .30:
            bu = rng.randint(1800, 6200)
            px = rng.uniform(4.05, 4.55)
            fee = round(bu * rng.uniform(.04, .11), 2)
            b2b(rng.randint(480, 900), "grain_sold_to_elevator", ag_ws[-1], o, round(bu * px, 2), user=fee, method="check", fee_type="drying_and_storage_charges", fee=fee, lens=("rural",),
                ctx=dict(org=ag_ws[-1].name, farm=o.name, bu=bu, px="%.2f" % px))
        if weekday and cal["month"] in (2, 3, 4, 5) and rng.random() < .30:
            ws = ag_ws[0]
            amt = round(o.size ** .7 * rng.uniform(900, 4200), 2)
            b2b(rng.randint(450, 960), "farm_inputs_purchase", o, ws, amt, user=0.0, method="none", outcome="partial", third=amt, payer="Farm operating line of credit (First Medianville Bank)",
                fund="private", lens=("rural",), ctx=dict(org=ws.name, farm=o.name, what=rng.choice(["seed", "fertilizer", "diesel and propane", "crop protection", "greenhouse flats and soil"])))
    if barn is not None and barn.open is not None:
        sellers = [(o, None) for o in farms if "cattle" in o.notes or "corn" in o.notes] + [(None, p) for p in farmers]
        rng.shuffle(sellers)
        for o, p in sellers[:max(1, pois(rng, 10 * sc))]:
            head = rng.randint(2, 18)
            gross = round(head * rng.uniform(1150, 2450), 2)
            fee = round(gross * .035 + head * rng.uniform(6.5, 9.0), 2)
            t = rng.randint(690, 1000)
            if p is not None:
                H = p.hh
                p.wallet.give("savings", gross - fee)
                b2b(t, "livestock_sold_at_auction", barn, p, gross, user=fee, method="check", fee_type="commission_yardage_and_checkoff", fee=fee, P=p, H=H, tmin=rng.randint(180, 360),
                    miles=round(sim.dist(H.district, barn.district) * 2, 1), mode="car", lens=("rural",), ctx=dict(org=barn.name, head=head, net="%.2f" % (gross - fee)))
            else:
                b2b(t, "livestock_sold_at_auction", barn, o, gross, user=fee, method="check", fee_type="commission_yardage_and_checkoff", fee=fee, tmin=rng.randint(180, 360), lens=("rural",),
                    ctx=dict(org=barn.name, farm=o.name, head=head, net="%.2f" % (gross - fee)))
    for o in rng.sample(farms, min(len(farms), pois(rng, 1.2 * sc))):
        amt = round(rng.uniform(1400, 23000), 2)
        b2b(rng.randint(60, 360), "farm_program_payment", X["x_treasury"], o, amt, user=0.0, rtype="benefit_issuance", channel="automatic", method="ach", third=amt,
            payer="USDA Farm Service Agency program payment", fund="federal", lens=("rural", "public_finance"), ctx=dict(farm=o.name))
    # ---- 6. overhead that falls on this day
    landlords = K["landlord"]
    elec = K["electric"][0]
    acct = K.get("accounting", [])
    media = K.get("newspaper", []) + K.get("broadcast", [])
    vendors = K.get("construction", []) + K.get("repair_shop", [])
    services = K.get("admin_firm", []) + K.get("trash", [])
    dom = cal["dom"]
    for o in local:
        if o.otype != "business":
            continue
        small = o.size < 20
        z = o.size ** .8
        if rng.random() < ({1: .42, 2: .08, 3: .07, 4: .05, 5: .07}.get(dom, .012)) and o.kind not in ("landlord", "farm"):
            amt = round(z * rng.uniform(260, 520), 2)
            late = dom > 5 and rng.random() < .5
            fee = round(amt * .05, 2) if late else 0.0
            b2b(rng.randint(480, 1020), "commercial_rent_payment", o, rng.choice(landlords), amt, user=amt + fee, channel="online" if not small else "mail",
                method="ach" if not small else "check", fee_type="late_fee" if fee else "", fee=fee, ctx=dict(org=o.name, late="1" if late else ""))
        if rng.random() < 1 / 28.0:
            amt = round(z * rng.uniform(60, 150), 2)
            b2b(rng.randint(120, 420), "business_utility_bill", o, elec, amt, channel="automatic", method="ach", fr=(("price_spike",) if rng.random() < .1 else ()), ctx=dict(org=o.name))
        if rng.random() < 1 / 40.0:
            b2b(rng.randint(120, 420), "business_insurance_premium", o, X["x_autoins"], round(z * rng.uniform(55, 140), 2), channel="automatic", method="ach", ctx=dict(org=o.name))
        if small and rng.random() < .012:
            b2b(rng.randint(120, 420), "business_loan_payment", o, bank_ops, round(rng.uniform(480, 4600), 2), channel="automatic", method="ach", ctx=dict(org=o.name))
        if rng.random() < 1 / 28.0:
            b2b(rng.randint(60, 420), "software_subscription", o, sup, float(rng.choice([39, 69, 99, 149, 199, 299])), channel="automatic", method="credit", ctx=dict(org=o.name))
        if weekday and o.kind in ("restaurant", "fastfood", "bar", "auto_repair", "hotel", "fine_dining", "coffee") and rng.random() < .14 and services:
            sv = rng.choice(services)
            b2b(rng.randint(360, 900), "route_service_invoice", o, sv, round(rng.uniform(42, 190), 2), user=0.0, method="none", outcome="partial",
                ctx=dict(org=sv.name, buyer=o.name, what=rng.choice(["linen and uniforms", "grease trap pumping", "pest control", "trash and recycling", "hood cleaning"])))
        if weekday and cal["tax_season"] and small and acct and rng.random() < .008:
            a = rng.choice(acct)
            b2b(rng.randint(540, 1020), "accounting_fees", o, a, round(rng.uniform(350, 2400), 2), method="check", ctx=dict(org=a.name, buyer=o.name))
        if weekday and media and rng.random() < .006:
            m = rng.choice(media)
            b2b(rng.randint(540, 1020), "local_advertising", o, m, round(rng.uniform(150, 1400), 2), method="credit", ctx=dict(org=m.name, buyer=o.name))
        if weekday and o.kind == "landlord" and vendors and rng.random() < .25:
            v = rng.choice(vendors)
            b2b(rng.randint(480, 1020), "property_maintenance_invoice", o, v, round(math.exp(rng.gauss(math.log(520), .8)), 2), method="check", ctx=dict(org=v.name, buyer=o.name))
        if weekday and o.kind in ("prof_firm", "admin_firm", "construction", "trucking", "law", "accounting", "manufacturer", "wholesaler") and small:
            r = rng.random()
            if r < .035:
                amt = round(math.exp(rng.gauss(math.log(4800), .9)), 2)
                days = rng.choice([32, 38, 45, 47, 60, 63, 75, 90])
                oc = rng.choice(["rescheduled", "rescheduled", "failed", "partial"])
                sim.emit(rng.randint(540, 1000), "failed_attempt", "business", "overdue_invoice_follow_up", None, None, o, X["x_customers"], district=o.district, channel=rng.choice(["phone", "online"]),
                         gross=amt, tmin=rng.randint(10, 35), wait=rng.randint(0, 15), outcome=oc, fr=("wait", "paperwork"), lens=("small_business",),
                         ctx=dict(org=o.name, days=days, amt="%.0f" % amt, said=rng.choice(["the check is in the next run", "accounts payable never got the invoice", "the approver is out until Monday", "they are disputing two line items", "nobody picked up"])))
            elif r < .052:
                amt = round(math.exp(rng.gauss(math.log(3600), .9)), 2)
                b2b(rng.randint(300, 900), "late_invoice_paid", X["x_customers"], o, amt, channel="mail", method="check", fr=("wait",),
                    ctx=dict(org=o.name, days=rng.choice([41, 52, 58, 67, 84]), amt="%.0f" % amt))
    # ---- 7. public bodies paying vendors, grants and subsidies (not on bank holidays: v2 phase 5)
    if weekday and cal.get("bank_day", True):
        govs = K["county"] + K["city"] + K["school_district"]
        pool = vendors + K.get("prof_firm", []) + services + K.get("wholesaler", []) + K.get("trucking", [])
        for _ in range(pois(rng, 30 * sc if cal["dow"] == 2 else 8 * sc)):
            g, v = rng.choice(govs), rng.choice(pool)
            amt = round(math.exp(rng.gauss(math.log(2600), 1.2)), 2)
            b2b(rng.randint(540, 960), "government_vendor_payment", g, v, amt, method="check" if rng.random() < .5 else "ach", lens=("public_finance",),
                ctx=dict(org=g.name, vendor=v.name, days=rng.choice([18, 24, 30, 30, 41, 55])))
        cc = K.get("child_care", [])
        for o in rng.sample(cc, min(len(cc), pois(rng, 6 * sc))):
            amt = round(rng.uniform(900, 8600), 2)
            b2b(rng.randint(60, 360), "child_care_subsidy_payment_to_provider", K["benefits_office"][0], o, amt, user=0.0, rtype="benefit_issuance", channel="automatic", method="ach", third=amt,
                payer="State child care assistance (CCDF)", fund="mixed", lens=("family_care", "public_finance"), ctx=dict(org=o.name))
        np_ = K.get("nonprofit", [])
        if np_ and rng.random() < min(1.0, 1.2 * sc):
            grantee = rng.choice(K.get("food_pantry", []) + K.get("shelter", []) + K.get("community_action", []))
            amt = float(rng.choice([5000, 7500, 12000, 20000, 35000]))
            b2b(rng.randint(600, 900), "grant_disbursement", np_[0], grantee, amt, user=0.0, method="ach", third=amt, payer="United Fund of Greater Medianville annual campaign",
                fund="philanthropic", ctx=dict(org=grantee.name))
        # office lunches
        buyers = K.get("law", []) + K.get("prof_firm", []) + K.get("mgmt_hq", []) + K.get("insurer_office", []) + K.get("software", []) + K.get("bank_hq", []) + K.get("hospital", [])
        cat = K.get("caterer", []) + K.get("restaurant", [])[:30]
        for _ in range(pois(rng, 32 * sc)):
            if not buyers or not cat:
                break
            o, c = rng.choice(buyers), rng.choice(cat)
            amt = round(rng.uniform(110, 640), 2)
            tip = round(amt * rng.choice([.10, .15, .18]), 2)
            c.rev += amt
            c.cc += amt
            c.ntx += 1
            b2b(rng.randint(600, 760), "office_catering_order", o, c, amt + tip, method="credit", fee_type="delivery_and_gratuity", fee=tip, user=amt + tip,
                ctx=dict(org=c.name, buyer=o.name, n=rng.choice([8, 10, 12, 15, 20, 25, 40])))
    # ---- 8. the self-employed buying what the work needs
    SE = {"general contractor": (.40, (60, 900), "home_center", "building materials"), "landscaper": (.30, (25, 140), "gas", "fuel and trimmer line"),
          "house cleaner": (.15, (15, 60), "dollar", "cleaning supplies"), "food vendor": (.60, (120, 600), "warehouse_club", "food and packaging"),
          "home child care provider": (.30, (25, 90), "grocery_full", "snacks and supplies"), "truck owner-operator": (.70, (280, 720), "gas", "diesel"),
          "shop owner": (.20, (200, 2400), "wholesaler", "inventory"), "hair stylist": (.08, (30, 160), "pharmacy", "color and supplies")}
    for p in sim.persons:
        if p.emp != "self_employed" or not p.works or p.wallet is None:
            continue
        spec = SE.get(p.occ)
        if spec and rng.random() < spec[0]:
            org = sim.pick((spec[2],), p.hh.district, 8.0)
            if org is None:
                continue
            amt = round(rng.uniform(*spec[1]), 2)
            W = p.wallet
            m = next((x for x in ("debit", "credit", "cash") if W.avail(x) >= amt), None)
            t = rng.randint(360, 1020)
            if m is None:
                sim.emit(t, "failed_attempt", "business", "self_employed_supplies", p, p.hh, p, org, gross=amt, tmin=10, outcome="abandoned", fr=("insufficient_funds",),
                         lens=("small_business",), ctx=dict(org=org.name, what=spec[3], reason="the job's materials cost more than was on hand before the customer paid"))
                continue
            fee = round(amt * .035, 2) if (p.occ == "truck owner-operator" and m != "cash") else 0.0
            W.take(m, amt + fee)
            b2b(t, "self_employed_supplies", p, org, amt, user=amt + fee, method=m, fee_type="fuel_card_fee" if fee else "", fee=fee, P=p, H=p.hh, tmin=rng.randint(8, 30),
                ctx=dict(org=org.name, what=spec[3], occ=p.occ))
        if p.occ in ("independent consultant", "freelance designer", "general contractor", "truck owner-operator", "landscaper") and rng.random() < .028:
            amt = round(math.exp(rng.gauss(math.log(2200), .9)), 2)
            sim.emit(rng.randint(540, 1000), "failed_attempt", "business", "overdue_invoice_follow_up", p, p.hh, p, X["x_customers"], channel=rng.choice(["phone", "online"]), gross=amt,
                     tmin=rng.randint(8, 30), outcome=rng.choice(["rescheduled", "rescheduled", "failed", "partial"]), fr=("wait", "paperwork"), lens=("small_business",),
                     ctx=dict(org="my own business", days=rng.choice([31, 36, 45, 52, 60, 75]), amt="%.0f" % amt,
                              said=rng.choice(["the check is in the next run", "accounts payable never got the invoice", "the client wants to wait until the job is finished", "nobody picked up"])))
