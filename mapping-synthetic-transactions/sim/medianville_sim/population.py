"""Households and persons for Medianville: whole households drawn from national-style distributions."""
import math
import numpy as np
from .config import (DISTRICTS, DSHARE, DIST, SECTORS, SEC_AFF, SEC_DIST, SEC_YOUNG, SEC_OLD, UNION, CADENCE,
                     PAY_WEEKDAY, OCC, GENERATIONS, SS_AVG_RETIRED, SS_AVG_DISABLED, SSI_FBR, SNAP_MAX,
                     POVERTY_BASE, POVERTY_STEP, TRANSIT_SERVED)
from . import config as C

EDU = ["less_than_high_school", "high_school", "some_college", "associate", "bachelor", "graduate"]


class Person:
    __slots__ = ("pid", "hh", "age", "sex", "race", "rel", "edu", "dis", "cov", "plan", "emp", "occ", "org", "sector",
                 "union", "sched", "slot", "wsched", "cadence", "payday", "care_for", "benefits", "wage", "ft", "tipped",
                 "bday", "by", "vet", "ss", "ss_type", "ss_cohort", "ssi", "pension", "ui", "va", "inv", "income",
                 "student", "school", "grade", "meal", "wallet", "cashpref", "nrx", "esrd", "home_care", "mode", "wfh",
                 "works", "busy", "free", "wake", "bed", "gig", "smoker", "dental", "wd", "seasonal", "garnish",
                 "sloan", "cared_by", "medigap", "inpatient", "bnpl", "absent", "k401", "prem", "lunch", "shift", "cm", "night", "psl")

    def __init__(self, pid, hh, age, sex, rel):
        self.pid, self.hh, self.age, self.sex, self.rel = pid, hh, age, sex, rel
        self.race = self.edu = self.dis = self.cov = self.plan = None
        self.emp, self.occ, self.org, self.sector = "child" if age < 16 else "not_in_labor_force", "", None, ""
        self.union = False
        self.sched = self.slot = None
        self.wsched, self.cadence, self.payday = "none", "none", None
        self.care_for, self.benefits, self.cared_by = [], [], []
        self.wage, self.ft, self.tipped = 0.0, False, False
        self.bday, self.by = 1, 0
        self.vet = False
        self.psl = False   # access to paid sick leave (v2; set by assign_sick_leave)
        self.ss, self.ss_type, self.ss_cohort = 0.0, None, None
        self.ssi = self.pension = self.ui = self.va = self.inv = self.income = 0.0
        self.student = self.school = self.grade = self.meal = None
        self.wallet = None
        self.cashpref, self.nrx, self.esrd, self.home_care = 0.2, 0, False, None
        self.mode, self.wfh, self.works = "car", False, False
        self.busy, self.free, self.wake, self.bed = [], [], 390, 1350
        self.gig = self.smoker = self.dental = self.seasonal = self.garnish = False
        self.wd = None
        self.sloan = 0.0
        self.medigap = self.inpatient = self.bnpl = self.absent = False
        self.k401 = self.prem = 0.0
        self.lunch, self.shift, self.cm, self.night = None, [], 0, False


class Household:
    __slots__ = ("hid", "district", "htype", "members", "income", "alice", "banked", "tenure", "housing_cost", "vehicles",
                 "internet", "lang", "notes", "lep", "immigrant", "recent", "race", "z", "wallets", "bills", "snap",
                 "snap_day", "wic", "wic_day", "tanf", "tanf_day", "subsidized", "mortgage", "escrow", "hoa", "ev", "gq",
                 "fragile", "landlord", "rent_day", "head", "adults", "kids", "pov_ratio", "cs", "util_incl", "gasheat",
                 "washer", "mobile_home", "ccdf", "liheap", "pets", "snap_bal", "wic_bal", "flags", "late_rent", "facility", "tloan")

    def __init__(self, hid, district, htype):
        self.hid, self.district, self.htype = hid, district, htype
        self.members, self.notes, self.wallets, self.bills, self.flags = [], [], [], [], set()
        self.income = 0.0
        self.alice = self.banked = self.tenure = None
        self.housing_cost, self.vehicles, self.internet, self.lang = 0.0, 0, "yes", "English"
        self.lep = self.immigrant = self.recent = False
        self.race, self.z = None, 0.0
        self.snap = self.wic = self.tanf = self.cs = 0.0
        self.snap_day = self.wic_day = self.tanf_day = None
        self.subsidized = self.mortgage = self.escrow = False
        self.hoa, self.ev, self.gq = 0.0, 0, None
        self.fragile, self.landlord, self.rent_day = False, None, None
        self.tloan = None   # an open auto title loan (v2; finance.open_title_loans)
        self.head, self.adults, self.kids = None, [], []
        self.pov_ratio = 1.0
        self.util_incl = self.gasheat = self.washer = self.mobile_home = self.ccdf = self.liheap = False
        self.pets = 0
        self.snap_bal = self.wic_bal = 0.0
        self.late_rent = False
        self.facility = None


TYPE_W = {"married_kids": .170, "married_nokids": .264, "single_parent": .066, "alone": .272, "roommates": .058,
          "cohab_kids": .025, "multigen": .047, "adult_child": .086, "other_family": .011}
TYPE_SIZE = {"married_kids": 4.0, "married_nokids": 2.0, "single_parent": 2.75, "alone": 1.0, "roommates": 2.5,
             "cohab_kids": 3.7, "multigen": 4.9, "adult_child": 3.25, "other_family": 2.9}
TYPE_D = {
    "D1": {"alone": 1.30, "roommates": 1.8, "married_kids": .70, "married_nokids": .80, "single_parent": 1.15},
    "D2": {"single_parent": 1.20, "multigen": 1.5, "alone": .95, "cohab_kids": 1.2},
    "D3": {"married_kids": 1.45, "married_nokids": 1.15, "alone": .65, "roommates": .5, "multigen": .9},
    "D4": {},
    "D5": {"alone": 1.10, "married_nokids": 1.1, "roommates": .6},
    "D6": {"married_nokids": 1.30, "alone": .85, "roommates": .3, "multigen": 1.2},
}
AGE = {
    "married_kids": [(24, 29, .07), (30, 34, .17), (35, 39, .25), (40, 44, .25), (45, 49, .16), (50, 56, .10)],
    "married_nokids": [(22, 29, .06), (30, 39, .07), (40, 49, .08), (50, 59, .23), (60, 69, .27), (70, 79, .21), (80, 92, .08)],
    "single_parent": [(19, 24, .10), (25, 29, .17), (30, 34, .22), (35, 39, .21), (40, 44, .16), (45, 54, .14)],
    "alone": [(19, 24, .04), (25, 34, .115), (35, 44, .09), (45, 54, .11), (55, 64, .175), (65, 74, .22), (75, 84, .17), (85, 97, .08)],
    "roommates": [(19, 24, .36), (25, 34, .33), (35, 49, .15), (50, 64, .12), (65, 80, .04)],
    "cohab_kids": [(20, 24, .14), (25, 29, .26), (30, 34, .26), (35, 39, .18), (40, 48, .16)],
    "multigen": [(48, 59, .35), (60, 69, .40), (70, 82, .25)],
    "adult_child": [(44, 54, .35), (55, 64, .42), (65, 78, .23)],
    "other_family": [(22, 34, .30), (35, 54, .35), (55, 75, .35)],
}
RACE_D = {  # white_nh, hispanic, black_nh, asian_nh, aian_nh, multiracial_other
    "D1": [.44, .21, .20, .09, .005, .055], "D2": [.44, .28, .14, .09, .005, .045], "D3": [.68, .13, .07, .07, .003, .047],
    "D4": [.62, .17, .13, .03, .005, .045], "D5": [.765, .11, .08, .01, .015, .02], "D6": [.80, .11, .04, .005, .02, .025],
}
RACES = ["white_non_hispanic", "hispanic", "black_non_hispanic", "asian_non_hispanic", "american_indian_alaska_native", "multiracial_or_other"]
Z_D = {"D1": -.05, "D2": -.28, "D3": .40, "D4": -.05, "D5": -.30, "D6": -.12}
EMP_AGE = [(16, 17, .18), (18, 19, .42), (20, 24, .67), (25, 34, .81), (35, 44, .82), (45, 54, .81), (55, 59, .73),
           (60, 64, .58), (65, 69, .34), (70, 74, .20), (75, 79, .10), (80, 120, .035)]
DIS_AGE = [(0, 4, .008), (5, 17, .058), (18, 34, .075), (35, 64, .125), (65, 74, .24), (75, 120, .46)]
GQ_PLAN = [("nursing_home", "D2", 180, "Maple Glen Nursing & Rehabilitation"), ("nursing_home", "D4", 130, "Cedar Hollow Care Center"),
           ("nursing_home", "D5", 60, "Prairie View Manor"), ("assisted_living", "D3", 80, "Wexford Commons Senior Living"),
           ("college_dorm", "D4", 1100, "Wexley College"), ("jail", "D4", 240, "Medianville County Detention Center"),
           ("group_home", "D1", 40, None), ("group_home", "D2", 40, None), ("group_home", "D4", 30, None),
           ("shelter", "D1", 100, "Harbor House Shelter"), ("residential_treatment", "D1", 50, None)]


def tbl(tab, age):
    for a, b, v in tab:
        if a <= age <= b:
            return v
    return tab[-1][2]


def generation(by):
    for y, g in GENERATIONS:
        if by >= y:
            return g
    return "greatest"


