# How the Medianville day was built: approach and steps

v1 shipped under the city's first name, Halvern. Its zip, `data/halvern/` and the archived viewers keep that name.

Companion to the [transaction generator prompt](medianville-transaction-generator-prompt.md) (the specification) and the [run record](medianville-2027-03-03-run-record.md) (the results). This note records how the dataset was produced, so the method can be repeated, criticized or changed.

## Model and setup

- **Model:** Claude Fable 5.2 (`claude-fable-5-2`), working as an agent in the Claude app, in one long session on 2026-11-16.
- **Environment:** a private Linux workspace with Python 3.13 and numpy. No other libraries.
- **Tools used:** a shell to run code, file read/write/edit, web search for a handful of 2027 program figures, a task list, and the project's docs.
- **No sub-agents.** One model wrote the code, ran it, read the output and wrote the 500 hand-written records.
- **Context limits:** the session outgrew the model's context window more than once and was continued from an automatic summary. The code and files on disk carried the work across those breaks; the summaries carried the decisions. Some detail of the early steps below therefore comes from those summaries, not from a verbatim record.
- **Input:** the prompt alone, run in GENERATOR mode with seed 20270303, date Wednesday March 3, 2027, ordinary weather, full city.

## The core decision: simulate, do not write

A model cannot write 200,000 consistent records by hand. Money would not reconcile and people would be in two places at once. So the model wrote a simulator, and used its own writing only where writing adds something: the job statements, the narrative templates and the 500 detailed records. The split is:

| Layer | Made by | Why |
|---|---|---|
| People, households, employers, balances, bills | Code, from the seed | Consistency at scale |
| What happens on the day | Code, from the date and weather | Time and money must add up |
| Text for every record | Templates the model wrote, filled by code | 367 job kinds, several phrasings each |
| Text for 500 sampled records | The model, one record at a time | Richness and a check on believability |

## Steps, in order

**1. Read the specification and fix the conventions.** The 31 columns, the controlled vocabularies, and the meaning of each amount field were settled before any code: gross is the face amount, user-paid includes fees, a public service carries its full cost as imputed public cost.

**2. Look up the few facts that had to be real.** The 2027 Social Security adjustment, SSI amounts, the projected Medicare Part B premium, fiscal 2027 SNAP allotments and deductions, and current Consumer Expenditure Survey shares. Everything else is an estimate, and each one is listed with a rationale in `assumptions.csv`.

**3. Build the organizations.** About 1,670 invented businesses, agencies, churches and schools across six districts, with hours, accepted payment methods and staff sizes, plus outside parties such as the Treasury, card processors and "customers in general".

**4. Build the population.** Households by type and district, then people with age, education, disability, language, coverage and benefits. Employment was fitted so that jobs match the 21-sector mix in the prompt. Wages, rents and mortgage costs were scaled until 41.5% of households fell below the ALICE threshold. (Note added 2026-11-20: the wage scale this produced, 1.23, pays each worker about 14% above real pay for their occupation, which makes up for Medianville's smaller households. See the wage note in the [data update plan](../03-grounding-in-evidence/medianville-data-update-plan.md).)

**5. Build each household's finances.** Wallets (checking, savings, cash, prepaid, card debt) and a list of recurring bills with due days and payment methods. The liquid-funds threshold was solved so that exactly 63% of adults could cover a $400 emergency.

**6. Plan and settle the day.** Each household first gets a skeleton of work, school and sleep. Generators then add income, bills, health care, school, caregiving, food, shopping, transport, public services, money services and miscellany, each claiming time from the person's free hours. Every action goes into one queue ordered by minute, and is settled in time order against the wallet. That ordering is what makes a declined card at 5 p.m. depend on a bill that drafted at 2 a.m.

**7. Add what households do not generate.** City-level life events at national daily rates (births, deaths, moves, admissions, evictions, court, jail, shelter, nursing home days), then the business day: payroll runs, tax deposits, card settlements, supply deliveries, farm sales, vendor payments.

**8. Calibrate.** Run, read the summary, adjust a knob, run again. Two knobs did most of the work: purchase frequency (to reach about 43 payments per adult per month) and a cash multiplier (to reach 14% cash). Each full run takes about 30 seconds, which made this loop cheap.

**9. Validate.** Automated checks: opening balance plus inflows minus outflows equals closing balance for every household; no person exceeds 24 hours; every paycheck has withholding and FICA rows; every value is in its controlled vocabulary; every job statement has the required sentence form; identical output under a changed hash seed.

**10. Hand-write 500 records.** A stratified sample was drawn across district, record type and income group. For each, the model read a one-line digest of the record (who, household, counterparty, amounts, method, time, outcome, friction) and wrote a situation, motivation, outcome and narrative. These were written in eight batches and merged into `detailed_overrides.csv`, keyed by record id, job category and actor so that text cannot land on the wrong row.

**11. Write the README, package, and record the run.**

## What reading the sample caught

Reading 500 records closely was the most effective test in the whole build. It exposed problems that the numeric checks passed:

- Union dues were being paid to a charity. Fixed by adding invented union locals.
- Alarm monitoring was billed by an online retailer. Fixed with an invented alarm company.
- A 91-year-old was working as a schoolteacher. Employment past age 80 was tapered sharply.
- A group-home resident held an implausible job. Capped.
- Lottery text said "cash only" on a debit purchase, and gig payouts named no platform. Templates fixed.
- Two-thirds of templated job statements said "I want X" where the prompt specifies "I want to". A rule now rewrites them.

Each population fix changed the random draws and so the record ids, which meant redrawing the sample. For that reason the simulator was frozen before the hand-writing began, and later fixes were limited to text.

## Problems solved along the way

- **Too many overdrafts** (about ten times a realistic rate). Autopay accounts are now topped up before a due date most of the time, and fewer accounts opt in to overdraft.
- **The $400 target was first met by shrinking all balances**, which left median checking near zero. Replaced with realistic balances and a solved threshold.
- **Time conflicts**, such as jurors also working a shift. Fixed by letting fixed commitments claim time before errands.
- **Unlucky draws on rare events** (zero births). Replaced with low-variance rounding.
- **Hidden non-determinism** from Python's string hashing. Replaced with arithmetic on ids.

## What was not fixed

Found after the freeze and left in, because fixing them would have invalidated the hand-written sample:

- Some employer and occupation pairs are odd (a call-center worker on a janitorial company's payroll).
- Trip distances come from a district table, so some errands are implausibly far, and one 97-year-old walks four miles.
- "Orthodontics" offices appear as general dental visits.
- Marriage licenses and divorce filings both came out at zero for the day.
- Tax refunds are drawn from distributions, not computed from returns.

## Judgment calls a reviewer should know about

- **Federal names are real** (IRS, Treasury, Medicare, SNAP, Postal Service); every local name is invented. The prompt asks for invented agencies but also requires those programs by name.
- **Full city is 41,400 households**, not 40,000, to land near 100,000 residents.
- **A "payment"** follows the Federal Reserve diary's idea and excludes payroll deductions, card-bill payments and ATM withdrawals.
- **Friction cost** values time at the city's median hourly wage.
- **Group-quarters residents** are one-person units and are left out of the spending comparison.

## If this is run again

1. Do the close reading earlier and on a smaller sample, before calibration is finished, so fixes are cheap.
2. Derive trip distance from locations, not a district table.
3. Tie occupations to employers, not only to sectors.
4. Have a second reader that has not seen the code review a fresh sample for believability.
5. Keep the freeze rule: no change to the simulator once hand-written text exists.
