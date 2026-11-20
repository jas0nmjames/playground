"""Carried state for runs of several days (plan section 4, option B; phase 4).

A one-day run starts every household from the opening balances and draws the day's events on their own. A carried run
(simulate.py --days N, --state-in, or --carry) also hands each day's unfinished business to the next one.

Nothing here runs in a one-day run. Every hook in the rest of the simulator is guarded by `sim.carry is not None`, and
the guard comes before any random draw, so the one-day path (and with it the typed-day year) stays byte for byte as it
was. Decisions made only in carried runs draw from `crng`, a stream of their own for the date, so they do not shift the
day's main stream more than the changed balances already do.

Records keep their one-day schema. A chain that crosses days is written to `links.csv` beside `records.csv`: one row per
record that belongs to a chain, naming the chain, its step and the earlier record (date and record id) it follows from.
"""
import csv
import datetime as dt
import os
import random

LINK_COLS = ["record_id", "chain", "chain_id", "step", "account_id", "household_id", "earlier_date", "earlier_record_id", "note"]


def D(s):
    return dt.date.fromisoformat(s)


class Carry:
    def __init__(self, seed, first):
        self.seed = seed
        self.first = first          # ISO date of the run's first carried day
        self.date = None            # ISO date of the day being simulated
        self.n = 0                  # carried days simulated before this one
        self.seq = 0                # id counter for chains and queue entries
        self.retries = []           # bills waiting to be paid again (retry queue)
        self.util = {}              # household id -> shutoff notice timer
        self.od = {}                # account id -> overdraft streak
        self.loans = []             # open payday and online installment loans
        self.tloans = {}            # household id -> title loan (None once paid off or repossessed)
        self.cars_lost = {}         # household id -> cars repossessed during the run
        self.refunded = set()       # accounts that received this tax season's refund
        self.filed = set()          # households that filed this tax season
        self.links = []             # today's links.csv rows (record ids filled in after the day is written)
        self.refs = []              # references to today's records waiting for their record ids

    # ------------------------------------------------------------------ state
    @classmethod
    def from_state(cls, st):
        c = cls(st["seed"], st["first"])
        c.n, c.seq = st["n"], st["seq"]
        c.retries, c.util, c.od, c.loans = st["retries"], st["util"], st["od"], st["loans"]
        c.tloans, c.cars_lost = st["tloans"], st["cars_lost"]
        c.refunded, c.filed = set(st["refunded"]), set(st["filed"])
        return c

    def to_state(self):
        return dict(seed=self.seed, first=self.first, n=self.n + 1, seq=self.seq, retries=self.retries, util=self.util, od=self.od,
                    loans=self.loans, tloans=self.tloans, cars_lost=self.cars_lost, refunded=sorted(self.refunded), filed=sorted(self.filed))

    def new_id(self, prefix):
        self.seq += 1
        return "%s%06d" % (prefix, self.seq)

    # ------------------------------------------------------------------ the day
    def start_day(self, sim):
        """Called once the city is built and the carried balances are loaded, before the day is simulated."""
        sim.carry = self
        self.date = sim.cal["iso"]
        self.today = sim.cal["date"]
        self.crng = random.Random("carry|%s|%s" % (self.seed, self.date))
        self.links, self.refs = [], []
        self.hh = {H.hid: H for H in sim.households}
        self.wal = {W.wid: W for W in sim.wallets}
        self.per = {p.pid: p for p in sim.persons}
        self.org = {o.oid: o for o in sim.orgs}
        self._cal = {}

    def begin_day(self, sim, q):
        """After the day's schedules are drawn and before the households' own plans: carried obligations come first."""
        set_aside_for_bills(self, sim)
        retry_day(self, sim, q)
        shutoff_day(self, sim, q)

    def end_day(self, sim):
        """After the day's queue has run and card payments have posted."""

    def after_write(self, sim, out):
        """Record ids exist only once records.csv is written: resolve today's references and write links.csv."""
        rid = sim.rid
        for ref in self.refs:
            ref["rid"] = rid[ref.pop("idx")]
        with open(os.path.join(out, "links.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(LINK_COLS)
            rows = []
            for L in self.links:
                e = L["earlier"] or {}
                rows.append([rid[L["idx"]], L["chain"], L["chain_id"], L["step"], L["wid"], L["hid"], e.get("date", ""), e.get("rid", ""), L["note"]])
            rows.sort(key=lambda r: (r[0], r[1], r[3]))
            w.writerows(rows)
        return len(self.links)

    # ------------------------------------------------------------------ helpers
    def ref(self, idx):
        """A reference to one of today's records, filled in with its record id after the day is written."""
        r = {"date": self.date, "idx": idx}
        self.refs.append(r)
        return r

    def link(self, idx, chain, chain_id, step, W=None, H=None, earlier=None, note=""):
        """Put today's record `idx` into a chain. `earlier` is a reference from ref() (today or an earlier day)."""
        if idx is None:
            return None
        if H is None and W is not None:
            H = W.hh
        self.links.append(dict(idx=idx, chain=chain, chain_id=chain_id, step=step, wid=W.wid if W is not None else "",
                               hid=H.hid if H is not None else "", earlier=earlier, note=note))
        return self.ref(idx)

    def cal(self, d):
        """The simulator's calendar for another day (cached)."""
        c = self._cal.get(d)
        if c is None:
            from .config import calendar
            c = self._cal[d] = calendar(d)
        return c

    def days_from_today(self, iso):
        return (D(iso) - self.today).days

    def next_bank_day(self, d):
        while not self.cal(d)["bank_day"]:
            d += dt.timedelta(days=1)
        return d

    def add_bank_days(self, n):
        d = self.today
        while n > 0:
            d += dt.timedelta(days=1)
            if self.cal(d)["bank_day"]:
                n -= 1
        return d


# ---------------------------------------------------------------------------------------------- 1. retry queue for unpaid bills
# Who tries a missed bill again, and when (estimates, from common practice; no counting source):
# - An autopay that bounces is re-presented by billers that usually do: lenders, card issuers, insurers and schools.
#   NACHA's rules allow a returned debit to be presented again at most twice, and billers commonly wait a few business
#   days: here 3, then 5 more. After that the household has to pay by hand.
# - Landlords and utilities do not re-present. The household pays by hand on the next day money comes in (a paycheck,
#   Social Security, SSI, a pension or unemployment), or in 3 to 6 days when nothing is due within two weeks. It gives up
#   for the month after four tries; the bill stays past due in the carried state.
# - A card autopay that declines is retried by the merchant 2 and 5 days later, then dropped (the subscription lapses).
# - Savings and giving (investment and 529 contributions, tithes, donations) are not retried.
# Each missed bill carries the returned-payment fee its bounce drew, and a late fee from the bill's terms (LATE_FEE in
# day_a) once the payment is later than the grace period below. Rent's grace runs to the 5th, as in the one-day simulator.
REPRESENT = {"car_payment", "credit_card_payment", "student_loan_payment", "personal_loan_payment", "auto_insurance", "health_premium",
             "medigap_premium", "life_insurance", "mortgage", "bnpl_installment", "rent_to_own_payment", "medical_payment_plan",
             "college_payment_plan", "private_school_tuition", "home_insurance", "renters_insurance", "hoa_dues"}
NO_RETRY = {"investment_contribution", "college_savings_contribution", "recurring_donation", "recurring_tithe", "cleaning_service"}
CARD_ONLY = {"streaming_subscription", "other_subscription", "gym_membership", "pet_insurance"}
GRACE = {"rent": "5th", "lot_rent": "5th", "mortgage": 15, "car_payment": 10, "credit_card_payment": 1, "auto_insurance": 10,
         "electric_bill": 5, "gas_bill": 5, "water_bill": 5, "internet_bill": 5, "phone_bill": 5}
PARTIAL_OK = {"rent", "lot_rent", "electric_bill", "gas_bill", "water_bill", "car_payment", "bhph_car_payment"}
# Households that would be ready for a bill (finance.build_finance gives a one-day run's opening balances the same shares)
READY = {"poverty": .80, "alice": .90, "above": .97}


def set_aside_for_bills(c, sim):
    """In a one-day run the opening balance already holds the money set aside for the day's autopays
    (finance.build_finance). A carried day opens with yesterday's balances, so on the morning a bill is due the household
    moves the money from savings itself, as far as savings go (no money is made up), and the move is recorded."""
    from .day_a import due_today
    from .engine import ANY
    need = {}
    for H in sim.households:
        for b in H.bills:
            if b[4] not in ("p2p", "check_hand", "cash_hand") and due_today(b, sim.cal):
                need[b[5].wid] = need.get(b[5].wid, 0.0) + b[2]
    for wid, due in need.items():
        W = c.wal.get(wid)
        if W is None or W.bank is None or W.savings < 5 or W.bank >= due * 1.02 or c.crng.random() >= READY[W.status]:
            continue
        amt = round(min(W.savings, due * c.crng.uniform(1.03, 1.5) + c.crng.uniform(0, 40) - W.bank), 2)
        P = next((a for a in W.owners if a.age >= 18 and not a.inpatient), None)
        if amt < 5 or P is None:
            continue
        W.savings -= amt
        W.bank += amt
        sim.emit(c.crng.randint(5, 80), "transfer", "money_services", "transfer_from_savings", P, W.hh, P, W.bank_org, channel="app", method="ach",
                 gross=amt, tmin=3, ctx=dict(org=W.bank_org.name, amt="%.0f" % amt))
REPRESENT_GAPS = (3, 5)
CARD_GAPS = (2, 3)
MAX_MANUAL = 4


def bill_missed(c, sim, H, bi, W, P, idx, owed, fees=0.0, late=0.0, how="missed"):
    """A bill payment that failed (or was only partly paid) today joins the retry queue. `owed` is what is still unpaid of
    the bill itself, `fees` the returned-payment fee the failure drew, `late` a late fee already charged with it."""
    b = H.bills[bi]
    kind = b[0]
    if kind in NO_RETRY or owed < 1.0:
        return
    eid = c.new_id("B")
    first = c.link(idx, "unpaid_bill", eid, how, W=W)
    if how == "returned" and kind in REPRESENT:
        mode, nxt = "represent", c.add_bank_days(REPRESENT_GAPS[0])
    elif kind in CARD_ONLY:
        mode, nxt = "card", c.today + dt.timedelta(days=CARD_GAPS[0])
    else:
        mode, nxt = "manual", next_money_day(c, sim, W)
    c.retries.append(dict(id=eid, hid=H.hid, wid=W.wid, pid=P.pid, bill=bi, kind=kind, org=b[1].oid, owed=round(owed, 2), fees=round(fees + late, 2),
                          due=c.date, late=bool(late), ret=bool(fees), tries=1, mode=mode, next=nxt.isoformat(), last=first))


def next_money_day(c, sim, W):
    """The next day money comes into the account (after today), or 3-6 days out when nothing is due within two weeks."""
    from .day_a import paid_today
    owners = [p for p in W.owners if p.age >= 16]
    H = W.hh
    for k in range(1, 15):
        d = c.today + dt.timedelta(days=k)
        cal = c.cal(d)
        for p in owners:
            if p.emp in ("employed_full_time", "employed_part_time") and p.org is not None and paid_today(p, cal):
                return d
            if (p.ss and p.ss_cohort in cal["ss_cohorts"]) or ((p.ssi or p.va) and cal["ssi_today"]) or (p.pension and d.day == 1):
                return d
            if p.ui and cal["bank_day"] and (int(p.pid[1:]) % 5) == cal["dow"]:
                return d
        if W is H.wallets[0] and H.tanf and H.tanf_day == d.day:
            return d
    return c.today + dt.timedelta(days=c.crng.randint(3, 6))


def late_fee_due(c, e, b):
    """Has the grace period on this bill run out (as of today)?"""
    g = GRACE.get(e["kind"])
    if g is None:
        return False
    due = D(e["due"])
    if g == "5th":
        return c.today.day > 5 or (c.today.year, c.today.month) > (due.year, due.month)
    return (c.today - due).days > g


def retry_day(c, sim, q):
    """Schedule today's retries. Each runs at its own time and settles against the account as it stands then."""
    from .day_a import LATE_FEE, push
    from .engine import ANY, SHOP
    keep, today = [], c.date
    for e in c.retries:
        if e["next"] is None or e["next"] > today:
            keep.append(e)
            continue
        H, W, P = c.hh.get(e["hid"]), c.wal.get(e["wid"]), c.per.get(e["pid"])
        if H is None or W is None or e["bill"] >= len(H.bills) or H.bills[e["bill"]][0] != e["kind"]:
            continue
        if P is None or P.age < 18 or P.inpatient:
            P = next((a for a in W.owners if a.age >= 18 and not a.inpatient), None)
            if P is None:
                keep.append(dict(e, next=(c.today + dt.timedelta(days=1)).isoformat()))
                continue
        b = H.bills[e["bill"]]
        if e["mode"] == "represent" and not sim.cal["bank_day"]:
            keep.append(dict(e, next=c.next_bank_day(c.today).isoformat()))
            continue
        if not e["late"] and e["kind"] in LATE_FEE and late_fee_due(c, e, b):
            lf = float(c.crng.randint(*LATE_FEE[e["kind"]]))
            e["late"] = True
            e["fees"] = round(e["fees"] + lf, 2)
            e["late_now"] = lf
        keep.append(e)
        if e["mode"] == "represent":
            t = c.crng.randint(90, 420)
        elif e["mode"] == "card":
            t = c.crng.randint(30, 430)
        else:
            t = sim.slot_soft(P, c.crng.randint(4, 12), ((420, 540, 1), (690, 780, 1), (1020, 1320, 2)))
        push(q, t, lambda t=t, e=e, H=H, W=W, P=P, b=b: retry_attempt(c, sim, t, e, H, W, P, b))
    c.retries = keep


def retry_attempt(c, sim, t, e, H, W, P, b):
    from .finance import BILL_CAT
    kind, org = e["kind"], b[1]
    cat = BILL_CAT[kind][0]
    owed, fees = e["owed"], e["fees"]
    need = round(owed + fees, 2)
    late_days = (c.today - D(e["due"])).days
    n = e.get("n", 1) + 1           # payment attempts so far, not counting quiet waits
    ordinal = {2: "second", 3: "third", 4: "fourth", 5: "fifth"}.get(n, "%dth" % n)
    ctx = dict(org=org.name, amt="%.2f" % need, bill=kind.replace("_", " "))
    lf = e.pop("late_now", 0.0)
    if lf:
        ctx["late"] = "%.0f" % lf
    ftype = "+".join(x for x in (("late_fee" if e["late"] else ""), ("returned_payment_fee" if e.get("ret") else "")) if x) if fees else ""
    paid, method, channel, oc, trip = 0.0, "ach", "automatic", None, None
    if e["mode"] in ("represent", "card"):
        ctx["again"] = ("%s try: %s sent the payment again %d days after the first one %s" %
                        (ordinal, org.name, late_days, "bounced" if e["mode"] == "represent" else "was declined"))
        if e["mode"] == "represent":
            have = W.bank if W.bank is not None else -1.0
            if have >= need:
                W.take("ach", need)
                paid, oc = need, "completed"
            elif W.od and need - max(have, 0) < 900 and c.crng.random() < .6:
                W.take("ach", need + W.od_fee)
                sim.bump("overdraft")
                paid, oc = need + W.od_fee, "overdraft"
        else:
            i, oc0, m = sim.pay(t, P, H, W, None, cat, kind, need, channel="automatic", ctx=dict(ctx), rtype="bill_payment", quiet_fail=0.0, to=org,
                                fee=(ftype, fees) if fees else None)
            return _settle(c, sim, e, W, i, "paid_late" if oc0 == "completed" else "failed_again", need if oc0 == "completed" else 0.0, owed)
    else:
        # The household pays by hand once money is in. Someone who can see there is still not enough waits for the next
        # payday instead of trying (no record); a landlord or utility takes part of what is owed.
        ctx["again"] = "%s try, %d days after it was due" % (ordinal, late_days)
        method = "ach" if W.bank is not None else "cash"
        channel = ("online" if H.internet != "no" else "phone") if W.bank is not None else "in_person"
        have = W.avail(method)
        mn = round(max(35.0, .03 * owed), 2)
        if have >= need:
            paid, oc = need, "completed"
        elif kind == "credit_card_payment" and have >= mn + fees + 20:
            paid, oc = round(mn + fees, 2), "completed"
            ctx["again"] += "; paid the minimum, and the rest stays on the card"
        elif kind in PARTIAL_OK and have - fees > 20:
            paid, oc = round(have * c.crng.uniform(.6, .95), 2), "partial"
        else:
            return _settle(c, sim, e, W, None, "waited", 0.0, owed)
        W.take(method, paid)
        if channel == "in_person":
            dest = org if (org.open is not None and org.district != "EXT") else (sim.pick(("check_casher", "grocery_full", "supercenter"), H.district, 6.0) or org)
            miles, mode, mins, tfr = sim.trip(P, H, H.district, dest.district if dest.district != "EXT" else H.district)
            trip = dict(tmin=12 + mins, wait=c.crng.randint(0, 15), miles=miles, mode=mode)
            ctx["at"] = dest.name
    kw = trip or dict(tmin=0 if channel == "automatic" else 6)
    if oc in ("completed", "overdraft"):
        odf = W.od_fee if oc == "overdraft" else 0.0
        ft = "+".join(x for x in (ftype, "overdraft_fee" if odf else "") if x)
        i = sim.emit(t, "bill_payment", cat, kind, P, H, P, org, channel=channel, method=method, gross=owed, user=paid, fee_type=ft, fee=fees + odf,
                     fr=["insufficient_funds"] if odf else [], ctx=ctx, **kw)
        return _settle(c, sim, e, W, i, "paid_late", paid - odf, owed)
    if oc == "partial":
        ctx["short"] = "%.2f" % (need - paid)
        i = sim.emit(t, "bill_payment", cat, kind, P, H, P, org, channel=channel, method=method, gross=owed, user=paid, fee_type=ftype, fee=min(fees, paid),
                     outcome="partial", fr=["insufficient_funds"], ctx=ctx, **kw)
        return _settle(c, sim, e, W, i, "partial", paid, owed)
    ctx["reason"] = ("the re-sent payment bounced again" if e["mode"] == "represent" else
                     "there was still not enough in the account" if W.bank is not None else "there was still not enough cash")
    rf = float(c.crng.choice([15, 20, 25, 25, 30, 35])) if e["mode"] == "represent" else 0.0
    i = sim.emit(t, "failed_attempt", cat, kind, P, H, P, org, channel=channel, method=method, gross=owed, fee_type="returned_payment_fee" if rf else "",
                 fee=rf, tmin=0, outcome="failed", fr=["insufficient_funds"], ctx=ctx)
    e["fees"] = round(e["fees"] + rf, 2)
    e["ret"] = e.get("ret") or bool(rf)
    return _settle(c, sim, e, W, i, "failed_again", 0.0, owed)


def _settle(c, sim, e, W, i, step, paid, owed):
    """Update the queue entry after an attempt: drop it once paid, otherwise set the next try."""
    if i is not None:
        e["last"] = c.link(i, "unpaid_bill", e["id"], step, W=W, earlier=e["last"])
        e["n"] = e.get("n", 1) + 1
    e["tries"] += 1
    if step == "paid_late":
        e["next"] = None
        e["done"] = True
        c.retries.remove(e)
        return
    if step == "partial":
        fees = e["fees"]
        e["fees"] = round(max(0.0, fees - paid), 2)
        e["owed"] = round(owed - max(0.0, paid - fees), 2)
        if e["fees"] < 1.0:                 # a few cents of fee left over go back on the bill
            e["owed"] = round(e["owed"] + e["fees"], 2)
            e["fees"], e["ret"] = 0.0, False
        if e["owed"] < 1.0:
            c.retries.remove(e)
            return
    if e["mode"] == "represent" and e["tries"] <= len(REPRESENT_GAPS):
        e["next"] = c.add_bank_days(REPRESENT_GAPS[e["tries"] - 1]).isoformat()
    elif e["mode"] == "card":
        if e["tries"] <= len(CARD_GAPS):
            e["next"] = (c.today + dt.timedelta(days=CARD_GAPS[e["tries"] - 1])).isoformat()
        else:
            c.retries.remove(e)       # the subscription lapses
    else:
        if e["mode"] == "represent":
            e["mode"] = "manual"
        e["next"] = next_money_day(c, sim, W).isoformat() if e["tries"] <= MAX_MANUAL else None


# ---------------------------------------------------------------------------------------------- 2. notice-to-shutoff timers
# A shutoff notice gives a date. Before it, the household pays the past-due balance, sets up a payment plan, or asks the
# community action agency for crisis help; if none of that happens, a crew disconnects the service on a business day
# (Monday to Thursday) soon after the date. Getting it back costs the past-due amount (or the part the utility asks
# for) plus a reconnection fee, a phone call with a wait, a trip to a payment counter for anyone paying cash, and a
# reconnection the next business day; gas needs a technician and someone at home for a four-hour window.
# Sources: Form EIA-112, 2024 (sources/derived/eia112_disconnections_2024.csv): 85% of electric and 71% of gas
# disconnections are followed by a reconnection. The target pair T16 (40-55 notices a day) and T05 (11-12 disconnections a
# day) means about one notice in four ends in a shutoff (EIA counts every final notice, often several per household, and
# finds one in seven). The response shares below are estimates fitted to those two figures on the carried month.
CREW_DAYS = (0, 1, 2, 3)                # Monday to Thursday
CREW_LAG = (0, 0, 1, 2)                 # business days after the notice date before the crew comes (estimate)
PAY_IN_FULL, PLAN, PLAN_DOWN, ASK_HELP, HELP_PLEDGE = .85, .55, (.3, .5), .70, .30
RECONNECT_FEE = (35.0, 45.0, 50.0, 75.0)
NOTICE_WARM_DAYS = 10


def can_notice(c, H):
    """No second notice while one is running or the service is off."""
    return H.hid not in c.util


def notice_sent(c, sim, H, util, P, idx, past, days):
    """Today's notice (day_c.gen_misc) starts a timer."""
    tid = c.new_id("U")
    first = c.link(idx, "utility_shutoff", tid, "notice", W=H.wallets[0])
    due = c.today + dt.timedelta(days=days)
    c.util[H.hid] = dict(id=tid, hid=H.hid, pid=P.pid, bill=util[0], org=util[1].oid, past=round(past, 2), notice=c.date, due=due.isoformat(),
                         state="notice", off=None, plan=False, tries=0, last=first)


def warm_notices(c, sim):
    """A run's first day inherits the notices sent in the ten days before it that are still running (no records; those
    days are not simulated). Same rate and eligibility as day_c.gen_misc."""
    from .day_c import SHUTOFF_NOTICE
    for H in sim.households:
        if H.gq or H.alice == "above" or H.util_incl or H.hid in c.util:
            continue
        util = next((b for b in H.bills if b[0] in ("electric_bill", "gas_bill", "water_bill")), None)
        ad = [p for p in H.adults if not p.inpatient and p.wallet is not None]
        if util is None or not ad:
            continue
        for k in range(1, NOTICE_WARM_DAYS + 1):
            if c.crng.random() < SHUTOFF_NOTICE:
                days = c.crng.choice([5, 7, 10])
                due = c.today - dt.timedelta(days=k) + dt.timedelta(days=days)
                if due >= c.today:
                    c.util[H.hid] = dict(id=c.new_id("U"), hid=H.hid, pid=c.crng.choice(ad).pid, bill=util[0], org=util[1].oid,
                                         past=round(util[2] * c.crng.uniform(1.6, 3.2), 2), notice=(c.today - dt.timedelta(days=k)).isoformat(),
                                         due=due.isoformat(), state="notice", off=None, plan=False, tries=0, last=None, warm=True)
                break


def shutoff_day(c, sim, q):
    from .day_a import push
    if c.n == 0 and not c.util:
        warm_notices(c, sim)
    for hid in list(c.util):
        T = c.util[hid]
        H = c.hh.get(hid)
        P = c.per.get(T["pid"])
        if H is None or P is None:
            del c.util[hid]
            continue
        if P.inpatient:
            P = next((a for a in H.adults if not a.inpatient and a.wallet is not None), None)
            if P is None:
                continue
        if T["state"] == "notice":
            due = D(T["due"])
            if c.today >= due - dt.timedelta(days=1) and not T.get("decided"):
                T["decided"] = True
                t = sim.slot_soft(P, 15, ((480, 1260, 1.0),))
                push(q, t, lambda T=T, H=H, P=P, t=t: notice_response(c, sim, T, H, P, t))
            elif c.today >= due and sim.cal["bank_day"] and sim.cal["dow"] in CREW_DAYS:
                lag = c.crng.choice(CREW_LAG)
                if (c.today - due).days >= lag:
                    t = c.crng.randint(480, 660)
                    push(q, t, lambda T=T, H=H, P=P, t=t: disconnect(c, sim, T, H, P, t))
        elif T["state"] == "off":
            if T.get("reconnect_on") == c.date:
                t = c.crng.randint(540, 960)
                push(q, t, lambda T=T, H=H, P=P, t=t: reconnect(c, sim, T, H, P, t))
            elif not T.get("reconnect_on") and T.get("next") and T["next"] <= c.date:
                t = sim.slot_soft(P, 20, ((540, 1200, 1.0),))
                push(q, t, lambda T=T, H=H, P=P, t=t: try_reconnect(c, sim, T, H, P, t))


def _util(c, T):
    return c.org[T["org"]], T["bill"].replace("_bill", "")


def notice_response(c, sim, T, H, P, t):
    """The day before the shutoff date: pay, set up a plan, or ask for help. Whatever is not settled is shut off."""
    org, what = _util(c, T)
    W = H.wallets[0]
    past = T["past"]
    have = max(W.bank or 0.0, 0.0) + W.cash
    if have >= past * 1.1 and c.crng.random() < PAY_IN_FULL:
        i, oc, m = sim.pay(t, P, H, W, None, "utilities", "past_due_utility_payment", past, channel="phone" if W.bank is not None else "in_person",
                           ctx=dict(org=org.name, what=what), tmin=c.crng.randint(6, 15), wait=c.crng.randint(0, 20), rtype="bill_payment", quiet_fail=0.0,
                           to=org, lens=("housing",))
        if oc == "completed":
            c.link(i, "utility_shutoff", T["id"], "paid_before_shutoff", W=W, earlier=T["last"])
            del c.util[H.hid]
            return
    if have >= past * PLAN_DOWN[0] and c.crng.random() < PLAN:
        down = round(past * c.crng.uniform(*PLAN_DOWN), 2)
        i, oc, m = sim.pay(t, P, H, W, None, "utilities", "utility_payment_arrangement", down, channel="phone", ctx=dict(org=org.name, what=what, down="%.2f" % down,
                           rest="%.2f" % (past - down)), tmin=c.crng.randint(15, 35), wait=c.crng.randint(8, 40), rtype="bill_payment", quiet_fail=0.0, to=org,
                           lens=("housing",))
        if oc == "completed":
            T["last"] = c.link(i, "utility_shutoff", T["id"], "payment_plan", W=W, earlier=T["last"])
            T["past"] = round(past - down, 2)
            T["due"] = (c.today + dt.timedelta(days=c.crng.choice([14, 21, 28]))).isoformat()
            T["decided"], T["plan"] = False, True
            return
    if c.crng.random() < ASK_HELP:
        ca = sim.one("community_action")
        pledge = c.crng.random() < HELP_PLEDGE and sim.cal["weekday"]
        i = sim.emit(t, "non_monetary_job", "utilities", "sought_emergency_utility_help", P, H, P, ca, channel="phone", tmin=c.crng.randint(15, 40),
                     wait=c.crng.randint(5, 30), outcome="completed" if pledge else c.crng.choice(["rescheduled", "abandoned"]),
                     fr=("insufficient_funds", "paperwork"), lens=("housing",), ctx=dict(org=ca.name, what=what))
        T["last"] = c.link(i, "utility_shutoff", T["id"], "asked_for_help", W=W, earlier=T["last"])
        if pledge:
            amt = round(past * c.crng.uniform(.6, 1.0), 2)
            j = sim.emit(t + 60, "bill_payment", "utilities", "utility_assistance_pledge", P, H, ca, org, ben=P, channel="phone", method="none", gross=amt,
                         third=amt, payer="LIHEAP crisis assistance (via %s)" % ca.name, fund="federal", tmin=0, lens=("housing", "public_finance"),
                         related=i, ctx=dict(org=org.name, amt="%.2f" % amt, what=what, agency=ca.name))
            c.link(j, "utility_shutoff", T["id"], "assistance_pledged", W=W, earlier=T["last"])
            del c.util[H.hid]
            return
    # nothing settled: the timer runs out on the notice date (a later day's shutoff_day sends the crew)


def disconnect(c, sim, T, H, P, t):
    org, what = _util(c, T)
    i = sim.emit(t, "failed_attempt", "utilities", "service_disconnected_for_nonpayment", P, H, org, P, tmin=10, outcome="failed",
                 fr=("insufficient_funds",), lens=("housing",), ctx=dict(org=org.name, what=what, amt="%.2f" % T["past"],
                                                                         reason="the past-due balance was not paid by the notice date"))
    T["last"] = c.link(i, "utility_shutoff", T["id"], "disconnected", W=H.wallets[0], earlier=T["last"],
                       note="notice sent before the run began" if T.get("warm") and T["last"] is None else "")
    T["state"], T["off"] = "off", c.date
    from .day_a import push
    t2 = sim.slot_soft(P, 20, ((t + 20, 1260, 1.0),))
    push(sim.q, max(t2, t + 20), lambda: try_reconnect(c, sim, T, H, P, max(t2, t + 20)))


def try_reconnect(c, sim, T, H, P, t):
    """Call, pay what the utility asks plus the reconnection fee, and book the reconnection; or ask for help and wait."""
    org, what = _util(c, T)
    W = H.wallets[0]
    T["tries"] += 1
    fee = float(c.crng.choice(RECONNECT_FEE))
    need = round(T["past"] * (1.0 if T["plan"] else c.crng.choice([.5, .5, 1.0])), 2)
    cash_only = W.bank is None
    kw = dict(channel="phone", tmin=c.crng.randint(12, 30), wait=c.crng.randint(5, 25))
    if cash_only:
        dest = sim.pick(("check_casher", "grocery_full", "supercenter"), H.district, 6.0) or org
        miles, mode, mins, tfr = sim.trip(P, H, H.district, dest.district if dest.district != "EXT" else H.district)
        kw = dict(channel="in_person", tmin=15 + mins, wait=c.crng.randint(3, 20), miles=miles, mode=mode, fr=tuple(tfr))
    i, oc, m = sim.pay(t, P, H, W, None, "utilities", "reconnection_payment", need, ctx=dict(org=org.name, what=what), rtype="bill_payment",
                       fee=("reconnection_fee", fee), to=org, quiet_fail=0.0, lens=("housing",), **kw)
    if oc == "completed":
        T["last"] = c.link(i, "utility_shutoff", T["id"], "reconnection_paid", W=W, earlier=T["last"])
        T["past"] = round(max(0.0, T["past"] - need), 2)
        T["reconnect_on"] = c.next_bank_day(c.today + dt.timedelta(days=1)).isoformat()
        return
    T["last"] = c.link(i, "utility_shutoff", T["id"], "reconnection_unpaid", W=W, earlier=T["last"])
    ca = sim.one("community_action")
    pledge = sim.cal["weekday"] and c.crng.random() < HELP_PLEDGE
    j = sim.emit(t + 45, "non_monetary_job", "utilities", "sought_emergency_utility_help", P, H, P, ca, channel="phone", tmin=c.crng.randint(15, 40),
                 wait=c.crng.randint(5, 30), outcome="completed" if pledge else c.crng.choice(["rescheduled", "abandoned"]), related=i,
                 fr=("insufficient_funds", "paperwork"), lens=("housing",), ctx=dict(org=ca.name, what=what))
    T["last"] = c.link(j, "utility_shutoff", T["id"], "asked_for_help", W=W, earlier=T["last"])
    if pledge:
        amt = round(need + fee, 2)
        k = sim.emit(t + 120, "bill_payment", "utilities", "utility_assistance_pledge", P, H, ca, org, ben=P, channel="phone", method="none", gross=amt,
                     third=amt, payer="LIHEAP crisis assistance (via %s)" % ca.name, fund="federal", tmin=0, lens=("housing", "public_finance"),
                     related=j, ctx=dict(org=org.name, amt="%.2f" % amt, what=what, agency=ca.name))
        T["last"] = c.link(k, "utility_shutoff", T["id"], "assistance_pledged", W=W, earlier=T["last"])
        T["past"] = round(max(0.0, T["past"] - need), 2)
        T["reconnect_on"] = c.next_bank_day(c.today + dt.timedelta(days=1)).isoformat()
        return
    T["next"] = next_money_day(c, sim, W).isoformat()


def reconnect(c, sim, T, H, P, t):
    """The service comes back. Gas needs a technician to relight the pilots, with someone home for the window."""
    org, what = _util(c, T)
    days = (c.today - D(T["off"])).days
    home = what == "gas"
    i = sim.emit(t, "non_monetary_job", "utilities", "service_reconnected", P, H, org, P, channel="in_person" if home else "automatic",
                 tmin=240 if home else 0, wait=c.crng.randint(30, 200) if home else 0, fr=("wait",) if home else (), lens=("housing",),
                 ctx=dict(org=org.name, what=what, days=days))
    back = c.link(i, "utility_shutoff", T["id"], "reconnected", W=H.wallets[0], earlier=T["last"], note="%d days without %s" % (days, what))
    if home and P.works and P.wage and P.wsched != "fixed" and c.crng.random() < .5:
        lost = round(4 * P.wage / 2080.0, 2)
        j = sim.emit(t, "failed_attempt", "work", "late_or_missed_shift", P, H, P, P.org if P.org is not None else "", gross=lost, tmin=240, outcome="partial",
                     fr=("schedule_volatility", "wait"), lens=("labor", "housing"), related=i,
                     ctx=dict(hrs=4, lost="%.2f" % lost, why="someone had to be home for the gas technician"))
        c.link(j, "utility_shutoff", T["id"], "lost_work_hours", W=H.wallets[0], earlier=back)
    if T["past"] < 1.0:
        del c.util[H.hid]
    else:                       # the rest of a plan is still owed; a new notice can follow later
        T.update(state="notice", off=None, reconnect_on=None, decided=False, plan=True,
                 due=(c.today + dt.timedelta(days=c.crng.choice([21, 28]))).isoformat())
