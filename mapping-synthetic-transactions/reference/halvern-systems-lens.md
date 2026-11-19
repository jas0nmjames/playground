# Halvern Systems Lens: design record

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
- **The lens uses the Halvern in Motion design system,** not the Biesty ink-and-watercolor look of the first prototypes. Biesty survives in the structure (exploded plates, callouts with leader lines), not in the rendering.

## The page

- **Look.** The same system as v3: slate page (`#F3F5F8`), white surfaces, ink `#0E1B2E`, Figtree with tabular figures, 12 px corners and soft shadows, and Barlow Condensed for layer names, as on the map sheet. The header has the "Simulated city · no real people" chip and a Miniature | Map | Systems lens switch. Miniature and Map both open `v3/`. Record pins are solid record-type discs with white numbers, like feed icons, and loops are drawn in the action blue (`#1F5AF0`).
- **Layers.** The layers in the current story (the selection's chain plus the active loop) spread apart and get a blue dot in the layer list. The others collapse to slivers at half opacity with their labels hidden. Pointing at a layer in the list lifts it; selecting one shows it alone, and Show all layers or Esc brings the rest back.
- **Pace.** Each layer's label gives how fast it changes. Today changes by the minute, Economic over years, Political over decades, Built & natural and Social & cultural over generations, and Historical is bedrock that lasts a century.
- **Callouts.** For the selected story only, every circumstance gets a white card in a column to the right of the stack, with a leader line to its square. Each card shows its types, year, layer and full text, for example "1983 · Historical: Halvern Works closes: 1,900 union jobs gone." Circumstances outside the story keep short labels.
- **Today layer.** A small isometric town: houses, the Larkin Avenue shops, the church, warehouses on the old Works site, the highway trench and the creek, with the nine records pinned on the roofs.
- **Loops.** One at a time: R1 Fee spiral, R2 Rollover, R3 Time tax, B1 Circle buffer. Each is a closed curve through nodes on the layers they belong to, with arrowheads, + and − link signs, an R or B marker, and dotted "pushed by" arrows from circumstances on other layers. Every loop is a hypothesis for run 2 to test, and its sheet says so.
- **Details.** The right column is a sheet in v3's transaction style. A record shows a big amount (plum when it failed), status and type pills, the narrative, time, counterparty, kind and layer, and the circumstances that shaped it. A circumstance shows its types, body, when, layer and pace, what it rests on and what it shapes. A loop shows a numbered "How it runs" list with its signs, what pushes it, and where it shows up today.
- It opens on record 6 (1:05 p.m., payday loan renewed, $75 fee) with loop R2 drawn.

## Open questions

- How circumstances enter the data: a `context.csv` that drives the simulator, and `caused_by` links on records. That is part one of the next round, the data and model changes.
- Whether loops should come from the data (chains found across many days) or stay written by hand and be tested against it.
- Wiring the lens to the real run: opening it from a selected record in v3, and drawing the run's own households and places on the Today layer.
