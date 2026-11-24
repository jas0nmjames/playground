# Synthetic Mid-America: City Design v0.1

Nov 16, 2026 · @Jason James

## Purpose and principles

Medianville is a fictional city of 100,000 people whose residents match the US as a whole, built to generate one ordinary day of transactions and mine them for jobs that go badly at the margins.

- **People are national, places are local.** Households come from national survey data, not from any one city. Each district borrows its feel from real places within driving distance of Fayetteville, GA, so findings can be checked in person.
- **Every transaction is a job.** A purchase, a bill, a form or a wasted trip is recorded as someone trying to get something done, with its cost in money, time and effort.
- **Failures count.** Declined cards, closed offices, abandoned carts and repeat trips are transactions too; they are often the best project leads.
- **Real places are for texture, not for weights.** A visit can add a story or a friction type. It never changes the population mix, which stays tied to national data.

## Scale and population

Medianville has 100,000 residents in roughly 40,000 households, sampled from the Census Bureau's American Community Survey microdata (PUMS) and weighted to the whole country.

| Layer | Count (approx.) | Built from |
| --- | --- | --- |
| Residents | 100,000 | ACS PUMS person records |
| Households | \~40,000 | ACS PUMS household records, kept whole so ages, incomes and jobs inside a home stay consistent |
| Jobs held by residents | \~48,000 | National industry mix (see Economy) |
| Businesses and public agencies | Open question | Census County Business Patterns, scaled to 100,000 people |

- Drawing whole households keeps race, income, age, disability, household type, language, commute mode and housing tenure realistic together, not one at a time.
- Use a fixed random seed so the same Medianville can be rebuilt and compared across runs.
- 100,000 keeps one day of transactions small enough to read samples by hand. Scale up only after the pipeline works.

## Districts

