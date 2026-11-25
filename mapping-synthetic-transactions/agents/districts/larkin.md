> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.

# D2 Inner suburbs: Larkin Avenue

**Composite**: an invented block drawn from documented US patterns, not a real place. Part of https://medianville.netlify.app/agents/districts.md, which explains the layers and the ids.

Block id `larkin`, on Larkin Ave. Red-rated in 1938, split by the interstate spur in 1961, and left with check cashers when the branches closed.

The simulator puts 420 of the district's households on this block (`block_id = larkin` in households.csv and records.csv).

## Across the whole district (the district tier)

**Economic** (changes over years)

- **DW1** · 2016 · High-cost lenders fill the gap. Across the inner suburbs, storefront lenders stand in for the banks that left. Nationally about 12 million people a year use payday loans, paying about $520 in fees to keep borrowing $375, mostly for rent and utilities rather than emergencies.
  - Types: economic. Rests on: EC1, Hourly work, short-notice schedules; DH1, Neighborhoods graded for lending. Evidence: E019.
- **DW2** · 2024 · Behind on the utility bill. About one household in six is behind on utility bills, and utilities disconnected electric service about 13.5 million times in 2024. Nearly 40% of households earning under $50,000 struggle to pay for energy.
  - Types: economic, environmental. Rests on: DE1, Postwar houses getting old. Evidence: E082.

**Political** (changes over decades)

- **DW4** · 2026 · Local routes thinned. Local routes through the inner suburbs run short of drivers, and riders describe delays that have become routine for months at a time.
  - Types: political. Evidence: E067.

**Built & natural** (changes over generations)

- **DE1** · 1945–1970 · Postwar houses getting old. Most inner-suburb housing went up in the postwar building boom. The median American home is now more than 40 years old, and houses this age need new roofs, furnaces and wiring, costs that land on owners with the least saved.
  - Types: environmental, economic. Rests on: DH1, Neighborhoods graded for lending. Source: Census American Housing Survey (median year built).

**Social & cultural** (changes over generations)

- **DW3** · 2017 · Check cashers chosen on purpose. Many people here cash checks at a storefront even when they have a bank account. A researcher who worked behind a check-cashing counter found customers chose it for clear fees, fast money and service, to avoid surprise bank fees and holds.
  - Types: social, economic. Evidence: E014, E015.

**Historical** (bedrock, lasts a century)

- **DH1** · 1930s · Neighborhoods graded for lending. In the 1930s the federal Home Owners' Loan Corporation graded neighborhoods for mortgage risk, A to D, and the lowest grade was outlined in red. Federal mortgage insurance followed similar rules for decades, so lending, and the family wealth that comes with owning a home, flowed unevenly across the inner suburbs.
  - Types: historical, political, economic. Source: University of Richmond, Mapping Inequality (HOLC maps).

## On Larkin Avenue itself

**Economic** (changes over years)

- **P1** · 2009 · The last bank branches close. After a bank merger in 2009 both branches on Larkin Avenue closed. The nearest branch is now 2.6 miles away. The old Medianville Savings building is a check casher.
  - Types: economic. Rests on: H1, Rated “hazardous” on the 1938 appraisal map.
- **EC1** · today · Hourly work, short-notice schedules. Most jobs open to people here are hourly, with schedules posted less than a week ahead and pay docked for lateness. Income moves week to week, which makes autopay dates hard to plan around.
  - Types: economic. Rests on: H3, Medianville Works closes.

**Political** (changes over decades)

- **P2** · state law · State rules on check cashing and payday loans. State law lets check cashers charge 2 to 3 percent of a check and lets payday lenders charge $15 per $100 borrowed every two weeks, about 390% a year. A renewal pays the fee again without paying down the loan.
  - Types: political.
- **P3** · 2019 · Route 6 service cut. Facing a budget gap, the transit agency cut Route 6 from every 15 to every 30 minutes. Missing a bus now costs half an hour, and a late clock-in can cost part of a shift.
  - Types: political.
- **P4** · 2011 · Zoning and the missing grocery. Zoning keeps most blocks residential and allows shops only on the Larkin strip. The last supermarket closed in 2011 and none has replaced it, so daily food comes from the corner market and the dollar store.
  - Types: political, economic. Rests on: H1, Rated “hazardous” on the 1938 appraisal map.

**Built & natural** (changes over generations)

- **H2** · 1961 · The interstate spur goes through. The state routed an interstate spur through the red-rated blocks, where land was cheapest and residents had the least say. It cleared about 300 homes and split the district. The nearest walkable crossing is now 0.6 miles from the Route 6 stop.
  - Types: historical, political, environmental. Rests on: H1, Rated “hazardous” on the 1938 appraisal map.
- **E1** · today · Cutler Run floodplain. A third of the blocks by the creek sit in the 100-year floodplain. Homes with a mortgage there must carry flood insurance, a bill most of the city never sees. These were the cheapest lots, and the ones red-rated buyers could get.
  - Types: environmental. Rests on: H1, Rated “hazardous” on the 1938 appraisal map.
- **E2** · today · Highway air. Homes beside the spur breathe more traffic exhaust. Childhood asthma is higher here than in the rest of the city, and an attack often means the ER rather than a scheduled visit.
  - Types: environmental. Rests on: H2, The interstate spur goes through.

**Social & cultural** (changes over generations)

- **S1** · 1990s on · An immigrant gateway. Low rents after the plant closed made Larkin a first stop for new arrivals. Many households send money home every week, and many neighbors work and bank in more than one language.
  - Types: social, cultural. Rests on: H3, Medianville Works closes.
