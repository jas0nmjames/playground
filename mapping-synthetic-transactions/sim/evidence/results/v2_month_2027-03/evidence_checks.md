# Evidence checks: the March 2027 month

Simulator: v2 phase 5 (`sim/`, commit dd0e6b6). 31 days carried one into the next (2027-03-01 to 2027-03-31), full city, default seed: balances, the retry queue, shutoff notices, overdrafts, payday and title loans, SNAP balances and the weeks' hours all carry (`sim/medianville_sim/carry.py`). Chains across days are read from each day's `links.csv`. Targets are in `sim/evidence/month_targets.csv`; the typed-day targets (`sim/evidence_targets.csv`) are repeated below as monthly averages.

## Targets for the month

| Target | Item | Month | Target | Verdict | Status |
|---|---|---|---|---|---|
| M01 | Overdraft fees (T01) | 167.5 | 120 to 180 fees per day | in range | firm |
| M02 | Overdraft concentration | 1.1% | 9.0% (about 9% over a year) | more concentrated | firm |
| M03 | Overdraft to fee to late rent | 20 | present (> 0) | present | firm |
| M04 | Utility disconnections (T05) | 12.8 | 11 to 12 disconnections per day (within 25%) | in range | firm |
| M05 | Utility disconnect notices (T16) | 43.1 | 40 to 55 notices per day | in range | firm |
| M06 | Notices that end in a shutoff | 30.1% | 18.0% to 32.0% | in range | provisional |
| M07 | Shutoffs reconnected by month's end | 89.7% | 70.0% to 90.0% | in range | firm |
| M08 | Payday loans and renewals (T02) | 16.3 | 10 to 25 loans per day | in range | firm |
| M09 | Payday loans due that are renewed | 73.0% | 70.0% to 90.0% | in range | provisional |
| M10 | Title loan payments and rollovers (T03) | 7.1 | 5 to 10 payments per day | in range | firm |
| M11 | Adults with a bill unpaid at month's end | 15.0% | 11.0% to 19.0% | in range | firm |
| M12 | SNAP left two weeks after the load | 25.1% | report only | reported | provisional |
| M13 | SNAP left four weeks after the load | 8.5% | report only | reported | provisional |
| M14 | Checking on payday against ten days later | 1.38 | report only | reported | provisional |
| M15 | Week-to-week pay change (variable schedules) | 18.8% | report only | reported | provisional |

## The chains

**Notice to shutoff.** 1655 notice timers ran in the month (319 inherited from notices sent before March 1). Of the notices sent on days 1-20, 30.1% ended in a disconnection. Of the 271 households disconnected on days 1-24, 89.7% were reconnected by March 31. Steps: notice 1336, paid_before_shutoff 705, asked_for_help 651, disconnected 398, reconnected 317, reconnection_unpaid 282, payment_plan 255, reconnection_paid 234, assistance_pledged 222. Days without service before reconnection: 1: 189, 2: 1, 3: 8, 4: 4, 5: 2, 6: 3, 7: 14, 8+: 22.

**Overdraft to fee to late rent.** 1643 overdraft chains; 954 ran across more than one day, 981 drew more fees after the first and 629 drew the extended fee after a week below zero (3.2 fees a chain on average). 75 chains reached a missed rent payment within two weeks of a fee, and 20 of those then show the late or part payment of that rent.

**Overdraft concentration.** 1085 of 50869 checking accounts (2.1%) paid at least one overdraft fee in the month; the 9% of accounts that paid the most paid 100.0% of the 5191 fees, and 1.1% of accounts paid 79% of them (CFPB: 9% over a year). Fees per paying account: 1: 185, 2: 152, 3: 127, 4: 107, 5: 112, 6: 108, 7: 75, 8: 67, 9: 52, 10+: 100. Only accounts opted in to overdraft coverage can overdraw (about 6.6% of accounts, `finance.OD_OPT_IN`), so no month or year here can spread fees as widely as the CFPB found; that is set by the one-day population, which phase 4 does not change.

**Payday rollovers.** 642 payday loan chains (storefront and online); of 942 loans coming due, 73.0% were renewed for the fee, 155 repaid and 99 bounced. Steps: renewed 688, borrowed 253, repaid 155, bounced 99, repaid_after_bounce 33. At month's end 473 loans were open and 13 with collectors; the longest sequence had reached loan 32.

