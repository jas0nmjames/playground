"""Package a run as data/halvern_<date>.zip, the file v3 and the night map load.

    python tools/make_zip.py out ../halvern_2027-03-03.zip

The zip holds one folder, halvern/: the simulator (simulate.py, halvern_sim/, README.md, tools/), the hand-written
text (detailed_overrides.csv, detailed_sample_500.csv, detail_parts/), the systems lens's blocks.json, and the run's
tables under out/. Entries are sorted and stamped with one fixed time, so the same files make the same zip.
"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from halvern_sim.blocks import find_blocks  # noqa: E402

STAMP = (2027, 3, 3, 0, 0, 0)
OUT_FILES = ["records.csv", "household_ledger.csv", "organizations.csv", "households.csv", "public_services_context.csv", "persons.csv", "summary.md", "assumptions.csv"]


def main(out, dest):
    files = {}
    for root, dirs, names in os.walk(HERE):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", "out"))
        for n in names:
            if n.endswith(".pyc"):
                continue
            p = os.path.join(root, n)
            files["halvern/" + os.path.relpath(p, HERE).replace(os.sep, "/")] = p
    blocks = find_blocks(os.path.join(HERE, "halvern_sim", "x"))
    if blocks:
        files["halvern/blocks.json"] = blocks
    for n in OUT_FILES:
        files["halvern/out/" + n] = os.path.join(out, n)
    dirs = sorted({k.rsplit("/", i)[0] + "/" for k in files for i in range(1, k.count("/") + 1)})
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d in dirs:
            zi = zipfile.ZipInfo(d, STAMP); zi.external_attr = (0o40755 << 16) | 0x10
            z.writestr(zi, b"")
        for k in sorted(files):
            zi = zipfile.ZipInfo(k, STAMP); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
            with open(files[k], "rb") as f:
                z.writestr(zi, f.read(), compresslevel=9)
    print("wrote %s: %d files" % (dest, len(files)))


if __name__ == "__main__":
    main(*sys.argv[1:3])
