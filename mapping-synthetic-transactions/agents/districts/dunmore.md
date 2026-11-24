> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.

# D5 Rural town: Main Street, Dunmore

**Composite**: an invented block drawn from documented US patterns, not a real place. Part of https://medianville.netlify.app/agents/districts.md, which explains the layers and the ids.

Block id `dunmore`, on Main St. A grain-and-rail town that lost its railroad, its bank and its grocery; the mobile home park was sold to an investor in 2019.

The simulator puts 380 of the district's households on this block (`block_id = dunmore` in households.csv and records.csv).

## Across the whole district (the district tier)

**Economic** (changes over years)

- **DW1** · 2023 · Cash where the banks left. Across the rural towns, banking means a drive or a fee. About two-thirds of unbanked households use only cash, and an out-of-network ATM withdrawal averages a record $4.86.
  - Types: economic, social. Evidence: E011, E014.
- **DW2** · 2016 · Home care hours go unfilled. Approved home care often goes unstaffed. In one agency survey, 85% lacked staff to cover every shift and 43% left shifts unfilled at least seven times a month; one rural state counted about 11,000 approved hours unstaffed each week.
  - Types: economic, social. Rests on: DH1, Fewer, bigger farms. Evidence: E053, E054, E055.
- **DW3** · 2024 · Called in on a day off. The town's jobs are thin and the stores are short-staffed. Workers describe being called in at the last minute, even on days off, and scrambling for child care when they are.
  - Types: economic. Evidence: E040, E047.

**Political** (changes over decades)

- **DW4** · 2026 · Dialysis an hour away. Rural residents average about 14 miles to the nearest dialysis unit, but closures stretch that fast: when one small hospital closed its unit, a patient's time on the road tripled to more than nine hours a week.
  - Types: political, environmental. Rests on: DH1, Fewer, bigger farms. Evidence: E051, E052.

**Built & natural** (changes over generations)

- **DE1** · ongoing · Homes on rented land. Manufactured homes are far more common in rural towns than in cities. Many sit on rented lots in parks, so the owners own the house but not the ground under it, and moving the house is rarely practical.
  - Types: environmental, social. Rests on: DH1, Fewer, bigger farms. Source: Census American Community Survey (housing type), with the Housing Assistance Council's rural tabulations; CFPB, Manufactured Housing Finance (2021).

**Historical** (bedrock, lasts a century)

- **DH1** · 1935–today · Fewer, bigger farms. The number of US farms peaked at about 6.8 million in 1935 and is now about 1.9 million, on larger acreages with fewer workers. Towns that served many small farms lost customers, rail traffic and young families as the farms consolidated.
  - Types: historical, economic. Source: USDA Census of Agriculture; USDA ERS farm counts.

## On Main Street, Dunmore itself

**Economic** (changes over years)

- **EC1** · 2019 · The park is sold to an investor. The family that owned Prairie View sold it to an out-of-state investment firm in 2019. Lot rent has gone up four times since. Residents own their homes but not the land, and moving a home costs more than it is worth.
  - Types: economic.
- **EC2** · 2016 · The last bank branch closes. The last branch closed in 2016. The two ATMs in town belong to other networks and charge $3 to $5 a withdrawal, and many older residents still pay with cash.
  - Types: economic.
- **EC3** · 2014 · Dollar stores replace the grocery. The independent grocery closed in 2014, a year after the second dollar store opened. Fresh food now means a 19-mile drive, so most shopping is canned and packaged food from the dollar store.
  - Types: economic.

**Political** (changes over decades)

- **P1** · state program · The state pays Medicare premiums for low incomes. For older residents with low incomes, the state pays the Medicare Part B premium, about $200 a month. Enrollment takes paperwork that many eligible people never finish.
  - Types: political.
- **P2** · state rates · Medicaid home care rates. Medicaid pays home-care agencies about $19 an hour. Aides earn far less, with no pay for the 35-mile drive between clients, so visits are short and often cancelled.
  - Types: political, economic.

