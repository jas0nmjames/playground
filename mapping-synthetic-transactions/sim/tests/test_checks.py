"""The validation checks from the v1 build notes (reference/halvern-build-approach.md, step 9), as tests.

Each test recomputes its check from the output files (and, for time, the simulated shifts)
rather than trusting the summary the simulator writes about itself.
"""
import os
import re
import subprocess
import sys
from collections import defaultdict

import pytest

from conftest import REPO_DIR, SIM_DIR, TEST_HOUSEHOLDS, read_csv

# Controlled vocabularies from reference/halvern-transaction-generator-prompt.md
RECORD_TYPES = {"purchase", "bill_payment", "income", "benefit_issuance", "benefit_redemption", "transfer", "tax", "b2b",
                "public_service_encounter", "insurance_claim", "non_monetary_job", "failed_attempt"}
CHANNELS = {"in_person", "online", "app", "phone", "mail", "automatic"}
PAYMENT_METHODS = {"cash", "debit", "credit", "prepaid", "ebt_snap", "ebt_cash", "wic", "check", "ach", "p2p_app", "bnpl",
                   "money_order", "paycard", "payroll_deduction", "insurance", "none"}
OUTCOMES = {"completed", "partial", "declined", "abandoned", "rescheduled", "failed"}
FUNDING_LEVELS = {"", "federal", "state", "local", "mixed", "private", "philanthropic"}
FRICTION_TAGS = {"wait", "distance", "no_transit", "hours_mismatch", "missing_document", "language", "disability_access",
                 "digital_barrier", "fee", "insufficient_funds", "pending_hold", "benefits_cliff", "eligibility_confusion",
                 "out_of_stock", "outage", "caregiving_conflict", "schedule_volatility", "scam_attempt", "price_spike",
                 "paperwork", "repeat_trip", "other"}
LENS_TAGS = {"consumer_finance", "labor", "aging", "farmworker", "land_use", "disability", "rural", "housing", "health_cost",
             "education", "small_business", "public_finance", "family_care", "digital_access"}
DISTRICTS = {"", "D1", "D2", "D3", "D4", "D5", "D6"}

JOB_STATEMENT = re.compile(r"^When .+, I want to .+, so I can .+\.$", re.S)

# Whole-day stays and missed or cut shifts overlap the shift record by design; the simulator's own time check leaves them out too.
WHOLE_DAY = {"nursing_home_day", "skilled_nursing_rehab_day", "group_home_residential_services", "residential_treatment_day",
             "hospital_admission", "hospital_admission_uncompensated", "childbirth_hospital_stay", "at_hospital_for_a_birth",
             "stayed_home_with_sick_child", "missed_shift_for_sick_child", "late_or_missed_shift", "sent_home_early",
             "shift_cancelled_short_notice", "turned_down_extra_hours"}


def money(s):
    return float(s) if s else 0.0


# --- money reconciles per household ---------------------------------------------------------

def test_every_household_has_a_ledger_row(run10, ledger):
    sim, _ = run10
    assert len(ledger) == len(sim.households)


def test_money_reconciles_per_household(ledger):
    bad = []
    for r in ledger:
        open_net = sum(money(r[k]) for k in ("open_checking", "open_cash", "open_prepaid", "open_savings")) - money(r["open_card_debt"])
        close_net = sum(money(r[k]) for k in ("close_checking", "close_cash", "close_prepaid", "close_savings")) - money(r["close_card_debt"])
        flows = open_net + money(r["inflows"]) - money(r["outflows"])
        if r["reconciles"] != "yes" or abs(open_net - money(r["open_net"])) > .011 or abs(close_net - money(r["close_net"])) > .011 \
                or abs(flows - close_net) > .011:
            bad.append(r["household_id"])
    assert not bad, "%d households do not reconcile, e.g. %s" % (len(bad), bad[:5])


# --- nobody over 24 hours -------------------------------------------------------------------

def test_nobody_over_24_hours(run10, records):
    sim, _ = run10
    load = defaultdict(float)
    for r in records:
        if r["actor_person_id"] and r["channel"] == "in_person" and r["record_type"] != "public_service_encounter" \
                and r["job_category"].split(".", 1)[1] not in WHOLE_DAY:
            load[r["actor_person_id"]] += money(r["time_minutes"]) + money(r["wait_minutes"])
    over = []
    for p in sim.persons:
        work = sum(e - s for s, e in p.shift) if p.shift else 0
        if work + load.get(p.pid, 0.0) > 1440:
            over.append((p.pid, work + load[p.pid]))
    assert not over, "%d people exceed 24 hours, e.g. %s" % (len(over), over[:5])


def test_no_single_record_longer_than_a_day(records):
    assert max(money(r["time_minutes"]) for r in records) <= 1440


# --- every paycheck has withholding and FICA ------------------------------------------------

def test_every_paycheck_has_withholding_and_fica(records):
    paychecks = {r["record_id"] for r in records if r["record_type"] == "income" and r["job_category"].startswith("income.paycheck_")}
    assert paychecks, "no paychecks in the run"
    linked = defaultdict(set)
    for r in records:
        if r["job_category"] in ("income.payroll_income_tax_withholding", "income.payroll_fica"):
            linked[r["related_record_id"]].add(r["job_category"].split(".", 1)[1])
    missing = [rid for rid in paychecks if linked[rid] != {"payroll_income_tax_withholding", "payroll_fica"}]
    assert not missing, "%d paychecks lack withholding or FICA, e.g. %s" % (len(missing), missing[:5])


