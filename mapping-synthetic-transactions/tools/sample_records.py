#!/usr/bin/env python3
"""Draw a stratified sample of records from a run and write each one out as a card a person can read.

    python3 tools/sample_records.py RUN_DIR OUT.md [--n 160] [--salt 700] [--compare V1_RECORDS.csv]
                                    [--focus-share 0.35] [--selection SEL.json] [--label TEXT]

RUN_DIR is a folder `sim/simulate.py --out RUN_DIR` wrote. The sample is stratified by district x record type x
income group, like the simulator's own pick for hand-written text (`output.select_detailed`), with one change: with
--compare, a share of it (--focus-share) is drawn from the job kinds that are new since v1 or whose daily count moved
by half or more, one record per kind in turn, so the reading lands on what changed. --salt picks a different sample
from the same run: the close reading and the hand-written sample use different salts, so neither sees the other's
records first.

Each card shows what a reader needs to judge whether the record is believable (who, household, counterpart, money,
time, frictions, the record it follows from, the statement and the narrative) and nothing about the code. --selection
writes [record_id, job_category, actor_person_id] for every card, the signature `detailed_overrides.csv` keys on.
Reads the CSVs only: draws no random numbers from the simulator and changes nothing in RUN_DIR.
"""
import argparse
import csv
import json
import os
import random
from collections import Counter, defaultdict

DNAME = {"D1": "Downtown and core", "D2": "Inner suburbs", "D3": "Outer suburbs", "D4": "Satellite city",
         "D5": "Rural town", "D6": "Open country", "outside": "Outside Medianville", "": "no district"}


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def kind_counts(path):
    return Counter(r["job_category"] for r in rows(path))


def clock(ts):
    h, m = int(ts[11:13]), int(ts[14:16])
    return "%d:%02d %s" % (h % 12 or 12, m, "a.m." if h < 12 else "p.m.")


def money(v):
    x = float(v or 0)
    return ("-$%.2f" % -x) if x < 0 else ("$%.2f" % x)