**Title loans.** Steps: installment_paid 83, missed_payment 74, rolled_over 57, borrowed 56, repossessed 14, paid_off 6. 14 cars were repossessed and stayed gone for the rest of the month.

**Unpaid bills.** 49168 bills entered the retry queue (31.9% of households had at least one); steps: missed 19249, paid_late 18427, failed_again 16851, returned 16473, declined 8846, partial 8254, no_time 206. Households with a bill still unpaid on March 31: 15.0% of adults, counting the bills on their own account (SHED 2025: 15.2% of adults cannot pay all of this month's bills in full), and 19.6% of households. Households by group: above 14.2% entered, 6.4% open at the end, alice 48.1% entered, 26.2% open at the end, poverty 84.9% entered, 76.4% open at the end.

**SNAP balances** (share of the month's benefit left, by days since it loaded): day 0 96%, day 1 74%, day 3 55%, day 7 41%, day 10 33%, day 14 25%, day 21 15%, day 28 8%.

**Checking and the pay calendar** (households paid by direct deposit; checking against the household's month mean, by days since payday): 0: 1.20, 1: 1.13, 2: 1.09, 3: 1.04, 4: 1.01, 5: 0.99, 6: 0.94, 7: 0.96, 8: 0.94, 9: 0.92, 10: 0.89, 11: 0.87, 12: 0.87, 13: 0.85, 14: 0.88. Median checking at the start, middle and end of the month: poverty $30, $5, $3; alice $738, $684, $817; above $7,521, $8,139, $9,215.

**Weekly pay** (mean change from one weekly paycheck to the next): full time fixed 1.7% (6239 workers), part time 10.1% (1181 workers), variable 18.8% (3287 workers).

## Typed-day targets over the month

Each target in `sim/evidence_targets.csv`, as a plain average over the 31 days (March, not a weighted year).

| Target | Item | March average | Typed-day target | Verdict (as for the year) |
|---|---|---|---|---|
| T01 | Overdraft fees | 167.5 | 120 to 180 fees per day | in range |
| T02 | New payday loans | 3.9 | 10 to 25 loans per day | LOW; new sequences only in a carried run (with renewals, M08: 16.3 a day) |
| T03 | Auto title loan payments | 7.1 | 5 to 10 payments per day | in range |
| T04 | Title-loan repossessions | 0.5 | present (> 0) | present |
| T05 | Utility disconnections | 12.8 | 11 to 12 disconnections per day | in range |
| T16 | Utility disconnect notices | 43.1 | 40 to 55 notices per day | in range |
| T06 | Medical care delayed by debt | 2.1 | present (> 0) | present |
| T07 | Unpaid caregiving at home | 3,493 | 2750 to 4130 hours per day | in range |
| T15 | Unpaid caregiving on visits | 1,723 | 1220 to 6250 hours per day | in range |
| T08 | Aide visits not completed | 9.4% | report only | reported |
| T09 | Scam losses | 0.8% | report only | reported |
| T10 | Benefits-cliff job | 0.5 | present (> 0) | present |
| T11 | Rural cash share | - | 0.187 to 0.187 share of payments | not measured |
| T12 | Paid tax preparation | 55.5% | 0.49 to 0.59 share of returns filed | in range |
| T13 | Pawn, check cashing, money orders | 97.4 | report only | reported |
| T14 | Truly absent jobs | 110.9 | present (> 0) | present |

## Limits

- One month, started cold on March 1 except for what is inherited: shutoff notices from the ten days before, the payday loans and title loans already out, and the tax season so far. The retry queue and the overdraft chains start empty, so the first days run a little light.
- People, households, jobs and bills do not change during the month: a death, birth, move or new job drawn on one day does not carry to the next (that is option C, a year with the roster changing).
- Rural cash share (T11) needs each day's payment summary, which this report does not reread; see the days' `summary.md`.
- Overdraft fees can only fall on accounts opted in to coverage, so they stay more concentrated than the CFPB's 9% of accounts.
- Week-to-week hours, SNAP spending pace and the move of surplus checking to savings are labeled estimates (see `carry.py`).
