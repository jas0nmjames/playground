# Evidence checks: the typed-day set

Simulator unchanged (v1 code in `sim/`). 17 simulated days stand for 2027; each day's weight is the number of 2027 days in its class (`sim/evidence/typed_days.py`). Annual figures are weighted averages per day, or pooled shares. Targets are from `sim/evidence_targets.csv`; ranges and tolerances there are drafts until the evidence report's ids and grades are filled in.

## Targets against the weighted year

| Target | Item | Year (weighted) | Mar 3 (v1 day) | Target | Verdict | Status |
|---|---|---|---|---|---|---|
| T01 | Overdraft fees | 265.4 | 274.0 | 120 to 180 fees per day | HIGH | firm |
| T02 | New payday loans | 6.7 | 8.0 | 25 to 80 loans per day | LOW | provisional |
| T03 | Auto title loan payments | 0.0 | 0.0 | 15 to 25 payments per day | LOW | firm |
| T04 | Title-loan repossessions | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T05 | Utility disconnections | 8.1 | 8.0 | 11 to 12 disconnections per day | LOW | firm |
| T06 | Medical care delayed by debt | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T07 | Unpaid caregiving at home | 8,572 | 8,548 | about 67500 hours per day (provisional) | reported | provisional |
| T08 | Aide visits not completed | 7.7% | 7.5% | report only | reported | firm |
| T09 | Scam losses | 0.9% | 0.6% | report only | reported | provisional |
| T10 | Benefits-cliff job | 0.0 | 0.0 | present (> 0) | ABSENT | firm |
| T11 | Rural cash share | 17.8% | 16.8% | 21% (within 2 points) | LOW | firm |
| T12 | Paid tax preparation | 69.0% | 73.0% | 0.45 to 0.55 share of prepared returns | HIGH | provisional |
| T13 | Pawn, check cashing, money orders | 93.5 | 114.0 | report only | reported | firm |
| T14 | Truly absent jobs | 0.0 | 0.0 | present (> 0) | ABSENT | firm |

## Each day

| Date | Class | Weather | Weight | overdraft fees | payday loans new | title loans new | utility shutoff notices | utility disconnections | caregiving hours home | aide visits missed | scam losses | paid tax prep | free tax prep | records |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2027-03-03 | v1 baseline (not weighted) | ordinary | 0.0 | 274 | 8 | 4 | 26 | 8 | 8,548.1 | 51 | 2 | 108 | 40 | 201,753 |
| 2027-07-05 | holiday | ordinary | 12.0 | 315 | 7 | 2 | 25 | 8 | 8,656.3 | 57 | 4 | 0 | 0 | 159,917 |
| 2027-10-09 | saturday | ordinary | 52.0 | 244 | 14 | 2 | 20 | 9 | 8,648.6 | 0 | 3 | 0 | 0 | 129,092 |
| 2027-10-10 | sunday | ordinary | 52.0 | 275 | 0 | 0 | 31 | 8 | 8,658.6 | 0 | 7 | 0 | 0 | 137,090 |
| 2027-03-02 | eitc_wave | ordinary | 6.0 | 269 | 11 | 3 | 21 | 9 | 8,570.0 | 60 | 4 | 109 | 62 | 185,703 |
| 2027-09-01 | ssi_first | ordinary | 8.0 | 426 | 7 | 2 | 26 | 5 | 8,433.1 | 49 | 4 | 0 | 0 | 239,359 |
| 2027-11-03 | ss_third | ordinary | 9.0 | 278 | 5 | 1 | 22 | 5 | 8,719.6 | 59 | 2 | 0 | 0 | 198,346 |
| 2027-10-13 | ss_wednesday | ordinary | 12.0 | 256 | 10 | 2 | 23 | 9 | 8,518.5 | 46 | 5 | 0 | 0 | 198,762 |
| 2027-10-20 | ss_wednesday | ordinary | 12.0 | 269 | 7 | 3 | 19 | 7 | 8,503.1 | 52 | 0 | 0 | 0 | 204,730 |
| 2027-10-27 | ss_wednesday | ordinary | 12.0 | 226 | 9 | 6 | 27 | 14 | 8,683.3 | 52 | 1 | 0 | 0 | 197,806 |
| 2027-10-08 | friday | ordinary | 21.0 | 245 | 13 | 0 | 21 | 7 | 8,482.8 | 47 | 6 | 0 | 0 | 234,774 |
| 2027-10-15 | friday | ordinary | 21.0 | 286 | 5 | 0 | 25 | 9 | 8,509.7 | 50 | 3 | 0 | 0 | 258,019 |
| 2027-03-16 | tax_season_weekday | ordinary | 34.0 | 253 | 3 | 3 | 32 | 7 | 8,444.2 | 41 | 2 | 112 | 48 | 189,109 |
| 2027-10-05 | weekday_early | ordinary | 31.0 | 275 | 2 | 6 | 23 | 8 | 8,656.3 | 51 | 2 | 0 | 0 | 191,082 |
| 2027-10-14 | weekday_mid | ordinary | 32.0 | 281 | 8 | 6 | 24 | 6 | 8,595.3 | 50 | 2 | 0 | 0 | 188,006 |
| 2027-10-26 | weekday_late | ordinary | 39.0 | 249 | 7 | 1 | 27 | 9 | 8,426.0 | 62 | 2 | 0 | 0 | 179,578 |
| 2027-01-19 | storm | storm | 4.0 | 198 | 5 | 1 | 19 | 6 | 8,647.6 | 117 | 2 | 0 | 0 | 125,514 |
| 2027-07-22 | heat | heat | 8.0 | 224 | 9 | 2 | 33 | 10 | 8,569.5 | 50 | 3 | 0 | 0 | 143,850 |

## Supporting figures (weighted year, per day)

- overdraft fee dollars: 7,408
- payday rollovers: 3.3
- payday repayments: 8.3
- title loans new: 2.3
- utility shutoff notices: 25.3
- utility reconnections: 8.6
- medical payment plans: 136.5
- caregiving hours visits: 1,720
- caregiving zero dollar records: 5,347
- aide visits: 488.0
- aide misses with linked record: 3.7
- scam attempts: 366.8
- scam loss dollars: 2,282
- benefits cliff tagged: 6.4
- pawn: 23.1
- check cashing: 42.7
- money orders: 27.7
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
