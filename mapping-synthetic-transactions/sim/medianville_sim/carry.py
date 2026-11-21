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
        self.anchor = {}            # account id -> checking balance on the run's first day (the SCF-matched opening)
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
        c.anchor = st["anchor"]
        return c

    def to_state(self):
        return dict(seed=self.seed, first=self.first, n=self.n + 1, seq=self.seq, retries=self.retries, util=self.util, od=self.od,
                    loans=self.loans, tloans=self.tloans, cars_lost=self.cars_lost, refunded=sorted(self.refunded), filed=sorted(self.filed),
                    anchor=self.anchor)

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
        self.od_today = {}
        self.hh = {H.hid: H for H in sim.households}
        self.wal = {W.wid: W for W in sim.wallets}
        self.per = {p.pid: p for p in sim.persons}
        self.org = {o.oid: o for o in sim.orgs}
        self._cal = {}
        start_title_loans(self, sim)
        if self.n == 0:
            warm_tax_season(self, sim)
            self.anchor = {W.wid: round(W.bank, 2) for W in sim.wallets if W.bank is not None}

    def begin_day(self, sim, q):
        """After the day's schedules are drawn and before the households' own plans: carried obligations come first."""
        overdraft_overnight(self, sim)
        set_aside_for_bills(self, sim)
        retry_day(self, sim, q)
        shutoff_day(self, sim, q)
        payday_day(self, sim, q)
        title_day(self, sim, q)

    def end_day(self, sim):
        """After the day's queue has run and card payments have posted."""
        overdraft_end_of_day(self, sim)
        self.loans = [L for L in self.loans if L["status"] != "closed"]
        sweep_surplus(self, sim)

    # overdraft chains (section 3 below): called from engine.Sim.pay, day_a.gen_bills and the retry queue
    def snap_pace(self, H):
        """How much more (or less) often a SNAP household makes its main grocery trip, by how much of the month's benefit
        is left (section 5 below)."""
        return min(SNAP_PACE[2], max(SNAP_PACE[1], SNAP_PACE[0] + SNAP_PACE[3] * H.snap_bal / max(1.0, H.snap)))

    def file_once(self, H):
        """One tax return a season (free preparation, paid preparation or software)."""
        if H.hid in self.filed:
            return False
        self.filed.add(H.hid)
        return True

    def od_ok(self, W, amt):
        """Will the bank cover this item into overdraft? Not past the daily fee cap, and not past the account's overdraft
        limit; otherwise the item is declined or returned."""
        return self.od_today.get(W.wid, 0) < OD_DAILY_CAP and (W.bank or 0.0) - amt >= -OD_LIMIT

    def overdraft(self, sim, W, idx):
        overdraft_fee_charged(self, sim, W, idx)

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
    e = dict(id=eid, hid=H.hid, wid=W.wid, pid=P.pid, bill=bi, kind=kind, org=b[1].oid, owed=round(owed, 2), fees=round(fees + late, 2),
             due=c.date, late=bool(late), ret=bool(fees), tries=1, mode=mode, next=nxt.isoformat(), last=first)
    c.retries.append(e)
    if kind in RENT_KINDS:
        rent_after_overdraft(c, W, idx, e)


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
        if P is None or P.age < 18 or (P.inpatient and e["mode"] == "manual"):
            # a lender's or merchant's retry needs nobody at home; paying by hand needs an adult who is not in hospital
            P = next((a for a in W.owners if a.age >= 18 and not (a.inpatient and e["mode"] == "manual")), None)
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
            elif W.od and need - max(have, 0) < 900 and c.od_ok(W, need) and c.crng.random() < .6:
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
        if odf:
            c.overdraft(sim, W, i)
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
        if e.get("od") and step in ("paid_late", "partial"):
            e["od_last"] = c.link(i, "overdraft", e["od"], "late_rent_paid" if step == "paid_late" else "late_rent_part", W=W, earlier=e.get("od_last"))
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


