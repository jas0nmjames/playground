# Medianville, March 3, 2027: real human evidence beside the synthetic day

> **Kept as written (first pass, November 17, 2026).** This is the research that came between v1 and v2: real accounts set beside the first run. It was written against v1's 500 hand-written records, so section 2 describes v1's gaps. v2 has since added most of them (overdraft fees, payday and title loans, shutoffs, medical debt, caregiving, aide no-shows, work reporting, SNAP interviews, benefits cliffs, lender shutoffs, scam losses, Direct Express, call-ins, H-2A workers); see the [data update plan](../reference/medianville-data-update-plan.md). The systems lens's district circumstances (`DW1`–`DW4` in `systems-lens/blocks.json`) were drafted from it and keep its `E`-row ids. Its files are all here: [`sources.csv`](sources.csv) (69), [`evidence.csv`](evidence.csv) (76) and [`quotes.csv`](quotes.csv) (25), from the [research prompt](research-prompt.md). No real person's words or record go into a Medianville record.

First pass, November 17, 2026. Companion files: `sources.csv` (69 sources), `evidence.csv` (76 findings), `quotes.csv` (25 quotes).

**How this pass was run.** The run's `records.csv` was not available, so the step that samples 20 records per friction used the 500 hand-written records in `detailed_sample_500.csv` instead. That sample is stratified by record type, not random, so it can show what kinds of records exist but not how often they happen. Quotes are held to under 15 words, with one quote per source, which is stricter than the prompt's 20-word limit. That is why there are 25 quotes rather than 60: many strong sources (the Fed, FDIC, NWLC, the Shift Project) publish figures but no first-person voices.

Sim references: **F1–F6** are the findings in the run record. **R-numbers** are records in the 500-record sample.

---

## 1. Scorecard

| # | Simulation finding | Verdict | Best evidence |
|---|---|---|---|
| F1 | 13.4% of households had a failed attempt (poverty 28.5%, ALICE 16.1%, above 9.5%) | **Direction confirmed; size can't be tested.** No source measures a daily failure rate. Every source agrees that failures pile up as income falls. | 77% of MARTA riders missed something important in a month (E043); procedural reasons were two-thirds or more of Medicaid disenrollments (E023); missed interviews drive up to half of SNAP denials (E025) |
| F2 | Unpaid jobs took 16,736 hours; home caregiving is half (about 8,368 hours) | **Probably far too low.** At AARP's rate (about 1 in 4 adults caring, 27 hours a week), Medianville's roughly 78,000 adults would give about 67,500 caregiving hours a day, about 8 times the simulated figure. That estimate assumes 78% of residents are adults. AARP hours are self-reported and run higher than time diaries, so check against the American Time Use Survey (ATUS) before changing the generator. | E048, E049 |
| F3 | Tax-prep and refund-transfer fees are the largest fee for poverty and ALICE households | **Plausible for a March refund day, but partly an artifact.** Medianville has no overdraft fees: none appear in the 500-record sample, and that should be confirmed in `records.csv`. Over a year, overdraft fees probably rival tax-time fees for these households. Also, only 1 of 20 refund deposits in the sample carries a prep fee, while about half of EITC claimants use paid preparers. That one fee took 41.9% of a small refund, about double PPI's upper range. | E001, E003, E008–E010 |
| F4 | Costliest frictions: fees, distance, waits, schedule volatility, no transit | **Confirmed in kind.** Missing: high-cost debt (title pawns, payday loans), utility arrears and shutoffs, medical debt, and home-care no-shows as their own category. | E011, E040, E041, E056, E019, E082 |
| F5 | Cash share 14.3% overall, 37.2% for poverty households, 16.8% rural | **Rural share runs low.** It is 16.8% against the payment diary's 21% target for rural areas. The high share for poverty households fits FDIC's finding that two-thirds of unbanked households use only cash. | E014; generator anchor |
| F6 | 63% could cover a $400 emergency | **Matches, but not an independent check.** Medianville was calibrated to this survey. | E016 |

---

## 2. What the simulation is missing (generator changes)

