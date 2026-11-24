> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.

# D3 Outer suburbs: Fox Hollow

**Composite**: an invented block drawn from documented US patterns, not a real place. Part of https://medianville.netlify.app/agents/districts.md, which explains the layers and the ids.

Block id `foxhollow`, on Fox Hollow Dr. Dairy farms subdivided after 1994, reached by a private toll road, and run by homeowners’ associations instead of a city.

The simulator puts 420 of the district's households on this block (`block_id = foxhollow` in households.csv and records.csv).

## Across the whole district (the district tier)

**Economic** (changes over years)

- **DW1** · 2025 · Child care priced like rent. Across the outer suburbs, two-earner families buy child care to cover long commutes. Nationally it averaged $13,184 a year in 2025, about 10% of a two-parent household's income and a third of a single parent's.
  - Types: economic, social. Rests on: DE1, Zoned for driving. Evidence: E081.

**Political** (changes over decades)

- **DW3** · 2025 · Errands that still need a counter. Government errands still mean a drive and a wait. In one state about 68% of driver's license transactions happen in person, and customers at a suburban office reported waits from half an hour to more than two hours, far above the agency's statewide average.
  - Types: political. Rests on: DE1, Zoned for driving. Evidence: E084, E085, E086.

**Built & natural** (changes over generations)

- **DE1** · 2001–2016 · Zoned for driving. Farmland kept giving way to development: American Farmland Trust counts about 11 million acres of farm and ranch land converted nationally from 2001 to 2016, most of it to low-density housing. Zoning keeps homes, shops and schools in separate areas, so almost every errand needs a car.
  - Types: environmental, political. Rests on: DH1, Interchanges reach the farms. Source: American Farmland Trust, Farms Under Threat (2020).

**Social & cultural** (changes over generations)

- **DW2** · 2025 · Caring for parents from a distance. Many families here care for an aging parent while both adults work. Family caregivers now spend about $11,508 a year out of pocket, about 31% of their income, and half have made a major financial sacrifice.
  - Types: social, economic. Evidence: E048, E049.

**Historical** (bedrock, lasts a century)

- **DH1** · 1956 · Interchanges reach the farms. The 1956 interstate program put highway exits in farm country within commuting distance of the city. Over the following decades, land near the interchanges turned into subdivisions and shopping centers, and the outer suburbs grew around the car.
  - Types: historical, political. Source: Federal-Aid Highway Act of 1956.

## On Fox Hollow itself

**Economic** (changes over years)

- **EC1** · today · Jobs 13 miles away, two cars needed. Most jobs are downtown or along the interstate, 13 miles or more by the Parkway. With two earners and no bus, a family needs two cars, and car payments and insurance are the second-largest bill after the mortgage.
  - Types: economic.
- **EC2** · 2026 · The reassessment raises escrow. The county reassessed every home last year. Mortgage servicers recalculated escrow, and monthly payments rose about $210 with no change in the loan.
  - Types: economic, political. Rests on: H1, The dairy farms are subdivided.

**Political** (changes over decades)

- **P1** · 2006 · The Parkway: a private toll road. The state leased the Parkway to a private operator for 50 years. There are no booths: cameras read plates and mail a bill, with a $4.50 administrative fee each time, and the fees double when a bill goes unpaid.
  - Types: political, economic.
- **P2** · 1996 · An HOA for every new subdivision. To avoid paying for new roads, pools and storm ponds, the county required each subdivision to form a homeowners' association. Dues pay for what a city would, and an association can fine and file liens.
  - Types: political. Rests on: H1, The dairy farms are subdivided.
- **P3** · today · Unincorporated: no city services. Fox Hollow was never annexed by a city. Trash, recycling and snow plowing come from private contractors billed to each household, and the county sheriff patrols from 13 miles away.
  - Types: political.

**Built & natural** (changes over generations)

