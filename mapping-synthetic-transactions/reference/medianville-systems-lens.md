# Medianville Systems Lens: design record

How the systems lens came about, which directions were tried, and what was decided. Built in the Claude app on November 18, 2026. The live page is [`systems-lens/`](../systems-lens/), and the three earlier directions are kept at [`systems-lens/directions.html`](../systems-lens/directions.html).

## Why

The lens brings two ways of reading into the project. The first is system dynamics: stocks, flows and feedback. The second is societal context, after Donald Martin Jr.'s definition: "the dynamic and complex collection of social, cultural, historical, political, economic and environmental circumstances that surround and shape people, places and problems." The animated views are already busy, so the lens is a separate view. In the full design you select a place or record in the city and choose **Cut away**. The city freezes and the lens opens on that record, and **Back to the city** returns to it. In this prototype, Back to the city only opens Miniature and Map; it doesn't carry the selection across yet.

## Content (placeholder, composite)

One district: Larkin Avenue, D2 Inner suburbs. Twelve circumstances, each tagged with one or more of Martin's six types, linked to nine of the day's records. Circumstances also rest on each other. For example, the 2009 branch closures rest on the 1938 appraisal map, and the missed bus rests on the 2019 Route 6 cut and the 1961 interstate spur. Every circumstance is an invented composite of documented US patterns, labeled that way on screen. The nine records are written for the prototype; they are not rows from `halvern_2027-03-03.zip`.

## Three directions

| Direction | Idea | Strength | Risk |
|---|---|---|---|
| 1. Section | The district sliced open, after Stephen Biesty's cross-sections. Records are numbered on the street; the layers below are ordered by how slowly they change. Selecting a record draws dashed lines down through every circumstance it rests on. | History reads physically as "underneath". | Little room for how things line up in space. |
| 2. Exploded view | Six aligned isometric plates of the same blocks. A column marks the same square on every plate, and lines drop from a record to what shaped it. | Shows what lines up: the redlined blocks, the highway, the missing banks and the exhaust zone fall on the same squares. | Dense. |
| 3. The Works | One household as plumbing (tanks, pipes, leaks, valves) with feedback loops and policy what-ifs. | The only direction that showed feedback and counterfactuals. | The plumbing literalism takes reading. |

## Decisions

- **The Works is dropped.** Drawing system-dynamics stocks and flows as realistic plumbing ties an abstract model to physical pipes the city doesn't have.
- **Exploded view is the direction.** A Section drawing beside the plates was tried and removed as too busy. What it showed, how slowly each layer changes and the full text of each circumstance, now lives on the plates as pace labels and callouts.
- **"What if" (removing a circumstance) waits for run 2.** Today the links between records and circumstances are written by hand, and the simulator doesn't use them. A remove button would present an illustration as a model result. In run 2, a what-if becomes a second run with the same seed and one `context.csv` setting changed, compared with the first.
- **The lens uses the Medianville in Motion design system,** not the Biesty ink-and-watercolor look of the first prototypes. Biesty survives in the structure (exploded plates, callouts with leader lines), not in the rendering.

## The page