# ---------------------------------------------------------------------------------------------- 3. overdraft chains
# Once balances carry, an account that goes below zero stays there until money comes in, so the next card swipe or
# autopay overdraws it again: one overdraft leads to more fees, and a rent payment that comes due while the account is
# under water fails and is paid late with the lease's late fee. A chain runs from an account's first overdraft fee until
# it closes a day at or above zero.
# Bank terms (estimates; banks that still charge overdraft fees mostly cap them per day and many have dropped extended
# fees, but the local banks here keep them): at most three overdraft fees a day; no item that would take the account more
# than $500 below zero; an extended overdraft fee, equal to the bank's overdraft fee, once an account has been below zero
# for seven days. Someone whose account is already below zero tries a card that will not clear about a third as often
# (engine.Sim.methods).
# Concentration is measured, not set: the CFPB found 9% of accounts paying 79% of overdraft and NSF fees over a year
# ("Data point: Frequent overdrafters", 2017). Overdraft fees fall only on accounts opted in to coverage
# (finance.OD_OPT_IN), which the one-day simulator already fixes.
RENT_WINDOW = 14               # a rent payment missed within two weeks of an overdraft fee joins that overdraft's chain
OD_DAILY_CAP = 3
OD_LIMIT = 500.0                # the furthest below zero a bank lets an account go (estimate; a one-day run caps each item at $260)
EXTENDED_OD_DAYS = 7
RENT_KINDS = ("rent", "lot_rent")


def overdraft_fee_charged(c, sim, W, idx):
    c.od_today[W.wid] = c.od_today.get(W.wid, 0) + 1
    o = c.od.get(W.wid)
    if o is None or (o.get("closed") and o["closed"] < c.date):
        o = c.od[W.wid] = dict(id=c.new_id("O"), start=c.date, last=None, fees=0, neg_since=None, ext=False, closed=None)
        step = "first_overdraft"
    else:
        step = "more_fees"
    o["last"] = c.link(idx, "overdraft", o["id"], step, W=W, earlier=o["last"])
    o["fees"] += 1
    o["last_fee"] = c.date


def overdraft_overnight(c, sim):
    """An account below zero for a week draws the extended overdraft fee, once per chain."""
    for wid, o in c.od.items():
        W = c.wal.get(wid)
        if W is None or W.bank is None or not W.od_fee or o["ext"] or o["neg_since"] is None or o.get("closed"):
            continue
        days = (c.today - D(o["neg_since"])).days
        if days >= EXTENDED_OD_DAYS and W.bank < 0:
            P = next((a for a in W.owners if a.age >= 18), W.owners[0])
            fee = float(W.od_fee)
            W.take("debit", fee)
            i = sim.emit(c.crng.randint(1, 4), "bill_payment", "money_services", "extended_overdraft_fee", P, W.hh, P, W.bank_org, channel="automatic",
                         method="debit", gross=fee, user=fee, fee_type="extended_overdraft_fee", fee=fee, fr=("insufficient_funds",),
                         ctx=dict(org=W.bank_org.name, amt="%.0f" % fee, days=days))
            o["last"] = c.link(i, "overdraft", o["id"], "extended_fee", W=W, earlier=o["last"])
            o["ext"] = True


def overdraft_end_of_day(c, sim):
    """A chain stays open while the account closes the day below zero. A closed chain is remembered for two weeks, so a
    rent payment the fees left short can still be tied to it."""
    for wid in list(c.od):
        W = c.wal.get(wid)
        o = c.od[wid]
        if W is None or W.bank is None or W.bank >= 0:
            if o.get("closed") is None:
                o["closed"] = c.date
            if (c.today - D(o["last_fee"])).days >= RENT_WINDOW:
                del c.od[wid]
        else:
            o["closed"] = None
            if o["neg_since"] is None:
                o["neg_since"] = c.date


def rent_after_overdraft(c, W, idx, e):
    """A rent payment that fails within two weeks of an overdraft fee on the same account joins that overdraft's chain."""
    o = c.od.get(W.wid)
    if o is None or (c.today - D(o["last_fee"])).days > RENT_WINDOW:
        return
    e["od"] = o["id"]
    o["last"] = e["od_last"] = c.link(idx, "overdraft", o["id"], "rent_missed", W=W, earlier=o["last"])


