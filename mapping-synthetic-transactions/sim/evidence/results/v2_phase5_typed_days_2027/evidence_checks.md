# Evidence checks: the typed-day set

Simulator: v2 phase 5: the close-reading fixes (`sim/`, after commit dd0e6b6). 18 simulated days stand for 2027; each day's weight is the number of 2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence report's ids and grades are filled in.

## Targets against the weighted year

| Target | Item | Year (weighted) | Mar 3 | Target | Verdict | Status |
|---|---|---|---|---|---|---|
| T01 | Overdraft fees | 139.3 | 149.0 | 120 to 180 fees per day | in range | firm |
| T02 | New payday loans | 15.4 | 31.0 | 10 to 25 loans per day | in range | firm |
| T03 | Auto title loan payments | 7.8 | 7.0 | 5 to 10 payments per day | in range | firm |
| T04 | Title-loan repossessions | 1.2 | 1.0 | present (> 0) | present | firm |
| T05 | Utility disconnections | 13.0 | 8.0 | 11 to 12 disconnections per day | in range | firm |
| T16 | Utility disconnect notices | 49.4 | 49.0 | 40 to 55 notices per day | in range | firm |
| T06 | Medical care delayed by debt | 2.4 | 3.0 | present (> 0) | present | firm |
| T07 | Unpaid caregiving at home | 3,469 | 3,532 | 2750 to 4130 hours per day | in range | firm |
| T15 | Unpaid caregiving on visits | 1,725 | 1,804 | 1220 to 6250 hours per day | in range | provisional |
| T08 | Aide visits not completed | 7.9% | 9.3% | report only | reported | firm |
| T09 | Scam losses | 0.9% | 1.4% | report only | reported | provisional |
| T10 | Benefits-cliff job | 0.8 | 1.0 | present (> 0) | present | firm |
| T11 | Rural cash share | 18.8% | 17.3% | 19% (within 2 points) | in range | firm |
| T12 | Paid tax preparation | 53.5% | 53.0% | 0.49 to 0.59 share of returns filed | in range | firm |
| T13 | Pawn, check cashing, money orders | 99.4 | 117.0 | report only | reported | firm |
| T14 | Truly absent jobs | 128.2 | 121.0 | present (> 0) | present | firm |

## Each day

