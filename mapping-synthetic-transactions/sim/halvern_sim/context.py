"""public_services_context.csv and assumptions.csv."""
import csv

from . import config as C
from .day_c import SCHOOL_COST, LUNCH_COST, BFAST_COST
from .day_b import TRANSIT_COST


def context_rows(sim):
    """One row per agency or service: approximate daily operating cost behind the day (annual budget / 365)."""
    PP, HH = sim.persons, sim.households
    n = len(PP)
    k = n / 100000.0

    def pc(per_capita_year):
        return per_capita_year * n / 365.0
    k12 = [0, 0, 0]
    for p in PP:
        if p.student == "public_k12" and p.school is not None:
            d = p.school.district
            k12[0 if d in ("D1", "D2", "D3") else 1 if d == "D4" else 2] += 1
    sd = sim.by_kind["school_district"]
    hs = sum(1 for p in PP if p.student == "head_start")
    pk = sum(1 for p in PP if p.student == "public_prek")
    ss = sum(p.ss for p in PP) * 12 / 365.0
    ssi = sum(p.ssi for p in PP) * 12 / 365.0
    va = sum(p.va for p in PP) * 12 / 365.0
    ui = sum(p.ui for p in PP) * 12 / 365.0
    snap = sum(H.snap for H in HH) * 12 / 365.0
    wic = sum(H.wic for H in HH) * 12 / 365.0
    tanf = sum(H.tanf for H in HH) * 12 / 365.0
    mcaid = sum(1 for p in PP if p.cov in ("medicaid", "medicare_medicaid_dual"))
    mcare = sum(1 for p in PP if p.cov.startswith("medicare"))
    mkt = sum(1 for p in PP if p.cov == "marketplace")
    vets = sum(1 for p in PP if p.vet)
    sub = sum(1 for H in HH if H.subsidized)
    jail = sum(1 for H in HH if H.gq == "jail")
    rides = sum(1 for r in sim.rows if r[3] == "transportation.transit_ride")
    eitc = sum(r[13] for r in sim.rows if r[3] == "income.refundable_tax_credit")
    R = []

    def add(name, level, cost, fund, note):
        R.append([name, level, int(round(cost, -2)) if cost >= 1000 else int(round(cost)), fund, note])
    for i, o in enumerate(sd):
        if i < 3 and k12[i]:
            add("%s (K-12 schools)" % o.name, "local", k12[i] * SCHOOL_COST[i] * 180 / 365.0, "state aid, local property tax, federal Title I and IDEA",
                "%d students x $%.2f per school day x 180 days / 365; itemized per student in records.csv" % (k12[i], SCHOOL_COST[i]))
    add("School meal programs", "federal", sum(k12) * (.6 * LUNCH_COST + .3 * BFAST_COST) * 180 / 365.0, "USDA reimbursements, family payments", "itemized per meal in records.csv")
    add("Head Start", "federal", hs * 88.0 * 170 / 365.0, "HHS grant", "%d children; itemized per child-day" % hs)
    add("State pre-kindergarten", "state", pk * 47.5 * 180 / 365.0, "state lottery and general funds", "%d children; itemized per child-day" % pk)
    add(sim.by_kind["community_college"][0].name, "state", pc(640), "state appropriation, tuition, Pell grants", "not itemized; tuition payments appear when due")
    add("Police (city departments and county sheriff patrol)", "local", pc(455), "city and county general funds", "not itemized")
    add("Fire and rescue", "local", pc(205), "city and county general funds", "not itemized")
    add("Halvern County EMS", "local", pc(66), "county EMS levy, patient billing", "calls are itemized (ambulance transports and no-transport responses)")
    add("911 dispatch", "local", pc(29), "county general fund, phone surcharge", "not itemized")
    add("County jail", "local", jail * 124.0, "county general fund", "%d people held; itemized per person-day" % jail)
    add("Courts, prosecution and public defense", "state", pc(165), "state and county funds, fines and fees", "court appearances and fine payments are itemized")
    add("State prisons (Halvern's per-capita share)", "state", pc(270), "state general fund", "not itemized; residents in state prison are outside the city")
    add("Streets, signals and streetlights (city and county)", "local", pc(285), "local sales and property tax, state gas-tax share", "not itemized")
    add("State highways (Halvern's per-capita share)", "state", pc(430), "state and federal fuel taxes", "not itemized")
    add("Water and sewer utilities", "local", pc(540), "customer rates", "household bills are itemized on their due dates")
    add("Trash and recycling", "local", pc(98), "customer fees", "bills itemized on due dates")
    add("Stormwater and drainage", "local", pc(37), "stormwater fee", "not itemized")
    add("Halvern Area Transit (bus and paratransit)", "local", rides * TRANSIT_COST * 1.12, "local sales tax, state aid, federal formula funds, fares",
        "%d boardings today x $%.2f, plus paratransit; itemized per ride" % (rides, TRANSIT_COST))
    add("Public libraries", "local", pc(50), "city and county property tax, state aid", "visits, computer sessions and story times are itemized")
    add("Parks and recreation", "local", pc(110), "city general fund, program fees", "organized programs are itemized; ordinary park use is not")
    add("Public health department", "local", pc(88), "state and federal public health grants, county funds", "clinic visits and WIC appointments are itemized")
    add("Senior services and meals", "local", pc(34), "Older Americans Act funds, county funds, donations", "meals are itemized")
    add("Child welfare and county social services", "state", pc(215), "state and federal funds", "not itemized")
    add("Benefits administration (SNAP, Medicaid, TANF eligibility offices)", "state", pc(92), "state and federal administrative funds", "renewal paperwork is itemized as unpaid time")
    add("Workforce career center and unemployment insurance administration", "state", pc(41), "federal WIOA and UI administrative grants", "career center visits are itemized")
    add("General government (administration, assessor, elections, clerks)", "local", pc(320), "property and sales tax", "permits and license fees are itemized")
    add("Code enforcement and animal control", "local", pc(19), "city general fund", "not itemized")
    add("Halvern Housing Authority and rent subsidies", "federal", sub * 1010.0 * 12 / 365.0, "HUD housing assistance payments", "%d subsidized households; landlord subsidy payments post on the 1st" % sub)
    add("Medicaid and CHIP (medical spending for residents)", "state", mcaid * 9400.0 / 365.0, "federal and state Medicaid funds", "%d enrollees; today's claims are itemized" % mcaid)
    add("Medicare (medical spending for residents)", "federal", mcare * 16900.0 / 365.0, "payroll tax, premiums, general revenue", "%d enrollees; today's claims are itemized" % mcare)
    add("Marketplace premium tax credits", "federal", mkt * 4300.0 / 365.0, "federal general revenue", "%d enrollees; paid to insurers monthly" % mkt)
    add("Veterans health care", "federal", vets * .5 * 14500.0 / 365.0, "VA appropriations", "%d veterans, about half enrolled" % vets)
    add("Social Security (retirement, survivors, disability)", "federal", ss, "payroll tax, trust funds", "monthly benefits / 30.4; deposits itemized on each person's pay date")
    add("Supplemental Security Income", "federal", ssi, "federal general revenue", "paid on the 1st")
    add("VA disability compensation and pensions", "federal", va, "federal general revenue", "paid on the 1st")
    add("SNAP food benefits", "federal", snap, "USDA", "issuances itemized on each household's issuance day (1st to 10th)")
    add("WIC", "federal", wic * 1.35, "USDA", "food benefits plus clinic costs")
    add("TANF cash assistance", "state", tanf, "federal block grant and state funds", "issued on days 1 to 3")
    add("Unemployment insurance benefits", "state", ui, "employer payroll taxes", "weekly payments itemized")
    add("Refundable tax credits (EITC, Child Tax Credit), annual average", "federal", n * 0.165 / 2.4 * 3100.0 / 365.0, "federal general revenue",
        "paid once a year in tax season; today's refunds are itemized (today alone: $%s in refundable credits)" % "{:,.0f}".format(eitc))
    add("Child care subsidies (CCDF)", "state", pc(38), "federal block grant and state match", "parent copays itemized; provider payments appear as business records")
    add("Energy assistance (LIHEAP)", "federal", pc(14), "federal block grant", "pledges itemized when made")
    add("U.S. Postal Service (local operations)", "federal", pc(245), "postage", "self-funded; counter purchases itemized")
    add("National defense (Halvern's per-capita share)", "federal", pc(2700), "federal general revenue and borrowing", "national spending shown for scale; not local operations")
    add("Interest on federal debt (per-capita share)", "federal", pc(3000), "federal general revenue and borrowing", "national spending shown for scale")
    return R


