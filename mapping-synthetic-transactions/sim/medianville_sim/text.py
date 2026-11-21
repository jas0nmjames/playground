"""Plain-language text for records: job statements ("When..., I want to..., so I can...") and one-line narratives.

Each kind maps to (action phrase, [job statements], [narratives]). Placeholders in braces come from the record's context.
A stratified sample of rows is later overwritten with hand-written text (see detailed_overrides.csv)."""
import re
from .text_lib import T

MISSING = {}
METHODS = {"cash": "cash", "debit": "the debit card", "credit": "a credit card", "prepaid": "the prepaid card", "check": "a check", "ach": "a bank transfer"}
OWN_FAIL = {"missed_bus", "car_wont_start", "grocery_item_out_of_stock", "sent_home_early", "shift_cancelled_short_notice", "missed_shift_for_sick_child",
            "late_or_missed_shift", "overdue_invoice_follow_up", "snap_benefits_stolen", "wic_item_rejected_at_register", "power_outage", "public_school_day",
            "repair_estimate_too_high", "check_not_cashed_yet", "appointment_rescheduled_no_free_time", "shutoff_notice_received", "eviction_notice_received",
            "card_charge_dispute", "online_order_return_dropoff", "payday_loan_rollover", "housing_case_management_meeting"}
FR_TEXT = {"insufficient_funds": "there was not enough money to cover it", "hours_mismatch": "the hours did not line up with a workday", "missing_document": "a required document was missing",
           "outage": "the system was down", "vehicle_lost": "the car was taken by the lender", "out_of_stock": "it was out of stock", "wait": "the wait was too long", "no_transit": "there was no way to get there",
           "paperwork": "the paperwork was not accepted", "digital_barrier": "it could only be done online", "caregiving_conflict": "nobody else could watch the family",
           "schedule_volatility": "the work schedule changed", "language": "nobody there spoke the language", "price_spike": "the price was higher than expected",
           "other": "it did not go through", "pending_hold": "a hold tied up the money", "eligibility_confusion": "the rules were not clear", "distance": "it was too far to get to today"}
TAIL = {"vehicle_lost": " No car today: the lender took it.", "language": " Needed help with the English-only forms.", "digital_barrier": " Done on a phone because there is no internet at home.",
        "disability_access": " The place was not set up for someone with a disability.", "distance": " A long drive each way.",
        "no_transit": " No bus goes there, so it took a ride from someone.", "pending_hold": " The money is on hold for a few days.",
        "price_spike": " It cost more than last time.", "out_of_stock": " One thing on the list was out.", "eligibility_confusion": " The rules were hard to follow."}
PURPOSE = {"commute": "the commute", "errand": "an errand", "groceries": "the grocery run", "class": "a class", "medical appointment": "a medical appointment",
           "job interview": "a job interview"}
REL = {"head": "family member", "spouse": "spouse", "unmarried_partner": "partner", "parent": "parent", "child": "child", "adult_child": "grown child",
       "grandchild": "grandchild", "sibling": "sibling", "other_relative": "relative", "roommate": "housemate", "resident": "relative", "child_in_law": "in-law"}
FAIL_NARR = {"public_school_day": ["Absent from {school}: {reason}.", "Not in class at {school} today; {reason}."]}
DEFAULT_REASON = {"social_security_office_visit": "the line outlasted the office hours and a return ticket was handed out",
                  "court_appearance": "the case was continued to another date", "sought_emergency_utility_help": "this month's assistance money was already spent",
                  "eviction_hearing": "the hearing went against the tenant", "energy_assistance_application": "the application could not be finished today",
                  "repair_request_to_landlord": "the office line went to voicemail", "p2p_transfer": "the linked account did not have enough to cover it"}
GEN = ("take care of {label}", ["When {label} comes due, I want to take care of it without losing the day, so I can get back to everything else."], ["{Label}."])