def build_population(sim):
    rng, nrg, cal = sim.rng, sim.nrg, sim.cal
    N = sim.cfg["N_HOUSEHOLDS"]
    scale = N / float(C.FULL_CITY_HOUSEHOLDS)
    year = cal["date"].year
    HH, PP = [], []

    def person(H, age, sex, rel):
        age = max(0, min(101, int(age)))
        p = Person("P%06d" % (len(PP) + 1), H, age, sex, rel)
        p.bday = rng.randint(1, 28) if rng.random() < .92 else rng.randint(29, 31)
        bmonth = rng.randint(1, 12)
        p.by = year - age - (1 if (bmonth, p.bday) > (cal["date"].month, cal["date"].day) else 0)
        H.members.append(p)
        PP.append(p)
        return p

    # ---------- 1. household skeletons
    tw = {}
    for d in DISTRICTS:
        w = {t: TYPE_W[t] * TYPE_D[d].get(t, 1.0) for t in TYPE_W}
        s = sum(w.values())
        tw[d] = {t: v / s for t, v in w.items()}
    avg = {d: sum(tw[d][t] * TYPE_SIZE[t] for t in TYPE_W) for d in DISTRICTS}
    raw = {d: DSHARE[d] / avg[d] for d in DISTRICTS}
    tot = sum(raw.values())
    counts = {d: int(round(N * raw[d] / tot)) for d in DISTRICTS}
    counts["D1"] += N - sum(counts.values())

    def agew(d, lo, hi):
        mid = (lo + hi) / 2.0
        if d == "D1":
            return 1.35 if mid < 35 else (.8 if mid >= 65 else 1)
        if d == "D2":
            return 1.1 if mid < 35 else 1
        if d == "D3":
            return 1.2 if 30 <= mid < 55 else (.75 if mid >= 75 else 1)
        if d == "D5":
            return 1.3 if mid >= 55 else (.8 if mid < 35 else 1)
        if d == "D6":
            return 1.35 if mid >= 55 else (.7 if mid < 35 else 1)
        return 1

    def head_age(t, d):
        b = AGE[t]
        lo, hi, _ = rng.choices(b, [w * agew(d, lo, hi) for lo, hi, w in b])[0]
        return rng.randint(lo, hi)

    def kids_for(H, mother_age, n, must_minor=True):
        a = mother_age - int(rng.triangular(17, 38, 25.5))
        if a > 17:
            a = rng.randint(8, 17) if must_minor else a
        a = max(0, a)
        out = []
        for i in range(n):
            if a < 0:
                break
            out.append(person(H, a, rng.choice("MF"), "child"))
            a -= rng.randint(1, 4)
            if a < 0 and rng.random() < .5:
                a = 0
        return out

    def osex(s):
        return ("F" if s == "M" else "M") if rng.random() > .015 else s

    types = list(TYPE_W)
    for d in DISTRICTS:
        tws = [tw[d][t] for t in types]
        for _ in range(counts[d]):
            t = rng.choices(types, tws)[0]
            H = Household("H%05d" % (len(HH) + 1), d, t)
            HH.append(H)
            a = head_age(t, d)
            if t in ("married_kids", "cohab_kids"):
                hs = "M" if rng.random() < .55 else "F"
                h = person(H, a, hs, "head")
                ss = osex(hs)
                sp = person(H, a + int(rng.gauss(-1.5 if hs == "M" else 1.5, 3)), ss, "spouse" if t == "married_kids" else "unmarried_partner")
                sp.age = max(18, sp.age)
                ma = h.age if hs == "F" else sp.age
                n = rng.choices([1, 2, 3, 4, 5], [.40, .39, .15, .045, .015])[0] if t == "married_kids" else rng.choices([1, 2, 3], [.5, .33, .17])[0]
                kids_for(H, ma, n)
                if t == "married_kids" and ma >= 42 and rng.random() < .22:
                    person(H, min(ma - 19, rng.randint(18, 22)), rng.choice("MF"), "adult_child")
            elif t == "married_nokids":
                hs = "M" if rng.random() < .55 else "F"
                h = person(H, a, hs, "head")
                sp = person(H, a + int(rng.gauss(-1.5 if hs == "M" else 1.5, 3.5)), osex(hs), "spouse")
                sp.age = max(18, sp.age)
            elif t == "single_parent":
                hs = "F" if rng.random() < .80 else "M"
                h = person(H, a, hs, "head")
                kids_for(H, a if hs == "F" else a - 2, rng.choices([1, 2, 3, 4], [.50, .31, .13, .06])[0])
            elif t == "alone":
                pf = .67 if a >= 75 else (.58 if a >= 65 else .46)
                person(H, a, "F" if rng.random() < pf else "M", "head")
            elif t == "roommates":
                hs = rng.choice("MF")
                person(H, a, hs, "head")
                if rng.random() < .45:
                    person(H, max(18, a + int(rng.gauss(0, 3))), osex(hs) if rng.random() < .9 else hs, "unmarried_partner")
                else:
                    for _i in range(rng.choices([1, 2, 3], [.62, .26, .12])[0]):
                        person(H, max(18, a + int(rng.gauss(0, 4))), rng.choice("MF"), "roommate")
            elif t == "multigen":
                if rng.random() < .55:
                    hs = rng.choice("MF")
                    person(H, a, hs, "head")
                    if rng.random() < .5:
                        person(H, a + int(rng.gauss(0, 3)), osex(hs), "spouse")
                    ca = max(19, a - rng.randint(20, 32))
                    cs = rng.choice("MF")
                    person(H, ca, cs, "adult_child")
                    if rng.random() < .35:
                        person(H, max(19, ca + int(rng.gauss(0, 3))), osex(cs), "child_in_law")
                    for k in kids_for(H, ca, rng.choices([1, 2, 3], [.5, .35, .15])[0]):
                        k.rel = "grandchild"
                else:
                    a2 = rng.randint(31, 50)
                    hs = rng.choice("MF")
                    person(H, a2, hs, "head")
                    if rng.random() < .7:
                        person(H, a2 + int(rng.gauss(0, 3)), osex(hs), "spouse")
                    kids_for(H, a2, rng.choices([1, 2, 3], [.4, .4, .2])[0])
                    pa = a2 + rng.randint(22, 33)
                    person(H, pa, "F" if rng.random() < .68 else "M", "parent")
                    if rng.random() < .3:
                        person(H, pa + int(rng.gauss(1, 3)), "M", "parent")
            elif t == "adult_child":
                hs = rng.choice("MF")
                person(H, a, hs, "head")
                if rng.random() < .68:
                    person(H, a + int(rng.gauss(0, 3)), osex(hs), "spouse")
                for _i in range(1 if rng.random() < .75 else 2):
                    person(H, min(38, max(18, a - rng.randint(20, 36))), rng.choice("MF"), "adult_child")
                if rng.random() < .2 and a < 60:
                    person(H, rng.randint(12, 17), rng.choice("MF"), "child")
            else:  # other_family
                v = rng.random()
                if v < .38:      # grandparent(s) raising grandchildren
                    a = max(a, rng.randint(52, 72))
                    hs = "F" if rng.random() < .65 else "M"
                    person(H, a, hs, "head")
                    if rng.random() < .5:
                        person(H, a + int(rng.gauss(0, 3)), osex(hs), "spouse")
                    for _i in range(rng.choice([1, 1, 2])):
                        person(H, rng.randint(2, 16), rng.choice("MF"), "grandchild")
                else:           # siblings or other relatives
                    person(H, a, rng.choice("MF"), "head")
                    for _i in range(rng.choice([1, 1, 2])):
                        person(H, max(18, a + int(rng.gauss(0, 6))), rng.choice("MF"), "sibling" if v < .8 else "other_relative")
            for p in H.members:
                p.age = max(0, min(101, p.age))

    # ---------- 2. group quarters (each resident is a one-person unit flagged in household_type)
    for kind, d, n, fac in GQ_PLAN:
        for _ in range(max(1, int(round(n * scale)))):
            H = Household("H%05d" % (len(HH) + 1), d, "group_quarters:" + kind)
            H.gq, H.facility = kind, fac
            HH.append(H)
            if kind in ("nursing_home", "assisted_living"):
                a = int(min(101, max(58, rng.gauss(83, 9))))
                person(H, a, "F" if rng.random() < .66 else "M", "resident")
            elif kind == "college_dorm":
                person(H, rng.choices([18, 19, 20, 21, 22], [.3, .28, .22, .15, .05])[0], rng.choice("MF"), "resident")
            elif kind == "jail":
                person(H, int(min(70, max(18, rng.gauss(35, 11)))), "M" if rng.random() < .86 else "F", "resident")
            elif kind == "group_home":
                person(H, rng.randint(19, 68), rng.choice("MF"), "resident")
            elif kind == "shelter":
                person(H, int(min(75, max(18, rng.gauss(44, 13)))), "M" if rng.random() < .68 else "F", "resident")
            else:
                person(H, rng.randint(19, 60), "M" if rng.random() < .6 else "F", "resident")

    # ---------- 3. race, language, latent SES, disability, education, veteran
    LANG_ASIAN = ["Chinese", "Vietnamese", "Tagalog", "Korean", "Hindi", "Gujarati", "Nepali"]
    for H in HH:
        d = H.district
        H.race = rng.choices(RACES, RACE_D[d])[0]
        H.z = rng.gauss(Z_D[d], 1.15 if d == "D1" else 1.0)
        if H.gq == "college_dorm":
            H.z = rng.gauss(.4, .8)
        elif H.gq in ("jail", "shelter", "group_home", "residential_treatment"):
            H.z = rng.gauss(-1.0, .7)
        r = rng.random()
        if H.race == "hispanic":
            H.lang = "Spanish" if r < .52 else "English"
        elif H.race == "asian_non_hispanic":
            H.lang = rng.choice(LANG_ASIAN) if r < .55 else "English"
        elif H.race == "white_non_hispanic":
            H.lang = rng.choice(["Russian", "Arabic", "Polish", "Portuguese", "Ukrainian", "Bosnian"]) if r < .035 else "English"
        elif H.race == "black_non_hispanic":
            H.lang = rng.choice(["Haitian Creole", "French", "Amharic", "Somali", "Swahili"]) if r < .07 else "English"
        else:
            H.lang = rng.choice(["Spanish", "Arabic", "Karen", "Marshallese"]) if r < .08 else "English"
        if H.gq and H.gq != "shelter":
            H.lang = "English" if rng.random() < .95 else H.lang
        if H.lang != "English":
            H.lep = rng.random() < .30
            H.immigrant = rng.random() < .80
            H.recent = H.immigrant and rng.random() < .16
        else:
            H.immigrant = rng.random() < .045
            H.recent = H.immigrant and rng.random() < .06
        for p in H.members:
            p.race = H.race
            if p.rel in ("spouse", "unmarried_partner", "roommate", "child_in_law") and rng.random() < (.12 if p.rel != "roommate" else .45):
                p.race = rng.choices(RACES, RACE_D[d])[0]
        if len({p.race for p in H.members if p.rel in ("head", "spouse", "unmarried_partner")}) > 1:
            for p in H.members:
                if p.rel in ("child", "grandchild"):
                    p.race = "multiracial_or_other"
    cuts = [-1.31, -.372, .113, .358, 1.103]
    for H in HH:
        for p in H.members:
            a = p.age
            pd = tbl(DIS_AGE, a) * (1.35 if H.z < -.8 else (.75 if H.z > .8 else 1))
            if H.gq in ("nursing_home", "assisted_living"):
                pd = .97
            elif H.gq == "group_home":
                pd = 1.0
            elif H.gq in ("shelter", "residential_treatment"):
                pd = .42
            if rng.random() < pd:
                if a < 18:
                    p.dis = rng.choices(["cognitive", "hearing", "vision", "ambulatory", "self_care"], [.62, .1, .1, .1, .08])[0]
                elif a < 65:
                    p.dis = rng.choices(["cognitive", "ambulatory", "independent_living", "hearing", "vision", "self_care", "multiple"], [.30, .26, .12, .10, .08, .04, .10])[0]
                else:
                    p.dis = rng.choices(["ambulatory", "hearing", "independent_living", "cognitive", "vision", "self_care", "multiple"], [.32, .20, .13, .10, .07, .06, .12])[0]
                if H.gq == "nursing_home":
                    p.dis = rng.choice(["self_care", "multiple", "cognitive", "ambulatory"])
                elif H.gq == "group_home":
                    p.dis = rng.choice(["cognitive", "cognitive", "independent_living", "multiple"])
            else:
                p.dis = "none"
            if a >= 18:
                e = .72 * H.z + .69 * rng.gauss(0, 1) + (.12 if 25 <= a < 45 else (-.15 if a >= 70 else 0))
                lvl = sum(1 for c in cuts if e > c)
                if a < 22:
                    lvl = min(lvl, 2)
                elif a < 24:
                    lvl = min(lvl, 4)
                if H.gq == "college_dorm":
                    lvl = 2
                elif H.gq in ("group_home", "shelter", "residential_treatment", "jail"):
                    lvl = min(lvl, 2)
                p.edu = lvl
            pv = 0.0
            if a >= 18:
                if p.sex == "M":
                    pv = .30 if a >= 75 else (.20 if a >= 65 else (.075 if a >= 35 else .025))
                else:
                    pv = .016 if a < 65 else .012
            p.vet = rng.random() < pv

    # ---------- 4. employment
    adults = [p for p in PP if p.age >= 16]
    base = []
    for p in adults:
        H = p.hh
        q = tbl(EMP_AGE, p.age)
        if p.edu is not None:
            q += (.06 if p.edu == 5 else .04 if p.edu == 4 else (-.10 if p.edu == 0 else 0))
        if p.sex == "F" and any(k.age < 5 for k in H.members) and p.rel in ("head", "spouse", "unmarried_partner", "adult_child"):
            q -= .11
        q += .035 * H.z
        if p.age >= 80:     # very few people work past 80; almost none past 90
            q = min(q, .030 if p.age < 85 else (.011 if p.age < 90 else .003))
        if p.dis != "none":
            q *= .22 if p.dis in ("self_care", "independent_living", "multiple") else .42
        if H.gq in ("nursing_home", "assisted_living", "jail", "residential_treatment"):
            q = 0.0
        elif H.gq == "college_dorm":
            q = .33
        elif H.gq == "group_home":
            q = .15
        elif H.gq == "shelter":
            q = .28
        base.append(min(.985, max(0.0, q)))
    target = .48 * len(PP)
    lo, hi = -3.0, 3.0
    arr = np.array(base)
    lg = np.log(np.clip(arr, 1e-6, 1 - 1e-6) / (1 - np.clip(arr, 1e-6, 1 - 1e-6)))
    for _ in range(40):
        mid = (lo + hi) / 2
        s = (1 / (1 + np.exp(-(lg + mid))) * (arr > 0)).sum()
        if s < target:
            lo = mid
        else:
            hi = mid
    pe = 1 / (1 + np.exp(-(lg + (lo + hi) / 2))) * (arr > 0)
    u = nrg.random(len(adults))
    emp = [p for p, a, b in zip(adults, pe, u) if b < a]
    for p in emp:
        a = p.age
        ppt = .75 if a < 20 else .32 if a < 25 else .11 if a < 55 else .15 if a < 65 else .42
        if p.sex == "F" and any(k.age < 13 for k in p.hh.members) and 25 <= a < 55:
            ppt = .19
        if p.hh.gq:
            ppt = .9
        p.ft = rng.random() > ppt
        p.emp = "employed_full_time" if p.ft else "employed_part_time"
    # sectors by iterative proportional fitting
    codes = [c for c, _, _ in SECTORS]
    A = np.zeros((len(emp), len(codes)))
    for i, p in enumerate(emp):
        e = p.edu if p.edu is not None else 0
        d = p.hh.district
        for j, c in enumerate(codes):
            ew, fs = SEC_AFF[c]
            w = ew[e] * (fs if p.sex == "F" else 1 - fs) * 2
            w *= SEC_DIST.get(c, {}).get(d, 1.0)
            if p.age < 25:
                w *= SEC_YOUNG.get(c, 1.0)
            elif p.age >= 55:
                w *= SEC_OLD.get(c, 1.0)
            if not p.ft and c in ("mfg", "constr", "mgmt", "util", "fin"):
                w *= .35
            A[i, j] = w
    tgt = np.array([s for _, _, s in SECTORS])
    tgt = tgt / tgt.sum() * len(emp)
    wv = np.ones(len(codes))
    for _ in range(25):
        P = A * wv
        P /= P.sum(1, keepdims=True)
        wv *= tgt / P.sum(0)
    P = A * wv
    P /= P.sum(1, keepdims=True)
    cum = P.cumsum(1)
    uu = nrg.random(len(emp))
    sidx = (cum < uu[:, None]).sum(1).clip(0, len(codes) - 1)
    for p, j in zip(emp, sidx):
        p.sector = codes[j]

    by_kind = sim.by_kind
    secorgs = {}
    for o in sim.orgs:
        if o.district == "EXT" or o.kind.startswith("school_") and o.kind != "school_district":
            continue
        for c in codes:
            if o.sector == C.SECNAME[c]:
                secorgs.setdefault(c, []).append(o)
    OK = OCC_KINDS
    outemp = by_kind["x_outemp"][0]
    for p in emp:
        H, c = p.hh, p.sector
        e = p.edu if p.edu is not None else 0
        occs = OCC[c]
        ws = []
        for (t, wg, w, me, sk, tip) in occs:
            f = 1.0 if e >= me else (.04 if me - e >= 2 else .15)
            if me <= 1 and e >= 4:
                f *= .25
            if p.age < 22 and wg > 60000:
                f *= .1
            ws.append(w * f)
        t, wg, w, me, sk, tip = rng.choices(occs, ws)[0]
        p.occ, p.sched, p.tipped = t, sk, bool(tip)
        af = .72 if p.age < 20 else .82 if p.age < 25 else .92 if p.age < 30 else 1.0 if p.age < 40 else 1.06 if p.age < 55 else 1.04 if p.age < 65 else .92
        sg = .42 if me >= 4 else .22
        wage = wg * C.WAGE_SCALE * math.exp(rng.gauss(0, sg) + .13 * H.z) * af   # WAGE_SCALE pays ~14% above real pay on purpose; see config.py
        if wg >= 130000 and rng.random() < .12:
            wage *= rng.uniform(1.3, 2.6)
        hrs = 1.0 if p.ft else rng.uniform(.35, .72)
        p.seasonal = t in ("crop farmworker", "landscaping worker", "golf course groundskeeper", "landscaper", "lifeguard")
        if p.seasonal:
            hrs *= .8
        p.wage = max(wage * hrs, 4500)
        if c == "self":
            p.emp = "self_employed"
            p.org, p.cadence, p.wd = None, "irregular", H.district
            p.gig = t == "rideshare and delivery driver"
        else:
            if rng.random() < .05 and not H.gq:
                p.org, p.wd = outemp, "EXT"
            else:
                kinds = OK.get(t)
                cand = []
                if kinds:
                    for k in kinds:
                        cand.extend(by_kind.get(k, []))
                if not cand:
                    cand = secorgs.get(c, [])
                if t == "nanny":
                    p.org = by_kind["x_customers"][0]
                    p.wd = rng.choice(["D3", "D3", "D1", H.district])
                else:
                    wts = [o.size * (1.0 if o.district == H.district else math.exp(-DIST[(H.district, o.district)] / 16.0) + .04) for o in cand]
                    p.org = rng.choices(cand, wts)[0]
                    p.wd = p.org.district
                    p.org.emp += 1
            cw = CADENCE.get(c, CADENCE["default"])
            p.cadence = rng.choices(["weekly", "biweekly", "semimonthly", "monthly"], cw)[0]
            if p.cadence in ("weekly", "biweekly"):
                p.payday = (rng.choices([x[1] for x in PAY_WEEKDAY], [x[0] for x in PAY_WEEKDAY])[0], rng.randint(0, 1))
            elif p.cadence == "semimonthly":
                p.payday = rng.choices([(15, 31), (1, 16), (5, 20), (3, 18)], [.60, .25, .12, .03])[0]
            else:
                p.payday = rng.choices([(1,), (31,), (15,)], [.45, .45, .10])[0]
            p.union = rng.random() < UNION.get(c, .03) * (1.7 if t in ("public school teacher", "police officer", "firefighter", "mail carrier", "transit bus operator", "electrical lineworker", "electrician") else 1.0)
        # stable shift slot
        if sk in ("shift3",):
            p.slot = rng.choices([1, 2, 3], [.52, .28, .20])[0]
        elif sk == "shift12":
            p.slot = rng.choices([1, 3], [.66, .34])[0]
        elif sk == "night":
            p.slot = 3
        else:
            p.slot = 0
        p.wsched = ("night" if p.slot == 3 or sk == "late" else "variable" if sk in ("var", "gig", "farm") else "fixed")
        if c in ("retail", "food", "admin", "self", "trans", "arts") and p.age < 45 and not p.gig and rng.random() < .06:
            p.gig = True     # side gig on top of main job
    # everyone else
    for p in adults:
        if p.emp.startswith("employed") or p.emp == "self_employed":
            continue
        H, a = p.hh, p.age
        if H.gq == "college_dorm":
            p.emp, p.student = "student", "college"
        elif H.gq in ("nursing_home", "assisted_living"):
            p.emp = "retired"
        elif H.gq == "jail":
            p.emp = "not_in_labor_force"
        elif a < 19:
            p.emp = "student"
        elif a < 25 and rng.random() < .42:
            p.emp, p.student = "student", "college"
        elif a >= 62 or (a >= 55 and rng.random() < .25):
            p.emp = "retired"
        elif p.dis != "none" and rng.random() < .7:
            p.emp = "not_in_labor_force"
        elif rng.random() < (.27 if a < 55 else .13):
            p.emp = "unemployed"
        else:
            p.emp = "not_in_labor_force"
    for p in emp:
        if p.hh.gq == "college_dorm" or (p.age < 25 and not p.ft and rng.random() < .55 and p.age >= 18):
            p.student = "college"

    # ---------- 5. children and students
    schools = {}
    for k in ("school_elem", "school_mid", "school_high"):
        for o in by_kind.get(k, []):
            schools.setdefault((k, o.district), []).append(o)
    priv = by_kind.get("private_school", [])
    for H in HH:
        d = H.district
        for p in H.members:
            a = p.age
            if 5 <= a <= 17 or (a == 18 and p.emp == "student" and rng.random() < .5):
                r = rng.random()
                ppriv = .05 + .07 * max(0, H.z)
                g = min(12, max(0, a - 5))
                p.grade = g
                if a >= 16 and rng.random() < .03:
                    p.student = None      # left school
                    continue
                if r < ppriv and priv:
                    p.student, p.school = "private_k12", rng.choice(priv)
                elif r < ppriv + .035:
                    p.student = "homeschool"
                else:
                    k = "school_elem" if g <= 5 else ("school_mid" if g <= 8 else "school_high")
                    dd = d
                    if (k, dd) not in schools:
                        dd = "D5" if d == "D6" else d
                    lst = schools.get((k, dd)) or schools.get((k, "D1"))
                    p.student, p.school = "public_k12", lst[int(H.hid[1:]) % len(lst)]
            elif a < 5:
                p.student = None

    # ---------- 6. non-wage income
    for H in HH:
        for p in H.members:
            a = p.age
            working_ft = p.emp == "employed_full_time"
            if a >= 62:
                ps = .33 if a < 65 else .68 if a < 67 else .90 if a < 70 else .96
                if working_ft and a < 67:
                    ps *= .25
                if rng.random() < ps:
                    b = SS_AVG_RETIRED * math.exp(.20 * H.z + rng.gauss(0, .26)) * (.90 if p.sex == "F" else 1.07)
                    if a < 67:
                        b *= .82
                    p.ss, p.ss_type = min(5100, max(640, b)), "social_security_retirement"
            if p.ss == 0 and 18 <= a < 67 and p.dis != "none" and not working_ft:
                if rng.random() < (.52 if p.emp != "employed_part_time" else .18):
                    p.ss, p.ss_type = min(3600, max(560, rng.gauss(SS_AVG_DISABLED, 430))), "ssdi"
            if p.ss == 0 and a < 62 and a >= 18 and p.rel == "head" and H.htype in ("single_parent", "alone") and rng.random() < .012:
                p.ss, p.ss_type = rng.uniform(900, 2300), "social_security_survivor"
            # SSI
            if a >= 18 and p.dis != "none" and not working_ft and H.z < .3:
                if p.ss == 0 and rng.random() < .58:
                    p.ssi = SSI_FBR * (1 if p.rel in ("head", "spouse", "resident") else .667)
                elif 0 < p.ss < SSI_FBR and rng.random() < .75:
                    p.ssi = SSI_FBR + 20 - p.ss
            elif a >= 65 and p.ss < 780 and H.z < -.4 and rng.random() < .55:
                p.ssi = max(40, SSI_FBR + 20 - p.ss)
            elif a < 18 and p.dis != "none" and H.z < -.2 and rng.random() < .45:
                p.ssi = SSI_FBR * .85
            if H.gq == "nursing_home" and p.ssi:
                p.ssi = 30.0
            # pensions, retirement draws, investment income
            if a >= 60 and p.emp == "retired":
                if rng.random() < .30 + .06 * H.z:
                    p.pension = max(250, rng.lognormvariate(math.log(1750), .6) * math.exp(.15 * H.z))
                if rng.random() < .24 + .13 * H.z:
                    p.inv += max(150, rng.lognormvariate(math.log(1300), .8) * math.exp(.3 * H.z))
            if a >= 25 and rng.random() < 1 / (1 + math.exp(-(1.6 * H.z - 2.4))):
                p.inv += rng.lognormvariate(math.log(900), 1.2) * math.exp(.35 * H.z)
            if p.emp == "unemployed" and rng.random() < .24:
                p.ui = rng.uniform(210, 560) * 4.33
            if p.vet and rng.random() < .31:
                p.va = rng.choices([185, 560, 1150, 1780, 2450, 3940], [.22, .2, .18, .15, .13, .12])[0] * rng.uniform(.95, 1.05)
    ret = [p.ss for p in PP if p.ss_type == "social_security_retirement"]
    if ret:
        k = SS_AVG_RETIRED / (sum(ret) / len(ret))
        for p in PP:
            if p.ss_type == "social_security_retirement":
                p.ss = round(min(5180, p.ss * k), 2)

    # ---------- 7. household roll-up: income, poverty, ALICE
    for H in HH:
        H.head = H.members[0]
        H.adults = [p for p in H.members if p.age >= 18]
        H.kids = [p for p in H.members if p.age < 18]
        if not H.adults:
            H.adults = [H.head]
        if H.htype == "single_parent" and rng.random() < .31:
            H.cs = rng.choice([180, 260, 340, 420, 520, 640, 800]) * rng.uniform(.9, 1.1)
        for p in H.members:
            p.income = p.wage + 12 * (p.ss + p.ssi + p.pension + p.ui + p.va + p.inv)
        H.income = sum(p.income for p in H.members) + 12 * H.cs
        n = len(H.members)
        pov = POVERTY_BASE + POVERTY_STEP * (n - 1)
        H.pov_ratio = H.income / pov
        if H.htype == "single_parent" and H.pov_ratio < .5 and rng.random() < .30 or (H.htype == "other_family" and H.kids and H.pov_ratio < .7 and rng.random() < .25):
            H.tanf = rng.choice([310, 420, 480, 540, 610])
            H.tanf_day = rng.choice([1, 2, 3])
            H.income += 12 * H.tanf
            H.pov_ratio = H.income / pov

    def budget(H):
        ad = max(1, len(H.adults))
        b = 36000 + 15500 * (ad - 1) + 21000 * sum(1 for k in H.kids if k.age < 5) + 12000 * sum(1 for k in H.kids if k.age >= 5)
        if all(p.age >= 65 for p in H.adults):
            b += 2500
        return b * {"D1": 1.05, "D2": 1.0, "D3": 1.08, "D4": .95, "D5": .88, "D6": .90}[H.district]
    reg = [H for H in HH if not H.gq]
    ratios = sorted(H.income / budget(H) for H in reg)
    npov = sum(1 for H in reg if H.pov_ratio < 1)
    kq = ratios[int(.415 * len(ratios))]          # scale the survival budget so ~41.5% fall below it (anchor: ~4 in 10)
    sim.alice_scale = kq
    for H in HH:
        if H.pov_ratio < 1:
            H.alice = "poverty"
        elif H.gq:
            H.alice = "alice" if H.income < 30000 else "above"
        else:
            H.alice = "alice" if H.income / budget(H) < kq else "above"

    # ---------- 8. coverage
    for H in HH:
        fpl = H.pov_ratio
        emp_cov = None
        for p in H.adults:
            if p.emp == "employed_full_time" and p.sector != "self":
                offer = .95 if p.sector in ("gov", "fed", "mfg", "fin", "util", "mgmt", "prof", "health", "info", "whole", "pedu") else .72
                take = .62 if p.wage < 30000 else .84 if p.wage < 55000 else .95
                if rng.random() < offer * take:
                    emp_cov = p
                    break
        for p in H.members:
            a = p.age
            r = rng.random()
            dual_ok = (fpl < 1.38 or p.ssi > 0)
            if H.gq == "jail":
                p.cov = "uninsured"
            elif a >= 65 or (p.ss_type == "ssdi" and r < .85):
                if a >= 65 and p.emp == "employed_full_time" and emp_cov is p:
                    p.cov = "employer"
                elif dual_ok and rng.random() < .80 or H.gq == "nursing_home" and rng.random() < .62:
                    p.cov = "medicare_medicaid_dual"
                elif rng.random() < .54:
                    p.cov = "medicare_advantage"
                else:
                    p.cov = "medicare"
                    p.medigap = rng.random() < (.45 + .12 * H.z)
            elif p.ssi > 0:
                p.cov = "medicaid"
            elif p.vet and r < .22:
                p.cov = "va"
            elif p.occ == "active-duty service member" or (H.head.occ == "active-duty service member"):
                p.cov = "military"
            elif a < 19:
                if fpl < 1.38:
                    p.cov = "medicaid" if r < .88 else "uninsured"
                elif fpl < 2.5:
                    p.cov = "employer" if (emp_cov and r < .50) else ("medicaid" if r < .90 else "uninsured")
                else:
                    p.cov = "employer" if emp_cov and r < .95 else ("marketplace" if r < .55 else "medicaid" if r < .80 else "uninsured")
            else:
                if emp_cov is p:
                    p.cov = "employer"
                elif emp_cov and p.rel in ("spouse", "head", "unmarried_partner") and r < (.86 if p.rel != "unmarried_partner" else .40):
                    p.cov = "employer"
                elif emp_cov and p.rel in ("child", "adult_child") and a < 26 and r < .75:
                    p.cov = "employer"
                elif H.gq == "college_dorm":
                    p.cov = "employer" if r < .72 else ("marketplace" if r < .86 else "uninsured")
                elif fpl < 1.38:
                    p.cov = "medicaid" if r < .66 else ("marketplace" if r < .73 else "uninsured")
                elif fpl < 4.0:
                    p.cov = "marketplace" if r < .34 else ("medicaid" if r < .45 else "uninsured" if r < .80 else "other_private")
                else:
                    p.cov = "marketplace" if r < .50 else ("other_private" if r < .72 else "uninsured")
            if p.cov in ("employer", "marketplace", "other_private"):
                p.plan = "hdhp" if rng.random() < (.32 if p.cov == "employer" else .58) else "copay"
            dc = {"employer": .80, "medicaid": 1.0 if a < 21 else .42, "medicare_advantage": .6, "medicare": .12,
                  "medicare_medicaid_dual": .45, "marketplace": .25, "military": .9, "va": .3, "other_private": .3}.get(p.cov, 0)
            p.dental = rng.random() < dc

    # ---------- 9. tenure, housing cost, vehicles, internet, banking
    def own_logit(H):
        a = min(78, H.head.age)
        x = -1.9 + .052 * (a - 18) + 1.05 * math.log(max(H.income, 6000) / 60000.0)
        x += {"married_kids": .9, "married_nokids": .9, "alone": -.2, "roommates": -1.7, "single_parent": -.5,
              "multigen": .5, "adult_child": .8, "cohab_kids": -.5, "other_family": .1}[H.htype]
        x += {"D1": -1.0, "D2": -.3, "D3": .8, "D4": 0, "D5": .35, "D6": 1.0}[H.district]
        return x
    lgs = np.array([own_logit(H) for H in reg])
    lo, hi = -4.0, 4.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if (1 / (1 + np.exp(-(lgs + mid)))).mean() < .65:
            lo = mid
        else:
            hi = mid
    po = 1 / (1 + np.exp(-(lgs + (lo + hi) / 2)))
    RENT = {"D1": 1790, "D2": 1560, "D3": 2080, "D4": 1380, "D5": 1010, "D6": 930}
    PITI = {"D1": 1700, "D2": 1500, "D3": 2180, "D4": 1380, "D5": 1020, "D6": 1080}
    landlords = {d: [o for o in by_kind["landlord"] if o.district == d] for d in DISTRICTS}
    ha = by_kind["housing_authority"][0]
    for H, pown in zip(reg, po):
        d, n, mi = H.district, len(H.members), H.income / 12.0
        a = H.head.age
        if rng.random() < pown:
            pm = .88 if a < 35 else .85 if a < 45 else .76 if a < 55 else .58 if a < 65 else .38 if a < 75 else .20
            H.mortgage = rng.random() < pm
            H.mobile_home = d in ("D2", "D5", "D6") and H.z < -.2 and rng.random() < (.30 if d != "D2" else .12)
            if H.mortgage:
                H.tenure = "owner_with_mortgage"
                H.housing_cost = min(9800, max(PITI[d] * rng.uniform(.75, 1.15), mi * rng.uniform(.14, .29)))
                if H.mobile_home:
                    H.housing_cost = rng.uniform(520, 900)
                H.escrow = rng.random() < .80
            else:
                H.tenure = "owner_free_and_clear"
                H.housing_cost = max(260, min(1900, (PITI[d] * .30 + mi * .035) * rng.uniform(.7, 1.3)))
                if H.mobile_home:
                    H.housing_cost = rng.uniform(380, 560)       # lot rent
            if d == "D3" and rng.random() < .62:
                H.hoa = rng.choice([35, 45, 60, 85, 110, 140])
            elif d == "D1" and rng.random() < .35:
                H.hoa = rng.choice([220, 310, 380, 460])
        else:
            H.tenure = "renter"
            sf = {1: .82, 2: .93, 3: 1.03, 4: 1.14}.get(n, 1.25)
            rent = RENT[d] * sf * math.exp(.12 * H.z + rng.gauss(0, .17))
            if H.alice == "poverty" and rng.random() < .30 or (H.alice == "alice" and rng.random() < .05):
                H.subsidized = True
                rent = max(50, .30 * mi)
                H.landlord = ha if rng.random() < .45 else rng.choice(landlords[d] or landlords["D1"])
                H.notes.append("subsidized_housing")
            else:
                if rent > .72 * mi:
                    rent = max(380, .72 * mi * rng.uniform(.85, 1.0)) if mi > 0 else 380
                H.landlord = rng.choice(landlords[d] or landlords["D1"])
            H.housing_cost = rent
            H.util_incl = rng.random() < (.30 if d == "D1" else .12)
            H.mobile_home = d in ("D2", "D5", "D6") and rng.random() < .15
        H.housing_cost = round(H.housing_cost, 0)
        H.washer = H.tenure != "renter" or rng.random() < (.45 if d in ("D1", "D2") else .7)
        H.gasheat = rng.random() < {"D1": .62, "D2": .62, "D3": .66, "D4": .58, "D5": .40, "D6": .12}[d]
        # vehicles
        nad = len([p for p in H.members if p.age >= 16])
        p0 = {"D1": .20, "D2": .09, "D3": .02, "D4": .08, "D5": .06, "D6": .025}[d]
        p0 *= 2.3 if H.alice == "poverty" else 1.3 if H.alice == "alice" else .5
        if a >= 80:
            p0 *= 2
        if rng.random() < min(.9, p0):
            H.vehicles = 0
        else:
            if nad <= 1:
                v = rng.choices([1, 2], [.88, .12])[0]
            elif nad == 2:
                v = rng.choices([1, 2, 3], [.26, .58, .16])[0]
            else:
                v = rng.choices([2, 3, 4], [.35, .45, .20])[0]
            if H.alice != "above" and v > 1 and rng.random() < .40:
                v -= 1
            if d in ("D5", "D6") and H.z > .2 and rng.random() < .35:
                v += 1
            H.vehicles = v
            if H.z > .5 and d in ("D1", "D2", "D3") and rng.random() < .09:
                H.ev = 1
        # internet
        pn = .035 + (.11 if a >= 75 else 0) + (.07 if H.alice == "poverty" else 0) + (.05 if d in ("D5", "D6") else 0)
        pmob = .06 + (.10 if H.alice == "poverty" else .06 if H.alice == "alice" else 0) + (.04 if a < 35 else 0) + (.05 if d in ("D5", "D6") else 0)
        r = rng.random()
        H.internet = "no" if r < pn else ("mobile_only" if r < pn + pmob else "yes")
        # banking
        pu = {"poverty": .16, "alice": .045, "above": .006}[H.alice] * (1.5 if H.lep else 1.0)
        pub = {"poverty": .28, "alice": .20, "above": .07}[H.alice]
        r = rng.random()
        H.banked = "unbanked" if r < pu else ("underbanked" if r < pu + pub else "banked")
        H.pets = 0 if rng.random() > .62 else rng.choice([1, 1, 2])
        H.rent_day = None
    for H in HH:
        if H.gq:
            H.tenure = "group_quarters"
            H.internet = "yes" if H.gq in ("college_dorm", "assisted_living") else ("mobile_only" if H.gq in ("shelter", "group_home", "residential_treatment") else "no")
            H.banked = ("banked" if H.gq in ("college_dorm", "assisted_living") or rng.random() < .5 else rng.choice(["unbanked", "underbanked"]))
            if H.gq == "jail":
                H.banked = "unbanked"
            H.vehicles = 1 if (H.gq == "college_dorm" and rng.random() < .35) else 0
            H.housing_cost = 0

    # ---------- 10. benefits
    for H in HH:
        if H.gq:
            continue
        n, mi = len(H.members), H.income / 12.0
        pov_m = (POVERTY_BASE + POVERTY_STEP * (n - 1)) / 12.0
        eld = all((p.age >= 60 or p.dis != "none") for p in H.adults)
        if mi <= (2.0 if eld else 1.30) * pov_m:
            part = .50 if eld and not H.kids else (.86 if H.kids else .60)
            if H.recent:
                part *= .35
            if rng.random() < part:
                earned = sum(p.wage for p in H.members) / 12.0
                std = 215 if n <= 3 else 229 if n == 4 else 268 if n == 5 else 308
                inc2 = max(0, mi - .2 * earned - std)
                shelter = H.housing_cost + (0 if H.util_incl else 430)
                ex = max(0, shelter - .5 * inc2)
                if not eld:
                    ex = min(ex, 769)
                net = max(0, inc2 - ex)
                ben = SNAP_MAX.get(n, SNAP_MAX[8] + 225 * (n - 8)) - .3 * net
                if ben < 25 and n <= 2:
                    ben = 25
                if ben >= 20:
                    H.snap = round(ben)
                    rng.randint(1, 10)   # v1's load-day draw, kept so the main stream (and the people) stay the same
                    H.snap_day = C.draw_table(C.side_rng(sim.cfg["RANDOM_SEED"], "snap_day", H.hid).random(), C.SNAP_LOAD_DAYS)
        wic_ok = [p for p in H.members if p.age < 5]
        if wic_ok and (mi <= 1.85 * pov_m or H.snap) and rng.random() < .74:
            H.wic = 62.0 * len(wic_ok) + (58 if any(p.age < 1 for p in wic_ok) else 0)
            H.wic_day = rng.randint(1, 28)
        if H.alice == "poverty" and rng.random() < .07:
            H.liheap = True
        for p in H.members:
            if p.student == "public_k12":
                cep = "community eligibility" in p.school.notes
                if cep or mi <= 1.30 * pov_m or H.snap or H.tanf:
                    p.meal = "free"
                elif mi <= 1.85 * pov_m:
                    p.meal = "reduced"
                else:
                    p.meal = "paid"
            if p.age in (3, 4):
                r = rng.random()
                if mi <= pov_m * 1.0 and r < .38:
                    p.student = "head_start"
                elif r < (.62 if p.age == 4 else .16):
                    p.student = "public_prek"
        working_parents = all(q.emp.startswith("employed") or q.emp == "self_employed" for q in H.adults if q.rel in ("head", "spouse", "unmarried_partner"))
        has_gran = any(q.rel in ("parent",) or (q.rel == "head" and H.htype == "multigen") for q in H.adults if q.emp in ("retired", "not_in_labor_force"))
        for p in H.members:
            if p.age < 5 and p.student is None and working_parents:
                r = rng.random()
                if has_gran and r < .7:
                    p.student = "relative_care"
                elif r < .44:
                    p.student = "child_care_center"
                elif r < .62:
                    p.student = "family_child_care"
                elif r < .86:
                    p.student = "relative_care"
        if any(p.student in ("child_care_center", "family_child_care") for p in H.members) and H.pov_ratio < 2.0 and rng.random() < .22:
            H.ccdf = True

    # ---------- 11. payment cohorts, labels, misc person attributes
    for H in HH:
        for p in H.members:
            if p.ss > 0:
                start_year = p.by + (62 if p.ss_type == "social_security_retirement" else 40)
                if p.ssi > 0 or p.cov == "medicare_medicaid_dual" or start_year < 1997 and p.age > 91:
                    p.ss_cohort = "3rd"
                else:
                    p.ss_cohort = "wed2" if p.bday <= 10 else ("wed3" if p.bday <= 20 else "wed4")
            a = p.age
            lam = .25 if a < 18 else .5 if a < 35 else 1.0 if a < 50 else 2.2 if a < 65 else 4.0 if a < 80 else 5.0
            if p.dis != "none":
                lam += 1.5
            p.nrx = int(nrg.poisson(lam))
            pes = (.0045 if a >= 45 else .0007 if a >= 18 else 0) * (2.2 if p.dis != "none" else .8)
            p.esrd = rng.random() < pes and not H.gq == "jail"
            if p.dis in ("self_care", "independent_living", "multiple", "ambulatory", "cognitive") and a >= 18 and not H.gq:
                if rng.random() < (.36 if a >= 65 else .10):
                    p.home_care = "medicaid" if p.cov in ("medicare_medicaid_dual", "medicaid") else rng.choice(["medicare", "private_pay", "private_pay"])
            if a >= 18:
                ps = [.20, .17, .13, .11, .05, .03][p.edu if p.edu is not None else 1] * (.6 if a >= 65 else 1)
                p.smoker = rng.random() < ps
            cp = .15 + (.25 if a >= 55 else 0) + (.15 if a >= 70 else 0) + (.20 if H.alice == "poverty" else .10 if H.alice == "alice" else 0)
            cp += (.17 if H.district in ("D5", "D6") else 0) + (.15 if H.banked == "underbanked" else 0) - (.10 if a < 35 else 0) - (.10 if H.income > 150000 else 0)
            p.cashpref = .95 if H.banked == "unbanked" else min(.92, max(.02, cp + rng.gauss(0, .08)))
            if 20 <= a <= 60 and (p.edu or 0) >= 2:
                psl = (.34 if a < 35 else .22 if a < 45 else .11) * (1.2 if (p.edu or 0) >= 4 else .8)
                if rng.random() < psl:
                    p.sloan = rng.choice([110, 160, 220, 290, 350, 430, 560, 780]) * rng.uniform(.9, 1.1)
            if a >= 18 and rng.random() < (.085 if a < 45 else .04) * (1.3 if H.alice == "alice" else 1):
                p.bnpl = True
            if p.emp.startswith("employed") and H.alice != "above" and rng.random() < .028:
                p.garnish = True
            if p.emp.startswith("employed") and p.org is not None:
                p.k401 = (rng.choice([.03, .04, .05, .06, .08, .10]) if rng.random() < (.25 if p.wage < 35000 else .52 if p.wage < 70000 else .74) and p.ft else 0.0)
            # commute mode
            if p.emp.startswith("employed") or p.emp == "self_employed":
                d = H.district
                drivers = len([q for q in H.members if q.age >= 16])
                has_car = H.vehicles >= drivers or (H.vehicles > 0 and rng.random() < H.vehicles / max(1, drivers) + .15)
                r = rng.random()
                if p.sector in ("prof", "fin", "info", "mgmt") and r < .16 or (p.occ in ("freelance designer", "independent consultant", "home child care provider") and r < .8):
                    p.mode = "work_from_home"
                elif has_car:
                    p.mode = "car" if r < .93 else ("carpool" if r < .97 else ("transit" if TRANSIT_SERVED[d] > .5 else "car"))
                else:
                    t = TRANSIT_SERVED[d]
                    p.mode = "transit" if rng.random() < t * .75 else rng.choices(["carpool", "walk", "bike", "rideshare"], [.5, .3, .1, .1])[0]
                    if p.wd == d and d in ("D1", "D4", "D5") and rng.random() < .3:
                        p.mode = "walk"
            b = []
            if p.ss_type:
                b.append("%s(pay:%s)" % (p.ss_type, p.ss_cohort))
            if p.ssi > 0:
                b.append("ssi(pay:1st)")
            if p.pension:
                b.append("pension")
            if p.ui:
                b.append("unemployment_insurance")
            if p.va:
                b.append("va_disability_compensation(pay:1st)")
            if H.snap:
                b.append("snap(issue_day:%d)" % H.snap_day)
            if H.wic and (p.age < 5 or (p.sex == "F" and p.rel in ("head", "spouse", "unmarried_partner") and any(k.age < 1 for k in H.members))):
                b.append("wic")
            if H.tanf and p.rel == "head":
                b.append("tanf(pay_day:%d)" % H.tanf_day)
            if H.cs and p.rel == "head":
                b.append("child_support_received")
            if p.meal in ("free", "reduced"):
                b.append(p.meal + "_school_meals")
            if p.student == "head_start":
                b.append("head_start")
            if H.subsidized and p.rel == "head":
                b.append("housing_assistance")
            if H.ccdf and p.student in ("child_care_center", "family_child_care"):
                b.append("child_care_subsidy")
            if H.liheap and p.rel == "head":
                b.append("energy_assistance")
            if p.vet:
                b.append("veteran")
            p.benefits = b

    # ---------- 12. caregiving links
    pool = [p for p in PP if 32 <= p.age <= 70 and p.dis == "none" and not p.hh.gq]
    by_d = {}
    for p in pool:
        by_d.setdefault(p.hh.district, []).append(p)
    for H in HH:
        if H.gq in ("jail", "college_dorm"):
            continue
        for p in H.members:
            need = (p.dis in ("self_care", "independent_living", "multiple", "cognitive", "ambulatory") and (p.age >= 60 or p.dis in ("self_care", "multiple", "cognitive"))) or p.age >= 84
            if p.age < 18:
                need = p.dis != "none"
            if not need:
                continue
            inside = [q for q in H.members if q is not p and q.age >= 18 and q.dis in ("none", "hearing", "vision")]
            if inside and rng.random() < .85:
                q = inside[0] if p.age < 18 else rng.choice(inside)
                q.care_for.append(p)
                p.cared_by.append(q)
            if (not inside or rng.random() < .25) and rng.random() < (.62 if not H.gq else .40):
                dd = H.district if rng.random() < .6 else rng.choice(DISTRICTS)
                cand = by_d.get(dd) or pool
                q = rng.choice(cand)
                if q.hh is not H and len(q.care_for) < 2:
                    q.care_for.append(p)
                    p.cared_by.append(q)
    # households notes
    for H in HH:
        if H.recent:
            H.notes.append("recent_immigrant_household")
        elif H.immigrant:
            H.notes.append("immigrant_household")
        if H.lep:
            H.notes.append("limited_english")
        if any(p.vet for p in H.members):
            H.notes.append("veteran_in_household")
        if H.mobile_home:
            H.notes.append("mobile_home")
        if H.ev:
            H.notes.append("has_ev")
        if any(p.care_for for p in H.members):
            H.notes.append("unpaid_caregiver_in_household")
        if any(p.gig for p in H.members):
            H.notes.append("gig_worker")
        if any(p.seasonal and p.sector == "ag" for p in H.members):
            H.notes.append("seasonal_farmworker")
        if any(p.emp == "self_employed" and not p.gig for p in H.members):
            H.notes.append("small_business_owner")
        if any(p.wd == "EXT" for p in H.members):
            H.notes.append("out_commuter")
        if H.gq and H.facility:
            H.notes.append("facility:" + H.facility)
    adjust_banking(sim, HH)
    assign_sick_leave(sim, PP)
    reshape_owner_costs(sim, HH)
    add_h2a_workers(sim, HH, PP)
    sim.households, sim.persons = HH, PP
    sim.n_pov_raw = npov
    return HH, PP


