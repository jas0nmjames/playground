# Evidence checks: the typed-day set

Simulator: v2 in progress (`sim/`): caregiving at home from ATUS; calendar batch; inputs batch; missing-jobs batch (title loans, repossessions, lender shutoffs, care put off, abandoned prescriptions, care purchases, SNAP interviews, Medicaid work-report failures, H-2A workers, cliff, call-ins, Direct Express, aide no-show cover). 18 simulated days stand for 2027; each day's weight is the number of 2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence report's ids and grades are filled in.

## Targets against the weighted year

| Target | Item | Year (weighted) | Mar 3 | Target | Verdict | Status |
|---|---|---|---|---|---|---|
| T01 | Overdraft fees | 188.4 | 207.0 | 120 to 180 fees per day | HIGH | firm |
| T02 | New payday loans | 7.5 | 11.0 | 25 to 80 loans per day | LOW | provisional |
| T03 | Auto title loan payments | 7.8 | 7.0 | 5 to 10 payments per day | in range | firm |
| T04 | Title-loan repossessions | 1.1 | 1.0 | present (> 0) | present | firm |
| T05 | Utility disconnections | 8.9 | 4.0 | 11 to 12 disconnections per day | in range | firm |
| T16 | Utility disconnect notices | 25.6 | 19.0 | 40 to 55 notices per day | LOW | firm |
| T06 | Medical care delayed by debt | 2.1 | 2.0 | present (> 0) | present | firm |
| T07 | Unpaid caregiving at home | 3,485 | 3,524 | 2750 to 4130 hours per day | in range | firm |
| T15 | Unpaid caregiving on visits | 1,703 | 1,676 | 1220 to 6250 hours per day | in range | provisional |
| T08 | Aide visits not completed | 7.2% | 7.1% | report only | reported | firm |
| T09 | Scam losses | 0.8% | 1.1% | report only | reported | provisional |
| T10 | Benefits-cliff job | 0.9 | 0.0 | present (> 0) | present | firm |
| T11 | Rural cash share | 17.4% | 16.7% | 21% (within 2 points) | LOW | firm |
| T12 | Paid tax preparation | 75.4% | 68.6% | 0.45 to 0.55 share of prepared returns | HIGH | provisional |
| T13 | Pawn, check cashing, money orders | 95.5 | 122.0 | report only | reported | firm |
| T14 | Truly absent jobs | 131.6 | 113.0 | present (> 0) | present | firm |

## Each day

