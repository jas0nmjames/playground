#!/usr/bin/env python3
"""Pack v2's one-day runs as data/runs/v2/medianville_<date>.zip and write data/runs/manifest.json.

    python3 tools/pack_runs.py RUNS_DIR [--commit SHA] [--out data/runs]

RUNS_DIR holds one folder per day, each written by `sim/simulate.py --date D [--weather W] --out RUNS_DIR/<folder>`:
the baseline day as `2027-03-03`, and the typed-day set (sim/evidence/typed_days.py) as `<date>` or `<date>_<weather>`.
Every day in the typed-day set must be there. Each zip holds, under medianville_<date>/:

    README.md          what the day is (its class, weather and weight in the year) and how to rebuild it
    SHA256SUMS         the SHA-256 of every other file, so two builds can be compared file by file
    records.csv, households.csv, persons.csv, organizations.csv, household_ledger.csv,
    public_services_context.csv, assumptions.csv, summary.md      the run's tables
    blocks.json        the systems lens's mapped blocks the records are tagged with
    simulate.py, medianville_sim/   the simulator that made it
    detailed_overrides.csv, detailed_sample.csv   the hand-written text (baseline day only, once it exists)

manifest.json lists every published run, v1 first: id, version, date, label, class, weather, weight, records, bytes,
sha256 and path (relative to mapping-synthetic-transactions/), and names the default run the viewers open.

Deterministic: entries sorted, every timestamp the run's date at 00:00, permissions 644, deflate level 9. A zip's SHA-256
depends on the zlib that compresses it; SHA256SUMS does not.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import zipfile
import zlib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(HERE, "sim")
sys.path.insert(0, SIM)
sys.path.insert(0, os.path.join(SIM, "evidence"))
import typed_days  # noqa: E402

BASELINE = "2027-03-03"
TABLES = ("records.csv", "households.csv", "persons.csv", "organizations.csv", "household_ledger.csv",
          "public_services_context.csv", "assumptions.csv", "summary.md")
V1 = [  # published before v2; never rebuilt here
    {"id": "v1-2027-03-03", "version": "v1", "date": "2027-03-03", "class": "baseline", "weather": "ordinary", "weight": None,
     "label": "v1 · Wednesday, March 3, 2027 (500 hand-written records)", "path": "data/medianville_2027-03-03.zip",
     "records": 201753, "handwritten": 500},
]
CLASS_LABEL = {
    "baseline": "the baseline day", "holiday_major": "major holiday", "holiday_minor": "minor holiday", "saturday": "Saturday",
    "sunday": "Sunday", "eitc_wave": "EITC refund wave", "ssi_first": "SSI day", "ss_third": "Social Security on the 3rd",
    "ss_wednesday": "Social Security Wednesday", "friday": "Friday payday", "tax_season_weekday": "tax-season weekday",
    "weekday_early": "early-month weekday", "weekday_mid": "mid-month weekday", "weekday_late": "late-month weekday",
    "storm": "storm day", "heat": "heat day",
}

README = """# Medianville, {long}: one simulated day (v2)

A synthetic city of about 100,000 people (41,400 households), simulated for one day. Simulated city: no real people,
businesses or local agencies. Federal programs keep their real names because the records could not show them otherwise.

| | |
|---|---|
| Date | {long} |
| Kind of day | {kind} |
| Weather | {weather} |
| Weight in the year | {weight} |
| Records | {records:,} |
| Hand-written records | {hand} |
| Simulator | `sim/` in jas0nmjames/playground (mapping-synthetic-transactions), commit {commit} |

{about}

## Files

- `records.csv`: every record of the day, one job someone was trying to get done, in time order.
- `households.csv`, `persons.csv`, `organizations.csv`: who is in the city.
- `household_ledger.csv`: each household's opening and closing balances; the money reconciles.
- `public_services_context.csv`, `assumptions.csv`, `summary.md`: what public services cost, every estimate and its
  source, and the day in figures.
- `blocks.json`: the systems lens's mapped blocks, which tag records with `block_id`, `block_pattern` and `context_ids`.
- `simulate.py`, `medianville_sim/`: the simulator, unchanged from the commit above.
{hand_files}- `SHA256SUMS`: the SHA-256 of every file here.

## Rebuild it

Python 3.11 and numpy 2.4.6 reproduce every table byte for byte (other versions may not):

```
python simulate.py --date {date}{weather_flag} --out out
```

