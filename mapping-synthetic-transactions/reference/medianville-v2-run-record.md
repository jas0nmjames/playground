# Medianville run record: v2, the published days

Packed 2026-11-21 in Claude Code on Jason's Mac, on branch `medianville-v2-phase5`, as the [data update plan](medianville-data-update-plan.md)'s phase 5. Nineteen one-day runs of the same city: the baseline day, Wednesday, March 3, 2027, with 300 hand-written records, and the 18 typed days that stand for 2027 (`sim/evidence/typed_days.py`). Seed 20270303, full city (41,400 households plus group quarters, 99,743 residents), records tagged with the systems lens's mapped blocks. Each day is its own run: nothing carries from one to the next (the carried month is the [month run record](medianville-2027-03-month-run-record.md)).

## Where they are

`data/runs/v2/medianville_<date>.zip`, listed with v1 in `data/runs/manifest.json`, which the viewers read (`runs.js`). The latest viewer and the explorer open the baseline day; `?run=v2-<date>` or the day menu opens another. 283 MB together, 11.9 to 18.6 MB each.

| Date | Kind of day | Weather | Weight (days of 2027) | Records | Zip | SHA-256 |
|---|---|---|---|---|---|---|
| Wed, Mar 3 | Baseline day | ordinary | — | 202,402 | 16.3 MB | `d80dfd6b9151…` |
| Mon, Jul 5 | Major holiday | ordinary | 7.00 | 119,115 | 11.9 MB | `a2b918a8187f…` |
| Mon, Oct 11 | Minor holiday | ordinary | 5.00 | 155,296 | 13.3 MB | `b16ea98133d9…` |
| Sat, Oct 9 | Saturday | ordinary | 52.00 | 126,424 | 12.1 MB | `575782906f65…` |
| Sun, Oct 10 | Sunday | ordinary | 52.00 | 139,027 | 12.8 MB | `ee3f3adc2b7f…` |
| Tue, Mar 2 | EITC refund wave | ordinary | 6.00 | 177,973 | 14.6 MB | `2a5243aaddc8…` |
| Wed, Sep 1 | SSI day | ordinary | 11.00 | 240,834 | 18.0 MB | `fde2bb9317d0…` |
| Wed, Nov 3 | Social Security on the 3rd | ordinary | 9.00 | 199,890 | 16.0 MB | `eac89ba19107…` |
| Wed, Oct 13 | Social Security Wednesday | ordinary | 12.00 | 200,446 | 15.7 MB | `1eb177aaf3d9…` |
| Wed, Oct 20 | Social Security Wednesday | ordinary | 12.00 | 206,185 | 16.0 MB | `3b35d917a76e…` |
| Wed, Oct 27 | Social Security Wednesday | ordinary | 12.00 | 199,261 | 15.6 MB | `59d8f6f62c01…` |
| Fri, Oct 8 | Friday payday | ordinary | 20.00 | 248,940 | 17.7 MB | `3f3619abba51…` |
| Fri, Oct 15 | Friday payday | ordinary | 20.00 | 271,920 | 18.6 MB | `da0227686e9f…` |
| Tue, Mar 16 | Tax-season weekday | ordinary | 34.00 | 182,037 | 14.7 MB | `52cf0a92581f…` |
| Tue, Oct 5 | Early-month weekday | ordinary | 31.79 | 184,121 | 15.0 MB | `8803fea38baf…` |
| Thu, Oct 14 | Mid-month weekday | ordinary | 32.79 | 188,685 | 15.1 MB | `271455c942f5…` |
| Tue, Oct 26 | Late-month weekday | ordinary | 38.79 | 171,600 | 14.1 MB | `1725063c831e…` |
| Tue, Jan 19 | Storm | storm | 1.36 | 137,751 | 12.5 MB | `02a6f623b383…` |
| Thu, Jul 22 | Heat | heat | 8.27 | 144,756 | 13.2 MB | `b3aff16381f0…` |

The weights add up to 365. The full SHA-256 of each zip is in the manifest.

## What each zip holds

Under `medianville_<date>/`: the day's tables (`records.csv`, `households.csv`, `persons.csv`, `organizations.csv`, `household_ledger.csv`, `public_services_context.csv`, `assumptions.csv`, `summary.md`), the systems lens's `blocks.json`, the simulator (`simulate.py`, `medianville_sim/`), a `README.md` naming the day's class, weather and weight, and `SHA256SUMS`. The baseline day also carries `detailed_overrides.csv` and `detailed_sample.csv`, the hand-written text and the 300 finished records.

| | |
|---|---|
| Simulator | `sim/` at commit `dd0e6b6`, frozen for v2; hand-written text added at `55aa238` |
| Built with | Python 3.11.5 (python.org installer), numpy 2.4.6, zlib 1.2.12, macOS on arm64; about 20 s a day |
| Checks | Each zip's files pass its `SHA256SUMS` and each zip matches the manifest's SHA-256. Packing all 19 days twice gave the same zips and the same manifest. The baseline day holds exactly 300 hand-written records, and the rest of its columns match the run without them. Every day's record count matches the typed-day evidence run (`sim/evidence/results/v2_phase5_typed_days_2027`). |

## Rebuilding them

From a checkout at the commit that added this file, with the venv from the month run record:

```bash
cd mapping-synthetic-transactions/sim
"$HOME/medianville-venv/bin/python" simulate.py --out "$HOME/medianville-days/2027-03-03"
"$HOME/medianville-venv/bin/python" -c "import sys; sys.path.insert(0, 'evidence'); import typed_days; [print(r['date'], r['weather']) for r in typed_days.day_set()]" > /tmp/days.txt
while read d w; do "$HOME/medianville-venv/bin/python" simulate.py --date $d --weather $w --out "$HOME/medianville-days/$d$([ $w = ordinary ] || echo _$w)"; done < /tmp/days.txt
"$HOME/medianville-venv/bin/python" ../tools/pack_runs.py "$HOME/medianville-days" --commit "dd0e6b6 (hand-written text: 55aa238)"
```

`pack_runs.py` writes the zips and the manifest in place. A different zlib gives different zip bytes but the same `SHA256SUMS`; a different Python or numpy can change the records.

## Known limits

v2 keeps v1's people (decision 2.10), so the population's problems that the [close reading](medianville-v2-close-reading.md) found stay until v3 redraws it:
- SSI against income and spouse rules;
- coverage against eligibility;
- the $380 rent for every renter without income;
- refundable credits on high incomes;
- jobs paired with unrelated employers;
- some 60-80 mile trips.

Overdraft fees fall on fewer accounts than in life (plan section 9, item 6). `time_minutes` counts the wait but not the travel. Wages carry v1's boost: compare households, not occupations.
