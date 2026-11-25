# M3 Grounding in evidence

## When

2026-11-17 to 2026-11-19. The evidence research ran in the Claude app on Nov 17; the [data update plan](medianville-data-update-plan.md) was written on Nov 18; phases 0 to 2 landed in commit [`e077162`](https://github.com/jas0nmjames/playground/commit/e077162) (Nov 18, pushed straight to `development`), [#61](https://github.com/jas0nmjames/playground/pull/61) and [#65](https://github.com/jas0nmjames/playground/pull/65) (Nov 19). The evidence files themselves came into the repo later, in [#86](https://github.com/jas0nmjames/playground/pull/86) on Nov 22. M3 overlaps [M4](../04-the-refined-city/), which ran beside it. [GitHub milestone](https://github.com/jas0nmjames/playground/issues?q=milestone%3A%22Medianville+%C2%B7+M3+Grounding+in+evidence%22). No release: there's no new viewer to snapshot, and the evidence's effect on the data is in [M5](../05-more-time/)'s.

## What I wanted

I wanted publicly available research to become something you can explore, without relying on private data that couldn't be shared.

## What I asked for

- [The research prompt](../../evidence/research-prompt.md), kept as written: find real human evidence to set beside the synthetic day, from left, right and nonpartisan sources.
- The [data update plan](medianville-data-update-plan.md) began as a Claude-app brief: fold in the evidence, then go past one day.

## What came back

- **The human evidence report** ([`evidence/report.md`](../../evidence/report.md)): the first day scored against 69 real sources, with 76 findings and 25 quotes in [`evidence/`](../../evidence/). It named what the day was missing (overdraft fees, payday and title loans, shutoffs, medical debt, caregiving, aide no-shows, work reporting), and nine project leads and eight field-visit prompts for [Next](../next-mining-for-projects/).
- **The data update plan**: how evidence gets into the data, what to download, how to go past one day, and the phases 0 to 6 with their status.
- **Phases 0 to 2:** the simulator copied to `sim/` with tests that v1 reproduces byte for byte (phase 0); `sim/evidence_targets.csv` and the typed-day set measured on the unchanged simulator (phase 1); and 41 public datasets downloaded and logged in [`sources/manifest.csv`](../../sources/manifest.csv), raw files outside git (phase 2).

## What I decided, and roads not taken

- [2.8 Only strong evidence sets a rate](../decisions.md#28-only-strong-evidence-sets-a-rate): evidence graded A or B moves a rate; weaker evidence only adds job kinds and texture.
- [2.9 Past one day: typical days first, then a month](../decisions.md#29-past-one-day-typical-days-first-then-a-month).
- [2.10 Same people for v2, real households in v3](../decisions.md#210-same-people-for-v2-real-households-in-v3): not taken yet, drawing households from Census microdata (ACS PUMS), which waits for v3.
- Not taken: quoting real people in records. Real evidence enters only as numbers ([2.7](../decisions.md#27-keep-real-and-synthetic-apart)).

## Who did what

**Jason James:** the decision to ground the day in real accounts, the rule that only strong evidence moves a rate, and how far past one day to go. **Claude:** researched the 69 sources and wrote the report in the Claude app, wrote the plan, and in Claude Code sessions in the cloud and on Jason's Mac copied the simulator, wrote the targets and checks, and fetched and logged the datasets.

## What it set up next

Targets and inputs for the simulator changes of [M5](../05-more-time/) (phase 3 onward), and the district circumstances behind the systems lens in [M4](../04-the-refined-city/).