- **E1** · 1990s · Cul-de-sacs, no sidewalks or bus. The streets were laid out as loops and dead ends, with no sidewalks to the school or the shops. Every trip is a drive, including the half-mile to school.
  - Types: environmental, political.

**Social & cultural** (changes over generations)

- **S1** · today · The activity economy. Children's evenings and weekends are filled with paid activities. The schedule is a status marker and a second job for whichever parent drives.
  - Types: social, cultural.

**Historical** (bedrock, lasts a century)

- **H1** · 1994–2008 · The dairy farms are subdivided. Two family dairies sold out as milk prices fell and land values rose. Builders platted them into cul-de-sacs of four-bedroom houses, sold with builder financing to families moving out from the inner suburbs.
  - Types: historical, environmental. Rests on: DH1, Interchanges reach the farms.

## Patterns: the records the block's circumstances shape

A record from the block's households that matches a pattern (the first that matches, in this order; the rules are regular expressions) carries its id in `block_pattern` and the circumstances it links to in `context_ids`. Pattern ids and loop ids are separate: pattern R1 is not loop R1.

- **F1** Toll bills (bill): links P1; tagged when job_category matches `^transportation\.(toll|toll_account_reload)$` and outcome matches `^completed$`.
- **F2** Unpaid tolls and fees (fail): links P1; tagged when fee_type matches `pay_by_plate` or job_category matches `^transportation\.toll` and outcome matches `^(declined|failed|partial|abandoned|rescheduled)$`.
- **F3** HOA dues (bill): links P2; tagged when job_category matches `hoa_dues`.
- **F4** Private trash pickup (bill): links P3; tagged when job_category matches `trash_bill`.
- **F5** School drop-off and pickup (unpaid): links E1; tagged when job_category matches `school_(dropoff|pickup)$`.
- **F6** Lessons and activities (bill): links S1; tagged when job_category matches `lessons_tuition|youth_sports_registration|private_school_tuition|after_school_fee`.
- **F7** Mortgage and escrow (bill): links EC2, H1; tagged when job_category matches `property_tax_escrow|^housing\.mortgage$`.
- **F8** Car payments (bill): links EC1, E1; tagged when job_category matches `^transportation\.car_payment$`.

## Loops (hypotheses for the next run to test)

- **R1 Plate-bill pileup** (reinforcing). A toll bill that goes unpaid gets a fee, and the fee doubles. The bigger bill is harder to pay on time, so more of the next bills go unpaid.
  - Bills paid on time → Unpaid tolls (−): Fewer bills paid on time means more unpaid tolls.
  - Unpaid tolls → Fees added (+): More unpaid tolls mean more fees.
  - Fees added → Bills paid on time (−): More fees make the next bill harder to pay on time.
  - Pushed + by P1: The concession sets a $4.50 fee that doubles.
  - Seen in the records of pattern F2.
- **B1 Carpool** (balancing). School trips by car pile up for every family. Neighbors trade drop-offs, which cuts each family's trips and eases the load.
  - School trips by car → Carpools with neighbors (+): More trips mean more carpools.
  - Carpools with neighbors → Trips per family (−): More carpools mean fewer trips per family.
  - Trips per family → School trips by car (+): Fewer trips per family mean fewer school trips by car.
  - Pushed + by E1: No sidewalks make every trip a drive.
  - Seen in the records of pattern F5.
- **D1 Buying back time** (reinforcing). Long drives eat the hours between work, school and home, so families pay for care and activities to cover them. Paying for those takes more hours at work, which leaves even less slack for the driving.
  - Hours lost to driving → Paid care and activities (+): More hours in the car mean more paid care to cover them.
  - Paid care and activities → Hours worked to pay for them (+): More paid care means more hours worked to pay for it.
  - Hours worked to pay for them → Hours lost to driving (+): More hours at work leave less slack in the day.
  - Pushed + by DW1: Child care priced like rent makes every covered hour expensive.
  - Pushed + by DE1: Zoning that separates everything puts more miles in every day.
  - Seen in the records of patterns F5, F6.
