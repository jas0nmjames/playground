# Prompt: Find real human evidence to set beside Medianville's synthetic day

> Kept as written (November 17, 2026). This is the prompt that produced the files in this folder. The run it describes is v1's baseline day.

Paste everything below the line into a research-capable model (Fable or Claude with web search). Edit the PARAMETERS block first. Attach `records.csv`, `summary.md` and `detailed_sample_500.csv` from the run if you can. If you can't, the prompt still works from the summary included below.

---

## PARAMETERS (edit these)

- RUN: Medianville baseline day, Wednesday, March 3, 2027 (seed 20270303)
- PRIORITY_FRICTIONS: fees (tax-prep and refund-transfer, overdraft, check-cashing), distance and no transit, waits, schedule volatility, failed attempts, unpaid caregiving
- PRIORITY_POPULATIONS: households in poverty and ALICE households, older adults on fixed incomes, rural residents, unbanked and underbanked people, people with disabilities, people with limited English, farmworkers, small-business owners
- RECENCY: prefer 2019 to 2026; older classics are fine if nothing newer covers the topic. Flag anything from before COVID that may be out of date.
- GEOGRAPHY: national first. Southeast and Georgia sources are a bonus, because field visits happen near Fayetteville, GA.
- DEPTH: about 150 evidence records and 60 or more usable quotes in the first pass
- OUTPUT: CSV files plus one markdown report, as described below

## Your role

You are a qualitative research lead and evidence librarian. Medianville is a fictional city of about 100,000 people whose residents match the US as a whole. A simulator produced one day of about 200,000 transactions, encounters and "jobs to be done." Each record says what someone was trying to do, what it cost in money and time, and whether it worked.

The synthetic data shows patterns. It cannot show how those moments feel or what people actually say about them. Your job is to find real studies of consumers and real first-person accounts that confirm, contradict or deepen what the simulation shows. The goal is to mine the day for small, practical projects that improve daily life at the margins.

## What the simulation found (test these)

- 13.4% of households had at least one failed attempt: 28.5% in poverty, 16.1% ALICE, 9.5% above the ALICE threshold.
- Unpaid jobs took 16,736 hours in one day, and half of that was caregiving at home.
- Tax-prep and refund-transfer fees were the largest fee for poverty and ALICE households. For households above the threshold, it was card interest.
- The frictions that cost the most combined time and money were fees, distance, waits, schedule volatility and lack of transit.
- Cash was 14.3% of payments overall, 37.2% for households in poverty and 16.8% in rural areas.
- 63% of adults could cover a $400 emergency.

For each finding, look for real evidence on three questions: Is it right? Is it the right size? What is it like for the person living it?

## Hard rules

1. **Real and checkable only.** Every finding and quote needs a working link or a full citation (author, title, publisher, year, page or timestamp). Never invent, merge or "clean up" a quote. If you can't verify a quote, leave it out.
2. **Short quotes.** Keep each quote under 20 words, with no more than one quote per source per evidence record. Paraphrase everything else in your own words.
3. **People's privacy.** Use only published or public material. Name a person only if the source named them with consent (journalism, oral histories, testimony, books). For forum and social posts, paraphrase them and don't record usernames. Never try to identify someone who wrote anonymously.
4. **Keep real and synthetic apart.** Don't write real quotes into synthetic records or give them to fictional Medianville residents. Link evidence to Medianville by job category, friction tag and household type instead.
5. **Balance.** For every major friction, look for accounts from more than one angle: the person facing it, the frontline worker or small-business owner on the other side, and the agency or firm that designed the system. Use the City Design doc's paired think tanks (left, center and right) so each friction gets at least two diagnoses.
6. **Say how strong the evidence is.** A national survey, an ethnography of 40 families, a news anecdote and a Reddit thread are not equal. Grade every record.
7. **No moralizing.** Report what people say and do, not judgments about their choices.

## Where to search (search widely, then go deep)

Search for each priority friction and population separately. Combined queries give shallow results. Use these source types as a checklist, not a limit:

- **Financial diaries and ethnographies:** the US Financial Diaries project; book-length ethnographies of low-income financial life, eviction, check-cashers and payday lending, $2-a-day poverty, EITC and refund season, and debt
- **Administrative burden research:** studies of benefits paperwork, renewals and "time tax," including work from Code for America and the academic literature on administrative burden
- **Scheduling and low-wage work:** the Shift Project and similar survey-plus-interview studies of hourly retail and food-service workers
- **Federal and Fed qualitative work:** open-ended responses and focus groups from the Fed's SHED, Fed community development reports (the Atlanta Fed especially), CFPB reports, and the CFPB consumer complaint database's published narratives (check what is still public)
- **Advocacy and research groups' first-person work:** United For ALICE, AARP caregiving research, Financial Health Network, Urban Institute, Aspen Institute Financial Security Program, Commonwealth, ideas42, Prosperity Now, KFF (medical debt), National Consumer Law Center, Fines and Fees Justice Center, the National Agricultural Workers Survey and farmworker advocates, disability and digital-inclusion groups
- **Right and center-right sources:** AEI poverty studies, Institute for Family Studies, Manhattan Institute, Mercatus, Cato, NFIB small-business surveys, Georgia Public Policy Foundation, for fees, licensing, regulation and small-business costs
- **Journalism with named sources:** long-form reporting, public radio (including Planet Money and local NPR stations), ProPublica, The Daily Yonder for rural life, More Perfect Union video reporting, and Georgia outlets such as the AJC, Georgia Public Broadcasting and Capital B Atlanta
- **Oral histories and testimony:** StoryCorps, university oral-history archives, public comments in federal rulemaking (regulations.gov), and congressional and state legislative testimony
- **Design and JTBD research:** published jobs-to-be-done "switch" interviews and service-design case studies about banking, benefits, health care and transit, which match Medianville's "When…, I want…, so I can…" form
- **Public reviews and forums, with care:** reviews of DMVs, clinics, transit and check-cashers, and forums such as r/povertyfinance. Use these to find friction types and wording, never for frequencies.

