# The story of Medianville

Medianville was dreamed as a question about which American town is most like America, built as one simulated day and a way to watch it, grounded in real evidence, refined into a city you can read through a systems lens, and given more time: a year of typed days and a month carried day to day. Milestones 1 through 5 took about a week, from November 16 to 22, 2026, with milestones 3, 4 and 5 running side by side. What's next is the reason for all of it: mining the city for small, practical projects that improve daily life at the margins.

Each milestone has a folder with its documents, screenshots and a README: when, what Jason wanted, what he asked for, what came back, what was decided and what was dropped, who did what, and what it set up. Every decision is in [the decision log](decisions.md), tagged with its milestone. The frozen viewers are in [the archive](../archive/).

## Versions

Folders, tags and milestone titles use milestone names; viewers and data runs keep their own version numbers.

| Milestone | Viewer | Data run | Data plan phases |
|---|---|---|---|
| M1 One day | v1, the night map ([archived](../archive/m1-night-map/)) | v1: `halvern_2027-03-03.zip` | — |
| M2 Miniature and Map | v3 as first shipped ([archived](../archive/m2-miniature-and-map/)) | v1 | — |
| M3 Grounding in evidence | — | v1, measured against evidence targets | 0, 1, 2 |
| M4 The refined city | latest (root) | v1 renamed: `medianville_2027-03-03.zip` | 3b (rename) |
| M5 More time | latest, with the day menu | v2: 19 days and the March month | 3, 4, 5, "6"* |
| M6 Refinements | latest | v2 | — |
| M7 Open to agents | latest, with Copy for AI | v2, with pages for agents | — |

\* [#82](https://github.com/jas0nmjames/playground/pull/82), the systems lens's district tier, shipped as "phase 6" of v2. The [data update plan](03-grounding-in-evidence/medianville-data-update-plan.md#8-phases)'s own phase 6 (households from ACS microdata, a year at 10%) is still to come.

## The milestones

- [M0 The idea](00-the-idea/), before 2026-11-16: transactions as jobs to be done, a synthetic city instead of a real one, the systems lens and the four clocks.
- [M1 One day](01-one-day/), Nov 16–17: the generator prompt, the simulator, the 201,753-record day, the 500 hand-written records and the first viewer, the night map.
- [M2 Miniature and Map](02-miniature-and-map/), Nov 17: three visual directions prototyped, Tabletop chosen, then v3: two views of one city.
- [M3 Grounding in evidence](03-grounding-in-evidence/), Nov 17–19 (the files reached the repo Nov 22): 69 sources of real evidence, the data update plan, the evidence targets and the downloaded datasets.
- [M4 The refined city](04-the-refined-city/), Nov 18–20: the systems lens, mapped blocks, the photographic miniature, sound, the data explorer, the repo reorganized, the intro and About page, and the rename to Medianville.
- [M5 More time](05-more-time/), Nov 20–21: v2's simulator changes, the typed-day year, the March 2027 month, close reading and publishing, and the lens's district tier.
- [M6 Refinements](06-refinements/), Nov 21 onward: polish, rendering fixes, the day control, Sound on the city, the explorer header, and this story. Its README keeps a running log.
- [M7 Open to agents](07-open-to-agents/), Nov 24 onward: the site made readable by agents and LLMs. The first pass: `llms.txt`, Markdown pages for every run and district, a data dictionary, licenses for the data, and Copy for AI on a record.

## Next

[Mining for projects](next-mining-for-projects/) hasn't started. It's the project's actual goal: rank the frictions across the year and the month, recheck the project leads the evidence report named against v2, and make the field visits, so that what the synthetic city suggests can be checked in real places.

## Where the documents were

Until 2026-11-24 the documents were in `reference/`. They kept their file names when they moved, so their history follows them. The frozen simulator in `sim/`, `sim/evidence_targets.csv` and the packing tools still name the old paths, because changing them would change the published zips and manifest.

| Was | Now |
|---|---|
| `reference/design-decisions.md` | [`decisions.md`](decisions.md) |
| `reference/seeing-the-margins.md` | [`00-the-idea/seeing-the-margins.md`](00-the-idea/seeing-the-margins.md) |
| `reference/synthetic-mid-america-city-design-v0.1.md` | [`00-the-idea/synthetic-mid-america-city-design-v0.1.md`](00-the-idea/synthetic-mid-america-city-design-v0.1.md) |
| `reference/medianville-transaction-generator-prompt.md` | [`01-one-day/medianville-transaction-generator-prompt.md`](01-one-day/medianville-transaction-generator-prompt.md) |
| `reference/medianville-build-approach.md` | [`01-one-day/medianville-build-approach.md`](01-one-day/medianville-build-approach.md) |
| `reference/medianville-2027-03-03-run-record.md` | [`01-one-day/medianville-2027-03-03-run-record.md`](01-one-day/medianville-2027-03-03-run-record.md) |
| `reference/medianville-data-update-plan.md` | [`03-grounding-in-evidence/medianville-data-update-plan.md`](03-grounding-in-evidence/medianville-data-update-plan.md) |
| `reference/medianville-systems-lens.md` | [`04-the-refined-city/medianville-systems-lens.md`](04-the-refined-city/medianville-systems-lens.md) |
| `reference/medianville-miniature-realism.md` | [`04-the-refined-city/medianville-miniature-realism.md`](04-the-refined-city/medianville-miniature-realism.md) |
| `reference/medianville-v2-run-record.md` | [`05-more-time/medianville-v2-run-record.md`](05-more-time/medianville-v2-run-record.md) |
| `reference/medianville-2027-03-month-run-record.md` | [`05-more-time/medianville-2027-03-month-run-record.md`](05-more-time/medianville-2027-03-month-run-record.md) |
| `reference/medianville-v2-close-reading.md` | [`05-more-time/medianville-v2-close-reading.md`](05-more-time/medianville-v2-close-reading.md) |
| `reference/medianville-v2-second-reader.md` | [`05-more-time/medianville-v2-second-reader.md`](05-more-time/medianville-v2-second-reader.md) |
| `reference/medianville-v2-handwritten-second-reader.md` | [`05-more-time/medianville-v2-handwritten-second-reader.md`](05-more-time/medianville-v2-handwritten-second-reader.md) |