Medianville has six districts sized to the national split of 31% urban core, 55% suburban and small metro, and 14% rural ([Pew Research Center](https://www.pewresearch.org/social-trends/2018/05/22/demographic-and-economic-trends-in-urban-suburban-and-rural-communities/)); how each band divides into districts is a design choice.

| District | Share of residents | Pew band | Character | Real places to visit (from Fayetteville) |
| --- | --- | --- | --- | --- |
| Downtown and core neighborhoods | 31% | Urban core | Dense, transit-served, renters, government offices, nightlife and night shifts | Five Points MARTA station, West End, downtown Atlanta government and court buildings |
| Inner suburbs | 20% | Suburban | Older housing, apartments, immigrant gateways, airport and service jobs | Forest Park, Riverdale and Jonesboro (Clayton County); Buford Highway corridor |
| Outer suburbs | 22% | Suburban | New-build subdivisions, car-dependent, big-box retail, long commutes | Fayetteville, Peachtree City, Tyrone, McDonough (Henry County) |
| Satellite city | 13% | Small metro | Historic downtown, hospital, county seat, mixed old and new industry | Griffin, Newnan's square, Macon for a larger version |
| Rural town | 8% | Rural | County seat of a few thousand, dollar stores, thin services, long drives | Zebulon (Pike), Barnesville (Lamar), Greenville (Meriwether), Thomaston (Upson) |
| Open country | 6% | Rural | Farms, scattered homes, well water, distance to everything | Pike and Meriwether farmland; peach orchards around Fort Valley |

The outer suburbs sit closest to home, but they are probably wealthier than the national average. Don't let them set the baseline.

## Economy

Medianville's \~48,000 jobs follow the 2025 national industry mix from the [BLS Employment Projections table](https://www.bls.gov/emp/tables/employment-by-major-industry-sector.htm). Health care and state and local government are the two biggest employers, ahead of retail and food service.

| Sector | US share, 2025 | Medianville jobs (approx.) | Real site to visit |
| --- | --- | --- | --- |
| Health care and social assistance | 13.7% | 6,600 | Piedmont Fayette Hospital; a dialysis center, nursing home or home-care agency |
| State and local government | 12.1% | 5,800 | A public school at pickup time; a Department of Driver Services center; the Clayton County courthouse in Jonesboro |
| Retail trade | 9.1% | 4,400 | Fayette Pavilion big-box strip; a Dollar General in a rural town |
| Accommodation and food services | 8.3% | 4,000 | Waffle House and drive-thrus on GA-85 at shift change |
| Manufacturing | 7.4% | 3,600 | Kia Georgia plant area, West Point; Peachtree City industrial park |
| Professional, scientific and technical | 6.3% | 3,000 | Office parks; remote workers at libraries and coffee shops |
| Self-employed | 5.8% | 2,800 | Barbers, contractors, gig drivers waiting at the airport cell-phone lot |
| Administrative and support | 5.3% | 2,500 | Staffing agencies; janitorial and security contractors |
| Construction | 4.9% | 2,400 | New-build subdivisions in Fayette and Henry counties |
| Finance and insurance | 4.0% | 1,900 | A bank branch, and a check-casher or title lender on the same strip |
| Transportation and warehousing | 3.9% | 1,900 | Hartsfield-Jackson airport; distribution centers along I-75 at McDonough and I-85 at Union City |
| All other sectors | 19.4% | 9,300 | Other services (repair, salons, churches), wholesale, private schools and colleges, federal government, information, real estate, arts and others |
| Agriculture (within all other) | 0.9% | 430 | Peach and pecan farms around Fort Valley |

Trilith Studios in Fayetteville is real and interesting, but film production is a tiny share of national jobs. Treat it as local color, not part of Medianville's economy.

## Transaction model

A transaction is any attempt by a household, business or agency to get a job done that costs money, time or effort, whether or not it succeeds.

**Transaction classes**

- **Purchases:** card, cash, digital wallet, Buy Now Pay Later
- **Bills and recurring payments:** rent, utilities, phone, insurance, subscriptions, loan payments
- **Income events:** payroll, gig payouts, tips, Social Security, SNAP/EBT and other benefits
- **Transfers:** person-to-person apps, family support, remittances
- **Business-to-business:** supplier invoices, payroll runs, rent, fuel
- **Government:** taxes, fees, fines, permits, license renewals, court dates
- **Non-monetary jobs:** appointments, waiting, forms, travel, caregiving, returns, disputes
- **Failures:** declined, abandoned, closed, out of stock, wrong document, come back tomorrow

**Record schema**

| Field | Example |
| --- | --- |
| tx\_id | H-0412-017 |
| timestamp | 07:42 |
| actor | Household 0412, adult 2 (home health aide, inner suburbs) |
| counterparty | Gas station, outer suburbs |
| job | When my shift starts across the county, I want enough gas to get there, so I can keep the hours |
| class | Purchase |
| channel and method | In person, debit card |
| amount | $20.00 |
| time cost | 12 minutes, including a 6-minute detour |
| outcome | Completed after the first card was declined for a pending hold |
| friction tags | Pending authorization hold; detour; low balance |
| district | Outer suburbs |

The job statement uses the "When…, I want…, so I can…" form, so the same job can be compared across very different households.

## Field visit plan

The first round is eight visits, one or two per district, each timed to a busy moment when jobs pile up. Each visit tests friction types the synthetic day suggests.

| # | Visit | District | When | What to watch for |
| --- | --- | --- | --- | --- |
| 1 | Department of Driver Services center | Satellite city or inner suburbs | Weekday opening | Wait times, missing documents, how many people leave and come back |
| 2 | Five Points MARTA station | Downtown | Weekday 7–9 am | Fare payment, transfers, how people get to work without a car |
| 3 | Gas station and Waffle House on a highway exit | Outer suburbs | Shift change, about 6 am | Small purchases, declines, cash vs card, workers between jobs |
| 4 | Laundromat and check-casher strip | Inner suburbs (Forest Park or Riverdale) | Saturday morning | Cash use, money orders, bill payment, remittances, languages |
| 5 | Dollar General and pharmacy | Rural town (Zebulon or Greenville) | Late afternoon | Distance, what's out of stock, prescription pickup, EBT use |
| 6 | Public school pickup line | Outer suburbs | Weekday afternoon | Parent time costs, caregiving logistics, fees and fundraising |
| 7 | Hospital emergency department waiting room or urgent care | Satellite city (Griffin) | Weekday evening | Insurance checks, payment plans, transportation home |
| 8 | Farm stand or orchard store | Open country (Fort Valley area) | Saturday | Seasonal cash business, card readers, how farms sell and get paid |

Keep notes in the same record schema, tagged as observed rather than synthetic, so field stories and simulated transactions sit side by side.

Observe public spaces only, and don't record identifiable people without consent.

## Advocacy and agency lenses

Each lens adds fields, friction tags or household types that a plain demographic sample would miss. Use them as checklists when reviewing a simulated day, not as weights.

**Lenses you named**

| Lens | What it watches | What it adds to Medianville | Data or material to pull | Where to see it locally |
| --- | --- | --- | --- | --- |
| A More Perfect Union | Worker and consumer stories: wages, prices, corporate practices, junk fees | Story-first framing; checks that simulated frictions match what real people describe on camera | Their video reporting, as qualitative prompts | Any field visit, as an interview style |
| Strong Towns | Whether a place's land use pays for its own infrastructure; car dependency; stroads; incremental development | Cost of distance and driving per transaction; tax value per acre by district; who pays for roads and pipes | Strong Towns case studies; county parcel and budget data | GA-85 and GA-314 commercial strips vs. downtown Fayetteville or Griffin |
| AFL-CIO and member unions (SEIU, UFCW, Teamsters, UNITE HERE, UAW) | Wages, scheduling, safety, benefits, the right to organize | Shift timing and schedule volatility; pay cadence; union status per worker; benefits gaps | BLS union membership data; union contract summaries | Warehouses on I-75 and I-85; airport; hospital shift change |
| Farmworker advocates (UFW, Farmworker Justice, Coalition of Immokalee Workers) | Heat, housing, wage theft, seasonal and guest-worker (H-2A) labor | Seasonal households, employer housing, cash wages, remittances, language access | USDA National Agricultural Workers Survey (NAWS) | Orchards and packing sheds around Fort Valley in season |
| AARP | Older adults: Social Security, Medicare, family caregiving, scams, aging in place | Unpaid caregiver time; fixed-income payment dates; fraud exposure; digital-access limits | AARP caregiving research; AARP Livability Index | Senior centers; pharmacy counters; church fellowship halls |
| CFPB | Credit, overdraft and junk fees, debt collection, complaints about financial firms | Fee events as transactions; complaint categories as friction tags | Public complaint database (check what's still published); Making Ends Meet survey | Bank branches next to check-cashers and title lenders |
| Other federal sources (Fed, FTC, FDIC, BLS, USDA) | Household fragility, fraud, unbanked households, spending, food access | Emergency-expense shocks; fraud losses; unbanked share; spending categories; food deserts | Fed SHED; FTC Consumer Sentinel; FDIC unbanked survey; BLS Consumer Expenditure Survey; USDA Food Access Research Atlas | Rural town and inner-suburb visits |

**Lenses you may be missing**

| Lens | Why it matters for Medianville |
| --- | --- |
| United For ALICE (United Way) | Counts working households that earn above poverty but below a local survival budget, which is the core population for "margins" |
| JPMorgan Chase Institute | Research built on de-identified transaction data, the closest published analog to this project's method |
| Financial Health Network | Measures financial health beyond income: spending, saving, borrowing, planning |
| National Consumer Law Center; Consumer Reports; Center for Responsible Lending | Debt collection, utility shutoffs, auto lending, product safety, payday and installment loans |
| KFF | Health costs, insurance gaps and medical debt |
| National Low Income Housing Coalition; Urban Institute | Rent burden, evictions, housing supply |
| Feeding America | Food insecurity by county |
| Disability advocates (National Disability Rights Network, AAPD) | Accessibility of the places and systems where transactions happen |
| Fines and Fees Justice Center; Institute for Justice | Court fines, fees and licensing barriers, a concern on both left and right |
| NFIB and local chambers of commerce | Small-business owners' costs: card fees, hiring, rules, cash flow |
| AEI Housing Center; Brookings Metro | Housing markets and metro economics, from market-oriented and center-left views |
| Center for Rural Affairs; The Daily Yonder | Rural services, broadband, health care and farm economics |
| Child Care Aware of America | Child care cost and supply, which shapes parents' work hours |
| TransitCenter; Smart Growth America | Transit access and road safety for people without cars |
| National Digital Inclusion Alliance | Who can't do a transaction online and what they do instead |

**New schema fields these lenses suggest**

- `alice_status`: poverty, ALICE, or above threshold
- `pay_cadence` and `schedule_volatility`: when money arrives and how predictable hours are
- `fee_paid`: overdraft, late, convenience or check-cashing fees attached to a transaction
- `fraud_exposure`: scam contact or loss
- `caregiver_time`: unpaid minutes spent on someone else's job
- `access_need`: disability, language or digital-access barrier
- `infrastructure_cost`: distance driven and the public cost of the route

## Research and think-tank lenses

NBER and Federal Reserve research set Medianville's numbers. Think tanks from left and right are used in pairs, so every topic is read through at least two theories of what causes the friction and what would fix it.

**Academic and Fed research for calibration**

| Source | What to take from it |
| --- | --- |
| [NBER: Household Financial Transaction Data (Baker and Kueng)](https://www.nber.org/papers/w29027) | A review of research built on transaction data from banks, fintech apps and payment processors; a map of methods and pitfalls |
| [Diary of Consumer Payment Choice (Boston and Atlanta Feds)](https://conference.nber.org/conf_papers/f176301.pdf) | Day-by-day payment diaries from real consumers: the best base for Medianville's daily transaction count and payment-method mix |
| NBER Innovative Data in Household Finance meetings | Current papers on spending, liquidity and income timing, such as spending jumps on payday |
| Opportunity Insights (Opportunity Atlas) | Economic mobility by county and neighborhood, to make districts' prospects realistic |
| Atlanta Fed benefits-cliff tools | Where a raise costs a family more in lost benefits than it earns, a classic margin problem |

NBER working papers are not peer reviewed. Check whether a paper has since been published before leaning on it.

**Paired think tanks by topic**

| Topic | Left or center-left | Center or bipartisan | Right, center-right or libertarian |
| --- | --- | --- | --- |
| Poverty and the safety net | Center on Budget and Policy Priorities; Urban Institute | Bipartisan Policy Center | American Enterprise Institute (poverty studies) |
| Wages and work | Economic Policy Institute | Niskanen Center | American Compass; Manhattan Institute |
| Housing and land use | Brookings Metro; Urban Institute | Strong Towns | AEI Housing Center; Cato and Mercatus on zoning |
| Regulation and consumer finance | Roosevelt Institute; Center for American Progress | Bipartisan Policy Center | Cato; Mercatus Center; Competitive Enterprise Institute |
| Family, child care and caregiving | Center for American Progress | Brookings Hamilton Project | Institute for Family Studies; AEI |
| Place-based distress | Brookings Metro | Economic Innovation Group (Distressed Communities Index) | Heritage Foundation |
| Education and workforce | Education Trust; Brookings Hamilton Project | Third Way | Manhattan Institute; Thomas B. Fordham Institute |
| Health costs | Commonwealth Fund | KFF | Paragon Health Institute; Cato |
| Georgia state policy | Georgia Budget and Policy Institute |  | Georgia Public Policy Foundation |

Labels are approximate and many of these groups call themselves nonpartisan. Take their mechanisms and data, check figures against primary sources, and record which lens a project idea came from.

**How to use the pairs.** For each top friction in a simulated day, write one line of diagnosis from each side, for example "benefits cliff" vs. "licensing barrier" for a stuck home-care aide. Projects that both diagnoses support are the strongest candidates.

## Federal statistics

Census surveys build Medianville's people, CBO and BLS set its money and time, and long-running panels show how households change. Several sources were cut or redesigned in 2025 and 2026, so check each one's status before using it.

| Source | What it gives Medianville | Status to check |
| --- | --- | --- |
| Census: American Community Survey and PUMS | The base population: households, income, jobs, housing, commutes | Annual |
| Census: decennial census and population estimates | How each kind of place has changed since 1990 | 2030 census in preparation |
| Census: Current Population Survey (ASEC) | Yearly income, poverty, insurance, Supplemental Poverty Measure | Food security supplement discontinued |
| Census: Survey of Income and Program Participation (SIPP) | Month-to-month swings in income, jobs and benefits | Funding cut and [redesign under test](https://thecensusproject.org/2026/08/10/census-bureau-plans-new-sipp-method-field-test/) |
| Census: Household Trends and Outlook Pulse Survey | Fast-turnaround household hardship and expectations | Successor to the Household Pulse Survey |
| Census: LEHD OnTheMap | Where people live vs. where they work, by block | Annual |
| Census: County Business Patterns and Nonemployer Statistics | How many businesses of each type, including one-person firms | Annual |
| Census and HUD: American Housing Survey | Housing condition, costs and moves | Every two years |
| [CBO: Distribution of Household Income](https://www.cbo.gov/system/files/2026-09/62761-Household-Income-2023.pdf) | Income before and after taxes and transfers by income group, 1979 to 2023 | Latest released September 2026 |
| CBO: Demographic Outlook, 2026 to 2056 | Aging, births, deaths and immigration for future Medianville snapshots | Released January 2026 |
| BLS: American Time Use Survey | Minutes per day spent on errands, care, travel and waiting: the time cost of jobs | Annual |
| BLS: Consumer Expenditure Survey and CPI | What households buy and how prices change by category | Ongoing |
| BEA: Regional Price Parities | How much costs differ between places | Annual |
| Fed: Survey of Consumer Finances | Wealth, debt and accounts by household | Every three years |
| DOT: National Household Travel Survey | Trips per person per day, by purpose and mode | Periodic |
| Panels: PSID (since 1968), NLSY, Health and Retirement Study | How the same families change over decades and across generations | University-run, federally funded |
| IRS migration data | County-to-county moves, for growth and decline | Annual |

## Change over time

One simulated day shows needs at a single moment. Medianville runs on four clocks so projects also fit how needs change across a life, between generations and over a community's history.

| Clock | What changes | How Medianville models it | Data |
| --- | --- | --- | --- |
| The calendar | Day of week, the 1st and 15th of the month, school year, tax-refund season, holidays, heat and storms | Run several sample days, not one: a weekday, a Saturday, the 1st, a February refund day, a storm day | ATUS; Diary of Consumer Payment Choice; benefit payment schedules |
| A life | Birth, school, first job, partnering, divorce, illness, caregiving, retirement, widowhood | Move the same households forward year by year with realistic transition rates; tie job statements to life stage | PSID; SIPP; NLSY; Health and Retirement Study |
| A generation | The same job done differently by different cohorts: paying a bill by check at a counter vs. through an app | Tag every person's birth cohort and compare the same job across cohorts | Diary of Consumer Payment Choice by age; ATUS; Pew generational research |
| A community | Districts are built, mature, age, decline or renew | Give each district an age and a direction, and build Medianville snapshots at minus 20, minus 10, now, plus 10 and plus 20 years | Decennial census history; IRS migration; building permits; Distressed Communities Index over time; CBO projections |

**Age, cohort or era.** When a behavior differs by age, decide why before projecting it forward. Some habits come with a life stage and repeat for each new generation; some belong to a cohort and age with it; some come from the era and change everyone. Cash is an example worth testing: the [2026 Diary of Consumer Payment Choice](https://www.frbservices.org/binaries/content/assets/crsocms/news/research/2026-diary-consumer-payments-choice.pdf) found the gap in cash use by age and income had widened since 2016.

**Community life cycles to see locally**

- **A new-build subdivision (outer suburbs):** young families and new roads today. Model the same streets in 25 years, when kids leave and pipes and pavement come due.
- **A planned suburb now decades old (Peachtree City):** aging residents, golf-cart errands, early infrastructure renewal.
- **An older inner suburb (Clayton County):** housing built for an earlier wave of residents, now home to renters, newcomers and airport workers.
- **A historic downtown (Griffin, Newnan):** decline after malls and bypasses, then partial revival.
- **A rural county seat (Zebulon, Greenville):** an aging population, consolidated schools, longer trips for health care.

**Shock scenarios.** Rerun a snapshot with one change: a major plant opens or closes, a storm, a rate spike, a benefits rule change, a hospital closing. Then compare which jobs break first and for whom.

## Calibration and open decisions

Medianville passes if it matches national figures on the same measures published rankings use.

- **Demographic similarity:** score Medianville on age, education, race and ethnicity using Jed Kolko's FiveThirtyEight similarity method. The best real metro scored 93.2; Medianville should beat it.
- **Broad resemblance:** recompute WalletHub-style measures (income, household size, housing tenure, gender). The top real metro, Indianapolis, scored 93.50 in [WalletHub's 2016 ranking](https://wallethub.com/edu/metro-areas-that-most-and-least-resemble-the-us/6109).
- **Jobs and places:** check the industry mix against BLS and the district split against Pew's 31/55/14.

**Open decisions**

- [ ] Daily transaction volume per household: set it from the Diary of Consumer Payment Choice, checked against the Federal Reserve Payments Study, not from guesses
- [ ] Businesses and agencies: how many of each type, and whether they get their own job statements
- [ ] Which day to simulate: a weekday, a Saturday, or the 1st of the month, when rent, benefits and bills land together
- [ ] Whether unpaid work (caregiving, errands, school logistics) counts toward daily volume or is tracked separately
- [ ] Which future and past snapshot years to build, and which transition rates to use for aging households
- [ ] Final name for the city

**Sources**

- [Pew Research Center: demographic and economic trends in urban, suburban and rural communities](https://www.pewresearch.org/social-trends/2018/05/22/demographic-and-economic-trends-in-urban-suburban-and-rural-communities/)
- [BLS: employment by major industry sector](https://www.bls.gov/emp/tables/employment-by-major-industry-sector.htm)
- [WalletHub: metro areas that most and least resemble the US](https://wallethub.com/edu/metro-areas-that-most-and-least-resemble-the-us/6109)