# Unbanked share of households by income: FDIC National Survey of Unbanked and Underbanked Households 2023
# (sources/raw/fdic_unbanked/hh2023_analys.csv; hunbnk weighted by hhsupwgt; 4.2% overall). Income bands are in 2023
# dollars (Medianville's 2027 incomes / 1.13). v1's rule, keyed on ALICE status, gave 3.6% and ran low at the bottom
# (16.9% under $15,000) and a little high at the top. The 2023 file carries no underbanked measure, so that share is kept.
FDIC_UNBANKED = ((15000, .218), (30000, .090), (50000, .045), (75000, .018), (float("inf"), .007))
DOLLARS_2027_PER_2023 = 1.13


def adjust_banking(sim, HH):
    """Move households between banked and unbanked, within each income band, until the band matches FDIC 2023.
    Uses its own random stream so the people and everything drawn before stay as in v1."""
    srng = C.side_rng(sim.cfg["RANDOM_SEED"], "banking")
    bands = {}
    for H in HH:
        if H.gq:
            continue
        inc = H.income / DOLLARS_2027_PER_2023
        k = next(i for i, (hi, _) in enumerate(FDIC_UNBANKED) if inc < hi)
        bands.setdefault(k, []).append(H)
    for k, hs in sorted(bands.items()):
        want = int(round(FDIC_UNBANKED[k][1] * len(hs)))
        unb = [H for H in hs if H.banked == "unbanked"]
        if len(unb) < want:
            pool = [H for H in hs if H.banked == "underbanked"]
            srng.shuffle(pool)
            rest = [H for H in hs if H.banked == "banked"]
            srng.shuffle(rest)
            for H in (pool + rest)[:want - len(unb)]:
                H.banked = "unbanked"
                for p in H.members:
                    p.cashpref = .95
        elif len(unb) > want:
            srng.shuffle(unb)
            for H in unb[:len(unb) - want]:
                H.banked = "underbanked"   # newly banked households mostly still use check cashers and money orders
                for p in H.members:
                    p.cashpref = min(.92, max(.02, .45 + srng.gauss(0, .12)))


