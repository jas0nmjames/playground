# Medianville source downloads: instructions for Claude Code

Companion to `halvern-download-manifest.csv` (51 datasets) and `medianville-data-update-plan.md` (phase 2). Run in `playground/mapping-synthetic-transactions` on a feature branch; merge into `development`, never `main`.

## Setup

1. Copy `halvern-download-manifest.csv` to `sources/manifest.csv`.
2. Add `sources/raw/` to `.gitignore`. Commit the manifest and anything in `sources/derived/`, never the raw files.

## For each row, in tier order (1, then 2; 3 and 4 only when asked)

1. Open `landing_url`. The URLs are landing pages, not direct file links: find the file described in `get`, newest vintage first, and check it against `target_vintage`. If the page has moved, search the publisher's site; don't take files from mirrors or aggregators.
2. Download into `save_to` (`sources/raw/<id>/`). Keep the original file names and formats. Fetch the codebook or technical notes with every microdata file.
3. Fill in `downloaded_on`, `actual_vintage`, `files` (semicolon-separated), `bytes` and `sha256`, and set `status` to `fetched`. Copy the terms of use into `license_or_terms`.
4. If a file can't be had, set `status` to `not_available` (not published, discontinued or behind a form) or `needs_jason` (a registration or sign-in), with a note on why. Don't guess at contents.

## Rules

- **Size.** Rows marked `large` (CE microdata, MEPS, ACS PUMS, SIPP, CFPB complaints, PSID, HRS) can run to several GB. Ask before downloading anything over 1 GB.
- **Registration.** PSID and HRS need a free account in Jason's name. Mark them `needs_jason`; don't create accounts.
- **Compiled sources.** SNAP issuance schedules and 2027 holidays have no single file. Save the pages you used in `raw/`, and write the compiled table to `sources/derived/` with each row's source URL.
- **Real and synthetic stay apart.** These files set rates and distributions. No real person's words or record (complaint narratives especially) goes into a Medianville record.
- **Report back.** A table of rows by status, total size, anything newer or older than `target_vintage`, and every `needs_jason` row.
