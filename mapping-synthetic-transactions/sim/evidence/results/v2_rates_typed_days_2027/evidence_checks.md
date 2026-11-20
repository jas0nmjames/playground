# Evidence checks: the typed-day set

Simulator: v2 (`sim/`): all batches; rates tuned. 18 simulated days stand for 2027; each day's weight is the number of 2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence report's ids and grades are filled in.

## Targets against the weighted year

| Target | Item | Year (weighted) | Mar 3 | Target | Verdict | Status |
|---|---|---|---|---|---|---|
| T01 | Overdraft fees | 142.6 | 159.0 | 120 to 180 fees per day | in range | firm |
| T02 | New payday loans | 19.0 | 34.0 | 10 to 25 loans per day | in range | firm |
| T03 | Auto title loan payments | 7.8 | 5.0 | 5 to 10 payments per day | in range | firm |
| T04 | Title-loan repossessions | 1.1 | 1.0 | present (> 0) | present | firm |
| T05 | Utility disconnections | 12.4 | 10.0 | 11 to 12 disconnections per day | in range | firm |
| T16 | Utility disconnect notices | 43.3 | 44.0 | 40 to 55 notices per day | in range | firm |
| T06 | Medical care delayed by debt | 2.5 | 4.0 | present (> 0) | present | firm |
| T07 | Unpaid caregiving at home | 3,458 | 3,491 | 2750 to 4130 hours per day | in range | firm |
| T15 | Unpaid caregiving on visits | 1,716 | 1,746 | 1220 to 6250 hours per day | in range | provisional |
| T08 | Aide visits not completed | 7.5% | 6.9% | report only | reported | firm |
| T09 | Scam losses | 0.8% | 1.6% | report only | reported | provisional |
| T10 | Benefits-cliff job | 0.8 | 0.0 | present (> 0) | present | firm |
| T11 | Rural cash share | 18.7% | 17.6% | 19% (within 2 points) | in range | firm |
| T12 | Paid tax preparation | 50.5% | 53.5% | 0.49 to 0.59 share of returns filed | in range | firm |
| T13 | Pawn, check cashing, money orders | 99.6 | 106.0 | report only | reported | firm |
| T14 | Truly absent jobs | 130.2 | 112.0 | present (> 0) | present | firm |

## Each day

