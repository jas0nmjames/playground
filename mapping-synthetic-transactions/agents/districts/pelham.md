> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.

# D1 Downtown and core neighborhoods: Pelham Street

**Composite**: an invented block drawn from documented US patterns, not a real place. Part of https://medianville.netlify.app/agents/districts.md, which explains the layers and the ids.

Block id `pelham`, on Pelham St. Rowhouses cleared for a civic center in 1962, rooming hotels torn down in the 1980s, and rents climbing as the towers fill.

The simulator puts 520 of the district's households on this block (`block_id = pelham` in households.csv and records.csv).

## Across the whole district (the district tier)

**Economic** (changes over years)

- **DW1** · 2025 · Fees fall on thin balances. Across downtown, short balances cost money. Nationally an out-of-network ATM withdrawal averages $4.86 and an overdraft about $27, and about 9% of accounts pay 79% of all overdraft and returned-payment fees.
  - Types: economic. Evidence: E009, E011.
- **DW3** · 2024 · Schedules with little notice. Downtown jobs are mostly hourly service work. Nationally about two-thirds of service workers get their schedules with less than two weeks' notice, and 11% had a shift cancelled in the past month.
  - Types: economic, social. Evidence: E040, E046.

**Political** (changes over decades)

- **DW2** · 2025 · Buses that don't come. Downtown riders depend on buses that run late or not at all. Where a route cancels 5% of trips, a five-day commuter meets a no-show bus about once every two weeks. In one large rider survey, 77% said bus problems made them miss something important in the past month.
  - Types: political, environmental. Rests on: DE1, Pavement holds the heat. Evidence: E041, E043.

**Built & natural** (changes over generations)

- **DE1** · ongoing · Pavement holds the heat. Downtown is mostly pavement and roofs with few trees. The EPA estimates the heat island effect makes daytime temperatures in urban areas about 1 to 7°F higher than in outlying areas, which raises cooling bills and makes waiting at a bus stop harder.
  - Types: environmental. Rests on: DH1, Renewal and highways through downtown. Source: US EPA, Heat Island Effect (Learn About Heat Islands).

**Historical** (bedrock, lasts a century)

- **DH1** · 1949–1974 · Renewal and highways through downtown. From the Housing Act of 1949 to the program's end in 1974, federal urban renewal cleared older downtown blocks across the country, and the 1956 interstate program routed highways through many of them. Cheap housing near downtown jobs was among what was lost.
  - Types: historical, political. Source: Housing Act of 1949, Title I; Federal-Aid Highway Act of 1956; University of Richmond, Renewing Inequality.

## On Pelham Street itself

**Economic** (changes over years)

- **EC1** · since 2018 · Rents up 40 percent as offices become lofts. Empty office floors are being converted to apartments that rent at the top of the market, and older walk-ups have raised rents to match. Wages for the jobs downtown have not kept pace, so rent takes more than half of many paychecks.
  - Types: economic. Rests on: H2, The rooming hotels come down.
- **EC2** · 2014 · A plasma center in the old department store. The plasma center pays about $40 a visit, more for new donors, up to twice a week. For people between paychecks it is the fastest legal cash downtown.
  - Types: economic.

**Political** (changes over decades)

- **P1** · 2021 · Night buses end at 11 p.m.. After ridership fell in 2020 the transit agency ended most routes at 11 p.m. Late shifts in hospitals, restaurants and warehouses still end after midnight, so the trip home is a ride-hail or a long walk.
  - Types: political.
- **P2** · state law · Landlord law: late fees and fast evictions. State law lets landlords charge a late fee of 10 percent of the rent after five days and file for eviction ten days after a missed payment. A short month becomes a fee, then a court date.
  - Types: political.

**Built & natural** (changes over generations)

- **E1** · pre-1950 · Walk-ups with no laundry hookups. Most of the older apartments were built without washer hookups, and landlords have not added them. Laundry means a trip to the laundromat with quarters or a card, several times a week for a family.
  - Types: environmental, economic.
- **E2** · 1964 · Parking where the homes stood. Much of the cleared land became surface lots and a five-level garage for county workers. Residents without a car pay the same meter rates as commuters for a short stop.
  - Types: environmental, political. Rests on: H1, Urban renewal clears the Pelham rowhouses.

**Social & cultural** (changes over generations)

