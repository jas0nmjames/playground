# Medianville run record: March 2027, carried day to day (v2, phase 4)

Rebuilt 2026-11-21 in Claude Code on Jason's Mac, on branch `medianville-v2-phase5`, after the [close reading](medianville-v2-close-reading.md)'s fixes; first built 2026-11-20 in the [data update plan](../03-grounding-in-evidence/medianville-data-update-plan.md)'s phase 4 (that build, SHA-256 `7339315…ed58`, is superseded). Thirty-one days, March 1-31, 2027, each starting from the balances and unfinished business of the day before (`sim/medianville_sim/carry.py`; decisions 1.7-1.15 in the [decision log](../decisions.md)). Seed 20270303, full city (41,400 households plus 2,099 group-quarters units, 99,743 residents), ordinary weather, records tagged with the systems lens's mapped blocks. No hand-written text: that belongs to the one-day baseline. Deterministic: the same commit, Python and numpy reproduce every file byte for byte.

## Download

**[Download (about 460 MB), not needed to use the site](https://github.com/jas0nmjames/playground/releases/download/medianville-v2-month-2027-03/medianville_2027-03_month.zip)**, from the GitHub Release [`medianville-v2-month-2027-03`](https://github.com/jas0nmjames/playground/releases/tag/medianville-v2-month-2027-03). The viewers, the explorer and the systems lens never load it.

| | |
|---|---|
| File | `medianville_2027-03_month.zip` (built at `data/medianville_2027-03_month.zip`, which git ignores) |
| Dates | 2027-03-01 to 2027-03-31, 31 days |
| Records | 5,732,158 (184,908 a day on average; 126,465 on the lightest day, 254,851 on the heaviest) |
| Size | 460,891,403 bytes zipped (461 MB); 3,100,824,994 bytes unpacked (3.10 GB); 285 files |
| SHA-256 | `5aa7da829b9e22a9d0212a66ed6cd210a80f1c8ba52bd1b863c4c564ad729c3f` |
| SHA-256 of the `SHA256SUMS` inside | `05f914f27f25c7ba3a864b16cfb4d2e4d2bb097f60e2ca52e7f366d54ac1a47c` |
| Simulator | `sim/` at commit `dd0e6b6`, frozen for v2 (no change once hand-written text exists) |
| Built with | Python 3.11.5 (python.org installer), numpy 2.4.6, zlib 1.2.12, macOS 26.7.3 on arm64; 672 s for the 31 days, under 1 GB of memory |
| Release download checked | Not yet. The Release still holds the phase 4 build (459,134,321 bytes, SHA-256 `7339315…ed58`); this file replaces it under the same name, and the row is filled in once the download is checked. |

The zip's SHA-256 depends on the zlib that compresses it. `SHA256SUMS` lists the SHA-256 of every file inside, so two builds whose zips differ can still be compared file by file.

## What is in it

Under `medianville_2027-03/`:

- `README.md`, `SHA256SUMS`
- `summary.md` and `evidence_checks.md`: the month in figures and its evidence checks (the same files are in the repo, in `sim/evidence/results/v2_month_2027-03/`), and `month_day_metrics.csv`, every measured figure day by day
- One folder per day with the one-day tables (`records.csv`, `households.csv`, `persons.csv`, `organizations.csv`, `household_ledger.csv`, `public_services_context.csv`, `assumptions.csv`, `summary.md`) and `links.csv`, which ties records into chains across days: the chain (`unpaid_bill`, `utility_shutoff`, `overdraft`, `payday_loan`, `title_loan`), its id and step, the account and household, and the earlier record (date and record id) it follows from. Record ids start again at R0000001 each day, so a record is named by its date and id together.
- `state_2027-03-31.json`: the carried state after the last day; `simulate.py --date 2027-04-01 --state-in state_2027-03-31.json` goes on into April.

## The chains, in figures

Full report: [`sim/evidence/results/v2_month_2027-03/evidence_checks.md`](../../sim/evidence/results/v2_month_2027-03/evidence_checks.md). Targets: `sim/evidence/month_targets.csv`.

| Check | March | Target |
|---|---|---|
| Overdraft fees (T01) | 167.5 a day | 120-180 |
| Accounts that paid 79% of overdraft fees | 1.1% | about 9% over a year (CFPB 2017): **more concentrated** (see below) |
| Overdraft to fee to late rent | 75 chains reach a missed rent payment within two weeks of a fee; 20 then show the late or part payment | present |
| Disconnect notices (T16) | 43.1 a day | 40-55 |
| Disconnections (T05) | 12.8 a day | 11-12, within 25% |
| Notices that end in a shutoff | 30.1% | about one in four (18-32%) |
| Shutoffs reconnected by month's end | 89.7% | EIA-112 2024: 85% electric, 71% gas (70-90%) |
| Payday loans and renewals (T02) | 16.3 a day | 10-25 |
| Payday loans due that are renewed | 73.0% | CFPB 2014: over 80% (70-90%) |
| Title payments and rollovers (T03) | 7.1 a day | 5-10 |
| Adults with a bill unpaid at month's end | 15.0% (19.6% of households) | SHED 2025: 15.2% (11-19%) |
| SNAP left 14 and 28 days after loading | 25%, 8% | estimate |
| Checking on payday against 10-13 days later | 1.38 times | estimate |
| Week-to-week pay change, variable schedules | 18.8% (part-time 10.1%, full-time fixed 1.7%) | estimate |

Every household's money reconciles on every day. The typed-day targets hold as March averages as well (overdrafts, title payments, disconnections, notices, caregiving, paid tax preparation); T02's one-day count of new loans reads low in a carried month because renewals are counted separately (M08).

**Overdraft concentration is the one check the month misses, and it was left for v3 (the plan's section 9, item 6).** Only accounts opted in to debit-card overdraft coverage can overdraw (`finance.OD_OPT_IN`, about 6.6% of accounts), and that is part of the one-day population, which the brief keeps unchanged. So 2.1% of accounts paid any fee in March and 1.1% paid 79% of them. Spreading fees means letting banks pay ACH and recurring items into overdraft for accounts without the opt-in, which changes the one-day path; it is listed for Jason in the plan's section 9, item 6.

## Rebuilding it

From a checkout of `jas0nmjames/playground` at the commit that added this file:

```bash
python3.11 -m venv "$HOME/medianville-venv"
"$HOME/medianville-venv/bin/pip" install numpy==2.4.6
cd mapping-synthetic-transactions/sim
"$HOME/medianville-venv/bin/python" simulate.py --date 2027-03-01 --days 31 --out "$HOME/medianville-month"
"$HOME/medianville-venv/bin/python" evidence/month.py "$HOME/medianville-month" evidence/results/v2_month_2027-03 --label 'v2 phase 5 (`sim/`, commit dd0e6b6)'
"$HOME/medianville-venv/bin/python" ../tools/pack_month.py "$HOME/medianville-month" evidence/results/v2_month_2027-03 ../data/medianville_2027-03_month.zip
shasum -a 256 ../data/medianville_2027-03_month.zip
```

The venv and the month folder sit outside the repo; the zip lands in `data/`, which git ignores for it. The run takes about 12 minutes and 3.4 GB of disk (the day folders plus a state file per day). `month.py` rewrites the two committed results files; with the same inputs they come out unchanged. If the zip's SHA-256 differs, unpack it and run `shasum -a 256 -c SHA256SUMS` inside: if every file passes, only the compression differs (a different zlib); if a file fails, the simulation differs, and the Python or numpy version is the first thing to check.

Checked before publishing (2026-11-21): packing twice gave the same SHA-256; all 284 files listed in `SHA256SUMS` passed, read straight from the zip; rerunning the first two days at full scale reproduced their records, links, ledgers, households, summaries and carried state byte for byte. The typed-day year for the same simulator is `sim/evidence/results/v2_phase5_typed_days_2027`. (Phase 4's build was checked the same way, with three days.)

## Known limits

- One month, started on March 1. It inherits the shutoff notices of the ten days before, the payday and title loans already out and the tax season so far; the retry queue and overdraft chains start empty, so the first days run a little light.
- People, households, jobs and bills stay the same all month: a birth, death, move or new job drawn on one day does not carry to the next (that waits for a year with the roster changing, option C).
- The response shares at a shutoff notice, the overdraft terms, the retry schedules, the SNAP spending pace, the move of surplus checking to savings and the weekly hours are estimates, labeled in `carry.py`; SIPP and the JPMorgan Chase Institute's figures were not downloaded.
- Overdraft fees fall on far fewer accounts than in life (above).
- Wages carry v1's boost (decision 9.1 in the plan): compare households, not occupations.