# ---------------------------------------------------------------------------------------------- 4. payday and title rollovers
# Payday loans. CFPB, "Data Point: Payday Lending" (2014; sources/raw/payday_cfpb): over 80% of loans are renewed or
# followed by another loan within 14 days; of new loan sequences, 38% end with the first loan repaid and 5% with it in
# default (borrowers paid weekly to semimonthly; 30% and 4% for monthly borrowers); 12% run to 11 or more loans; half of
# all loans are in sequences of 10 or more; 64% of new borrowers become renewers and 20% defaulters. A first loan here is
# meant to be repaid 38% of the time, renewed 57% and defaulted 5%; each later one renewed 84%, repaid 12% and defaulted
# 4%. That reproduces the 80% renewal share, the 12% of sequences past ten loans and half of loans in long sequences.
# What the account holds can change the plan: a loan meant to be repaid that cannot be is renewed for the fee, and a
# renewal whose fee cannot be paid bounces. A bounced loan is re-presented twice (3 and 5 business days later) and then
# goes to collections. Each loan is due on the borrower's first payday at least a week away (two weeks for most).
# The one-day simulator's "new loans" stand for loans and renewals together (T02 counts both, as the California and
# Texas reports do), so a carried run starts a new sequence at 1/4.56 of the one-day rate (4.56 loans per sequence).
PAYDAY_FIRST = (.38, .57, .05)          # repay, renew, default
PAYDAY_LATER = (.12, .84, .04)
PAYDAY_SEQ_START = 1 / 4.56
PAYDAY_REPRESENT = (3, 5)
PAYDAY_TERM_MIN = 7


def payday_start_ok(c, W):
    """A new loan sequence (one at a time per account)."""
    return not any(L["wid"] == W.wid and L["status"] != "collections" for L in c.loans) and c.crng.random() < PAYDAY_SEQ_START


def next_payday(c, sim, W, P, min_days=PAYDAY_TERM_MIN):
    """The borrower's first payday at least `min_days` away (a post-dated check or debit is set for it); else two weeks."""
    from .day_a import paid_today
    owners = [P] + [p for p in W.owners if p is not P and p.age >= 18]
    for k in range(min_days, 36):
        d = c.today + dt.timedelta(days=k)
        cal = c.cal(d)
        for p in owners:
            if p.emp in ("employed_full_time", "employed_part_time") and p.org is not None and paid_today(p, cal):
                return d
            if (p.ss and p.ss_cohort in cal["ss_cohorts"]) or ((p.ssi or p.va) and cal["ssi_today"]):
                return d
    return c.next_bank_day(c.today + dt.timedelta(days=14))


def payday_opened(c, sim, W, P, org, amt, fee, idx, kind="storefront"):
    lid = c.new_id("P")
    first = c.link(idx, "payday_loan", lid, "borrowed", W=W)
    c.loans.append(dict(id=lid, kind=kind, hid=W.hh.hid, wid=W.wid, pid=P.pid, org=org.oid, principal=amt, fee=round(fee, 2), n=1, fees_paid=0.0,
                        due=next_payday(c, sim, W, P).isoformat(), start=c.date, status="open", tries=0, last=first))


