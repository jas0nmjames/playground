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
