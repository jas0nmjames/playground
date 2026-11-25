Medianville is ready to share publicly. Shorten the intro, explain the features in the project README with GIFs, add "Try it" links, make the site describe only work done to date, and add my words on why I made it.

Repo: jas0nmjames/playground. Work in mapping-synthetic-transactions/. Branch off development and open one PR into development (never main; see CLAUDE.md). File it under M6 Refinements. Save this prompt word for word as story/06-refinements/prompts/public-sharing-pass.md.

Check every figure and record ID below against the data before using it. If the code or data contradicts this prompt, follow the repo and say so in the PR.

## 1. Intro modal
Replace the body copy with exactly this:

  [chip] Simulated city · no real people
  One day in Medianville
  Medianville is a fictitious American city of about 100,000 people. Built with publicly available research, it simulates representative days of financial life and beyond, including government services and unpaid labor. It shows the human goal behind each transaction and maps the surrounding societal contexts.
  [Enter the city]  [Explore the data]  About the project →
  By Jason James, built with Claude.

Keep the llms.txt line for agents, the loading state on the primary button, dismissal memory (same key), deep links skipping the modal, the About button, and all accessibility behaviour. Remove code that only filled the old copy's date and counts.

## 2. Only work done to date
Plans may stay in story/ and the decision log. The served pages and agent files must not describe unfinished or future work as part of the project. Known places:
- about/index.html: delete "It's paired with visits to real places around Atlanta for examples and stories."
- about/index.html: delete the "What's next" paragraph about a third version.
- about/index.html: delete the "Ten more are listed for later versions…" sentence.
- about/index.html: "They aren't drawn from Census microdata yet; that's planned for the third version." becomes "They aren't drawn from Census microdata."
- about/index.html, Limits: delete "The third version, drawn from Census microdata, redraws the households."
- systems-lens/index.html: "Loops are hypotheses for run 2 to test." becomes "Loops are hypotheses, not findings."
- systems-lens/index.html: "This loop is a hypothesis drawn for the prototype… Run 2's caused_by links…" becomes "This loop is a hypothesis, not a finding." First check the v2 and month run records; if a loop was tested, tell me before wording it.
- llms.txt: "No what-if scenarios are modeled yet." becomes "No what-if scenarios are modeled."
- agents/month.md says a check "was left for v3". Reword in the generator or its source so it states the gap without promising a version. Don't change any result.
Then rebuild with tools/build_agent_pages.py (agents/ and llms-full.txt). Search the served files again for other forward-looking claims (will, yet, planned, later, next, v3, run 2, visits) and list what you found and did.
In story/decisions.md §1.2, add a dated note that the real-place visits are planned and have not been made.