def write_context(sim, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["agency_or_service", "level", "daily_operating_cost_estimate", "main_funding_source", "notes"])
        w.writerows(context_rows(sim))


def assumption_rows(sim, S=None):
    P = sim.cfg
    A = []

    def a(name, value, why, src="estimate"):
        A.append([name, value, why, src])
    a("simulation date", sim.cal["iso"], "weekday early in the month during tax-refund season", "prompt parameter")
    a("random seed", P["RANDOM_SEED"], "population and day are reproducible from the seed", "prompt parameter")
    a("full-city households", C.FULL_CITY_HOUSEHOLDS, "sized so households plus group quarters give about 100,000 residents at 2.36 people per household", "design choice")
    a("group-quarters residents", "nursing homes 370; assisted living 80; college dorms 1,100; county jail 240; group homes 110; shelter 100; residential treatment 50",
      "about 2% of residents, near the Census group-quarters share; each resident is a one-person unit", "estimate")
    a("district shares", "D1 31%, D2 20%, D3 22%, D4 13%, D5 8%, D6 6%", "31/55/14 urban, suburban, rural split from Pew; division inside bands as given", "anchor (prompt)")
    a("household type mix", "married with children 17.0%; married without 26.4%; living alone 27.2%; single parent 6.6%; roommates 5.8%; cohabiting with children 2.5%; multigenerational 4.7%; adult child at home 8.6%; other family 1.1%",
      "modeled on national household composition and adjusted by district", "estimate")
    a("residents with jobs", "48% of residents", "about 48,000 jobs among about 100,000 residents", "anchor (prompt)")
    a("industry mix", "21 sectors at the shares in the prompt", "fitted by iterative proportional fitting over education, sex, age and district affinities", "anchor (prompt)")
    a("out-commuters", "5% of wage workers", "prompt asks to keep commuting across the city line small", "design choice")
    a("in-commuters", "4.5% of positions at Halvern employers", "prompt asks to keep commuting across the city line small", "design choice")
    a("occupation wages", "full-time base wages by occupation x %.2f" % C.WAGE_SCALE, "base wages follow national occupational pay; the scale sets median household income near $78,000 in 2027 dollars", "estimate")
    a("poverty guideline 2027", "$%d plus $%d per additional person" % (C.POVERTY_BASE, C.POVERTY_STEP), "2026 HHS guideline carried forward for inflation", "estimate")
    a("ALICE survival budget", "$36,000 one adult; +$15,500 per added adult; +$21,000 per child under 5; +$12,000 per older child; +$2,500 all-senior; district cost index 0.88 to 1.08; scaled by %.3f" % sim.alice_scale,
      "scale solved so 41.5% of households fall below the threshold", "anchor-driven (United For ALICE: roughly 4 in 10)")
    a("$400 emergency coverage", "able if liquid funds are at least ${:,.0f} or $400 is free on a card paid in full".format(sim.liq_mult),
      "threshold solved so 63% of adults qualify; many people with a few hundred dollars would still not spend it on an emergency", "anchor-driven (Fed SHED 2025: 63%)")
    a("opening balances", "checking median 0.10 / 0.20 / 0.80 of monthly net income for poverty / ALICE / above; savings 0.02 / 0.10 / 2.2 months; households carrying card debt hold a quarter of that",
      "sets who can absorb a bill and who overdrafts", "estimate")
    a("autopay readiness", "80% / 90% / 97% of poverty / ALICE / above households keep enough in checking for autopay bills due today", "the rest become the day's overdrafts and returned payments", "estimate")
    a("unbanked and underbanked", "unbanked 16% / 4.5% / 0.6% and underbanked 28% / 20% / 7% of poverty / ALICE / above households; 1.5x unbanked for limited-English households",
      "pattern of the FDIC household survey", "estimate")
    a("credit cards", "held by 45% / 72% / 93% of wallets; 62% / 58% / 34% of holders carry a balance", "sets credit use, interest charges and the $400 measure", "estimate")
    a("Social Security average retired-worker benefit", "$%.0f a month" % C.SS_AVG_RETIRED, "SSA estimate for January 2027 after the 3.6% cost-of-living adjustment", "SSA announcement, October 2026")
    a("Social Security average disabled-worker benefit", "$%.0f a month" % C.SS_AVG_DISABLED, "SSA estimate after the 2027 adjustment", "SSA announcement, October 2026")
    a("SSI federal benefit rate", "$%.0f individual" % C.SSI_FBR, "2027 rate", "SSA announcement, October 2026")
    a("Medicare Part B premium", "$%.2f a month" % C.PART_B_PREMIUM, "2026 Medicare Trustees projection for 2027; CMS had not published the final figure when this was built", "projection")
    a("Medicare Part B deductible", "$%.0f" % C.PART_B_DEDUCTIBLE, "2026 Medicare Trustees projection for 2027", "projection")
    a("Social Security payment schedule", "3rd of the month for pre-May-1997 beneficiaries, people who also get SSI, and people whose Medicare premium the state pays; otherwise 2nd, 3rd or 4th Wednesday by birth day; SSI on the 1st",
      "SSA payment calendar; March 3, 2027 is a first Wednesday, so only the 3rd-of-month group is paid", "SSA rules")
    a("SNAP maximum allotments", "$306 / $562 / $808 / $1,023 for 1 to 4 people; minimum $25; shelter cap $769", "USDA fiscal year 2027 cost-of-living adjustments", "USDA, August 2026")
    a("SNAP issuance schedule", "days 1 to 10 by case", "states stagger issuance; the fictional state uses ten days", "design choice")
    a("SNAP participation", "about 11% of residents", "eligible households take up at 50% to 86% depending on age and children", "estimate")
    a("tax refunds on the day", "17% of EITC households with children and about 1% of other filers receive a federal refund", "refunds with refundable credits are released in a wave from late February into early March", "estimate from IRS filing-season patterns")
    a("refund-transfer products", "24% of EITC refunds; $190 to $420 preparation plus $45 to $65 transfer fee", "fees are deducted before the refund reaches the filer", "estimate")
    a("sales tax", "%.1f%% on taxable goods and prepared food" % (100 * C.SALES_TAX), "near the national average combined rate; groceries, prescriptions, most services and motor fuel are not taxed at the register", "estimate")
    a("income tax withholding", "federal 3.5%% to 16%% of gross by wage less 1.8 points per child; state %.1f%%" % (100 * C.STATE_INCOME_TAX * .9), "stand-in for withholding tables in a national-average state", "estimate")
    a("payroll tax", "7.65% employee and 7.65% employer, plus about 1.1% employer unemployment taxes", "statutory FICA rates", "statute; unemployment tax share estimated")
    a("pay frequency", "weekly 27%, biweekly 43%, semimonthly 19%, monthly 11% overall, varied by sector; paydays 62% Friday, 9% Wednesday", "BLS pay-frequency shares; weekday split estimated", "estimate")
    a("purchase frequency", "everyday purchase rates x %.2f" % P["PURCHASE_FREQ"], "calibrated so adults make about 43 payments a month", "anchor-driven (Fed payment diary 2026)")
    a("cash propensity", "38%% of purchases under $5 falling to 4%% over $100, scaled by age, income, district and banking status, x %.2f" % P["CASH_MULT"], "calibrated so cash is about 14% of payments", "anchor-driven (Fed payment diary 2026)")
    a("gasoline price", "$%.2f a gallon" % P["GAS_PRICE"], "regular unleaded, early 2027", "estimate")
    a("public school cost", "$%.2f / $%.2f / $%.2f per pupil per school day by district; 2.05x for students with disabilities" % tuple(SCHOOL_COST), "about $18,600 a year over 180 days", "estimate from Census school finance trend")
    a("school meals", "lunch costs $%.2f, breakfast $%.2f; paid prices $3.25 to $3.50 and $2.00 to $2.10; reduced $0.40 and $0.30" % (LUNCH_COST, BFAST_COST), "near federal reimbursement levels", "estimate")
    a("Head Start and pre-K", "$88.00 and $47.50 per child-day", "annual per-child funding over the program year", "estimate")
    a("transit", "$%.2f operating cost per boarding; fare $1.75, reduced $0.85; monthly pass $56" % TRANSIT_COST, "mid-size bus system", "estimate")
    a("other imputed service costs", "library visit $9.60; computer session $13.40; story time $11.80; senior meal $12.60; home-delivered meal $14.20; shelter night $74; jail day $124; EMS transport $1,250; EMS response $448; public health clinic visit $118; WIC appointment $48; career center visit $66; free tax preparation $245; legal aid consult $315; paratransit ride $58",
      "budget divided by units of service for agencies of this size", "estimate")
    a("medical prices", "office visit $138, specialist $215, urgent care $188, emergency visit median $1,650, dialysis $305, home health visit $172; paid at 60% (Medicaid) to 125% (self-pay) of base by payer",
      "allowed amounts; billed charges are not modeled separately", "estimate")
    a("prescriptions", "generic cash price median $28, brand $520; plans pay on 45% / 82% of cash price; copays by coverage", "amount_gross shows the cash price, with copay and plan payment beside it", "estimate")
    a("health care use", "doctor visits 1.8 to 7.5 a year by age; emergency visits 0.42 per person a year; about 24 admissions a day", "national ambulatory and hospital use rates", "estimate")
    a("vital and moving rates", "births 10.7 and deaths 9.2 per 1,000 a year; marriages about 6 and divorces 2.4 per 1,000; 9 household moves and 4.4 eviction filings a day", "national rates applied to 100,000 residents; counts rounded at random to the nearest whole event", "estimate")
    a("overdraft", "13% / 5% of non-affluent / affluent accounts opted in; fee $25 to $34; returned-payment fee $15 to $35", "sets how short accounts fail", "estimate")
    a("ATM fees", "22% of withdrawals out of network (47% rural, 57% online-bank customers); $5.50 to $7.00 combined", "bank deserts raise out-of-network use", "estimate")
    a("small-dollar credit", "payday loans $200 to $500 at $15 to $17.50 per $100; title loans 25% a month; pawn 22% a month; earned-wage advances $40 to $150 for $2.99 to $5.99", "typical storefront terms", "estimate")
    a("remittances", "1.7% to 3% of immigrant households send $80 to $400 on the day; fees $2 to $10; 1% federal excise on cash-funded transfers", "the excise follows the 2025 federal law as understood here; verify before relying on it", "estimate")
    a("person-to-person payments", "4.45% of adults send one today; 13% of receipts are cashed out instantly for 1.75%", "about 1.3 a month per adult", "estimate")
    a("card interest and late fees", "21% to 30% APR posted monthly; late fee $30 to $41", "revolving balances only", "estimate")
    a("card processing", "credit 2.4% to 3.1%, debit 0.7% to 1.2%, plus $0.10 a transaction; delivery platforms keep 15% to 30%", "merchant-side costs in business records", "estimate")
    a("payroll tax deposits", "36% of employers with 30 or more staff deposit on a Wednesday; 24% to 30% of a pay period's payroll", "semiweekly deposit rule: Wednesday covers the prior Wednesday-to-Friday paydays", "estimate")
    a("Medicaid work-hours reporting", "monthly report for covered adults 19 to 64 without young children", "assumes the fictional state applied the 2025 federal requirement on its default start date", "assumption")
    a("incidents on the day", "state benefits portal down 10:40 to 13:25; card readers down 17:05 to 17:50 at one grocery store; a bus short on a trunk route 07:15 to 08:20", "ordinary-day disruptions; edit in PARAMS", "design choice")
    a("language and disability frictions", "18% of agency and clinic encounters for limited-English households; 6% of in-person trips for people with mobility or vision disabilities; 30% of phone calls for people with hearing disabilities",
      "applied by a fixed rule so results are reproducible", "estimate")
    a("benefit-limit trade-offs", "0.45% of variable-schedule workers in benefit households turn down hours on the day; 22% of working SNAP households see a cut at recertification", "represents benefit cliffs", "estimate")
    a("value of time", "median hourly wage of Halvern workers" + (" ($%.2f)" % S["time_value"] if S else ""), "used only to rank frictions in summary.md", "derived")
    a("property tax", "escrow share 16% to 24% of a mortgage payment; direct payers 0.45% a day in March and September", "installments due April 1 and October 1 in the fictional counties", "design choice")
    a("housing costs", "base rent $1,790 (D1), $1,560 (D2), $2,080 (D3), $1,380 (D4), $1,010 (D5), $930 (D6), scaled by size and income; subsidized tenants pay 30% of income", "2027 dollars", "estimate")
    a("child care", "$290 / $255 / $215 a week for infants, toddlers, preschoolers; subsidized families pay 7% of income", "center rates; home-based care 20% less", "estimate")
    a("vehicle purchases", "0.085% of households buy a vehicle on the day", "about 40 sales a day for a city this size", "estimate")
    a("scam attempts", "0.42% of adults (0.67% of those 65 and older) deal with one; 1.4% lose money", "frequency of fraud contacts", "estimate")
    a("consumer expenditure shares", "housing 33.9%, transportation 16.5%, food 13.0%, insurance and pensions 12.4% (2025); healthcare 7.9%, entertainment 4.6%, apparel 2.5%, education 2.0% (2024)",
      "comparison targets in summary.md", "BLS Consumer Expenditure Surveys")
    return A


def write_assumptions(sim, path, S=None):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["assumption", "value", "rationale", "source_or_estimate"])
        w.writerows(assumption_rows(sim, S))