# Access to paid sick leave by wage, NCS March 2026 (sources/raw/ncs_benefits, all-data sheet, provision 087, civilian
# workers): lowest 10% of wages 48%, lowest 25% 63%, second 25% 85%, third 25% 91%, highest 25% 95%, highest 10% 97%;
# full-time 90%, part-time 59%. Bands between published cuts are solved from them (10-25%: 73%; 75-90%: 94%). v1 gave
# none to anyone on a variable schedule or earning under $42,000.
PSL_BY_WAGE_RANK = ((.10, .48), (.25, .73), (.50, .85), (.75, .91), (.90, .94), (1.01, .97))


def assign_sick_leave(sim, PP):
    """Paid sick leave by the worker's wage rank among Medianville's employees; part-time a little lower, self-employed none.
    Own random stream, so nothing else moves."""
    srng = C.side_rng(sim.cfg["RANDOM_SEED"], "sick_leave")
    emp = sorted((p for p in PP if p.emp in ("employed_full_time", "employed_part_time")), key=lambda p: (p.wage, p.pid))
    n = len(emp)
    for i, p in enumerate(emp):
        rank = (i + .5) / n
        pr = next(v for hi, v in PSL_BY_WAGE_RANK if rank < hi)
        if not p.ft:
            pr *= .85
        p.psl = srng.random() < pr