If a source is paywalled or unreachable, record it with its citation and mark it `not_accessed` rather than guessing what it says.

## Output files

### sources.csv
`source_id, title, authors_or_org, publisher, year, url, source_type (survey|diary_study|ethnography|interview_study|admin_data|complaint_narratives|journalism|oral_history|testimony|review_or_forum|design_research), method, sample_size, population, geography, lens (left|center|right|nonpartisan|advocacy|industry|government), accessed (yes|partial|not_accessed), notes`

### evidence.csv (one row per finding linked to Medianville)
`evidence_id, source_id, job_category, record_type, friction_tags, lens_tags, alice_status, household_or_person_type, district_type (urban_core|inner_suburb|outer_suburb|satellite_city|rural_town|open_country|national), finding_paraphrase, figure_if_any, relation_to_sim (confirms|contradicts|sizes_differently|adds_missing_job|adds_texture), sim_reference, strength (A|B|C|D), strength_note`

Use Medianville's own vocabularies for `record_type`, `friction_tags` and `lens_tags`:
- `friction_tags`: wait, distance, no_transit, hours_mismatch, missing_document, language, disability_access, digital_barrier, fee, insufficient_funds, pending_hold, benefits_cliff, eligibility_confusion, out_of_stock, outage, caregiving_conflict, schedule_volatility, scam_attempt, price_spike, paperwork, repeat_trip, other
- `lens_tags`: consumer_finance, labor, aging, farmworker, land_use, disability, rural, housing, health_cost, education, small_business, public_finance, family_care, digital_access

Strength grades:
- A: nationally representative survey or administrative data
- B: systematic qualitative study (diaries, interviews, ethnography) with a stated method and sample
- C: journalism, testimony or oral history about named people
- D: reviews, forums or a single anecdote

### quotes.csv
`quote_id, evidence_id, source_id, quote (under 20 words, exact), speaker_description (e.g., "home health aide, 40s, rural Georgia"), speaker_named_in_source (yes|no), location_in_source (page, timestamp or paragraph), job_statement_rewrite`

`job_statement_rewrite` restates what the speaker was trying to do in Medianville's form, "When [situation], I want to [motivation], so I can [outcome]," in your words, not theirs.

### report.md
1. **Scorecard:** each simulation finding above, rated confirmed, contradicted, wrong size or no evidence found, with the two or three best sources for each.
2. **What the simulation is missing:** jobs, frictions or household types that come up repeatedly in real accounts but are absent or rare in Medianville. List concrete generator changes (a new job category, a new friction tag, a changed probability).
3. **Top 10 frictions with real voices:** for each, one-paragraph synthesis, how often it happens (best figure available), who it hits, one or two short quotes, and the diagnoses from at least two lenses.
4. **Project leads:** five to ten small, practical project ideas that both the synthetic data and the real evidence support, each with the evidence IDs behind it.
5. **Field-visit prompts:** for each of the eight planned visits (Driver Services center, Five Points MARTA, a highway-exit gas station and Waffle House at shift change, a laundromat and check-casher strip, a rural Dollar General and pharmacy, a school pickup line, an ER or urgent care, a farm stand), three things the literature says to look and listen for.
6. **Gaps and cautions:** where evidence was thin, old, local or one-sided, and sources you couldn't access.

## How to work

1. Start with a search plan: one line per priority friction and population, with the source types you'll try. Then run it.
2. Search each topic separately and follow citations from the best sources to the studies they rely on.
3. Read the source itself before recording a finding or quote, not just a search snippet or a summary of it.
4. When a real account contradicts the simulation, record it prominently. Contradictions are the most useful result.
5. If you have the run files, use them to sample 20 records for each top friction and check whether the real accounts would recognize them as true.

## Quality bar

Before delivering, check your work as a skeptical ethnographer, a survey methodologist and a fact-checker would:
- Could someone find each quote at the location you gave, with the same words?
- Does each friction have evidence from more than one kind of source and more than one viewpoint?
- Are low-income, older, rural, disabled and limited-English people heard in their own words, not only described by researchers?
- Are high-income households and small-business owners represented where the simulation includes them?
- Did you keep national frequencies (grade A and B) separate from vivid anecdotes (grade C and D)?
