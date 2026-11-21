"""Pipeline: build the city, simulate one day, write the tables."""
import heapq
import random
import time

from .engine import Sim
from .orgs import build_orgs, index_orgs
from .population import build_population
from .finance import build_finance
from . import day_a, day_b, day_c, day_e


def build(cfg, log=print):
    t0 = time.time()
    sim = Sim(cfg)
    sim.orgs = build_orgs(sim.rng, sim.cal, sim.scale)
    sim.by_kind, sim.by_kd = index_orgs(sim.orgs)
    sim.by_name = {o.name: o for o in sim.orgs}
    sim.X = {k: v[0] for k, v in sim.by_kind.items() if k.startswith("x_")}
    build_population(sim)
    for o in sim.orgs:
        if o.district != "EXT" and not o.kind.startswith("school_e") and o.kind not in ("school_mid", "school_high"):
            o.size = max(1, int(round(o.emp * 1.045 + .3))) if o.emp else max(1, min(o.size, 2))
    log("  population: %d households, %d persons, %d orgs (%.1fs)" % (len(sim.households), len(sim.persons), len(sim.orgs), time.time() - t0))
    build_finance(sim)
    log("  finance: %d wallets, %d recurring obligations (%.1fs)" % (len(sim.wallets), sim.n_bills, time.time() - t0))
    from .orgs import add_cbp_outlets
    log("  added %d storefronts to reach County Business Patterns rates" % add_cbp_outlets(sim))
    # everything above is date-independent given the seed; the day itself gets its own stream
    sim.rng = random.Random("%s|%s|%s" % (cfg["RANDOM_SEED"], sim.cal["iso"], cfg["WEATHER"]))
    sim.trng = random.Random("text|%s|%s" % (cfg["RANDOM_SEED"], sim.cal["iso"]))
    return sim


def simulate(sim, log=print):
    t0 = time.time()
    q = []
    sim.q = q
    sim.init_day()
    for H in sim.households:
        day_a.skeleton(sim, H)
    day_c.pre_day(sim)
    day_c.overnight_lenders(sim)
    if sim.carry is not None:
        sim.carry.begin_day(sim, q)
    # fixed commitments claim time first (appointments, school runs, care), then errands fit around them
    gens = [day_a.gen_income, day_a.gen_bills, day_b.gen_health, day_b.gen_skipped_care, day_c.gen_school, day_c.gen_care, day_b.gen_food, day_b.gen_shopping, day_b.gen_transport,
            day_c.gen_public, day_c.gen_money, day_c.gen_title_loans, day_c.gen_misc]
    for H in sim.households:
        for g in gens:
            g(sim, H, q)
    day_e.city_events(sim, q)
    log("  planned %d queued actions (%.1fs)" % (len(q), time.time() - t0))
    while q:
        t, _, fn = heapq.heappop(q)
        fn()
    day_e.end_of_day(sim)
    if sim.carry is not None:
        sim.carry.end_day(sim)
    try:
        from . import day_d
        day_d.business_day(sim)
    except ImportError:
        pass
    log("  settled: %d records (%.1fs)" % (len(sim.rows), time.time() - t0))
    return sim