# Owner housing costs (mortgage payment, or taxes, insurance and fees; utilities are separate bills), drawn from what
# owners at the same income pay in AHS 2023 (sources/derived/ahs_owner_costs.csv, sources/tools/ahs_owner_costs.py:
# TOTHCAMT less UTILAMT, weighted quantiles by HINCP band). Income bands are in 2023 dollars (Medianville's 2027 incomes
# / 1.13) and costs are carried to 2027 by the same factor, then scaled by district (OWNER_PITI, relative to the city's
# owner-weighted mean). v1 tied owners' costs to income too tightly (mortgages at least 14-29% of it); batch I's first
# redraw matched AHS's cost burdens but drew cost apart from income, which put 9% of owners without a mortgage at its
# $2,500 cap and had a 95-year-old on $16,648 paying $2,476 a month (v2 close reading, item 1).
# AHS has about 4.5% of owners paying more than their whole income, mostly owners living on savings that HINCP leaves
# out; Medianville counts withdrawals as income, so costs are held to 60% of income without a mortgage and 80% with one
# (an estimate). Applied after the population is built, on its own stream, so v1's people and draws stay as they were.
OWNER_PITI = {"D1": 1700, "D2": 1500, "D3": 2180, "D4": 1380, "D5": 1020, "D6": 1080}
AHS_DOLLARS = 1.13
AHS_QS = (.01, .05, .10, .20, .30, .40, .50, .60, .70, .80, .90, .95, .99)
AHS_OWNER_COST = {   # (income band from, to) -> monthly cost at AHS_QS, 2023 dollars
    "free": [((0, 25000), (2, 33, 64, 122, 182, 241, 311, 390, 499, 631, 914, 1307, 3196)),
             ((25000, 50000), (21, 68, 116, 174, 234, 290, 360, 441, 551, 695, 996, 1352, 3148)),
             ((50000, 100000), (38, 106, 160, 228, 289, 352, 422, 504, 617, 768, 1070, 1425, 3091)),
             ((100000, 200000), (76, 192, 242, 323, 387, 475, 551, 654, 781, 980, 1286, 1758, 4445)),
             ((200000, None), (66, 270, 366, 481, 599, 699, 805, 950, 1157, 1494, 2048, 2745, 7349))],
    "mortgage": [((0, 25000), (114, 330, 446, 587, 740, 892, 1109, 1357, 1576, 2024, 2866, 4262, 10397)),
                 ((25000, 50000), (286, 444, 551, 710, 833, 956, 1087, 1243, 1453, 1766, 2419, 3295, 8222)),
                 ((50000, 100000), (381, 595, 720, 905, 1056, 1199, 1378, 1588, 1825, 2191, 2870, 3698, 9872)),
                 ((100000, 200000), (511, 750, 922, 1187, 1381, 1571, 1781, 2028, 2336, 2728, 3411, 4263, 9029)),
                 ((200000, None), (675, 1112, 1385, 1798, 2125, 2406, 2754, 3161, 3635, 4316, 5630, 7294, 14590))],
}
OWNER_COST_CAP = {"free": (.60, 100), "mortgage": (.80, 400)}   # share of monthly income, and a floor for very low incomes


