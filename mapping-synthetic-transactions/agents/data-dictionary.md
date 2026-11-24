> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.

# Data dictionary

Every column of the tables in a Medianville run, what each value means, and where that is written down. Columns nothing in the repository describes are marked *undocumented*: read their values, not a meaning. Counts are from the baseline day, `v2-2027-03-03` (202,402 records), unless a column says otherwise. Every table is synthetic: no row describes a real person, household, business or place.

## The files in a run

A run is one zip (download links in https://medianville.netlify.app/agents/runs.md). Inside a v2 zip, under `medianville_<date>/`:

- `records.csv`: every record of the day, one job someone was trying to get done, in time order.
- `households.csv`, `persons.csv`, `organizations.csv`: who is in the city.
- `household_ledger.csv`: each household's opening and closing balances; the money reconciles.
- `public_services_context.csv`, `assumptions.csv`, `summary.md`: what public services cost, every estimate and its source, and the day in figures.
- `blocks.json`: the systems lens's mapped blocks (https://medianville.netlify.app/agents/districts.md).
- `simulate.py`, `medianville_sim/`: the simulator. `SHA256SUMS`: the SHA-256 of every file.
- The baseline day only: `detailed_overrides.csv` and `detailed_sample.csv`, the hand-written text and the hand-written records on their own.

The v1 zip keeps its tables under `medianville/out/` and its 500 hand-written records in `detailed_sample_500.csv`. The carried month adds `links.csv` to each day (https://medianville.netlify.app/agents/month.md).

## Units and formats

- Money: US dollars, two decimals in records.csv and household_ledger.csv, whole dollars for `annual_income` and `monthly_housing_cost`. Dollar figures are 2027 dollars where the summary says so (the median household income).
- Time: minutes (`time_minutes`, `wait_minutes`); `timestamp_local` is `YYYY-MM-DDTHH:MM:SS`, local to the city.
- Distance: miles (`travel_miles`).
- Lists inside a cell are separated by `;`. Empty means none.
- Text is UTF-8 CSV with a header row.

## Ids

| Id | Format | Example | Table |
|---|---|---|---|
| Record | `R` + 7 digits | `R0000001` | records.csv (restarts in every run and every day) |
| Household | `H` + 5 digits | `H05202` | households.csv |
| Person | `P` + 6 digits | `P011429` | persons.csv |
| Organization | `O` + 4 digits | `O1076` | organizations.csv (outside parties included) |
| Run | `v<version>-<date>` | `v2-2027-03-03` | data/runs/manifest.json |
| Block | a lowercase name | `larkin` | blocks.json `blocks[].id` |
| Pattern | letters and a number, per block | `R3` | blocks.json `patterns[].id` (unique within a block, not across blocks) |
| Circumstance | letters and a number, per block | `EC1`, `DH1` | blocks.json `contexts[].id`; the D… ids are the district tier |
| Evidence | `E` + 3 digits | `E009` | evidence/evidence.csv on GitHub (third-party material) |

## Districts

Shares are the prompt's targets; the baseline day's are in its summary (30.5 / 19.7 / 21.6 / 14.3 / 7.9 / 6.0%). Each district has one mapped block in the systems lens.

| Code | District | Share of residents | Character | Mapped block |
|---|---|---|---|---|
| D1 | Downtown and core neighborhoods | 31% | Dense, transit-served, renters, government offices, night shifts | Pelham Street (`pelham`) |
| D2 | Inner suburbs | 20% | Older housing and apartments, immigrant gateways, airport and service jobs | Larkin Avenue (`larkin`) |
| D3 | Outer suburbs | 22% | New-build subdivisions, car-dependent, big-box retail, long commutes | Fox Hollow (`foxhollow`) |
| D4 | Satellite city | 13% | Historic downtown, regional hospital, county seat, mixed old and new industry | Mill Street, Ashford Mills (`ashford`) |
| D5 | Rural town | 8% | County seat of a few thousand, dollar stores, thin services, long drives | Main Street, Dunmore (`dunmore`) |
| D6 | Open country | 6% | Farms, scattered homes, well water, distance to everything | Route 9 Crossroads (`crossroads`) |

Every published run, v1 included, has exactly these columns in each table.

## records.csv

202,402 rows on the baseline day, 34 columns.

| Column | Meaning | Source |
|---|---|---|
| `record_id` | One row per transaction, encounter or job attempt. `R` and 7 digits; the table is in time order. Ids start again at R0000001 in every run (and every day of the month), so name a record by its run and id. | prompt, day README, month record |
| `timestamp_local` | When the record started (the explorer's "Started"), as `YYYY-MM-DDTHH:MM:SS` on the simulated date. The engine keeps every record inside the day's 1,440 minutes. | explorer, engine.py |
| `record_type` | One of 12 kinds (values below). The prompt lists them without defining each. | prompt |
| `job_category` | `category.kind`, for example `food.grocery_snap_purchase`. 383 distinct on the v2 baseline day (367 in v1). Categories below. | v1 README, summary |
| `job_statement` | "When [situation], I want to [motivation], so I can [outcome]." Written from the actor's point of view, in plain words. Templated, except the hand-written records. | prompt, v1 README |
| `actor_person_id` | A person id (`P…`). The prompt writes `job_statement` from the actor's point of view; no fuller definition is written down. | v1 README, prompt |
| `household_id` | A household id (`H…`), as in households.csv. Otherwise undocumented. | v1 README |
| `from_party_id` | The party the record goes from: `P…` people, `H…` households, `O…` organizations, including outside parties such as the Treasury, card networks and "Customers (general public)". The viewer draws each record as an arc from one party to the other. | v1 README, README |
| `to_party_id` | The party the record goes to; ids as in `from_party_id`. | v1 README, README |
| `beneficiary_person_id` | A person id. The record-reading tool labels it "For" when it differs from the actor. Otherwise undocumented. | sample_records.py |
| `district` | District code, D1 to D6 (table below). | prompt |
| `channel` | in_person, online, app, phone, mail or automatic. | prompt |
| `payment_method` | cash, debit, credit, prepaid, ebt_snap, ebt_cash, wic, check, ach, p2p_app, bnpl, money_order, paycard, payroll_deduction, insurance or none. | prompt |
| `amount_gross` | The face amount, in dollars: the price including sales tax and before fees; for a transfer the amount moved; for a prescription the cash price; for a public service the full cost of providing it. | v1 README |
| `amount_paid_by_user` | What left the person's pocket, fees included (often 0). | v1 README, prompt |
| `amount_paid_by_third_party` | What an insurer, program or agency paid. | v1 README |
| `third_party_payer` | Names who paid `amount_paid_by_third_party`: the program, insurer or agency. | v1 README, prompt |
| `funding_level` | federal, state, local, mixed, private or philanthropic. | prompt |
| `imputed_public_cost` | The full cost of a public service whether or not anyone was charged; the estimates are in assumptions.csv. | v1 README, prompt |
| `sales_tax` | Included in `amount_gross`, at 7% on taxable goods (groceries and prescriptions exempt). | v1 README, config.py |
| `fee_type` | The kind of fee, such as `overdraft_fee` or `late_fee`; `+` joins two (`late_fee+postage`). | text.py |
| `fee_amount` | The fee in dollars. Fees include overdraft, late, ATM, check-cashing, money-order, convenience, delivery, card-interest and loan finance charges. A fee above 0 adds the `fee` friction tag. | summary, engine.py |
| `time_minutes` | Time spent, in minutes (the explorer's "Time spent"). It counts the wait but not the travel. | explorer, README, engine.py |
| `wait_minutes` | Waiting, in minutes (the explorer's "Waiting"). A wait of 20 minutes or more adds the `wait` friction tag. | explorer, engine.py |
| `travel_miles` | Travel, in miles. Distances come from a district-to-district table, so some single trips look long for the errand. 24 miles or more adds the `distance` friction tag. | explorer, v1 README, engine.py |
| `travel_mode` | The explorer's "Travel mode". Otherwise undocumented (values below). | explorer |
| `outcome` | completed, partial, declined, abandoned, rescheduled or failed. A record "didn't work" when it is a `failed_attempt` or ended declined, abandoned, failed or rescheduled; partial counts as worked. | prompt, README |
| `friction_tags` | What got in the way, `;`-separated, from the 22 tags below; empty for none. The engine adds `fee`, `wait` and `distance` by rule (above). | prompt, engine.py |
| `lens_tags` | Which perspective would flag this record, `;`-separated (values below). Not the systems lens: that is `block_id`, `block_pattern` and `context_ids`. | prompt, README |
| `related_record_id` | Links records: every paycheck has linked rows for income tax withholding and FICA; a Social Security deposit shows the gross benefit and the Part B premium is a linked row; a retry points to the attempt that failed. | v1 README |
| `narrative` | One short sentence of context. Hand-written narratives start with `[detailed]` (300 on the v2 baseline day, 500 in v1). | prompt, day README |
| `block_id` | The block whose household made the record, or empty. | blocks.py |
| `block_pattern` | The first pattern in that block the record matches, or empty. | blocks.py |
| `context_ids` | The circumstances that pattern links to, separated by `;`. | blocks.py |

**`record_type` values:** `purchase` 79,168, `public_service_encounter` 40,071, `bill_payment` 30,738, `non_monetary_job` 13,234, `transfer` 8,553, `income` 6,601, `tax` 5,554, `insurance_claim` 5,502, `failed_attempt` 5,009, `benefit_issuance` 3,607, `b2b` 3,140, `benefit_redemption` 1,225.

**`outcome` values:** `completed` 194,366, `partial` 2,064, `failed` 2,018, `declined` 1,851, `abandoned` 1,585, `rescheduled` 518.

**`friction_tags` values:** (empty) 171,135, `fee` 10,096, `distance` 6,492, `wait` 3,924, `insufficient_funds` 3,615, `no_transit` 2,309, `caregiving_conflict` 2,076, `other` 1,478, `schedule_volatility` 723, `digital_barrier` 691, `price_spike` 535, `out_of_stock` 463, `pending_hold` 421, `scam_attempt` 390, `disability_access` 357, `repeat_trip` 322, `paperwork` 264, `hours_mismatch` 205, `outage` 119, `language` 116, `missing_document` 60, `eligibility_confusion` 22, `benefits_cliff` 8.

**`lens_tags` values:** (empty) 77,861, `public_finance` 57,585, `consumer_finance` 21,952, `aging` 20,690, `land_use` 17,484, `education` 16,915, `labor` 16,774, `disability` 16,071, `family_care` 14,601, `rural` 12,038, `health_cost` 9,399, `housing` 6,531, `small_business` 3,675, `digital_access` 3,058, `farmworker` 440.

**`channel` values:** `in_person` 135,370, `automatic` 40,739, `online` 13,903, `app` 8,795, `phone` 2,282, `mail` 1,313.

**`payment_method` values:** `none` 48,673, `credit` 41,713, `debit` 40,696, `ach` 22,690, `cash` 18,441, `prepaid` 11,429, `payroll_deduction` 7,415, `p2p_app` 3,944, `insurance` 2,938, `check` 2,581, `ebt_snap` 1,426, `wic` 181, `ebt_cash` 114, `paycard` 69, `money_order` 57, `bnpl` 35.

**`funding_level` values:** (empty) 149,025, `mixed` 30,004, `federal` 18,650, `private` 2,503, `local` 1,035, `state` 704, `philanthropic` 481.

**`travel_mode` values:** (empty) 97,970, `car` 77,804, `transit` 12,281, `school_bus` 7,285, `walk` 3,890, `ride_from_family_or_friend` 2,762, `bike` 154, `carpool` 131, `ambulance` 80, `paratransit` 45.

**`job_category` categories (the part before the dot):** `food` 61,737, `discretionary` 27,048, `transportation` 22,505, `children_education` 16,912, `income` 14,863, `health` 13,775, `money_services` 11,707, `care_and_household` 10,716, `utilities` 7,232, `housing` 6,461, `business` 4,008, `giving_faith` 2,070, `work` 1,611, `civic_legal` 932, `public_services` 825.

**`district` values:** `D1` 65,849, `D2` 40,920, `D3` 40,592, `D4` 28,792, `D5` 15,344, `D6` 10,905.

**`block_id` values:** (empty) 187,742, `foxhollow` 3,625, `pelham` 2,964, `larkin` 2,437, `crossroads` 2,295, `dunmore` 1,844, `ashford` 1,495.

## households.csv

43,499 rows on the baseline day, 16 columns.

| Column | Meaning | Source |
|---|---|---|
| `household_id` | `H` and 5 digits. | v1 README |
| `district` | D1 to D6. | prompt |
| `weight` | 1 for the full city and larger when you run a sample (written as 1 ÷ the run's scale). Every published run is the full city. | v1 README, output.py |
| `household_type` | Values below. People in nursing homes, the jail, dorms, shelters and group homes are one-person units with a type starting `group_quarters:`. The other codes are not defined one by one. | v1 README |
| `size` | The number of members. | output.py |
| `annual_income` | The household's annual income, rounded to the dollar; the summary gives its median in 2027 dollars. | output.py, summary |
| `income_source_mix` | Each source's share of income, `source:share` separated by `;`, largest first, sources under 0.5% left out; `none` with no income. Sources: wages, self_employment, social_security, ssi, pension, investments_and_retirement_draws, unemployment_insurance, va_compensation, child_support, tanf. | output.py |
| `alice_status` | poverty, alice or above. Below United For ALICE's survival-budget threshold means in poverty or employed but unable to afford basics. | prompt |
| `banked_status` | banked, underbanked or unbanked. | prompt |
| `housing_tenure` | undocumented (values below). | — |
| `monthly_housing_cost` | undocumented; whole dollars. | output.py |
| `vehicles` | undocumented; a count (values below). | — |
| `internet_at_home` | yes, no or mobile_only. | prompt |
| `primary_language` | undocumented (values below). | — |
| `notes` | Free text, often empty; households with SNAP carry `snap_monthly=<n>`. | output.py |
| `block_id` | The mapped block the household lives on, or empty. | v1 README |

**`household_type` values:** `alone` 11,382, `married_nokids` 10,635, `married_kids` 6,850, `adult_child` 3,488, `single_parent` 2,938, `roommates` 2,515, `multigen` 2,119, `group_quarters:college_dorm` 1,100, `cohab_kids` 1,030, `other_family` 443, `group_quarters:nursing_home` 370, `group_quarters:jail` 240, `group_quarters:group_home` 110, `group_quarters:shelter` 100, `group_quarters:assisted_living` 80, `group_quarters:residential_treatment` 50, `group_quarters:h2a_worker_housing` 49.

**`housing_tenure` values:** `owner_with_mortgage` 16,034, `renter` 14,589, `owner_free_and_clear` 10,777, `group_quarters` 2,099.

**`alice_status` values:** `above` 24,646, `alice` 13,572, `poverty` 5,281.

**`banked_status` values:** `banked` 35,970, `underbanked` 5,400, `unbanked` 2,129.

**`internet_at_home` values:** `yes` 35,632, `mobile_only` 4,676, `no` 3,191.

**`vehicles` values:** `1` 17,491, `2` 13,476, `0` 6,125, `3` 5,238, `4` 1,147, `5` 22.

**`primary_language` values:** `English` 36,306, `Spanish` 4,179, `Korean` 238, `Nepali` 234, `Hindi` 233, `Chinese` 227, `Tagalog` 226, `Vietnamese` 225, `Gujarati` 217, `Arabic` 170, `Russian` 161, `Portuguese` 147, `Polish` 146, `Bosnian` 138, `Ukrainian` 130, `Somali` 98, `French` 97, `Amharic` 85, `Haitian Creole` 73, `Swahili` 72, `Marshallese` 50, `Karen` 47.

## persons.csv

99,743 rows on the baseline day, 19 columns.

| Column | Meaning | Source |
|---|---|---|
| `person_id` | `P` and 6 digits. | v1 README |
| `household_id` | The person's household. | output.py |
| `age` | undocumented. | — |
| `birth_cohort` | The generation and birth year, for example `millennial_1987`. Generations by birth year: gen_alpha 2013 on, gen_z 1997, millennial 1981, gen_x 1965, baby_boomer 1946, silent 1928, greatest before. | v1 README, config.py |
| `sex` | undocumented (F or M). | — |
| `race_ethnicity` | undocumented (values below). | — |
| `relationship_to_head` | undocumented (values below). | — |
| `education` | undocumented (values below; `not_applicable` when none is set). | output.py |
| `disability` | none, or the type (values below). | prompt |
| `health_coverage` | undocumented (values below). | — |
| `employment_status` | undocumented (values below). | — |
| `occupation` | undocumented; free text, such as `line cook`. | — |
| `employer_org_id` | The employer's organization id, or empty. | output.py |
| `industry_sector` | The employer's sector: one of the 21 sectors of the prompt's economy table, or empty when none is set. | prompt |
| `union_member` | yes or no. | prompt |
| `work_schedule` | fixed, variable, night or none. | prompt |
| `pay_cadence` | weekly, biweekly, semimonthly, monthly, irregular or none. | prompt |
| `caregiver_for` | The person ids this person cares for, `;`-separated, or none. | prompt, output.py |
| `benefits_received` | `;`-separated, or none. Social Security and SSDI carry their pay day: `(pay:3rd)` for long-time beneficiaries, people who also get SSI and people whose Medicare premium the state pays; otherwise `(pay:wed2)`, `(pay:wed3)` or `(pay:wed4)`, the second, third or fourth Wednesday, by birthday (1st to 10th, 11th to 20th, 21st on). SSI and VA compensation `(pay:1st)`; SNAP `(issue_day:N)`, the day of the month it is loaded. | output.py, population.py, summary |

**`sex` values:** `F` 51,108, `M` 48,635.

**`race_ethnicity` values:** `white_non_hispanic` 55,989, `hispanic` 18,560, `black_non_hispanic` 12,618, `asian_non_hispanic` 6,669, `multiracial_or_other` 5,339, `american_indian_alaska_native` 568.

**`relationship_to_head` values:** `head` 41,400, `spouse` 21,173, `child` 20,693, `adult_child` 6,084, `unmarried_partner` 2,144, `resident` 2,099, `roommate` 2,074, `grandchild` 2,045, `parent` 1,211, `child_in_law` 444, `sibling` 251, `other_relative` 125.

**`education` values:** `not_applicable` 22,738, `high_school` 19,294, `some_college` 16,696, `bachelor` 16,100, `graduate` 10,383, `less_than_high_school` 7,998, `associate` 6,534.

**`disability` values:** `none` 85,629, `ambulatory` 3,842, `cognitive` 3,400, `hearing` 1,991, `independent_living` 1,594, `multiple` 1,442, `vision` 1,074, `self_care` 771.

**`health_coverage` values:** `employer` 46,064, `medicaid` 13,782, `uninsured` 10,055, `medicare_advantage` 8,627, `medicare` 7,472, `marketplace` 6,995, `other_private` 3,814, `medicare_medicaid_dual` 2,356, `va` 468, `military` 110.

**`employment_status` values:** `employed_full_time` 36,619, `child` 20,913, `retired` 16,428, `not_in_labor_force` 9,275, `employed_part_time` 8,418, `student` 3,298, `self_employed` 2,740, `unemployed` 2,052.

**`work_schedule` values:** `none` 51,966, `fixed` 33,516, `variable` 11,754, `night` 2,507.

**`pay_cadence` values:** `none` 51,966, `biweekly` 23,126, `weekly` 10,707, `semimonthly` 7,553, `monthly` 3,651, `irregular` 2,740.

## organizations.csv

1,820 rows on the baseline day, 9 columns.

| Column | Meaning | Source |
|---|---|---|
| `org_id` | `O` and 4 digits; outside parties included. | v1 README |
| `name` | Invented, like every business and local agency; federal programs and agencies keep their real names. | day README, v1 README |
| `org_type` | business, nonprofit, government, religious or financial. | prompt |
| `sector` | The sector (values below). | prompt |
| `district` | D1 to D6, or `outside` for parties outside the city. | output.py |
| `size_employees` | undocumented; empty for outside parties. | output.py |
| `accepts` | The payment methods it takes, `;`-separated. | prompt |
| `hours` | undocumented; `HH:MM-HH:MM`. | — |
| `notes` | Free text; employers in the city carry `medianville_residents_on_staff=<n>`. | output.py |

**`org_type` values:** `business` 1,486, `religious` 120, `government` 97, `financial` 68, `nonprofit` 49.

**`district` values:** `D1` 489, `D3` 410, `D2` 360, `D4` 278, `D5` 142, `outside` 79, `D6` 62.

**`sector` values:** `Other services (repair, salons, religious organizations)` 337, `Accommodation and food services` 278, `Retail trade` 250, `Health care and social assistance` 223, `Construction` 148, `Professional, scientific and technical services` 123, `Finance and insurance` 111, `State and local government (including public schools)` 75, `Administrative and support services` 44, `Wholesale trade` 37, `Real estate` 34, `Manufacturing` 30, `Transportation and warehousing` 24, `Arts, entertainment and recreation` 23, `Private educational services` 21, `Federal government` 19, `Information` 19, `Agriculture, forestry and fishing` 11, `Many parties (not one organization)` 5, `Management of companies` 4, `Utilities and mining` 4.

## household_ledger.csv

43,499 rows on the baseline day, 20 columns.

| Column | Meaning | Source |
|---|---|---|
| `household_id` | The household. | output.py |
| `wallets` | The number of the household's wallets. Otherwise undocumented. | output.py |
| `open_checking` | Checking at the start of the day, in dollars, summed over the household's wallets; the same for each `open_` and `close_` column. | output.py |
| `open_cash` | Cash at the start of the day. | output.py |
| `open_prepaid` | Prepaid cards at the start of the day. | output.py |
| `open_savings` | Savings at the start of the day. | output.py |
| `open_card_debt` | Credit card balance owed at the start of the day. | output.py |
| `inflows` | Money in during the day. | output.py |
| `outflows` | Money out during the day. | output.py |
| `close_checking` | Checking at the end of the day. | output.py |
| `close_cash` | Cash at the end of the day. | output.py |
| `close_prepaid` | Prepaid cards at the end of the day. | output.py |
| `close_savings` | Savings at the end of the day. | output.py |
| `close_card_debt` | Credit card balance owed at the end of the day. | output.py |
| `open_net` | checking + cash + prepaid + savings − card debt, at the start of the day. | output.py |
| `close_net` | The same at the end of the day. | output.py |
| `reconciles` | yes when `open_net + inflows − outflows` equals `close_net` to within 6 cents. "The money reconciles." | output.py, day README |
| `snap_open` | The SNAP balance at the start of the day. | output.py |
| `snap_close` | The SNAP balance at the end of the day. | output.py |
| `could_cover_400_emergency` | yes or no. The SHED anchor: 63% of adults would cover a $400 emergency with cash or its equivalent; the run solves a liquid-funds threshold ($4,263 on the baseline day) or $400 free on a card paid in full. | output.py, summary |

## public_services_context.csv

47 rows on the baseline day, 5 columns.

| Column | Meaning | Source |
|---|---|---|
| `agency_or_service` | One row per agency or service, with its approximate daily operating cost and main funding source, so analysts can see the full public budget behind the day. | prompt |
| `level` | federal, state or local. | prompt |
| `daily_operating_cost_estimate` | The approximate daily operating cost, in dollars. | prompt |
| `main_funding_source` | The main funding source; free text. | prompt |
| `notes` | undocumented; free text. | — |

## assumptions.csv

64 rows on the baseline day, 4 columns.

| Column | Meaning | Source |
|---|---|---|
| `assumption` | Every estimate, its value, a one-line rationale, and whether it is an anchor or an estimate. | v1 README |
| `value` | The value. | prompt |
| `rationale` | A one-line rationale. | v1 README |
| `source_or_estimate` | Whether it is an anchor or an estimate, and its source. | v1 README, prompt |

## Sources

- **prompt**: the generator prompt the first run was made from, https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/01-one-day/medianville-transaction-generator-prompt.md ("Output files")
- **v1 README**: the README.md inside the v1 zip, https://raw.githubusercontent.com/jas0nmjames/playground/main/mapping-synthetic-transactions/data/medianville_2027-03-03.zip ("Reading records.csv")
- **day README**: the README.md inside each v2 zip ("Files"); see https://medianville.netlify.app/agents/runs/v2-2027-03-03.md
- **summary**: the run's summary.md; the baseline day's is in https://medianville.netlify.app/agents/runs/v2-2027-03-03.md
- **README**: the project README, https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/README.md
- **explorer**: the label the data explorer gives the column, https://medianville.netlify.app/explorer/
- **output.py**: the code that writes the tables, https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sim/medianville_sim/output.py
- **engine.py**: the code that writes each record, https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sim/medianville_sim/engine.py
- **blocks.py**: the code that tags records with the systems lens's blocks, https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sim/medianville_sim/blocks.py
- **population.py**: https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sim/medianville_sim/population.py
- **config.py**: https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sim/medianville_sim/config.py
- **text.py**: https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sim/medianville_sim/text.py
- **sample_records.py**: the tool that prints records as cards for reading, https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/tools/sample_records.py
- **month record**: https://medianville.netlify.app/agents/month.md
