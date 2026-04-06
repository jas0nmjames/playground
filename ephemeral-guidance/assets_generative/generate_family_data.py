#!/usr/bin/env python3
"""
Generate a full year of realistic financial data for a middle-class family of 5
in the Atlanta, GA area. Outputs separate JSON files for design prototyping.

Family:
  - Marcus (husband, 38) - Software support analyst, $68K
  - Jasmine (wife, 36) - Marketing coordinator, $54K
  - Darius (teenager, 15) - has own custodial checking + debit card
  - Amara (elementary, 8)
  - Elijah (infant, 14 months at start of data)

Combined gross: ~$122K  |  Atlanta, GA metro area
"""

import json
import random
import hashlib
from datetime import date, timedelta
from copy import deepcopy
from pathlib import Path

random.seed(42)  # reproducible

OUT_DIR = Path(__file__).parent
YEAR = 2025
START = date(YEAR, 1, 1)
END = date(YEAR, 12, 31)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def tid():
    return f"txn_{random.randint(100000, 999999)}"

def ref():
    return f"REF{random.randint(100000, 999999)}"

def auth():
    return f"A{random.randint(10000, 99999)}"

def dev_id():
    return f"dev_{random.randint(1000, 9999)}"

def ip():
    return f"198.51.{random.randint(100,110)}.{random.randint(1,254)}"

def jitter(base, pct=0.15):
    """Return base +/- pct variation."""
    return round(base * (1 + random.uniform(-pct, pct)), 2)

def pick_time():
    h = random.randint(7, 22)
    m = random.randint(0, 59)
    return f"{h:02d}:{m:02d}:00"

def biweekly_dates(start, end, first_pay):
    """Yield biweekly dates from first_pay within [start, end]."""
    d = first_pay
    while d <= end:
        if d >= start:
            yield d
        d += timedelta(days=14)

def monthly_dates(start, end, day_of_month):
    """Yield monthly dates."""
    from calendar import monthrange
    d = start.replace(day=min(day_of_month, 28))
    while d <= end:
        if d >= start:
            yield d
        m = d.month + 1
        y = d.year
        if m > 12:
            m = 1
            y += 1
        d = date(y, m, min(day_of_month, monthrange(y, m)[1]))

def weekly_dates(start, end, weekday=4):
    """Yield weekly dates for given weekday (0=Mon)."""
    d = start
    while d.weekday() != weekday:
        d += timedelta(days=1)
    while d <= end:
        yield d
        d += timedelta(days=7)

def random_dates_per_month(start, end, per_month_range):
    """Yield random dates, per_month_range = (min, max) per calendar month."""
    from calendar import monthrange
    d = start
    while d <= end:
        y, m = d.year, d.month
        last_day = monthrange(y, m)[1]
        count = random.randint(*per_month_range)
        days = sorted(random.sample(range(1, last_day + 1), min(count, last_day)))
        for day in days:
            dt = date(y, m, day)
            if start <= dt <= end:
                yield dt
        # next month
        if m == 12:
            d = date(y + 1, 1, 1)
        else:
            d = date(y, m + 1, 1)

# ---------------------------------------------------------------------------
# Atlanta-area merchants & locations
# ---------------------------------------------------------------------------

ATLANTA_LOCATIONS = {
    "Decatur": {"lat": 33.7748, "lng": -84.2963, "zip": "30030"},
    "Marietta": {"lat": 33.9526, "lng": -84.5499, "zip": "30060"},
    "Roswell": {"lat": 34.0234, "lng": -84.3616, "zip": "30075"},
    "Alpharetta": {"lat": 34.0754, "lng": -84.2941, "zip": "30009"},
    "Tucker": {"lat": 33.8554, "lng": -84.2171, "zip": "30084"},
    "Stone Mountain": {"lat": 33.8081, "lng": -84.1702, "zip": "30083"},
    "Brookhaven": {"lat": 33.8651, "lng": -84.3365, "zip": "30319"},
    "Sandy Springs": {"lat": 33.9304, "lng": -84.3733, "zip": "30328"},
    "East Point": {"lat": 33.6796, "lng": -84.4393, "zip": "30344"},
    "Dunwoody": {"lat": 33.9462, "lng": -84.3346, "zip": "30338"},
}

def rand_loc():
    city = random.choice(list(ATLANTA_LOCATIONS.keys()))
    loc = ATLANTA_LOCATIONS[city]
    return {
        "address": f"{random.randint(100,9999)} {random.choice(['Peachtree','Ponce de Leon','Memorial','Buford Hwy','Roswell Rd','Clairmont','Lavista','Briarcliff','N Druid Hills','Chamblee Dunwoody'])} {random.choice(['Rd','St','Ave','Blvd','Dr'])}",
        "city": city,
        "state": "GA",
        "postal_code": loc["zip"],
        "country": "US",
    }, loc["lat"] + random.uniform(-0.01, 0.01), loc["lng"] + random.uniform(-0.01, 0.01)


GROCERIES = [
    ("Kroger", "KROGER #1234 GA"),
    ("Publix", "PUBLIX SUPER MARKETS GA"),
    ("Walmart Supercenter", "WAL-MART SUPERCENTER GA"),
    ("ALDI", "ALDI STORES GA"),
    ("Trader Joe's", "TRADER JOE'S #735 GA"),
    ("Costco", "COSTCO WHOLESALE GA"),
    ("Sprouts Farmers Market", "SPROUTS FARMERS MARKET GA"),
]

GAS_STATIONS = [
    ("QuikTrip", "QT #4521 GA"),
    ("RaceTrac", "RACETRAC #2345 GA"),
    ("Shell", "SHELL OIL GA"),
    ("BP", "BP POS GA"),
    ("Chevron", "CHEVRON POS GA"),
]

RESTAURANTS = [
    ("Chick-fil-A", "CHICK-FIL-A #01234 GA"),
    ("Waffle House", "WAFFLE HOUSE #1876 GA"),
    ("Zaxby's", "ZAXBY'S #567 GA"),
    ("Willy's Mexicana Grill", "WILLY'S MEXICANA GRILL GA"),
    ("Mellow Mushroom", "MELLOW MUSHROOM GA"),
    ("The Varsity", "THE VARSITY INC GA"),
    ("Chipotle", "CHIPOTLE ONLINE GA"),
    ("Panera Bread", "PANERA BREAD #3456 GA"),
    ("Olive Garden", "DARDEN REST OLIVE GARDEN GA"),
    ("McDonald's", "MCDONALD'S #12345 GA"),
    ("Starbucks", "STARBUCKS #98765 GA"),
    ("Dunkin'", "DUNKIN DONUTS GA"),
    ("Chili's", "CHILIS GRILL GA"),
    ("Panda Express", "PANDA EXPRESS GA"),
    ("Taco Bell", "TACO BELL GA"),
    ("Wendy's", "WENDYS GA"),
    ("Popeyes", "POPEYES LA KITCHEN GA"),
    ("Domino's Pizza", "DOMINOS PIZZA GA"),
]

SHOPPING = [
    ("Target", "TARGET T-1234 GA", "general"),
    ("Walmart", "WAL-MART #1234 GA", "general"),
    ("Amazon.com", "AMZN MKTP US*AB1CD2EF", "ecommerce"),
    ("Amazon.com", "AMAZON.COM*AB3EF4GH", "ecommerce"),
    ("Old Navy", "OLD NAVY #3456 GA", "clothing"),
    ("TJ Maxx", "TJ MAXX #1234 GA", "clothing"),
    ("Marshalls", "MARSHALLS #5678 GA", "clothing"),
    ("Dick's Sporting Goods", "DICKS SPORTING GOODS GA", "sporting"),
    ("Dollar Tree", "DOLLAR TREE #4567 GA", "general"),
    ("Five Below", "FIVE BELOW #789 GA", "general"),
    ("Home Depot", "HOME DEPOT #1234 GA", "home"),
    ("Lowe's", "LOWES #5678 GA", "home"),
    ("Bath & Body Works", "BATH BODY WORKS GA", "personal_care"),
    ("CVS Pharmacy", "CVS PHARMACY #1234 GA", "health"),
    ("Walgreens", "WALGREENS #5678 GA", "health"),
    ("PetSmart", "PETSMART #901 GA", "pets"),
    ("GameStop", "GAMESTOP #4321 GA", "entertainment"),
    ("Best Buy", "BEST BUY #567 GA", "electronics"),
    ("IKEA", "IKEA ATLANTA GA", "home"),
]

SUBSCRIPTIONS = [
    ("Netflix", "NETFLIX.COM", 15.49),
    ("Disney+", "DISNEYPLUS", 13.99),
    ("Spotify Family", "SPOTIFY USA", 16.99),
    ("Apple One Family", "APPLE.COM/BILL", 22.95),
    ("YouTube Premium", "GOOGLE*YOUTUBE PREMIUM", 13.99),
    ("Xbox Game Pass", "MICROSOFT*XBOX", 16.99),
    ("Amazon Prime", "AMAZON PRIME MEMBERSHIP", 14.99),
    ("Hulu", "HULU*SUBSCRIPTION", 7.99),
]