# v2 phase 5: statements and narratives that fit the person and the place. The v2 close reading found work talk from
# people who don't work, gas from households with no car, "support my church" at mosques and temples, and a
# self-employed stylist afraid of "losing my job". Each rule swaps in wording; the text draws its own random numbers,
# so no figure moves. (kind, test on who) -> (statements or None, narratives or None).
NO_WORK = {
    "fast_food": ["When everyone is hungry and we are still out, I want something cheap and fast, so I can get us fed without another stop.",
                  "When I do not feel like cooking, I want something hot and quick, so I can eat without a sink full of dishes."],
    "gas_fill_up": ["When the tank is near empty, I want to fill up, so I can get through the week's errands.",
                    "When I only have a few dollars until the next check, I want enough gas for the next trips, so I can keep driving.",
                    "When I pass the cheapest station, I want to top off, so I can avoid paying more later."],
    "haircut": ["When I am overdue for a cut, I want an hour in the chair, so I can feel like myself again."],
    "school_dropoff": ["When the bell is about to ring, I want the kids at the door, so I can get them there on time."],
    "car_repossessed": ["When I fall behind on the title loan, I want to keep the car, so I can still get to appointments and the store."],
    "car_disabled_by_lender": ["When I head out in the morning, I want the car to start, so I can get where I need to go."],
    "caregiving_at_home": ["When someone in my home cannot manage alone, I want to help with the day's needs, so I can keep them safe at home.",
                           "When care falls to me, I want to fit it around everything else, so I can keep the house running too."],
}
NO_WORK_NARR = {"school_dropoff": ["Car line at {school}.", "Dropped {n} at {school}."]}
NO_CAR = {"cash_tips": ["When the shift ends, I want my tips counted out, so I can buy groceries on the way home."],
          "gig_payout_instant": ["When I finish a shift of deliveries, I want today's earnings now, so I can cover tomorrow's costs."]}
SELF_EMP = {"missed_shift_for_sick_child": ["When my child is sick and there is no one else, I want to stay home without losing my customers, so I can take care of them."]}
FAITH = (("Masjid", "my mosque"), ("Islamic", "my mosque"), ("Mosque", "my mosque"), ("Synagogue", "my synagogue"), ("Beth ", "my synagogue"),
         ("Gurdwara", "the gurdwara"), ("Buddhist", "the center"), ("Hindu", "the temple"), ("Temple", "the temple"))
P2P_OWED = ("splitting", "paying a friend back", "buying a used item", "a share of rent")
SS_KIND = {"social security retirement": "Social Security retirement", "ssdi": "Social Security disability (SSDI)",
           "social security survivor": "Social Security survivor"}
COUNT = {1: "one child", 2: "two kids", 3: "three kids", 4: "four kids", 5: "five kids"}


def fit(kind, c, who, hh):
    """Statements and narratives that fit this person and place, or (None, None) to keep the template's own."""
    if kind == "church_offering":
        place = next((w for k, w in FAITH if k in c.get("org", "")), None)
        if place:
            return (["When I go to services, I want to give what I can, so I can support %s." % place],
                    ["Donation at {org}.", "Gift at {org} during the week's gathering."])
    if kind == "p2p_transfer" and c.get("why"):
        owed = c["why"].startswith(P2P_OWED)
        return ([T["p2p_transfer"][1][0 if owed else 1]], None)
    if who is not None:
        if who.emp == "self_employed" and kind in SELF_EMP:
            return SELF_EMP[kind], None
        if not who.works and kind in NO_WORK:
            return NO_WORK[kind], NO_WORK_NARR.get(kind)
    if hh is not None and not hh.vehicles and kind in NO_CAR:
        return NO_CAR[kind], None
    return None, None


class _D(dict):
    def __missing__(self, k):
        return ""


def _f(s, c):
    try:
        return s.format_map(c)
    except Exception:
        return s


def _cap(s):
    return s[:1].upper() + s[1:] if s else s


_KEEP_TO = ("place", "somewhere", "brought", "sent", "way", "time", "chance", "room", "money", "right", "enough")
_X_TO_V = re.compile(r"^((?:\S+ ){0,3}\S+) to (\w+)(.*)$")


def want_to(js):
    """Put a job statement into the exact form 'When ..., I want to ..., so I can ...'."""
    if ", I want to " in js or ", I want " not in js:
        return js
    head, rest = js.split(", I want ", 1)
    if ", so " not in rest:
        return js
    mot, tail = rest.split(", so ", 1)
    m = _X_TO_V.match(mot)
    if m and m.group(1).split()[-1] not in _KEEP_TO:
        mot = "%s %s%s" % (m.group(1), m.group(2), m.group(3))     # "it to clear" -> "have it clear"
    return "%s, I want to have %s, so %s" % (head, mot, tail)


