"""Tests for carried runs (phase 4): the one-day path is untouched, and carried state survives the trip between days."""
import csv
import hashlib
import os

from conftest import read_csv
from medianville_sim.carry import LINK_COLS, Carry

# The 10% one-day run (conftest.run10) as the simulator wrote it before phase 4 (development at 7013a0f). Carried runs
# must not change a single byte of it; the typed-day year (sim/evidence/results/v2_rates_typed_days_2027) is checked
# the same way at full scale.
ONE_DAY_SHA256 = {
    "records.csv": "a238cf07e6a72bae6dfb4036c09305e0ca0fe888029aab769710eab4382d3db2",
    "household_ledger.csv": "5292312ecace971833c9094defbf92eb4fa7a35cf3f16cead2712bac77289179",
    "summary.md": "31182e59abce0382170a471927585b0e80665d7522563b9f2d9dffd040a6a9cf",
}


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_one_day_path_unchanged(run10):
    sim, out = run10
    assert sim.carry is None
    assert not os.path.exists(os.path.join(out, "links.csv"))
    for name, want in ONE_DAY_SHA256.items():
        assert sha(os.path.join(out, name)) == want, name


def test_carried_days_write_links_and_state(carried10):
    for (date, out), st in zip(carried10["days"], carried10["states"]):
        with open(os.path.join(out, "links.csv"), newline="", encoding="utf-8") as f:
            assert next(csv.reader(f)) == LINK_COLS
        assert st["date"] == date and st["carry"]["first"] == carried10["days"][0][0]
    assert [st["carry"]["n"] for st in carried10["states"]] == list(range(1, len(carried10["days"]) + 1))


def test_state_round_trip(carried10):
    st = carried10["states"][-1]["carry"]
    again = Carry.from_state(st).to_state()
    again["n"] -= 1          # to_state counts the day just finished
    assert again == st


def test_carried_ledgers_reconcile(carried10):
    for date, out in carried10["days"]:
        led = read_csv(os.path.join(out, "household_ledger.csv"))
        assert all(r["reconciles"] == "yes" for r in led), date


def test_balances_carry_from_one_day_to_the_next(carried10):
    (d1, o1), (d2, o2) = carried10["days"][:2]
    close = {r["household_id"]: r for r in read_csv(os.path.join(o1, "household_ledger.csv"))}
    for r in read_csv(os.path.join(o2, "household_ledger.csv")):
        c = close[r["household_id"]]
        for k in ("checking", "cash", "prepaid", "savings", "card_debt"):
            assert r["open_" + k] == c["close_" + k], (r["household_id"], k)


def test_carried_runs_are_deterministic(carried10, tmp_path):
    """Two carried days rerun from scratch match the fixture's first two days byte for byte (same seed)."""
    import datetime as dt
    import simulate
    from conftest import TEST_HOUSEHOLDS
    from medianville_sim.config import PARAMS

    cfg = dict(PARAMS)
    cfg["N_HOUSEHOLDS"] = TEST_HOUSEHOLDS
    state = None
    for k, (date, folder) in enumerate(carried10["days"][:2]):
        cfg["SIM_DATE"] = dt.date.fromisoformat(date)
        out = str(tmp_path / date)
        st = str(tmp_path / ("state_%s.json" % date))
        simulate.run_day(cfg, out, state_in=state, state_out=st, overrides=None, blocks_path=None, log=lambda *a: None, carried=True)
        for name in ("records.csv", "links.csv", "household_ledger.csv"):
            assert sha(os.path.join(out, name)) == sha(os.path.join(folder, name)), (date, name)
        state = st
