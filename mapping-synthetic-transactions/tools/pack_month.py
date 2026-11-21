#!/usr/bin/env python3
"""Pack a carried month into one zip, the same bytes every time.

    python3 tools/pack_month.py MONTH_DIR REPORT_DIR OUT.zip

MONTH_DIR is the folder `sim/simulate.py --date 2027-03-01 --days 31 --out MONTH_DIR` wrote (after
`sim/evidence/month.py MONTH_DIR REPORT_DIR` has added month_day_metrics.csv). The zip holds, under medianville_2027-03/:
    README.md                 what is in the bundle and how to rebuild it
    SHA256SUMS                the SHA-256 of every other file, so two builds can be compared file by file
    summary.md, evidence_checks.md, month_day_metrics.csv   the month (from REPORT_DIR and MONTH_DIR)
    2027-03-01/ ... 2027-03-31/   each day's records.csv, links.csv, household_ledger.csv, households.csv, persons.csv,
                              organizations.csv, public_services_context.csv, assumptions.csv and summary.md
    state_2027-03-31.json     the carried state after the last day (balances, queues, timers, loan books), to go on into April
The day-by-day state files are left out (each is the day before the next one's opening balances).

Deterministic: entries in sorted order, every timestamp 2027-03-31 00:00, permissions 644, deflate level 9. The zip's
SHA-256 depends on the zlib that compresses it; SHA256SUMS does not.
"""
import hashlib
import io
import os
import sys
import zipfile
import zlib

STAMP = (2027, 3, 31, 0, 0, 0)
TOP = "medianville_2027-03/"
DAY_FILES = ("records.csv", "links.csv", "household_ledger.csv", "households.csv", "persons.csv", "organizations.csv",
             "public_services_context.csv", "assumptions.csv", "summary.md")

README = """# Medianville, March 2027: the carried month

A synthetic city of about 100,000 people (41,400 households), simulated one day at a time from March 1 to March 31, 2027,
with each day starting from the balances and unfinished business of the day before. Simulated city: no real people.

Made by `sim/simulate.py --date 2027-03-01 --days 31` in jas0nmjames/playground (mapping-synthetic-transactions), seed
20270303, full city, ordinary weather. See `reference/medianville-2027-03-month-run-record.md` in the repo for the
commit, the versions and the SHA-256 of this zip, and `sim/medianville_sim/carry.py` for what carries between days.

- `summary.md`, `evidence_checks.md`: the month in figures and its evidence checks.
- `month_day_metrics.csv`: every measured figure, day by day.
- One folder per day, with the same tables as a one-day run plus `links.csv`, which ties records into chains across days
  (unpaid bills, shutoff notices, overdrafts, payday and title loans): each row names the chain, its step and the
  earlier record (date and record id) it follows from. Record ids start again at R0000001 each day, so a record is
  named by its date and id together.
- `state_2027-03-31.json`: the carried state after the last day; `--state-in` continues the run into April.
- `SHA256SUMS`: the SHA-256 of every file here.
"""


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main(month, report, out):
    days = sorted(d for d in os.listdir(month) if d[:4].isdigit() and os.path.isdir(os.path.join(month, d)))
    files = [("README.md", README.encode("utf-8"))]
    for name, folder in (("summary.md", report), ("evidence_checks.md", report), ("month_day_metrics.csv", month)):
        with open(os.path.join(folder, name), "rb") as f:
            files.append((name, f.read()))
    last = "state_%s.json" % days[-1]
    paths = [(last, os.path.join(month, last))]
    for d in days:
        for name in DAY_FILES:
            paths.append(("%s/%s" % (d, name), os.path.join(month, d, name)))
    sums = []
    for name, data in files:
        sums.append((name, sha(data)))
    for name, path in paths:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        sums.append((name, h.hexdigest()))
    files.append(("SHA256SUMS", "".join("%s  %s\n" % (h, n) for n, h in sorted(sums)).encode("utf-8")))
    entries = sorted([(n, ("bytes", b)) for n, b in files] + [(n, ("path", p)) for n, p in paths])
    dirs = sorted({TOP} | {TOP + n.split("/")[0] + "/" for n, _ in entries if "/" in n})
    tmp = out + ".part"
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d in dirs:
            zi = zipfile.ZipInfo(d, STAMP)
            zi.external_attr = (0o40755 << 16) | 0x10
            z.writestr(zi, b"")
        for name, (how, src) in entries:
            zi = zipfile.ZipInfo(TOP + name, STAMP)
            zi.external_attr = 0o100644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            for attr in ("compress_level", "_compresslevel"):      # Python 3.13 renamed it; 3.11 has only the private name
                try:
                    setattr(zi, attr, 9)
                except AttributeError:
                    pass
            if how == "bytes":
                z.writestr(zi, src, compresslevel=9)
            else:
                with open(src, "rb") as f, z.open(zi, "w") as w:
                    for chunk in iter(lambda: f.read(1 << 20), b""):
                        w.write(chunk)
    os.replace(tmp, out)
    size = os.path.getsize(out)
    unpacked = sum(len(b) for _, b in files) + sum(os.path.getsize(p) for _, p in paths)
    h = hashlib.sha256()
    with open(out, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    print("wrote %s: %d entries, %s bytes (%.0f MB), %s bytes unpacked (%.2f GB)" % (out, len(entries), "{:,}".format(size), size / 1e6,
                                                                                    "{:,}".format(unpacked), unpacked / 1e9))
    print("sha256", h.hexdigest())
    print("SHA256SUMS sha256", sha(files[-1][1]))
    print("zlib", zlib.ZLIB_RUNTIME_VERSION, "python", sys.version.split()[0])


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    main(*sys.argv[1:])
