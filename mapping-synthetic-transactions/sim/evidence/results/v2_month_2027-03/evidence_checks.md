# Evidence checks: the March 2027 month

Simulator: v2 phase 4 (`sim/`, commit 71accfe). 31 days carried one into the next (2027-03-01 to 2027-03-31), full city, default seed: balances, the retry queue, shutoff notices, overdrafts, payday and title loans, SNAP balances and the weeks' hours all carry (`sim/medianville_sim/carry.py`). Chains across days are read from each day's `links.csv`. Targets are in `sim/evidence/month_targets.csv`; the typed-day targets (`sim/evidence_targets.csv`) are repeated below as monthly averages.

## Targets for the month

| Target | Item | Month | Target | Verdict | Status |
|---|---|---|---|---|---|
| M01 | Overdraft fees (T01) | 168.3 | 120 to 180 fees per day | in range | firm |
| M02 | Overdraft concentration | 1.1% | 9.0% (about 9% over a year) | more concentrated | firm |
| M03 | Overdraft to fee to late rent | 30 | present (> 0) | present | firm |
| M04 | Utility disconnections (T05) | 12.4 | 11 to 12 disconnections per day (within 25%) | in range | firm |
| M05 | Utility disconnect notices (T16) | 41.5 | 40 to 55 notices per day | in range | firm |
| M06 | Notices that end in a shutoff | 29.3% | 18.0% to 32.0% | in range | provisional |
| M07 | Shutoffs reconnected by month's end | 89.2% | 70.0% to 90.0% | in range | firm |
| M08 | Payday loans and renewals (T02) | 17.8 | 10 to 25 loans per day | in range | firm |
| M09 | Payday loans due that are renewed | 75.8% | 70.0% to 90.0% | in range | provisional |
| M10 | Title loan payments and rollovers (T03) | 7.2 | 5 to 10 payments per day | in range | firm |
| M11 | Adults with a bill unpaid at month's end | 14.7% | 11.0% to 19.0% | in range | firm |
| M12 | SNAP left two weeks after the load | 25.1% | report only | reported | provisional |
| M13 | SNAP left four weeks after the load | 8.0% | report only | reported | provisional |
| M14 | Checking on payday against ten days later | 1.38 | report only | reported | provisional |
| M15 | Week-to-week pay change (variable schedules) | 18.7% | report only | reported | provisional |

## The chains

**Notice to shutoff.** 1614 notice timers ran in the month (326 inherited from notices sent before March 1). Of the notices sent on days 1-20, 29.3% ended in a disconnection. Of the 279 households disconnected on days 1-24, 89.2% were reconnected by March 31. Steps: notice 1288, paid_before_shutoff 734, asked_for_help 647, disconnected 383, reconnected 305, reconnection_unpaid 292, payment_plan 229, reconnection_paid 217, assistance_pledged 217. Days without service before reconnection: 1: 200, 2: 2, 3: 6, 4: 5, 5: 3, 6: 4, 7: 9, 8+: 20.

**Overdraft to fee to late rent.** 1628 overdraft chains; 1003 ran across more than one day, 1004 drew more fees after the first and 651 drew the extended fee after a week below zero (3.2 fees a chain on average). 84 chains reached a missed rent payment within two weeks of a fee, and 30 of those then show the late or part payment of that rent.

**Overdraft concentration.** 1087 of 50869 checking accounts (2.1%) paid at least one overdraft fee in the month; the 9% of accounts that paid the most paid 100.0% of the 5217 fees, and 1.1% of accounts paid 79% of them (CFPB: 9% over a year). Fees per paying account: 1: 215, 2: 130, 3: 114, 4: 105, 5: 119, 6: 92, 7: 100, 8: 64, 9: 53, 10+: 95. Only accounts opted in to overdraft coverage can overdraw (about 6.6% of accounts, `finance.OD_OPT_IN`), so no month or year here can spread fees as widely as the CFPB found; that is set by the one-day population, which phase 4 does not change.

**Payday rollovers.** 633 payday loan chains (storefront and online); of 1045 loans coming due, 75.8% were renewed for the fee, 157 repaid and 96 bounced. Steps: renewed 792, borrowed 251, repaid 157, bounced 96, repaid_after_bounce 30. At month's end 467 loans were open and 13 with collectors; the longest sequence had reached loan 31.

