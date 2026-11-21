"""Core engine: clock, scheduling, organization choice, payment settlement and record emission."""
import bisect
import csv
import math
import random
import numpy as np
from .config import DIST, INTRA, TRANSIT_SERVED, SALES_TAX, FULL_CITY_HOUSEHOLDS, calendar, weather_mult
from . import text as TX

from .blocks import COLS as BLOCK_COLS

COLS = ["record_id", "timestamp_local", "record_type", "job_category", "job_statement", "actor_person_id", "household_id",
        "from_party_id", "to_party_id", "beneficiary_person_id", "district", "channel", "payment_method", "amount_gross",
        "amount_paid_by_user", "amount_paid_by_third_party", "third_party_payer", "funding_level", "imputed_public_cost",
        "sales_tax", "fee_type", "fee_amount", "time_minutes", "wait_minutes", "travel_miles", "travel_mode", "outcome",
        "friction_tags", "lens_tags", "related_record_id", "narrative"]
CARDS = ("debit", "credit", "prepaid")
FARM_OCC = ("crop farmworker", "packing shed worker", "farm equipment operator", "dairy and livestock worker", "crew leader", "farmer", "farm manager")

MORN = ((345, 560, 1.0),)
LUNCH = ((660, 815, 1.0),)
AFT = ((810, 1020, 1.0),)
EVE = ((1020, 1275, 1.0),)
DAY = ((540, 1020, 1.0),)
ANY = ((400, 1300, 1.0),)
MEAL = ((390, 545, .5), (660, 815, 2.0), (1020, 1240, 2.0))
# Shopping and gas windows: hourly preference weights, filled in for the day by set_day_windows() (lists, so the modules
# that import them see the day's values). Fitted so the realized hours match ATUS 2025 (see config.SHOP_HOURS).
SHOP = [(540, 720, 1.0), (720, 1020, 1.2), (1020, 1250, 1.7)]
GAS = [(330, 560, 1.2), (690, 800, .5), (930, 1290, 1.5)]


def set_day_windows(cal):
    from .config import SHOP_HOURS, GAS_HOURS
    k = "weekday" if cal["weekday"] and not cal["holiday"] else "weekend"
    SHOP[:] = [(h * 60, h * 60 + 60, w) for h, w in sorted(SHOP_HOURS[k].items()) if w > 0]
    GAS[:] = [(h * 60, h * 60 + 60, w) for h, w in sorted(GAS_HOURS[k].items()) if w > 0]
OFFICE = ((525, 960, 1.0),)
NIGHT = ((1140, 1410, 1.0),)


# Extra cash use in the rural districts (v2). DCPC 2025 (sources/raw/dcpc): cash is 13.5% of payments overall and 18.7% for
# respondents in urban_cat 1, the 14% group taken to be rural (the codebook does not label the field). Fitted on the typed-day
# year so D5 and D6 land near 18.7%.
RURAL_CASH = {"D5": 1.12, "D6": 1.12}


def base_cash(a):
    return .38 if a < 5 else .30 if a < 10 else .20 if a < 25 else .13 if a < 50 else .08 if a < 100 else .04


