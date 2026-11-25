> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.

# D6 Open country: Route 9 Crossroads

**Composite**: an invented block drawn from documented US patterns, not a real place. Part of https://medianville.netlify.app/agents/districts.md, which explains the layers and the ids.

Block id `crossroads`, on County Rd 12. Farm country consolidated in the 1980s, eleven miles from town, with no bus, no pharmacy and broadband that stops at Route 9.

The simulator puts 360 of the district's households on this block (`block_id = crossroads` in households.csv and records.csv).

## Across the whole district (the district tier)

**Economic** (changes over years)

- **DW2** · 2022 · Prices at the counter, debt after. When a prescription costs more than $250 out of pocket, more than half are left at the counter. 41% of adults carry health care debt, and about two-thirds of them have put off care because of cost.
  - Types: economic. Rests on: DW1, A pharmacy desert. Evidence: E058, E059, E060.

**Political** (changes over decades)

- **DW4** · 2025 · Seasonal guest workers. Farms here hire seasonal crews on H-2A visas, whose minimum wage is set by federal rule and has been fought over in court. Nationally they are a small group, but in farm counties they are much of the harvest.
  - Types: political, economic. Evidence: E087, E088.

**Built & natural** (changes over generations)

- **DW1** · 2024 · A pharmacy desert. Across open country, prescriptions mean a long drive. About 1 in 7 Americans lives in a pharmacy desert, and nonmetro residents average an 85-minute, 36-mile round trip. More than 7,000 pharmacies closed from 2022 through 2024.
  - Types: environmental, economic. Rests on: DE1, Services consolidated far away. Evidence: E056, E057.
- **DE1** · 1940–today · Services consolidated far away. Rural services were merged into fewer, farther places. The number of public school districts fell from about 117,000 in 1940 to about 13,000 today, and more than a hundred rural hospitals have closed or stopped inpatient care since 2010. Each merger added miles to ordinary trips.
  - Types: environmental, political. Rests on: DH1, The farm crisis. Source: NCES Digest of Education Statistics, table 214.10; UNC Sheps Center rural hospital closures.

**Social & cultural** (changes over generations)

- **DW3** · 2024 · Caregivers on the road. Out here a treatment day can be a whole day. In one rural region, dialysis patients ride a medical transit bus more than 200 miles, three days a week, and the family members who go with them say it takes most of their free time.
  - Types: social, economic. Rests on: DE1, Services consolidated far away. Evidence: E050.

**Historical** (bedrock, lasts a century)

- **DH1** · 1980s · The farm crisis. In the early 1980s high interest rates and falling export prices collapsed farmland values. From their 1982 peak to 1987 they fell by about a third nationally, and by more than half in Iowa. Many indebted farms were sold, and the people and businesses around them left too.
  - Types: historical, economic. Source: USDA ERS farm real estate values, as reported in FDIC, History of the Eighties, vol. 1, ch. 8 (1997).

## On Route 9 Crossroads itself

**Economic** (changes over years)

- **EC1** · today · Patchwork work. Year-round jobs are 11 miles away. Many households here piece together seasonal work at the packing shed, small self-employed jobs and gig work, paid irregularly and often through apps.
  - Types: economic. Rests on: H1, The farm crisis.
- **EC2** · 2018 · The pharmacy closes. The pharmacy at the crossroads closed in 2018 when its owner retired and no buyer came forward. Prescriptions come by mail now, a few days late when the mail is.
  - Types: economic.

**Political** (changes over decades)

- **P1** · today · No public transit in the county. The county has no bus. A volunteer van runs to Medianville once a week by reservation for medical trips. Anyone without a car pays a neighbor for rides to work.
  - Types: political.
- **P2** · 2009 · School districts consolidated. The township schools merged into a county district in 2009. Children ride the bus 50 minutes each way, and the district serves breakfast to everyone because so many leave home before 6:30.
  - Types: political.

**Built & natural** (changes over generations)

