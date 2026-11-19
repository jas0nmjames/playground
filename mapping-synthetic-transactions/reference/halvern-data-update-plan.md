# Halvern data update plan: fold in the human evidence, then go past one day

Written 2026-11-18. Reads with `claude/halvern-human-evidence-report.md` (the evidence), `claude/halvern-transaction-generator-prompt.md` (the spec), `claude/halvern-build-approach.md` (how v1 was built) and the City Design v0.1 and "Seeing the Margins" docs (the four clocks). The work happens in Claude Code, in `playground/mapping-synthetic-transactions`, on a feature branch merged into `development`.

## 1. Where things stand

- **One run exists:** `halvern_2027-03-03.zip`, 201,753 records. The copies in Downloads, in this project and in the repo's `data/` folder are the same file (same SHA-256).
- **The repo already holds** the zip, the unpacked simulator (`data/halvern/`, about 8,500 lines of Python), the 500 hand-written records, both viewers (night map and v3), and five reference docs. It does **not** yet hold the human-evidence files (report, sources, evidence, quotes) or the research prompt.
- **The simulator can already** run any date, storms and heat, price and outage shocks, a smaller city, and several days in a row with balances carried forward.

### The evidence report's gap list was checked against the full run

The evidence pass only had the 500-record sample, so it called several things "missing" that the full `records.csv` already contains. Checked today against all 201,753 records:

| Item | Report said | Full run actually has | Evidence target (rough, scaled to Halvern) | What to do |
|---|---|---|---|---|
| Overdraft fees | none | **274 fees** in 223 households (poverty 122, ALICE 102, above 50) | about 150 a day, averaged over a year | Probably **too many**, not too few. Measure across a month before changing (a 3rd-of-the-month Wednesday is heavy for autopays). |
| Payday loans | none | 8 new loans, 4 rollovers, 11 repayments | 25 to 80 loans a day (Pew 2013–16 figures; the industry has shrunk since) | Raise moderately once newer data is found. |
| Auto title loans | none | 4 new loans, **no payments, no repossessions** | about 15 to 25 payments a day (2.5 million borrowers scaled to Halvern, about 750) | Add payments and the repossession and lost-car chain. |
| Pawn, check cashing, money orders | none | 21, 40 and 53 records | no good daily figure | Keep. |
| Utility shutoffs | none | 26 notices, 8 disconnections, 8 reconnections | 11 to 12 disconnections a day | Small raise, and make it a multi-day chain. |
| Medical debt | none | 137 payment-plan payments; no "care delayed by debt" | 41% of adults have some health care debt | Add the delay link; check the installment rate. |
| Home caregiving | 8,368 hours | 8,548 hours at home, 1,691 on visits | AARP rates imply about 67,500 | **Download ATUS first**; AARP self-reports run high. |
| Aide visits | low no-show rate | 678 visits, 51 not completed (7.5%) | agencies miss shifts several times a month | Check each miss links to a family member's lost work. |
| Scams | one, no loss | 357 attempts, 2 losses | rare losses, very large ones (6% of reports, 70% of dollars) | Add a heavy-tailed loss size. |
| Benefits cliff | absent | 6 records tagged, no job of its own | — | Add the job. |
| Rural cash | 16.8% | 16.8% | 21% | Raise. |
| Truly absent | | car disabled by lender; Direct Express failures; called in on a day off; keeping availability open; SNAP interview calls; title payments and repossessions; H-2A households | | Add. |

So the update is part **correction** (overdraft likely high), part **addition** (the truly absent jobs) and part **settling with better data** (caregiving). The generator prompt's new "frictions the review found missing" section repeats the sample-only view and should be revised to this table.

## 2. How evidence gets into the data (the mechanism)

Keep real and synthetic apart, as the research prompt requires: no real quote or person ever goes into a record. Evidence enters through numbers and links only.

