"""v2's hand-written records (phase 5): 300 of the baseline day's records, keyed by id, job and actor."""
import csv
import json
import os
import re

import pytest

from conftest import SIM_DIR

OVERRIDES = os.path.join(SIM_DIR, "detailed_overrides.csv")
SAMPLE = os.path.join(SIM_DIR, "detailed_sample.csv")
SELECTION = os.path.join(SIM_DIR, "detail_parts", "selection.json")


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_every_selected_record_is_written_once():
    ov = rows(OVERRIDES)
    with open(SELECTION) as f:
        sel = json.load(f)
    assert len(ov) == len(sel) == 300
    assert len({r["record_id"] for r in ov}) == 300
    sig = {r[0]: (r[1], r[2]) for r in sel}
    for r in ov:
        assert sig[r["record_id"]] == (r["job_category"], r["actor_person_id"]), r["record_id"]


def test_text_has_the_house_form():
    for r in rows(OVERRIDES):
        assert re.fullmatch(r"When [^|]+, I want to [^|]+, so I can [^|]+\.", r["job_statement"]), r["record_id"]
        assert r["narrative"].startswith("[detailed] ") and r["narrative"].endswith((".", "!", "?")), r["record_id"]


def test_sample_holds_the_finished_rows():
    ov = {r["record_id"]: r for r in rows(OVERRIDES)}
    sample = rows(SAMPLE)
    assert len(sample) == 300
    for r in sample:
        assert r["narrative"] == ov[r["record_id"]]["narrative"] and r["job_statement"] == ov[r["record_id"]]["job_statement"]


@pytest.mark.slow
def test_the_baseline_day_applies_all_300(tmp_path):
    import simulate
    from medianville_sim.config import PARAMS
    sim, _ = simulate.run_day(dict(PARAMS), str(tmp_path), overrides=OVERRIDES, blocks_path=None, log=lambda *a: None)
    hand = [r for r in rows(os.path.join(tmp_path, "records.csv")) if r["narrative"].startswith("[detailed]")]
    assert len(hand) == 300