| Date | Class | Weather | Weight | overdraft fees | payday loans new | title loans new | utility shutoff notices | utility disconnections | caregiving hours home | aide visits missed | scam losses | paid tax prep | free tax prep | records |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027-03-03 | Mar 3 baseline (not weighted) | ordinary | 0.0 | 149 | 31 | 3 | 49 | 8 | 3,532.4 | 64 | 5 | 222 | 54 | 202,402 |
| 2027-07-05 | holiday_major | ordinary | 7.0 | 160 | 0 | 0 | 39 | 7 | 3,437.9 | 56 | 3 | 0 | 0 | 119,115 |
| 2027-10-11 | holiday_minor | ordinary | 5.0 | 129 | 23 | 1 | 47 | 13 | 3,484.1 | 40 | 0 | 0 | 0 | 155,296 |
| 2027-10-09 | saturday | ordinary | 52.0 | 154 | 23 | 2 | 48 | 17 | 3,482.8 | 0 | 3 | 0 | 0 | 126,424 |
| 2027-10-10 | sunday | ordinary | 52.0 | 131 | 0 | 0 | 51 | 10 | 3,519.9 | 0 | 3 | 0 | 0 | 139,027 |
| 2027-03-02 | eitc_wave | ordinary | 6.0 | 177 | 23 | 1 | 39 | 7 | 3,493.3 | 43 | 4 | 232 | 46 | 177,973 |
| 2027-09-01 | ssi_first | ordinary | 11.0 | 244 | 17 | 2 | 46 | 9 | 3,460.9 | 52 | 3 | 0 | 0 | 240,834 |
| 2027-11-03 | ss_third | ordinary | 9.0 | 169 | 25 | 0 | 47 | 10 | 3,492.0 | 52 | 3 | 0 | 0 | 199,890 |
| 2027-10-13 | ss_wednesday | ordinary | 12.0 | 127 | 19 | 4 | 52 | 12 | 3,497.8 | 56 | 3 | 0 | 0 | 200,446 |
| 2027-10-20 | ss_wednesday | ordinary | 12.0 | 142 | 24 | 1 | 36 | 14 | 3,502.5 | 48 | 3 | 0 | 0 | 206,185 |
| 2027-10-27 | ss_wednesday | ordinary | 12.0 | 143 | 17 | 2 | 51 | 20 | 3,436.7 | 51 | 4 | 0 | 0 | 199,261 |
| 2027-10-08 | friday | ordinary | 20.0 | 143 | 18 | 1 | 48 | 10 | 3,483.3 | 58 | 1 | 0 | 0 | 248,940 |
| 2027-10-15 | friday | ordinary | 20.0 | 154 | 20 | 2 | 44 | 19 | 3,436.1 | 47 | 5 | 0 | 0 | 271,920 |
| 2027-03-16 | tax_season_weekday | ordinary | 34.0 | 117 | 16 | 2 | 53 | 9 | 3,415.5 | 59 | 4 | 224 | 49 | 182,037 |
| 2027-10-05 | weekday_early | ordinary | 31.8 | 136 | 11 | 2 | 55 | 15 | 3,485.5 | 70 | 5 | 0 | 0 | 184,121 |
| 2027-10-14 | weekday_mid | ordinary | 32.8 | 131 | 17 | 2 | 63 | 11 | 3,400.6 | 47 | 3 | 0 | 0 | 188,685 |
| 2027-10-26 | weekday_late | ordinary | 38.8 | 112 | 17 | 3 | 43 | 16 | 3,475.6 | 50 | 3 | 0 | 0 | 171,600 |
| 2027-01-19 | storm | storm | 1.4 | 100 | 19 | 3 | 40 | 13 | 3,463.4 | 120 | 3 | 0 | 0 | 137,751 |
| 2027-07-22 | heat | heat | 8.3 | 124 | 18 | 3 | 42 | 10 | 3,450.8 | 44 | 0 | 0 | 0 | 144,756 |

## Supporting figures (weighted year, per day)

- overdraft fee dollars: 3,897
- payday rollovers: 8.6
- payday repayments: 32.4
- title loans new: 1.7
- utility shutoff notices: 49.4
- utility reconnections: 13.9
- medical payment plans: 113.3
- caregiving hours visits: 1,725
- caregiving zero dollar records: 5,113
- aide visits: 489.9
- aide misses with linked record: 21.2
- scam attempts: 365.6
- scam loss dollars: 40,063
- benefits cliff tagged: 7.0
- pawn: 25.1
- check cashing: 44.7
- money orders: 29.5
- absent car disabled by lender: 1.5
- absent direct express failure: 2.1
- absent called in on day off: 51.3
- absent snap interview call: 5.5
- absent h2a households: 67.8
- largest single scam loss on any typed day: $273,665

## Limits

- Each day is simulated from the same opening balances; nothing carries between days (option A). Chains such as notice to shutoff, and the concentration of overdraft fees, need the month run (option B).
- Most classes are represented by October days. Heating-season (Nov-Mar) and cooling-season (Jun-Sep) effects are only in the days that fall in those months.
- Storm (1.36) and heat (8.27) weekdays a year are 2015-2025 averages for Medianville's counties (`sources/derived/weather_days.csv`); afternoon thunderstorms are not modeled.
- Wages are boosted on purpose: every worker is paid 1.23 times the national pay for their occupation (about 14% above real 2027 pay) to make up for Medianville's smaller households. Household money is closer to right this way; pay for a single job is not. Kept for v2, dropped in v3 (see WAGE_SCALE in `sim/medianville_sim/config.py`).
