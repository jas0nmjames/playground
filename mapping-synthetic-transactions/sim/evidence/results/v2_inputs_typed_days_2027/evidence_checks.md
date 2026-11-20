# Evidence checks: the typed-day set

Simulator: v2 in progress (`sim/`): caregiving at home from ATUS; calendar batch; inputs batch (FDIC banking, SCF balances, AHS owner costs, MEPS health costs, NDCP child care, NTD transit, NCS sick leave, NCHS marriages and divorces). 18 simulated days stand for 2027; each day's weight is the number of 2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence report's ids and grades are filled in.

## Targets against the weighted year

| Target | Item | Year (weighted) | Mar 3 | Target | Verdict | Status |
|---|---|---|---|---|---|---|
| T01 | Overdraft fees | 189.0 | 210.0 | 120 to 180 fees per day | HIGH | firm |
| T02 | New payday loans | 6.9 | 7.0 | 25 to 80 loans per day | LOW | provisional |
| T03 | Auto title loan payments | 0.0 | 0.0 | 15 to 25 payments per day | LOW | firm |
| T04 | Title-loan repossessions | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T05 | Utility disconnections | 8.8 | 11.0 | 11 to 12 disconnections per day | in range | firm |
| T16 | Utility disconnect notices | 21.6 | 25.0 | 40 to 55 notices per day | LOW | firm |
| T06 | Medical care delayed by debt | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T07 | Unpaid caregiving at home | 3,512 | 3,498 | 2750 to 4130 hours per day | in range | firm |
| T15 | Unpaid caregiving on visits | 1,727 | 1,673 | 1220 to 6250 hours per day | in range | provisional |
| T08 | Aide visits not completed | 7.7% | 7.4% | report only | reported | firm |
| T09 | Scam losses | 0.4% | 0.3% | report only | reported | provisional |
| T10 | Benefits-cliff job | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T11 | Rural cash share | 17.5% | 16.9% | 21% (within 2 points) | LOW | firm |
| T12 | Paid tax preparation | 69.2% | 70.7% | 0.45 to 0.55 share of prepared returns | HIGH | provisional |
| T13 | Pawn, check cashing, money orders | 96.1 | 112.0 | report only | reported | firm |
| T14 | Truly absent jobs | 0.0 | 0.0 | present (> 0) | ABSENT | firm |

## Each day

| Date | Class | Weather | Weight | overdraft fees | payday loans new | title loans new | utility shutoff notices | utility disconnections | caregiving hours home | aide visits missed | scam losses | paid tax prep | free tax prep | records |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027-03-03 | Mar 3 baseline (not weighted) | ordinary | 0.0 | 210 | 7 | 0 | 25 | 11 | 3,497.9 | 48 | 1 | 111 | 46 | 201,171 |
| 2027-07-05 | holiday_major | ordinary | 7.0 | 209 | 0 | 0 | 18 | 11 | 3,463.2 | 51 | 2 | 0 | 0 | 118,216 |
| 2027-10-11 | holiday_minor | ordinary | 5.0 | 145 | 7 | 5 | 20 | 12 | 3,427.3 | 55 | 3 | 0 | 0 | 153,804 |
| 2027-10-09 | saturday | ordinary | 52.0 | 184 | 11 | 1 | 21 | 6 | 3,521.9 | 0 | 1 | 0 | 0 | 125,834 |
| 2027-10-10 | sunday | ordinary | 52.0 | 215 | 0 | 0 | 23 | 10 | 3,582.4 | 0 | 1 | 0 | 0 | 137,887 |
| 2027-03-02 | eitc_wave | ordinary | 6.0 | 199 | 6 | 2 | 16 | 8 | 3,491.5 | 62 | 1 | 138 | 55 | 176,813 |
| 2027-09-01 | ssi_first | ordinary | 11.0 | 312 | 13 | 3 | 22 | 11 | 3,495.3 | 64 | 1 | 0 | 0 | 239,657 |
| 2027-11-03 | ss_third | ordinary | 9.0 | 181 | 7 | 5 | 30 | 5 | 3,519.3 | 41 | 5 | 0 | 0 | 199,191 |
| 2027-10-13 | ss_wednesday | ordinary | 12.0 | 164 | 7 | 4 | 22 | 5 | 3,428.2 | 47 | 3 | 0 | 0 | 198,909 |
| 2027-10-20 | ss_wednesday | ordinary | 12.0 | 195 | 4 | 1 | 23 | 10 | 3,375.5 | 65 | 3 | 0 | 0 | 204,709 |
| 2027-10-27 | ss_wednesday | ordinary | 12.0 | 170 | 4 | 5 | 22 | 6 | 3,498.8 | 52 | 3 | 0 | 0 | 198,445 |
| 2027-10-08 | friday | ordinary | 20.0 | 205 | 7 | 1 | 25 | 12 | 3,527.0 | 52 | 1 | 0 | 0 | 247,645 |
| 2027-10-15 | friday | ordinary | 20.0 | 207 | 6 | 2 | 24 | 3 | 3,585.1 | 48 | 1 | 0 | 0 | 270,873 |
| 2027-03-16 | tax_season_weekday | ordinary | 34.0 | 156 | 11 | 1 | 23 | 8 | 3,449.1 | 52 | 3 | 103 | 47 | 181,240 |
| 2027-10-05 | weekday_early | ordinary | 31.8 | 192 | 8 | 1 | 24 | 11 | 3,408.0 | 55 | 2 | 0 | 0 | 183,208 |
| 2027-10-14 | weekday_mid | ordinary | 32.8 | 169 | 11 | 7 | 14 | 10 | 3,549.7 | 54 | 0 | 0 | 0 | 187,866 |
| 2027-10-26 | weekday_late | ordinary | 38.8 | 179 | 3 | 4 | 19 | 11 | 3,588.8 | 49 | 0 | 0 | 0 | 170,510 |
| 2027-01-19 | storm | storm | 1.4 | 119 | 9 | 1 | 21 | 8 | 3,474.0 | 125 | 2 | 0 | 0 | 136,697 |
| 2027-07-22 | heat | heat | 8.3 | 139 | 12 | 4 | 24 | 10 | 3,420.5 | 45 | 1 | 0 | 0 | 144,280 |

## Supporting figures (weighted year, per day)

- overdraft fee dollars: 5,270
- payday rollovers: 3.7
- payday repayments: 8.6
- title loans new: 2.3
- utility shutoff notices: 21.6
- utility reconnections: 9.0
- medical payment plans: 114.7
- caregiving hours visits: 1,727
- caregiving zero dollar records: 5,154
- aide visits: 490.5
- aide misses with linked record: 3.1
- scam attempts: 360.1
- scam loss dollars: 892.7
- benefits cliff tagged: 8.1
- pawn: 24.0
- check cashing: 42.9
- money orders: 29.2
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
