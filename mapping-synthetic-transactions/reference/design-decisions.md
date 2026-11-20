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
- **Who:** Jason. **When:** decided 2026-11-19; moved up on 2026-11-20 to run right after phase 3, so the v2 run and its hand-written records are made under the new name; done in the `medianville-rename` pull request. **Source:** `medianville-data-update-plan.md`, phase 3b.
- **Kept:** The frozen v1 run (`data/halvern_2027-03-03.zip` and `data/halvern/`) and the archived viewers (`v1/` and `v3/`) keep Halvern, as a record of what shipped. Past results in `sim/evidence/results/` keep it too. Decided 2026-11-20.

### 1.6 A renamed copy of v1 for the latest pages
- **Decided:** `tools/rename_run.py` writes `data/medianville_2027-03-03.zip` from the frozen v1 zip with only the name changed: the case map is applied to every file's contents and paths, and every other byte, timestamp and permission is kept. The latest viewer, the explorer and the systems lens load the copy; the archived viewers keep loading the original.
- **Why:** Until v2 is packaged, the latest pages show v1's records, and those name the city's own places (its transit agency, its savings bank, its hospital) under the old name. Without the copy, every record sheet in the renamed pages would say the old name.
- **Considered:** Renaming the names in each page as the records load, which every page would have to repeat; waiting for v2, which leaves the old name on screen until then.
- **Cost:** A second 16 MB zip in the repo, and a copy that has to be kept honest. `sim/tests/test_rename_run.py` checks that mapping the copy back gives every file of the v1 zip byte for byte, in the same order, with the same timestamps and permissions. When v2 ships, the latest pages move to `data/runs/v2/` and the copy can go.
- **Who:** Jason. **When:** 2026-11-20. **Source:** `medianville-data-update-plan.md`, phase 3b.

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
