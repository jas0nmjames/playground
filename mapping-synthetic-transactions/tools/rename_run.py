#!/usr/bin/env python3
"""Write a renamed copy of a packaged run: the city's first name, Halvern, becomes Medianville.

    python3 tools/rename_run.py                      # data/halvern_2027-03-03.zip -> data/medianville_2027-03-03.zip
    python3 tools/rename_run.py SRC.zip DEST.zip
    python3 tools/rename_run.py --reverse SRC.zip DEST.zip    # Medianville back to Halvern, for checking

The v1 run shipped as data/halvern_2027-03-03.zip and stays frozen under that name for the archived viewers. Until
v2 is packaged, the latest pages show v1's records, which name places such as "Halvern Transit". This writes a copy
with the case map applied to every file's contents and to every path in the zip (halvern/ becomes medianville/):

    Halvern -> Medianville, halvern -> medianville, HALVERN -> MEDIANVILLE (so halvern_sim -> medianville_sim)

Nothing else changes: the entries keep their order, timestamps, permissions and compression, and every other byte of
every file is the same. Because the source has no "medianville" in any case, mapping the copy back reproduces every
file of the source exactly; sim/tests/test_rename_run.py checks that.
"""
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "halvern_2027-03-03.zip")
DEST = os.path.join(ROOT, "data", "medianville_2027-03-03.zip")

FORWARD = [(b"HALVERN", b"MEDIANVILLE"), (b"Halvern", b"Medianville"), (b"halvern", b"medianville")]
REVERSE = [(b, a) for a, b in FORWARD]


def rename(data, pairs=FORWARD):
    """Apply the case map to bytes (or a str, for paths)."""
    if isinstance(data, str):
        return rename(data.encode("utf-8"), pairs).decode("utf-8")
    for a, b in pairs:
        data = data.replace(a, b)
    return data


def check_source(z, pairs):
    """The map is only reversible if the target spellings are absent from the source, in any case."""
    target = re.compile(b"(?i)" + re.escape(pairs[0][1]))
    for info in z.infolist():
        if target.search(info.filename.encode("utf-8")) or target.search(z.read(info)):
            raise SystemExit("%s already contains %r; the copy could not be mapped back exactly" % (info.filename, pairs[0][1]))


def copy_info(info, name):
    zi = zipfile.ZipInfo(name, info.date_time)
    for k in ("compress_type", "comment", "extra", "create_system", "internal_attr", "external_attr"):
        setattr(zi, k, getattr(info, k))
    return zi


def rename_zip(src, dest, pairs=FORWARD):
    with zipfile.ZipFile(src) as z:
        check_source(z, pairs)
        tmp = dest + ".part"
        with zipfile.ZipFile(tmp, "w") as out:
            out.comment = z.comment
            for info in z.infolist():
                level = 9 if info.compress_type == zipfile.ZIP_DEFLATED else None
                out.writestr(copy_info(info, rename(info.filename, pairs)), rename(z.read(info), pairs), compresslevel=level)
    os.replace(tmp, dest)
    return dest


def main(argv):
    pairs = REVERSE if argv[:1] == ["--reverse"] else FORWARD
    args = argv[1:] if pairs is REVERSE else argv
    src, dest = (args + [None, None])[:2] if args else (SRC, DEST)
    if not dest:
        raise SystemExit(__doc__)
    rename_zip(src, dest, pairs)
    with zipfile.ZipFile(dest) as z:
        print("wrote %s: %d entries, %d bytes" % (os.path.relpath(dest), len(z.infolist()), os.path.getsize(dest)))


if __name__ == "__main__":
    main(sys.argv[1:])
