"""Phase 5 fix 2: record problems the v2 close reading found (reference/medianville-v2-close-reading.md, items 5-9)."""
import os

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


def f(r, k):
    return float(r[k] or 0)


def kind(r):
    return r["job_category"].split(".", 1)[1]


def test_prescription_claims_add_up(tables):
    rec = tables[0]
    rx = [r for r in rec if r["record_type"] == "insurance_claim" and kind(r) in ("prescription_pickup", "prescription_mail_order")]
    assert len(rx) > 100
    for r in rx:
        assert abs(f(r, "amount_gross") - (f(r, "amount_paid_by_user") - f(r, "fee_amount")) - f(r, "amount_paid_by_third_party")) <= .011, r["record_id"]
        assert "cash price" in r["narrative"] or "prescription" in r["narrative"] or "refill" in r["narrative"]


def test_uninsured_emergency_visits_cost_hours_not_minutes(tables):
    rec = tables[0]
    for r in rec:
        if kind(r) == "emergency_visit_uncompensated":
            assert f(r, "amount_gross") >= 300, r["record_id"]
            assert "written off as charity care" in r["narrative"]


def test_patients_go_to_practices_that_see_them(tables):
    rec, per, _, org = tables
    n = 0
    for r in rec:
        if kind(r) not in ("doctor_visit", "specialist_visit", "telehealth_visit", "appointment_rescheduled_no_free_time"):
            continue
        p = per.get(r["beneficiary_person_id"])
        o = org.get(r["to_party_id"]) or org.get(r["from_party_id"])
        if p is None or o is None:
            continue
        n += 1
        if int(p["age"]) >= 18:
            assert "Pediatric" not in o["name"], r["record_id"]
        if p["sex"] == "M" or int(p["age"]) < 18:
            assert "Women's Health" not in o["name"], r["record_id"]
    assert n > 50


def test_waits_fit_inside_the_time(tables):
    for r in tables[0]:
        assert f(r, "wait_minutes") <= f(r, "time_minutes"), r["record_id"]


def test_shipments_go_to_business_customers(tables):
    rec, _, _, org = tables
    ship = [r for r in rec if kind(r) == "customer_shipment_invoiced"]
    assert ship
    assert {org[r["from_party_id"]]["name"] for r in ship} == {"Out-of-area business customers"}


def test_pseudo_parties_are_not_filed_as_salons(tables):
    org = tables[3]
    names = {o["name"]: o["sector"] for o in org.values()}
    for n in ("Customers (general public)", "Out-of-area employers", "Family abroad", "Unknown party (suspected scam)"):
        assert names[n] == "Many parties (not one organization)"


def test_child_care_subsidies_come_from_the_state_agency(tables):
    rec, _, _, org = tables
    for r in rec:
        if kind(r) == "child_care_subsidy_payment_to_provider":
            assert org[r["from_party_id"]]["name"].startswith("State Department of Family & Economic Services")


def test_instant_cash_outs_charge_the_fee_they_name(tables):
    rec, _, hh, _ = tables
    outs = [r for r in rec if kind(r) == "p2p_instant_cash_out"]
    assert outs
    for r in outs:
        assert hh[r["household_id"]]["banked_status"] != "unbanked", r["record_id"]
        assert f(r, "fee_amount") > 0 and "%.2f" % f(r, "fee_amount") in r["narrative"]


def test_first_licenses_go_to_the_young_and_newly_arrived(tables):
    rec, per, hh, _ = tables
    for r in rec:
        if kind(r) == "first_driver_license":
            p, h = per[r["actor_person_id"]], hh[r["household_id"]]
            assert int(p["age"]) <= 24 or "immigrant_household" in h["notes"], r["record_id"]


def test_one_marriage_fee_per_courthouse(tables):
    rec, _, _, org = tables
    fees = {}
    for r in rec:
        if kind(r) == "marriage_license" and r["outcome"] == "completed":
            fees.setdefault(r["to_party_id"], set()).add(f(r, "amount_gross"))
    assert all(len(v) == 1 for v in fees.values()), fees


def test_refund_narratives_name_the_parts(tables):
    for r in tables[0]:
        if kind(r) == "federal_tax_refund" and "in all" in r["narrative"]:
            assert "%.2f" % f(r, "amount_gross") in r["narrative"], r["record_id"]