def make(rng, kind, ctx, outcome, F, wait, fee, fee_type, who=None, hh=None):
    spec = T.get(kind)
    c = _D(ctx)
    if c.get("occ"):
        c["an_occ"] = ("an " if c["occ"][:1].lower() in "aeiou" else "a ") + c["occ"]
    if isinstance(c.get("n"), int) and kind in ("school_dropoff", "school_pickup", "pickup_arranged_with_someone_else"):
        c["n"] = COUNT.get(c["n"], "%d kids" % c["n"])
    if kind == "social_security_deposit" and c.get("kind"):
        c["kind"] = SS_KIND.get(c["kind"], c["kind"])
    if str(c.get("hrs")) in ("1", "1.0"):
        c["hrs_word"] = "1 hour"
    elif c.get("hrs"):
        c["hrs_word"] = "%s hours" % c["hrs"]
    c["label"] = kind.replace("_", " ")
    c["Label"] = _cap(c["label"])
    if c.get("org") == "Out-of-area employers":
        c["org"] = "an employer outside Medianville"
    elif c.get("org") == "Out-of-area suppliers":
        c["org"] = "a supplier outside Medianville"
    if ctx.get("purpose") in PURPOSE:
        c["purpose"] = PURPOSE[ctx["purpose"]]
    if "grade" in ctx:
        c["grade"] = "kindergarten" if ctx["grade"] in (0, "0") else "grade %s" % ctx["grade"]
    if "rel" in ctx:
        c["rel"] = REL.get(ctx["rel"], "relative")
    if spec is None:
        MISSING[kind] = MISSING.get(kind, 0) + 1
        spec = GEN
    act, jss, nss = spec
    alt_js, alt_ns = fit(kind, c, who, hh)
    jss, nss = alt_js or jss, alt_ns or nss
    js = _f(jss[0] if len(jss) == 1 else rng.choice(jss), c)
    act = _f(act, c)
    bad = outcome in ("declined", "abandoned", "failed", "rescheduled")
    if bad and kind not in OWN_FAIL:
        why = ctx.get("reason") or DEFAULT_REASON.get(kind) or next((FR_TEXT[t] for t in F if t in FR_TEXT), "it did not work out today")
        narr = _cap(rng.choice(["Tried to %s, but %s.", "Could not %s: %s.", "Set out to %s; %s."]) % (act, why))
        if outcome == "rescheduled":
            narr += rng.choice([" Will try again another day.", " Put off to another day.", ""])
        return want_to(js), narr
    if bad and kind in FAIL_NARR:
        return want_to(js), _cap(_f(rng.choice(FAIL_NARR[kind]), c))
    if kind == "transit_ride" and ctx.get("free"):
        nss = ["Rode the bus for {purpose} on a monthly pass.", "Bus ride for {purpose}; tapped the pass."]
    narr = _cap(_f(nss[0] if len(nss) == 1 else rng.choice(nss), c))
    tails = []
    if ctx.get("again"):          # carried runs: a retried bill (medianville_sim/carry.py)
        tails.append(" " + _cap(ctx["again"]) + ".")
    if ctx.get("debt"):
        tails.append(" The meal account was empty, so it went on the tab as a debt.")
    if ctx.get("waiver"):
        tails.append(" The fee was covered by a league scholarship.")
    if ctx.get("cut"):
        tails.append(" The new benefit is $%s a month lower because of a raise at work." % ctx["cut"])
    if ctx.get("deduct"):
        tails.append(" The preparer's fee will come out of the refund.")
    r = ctx.get("retry")
    if r:
        tails.append(" The first try was declined; %s went through." % METHODS[r] if r in METHODS else " Second attempt, %s." % r)
    if ctx.get("short"):
        tails.append(" Came up $%s short of the full amount." % ctx["short"])
    lt = ctx.get("later")
    if lt and lt not in ("0", "0.00", "0.0"):
        tails.append(" About $%s more will be billed later%s." % (lt, " (%s)" % ctx["later_why"] if ctx.get("later_why") else ""))
    if ctx.get("late") and ctx.get("late") != "1":
        tails.append(" Includes a $%s late fee." % ctx["late"])
    if ctx.get("hike"):
        tails.append(" The price had gone up since last time.")
    if ctx.get("split"):
        tails.append(" This covered what SNAP did not.")
    if fee and fee > 0 and "fee" not in narr.lower() and len(tails) < 2:
        tails.append(" Fee: $%.2f (%s)." % (fee, fee_type.replace("+", " and ").replace("_", " ").replace("atm", "ATM")))
    if wait and wait >= 25 and len(tails) < 2 and "wait" not in narr.lower() and str(wait) not in narr:
        tails.append(" Waited %d minutes." % wait)
    if len(tails) < 2 and kind not in OWN_FAIL:
        for t in F:
            if t in TAIL and rng.random() < .6:
                tails.append(TAIL[t])
                break
    return want_to(js), narr + "".join(tails[:2])