Then `shasum -a 256 out/records.csv` against `SHA256SUMS`. The weights come from `sim/evidence/typed_days.py` in the repo:
each class of 2027 days is stood for by one or two simulated days, and the weights add up to the 365 days of the year.
"""


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_records(path):
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def long_date(iso):
    d = dt.date.fromisoformat(iso)
    return d.strftime("%A, %B ") + str(d.day) + d.strftime(", %Y")


def sim_files():
    out = [("simulate.py", os.path.join(SIM, "simulate.py"))]
    pkg = os.path.join(SIM, "medianville_sim")
    for n in sorted(os.listdir(pkg)):
        if n.endswith(".py"):
            out.append(("medianville_sim/" + n, os.path.join(pkg, n)))
    return out


def write_zip(out, top, stamp, files):
    """files: [(name, bytes_or_path)]; names are under top/."""
    dirs = sorted({top} | {top + n.rsplit("/", 1)[0] + "/" for n, _ in files if "/" in n})
    tmp = out + ".part"
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d in dirs:
            zi = zipfile.ZipInfo(d, stamp)
            zi.external_attr = (0o40755 << 16) | 0x10
            z.writestr(zi, b"")
        for name, src in sorted(files):
            zi = zipfile.ZipInfo(top + name, stamp)
            zi.external_attr = 0o100644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            for attr in ("compress_level", "_compresslevel"):      # Python 3.13 renamed it; 3.11 has only the private name
                try:
                    setattr(zi, attr, 9)
                except AttributeError:
                    pass
            if isinstance(src, bytes):
                z.writestr(zi, src, compresslevel=9)
            else:
                with open(src, "rb") as f, z.open(zi, "w") as w:
                    for chunk in iter(lambda: f.read(1 << 20), b""):
                        w.write(chunk)
    os.replace(tmp, out)


def pack_day(row, run_dir, out_dir, commit):
    date, weather = row["date"], row["weather"]
    top = "medianville_%s/" % date
    records = count_records(os.path.join(run_dir, "records.csv"))
    hand = 0
    ov = os.path.join(SIM, "detailed_overrides.csv")
    extra = []
    if row["class"] == "baseline" and os.path.exists(ov):
        with open(os.path.join(run_dir, "records.csv"), newline="", encoding="utf-8") as f:
            hand = sum(1 for r in csv.DictReader(f) if r["narrative"].startswith("[detailed]"))
        extra.append(("detailed_overrides.csv", ov))
        sample = os.path.join(SIM, "detailed_sample.csv")
        if os.path.exists(sample):
            extra.append(("detailed_sample.csv", sample))
    weight = row["weight"]
    if row["class"] == "baseline":
        about = ("The baseline day: the date the simulator runs by default, and the only day with hand-written text. It is "
                 "not weighted into the year; the typed-day set stands for the year.")
        wtxt = "not weighted (the baseline day)"
    else:
        about = "One of the typed-day set that stands for 2027: %s." % row["covers"]
        wtxt = "%.2f of 365 days" % weight
    hand_files = ("- `detailed_overrides.csv`, `detailed_sample.csv`: the hand-written text, keyed to this day's record ids, "
                  "and the hand-written records on their own.\n" if hand else "")
    readme = README.format(long=long_date(date), kind=CLASS_LABEL[row["class"]], weather=weather, weight=wtxt, records=records,
                           hand=("%d (their narratives start with `[detailed]`)" % hand) if hand else "none (only the baseline day has them)",
                           commit=commit, about=about, hand_files=hand_files, date=date,
                           weather_flag="" if weather == "ordinary" else " --weather " + weather).encode("utf-8")
    files = [("README.md", readme)] + [(n, os.path.join(run_dir, n)) for n in TABLES]
    blocks = os.path.join(HERE, "systems-lens", "blocks.json")
    files += [("blocks.json", blocks)] + sim_files() + extra
    sums = sorted((n, hashlib.sha256(s).hexdigest() if isinstance(s, bytes) else sha_file(s)) for n, s in files)
    files.append(("SHA256SUMS", "".join("%s  %s\n" % (h, n) for n, h in sums).encode("utf-8")))
    d = dt.date.fromisoformat(date)
    path = os.path.join(out_dir, "v2", "medianville_%s.zip" % date)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_zip(path, top, (d.year, d.month, d.day, 0, 0, 0), files)
    size = os.path.getsize(path)
    label = "%s · %s%s" % (long_date(date), CLASS_LABEL[row["class"]], " (%d hand-written records)" % hand if hand else "")
    entry = {"id": "v2-%s" % date, "version": "v2", "date": date, "class": row["class"], "weather": weather,
             "weight": None if row["class"] == "baseline" else round(weight, 4), "label": "v2 · " + label,
             "path": "data/runs/v2/" + os.path.basename(path), "records": records, "bytes": size,
             "sha256": sha_file(path), "handwritten": hand}
    print("%s  %-19s %-8s %7d records  %5.1f MB" % (date, row["class"], weather, records, size / 1e6))
    return entry


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs")
    ap.add_argument("--commit", default="(not recorded)")
    ap.add_argument("--out", default=os.path.join(HERE, "data", "runs"))
    a = ap.parse_args()
    rows = [{"date": BASELINE, "class": "baseline", "weather": "ordinary", "weight": None, "covers": ""}] + typed_days.day_set()
    entries = []
    for row in rows:
        folder = row["date"] + ("" if row["weather"] == "ordinary" else "_" + row["weather"])
        run_dir = os.path.join(a.runs, folder)
        if not os.path.exists(os.path.join(run_dir, "records.csv")):
            sys.exit("missing %s" % run_dir)
        entries.append(pack_day(row, run_dir, a.out, a.commit))
    v1 = []
    for e in V1:
        e = dict(e)
        p = os.path.join(HERE, e["path"])
        e["bytes"], e["sha256"] = os.path.getsize(p), sha_file(p)
        v1.append(e)
    man = {"about": "Every published Medianville run. Paths are relative to mapping-synthetic-transactions/. The viewers "
                    "open `default` unless the page is given ?run=<id>. The month (March 2027, 31 carried days) is a GitHub "
                    "Release download, not listed here: see reference/medianville-2027-03-month-run-record.md.",
           "default": "v2-%s" % BASELINE, "simulator_commit": a.commit, "runs": v1 + entries}
    with open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
        f.write("\n")
    total = sum(e["bytes"] for e in entries)
    print("wrote %d zips (%.0f MB) and %s; zlib %s, python %s" % (len(entries), total / 1e6, os.path.join(a.out, "manifest.json"),
                                                                    zlib.ZLIB_RUNTIME_VERSION, sys.version.split()[0]))


if __name__ == "__main__":
    main()
