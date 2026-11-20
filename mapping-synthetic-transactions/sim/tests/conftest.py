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
    from halvern_sim.config import PARAMS

    out = str(tmp_path_factory.mktemp("halvern10"))
    cfg = dict(PARAMS)
    cfg["N_HOUSEHOLDS"] = TEST_HOUSEHOLDS
    sim, _ = simulate.run_day(cfg, out, overrides=None, blocks_path=BLOCKS, log=lambda *a: None)
    return sim, out


@pytest.fixture(scope="session")
def records(run10):
    return read_csv(os.path.join(run10[1], "records.csv"))


@pytest.fixture(scope="session")
def ledger(run10):
    return read_csv(os.path.join(run10[1], "household_ledger.csv"))
