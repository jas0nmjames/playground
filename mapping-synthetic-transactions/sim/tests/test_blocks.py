"""The systems lens's mapped blocks: systems-lens/blocks.json, and the three columns the simulator tags from it."""
import json
import os
import re
import subprocess
import sys
import zipfile

import pytest

from conftest import BLOCKS, REPO_DIR, SIM_DIR, TEST_HOUSEHOLDS, read_csv

BLOCK_COLS = ["block_id", "block_pattern", "context_ids"]
# The published baseline day, which ships the blocks.json it was tagged with (the same file every published run used).
PUBLISHED = os.path.join(REPO_DIR, "data", "runs", "v2", "medianville_2027-03-03.zip")


def published_blocks(path):
    """The blocks.json inside a published run's zip, as bytes, or None."""
    with zipfile.ZipFile(path) as z:
        name = next((n for n in z.namelist() if n.endswith("/blocks.json") or n == "blocks.json"), None)
        return z.read(name) if name else None


def tagger_inputs(d):
    """What the tagger reads (sim/medianville_sim/blocks.py): each block's id, district, select and patterns."""
    return [{k: b.get(k) for k in ("id", "district", "select", "patterns")} for b in d["blocks"]]


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
            assert len(c["rep"]) == 2, (b["id"], c["id"])  # where the lens anchors it on its layer
            # the district tier: circumstances true across the block's whole district
            if "scope" in c:
                assert c["scope"] == "district", (b["id"], c["id"])
            for e in c.get("evidence_ids", []):
                assert re.fullmatch(r"E\d{3}", e), (b["id"], c["id"], e)
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
            # the lens says a reinforcing loop has an even number of minus links and a balancing one an odd number
            minus = sum(1 for _, _, sign, *_ in L["links"] if sign in ("−", "-"))
            assert (minus % 2 == 0) == (L["kind"] == "R"), (b["id"], k, minus)
        assert b["start"]["pattern"] in pids and b["start"]["loop"] in b["loops"], b["id"]
        if "districtStart" in b:
            assert b["districtStart"]["loop"] in b["loops"], b["id"]


def test_every_district_has_its_deeper_layers():
    """In district mode the lens shows a historical, political, economic and built circumstance for every district."""
    for b in doc()["blocks"]:
        layers = {c["layer"] for c in b["contexts"] if c.get("scope") == "district"}
        assert {"hist", "pol", "econ", "env"} <= layers, (b["id"], sorted(layers))
        assert "districtStart" in b, b["id"]


def test_published_runs_keep_their_tags():
    """Every published run shipped the blocks.json it was tagged with; what the tagger reads from it is unchanged."""
    with open(os.path.join(REPO_DIR, "data", "runs", "manifest.json"), encoding="utf-8") as f:
        runs = json.load(f)["runs"]
    now, checked = tagger_inputs(doc()), 0
    for r in runs:
        path = os.path.join(REPO_DIR, r["path"])
        if not os.path.exists(path):
            continue
        old = published_blocks(path)
        assert old is not None, r["id"]
        assert tagger_inputs(json.loads(old)) == now, r["id"]
        checked += 1
    assert checked, "no published run found"


def test_old_and_new_blocks_tag_the_same(run10, tmp_path):
    """Tagging the test city with the published blocks.json and with this one writes identical records.csv and
    households.csv: the lens's display content (contexts, loops, districtStart) never reaches the tags."""
    if not os.path.exists(PUBLISHED):
        pytest.skip("the published baseline run is not in this checkout")
    old = tmp_path / "blocks_published.json"
    old.write_bytes(published_blocks(PUBLISHED))
    assert json.loads(old.read_bytes()) != doc(), "expected the published blocks.json to predate this one"
    out = tmp_path / "old"
    subprocess.run([sys.executable, os.path.join(SIM_DIR, "simulate.py"), "--households", str(TEST_HOUSEHOLDS), "--out", str(out),
                    "--overrides", "", "--blocks", str(old)], check=True, cwd=SIM_DIR, capture_output=True)
    for name in ("records.csv", "households.csv"):
        with open(os.path.join(run10[1], name), "rb") as a, open(os.path.join(out, name), "rb") as b:
            assert a.read() == b.read(), name


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