def warm_payday_loans(c, sim):
    """The loans already out on a run's first day: about one per (one-day new-loan rate x days a loan is out) eligible
    accounts, each at a point in its sequence drawn from the steady state, due within its term (no records: those loans
    were taken before the run began)."""
    from .day_c import PAYDAY_NEW
    lenders, online = sim.by_kind.get("payday") or [], sim.X["x_cc2"]
    stay = [1.0, PAYDAY_FIRST[1]]
    for k in range(2, 30):
        stay.append(stay[-1] * PAYDAY_LATER[1])
    for H in sim.households:
        if H.gq in ("jail", "nursing_home"):
            continue
        for W in H.wallets:
            own = [p for p in W.owners if p.age >= 18 and not p.inpatient]
            if not own or W.bank is None or not (W.status != "above" or W.revolver) or not any(p.wage > 0 for p in own):
                continue
            P = c.crng.choice(own)
            due = next_payday(c, sim, W, P, 1)
            term = max(7, (due - c.today).days)
            if c.crng.random() >= PAYDAY_NEW * term:
                continue
            store = bool(lenders) and c.crng.random() < .58
            org = min(lenders, key=lambda o: (o.district != H.district, c.crng.random())) if store else online
            amt = float(c.crng.choice([200, 255, 300, 300, 350, 400, 500]))
            fee = round(amt * c.crng.choice([.15, .15, .175]) * (1.0 if store else 1.6), 2)
            u, n = c.crng.random() * sum(stay), 1
            acc = stay[0]
            while acc < u and n < len(stay):
                acc += stay[n]
                n += 1
            c.loans.append(dict(id=c.new_id("P"), kind="storefront" if store else "online", hid=H.hid, wid=W.wid, pid=P.pid, org=org.oid, principal=amt,
                                fee=fee, n=n, fees_paid=round(fee * (n - 1), 2), due=due.isoformat(), start=None, status="open", tries=0, last=None, warm=True))


def payday_day(c, sim, q):
    from .day_a import push
    if c.n == 0 and not c.loans:
        warm_payday_loans(c, sim)
    if not sim.cal["bank_day"]:
        return
    for L in c.loans:
        if L["status"] == "collections" or L["due"] > c.date:
            continue
        H, W, P = c.hh.get(L["hid"]), c.wal.get(L["wid"]), c.per.get(L["pid"])
        if H is None or W is None or P is None or W.bank is None:
            L["status"] = "collections"
            continue
        t = c.crng.randint(200, 420)
        push(q, t, lambda L=L, H=H, W=W, P=P, t=t: payday_due(c, sim, L, H, W, P, t))
    c.loans = [L for L in c.loans if L["status"] != "closed"]


def payday_due(c, sim, L, H, W, P, t):
    org = c.org[L["org"]]
    store = L["kind"] == "storefront"
    due = round(L["principal"] + L["fee"], 2)
    fee = L["fee"]
    k_repay, k_roll = ("payday_loan_repayment", "payday_loan_rollover") if store else ("online_loan_repayment", "online_loan_renewal")
    ctx = dict(org=org.name, amt="%.2f" % due, fee="%.2f" % fee, n=L["n"], principal="%.0f" % L["principal"])
    first_note = "loan taken before the run began" if L.get("warm") and L["last"] is None else ""
    if L["status"] == "default":                     # the lender re-presents the bounced debit
        if W.bank >= due:
            W.take("ach", due)
            ctx["again"] = "the lender sent the debit again after it bounced"
            i = sim.emit(t, "bill_payment", "money_services", k_repay, P, H, P, org, channel="automatic", method="ach", gross=due, user=due,
                         fee_type="payday_finance_charge", fee=fee, ctx=ctx)
            L["last"] = c.link(i, "payday_loan", L["id"], "repaid_after_bounce", W=W, earlier=L["last"])
            L["status"] = "closed"
            return
        return _payday_bounce(c, sim, L, H, W, P, t, org, due, ctx, k_repay)
    plan = PAYDAY_FIRST if L["n"] == 1 else PAYDAY_LATER
    r = c.crng.random()
    intent = "repay" if r < plan[0] else "renew" if r < plan[0] + plan[1] else "default"
    if intent == "repay" and W.bank >= due:
        W.take("ach", due)
        i = sim.emit(t, "bill_payment", "money_services", k_repay, P, H, P, org, channel="automatic", method="ach", gross=due, user=due,
                     fee_type="payday_finance_charge", fee=fee, ctx=ctx)
        L["last"] = c.link(i, "payday_loan", L["id"], "repaid", W=W, earlier=L["last"], note=first_note)
        L["status"] = "closed"
        return
    if intent != "default" and (W.bank >= fee or (store and W.cash >= fee)):
        m = "ach" if W.bank >= fee else "cash"
        W.take(m, fee)
        L["fees_paid"] = round(L["fees_paid"] + fee, 2)
        ctx["again"] = ("renewal number %d of the same $%.0f; $%.0f in fees so far" % (L["n"], L["principal"], L["fees_paid"]))
        i = sim.emit(t if m == "ach" else c.crng.randint(600, 1000), "bill_payment", "money_services", k_roll, P, H, P, org,
                     channel="automatic" if m == "ach" else "in_person", method=m, gross=due, user=fee, fee_type="rollover_fee", fee=fee, outcome="partial",
                     fr=("insufficient_funds",), tmin=0 if m == "ach" else 20, ctx=ctx)
        L["last"] = c.link(i, "payday_loan", L["id"], "renewed", W=W, earlier=L["last"], note=first_note)
        L["n"] += 1
        L["due"] = next_payday(c, sim, W, P).isoformat()
        return
    return _payday_bounce(c, sim, L, H, W, P, t, org, due, ctx, k_repay, first_note)