def pick(recs, hh, n, salt, focus, focus_share):
    rng = random.Random(20270303 + salt)
    chosen = []
    if focus:
        by_kind = defaultdict(list)
        for i, r in enumerate(recs):
            if r["job_category"] in focus:
                by_kind[r["job_category"]].append(i)
        kinds = sorted(by_kind)
        for k in kinds:
            rng.shuffle(by_kind[k])
        want = int(round(n * focus_share))
        depth = 0
        while len(chosen) < want and any(len(by_kind[k]) > depth for k in kinds):
            for k in kinds:
                if len(chosen) < want and len(by_kind[k]) > depth:
                    chosen.append(by_kind[k][depth])
            depth += 1
    taken = set(chosen)
    cells = defaultdict(list)
    for i, r in enumerate(recs):
        if i in taken:
            continue
        H = hh.get(r["household_id"])
        cells[(r["district"] or "none", r["record_type"], H["alice_status"] if H else "org")].append(i)
    keys = sorted(cells)
    left = n - len(chosen)
    per = max(1, left // len(keys))
    strat = []
    for k in keys:
        lst = cells[k]
        rng.shuffle(lst)
        seen, take = set(), []
        for i in lst:
            if recs[i]["job_category"] not in seen:
                take.append(i)
                seen.add(recs[i]["job_category"])
            if len(take) >= per:
                break
        strat += take
    s = set(strat)
    rest = [i for k in keys for i in cells[k][:6] if i not in s]
    rng.shuffle(rest)
    rng.shuffle(strat)
    chosen += (strat + rest)[:left]
    return sorted(chosen, key=lambda i: (recs[i]["timestamp_local"], recs[i]["record_id"]))


def person_line(p, orgs):
    if p is None:
        return None
    sex = {"F": "woman", "M": "man"}.get(p["sex"], "person")
    age = int(p["age"])
    if age < 18:
        sex = {"F": "girl", "M": "boy"}.get(p["sex"], "child")
    bits = ["%s, %d" % (sex, age)]
    emp = p["employment_status"].replace("employed_", "").replace("_", " ")
    job = p["occupation"] or ""
    if job and job != "none":
        bits.append("%s (%s)" % (job, emp))
    else:
        bits.append(emp)
    o = orgs.get(p["employer_org_id"])
    if o:
        bits.append("works at %s" % o["name"])
    if p["work_schedule"] not in ("", "none"):
        bits.append("schedule %s, paid %s" % (p["work_schedule"], p["pay_cadence"]))
    if p["disability"] != "none":
        bits.append("disability: %s" % p["disability"])
    bits.append("coverage: %s" % p["health_coverage"])
    if p["benefits_received"] not in ("", "none"):
        bits.append("benefits: %s" % p["benefits_received"].replace(";", ", "))
    if p["caregiver_for"] not in ("", "none"):
        bits.append("caregiver for %s" % p["caregiver_for"])
    bits.append("%s, %s" % (p["race_ethnicity"].replace("_", " "), p["education"].replace("_", " ")))
    return "; ".join(bits)


def household_line(H):
    if H is None:
        return None
    t = H["household_type"].replace("group_quarters:", "group quarters: ").replace("_", " ")
    s = "%s, %s %s, $%s a year (%s), %s, %s, %s" % (
        t, H["size"], "person" if H["size"] == "1" else "people",format(int(float(H["annual_income"])), ","), H["income_source_mix"], H["alice_status"],
        H["banked_status"], H["housing_tenure"].replace("_", " "))
    if float(H["monthly_housing_cost"] or 0):
        s += " ($%s a month)" % format(int(float(H["monthly_housing_cost"])), ",")
    s += ", %s vehicle%s, internet %s, %s" % (H["vehicles"], "" if H["vehicles"] == "1" else "s", H["internet_at_home"], H["primary_language"])
    if H["notes"]:
        s += "; notes: %s" % H["notes"]
    return s


def party(pid, orgs, people):
    if not pid:
        return None
    if pid in orgs:
        o = orgs[pid]
        return "%s (%s, %s, %s)" % (o["name"], o["org_type"], o["sector"], DNAME.get(o["district"], o["district"]))
    if pid in people:
        return "%s (resident %s)" % (person_line(people[pid], orgs).split(";")[0], pid)
    return pid


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=160)
    ap.add_argument("--salt", type=int, default=700)
    ap.add_argument("--compare", help="v1's records.csv: focus part of the sample on kinds that are new or moved")
    ap.add_argument("--focus-share", type=float, default=0.35)
    ap.add_argument("--selection", help="write [record_id, job_category, actor_person_id] per card here")
    ap.add_argument("--label", default="")
    ap.add_argument("--start", type=int, default=1, help="number the cards from here")
    ap.add_argument("--compact", action="store_true", help="one line per record (for the writer) instead of cards")
    ap.add_argument("--ids", help="a selection.json ([record_id, ...] rows): show exactly these records instead of drawing a sample")
    a = ap.parse_args()

    recs = list(rows(os.path.join(a.run, "records.csv")))
    hh = {r["household_id"]: r for r in rows(os.path.join(a.run, "households.csv"))}
    orgs = {r["org_id"]: r for r in rows(os.path.join(a.run, "organizations.csv"))}
    focus = set()
    if a.compare:
        old, new = kind_counts(a.compare), Counter(r["job_category"] for r in recs)
        for k, c in new.items():
            o = old.get(k, 0)
            if o == 0 or (max(c, o) >= 5 and (c >= 1.5 * o or c <= o / 1.5)):
                focus.add(k)
    if a.ids:
        with open(a.ids) as f:
            want = {row[0] for row in json.load(f)}
        idx = [i for i, r in enumerate(recs) if r["record_id"] in want]
    else:
        idx = pick(recs, hh, a.n, a.salt, focus, a.focus_share if focus else 0)
    need = set()
    for i in idx:
        r = recs[i]
        need.update(x for x in (r["actor_person_id"], r["beneficiary_person_id"], r["from_party_id"], r["to_party_id"]) if x.startswith("P"))
    people = {p["person_id"]: p for p in rows(os.path.join(a.run, "persons.csv")) if p["person_id"] in need}
    by_id = {r["record_id"]: r for r in recs}

    if a.compact:
        lines = []
        for i in idx:
            r = recs[i]
            p, H = people.get(r["actor_person_id"]), hh.get(r["household_id"])
            who = "-"
            if p is not None:
                who = "%s%s %s" % (p["sex"], p["age"], (p["occupation"] if p["occupation"] not in ("", "none") else p["employment_status"]).replace("employed_", ""))
                if p["disability"] != "none":
                    who += " dis:" + p["disability"]
                who += " cov:" + p["health_coverage"]
                if p["benefits_received"] not in ("", "none"):
                    who += " ben:" + p["benefits_received"]
            hd = "-"
            if H is not None:
                hd = "%s %sp $%dk %s %s %s veh%s %s" % (H["household_type"].replace("group_quarters:", "GQ:"), H["size"], round(float(H["annual_income"]) / 1000),
                                                       H["alice_status"], H["banked_status"], H["housing_tenure"].replace("owner_", "own_"), H["vehicles"], H["primary_language"])
            other = next((orgs[x]["name"] for x in (r["to_party_id"], r["from_party_id"]) if x in orgs), "-")
            ben = ""
            if r["beneficiary_person_id"] and r["beneficiary_person_id"] != r["actor_person_id"] and r["beneficiary_person_id"] in people:
                b = people[r["beneficiary_person_id"]]
                ben = " for:%s%s" % (b["sex"], b["age"])
            m = "g%s u%s" % (r["amount_gross"], r["amount_paid_by_user"])
            if float(r["amount_paid_by_third_party"] or 0):
                m += " t%s[%s]" % (r["amount_paid_by_third_party"], r["third_party_payer"][:40])
            if float(r["fee_amount"] or 0):
                m += " fee%s(%s)" % (r["fee_amount"], r["fee_type"])
            tm = "%sm" % r["time_minutes"] + (" w%s" % r["wait_minutes"] if r["wait_minutes"] not in ("", "0") else "") + \
                 (" %smi %s" % (r["travel_miles"], r["travel_mode"]) if float(r["travel_miles"] or 0) else "")
            rel = ""
            if r["related_record_id"] in by_id:
                q = by_id[r["related_record_id"]]
                rel = " after:%s/%s" % (q["job_category"].split(".")[1], q["outcome"])
            lines.append("%s %s %s %s %s | %s | %s | %s%s | %s | %s/%s | %s | %s %s%s | %s" % (
                r["record_id"], r["timestamp_local"][11:16], r["record_type"], r["job_category"], r["district"], who, hd, other, ben, m,
                r["payment_method"], r["channel"], tm, r["outcome"], r["friction_tags"], rel, r["narrative"]))
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        if a.selection:
            with open(a.selection, "w") as f:
                json.dump([[recs[i]["record_id"], recs[i]["job_category"], recs[i]["actor_person_id"]] for i in idx], f)
        print("%d lines to %s; %d focus kinds; record types %s" % (len(idx), a.out, len(focus), Counter(recs[i]["record_type"] for i in idx).most_common()))
        return
    out = ["# Records to read%s" % (": " + a.label if a.label else ""), "",
           "%d records from `%s` (%d records in the run). Stratified by district, record type and income group%s." % (
               len(idx), os.path.basename(os.path.normpath(a.run)), len(recs),
               "; %d of them drawn from the %d job kinds that are new since v1 or moved by half or more" % (
                   sum(1 for i in idx if recs[i]["job_category"] in focus), len(focus)) if focus else ""), ""]
    sel = []
    for n, i in enumerate(idx, a.start):
        r = recs[i]
        H = hh.get(r["household_id"])
        out.append("## %d. %s · %s · %s%s" % (n, r["record_id"], clock(r["timestamp_local"]), DNAME.get(r["district"], r["district"]),
                                              " · new or changed kind" if r["job_category"] in focus else ""))
        out.append("")
        L = [("Job", "%s (%s), outcome %s" % (r["job_category"], r["record_type"], r["outcome"]))]
        L.append(("Who", person_line(people.get(r["actor_person_id"]), orgs) or party(r["actor_person_id"], orgs, people) or "none"))
        if r["beneficiary_person_id"] and r["beneficiary_person_id"] != r["actor_person_id"]:
            L.append(("For", party(r["beneficiary_person_id"], orgs, people)))
        L.append(("Household", household_line(H) or "none"))
        L.append(("From", party(r["from_party_id"], orgs, people) or "none"))
        L.append(("To", party(r["to_party_id"], orgs, people) or "none"))
        m = "gross %s, paid by the person %s" % (money(r["amount_gross"]), money(r["amount_paid_by_user"]))
        if float(r["amount_paid_by_third_party"] or 0):
            m += ", paid by %s %s" % (r["third_party_payer"] or "a third party", money(r["amount_paid_by_third_party"]))
        if float(r["imputed_public_cost"] or 0):
            m += ", public cost %s (%s funding)" % (money(r["imputed_public_cost"]), r["funding_level"])
        if float(r["sales_tax"] or 0):
            m += ", sales tax %s" % money(r["sales_tax"])
        if float(r["fee_amount"] or 0):
            m += ", fee %s (%s)" % (money(r["fee_amount"]), r["fee_type"])
        L.append(("Money", m))
        L.append(("Paid with", "%s, %s" % (r["payment_method"], r["channel"])))
        t = "%s min" % r["time_minutes"]
        if r["wait_minutes"] not in ("", "0"):
            t += ", waited %s min" % r["wait_minutes"]
        if float(r["travel_miles"] or 0):
            t += ", %s mi by %s" % (r["travel_miles"], r["travel_mode"])
        L.append(("Time", t))
        if r["friction_tags"]:
            L.append(("Frictions", r["friction_tags"].replace(";", ", ")))
        if r["related_record_id"]:
            q = by_id.get(r["related_record_id"])
            L.append(("Follows", "%s (%s, %s, %s)" % (r["related_record_id"], q["job_category"], q["outcome"], clock(q["timestamp_local"])) if q else r["related_record_id"]))
        L.append(("Statement", r["job_statement"]))
        L.append(("Narrative", r["narrative"]))
        out += ["- **%s:** %s" % kv for kv in L]
        out.append("")
        sel.append([r["record_id"], r["job_category"], r["actor_person_id"]])
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    if a.selection:
        with open(a.selection, "w") as f:
            json.dump(sel, f)
    print("%d cards to %s; %d focus kinds; record types %s" % (len(idx), a.out, len(focus), Counter(recs[i]["record_type"] for i in idx).most_common()))


if __name__ == "__main__":
    main()
