# Medianville v2 close reading (phase 5)

Read 2026-11-21 in Claude Code, on branch `medianville-v2-phase5`, before the simulator is frozen for v2's hand-written records (decision 2.5). It follows the build notes' advice (decision 2.6): read a smaller sample, earlier, and add a second reader who has not seen the code.

## The sample

200 records, drawn by `tools/sample_records.py` with salt 700, so they share nothing with the hand-written sample (salt 500):

- 160 from the v2 baseline day, Wednesday, March 3, 2027 (202,462 records), stratified by district, record type and income group, like the simulator's own pick. 56 of them come from the 43 job kinds that are new since v1 or whose daily count moved by half or more, one per kind in turn, so the reading lands on what changed.
- 40 from five typed days, 8 each: the storm day (January 19), the EITC refund day (March 2), Independence Day observed (July 5), a Friday payday (October 8) and a Saturday (October 9).

Each record was turned into a card showing who, household, counterpart, money, time, travel, frictions, the record it follows from, and the statement and narrative. Two readers read all 200:

1. **Claude Code**, which built the simulator, card by card, then measured each suspicion across the whole baseline day and against v1's March 3.
2. **A second reader**, a separate Claude agent given only the cards: no code, no repository, no web. Its report is below, unedited in substance.

## What the first reader found

Counts are for the whole v2 baseline day unless they say otherwise; v1 is the same day in the frozen v1 run.

### New in v2

1. **Owners without a mortgage pay too much for housing.** 990 of 10,777 free-and-clear owners (9%) pay exactly $2,500 a month, the cap on batch I's redraw (`population.reshape_owner_costs`); their median income is $90,568. 163 of them pay more than their whole income for housing (v1: 3). The redraw matched AHS 2023's cost burdens, but with a cost drawn apart from income and a wide spread (median $613, 90th percentile $2,382), so a 95-year-old on $16,648 a year pays $2,476 a month. Cards 15, 36, 78. This is the one regression v2 introduced.

### Carried over from v1's population (decision 1 keeps it for v2)

2. **SSI where it couldn't be paid.** 831 of 3,160 SSI recipients live in households with more than $60,000 a year, 1,082 are married (a spouse's income counts against SSI), and 747 have no Medicaid, which SSI brings with it in most states. A regional manager in a $227,200 household draws SSI (card 183). 42 SSI recipients pay their own Medicare Part B premium today, where the state would pay it.
3. **Jobs and employers that don't go together**: a software developer and an administrative assistant at a pet clinic, an engineer at a law firm, an appraiser at an apartment complex, a farmer who rents downtown (cards 73, 84, 129, 142, 161). Group 4's "occupations tied to employers" was not done in phase 3.
4. **Housing costs and incomes that don't fit the household**: mortgages larger than income (683 households, half of them the cap in item 1), roommate households on $400,000.

### Records and text, fixable without touching the population

5. **Long trips.** 1,747 trips a day are over 40 miles (v1: 2,067): 79 miles to roll over a title loan when the same lender has a branch 7 miles away, 78 miles to apply for energy assistance, 60 miles each way to make a $75 weekly car payment (cards 61, 62, 105). Group 4's "distances from locations" was not done either.
6. **Money that doesn't add up on insurance claims.** On 2,856 of 5,440 claims the gross is not what the person and the insurer paid, mostly prescriptions where the gross is the list price (cards 24, 124, 125, 165). An uninsured 6.9-hour emergency visit is billed $181.59 in all, and the narrative says "about $182 more will be billed later" (card 53).
7. **Adults seen at pediatric practices**: 162 visits a day (card 81).
8. **Fees in the narrative but not in the fee column**: 18 instant cash-outs a day say "fee $0.43" with no fee recorded (card 160).
9. **Templates that don't fit the person or place**:
   - "Sorting pills and paying bills" as care for a child under 16, 124 times a day (card 88).
   - The church offering's "support my church" and "when the plate comes around" at mosques, temples, a synagogue and a gurdwara, 32 times a day (card 140).
   - "When I am building a water heater swap" (card 150); "Pay as a appraiser" (card 161).
   - A self-employed stylist staying home "without losing my job" (card 51); a retiree with "no time to cook between work and everything else" (card 196).
   - Unbanked people wanting app money "in my bank today", 14 a day (card 160).
   - Shipments invoiced to "Customers (general public)" with outcome partial, 8 a day, one for $1.19 million (cards 47, 128).
   - Child care subsidies paid by "State EBT (SNAP, WIC, TANF)" (cards 162, 170, 177); an online installment loan from a credit card company (card 154).
   - A federal refund of $924.64 whose narrative says "$9083.80 in all" (card 10).
   - Social Security narratives in two styles, one with "social security" in lower case (cards 2, 9, 21).
   - The marriage license costs $62 on one card and $76 on another at the same courthouse (cards 65, 115).
   - All five first driver's licenses of the day go to people aged 38 to 83 (cards 76, 108).

### What reads true

