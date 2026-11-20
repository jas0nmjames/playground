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

## Open questions

- How circumstances drive the data, not only label it: today `context_ids` says which circumstances a record's pattern is mapped to. The next step is a setting per circumstance that the simulator uses, so a what-if becomes a second run with one setting changed.
- Whether loops should come from the data (chains found across many days) or stay written by hand and be tested against it.
- Drawing the run's own households and places on the Today layer, instead of a composite town with one pin per pattern.
