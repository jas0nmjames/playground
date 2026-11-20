"""Tests for the evidence checks: the typed-day weights and the per-day measurement."""
import csv
import datetime as dt
import os
import sys

from conftest import SIM_DIR

sys.path.insert(0, os.path.join(SIM_DIR, "evidence"))
import checks  # noqa: E402
import typed_days  # noqa: E402


def test_weights_cover_the_year():
    rows = typed_days.day_set()
    assert abs(sum(r["weight"] for r in rows) - 365) < 1e-9
    assert all(r["weight"] > 0 for r in rows)


def test_every_day_of_2027_has_one_class():
    hol = typed_days.holidays()
    assert len(hol) == 12
    d = dt.date(2027, 1, 1)
    while d.year == 2027:
        assert typed_days.classify(d, hol) in typed_days.CLASSES
        d += dt.timedelta(days=1)


def test_representatives_sit_in_their_class():
    hol = typed_days.holidays()
    for k, (days, weather, _) in typed_days.CLASSES.items():
        if weather == "ordinary":
            for day in days:
                assert typed_days.classify(day, hol) == k, (day, k)


def test_every_target_metric_is_measured(run10):
    sim, out = run10
    from halvern_sim import output
    m = checks.measure_dir(out, output.summarize(sim))
    day = [dict(date="x", cls="x", weather="ordinary", weight=1.0, m=m)]
    with open(checks.TARGETS, newline="") as f:
        targets = list(csv.DictReader(f))
    assert len(targets) == 16
    for t in targets:
        v = checks.year_value(t["metric"], day)
        assert v is not None, t["metric"]
        assert checks.verdict(t, v) != "?", t["target_id"]


def test_measurement_matches_the_records(run10, records):
    _, out = run10
    m = checks.measure_dir(out)
    assert m["records"] == len(records)
    assert m["overdraft_fees"] == sum(1 for r in records if "overdraft_fee" in r["fee_type"])
    assert m["utility_disconnections"] == sum(1 for r in records if r["job_category"] == "utilities.service_disconnected_for_nonpayment")
