# Evidence checks: the typed-day set

Simulator: v2 in progress (`sim/`): caregiving at home from ATUS; calendar, inputs and missing-jobs batches; places batch (CBP storefronts, rural grocery trips, a rural dialysis clinic). 18 simulated days stand for 2027; each day's weight is the number of 2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence report's ids and grades are filled in.

## Targets against the weighted year

| Target | Item | Year (weighted) | Mar 3 | Target | Verdict | Status |
|---|---|---|---|---|---|---|
| T01 | Overdraft fees | 196.2 | 213.0 | 120 to 180 fees per day | HIGH | firm |
| T02 | New payday loans | 5.4 | 6.0 | 25 to 80 loans per day | LOW | provisional |
| T03 | Auto title loan payments | 7.9 | 7.0 | 5 to 10 payments per day | in range | firm |
| T04 | Title-loan repossessions | 1.1 | 1.0 | present (> 0) | present | firm |
| T05 | Utility disconnections | 7.9 | 10.0 | 11 to 12 disconnections per day | LOW | firm |
| T16 | Utility disconnect notices | 23.6 | 32.0 | 40 to 55 notices per day | LOW | firm |
| T06 | Medical care delayed by debt | 2.9 | 3.0 | present (> 0) | present | firm |
| T07 | Unpaid caregiving at home | 3,480 | 3,510 | 2750 to 4130 hours per day | in range | firm |
| T15 | Unpaid caregiving on visits | 1,725 | 1,766 | 1220 to 6250 hours per day | in range | provisional |
| T08 | Aide visits not completed | 7.0% | 5.9% | report only | reported | firm |
| T09 | Scam losses | 0.9% | 0.6% | report only | reported | provisional |
| T10 | Benefits-cliff job | 0.8 | 0.0 | present (> 0) | present | firm |
| T11 | Rural cash share | 17.3% | 16.2% | 21% (within 2 points) | LOW | firm |
| T12 | Paid tax preparation | 70.1% | 71.7% | 0.45 to 0.55 share of prepared returns | HIGH | provisional |
| T13 | Pawn, check cashing, money orders | 98.8 | 117.0 | report only | reported | firm |
| T14 | Truly absent jobs | 128.3 | 116.0 | present (> 0) | present | firm |

## Each day