**Title loans.** Steps: installment_paid 86, missed_payment 75, rolled_over 55, borrowed 54, repossessed 10, paid_off 6. 10 cars were repossessed and stayed gone for the rest of the month.

**Unpaid bills.** 49034 bills entered the retry queue (31.8% of households had at least one); steps: missed 19303, paid_late 18401, failed_again 16848, returned 16334, declined 8905, partial 7886, no_time 237. Households with a bill still unpaid on March 31: 14.7% of adults, counting the bills on their own account (SHED 2025: 15.2% of adults cannot pay all of this month's bills in full), and 19.4% of households. Households by group: above 14.1% entered, 6.2% open at the end, alice 48.0% entered, 26.0% open at the end, poverty 84.5% entered, 76.3% open at the end.

**SNAP balances** (share of the month's benefit left, by days since it loaded): day 0 96%, day 1 74%, day 3 56%, day 7 41%, day 10 33%, day 14 25%, day 21 14%, day 28 8%.

**Checking and the pay calendar** (households paid by direct deposit; checking against the household's month mean, by days since payday): 0: 1.20, 1: 1.13, 2: 1.09, 3: 1.04, 4: 1.01, 5: 0.99, 6: 0.94, 7: 0.96, 8: 0.94, 9: 0.92, 10: 0.89, 11: 0.88, 12: 0.87, 13: 0.85, 14: 0.88. Median checking at the start, middle and end of the month: poverty $31, $5, $3; alice $740, $680, $839; above $7,579, $8,249, $9,295.

**Weekly pay** (mean change from one weekly paycheck to the next): full time fixed 1.7% (6239 workers), part time 10.2% (1181 workers), variable 18.7% (3287 workers).

## Typed-day targets over the month

Each target in `sim/evidence_targets.csv`, as a plain average over the 31 days (March, not a weighted year).

| Target | Item | March average | Typed-day target | Verdict (as for the year) |
|---|---|---|---|---|
| T01 | Overdraft fees | 168.3 | 120 to 180 fees per day | in range |
| T02 | New payday loans | 3.8 | 10 to 25 loans per day | LOW; new sequences only in a carried run (with renewals, M08: 17.8 a day) |
| T03 | Auto title loan payments | 7.2 | 5 to 10 payments per day | in range |
| T04 | Title-loan repossessions | 0.3 | present (> 0) | present |
| T05 | Utility disconnections | 12.4 | 11 to 12 disconnections per day | in range |
| T16 | Utility disconnect notices | 41.5 | 40 to 55 notices per day | in range |
| T06 | Medical care delayed by debt | 2.6 | present (> 0) | present |
| T07 | Unpaid caregiving at home | 3,484 | 2750 to 4130 hours per day | in range |
| T15 | Unpaid caregiving on visits | 1,731 | 1220 to 6250 hours per day | in range |
| T08 | Aide visits not completed | 10.1% | report only | reported |
| T09 | Scam losses | 0.7% | report only | reported |
| T10 | Benefits-cliff job | 0.3 | present (> 0) | present |
| T11 | Rural cash share | - | 0.187 to 0.187 share of payments | not measured |
| T12 | Paid tax preparation | 54.9% | 0.49 to 0.59 share of returns filed | in range |
| T13 | Pawn, check cashing, money orders | 96.8 | report only | reported |
| T14 | Truly absent jobs | 113.6 | present (> 0) | present |

## Limits

- One month, started cold on March 1 except for what is inherited: shutoff notices from the ten days before, the payday loans and title loans already out, and the tax season so far. The retry queue and the overdraft chains start empty, so the first days run a little light.
- People, households, jobs and bills do not change during the month: a death, birth, move or new job drawn on one day does not carry to the next (that is option C, a year with the roster changing).
- Rural cash share (T11) needs each day's payment summary, which this report does not reread; see the days' `summary.md`.
- Overdraft fees can only fall on accounts opted in to coverage, so they stay more concentrated than the CFPB's 9% of accounts.
- Week-to-week hours, SNAP spending pace and the move of surplus checking to savings are labeled estimates (see `carry.py`).