TEEN_MERCHANTS = [
    ("Chick-fil-A", "CHICK-FIL-A GA", "restaurants", (6, 14)),
    ("McDonald's", "MCDONALDS GA", "restaurants", (5, 12)),
    ("Starbucks", "STARBUCKS GA", "restaurants", (4, 8)),
    ("GameStop", "GAMESTOP GA", "entertainment", (10, 60)),
    ("Steam", "STEAMPOWERED.COM", "entertainment", (5, 40)),
    ("Regal Cinemas", "REGAL CINEMAS GA", "entertainment", (12, 25)),
    ("Taco Bell", "TACO BELL GA", "restaurants", (5, 11)),
    ("Five Below", "FIVE BELOW GA", "general", (5, 25)),
    ("7-Eleven", "7-ELEVEN GA", "convenience", (3, 12)),
    ("Wingstop", "WINGSTOP GA", "restaurants", (10, 18)),
    ("Amazon.com", "AMZN MKTP US*TEEN", "ecommerce", (8, 50)),
]

HEALTHCARE = [
    ("Children's Healthcare of Atlanta", "CHILDRENS HEALTHCARE ATL", (30, 250)),
    ("Piedmont Healthcare", "PIEDMONT HEALTHCARE GA", (25, 300)),
    ("Kaiser Permanente", "KAISER PERMANENTE GA", (20, 150)),
    ("CVS Pharmacy", "CVS PHARMACY RX GA", (8, 85)),
    ("Walgreens Pharmacy", "WALGREENS RX GA", (8, 65)),
    ("Bright Smiles Dental", "BRIGHT SMILES DENTAL GA", (50, 200)),
    ("Pearle Vision", "PEARLE VISION GA", (50, 250)),
    ("Pediatric Associates", "PEDIATRIC ASSOC GA", (25, 175)),
]

# ---------------------------------------------------------------------------
# Family members
# ---------------------------------------------------------------------------

FAMILY = [
    {
        "member_id": "member_marcus",
        "first_name": "Marcus",
        "last_name": "Thompson",
        "role": "husband",
        "date_of_birth": "1987-03-14",
        "age": 38,
        "occupation": "Software Support Analyst",
        "employer": "TechBridge Solutions",
        "annual_salary": 68000,
        "devices": ["iPhone 15", "MacBook Air"],
    },
    {
        "member_id": "member_jasmine",
        "first_name": "Jasmine",
        "last_name": "Thompson",
        "role": "wife",
        "date_of_birth": "1989-06-22",
        "age": 36,
        "occupation": "Marketing Coordinator",
        "employer": "Peachtree Media Group",
        "annual_salary": 54000,
        "devices": ["Galaxy S24", "Dell Laptop"],
    },
    {
        "member_id": "member_darius",
        "first_name": "Darius",
        "last_name": "Thompson",
        "role": "teenager",
        "date_of_birth": "2010-01-08",
        "age": 15,
        "school": "Lakeside High School",
        "grade": "10th",
        "devices": ["iPhone SE"],
    },
    {
        "member_id": "member_amara",
        "first_name": "Amara",
        "last_name": "Thompson",
        "role": "child",
        "date_of_birth": "2017-04-15",
        "age": 8,
        "school": "Sagamore Hills Elementary",
        "grade": "3rd",
        "devices": [],
    },
    {
        "member_id": "member_elijah",
        "first_name": "Elijah",
        "last_name": "Thompson",
        "role": "infant",
        "date_of_birth": "2023-11-02",
        "age": 1,
        "daycare": "KinderCare Learning Center - Tucker",
        "devices": [],
    },
]

# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

ACCOUNTS = [
    {
        "account_id": "acct_joint_chk",
        "account_name": "Joint Checking",
        "account_type": "checking",
        "institution": "SunTrust / Truist",
        "routing_number": "061000104",
        "account_number_masked": "****4821",
        "owners": ["member_marcus", "member_jasmine"],
        "opening_balance": 3842.50,
        "interest_rate": 0.01,
    },
    {
        "account_id": "acct_joint_sav",
        "account_name": "Joint Savings",
        "account_type": "savings",
        "institution": "SunTrust / Truist",
        "routing_number": "061000104",
        "account_number_masked": "****4822",
        "owners": ["member_marcus", "member_jasmine"],
        "opening_balance": 8200.00,
        "interest_rate": 0.05,
    },
    {
        "account_id": "acct_hysa",
        "account_name": "Emergency Fund (HYSA)",
        "account_type": "high_yield_savings",
        "institution": "Marcus by Goldman Sachs",
        "routing_number": "124085024",
        "account_number_masked": "****7103",
        "owners": ["member_marcus", "member_jasmine"],
        "opening_balance": 12450.00,
        "interest_rate": 4.25,
    },
    {
        "account_id": "acct_joint_cc",
        "account_name": "Joint Credit Card",
        "account_type": "credit_card",
        "institution": "Chase",
        "card_network": "Visa",
        "card_type": "Chase Freedom Unlimited",
        "account_number_masked": "****3390",
        "credit_limit": 12000,
        "owners": ["member_marcus", "member_jasmine"],
        "opening_balance": -1243.67,  # negative = owed
        "interest_rate": 22.49,
    },
    {
        "account_id": "acct_marcus_cc",
        "account_name": "Marcus's Credit Card",
        "account_type": "credit_card",
        "institution": "Capital One",
        "card_network": "Mastercard",
        "card_type": "Capital One Quicksilver",
        "account_number_masked": "****8815",
        "credit_limit": 8000,
        "owners": ["member_marcus"],
        "opening_balance": -487.22,
        "interest_rate": 24.99,
    },
    {
        "account_id": "acct_teen_chk",
        "account_name": "Darius's Checking (Custodial)",
        "account_type": "checking",
        "institution": "SunTrust / Truist",
        "routing_number": "061000104",
        "account_number_masked": "****6155",
        "owners": ["member_darius"],
        "custodian": "member_marcus",
        "opening_balance": 245.00,
        "interest_rate": 0.01,
    },
    {
        "account_id": "acct_marcus_401k",
        "account_name": "Marcus's 401(k)",
        "account_type": "401k",
        "institution": "Fidelity",
        "plan_name": "TechBridge Solutions 401(k) Plan",
        "account_number_masked": "****9201",
        "owners": ["member_marcus"],
        "opening_balance": 42800.00,
        "employer_match": "100% up to 4%",
        "contribution_rate_pct": 6,
    },
    {
        "account_id": "acct_jasmine_401k",
        "account_name": "Jasmine's 401(k)",
        "account_type": "401k",
        "institution": "Vanguard",
        "plan_name": "Peachtree Media 401(k) Plan",
        "account_number_masked": "****9302",
        "owners": ["member_jasmine"],
        "opening_balance": 28500.00,
        "employer_match": "50% up to 6%",
        "contribution_rate_pct": 6,
    },
    {
        "account_id": "acct_jasmine_ira",
        "account_name": "Jasmine's Roth IRA",
        "account_type": "roth_ira",
        "institution": "Vanguard",
        "account_number_masked": "****9401",
        "owners": ["member_jasmine"],
        "opening_balance": 11200.00,
    },
    {
        "account_id": "acct_529_darius",
        "account_name": "Darius's 529 Plan",
        "account_type": "529",
        "institution": "Path2College 529 Plan (Georgia)",
        "account_number_masked": "****5291",
        "owners": ["member_darius"],
        "custodian": "member_marcus",
        "opening_balance": 18750.00,
    },
    {
        "account_id": "acct_529_amara",
        "account_name": "Amara's 529 Plan",
        "account_type": "529",
        "institution": "Path2College 529 Plan (Georgia)",
        "account_number_masked": "****5292",
        "owners": ["member_amara"],
        "custodian": "member_jasmine",
        "opening_balance": 9200.00,
    },
    {
        "account_id": "acct_529_elijah",
        "account_name": "Elijah's 529 Plan",
        "account_type": "529",
        "institution": "Path2College 529 Plan (Georgia)",
        "account_number_masked": "****5293",
        "owners": ["member_elijah"],
        "custodian": "member_marcus",
        "opening_balance": 2400.00,
    },
    {
        "account_id": "acct_brokerage",
        "account_name": "Joint Brokerage",
        "account_type": "brokerage",
        "institution": "Fidelity",
        "account_number_masked": "****7750",
        "owners": ["member_marcus", "member_jasmine"],
        "opening_balance": 6800.00,
    },
    {
        "account_id": "acct_crypto",
        "account_name": "Marcus's Crypto",
        "account_type": "crypto",
        "institution": "Coinbase",
        "account_number_masked": "****CB01",
        "owners": ["member_marcus"],
        "opening_balance": 1250.00,
    },
]

# ---------------------------------------------------------------------------
# Transaction builder
# ---------------------------------------------------------------------------

ALL_TRANSACTIONS = []