| Date | Class | Weather | Weight | overdraft fees | payday loans new | title loans new | utility shutoff notices | utility disconnections | caregiving hours home | aide visits missed | scam losses | paid tax prep | free tax prep | records |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027-03-03 | Mar 3 baseline (not weighted) | ordinary | 0.0 | 213 | 6 | 2 | 32 | 10 | 3,510.2 | 40 | 2 | 109 | 43 | 202,755 |
| 2027-07-05 | holiday_major | ordinary | 7.0 | 198 | 0 | 0 | 18 | 5 | 3,421.6 | 59 | 4 | 0 | 0 | 119,068 |
| 2027-10-11 | holiday_minor | ordinary | 5.0 | 194 | 6 | 1 | 15 | 9 | 3,515.3 | 45 | 2 | 0 | 0 | 153,893 |
| 2027-10-09 | saturday | ordinary | 52.0 | 192 | 6 | 0 | 23 | 6 | 3,460.2 | 0 | 6 | 0 | 0 | 125,733 |
| 2027-10-10 | sunday | ordinary | 52.0 | 206 | 0 | 0 | 24 | 13 | 3,465.2 | 0 | 3 | 0 | 0 | 139,138 |
| 2027-03-02 | eitc_wave | ordinary | 6.0 | 198 | 6 | 2 | 20 | 8 | 3,512.6 | 56 | 2 | 117 | 52 | 177,349 |
| 2027-09-01 | ssi_first | ordinary | 11.0 | 336 | 12 | 3 | 25 | 9 | 3,457.8 | 46 | 2 | 0 | 0 | 240,997 |
| 2027-11-03 | ss_third | ordinary | 9.0 | 217 | 2 | 1 | 25 | 9 | 3,485.8 | 55 | 2 | 0 | 0 | 199,959 |
| 2027-10-13 | ss_wednesday | ordinary | 12.0 | 171 | 4 | 2 | 19 | 7 | 3,501.5 | 45 | 2 | 0 | 0 | 200,320 |
| 2027-10-20 | ss_wednesday | ordinary | 12.0 | 209 | 8 | 3 | 26 | 10 | 3,492.8 | 48 | 1 | 0 | 0 | 205,280 |
| 2027-10-27 | ss_wednesday | ordinary | 12.0 | 212 | 6 | 0 | 20 | 14 | 3,501.4 | 47 | 4 | 0 | 0 | 199,472 |
| 2027-10-08 | friday | ordinary | 20.0 | 176 | 7 | 2 | 18 | 5 | 3,489.0 | 44 | 4 | 0 | 0 | 248,039 |
| 2027-10-15 | friday | ordinary | 20.0 | 196 | 3 | 2 | 33 | 7 | 3,416.2 | 59 | 2 | 0 | 0 | 272,247 |
| 2027-03-16 | tax_season_weekday | ordinary | 34.0 | 165 | 6 | 1 | 28 | 5 | 3,498.6 | 43 | 6 | 111 | 47 | 182,245 |
| 2027-10-05 | weekday_early | ordinary | 31.8 | 213 | 6 | 1 | 26 | 9 | 3,443.2 | 43 | 4 | 0 | 0 | 183,444 |
| 2027-10-14 | weekday_mid | ordinary | 32.8 | 207 | 7 | 3 | 25 | 3 | 3,516.7 | 53 | 2 | 0 | 0 | 189,260 |
| 2027-10-26 | weekday_late | ordinary | 38.8 | 170 | 9 | 2 | 20 | 9 | 3,544.0 | 47 | 0 | 0 | 0 | 172,373 |
| 2027-01-19 | storm | storm | 1.4 | 138 | 10 | 5 | 22 | 8 | 3,505.5 | 118 | 2 | 0 | 0 | 137,392 |
| 2027-07-22 | heat | heat | 8.3 | 149 | 5 | 4 | 18 | 9 | 3,407.4 | 53 | 3 | 0 | 0 | 144,704 |

## Supporting figures (weighted year, per day)

- overdraft fee dollars: 5,522
- payday rollovers: 2.8
- payday repayments: 10.1
- title loans new: 1.3
- utility shutoff notices: 23.6
- utility reconnections: 8.4
- medical payment plans: 113.4
- caregiving hours visits: 1,725
- caregiving zero dollar records: 5,146
- aide visits: 496.2
- aide misses with linked record: 18.7
- scam attempts: 376.2
- scam loss dollars: 1,843
- benefits cliff tagged: 7.7
- pawn: 24.8
- check cashing: 45.3
- money orders: 28.7
- absent car disabled by lender: 1.6
- absent direct express failure: 1.6
- absent called in on day off: 50.3
- absent snap interview call: 7.1
- absent h2a households: 67.8
- largest single scam loss on any typed day: $1,500

## Limits

- Each day is simulated from the same opening balances; nothing carries between days (option A). Chains such as notice to shutoff, and the concentration of overdraft fees, need the month run (option B).
- Most classes are represented by October days. Heating-season (Nov-Mar) and cooling-season (Jun-Sep) effects are only in the days that fall in those months.
- Storm (1.36) and heat (8.27) weekdays a year are 2015-2025 averages for Halvern's counties (`sources/derived/weather_days.csv`); afternoon thunderstorms are not modeled.
- Wages are boosted on purpose: every worker is paid 1.23 times the national pay for their occupation (about 14% above real 2027 pay) to make up for Halvern's smaller households. Household money is closer to right this way; pay for a single job is not. Kept for v2, dropped in v3 (see WAGE_SCALE in `sim/halvern_sim/config.py`).