def _payday_bounce(c, sim, L, H, W, P, t, org, due, ctx, kind, note=""):
    nsf = float(c.crng.choice([15, 25, 30, 35]))
    ctx["reason"] = "the lender's debit bounced" if L["status"] != "default" else "the re-sent debit bounced again"
    i = sim.emit(t, "failed_attempt", "money_services", kind, P, H, P, org, channel="automatic", method="ach", gross=due, fee_type="returned_payment_fee",
                 fee=nsf, outcome="failed", fr=("insufficient_funds",), ctx=ctx)
    L["last"] = c.link(i, "payday_loan", L["id"], "bounced", W=W, earlier=L["last"], note=note)
    L["fee"] = round(L["fee"] + nsf, 2)
    L["status"] = "default"
    L["tries"] += 1
    if L["tries"] <= len(PAYDAY_REPRESENT):
        L["due"] = c.add_bank_days(PAYDAY_REPRESENT[L["tries"] - 1]).isoformat()
    else:
        L["status"] = "collections"          # sold or sent to a collector; no more debits this month


# Title loans: the stock opened by finance.open_title_loans on a run's first day is carried from then on. A missed
# payment leaves the loan behind (twice as likely to end in repossession, day_c.overnight_lenders) until paid, tried
# again on the next day money comes in; a repossessed car stays gone for the rest of the run; a title loan taken during the
# run joins the book, due a month later.
def start_title_loans(c, sim):
    if c.n == 0 and not c.tloans:
        for H in sim.households:
            if H.tloan is not None:
                L = dict(H.tloan)
                c.tloans[H.hid] = dict(L, org=L["org"].oid, late=False, last=None, warm=True, id=c.new_id("T"))
    for H in sim.households:
        lost = c.cars_lost.get(H.hid, 0)
        if lost:
            H.vehicles = max(0, H.vehicles - lost)
        if H.hid in c.tloans:
            L = c.tloans[H.hid]
            H.tloan = None if L is None else dict(L, org=c.org[L["org"]])
        elif H.tloan is not None:
            H.tloan = None      # the build draws the same stock every day; only the carried book counts


def title_taken(c, sim, H, P, org, amt, idx):
    if c.tloans.get(H.hid):
        return
    tid = c.new_id("T")
    c.tloans[H.hid] = dict(id=tid, kind="single", org=org.oid, principal=float(amt), dom=min(28, c.today.day), left=1, months=0, late=False,
                           last=c.link(idx, "title_loan", tid, "borrowed", H=H), start=c.date)


def repossessed(c, sim, H, idx):
    L = c.tloans.get(H.hid)
    if L:
        c.link(idx, "title_loan", L["id"], "repossessed", H=H, earlier=L.get("last"),
               note="loan taken before the run began" if L.get("warm") and L.get("last") is None else "")
    c.tloans[H.hid] = None
    c.cars_lost[H.hid] = c.cars_lost.get(H.hid, 0) + 1