def ahs_owner_quantile(kind, income_2023, u):
    """Monthly cost at quantile u for an owner household with this 2023-dollar income: piecewise linear between the AHS
    quantiles, running on to half the 1st percentile at u=0 and 1.25 times the 99th at u=1, so no value is a pile-up."""
    qs = next(q for (lo, hi), q in AHS_OWNER_COST[kind] if income_2023 >= lo and (hi is None or income_2023 < hi))
    xs = (0.0,) + AHS_QS + (1.0,)
    ys = (qs[0] * .5,) + qs + (qs[-1] * 1.25,)
    for i in range(1, len(xs)):
        if u <= xs[i]:
            t = (u - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def reshape_owner_costs(sim, HH):
    srng = C.side_rng(sim.cfg["RANDOM_SEED"], "owner_cost")
    owners = [H for H in HH if not H.gq and H.tenure in ("owner_with_mortgage", "owner_free_and_clear") and not H.mobile_home]
    mean_piti = sum(OWNER_PITI[H.district] for H in owners) / max(1, len(owners))
    for H in owners:
        kind = "mortgage" if H.tenure == "owner_with_mortgage" else "free"
        u = srng.random()
        cost = ahs_owner_quantile(kind, H.income / AHS_DOLLARS, u) * AHS_DOLLARS * OWNER_PITI[H.district] / mean_piti
        share, floor = OWNER_COST_CAP[kind]
        cap = max(floor, share * H.income / 12.0)
        if cost > cap:   # held under the cap, spread over its top quarter by the same draw, so no amount piles up
            cost = cap * (.75 + .25 * ((u * 7919.0) % 1.0))
        H.housing_cost = round(max(1.0, cost), 0)


# H-2A guest workers on the job, per 1,000 US residents, by month: DOL's FY2025 disclosure file
# (sources/derived/h2a_on_the_job.csv, sources/tools/h2a_season.py), certified positions counted from employment start
# to end. National rates, as Medianville's people are national; Georgia peaks earlier (peaches) and higher.
H2A_PER_1000 = {1: .267, 2: .335, 3: .488, 4: .612, 5: .672, 6: .677, 7: .649, 8: .657, 9: .712, 10: .714, 11: .564, 12: .334}
H2A_WAGE_2027 = 16.23 * 1.03 ** 2   # FY2025 median certified wage offer, carried to 2027 at 3% a year; not boosted by
                                     # WAGE_SCALE, which makes up for resident household size (see config.py)


def add_h2a_workers(sim, HH, PP):
    """H-2A workers in employer housing on the open-country farms, each a one-person group-quarters unit (the Census
    counts workers' dormitories as group quarters). The roster is drawn whole from its own stream and only the workers on
    the job that month are added, at the end, so nobody else in Medianville changes."""
    farms = sorted((o for o in sim.by_kind.get("farm", []) if o.district in ("D6", "D5")), key=lambda o: (-o.size, o.oid))
    if not farms:
        return
    srng = C.side_rng(sim.cfg["RANDOM_SEED"], "h2a")
    n = int(round(H2A_PER_1000[sim.cal["month"]] * len(PP) / 1000.0))
    year = sim.cal["date"].year
    hosts = farms[:max(1, min(3, len(farms)))]
    roster = []
    for k in range(int(round(max(H2A_PER_1000.values()) * len(PP) / 1000.0))):
        roster.append((hosts[k % len(hosts)], int(min(55, max(21, srng.gauss(32, 7)))), "M" if srng.random() < .95 else "F",
                       srng.random() < .4, srng.randint(0, 1), math.exp(srng.gauss(0, .05))))
    for org, age, sex, unbanked, edu, wf in roster[:n]:
        H = Household("H%05d" % (len(HH) + 1), org.district, "group_quarters:h2a_worker_housing")
        H.gq, H.facility = "h2a_worker_housing", "%s worker housing" % org.name
        H.tenure, H.housing_cost, H.vehicles, H.internet = "group_quarters", 0.0, 0, "mobile_only"
        H.lang, H.lep, H.immigrant, H.recent, H.race, H.z = "Spanish", True, True, True, "hispanic", -.6
        H.banked = "unbanked" if unbanked else "underbanked"
        H.notes += ["h2a_guest_worker", "employer_provided_housing", "facility:" + H.facility]
        p = Person("P%06d" % (len(PP) + 1), H, age, sex, "resident")
        p.bday, p.by = 1 + (age * 7) % 28, year - age
        p.race, p.edu, p.dis, p.cov = "hispanic", edu, "none", "uninsured"
        p.emp, p.occ, p.org, p.sector, p.wd = "employed_full_time", "crop farmworker", org, "ag", org.district
        p.sched, p.wsched, p.cadence, p.payday, p.ft, p.seasonal = "farm", "variable", "weekly", (4,), True, True
        p.wage = round(H2A_WAGE_2027 * 2080 * wf, 2)
        p.income, p.cashpref, p.mode = p.wage, .6, "walk"   # housing is on the farm; employers must provide transport, free
        org.emp += 1
        H.members.append(p)
        H.head, H.adults, H.kids = p, [p], []
        H.income = p.income
        H.alice = "alice"
        H.pov_ratio = H.income / C.POVERTY_BASE
        HH.append(H)
        PP.append(p)


OCC_KINDS = {
    "public school teacher": ("school_district",), "teaching assistant": ("school_district", "private_school"),
    "school bus driver": ("school_district",), "school custodian": ("school_district",), "school cafeteria worker": ("school_district",),
    "school counselor": ("school_district",), "school principal": ("school_district",),
    "police officer": ("city", "county"), "firefighter": ("city",), "municipal clerk": ("city", "county", "courthouse"),
    "public works maintenance worker": ("city", "county", "water"), "public civil engineer": ("city", "county", "tollway"),
    "city administrator": ("city", "county"), "parks and recreation worker": ("parks",), "corrections officer": ("jail",),
    "benefits caseworker": ("benefits_office", "housing_authority", "senior_center"), "state office clerk": ("dmv", "benefits_office", "workforce", "probation", "tollway"),
    "library assistant": ("library",), "transit bus operator": ("transit", "paratransit", "rural_transit"),
    "community college instructor": ("community_college",), "court clerk": ("courthouse",), "water treatment operator": ("water",),
    "911 dispatcher": ("county", "ems"), "public health nurse": ("health_dept",), "paramedic": ("ems",),
    "registered nurse": ("hospital", "hospital", "nursing_home", "home_health", "fqhc", "physician", "dialysis", "hospice"),
    "nursing assistant": ("hospital", "nursing_home", "nursing_home", "assisted_living"), "licensed practical nurse": ("nursing_home", "hospital", "physician", "home_health"),
    "hospital housekeeper": ("hospital", "nursing_home"), "lab technician": ("hospital",), "physician": ("hospital", "physician", "fqhc", "urgent_care"),
    "nurse practitioner": ("physician", "fqhc", "urgent_care", "hospital"), "home health aide": ("home_health",),
    "dental hygienist": ("dental",), "dental assistant": ("dental",), "child care worker": ("child_care", "head_start", "after_school"),
    "social worker": ("hospital", "fqhc", "community_action", "shelter", "hospice", "behavioral"), "physical therapist": ("pt_clinic", "hospital"),
    "medical assistant": ("physician", "fqhc", "urgent_care"), "medical billing clerk": ("hospital", "physician", "dental"),
    "medical receptionist": ("physician", "dental", "vision", "fqhc", "behavioral"), "health services manager": ("hospital", "nursing_home", "fqhc", "home_health"),
    "pharmacist": ("pharmacy",), "pharmacy technician": ("pharmacy",), "car salesperson": ("car_dealer", "bhph_dealer"),
    "grocery deli worker": ("grocery_full", "supercenter", "warehouse_club"), "overnight stocker": ("supercenter", "grocery_full", "warehouse_club", "home_center"),
    "hotel desk clerk": ("hotel",), "hotel housekeeper": ("hotel",), "bartender": ("bar", "restaurant", "fine_dining"),
    "server": ("restaurant", "restaurant", "fine_dining"), "host": ("restaurant", "fine_dining"), "fast food worker": ("fastfood", "fastfood", "coffee"),
    "mail carrier": ("post_office",), "postal clerk": ("post_office",), "VA nurse": ("va_clinic",), "VA clinic clerk": ("va_clinic",),
    "Social Security claims specialist": ("ssa",), "airport security officer": ("federal_office",), "active-duty service member": ("armory",),
    "bank teller": ("bank", "credit_union"), "personal banker": ("bank", "credit_union"), "branch manager": ("bank", "credit_union"),
    "loan officer": ("bank", "credit_union", "bank_hq"), "insurance agent": ("insurance_agency",), "claims adjuster": ("insurer_office",),
    "underwriter": ("insurer_office", "bank_hq"), "insurance call center rep": ("insurer_office",), "financial advisor": ("advisor",),
    "auto mechanic": ("auto_repair", "tire", "oil_change"), "hairdresser": ("salon",), "nail technician": ("nail",), "clergy": ("church",),
    "church administrator": ("church",), "laundry worker": ("laundromat", "dry_cleaner"), "funeral attendant": ("funeral",),
    "pet groomer": ("pet_groom",), "appliance repair technician": ("repair_shop",), "car wash attendant": ("car_wash",),
    "nonprofit program coordinator": ("nonprofit",), "membership organization staff": ("nonprofit",),
    "private school teacher": ("private_school",), "college professor": ("college_private",), "college staff member": ("college_private",),
    "campus food service worker": ("college_private",), "tutor": ("tutoring",), "trade school instructor": ("trade_school",),
    "fitness and dance instructor": ("studio",), "crop farmworker": ("farm",), "farm equipment operator": ("farm",),
    "dairy and livestock worker": ("farm",), "farm manager": ("farm",), "crew leader": ("farm",), "packing shed worker": ("packing",),
    "logging worker": ("farm",), "quarry equipment operator": ("quarry",), "electrical lineworker": ("electric", "electric_coop"),
    "plant operator": ("electric", "gas_util"), "utility field technician": ("electric", "electric_coop", "gas_util"),
    "utility customer service rep": ("electric", "electric_coop", "gas_util"), "utility engineer": ("electric", "gas_util"),
    "telecom installer": ("isp",), "cable customer service rep": ("isp",), "telecom sales rep": ("isp",), "web developer": ("software",),
    "reporter": ("newspaper", "broadcast"), "editor": ("newspaper",), "broadcast technician": ("broadcast",), "data center technician": ("data_center",),
    "cinema worker": ("cinema",), "fitness trainer": ("gym", "after_school"), "recreation attendant": ("trampoline", "bowling", "golf", "country_club"),
    "coach": ("youth_sports", "after_school", "gym"), "musician": ("theater",), "museum educator": ("museum",),
    "golf course groundskeeper": ("country_club", "golf"), "bowling and gaming attendant": ("bowling",), "lifeguard": ("after_school",),
    "venue manager": ("theater", "museum", "country_club"), "attorney": ("law", "legal_aid"), "paralegal": ("law", "legal_aid"),
    "accountant": ("accounting", "tax_prep"), "veterinary technician": ("vet",), "veterinarian": ("vet",),
    "truck driver": ("trucking", "warehouse"), "parcel delivery driver": ("warehouse",), "airport ground crew": ("warehouse", "airport"),
}