1. **Overdraft and NSF fees.** About 24% of households are charged at least one overdraft fee a year, and 9% of accounts pay 79% of all overdraft and NSF fees. The average overdraft fee is $26.77. Medianville records insufficient funds only as declines, 27 of them in the sample. Many of those should be paid as overdrafts with a fee instead, especially ACH drafts, checks and opted-in debit. A rough estimate (it assumes about 20 fees a year for the most frequent overdrafters) is about 150 overdraft fees a day in a city of 41,400 households. At that rate, a 500-record sample would contain fewer than one, so the sample can't settle this. Check `fee_type` in `records.csv`. (E008–E011, E013, E089)
2. **High-cost credit.** Payday borrowing (about 12 million people a year), auto title loans (about 2.5 million), pawn loans and check cashing are all absent from the sample. Georgia bans payday loans but allows title pawns at up to about 187.5% interest. Add new jobs `money_services.title_pawn_payment` and `money_services.payday_loan`, plus links to car repossession. (E018–E022, E015)
3. **Utility arrears and shutoffs.** One in six households is behind on utility bills, and utilities disconnected electric service about 13.5 million times in 2024. Scaled to Medianville, that is roughly 11–12 disconnections a day. Add shutoff notices, disconnections and reconnection fees. (E082)
4. **Medical debt.** 41% of adults have health care debt (57% with incomes under $40,000). Add medical-debt installment payments and care delayed because of debt. (E059, E060)
5. **Caregiving: hours and money.** Raise caregiving time, or confirm it against ATUS first. Add out-of-pocket caregiving costs, now about $11,508 a year on average. Caregiving records in the sample all cost $0. (E048, E049)
6. **Home-care no-shows.** Agencies report shifts they cannot fill many times a month. Raise the no-show rate for aide visits and link each no-show to a family member's lost work hours. (E053–E055)
7. **Work-reporting friction.** Medianville's two Medicaid work-hours reports took 12–16 minutes and went smoothly. Georgia's experience includes upload confusion, websites that go down, and worry among people whose hours change from week to week. Add failure and retry rates, and link them to `schedule_volatility`. (E026–E028, E031)
8. **SNAP interviews and renewals.** Add interview calls scheduled during work shifts and the churn that follows a missed one, including the agency's cost of about $80 per churn. (E024, E025)
9. **Benefits cliffs.** No sample record carries `benefits_cliff`. Add `work.raise_declined_benefits_cliff`, for example a roughly $200 raise that costs about $800 in benefits. (E066)
10. **Car as collateral.** Add a lender-disabled car as a failure type. One Southeast servicer disabled cars more than 5,200 times when the borrower was not in default. (E061–E063)
11. **Fraud losses.** The sample's only scam attempt was caught with no loss. Real losses among older adults are rare but very large: six-figure cases are 6% of reports and 70% of dollars lost. (E077)
12. **Benefit-card service failures.** Add Direct Express call-center failures for people who receive benefits on a card. (E079)
13. **Last-minute call-ins and open availability.** Add being called in on a day off and having to keep availability open as unpaid jobs. (E045, E047)
14. **Guest workers.** There are no H-2A households in the sample, although Georgia hosted about 43,000 H-2A workers in 2024. Nationally they are a small group, so add a few seasonal households or note them as out of scope. (E087)
15. **Shock scenarios to add:** a pharmacy closure, a closed rural dialysis unit, and a transit operator shortage. (E051, E057, E067)

---

## 3. Top 10 frictions, with real voices

**1. Fees on thin balances (overdraft, ATM, check cashing).** About a quarter of people live in households that pay overdraft fees each year, and the burden falls hardest on lower-income households. Out-of-network ATM withdrawals average $4.86, the highest ever recorded, and Atlanta's $5.37 is the highest of any large metro. A researcher who worked behind a check-cashing counter heard that "RiteCheck customers told me clearly that bank fees were an important factor." *Left diagnosis:* cap fees and require banks to disclose them. *Right/industry diagnosis:* caps remove a service that customers say they value, leaving people with "few, if any, other options for meeting short-term liquidity needs." (E010, E011, E013, E015)

**2. Tax-time fees and refund timing.** About half of EITC claimants use paid preparers. A refund transfer costs about $40–$50 before preparation fees, and the fees are often disclosed only after the return is done. The IRS's free Direct File tool was dropped in 2026. An advocate said of the cost: "That's just prohibitive for a lot of low-income families." *Other side:* Treasury pointed to participation below 0.5% and to the free options that remain. (E001–E005)