def test_payroll_tax_rows_point_at_a_paycheck(records):
    by_id = {r["record_id"]: r for r in records}
    orphans = [r["record_id"] for r in records if r["job_category"] in ("income.payroll_income_tax_withholding", "income.payroll_fica")
               and not by_id.get(r["related_record_id"], {}).get("job_category", "").startswith("income.paycheck_")]
    assert not orphans, orphans[:5]


# --- every value in its controlled vocabulary -----------------------------------------------

@pytest.mark.parametrize("column,allowed", [
    ("record_type", RECORD_TYPES), ("channel", CHANNELS), ("payment_method", PAYMENT_METHODS),
    ("outcome", OUTCOMES), ("funding_level", FUNDING_LEVELS), ("district", DISTRICTS)])
def test_single_value_vocabulary(records, column, allowed):
    bad = {r[column] for r in records} - allowed
    assert not bad, "%s has values outside the vocabulary: %s" % (column, sorted(bad))


@pytest.mark.parametrize("column,allowed", [("friction_tags", FRICTION_TAGS), ("lens_tags", LENS_TAGS)])
def test_tag_vocabulary(records, column, allowed):
    bad = {t for r in records for t in r[column].split(";") if t} - allowed
    assert not bad, "%s has tags outside the vocabulary: %s" % (column, sorted(bad))


def test_job_category_form(records):
    bad = {r["job_category"] for r in records if not re.fullmatch(r"[a-z_]+\.[a-z0-9_]+", r["job_category"])}
    assert not bad, sorted(bad)[:10]


def test_referenced_ids_exist(run10, records):
    _, out = run10
    people = {r["person_id"] for r in read_csv(os.path.join(out, "persons.csv"))}
    homes = {r["household_id"] for r in read_csv(os.path.join(out, "households.csv"))}
    orgs = {r["org_id"] for r in read_csv(os.path.join(out, "organizations.csv"))}
    rec_ids = {r["record_id"] for r in records}
    known = people | homes | orgs
    bad = []
    for r in records:
        for col in ("from_party_id", "to_party_id"):
            if r[col] and r[col] not in known:
                bad.append((r["record_id"], col, r[col]))
        if r["actor_person_id"] and r["actor_person_id"] not in people:
            bad.append((r["record_id"], "actor_person_id", r["actor_person_id"]))
        if r["household_id"] and r["household_id"] not in homes:
            bad.append((r["record_id"], "household_id", r["household_id"]))
        if r["related_record_id"] and r["related_record_id"] not in rec_ids:
            bad.append((r["record_id"], "related_record_id", r["related_record_id"]))
    assert not bad, "%d dangling ids, e.g. %s" % (len(bad), bad[:5])


# --- every job statement in the "When..., I want to..., so I can..." form --------------------

def test_job_statement_form(records):
    bad = [(r["record_id"], r["job_statement"]) for r in records if not JOB_STATEMENT.match(r["job_statement"])]
    assert not bad, "%d job statements are out of form, e.g. %s" % (len(bad), bad[:3])


# --- determinism ----------------------------------------------------------------------------

def test_identical_output_under_a_changed_hash_seed(run10, tmp_path):
    """Same seed and options, different PYTHONHASHSEED: records.csv must be byte-identical."""
    _, out = run10
    env = dict(os.environ, PYTHONHASHSEED="12345")
    subprocess.run([sys.executable, os.path.join(SIM_DIR, "simulate.py"), "--households", str(TEST_HOUSEHOLDS), "--out", str(tmp_path),
                    "--overrides", ""], check=True, env=env, cwd=SIM_DIR, capture_output=True)
    for name in ("records.csv", "household_ledger.csv", "persons.csv", "households.csv"):
        with open(os.path.join(out, name), "rb") as a, open(os.path.join(tmp_path, name), "rb") as b:
            assert a.read() == b.read(), name


# --- v1 reproduces --------------------------------------------------------------------------

@pytest.mark.slow
def test_v1_reproduces_byte_for_byte(tmp_path):
    """The full baseline day from sim/, with v1's hand-written text, matches data/halvern_2027-03-03.zip exactly."""
    import zipfile
    zpath = os.path.join(REPO_DIR, "data", "halvern_2027-03-03.zip")
    overrides = os.path.join(REPO_DIR, "data", "halvern", "detailed_overrides.csv")
    subprocess.run([sys.executable, os.path.join(SIM_DIR, "simulate.py"), "--out", str(tmp_path), "--overrides", overrides],
                   check=True, cwd=SIM_DIR, capture_output=True)
    with zipfile.ZipFile(zpath) as z:
        for name in ("records.csv", "household_ledger.csv", "households.csv", "persons.csv", "organizations.csv",
                     "public_services_context.csv", "assumptions.csv", "summary.md"):
            with open(os.path.join(tmp_path, name), "rb") as f:
                assert f.read() == z.read("halvern/out/" + name), name
