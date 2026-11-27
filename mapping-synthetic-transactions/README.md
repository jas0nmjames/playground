---
published: 2026-11-17
updated: 2026-11-24
tags: generative
url: https://medianville.netlify.app/
title: Medianville
summary: One simulated day in Medianville, an invented American city of about 100,000 people, played back record by record (purchases, bills, paychecks, bus rides, failed attempts) on a 3D miniature town and a printed map sheet, with a systems lens and a data explorer.
pinned: 1
status: active
issue: 115
---

# Medianville

[![Netlify Status](https://api.netlify.com/api/v1/badges/7162487b-5b7b-4cba-829f-bf319d02e97c/deploy-status)](https://app.netlify.com/projects/medianville/deploys)

Medianville is a fictitious American city of about 100,000 people. Built with publicly available research, it simulates representative days of financial life and beyond, including government services and unpaid labor. It shows the human goal behind each transaction and maps the surrounding societal contexts.

**[Open the city](https://medianville.netlify.app/)** · Simulated city, no real people

![The miniature town around noon, playing at five minutes a second: record paths arc between homes, towers and stores, with the Activity panel counting money moved, records, failures and unpaid hours. The pointer switches to the Map view, the same town as a printed map sheet, and back.](readme-media/01-city.gif)

## One household's day

This household starts March 3, 2027 with $295.04 in checking and $49 in cash. Car insurance ($268.45) drafts at 1:46 a.m. At 11:23 a.m. the debit card is declined for $36.84 of gas, so they pay cash. At 6:05 p.m. they give up on the week's groceries ($56.81): there isn't enough on hand or on any card.

![Household H22924's declined $36.84 gas purchase at 11:23 a.m., open in the record sheet. The timeline is dragged into the evening, and the household's day then lists the abandoned groceries at 6:05 p.m., the cash fill-up, the declined card and the car insurance at 1:46 a.m.](readme-media/02-household.gif)

[Try it →](https://medianville.netlify.app/?intro=0&run=v2-2027-03-03#household=H22924)

## More than money

Government services and unpaid labor are records too. On the baseline day, more than one record in four is a public service (40,071) or an unpaid job (13,234).

- A 56-year-old spends four hours caring for his wife when the home care aide misses the visit. [Try it →](https://medianville.netlify.app/explorer/?run=v2-2027-03-03#record-R0077959)
- County EMS helps a 77-year-old up after a fall; the county levy covers the $448 cost. [Try it →](https://medianville.netlify.app/explorer/?run=v2-2027-03-03#record-R0201900)
- A 59-year-old waits 71 minutes on the IRS phone line about a missing refund. [Try it →](https://medianville.netlify.app/explorer/?run=v2-2027-03-03#record-R0188947)

![The Activity panel's chips switch off purchases, income, bills and failures one at a time, until only public services (violet dashed paths) and unpaid work (white dotted paths) cross the miniature town on a weekday morning.](readme-media/03-beyond-money.gif)

## Why I made this

The private sector often focuses on dollars, cents and quarterly profitability. My history and liberal arts background, and my MBA in sustainability with its triple bottom line, push me to look wider, including at unpaid labor and government services.

I hope it gives researchers, teams and historians ideas about what large language models can produce, and how to build richer views into the stories we tell.

This doesn't replace research with real people. It's a way to explore what public research says and find questions worth checking.

## How it was made

A simulator produces the records. People, households, employers and bills come from a seed, and each day is settled minute by minute against every household's money. Claude Fable 5.2 wrote the first simulator and generated the first day. Claude Opus 5.5 wrote v2, the data the site opens on, with rates set from 42 public datasets. Claude also hand-wrote 800 detailed records (500 in v1, 300 in v2). Jason James had the idea, framed it and made the design decisions; Claude built the viewers under his direction.

## The city

**Miniature and map.** Switch between a miniature town and a printed map (M). Turn, tilt and zoom the miniature. People walk on two legs, trees sway in the wind, contact shadows are softer, and clouds cast slow shadows by day (all still under reduced motion). Sound is off until you turn it on.

[Try it: miniature →](https://medianville.netlify.app/?intro=0) · [Try it: map →](https://medianville.netlify.app/?intro=0#view=map)

**Playback speed.** Live, or 1, 5 or 20 minutes a second.

![Playback in Live at 7:41 a.m., when the city is taking children to school; the pointer switches to 5 and then 20 minutes a second, and drags the timeline into the evening.](readme-media/04-speed.gif)

[Try it →](https://medianville.netlify.app/?intro=0)

**Change the day.** The baseline Wednesday plus 18 other typed days of 2027, including a winter storm, a heat wave, tax refunds and Social Security Wednesdays.

![The day menu opens under the day control and lists v2's 19 days and v1's March 3. Choosing Tuesday, January 19, the winter storm, reloads the city on that day, with power outages among the latest records.](readme-media/05-days.gif)

[Try it: winter storm →](https://medianville.netlify.app/?intro=0&run=v2-2027-01-19)

**Records and households.** Open a record to see who paid whom, how, whether it worked and the job someone was trying to get done, then see the household's whole day.

[Try it →](https://medianville.netlify.app/?intro=0&run=v2-2027-03-03#record=R0093156)

## Data explorer

Records, households, people, organizations and a summary, with filters, search, group-by and CSV download.

![The data explorer on the baseline day. Ticking Didn't work narrows 202,402 records to 6,168, and the first of them, a missed bus at midnight, opens in a side sheet with its job statement, parties and money.](readme-media/06-explorer.gif)

[Try it →](https://medianville.netlify.app/explorer/)

## Systems lens

The lens builds on "societal context", which Donald Martin Jr. advocates for: people, places and problems are shaped by shifting social, cultural, historical, political, economic and environmental conditions. It maps one block per district, in six layers: today, economic, political, built and natural, social and cultural, historical. The circumstances are composites of documented US patterns, and the loops are hypotheses, not findings.

![From household H22924's day, What shaped this household's day opens the systems lens over the paused city, on Fox Hollow across the outer suburbs. Pointing at each of the six layers in the list, from Today down to Historical, lifts it in the drawing.](readme-media/07-lens.gif)

[Try it →](https://medianville.netlify.app/#lens=larkin/district)

## For agents and LLMs

Start at [llms.txt](https://medianville.netlify.app/llms.txt). Plain-markdown pages cover the method, data dictionary, runs and districts, and "Copy for AI" copies a record with context. Data is CC BY 4.0; cite it as synthetic.

How it's built: [`llms.txt`](llms.txt) is written by hand, with the provenance note to say once at the start of a session. [`agents/`](agents/) holds the Markdown pages (the About page, a data dictionary for every table, every run with its README and summary, the districts and the March month), and [`llms-full.txt`](llms-full.txt) is all of it in one file; every page starts with a line pointing back to `llms.txt`. `tools/build_agent_pages.py` (standard library only) writes `agents/`, `llms-full.txt` and the About page's schema.org Dataset from the About page, the run zips, the manifest, `systems-lens/blocks.json` and the month run record; run it after changing any of them and commit what it writes, since `sim/tests/test_agent_pages.py` fails when a page is stale. Agents bring their own compute: the day zips are linked on GitHub (`raw.githubusercontent.com`), not on this site, [`robots.txt`](robots.txt) keeps crawlers off the zips, and [`_headers`](_headers) serves the agent files as Markdown. Every page links `llms.txt` as **For agents** and in its head as `rel="alternate"`, and the viewer's intro ends with a line for agents.

## What's real and what isn't

- **Real:** national rates and program rules, and federal program names such as the IRS, Medicare and SNAP.
- **Invented:** every person, household, business, local agency, church and street.
- **Composite:** the systems lens blocks.

Main limits:
- Households are built by rule to match national shares, not drawn from Census microdata.
- Wages run about 14% high on purpose, to make up for households smaller than real ones.
- Each typed day is simulated on its own; only the March month carries bills and loans forward.
- Positions in the animated city are approximate.

The full list is on the [About page](https://medianville.netlify.app/about/).

## History

The work is told as milestones, each with its own chapter in [the story](story/). Folders, tags and milestone titles use these names; viewers and data runs keep their own version numbers.

| Milestone | Viewer | Data run | Data plan phases |
|---|---|---|---|
| [M1 One day](story/01-one-day/) | v1, the first viewer ([archived](archive/)) | v1: `halvern_2027-03-03.zip` | — |
| [M2 Miniature and Map](story/02-miniature-and-map/) | v3 as first shipped ([archived](archive/)) | v1 | — |
| [M3 Grounding in evidence](story/03-grounding-in-evidence/) | — | v1, measured against evidence targets | 0, 1, 2 |
| [M4 The refined city](story/04-the-refined-city/) | latest (root) | v1 renamed: `medianville_2027-03-03.zip` | 3b (rename) |
| [M5 More time](story/05-more-time/) | latest, with the day menu | v2: 19 days and the March month | 3, 4, 5, "6"* |
| [M6 Refinements](story/06-refinements/) | latest | v2 | — |
| [M7 Open to agents](story/07-open-to-agents/) | latest, with Copy for AI | v2, with pages for agents ([For agents](#for-agents-and-llms)) | — |

\* [#82](https://github.com/jas0nmjames/playground/pull/82), the systems lens's district tier, shipped as "phase 6" of v2; the data update plan's own phase 6 is still to come.

[M0 The idea](story/00-the-idea/) came before any of it, and [Next: mining for projects](story/next-mining-for-projects/) is the goal still ahead. No viewer v2 shipped: the second round was a set of visual-direction prototypes in the Claude app, and the chosen direction became v3. The [archive](archive/) keeps the frozen viewers; they change only in their relative paths and an "Archived version" link back to the latest. The city was called Halvern before 2026-11-20, and the archives keep that name.

### Data runs

| Data run | File | Status |
|---|---|---|
| v1: Wednesday, March 3, 2027 | `data/halvern_2027-03-03.zip` | Frozen as shipped. The archived viewers load it. |
| v1, renamed | `data/medianville_2027-03-03.zip` | The same run with only the city's name changed, written by `tools/rename_run.py`. The latest viewer and the explorer list it in their day menu as v1. |
| v2: the evidence update | `data/runs/v2/medianville_<date>.zip`, 19 days listed in `data/runs/manifest.json`; simulator in `sim/` (the `medianville_sim` package), frozen at commit `dd0e6b6` | Current, 2026-11-21. The baseline day (Wednesday, March 3, 2027, with 300 hand-written records) and the 18 typed days that stand for 2027. The latest viewer and the explorer open the baseline day; `?run=<id>` or the day menu opens another. See the [data update plan](story/03-grounding-in-evidence/medianville-data-update-plan.md) and the [close reading](story/05-more-time/medianville-v2-close-reading.md). |
| v2, phase 4: March 1–31, 2027, carried day to day | GitHub Release `medianville-v2-month-2027-03`: [download (about 460 MB), not needed to use the site](https://github.com/jas0nmjames/playground/releases/download/medianville-v2-month-2027-03/medianville_2027-03_month.zip) | Built 2026-11-20 and rebuilt 2026-11-21 on the frozen simulator: 5.7 million records with the chains across days (unpaid bills, shutoffs, overdrafts, payday and title loans). The pages never load it. Checks and summary in `sim/evidence/results/v2_month_2027-03/`; see the [month run record](story/05-more-time/medianville-2027-03-month-run-record.md). |

## Running them locally

No build step. Serve the folder, then open `/` for the latest viewer, `/systems-lens/` for the systems lens, `/explorer/` for the data explorer and `/archive/` for the archived viewers:

```bash
python3 -m http.server 5181 --directory mapping-synthetic-transactions
```

Opening an `index.html` as a file can't fetch the data, so each animated page then plays its placeholder day, and the explorer says it couldn't load the run. The Miniature also needs internet access for three.js and its fonts.

The README's GIFs (`readme-media/`) are taken the same way, from a local server of this folder, with the Google Chrome on this computer and nothing to install. From this folder:

```bash
node tools/capture_readme_gifs.mjs
```

That retakes all seven at 1280 × 800, written 800 px wide at 10 frames a second; name some (`node tools/capture_readme_gifs.mjs 02 05`) to retake only those, and add `--frames DIR` to save about one frame a second of each, read back from the GIF, to look at. No page on the site loads them.


## Running the simulator

The v2 simulator needs Python 3.10 or later and numpy. From `sim/`:

```bash
python3 simulate.py --out out
```

That is one day (Wednesday, March 3, 2027, the full city, seed 20270303). `--date`, `--weather storm|heat`, `--households N` and `--seed N` change it. With `--days N` the city is carried forward day by day: balances, unpaid bills waiting to be retried, shutoff notices running out, overdrafts, payday and title loans, SNAP balances and the weeks' hours all carry (`sim/medianville_sim/carry.py`), and each day also writes `links.csv`, which ties records into chains across days. `--state-out` and `--state-in` save and continue a carried run; `--carry` carries a single day.

The March 2027 month (phase 4), its checks and its bundle:

```bash
python3 simulate.py --date 2027-03-01 --days 31 --out month
```

```bash
python3 evidence/month.py month evidence/results/v2_month_2027-03
```

```bash
python3 ../tools/pack_month.py month evidence/results/v2_month_2027-03 ../data/medianville_2027-03_month.zip
```

The typed-day year: `python3 evidence/checks.py run OUT --label TEXT`. Tests: `python3 -m pytest tests --run-slow`.

The published days (phase 5): run the baseline day and each typed day into one folder (`simulate.py --out runs/2027-03-03`, then `--date D [--weather W] --out runs/D` for each day `evidence/typed_days.py` lists), then

```bash
python3 ../tools/pack_runs.py runs --commit dd0e6b6
```

which writes `data/runs/v2/medianville_<date>.zip` and `data/runs/manifest.json`, the same bytes every time. The baseline day picks up the hand-written text from `sim/detailed_overrides.csv` by itself. `tools/sample_records.py` draws a stratified sample of a run as readable cards (the close reading) or one line a record (for writing); `tools/merge_detailed.py` merges `sim/detail_parts/part*.txt` into the overrides.

## What's in this folder

| Path | What it is |
|---|---|
| `index.html` | The latest viewer, Miniature and Map: the city plan, both views, the activity panel, playback, the systems lens overlay and the first-visit intro |
| `about/index.html` | The About page: what the project is, where it came from, how it was made, sources, limits and credits. Plain HTML and CSS. |
| `real-day.js` | Loads the run for the latest viewer and folds it onto its town (see below) |
| `runs.js` | Reads `data/runs/manifest.json` for both viewers: which day to open (the default, or `?run=<id>`) and the day menu |
| `sound.js` | The latest viewer's sound, generated in the browser with Web Audio |
| `archive/` | The frozen viewers, one folder per milestone (M1's first viewer, and v3 as first shipped with its `real-day.js`), each with its own README, and an [index page](archive/) that shows them side by side |
| `v1/index.html`, `v3/index.html` | Redirects to the archive, so old links and bookmarks still work |
| `systems-lens/index.html` | The systems lens: the layers, callouts, loops and details sheet, with its prototype content built in |
| `explorer/index.html` | The data explorer: loading, tables, filters, search, group-by, detail sheets and summary, in one page |
| `systems-lens/directions.html` | The three directions tried first (Section, Exploded view, The Works), in their original hand-drawn style |
| `fflate.js` | [fflate](https://github.com/101arrowz/fflate) (MIT), used by every page to unzip the run in the browser |
| `data/halvern_2027-03-03.zip` | The v1 run, frozen exactly as delivered under the city's first name: the data tables, the simulator, and the hand-written records. The archived viewers load this file. |
| `data/medianville_2027-03-03.zip` | The same run with only the name changed, in every file's contents and paths (`medianville/`). The day menu lists it as v1. |
| `data/runs/manifest.json`, `data/runs/v2/medianville_<date>.zip` | v2's published days: the baseline day and the 18 typed days, each a zip of the day's tables, the systems lens's blocks, the simulator, a README and `SHA256SUMS` (the baseline day also carries the hand-written text). The manifest lists every run, v1 included, with its size and SHA-256. |
| `tools/rename_run.py` | Writes the renamed copy from the frozen zip. Mapping the copy back gives every file of the original byte for byte; `sim/tests/test_rename_run.py` checks it. |
| `data/halvern/` | The frozen v1 package unpacked so it can be read on GitHub, without the four large tables (`records.csv`, 77 MB; `persons.csv`; `households.csv`; `household_ledger.csv`), which are only in the zip |
| `data/halvern/out/summary.md` | Counts, calibration against the anchors, fees, public dollars and the costliest frictions |
| `data/halvern/detailed_sample_500.csv` | The 500 hand-written records |
| `data/halvern/simulate.py`, `halvern_sim/` | The v1 simulator, frozen (Python 3.10+ and numpy). The package's own [README](data/halvern/README.md) explains how to re-run it for another date, a storm, or several days in a row. `sim/tests` checks that it still reproduces the zip byte for byte. |
| `sim/detailed_overrides.csv`, `sim/detailed_sample.csv`, `sim/detail_parts/` | v2's 300 hand-written records: the text keyed to the baseline day's record ids, the finished rows on their own, and the parts they were written in |
| `tools/pack_runs.py`, `tools/sample_records.py`, `tools/merge_detailed.py` | Pack the published days and write the manifest; draw samples to read or write; merge the hand-written parts |
| `sim/simulate.py`, `sim/medianville_sim/` | The v2 simulator, frozen for v2's hand-written records, with its tests (`sim/tests/`), evidence targets (`sim/evidence_targets.csv`) and typed-day checks (`sim/evidence/`). See the [data update plan](story/03-grounding-in-evidence/medianville-data-update-plan.md). `medianville_sim/carry.py` is what a run of several days carries from one day to the next (phase 4). |
| `sim/evidence/month.py`, `sim/evidence/month_targets.csv` | The month's evidence checks: its targets, the chains across days, and the typed-day targets over the month |
| `sim/evidence/results/v2_month_2027-03/` | The March 2027 month's `summary.md` and `evidence_checks.md`. The month itself is a Release download (above), not in the repo. |
| `tools/pack_month.py` | Packs a carried month into one zip, the same bytes every time, with a `SHA256SUMS` file inside |
| `evidence/` | The real-accounts research that came before the downloads: the human-evidence report (the first day scored against 69 real sources), its 69 sources, 76 findings and 25 quotes, and the prompt that produced them. The findings' `E` ids are the `evidence_ids` in `systems-lens/blocks.json`. |
| `sources/` | The download manifest and log, the tools that build `sources/derived/` from the raw downloads, and the derived tables the simulator reads. Raw files stay out of git. |
| `story/` | How the project was made, one folder per milestone: the documents behind it, the decision log and the screenshots, listed below |
| `tools/check_links.py` | Checks every link in the project's documents and pages, relative or to this repo on GitHub, Pages and the Netlify site |
| `llms.txt`, `llms-full.txt`, `agents/` | The pages for agents and LLMs (see [For agents and LLMs](#for-agents-and-llms)); `llms.txt` by hand, the rest written by `tools/build_agent_pages.py` |
| `readme-media/`, `tools/capture_readme_gifs.mjs` | The GIFs in this README, and the script that retakes them (see [Running them locally](#running-them-locally)). No page on the site loads them. |
| `robots.txt`, `_headers` | Crawlers welcome everywhere but the zips; Netlify's headers for the agent files and the data |
| `LICENSE-DATA`, `CITATION.cff` | The CC BY 4.0 notice for the data and documents, and how to cite them (see [License](#license)) |

### The story and its documents

[`story/`](story/) tells the project as milestones and holds the documents behind it, each in the milestone that produced it:

- [The story](story/README.md): the arc on one page, with the version table and a line per milestone.
- [Design decision log](story/decisions.md): every decision behind the project, with why, what else was considered, what it costs, whose call it was and its milestone.
- **M0 The idea:** [Seeing the Margins: What a Representative American Day Reveals](story/00-the-idea/seeing-the-margins.md), the research white paper (why no real city stands in for the US, and what fragility, payment habits and government look like in an ordinary day), and [Synthetic Mid-America: City Design v0.1](story/00-the-idea/synthetic-mid-america-city-design-v0.1.md), the design of the city: districts, economy, transaction model, field visits, and the lenses used to read it.
- **M1 One day:** [the transaction generator prompt](story/01-one-day/medianville-transaction-generator-prompt.md) that generated the data; [how the day was built](story/01-one-day/medianville-build-approach.md): the method, what close reading of the sample caught, and what was left unfixed; and the [run record](story/01-one-day/medianville-2027-03-03-run-record.md): what the run produced and how close it came to each anchor.
- **M3 Grounding in evidence:** the [data update plan](story/03-grounding-in-evidence/medianville-data-update-plan.md): how the evidence was folded in and the run went past one day, phase by phase, with each phase's status; and the [human evidence report](evidence/report.md): the first day scored against 69 real sources, kept as written, with its [sources](evidence/sources.csv), [findings](evidence/evidence.csv), [quotes](evidence/quotes.csv) and [research prompt](evidence/research-prompt.md).
- **M4 The refined city:** the [systems lens design record](story/04-the-refined-city/medianville-systems-lens.md): the directions tried, what was decided, and what waits for the next run; and the [miniature realism design record](story/04-the-refined-city/medianville-miniature-realism.md): the tilt-shift references, the iterations tried in the realism lab, what was kept and how it works.
- **M5 More time:** the [v2 run record](story/05-more-time/medianville-v2-run-record.md): the 19 published days (phase 5): kinds, weights, records, sizes, SHA-256, how they were checked and how to rebuild them; the [month run record](story/05-more-time/medianville-2027-03-month-run-record.md): the March 2027 month (phase 4, rebuilt in phase 5): dates, seed, records, size, SHA-256, how to rebuild it, and where to download it; and the [v2 close reading](story/05-more-time/medianville-v2-close-reading.md): 200 records read by two readers before v2 was frozen, what they found, what was fixed and what was left for v3. The second readers' reports on [the sample](story/05-more-time/medianville-v2-second-reader.md) and on [the hand-written records](story/05-more-time/medianville-v2-handwritten-second-reader.md) are kept as written.

The documents were in `reference/` until 2026-11-24. The frozen simulator in `sim/`, its targets and the packing tools still name them by their old `reference/` paths, because changing them would change the published zips; [the story's README](story/README.md#where-the-documents-were) maps each old path to its new one.

Everything in the data is synthetic. People, businesses and local agencies are invented. Federal programs keep their real names because the specification requires them. Synthetic data suggests where to look; it isn't evidence.

### Data sources

The research came in four rounds, and the [About page](https://jas0nmjames.github.io/playground/mapping-synthetic-transactions/about/#sources) lists every source:

1. **Calibration anchors** for the first run: the American Community Survey, Current Employment Statistics, the Diary of Consumer Payment Choice, SHED, United For ALICE, the Consumer Expenditure Survey and 2027 program figures ([run record](story/01-one-day/medianville-2027-03-03-run-record.md)).
2. **Real accounts** beside the first day: 69 sources, 76 findings and 25 quotes in [`evidence/`](evidence/), summed up in the [evidence report](evidence/report.md), which named what v2 had to add.
3. **Downloaded datasets** that set v2's rates: 42 public datasets in [`sources/manifest.csv`](sources/manifest.csv), built into `sources/derived/` and named target by target in `sim/evidence_targets.csv`.
4. **District history** behind the systems lens: each circumstance's `source_note` in `systems-lens/blocks.json`.

**Wages are boosted on purpose.** Each worker is paid 1.23 times the national pay for their occupation, about 14% more than a real worker in the same job in 2027. Medianville's households are smaller than real ones, so fewer paychecks reach each home, and the boost makes up for it. Household incomes, balances and bills are closer to right this way, but one person's paycheck runs high, so compare households rather than occupations. The [data update plan](story/03-grounding-in-evidence/medianville-data-update-plan.md) explains the numbers.

**What v2 still gets wrong.** v2 keeps v1's people so the two can be compared, and some of v1's households don't hold up. The [close reading](story/05-more-time/medianville-v2-close-reading.md) lists them:
- SSI goes to people whose household income or spouse rules it out, and some SSI recipients have no Medicaid.
- Coverage doesn't always follow eligibility, such as uninsured adults with no income.
- Every renter with no income pays the same $380.
- Refundable credits reach some households earning well over the EITC limit (about 140 of the day's 640).
- Some jobs are paired with unrelated employers.
- A few trips run 60 to 80 miles.
- Overdraft fees fall on fewer accounts than in life.
- `time_minutes` counts the wait but not the travel.

## How the Miniature and Map use the real day (since v3)

The figures in this section are for v1's March 3, the day v3 first loaded; v2's days differ a little (the explorer and each run's `summary.md` have their counts).

v3 was built as a Claude artifact around its own placeholder day: 4,130 records among 225 homes and 100 named buildings. `real-day.js` (once `v3/real-day.js`; the copy as first shipped is in [`archive/m2-miniature-and-map/`](archive/m2-miniature-and-map/)) swaps in the real run once it has downloaded. Records keep their real ids, names, amounts, districts, job statements and narratives. Only where they are drawn is approximate, because v3 draws one small town rather than the run's six districts.

**Homes.** Each household is drawn at one of v3's homes in the area its district folds into, picked by a hash of its id:

| Run's districts | Drawn at | Households |
|---|---|---|
| D1 Downtown, D2 Inner suburbs | Millbank's rowhouses (180 homes) | 22,222 |
| D3 Outer suburbs, D4 Satellite city, D5 Rural town | Brookfield Commons' houses (44 homes) | 18,781 |
| D6 Open country | The farm in Cutler Fields (1 home) | 2,447 |

People are drawn at their household's home. Record sheets still name the real district, such as "Household H14044 · Inner suburbs".

**Places.** Each of the 1,672 organizations is drawn at a v3 building of the closest kind, judged by its sector and name: diners (224), sheds for industry, construction, wholesale and transport (222), big-box stores, pharmacies and auto shops (178), office towers for finance, professional services and information (174), offices (166), the clinic (163), the church (121), corner shops, salons and barbers (108), the school, which also stands for child care and preschools (77), gas stations (40), city hall (39), the bank (32), grocery stores (31), the farm stand (11), the utility (6) and the transit center (2). The 78 parties outside Medianville, such as federal agencies, card networks and online services, sit at the east end of Route 9, "out of town".

**Kinds.** v3 had five record kinds. Public services were 39,000 of the day's records, so they get a sixth kind of their own rather than being drawn as purchases:

| Kind | Record types | Records |
|---|---|---|
| Purchase | purchase, benefit redemption, transfer, business to business | 90,797 |
| Income | income, benefit issuance | 10,258 |
| Bill | bill payment, tax, insurance claim | 41,785 |
| Public service (new: violet, long dashes, ring) | public service encounter | 38,975 |
| Unpaid work | non-monetary job | 13,042 |
| Failure | every failed attempt, plus anything declined, abandoned, failed or rescheduled | 6,896 |

**Volume.** The placeholder day had about 3 records a minute; the real one averages 140, with bursts in the hundreds. v3 now draws at most 28 new paths a second (14 on small screens) and caps the miniature's walking and driving figures. The counters, the activity feed, the failure pins and the timeline still count every record. A household whose day is open always has all of its paths drawn.

**Failures.** A failure gets a pin only at a place: the building of the organization involved, the nearest bus stop for a missed bus, or Route 9 for a party out of town. Failures with no outside party, such as a missed caregiving visit, are counted but not pinned.

**Memory.** Each record is a small object; a sheet reads the rest of the record's row from the CSV bytes only when it opens. The whole day used about 180 MB of JavaScript memory in Chromium.

By midnight v3 shows $56.1 million moved, 6,896 failures and 15,650 unpaid hours. The summary's 16,736 hours count all 13,201 non-monetary jobs, while v3 counts the 13,042 that didn't fail.

### How the miniature looks

The miniature's look came out of a realism lab built against tilt-shift photographs (see [the design record](story/04-the-refined-city/medianville-miniature-realism.md)). It keeps the town, the record language and the focus blur, and adds:

- **Sun and sky.** A solar path for March 3 near 39° N, with north up as on the Map: sunrise 6:48 a.m., sunset 6:12 p.m., the sun 44° high at noon. Sky colours follow the sun's height and light the town through an environment map, so shade takes the sky's colour and glass and paint reflect it. Exposure adjusts to the light.
- **Filmic tone.** Highlights roll off instead of clipping, with the saturation, contrast, split toning and grain of a print.
- **Contact shadows.** Darkening where things meet the ground and each other, so nothing floats.
- **Night lights.** Windows glow in the same occupancy pattern as before, lamps throw pools of light, cars have headlights and tail lights, signals cycle, and bright light blooms.
- **Street detail.** Lane lines, a double yellow line on the main roads, crosswalks and stop bars, signals and stop signs, cars parked along the curbs, hydrants, manholes, street trees downtown, lamps on the local streets, and units and water tanks on flat roofs.
- **Materials.** Paint, glass and water reflect the sky; walls, roofs, pavement and grass carry grain; no two parts are exactly the same colour.
- **Past the board.** The town sits in a wider region instead of on a table: suburbs, farms to the south-west and industry to the south-east, fading into haze.
- **Windows on every side,** so the board can turn.

The town itself is unchanged. Every addition draws from its own random stream, so each building, footprint, home, anchor and front-facing window is the same as before, in the same order; the plain centre dashes on the main roads gave way to the double yellow line. The Map and the run see the same city.

### Known limits

- The miniature needs WebGL and loads three.js 0.160.0 from jsDelivr. If either is missing, v3 switches to the map after 12 seconds.
- Positions are approximate, as described above, and a building's sheet lists the real places it stands for. v3's map labels and building names are its own inventions.
- In this container's software rendering, the miniature ran at about one frame a second, as the unmodified artifact did. Frame rates on real hardware weren't measured. The new look draws the scene twice plus its shadows, about six million triangles a frame with the land past the board, and renders at no more than 1.5 times the screen's pixel density to pay for it.

## License

The code (the simulator in `sim/`, `tools/`, and the pages' HTML, JavaScript and CSS) is under the Mozilla Public License 2.0, the repository's [license](../LICENSE). The generated data, `systems-lens/blocks.json`, the hand-written records, the agent pages, the documents and the images are under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) ([`LICENSE-DATA`](LICENSE-DATA)). [`evidence/`](evidence/) is third-party material (quotes, sources and citations) and is under neither; the public datasets in `sources/` keep their publishers' terms. `fflate.js` is MIT.

Cite it as: James, J. (2026). Medianville: a simulated American city's transactions [synthetic dataset]. https://medianville.netlify.app/ Data under CC BY 4.0. [`CITATION.cff`](CITATION.cff) has the same. Please say that the data is synthetic; the license can't require it, so the project asks.

## Claude

The data was generated by Claude Fable 5.2 (`claude-fable-5-2`) in the Claude app, in one long session on November 16, 2026. That session is described in [How the Medianville day was built](story/01-one-day/medianville-build-approach.md). The research, the city design, the first viewer (now in the archive) and v3 were also made with Claude in the Claude app. None of those sessions can be counted from here.

The work in this repository was one Claude Code session (claude-opus-5-5) on November 17, 2026, in three passes:

1. **Moving the first viewer (now in the archive) here.** Matched the project to its artifact, copied the page and unzip library, unpacked the run, added the reference documents, made the page load the run on its own, added the footer, tested it in headless Chromium at desktop and phone sizes, fixed the caption overflow that showed, wrote this README, and opened the pull request into `development`.
2. **Finding v3.** Found v3, Miniature and Map, among the artifacts and checked what it needed to show the real day.
3. **v3 on the real day.** Read v3 in full, wrote `v3/real-day.js`, and changed v3 for real volumes: the public-service kind, the path budget, place-only pins, failure marks, real labels and sheets, and the header status. Fixed the garbled names and the failure count in both versions. Tested v3 in headless Chromium with three.js served locally: the day loaded in about 15 seconds with no errors, the counters matched the run's summary, and the record, household, building and pin sheets showed the right data. Took the screenshots, updated this README and the root README, and opened the pull request into `development`.

The systems lens was one Claude app session (claude-opus-5-5) on November 18, 2026, with the repository attached at the end. It explored three directions in the Biesty style, settled on the exploded view, added loops and callouts, restyled it to match v3, and then added the pages, the design record and the screenshot here, and opened the pull request into `development`. Its row is an estimate of about 90 model requests, counted from the session's tool calls rather than measured.

The data explorer was one Claude app session (claude-opus-5-5) on November 19, 2026. It read the run and v3's loader, wrote `explorer/index.html`, checked its counts against the run's summary, tested it in headless Chrome at desktop and phone sizes, took the screenshot, and wrote these README sections. That session couldn't push, so the change came to this repository as a patch. Its row is an estimate of about 70 model requests, counted from the session's tool calls rather than measured.

v2's first three phases were Claude Code sessions (claude-opus-5-5) from November 18 to 20, 2026, recorded here from their commits rather than measured. A cloud session copied the simulator, wrote the evidence targets and the typed-day set with their checks, and fetched the downloads that cloud machines could reach; another tagged records with the systems lens's blocks. A session on Jason's Mac fetched the rest from a home connection, set caregiving from ATUS, and made batches C (calendar and day weights), I (household inputs), J (the missing jobs), P (places and organizations) and R (rates tuned to the targets). Their rows have no figures, so the totals leave them out.

The intro, the About page and the data links were one Claude Code session (claude-opus-5-5) on November 20, 2026, from Jason's handoff and decision log. It checked the repository for the old name, wrote the intro over the viewer and the About page, added the Data and About links and the explorer links in the record and household sheets, added the decision log to `reference/`, tested it all in headless Chrome at desktop and phone sizes (51 checks, covering focus, keys, deep links, blocked storage and reduced motion), ran the simulator's tests, took the screenshots, updated this README and opened the pull request into `development`. Its row counts 56 model requests measured in the session transcript and about 10 more estimated for the README, the commit, the pull request and the reply.

The rename to Medianville was one Claude Code session (claude-opus-5-5) on November 20, 2026, from Jason's brief, between v2's phase 3 and packaging. Before changing anything it ran the v2 simulator over the typed-day set and kept every output outside git. It renamed the simulator package and every invented name, reran the year, and mapped every output back to the old name: all 181 files matched batch R byte for byte. It wrote `tools/rename_run.py` and the renamed copy of v1 with a round-trip test, renamed the pages, the sound setting's key and the reference docs, updated the decision log, the data update plan and this README, ran the simulator's tests, tested the pages in headless Chrome at desktop and phone sizes, retook six screenshots and opened the pull request into `development`. Its row counts 182 model requests measured in the session transcript and about 15 more estimated for the commit, the pull request and the reply; at the time of measuring, the session had used ≈ 50M tokens, about 99% of them cache reads.

Phase 4, the month, was one Claude Code session (claude-opus-5-5) on November 20, 2026, from Jason's brief. It set up Python 3.11 and numpy on the Mac and checked that the unchanged simulator reproduced the typed-day year byte for byte, then made the simulator carry consequences from one day to the next, one commit per change: a retry queue for unpaid bills, notice-to-shutoff timers, overdraft chains, payday and title rollovers, SNAP and checking balance paths, and week-to-week income, each with its tests. It reran the typed-day year after every commit (unchanged each time), fixed an old scam-loss branch that made money when carried balances triggered it, wrote two source tools (SHED bills, EIA-112 disconnections), ran March 2027 at full scale twice (fitting four carried-only terms after the first), wrote the month's evidence checks and packing tool, built the bundle, and updated the plan, the decision log and this README. Its row counts 205 model requests measured in the session transcript and about 10 more estimated for the commit, the pull request and the reply; at the time of measuring, the session had used ≈ 92M tokens, about 98% of them cache reads. The two full-city month runs, the typed-day reruns and the tests ran on the Mac's CPU and are not counted.

Phase 5, reading and publishing v2, was one Claude Code session (claude-opus-5-5) on November 21, 2026, from Jason's go-ahead.

1. **Groundwork.** It built the run packer, the manifest and the day menu for both viewers, and tested them in the browser at desktop and phone widths.
2. **Close reading.** It drew 200 fresh records as cards and read them, then measured each suspicion across the whole day against v1. A second Claude agent read the same cards without the code.
3. **Fixes.** On Jason's choice it made three fixes, one commit and one test file each: owner housing costs from AHS by income, the records, and the text. It reran the typed-day year and the month (every target held), and verified and recorded the month.
4. **Hand-written records.** It froze the simulator and wrote 300 hand-written records. A second agent checked them against their fields, and it fixed what that turned up.
5. **Publishing.** It packed and verified the 19 days and updated this README, the About page, the plan, the decision log and the run records.

Phase 6, removing the systems lens's dead ends, was one Claude Code session (claude-opus-5-5) on November 21, 2026, from Jason's handoff and its district history addendum. It wrote the district tier into `systems-lens/blocks.json` (34 circumstances and six district loops, every existing id kept), checked the figures in the twelve historical and built circumstances against their sources with three web-reading agents and the BLS, FDIC and Census data themselves, and reworded six (listed in the [design record](story/04-the-refined-city/medianville-systems-lens.md)). It added district mode to the lens, the fourth case to the viewer's record and household sheets, and the explorer's link and "Lens tags" label; extended the blocks test and added tests that every published run's tags hold; and checked it all in headless Chrome: 56 records and every household type on each of the 20 days (1,120 records and 339 households opened in the lens, with no disabled rows and no page errors), the explorer's link for a record of each kind on every day (60 links, each opening the right block in the right mode, on the same day), and the pages at desktop and phone widths. It updated this README, the About page, the design record and the decision log, and opened the pull request into `development`.


The polish pass was one Claude Code session (claude-opus-5-5) on November 22, 2026, from Jason's list of adjustments. It planned the work at medium effort, then made it in three phases, one commit each, checking every phase in the browser at phone, tablet and desktop widths: Live playback by default, turning the board while paused, the new title and subtitle, and the "Sample day" chip; the map's margin rebuilt and the sheet restyled in the viewer's type and colors; and the compact header with its menu, the view switch and lens over the city, the day menu beside the clock, and the footer fitted to a phone. It retook the miniature, map and intro screenshots, and updated this README and the decision log.

The sources and docs review was one Claude Code session (claude-opus-5-5) on November 22, 2026, from Jason's question about missing sources. It checked the About page, the intro, the explorer, the READMEs and the reference docs against the published v2 run, brought the human-evidence report and its 69 sources into `evidence/`, rewrote the About page's sources (all four rounds of research, every downloaded dataset), method, limits and credits for v2, and updated the sources and root READMEs.
The milestones pass was one Claude Code session (claude-opus-5-5) on November 24, 2026, from Jason's handoff. It moved the frozen viewers into `archive/` and the documents into `story/`, one folder per milestone, with a README for each, and tagged every entry in the decision log with its milestone. It took the first viewer off the live pages and the directory, wrote a link checker and the script for the GitHub milestones, tags and releases, and tested the pages in headless Chromium at desktop and phone widths. It retook the thumbnail and the preview, frame by frame on a paused clock because this container renders WebGL in software. In the same session it added a `status` to every project in the playground and wrote `scripts/sync-github.mjs` (pull request #91). Its row is an estimate of about 140 model requests, counted from the session's tool calls.

The first pass of M7, opening the site to agents, was one Claude Code session (claude-opus-5-5) on November 24 and 25, 2026, from Jason's brief. It saved the brief, wrote `tools/build_agent_pages.py` and the pages it writes (the About page as Markdown, the data dictionary, the runs and each run's README and summary, the districts, the month and `llms-full.txt`), `llms.txt` from Jason's draft, the head tags and JSON-LD, the data license and citation, `robots.txt` and `_headers`, and Copy for AI in the viewer and the explorer, and, at Jason's request, a visible For agents link on every page. It extended the link checker, added the agent pages' tests, and checked the five pages and the button in headless Chrome at desktop and phone widths, with three.js served locally because this container can't reach jsDelivr. It updated this README, the story and the decision log, and opened [#134](https://github.com/jas0nmjames/playground/pull/134) into `development`.

The public sharing pass was one Claude Code session (claude-opus-5-5) on November 25, 2026, from Jason's brief, saved as [`story/06-refinements/prompts/public-sharing-pass.md`](story/06-refinements/prompts/public-sharing-pass.md). It checked the brief's figures and record ids against the baseline day, shortened the intro, added the viewer's `#record=` and `#household=` links, took the lines about unfinished work out of the About page, the systems lens, `llms.txt` and the agent pages, wrote `tools/capture_readme_gifs.mjs` (with its own GIF encoder, since this Mac has no ffmpeg) and took the seven GIFs, rewrote this README around them, put Jason's words into the story and added 6.6 to 6.8 to the decision log. It checked the intro and every Try it link in headless Chrome at desktop and phone widths, and rebuilt the baseline day's households in a scratch run to explain one household's declined card, without changing any data. It opened [#138](https://github.com/jas0nmjames/playground/pull/138) into `development`.

The lens on laptops was one Claude Code session (claude-opus-5-5) on November 25, 2026, started by the public sharing pass. That pass had found that in the viewer the systems lens is 112 px narrower than the window, so at 1280 × 800 it fell under its 1,240 px breakpoint and stacked, cutting off three of its six layer buttons. Measuring every block in headless Chrome showed the same at 1366 × 768, where the lens kept three columns but its tools column ran past the frame. The session let the lens's side columns give way, so the three columns hold down to 1,100 px, and tightened the tools column's spacing when the lens is 720 px tall or less. It checked all six blocks at 1280 × 800 and 1366 × 768 in the viewer (every layer button in view, and a real pointer hover lifting each one), other desktop sizes, the standalone page, and 1024 px and phone widths (unchanged). It changed the 07 GIF's scene to lift all six layers, retook it, and opened [#139](https://github.com/jas0nmjames/playground/pull/139) into `development`, stacked on #138.

| Created | Tool | Model | Estimated energy consumption[^claude] | Estimated carbon emissions | Estimated water usage |
|---|---|---|---|---|---|
| November 16, 2026 | Claude app | claude-fable-5-2 | not measurable from here | — | — |
| November 2026 | Claude app (research, city design, first viewer, v3) | (unknown) | not measurable from here | — | — |
| November 17, 2026 | Claude Code | claude-opus-5-5 | 0.702 kWh | 0.271 kg CO₂ | 0.351 L |
| November 17, 2026 | Claude Code | claude-opus-5-5 | 0.108 kWh | 0.042 kg CO₂ | 0.054 L |
| November 17, 2026 | Claude Code | claude-opus-5-5 | 1.008 kWh | 0.389 kg CO₂ | 0.504 L |
| November 18, 2026 | Claude app (systems lens) | claude-opus-5-5 | 1.620 kWh | 0.625 kg CO₂ | 0.810 L |
| November 19, 2026 | Claude app (data explorer) | claude-opus-5-5 | 1.260 kWh | 0.486 kg CO₂ | 0.630 L |
| November 18–19, 2026 | Claude Code, cloud (v2 phases 0–2: simulator copy, targets, typed days, downloads) | claude-opus-5-5 | not measured | — | — |
| November 19, 2026 | Claude Code, cloud (tagging records with the lens's blocks) | claude-opus-5-5 | not measured | — | — |
| November 19–20, 2026 | Claude Code, on the Mac (v2 phase 2 home downloads; phase 3 batches C, I, J, P and R) | claude-opus-5-5 | not measured | — | — |
| November 20, 2026 | Claude Code (intro, About page, data links) | claude-opus-5-5 | 1.188 kWh | 0.459 kg CO₂ | 0.594 L |
| November 20, 2026 | Claude Code (rename to Medianville) | claude-opus-5-5 | 3.546 kWh | 1.369 kg CO₂ | 1.773 L |
| November 20, 2026 | Claude Code (phase 4: the month) | claude-opus-5-5 | 3.870 kWh | 1.494 kg CO₂ | 1.935 L |
| November 21, 2026 | Claude Code (phase 5: read and publish) | claude-opus-5-5 | 5.400 kWh | 2.084 kg CO₂ | 2.700 L |
| November 21, 2026 | Claude Code (phase 6: the lens's dead ends) | claude-opus-5-5 | 3.258 kWh | 1.258 kg CO₂ | 1.629 L |
| November 22, 2026 | Claude Code (polish pass) | claude-opus-5-5 | 2.160 kWh | 0.834 kg CO₂ | 1.080 L |
| November 22, 2026 | Claude Code (sources and docs review) | claude-opus-5-5 | 0.810 kWh | 0.313 kg CO₂ | 0.405 L |
| November 24, 2026 | Claude Code (milestones, story and archive; the playground's status and GitHub sync) | claude-opus-5-5 | 2.520 kWh | 0.973 kg CO₂ | 1.260 L |
| November 24–25, 2026 | Claude Code (M7 first pass: open to agents) | claude-opus-5-5 | 2.970 kWh | 1.146 kg CO₂ | 1.485 L |
| November 25, 2026 | Claude Code (public sharing pass: intro, README and GIFs) | claude-opus-5-5 | 2.700 kWh | 1.042 kg CO₂ | 1.350 L |
| November 25, 2026 | Claude Code (the systems lens on laptops) | claude-opus-5-5 | 1.260 kWh | 0.486 kg CO₂ | 0.630 L |
| **Total (countable)** | | | **34.380 kWh** | **13.271 kg CO₂** | **17.190 L** |

[^claude]: assuming 18 Wh per model API request; carbon at 0.386 kg CO₂ per kWh and water at 0.5 L per kWh, as across this playground; does not include estimate for foundation model training. The Claude Code rows are the three passes above: 39 and 6 requests measured in the session transcript, and 56 for the third, of which 41 were measured before this README was written and 15 are an estimate for the README, the commit, the pull request and the reply. The first pass was estimated at 32 requests when it shipped and measured at 39 afterwards. That's 101 requests in all; at the time of measuring, the session had used ≈ 24M tokens, about 97% of them cache reads. The phase 5 row is 300 requests: 285 measured in the session's transcript and its two reader agents' transcripts (deduplicated by message id; about 106M tokens, nearly all cache reads), and 15 estimated for the last commit, the pull request and the reply. The phase 6 row is 181 requests: 151 measured in the session's transcript and its three web-reading agents' transcripts (deduplicated by message id; about 42M tokens, 98% of them cache reads), and 30 estimated for the README, the commits, the pull request and the reply. The polish pass row is 120 requests: 104 measured in the session's transcript (deduplicated by message id; about 18M tokens, 98% of them cache reads), and 16 estimated for the README, the last commit and the reply. The sources and docs review is an estimate of about 45 requests, counted from the session's tool calls. The M7 first pass row is 165 requests: 157 measured in the session's transcript (deduplicated by message id; about 54M tokens, 98% of them cache reads), and 8 estimated for the last commit, the pull request's update and the reply. The public sharing pass row is 150 requests: 128 measured in the session's transcript (deduplicated by message id; about 34M tokens, 99% of them cache reads), and 22 estimated for the last edits, the commit, the pull request and the reply. The lens on laptops row is 70 requests: 55 measured in the session's transcript (deduplicated by message id; about 8.5M tokens, 97% of them cache reads), and 15 estimated for the README, the commits, the pull request and the reply.
