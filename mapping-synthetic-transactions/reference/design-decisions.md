# Medianville: design decision log

Started 2026-11-20. One place for the decisions behind the project, gathered from the dated docs in this project, so the reasoning can be read, criticized or reversed without digging through ten files. It goes into the repo as `reference/design-decisions.md`, and the site's About page links to it.

**Each entry:** what was decided, why, what else was considered, and what it costs. **Who** says whose call it was: *Jason* (his direction or choice), *Build* (a method choice Claude made while building, recorded in the build notes), or *Jason, on a proposal* (Claude proposed it and Jason chose it). **Source** is the project doc that records it. Project docs written before the rename keep the old name, Halvern, in their file names; the ones copied into `reference/` were renamed with the city on 2026-11-20.

New decisions go at the end of their section with a date. A reversed decision stays in the log, marked *Superseded* with a pointer to the new entry.

---

## 1. The idea and its framing

### 1.1 Every transaction is a job to be done
- **Decided:** A record is anything someone did to get something done, not only money changing hands: a purchase, a bill, a benefit deposit, a form, a wait, a declined card, a wasted trip, an hour of unpaid care. Each record says what the job was, who paid, who else paid, what it cost in time and effort, and whether it worked.
- **Why:** The project exists to find small, practical projects that improve daily life at the margins. At the margins, the frustration is often in the non-monetary jobs and the failures, which a spending dataset would leave out.
- **Who:** Jason (the project's premise and title). **When:** before 2026-11-16. **Source:** `medianville-transaction-generator-prompt.md`.

### 1.2 A synthetic city, not a real one
- **Decided:** Build a fictional city weighted to the whole country, and visit real places in the Atlanta area for examples and anecdotes.
- **Why:** The starting question was which American town is most like America. The published rankings (FiveThirtyEight, WalletHub) each pick a different winner, and every real metro that scores well underweights rural and small-town life, where many margin problems are. None of them measures industry mix.
- **Considered:** A real test-market city (Columbus, Indianapolis); "a synthetic Indianapolis".
- **Cost:** The city can't be checked against a real place. Real-world grounding has to come from national data and field visits.
- **Who:** Jason, on a proposal. **When:** 2026-11-16.

### 1.3 Six districts in national proportions
- **Decided:** Downtown, inner suburbs, outer suburbs, a satellite city, a rural town and open country, sized so the rural share and drive distances come out at national rates.
- **Who:** Jason, on a proposal. **Source:** generator prompt.

### 1.4 A systems lens alongside the city
- **Decided:** Show the circumstances that shape each job (social, cultural, historical, political, economic and environmental) and the feedback loops between jobs, as well as the jobs themselves.
- **Why:** After Donald Martin Jr.'s talk at the Reimagining AI conference (2025) and his definition of societal context. A day of transactions shows what happened. The lens is for showing why it keeps happening to the same people.
- **Who:** Jason. **When:** 2026-11-18. **Source:** `halvern-systems-lens-prototypes.md`.

### 1.5 The name: Medianville
- **Decided:** The city was renamed from Halvern to Medianville, a nod to the Lynds' *Middletown* (1929) and the "typical town" studies that followed it.
- **Why:** The name should say what the city is for. Unlike the Lynds' Muncie, Medianville's typicality comes from weighting, not from leaving groups out. The README carries a naming note.
- **Considered:** Renaming right away, or after the v2 data was packaged. It was first held until after v2 so it would happen only once, across everything. Renaming between phase 3 and packaging still does it once, and before any v2 run or hand-written record exists, so none of them has to be renamed afterwards.
- **Who:** Jason. **When:** decided 2026-11-19; moved up on 2026-11-20 to run right after phase 3, so the v2 run and its hand-written records are made under the new name; done in [pull request #77](https://github.com/jas0nmjames/playground/pull/77). **Source:** `medianville-data-update-plan.md`, phase 3b.
- **Kept:** The frozen v1 run (`data/halvern_2027-03-03.zip` and `data/halvern/`) and the archived viewers (`v1/` and `v3/`) keep Halvern, as a record of what shipped. Past results in `sim/evidence/results/` keep it too. Decided 2026-11-20.

### 1.6 A renamed copy of v1 for the latest pages
- **Decided:** `tools/rename_run.py` writes `data/medianville_2027-03-03.zip` from the frozen v1 zip with only the name changed: the case map is applied to every file's contents and paths, and every other byte, timestamp and permission is kept. The latest viewer, the explorer and the systems lens load the copy; the archived viewers keep loading the original.
- **Why:** Until v2 is packaged, the latest pages show v1's records, and those name the city's own places (its transit agency, its savings bank, its hospital) under the old name. Without the copy, every record sheet in the renamed pages would say the old name.
- **Considered:** Renaming the names in each page as the records load, which every page would have to repeat; waiting for v2, which leaves the old name on screen until then.
- **Cost:** A second 16 MB zip in the repo, and a copy that has to be kept honest. `sim/tests/test_rename_run.py` checks that mapping the copy back gives every file of the v1 zip byte for byte, in the same order, with the same timestamps and permissions. When v2 ships, the latest pages move to `data/runs/v2/` and the copy can go.
- **Who:** Jason. **When:** 2026-11-20. **Source:** `medianville-data-update-plan.md`, phase 3b.

### 1.7 Carried runs leave the one-day path untouched
- **Decided:** Everything that carries from one day to the next lives in `sim/medianville_sim/carry.py` and runs only in a carried run (`--days` above 1, `--state-in`, or `--carry`). Every hook elsewhere is guarded before any random draw, decisions made only in carried runs draw from a stream of their own, and records keep their 31 columns. Chains that cross days go in a new `links.csv` beside each day's records: the chain, its step, and the earlier record (date and record id) it follows from.
- **Why:** The brief: the one-day path must not change. Each commit was rerun over the typed-day year and `v2_rates_typed_days_2027` came out byte for byte; `tests/test_carry.py` pins the 10% one-day run's hashes. Record ids start again each day, so a cross-day link has to name the date too, and a separate file keeps the records' schema the same for every viewer.
- **Considered:** A new column in `records.csv` (would change every one-day file); a burn-in of simulated February days (the month would not open on the SCF-matched balances).
- **Cost:** A carried day and a one-day run of the same date differ, by design. Two code paths to keep in step.
- **Who:** Jason (the rule), Build (the method). **When:** 2026-11-20. **Source:** `medianville-data-update-plan.md`, phase 4.

### 1.8 The month opens on March 1 with what was already in motion
- **Decided:** The month starts from March 1's opening balances. It inherits, without records, what earlier days would have set going: shutoff notices sent in the ten days before, the payday loans and title loans already out (in steady state), and the tax season so far (who has filed or been refunded). The retry queue and overdraft chains start empty.
- **Why:** Without the inheritance, the first week would have no disconnections and no loans coming due. A burn-in of February days would drift the opening balances away from the SCF match.
- **Cost:** The first few days run a little light on retries and overdraft chains.
- **Who:** Build. **When:** 2026-11-20.

### 1.9 Retrying unpaid bills, and setting money aside for them
- **Decided:** A bill not paid in full on its due day joins a retry queue. Lenders, card issuers, insurers and schools re-present a bounced autopay twice (3, then 5 business days later; NACHA allows two). Landlords and utilities do not: the household pays by hand on the next day money comes in, with part payments for rent and utilities and the minimum for a card. Merchants retry a declined card 2 and 5 days later, then the subscription lapses. Each retry carries the returned-payment fee and, after the grace period, the late fee from the bill's terms. On the morning a bill is due, a carried household moves money from savings for it, as far as savings go, and the move is recorded.
- **Why:** A one-day run's opening balances already include the money set aside for that day's autopays (`finance.build_finance`); without the same habit on later days, bills failed for want of the build-time top-up, and 39% of households missed a bill in March. With it, the share of adults with a bill still unpaid on their own account on March 31 lands near SHED 2025's 15.2% of adults who cannot pay all of this month's bills (`sources/tools/shed_bills.py`). It is read per adult, as SHED asks it; the share of households runs higher, since any one account in the household counts.
- **Cost:** The schedules are common practice, not counted. SHED's EF5C is read from its answers, because the codebook's text could not be extracted.
- **Who:** Build. **When:** 2026-11-20.

### 1.10 Shutoffs come only from notice timers
- **Decided:** In a carried run a shutoff notice starts a timer. The day before the date the household pays (85% of those who can), sets up a payment plan (70% of those who can make a down payment), or asks the community action agency for crisis help (pledged four times in ten); otherwise a crew disconnects on a Monday-to-Thursday business day at or soon after the date. Reconnection takes the past-due amount or part of it, a $35-75 fee, a call or a trip to a payment counter, and the next business day; gas needs someone home for a four-hour window.
- **Why:** The notice and shutoff rates (T16, T05) are kept, and the share of notices that end in a shutoff falls out of the household's money. The response shares are fitted to about one notice in four on the full-city month (the first fit, with plans at 55% and pledges at 30%, shut off 35% of notices and ran 14.6 disconnections a day); EIA-112 2024's reconnection shares (85% electric, 71% gas) check the other end.
- **Cost:** The response shares are estimates fitted on the month, not measured.
- **Who:** Build. **When:** 2026-11-20.

### 1.11 Overdraft chains, and concentration left as measured
- **Decided:** Carried, an overdrawn account stays below zero until money comes in, so one overdraft leads to more. Banks cap overdraft fees at three a day, cover no item past $400 below zero, and charge an extended fee after a week; someone already below zero tries a card that will not clear 10% of the time, against 35% in a one-day run. A rent payment missed within two weeks of a fee joins the overdraft's chain. Concentration is measured, not forced.
- **Why:** Without a total limit, the one-day rule (any item up to $260 short) let accounts sink without end and the month ran near 290 fees a day; with a $500 limit the full-city month still ran 187.5. The $400 limit and the 10% habit were fitted to T01 on the full-city month. The CFPB's 9% of accounts paying 79% of fees cannot be reached: only the 6.6% of accounts opted in to coverage can overdraw, and that is set by the one-day population.
- **Considered:** Letting banks pay ACH and recurring items into overdraft for accounts without the opt-in (Reg E's opt-in covers only ATM and one-time card payments), which would spread fees; it changes the one-day path, so it is left to Jason (plan section 9, item 6).
- **Cost:** Fees in the month fall on far fewer accounts than in life.
- **Who:** Build; the open question is Jason's. **When:** 2026-11-20.

### 1.12 Payday loans as sequences, counted with their renewals
- **Decided:** Payday and online loans sit in a loan book, each due on the borrower's first payday a week or more away. A first loan is meant to be repaid 38% of the time, renewed 57% and defaulted 5%; later ones are renewed 84%, after CFPB's 2014 data point. What the account holds can turn a repayment into a renewal and a renewal into a bounce. A bounced loan is re-presented twice, then goes to collections. New sequences start at 1/4.56 of the one-day rate, and T02 is read in the month as loans plus renewals. Title loans carry too: rollovers pay the fee again, a missed payment raises the repossession risk, and a repossessed car stays gone.
- **Why:** The one-day draws of loans and repayments are unrelated to each other. The California and Texas reports behind T02 count loans and refinances together, and CFPB's sequence shape reproduces its 80% renewal share and long tail.
- **Cost:** Repaying and borrowing again the same day (common where rollovers are banned) is folded into renewals.
- **Who:** Build. **When:** 2026-11-20.

### 1.13 One refund a season, SNAP that runs down, and surplus moved to savings
- **Decided:** In a carried run each account gets one federal and one state refund a season and each household files once. SNAP shopping comes more often the more of the month's benefit is left. On a day money comes in, an account above twice its opening balance plus $500 moves the excess over 1.5 times the opening balance to savings, recorded as a transfer.
- **Why:** Drawn fresh each day, refunds paid the same filers again and again (about $2,200 per ALICE household in a test March). SNAP was left a fifth unspent at month's end. And because the one-day simulator sets spending by counts and shares rather than dollars, households above ALICE take in more than they spend, so checking climbed about $3,400 a month instead of following the pay calendar.
- **Cost:** The SNAP pace and the sweep are estimates; the sweep hides the under-spending in savings rather than fixing it, which waits for v3's spending model.
- **Who:** Build. **When:** 2026-11-20.

### 1.14 Weekly hours swing for hourly and gig workers
- **Decided:** Each hourly or gig worker gets a weekly hours factor (lognormal, mean 1; standard deviation .22 for variable schedules, .12 for other part-timers, .38 for gig work; each week correlated about .44 with the one before). It scales the days worked that week, the paycheck for the weeks it covers, and gig earnings.
- **Why:** The brief asked for week-to-week income volatility from SIPP or the JPMorgan Chase Institute if downloaded. Neither was (`sources/manifest.csv`: to_fetch), so the sizes are labeled estimates.
- **Cost:** Estimates until SIPP or JPMC figures are downloaded.
- **Who:** Build. **When:** 2026-11-20.

### 1.15 The month ships as a Release bundle, not on the site
- **Decided:** The March 2027 month is packed by `tools/pack_month.py` into `data/medianville_2027-03_month.zip` (gitignored): each day's tables and `links.csv`, the last day's carried state, the month's summary and checks, and a `SHA256SUMS` file. It goes into the GitHub Release `medianville-v2-month-2027-03`, which Jason creates. The repo keeps only the run record, the month's `summary.md` and `evidence_checks.md`; the README links the Release as a download not needed to use the site.
- **Why:** At about half a gigabyte it is too big for the repo and the Pages site, and visitors should never download it. The zip is built the same way every time (sorted entries, fixed timestamps, fixed permissions, deflate level 9), so a rebuild with the same Python and zlib gives the same SHA-256, and `SHA256SUMS` compares the contents even when zlib differs.
- **Who:** Jason (where it lives), Build (the format). **When:** 2026-11-20. **Source:** `reference/medianville-2027-03-month-run-record.md`.

---

## 2. Method: how the data is made

### 2.1 Simulate, don't write
- **Decided:** Code generates the population, the finances and the day. The model writes only the job statements, the text templates and 500 records by hand.
- **Why:** No model can write 200,000 consistent records by hand. Money wouldn't reconcile, and people would be in two places at once.
- **Who:** Build. **When:** 2026-11-16. **Source:** `medianville-build-approach.md`.

### 2.2 Settle the day in time order against real wallets
- **Decided:** Every action goes into one queue ordered by minute and is settled against the household's balance.
- **Why:** That's what makes a declined card at 5 p.m. depend on a bill that drafted at 2 a.m. Cascades are the point of the project.
- **Who:** Build. **Source:** build approach.

### 2.3 Calibrate to published anchors, and label every estimate
- **Decided:** Calibrate to a fixed set of targets: about 100,000 residents, the BLS industry mix, 43 payments per adult per month, a 14% cash share, 63% of adults able to cover a $400 emergency, 4 in 10 households below the ALICE threshold, and the Consumer Expenditure Survey spending order. Every figure that isn't derived from an anchor goes in `assumptions.csv` with a reason.
- **Why:** A synthetic city can only be trusted where it can be checked.
- **Who:** Jason, on a proposal (the generator prompt). **Source:** run record.

### 2.4 Real federal names, invented local ones
- **Decided:** The IRS, Treasury, Medicare, SNAP and the Postal Service keep their real names. Every person, business, agency, church and street is invented.
- **Why:** The program rules are real and national, and the jobs make no sense without them. Local names would point at real people and places.
- **Who:** Build, reconciling two rules in the prompt. **Source:** build approach.

### 2.5 Freeze the simulator before hand-writing
- **Decided:** No change to the simulator once hand-written text exists. Later fixes are limited to text, and known problems are listed rather than fixed.
- **Why:** Any population change redraws the random numbers and the record ids, and then the 500 hand-written records land on the wrong rows.
- **Cost:** Some known oddities stay in v1: odd employer and occupation pairs, long errand trips, zero marriages and divorces.
- **Who:** Build. **Source:** build approach.

### 2.6 Read a sample closely, as a test
- **Decided:** Reading 500 records one at a time counts as a validation step, alongside the automated checks.
- **Why:** It caught what the numeric checks passed: union dues paid to a charity, a 91-year-old schoolteacher, "cash only" text on a debit purchase.
- **Next time:** Do it earlier, on a smaller sample, and add a second reader that hasn't seen the code.
- **Who:** Build. **Source:** build approach.

### 2.7 Keep real and synthetic apart
- **Decided:** No real quote or real person ever goes into a record. Real evidence enters only as numbers (targets, rates) and as links by job category, friction and household type.
- **Why:** Putting a real person's words in a fictional resident's mouth would be fabrication, and it would make the synthetic data look more real than it is.
- **Who:** Jason, on a proposal. **When:** 2026-11-17. **Source:** `halvern-human-evidence-research-prompt.md`, data update plan section 2.

### 2.8 Only strong evidence sets a rate
- **Decided:** Only evidence graded A or B moves a rate in the simulator. Weaker evidence can add job kinds and texture, but not frequencies.
- **Who:** Jason, on a proposal. **When:** 2026-11-18. **Source:** data update plan.

### 2.9 Past one day: typical days first, then a month
- **Decided:** After the baseline day, run a weighted set of 10 to 12 typical days that stand for a year, then one continuous month with balances carried forward.
- **Why:** One Wednesday can't balance annual spending shares. Rare events are too noisy to rank, and the most promising problems play out across days.
- **Who:** Jason, on a proposal. **When:** 2026-11-18. **Source:** data update plan section 4.

### 2.10 Same people for v2, real households in v3
- **Decided (recommended; confirm):** v2 keeps v1's population so before-and-after comparisons stay clean. Drawing real household structures from ACS microdata waits for v3.
- **Note:** v1's households are built by rule to match national shares. They aren't drawn from ACS microdata, so site copy shouldn't say they are.
- **Source:** data update plan section 9.

### 2.11 Fix what v2 broke and what the records say wrong; leave the people for v3
- **Decided:** Before the freeze, fix the one problem v2 made worse (owners' housing costs drawn apart from income), the records that don't add up or don't fit (claims, practices, invoices, payers, fees, waits), and text that doesn't fit the person or place. Leave the population's problems (SSI and Medicaid against income, coverage against eligibility, $0-income rent, jobs tied to the wrong employers, long trips) as v2's known limits.
- **Why:** The fixes change no one's identity, so 2.10's before-and-after comparison holds, and every typed-day target stayed in range after them. The population's problems are v1's and need the population redrawn, which v3 does from microdata anyway.
- **Considered:** Fixing the population's problems now as well (breaks comparability and means retuning); freezing as it was (keeps a regression v2 introduced).
- **Cost:** v2 still shows SSI where it couldn't be paid, refundable credits on high incomes and some 60-80 mile trips. The month was rebuilt, and its Release asset has to be replaced.
- **Who:** Jason, on a proposal. **When:** 2026-11-21. **Source:** `reference/medianville-v2-close-reading.md`.

### 2.12 Two readers, and a second reader for the hand-written text
- **Decided:** The close reading had two readers for 200 records: Claude Code, which built the simulator and then measured each suspicion across the whole day, and a separate agent that saw only the record cards. After the freeze, 300 records were hand-written (40% from the job kinds new or changed since v1, the rest stratified), and a second reader that had not seen the code checked each one against its own fields.
- **Why:** 2.6's "next time": a reader who knows the code reads past what it expects. The outside reader found the $380 rent floor and the ignored travel time, which the first reader had missed.
- **Who:** Build, following 2.6. **When:** 2026-11-21. **Source:** close reading; `sim/detail_parts/`.

---

## 3. The viewer: how the day is shown

### 3.1 Three visual directions, prototyped, then Tabletop
- **Decided:** Of three briefs (Tiles, an isometric pixel city; Tabletop, a tilt-shift miniature; and Six Streets, a cut-paper cross-section), the Tabletop look was chosen. It was then revised with Tiles' range of buildings, flight-path arcs instead of flipping discs, a range of skin tones on the figures and softer shapes.
- **Why:** It had the strongest sense of a real place. Tiles and Six Streets each had a part worth keeping: building variety, and a per-district failure count.
- **Who:** Jason. **When:** 2026-11-17. **Source:** `halvern-visual-directions-prototypes.md`.

### 3.2 Two views of one city: Miniature and Map
- **Decided:** Two views of the same city: the Miniature, and an invented quadrangle map sheet. They share centre, zoom, records, filters and selection, and the M key switches between them.
- **Why:** The Miniature makes the city feel lived in. The Map makes places and distance readable.
- **Who:** Jason. **When:** 2026-11-17. **Source:** `halvern-two-views-refinement-prompt.md`.

### 3.3 One record language across both views
- **Decided:** Each record kind gets a colour, a line pattern and a head shape: purchase amber with a circle, income green with a diamond, bill blue dashes with a square, unpaid work short dashes with a ring, and a failure plum, stopping halfway at an ×.
- **Why:** Pattern and shape carry the type as well as colour, so the record kind still reads for colour-blind viewers (checked against Machado 2009 simulations).
- **Source:** visual directions prototypes.

### 3.4 Failures are never sampled
- **Decided:** At any zoom or speed, every failure is drawn. Failure pins are one per place with a count, so they don't pile up into clutter.
- **Why:** Failures are what the project is looking for.
- **Source:** visual directions briefs and prototypes.

### 3.5 A finance-app interface
- **Decided:** Figtree with tabular figures, summary tiles, an Activity feed with signed amounts, transaction sheets and a timeline histogram, with a "Simulated city · no real people" chip in the header.
- **Why:** Most people already know how to read a banking app. The chip is there so no one mistakes the records for real people.
- **Source:** visual directions prototypes.

### 3.6 A photographic miniature, without lens blur
- **Decided:** Keep the Light, Surface and Horizon iterations (filmic tone, sun and sky, contact shadows, night lights, materials, street detail, land past the board). Drop the tilted-plane lens blur. Add turning and tilting with mouse, touch and keys.
- **Who:** Jason. **When:** 2026-11-19. **Source:** `halvern-miniature-realism-lab.md`.

### 3.7 Sound: off by default, Mix A
- **Decided:** Sound starts off. There are two layers: ambience for realism, and records as sound (a pluck pitched by record kind, a low thud for anything not completed, and a pluck cloud above 12 records a second). Ambience never scales with playback speed. The background stays low and the separate sounds stay up.
- **Who:** Jason. **When:** 2026-11-20. **Source:** `halvern-sound-lab.md`.

### 3.8 The real day preloaded
- **Decided:** Every page loads the run from the repo when it opens. There's no upload step, and a placeholder day plays only while the file downloads.
- **Who:** Jason. **Source:** `halvern-in-motion-viewer.md`.

---

## 4. The systems lens

### 4.1 Exploded view; The Works and Section dropped
- **Decided:** The lens is an exploded view: six aligned layers of the same blocks, with threads from a record down to what shaped it. The Section view folds into it (how slowly each layer changes). The Works, which drew one household as plumbing, is dropped.
- **Why:** Stacked layers show how circumstances pile up in the same places, such as a redline, a highway, missing banks and an exhaust zone on the same squares. The plumbing tied an abstract model to pipes the city doesn't have.
- **Who:** Jason. **When:** 2026-11-18. **Source:** systems lens prototypes.

### 4.2 "What if" waits for real model runs
- **Decided:** No button to remove a circumstance until the circumstances drive the simulator. Then a "what if" becomes a second run with the same seed and one setting changed.
- **Why:** Today the links between records and circumstances are drawn by hand. A remove button would show an illustration as if it were a model result.
- **Who:** Jason, on a proposal. **When:** 2026-11-18. **Source:** systems lens prototypes.

### 4.3 One visual system, with Biesty in the structure only
- **Decided:** The lens uses the viewer's design system. Stephen Biesty's influence survives in the structure (exploded layers, callouts with leader lines), not in an ink-and-watercolour rendering.
- **Who:** Jason. **When:** 2026-11-18.

### 4.4 The lens as an overlay on the city
- **Decided:** A Map | Miniature switch, opening on Miniature, plus a separate Systems lens toggle (L). The lens grows out of a record's Details rail. Playback pauses, and Back to the city or Esc returns to the same record.
- **Considered:** The lens as a third view in the switch (option A on the IA canvas).
- **Who:** Jason. **When:** 2026-11-19. **Source:** `halvern-mapped-blocks.md`.

### 4.5 One mapped block per district, from one file
- **Decided:** One composite block per district. `systems-lens/blocks.json` is the single source: the lens draws from it, and the simulator tags records from it after the day without drawing any random numbers.
- **Cost:** The circumstances and figures are Claude-drafted composites of documented US patterns. They're labelled composite on screen and are waiting for Jason's review.
- **Source:** mapped blocks.

### 4.6 A district tier, so no record is a dead end
- **Decided:** Each mapped block also carries circumstances true across its whole district (`"scope": "district"`) and a district loop (`D1`, opened by `districtStart`). A record or household off the mapped blocks opens its district's block in district mode: the district tier is the story, each with an "Across" pill naming the district, the block's own circumstances fold away, and the bar above the lens says the record is from elsewhere in the district. The explorer links to the lens by the same rules, and its "Lens" filter becomes "Lens tags".
- **Why:** About 93% of records ended at a disabled "Not mapped yet" row. A district tier is honest about scale: it says what holds across the district without implying the record happened on the block.
- **Also decided:** Seasonal guest workers in open country go on the political layer, so every district has a political circumstance. The social layer stays empty downtown, in the satellite city and in the rural town for now.
- **Cost:** Display content only: no simulator change, no new or changed patterns or select rules, so every published run's tags stay valid. The district circumstances are Claude-drafted from the human-evidence report and national history, with figures checked against their sources; they wait for Jason's review like the blocks.
- **Who:** Jason. **When:** 2026-11-21. **Source:** `medianville-phase6-lens-dead-ends-handoff.md` and its district history addendum.

---

## 5. Data access and the repo

### 5.1 A separate data explorer
- **Decided:** A table-based explorer on its own page, with filters, search, group-by, detail sheets and CSV download. It isn't a Claude artifact.
- **Why:** Browsing the records directly is a different task from watching the day. An artifact can't fetch from GitHub Pages, so it would have to carry the 16 MB zip itself.
- **Source:** `halvern-data-explorer.md`.

### 5.2 Latest viewer at the root, archives frozen
- **Decided:** The latest viewer lives at the folder root, v1 (the night map) and v3 (as first shipped) are frozen archives, and no viewer v2 shipped.
- **Who:** Jason. **When:** 2026-11-20. **Source:** `halvern-integration-plan.md`.

### 5.3 Design labs stay in the project
- **Decided:** Design labs happen as artifacts in this project, and nothing reaches the repo on its own. Work merges into `development` first, and Jason promotes to `main`.
- **Source:** integration plan.

### 5.4 Days chosen from a manifest, each its own link
- **Decided:** Both viewers read `data/runs/manifest.json` through `runs.js`, open its default run (v2's baseline day) and list every run, v1 included, in a day menu. Choosing a day reloads the page with `?run=<id>`, and the link to the other viewer carries it. Without the manifest the pages load v1's zip, as before.
- **Why:** A reload gives every day its own address and avoids resetting a loaded day in place. A manifest lets new runs ship without touching the pages.
- **Who:** Build, on the plan's section 7. **When:** 2026-11-21.

### 5.5 The typed-day zips go in the repo, once
- **Decided:** The baseline day and the 18 typed days are committed as `data/runs/v2/medianville_<date>.zip` (about 280 MB together), only after the simulator was frozen and the hand-written text merged.
- **Why:** The site must serve them (Pages doesn't serve Git LFS), and a zip committed twice stays in the history twice.
- **Cost:** The repository grows by about 280 MB. The month stays a Release download (1.15).
- **Who:** Jason (plan section 7), Build (when). **When:** 2026-11-21.

---

## 6. Explaining the project (2026-11-20)

### 6.1 A first-visit intro overlay
- **Decided:** A dismissible overlay on first visit says what the city is, the goal, how it was made and who made it. It's remembered once dismissed, reopened from an About button, and skipped by deep links. It doubles as the loading moment.
- **Who:** Jason.

### 6.2 Plain credit, both ways
- **Decided:** The overlay and the About page say plainly what Claude did (wrote the simulator, generated the day, hand-wrote 500 records, built the viewers) and what Jason did (the idea and where it came from, the framing, and the direction and decisions throughout).
- **Who:** Jason.

### 6.3 About gets its own page
- **Decided:** `about/` is a page of its own, linked from the overlay, the viewer header and the explorer. It covers the goal, the origin, the method, the data sources, what's real and what isn't, the limits and the credits.
- **Who:** Jason.

### 6.4 The decision log is linked, not shown
- **Decided:** This log lives in the docs and the repo. The About page links to it but doesn't reproduce it.
- **Who:** Jason, on a proposal.

### 6.5 Links to the data explorer
- **Decided:** "Data" goes in the viewer header (not in the view switch, since the explorer is a different page). The overlay carries a secondary button, and each record's Details rail gets an "Open in data explorer" link to that record.
- **Who:** Jason, on a proposal.

## 7. Polish pass (2026-11-22)

### 7.1 The viewer opens in Live
- **Decided:** Playback starts at Live: the simulated day plays at the visitor's own time of day, one minute a minute. 1, 5 and 20 min/s are still one tap away. A visit at night opens on a quiet, dark city, and that's accepted.
- **Who:** Jason.

### 7.2 "Medianville", with a subtitle that says what it is
- **Decided:** The header reads **Medianville** with the subtitle "One day of transactions in a simulated American city", replacing "Medianville in Motion". Because the subtitle says "simulated", the header drops its "Simulated city · no real people" chip. The chip stays in the intro overlay and on About.
- **Who:** Jason, choosing from proposals.

### 7.3 "Sample day", not "placeholder" and "the real one"
- **Decided:** While the run downloads, the chip reads "Sample day · loading the full simulation". "The real one" suggested real data, and nothing on the page is real.
- **Who:** Jason, on a proposal.

### 7.4 The board turns while paused
- **Decided:** Turning, tilting and north-up ease into place even while playback is paused. Only the city's motion (records, vehicles, people) stops.
- **Who:** Jason.

### 7.5 The map sheet joins the viewer's look
- **Decided:** The Map keeps its topographic drawing (contours, cased roads, creek, symbols) but takes the viewer's design system: Figtree instead of Barlow Condensed, navy ink (`#0E1B2E`) instead of black, lighter paper (`#FBF9F4`), and the slate page behind the sheet instead of warm grey, with a thin border and soft shadow like the viewer's cards. The italic serif stays only for the creek's name, as on printed maps. Street names use an en space between words, since a plain space nearly vanishes at map sizes.
- **Decided:** The margin below the frame is laid out in clear columns: the legend on the left, the scale and north arrow on the right, and the title block under them. It starts a clear gap below the outer frame line, which used to run through the LEGEND heading.
- **Who:** Jason, on a proposal.
