# Halvern: one simulated day of transactions in a synthetic American city

Halvern is an invented city of about 100,000 people. This package holds one generated day
(Wednesday, March 3, 2027) and the simulator that produced it. Every record is a job someone
was trying to get done: a purchase, a bill, a benefit, a school day, a bus ride, a failed
attempt, an hour of unpaid care.

Nothing here describes a real person, business or local agency. Names of people, companies,
churches, schools, city and county offices were invented, and any resemblance to a real one is
coincidental. Federal programs and agencies that the specification itself requires (Social
Security, Medicare, Medicaid, SNAP, WIC, TANF, the IRS, the Treasury, the Postal Service) keep
their real names, because the records could not show a Part B premium or a SNAP purchase otherwise.

## What is in the package

| File | What it holds |
|---|---|
| `out/records.csv` | 201,753 records, 34 columns, in time order. The main table. The last three tag records with the systems lens's mapped blocks. |
| `out/households.csv` | 43,450 rows: 41,400 households plus 2,050 one-person group-quarters units; `block_id` names the mapped block a household lives on |
| `out/persons.csv` | 99,694 residents |
| `out/organizations.csv` | 1,672 businesses, agencies, nonprofits and outside parties |
| `out/public_services_context.csv` | One row per agency or service with its daily operating cost and funding |
| `out/assumptions.csv` | Every estimate, its value, a one-line rationale, and whether it is an anchor or an estimate |
| `out/summary.md` | Counts, calibration against the anchors, fees, public dollars, costliest frictions, checks |
| `out/household_ledger.csv` | Opening and closing balances per household, proving the money reconciles |
| `detailed_sample_500.csv` | The 500 hand-written records on their own, for quick reading |
| `simulate.py`, `halvern_sim/` | The simulator |
| `detailed_overrides.csv` | The hand-written text, keyed to record ids of the baseline day |
| `blocks.json` | The systems lens's six mapped blocks, one per district (a copy of `systems-lens/blocks.json`) |
| `tools/` | Scripts used to pick the 500 records, merge the hand-written text, and package a run as a zip (`make_zip.py`) |

## Run it

Requires Python 3.10 or later and `numpy`. A full day takes about 30 seconds.

```
python simulate.py                       # the baseline day, written to ./out
python simulate.py --out elsewhere       # same day, different folder
python simulate.py --households 4140     # a 10% city for quick tests
python simulate.py --seed 7              # a different city with the same structure
```

The same seed, date and options always give byte-identical files.

## Change the date

```
python simulate.py --date 2027-03-05 --out out_fri     # a Friday payday
python simulate.py --date 2027-03-10 --out out_wed2    # second Wednesday: a Social Security cohort is paid
python simulate.py --date 2027-07-04 --out out_july4   # a holiday in summer
```

The residents, employers, bills and balances are built from the seed alone, so the same people
appear on every date. The date then decides what happens: which pay cycles land, which Social
Security cohort is paid (the 3rd, or the second, third or fourth Wednesday), SSI on the 1st,
which bills are due by day of month, SNAP issuance day by case, whether school is in session,
tax-refund season, weekend hours and closures, church services. The default date is set by
`SIM_DATE` in `halvern_sim/config.py`.

## Storms and other shocks

```
python simulate.py --weather storm --out out_storm     # winter storm
python simulate.py --weather heat --out out_heat       # heat wave
python simulate.py --gas-price 4.79 --out out_gas      # fuel price shock
python simulate.py --grocery-price-mult 1.12           # groceries 12% dearer
python simulate.py --portal-outage 480-1020            # benefits portal down 8am to 5pm
python simulate.py --portal-outage none                # no outage
```

`--weather` changes many rates at once (trips, transit delays, missed shifts, school closure,
emergency visits, outages, deliveries); the multipliers are in `weather_mult()` in `config.py`.
Other shocks are plain numbers in `PARAMS` in the same file: `CARD_READER_OUTAGE` and
`BUS_BREAKDOWN` (start and end minute of the incident), `PURCHASE_FREQ`, `CASH_MULT`,
`GAS_PRICE`. Benefit amounts, the Part B premium, poverty guidelines, tax rates and the wage
scale are also there. To model a policy change (a benefit cut, a fee cap, a new bus route),
change the number or the few lines that use it and compare the two output folders.

