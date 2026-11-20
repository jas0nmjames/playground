#!/usr/bin/env python3
"""Establishments per 100,000 residents for the kinds of organization Halvern has, from County Business Patterns 2023.

    python3 -I sources/tools/cbp_outlets.py

Reads sources/raw/cbp/cbp23us.zip (national file, all legal forms; NAICS 2017 codes) and writes
sources/derived/cbp_establishments_per_100k.csv: Halvern kinds, the NAICS codes summed for them, US establishments,
and establishments per 100,000 residents (US population 2023, about 334.9 million, stated here). CBP counts only
establishments with paid employees, so kinds with many one-person businesses (salons, storefront churches) run low.
"""
import csv
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
ZIP = os.path.join(SOURCES, "raw", "cbp", "cbp23us.zip")
OUT = os.path.join(SOURCES, "derived", "cbp_establishments_per_100k.csv")
US_POP_2023 = 334_900_000
MAP = [("grocery_full grocery_indep grocery_discount", "445110"), ("supercenter warehouse_club", "452311"), ("department", "452210"),
       ("dollar", "452319"), ("pharmacy", "446110"), ("gas", "447110 447190"), ("fastfood", "722513"), ("restaurant fine_dining", "722511"),
       ("coffee", "722515"), ("bar", "722410"), ("bank credit_union", "522110 522130"), ("child_care", "624410"), ("physician", "621111"),
       ("dental", "621210"), ("home_health", "621610"), ("dialysis", "621492"), ("hospital", "622110"), ("nursing_home", "623110"),
       ("assisted_living", "623312"), ("auto_repair tire oil_change", "811111 811112 811191 811198"), ("car_dealer bhph_dealer", "441110 441120"),
       ("salon", "812112"), ("nail", "812113"), ("laundromat dry_cleaner", "812310 812320"), ("church", "813110"), ("hotel", "721110"),
       ("gym", "713940"), ("funeral", "812210"), ("vet", "541940"), ("law", "541110"), ("accounting tax_prep", "541211 541213 541219"),
       ("pawn check_casher payday title_loan", "522390 522291"), ("urgent_care", "621493"), ("liquor", "445310"), ("auto_parts", "441310"),
       ("clothing", "448110 448120 448130 448140 448150 448190"), ("home_center hardware", "444110 444130"), ("electronics phone_store", "443142")]


def main():
    est = {}
    with zipfile.ZipFile(ZIP) as z:
        for r in csv.DictReader(io.TextIOWrapper(z.open("cbp23us.txt"), encoding="latin-1", newline="")):
            if r["lfo"] == "-":
                est[r["naics"].strip("-/")] = int(r["est"])
    rows = []
    for kinds, codes in MAP:
        n = sum(est.get(c, 0) for c in codes.split())
        rows.append({"halvern_kinds": kinds, "naics_2017": codes, "us_establishments": n, "per_100k": "%.2f" % (n / US_POP_2023 * 1e5)})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("%-40s %8d  %6s per 100k" % (r["halvern_kinds"], r["us_establishments"], r["per_100k"]))
    print("wrote %s" % os.path.relpath(OUT, os.path.dirname(SOURCES)))


if __name__ == "__main__":
    main()
