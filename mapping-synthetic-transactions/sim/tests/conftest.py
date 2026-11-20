"""Shared fixtures: one 10% city (4,140 households) simulated once per test session.

Run from sim/:  python3 -m pytest tests            (fast checks, about 10 seconds)
                python3 -m pytest tests --run-slow (adds the full-city v1 reproduction, about 30 seconds more)
"""
import csv
import os
import sys

import pytest

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(SIM_DIR)
if SIM_DIR not in sys.path:
    sys.path.insert(0, SIM_DIR)

TEST_HOUSEHOLDS = 4140
BLOCKS = os.path.join(REPO_DIR, "systems-lens", "blocks.json")


def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", default=False, help="also run the full-city v1 reproduction test")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: full-city runs; skipped unless --run-slow is given")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip = pytest.mark.skip(reason="needs --run-slow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="session")
def run10(tmp_path_factory):
    """Simulate the baseline date for a 10% city. Returns (sim, output folder)."""
    import simulate
    from medianville_sim.config import PARAMS

    out = str(tmp_path_factory.mktemp("medianville10"))
    cfg = dict(PARAMS)
    cfg["N_HOUSEHOLDS"] = TEST_HOUSEHOLDS
    sim, _ = simulate.run_day(cfg, out, overrides=None, blocks_path=BLOCKS, log=lambda *a: None)
    return sim, out


# The carried run used by the phase 4 tests: a 10% city carried from March 1 (a Monday) through March 12, long enough
# for a ten-day shutoff notice to run out, a two-week payday loan to come due and two pay weeks to pass.
CARRIED_FIRST, CARRIED_DAYS = "2027-03-01", 12


@pytest.fixture(scope="session")
def carried10(tmp_path_factory):
    """Simulate a carried 10% city. Returns {"days": [(date, folder)], "states": [state dicts], "out": root}."""
    import datetime as dt
    import json
    import simulate
    from medianville_sim.config import PARAMS

    root = str(tmp_path_factory.mktemp("medianville10_carried"))
    cfg = dict(PARAMS)
    cfg["N_HOUSEHOLDS"] = TEST_HOUSEHOLDS
    first = dt.date.fromisoformat(CARRIED_FIRST)
    days, states, state = [], [], None
    for i in range(CARRIED_DAYS):
        cfg["SIM_DATE"] = first + dt.timedelta(days=i)
        out = os.path.join(root, cfg["SIM_DATE"].isoformat())
        st_out = os.path.join(root, "state_%s.json" % cfg["SIM_DATE"].isoformat())
        simulate.run_day(cfg, out, state_in=state, state_out=st_out, overrides=None, blocks_path=None, log=lambda *a: None, carried=True)
        with open(st_out) as f:
            states.append(json.load(f))
        days.append((cfg["SIM_DATE"].isoformat(), out))
        state = st_out
    return {"days": days, "states": states, "out": root}


@pytest.fixture(scope="session")
def records(run10):
    return read_csv(os.path.join(run10[1], "records.csv"))


@pytest.fixture(scope="session")
def ledger(run10):
    return read_csv(os.path.join(run10[1], "household_ledger.csv"))
