# M0 The idea

## When

Before 2026-11-16, written up on 2026-11-16. No pull requests, commits or tag: this milestone is the thinking that came before any code. Its two documents came into the repo with [M1](../01-one-day/) in [#54](https://github.com/jas0nmjames/playground/pull/54). [GitHub milestone](https://github.com/jas0nmjames/playground/issues?q=milestone%3A%22Medianville+%C2%B7+M0+The+idea%22) (no release).

## What I wanted

TODO(Jason): the question in your own words. The About page puts it as: which American city or town best matches the country's mix of wealth, race, class, industry and gender?

## What I asked for

The prompts for the research and the city design were written in the Claude app.

- To add: the research prompt behind *Seeing the Margins*, copied word for word into `prompts/`.
- To add: the prompt behind *City Design v0.1*, copied word for word into `prompts/`.

## What came back

- [Seeing the Margins: What a Representative American Day Reveals](seeing-the-margins.md), the white paper. No real city stands in for the United States; the closest are mid-size metros, and every one of them underweights rural and small-town life. Fragility is the norm, not the edge (63% of adults would cover a $400 expense in cash), and needs move on four clocks: the calendar, the life course, the generation and the community's life cycle.
- [Synthetic Mid-America: City Design v0.1](synthetic-mid-america-city-design-v0.1.md), the design: about 100,000 people in six districts sized to national shares, every transaction recorded as a job, failures counted as transactions, eight field visits around Fayetteville, GA, and the advocacy, research and federal lenses for reading the day.

## What I decided, and roads not taken

- [1.1 Every transaction is a job to be done](../decisions.md#11-every-transaction-is-a-job-to-be-done), the framing the whole project rests on.
- [1.2 A synthetic city, not a real one](../decisions.md#12-a-synthetic-city-not-a-real-one). Not taken: a real test-market city (Columbus, Indianapolis), or "a synthetic Indianapolis".
- [1.3 Six districts in national proportions](../decisions.md#13-six-districts-in-national-proportions).
- [1.4 A systems lens alongside the city](../decisions.md#14-a-systems-lens-alongside-the-city), from Donald Martin Jr.'s idea of societal context, which waited until [M4](../04-the-refined-city/) to be built.

## Who did what

**Jason James:** the question, the jobs-to-be-done framing, the systems lens and the decision to build a synthetic city. **Claude:** researched the published rankings and national data behind the white paper and drafted the city design, in the Claude app under Jason's direction.

## What it set up next

A specification for one ordinary day, which [M1](../01-one-day/) turned into a generator prompt and 201,753 records.
