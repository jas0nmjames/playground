> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.

# D4 Satellite city: Mill Street, Ashford Mills

**Composite**: an invented block drawn from documented US patterns, not a real place. Part of https://medianville.netlify.app/agents/districts.md, which explains the layers and the ids.

Block id `ashford`, on Mill St. A textile town whose mill closed in 1998; the county jail went into the mill yard and the college became the biggest employer.

The simulator puts 480 of the district's households on this block (`block_id = ashford` in households.csv and records.csv).

## Across the whole district (the district tier)

**Economic** (changes over years)

- **DW2** · 2025 · Hours that won't hold still. Retail and restaurant hours change from week to week, so a monthly work report can fail even for people who work. In one state's first year, enrollees struggled to upload proof and the website sometimes went down.
  - Types: economic, political. Rests on: DW1, Paperwork that ends coverage; DH1, The factories close. Evidence: E026, E027, E031.
- **DW4** · 2018 · The car as collateral. Subprime car loans here often come with starter-interrupt devices. One Southeast servicer admitted disabling cars at least 5,200 times when the borrower was not in default. Lenders say the devices let them lend to people who would otherwise be turned down.
  - Types: economic. Rests on: DH1, The factories close. Evidence: E061, E063, E064.

**Political** (changes over decades)

- **DW1** · 2027 · Paperwork that ends coverage. Across the satellite city, coverage depends on paperwork. In the Medicaid unwinding, two-thirds or more of disenrollments were procedural; missed interviews cause up to half of SNAP denials; and each churn costs the agency about $80. Work reporting for Medicaid starts nationally in January 2027.
  - Types: political. Evidence: E023, E024, E025, E030.
- **DW3** · 2024 · Raises that cost more than they pay. Benefits phase out sharply as pay rises. One restaurant worker's raise of about $200 a month would have cost her more than $800 a month in assistance, so some workers turn raises down.
  - Types: political, economic. Evidence: E066.

**Built & natural** (changes over generations)

