# Prompt: Generate one simulated day of transactions for Halvern, a synthetic American city

Copy everything below the line into Fable. Edit the PARAMETERS block first.

---

## PARAMETERS (edit these)

- SIM_DATE: Wednesday, March 3, 2027 (a weekday early in the month, during tax-refund season)
- WEATHER: ordinary early-spring day, no storm
- SCALE: full city (about 100,000 residents in about 40,000 households)
- MODE: GENERATOR if you can write and run code; otherwise BATCH
- BATCH_SIZE (BATCH mode only): 25 households per response
- RANDOM_SEED: 20270303
- OUTPUT: CSV files, UTF-8, comma-separated, header row, one file per table

## Your role

You are a synthetic-data designer and economic simulation modeler. Build a realistic, internally consistent dataset of every transaction, public service encounter and everyday "job" attempted in one day in Halvern, a fictional US city whose population mirrors the United States as a whole.

This dataset will be mined for small, practical projects that improve daily life at the margins. So it matters as much to capture friction, failure, time costs, fees and unpaid effort as to capture spending.

The core idea: **every transaction is a job to be done.** A purchase, a bill, a benefit deposit, a library visit, a form, a wait, a declined card or a wasted trip is a record of someone trying to get something done. Each record says what the job was, who paid, who else paid, what it cost in time and effort, and whether it worked.

## Hard rules

1. Everything is fictional. Invent all names for people, businesses and agencies. Do not use real company names or real people. Real places only inspired the districts; never name them in the data.
2. National, not local. Population mix, incomes, industries and payment habits follow US national patterns, not Georgia or any single metro.
3. Internal consistency. A person's transactions must fit their household, income, job, age, health, district, vehicle, bank account status and schedule. Money cannot appear from nowhere: account balances, benefits, paychecks and debts should roughly reconcile.
4. Include the unglamorous and the rare. Cover low-income and high-income lives, the old and the young, rural and urban, the healthy and the sick, workers and non-workers.
5. Label estimates. Any figure you estimate rather than derive from the anchors below goes in an `assumptions.csv` file with a one-line rationale.
6. No moralizing. Record what happens, not judgments about people's choices.

## City context

### Population
- About 100,000 residents in about 40,000 households, modeled on the US Census Bureau's American Community Survey microdata, weighted to the whole country.
- Draw whole households so that ages, incomes, jobs, disability, language, housing tenure and commute mode stay consistent inside each home.
- Include the full range of US household types: married couples with and without children, single parents, adults living alone (many of them older), roommates, multigenerational households, adult children living with parents, and people in group quarters (nursing homes, college dorms, a small jail).
- Include people with no bank account, people who rely on prepaid cards or cash, recent immigrants, veterans, people with disabilities, unpaid family caregivers, students, retirees, gig workers, seasonal farmworkers and small-business owners.

### Districts (share of residents)
| Code | District | Share | Character |
|---|---|---|---|
| D1 | Downtown and core neighborhoods | 31% | Dense, transit-served, renters, government offices, night shifts |
| D2 | Inner suburbs | 20% | Older housing and apartments, immigrant gateways, airport and service jobs |
| D3 | Outer suburbs | 22% | New-build subdivisions, car-dependent, big-box retail, long commutes |
| D4 | Satellite city | 13% | Historic downtown, regional hospital, county seat, mixed old and new industry |
| D5 | Rural town | 8% | County seat of a few thousand, dollar stores, thin services, long drives |
| D6 | Open country | 6% | Farms, scattered homes, well water, distance to everything |

The 31/55/14 urban, suburban and rural split comes from Pew Research Center's county classification. How the 55% and 14% bands divide into districts is a design choice.

### Economy
About 48,000 Halvern residents hold jobs, distributed to match the 2025 national industry mix (BLS Employment Projections):

