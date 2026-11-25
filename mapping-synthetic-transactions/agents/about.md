> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.

The About page of https://medianville.netlify.app/about/ as plain Markdown, written from about/index.html by tools/build_agent_pages.py. Links into the repository point at its main branch.

# One day in Medianville

Medianville is a model of an ordinary day in an ordinary American city, made so that the jobs people do, and the systems around them, can be seen together.

## What this is

Medianville is a simulated American city of about 100,000 people, built to match the country as a whole. The site opens on one day there, Wednesday, March 3, 2027: about 200,000 transactions. Paychecks, bus fares, autopays, declined cards, hours of unpaid caregiving. A menu in the header opens 18 other days that together stand for the year (Saturdays and Sundays, paydays, holidays, a storm, a heat wave), and the first version of the day.

Each one is a *job to be done*: something a person was trying to get done. A record can be a purchase or a bill, but it can also be a form, a wait, a wasted trip or an hour spent caring for a parent. Each says what the job was, who paid, who else paid, what it cost in time and effort, and whether it worked.

Seen together, the jobs show how they collide (a bill that drafts at 2 a.m. declines a card at 5 p.m.) and the systems underneath that decide who they work for. The goal is to find small, practical fixes for daily life at the margins.

There are two ways in. [The city](https://medianville.netlify.app/) plays the day back on a miniature town or a printed map, with a systems lens that opens over it. The [data explorer](https://medianville.netlify.app/explorer/) lays out the same records as tables to filter, search and group.

## Where it came from

It began with a question Jason asked: which American city or town best matches the country’s mix of wealth, race, class, industry and gender? The published rankings each pick a different winner, and the places that score well tend to leave out rural and small-town life, where many of the hardest daily jobs are.

So the city is synthetic, weighted to the whole country.

The framing is Jason’s: every transaction is a job to be done, including the unpaid ones and the ones that fail.

The systems lens comes from Donald Martin Jr.’s idea of societal context: the social, cultural, historical, political, economic and environmental circumstances that surround and shape people, places and problems. Jason heard him speak at blackcomputeHER.org’s 2025 AI Summit, [Reimagining AI in Our Own Image](https://blackcomputeher.org/ai-summit/).

The name nods to Robert and Helen Lynd’s *Middletown* (1929), the study of Muncie, Indiana that started a long line of “typical town” research. Unlike their Muncie, Medianville’s typicality comes from weighting, not from leaving groups out.

The city was called Halvern until November 20, 2026. The first run as it shipped and the archived versions keep that name.

## How it was made

**Simulate, don’t write.** No one, human or model, can write 200,000 consistent records by hand: money wouldn’t reconcile, and people would be in two places at once. So code does it.

- People, households, employers and bills are generated from a seed. The same seed and options reproduce the files byte for byte.
- The day is settled minute by minute against each household’s money. Every action goes into one queue in time order, so a bill at 2 a.m. can decline a card at 5 p.m.
- The first run was calibrated to published anchors and checked: money reconciles for every household, nobody exceeds 24 hours in a day, and every paycheck has its withholding.
- Then 500 records were read and written by hand as a believability test. Reading them caught what the numeric checks passed, such as union dues paid to a charity and a 91-year-old schoolteacher.
- The second version (v2) keeps the same people and sets its rates from real evidence: first a pass of real accounts read beside the first day, then 42 downloaded public datasets. Only strong evidence is allowed to move a rate, and the rates are checked against their targets across the year.
- v2 runs 18 typed days that stand for 2027 (weekends, paydays, benefit days, holidays, tax season, a winter storm, a heat wave) beside the same Wednesday. Before it was frozen, two readers read 200 of its records, and 300 more of the baseline day were written by hand.

The city on this site opens on v2’s Wednesday. The day menu holds the 18 other days and the first version of the Wednesday, for comparison. A whole month, March 2027, carried day to day so unpaid bills, shutoffs and loan rollovers chain across days, is a separate download the site doesn’t load.

The longer account is in [how the first day was built](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/01-one-day/medianville-build-approach.md), the [first run record](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/01-one-day/medianville-2027-03-03-run-record.md), the [data update plan](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/03-grounding-in-evidence/medianville-data-update-plan.md) and the [v2 run record](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/05-more-time/medianville-v2-run-record.md).

## Data sources

The research came in four rounds. Real evidence enters Medianville only as numbers: rates, shares and calendars. No real person’s words or record appear in a record.

### 1. Calibration anchors (the first run)

The first run was calibrated to these:

- [American Community Survey](https://www.census.gov/programs-surveys/acs) (Census Bureau): national shares of household types, income, tenure, language and more
- [Current Employment Statistics](https://www.bls.gov/ces/) (BLS): the industry mix of jobs
- [Diary of Consumer Payment Choice](https://www.atlantafed.org/research-and-data/surveys/survey-and-diary-of-consumer-payment-choice) (Federal Reserve): about 43 payments per adult a month, 14% of them in cash
- [Survey of Household Economics and Decisionmaking](https://www.federalreserve.gov/consumerscommunities/shed.htm) (Federal Reserve): 63% of adults could cover a $400 emergency
- [United For ALICE](https://www.unitedforalice.org/): about 4 in 10 households below the ALICE threshold
- [Consumer Expenditure Survey](https://www.bls.gov/cex/) (BLS): the order of spending, housing first, then transportation, then food
- 2027 program figures from [Social Security](https://www.ssa.gov/cola/), [SNAP](https://www.fns.usda.gov/snap) and [Medicare](https://www.medicare.gov/basics/costs/medicare-costs)

The thinking behind the city is in the white paper, [Seeing the Margins](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/00-the-idea/seeing-the-margins.md), and the [city design](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/00-the-idea/synthetic-mid-america-city-design-v0.1.md).

### 2. Real accounts beside the first day

Next, 69 sources were read beside the first day’s records: government reports and data, surveys, investigative and local journalism, and advocacy, industry and think-tank positions from left and right. They gave 76 findings on fees, high-cost loans, shutoffs, benefit paperwork, buses, schedules, caregiving, home care and distance to care. The [evidence report](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/evidence/report.md) scores the first day against them and lists what it was missing, which became v2’s new jobs and the district circumstances in the systems lens. The [evidence folder](https://github.com/jas0nmjames/playground/tree/main/mapping-synthetic-transactions/evidence) holds every source, finding and quote. The quotes stay there: none is given to a Medianville resident.

### 3. Downloaded datasets that set v2’s rates

Then 42 public datasets were downloaded, each logged in the [sources manifest](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sources/manifest.csv) with its publisher, vintage, files, checksums and terms:

**Time and care**

- [American Time Use Survey](https://www.bls.gov/tus/) (BLS): annual tables, the eldercare release and the 2003–2025 microdata, for caregiving hours and when in the day errands, care and shopping happen
- [National Database of Childcare Prices](https://www.dol.gov/agencies/wb/topics/featured-childcare) (Department of Labor): weekly child care prices
- [National Compensation Survey: Employee Benefits](https://www.bls.gov/ebs/) (BLS): paid sick leave by wage level

**Money and payments**

- [Survey and Diary of Consumer Payment Choice](https://www.atlantafed.org/research-and-data/surveys/survey-and-diary-of-consumer-payment-choice) (Federal Reserve Bank of Atlanta), 2025: cash use by income, age and rural areas
- [Survey of Household Economics and Decisionmaking](https://www.federalreserve.gov/consumerscommunities/shed_data.htm) (Federal Reserve), 2025 microdata: bills unpaid and care skipped, on the same households
- [Survey of Consumer Finances](https://www.federalreserve.gov/econres/scfindex.htm) (Federal Reserve), 2025: balances, debts and assets
- [National Survey of Unbanked and Underbanked Households](https://www.fdic.gov/household-survey) (FDIC), 2023
- [Consumer Expenditure Survey microdata](https://www.bls.gov/cex/pumd.htm) (BLS), 2025: what households buy, how often and for how much
- [Bank call reports](https://cdr.ffiec.gov/public/PWS/DownloadBulkData.aspx) (FFIEC): overdraft and NSF revenue
- [Household Debt and Credit Report](https://www.newyorkfed.org/microeconomics/hhdc) (Federal Reserve Bank of New York): delinquency by loan type

**High-cost credit and fraud**

- [Payday lending annual report](https://dfpi.ca.gov/publications/payday-lenders-publications) (California DFPI), 2025
- [Credit Access Business reports](https://occc.texas.gov) (Texas OCCC), 2025: payday and title loans, refinances and repossessions
- [Data Point: Payday Lending](https://www.consumerfinance.gov/data-research/research-reports/cfpb-data-points-payday-lending/) (CFPB): loan sequences and rollovers
- [Title Pledge Report](https://www.tn.gov/tdfi.html) (Tennessee TDFI), 2026
- [Consumer Sentinel Network Data Book](https://www.ftc.gov/data) (FTC), 2024, and the [Elder Fraud Report](https://www.ic3.gov/AnnualReport/Reports) (FBI IC3): how large losses run

**Housing and utilities**

- [American Housing Survey](https://www.census.gov/programs-surveys/ahs/data.html) (Census Bureau and HUD), 2023: owners’ housing costs by income
- [Residential Energy Consumption Survey](https://www.eia.gov/consumption/residential/) (EIA), 2024: disconnect notices
- [Utility disconnections](https://utilitydisconnections.org/): EIA’s 2024 utility-level data and report, with the Energy Justice Lab’s documentation
- [Eviction Tracking System](https://evictionlab.org/eviction-tracking/) (Eviction Lab, Princeton)

**Benefits, taxes and the calendar**

- [Schedule of Social Security Benefit Payments 2027](https://www.ssa.gov/pubs/EN-05-10031-2027.pdf) (SSA) and [federal holidays 2027](https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/) (OPM)
- SNAP issuance schedules from eight state agencies, and [SNAP Quality Control data](https://snapqcdata.net/) (USDA FNS), FY2024
- [Medicaid renewal and work-reporting data](https://data.medicaid.gov/) (CMS and Georgia Pathways)
- [Refund timing](https://www.irs.gov/refunds) and [Statistics of Income](https://www.irs.gov/statistics/soi-tax-stats-individual-statistical-tables-by-size-of-adjusted-gross-income) (IRS): when EITC refunds land and who uses a paid preparer

**Work, places and getting around**

- [Occupational Employment and Wage Statistics](https://www.bls.gov/oes/tables.htm) (BLS), May 2025
- [County Business Patterns](https://www.census.gov/programs-surveys/cbp/data/datasets.html) (Census Bureau), 2023: how many of each kind of business
- [National Agricultural Workers Survey](https://www.dol.gov/agencies/eta/national-agricultural-workers-survey/data) and [H-2A disclosure data](https://www.dol.gov/agencies/eta/foreign-labor/performance) (Department of Labor): farmworkers and guest workers
- [National Transit Database](https://www.transit.dot.gov/ntd/ntd-data) (FTA), [Food Access Research Atlas](https://www.ers.usda.gov/data-products/food-access-research-atlas/) and [Rural-Urban Continuum Codes](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/) (USDA ERS)

**Health, life events and weather**

- [Medical Expenditure Panel Survey](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files.jsp) (AHRQ), 2024, and [dialysis facilities](https://data.cms.gov/provider-data/topics/dialysis-facilities) (CMS)
- [Births, deaths, marriages and divorces](https://www.cdc.gov/nchs/nvss/marriage-divorce.htm) (CDC NCHS) and [migration data](https://www.irs.gov/statistics/soi-tax-stats-migration-data) (IRS)
- [Storm Events Database](https://www.ncei.noaa.gov/stormevents/ftp.jsp) and [GHCN-Daily](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily) for Atlanta’s airport (NOAA): how often storm and heat days come

v2 is checked against them across the [typed-day year](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sim/evidence/results/v2_phase5_typed_days_2027/evidence_checks.md) and the [March month](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sim/evidence/results/v2_month_2027-03/evidence_checks.md).

### 4. History behind the systems lens

Each district’s historical and built circumstances name their own sources: the Housing Act of 1949 and the Federal-Aid Highway Act of 1956; the University of Richmond’s [Mapping Inequality](https://dsl.richmond.edu/panorama/redlining/) and [Renewing Inequality](https://dsl.richmond.edu/panorama/renewal/); the EPA on heat islands and brownfields; BLS manufacturing employment; the American Housing Survey and American Community Survey; the USDA Census of Agriculture and farm real estate values; American Farmland Trust; the NCES Digest of Education Statistics; and the UNC Sheps Center’s rural hospital closures. The [design record](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/04-the-refined-city/medianville-systems-lens.md) lists the figures that were checked and reworded.

Households in both versions are built by rule to match national shares. They aren’t drawn from Census microdata.

## What’s real and what isn’t

- **Real:** national rates and program rules, and the names of federal programs and agencies, such as the IRS, Medicare, SNAP and the Postal Service. The jobs make no sense without them.
- **Invented:** every person, household, business, local agency, church and street.
- The blocks in the systems lens are composites of documented US patterns, such as redlining, branch closures and cut bus routes. They’re labelled as composites on screen. Each district also has circumstances that hold across the whole district, written from national figures and documented cases, with nothing local named.
- No real quote or real person ever appears in a record. Real evidence enters only as numbers.

## Limits

v2 keeps the first run’s people so the two can be compared, and some of those households don’t hold up. The [close reading](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/05-more-time/medianville-v2-close-reading.md) lists them:

- Some SSI goes to people whose income or spouse rules it out, and coverage doesn’t always follow eligibility.
- Every renter with no income pays the same rent, and some refundable credits reach households earning well over the limit.
- Wages run about 14% high on purpose, to make up for households that are smaller than real ones. Compare households, not occupations.
- A few jobs are paired with unrelated employers, and a few trips run 60 to 80 miles.
- Overdraft fees fall on fewer accounts than in life.
- Each typed day is simulated on its own. Only the March month carries unpaid bills and loans from one day to the next.
- Some 2027 figures, such as the Medicare Part B premium, are projections.
- In the animated city, positions are approximate: the run’s six districts are drawn on a smaller model town.

## Who made it

**Jason James**

The idea and where it came from, the jobs-to-be-done framing, the systems lens, and every design decision: the visual direction, the views, the sound and the structure.

**Claude (Anthropic’s AI model)**

Researched the anchors and the real evidence, logged the downloaded datasets, wrote both simulators and generated the days (Claude Fable 5.2 for the first run, Claude Opus 5.5 for v2), hand-wrote the 800 detailed records (500 in the first run, 300 in v2), and built the viewers, the systems lens and the explorer, working in Claude and Claude Code under Jason’s direction.

Every design decision, and why, is in the [decision log](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/decisions.md).

## Links

- [For agents and LLMs](https://medianville.netlify.app/llms.txt) · what to read first, the data dictionary, every day’s summary and the downloads, as plain text
- [The repository](https://github.com/jas0nmjames/playground/tree/main/mapping-synthetic-transactions) · code, data and documents
- [README](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/README.md) · the views, how they work, and what Claude did
- [Decision log](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/decisions.md)
- [First run record](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/01-one-day/medianville-2027-03-03-run-record.md) · the first day’s calibration and checks
- [v2 run record](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/05-more-time/medianville-v2-run-record.md) · the 19 published days, their weights and checks
- [Data update plan](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/03-grounding-in-evidence/medianville-data-update-plan.md) · how the evidence moved each rate
- [Evidence report](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/evidence/report.md) and [sources manifest](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/sources/manifest.csv) · the real accounts and the downloaded datasets
- [Close reading](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/05-more-time/medianville-v2-close-reading.md) · two readers on 200 records before v2 was frozen, and what was fixed
- [How the first day was built](https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/story/01-one-day/medianville-build-approach.md)
- Earlier versions are kept in the [archive](https://medianville.netlify.app/archive/), and how the project was made is in [the story](https://github.com/jas0nmjames/playground/tree/main/mapping-synthetic-transactions/story).

Built by [Jason James](https://jasonjames.works) with [Claude](https://claude.ai) · [The city](https://medianville.netlify.app/) · [Data](https://medianville.netlify.app/explorer/) · [For agents](https://medianville.netlify.app/llms.txt)
