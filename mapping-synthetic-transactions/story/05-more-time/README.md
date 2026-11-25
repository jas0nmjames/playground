# M5 More time

## When

2026-11-20 to 2026-11-21, in [#71](https://github.com/jas0nmjames/playground/pull/71) (phase 3), [#78](https://github.com/jas0nmjames/playground/pull/78) (phase 4, the month), [#80](https://github.com/jas0nmjames/playground/pull/80) (the month's Release checked), [#81](https://github.com/jas0nmjames/playground/pull/81) (phase 5, close reading and publishing) and [#82](https://github.com/jas0nmjames/playground/pull/82) (the lens's district tier, called phase 6), merged at [`23265ff`](https://github.com/jas0nmjames/playground/commit/23265ff). It overlaps [M4](../04-the-refined-city/): the rename, phase 3b, ran between phases 3 and 4. [GitHub milestone](https://github.com/jas0nmjames/playground/issues?q=milestone%3A%22Medianville+%C2%B7+M5+More+time%22) · [release `medianville-m5-more-time`](https://github.com/jas0nmjames/playground/releases/tag/medianville-m5-more-time) · the month's own release, [`medianville-v2-month-2027-03`](https://github.com/jas0nmjames/playground/releases/tag/medianville-v2-month-2027-03).

## What I wanted

Financial activity isn't the same from one day to the next, something Claude reminded me of. Pulling in more simulated days lets us reach different conclusions. It also mattered that the experience stayed usable, both as an interface and as a build: rather than sending every visitor hundreds of megabytes at once, the site downloads each day only when you open it.

## What I asked for

- Phases 3 to 5 followed the [data update plan](../03-grounding-in-evidence/medianville-data-update-plan.md), with a brief from Jason for each session.
- To add: the briefs for phase 4 (the month), phase 5 (read and publish) and the phase 6 handoff with its district history addendum, copied word for word into `prompts/`.

## What came back

- **The simulator changes** (phase 3, [#71](https://github.com/jas0nmjames/playground/pull/71)): batches C (calendar and day weights), I (household inputs), J (the missing jobs), P (places and organizations) and R (rates tuned to the targets).
- **The typed-day year**: 18 typed days that stand for 2027 (weekends, paydays, benefit days, holidays, tax season, a storm, a heat wave) beside the baseline day, weighted to the 365 days, each checked against the evidence targets.
- **The March 2027 month** (phase 4, [month run record](medianville-2027-03-month-run-record.md)): 31 days carried one into the next, so unpaid bills, shutoffs, overdrafts and payday and title loans chain across days. 5.7 million records, published as a [Release download](https://github.com/jas0nmjames/playground/releases/tag/medianville-v2-month-2027-03), not on the site.
- **Close reading and publishing** (phase 5): 200 records read by two readers ([close reading](medianville-v2-close-reading.md); the second readers on [the sample](medianville-v2-second-reader.md) and on [the hand-written records](medianville-v2-handwritten-second-reader.md)), three fixes, the simulator frozen, 300 hand-written records, and the 19 days published with the day menu ([v2 run record](medianville-v2-run-record.md)).
- **The district tier** ([#82](https://github.com/jas0nmjames/playground/pull/82)): every record now opens the systems lens, on its own block or on its district's.

## What I decided, and roads not taken

- Carried days: [1.7 to 1.15](../decisions.md#17-carried-runs-leave-the-one-day-path-untouched), from leaving the one-day path untouched to shipping the month as a Release bundle ([1.15](../decisions.md#115-the-month-ships-as-a-release-bundle-not-on-the-site)).
- Reading: [2.11 Fix what v2 broke; leave the people for v3](../decisions.md#211-fix-what-v2-broke-and-what-the-records-say-wrong-leave-the-people-for-v3) (not taken: fixing the population now, or freezing with v2's regression), [2.12 Two readers](../decisions.md#212-two-readers-and-a-second-reader-for-the-hand-written-text).
- Publishing: [5.4 Days chosen from a manifest](../decisions.md#54-days-chosen-from-a-manifest-each-its-own-link), [5.5 The typed-day zips go in the repo, once](../decisions.md#55-the-typed-day-zips-go-in-the-repo-once).
- The lens: [4.6 A district tier, so no record is a dead end](../decisions.md#46-a-district-tier-so-no-record-is-a-dead-end), which fixed the dead end M4 left. "What if" still waits for circumstances that drive the simulator.
- Left for v3: households drawn from Census microdata at their real size, which also drops the 1.23 wage boost. The plan's own phase 6 (ACS PUMS, a year at 10%) is still to come; #82's "phase 6" was the lens work.

## Who did what

**Jason James:** how far past one day to go, which fixes to make before the freeze, and the district history. **Claude:** in Claude Code sessions in the cloud and on Jason's Mac, changed the simulator one commit at a time, ran the year and the month, read the records with a second agent, wrote the 300 records, packed and verified the 19 days, and wrote the district tier and its checks.

## What it set up next

v2, the data the site runs on today. [M6](../06-refinements/) polished how it's shown.