The new v2 jobs read well: called in on a day off, keeping a day open for shifts, a family member covering a missed aide visit or leaving work for it, prescriptions and dental care put off over cost, a payday rollover that pays only the $45 fee, a title rollover that leaves the $1,000 owed, a car repossessed overnight, a SNAP interview by phone, a car bought for cash with the tax refund. Fees are in the right ranges (payday $15 per $100, title rollovers 25% a month, refund transfers, out-of-network ATMs), and the calendar shows (refunds in tax season, rent late on the 19th with a 5% fee, Social Security cohorts).

## What the second reader found

Full report: [medianville-v2-second-reader.md](medianville-v2-second-reader.md). Its verdict: single transactions are believable (fees, program amounts, paydays and timing match how money moves), but the households behind them often are not. Its twelve patterns, most serious first, with what the whole baseline day shows:

| # | Second reader's pattern | Across the baseline day | Where it comes from |
|---|---|---|---|
| P1 | Housing costs at or above income; free-and-clear owners at $2,000-2,500 | 683 households pay more than their income (v1: 336); 990 free-and-clear owners at the $2,500 cap | v2's owner-cost redraw (item 1 above), on top of v1 |
| P2 | Health claims don't add up; a $182 emergency stay; Medicare billing 74% to the patient | 2,856 of 5,440 claims | v1 |
| P3 | SSI against income and deeming rules; SSI without Medicaid | 831 in households over $60,000, 1,082 married, 747 without Medicaid | v1 population |
| P4 | Statements that contradict the person: work talk from people who don't work, gas from people without cars, church words at a temple, a child "sorting pills" | 124 children, 32 non-church offerings | v1 templates |
| P5 | Coverage against eligibility: uninsured adults on $0 income in what reads as an expansion state, marketplace at $0, a nursing-home resident without Medicaid | (not measured) | v1 population |
| P6 | Placeholder counterparties ("Out-of-area employers", "Customers (general public)" filed under salons) and invoices running backwards | 8 reversed invoices a day | v1 |
| P7 | 60-80 mile trips; times that ignore travel (158 miles in 11 minutes); waits longer than the whole visit | 1,747 trips over 40 miles; 7,512 car trips faster than 72 mph; 5,215 waits longer than the record's time (v1: 2,067, 7,728, 5,126) | v1; `time_minutes` leaves travel out, which no document says |
| P8 | Every $0-income renter pays exactly $380 with no cash aid | 1,072 of 1,734 zero-income households at $380 | v1 population |
| P9 | Jobs, employers, wages and degrees that don't fit | (item 3 above) | v1 population |
| P10 | "Could not cover $400" on high incomes | 18% of households on $100,000-200,000, 5% over $200,000 (v1: 13%, 4%) | v1, a little higher in v2; SHED puts about 1 in 8 at $100,000 and over, so this one reads worse on cards than it is |
| P11 | Smaller rule slips: free school meals at $77,000-88,000, ACH on a holiday and a Saturday, monthly escrow paid straight to the county | | v1 |
| P12 | Narrative amounts or channels that disagree with the fields | | v1 |

It also noted that the 8 storm-day cards show no sign of the storm. The storm works through rates (more cancellations, closures and outages), so a small sample can miss it.

## What the two readings add up to

Both readers found the same few things. The households carry most of the trouble; the transactions mostly hold up. Sorted by what fixing them would cost:

1. **v2's owner-cost redraw** (P1). It is the one problem v2 made worse, and it runs on its own random stream after the population is built, so fixing it changes no one's identity. It does change balances, so every record downstream moves and the typed-day year and the month have to be rerun.
2. **Record and text fixes that leave the population alone**: templates that read by age, faith, work and banking (P4); invoices in the right direction and named customers (P6); claims that close, gross = insurer + person + adjustment (P2); adults sent to adult practices; fees in the fee column; the child care subsidy payer. Text-only changes that keep each template list the same length draw the same random numbers, so they move no figures; the others move a few.
3. **Population rules carried over from v1** (P3, P5, P8, P9; items 2-4): SSI and Medicaid against income, coverage against eligibility, $0-income rent, jobs tied to employers, distances from locations (P7). Decision 1 kept v1's population for v2 so that before-and-after comparisons stay clean, and v3 redraws it from ACS PUMS anyway.

## Decisions

**Decided 2026-11-21 (Jason): fix 1 and 2, then freeze; leave 3 for v3.** The fixes are made one commit and one test file each, the typed-day year and the month are rerun after them, and the population problems in 3 are listed as v2's known limits. What each fix did is in [Fixes made](#fixes-made).

## Fixes made