- **DE1** · ongoing · Empty mills and old ground. The closed plants left large buildings and sites that may be contaminated. The EPA puts the number of brownfields nationally at 450,000 to 1 million; cleanup costs keep many idle, so the land that once held the jobs sits empty.
  - Types: environmental, economic. Rests on: DH1, The factories close. Source: US EPA, Brownfields (frequently asked questions; GAO's 2004 estimate).

**Historical** (bedrock, lasts a century)

- **DH1** · 1979–2010 · The factories close. US manufacturing employment peaked in 1979 at about 19.6 million jobs and fell by roughly a third during the 2000s alone. Mill and factory towns lost their steady, full-time work, and hourly service jobs took its place.
  - Types: historical, economic. Source: BLS Current Employment Statistics, manufacturing employment (CES3000000001).

## On Mill Street, Ashford Mills itself

**Economic** (changes over years)

- **EC1** · today · The college is the biggest employer. With the mill gone, Wexley College employs more people than anyone else in town, and its students fill the rentals near campus. Dining services and housekeeping are hourly work with semester breaks.
  - Types: economic.
- **EC2** · 2010s · Rent-to-own and pay advances on Mill Street. Where the mill workers' shops were, Mill Street now has a rent-to-own store and a pay-advance app's kiosk. Both serve people with thin credit, and both cost far more over a year than buying or borrowing from a bank.
  - Types: economic. Rests on: H1, Ashford Mills closes.

**Political** (changes over decades)

- **P1** · 2004 · The county jail goes into the mill yard. The county needed a bigger jail and the mill site was cheap and already zoned industrial. It holds about 240 people, most of them waiting for trial because they could not post bail.
  - Types: political, historical. Rests on: H1, Ashford Mills closes.
- **P2** · contract · Jail phone and commissary contracts. The county contracts phone calls, video visits and the commissary to private vendors and keeps a share of what families pay. A 15-minute call costs $3.15, and money for snacks or soap goes through a deposit fee.
  - Types: political, economic.
- **P3** · 2015 · The bus to Medianville is cut. The regional bus that ran to Medianville every hour was cut in 2015. A county van runs twice a day by reservation. People without a car pay neighbors or apps for rides, or search for one each morning.
  - Types: political.

**Built & natural** (changes over generations)

- **E1** · 2017 · The hospital closes; urgent care stays. The 60-bed hospital closed in 2017 after it was bought by a regional system. An urgent care clinic stayed in part of the building. Anything serious means a 19-mile trip to Medianville.
  - Types: environmental, economic.

**Social & cultural** (changes over generations)

- **S1** · today · Families who visit the jail. Most people held in the jail are from Medianville and the county, so their families come in by car or not at all. Calls and deposits are how most of them stay in touch.
  - Types: social. Rests on: P1, The county jail goes into the mill yard.

**Historical** (bedrock, lasts a century)

- **H1** · 1998 · Ashford Mills closes. The textile mill that gave the town its name ran for 96 years. It closed in 1998 as production moved overseas, and the mill houses along the river were sold to absentee landlords.
  - Types: historical, economic. Rests on: DH1, The factories close.

## Patterns: the records the block's circumstances shape

A record from the block's households that matches a pattern (the first that matches, in this order; the rules are regular expressions) carries its id in `block_pattern` and the circumstances it links to in `context_ids`. Pattern ids and loop ids are separate: pattern R1 is not loop R1.

- **M1** Dining hall meals (purchase): links EC1; tagged when job_category matches `dining_hall_meal`.
- **M2** Calls from the jail (bill): links P2, S1; tagged when job_category matches `jail_phone_call`.
- **M3** Commissary and deposits (purchase): links P2, P1; tagged when job_category matches `jail_commissary_purchase|jail_account_deposit`.
- **M4** Searching for a ride (fail): links P3; tagged when job_category matches `ride_search|ride_to_work_fee`.
- **M5** Rent-to-own payments (bill): links EC2, H1; tagged when job_category matches `rent_to_own_payment`.
- **M6** Pay advances (income): links EC2; tagged when job_category matches `earned_wage_advance`.
- **M7** Urgent care (purchase): links E1; tagged when job_category matches `urgent_care_visit`.

## Loops (hypotheses, not findings)

- **R1 Advance loop** (reinforcing). A pay advance covers the gap now and comes out of the next paycheck with a fee. The smaller paycheck leaves the next week short, so the next advance comes sooner.
  - Paycheck left → Pay advances (−): A smaller paycheck means more advances.
  - Pay advances → Fees and repayments (+): More advances mean more fees and repayments.
  - Fees and repayments → Paycheck left (−): More repayments leave less of the paycheck.
  - Pushed + by EC2: Mill Street storefronts make advances the nearest credit.
  - Seen in the records of pattern M6.
- **R2 Distance tax** (reinforcing). Without a bus, getting to work means paying for rides or searching for one. Paid rides drain the money that would go toward a car, which keeps the household paying for rides.
  - A working car → Paid rides and searches (−): No car means more paid rides.
  - Paid rides and searches → Cash left (−): More paid rides leave less cash.
  - Cash left → A working car (+): More cash makes a working car possible.
  - Pushed + by P3: With Route 14 gone there is no other way to Medianville.
  - Seen in the records of pattern M4.
- **D1 Churn** (reinforcing). Hours that change week to week make a monthly work report easy to miss. A missed report ends coverage, care gets put off until it is urgent, and the sick days and urgent visits move the hours again.
  - Hours change → Report missed or rejected (+): Hours that move make a monthly report easy to miss.
  - Report missed or rejected → Coverage lost (+): A missed or rejected report ends coverage.
  - Coverage lost → Care put off, then urgent (+): Without coverage, care waits until it is urgent.
  - Care put off, then urgent → Hours change (+): Sick days and urgent visits move the hours again.
  - Pushed + by DW1: Procedural rules end coverage over one missed form.
  - Pushed + by DW2: Retail and restaurant hours change week to week.
  - Pushed + by DH1: Steady mill jobs gave way to hourly work whose hours move.
  - Seen in the records of pattern M7.