def make_txn(
    dt, merchant, amount, acct_id, category,
    txn_type="purchase", credit=False,
    raw_desc=None, entry="chip", payment="debit_card",
    network="Visa", device="iPhone 15", member_id="member_marcus",
    channel="api", notes="", tags=None,
    mcc="5411", reward_pts=0, cashback=0.0,
):
    loc, lat, lng = rand_loc()
    if "amazon" in merchant.lower() or "netflix" in merchant.lower() or "online" in (raw_desc or "").lower() or "steam" in merchant.lower():
        entry = "online"
        channel = random.choice(["web", "mobile_app"])
    return {
        "transaction_id": tid(),
        "date": dt.isoformat(),
        "time": pick_time(),
        "merchant": merchant,
        "amount": round(amount, 2),
        "currency": "USD",
        "type": "credit" if credit else "debit",
        "status": "posted",
        "transaction_type": txn_type,
        "category": category,
        "raw_description": raw_desc or merchant.upper() + " GA",
        "clean_description": merchant,
        "merchant_location": loc,
        "entry_method": entry,
        "payment_method": payment,
        "network": network,
        "tags": tags or [],
        "notes": notes,
        "running_balance": 0,  # filled later
        "payee_name": "" if not credit else merchant,
        "payer_name": merchant if not credit else "",
        "merchant_category_code": mcc,
        "device_used": device,
        "auth_amount": round(amount, 2),
        "capture_amount": round(amount, 2),
        "auth_code": auth(),
        "reference_number": ref(),
        "check_number": "",
        "routing_number": "",
        "account_number_masked": next(
            a["account_number_masked"] for a in ACCOUNTS if a["account_id"] == acct_id
        ),
        "foreign_currency_amount": None,
        "foreign_currency_code": None,
        "exchange_rate": None,
        "fee_amount": None,
        "reward_points_earned": reward_pts,
        "cashback_amount": cashback,
        "split_details": [],
        "geo_latitude": round(lat, 6),
        "geo_longitude": round(lng, 6),
        "initiated_ip": ip(),
        "device_id": dev_id(),
        "user_agent": "Mozilla/5.0 (iPhone; iOS 18...)" if "iPhone" in device else "Mozilla/5.0 (Linux; Android 15...)",
        "compliance_flags": [],
        "account_id": acct_id,
        "member_id": member_id,
        "is_final_capture": True,
        "channel": channel,
        "initiated_by": "user",
    }


# ---------------------------------------------------------------------------
# Generate salary / income
# ---------------------------------------------------------------------------

# Marcus: $68K gross -> ~$2,090 net biweekly (after 401k 6%, taxes, benefits)
# 401k contribution: $68K * 6% = $4,080/yr = ~$157/pay period
# Employer match 4% = $2,720/yr = ~$104.62/pay period
for dt in biweekly_dates(START, END, date(2025, 1, 10)):
    net = jitter(2090, 0.005)
    ALL_TRANSACTIONS.append(make_txn(
        dt, "TechBridge Solutions - Payroll", net, "acct_joint_chk",
        "salary", txn_type="salary", credit=True,
        raw_desc="TECHBRIDGE SOL PAYROLL DIR DEP",
        entry="ach", payment="direct_deposit", network="ACH",
        device="N/A", member_id="member_marcus", channel="ach",
        mcc="0000",
    ))

# Jasmine: $54K gross -> ~$1,660 net biweekly
# 401k contribution: $54K * 6% = $3,240/yr = ~$124.62/pay period
# Employer match 3% = $1,620/yr = ~$62.31/pay period
for dt in biweekly_dates(START, END, date(2025, 1, 3)):
    net = jitter(1660, 0.005)
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Peachtree Media Group - Payroll", net, "acct_joint_chk",
        "salary", txn_type="salary", credit=True,
        raw_desc="PEACHTREE MEDIA PAYROLL DIR DEP",
        entry="ach", payment="direct_deposit", network="ACH",
        device="N/A", member_id="member_jasmine", channel="ach",
        mcc="0000",
    ))

# Tax refund in February
ALL_TRANSACTIONS.append(make_txn(
    date(2025, 2, 21), "IRS Tax Refund", 3247.00, "acct_joint_chk",
    "tax_refund", txn_type="deposit", credit=True,
    raw_desc="IRS TREAS 310 TAX REFUND",
    entry="ach", payment="direct_deposit", network="ACH",
    device="N/A", member_id="member_marcus", channel="ach",
    mcc="0000",
))

# Georgia state tax refund
ALL_TRANSACTIONS.append(make_txn(
    date(2025, 3, 7), "Georgia Dept of Revenue", 412.00, "acct_joint_chk",
    "tax_refund", txn_type="deposit", credit=True,
    raw_desc="GA DEPT REVENUE TAX REFUND",
    entry="ach", payment="direct_deposit", network="ACH",
    device="N/A", member_id="member_marcus", channel="ach",
    mcc="0000",
))

# ---------------------------------------------------------------------------
# Fixed monthly expenses from joint checking
# ---------------------------------------------------------------------------

for dt in monthly_dates(START, END, 1):
    # Mortgage
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Truist Mortgage", 1842.00, "acct_joint_chk",
        "housing", txn_type="bill_payment",
        raw_desc="TRUIST MORTGAGE PMT",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="6012",
    ))

for dt in monthly_dates(START, END, 5):
    # Daycare - KinderCare
    ALL_TRANSACTIONS.append(make_txn(
        dt, "KinderCare Learning Center", 1185.00, "acct_joint_chk",
        "childcare", txn_type="bill_payment",
        raw_desc="KINDERCARE TUCKER GA",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="8211",
    ))

for dt in monthly_dates(START, END, 15):
    # Car payment 1 - Marcus's car
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Capital One Auto Finance", 348.00, "acct_joint_chk",
        "auto_loan", txn_type="bill_payment",
        raw_desc="CAPITAL ONE AUTO FINANCE PMT",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="6012",
    ))

for dt in monthly_dates(START, END, 15):
    # Car payment 2 - Jasmine's car
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Ally Financial Auto", 289.00, "acct_joint_chk",
        "auto_loan", txn_type="bill_payment",
        raw_desc="ALLY FINANCIAL AUTO PMT",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="6012",
    ))

for dt in monthly_dates(START, END, 20):
    # Auto insurance
    ALL_TRANSACTIONS.append(make_txn(
        dt, "State Farm Insurance", jitter(218, 0.01), "acct_joint_chk",
        "insurance", txn_type="bill_payment",
        raw_desc="STATE FARM INS PREM",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="6300",
    ))

for dt in monthly_dates(START, END, 18):
    # Georgia Power
    month_num = dt.month
    electric = {1: 165, 2: 155, 3: 130, 4: 110, 5: 135, 6: 185, 7: 210, 8: 220, 9: 190, 10: 140, 11: 120, 12: 155}
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Georgia Power", jitter(electric[month_num], 0.08), "acct_joint_chk",
        "utilities", txn_type="bill_payment",
        raw_desc="GEORGIA POWER ELEC",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="4900",
    ))

for dt in monthly_dates(START, END, 22):
    # Atlanta Gas Light
    month_num = dt.month
    gas_bill = {1: 95, 2: 88, 3: 65, 4: 40, 5: 30, 6: 25, 7: 22, 8: 22, 9: 25, 10: 35, 11: 55, 12: 82}
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Atlanta Gas Light", jitter(gas_bill[month_num], 0.10), "acct_joint_chk",
        "utilities", txn_type="bill_payment",
        raw_desc="ATLANTA GAS LIGHT",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="4900",
    ))

for dt in monthly_dates(START, END, 12):
    # DeKalb County Water
    ALL_TRANSACTIONS.append(make_txn(
        dt, "DeKalb County Water", jitter(72, 0.12), "acct_joint_chk",
        "utilities", txn_type="bill_payment",
        raw_desc="DEKALB COUNTY WATER SVC",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="4900",
    ))

for dt in monthly_dates(START, END, 8):
    # Xfinity internet
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Xfinity / Comcast", 79.99, "acct_joint_chk",
        "utilities", txn_type="bill_payment",
        raw_desc="COMCAST CABLE COMM",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="4899",
    ))

for dt in monthly_dates(START, END, 10):
    # T-Mobile family plan
    ALL_TRANSACTIONS.append(make_txn(
        dt, "T-Mobile", 185.00, "acct_joint_chk",
        "utilities", txn_type="bill_payment",
        raw_desc="T-MOBILE*PAYMENT",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="4812",
    ))

# Transfer to savings (monthly)
for dt in monthly_dates(START, END, 2):
    amt = random.choice([200, 250, 300, 250, 300, 200, 150, 200, 250, 300, 200, 250])
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Transfer to Savings", amt, "acct_joint_chk",
        "transfer", txn_type="transfer",
        raw_desc="ONLINE TRANSFER TO SAV ****4822",
        entry="ach", payment="ach_transfer", network="ACH",
        device="iPhone 15", channel="mobile_app", mcc="0000",
    ))
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Transfer from Checking", amt, "acct_joint_sav",
        "transfer", txn_type="transfer", credit=True,
        raw_desc="ONLINE TRANSFER FROM CHK ****4821",
        entry="ach", payment="ach_transfer", network="ACH",
        device="iPhone 15", channel="mobile_app", mcc="0000",
    ))

