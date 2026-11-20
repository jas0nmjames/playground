# Evidence checks: the typed-day set

Simulator: v2 in progress (`sim/`): caregiving at home from ATUS; calendar batch (holidays, bank-day pay and autopays, SNAP load days, ATUS hours, DCPC day of week, NOAA weights). 18 simulated days stand for 2027; each day's weight is the number of 2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence report's ids and grades are filled in.

## Targets against the weighted year

| Target | Item | Year (weighted) | Mar 3 | Target | Verdict | Status |
|---|---|---|---|---|---|---|
| T01 | Overdraft fees | 268.5 | 251.0 | 120 to 180 fees per day | HIGH | firm |
| T02 | New payday loans | 7.1 | 9.0 | 25 to 80 loans per day | LOW | provisional |
| T03 | Auto title loan payments | 0.0 | 0.0 | 15 to 25 payments per day | LOW | firm |
| T04 | Title-loan repossessions | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T05 | Utility disconnections | 7.5 | 8.0 | 11 to 12 disconnections per day | LOW | firm |
| T06 | Medical care delayed by debt | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T07 | Unpaid caregiving at home | 3,509 | 3,423 | 2750 to 4130 hours per day | in range | firm |
| T15 | Unpaid caregiving on visits | 1,710 | 1,679 | 1220 to 6250 hours per day | in range | provisional |
| T08 | Aide visits not completed | 7.8% | 7.4% | report only | reported | firm |
| T09 | Scam losses | 0.6% | 0.8% | report only | reported | provisional |
| T10 | Benefits-cliff job | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T11 | Rural cash share | 18.0% | 17.0% | 21% (within 2 points) | LOW | firm |
| T12 | Paid tax preparation | 69.0% | 69.2% | 0.45 to 0.55 share of prepared returns | HIGH | provisional |
| T13 | Pawn, check cashing, money orders | 97.2 | 101.0 | report only | reported | firm |
| T14 | Truly absent jobs | 0.0 | 0.0 | present (> 0) | ABSENT | firm |

## Each day

| Date | Class | Weather | Weight | overdraft fees | payday loans new | title loans new | utility shutoff notices | utility disconnections | caregiving hours home | aide visits missed | scam losses | paid tax prep | free tax prep | records |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027-03-03 | Mar 3 baseline (not weighted) | ordinary | 0.0 | 251 | 9 | 1 | 25 | 8 | 3,422.6 | 51 | 3 | 108 | 48 | 201,769 |
| 2027-07-05 | holiday_major | ordinary | 7.0 | 250 | 0 | 0 | 12 | 8 | 3,468.8 | 63 | 3 | 0 | 0 | 118,044 |
| 2027-10-11 | holiday_minor | ordinary | 5.0 | 231 | 10 | 2 | 22 | 12 | 3,481.2 | 55 | 3 | 0 | 0 | 154,517 |
| 2027-10-09 | saturday | ordinary | 52.0 | 270 | 8 | 4 | 23 | 2 | 3,511.9 | 0 | 4 | 0 | 0 | 125,662 |
| 2027-10-10 | sunday | ordinary | 52.0 | 300 | 0 | 0 | 21 | 9 | 3,522.9 | 0 | 0 | 0 | 0 | 137,722 |
| 2027-03-02 | eitc_wave | ordinary | 6.0 | 238 | 8 | 3 | 26 | 11 | 3,480.1 | 58 | 2 | 100 | 41 | 176,781 |
| 2027-09-01 | ssi_first | ordinary | 11.0 | 418 | 13 | 2 | 29 | 6 | 3,515.5 | 52 | 2 | 0 | 0 | 239,722 |
| 2027-11-03 | ss_third | ordinary | 9.0 | 282 | 9 | 5 | 24 | 7 | 3,411.3 | 56 | 4 | 0 | 0 | 199,243 |
| 2027-10-13 | ss_wednesday | ordinary | 12.0 | 267 | 7 | 0 | 17 | 7 | 3,574.6 | 55 | 2 | 0 | 0 | 199,664 |
| 2027-10-20 | ss_wednesday | ordinary | 12.0 | 269 | 10 | 4 | 22 | 4 | 3,471.4 | 59 | 3 | 0 | 0 | 204,725 |
| 2027-10-27 | ss_wednesday | ordinary | 12.0 | 258 | 2 | 1 | 24 | 9 | 3,555.1 | 42 | 3 | 0 | 0 | 198,437 |
| 2027-10-08 | friday | ordinary | 20.0 | 260 | 7 | 2 | 19 | 9 | 3,517.0 | 44 | 5 | 0 | 0 | 246,456 |
| 2027-10-15 | friday | ordinary | 20.0 | 267 | 13 | 3 | 18 | 8 | 3,484.9 | 57 | 2 | 0 | 0 | 271,537 |
| 2027-03-16 | tax_season_weekday | ordinary | 34.0 | 237 | 9 | 4 | 29 | 4 | 3,564.9 | 62 | 1 | 114 | 52 | 181,096 |
| 2027-10-05 | weekday_early | ordinary | 31.8 | 287 | 10 | 3 | 24 | 12 | 3,449.7 | 52 | 2 | 0 | 0 | 183,706 |
| 2027-10-14 | weekday_mid | ordinary | 32.8 | 238 | 8 | 5 | 32 | 7 | 3,463.5 | 52 | 3 | 0 | 0 | 188,377 |
| 2027-10-26 | weekday_late | ordinary | 38.8 | 253 | 8 | 6 | 30 | 12 | 3,539.7 | 54 | 2 | 0 | 0 | 171,855 |
| 2027-01-19 | storm | storm | 1.4 | 213 | 5 | 5 | 27 | 9 | 3,469.9 | 121 | 3 | 0 | 0 | 136,706 |
| 2027-07-22 | heat | heat | 8.3 | 210 | 4 | 5 | 28 | 6 | 3,543.4 | 58 | 0 | 0 | 0 | 144,158 |

## Supporting figures (weighted year, per day)

- overdraft fee dollars: 7,458
- payday rollovers: 3.1
- payday repayments: 8.2
- title loans new: 3.1
- utility shutoff notices: 24.4
- utility reconnections: 7.9
- medical payment plans: 118.8
- caregiving hours visits: 1,710
- caregiving zero dollar records: 5,141
- aide visits: 499.3
- aide misses with linked record: 3.6
- scam attempts: 367.5
- scam loss dollars: 1,338
- benefits cliff tagged: 6.1
- pawn: 26.8
- check cashing: 42.5
- money orders: 27.9
- absent car disabled by lender: 0.0
- absent direct express failure: 0.0
- absent called in on day off: 0.0
- absent snap interview call: 0.0
- absent h2a households: 0.0
- largest single scam loss on any typed day: $1,500

## Limits

- Each day is simulated from the same opening balances; nothing carries between days (option A). Chains such as notice to shutoff, and the concentration of overdraft fees, need the month run (option B).
- Most classes are represented by October days. Heating-season (Nov-Mar) and cooling-season (Jun-Sep) effects are only in the days that fall in those months.
- Storm (1.36) and heat (8.27) weekdays a year are 2015-2025 averages for Halvern's counties (`sources/derived/weather_days.csv`); afternoon thunderstorms are not modeled.