| Sector | Share of jobs |
|---|---|
| Health care and social assistance | 13.7% |
| State and local government (including public schools) | 12.1% |
| Retail trade | 9.1% |
| Accommodation and food services | 8.3% |
| Manufacturing | 7.4% |
| Professional, scientific and technical services | 6.3% |
| Self-employed | 5.8% |
| Administrative and support services | 5.3% |
| Construction | 4.9% |
| Finance and insurance | 4.0% |
| Transportation and warehousing | 3.9% |
| Other services (repair, salons, religious organizations) | 3.9% |
| Wholesale trade | 3.6% |
| Private educational services | 2.4% |
| Federal government | 1.7% |
| Information | 1.7% |
| Arts, entertainment and recreation | 1.6% |
| Management of companies | 1.5% |
| Real estate | 1.4% |
| Agriculture, forestry and fishing | 0.9% |
| Utilities and mining | 0.7% |

Some residents commute out of Halvern and some outsiders commute in. Keep both small and note them.

Create the organizations these jobs belong to: a regional hospital and clinics, a public school district and a few private schools, a community college, grocery chains and independent groceries, dollar stores, big-box stores, gas stations, fast food and sit-down restaurants, a manufacturing plant, distribution warehouses, banks, a credit union, check-cashers and a payday lender, churches, a public library system, a transit agency, city and county governments, a courthouse, a driver-license office, utilities, farms and a packing shed, and many small businesses.

### Calibration anchors
Hit these within reason and report how close you got:

- **Payments:** in the Federal Reserve's 2026 Diary of Consumer Payment Choice (2025 data), consumers made about 47 payments per month: about 16 by credit card, 15 by debit card and 6.5 in cash (14% of payments). Cash is 19% of payments for people 55 and older, 10% for ages 25 to 54 and 6% under 25; 21% in rural areas and about 12 to 13% in urban and suburban areas. Rural residents make fewer payments overall (about 42 a month vs. 53 urban). Five of six cash payments are under $25.
- **Financial fragility:** in the Fed's 2025 household survey (SHED), 63% of adults would cover a $400 emergency expense with cash or its equivalent.
- **Working but struggling:** roughly 4 in 10 households are below United For ALICE's survival-budget threshold, meaning in poverty or employed but unable to afford basics.
- **Spending mix:** household spending by category should roughly follow the BLS Consumer Expenditure Survey. Housing is the largest category, then transportation, food and health care.
- **Life events:** births, deaths, marriages, divorces, move-ins and move-outs at national daily rates for a city of 100,000. State your rate assumptions.

## How to represent government and third-party payers

Do not leave government out. Represent it in three ways.

**1. Money flowing in (transfers).** Record these as income or benefit records from a government party to a person or household:
- Social Security retirement and disability, paid on the schedule that applies to SIM_DATE by birth date. Some long-time recipients are paid on the 3rd; Supplemental Security Income arrives on the 1st.
- SNAP (food benefits) loaded onto EBT cards on a staggered state schedule; WIC; TANF cash; unemployment insurance; VA benefits; child support passed through the state.
- Tax refunds, including Earned Income Tax Credit and Child Tax Credit refunds arriving by direct deposit or on prepaid cards. This is tax-refund season, so include them.

**2. Services delivered at little or no cost to the user (public service encounters).** Record every encounter as a record with:
- `amount_paid_by_user` (often 0)
- `amount_paid_by_third_party`, with `third_party_payer` naming the program
- `imputed_public_cost`: your estimate of what the service costs to provide, which goes in assumptions.csv
- `funding_level`: federal, state, local, mixed, private or philanthropic

Include, at minimum: a public school day for every enrolled child (one record per student, imputed per-pupil daily cost), free and reduced-price school meals, library visits, checkouts and computer sessions, public transit rides (the fare paid plus the subsidy), public health clinic visits, emergency department visits including uncompensated care, EMS calls, parks and recreation programs, senior center meals, and Head Start and pre-K.

**3. Health care with layered payers.** For each medical encounter, record what the patient paid at the point of service (copay, deductible or self-pay) and what Medicare, Medicaid, a private insurer or the VA paid or will pay. Medicare Part B premiums are deducted from Social Security deposits; show the gross and net amounts. Prescriptions show the cash price, insurance payment and copay.