# Monthly transfer to HYSA
for dt in monthly_dates(START, END, 3):
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Transfer to HYSA", 150.00, "acct_joint_chk",
        "transfer", txn_type="transfer",
        raw_desc="EXT TRANSFER TO MARCUS GOLDMAN ****7103",
        entry="ach", payment="ach_transfer", network="ACH",
        device="iPhone 15", channel="mobile_app", mcc="0000",
    ))
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Transfer from Truist Checking", 150.00, "acct_hysa",
        "transfer", txn_type="transfer", credit=True,
        raw_desc="EXT TRANSFER FROM TRUIST ****4821",
        entry="ach", payment="ach_transfer", network="ACH",
        device="iPhone 15", channel="mobile_app", mcc="0000",
    ))

# HYSA interest (monthly)
for dt in monthly_dates(START, END, 28):
    # ~4.25% APY on growing balance, approximate
    interest = round(random.uniform(42, 55), 2)
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Interest Payment", interest, "acct_hysa",
        "interest", txn_type="interest", credit=True,
        raw_desc="INTEREST PAYMENT",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="0000",
    ))

# Allowance to teen (biweekly)
for dt in biweekly_dates(START, END, date(2025, 1, 10)):
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Transfer to Darius", 40.00, "acct_joint_chk",
        "transfer", txn_type="transfer",
        raw_desc="ONLINE TRANSFER TO CHK ****6155",
        entry="ach", payment="ach_transfer", network="ACH",
        device="iPhone 15", channel="mobile_app", mcc="0000",
    ))
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Allowance from Parents", 40.00, "acct_teen_chk",
        "transfer", txn_type="transfer", credit=True,
        raw_desc="ONLINE TRANSFER FROM CHK ****4821",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="0000",
    ))

# ---------------------------------------------------------------------------
# Subscriptions (joint credit card)
# ---------------------------------------------------------------------------

for sub_name, sub_raw, sub_amt in SUBSCRIPTIONS:
    for dt in monthly_dates(START, END, random.randint(1, 28)):
        ALL_TRANSACTIONS.append(make_txn(
            dt, sub_name, sub_amt, "acct_joint_cc",
            "subscriptions", txn_type="purchase",
            raw_desc=sub_raw,
            entry="online", payment="credit_card", network="Visa",
            device=random.choice(["iPhone 15", "Galaxy S24"]),
            channel="web", mcc="5968",
            reward_pts=int(sub_amt),
            cashback=round(sub_amt * 0.015, 2),
        ))

# Credit card payments (monthly, from joint checking)
for dt in monthly_dates(START, END, 25):
    cc_pmt = jitter(1200, 0.20)
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Chase CC Payment", cc_pmt, "acct_joint_chk",
        "credit_card_payment", txn_type="payment",
        raw_desc="CHASE CREDIT CRD AUTOPAY",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="0000",
    ))
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Payment - Thank You", cc_pmt, "acct_joint_cc",
        "credit_card_payment", txn_type="payment", credit=True,
        raw_desc="PAYMENT RECEIVED - THANK YOU",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="0000",
    ))

# Marcus CC payment
for dt in monthly_dates(START, END, 28):
    cc_pmt = jitter(350, 0.25)
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Capital One CC Payment", cc_pmt, "acct_joint_chk",
        "credit_card_payment", txn_type="payment",
        raw_desc="CAPITAL ONE CARD ONLINE PMT",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="0000",
    ))
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Payment - Thank You", cc_pmt, "acct_marcus_cc",
        "credit_card_payment", txn_type="payment", credit=True,
        raw_desc="PAYMENT RECEIVED - THANK YOU",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="0000",
    ))

# ---------------------------------------------------------------------------
# Variable spending — groceries
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (6, 10)):
    merch, raw = random.choice(GROCERIES)
    amt = jitter(random.choice([45, 62, 78, 95, 110, 132, 55, 88, 150, 67]), 0.20)
    acct = random.choice(["acct_joint_chk", "acct_joint_cc"])
    pm = "debit_card" if "chk" in acct else "credit_card"
    nw = "Mastercard" if "chk" in acct else "Visa"
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, acct, "groceries",
        raw_desc=raw, entry=random.choice(["chip", "tap", "swipe"]),
        payment=pm, network=nw,
        device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel=random.choice(["api", "mobile_app"]),
        mcc="5411",
        reward_pts=int(amt) if "cc" in acct else 0,
        cashback=round(amt * 0.015, 2) if "cc" in acct else 0,
    ))

# ---------------------------------------------------------------------------
# Gas
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (4, 7)):
    merch, raw = random.choice(GAS_STATIONS)
    amt = jitter(random.choice([35, 42, 48, 52, 38, 45]), 0.10)
    acct = random.choice(["acct_joint_chk", "acct_joint_cc", "acct_marcus_cc"])
    pm = "debit_card" if "chk" in acct else "credit_card"
    nw = "Mastercard" if "marcus_cc" in acct else ("Visa" if "joint_cc" in acct else "Mastercard")
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, acct, "fuel",
        raw_desc=raw, entry=random.choice(["chip", "tap"]),
        payment=pm, network=nw,
        device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel="api", mcc="5541",
    ))

# ---------------------------------------------------------------------------
# Restaurants / dining
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (6, 12)):
    merch, raw = random.choice(RESTAURANTS)
    if merch in ("Olive Garden", "Chili's", "Mellow Mushroom"):
        amt = jitter(random.choice([55, 68, 75, 82, 95]), 0.15)
    elif merch in ("Starbucks", "Dunkin'"):
        amt = jitter(random.choice([5.50, 6.75, 8.25, 12.40]), 0.15)
    else:
        amt = jitter(random.choice([8, 12, 15, 18, 22, 28, 35]), 0.20)
    acct = random.choice(["acct_joint_cc", "acct_joint_cc", "acct_marcus_cc", "acct_joint_chk"])
    pm = "debit_card" if "chk" in acct else "credit_card"
    entry_m = random.choice(["chip", "tap", "online"]) if "Chipotle" not in merch else "online"
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, acct, "restaurants",
        raw_desc=raw, entry=entry_m,
        payment=pm if entry_m != "tap" else "apple_pay",
        network="Visa" if "joint_cc" in acct else "Mastercard",
        device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel=random.choice(["api", "mobile_app"]),
        mcc="5812",
    ))

# ---------------------------------------------------------------------------
# Shopping / general
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (4, 8)):
    merch, raw, sub_cat = random.choice(SHOPPING)
    if sub_cat == "ecommerce":
        amt = jitter(random.choice([15, 25, 35, 48, 65, 85, 22, 110, 42]), 0.25)
    elif sub_cat in ("clothing",):
        amt = jitter(random.choice([25, 38, 55, 72, 45, 90]), 0.20)
    elif sub_cat == "home":
        amt = jitter(random.choice([22, 45, 68, 95, 120, 35]), 0.25)
    elif sub_cat == "electronics":
        amt = jitter(random.choice([30, 55, 120, 200, 80]), 0.15)
    else:
        amt = jitter(random.choice([8, 15, 22, 35, 48, 18, 28]), 0.20)
    acct = random.choice(["acct_joint_cc", "acct_joint_cc", "acct_marcus_cc", "acct_joint_chk"])
    pm = "debit_card" if "chk" in acct else "credit_card"
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, acct, sub_cat if sub_cat != "general" else "shopping",
        raw_desc=raw,
        entry="online" if sub_cat == "ecommerce" else random.choice(["chip", "tap"]),
        payment=pm, network="Visa" if "joint_cc" in acct else "Mastercard",
        device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel="web" if sub_cat == "ecommerce" else random.choice(["api", "mobile_app"]),
        mcc="5311",
    ))

# ---------------------------------------------------------------------------
# Healthcare / medical
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (0, 3)):
    if random.random() < 0.4:
        continue  # skip some months
    merch, raw, (lo, hi) = random.choice(HEALTHCARE)
    amt = round(random.uniform(lo, hi), 2)
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, random.choice(["acct_joint_chk", "acct_joint_cc"]),
        "health", raw_desc=raw,
        entry="chip", payment=random.choice(["debit_card", "credit_card"]),
        network="Visa", device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel="api", mcc="8011",
    ))

# ---------------------------------------------------------------------------
# Kids activities / school
# ---------------------------------------------------------------------------

# After-school program for Amara (monthly)
for dt in monthly_dates(START, END, 1):
    if dt.month in (6, 7):  # summer break
        continue
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Sagamore Hills After-School", 225.00, "acct_joint_chk",
        "childcare", txn_type="bill_payment",
        raw_desc="SAGAMORE HILLS AFTER SCHOOL",
        entry="online", payment="ach_transfer", network="ACH",
        device="Galaxy S24", member_id="member_jasmine",
        channel="web", mcc="8211",
    ))

