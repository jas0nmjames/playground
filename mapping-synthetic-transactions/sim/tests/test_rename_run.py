"""The renamed copy of the v1 run (data/medianville_2027-03-03.zip) differs from the frozen v1 zip only in the name.

tools/rename_run.py writes it by applying the case map to every file's contents and path. Mapping it back must give
every file of data/halvern_2027-03-03.zip byte for byte, in the same order, with the same timestamps and permissions.
"""
import importlib.util
import os
import re
import zipfile

from conftest import REPO_DIR

V1_ZIP = os.path.join(REPO_DIR, "data", "halvern_2027-03-03.zip")
COPY_ZIP = os.path.join(REPO_DIR, "data", "medianville_2027-03-03.zip")


def load_tool():
    spec = importlib.util.spec_from_file_location("rename_run", os.path.join(REPO_DIR, "tools", "rename_run.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_copy_maps_back_to_v1_byte_for_byte():
    rr = load_tool()
    with zipfile.ZipFile(V1_ZIP) as v1, zipfile.ZipFile(COPY_ZIP) as cp:
        a, b = v1.infolist(), cp.infolist()
        assert [rr.rename(i.filename, rr.REVERSE) for i in b] == [i.filename for i in a]
        for i, j in zip(a, b):
            assert (j.date_time, j.compress_type, j.external_attr, j.create_system) == \
                   (i.date_time, i.compress_type, i.external_attr, i.create_system), i.filename
            assert rr.rename(cp.read(j), rr.REVERSE) == v1.read(i), i.filename
            assert cp.read(j) == rr.rename(v1.read(i)), i.filename


def test_copy_has_no_old_name():
    old = re.compile(b"(?i)halvern")
    with zipfile.ZipFile(COPY_ZIP) as cp:
        for j in cp.infolist():
            assert not old.search(j.filename.encode("utf-8")), j.filename
            assert not old.search(cp.read(j)), j.filename


def test_rename_strings():
    rr = load_tool()
    assert rr.rename("First Halvern Bank, halvern_sim, HALVERN QUADRANGLE, Halvern's") == \
        "First Medianville Bank, medianville_sim, MEDIANVILLE QUADRANGLE, Medianville's"
    assert rr.rename(rr.rename(b"halvern/out/records.csv"), rr.REVERSE) == b"halvern/out/records.csv"
