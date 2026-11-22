# Evidence

The real-world research read beside Medianville. Nothing here goes into a record: real evidence enters the simulation only as numbers, and no real person's words or record appear in Medianville.

| File | What it is |
|---|---|
| [`report.md`](report.md) | The human-evidence report (first pass, November 17, 2026): the first day scored against 69 real sources, what it was missing (which became v2's new jobs), ten frictions with real voices, project leads and field-visit prompts. Kept as written. |
| [`sources.csv`](sources.csv) | The report's 69 sources: title, publisher, year, URL, method, sample, population, geography and lens (nonpartisan, government, advocacy, industry, center, right). |

Still in the Claude project, not yet here: the 76 findings (`evidence.csv`, the `E` ids cited in the report and in `systems-lens/blocks.json`), the 25 quotes (`quotes.csv`) and the research prompt. The [data update plan](../reference/medianville-data-update-plan.md), section 2, describes the `evidence_links.csv` that will join findings to records.

The other research:

- **Calibration anchors** for the first run: the [run record](../reference/medianville-2027-03-03-run-record.md) and the white paper, [Seeing the Margins](../reference/seeing-the-margins.md).
- **Downloaded datasets** that set v2's rates: [`../sources/manifest.csv`](../sources/manifest.csv) (52 rows: 42 fetched, 10 listed for later versions), with the derived tables in `../sources/derived/` and the targets in `../sim/evidence_targets.csv`.
- **District history** behind the systems lens: each circumstance's `source_note` in `../systems-lens/blocks.json`, checked as recorded in the [design record](../reference/medianville-systems-lens.md).