**3. Paperwork churn in Medicaid and SNAP.** Two-thirds or more of Medicaid disenrollments were procedural. In Georgia, one enrollee who already met the work requirement said "I was struggling" to figure out how to upload proof. *Supporter view:* the governor says "What we are doing is working." Work reporting becomes national in 2027. (E023, E029–E031)

**4. Unreliable buses.** No MARTA bus route met its service target in 2025. A legally blind rider asked simply: "Just come when you say you're going to come." A Memphis rider whose free bus often didn't show spent $130 on rideshare in three months. *Diagnoses:* more operators and funding (left), or better management and cost control. (E041–E043, E067)

**5. Schedule volatility.** About two-thirds of service workers get less than two weeks' notice of their schedules, and 11% had a shift cancelled in the past month. One worker said: "Having to give them that much availability, it means you're at their mercy." *Diagnoses:* fair-workweek laws (left), or flexible labor markets and voluntary scheduling tools (right). (E040, E044–E047)

**6. Unpaid caregiving.** About 63 million caregivers give an average of 27 hours a week, and their out-of-pocket costs now average about $11,508 a year. A caregiver who left her career called it "definitely scary." A daughter who rides her mother's dialysis bus said, "I don't have much free time anymore." *Diagnoses:* paid leave and caregiver tax credits (left), or family-centered support and tax relief (right). (E048–E050)

**7. Home-care gaps.** Approved home-care hours go unstaffed. One woman said "I couldn't find anybody reliable" to replace her aide. A man whose shifts were cut said: "I'll skip a meal or wait later several hours to take a pill." *Diagnoses:* higher Medicaid pay rates for aides (left), or fewer licensing and labor barriers for aide work (right). (E053–E055)

**8. Distance to care.** About 48 million people live in pharmacy deserts; in nonmetro areas, the average round trip to a pharmacy is 36 miles. When a rural Nebraska dialysis unit closed, one patient said dialysis "is one thing that we really need here." A man whose local pharmacy closed said: "I was really mad." (E051, E052, E056, E057)

**9. Prices at the pharmacy counter, and medical debt.** More than half of prescriptions costing over $250 are abandoned at the counter. 41% of adults carry health care debt. A Georgia oncologist whose patients have given up treatment for fear of debt called it "barbaric." (E058–E060)

**10. The car as collateral (title pawns and kill switches).** One in five Georgia title-pawn borrowers loses the car. A Gwinnett borrower said: "It's giving me anxiety, it's making me worry and this is a daily thing." A buy-here-pay-here customer whose car was shut off said: "I was very anxious." *Industry view:* the devices "enabled customers to obtain loans who would otherwise be unable to obtain financing." (E020–E022, E061–E064)

---

## 4. Project leads (backed by both the simulation and the evidence)

1. **Refund-day fee check.** A one-page, plain-language comparison of the full prep-plus-transfer cost against VITA, handed out before filing. The aim is to make fees visible before the return is prepared, not after. (Sample R0023584; E001–E005)
2. **Payday-timed low-balance alerts.** Warn people one day before a scheduled draft would fail, timed to their actual pay dates. 43% of people who overdrafted were surprised by it. (27 insufficient-funds records; E008, E017)
3. **Renewal checklist and text reminders.** A missing-page checklist plus reminders for Medicaid and SNAP renewals and the new work reports, based on Code for America's texting pilots. (R0134623, R0175310; E023–E026)
4. **Ghost-bus log.** Riders log scheduled buses that never came, and the log is compared with the agency's cancellation data. Test it on a Medianville-like route and at Five Points. (R0028291, R0045456; E041, E043)
5. **Backup child care for sick days.** A shared roster of backup care for hourly workers who have no paid sick time. (R0048156, R0049866; E044)
6. **Call ahead to the pharmacy.** A phone or text check of stock and out-of-pocket price before a rural pickup trip. (R0079347, R0088266, R0160333; E056, E058)
7. **Home-care no-show fallback.** The agency alerts the family as soon as a shift goes unfilled, and a pre-arranged neighbor or relative covers. (R0079760; E053, E054)
8. **Title-pawn exit referrals.** Point Georgia title-pawn borrowers to credit-union refinancing. This belongs in Medianville only after the generator change in section 2, item 2. (E020–E022)
9. **Invoice follow-up nudges.** Automatic reminders on small-business invoices more than 30 days past due. (R0081554, R0093069, R0095695, R0098143; E073)

