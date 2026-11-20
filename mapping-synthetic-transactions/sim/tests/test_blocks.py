"""The systems lens's mapped blocks: systems-lens/blocks.json, and the three columns the simulator tags from it."""
import json
import os
import re
import subprocess
import sys

from conftest import BLOCKS, SIM_DIR, TEST_HOUSEHOLDS, read_csv

BLOCK_COLS = ["block_id", "block_pattern", "context_ids"]


def doc():
    with open(BLOCKS, encoding="utf-8") as f:
        return json.load(f)


def test_blocks_file_is_consistent():
    d = doc()
    assert len({b["district"] for b in d["blocks"]}) == len(d["blocks"]), "one block per district"
    for b in d["blocks"]:
        ids = {c["id"] for c in b["contexts"]}
        pids = {p["id"] for p in b["patterns"]}
        assert len(ids) == len(b["contexts"]) and len(pids) == len(b["patterns"]), b["id"]
        for c in b["contexts"]:
            assert set(c["under"]) <= ids, (b["id"], c["id"])
            assert c["layer"] in ("hist", "pol", "econ", "env", "soc"), (b["id"], c["id"])
        for p in b["patterns"]:
            assert set(p["links"]) <= ids, (b["id"], p["id"])
            for m in p["match"]:
                assert set(m) <= {"cat", "type", "fee", "outcome"}, (b["id"], p["id"])
                for v in m.values():
                    re.compile(v)
        for k, L in b["loops"].items():
            assert set(L["seen"]) <= pids, (b["id"], k)
            nodes = {n["k"] for n in L["nodes"]}
            assert all(a in nodes and z in nodes for a, z, *_ in L["links"]), (b["id"], k)
            assert all(dr["from"] in ids and dr["to"] in nodes for dr in L.get("drivers", [])), (b["id"], k)
        assert b["start"]["pattern"] in pids and b["start"]["loop"] in b["loops"], b["id"]


def test_records_carry_block_columns(run10, records):
    assert list(records[0].keys())[-3:] == BLOCK_COLS


def test_tags_agree_with_households_and_blocks(run10, records):
    d = doc()
    blocks = {b["id"]: b for b in d["blocks"]}
    hh = {h["household_id"]: h for h in read_csv(os.path.join(run10[1], "households.csv"))}
    tagged = 0
    for r in records:
        bid = r["block_id"]
        if not bid:
            assert not r["block_pattern"] and not r["context_ids"], r["record_id"]
            continue
        tagged += 1
        h = hh[r["household_id"]]
        assert h["block_id"] == bid and h["district"] == blocks[bid]["district"], r["record_id"]
        if r["block_pattern"]:
            p = next(p for p in blocks[bid]["patterns"] if p["id"] == r["block_pattern"])
            assert r["context_ids"] == ";".join(p["links"]), r["record_id"]
    assert tagged, "no records were tagged"


def test_tagging_leaves_the_day_unchanged(run10, tmp_path):
    """--no-blocks writes the same records, minus the three columns: tagging draws no random numbers."""
    _, out = run10
    subprocess.run([sys.executable, os.path.join(SIM_DIR, "simulate.py"), "--households", str(TEST_HOUSEHOLDS), "--out", str(tmp_path),
                    "--overrides", "", "--no-blocks"], check=True, cwd=SIM_DIR, capture_output=True)
    with_tags = read_csv(os.path.join(out, "records.csv"))
    without = read_csv(os.path.join(tmp_path, "records.csv"))
    assert len(with_tags) == len(without)
    for a, b in zip(with_tags, without):
        assert {k: v for k, v in a.items() if k not in BLOCK_COLS} == b