## Move the city forward in time

```
python simulate.py --days 7 --out week                 # March 3 through March 9
```

This writes one folder per day (`week/2027-03-03/`, and so on) and a `state_<date>.json` after each day.
Each day starts from the balances the previous day ended with: checking, savings, cash,
prepaid cards, card debt, SNAP and WIC balances. To continue later, or to branch:

```
python simulate.py --date 2027-03-10 --state-in week/state_2027-03-09.json --state-out week/state_2027-03-10.json --out week/2027-03-10
```

What carries forward and what does not:

- Carries forward: every balance, so a bounced payment on Tuesday leaves less on Wednesday.
- Does not carry forward: the roster. Nobody ages, changes jobs or moves between days; a birth
  or death is recorded on its day but the household list is not edited. For a month this is a
  fair approximation. For a year, advance the roster in `population.py` between runs.
- An unpaid bill is not automatically retried on a later day; it shows up as arrears only
  through the lower balance.

## Reading records.csv

- `job_category` is `category.kind`, for example `food.grocery_snap_purchase`. There are 367 kinds.
- `amount_gross` is the face amount: the price including sales tax and before fees; for a
  transfer the amount moved; for a prescription the cash price; for a public service the full
  cost of providing it.
- `amount_paid_by_user` is what left the person's pocket, fees included.
  `amount_paid_by_third_party` is what an insurer, program or agency paid, and
  `third_party_payer` names it. `imputed_public_cost` is the full cost of a public service
  whether or not anyone was charged.
- `sales_tax` is included in `amount_gross`, at 7% on taxable goods.
- Every paycheck has linked rows for income tax withholding and FICA (`related_record_id`).
  A Social Security deposit shows the gross benefit; the Part B premium is a linked row.
- A retry points to the attempt that failed through `related_record_id`.
- Party ids: `P…` people, `H…` households, `O…` organizations including outside parties such
  as the Treasury, card networks, and "Customers (general public)".
- People in nursing homes, the jail, dorms, shelters and group homes are one-person units in
  `households.csv` with `household_type` starting `group_quarters:`.
- `birth_cohort` in `persons.csv` is the generation and birth year, for example `millennial_1987`.
- `weight` in `households.csv` is 1 for the full city and larger when you run a sample.
- `block_id`, `block_pattern` and `context_ids` come from `blocks.json`. Each block chooses about 400 households in its
  district, and every record those households make carries the block's id. A record that follows one of the block's
  patterns, such as a payday loan on Larkin Avenue, also carries the pattern and the circumstances it links to. The pass
  runs after the day and draws no random numbers, so the other 31 columns are the same with or without it. Turn it off
  with `--no-blocks`, or point at another file with `--blocks`.

## The 500 hand-written records

The simulator writes templated text for every row. A stratified sample of 500 rows, covering
every district, record type and income group, then had its `job_statement` and `narrative`
written by hand; those narratives start with `[detailed]`. The text is stored in
`detailed_overrides.csv` and is applied only to the baseline day (default date, seed, size,
weather and prices), where each record id, job category and actor match. Any other run gets
templated text throughout. To redo the sample after changing the simulator, run
`tools/make_detailed_dump.py`, rewrite `detail_parts/part*.txt`, then `tools/merge_detailed.py`.

## Limits worth knowing

- One day cannot match annual spending shares. Rent bunches at the start of the month and few
  people are paid on a Wednesday the 3rd; `summary.md` explains each gap.
- The 2027 Medicare Part B premium ($209.50) is a projection, not a published figure. SNAP
  amounts are the fiscal 2027 allotments; the Social Security adjustment is the announced 3.6%.
- Tax refunds and credits are drawn from distributions, not computed from a tax return.
- Travel distances come from a district-to-district table, so some single trips look long for
  the errand.
- All of this is labeled, with rationale, in `assumptions.csv`.
