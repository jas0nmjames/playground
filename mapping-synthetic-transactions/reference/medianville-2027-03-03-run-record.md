# Medianville run record: Wednesday, March 3, 2027 (baseline day)

v1 shipped under the city's first name, Halvern. Its zip, `data/halvern/` and the archived viewers keep that name.

Generated 2026-11-16 from the [transaction generator prompt](medianville-transaction-generator-prompt.md) in GENERATOR mode.
Seed 20270303, weather ordinary, full city. Deterministic: the same options reproduce the files byte for byte.

## Deliverable

`halvern_2027-03-03.zip` (16 MB; 107 MB unpacked), delivered in the chat that produced it. Since 2026-11-20 the latest pages load a copy with only the name changed, `data/medianville_2027-03-03.zip` (decision 1.6 in the [decision log](design-decisions.md)). The original holds:

- `out/records.csv`: 201,753 records, 31 columns, 367 job categories
- `out/households.csv` (41,400 households + 2,050 group-quarters units), `out/persons.csv` (99,694), `out/organizations.csv` (1,672)
- `out/public_services_context.csv`, `out/assumptions.csv`, `out/summary.md`, `out/household_ledger.csv`
- `detailed_sample_500.csv`: the 500 hand-written records (narrative starts with `[detailed]`)
- `simulate.py` + `halvern_sim/` (about 8,400 lines of Python, needs numpy), `README.md`

## Calibration reached

| Anchor | Target | Simulated |
|---|---|---|
| Residents / resident jobs | ~100,000 / ~48,000 | 99,694 / 47,728 |
| Industry mix | BLS shares | largest gap 0.2 points |
| Payments per adult per month | ~43 | 44.3 |
| Cash share of payments | ~14% | 14.3% (55+ 17.5%; poverty 37.2%; rural 16.8%) |
| Could cover a $400 emergency | 63% | 63.0% |
| Below ALICE threshold | ~4 in 10 | 41.5% (10.0% poverty + 31.5% ALICE) |
| Spending order | housing, transportation, food | 40.4%, 15.0%, 14.6% of the day's outlays |

Checks: money reconciles for every household; nobody exceeds 24 hours; every paycheck has linked withholding and FICA.

## Findings worth mining

- 13.4% of households had at least one failed attempt (poverty 28.5%, ALICE 16.1%, above 9.5%).
- Unpaid jobs took 16,736 hours; caregiving at home is half of it.
- Fees: tax-prep and refund-transfer fees are the largest fee for poverty and ALICE households; card interest for those above.
- Costliest frictions by combined time and money: fees, distance, waits, schedule volatility, no transit.
- Public dollars on the day: $7.8M in transfers in, $2.9M in services delivered.

## Known limits

- One day cannot match annual CES shares: rent bunches early in the month and few people are paid on a Wednesday the 3rd, so the insurance/pensions share runs low (5.2% vs 12.4%).
- SSI and VA pay on the 1st, so they are absent; most Social Security pays on later Wednesdays.
- The 2027 Part B premium ($209.50) is a projection. Tax refunds are drawn from distributions.
- Trip distances come from a district-to-district table, so a few errands look long.
- Federal programs and agencies keep real names (the prompt requires them); everything local is invented.

## Re-running

`python simulate.py --date YYYY-MM-DD`, `--weather storm|heat`, `--gas-price`, `--grocery-price-mult`, `--portal-outage`, `--days N` (carries balances forward), `--households N`, `--seed N`. Hand-written text applies only to the baseline day.