- **E1** · today · Broadband stops at Route 9. The cable line follows Route 9 and stops. East of the highway, internet means a phone plan, which works for deposits and payments but not much else.
  - Types: environmental, political.
- **E2** · today · Eleven miles to town. The nearest town is 11 miles away and the nearest city 25. Every errand, shift and appointment starts with a drive.
  - Types: environmental.

**Social & cultural** (changes over generations)

- **S1** · today · Church ride lists. The church at the crossroads keeps a list of who can drive when. Rides to work are paid, a few dollars toward gas; rides to the doctor usually are not.
  - Types: social, cultural.

**Historical** (bedrock, lasts a century)

- **H1** · 1980–95 · The farm crisis. High interest rates and falling land prices in the 1980s broke many family farms. Neighbors bought them out, and today four operations farm what forty families did. Former farm families stayed on and found other work.
  - Types: historical, economic. Rests on: DH1, The farm crisis.

## Patterns: the records the block's circumstances shape

A record from the block's households that matches a pattern (the first that matches, in this order; the rules are regular expressions) carries its id in `block_pattern` and the circumstances it links to in `context_ids`. Pattern ids and loop ids are separate: pattern R1 is not loop R1.

- **C1** Paid rides to work (bill): links P1, E2; tagged when job_category matches `ride_to_work_fee`.
- **C2** Self-employed and seasonal pay (income): links EC1, H1; tagged when job_category matches `self_employment_receipts|self_employed_supplies`.
- **C3** Prescriptions by mail (purchase): links EC2; tagged when job_category matches `prescription_mail_order`.
- **C4** Instant cash-outs (income): links EC1, E1; tagged when job_category matches `p2p_instant_cash_out|gig_payout_instant`.
- **C5** Deposits by phone (income): links E1; tagged when job_category matches `mobile_check_deposit`.
- **C6** School breakfast (unpaid): links P2; tagged when job_category matches `school_breakfast`.
- **C7** Care from neighbors (unpaid): links S1, E2; tagged when job_category matches `caregiving_visit|escort_to_appointment`.

## Loops (hypotheses for the next run to test)

- **R1 Ride debt** (reinforcing). Without a working car, getting to work means paying for rides. What goes to rides doesn't go to repairs, so the car stays broken and the rides continue.
  - A working car → Paid rides (−): No car means more paid rides.
  - Paid rides → Money for repairs (−): More paid rides leave less for repairs.
  - Money for repairs → A working car (+): Money for repairs keeps the car running.
  - Pushed + by P1: With no county transit, rides are the only option.
  - Seen in the records of pattern C1.
- **B1 Ride list** (balancing). When someone needs a ride, the church list finds a driver. The more drivers on the list, the fewer trips go unmade.
  - Rides needed → Drivers on the list (+): More need recruits more drivers.
  - Drivers on the list → Trips not made (−): More drivers mean fewer trips missed.
  - Trips not made → Rides needed (+): Missed trips come back as more need.
  - Pushed + by E2: Eleven miles to town makes every trip a ride.
  - Seen in the records of pattern C7.
- **D1 Distance and price** (reinforcing). Out here a prescription means a long drive, so some get skipped or put off. Conditions worsen, which means more trips to care, and every trip pays the distance again.
  - Miles to the pharmacy → Prescriptions skipped or delayed (+): More miles mean more prescriptions skipped or put off.
  - Prescriptions skipped or delayed → Condition worsens (+): Skipped doses let a condition worsen.
  - Condition worsens → More trips to care (+): A worse condition means more trips to care.
  - More trips to care → Miles to the pharmacy (+): More trips make the distance cost more.
  - Pushed + by DW1: A pharmacy desert puts the counter a long drive away.
  - Pushed + by DW2: Prices over $250 mean most are left at the counter.
  - Pushed + by DE1: Each consolidation adds miles between people and care.
  - Seen in the records of patterns C3, C7.