- **S2** · today · Church savings circles. Several congregations run rotating savings circles. Each member pays in every week and takes the whole pot in turn. With no branch nearby, the circle is the neighborhood’s savings account and emergency fund.
  - Types: cultural, economic. Rests on: S1, An immigrant gateway; P1, The last bank branches close.

**Historical** (bedrock, lasts a century)

- **H1** · 1938 · Rated “hazardous” on the 1938 appraisal map. A federal appraisal map graded the Larkin Avenue blocks red, citing the race of residents and the age of the housing. For decades lenders treated red-rated blocks as too risky for mortgages and deposits, so home ownership, equity and bank branches stayed thin here.
  - Types: historical, political. Rests on: DH1, Neighborhoods graded for lending.
- **H3** · 1983 · Medianville Works closes. The stamping plant at the north end of the district closed in 1983. Its union jobs paid enough to own a house on one income. What replaced them was warehouse, retail and care work, most of it hourly.
  - Types: historical, economic.

## Patterns: the records the block's circumstances shape

A record from the block's households that matches a pattern (the first that matches, in this order; the rules are regular expressions) carries its id in `block_pattern` and the circumstances it links to in `context_ids`. Pattern ids and loop ids are separate: pattern R1 is not loop R1.

- **R8** Home and flood insurance bills (bill): links E1; tagged when job_category matches `^housing\.(home_insurance|renters_insurance)$`.
- **R1** Missed buses (fail): links P3, H2; tagged when job_category matches `missed_bus`.
- **R10** Groceries at the corner market (purchase): links P4; tagged when job_category matches `^food\.(convenience_store|grocery_fill_in)$`.
- **R7** Emergency room visits (purchase): links E2; tagged when job_category matches `emergency_(department_visit|visit_uncompensated)`.
- **R2** Paychecks cashed for a fee (income): links P1, P2; tagged when job_category matches `check_cashing|paycheck_paper_check`.
- **R3** Payday loan renewals (bill): links P2, EC1; tagged when job_category matches `payday_loan`.
- **R4** Overdrafts and declined cards (fail): links EC1; tagged when fee_type matches `overdraft_fee|returned_payment_fee` or job_category matches `^food\.dollar_store$` and outcome matches `^(declined|failed|partial|abandoned|rescheduled)$`.
- **R6** Savings circle payments (unpaid): links S2; no match rule, so no record carries it.
- **R5** Money sent abroad (bill): links S1, P1; tagged when job_category matches `remittance_sent`.

## Loops (hypotheses for the next run to test)

- **R1 Fee spiral** (reinforcing). A low balance lets a payment overdraw the account. The overdraft fee lowers the balance again, so the next payment is more likely to bounce.
  - Balance after bills → Payments that overdraw (−): A lower balance means more payments overdraw.
  - Payments that overdraw → Overdraft fees (+): More overdrafts mean more fees.
  - Overdraft fees → Balance after bills (−): More fees mean a lower balance.
  - Pushed + by EC1: Pay that moves week to week makes autopay dates miss.
  - Seen in the records of pattern R4.
- **R2 Rollover** (reinforcing). A short week leads to a payday loan. Each renewal pays the fee without paying down the loan, which leaves the next week short again.
  - Cash left after bills → Payday renewals (−): Less cash left means more renewals.
  - Payday renewals → Fees paid to the lender (+): More renewals mean more fees.
  - Fees paid to the lender → Cash left after bills (−): More fees leave less cash.
  - Pushed + by P2: State law sets the fee at $15 per $100 per renewal.
  - Pushed + by P1: With no branch nearby there is no small-dollar loan from a bank.
  - Seen in the records of pattern R3.
- **R3 Time tax** (reinforcing). A missed bus means a late clock-in and docked pay. Less pay pushes back fixing the car, which keeps the household on the bus.
  - Rides Route 6 → Late clock-ins (+): More bus trips mean more late clock-ins.
  - Late clock-ins → Docked pay (+): More late clock-ins mean more docked pay.
  - Docked pay → Money to fix the car (−): More docked pay leaves less for the car.
  - Money to fix the car → Rides Route 6 (−): Less for the car means more bus trips.
  - Pushed + by P3: Buses every 30 minutes make each miss cost more.
  - Pushed + by H2: The spur forces a long walk to the next stop.
  - Seen in the records of pattern R1.
- **B1 Circle buffer** (balancing). A shortfall sends the household to its savings circle instead of a lender. The payout covers the gap, which works against the rollover loop.
  - Shortfall this week → Turns to the circle (+): A shortfall means turning to the circle.
  - Turns to the circle → Payout covers the gap (+): Turning to the circle brings a payout.
  - Payout covers the gap → Shortfall this week (−): A payout shrinks the shortfall.
  - Pushed + by S2: Congregations run the circles.
  - Seen in the records of pattern R6.
- **D1 Borrowing to cover borrowing** (reinforcing). A paycheck that comes up short gets covered with a payday loan or an overdraft. The fees come due out of the next paycheck, which leaves it short too, so the borrowing repeats.
  - Short before payday → High-cost loan or overdraft (+): Coming up short means another high-cost loan or overdraft.
  - High-cost loan or overdraft → Fees due next payday (+): More borrowing means more fees due.
  - Fees due next payday → Short before payday (+): The fees leave the next paycheck short too.
  - Pushed + by DW1: Storefront lenders are the nearest credit.
  - Pushed + by DH1: Decades of lending exclusion left less family wealth to fall back on.
  - Seen in the records of patterns R3, R4.