# Summer camp for Amara (June-July)
for dt in [date(2025, 6, 2), date(2025, 7, 1)]:
    ALL_TRANSACTIONS.append(make_txn(
        dt, "YMCA Summer Day Camp", 375.00, "acct_joint_chk",
        "childcare", txn_type="bill_payment",
        raw_desc="YMCA OF METRO ATLANTA DAY CAMP",
        entry="online", payment="credit_card", network="Visa",
        device="Galaxy S24", member_id="member_jasmine",
        channel="web", mcc="8211",
    ))

# Darius's school activities
for dt in [date(2025, 1, 15), date(2025, 3, 10), date(2025, 8, 5), date(2025, 9, 2), date(2025, 10, 20)]:
    items = [
        ("Lakeside HS Athletics", 85.00, "LAKESIDE HIGH SCHOOL ATH"),
        ("Lakeside HS Band", 120.00, "LAKESIDE HS BAND FEE"),
        ("School Spirit Wear", 45.00, "LAKESIDE SPIRIT WEAR"),
        ("AP Exam Fee", 98.00, "COLLEGE BOARD AP EXAM"),
        ("Field Trip Fee", 35.00, "LAKESIDE HS FIELD TRIP"),
    ]
    merch, amt, raw = random.choice(items)
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, "acct_joint_chk",
        "education", txn_type="purchase",
        raw_desc=raw, entry="online", payment="debit_card",
        network="Mastercard", device="Galaxy S24",
        member_id="member_jasmine", channel="web", mcc="8211",
    ))

# Back to school shopping (August)
bts_items = [
    ("Target", 145.00, "TARGET T-1234 BTS GA"),
    ("Walmart", 98.50, "WAL-MART #1234 GA"),
    ("Staples", 67.25, "STAPLES #567 GA"),
    ("Old Navy", 112.00, "OLD NAVY #3456 GA"),
    ("Dick's Sporting Goods", 89.99, "DICKS SPORTING GOODS GA"),
    ("Amazon.com", 156.78, "AMZN MKTP US*BTS2025"),
]
for merch, amt, raw in bts_items:
    dt = date(2025, 8, random.randint(1, 15))
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, jitter(amt, 0.10), "acct_joint_cc",
        "shopping", txn_type="purchase",
        raw_desc=raw, entry="chip" if "Amazon" not in merch else "online",
        payment="credit_card", network="Visa",
        device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id="member_jasmine", channel="api",
        mcc="5311", tags=["back_to_school"],
    ))

# Holiday shopping (November-December)
holiday_items = [
    ("Amazon.com", (25, 200)),
    ("Target", (20, 150)),
    ("Best Buy", (30, 300)),
    ("GameStop", (20, 70)),
    ("Dick's Sporting Goods", (25, 120)),
    ("Bath & Body Works", (15, 60)),
    ("Old Navy", (20, 80)),
    ("Walmart", (15, 100)),
]
for _ in range(18):
    merch, (lo, hi) = random.choice(holiday_items)
    amt = round(random.uniform(lo, hi), 2)
    dt = date(2025, random.choice([11, 12]), random.randint(1, 28))
    raw = merch.upper().replace("'", "") + " GA" if "Amazon" not in merch else "AMZN MKTP US*HOLIDAY"
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, "acct_joint_cc",
        "shopping", txn_type="purchase",
        raw_desc=raw, entry="online" if "Amazon" in merch else "chip",
        payment="credit_card", network="Visa",
        device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel="web" if "Amazon" in merch else "api",
        mcc="5311", tags=["holiday"],
    ))

# ---------------------------------------------------------------------------
# Teen spending (from custodial checking)
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (5, 10)):
    merch, raw, cat, (lo, hi) = random.choice(TEEN_MERCHANTS)
    amt = round(random.uniform(lo, hi), 2)
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, "acct_teen_chk",
        cat, raw_desc=raw,
        entry="tap" if "Steam" not in merch and "Amazon" not in merch else "online",
        payment="debit_card" if "Steam" not in merch and "Amazon" not in merch else "debit_card",
        network="Mastercard",
        device="iPhone SE", member_id="member_darius",
        channel="mobile_app" if "Steam" not in merch else "web",
        mcc="5812" if cat == "restaurants" else "5999",
    ))

# Birthday money deposit for Darius (January)
ALL_TRANSACTIONS.append(make_txn(
    date(2025, 1, 10), "Birthday Money - Grandparents", 100.00, "acct_teen_chk",
    "gift", txn_type="deposit", credit=True,
    raw_desc="MOBILE CHECK DEPOSIT",
    entry="online", payment="check", network="Check",
    device="iPhone SE", member_id="member_darius",
    channel="mobile_app", mcc="0000",
))

# Summer job income for Darius (June-August, weekly)
for dt in weekly_dates(date(2025, 6, 7), date(2025, 8, 23), weekday=5):  # Saturdays
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Chick-fil-A Payroll", jitter(185, 0.05), "acct_teen_chk",
        "salary", txn_type="salary", credit=True,
        raw_desc="CFA RESTAURANT PAYROLL",
        entry="ach", payment="direct_deposit", network="ACH",
        device="N/A", member_id="member_darius",
        channel="ach", mcc="0000",
    ))

# ---------------------------------------------------------------------------
# Marcus CC spending (gas, some personal, tech)
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (2, 5)):
    choices = [
        ("Micro Center", "MICRO CENTER GA", "electronics", (15, 120)),
        ("Steam", "STEAMPOWERED.COM", "entertainment", (10, 60)),
        ("Home Depot", "HOME DEPOT #1234 GA", "home", (15, 85)),
        ("AutoZone", "AUTOZONE #4567 GA", "auto", (12, 65)),
        ("Great Clips", "GREAT CLIPS GA", "personal_care", (18, 28)),
        ("Lowe's", "LOWES #5678 GA", "home", (20, 90)),
    ]
    merch, raw, cat, (lo, hi) = random.choice(choices)
    amt = round(random.uniform(lo, hi), 2)
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, amt, "acct_marcus_cc",
        cat, raw_desc=raw,
        entry="chip" if "Steam" not in merch else "online",
        payment="credit_card", network="Mastercard",
        device="iPhone 15", member_id="member_marcus",
        channel="api" if "Steam" not in merch else "web",
        mcc="5732" if cat == "electronics" else "5999",
    ))

# ---------------------------------------------------------------------------
# ATM withdrawals
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (1, 3)):
    amt = random.choice([40, 60, 80, 100, 60, 40, 100, 60])
    ALL_TRANSACTIONS.append(make_txn(
        dt, "ATM Withdrawal", amt, "acct_joint_chk",
        "cash", txn_type="withdrawal",
        raw_desc=f"ATM WITHDRAWAL TRUIST #{random.randint(1000,9999)} GA",
        entry="chip", payment="debit_card", network="Mastercard",
        device="N/A", member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel="atm", mcc="6011",
    ))

# ---------------------------------------------------------------------------
# Bank fees
# ---------------------------------------------------------------------------

# Occasional fees
for dt in [date(2025, 3, 15), date(2025, 7, 22), date(2025, 10, 5)]:
    ALL_TRANSACTIONS.append(make_txn(
        dt, "Bank Service Fee", 12.00, "acct_joint_chk",
        "fees", txn_type="fee",
        raw_desc="MONTHLY SERVICE FEE",
        entry="ach", payment="ach_transfer", network="ACH",
        device="N/A", channel="ach", mcc="0000",
    ))

# ---------------------------------------------------------------------------
# Seasonal / one-time
# ---------------------------------------------------------------------------

SPECIALS = [
    (date(2025, 2, 14), "Maggiano's Little Italy", 98.50, "acct_joint_cc", "restaurants", "MAGGIANOS LITTLE ITALY GA", ["valentines"]),
    (date(2025, 3, 15), "TurboTax", 89.00, "acct_joint_cc", "financial_services", "INTUIT TURBOTAX", ["taxes"]),
    (date(2025, 4, 20), "Home Depot", 245.00, "acct_joint_cc", "home", "HOME DEPOT #1234 GA", ["spring_project"]),
    (date(2025, 5, 11), "Brunch & Bloom ATL", 75.00, "acct_joint_cc", "restaurants", "BRUNCH AND BLOOM ATL GA", ["mothers_day"]),
    (date(2025, 6, 15), "Six Flags Over Georgia", 185.00, "acct_joint_cc", "entertainment", "SIX FLAGS OVER GA", ["summer"]),
    (date(2025, 6, 28), "Georgia Aquarium", 112.00, "acct_joint_cc", "entertainment", "GEORGIA AQUARIUM GA", ["summer"]),
    (date(2025, 7, 4), "Publix", 88.50, "acct_joint_chk", "groceries", "PUBLIX SUPER MARKETS GA", ["july_4th"]),
    (date(2025, 7, 12), "Stone Mountain Park", 55.00, "acct_joint_cc", "entertainment", "STONE MOUNTAIN PARK GA", ["summer"]),
    (date(2025, 8, 25), "Piedmont Urgent Care", 150.00, "acct_joint_chk", "health", "PIEDMONT URGENT CARE GA", []),
    (date(2025, 9, 1), "Costco", 385.00, "acct_joint_cc", "shopping", "COSTCO WHOLESALE GA", ["labor_day"]),
    (date(2025, 10, 15), "Spirit Halloween", 65.00, "acct_joint_cc", "shopping", "SPIRIT HALLOWEEN GA", ["halloween"]),
    (date(2025, 10, 28), "Party City", 42.00, "acct_joint_cc", "shopping", "PARTY CITY GA", ["halloween"]),
    (date(2025, 11, 28), "Walmart", 245.00, "acct_joint_cc", "shopping", "WAL-MART #1234 GA", ["black_friday"]),
    (date(2025, 11, 29), "Best Buy", 399.99, "acct_joint_cc", "electronics", "BEST BUY #567 GA", ["black_friday"]),
    (date(2025, 12, 15), "USPS Shipping", 38.50, "acct_joint_chk", "shipping", "USPS PO GA", ["holiday"]),
    (date(2025, 12, 24), "Kroger", 165.00, "acct_joint_chk", "groceries", "KROGER #1234 GA", ["holiday"]),
    (date(2025, 12, 31), "The Roof at Ponce City Market", 120.00, "acct_joint_cc", "restaurants", "THE ROOF PONCE CITY MKT GA", ["new_years"]),
]

