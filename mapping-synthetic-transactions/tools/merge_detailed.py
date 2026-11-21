#!/usr/bin/env python3
"""Merge v2's hand-written parts into sim/detailed_overrides.csv, and pull the finished records out of a run.

    python3 tools/merge_detailed.py                    # parts -> sim/detailed_overrides.csv
    python3 tools/merge_detailed.py --sample RUN_DIR   # also: RUN_DIR's [detailed] rows -> sim/detailed_sample.csv

The sample is drawn from the baseline day by `tools/sample_records.py RUN_DIR OUT.md --salt 500 --compare V1_RECORDS
--selection sim/detail_parts/selection.json`, which writes [record_id, job_category, actor_person_id] for each record.
The text is written in sim/detail_parts/part*.txt, one record a line:

    record_id|situation|motivation|outcome|narrative

job_statement = "When <situation>, I want to <motivation>, so I can <outcome>."
narrative     = "[detailed] <narrative>"

job_category and actor_person_id are stored with the text as a signature, so `simulate.py` applies an override only to
the exact record it was written for, and only on the baseline day (decision 2.5: the simulator is frozen once this file
exists). After merging, rerun the baseline day and pass its folder to --sample.
"""
import argparse
import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(HERE, "sim")
PARTS = os.path.join(SIM, "detail_parts")


def merge():
    with open(os.path.join(PARTS, "selection.json")) as f:
        sel = json.load(f)
    sig = {r[0]: (r[1], r[2]) for r in sel}
    rows, seen, bad = [], set(), 0
    for path in sorted(glob.glob(os.path.join(PARTS, "part*.txt"))):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                parts = line.split("|")
                where = "%s:%d" % (os.path.basename(path), n)
                if len(parts) != 5:
                    print("BAD FIELD COUNT", where, len(parts), line[:80]); bad += 1; continue
                rid, sit, mot, outc, narr = [x.strip() for x in parts]
                if rid not in sig:
                    print("NOT IN SELECTION", where, rid); bad += 1; continue
                if rid in seen:
                    print("DUPLICATE", where, rid); bad += 1; continue
                seen.add(rid)
                for x in (sit, mot, outc):
                    if not x or x.endswith(".") or x.lower().startswith(("when ", "i want", "so i can")):
                        print("CHECK PHRASE", where, rid, x[:60]); bad += 1
                if not narr.endswith((".", "!", "?")):
                    print("NO FINAL STOP", where, rid); bad += 1
                js = "When %s, I want to %s, so I can %s." % (sit, mot, outc)
                rows.append([rid, sig[rid][0], sig[rid][1], js, "[detailed] " + narr])
    missing = [r for r in sig if r not in seen]
    print("written %d of %d; missing %d %s; problems %d" % (len(rows), len(sig), len(missing), missing[:10], bad))
    rows.sort()
    with open(os.path.join(SIM, "detailed_overrides.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["record_id", "job_category", "actor_person_id", "job_statement", "narrative"])
        w.writerows(rows)
    return bad == 0 and not missing


def sample(run_dir):
    with open(os.path.join(run_dir, "records.csv"), newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        head = next(r)
        k = head.index("narrative")
        rows = [x for x in r if x[k].startswith("[detailed]")]
    with open(os.path.join(SIM, "detailed_sample.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(head)
        w.writerows(rows)
    print("%d hand-written records in %s -> sim/detailed_sample.csv" % (len(rows), run_dir))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", help="a baseline-day run made after merging: copy its hand-written rows to sim/detailed_sample.csv")
    a = ap.parse_args()
    ok = merge()
    if a.sample:
        with open(os.path.join(PARTS, "selection.json")) as f:
            want = len(json.load(f))
        got = len(sample(a.sample))
        if got != want:
            print("the run has %d hand-written records; the selection has %d" % (got, want)); ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