---

## 5. Field-visit prompts

1. **Driver Services center.** The agency reports a statewide average wait of about 6 minutes, while customers at the Fayetteville office reported waits from half an hour to more than two hours, so time waits yourself. Count people turned away for missing documents. Ask whether the errand could have been done online; about 68% of transactions are still in person. (E084–E086)
2. **Five Points MARTA, weekday 7–9 a.m.** Compare the app's arrival times with actual arrivals and note any ghost buses. Ask riders what their backup plan is and what it costs. Watch for paratransit riders and how long they wait. (E041–E043)
3. **Gas station and Waffle House on a highway exit, about 6 a.m.** Watch for small cash fill-ups in the $10–$20 range, as in the sample, and card declines. Ask workers coming off a shift how far ahead they know next week's schedule. Ask the owner about card fees. (E040, E074)
4. **Laundromat and check-casher strip, Forest Park or Riverdale.** Look for title-pawn storefronts and count ATMs that charge a surcharge. Ask check-casher customers why they don't use a bank, and listen for fees and how fast money clears. Note Direct Express card users, money orders and the languages spoken. MARTA delays on local Forest Park routes are a likely topic. (E011, E015, E020, E067, E079)
5. **Dollar General and pharmacy in a rural town.** Ask about drive times to the pharmacy and back-ordered or prior-authorization prescriptions. Watch for people leaving the counter without a prescription because of price. Note EBT purchases and the share paid in cash. (E056–E058)
6. **Public school pickup line.** Time how long the line takes, which the sample puts at 4–16 minutes. Ask who picks up when shifts run late. Ask about child care costs, which average $13,184 a year, and fees such as field trips and lunch accounts. (E044, E081)
7. **ER or urgent care, Griffin, weekday evening.** Ask how people will get home and what they think they will owe. Medical debt and Georgia's partial Medicaid coverage will come up. (E059, E060, E026)
8. **Farm stand or orchard store, Fort Valley area.** Ask whether they take cash only or use a card reader, and what the fees are. Ask about H-2A staffing and the changing wage floor. Watch whether customers pay with EBT, SNAP or cash. (E074, E087, E088)

---

## 6. Gaps and cautions

- **Fewer findings and quotes than the prompt asked for.** This pass has 76 evidence rows rather than about 150, and 25 quotes rather than 60 or more. A second pass should read CFPB complaint narratives, ATUS caregiving and eldercare tables, Diary of Consumer Payment Choice results by income, and Propel ATL's full rider report.
- **Older sources.** The Pew payday data are from 2013–2016, the Servon ethnography from 2017, Stateline on kill switches from 2018, and KFF Health News on home-care shortages from the pandemic era or earlier. Look for newer figures.
- **Lens balance.** Of the 69 sources, 35 are nonpartisan, 12 advocacy, 11 government, 7 industry, 2 center and 2 right. Right-of-center views come mostly from industry and from officials quoted in the news. Add AEI, the Manhattan Institute and Mercatus on safety-net design, licensing and fees.
- **Secondhand reads.** Several figures were read through summaries rather than the original documents: CFPB via a law-firm blog, QuickBooks via aggregators, and the FTC via news coverage. Bloomberg and BioCentury were paywalled. Verify the key numbers in the originals before publishing.
- **Some diagnoses are generic.** The left and right diagnoses for frictions 4–7 (transit, schedules, caregiving, home care) are standard framings, not taken from specific think-tank papers read in this pass. Source them from the paired think tanks in the City Design doc.
- **One working paper.** The NYU SNAP paper is not peer reviewed.
- **Calibrated anchors aren't independent checks.** The $400-emergency share, the ALICE shares and the cash shares were inputs to the simulation, so matching them proves little.
- **Estimates in this report.** The overdraft count (about 150 a day), disconnections (about 11–12 a day) and caregiving (about 67,500 hours a day) are rough conversions of national rates to Medianville's size. Each states its assumptions where it appears.