for dt, merch, amt, acct, cat, raw, tags in SPECIALS:
    ALL_TRANSACTIONS.append(make_txn(
        dt, merch, jitter(amt, 0.05), acct, cat,
        raw_desc=raw, entry="chip" if "AMZN" not in raw and "INTUIT" not in raw else "online",
        payment="credit_card" if "cc" in acct else "debit_card",
        network="Visa" if "joint_cc" in acct else "Mastercard",
        device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel="api", mcc="5812" if cat == "restaurants" else "5999",
        tags=tags,
    ))

# ---------------------------------------------------------------------------
# Venmo / Zelle (peer to peer)
# ---------------------------------------------------------------------------

for dt in random_dates_per_month(START, END, (0, 2)):
    if random.random() < 0.3:
        continue
    names = ["Sarah M.", "Kevin L.", "Tiffany R.", "Andre B.", "Lisa W."]
    name = random.choice(names)
    amt = round(random.uniform(15, 80), 2)
    is_credit = random.random() < 0.4
    ALL_TRANSACTIONS.append(make_txn(
        dt, f"Zelle {'from' if is_credit else 'to'} {name}", amt, "acct_joint_chk",
        "peer_to_peer", txn_type="transfer", credit=is_credit,
        raw_desc=f"ZELLE {'PAYMENT FROM' if is_credit else 'SEND TO'} {name.upper()}",
        entry="online", payment="ach_transfer", network="RTP",
        device=random.choice(["iPhone 15", "Galaxy S24"]),
        member_id=random.choice(["member_marcus", "member_jasmine"]),
        channel="mobile_app", mcc="0000",
    ))

# ---------------------------------------------------------------------------
# Sort all transactions and compute running balances per account
# ---------------------------------------------------------------------------

ALL_TRANSACTIONS.sort(key=lambda t: (t["account_id"], t["date"], t["time"]))

balances = {a["account_id"]: a["opening_balance"] for a in ACCOUNTS}
for t in ALL_TRANSACTIONS:
    aid = t["account_id"]
    if t["type"] == "credit":
        balances[aid] += t["amount"]
    else:
        balances[aid] -= t["amount"]
    t["running_balance"] = round(balances[aid], 2)


# ===========================================================================
# INVESTMENT DATA
# ===========================================================================

INVESTMENT_TRANSACTIONS = []

# ---------------------------------------------------------------------------
# Holdings definitions
# ---------------------------------------------------------------------------

MARCUS_401K_HOLDINGS = [
    {"ticker": "FXAIX", "name": "Fidelity 500 Index Fund", "allocation": 0.50, "asset_class": "us_large_cap"},
    {"ticker": "FSPSX", "name": "Fidelity International Index", "allocation": 0.15, "asset_class": "international"},
    {"ticker": "FSSNX", "name": "Fidelity Small Cap Index", "allocation": 0.10, "asset_class": "us_small_cap"},
    {"ticker": "FXNAX", "name": "Fidelity US Bond Index", "allocation": 0.20, "asset_class": "bonds"},
    {"ticker": "FDRXX", "name": "Fidelity Government Money Market", "allocation": 0.05, "asset_class": "money_market"},
]

JASMINE_401K_HOLDINGS = [
    {"ticker": "VFIAX", "name": "Vanguard 500 Index Fund Admiral", "allocation": 0.45, "asset_class": "us_large_cap"},
    {"ticker": "VTIAX", "name": "Vanguard Total Intl Stock Index Admiral", "allocation": 0.20, "asset_class": "international"},
    {"ticker": "VBTLX", "name": "Vanguard Total Bond Market Index Admiral", "allocation": 0.25, "asset_class": "bonds"},
    {"ticker": "VSCIX", "name": "Vanguard Small-Cap Index Institutional", "allocation": 0.10, "asset_class": "us_small_cap"},
]

IRA_HOLDINGS = [
    {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "allocation": 0.50, "asset_class": "us_total_market"},
    {"ticker": "VXUS", "name": "Vanguard Total International Stock ETF", "allocation": 0.20, "asset_class": "international"},
    {"ticker": "BND", "name": "Vanguard Total Bond Market ETF", "allocation": 0.15, "asset_class": "bonds"},
    {"ticker": "VNQ", "name": "Vanguard Real Estate ETF", "allocation": 0.10, "asset_class": "real_estate"},
    {"ticker": "VTIP", "name": "Vanguard Short-Term Inflation-Protected ETF", "allocation": 0.05, "asset_class": "tips"},
]

PLAN_529_HOLDINGS = [
    {"ticker": "GAAAX", "name": "Path2College Age-Based Aggressive", "allocation": 0.70, "asset_class": "target_allocation"},
    {"ticker": "GABAX", "name": "Path2College Age-Based Moderate", "allocation": 0.30, "asset_class": "target_allocation"},
]

BROKERAGE_HOLDINGS = [
    {"ticker": "VOO", "name": "Vanguard S&P 500 ETF", "allocation": 0.30, "asset_class": "us_large_cap"},
    {"ticker": "AAPL", "name": "Apple Inc.", "allocation": 0.12, "asset_class": "us_individual"},
    {"ticker": "MSFT", "name": "Microsoft Corp.", "allocation": 0.10, "asset_class": "us_individual"},
    {"ticker": "SCHD", "name": "Schwab U.S. Dividend Equity ETF", "allocation": 0.20, "asset_class": "us_dividend"},
    {"ticker": "QQQ", "name": "Invesco QQQ Trust", "allocation": 0.15, "asset_class": "us_growth"},
    {"ticker": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "allocation": 0.08, "asset_class": "emerging_markets"},
    {"ticker": "GLD", "name": "SPDR Gold Shares", "allocation": 0.05, "asset_class": "commodities"},
]

CRYPTO_HOLDINGS = [
    {"ticker": "BTC", "name": "Bitcoin", "allocation": 0.70, "asset_class": "cryptocurrency"},
    {"ticker": "ETH", "name": "Ethereum", "allocation": 0.30, "asset_class": "cryptocurrency"},
]

# Simulated monthly returns by asset class (very approximate 2025 scenario)
MONTHLY_RETURNS = {
    "us_large_cap":    [0.020, -0.012, 0.015, 0.008, 0.018, -0.005, 0.022, 0.010, -0.018, 0.014, 0.025, 0.012],
    "us_total_market": [0.018, -0.010, 0.014, 0.009, 0.016, -0.003, 0.020, 0.008, -0.015, 0.012, 0.022, 0.011],
    "us_small_cap":    [0.025, -0.020, 0.018, 0.005, 0.022, -0.010, 0.028, 0.012, -0.025, 0.018, 0.030, 0.015],
    "us_individual":   [0.030, -0.015, 0.020, 0.010, 0.025, -0.008, 0.032, 0.015, -0.020, 0.022, 0.028, 0.018],
    "us_growth":       [0.028, -0.018, 0.022, 0.012, 0.020, -0.010, 0.030, 0.014, -0.022, 0.020, 0.032, 0.016],
    "us_dividend":     [0.015, -0.008, 0.012, 0.006, 0.014, -0.002, 0.016, 0.008, -0.012, 0.010, 0.018, 0.008],
    "international":   [0.012, -0.008, 0.010, 0.015, 0.008, 0.005, 0.012, -0.005, -0.010, 0.008, 0.015, 0.010],
    "emerging_markets":[0.015, -0.012, 0.008, 0.018, 0.010, 0.008, 0.015, -0.008, -0.015, 0.012, 0.018, 0.012],
    "bonds":           [0.003, 0.005, 0.002, 0.004, 0.003, 0.004, 0.002, 0.003, 0.005, 0.003, 0.002, 0.004],
    "tips":            [0.002, 0.003, 0.002, 0.003, 0.002, 0.003, 0.002, 0.002, 0.004, 0.002, 0.002, 0.003],
    "real_estate":     [0.010, -0.005, 0.008, 0.012, 0.006, 0.002, 0.010, -0.003, -0.008, 0.008, 0.012, 0.006],
    "money_market":    [0.004, 0.004, 0.004, 0.004, 0.003, 0.003, 0.003, 0.004, 0.004, 0.004, 0.003, 0.004],
    "target_allocation":[0.015, -0.008, 0.012, 0.010, 0.014, -0.002, 0.018, 0.006, -0.012, 0.010, 0.020, 0.010],
    "commodities":     [0.005, 0.010, -0.005, 0.008, 0.012, -0.008, 0.005, 0.015, 0.010, -0.005, 0.008, 0.005],
    "cryptocurrency":  [0.08, -0.05, 0.12, -0.03, 0.06, -0.08, 0.15, 0.04, -0.10, 0.07, 0.20, 0.05],
}


