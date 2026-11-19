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
