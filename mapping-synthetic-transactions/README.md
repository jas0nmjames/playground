---
published: 2026-11-17
updated: 2026-11-17
tags: generative
---

# Transactions are Jobs to be Done: Synthetic Market Animation

An animated night map of Halvern, an invented American city of about 100,000 people. It plays back all 201,753 records from one simulated day (Wednesday, March 3, 2027): purchases, bills, paychecks, benefits, school days, bus rides, unpaid care and failed attempts. Each record moves as a light between a household and the party on the other side.

## Watching it

Open the [live page](https://jas0nmjames.github.io/playground/mapping-synthetic-transactions/). Placeholder records move while the real day downloads (16 MB), and then the clock starts at 6:30 a.m.

- **Clock and timeline.** Play or pause with the button or the space bar. Pick a speed from real time up to 30 minutes per second, and drag the timeline to jump. The bars show how busy each five minutes is, with failures in red.
- **Map.** The six districts are drawn as rings and clusters: downtown in the middle, inner and outer suburbs around it, and the satellite city, rural town and open country outside. Dots are households, squares are outside parties such as the Treasury, and the color of each light is the kind of record.
- **Records.** Tap a light or a line in the ticker to open the record: the job statement ("When…, I want to…, so I can…"), who paid, who else paid, the cost to the public, time, travel, frictions and outcome. From there you can show the household's whole day, follow it on the map, or open the attempt a retry links back to.
- **Filter.** Narrow the map by kind of record, district, friction or failure, the 500 hand-written records (marked ✎), or a word in the job name.
- **Load run.** Loads another run from your computer: a zip from the simulator, or `records.csv` with `organizations.csv`, `households.csv` and `persons.csv`.

No build step. Serve the folder to try it locally (opening `index.html` as a file can't fetch the data, so it shows the placeholder day and the Load run button):

```bash
python3 -m http.server 5181 --directory mapping-synthetic-transactions
```

## What's in this folder

| Path | What it is |
|---|---|
| `index.html` | The page: canvas map, timeline, ticker, record sheets and filters |
| `fflate.js` | [fflate](https://github.com/101arrowz/fflate) (MIT), used to unzip the run in the browser |
| `data/halvern_2027-03-03.zip` | The complete run, exactly as delivered: the data tables, the simulator, and the hand-written records. The page loads this file. |
| `data/halvern/` | The same package unpacked so it can be read on GitHub, without the four large tables (`records.csv`, 77 MB; `persons.csv`; `households.csv`; `household_ledger.csv`), which are only in the zip |
| `data/halvern/out/summary.md` | Counts, calibration against the anchors, fees, public dollars and the costliest frictions |
| `data/halvern/detailed_sample_500.csv` | The 500 hand-written records |
| `data/halvern/simulate.py`, `halvern_sim/` | The simulator (Python 3.10+ and numpy). The package's own [README](data/halvern/README.md) explains how to re-run it for another date, a storm, or several days in a row. |
| `reference/` | The documents behind the project, listed below |

### Reference documents

- [Seeing the Margins: What a Representative American Day Reveals](reference/seeing-the-margins.md): the research white paper. Why no real city stands in for the US, and what fragility, payment habits and government look like in an ordinary day.
- [Synthetic Mid-America: City Design v0.1](reference/synthetic-mid-america-city-design-v0.1.md): the design of the city, covering districts, economy, transaction model, field visits, and the lenses used to read it.
- [Halvern transaction generator prompt](reference/halvern-transaction-generator-prompt.md): the prompt that generated the data.
- [How the Halvern day was built](reference/halvern-build-approach.md): the method, what close reading of the sample caught, and what was left unfixed.
- [Halvern run record](reference/halvern-2027-03-03-run-record.md): what the run produced and how close it came to each anchor.

Everything in the data is synthetic. People, businesses and local agencies are invented. Federal programs keep their real names because the specification requires them. Synthetic data suggests where to look; it isn't evidence.

## How the page works

The page reads the CSVs directly as bytes, without turning every row into an object, so 201,753 records load in a few seconds. Each household and organization gets a fixed spot inside its district from a hash of its id, so the same entity always lands in the same place. As the clock advances, the page releases the records due by that time. It animates a sample of them along curved paths (up to 26 a frame on wide screens, 9 on phones), and the four counters stay exact. Records whose two ends are the same place, such as a school day, show as a ring that pulses outward instead.

Changes made when the page moved here from the Claude artifact:

- It loads `data/halvern_2027-03-03.zip` by itself on open, instead of asking for the file. If the download fails, it says so and falls back to the placeholder day and the Load run button.
- The placeholder day finishes building before the real one starts, so the two builds never share lookup tables.
- On narrow screens, floating captions near the left edge stayed partly off screen. They now stay inside the map.
- A footer credits the page and links to the impact figures below.

## Claude

The data was generated by Claude Fable 5.2 (`claude-fable-5-2`) in the Claude app, in one long session on November 16, 2026. That session is described in [How the Halvern day was built](reference/halvern-build-approach.md). The research, the city design and the animation were also made with Claude in the Claude app. None of those sessions can be counted from here.

The move into this repository was one Claude Code session (claude-opus-5-5) on November 17, 2026. It:

1. Matched the project to the artifact, copied its page and unzip library, unpacked the run, added the reference documents, and confirmed scope, privacy and branch with you.
2. Made the page load the committed run on its own and added the footer. It tested the page in headless Chromium at desktop and phone sizes: the full day loaded in about 4 seconds with no console errors and no sideways scroll. It fixed the caption overflow that test showed.
3. Wrote this README, updated the root directory, committed and opened the pull request into `development`.

| Created | Tool | Model | Estimated energy consumption[^claude] | Estimated carbon emissions | Estimated water usage |
|---|---|---|---|---|---|
| November 16, 2026 | Claude app | claude-fable-5-2 | not measurable from here | — | — |
| November 2026 | Claude app (research, city design, animation) | (unknown) | not measurable from here | — | — |
| November 17, 2026 | Claude Code | claude-opus-5-5 | 0.576 kWh | 0.222 kg CO₂ | 0.288 L |
| **Total (countable)** | | | **0.576 kWh** | **0.222 kg CO₂** | **0.288 L** |

[^claude]: assuming 18 Wh per model API request; carbon at 0.386 kg CO₂ per kWh and water at 0.5 L per kWh, as across this playground; does not include estimate for foundation model training. The Claude Code row is 32 requests: 24 measured in the session transcript before this README was written, plus an estimate of 8 for the README, the commit, the pull request and the reply. At the time of measuring, the session had used ≈ 4.3M tokens, about 96% of them cache reads.