| Date | Class | Weather | Weight | overdraft fees | payday loans new | title loans new | utility shutoff notices | utility disconnections | caregiving hours home | aide visits missed | scam losses | paid tax prep | free tax prep | records |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027-03-03 | Mar 3 baseline (not weighted) | ordinary | 0.0 | 207 | 11 | 1 | 19 | 4 | 3,524.3 | 52 | 4 | 107 | 49 | 202,421 |
| 2027-07-05 | holiday_major | ordinary | 7.0 | 196 | 0 | 0 | 24 | 11 | 3,363.4 | 52 | 3 | 0 | 0 | 119,077 |
| 2027-10-11 | holiday_minor | ordinary | 5.0 | 172 | 9 | 2 | 25 | 4 | 3,512.3 | 52 | 0 | 0 | 0 | 154,317 |
| 2027-10-09 | saturday | ordinary | 52.0 | 177 | 10 | 1 | 29 | 6 | 3,491.9 | 0 | 3 | 0 | 0 | 126,131 |
| 2027-10-10 | sunday | ordinary | 52.0 | 225 | 0 | 0 | 32 | 11 | 3,455.5 | 0 | 4 | 0 | 0 | 139,323 |
| 2027-03-02 | eitc_wave | ordinary | 6.0 | 178 | 5 | 2 | 21 | 10 | 3,452.0 | 51 | 2 | 95 | 55 | 177,895 |
| 2027-09-01 | ssi_first | ordinary | 11.0 | 324 | 12 | 2 | 26 | 8 | 3,470.4 | 43 | 1 | 0 | 0 | 239,934 |
| 2027-11-03 | ss_third | ordinary | 9.0 | 204 | 6 | 4 | 30 | 6 | 3,457.1 | 57 | 4 | 0 | 0 | 199,913 |
| 2027-10-13 | ss_wednesday | ordinary | 12.0 | 171 | 8 | 4 | 27 | 5 | 3,518.0 | 57 | 1 | 0 | 0 | 199,834 |
| 2027-10-20 | ss_wednesday | ordinary | 12.0 | 186 | 6 | 4 | 19 | 11 | 3,490.8 | 51 | 5 | 0 | 0 | 205,991 |
| 2027-10-27 | ss_wednesday | ordinary | 12.0 | 178 | 7 | 1 | 23 | 9 | 3,482.3 | 50 | 2 | 0 | 0 | 199,398 |
| 2027-10-08 | friday | ordinary | 20.0 | 190 | 9 | 2 | 18 | 10 | 3,532.8 | 35 | 1 | 0 | 0 | 248,918 |
| 2027-10-15 | friday | ordinary | 20.0 | 180 | 5 | 3 | 17 | 14 | 3,422.0 | 47 | 3 | 0 | 0 | 272,143 |
| 2027-03-16 | tax_season_weekday | ordinary | 34.0 | 162 | 8 | 2 | 17 | 8 | 3,437.5 | 48 | 3 | 142 | 42 | 181,672 |
| 2027-10-05 | weekday_early | ordinary | 31.8 | 217 | 9 | 5 | 26 | 5 | 3,545.1 | 59 | 1 | 0 | 0 | 184,371 |
| 2027-10-14 | weekday_mid | ordinary | 32.8 | 170 | 7 | 6 | 34 | 11 | 3,491.9 | 38 | 4 | 0 | 0 | 188,566 |
| 2027-10-26 | weekday_late | ordinary | 38.8 | 153 | 15 | 3 | 24 | 10 | 3,531.9 | 53 | 3 | 0 | 0 | 171,528 |
| 2027-01-19 | storm | storm | 1.4 | 149 | 11 | 2 | 21 | 8 | 3,548.9 | 106 | 5 | 0 | 0 | 137,085 |
| 2027-07-22 | heat | heat | 8.3 | 149 | 7 | 1 | 22 | 13 | 3,458.6 | 54 | 2 | 0 | 0 | 144,415 |

## Supporting figures (weighted year, per day)

- overdraft fee dollars: 5,250
- payday rollovers: 4.0
- payday repayments: 10.0
- title loans new: 2.4
- utility shutoff notices: 25.6
- utility reconnections: 9.0
- medical payment plans: 113.2
- caregiving hours visits: 1,703
- caregiving zero dollar records: 5,131
- aide visits: 487.4
- aide misses with linked record: 18.4
- scam attempts: 364.9
- scam loss dollars: 1,761
- benefits cliff tagged: 6.8
- pawn: 24.2
- check cashing: 42.1
- money orders: 29.2
- absent car disabled by lender: 1.6
- absent direct express failure: 1.5
- absent called in on day off: 53.3
- absent snap interview call: 7.4
- absent h2a households: 67.8
- largest single scam loss on any typed day: $1,500

## Limits

- Each day is simulated from the same opening balances; nothing carries between days (option A). Chains such as notice to shutoff, and the concentration of overdraft fees, need the month run (option B).
- Most classes are represented by October days. Heating-season (Nov-Mar) and cooling-season (Jun-Sep) effects are only in the days that fall in those months.
- Storm (1.36) and heat (8.27) weekdays a year are 2015-2025 averages for Halvern's counties (`sources/derived/weather_days.csv`); afternoon thunderstorms are not modeled.
- Wages are boosted on purpose: every worker is paid 1.23 times the national pay for their occupation (about 14% above real 2027 pay) to make up for Halvern's smaller households. Household money is closer to right this way; pay for a single job is not. Kept for v2, dropped in v3 (see WAGE_SCALE in `sim/halvern_sim/config.py`).