- **S1** · 1988 on · Services clustered downtown. The shelter, a free clinic and two meal programs sit within two blocks of each other on Pelham, because other neighborhoods objected to them. People who need them stay close, and their days are organized around intake hours.
  - Types: social, political. Rests on: H2, The rooming hotels come down.
- **S2** · today · Doubling up. To keep up with rent, many households here are two or three earners on one lease: roommates, adult children, cousins. Each owes a share to whoever holds the lease, often by app the night before rent is due.
  - Types: social, economic. Rests on: EC1, Rents up 40 percent as offices become lofts.

**Historical** (bedrock, lasts a century)

- **H1** · 1962 · Urban renewal clears the Pelham rowhouses. A federal urban renewal grant paid the city to clear eleven blocks of rowhouses west of the courthouse for a civic center and parking. About 900 households were moved, most of them renters, and few were offered a place to come back to.
  - Types: historical, political. Rests on: DH1, Renewal and highways through downtown.
- **H2** · 1979–86 · The rooming hotels come down. Downtown had four single-room hotels where a worker could rent by the week without a deposit. They were demolished for office towers in the 1980s, and nothing that cheap replaced them. The shelter on Pelham opened in 1988.
  - Types: historical, economic.

## Patterns: the records the block's circumstances shape

A record from the block's households that matches a pattern (the first that matches, in this order; the rules are regular expressions) carries its id in `block_pattern` and the circumstances it links to in `context_ids`. Pattern ids and loop ids are separate: pattern R1 is not loop R1.

- **A1** Missed buses (fail): links P1; tagged when job_category matches `missed_bus`.
- **A2** Late-night rides (purchase): links P1; tagged when job_category matches `ride_hail_trip`.
- **A3** Rent short (fail): links EC1, P2; tagged when job_category matches `^housing\.rent$` and outcome matches `^(declined|failed|partial|abandoned|rescheduled)$`.
- **A4** Shares of the rent (bill): links S2, EC1; tagged when job_category matches `roommate_rent_share`.
- **A5** Laundromat (purchase): links E1; tagged when job_category matches `laundromat`.
- **A6** Shelter nights (unpaid): links S1, H2; tagged when job_category matches `shelter_night`.
- **A7** Plasma payments (income): links EC2; tagged when job_category matches `plasma_donation_payment`.
- **A8** Parking (bill): links E2; tagged when job_category matches `parking_fee`.

## Loops (hypotheses, not findings)

- **R1 Late-fee ladder** (reinforcing). A short month means a partial rent payment. The late fee makes next month's bill bigger, so the next payment is more likely to fall short too.
  - Rent paid in full → Short payments (−): Less rent paid in full means more short payments.
  - Short payments → Late fees owed (+): More short payments mean more late fees.
  - Late fees owed → Rent paid in full (−): More fees owed leave less to pay rent in full.
  - Pushed + by P2: State law allows a 10% fee after five days.
  - Pushed − by EC1: Rising rents make full payment harder.
  - Seen in the records of pattern A3.
- **B1 Doubling up** (balancing). When rent outruns one paycheck, a household takes on a roommate or a relative. The shared lease closes the gap, which holds the late-fee ladder back, at the cost of space.
  - Rent gap → Roommates on the lease (+): A bigger gap means more roommates.
  - Roommates on the lease → Shares paid in (+): More roommates mean more shares paid in.
  - Shares paid in → Rent gap (−): More shares shrink the gap.
  - Pushed + by EC1: Rents up 40% since 2018 widen the gap.
  - Seen in the records of pattern A4.
- **D1 Backup rides drain the budget** (reinforcing). When the bus doesn't come, a ride-hail fills in. Each backup ride spends cash that could have gone toward a car or a home closer to work, so the bus stays the only way and the next no-show costs again.
  - Buses that don't come → Paid backup rides (+): More no-shows mean more ride-hail backups.
  - Paid backup rides → Cash left for a car or a closer home (−): Backup rides spend the cash.
  - Cash left for a car or a closer home → Buses that don't come (−): Less cash left keeps the bus the only way, no-shows and all.
  - Pushed + by DW2: Routes that cancel trips make no-shows routine.
  - Pushed + by DH1: Highways and renewal moved cheap housing away from the jobs, so more trips depend on the bus.
  - Seen in the records of patterns A1, A2.