**4. Taxes and background services.** Add `sales_tax` to every taxable purchase. Attach payroll withholding and FICA to every payroll record. Record property tax and escrow payments when they fall on SIM_DATE.

Do not create a record for every streetlight, road mile, water main or police patrol. Instead, write a `public_services_context.csv` file: one row per agency or service with its approximate daily operating cost and main funding source, so analysts can see the full public budget behind the day.

## What to cover

Each household's day should include whatever its members would realistically do. Across the city, the dataset must include all of the following, at believable frequencies:

- **Income:** payroll, by direct deposit, paper check or paycard; tips; gig-app payouts; self-employment receipts; Social Security; pensions; benefits; child support; family transfers; remittances received
- **Housing:** rent (including late rent and partial payments), mortgages, HOA dues, renters and home insurance, home repair
- **Utilities and connectivity:** electricity, gas, water, trash, internet, phone, including shutoff notices and reconnection fees
- **Transportation:** gas, EV charging, car payments, insurance, repairs, tires, registration, tolls, parking, rideshare, transit fares, bike repair, a car that won't start
- **Food:** groceries (SNAP and WIC purchases included), dollar store, convenience store, farmers market, fast food, coffee, sit-down restaurants, delivery apps, school lunch, office catering
- **Health:** pharmacy, copays, Medicare and Medicaid claims, dental, vision, therapy, dialysis, home health visits, over-the-counter medicine, medical debt payments
- **Children and education:** child care, after-school programs, private school tuition, college tuition and fees, student loans, school supplies, field trip fees, youth sports
- **Money services:** ATM withdrawals, overdraft and late fees, check cashing, money orders, payday and title loans, buy-now-pay-later installments, credit card payments, person-to-person app transfers, prepaid card reloads, pawn
- **Discretionary and luxury:** clothing, electronics, streaming and subscriptions, entertainment, travel bookings, a designer handbag, a boat payment, a country-club bill, fine dining, a jewelry purchase, investment contributions
- **Civic and legal:** court fines and fees, driver-license and registration fees, permits, voter-registration updates, notary fees, immigration filing fees, funeral costs
- **Giving and faith:** church offerings, online donations, GoFundMe contributions, gifts to family
- **Business-to-business:** restaurants buying from wholesalers, payroll runs, rent and utilities for businesses, farm sales to the packer, contractors buying materials, card-processing fees, a small business waiting on a late invoice
- **Non-monetary jobs:** appointments, waiting on hold, filling out a benefits renewal, caregiving visits, school pickup, returns and disputes, searching for a ride, looking for work, a job interview
- **Failures:** declined cards, insufficient funds, a closed office, a website outage, missing documents, out-of-stock items, a missed bus, a no-show contractor, a benefits renewal returned for a missing signature. Link each retry to its original attempt.

## Output files

### households.csv
`household_id, district, weight, household_type, size, annual_income, income_source_mix, alice_status (poverty|alice|above), banked_status (banked|underbanked|unbanked), housing_tenure, monthly_housing_cost, vehicles, internet_at_home (yes|no|mobile_only), primary_language, notes`

### persons.csv
`person_id, household_id, age, birth_cohort, sex, race_ethnicity, relationship_to_head, education, disability (none|type), health_coverage, employment_status, occupation, employer_org_id, industry_sector, union_member (yes|no), work_schedule (fixed|variable|night|none), pay_cadence (weekly|biweekly|semimonthly|monthly|irregular|none), caregiver_for (person_ids or none), benefits_received`

### organizations.csv
`org_id, name, org_type (business|nonprofit|government|religious|financial), sector, district, size_employees, accepts (payment methods), hours, notes`

### records.csv (one row per transaction, encounter or job attempt)
`record_id, timestamp_local, record_type, job_category, job_statement, actor_person_id, household_id, from_party_id, to_party_id, beneficiary_person_id, district, channel, payment_method, amount_gross, amount_paid_by_user, amount_paid_by_third_party, third_party_payer, funding_level, imputed_public_cost, sales_tax, fee_type, fee_amount, time_minutes, wait_minutes, travel_miles, travel_mode, outcome, friction_tags, lens_tags, related_record_id, narrative`

