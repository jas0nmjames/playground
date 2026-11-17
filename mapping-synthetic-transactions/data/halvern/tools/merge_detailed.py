#!/usr/bin/env python3
"""Merge the hand-written parts (detail_parts/part*.txt) into detailed_overrides.csv.

Each part line is:  record_id|situation|motivation|outcome|narrative
job_statement = "When <situation>, I want to <motivation>, so I can <outcome>."
narrative     = "[detailed] <narrative>"
The record's job_category and actor_person_id come from detail_parts/selection.json and are stored as a
signature, so an override is only applied to the exact record it was written for.
"""
import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sel = json.load(open(os.path.join(HERE, "detail_parts", "selection.json")))
sig = {r[0]: (r[1], r[2]) for r in sel}
rows, seen, bad = [], set(), 0
for path in sorted(glob.glob(os.path.join(HERE, "detail_parts", "part*.txt"))):
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 5:
            print("BAD FIELD COUNT", os.path.basename(path), n, len(parts), line[:80]); bad += 1; continue
        rid, sit, mot, outc, narr = [x.strip() for x in parts]
        if rid not in sig:
            print("NOT IN SELECTION", os.path.basename(path), n, rid); bad += 1; continue
        if rid in seen:
            print("DUPLICATE", rid); bad += 1; continue
        seen.add(rid)
        for x in (sit, mot, outc):
            if x.endswith(".") or x.lower().startswith(("when ", "i want", "so i can")):
                print("CHECK PHRASE", rid, x[:60]); bad += 1
        if not narr.endswith((".", "!", "?")):
            print("NO FINAL STOP", rid); bad += 1
        js = "When %s, I want to %s, so I can %s." % (sit, mot, outc)
        rows.append([rid, sig[rid][0], sig[rid][1], js, "[detailed] " + narr])
missing = [r for r in sig if r not in seen]
print("written", len(rows), "missing", len(missing), missing[:10], "problems", bad)
rows.sort()
with open(os.path.join(HERE, "detailed_overrides.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["record_id", "job_category", "actor_person_id", "job_statement", "narrative"])
    w.writerows(rows)
sys.exit(1 if (bad or missing) else 0)
