# Halvern, Wednesday March 3, 2027: one simulated day

Seed 20270303, weather ordinary, scale 1.00. Everything here is synthetic. Figures marked *anchor* come from the prompt; the rest are labeled estimates (see assumptions.csv).

## What was generated

| Table | Rows |
|---|---|
| records.csv | 201,753 |
| households.csv | 43,450 (41,400 households plus 2,050 one-person group-quarters units) |
| persons.csv | 99,694 |
| organizations.csv | 1,672 |

367 distinct job categories. 500 rows carry hand-written text (narrative starts with "[detailed]").

## Records by type and district

| record_type | D1 | D2 | D3 | D4 | D5 | D6 | total |
|---|---|---|---|---|---|---|---|
| purchase | 24,866 | 14,921 | 16,327 | 12,672 | 5,602 | 3,821 | 78,209 |
| bill_payment | 9,301 | 5,617 | 7,532 | 4,046 | 2,417 | 1,627 | 30,540 |
| income | 2,132 | 1,295 | 1,299 | 864 | 505 | 431 | 6,526 |
| benefit_issuance | 1,141 | 929 | 481 | 570 | 396 | 215 | 3,732 |
| benefit_redemption | 483 | 290 | 192 | 191 | 134 | 87 | 1,377 |
| transfer | 2,684 | 1,598 | 1,687 | 1,117 | 670 | 525 | 8,281 |
| tax | 1,663 | 1,106 | 1,338 | 790 | 376 | 295 | 5,568 |
| b2b | 851 | 637 | 673 | 458 | 221 | 90 | 2,930 |
| public_service_encounter | 15,157 | 9,058 | 6,388 | 4,350 | 2,747 | 2,253 | 39,953 |
| insurance_claim | 1,679 | 1,236 | 1,053 | 880 | 508 | 321 | 5,677 |
| non_monetary_job | 3,808 | 2,838 | 2,846 | 1,887 | 1,097 | 725 | 13,201 |
| failed_attempt | 2,112 | 1,190 | 892 | 847 | 421 | 297 | 5,759 |
| **all** | **65,877** | **40,715** | **40,708** | **28,672** | **15,094** | **10,687** | **201,753** |

## Calibration against the anchors

| Check | Target | Simulated | Note |
|---|---|---|---|
| Residents | about 100,000 | 99,694 | includes 2,050 people in group quarters |
| Households | about 40,000 | 41,400 | excludes group quarters |
| District shares (D1 to D6) | 31 / 20 / 22 / 13 / 8 / 6 % | 30.5 / 19.7 / 21.6 / 14.3 / 7.9 / 6.0 % | share of residents |
| Residents with jobs | about 48,000 | 47,728 | 2,253 commute out; about 2,352 positions at Halvern employers are filled by in-commuters |
| Industry mix | BLS shares in the prompt | largest gap 0.2 points | full table below |
| Payments per adult per month | about 43 | 44.3 | 112,116 payments by adults today x 30.4 days; definition below |
| Cash share of payments | about 14% | 14.3% | by count; 3.3% by value |
| Cash higher for 55+ | yes | 17.5% vs 12.4% under 55 | |
| Cash higher at lower incomes | yes | poverty 37.2%, ALICE 17.8%, above 10.3% | |
| Cash higher in rural districts | yes | rural 16.8%, suburban 13.2%, urban core 15.1% | |
| Adults who would cover a $400 emergency with cash or equivalent | 63% | 63.0% | threshold solved at $2,654 in liquid funds, or $400 free on a card paid in full |
| Households below the ALICE survival budget | roughly 4 in 10 | 41.5% | 10.0% in poverty plus 31.5% ALICE |
| Median household income | not anchored | $78,019 | 2027 dollars; estimate |
| Births | 2.9 a day | 3 | 10.7 per 1,000 residents a year |
| Deaths | 2.5 a day | 3 | 9.2 per 1,000 a year |
| Marriage licenses | 1.2 a weekday | 0 | about 6 per 1,000 a year, light on Wednesdays |
| Divorce filings | 0.7 a weekday | 0 | 2.4 per 1,000 a year |
| Household moves | about 9 a day | 9 | 8% of residents move in a year; move-ins recorded |
| Hospital admissions | about 24 a day | 22 | plus 110 people already inpatients |

A payment here follows the Federal Reserve diary's idea: a purchase, bill or person-to-person payment made by an adult, by any instrument including EBT. It leaves out payroll deductions, credit-card bill payments (the purchases were already counted), ATM withdrawals and transfers between a person's own accounts.