Controlled vocabularies:
- `record_type`: purchase, bill_payment, income, benefit_issuance, benefit_redemption, transfer, tax, b2b, public_service_encounter, insurance_claim, non_monetary_job, failed_attempt
- `channel`: in_person, online, app, phone, mail, automatic
- `payment_method`: cash, debit, credit, prepaid, ebt_snap, ebt_cash, wic, check, ach, p2p_app, bnpl, money_order, paycard, payroll_deduction, insurance, none
- `outcome`: completed, partial, declined, abandoned, rescheduled, failed
- `friction_tags` (semicolon-separated): wait, distance, no_transit, hours_mismatch, missing_document, language, disability_access, digital_barrier, fee, insufficient_funds, pending_hold, benefits_cliff, eligibility_confusion, out_of_stock, outage, caregiving_conflict, schedule_volatility, scam_attempt, price_spike, paperwork, repeat_trip, other
- `lens_tags` (semicolon-separated; which perspective would flag this record): consumer_finance, labor, aging, farmworker, land_use, disability, rural, housing, health_cost, education, small_business, public_finance, family_care, digital_access

`job_statement` uses the form: "When [situation], I want to [motivation], so I can [outcome]." Write it from the actor's point of view, in plain words.

`narrative` is one short sentence of context, for example: "Paid at the counter in quarters because the card reader was down."

### public_services_context.csv
`agency_or_service, level (federal|state|local), daily_operating_cost_estimate, main_funding_source, notes`

### assumptions.csv
`assumption, value, rationale, source_or_estimate`

### summary.md
Totals and checks: record counts by type and district; spending by category vs. Consumer Expenditure Survey shares; cash share vs. the payment diary; share of households with at least one failed attempt; total time spent on non-monetary jobs; total fees paid by income group; public dollars delivered as transfers vs. services; and the 10 frictions that cost the most combined time and money, with the household types they hit hardest.

## How to work

### If MODE = GENERATOR
1. Write a Python simulator that builds the households, persons and organizations tables from the anchors above. Generate each household's day from rule-based behavior: schedules, pay and benefit dates, needs by life stage, district distances, payment-method habits by age, income and banked status, and failure probabilities by friction type.
2. Use RANDOM_SEED so the run can be reproduced.
3. Generate the full city. Expect several hundred thousand records; report the actual count.
4. Write `job_statement` and `narrative` text from templates with variation. Then hand-write rich text for a stratified sample of 500 records covering every district, record type and income group, and flag those rows with `narrative` starting "[detailed]".
5. Validate: run the calibration checks, report the results in summary.md, and adjust parameters until the checks are within reason.
6. Deliver the CSV files and the simulator code. Include a README explaining how to change SIM_DATE, run storm or shock scenarios, and move the city forward in time.

### If MODE = BATCH
1. First response: write organizations.csv, then a stratified roster of 400 sample households and their persons (each household carrying a `weight` so that 400 households represent about 40,000), plus assumptions.csv. Make sure the sample includes every district, household type and income group, and the rare cases listed above.
2. Each later response: generate the complete day of records for the next BATCH_SIZE households in roster order, plus the business-to-business and public-service records their activity implies. Continue record_id numbering. End each response with "Next: households X–Y" and wait for me to say "continue."
3. After the last batch, write public_services_context.csv and summary.md.
4. Keep everything consistent across batches. If you need to fix an earlier record, write it in a corrections block instead of silently changing it.

## Quality bar

Before delivering, check your work like a skeptical demographer, a payments economist and a social worker would:
- Does each household's day add up in time? No one should be in two places at once or work 30 hours.
- Does the money add up? Are balances, paychecks, benefits and bills plausible for that household's income?
- Do low-income, older, rural, disabled and limited-English residents meet the frictions they actually face, without being reduced to stereotypes?
- Are high-income lives and luxury spending present at realistic frequency?
- Is government visible in every form: transfers in, services delivered, taxes out and payers in the background?
- Would a reader looking at 20 random records believe they came from a real American day?
