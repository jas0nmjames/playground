# Evidence checks: the typed-day set

Simulator: v2 in progress (`sim/`): caregiving at home set from ATUS; everything else as v1. 17 simulated days stand for 2027; each day's weight is the number of 2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence report's ids and grades are filled in.

## Targets against the weighted year

| Target | Item | Year (weighted) | Mar 3 | Target | Verdict | Status |
|---|---|---|---|---|---|---|
| T01 | Overdraft fees | 264.1 | 255.0 | 120 to 180 fees per day | HIGH | firm |
| T02 | New payday loans | 6.5 | 8.0 | 25 to 80 loans per day | LOW | provisional |
| T03 | Auto title loan payments | 0.0 | 0.0 | 15 to 25 payments per day | LOW | firm |
| T04 | Title-loan repossessions | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T05 | Utility disconnections | 6.8 | 10.0 | 11 to 12 disconnections per day | LOW | firm |
| T06 | Medical care delayed by debt | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T07 | Unpaid caregiving at home | 3,493 | 3,488 | 2750 to 4130 hours per day | in range | firm |
| T15 | Unpaid caregiving on visits | 1,722 | 1,709 | 1220 to 6250 hours per day | in range | provisional |
| T08 | Aide visits not completed | 7.6% | 6.4% | report only | reported | firm |
| T09 | Scam losses | 0.6% | 0.0% | report only | reported | provisional |
| T10 | Benefits-cliff job | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T11 | Rural cash share | 17.7% | 16.7% | 21% (within 2 points) | LOW | firm |
| T12 | Paid tax preparation | 65.0% | 63.6% | 0.45 to 0.55 share of prepared returns | HIGH | provisional |
| T13 | Pawn, check cashing, money orders | 98.3 | 124.0 | report only | reported | firm |
| T14 | Truly absent jobs | 0.0 | 0.0 | present (> 0) | ABSENT | firm |

## Each day

| Date | Class | Weather | Weight | overdraft fees | payday loans new | title loans new | utility shutoff notices | utility disconnections | caregiving hours home | aide visits missed | scam losses | paid tax prep | free tax prep | records |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027-03-03 | Mar 3 baseline (not weighted) | ordinary | 0.0 | 255 | 8 | 6 | 27 | 10 | 3,488.2 | 45 | 0 | 105 | 60 | 201,012 |
| 2027-07-05 | holiday | ordinary | 12.0 | 318 | 6 | 5 | 26 | 10 | 3,400.6 | 49 | 1 | 0 | 0 | 160,900 |
| 2027-10-09 | saturday | ordinary | 52.0 | 254 | 9 | 3 | 29 | 5 | 3,499.7 | 0 | 3 | 0 | 0 | 128,644 |
| 2027-10-10 | sunday | ordinary | 52.0 | 284 | 0 | 0 | 17 | 8 | 3,590.1 | 0 | 4 | 0 | 0 | 136,571 |
| 2027-03-02 | eitc_wave | ordinary | 6.0 | 249 | 11 | 1 | 18 | 9 | 3,458.2 | 49 | 2 | 114 | 58 | 184,645 |
| 2027-09-01 | ssi_first | ordinary | 8.0 | 429 | 8 | 4 | 22 | 8 | 3,467.9 | 47 | 3 | 0 | 0 | 238,518 |
| 2027-11-03 | ss_third | ordinary | 9.0 | 290 | 6 | 4 | 33 | 8 | 3,528.8 | 53 | 4 | 0 | 0 | 198,604 |
| 2027-10-13 | ss_wednesday | ordinary | 12.0 | 278 | 6 | 2 | 18 | 3 | 3,471.9 | 39 | 2 | 0 | 0 | 198,625 |
| 2027-10-20 | ss_wednesday | ordinary | 12.0 | 271 | 9 | 7 | 21 | 7 | 3,582.4 | 48 | 1 | 0 | 0 | 204,376 |
| 2027-10-27 | ss_wednesday | ordinary | 12.0 | 254 | 8 | 2 | 21 | 12 | 3,441.0 | 55 | 3 | 0 | 0 | 197,901 |
| 2027-10-08 | friday | ordinary | 21.0 | 234 | 10 | 3 | 27 | 10 | 3,504.3 | 53 | 0 | 0 | 0 | 234,899 |
| 2027-10-15 | friday | ordinary | 21.0 | 249 | 8 | 2 | 23 | 3 | 3,516.5 | 57 | 3 | 0 | 0 | 258,661 |
| 2027-03-16 | tax_season_weekday | ordinary | 34.0 | 241 | 7 | 4 | 20 | 4 | 3,454.3 | 49 | 1 | 99 | 54 | 188,501 |
| 2027-10-05 | weekday_early | ordinary | 31.0 | 274 | 5 | 6 | 18 | 11 | 3,357.1 | 55 | 1 | 0 | 0 | 191,559 |
| 2027-10-14 | weekday_mid | ordinary | 32.0 | 262 | 8 | 3 | 15 | 5 | 3,536.2 | 52 | 4 | 0 | 0 | 188,070 |
| 2027-10-26 | weekday_late | ordinary | 39.0 | 243 | 7 | 3 | 16 | 7 | 3,457.2 | 53 | 1 | 0 | 0 | 178,990 |
| 2027-01-19 | storm | storm | 4.0 | 201 | 8 | 6 | 20 | 4 | 3,468.8 | 111 | 3 | 0 | 0 | 125,340 |
| 2027-07-22 | heat | heat | 8.0 | 241 | 3 | 4 | 18 | 5 | 3,547.9 | 58 | 2 | 0 | 0 | 144,189 |

## Supporting figures (weighted year, per day)

- overdraft fee dollars: 7,404
- payday rollovers: 4.5
- payday repayments: 8.4
- title loans new: 3.1
- utility shutoff notices: 20.9
- utility reconnections: 7.1
- medical payment plans: 136.4
- caregiving hours visits: 1,722
- caregiving zero dollar records: 5,137
- aide visits: 496.7
- aide misses with linked record: 3.6
- scam attempts: 361.5
- scam loss dollars: 1,767
- benefits cliff tagged: 6.5
- pawn: 27.6
- check cashing: 42.7
- money orders: 28.1
- absent car disabled by lender: 0.0
- absent direct express failure: 0.0
- absent called in on day off: 0.0
- absent snap interview call: 0.0
- absent h2a households: 0.0
- largest single scam loss on any typed day: $1,500

## Limits

- Each day is simulated from the same opening balances; nothing carries between days (option A). Chains such as notice to shutoff, and the concentration of overdraft fees, need the month run (option B).
- Most classes are represented by October days. Heating-season (Nov-Mar) and cooling-season (Jun-Sep) effects are only in the days that fall in those months.
- The simulator has no federal-holiday logic, so the holiday day runs as an ordinary weekday.
- Storm and heat day counts (4 and 8) are placeholders until NOAA Storm Events data is downloaded.