**Built & natural** (changes over generations)

- **E1** · today · Thirty-five miles to the hospital. The nearest hospital and specialists are in Medianville, 35 miles on a two-lane highway. A routine appointment takes most of a day and someone to drive.
  - Types: environmental.

**Social & cultural** (changes over generations)

- **S1** · today · Aging in place. Most young adults left for Medianville or farther. Older residents stay in their homes, and care comes from a spouse, a neighbor, a church member or a relative who drives in.
  - Types: social, cultural. Rests on: H1, The railroad is abandoned.

**Historical** (bedrock, lasts a century)

- **H1** · 1979 · The railroad is abandoned. Dunmore grew up around a rail siding and a grain elevator. The railroad abandoned the branch in 1979, the elevator went to trucks, and Main Street lost the trade that came with the trains.
  - Types: historical, economic. Rests on: DH1, Fewer, bigger farms.

## Patterns: the records the block's circumstances shape

A record from the block's households that matches a pattern (the first that matches, in this order; the rules are regular expressions) carries its id in `block_pattern` and the circumstances it links to in `context_ids`. Pattern ids and loop ids are separate: pattern R1 is not loop R1.

- **N1** Lot rent (bill): links EC1; tagged when job_category matches `lot_rent`.
- **N2** ATM fees (bill): links EC2; tagged when fee_type matches `out_of_network_atm`.
- **N3** Dollar store groceries (purchase): links EC3; tagged when job_category matches `^food\.dollar_store$`.
- **N4** Medicare help from the state (income): links P1; tagged when job_category matches `medicare_part_b_state_buy_in`.
- **N5** Home-care visits (unpaid): links P2, S1; tagged when job_category matches `personal_care_aide_visit|home_health_nurse_visit`.
- **N6** Care from neighbors and kin (unpaid): links S1, E1; tagged when job_category matches `caregiving_visit|escort_to_appointment`.
- **N7** Car repairs (bill): links E1; tagged when job_category matches `car_repair|car_wont_start|jump_start|tow_and_roadside`.

## Loops (hypotheses for the next run to test)

- **R1 Lot-rent squeeze** (reinforcing). Each lot-rent increase leaves less cash. With less cash, moving the home out of the park is out of reach, so the owner can keep raising the rent.
  - Rent increases → Cash left after rent (−): More increases leave less cash.
  - Cash left after rent → Able to move out (+): More cash makes moving possible.
  - Able to move out → Rent increases (−): Fewer able to leave means increases stick.
  - Pushed + by EC1: An investor owner prices to what residents cannot escape.
  - Seen in the records of pattern N1.
- **B1 Neighbor care** (balancing). When an older neighbor needs care, others step in to visit and drive. Their help shrinks the unmet need, which holds the load in balance, until the helpers age too.
  - Care needed → Neighbors and kin help (+): More need brings more help.
  - Neighbors and kin help → Unmet care (−): More help leaves less unmet care.
  - Unmet care → Care needed (+): Unmet care turns into more need.
  - Pushed − by P2: Short, cancelled aide visits leave more to neighbors.
  - Seen in the records of pattern N6.
- **D1 The care gap** (reinforcing). When no aide comes, a family member covers the shift and loses work hours. The lost pay leaves less money for paid care, so more of the next week's shifts go unfilled too.
  - Aide shifts unfilled → Family member covers (+): More unfilled shifts mean more care from family.
  - Family member covers → Family work hours lost (+): More covering means more work hours lost.
  - Family work hours lost → Money for paid care (−): Lost hours leave less money for paid care.
  - Money for paid care → Aide shifts unfilled (−): Less money for paid care leaves more shifts unfilled.
  - Pushed + by DW2: Approved hours often have no aide to fill them.
  - Pushed + by DH1: Fewer working-age people stayed, so fewer are left to staff care.
  - Seen in the records of patterns N5, N6.