1. **Owner housing costs** (`population.reshape_owner_costs`, `tests/test_owner_costs.py`). Drawn from AHS 2023's cost quantiles for owners at the same income (`sources/tools/ahs_owner_costs.py` writes `sources/derived/ahs_owner_costs.csv`), carried to 2027 dollars and scaled by district, and held to 60% of income without a mortgage and 80% with one. On the full city: owners without a mortgage pay a median $496 a month (AHS $441 in 2023 dollars), 90th percentile $1,394 ($1,190); no amount is shared by more than 27 of 10,345 households (was 990 at $2,500); households paying more than their income fall from 683 to 78, all of them renters from v1. Burdens: without a mortgage, median 6.5% of income, 7% over 30% (AHS 7.8%, 14%; AHS's heaviest burdens are owners living on savings it doesn't count as income); with one, median 20%, 29% over 30% (AHS 18%, 24%).
2. **Records** (`tests/test_record_fixes.py`). Each moves some figures, so the typed-day year is rerun after them.
   - Prescription claims add up: the gross is what the fill was charged (the plan's price, or what an uninsured buyer paid), and the narrative names the cash price beside it ("cash price $21.84; the plan's price was $9.83 and the copay $0.00"). v1 showed the cash price as the gross.
   - Emergency visits: draws under $600 are pressed smoothly into $300-600 (v1's floor was $150). An uninsured visit's narrative says what the hospital bills and what it writes off as charity care, instead of "about $182 more will be billed later". A Medicare bill sent later names the Part B deductible and coinsurance.
   - Patients go to practices that see them: no adults at pediatric offices, no men or children at women's health, no children at internal medicine or cardiology (`Sim.pick(..., who=)`, the same single draw).
   - Manufacturers ship to a new outside party, "Out-of-area business customers" (wholesale trade), added last so no organization's id moves. The pseudo-parties (general public, out-of-area employers, family abroad and elsewhere, the scam party) are filed under "Many parties (not one organization)" instead of salons and churches.
   - State child care payments come from the State Department of Family & Economic Services, not the EBT processor; public bodies pay vendors and subsidies on bank days only.
   - Instant cash-outs go to bank debit cards, so the unbanked no longer make them, and the fee named is the fee charged.
   - A record's time includes its wait (about 5,200 a day had a wait longer than their time). Travel time stays outside `time_minutes`, which the README now says.
   - First driver's licenses go to people 24 and under or in immigrant households (the others become renewals); one marriage license fee per courthouse ($66 and $56); a refund narrative splits the refund from the refundable credits, which have their own record.
3. **Text** (`text.fit`, `tests/test_text_fits.py`). Text draws its own random numbers, so these change wording and nothing else: on the 10% city every column but `job_statement` and `narrative` comes out the same, and the ledger and summary are byte for byte.
   - People who don't work get statements without work in them (fast food, gas, haircuts, school drop-off, a repossessed car, care at home); households without a car tip out for groceries, not gas; self-employed parents fear losing customers, not their job.
   - Offerings at a mosque, synagogue, temple, gurdwara or Buddhist center support that place, not "my church", and drop the collection plate.
   - Care for a child under 16 is meals, medicine, dressing, watching, rides, therapy exercises and homework, never pills and bills (the same-length lists keep the main draws in line).
   - An app transfer's statement follows its purpose (settling up, or helping someone); "a" and "an" before occupations; "1 hour", not "1 hours"; "one child" and "two kids", not "Dropped 1"; "When the job is a water heater swap"; "Social Security disability (SSDI)" instead of "ssdi"; prescription narratives say "prescription" so they fit either statement.

## The hand-written records

After the fixes, the simulator was frozen at commit `dd0e6b6` (decision 2.5), and 300 records of the baseline day were drawn with salt 500. 120 of them (40%) came from the 59 job kinds new or changed since v1, one per kind in turn, and the rest were stratified by district, record type and income group. Claude Code wrote each one's job statement and narrative in `sim/detail_parts/part*.txt`. `tools/merge_detailed.py` merged them into `sim/detailed_overrides.csv`, keyed by record id, job and actor. Rerun, the baseline day applies all 300 and changes nothing else (`sim/tests/test_handwritten.py`).

A second reader that had not seen the code checked every one against its own fields. Its [report](medianville-v2-handwritten-second-reader.md) found 23 contradictions and 54 weaker problems.

**Contradictions.** All 23 were fixed. For example:
- tax withheld "every week" from a biweekly check;
- a mortgage draft for a home owned outright;
- a "brother" who is a 72-year-old woman;
- a woman with low vision who "drives";
- a nursing-home shift for a hospital worker;
- the Earned Income Tax Credit named for a $198,604 household;
- the same man filing for divorce in the morning and paying for "my wife's green card case" that night.

**Weaker problems.** 46 were fixed, along with every "round trip" and every relative the fields don't name. The rest were kept. Most of those are details the second reader couldn't see because they come from the simulator's own narrative, such as settlements in 21 days, $40 a month on a medical bill, an amount past due, or a federal and state split.

**Record problems the reading surfaced, listed as limits rather than hidden:**
- refundable credits paid to high-income households (about 140 of the day's 640);
- Medicare's home health benefit for a 42-year-old on a marketplace plan;
- federal withholding on incomes too low to owe;
- a 74-mile therapy trip that fits in 53 minutes, because `time_minutes` leaves out travel.

The second reader also found the text samey within a record type: more than a quarter of the statements end "so I can keep". Some were varied in the fixes. The rest is the cost of one writer in one sitting.
