"""Phase 5 fix 1: owners' housing costs are drawn from what owners at the same income pay in AHS 2023."""
import collections
import csv
import os

from conftest import REPO_DIR

from medianville_sim import population as P

DERIVED = os.path.join(REPO_DIR, "sources", "derived", "ahs_owner_costs.csv")


def owners(sim, tenure):
    return [H for H in sim.households if not H.gq and H.tenure == tenure and not H.mobile_home]


def test_table_matches_the_derived_file():
    with open(DERIVED, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    kind = {"free_and_clear": "free", "with_mortgage": "mortgage"}
    got = {(kind[r["mortgage_status"]], int(r["income_from"])): tuple(int(r["p%02d" % round(q * 100)]) for q in P.AHS_QS) for r in rows}
    want = {(k, lo): qs for k, bands in P.AHS_OWNER_COST.items() for (lo, _), qs in bands}
    assert got == want


def test_no_amount_piles_up(run10):
    sim, _ = run10
    for tenure in ("owner_free_and_clear", "owner_with_mortgage"):
        o = owners(sim, tenure)
        top, n = collections.Counter(H.housing_cost for H in o).most_common(1)[0]
        assert n <= max(5, .01 * len(o)), (tenure, top, n)


def test_costs_held_under_the_income_cap(run10):
    sim, _ = run10
    for tenure, kind in (("owner_free_and_clear", "free"), ("owner_with_mortgage", "mortgage")):
        share, floor = P.OWNER_COST_CAP[kind]
        for H in owners(sim, tenure):
            assert H.housing_cost <= max(floor, share * H.income / 12.0) + 1, (H.hid, H.income, H.housing_cost)


def test_medians_follow_ahs_by_income(run10):
    sim, _ = run10
    for tenure, kind in (("owner_free_and_clear", "free"), ("owner_with_mortgage", "mortgage")):
        o = owners(sim, tenure)
        for (lo, hi), qs in P.AHS_OWNER_COST[kind]:
            band = sorted(H.housing_cost for H in o if H.income / P.AHS_DOLLARS >= lo and (hi is None or H.income / P.AHS_DOLLARS < hi))
            if len(band) < 100:
                continue
            want = qs[P.AHS_QS.index(.5)] * P.AHS_DOLLARS
            got = band[len(band) // 2]
            assert .7 * want <= got <= 1.35 * want, (kind, lo, got, want)


def test_free_and_clear_costs_rise_with_income(run10):
    sim, _ = run10
    o = owners(sim, "owner_free_and_clear")
    low = sorted(H.housing_cost for H in o if H.income < 30000)
    high = sorted(H.housing_cost for H in o if H.income > 150000)
    assert low[len(low) // 2] < high[len(high) // 2]