def title_day(c, sim, q):
    from .day_c import go, TITLE_INSTALL_FEE, TITLE_PAYOFF_SHARE, TITLE_SINGLE_FEE
    from .engine import SHOP
    for hid, L in c.tloans.items():
        if not L:
            continue
        H = c.hh.get(hid)
        due_today = c.today.day == L["dom"] and (L.get("paid") or "")[:7] != c.date[:7]
        if H is None or H.gq or not (due_today or (L["late"] and L.get("next") and L["next"] <= c.date)):
            continue
        W = H.wallets[0]
        P = next((a for a in W.owners if a.age >= 18 and not a.inpatient), None)
        if P is None:
            continue
        org = c.org[L["org"]]
        p = L["principal"]
        if L["kind"] == "single":
            fee = round(p * TITLE_SINGLE_FEE, 2)
            payoff = W.liquid() >= p + fee and c.crng.random() < TITLE_PAYOFF_SHARE * 2
            kind, amt, f = ("title_loan_payment", p, ("title_loan_finance_charge", fee)) if payoff else ("title_loan_rollover", fee, None)
            ctx = dict(note=", which pays it off and gets the title back") if payoff else dict(owed="%.0f" % p, n=L["months"] + 1)
        else:
            part, fee = round(p / max(1, L["left"]), 2), round(p * TITLE_INSTALL_FEE, 2)
            payoff, kind, amt, f = L["left"] <= 1, "title_loan_payment", part, ("title_loan_finance_charge", fee)
            ctx = dict(note="; that was the last payment" if L["left"] <= 1 else "; %d payments left" % (L["left"] - 1))
        if L["late"]:
            ctx["again"] = "a late payment, after the one due on the %s was missed" % _ordinal_day(L["dom"])

        def fn(t, miles, mode, tfr, w, L=L, H=H, W=W, P=P, org=org, kind=kind, amt=amt, f=f, ctx=ctx, payoff=payoff):
            i, oc, m = sim.pay(t, P, H, W, org, "money_services", kind, amt, ctx=ctx, tmin=15 + w, wait=w, miles=miles, mode=mode, fr=tfr, rtype="bill_payment",
                               fee=f, quiet_fail=0.0, lens=("consumer_finance",))
            note = "loan taken before the run began" if L.get("warm") and L.get("last") is None else ""
            if oc != "completed":
                L["last"] = c.link(i, "title_loan", L["id"], "missed_payment", H=H, earlier=L.get("last"), note=note)
                L["late"], L["next"] = True, next_money_day(c, sim, W).isoformat()
                return
            L["late"], L["paid"] = False, c.date
            if L["kind"] == "single" and not payoff:
                L["months"] += 1
                L["last"] = c.link(i, "title_loan", L["id"], "rolled_over", H=H, earlier=L.get("last"), note=note)
            elif payoff:
                c.link(i, "title_loan", L["id"], "paid_off", H=H, earlier=L.get("last"), note=note)
                c.tloans[H.hid] = None
                H.tloan = None
            else:
                L["left"] -= 1
                L["last"] = c.link(i, "title_loan", L["id"], "installment_paid", H=H, earlier=L.get("last"), note=note)
        if go(sim, q, P, H, org, c.crng.randint(10, 25), SHOP, fn, wait=(0, 15)) is None:
            L["late"], L["next"] = True, (c.today + dt.timedelta(days=1)).isoformat()