- **Look.** The same system as v3: slate page (`#F3F5F8`), white surfaces, ink `#0E1B2E`, Figtree with tabular figures, 12 px corners and soft shadows, and Barlow Condensed for layer names, as on the map sheet. The header has the "Simulated city · no real people" chip and a Miniature | Map | Systems lens switch. Miniature and Map both open `v3/`. Record pins are solid record-type discs with white numbers, like feed icons, and loops are drawn in the action blue (`#1F5AF0`).
- **Layers.** The layers in the current story (the selection's chain plus the active loop) spread apart and get a blue dot in the layer list. The others collapse to slivers at half opacity with their labels hidden. Pointing at a layer in the list lifts it; selecting one shows it alone, and Show all layers or Esc brings the rest back.
- **Pace.** Each layer's label gives how fast it changes. Today changes by the minute, Economic over years, Political over decades, Built & natural and Social & cultural over generations, and Historical is bedrock that lasts a century.
- **Callouts.** For the selected story only, every circumstance gets a white card in a column to the right of the stack, with a leader line to its square. Each card shows its types, year, layer and full text, for example "1983 · Historical: Medianville Works closes: 1,900 union jobs gone." Circumstances outside the story keep short labels.
- **Today layer.** A small isometric town: houses, the Larkin Avenue shops, the church, warehouses on the old Works site, the highway trench and the creek, with the nine records pinned on the roofs.
- **Loops.** One at a time: R1 Fee spiral, R2 Rollover, R3 Time tax, B1 Circle buffer. Each is a closed curve through nodes on the layers they belong to, with arrowheads, + and − link signs, an R or B marker, and dotted "pushed by" arrows from circumstances on other layers. Every loop is a hypothesis for run 2 to test, and its sheet says so.
- **Details.** The right column is a sheet in v3's transaction style. A record shows a big amount (plum when it failed), status and type pills, the narrative, time, counterparty, kind and layer, and the circumstances that shaped it. A circumstance shows its types, body, when, layer and pace, what it rests on and what it shapes. A loop shows a numbered "How it runs" list with its signs, what pushes it, and where it shows up today.
- It opens on record 6 (1:05 p.m., payday loan renewed, $75 fee) with loop R2 drawn.

## Over the city, on six blocks (November 19, 2026)

The lens now opens over v3 instead of as its own page, and it reads the run.

- **Over the city.** The details rail widens into the lens; the record stays at the right edge, playback pauses, and Back to the city or Esc returns to the same record. The header has Map | Miniature plus a separate Systems lens toggle (L). `v3/#lens=<block>[/<pattern>[/<record>]]` links straight to a block, a pattern or a record, and `#view=map` or `#view=mini` picks the view.
- **One block per district.** `systems-lens/blocks.json` holds six composite blocks: Pelham Street (D1), Larkin Avenue (D2), Fox Hollow (D3), Mill Street in Ashford Mills (D4), Main Street in Dunmore (D5) and the Route 9 Crossroads (D6). Each has eight to twelve circumstances on the five lower layers, six to nine patterns pinned on the Today layer, two to four loops, and the drawing for its plates, in a small vocabulary of areas, lines, stops, labels, icons, badges and boxes. Larkin's text and drawing moved into the file unchanged.
- **Records are tagged.** The simulator reads the same file. Each block chooses its households from its district by the block's character (for Larkin: low income, underbanked, renting, a language other than English) and by whether their records follow its patterns, so every pattern the day supports has records. Records from those households carry `block_id`, plus `block_pattern` and `context_ids` when they follow a pattern. The tagging draws no random numbers; the other 31 columns are unchanged. 2,580 households are on mapped blocks.
- **The lens shows the real record.** Opened from a record, the details column shows that record (its job statement, narrative and parties) with the circumstances mapped to its pattern, and says that they are composites mapped to the pattern, not to this household's history. Opened with nothing picked, it lists the block's patterns with today's counts so far. Opened from a household's day, it lists that household's records on the block. A pattern's sheet shows its count, its latest records and the composite example written for it.
- **What is still composite.** The circumstances, years, figures and loops are drafted from documented US patterns and have not been checked against sources one by one. The match rules approximate: Larkin's flood-insurance pin matches home and renters insurance bills, and Ashford's ride pin matches ride searches and paid rides. Larkin's savings circle has no records, because the simulator does not model informal savings circles; its pin is dashed. The tags describe where a record happened, not why: the simulator does not yet use the circumstances to decide what happens.

### For review

The five new blocks were drafted for review. The specific figures most worth checking against sources: Pelham's 40% rent rise since 2018, 10% late fees and 10-day filings, the 11:04 p.m. last bus, and the $40 plasma payment; Fox Hollow's $4.50 pay-by-plate fee, the 2006 concession and the 18% escrow rise; Ashford's 1998 mill closure, 21¢-a-minute jail calls with a county commission, the 2015 bus cut and the 2017 hospital closure; Dunmore's lot rent rising from $310 to $455, the 2016 branch closure, the 19 miles to a grocery and the $19-an-hour Medicaid home-care rate; and the Crossroads' 2009 school consolidation, 2018 pharmacy closure and one-van-a-week transit. All are written as composites of patterns documented elsewhere in the US, not as facts about a real place.

## The district tier (November 21, 2026)

Phase 6 removed the lens's dead end. Until now a record's **What shaped this** opened the lens only when its household lived on a mapped block; for about 93% of records it was a disabled row reading "Not mapped yet". Every district has exactly one mapped block, so each block now also carries a district tier, and every other record opens its district's block on that tier.

- **In `blocks.json`.** Each block has five or six more circumstances with `"scope": "district"`: three or four present-day ones drafted from the human-evidence report (`DW1` to `DW4`, which keep that report's row ids in `evidence_ids`, for the evidence files to come), and one historical (`DH1`) and one built & natural (`DE1`), which name their sources in `source_note`. Neither field is shown yet. Each has a `rep` near its layer's right corner, the part of every plate the stack leaves visible, and no drawing: it holds across the district, so it marks no square on the street. Each block also has a district loop, `D1`, and `"districtStart": {"loop": "D1"}`. Every existing id is kept. Each block's own history now rests on the district's (`under` gains `DH1`), and some present-day district circumstances rest on the deeper ones. Seasonal guest workers in open country sit on the political layer, so every district has a political circumstance; the social layer stays empty downtown, in the satellite city and in the rural town.
- **The tags don't move.** The tagger reads only `select` and `patterns`, which are unchanged. `sim/tests/test_blocks.py` checks that every published run's zip carries the same tagger inputs, and that tagging the test city with the published `blocks.json` and with this one writes identical `records.csv` and `households.csv`.
- **District mode.** Opened from a record or household elsewhere in the district, the lens shows the district tier as the story: each circumstance's callout carries a dark **Across** pill, the district loop is drawn, and the block's own circumstances and patterns fold under **On Larkin Avenue itself** (for Larkin) in the details column. The bar above the lens says "Opened from a record elsewhere in Inner suburbs", so it never implies the record is on the block, and the details column shows that record. A district circumstance's sheet has the **Across Inner suburbs** and **Composite** pills and says it is not the block's own history. The district toggle in the left column (**Across Inner suburbs**) turns the mode on from the block's own view, and `#lens=<block>/district` (or `systems-lens/?block=<block>&district=1`) links to it.
- **The explorer.** A record's sheet links to the lens over the city by the same rules, on the same day, and the "Lens" filter is now "Lens tags", since it filters `lens_tags`, not the systems lens.
- **Loops.** The D1 drafts for downtown and the rural town were labelled reinforcing with one minus link, which the lens's own rule ("an even number of minus links") would contradict; their closing links are now minus ("Less cash left keeps the bus the only way", "Less money for paid care leaves more shifts unfilled"). The block file's test now checks every loop's sign against its kind.
- **Phones.** The lens fills the screen on a phone, and its bar wraps so the district note stays readable. Before, the open drawer showed above and below it.

### Figures checked

The twelve historical and built circumstances were checked against their sources before merge. Six held as drafted or needed only wording: the 1949 to 1974 urban renewal program and the 1956 highways; the EPA's 1 to 7°F daytime heat island range (it says "urban areas"); HOLC's A to D grades; the American Housing Survey's 44-year median home age in 2023; the 1956 interchanges; and farm counts (6.8 million in 1935, 1,900,487 in the 2022 Census of Agriculture). Six changed:

- **Factory jobs.** "About 19.5 million" became 19.6 million, BLS's own rounding of the June 1979 peak (19,553,000). "Roughly a third during the 2000s alone" holds: 17,284,000 in January 2000 to 11,465,000 in December 2009 is 33.7% (CES series CES3000000001, seasonally adjusted).
- **Brownfields.** "More than 450,000" became the EPA's own range, 450,000 to 1 million, a 2004 GAO estimate it still uses.
- **Farmland.** American Farmland Trust's 11 million acres (2001 to 2016) holds, but it was not all housing: about 4.1 million acres went to urban and highly developed use and nearly 7 million to low-density residential. "Farmland kept turning into housing" became "giving way to development … most of it to low-density housing".
- **Manufactured homes.** "About 6% of homes" is out of date: the 2024 American Community Survey counts 7.94 million mobile homes among 146.7 million housing units, 5.4%. "Moving one costs thousands" had no source. Both figures came out; the text now says they are far more common in rural towns, that many sit on rented lots, and that moving the house is rarely practical.
- **Farm crisis.** "In some Midwest states they fell by more than half from 1981 to 1987" was supported only for Iowa. USDA's series, as reported in the FDIC's *History of the Eighties* (chapter 8), has farmland per acre down 34% nationally from its 1982 peak to 1987 and 62% in Iowa ($1,694 to $652); by 1985 Nebraska, Illinois, Minnesota and Missouri were down 38% to 46% from 1981. It now says "by about a third nationally, and by more than half in Iowa", with that source in `source_note`.
- **School districts and hospitals.** NCES table 214.10 holds (117,108 regular public school districts in 1939–40, 13,318 in 2022–23); the text says "public school districts". "More than a hundred rural hospitals have closed since 2010" counts the Sheps Center's converted closures, which still offer some care: 155 since 2010, of which 87 closed completely. It now says "closed or stopped inpatient care".

The present-day `DW` circumstances are as drafted from the evidence report and were not re-checked here.

### For review

The district tier is a draft, like the blocks. Worth a look: the D2 lenders circumstance rests on Larkin's hourly work (`EC1`), as drafted, though its text ("banks that left") reads closer to Larkin's last bank branches (`P1`); and every block's district loop is keyed `D1`, which can read like district D1 in the loop list.

## Open questions

- How circumstances drive the data, not only label it: today `context_ids` says which circumstances a record's pattern is mapped to. The next step is a setting per circumstance that the simulator uses, so a what-if becomes a second run with one setting changed.
- Whether loops should come from the data (chains found across many days) or stay written by hand and be tested against it.
- Drawing the run's own households and places on the Today layer, instead of a composite town with one pin per pattern.
