# Medianville source downloads

The public datasets that set v2's rates. **Status (2026-11-22):** `manifest.csv` has 52 rows. All 42 rows in tiers 1 and 2 are `fetched`; the 10 in tiers 3 and 4 (ACS PUMS, NHTS, SIPP, JPMorgan Chase Institute, CFPB complaints; PSID, HRS, CBO, EIG, NOAA normals) are `to_fetch`, for later versions. `download_log.jsonl` records every file with its URL and SHA-256. Raw files stay out of git (`sources/raw/`); `tools/` builds the tables in `derived/` that the simulator reads, and `../sim/evidence_targets.csv` names the source behind each target. The About page lists them all. The real-accounts research that came before them is in [`../evidence/`](../evidence/). Finishing the downloads on a home connection is in [`MAC-DOWNLOADS.md`](MAC-DOWNLOADS.md).

## Instructions for Claude Code (phase 2, as written)

Companion to the manifest (written as `halvern-download-manifest.csv`, now `manifest.csv`) and [`medianville-data-update-plan.md`](../reference/medianville-data-update-plan.md) (phase 2). Run in `playground/mapping-synthetic-transactions` on a feature branch; merge into `development`, never `main`.

## Setup

1. Copy the download manifest to `sources/manifest.csv` (done).
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