1. **`evidence_targets.csv`**, a new table: one row per target, with `evidence_ids`, the generator parameter it moves, the target value or range, the tolerance, the unit (per day, per year, share of households) and the strength grade (A–D). Only A and B evidence sets a rate; C and D add job kinds and texture.
2. **`assumptions.csv` gains an `evidence_ids` column**, so every rate can be traced back to a source row.
3. **`summary.md` gains an "Evidence checks" section** that reports each target against the run, like the calibration anchors do now. Annual targets are checked against a weighted set of days (section 4), never against one Wednesday.
4. **`evidence_links.csv`** joins evidence rows to Halvern by `job_category`, `friction_tags` and household type, so the viewers and reports can say "real accounts of this" beside a synthetic record without merging them.

## 3. Data to download

**The full list (51 datasets in four tiers, with landing pages) is in `claude/halvern-download-manifest.csv`, with steps in `claude/halvern-download-instructions.md`.** The tables below are the core of it. The chat workspace can't reach most government sites, so downloads happen in Claude Code on your Mac. Each file goes into `sources/` with a `sources/manifest.csv` row: URL, vintage, date downloaded, SHA-256 and license. That also covers the "archive and version now" advice, given the federal survey cuts. Raw files stay out of git; the manifest goes in.

**Tier 1: needed for this update**

| Source | What it settles |
|---|---|
| American Time Use Survey (latest tables; eldercare and childcare tables; activity by time of day) | Caregiving hours (F2), time-of-day profiles for errands and care |
| Diary of Consumer Payment Choice public data (latest) | Cash by income, age and rurality; payments by day of week |
| SHED public microdata (2025) | Who is fragile together: can't cover $400, behind on bills, skipped care, so these land on the same households |
| 2027 payment calendars: Social Security, SSI, VA; a spread of state SNAP issuance schedules; federal holidays; IRS refund timing | The calendar clock |
| FTC Consumer Sentinel Data Book (latest) | Fraud loss sizes by age |
| Newer payday and title-loan figures (CFPB or state regulator reports) | Replaces Pew 2013–16 |

**Tier 2: realism adds for this update.** 27 sources that ground v2's rates and distributions. The most useful are the Consumer Expenditure Survey Diary (two weeks of real purchases per household), the Survey of Consumer Finances (opening balances and debts), MEPS (who pays what in health care) and County Business Patterns (how many organizations of each kind). The rest cover fees and credit, utilities and housing, work and benefits, places, farmworkers, life events, weather and fraud; see the manifest.

**Tier 3: next version**