### Payment instruments

| Instrument | Share of payments | Share of value |
|---|---|---|
| credit | 36.1% | 23.0% |
| debit | 31.8% | 18.8% |
| cash | 14.3% | 3.3% |
| ach | 9.2% | 46.6% |
| prepaid | 4.7% | 0.6% |
| p2p_app | 2.7% | 2.8% |
| check | 1.2% | 4.6% |
| money_order | 0.0% | 0.3% |
| ebt_cash | 0.0% | 0.0% |
| bnpl | 0.0% | 0.0% |

### Industry mix of residents' jobs

| Sector | Target % | Simulated % |
|---|---|---|
| Health care and social assistance | 13.7 | 13.6 |
| State and local government (including public schools) | 12.1 | 12.2 |
| Retail trade | 9.1 | 9.1 |
| Accommodation and food services | 8.3 | 8.2 |
| Manufacturing | 7.4 | 7.4 |
| Professional, scientific and technical services | 6.3 | 6.3 |
| Self-employed | 5.8 | 5.7 |
| Administrative and support services | 5.3 | 5.5 |
| Construction | 4.9 | 4.7 |
| Finance and insurance | 4.0 | 4.0 |
| Transportation and warehousing | 3.9 | 3.7 |
| Other services (repair, salons, religious organizations) | 3.9 | 3.9 |
| Wholesale trade | 3.6 | 3.5 |
| Private educational services | 2.4 | 2.4 |
| Federal government | 1.7 | 1.8 |
| Information | 1.7 | 1.8 |
| Arts, entertainment and recreation | 1.6 | 1.6 |
| Management of companies | 1.5 | 1.5 |
| Real estate | 1.4 | 1.5 |
| Agriculture, forestry and fishing | 0.9 | 0.9 |
| Utilities and mining | 0.7 | 0.7 |

## Spending mix against the Consumer Expenditure Survey

Out-of-pocket consumer spending recorded today: $10,416,131. Shares are compared with the BLS Consumer Expenditure Survey (2025 shares for the four largest components, 2024 for the rest).

| Category | CES share | Today's share | Today's dollars |
|---|---|---|---|
| housing | 33.9% | 40.4% | $4,212,620 |
| transportation | 16.5% | 15.0% | $1,565,971 |
| food | 13.0% | 14.6% | $1,524,392 |
| insurance pensions | 12.4% | 5.2% | $544,827 |
| healthcare | 7.9% | 7.6% | $787,002 |
| entertainment | 4.6% | 4.8% | $494,834 |
| contributions | 2.7% | 3.1% | $326,992 |
| apparel | 2.5% | 2.1% | $221,297 |
| education | 2.0% | 3.0% | $315,971 |
| personal care | 1.2% | 1.0% | $108,699 |
| alcohol | 0.8% | 0.5% | $47,402 |
| tobacco | 0.5% | 0.3% | $35,826 |
| misc | 2.0% | 2.2% | $230,299 |

Housing is the largest category, followed by transportation and food, as in the survey. A single day cannot match annual shares exactly: rent and mortgages bunch in the first days of the month, only about one worker in twenty is paid on a Wednesday the 3rd (so payroll-deducted Social Security and retirement contributions run low), and vehicle purchases are counted at full price on the day of sale. Recurring obligations spread over a month come to about $4,001,612 a day.

## Things that went wrong

- 6,896 records are failed attempts or ended declined, abandoned, failed or rescheduled; 1,943 later records are linked retries.
- 13.4% of households had at least one failed attempt (poverty 28.5%, ALICE 16.1%, above ALICE 9.5%).
- Card or account declines for insufficient funds: 811; technical declines: 641; declines during the card-reader outage at one grocery store: 81; overdrafts: 274; bounced autopays: 182.
- Purchases given up because nothing would cover them: 655. Prescriptions left at the counter over price: 84. Renewals stopped by the state portal outage: 6. Contractor no-shows: 9. Trips to a closed licensing office: 5.

## Unpaid time

13,201 non-monetary jobs took 16,736 hours in all (13 minutes per adult). Largest by time:

| Job | Hours |
|---|---|
| care_and_household.caregiving_at_home | 8,548 |
| care_and_household.caregiving_visit | 1,691 |
| care_and_household.school_dropoff | 1,267 |
| care_and_household.school_pickup | 1,247 |
| care_and_household.stayed_home_with_sick_child | 1,165 |
| work.job_applications_online | 1,050 |
| care_and_household.escort_to_appointment | 337 |
| civic_legal.jury_duty | 200 |
| civic_legal.court_appearance | 110 |
| discretionary.store_return | 100 |