## 3. "Try it" links in the viewer
Already supported: ?intro=0, ?run=<run id>, #view=map, #lens=<block>/district[/<record>]. The explorer supports #records, #summary, #record-<id> and #household-<id>.
Add two to the root viewer (the intro's deep-link test already matches these names):
- #record=<record_id>: once the real day has loaded, seek to the record, pause and open its sheet.
- #household=<household_id>: open the household view, paused just after its last record of the day.
Unknown IDs are ignored without errors. Add nothing else. Pin ?run=v2-2027-03-03 on every link that names a record or household.

## 4. README
Keep the frontmatter and the existing history, run-locally, license, citation and environmental-impact sections. Replace the introductory and feature material with the following, merging rather than duplicating existing "For agents" text. GIFs live in readme-media/. Put a "Try it →" link under each feature.

~~~
# Medianville

Medianville is a fictitious American city of about 100,000 people. Built with publicly
available research, it simulates representative days of financial life and beyond,
including government services and unpaid labor. It shows the human goal behind each
transaction and maps the surrounding societal contexts.

**[Open the city](https://medianville.netlify.app/)** · Simulated city, no real people

[GIF 01-city]

## One household's day
This household starts March 3, 2027 with $295.04 in checking and $49 in cash. Car
insurance ($268.45) drafts at 1:46 a.m. At 11:23 a.m. the debit card is declined for
$36.84 of gas, so they pay cash. At 6:05 p.m. they give up on the week's groceries
($56.81): there isn't enough on hand or on any card.

[GIF 02-household]  [Try it]

## More than money
Government services and unpaid labor are records too. On the baseline day, more than one
record in four is a public service (40,071) or an unpaid job (13,234).
- A 56-year-old spends four hours caring for his wife when the home care aide misses the visit. [Try it]
- County EMS helps a 77-year-old up after a fall; the county levy covers the $448 cost. [Try it]
- A 59-year-old waits 71 minutes on the IRS phone line about a missing refund. [Try it]

[GIF 03-beyond-money]

## Why I made this
The private sector often focuses on dollars, cents and quarterly profitability. My history
and liberal arts background, and my MBA in sustainability with its triple bottom line, push
me to look wider, including at unpaid labor and government services.

I hope it gives researchers, teams and historians ideas about what large language models can
produce, and how to build richer views into the stories we tell.

This doesn't replace research with real people. It's a way to explore what public research
says and find questions worth checking.

## How it was made
A simulator produces the records. People, households, employers and bills come from a
seed, and each day is settled minute by minute against every household's money. Claude
Fable 5.2 wrote the first simulator and generated the first day. Claude Opus 5.5 wrote
v2, the data the site opens on, with rates set from 42 public datasets. Claude also
hand-wrote 800 detailed records (500 in v1, 300 in v2). Jason James had the idea, framed
it and made the design decisions; Claude built the viewers under his direction.

## The city
**Miniature and map.** Switch between a miniature town and a printed map (M). Turn, tilt
and zoom the miniature. Sound is off until you turn it on. [Try it: miniature] [Try it: map]

**Playback speed.** Live, or 1, 5 or 20 minutes a second. [GIF 04-speed] [Try it]

**Change the day.** The baseline Wednesday plus 18 other typed days of 2027, including a
winter storm, a heat wave, tax refunds and Social Security Wednesdays. [GIF 05-days]
[Try it: winter storm]

**Records and households.** Open a record to see who paid whom, how, whether it worked and
the job someone was trying to get done, then see the household's whole day. [Try it]

## Data explorer
Records, households, people, organizations and a summary, with filters, search, group-by
and CSV download. [GIF 06-explorer] [Try it]

## Systems lens
The lens builds on "societal context", which Donald Martin Jr. advocates for: people, places
and problems are shaped by shifting social, cultural, historical, political, economic and
environmental conditions. It maps one block per district, in six layers: today, economic,
political, built and natural, social and cultural, historical. The circumstances are
composites of documented US patterns, and the loops are hypotheses, not findings.
[GIF 07-lens] [Try it]

## For agents and LLMs
Start at [llms.txt](https://medianville.netlify.app/llms.txt). Plain-markdown pages cover
the method, data dictionary, runs and districts, and "Copy for AI" copies a record with
context. Data is CC BY 4.0; cite it as synthetic.

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
~~~

Links (base https://medianville.netlify.app/):
- Household: ?intro=0&run=v2-2027-03-03#household=H22924
- Caregiving, EMS, IRS: explorer/?run=v2-2027-03-03#record-R0077959, then R0201900, R0188947
- Miniature: ?intro=0 · Map: ?intro=0#view=map · Speed: ?intro=0
- Winter storm: ?intro=0&run=v2-2027-01-19
- Records and households: ?intro=0&run=v2-2027-03-03#record=R0093156
- Explorer: explorer/ · Lens: #lens=larkin/district

Every model credit anywhere in the folder must match the About page: Fable 5.2 for the first run, Opus 5.5 for v2. Search for "Fable" and "Opus" and fix any that don't.

## 5. GIFs
Read scripts/capture-media.mjs first and reuse its approach. Make one repeatable command that regenerates all seven from a local server (put Medianville-specific steps in tools/ if the shared script is generic).

| File | Steps | About |
|---|---|---|
| 01-city | Miniature playing around noon; switch to Map and back | 8 s |
| 02-household | H22924: declined gas R0093156, then the household view after 6:05 p.m. showing insurance R0008866, the decline, cash R0093554 and abandoned groceries R0160776 | 12 s |
| 03-beyond-money | Use the Activity chips to show only public services and unpaid work (confirm how they toggle) | 8 s |
| 04-speed | Live, 5 min/s, 20 min/s; scrub the timeline | 8 s |
| 05-days | Day menu, choose the winter storm; trim the load wait | 6 s |
| 06-explorer | Filter to "Didn't work", open one record | 8 s |
| 07-lens | From H22924, open the lens and lift two or three layers | 10 s |

- Capture at 1280×800; output 800 px wide, 10–12 fps, looping. Aim under 5 MB each; 10 MB is the ceiling.
- Skip the intro. Show a visible cursor or click ring.
- Look at frames from every GIF before committing: right content, legible text, miniature rendering properly.
- Give each descriptive alt text. The surrounding text must make sense without the GIF.
- No site page should load the GIFs, so Netlify bandwidth stays as it is.

## 6. My words in story/
Each milestone README, and next-mining-for-projects, has a "## What I wanted" heading with a TODO(Jason) line. Replace the TODO line with the paragraph below, exactly. Don't rewrite or expand it, and don't add employer names. If something in these words doesn't match the repo, tell me instead of editing them. For 05-more-time, check that a visit downloads only the days it opens.

00-the-idea
> As a UX product designer, I want my work tied to real human context. Formal research does that, but I can't publish it, especially coming from a highly regulated industry like banking. So I wanted a fictitious world, something like SimCity or RollerCoaster Tycoon, but based in reality through secondary research. I studied history, and I'm used to looking closely at people's lives to find larger themes and stories about society.

01-one-day
> With Fable 5.2 newly released, I wanted to try a less common use of it from a design perspective. Instead of generating a richer and richer interface, I wanted to generate the transactions themselves: an unorthodox idea, a representative city's financial life that we could get real insight from.

02-miniature-and-map
> The night map was what Claude generated by default, but it looked more like a constellation or a picture of the universe than a representative American city. It wasn't a good vehicle for this data. The miniature and the map are ways to bring the city to life.

03-grounding-in-evidence
> I wanted publicly available research to become something you can explore, without relying on private data that couldn't be shared.

04-the-refined-city
> I didn't want a narrow view of a financial transaction. A person is trying to accomplish a goal, and I wanted to show how systems, society and history affect it. That brings my humanities background to a financial industry problem. The data tables and clear documentation help make it feel real.

05-more-time
> Financial activity isn't the same from one day to the next, something Claude reminded me of. Pulling in more simulated days lets us reach different conclusions. It also mattered that the experience stayed usable, both as an interface and as a build: rather than sending every visitor hundreds of megabytes at once, the site downloads each day only when you open it.

06-refinements
No paragraph. Delete the "## What I wanted" heading and its TODO line, and keep everything else.

07-open-to-agents
> The city is data-heavy, so opening it to AI agents made sense, especially as interfaces change. I'd been to a Figma book talk on *Sentient Design* and to blackcomputeHER.org's 2025 AI Summit, [Reimagining AI in Our Own Image](https://blackcomputeher.org/ai-summit/), where I particularly gained a lot from hearing Paz Perez speak and Donald Martin Jr. advocate for "societal context". I'm interested in Paz's work on model design and context, and agent access is a tangible way to start thinking about how to design around models, agents and their behavior.

next-mining-for-projects
> I want product and design teams to be able to mine and explore the city as a thinking partner.

If about/ names this conference, use the same name there and link it to the same page.

## 7. Log, checks and report
- story/decisions.md, section 6, next numbers, dated 2026-11-25, Who: Jason: (a) shorter intro, superseding part of 6.1 and keeping a one-line credit; (b) features explained in the README with GIFs, not an in-app welcome wizard; (c) the site describes only work done to date.
- Add this session's row to the README's environmental-impact table.
- pytest sim/tests and python3 tools/check_links.py pass. Nothing in sim/ or data/ changes.
- In headless Chrome at desktop and 390 px: new intro fits, every Try it link lands where it says (against the local server), no console errors.

Ask me before the PR:
- List any TODO(Jason) lines still left in story/ after section 6. Don't write them for me.

Report only, no data changes:
- Household H06551 (v2, March 3) has about $41k in household checking, yet its debit card is declined for insufficient funds (R0171548). It has two wallets. Say whether per-wallet balances explain it.

In the PR body: GIF sizes, the forward-looking lines found, any figure that didn't match, and a note that new links work on the live site only after I merge to main.