class Sim:
    def __init__(self, cfg):
        self.cfg = cfg
        self.rng = random.Random(cfg["RANDOM_SEED"])
        self.nrg = np.random.default_rng(cfg["RANDOM_SEED"])
        self.cal = calendar(cfg["SIM_DATE"])
        set_day_windows(self.cal)
        from . import config as _C
        self.dow_mult = _C.DOW_PURCHASE[self.cal["dow"]]
        self.wx = weather_mult(cfg["WEATHER"])
        self.scale = cfg["N_HOUSEHOLDS"] / float(FULL_CITY_HOUSEHOLDS)
        self.rows, self.kinds = [], []
        self.accrual = {}
        self.cash_mult = cfg.get("CASH_MULT", 1.0)
        self._pc = {}
        self.stats = {}
        self.seq = 0
        self.down_org = None
        self.incidents = []
        self.trng = random.Random(cfg["RANDOM_SEED"] + 7)
        self.payroll, self.tanf_idx, self.delivery_orders, self.toll_draw = {}, {}, [], {}
        self.passholders, self.skimmed = set(), set()
        self.carry = None             # carry.Carry in a carried run (several days); None in a one-day run

    # ------------------------------------------------------------------ helpers
    def bump(self, k, v=1):
        self.stats[k] = self.stats.get(k, 0) + v

    # v2 phase 5: practices a patient would not be seen at, by patient (close reading: 162 adults a day at pediatric offices)
    NOT_FOR = {"adult_f": ("Pediatric",), "adult_m": ("Pediatric", "Women's Health"),
               "child": ("Internal Medicine", "Women's Health", "Cardiology")}

    def pick(self, kinds, origin, scale=7.0, who=None):
        """One draw, weighted by size and distance. `who` ('child', 'adult_f', 'adult_m') leaves out practices that don't
        see that patient; the draw count is the same either way."""
        if origin not in INTRA:
            origin = "D2"
        key = (kinds, origin, scale, who)
        c = self._pc.get(key)
        if c is None:
            lst, cum, tot = [], [], 0.0
            skip = self.NOT_FOR.get(who, ())
            for k in kinds:
                for o in self.by_kind.get(k, ()):
                    if o.district == "EXT" or o.open is None or any(x in o.name for x in skip):
                        continue
                    tot += (o.size ** .5) * math.exp(-DIST[(origin, o.district)] / scale)
                    lst.append(o)
                    cum.append(tot)
            c = (lst, cum, tot)
            self._pc[key] = c
        if not c[0]:
            return None
        i = bisect.bisect(c[1], self.rng.random() * c[2])
        return c[0][min(i, len(c[0]) - 1)]

    def one(self, kind):
        return self.by_kind[kind][0]

    def dist(self, a, b):
        if a not in INTRA:
            a = "D2"
        if b not in INTRA:
            b = a
        return DIST[(a, b)]

    def init_day(self):
        """Per-day state that is not part of the standing population."""
        rng = self.rng
        self.payroll, self.tanf_idx, self.delivery_orders, self.toll_draw = {}, {}, [], {}
        self.passholders = set()
        for p in self.persons:
            H = p.hh
            if p.mode == "transit" and p.emp.startswith("employed"):
                if rng.random() < .45:
                    self.passholders.add(p.pid)
            elif H.vehicles == 0 and H.district in ("D1", "D2") and p.age >= 16 and rng.random() < .12:
                self.passholders.add(p.pid)
        snap_h = [H.hid for H in self.households if H.snap and H.snap_bal > 60]
        k = sum(1 for _ in snap_h if rng.random() < .0012)
        self.skimmed = set(rng.sample(snap_h, min(len(snap_h), k))) if k else set()
        groc = self.by_kind.get("grocery_full", [])
        self.down_org = rng.choice(groc) if groc else None

    def car_fail(self, H, P, q):
        """A car that will not start, and what the household does about it."""
        from .day_a import push
        rng = self.rng
        commuting = P.works and P.shift and not P.wfh and P.shift[0][0] > 0
        t = max(280, P.shift[0][0] - P.cm - 6) if commuting else rng.randint(450, 720)
        why = rng.choice(["a dead battery", "a dead battery", "a starter that only clicked", "a flat tire found in the driveway", "an empty tank and no cash for gas until payday"])
        W = P.wallet

        def run(t=t):
            i = self.emit(t, "failed_attempt", "transportation", "car_wont_start", P, H, P, "", tmin=rng.randint(8, 25), outcome="failed",
                          fr=("schedule_volatility",) if commuting else ("other",), lens=("land_use",) + (("labor",) if commuting else ()),
                          ctx=dict(why=why, work="1" if commuting else ""))
            r = rng.random()
            if "tank" in why:
                self.emit(t + 10, "non_monetary_job", "transportation", "ride_search", P, H, P, "", channel="phone", tmin=rng.randint(15, 40),
                          outcome="completed" if r < .6 else "abandoned", fr=("insufficient_funds", "no_transit") if H.district not in ("D1", "D2") else ("insufficient_funds",),
                          related=i, ctx=dict(why="the car was out of gas"))
            elif r < .34:
                self.emit(t + 12, "non_monetary_job", "transportation", "jump_start_from_neighbor", P, H, P, "", tmin=rng.randint(15, 40), related=i, ctx=dict(why=why))
            elif r < .68:
                org = self.pick(("towing", "auto_repair"), H.district, 9.0)
                amt = round(rng.uniform(95, 140) + (rng.uniform(150, 230) if "battery" in why or "starter" in why else rng.uniform(25, 60)), 2)
                self.pay(t + rng.randint(35, 80), P, H, W, org, "transportation", "tow_and_roadside_repair", amt, ctx=dict(why=why), tmin=rng.randint(40, 90),
                         wait=rng.randint(25, 80), related=i, quiet_fail=0.0, fr=("price_spike",))
            else:
                amt = round(rng.uniform(14, 38) * (1.6 if H.district in ("D5", "D6", "D3") else 1.0), 2)
                self.pay(t + rng.randint(8, 20), P, H, W, None, "transportation", "ride_hail_trip", amt, channel="app", ctx=dict(why=why), tmin=rng.randint(15, 35),
                         wait=rng.randint(6, 22), related=i, quiet_fail=0.0, to=self.X["x_ride1"])
            if commuting and P.emp != "self_employed" and P.wsched != "fixed" and rng.random() < .45:
                hrs = rng.choice([1, 1.5, 2, 4, 8])
                lost = round(hrs * P.wage / 2080.0, 2)
                self.emit(t + 30, "failed_attempt", "work", "late_or_missed_shift", P, H, P, P.org if P.org is not None else "", gross=lost, tmin=int(hrs * 60),
                          outcome="partial" if hrs < 8 else "failed", fr=("schedule_volatility",), lens=("labor",), related=i,
                          ctx=dict(hrs=hrs, lost="%.2f" % lost, why="the car would not start"))
        push(q, t, run)

    def trip(self, P, H, o_d, d_d, chained=False):
        rng = self.rng
        if o_d not in INTRA:
            o_d = H.district
        if d_d not in INTRA:
            d_d = o_d
        base = INTRA[d_d] * rng.uniform(.35, 1.5) if o_d == d_d else DIST[(o_d, d_d)] * rng.uniform(.92, 1.08)
        miles = base * 2 * (.6 if chained else 1.0)
        car = H.vehicles > 0 and P.age >= 16 and not (P.age >= 86 and P.dis != "none")
        fr = []
        if car:
            mode = "car"
        else:
            ts = min(TRANSIT_SERVED.get(o_d, 0), TRANSIT_SERVED.get(d_d, 0))
            if base <= .9:
                mode = "walk"
            elif rng.random() < ts * .8:
                mode = "transit"
            elif base <= 2.5 and rng.random() < .5:
                mode = "bike" if (P.age < 60 and rng.random() < .4) else "walk"
            else:
                mode = "ride_from_family_or_friend"
            if mode != "transit" and ts < .5 and base > .9:
                fr.append("no_transit")
            if H.flags and "car_lost_today" in H.flags and P.age >= 16:
                fr.append("vehicle_lost")
        mins = {"car": base * 2.1 + 4, "transit": base * 4.6 + 14, "walk": base * 19, "bike": base * 6 + 3}.get(mode, base * 2.1 + 12)
        return round(miles, 1), mode, int(min(mins, 75)), fr

    def slot(self, P, dur, prefs, o=0, c=1440):
        rng = self.rng
        if o is None:
            return None
        dur = max(1, int(dur))
        cands, tot = [], 0.0
        for f in P.free:
            if f[1] - f[0] < dur:
                continue
            for ws, we, w in prefs:
                lo, hi = max(f[0], ws, o), min(f[1], we, c) - dur
                if hi >= lo:
                    tot += w * (hi - lo + 10)
                    cands.append((tot, lo, hi, f))
        if not cands:
            for f in P.free:
                lo, hi = max(f[0], o), min(f[1], c) - dur
                if hi >= lo:
                    tot += hi - lo + 10
                    cands.append((tot, lo, hi, f))
            if not cands:
                return None
        r = rng.random() * tot
        for cm, lo, hi, f in cands:
            if r <= cm:
                break
        t = rng.randint(lo, hi)
        i = P.free.index(f)
        new = []
        if t - f[0] >= 4:
            new.append([f[0], t])
        if f[1] - (t + dur) >= 4:
            new.append([t + dur, f[1]])
        P.free[i:i + 1] = new
        return t

    def slot_soft(self, P, dur, prefs=ANY):
        """Short remote task: use free time if any, otherwise squeeze it into waking hours."""
        t = self.slot(P, dur, prefs)
        if t is None:
            t = self.rng.randint(min(P.wake + 10, 1300), max(P.wake + 20, min(P.bed - 5, 1430)))
        return t

    # ------------------------------------------------------------------ records
    def emit(self, t, rtype, cat, kind, P=None, H=None, frm="", to="", ben="", district=None, channel="in_person",
             method="none", gross=0.0, user=0.0, third=0.0, payer="", fund="", imputed=0.0, tax=0.0, fee_type="", fee=0.0,
             tmin=0, wait=0, miles=0.0, mode="", outcome="completed", fr=(), lens=(), related=None, ctx=None):
        if H is None and P is not None:
            H = P.hh
        t = int(max(0, min(1439, t)))
        if wait > tmin:          # time_minutes counts the wait (v2 phase 5: about 5,200 records a day had a wait longer than their time)
            tmin = tmin + wait
        F = list(dict.fromkeys(fr))
        if fee > 0 and "fee" not in F:
            F.append("fee")
        if wait >= 20 and "wait" not in F:
            F.append("wait")
        if miles >= 24 and "distance" not in F:
            F.append("distance")
        L = list(dict.fromkeys(lens))

        def ad(x):
            if x not in L:
                L.append(x)
        top = cat
        n = len(self.rows)
        # frictions that follow the person rather than the errand (deterministic, so they do not disturb the random stream)
        if H is not None and H.lep and "language" not in F and rtype not in ("benefit_issuance", "income", "tax", "b2b") and (
                (top in ("health", "civic_legal", "public_services") and channel in ("in_person", "phone")) or (top in ("utilities", "money_services", "housing") and channel == "phone")):
            if (n * 37 + t) % 100 < 18:
                F.append("language")
        if P is not None and "disability_access" not in F:
            if P.dis in ("ambulatory", "multiple", "vision") and channel == "in_person" and miles > 0 and top in ("health", "civic_legal", "public_services", "transportation", "food", "discretionary") and (n * 53 + t) % 100 < 6:
                F.append("disability_access")
            elif P.dis == "hearing" and channel == "phone" and (n * 29 + t) % 100 < 30:
                F.append("disability_access")
        if top == "housing":
            ad("housing")
        elif top == "health":
            if user > 0 or outcome != "completed" or "insufficient_funds" in F:
                ad("health_cost")
        elif top == "children_education":
            ad("education")
        elif top == "money_services":
            ad("consumer_finance")
        if rtype in ("benefit_issuance", "public_service_encounter", "tax") or (third > 0 and fund in ("federal", "state", "local", "mixed")):
            ad("public_finance")
        if fee > 0 or "insufficient_funds" in F or "pending_hold" in F or "scam_attempt" in F:
            ad("consumer_finance")
        if "caregiving_conflict" in F:
            ad("family_care")
        if "digital_barrier" in F or "outage" in F or (channel in ("online", "app") and H is not None and H.internet != "yes" and rtype != "income"):
            ad("digital_access")
        if "distance" in F or "no_transit" in F:
            ad("land_use")
        if "schedule_volatility" in F:
            ad("labor")
        if "disability_access" in F:
            ad("disability")
        if P is not None:
            if P.age >= 65 and (F or top in ("health", "income", "care_and_household", "public_services", "civic_legal", "money_services", "utilities", "housing")):
                ad("aging")
            if P.dis not in (None, "none") and (F or top in ("health", "income", "care_and_household", "public_services", "civic_legal", "transportation")):
                ad("disability")
            if P.occ in FARM_OCC and (top in ("income", "work", "business") or "distance" in F or "language" in F):
                ad("farmworker")
        if H is not None and H.district in ("D5", "D6") and (F or miles >= 8 or top in ("health", "public_services", "civic_legal", "utilities", "business", "income", "work")):
            ad("rural")
        js, narr = TX.make(self.trng, kind, ctx or {}, outcome, F, wait, fee, fee_type)
        frm = frm.pid if hasattr(frm, "pid") else frm.oid if hasattr(frm, "oid") else frm
        to = to.pid if hasattr(to, "pid") else to.oid if hasattr(to, "oid") else to
        ben = ben.pid if hasattr(ben, "pid") else ben
        idx = len(self.rows)
        self.rows.append([idx, t, rtype, cat + "." + kind, js, P.pid if P is not None else "", H.hid if H is not None else "",
                          frm, to, ben, district or (H.district if H is not None else ""), channel, method,
                          round(gross, 2), round(user, 2), round(third, 2), payer, fund, round(imputed, 2), round(tax, 2),
                          fee_type, round(fee, 2), int(tmin), int(wait), round(miles, 1), mode, outcome,
                          ";".join(F), ";".join(L), related, narr])
        return idx

    def set_outcome(self, idx, outcome):
        self.rows[idx][26] = outcome

    # ------------------------------------------------------------------ payments
    def methods(self, W, P, amt, channel, org, aware=.8):
        rng = self.rng
        acc = org.acc if org is not None and org.acc else {"cash", "debit", "credit", "prepaid"}
        has_d = W.bank is not None and ("debit" in acc)
        has_c = W.cc_limit > 0 and ("credit" in acc)
        has_p = W.prepaid is not None and ("prepaid" in acc or "debit" in acc)
        order = []
        if has_c and has_d:
            pc = (.42 if W.revolver else .72) + (.06 if channel != "in_person" else 0)
            if W.cc_limit - W.cc_bal < amt:
                pc = .08
            order = ["credit", "debit"] if rng.random() < pc else ["debit", "credit"]
        elif has_c:
            order = ["credit"]
        elif has_d:
            order = ["debit"]
        if has_p:
            if W.bank is None or rng.random() < .3:
                order.insert(0, "prepaid")
            else:
                order.append("prepaid")
        if channel != "in_person":
            out = order
        else:
            out = []
            cash_ok = "cash" in acc and W.cash >= amt
            pcash = base_cash(amt) * (.35 + 2.6 * P.cashpref) * self.cash_mult * RURAL_CASH.get(P.hh.district, 1.0)
            if W.bank is None:
                pcash = .62 if has_p else .9
            if cash_ok and rng.random() < min(.95, pcash):
                out.append("cash")
            out += order
            if "cash" in acc and "cash" not in out and (W.cash >= amt or not out):
                out.append("cash")
        # most people know when a card will not clear and do not try it
        # (carried runs: someone whose account is already below zero knows it and rarely tries the card; carry.py)
        keep = [m for m in out if W.avail(m) >= amt or (m == "debit" and W.od and rng.random() < (.35 if self.carry is None or W.bank >= 0 else .10))
                or rng.random() > aware]
        return keep

    def pay(self, t, P, H, W, org, cat, kind, amt, taxable=False, channel="in_person", ctx=None, tmin=0, wait=0, miles=0.0,
            mode="", fr=(), lens=(), rtype="purchase", force=None, fee=None, ben="", allow_partial=False, related=None,
            quiet_fail=.65, third=0.0, payer="", fund="", to=None, defer=0.0, zero="none", imputed=0.0):
        """Settle one consumer payment against the wallet. Returns (record index or None, outcome, method)."""
        rng = self.rng
        ctx = ctx or {}
        tax = round(amt * SALES_TAX, 2) if taxable else 0.0
        total = round(amt + tax, 2)
        ftype, famt = fee or ("", 0.0)
        need = round(max(0.0, total + famt - third - defer), 2)
        ctx.setdefault("org", org.name if org is not None else "")
        ctx.setdefault("amt", "%.2f" % need)
        done = "partial" if defer > 0 else "completed"
        if defer > 0:
            ctx["later"] = "%.2f" % defer
        to = to if to is not None else org
        if need < .005:
            i = self.emit(t, rtype, cat, kind, P, H, P, to, ben, channel=channel, method=zero, gross=total, user=0.0, third=third,
                          payer=payer, fund=fund, imputed=imputed, tax=tax, tmin=tmin, wait=wait, miles=miles, mode=mode, outcome=done,
                          fr=fr, lens=lens, related=related, ctx=ctx)
            return i, done, zero
        meths = list(force) if force else self.methods(W, P, need, channel, org)
        to = to if to is not None else org
        if not meths:
            if rng.random() < quiet_fail:
                return None, "skipped", None
            ctx["reason"] = "there was not enough money on hand or on any card"
            i = self.emit(t, "failed_attempt", cat, kind, P, H, P, to, ben, channel=channel, method="none", gross=total, tax=tax,
                          tmin=max(1, tmin // 3), miles=miles, mode=mode, outcome="abandoned", fr=tuple(fr) + ("insufficient_funds",),
                          lens=lens, related=related, ctx=ctx)
            self.bump("unaffordable")
            return i, "abandoned", None
        prev, tech_done, last_fail = related, False, None
        k = 0
        while k < len(meths):
            m = meths[k]
            k += 1
            have = W.avail(m)
            tech = (not tech_done) and m in CARDS and rng.random() < (.022 if channel in ("online", "app") else .0055)
            down = m in CARDS and org is not None and org is self.down_org and self.cfg["CARD_READER_OUTAGE"][0] <= t <= self.cfg["CARD_READER_OUTAGE"][1]
            f2type, f2 = ftype, famt
            od = False
            if m == "debit" and have < need and not tech and not down and W.od and need - max(have, 0) <= 260 and (self.carry is None or self.carry.od_ok(W, need)):
                od = True
                f2type, f2 = (ftype + "+overdraft_fee" if ftype else "overdraft_fee"), famt + W.od_fee
            if (have >= need or od) and not tech and not down:
                paid = need + (W.od_fee if od else 0)
                W.take(m, paid)
                if org is not None:
                    org.ntx += 1
                    org.rev += total
                    if m == "credit":
                        org.cc += total
                    elif m in ("debit", "prepaid"):
                        org.dc += total
                    elif m == "cash":
                        org.csh += total
                F = list(fr)
                if od:
                    F += ["insufficient_funds"]
                    self.bump("overdraft")
                if last_fail is not None:
                    ctx["retry"] = m
                i = self.emit(t, rtype, cat, kind, P, H, P, to, ben, channel=channel, method=m, gross=total, user=paid, third=third,
                              payer=payer, fund=fund, imputed=imputed, tax=tax, fee_type=f2type, fee=f2, tmin=tmin, wait=wait, miles=miles, mode=mode,
                              outcome=done, fr=F, lens=lens, related=prev, ctx=ctx)
                if od and self.carry is not None:
                    self.carry.overdraft(self, W, i)
                return i, done, m
            why = "outage" if down else ("other" if tech else "insufficient_funds")
            if tech:
                tech_done = True
                if rng.random() < .6:
                    meths.insert(k, m)
            c2 = dict(ctx)
            c2["reason"] = {"outage": "the card readers were down", "other": rng.choice(["the chip would not read", "the bank flagged the charge for review", "the card on file had expired", "the terminal timed out"]),
                            "insufficient_funds": ("the card was over its limit" if m == "credit" else "there was not enough in the account")}[why]
            c2["method"] = m
            last_fail = self.emit(t, "failed_attempt", cat, kind, P, H, P, to, ben, channel=channel, method=m, gross=total, tax=tax,
                                  tmin=max(1, min(6, tmin // 2 + 1)), wait=wait, miles=miles, mode=mode, outcome="declined",
                                  fr=tuple(fr) + (why,), lens=lens, related=prev, ctx=c2)
            self.bump("declined_" + why)
            prev = last_fail
            t += rng.randint(1, 4)
            wait, miles = 0, 0.0
        # every method failed
        if allow_partial:
            best = max(("cash", "debit", "prepaid", "credit"), key=lambda m: W.avail(m) if (m == "cash" or org is None or m in org.acc) else -1)
            have = W.avail(best)
            if have >= 6:
                part = round(min(have, need) * rng.uniform(.75, .98), 2)
                if part < need:
                    W.take(best, part)
                    if org is not None:
                        org.ntx += 1
                        org.rev += part
                        if best == "cash":
                            org.csh += part
                    ptax = round(part - part / (1 + SALES_TAX), 2) if taxable else 0.0
                    ctx["short"] = "%.2f" % (need - part)
                    i = self.emit(t, rtype, cat, kind, P, H, P, to, ben, channel=channel, method=best, gross=part, user=part, tax=ptax,
                                  tmin=tmin, miles=0, mode=mode, outcome="partial", fr=tuple(fr) + ("insufficient_funds",), lens=lens,
                                  related=prev, ctx=ctx)
                    return i, "partial", best
        if last_fail is not None:
            self.set_outcome(last_fail, "abandoned" if self.rows[last_fail][27].find("outage") < 0 else "failed")
        return last_fail, "abandoned", None

    def credit(self, W, amt, how="bank"):
        """Money arriving in a wallet."""
        if how == "bank" and W.bank is None:
            how = "prepaid" if W.prepaid is not None else "cash"
        W.give(how, amt)
        return how

    # ------------------------------------------------------------------ output
    def write_records(self, path, overrides=None, tagger=None):
        rows = self.rows
        order = sorted(range(len(rows)), key=lambda i: (rows[i][1], i))
        rid = [None] * len(rows)
        for n, i in enumerate(order):
            rid[i] = "R%07d" % (n + 1)
        self.rid = rid
        date = self.cal["iso"]
        nover = 0
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(COLS + (BLOCK_COLS if tagger else []))
            for i in order:
                r = list(rows[i])
                if tagger:
                    r += tagger.tag(rows[i])
                r[0] = rid[i]
                r[1] = "%sT%02d:%02d:00" % (date, r[1] // 60, r[1] % 60)
                r[29] = rid[r[29]] if r[29] is not None else ""
                for j in (13, 14, 15, 18, 19, 21):
                    r[j] = "%.2f" % r[j]
                if overrides and r[0] in overrides:
                    ov = overrides[r[0]]
                    if ov[0] == r[3] and ov[1] == r[5]:
                        r[4], r[30] = ov[2], ov[3]
                        nover += 1
                w.writerow(r)
        return nover