## Fees by income group

| Group | Fee records | Fees paid | Per household | Fees as share of purchases and bills | Largest fee types |
|---|---|---|---|---|---|
| poverty | 806 | $16,103 | $3.05 | 2.99% | tax prep and refund transfer fees ($6,483), overdraft fee ($3,433), returned payment fee ($1,845), card convenience fee ($665) |
| alice | 2,712 | $84,837 | $6.27 | 3.02% | tax prep and refund transfer fees ($44,666), interest charge ($16,249), delivery and service fees ($3,880), overdraft fee ($3,037) |
| above | 4,663 | $130,008 | $5.28 | 1.52% | interest charge ($65,485), tax prep and refund transfer fees ($14,132), delivery and service fees ($9,153), commission yardage and checkoff ($8,731) |

Fees include overdraft, late, ATM, check-cashing, money-order, convenience, delivery, card-interest and loan finance charges recorded on the day.

## Public dollars

| Flow | Dollars today | Largest items |
|---|---|---|
| Transfers in (benefit issuances and refundable credits) | $7,782,595 | social security deposit $3,879,968, refundable tax credit $3,645,094, snap issuance $167,327, unemployment benefit $38,156, tanf cash issuance $26,630 |
| Tax refunds of people's own overpayments | $1,956,210 | federal and state refunds, not counted as transfers |
| Services delivered (public payers' share of encounters and claims) | $2,940,554 | public school day $1,495,220, medicare part b state buy in $394,488, hospital admission $221,152, prescription pickup $100,081, transit ride $78,755 |
| Taxes paid by households (withholding, payroll tax, property tax, sales tax) | $1,433,216 | payroll income tax withholding $621,076, payroll fica $352,721, property tax escrow $194,165, sales tax on purchases $132,796, property tax payment $104,136 |
| Taxes sent in by employers (matching payroll tax, deposits of earlier withholding) | $6,871,746 | federal payroll tax deposit $6,469,394, employer payroll taxes $402,352 |

Monthly benefits that post on other days are not in today's transfers: SSI and VA compensation arrived March 1, and most Social Security is paid on the second to fourth Wednesdays. Today's Social Security goes to people paid on the 3rd: long-time beneficiaries, people who also get SSI, and people whose Medicare premium the state pays. public_services_context.csv gives the daily cost of the services that are not itemized (police, roads, water, and so on).

## The ten costliest frictions

Time is valued at $25.82 an hour, the median hourly wage of Halvern workers. Money is fees plus wages lost. A record with several tags splits its cost among them.

| Friction | Records | Hours | Fees and lost wages | Combined cost | Household types hit hardest (per household) | Income group hit hardest |
|---|---|---|---|---|---|---|
| fee | 9,966 | 264 | $324,258 | $331,071 | multigen, single_parent | alice |
| distance | 6,971 | 8,359 | $5,226 | $221,046 | multigen, adult_child | above |
| wait | 3,770 | 2,452 | $1,951 | $65,272 | multigen, adult_child | poverty |
| schedule_volatility | 641 | 786 | $22,677 | $42,975 | cohab_kids, married_kids | alice |
| no_transit | 2,328 | 915 | $386 | $24,013 | group_quarters:college_dorm, cohab_kids | poverty |
| caregiving_conflict | 2,015 | 397 | $6,538 | $16,795 | single_parent, married_kids | alice |
| insufficient_funds | 4,468 | 396 | $6,414 | $16,637 | roommates, other_family | poverty |
| other | 1,473 | 91 | $0 | $2,352 | adult_child, married_kids | above |
| repeat_trip | 307 | 82 | $0 | $2,127 | other_family, adult_child | above |
| disability_access | 385 | 63 | $1 | $1,640 | married_nokids, multigen | alice |

## Consistency checks

- Time: the busiest person has 19.2 hours of work plus in-person activity; 0 people exceed 24 hours. In-person activities are scheduled into each person's free time, so no one is in two places at once.
- Money: opening balance plus inflows minus outflows equals closing balance for all but 0 households (household_ledger.csv). 266 checking accounts end the day overdrawn.
- Every payroll record has linked withholding and FICA records; every Social Security deposit with a Medicare premium has a linked deduction; retries point to the attempt that failed.