| Date | Class | Weather | Weight | overdraft fees | payday loans new | title loans new | utility shutoff notices | utility disconnections | caregiving hours home | aide visits missed | scam losses | paid tax prep | free tax prep | records |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027-03-03 | Mar 3 baseline (not weighted) | ordinary | 0.0 | 159 | 34 | 4 | 44 | 10 | 3,490.6 | 48 | 6 | 223 | 48 | 202,462 |
| 2027-07-05 | holiday_major | ordinary | 7.0 | 149 | 0 | 0 | 37 | 12 | 3,366.6 | 62 | 2 | 0 | 0 | 119,310 |
| 2027-10-11 | holiday_minor | ordinary | 5.0 | 123 | 26 | 3 | 30 | 12 | 3,589.4 | 41 | 7 | 0 | 0 | 154,426 |
| 2027-10-09 | saturday | ordinary | 52.0 | 156 | 24 | 2 | 49 | 16 | 3,483.1 | 0 | 3 | 0 | 0 | 126,432 |
| 2027-10-10 | sunday | ordinary | 52.0 | 141 | 0 | 0 | 41 | 5 | 3,482.8 | 0 | 4 | 0 | 0 | 138,709 |
| 2027-03-02 | eitc_wave | ordinary | 6.0 | 154 | 19 | 1 | 46 | 14 | 3,380.0 | 39 | 6 | 220 | 53 | 177,368 |
| 2027-09-01 | ssi_first | ordinary | 11.0 | 234 | 23 | 2 | 40 | 8 | 3,451.6 | 45 | 1 | 0 | 0 | 240,572 |
| 2027-11-03 | ss_third | ordinary | 9.0 | 159 | 25 | 6 | 58 | 13 | 3,452.2 | 37 | 2 | 0 | 0 | 200,345 |
| 2027-10-13 | ss_wednesday | ordinary | 12.0 | 139 | 19 | 2 | 44 | 13 | 3,537.2 | 44 | 5 | 0 | 0 | 200,075 |
| 2027-10-20 | ss_wednesday | ordinary | 12.0 | 152 | 19 | 2 | 50 | 12 | 3,449.6 | 47 | 2 | 0 | 0 | 205,335 |
| 2027-10-27 | ss_wednesday | ordinary | 12.0 | 130 | 14 | 3 | 44 | 15 | 3,390.3 | 71 | 3 | 0 | 0 | 199,623 |
| 2027-10-08 | friday | ordinary | 20.0 | 128 | 22 | 0 | 45 | 6 | 3,468.9 | 59 | 2 | 0 | 0 | 248,305 |
| 2027-10-15 | friday | ordinary | 20.0 | 152 | 22 | 2 | 43 | 13 | 3,398.7 | 57 | 4 | 0 | 0 | 272,175 |
| 2027-03-16 | tax_season_weekday | ordinary | 34.0 | 123 | 26 | 1 | 40 | 13 | 3,408.4 | 51 | 4 | 195 | 54 | 182,267 |
| 2027-10-05 | weekday_early | ordinary | 31.8 | 141 | 33 | 2 | 35 | 16 | 3,430.9 | 51 | 1 | 0 | 0 | 184,181 |
| 2027-10-14 | weekday_mid | ordinary | 32.8 | 135 | 15 | 1 | 43 | 18 | 3,533.4 | 49 | 3 | 0 | 0 | 188,689 |
| 2027-10-26 | weekday_late | ordinary | 38.8 | 128 | 23 | 2 | 47 | 13 | 3,435.4 | 49 | 3 | 0 | 0 | 171,699 |
| 2027-01-19 | storm | storm | 1.4 | 105 | 14 | 4 | 48 | 14 | 3,504.2 | 119 | 2 | 0 | 0 | 137,986 |
| 2027-07-22 | heat | heat | 8.3 | 140 | 16 | 2 | 37 | 9 | 3,421.6 | 48 | 1 | 0 | 0 | 144,457 |

## Supporting figures (weighted year, per day)

- overdraft fee dollars: 3,977
- payday rollovers: 8.7
- payday repayments: 28.3
- title loans new: 1.5
- utility shutoff notices: 43.3
- utility reconnections: 12.8
- medical payment plans: 113.1
- caregiving hours visits: 1,716
- caregiving zero dollar records: 5,122
- aide visits: 491.8
- aide misses with linked record: 20.1
- scam attempts: 376.3
- scam loss dollars: 9,272
- benefits cliff tagged: 7.3
- pawn: 25.5
- check cashing: 44.3
- money orders: 29.7
- absent car disabled by lender: 1.6
- absent direct express failure: 1.7
- absent called in on day off: 52.7
- absent snap interview call: 6.4
- absent h2a households: 67.8
- largest single scam loss on any typed day: $91,102

## Limits

- Each day is simulated from the same opening balances; nothing carries between days (option A). Chains such as notice to shutoff, and the concentration of overdraft fees, need the month run (option B).
- Most classes are represented by October days. Heating-season (Nov-Mar) and cooling-season (Jun-Sep) effects are only in the days that fall in those months.
- Storm (1.36) and heat (8.27) weekdays a year are 2015-2025 averages for Halvern's counties (`sources/derived/weather_days.csv`); afternoon thunderstorms are not modeled.
- Wages are boosted on purpose: every worker is paid 1.23 times the national pay for their occupation (about 14% above real 2027 pay) to make up for Halvern's smaller households. Household money is closer to right this way; pay for a single job is not. Kept for v2, dropped in v3 (see WAGE_SCALE in `sim/halvern_sim/config.py`).