| Source | What it settles |
|---|---|
| ACS 1-year PUMS, national household and person files | Draw real household structures instead of rule-built ones (the prompt asked for this; v1 didn't do it) |
| NHTS 2022 trip file | Trip lengths by purpose and district type, fixing the district-table distance problem |
| SIPP or JPMorgan Chase Institute volatility figures | Month-to-month income swings for multi-day runs |
| CFPB complaint database (bulk) | Wording and friction kinds for templates; never frequencies |

**Tier 4: for the life and community clocks:** PSID and HRS transition rates, CBO's demographic outlook, the Distressed Communities Index over time, NOAA climate normals for storm and heat frequency.

## 4. Going past one day

A single day is too few for three reasons: annual shares (rent, insurance) can't balance in one day; rare events (8 shutoffs, 4 title loans) are too noisy to rank; and the most promising hypotheses ("money arrives after it's due", "skipped care cascades") play out across days. Four options, in order of cost:

| Option | What it is | Size | Needs from the generator |
|---|---|---|---|
| **A. A typed-day set** (recommended first) | 10–12 days that stand for a year, each with a weight: ordinary weekday early, mid and late month; Friday payday; Saturday; Sunday; the 1st; each Social Security Wednesday; a February refund day; a holiday; a storm day; a heat day | about 190 MB zipped | Almost nothing; runs today |
| **B. One continuous month** (recommended second) | March 1–31, 2027, balances carried day to day | about 500 MB zipped, 3.3 GB unpacked | Real carry-over: unpaid bills retried and fined, notices that become shutoffs, overdraft chains, SNAP balances running down, payday rollovers, income swings |
| **C. A year at 10% scale** | 4,140 households for 365 days, the roster aging and changing | about 600 MB zipped | Roster changes between days: aging, births, deaths, job changes, moves, new caregiving |
| **D. Past and future snapshots** | Halvern at −20, −10, +10, +20 years | per snapshot, as a day | District age and direction; CBO projections |

Do A first because it costs nothing and makes every annual target checkable. Then B, because most of the evidence is about chains over days. C and D are later.

## 5. Generator changes, in order

**Group 1: correct and settle (after the Phase 1 measurement)**
1. Overdraft: tune to the annual target across the typed-day set and keep it concentrated (9% of accounts pay 79% of fees).
2. Caregiving: set hours from ATUS; add out-of-pocket caregiving spending (no more $0 care records).
3. Rural cash toward 21%.
4. Tax-prep fees: check how many EITC refunds carry a paid-preparer fee against the roughly half who use preparers.

**Group 2: add the missing jobs** (use the existing naming, e.g. `money_services.title_loan_payment` beside `title_loan_disbursed`)
5. Title-loan payments, repossession, then the transport failures that follow.
6. `transportation.car_disabled_by_lender`, including some in error.
7. SNAP interview calls that collide with shifts, missed-interview churn, and the agency's $80 cost.
8. Medicaid work-report failures and retries tied to `schedule_volatility`.
9. `work.raise_declined_benefits_cliff`.
10. Called in on a day off; keeping availability open.
11. Direct Express call-center failures.
12. Medical care delayed by debt; abandoned prescriptions over $250.
13. Heavy-tailed scam losses for adults 60+.
14. A handful of H-2A households in open country, seasonal by date.

**Group 3: what multi-day needs** (for option B): retry queue for unpaid bills, late fees, notice-to-shutoff timers, rollover chains, SNAP and paycheck balance paths, income volatility.

**Group 4: v1 limits worth fixing now:** distances from locations instead of a district table; occupations tied to employers; marriage and divorce rates above zero.

## 6. The hand-written records

The 500 hand-written records are keyed to v1's record ids, and any population change redraws them. So:
- **v1 stays frozen** as `halvern_2027-03-03.zip`; the viewers keep working.
- **v2 gets its own sample** after the simulator is frozen again: about 300 records, weighted toward the new jobs, written in Claude Code and read by a second reader that hasn't seen the code, as the build notes recommend.

## 7. Where it lives in the repo

```
mapping-synthetic-transactions/
  data/
    halvern_2027-03-03.zip        v1, unchanged
    runs/manifest.json            every published run: id, version, date, label, records, path
    runs/v2/<date>.zip            the typed-day set only (each about 16 MB)
  sim/                            simulator v2, tests, evidence_targets.csv
  evidence/                       report, sources, evidence, quotes, evidence_links.csv
  sources/manifest.csv            download log (raw files gitignored)
  reference/                      existing docs, plus this plan and the research prompt
```

GitHub limits decide the rest: a file over 100 MB is refused, a Pages site should stay under about 1 GB, and Pages doesn't serve Git LFS files. The typed-day zips fit in the repo. The month and year bundles go to GitHub Releases or stay local; the simulator is deterministic, so anyone can rebuild them. Both viewers hard-code the v1 zip; the change is a run picker that reads `runs/manifest.json`.

## 8. Phases

| Phase | Work | Done when |
|---|---|---|
| 0. Set up | Bring the evidence files and this plan into the repo; copy the simulator to `sim/`; turn the existing checks into tests; confirm v1 reproduces byte for byte | Tests pass, v1 reproduces |
| 1. Measure | Write `evidence_targets.csv`; add the evidence checks to the summary; run the typed-day set with the **unchanged** simulator | Every target has a measured value across the year's days |
| 2. Download | Tier 1 and 2 sources, logged in the manifest | Caregiving, cash and calendars have real inputs |
| 3. Change | Groups 1, 2 and 4; recalibrate across the typed-day set | Anchors and evidence checks in tolerance |
| 4. A month | Group 3; run March 2027 | Chains visible: notice to shutoff, overdraft to fee to late rent |
| 5. Read and publish | Close reading of a fresh sample; hand-write v2's records; package; run picker in the viewers; update the README and project docs | PR into `development` |
| 6. Later | ACS PUMS population (v3); year at 10%; snapshots | — |

## 9. Decisions for you

1. **Same people or new people?** Keeping v1's population keeps comparisons clean (same households, before and after). Rebuilding from ACS PUMS is more truthful but breaks comparability and the hand-written sample. Recommended: keep the population for v2, rebuild in v3.
2. **How far past one day:** the typed-day set only, or the month too.
3. **Where the big bundles live:** Releases, or local only.
4. **Georgia evidence:** keep Halvern national, using Georgia-specific findings (title pawn rates, Pathways) for field visits and texture only. Recommended.
5. **Project docs:** revise the evidence report's section 2 and the generator prompt's friction section to match the table in section 1.

## 10. The v2 change list (added 2026-11-19, after the downloads)

Phase 2 brought in 41 datasets (about 2.0 GB, raw files outside git; see `sources/manifest.csv`). This is everything they support changing in the simulator. v1's 201,753 records are never edited: every change goes into `sim/`, and v2 is a fresh run over the typed-day set. "v1 now" is the March 3 run unless it says "a day" (the weighted typed-day year).

**Work order.** The rates in Group 1 (overdraft, cash, tax prep, disconnections, payday, scams) all depend on balances, spending, wages and the calendar, so the inputs are reset first and the rates are tuned last; tuning first would have to be redone. Order: calendar and weights (C), inputs (I), missing jobs (J), places and life events (P), then the rate corrections (R). Each batch is rerun across the typed-day year and committed on its own.

**Already done:** home caregiving set from ATUS 2023-25 (about 8,550 hours a day in v1, about 3,490 in v2; visits unchanged at about 1,700). Commit `bcae8f6`.

### C. Calendar and weights

| # | Change | v1 now | Source |
|---|---|---|---|
| C1 | Storm and heat day counts, which set the typed-day weights | placeholders, 4 and 8 | NOAA Storm Events 2015-25 |
| C2 | Federal holidays: closures and shifted payment dates | the holiday runs as an ordinary weekday | OPM 2027 (`sources/derived/federal_holidays_2027.csv`) |
| C3 | Social Security dates by birth-date cohort; SSI on the 1st | built in from the rule | SSA 2027 schedule |
| C4 | SNAP load days by state rule | one rule | `sources/derived/snap_issuance.csv` (8 states) |
| C5 | EITC/ACTC refund landing dates | Feb 26-Mar 5 wave | IRS 2026 releases (2027 notice due in January) |
| C6 | Time of day for errands, care, school pickup, shopping | hand-set profiles | ATUS 2025 activity file |
| C7 | Payments by day of week | hand-set | DCPC 2025 |

### I. Inputs that drive everyone

| # | Change | v1 now | Source |
|---|---|---|---|
| I1 | What households buy, how often, basket sizes | main grocery trip $92 | CE Diary and Interview 2025 |
| I2 | Opening balances, debts and assets by household type | rule-built | SCF 2025 |
| I3 | Fragility on the same households: can't cover $400, behind on bills, skipped care | each drawn separately | SHED 2025 microdata |
| I4 | Banking status by income and age | 4.3% unbanked, 12.9% underbanked | FDIC 2023 |
| I5 | Late payments by loan type | rule-built | NY Fed HHDC 2026 Q3 |
| I6 | Health costs: patient share and payer share by visit type | ER mean $1,885 | MEPS 2024 |
| I7 | Wages by occupation; fix odd employer-occupation pairs | hand table x 1.23 | OEWS May 2025 (national and by industry) |
| I8 | Paid sick leave by wage level | 142 stayed home with a sick child, 81 missed shifts | NCS March 2026 |
| I9 | Child care prices by age of child | median $319 a payment | NDCP 2022 |
| I10 | Transit fare and subsidy per ride | $9.80 gross a ride | NTD 2025 |
| I11 | Housing costs, repairs and condition | rule-built | AHS 2023 |
| I12 | Energy bills and energy hardship | median electric bill $153 | RECS 2024 |
| I13 | Eviction filings per day | 4 notices, 7 hearings | Eviction Lab monthly |
| I14 | SNAP benefit amounts and household makeup | median issuance $306 | SNAP QC FY2024 |
| I15 | Moves in and out | 9 move-ins | IRS migration 2022-23 |

I2, I3, I4 and I7 change the population's money and incomes (not who the people are), which touches decision 1 in section 9.

### J. Jobs to add

| # | Change | v1 now | Source |
|---|---|---|---|
| J1 | Title-loan payments, refinances, repossessions, then the lost-car trips | 0 payments (target 15-25 a day) | TX OCCC 2025-26, TN TDFI 2026 |
| J2 | `transportation.car_disabled_by_lender`, some in error | absent | (texture) |
| J3 | Care delayed by medical debt; prescriptions over $250 abandoned | absent | MEPS 2024 |
| J4 | `work.raise_declined_benefits_cliff` | 6.5 tagged records a day, no job | (texture) |
| J5 | SNAP interview calls that clash with shifts; missed-interview churn | absent | SNAP QC FY2024 |
| J6 | Medicaid work-report failures and retries | 76 reports | CMS renewals data (work reporting starts January 2027) |
| J7 | Called in on a day off; keeping availability open | absent | (texture) |
| J8 | Direct Express call-center failures | absent | (texture) |
| J9 | H-2A households in open country, seasonal | absent | H-2A FY2025-26, NAWS 1989-2022 |
| J10 | Out-of-pocket caregiving spending | 5,137 care records a day at $0 | CE 2025 |
| J11 | Aide no-shows linked to a family member's lost work | 3.6 of about 38 misses a day linked | (check) |

### P. Places, organizations, life events

| # | Change | v1 now | Source |
|---|---|---|---|
| P1 | How many organizations of each kind and size | rule-built | County Business Patterns 2023 |
| P2 | How rural D5 and D6 are | set by hand | RUCC 2023 |
| P3 | Distances to groceries and dialysis | district table | Food access (SRAM 2025), CMS dialysis list |
| P4 | Marriages and divorces | zero | NCHS 2000-24 |
| P5 | Births and deaths | 3 each | NCHS natality and mortality (not yet downloaded) |

### R. Rates tuned last

| # | Change | v1 now | Target | Source |
|---|---|---|---|---|
| R1 | Overdraft fees, kept concentrated | 264 a day, $29 average | 120-180 a day | plan; FFIEC Call Reports for revenue |
| R2 | Rural cash share (D5, D6) | 17.7% | 21%; recheck the city-wide 14% | DCPC 2025 |
| R3 | Paid tax preparation | 65% of prepared returns | about half | IRS SOI (no EITC-by-preparer table exists) |
| R4 | Utility disconnections, as a notice-to-shutoff chain | 6.8 a day | 11-12 a day | EIA 2024, RECS 2024 |
| R5 | Payday loans | 6.5 new a day, average $326 | reset from 2025 state reports | CA DFPI 2025 (average $251, 362% APR, about 70% repeat), TX OCCC, CFPB 2014 |
| R6 | Scam losses: rare and heavy-tailed, largest for 60+ | all $1,000-1,500 | heavy tail | FTC Sentinel 2024, IC3 2025 |

### What the downloads can't settle

Household structure stays rule-built until ACS PUMS (tier 3). General trip lengths need NHTS. Income swings need SIPP or JPMC. Overdraft concentration and notice-to-shutoff chains can only be checked across the month run (option B).
