# Finishing phase 2 on your Mac

The cloud session fetched 22 of the 41 tier 1–2 rows. The other 19 refuse requests from cloud machines
and need a home connection. The 22 downloaded files didn't survive the cloud session either: `sources/raw/`
is gitignored and that machine is gone. So the Mac session does two things:

1. **Re-download the 22 fetched rows** and check each file against the SHA-256 in `sources/download_log.jsonl`.
2. **Download the 19 blocked rows**, following `sources/README.md` (newest vintage first, publisher's own site
   only, codebooks with microdata, ask before anything over 1 GB).

Then fold everything into `sources/manifest.csv` and commit the manifest and log. Raw files are never committed.

You can do this by hand with the commands below, or open Claude Code on the Mac in your clone of
`playground` and paste the prompt at the end.

## 1. Set up

```bash
cd ~/path/to/playground && git checkout development && git pull
```

```bash
git checkout -b halvern-v2-downloads-mac
```

```bash
cd mapping-synthetic-transactions && python3 --version
```

Python 3.10 or later; the tools use the standard library only.

## 2. Re-download the 22 rows

```bash
python3 -I sources/tools/fetch.py refetch
```

It skips files already present and prints a tally. What each label means:

- `fetched`: downloaded and matching the logged hash.
- `CHANGED`: the publisher's file differs from the one logged in November, so they've updated it. Keep
  the new file, note what changed, and re-log it with `record` (step 4).
- `MANUAL`: the four FFIEC zips, which come through a web form. Get them with:

```bash
python3 -I sources/tools/ffiec_bulk.py get 4
```

Saved web pages (the `.html` files under `snap_issuance`, `irs_refund_timing` and others) will usually show
`CHANGED`, because pages change with every visit. That's expected: the compiled tables in `sources/derived/`
already record what each page said on 2026-11-18.

## 3. The 19 blocked rows

For each row, open the landing page, find the file described, and save it into `sources/raw/<id>/` with
its original name. Use the script where the site allows it:

```bash
python3 -I sources/tools/fetch.py links <landing_url> '<pattern>'
```

```bash
python3 -I sources/tools/fetch.py get <id> <file_url>
```

If a site blocks the script but your browser works (BLS often does this), download in the browser, move the
file into `sources/raw/<id>/`, and log it:

```bash
python3 -I sources/tools/fetch.py record <id> <file_url> "<file name>"
```

| id | Landing page | Get | Notes |
|---|---|---|---|
| **atus_tables** | https://www.bls.gov/tus/tables.htm | 2025 annual tables | **Most important**: sets caregiving hours (plan group 1, item 2) |
| **atus_eldercare** | https://www.bls.gov/news.release/elcare.toc.htm | Release tables 1–4 (2023–24) | Same |
| **atus_microdata** | https://www.bls.gov/tus/data.htm | Latest single-year and multi-year respondent, activity and roster files, with codebooks | Time-of-day profiles; check sizes (multi-year files are large) |
| ssa_schedule_2027 | https://www.ssa.gov/pubs/EN-05-10031-2027.pdf | The PDF | |
| ftc_sentinel | https://www.ftc.gov (Consumer Sentinel Data Book) | 2025 Data Book PDF if posted, else 2024; Explore Data downloads for losses by age and payment method | Sets the heavy-tailed scam losses (T09) |
| payday_cfpb | https://www.consumerfinance.gov/data-research/research-reports/cfpb-data-points-payday-lending/ | Report PDF (2014) | |
| title_state_reports | https://www.tn.gov/tdfi.html | Latest title-pledge report | |
| **ce_pumd** | https://www.bls.gov/cex/pumd.htm | Latest Diary and Interview CSV files plus documentation (2024 or 2025) | Large: check each file's size; **anything over 1 GB, decide first** |
| nyfed_hhdc | https://www.newyorkfed.org/microeconomics/hhdc | Latest quarter's data XLSX | Links load by JavaScript, so use the browser and `record` |
| eviction_lab | https://evictionlab.org/eviction-tracking/ | Weekly filings CSV | |
| oews | https://www.bls.gov/oes/tables.htm | May 2025 national and national industry-occupation XLSX | |
| ncs_benefits | https://www.bls.gov/ebs/ | Latest benefits tables (paid sick leave by wage level) | |
| ndcp | https://www.dol.gov/agencies/wb/topics/featured-childcare | Latest county-level file | |
| ntd | https://www.transit.dot.gov/ntd/ntd-data | 2024 annual data tables and monthly ridership | |
| cms_dialysis | https://data.cms.gov/provider-data/topics/dialysis-facilities | Facility list CSV | |
| naws | https://www.dol.gov/agencies/eta/national-agricultural-workers-survey/data | Public data files and codebook | |
| h2a_disclosure | https://www.dol.gov/agencies/eta/foreign-labor/performance | FY2025 H-2A disclosure file | |
| nchs_vital | https://www.cdc.gov/nchs/nvss/marriage-divorce.htm | National marriage and divorce rate tables; natality and mortality summaries | |
| noaa_storm_events | https://www.ncei.noaa.gov/stormevents/ftp.jsp | `StormEvents_details` CSV.gz for 2015–2025, plus the format document | Replaces the storm and heat day counts in `sim/evidence/typed_days.py` |

Rules from `sources/README.md` still apply:
- A row that needs a sign-in is `needs_jason`.
- A row that isn't published, or is behind a form, is `not_available`, with a note on why.
- Don't take files from mirrors or aggregators.

## 4. Update the manifest

For each row you fetched, edit its entry in `ROW_INFO` in `sources/tools/finalize.py`:

- the vintage you found;
- the terms of use, copied from the publisher's page;
- a short note, replacing the "refuses requests from this cloud session" text.

Then run:

```bash
python3 -I sources/tools/finalize.py
```

It prints the rows by status and the total size. Run it as often as you like: it rebuilds the generated part
of each note (after `Log:`) every time.

## 5. Commit

Commit only the manifest, the log and any changed tools, never `sources/raw/`:

```bash
git add sources/manifest.csv sources/download_log.jsonl sources/tools/
```

```bash
git status --short
```

Check that nothing under `sources/raw/` is listed, then:

```bash
git commit -m "Halvern v2 phase 2: blocked downloads fetched from home connection"
```

```bash
git push -u origin halvern-v2-downloads-mac
```

Merge into `development`, not `main`.

## Prompt for Claude Code on the Mac

> I'm finishing phase 2 of the Halvern v2 data update in `mapping-synthetic-transactions/`. Read
> `sources/MAC-DOWNLOADS.md` and `sources/README.md` first, then do steps 1–5 of MAC-DOWNLOADS.md on a
> feature branch off `development`. Re-download the 22 logged rows with `refetch` and `ffiec_bulk.py`, then
> the 19 blocked rows, from the publishers' own sites only. Ask me before any file over 1 GB. Don't create
> accounts. Never commit `sources/raw/`. If a site blocks your requests, tell me which file to download in
> my browser and log it with `fetch.py record` once I've saved it. When done, report:
> - rows by status;
> - total size;
> - any file whose hash changed;
> - any vintage newer or older than `target_vintage`;
> - anything that changes the plan.
>
> Commit, but don't push until I've reviewed.