def gen_investment_txns(account_id, holdings, opening_balance, contributions, member_id):
    """
    Generate monthly contribution + growth transactions for an investment account.
    contributions = list of (date, amount, source_desc) or a function returning them.
    Returns list of investment transactions and monthly snapshots.
    """
    txns = []
    snapshots = []

    # Initialize holdings with opening balance
    current_holdings = []
    for h in holdings:
        val = opening_balance * h["allocation"]
        current_holdings.append({
            "ticker": h["ticker"],
            "name": h["name"],
            "asset_class": h["asset_class"],
            "allocation": h["allocation"],
            "value": round(val, 2),
            "cost_basis": round(val * 0.92, 2),  # assume some unrealized gain
            "shares": round(val / random.uniform(50, 300), 4),
        })

    total_value = sum(ch["value"] for ch in current_holdings)

    for month_idx in range(12):
        month_num = month_idx + 1
        month_start = date(2025, month_num, 1)

        # Monthly contributions
        for contrib_date, contrib_amt, contrib_desc in contributions:
            if contrib_date.month == month_num:
                # Allocate contribution across holdings
                for ch in current_holdings:
                    buy_amt = round(contrib_amt * ch["allocation"], 2)
                    ch["value"] += buy_amt
                    ch["cost_basis"] += buy_amt
                    price = ch["value"] / ch["shares"] if ch["shares"] > 0 else random.uniform(50, 300)
                    new_shares = round(buy_amt / price, 4)
                    ch["shares"] += new_shares

                    txns.append({
                        "investment_transaction_id": tid(),
                        "date": contrib_date.isoformat(),
                        "account_id": account_id,
                        "member_id": member_id,
                        "type": "contribution",
                        "sub_type": "buy",
                        "ticker": ch["ticker"],
                        "name": ch["name"],
                        "shares": new_shares,
                        "price_per_share": round(price, 4),
                        "amount": buy_amt,
                        "fees": 0,
                        "description": contrib_desc,
                    })

        # Apply monthly returns
        for ch in current_holdings:
            ret = MONTHLY_RETURNS.get(ch["asset_class"], [0.005]*12)[month_idx]
            ret = ret * (1 + random.uniform(-0.3, 0.3))  # add noise
            gain = round(ch["value"] * ret, 2)
            ch["value"] = round(ch["value"] + gain, 2)

            if ret != 0:
                txns.append({
                    "investment_transaction_id": tid(),
                    "date": date(2025, month_num, 28).isoformat() if month_num != 2 else date(2025, 2, 28).isoformat(),
                    "account_id": account_id,
                    "member_id": member_id,
                    "type": "market_change",
                    "sub_type": "unrealized_gain" if gain >= 0 else "unrealized_loss",
                    "ticker": ch["ticker"],
                    "name": ch["name"],
                    "shares": 0,
                    "price_per_share": round(ch["value"] / ch["shares"], 4) if ch["shares"] > 0 else 0,
                    "amount": gain,
                    "fees": 0,
                    "description": f"Market {'gain' if gain >= 0 else 'loss'} for {month_start.strftime('%B %Y')}",
                })

        # Quarterly dividends (Mar, Jun, Sep, Dec)
        if month_num in (3, 6, 9, 12):
            for ch in current_holdings:
                if ch["asset_class"] in ("bonds", "us_dividend", "real_estate", "us_large_cap", "us_total_market", "money_market"):
                    div_rate = {"bonds": 0.01, "us_dividend": 0.008, "real_estate": 0.007, "us_large_cap": 0.003, "us_total_market": 0.003, "money_market": 0.01}.get(ch["asset_class"], 0.003)
                    div = round(ch["value"] * div_rate, 2)
                    if div > 0:
                        ch["value"] += div
                        ch["cost_basis"] += div  # reinvested
                        price = ch["value"] / ch["shares"] if ch["shares"] > 0 else 100
                        new_shares = round(div / price, 4)
                        ch["shares"] += new_shares

                        txns.append({
                            "investment_transaction_id": tid(),
                            "date": date(2025, month_num, 15).isoformat(),
                            "account_id": account_id,
                            "member_id": member_id,
                            "type": "dividend",
                            "sub_type": "reinvested",
                            "ticker": ch["ticker"],
                            "name": ch["name"],
                            "shares": new_shares,
                            "price_per_share": round(price, 4),
                            "amount": div,
                            "fees": 0,
                            "description": f"Dividend reinvestment - {ch['name']}",
                        })

        # Monthly snapshot
        total_value = sum(ch["value"] for ch in current_holdings)
        total_cost = sum(ch["cost_basis"] for ch in current_holdings)
        snapshots.append({
            "date": date(2025, month_num, 28).isoformat() if month_num != 2 else date(2025, 2, 28).isoformat(),
            "account_id": account_id,
            "total_value": round(total_value, 2),
            "total_cost_basis": round(total_cost, 2),
            "total_gain_loss": round(total_value - total_cost, 2),
            "total_gain_loss_pct": round((total_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0,
            "holdings": [
                {
                    "ticker": ch["ticker"],
                    "name": ch["name"],
                    "asset_class": ch["asset_class"],
                    "shares": ch["shares"],
                    "price_per_share": round(ch["value"] / ch["shares"], 4) if ch["shares"] > 0 else 0,
                    "market_value": ch["value"],
                    "cost_basis": ch["cost_basis"],
                    "gain_loss": round(ch["value"] - ch["cost_basis"], 2),
                    "gain_loss_pct": round((ch["value"] - ch["cost_basis"]) / ch["cost_basis"] * 100, 2) if ch["cost_basis"] > 0 else 0,
                    "allocation_pct": round(ch["value"] / total_value * 100, 2) if total_value > 0 else 0,
                }
                for ch in current_holdings
            ],
        })

    return txns, snapshots


# --- Marcus 401(k) contributions (biweekly, $157 employee + $104.62 match) ---
marcus_401k_contribs = []
for dt in biweekly_dates(START, END, date(2025, 1, 10)):
    marcus_401k_contribs.append((dt, 157.00 + 104.62, "Biweekly 401(k) contribution + employer match"))
m401k_txns, m401k_snaps = gen_investment_txns(
    "acct_marcus_401k", MARCUS_401K_HOLDINGS, 42800.00, marcus_401k_contribs, "member_marcus"
)
INVESTMENT_TRANSACTIONS.extend(m401k_txns)

# --- Jasmine 401(k) contributions (biweekly, $124.62 employee + $62.31 match) ---
jasmine_401k_contribs = []
for dt in biweekly_dates(START, END, date(2025, 1, 3)):
    jasmine_401k_contribs.append((dt, 124.62 + 62.31, "Biweekly 401(k) contribution + employer match"))
j401k_txns, j401k_snaps = gen_investment_txns(
    "acct_jasmine_401k", JASMINE_401K_HOLDINGS, 28500.00, jasmine_401k_contribs, "member_jasmine"
)
INVESTMENT_TRANSACTIONS.extend(j401k_txns)

# --- Jasmine Roth IRA ($250/month) ---
ira_contribs = []
for dt in monthly_dates(START, END, 5):
    ira_contribs.append((dt, 250.00, "Monthly Roth IRA contribution"))
ira_txns, ira_snaps = gen_investment_txns(
    "acct_jasmine_ira", IRA_HOLDINGS, 11200.00, ira_contribs, "member_jasmine"
)
INVESTMENT_TRANSACTIONS.extend(ira_txns)

# --- 529 Plans ---
# Darius: $100/mo
d529_contribs = [(dt, 100.00, "Monthly 529 contribution") for dt in monthly_dates(START, END, 1)]
d529_txns, d529_snaps = gen_investment_txns(
    "acct_529_darius", PLAN_529_HOLDINGS, 18750.00, d529_contribs, "member_darius"
)
INVESTMENT_TRANSACTIONS.extend(d529_txns)

# Amara: $100/mo
a529_contribs = [(dt, 100.00, "Monthly 529 contribution") for dt in monthly_dates(START, END, 1)]
a529_txns, a529_snaps = gen_investment_txns(
    "acct_529_amara", PLAN_529_HOLDINGS, 9200.00, a529_contribs, "member_amara"
)
INVESTMENT_TRANSACTIONS.extend(a529_txns)

# Elijah: $75/mo
e529_contribs = [(dt, 75.00, "Monthly 529 contribution") for dt in monthly_dates(START, END, 1)]
e529_txns, e529_snaps = gen_investment_txns(
    "acct_529_elijah", PLAN_529_HOLDINGS, 2400.00, e529_contribs, "member_elijah"
)
INVESTMENT_TRANSACTIONS.extend(e529_txns)

# --- Brokerage ($200/mo + a few individual trades) ---
brok_contribs = [(dt, 200.00, "Monthly brokerage contribution") for dt in monthly_dates(START, END, 10)]
brok_txns, brok_snaps = gen_investment_txns(
    "acct_brokerage", BROKERAGE_HOLDINGS, 6800.00, brok_contribs, "member_marcus"
)

# Add a few individual stock trades
individual_trades = [
    (date(2025, 2, 10), "AAPL", "Apple Inc.", "buy", 5, 188.50),
    (date(2025, 4, 22), "NVDA", "NVIDIA Corp.", "buy", 2, 850.00),
    (date(2025, 7, 15), "AAPL", "Apple Inc.", "sell", 3, 210.25),
    (date(2025, 9, 8), "AMZN", "Amazon.com Inc.", "buy", 3, 192.00),
    (date(2025, 11, 5), "NVDA", "NVIDIA Corp.", "sell", 1, 980.00),
]
for dt, ticker, name, side, shares, price in individual_trades:
    brok_txns.append({
        "investment_transaction_id": tid(),
        "date": dt.isoformat(),
        "account_id": "acct_brokerage",
        "member_id": "member_marcus",
        "type": "trade",
        "sub_type": side,
        "ticker": ticker,
        "name": name,
        "shares": shares,
        "price_per_share": price,
        "amount": round(shares * price, 2),
        "fees": round(random.uniform(0, 0.50), 2),
        "description": f"{'Buy' if side == 'buy' else 'Sell'} {shares} shares of {ticker}",
    })

INVESTMENT_TRANSACTIONS.extend(brok_txns)

# --- Crypto ---
crypto_contribs = []
# Small DCA buys every month + a couple spot buys
for dt in monthly_dates(START, END, 15):
    crypto_contribs.append((dt, 50.00, "Monthly DCA purchase"))
crypto_txns, crypto_snaps = gen_investment_txns(
    "acct_crypto", CRYPTO_HOLDINGS, 1250.00, crypto_contribs, "member_marcus"
)

# Extra crypto trades
crypto_extras = [
    (date(2025, 3, 5), "BTC", "Bitcoin", "buy", 0.005, 68000.00),
    (date(2025, 5, 20), "ETH", "Ethereum", "buy", 0.15, 3200.00),
    (date(2025, 8, 12), "BTC", "Bitcoin", "sell", 0.003, 75000.00),
    (date(2025, 11, 25), "SOL", "Solana", "buy", 2, 145.00),
]
for dt, ticker, name, side, shares, price in crypto_extras:
    crypto_txns.append({
        "investment_transaction_id": tid(),
        "date": dt.isoformat(),
        "account_id": "acct_crypto",
        "member_id": "member_marcus",
        "type": "trade",
        "sub_type": side,
        "ticker": ticker,
        "name": name,
        "shares": shares,
        "price_per_share": price,
        "amount": round(shares * price, 2),
        "fees": round(random.uniform(0.50, 5.00), 2),
        "description": f"{'Buy' if side == 'buy' else 'Sell'} {shares} {ticker}",
    })

INVESTMENT_TRANSACTIONS.extend(crypto_txns)

# Sort investment transactions
INVESTMENT_TRANSACTIONS.sort(key=lambda t: (t["account_id"], t["date"]))

# ---------------------------------------------------------------------------
# Monthly summaries
# ---------------------------------------------------------------------------

def compute_monthly_summaries():
    summaries = []
    for month_idx in range(12):
        month_num = month_idx + 1
        month_str = date(2025, month_num, 1).strftime("%Y-%m")

        month_txns = [t for t in ALL_TRANSACTIONS if t["date"].startswith(month_str)]

        income = sum(t["amount"] for t in month_txns if t["type"] == "credit" and t["transaction_type"] in ("salary", "deposit") and "transfer" not in t.get("category", ""))
        expenses = sum(t["amount"] for t in month_txns if t["type"] == "debit" and t["transaction_type"] not in ("transfer", "payment") and t["category"] not in ("transfer", "credit_card_payment"))
        transfers_out = sum(t["amount"] for t in month_txns if t["type"] == "debit" and t["category"] == "transfer")

        # Category breakdown (debits only, non-transfer)
        cats = {}
        for t in month_txns:
            if t["type"] == "debit" and t["category"] not in ("transfer", "credit_card_payment"):
                cats[t["category"]] = cats.get(t["category"], 0) + t["amount"]
        cats = {k: round(v, 2) for k, v in sorted(cats.items(), key=lambda x: -x[1])}

        summaries.append({
            "month": month_str,
            "total_income": round(income, 2),
            "total_expenses": round(expenses, 2),
            "net_cashflow": round(income - expenses, 2),
            "savings_rate_pct": round((income - expenses) / income * 100, 2) if income > 0 else 0,
            "transaction_count": len(month_txns),
            "expense_by_category": cats,
        })

    return summaries

MONTHLY_SUMMARIES = compute_monthly_summaries()

# ---------------------------------------------------------------------------
# Assemble all snapshots
# ---------------------------------------------------------------------------

ALL_SNAPSHOTS = {
    "acct_marcus_401k": m401k_snaps,
    "acct_jasmine_401k": j401k_snaps,
    "acct_jasmine_ira": ira_snaps,
    "acct_529_darius": d529_snaps,
    "acct_529_amara": a529_snaps,
    "acct_529_elijah": e529_snaps,
    "acct_brokerage": brok_snaps,
    "acct_crypto": crypto_snaps,
}

# Year-end net worth summary
def compute_net_worth():
    # Get final balances from transactions
    checking_savings = {aid: balances[aid] for aid in balances if any(
        a["account_type"] in ("checking", "savings", "high_yield_savings")
        for a in ACCOUNTS if a["account_id"] == aid
    )}

    # Investment account values (last snapshot)
    investment_values = {}
    for acct_id, snaps in ALL_SNAPSHOTS.items():
        if snaps:
            investment_values[acct_id] = snaps[-1]["total_value"]

    # Credit card balances (liabilities)
    cc_balances = {aid: balances[aid] for aid in balances if any(
        a["account_type"] == "credit_card" for a in ACCOUNTS if a["account_id"] == aid
    )}

    assets = sum(checking_savings.values()) + sum(investment_values.values())
    liabilities = abs(sum(min(0, v) for v in cc_balances.values()))

    # Estimated mortgage remaining
    mortgage_remaining = 245000
    # Estimated car loans remaining
    car_loans = 18500 + 12200

    return {
        "as_of": "2025-12-31",
        "assets": {
            "cash_and_checking": {k: round(v, 2) for k, v in checking_savings.items()},
            "investments": {k: round(v, 2) for k, v in investment_values.items()},
            "total_liquid_assets": round(sum(checking_savings.values()) + sum(investment_values.values()), 2),
        },
        "liabilities": {
            "credit_cards": {k: round(abs(min(0, v)), 2) for k, v in cc_balances.items()},
            "mortgage_estimated": mortgage_remaining,
            "auto_loans_estimated": car_loans,
            "total_liabilities": round(liabilities + mortgage_remaining + car_loans, 2),
        },
        "net_worth": round(assets - liabilities - mortgage_remaining - car_loans, 2),
    }

NET_WORTH = compute_net_worth()

# ===========================================================================
# WRITE OUTPUT FILES
# ===========================================================================

def write_json(filename, data):
    path = OUT_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Wrote {path.name}: ", end="")
    if isinstance(data, list):
        print(f"{len(data)} records")
    elif isinstance(data, dict):
        print(f"{len(data)} top-level keys")

print("Generating Thompson family financial data (2025)...\n")

write_json("family_members.json", FAMILY)
write_json("accounts.json", ACCOUNTS)
write_json("transactions.json", ALL_TRANSACTIONS)
write_json("investment_transactions.json", INVESTMENT_TRANSACTIONS)
write_json("holdings_snapshots.json", ALL_SNAPSHOTS)
write_json("monthly_summaries.json", MONTHLY_SUMMARIES)
write_json("net_worth.json", NET_WORTH)

print(f"\nTotal banking transactions: {len(ALL_TRANSACTIONS)}")
print(f"Total investment transactions: {len(INVESTMENT_TRANSACTIONS)}")
print(f"Year-end net worth: ${NET_WORTH['net_worth']:,.2f}")
print("\nDone!")
