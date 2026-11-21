"""Phase 5 fix 3: statements and narratives that fit the person and the place (v2 close reading, P4 and item 9)."""
import os
import re

import pytest

from conftest import read_csv


@pytest.fixture(scope="module")
def tables(run10):
    _, out = run10
    rec = read_csv(os.path.join(out, "records.csv"))
    per = {p["person_id"]: p for p in read_csv(os.path.join(out, "persons.csv"))}
    hh = {h["household_id"]: h for h in read_csv(os.path.join(out, "households.csv"))}
    org = {o["org_id"]: o for o in read_csv(os.path.join(out, "organizations.csv"))}
    return rec, per, hh, org


def kind(r):
    return r["job_category"].split(".", 1)[1]


def works(p):
    return p["employment_status"] in ("employed_full_time", "employed_part_time", "self_employed")


def test_children_are_not_helped_with_pills_and_bills(tables):
    rec, per, _, _ = tables
    kids = [r for r in rec if kind(r) == "caregiving_at_home" and r["beneficiary_person_id"] in per and int(per[r["beneficiary_person_id"]]["age"]) < 16]
    assert kids
    for r in kids:
        assert "pills" not in r["narrative"] and "paying bills" not in r["narrative"], r["record_id"]


def test_offerings_fit_the_faith(tables):
    rec, _, _, org = tables
    for r in rec:
        if kind(r) == "church_offering":
            name = org[r["to_party_id"]]["name"]
            if re.search(r"Masjid|Islamic|Mosque|Synagogue|Beth |Gurdwara|Buddhist|Hindu|Temple", name):
                assert "church" not in r["job_statement"] and "plate" not in r["job_statement"], (r["record_id"], name)


def test_no_work_talk_from_people_who_do_not_work(tables):
    rec, per, _, _ = tables
    n = 0
    for r in rec:
        p = per.get(r["actor_person_id"])
        if p is None or works(p):
            continue
        if kind(r) in ("fast_food", "gas_fill_up", "haircut", "school_dropoff", "car_repossessed", "car_disabled_by_lender", "caregiving_at_home"):
            n += 1
            assert not re.search(r"\bwork\b|on the clock", r["job_statement"] + " " + r["narrative"]), (r["record_id"], r["job_statement"])
    assert n > 50


def test_self_employed_do_not_fear_losing_a_job(tables):
    rec, per, _, _ = tables
    for r in rec:
        if kind(r) == "missed_shift_for_sick_child" and per[r["actor_person_id"]]["employment_status"] == "self_employed":
            assert "losing my job" not in r["job_statement"], r["record_id"]


def test_no_gas_talk_without_a_car(tables):
    rec, _, hh, _ = tables
    for r in rec:
        if kind(r) == "cash_tips" and hh[r["household_id"]]["vehicles"] == "0":
            assert "gas" not in r["job_statement"], r["record_id"]


def test_grammar(tables):
    rec = tables[0]
    for r in rec:
        text = r["job_statement"] + " " + r["narrative"]
        assert not re.search(r"\bas a [aeiou]", text), (r["record_id"], text)
        assert " 1 hours" not in text, r["record_id"]
        assert "I am building a" not in text, r["record_id"]
        if kind(r) == "social_security_deposit":
            assert "social security" not in r["narrative"] and "ssdi benefit" not in r["narrative"], r["record_id"]
        if kind(r) in ("school_dropoff", "school_pickup"):
            assert not re.search(r"(Dropped|Collected) \d", r["narrative"]), r["record_id"]


def test_app_transfers_say_why(tables):
    for r in tables[0]:
        if kind(r) == "p2p_transfer" and r["outcome"] == "completed":
            owed = re.search(r"splitting|paying a friend back|buying a used item|a share of rent", r["narrative"], re.I)
            assert ("owe someone" in r["job_statement"]) == bool(owed), (r["record_id"], r["narrative"])