def _ordinal_day(n):
    return "%d%s" % (n, "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


# ---------------------------------------------------------------------------------------------- 5. balance paths
# SNAP. Carried, the balance runs down from the day the month's benefit loads (day_a.gen_income) as the household shops
# (day_b.gen_food). Households spend fastest right after the load and stretch what is left: the main grocery trip comes
# more often the more of the month's benefit is left (a multiplier of .5 to 2.2, from .55 + 1.6 x balance/benefit). The
# coefficients are an estimate (no redemption-timing source was downloaded), fitted on the carried month so that about
# half the benefit is spent in the first week, about three quarters in two weeks, and little is left at the next load.
# A one-day run's opening SNAP balance (finance.build_finance) is unchanged.
SNAP_PACE = (.6, .5, 2.0, 1.25)          # intercept, floor, ceiling, slope

# Checking. Carried, checking rises on paydays and benefit days and falls with the bills and spending between them. The
# one-day simulator sets spending by counts and shares (payments per adult, the CE spending order), not by dollars against
# income, so households above ALICE take in more than they spend; carried, their checking would climb by about $3,400 a
# month. Most such households move what they do not need out of checking ("pay yourself first"). Here, on a day money
# comes in, an account holding more than twice its opening balance plus $500 moves the excess over one and a half times
# the opening balance to savings, recorded as a transfer (an estimate, so that checking follows the pay cycle around its
# opening level instead of drifting up). Opening balances are the SCF-matched ones of the run's first day.
SWEEP_ABOVE, SWEEP_KEEP, SWEEP_PAD = 2.0, 1.5, 500.0

# Once a season. The one-day simulator draws each day's tax refunds and filings on their own; carried day after day,
# the same filer would be refunded again and again (in a first March test, about $2,200 per ALICE household). In a
# carried run each account gets one federal and one state refund a season and each household files once
# (day_a.gen_income, day_c.gen_money and gen_public). The run's first day inherits the season so far: each account or
# household has already been refunded or filed with the chance the same daily rates give from January 25 to the day
# before, except that EITC and child tax credit refunds wait for the PATH Act wave (from February 26).
def warm_tax_season(c, sim):
    from .day_c import TAX_PAID
    start = dt.date(c.today.year, 1, 25)
    if c.today <= start:
        return
    days = [start + dt.timedelta(days=k) for k in range((c.today - start).days)]
    days = [d for d in days if c.cal(d)["tax_season"]]
    if not days:
        return
    wave = sum(1 for d in days if c.cal(d)["eitc_wave"])
    for H in sim.households:
        if H.gq:
            continue
        W0 = H.wallets[0]
        for W in H.wallets:
            earners = [p for p in W.owners if p.wage > 0]
            ad = [p for p in W.owners if p.age >= 18]
            if not ad:
                continue
            wages = sum(p.wage for p in earners)
            kids = len(H.kids) if W is W0 else 0
            eitc = bool(earners) and wages < (22000 if not kids else 52000 + 6000 * min(kids, 3)) and (kids or 25 <= ad[0].age < 65)
            if eitc and kids:
                stay = (1 - .17) ** wave            # PATH Act: no EITC refunds before the wave
            else:
                pr = .0105 if (earners or any(p.pension or p.inv for p in ad)) else .002
                stay = (1 - pr) ** len(days)
            if c.crng.random() >= stay:
                c.refunded.add("F:" + W.wid)
            if c.crng.random() >= (1 - .006) ** len(days):
                c.refunded.add("S:" + W.wid)
        if any(p.wage > 0 or p.pension or p.inv for p in H.adults):
            pf = TAX_PAID + (.0042 if H.internet != "no" else 0.0) + (.0036 if H.income < 69000 else 0.0)
            if c.crng.random() >= (1 - pf) ** len(days):
                c.filed.add(H.hid)


def money_in_today(c, sim, W):
    from .day_a import paid_today
    cal = sim.cal
    for p in W.owners:
        if p.emp in ("employed_full_time", "employed_part_time") and p.org is not None and paid_today(p, cal):
            return True
        if (p.ss and p.ss_cohort in cal["ss_cohorts"]) or ((p.ssi or p.va) and cal["ssi_today"]):
            return True
    return False


def sweep_surplus(c, sim):
    """End of a day money came in: move checking well above its opening level to savings."""
    for W in sim.wallets:
        a = c.anchor.get(W.wid)
        if a is None or W.bank is None or W.bank <= SWEEP_ABOVE * a + SWEEP_PAD or not money_in_today(c, sim, W):
            continue
        amt = round(W.bank - SWEEP_KEEP * a, 2)
        P = next((p for p in W.owners if p.age >= 18), None)
        if P is None or amt < 50:
            continue
        W.bank -= amt
        W.savings += amt
        sim.emit(c.crng.randint(1200, 1400), "transfer", "money_services", "transfer_to_savings", P, W.hh, P, W.bank_org, channel="app", method="ach",
                 gross=amt, tmin=3, ctx=dict(org=W.bank_org.name, amt="%.0f" % amt))
