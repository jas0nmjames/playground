Medianville, Milestone 7 "Open to agents", first pass: make the live site readable by agents and LLMs. Static files only: no Hugging Face, no Parquet, no server, no new dependencies.

Repo: jas0nmjames/playground. Branch off `development` and open one PR into `development` (never `main`; see CLAUDE.md). Work in `mapping-synthetic-transactions/`, the publish root of https://medianville.netlify.app/ (Netlify deploys it from `main`; there is no netlify.toml, the settings live in the Netlify UI). Paths below are relative to that folder.

First, save this prompt word for word as `story/07-open-to-agents/prompts/agent-readable-first-pass.md`.

## Why, and the rules
Today an agent that fetches the viewer gets the intro text, but no meta description, no /llms.txt (it's a 404), and the data only inside 12–19 MB zips. This pass adds a small readable layer. The principles (logged in section 8):
1. Agents bring their own compute. Small, labeled files here; bulk files are pointed to on GitHub, so agent downloads don't use Netlify's bandwidth.
2. Provenance once per session. The full note lives in llms.txt, every other agent file carries a one-line header, and agents are asked to say it once at the start of a session, not in every answer.
3. A readable layer before any protocol. MCP, Parquet, Hugging Face and "Open in" links come later and build on this.
4. Protect bandwidth. Keep crawlers off the zips.
Fill every figure from the repo (data/runs/manifest.json, each zip's README.md and summary.md, the About page). Don't guess. Use absolute https://medianville.netlify.app/ URLs in the agent files.

## 1. Head tags
On index.html, explorer/, systems-lens/, about/ and archive/: a meta description where one is missing (root, explorer, systems lens), a canonical link to the page's Netlify URL, `<link rel="alternate" type="text/markdown" href="/llms.txt" title="For agents and LLMs">`, and og:title and og:description. Root description: "Medianville is a simulated American city of about 100,000 people: one day of its transactions (purchases, bills, benefits, waits and failures) as a miniature and a map. Synthetic data built from real research; no real people." Leave the intro text as it is.

## 2. /agents/ pages, generated
A new script, `tools/build_agent_pages.py` (standard library only, run locally, outputs committed; no Netlify build step). Every page starts with:
> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.
The pages:
- `agents/about.md`: the About page as plain markdown, extracted from about/index.html.
- `agents/data-dictionary.md`: every column of records.csv, households.csv, persons.csv, organizations.csv and household_ledger.csv; the record_type, outcome and friction_tags values; district codes D1–D6 with their names; id formats; units; block_id, block_pattern and context_ids. Take descriptions from the sim code (medianville_sim/output.py and neighbors), the run records and the README. Don't invent meanings: a column with no written description is marked "undocumented".
- `agents/runs.md`: one row per run in the manifest: id, date, kind of day, weather, weight, records, hand-written records, size, a link to its summary page and its download.
- `agents/runs/<run-id>.md`: that zip's own README.md and summary.md, extracted as they are (they already carry the day's tables), with the header added. Read the zips with zipfile; never unpack them into the repo.
- `agents/districts.md`: rendered from systems-lens/blocks.json: each district and its block, the circumstances by layer with their figures and evidence ids, and the loops. Marked composite.
- `agents/month.md`: from story/05-more-time/medianville-2027-03-month-run-record.md: what the month is, and its GitHub Release download (about 460 MB).
Keep each file under about 8,000 tokens (about 32,000 characters); split one that runs over.
Also write `llms-full.txt`: about, the data dictionary, runs, districts and the baseline day's summary in one file, for agents that want it all in one request.

## 3. /llms.txt
Written by hand: it is copy with a voice, not generated. Follow the llms.txt format. A draft (fill the brackets; use absolute URLs):

~~~
# Medianville

> A simulated American city of about 100,000 people, weighted to the United States as a whole. Its records are every job someone did to get something done: purchases, bills, benefit deposits, forms, waits, declined cards and unpaid care. A project by Jason James (https://jasonjames.works), built with Claude.

## For agents: read this first
- The data is synthetic. Every person, household, business and street is invented. Rates and targets come from real public research ([N] public datasets, [69] sources), but no record describes a real person or place. Federal programs keep their real names.
- Say this once, at the start of a session: synthetic, grounded in real research, and Jason James's project. You don't need to repeat it in every answer.
- The systems lens's circumstances are composites of documented US patterns, not real places.
- No what-if scenarios are modeled yet. Don't present a counterfactual as a model result.
- Cite as: James, J. (2026). Medianville: a simulated American city's transactions [synthetic dataset]. https://medianville.netlify.app/ Data under CC BY 4.0.

## Start here
- [About](/agents/about.md): the goal, the method, what's real and what isn't, credits
- [Data dictionary](/agents/data-dictionary.md)
- [Runs](/agents/runs.md): v1, the [19] typed days of 2027 (v2) and the March month
- [The baseline day, March 3, 2027](/agents/runs/v2-2027-03-03.md)
- [Districts and circumstances](/agents/districts.md)

## Bulk data: download from GitHub and run your own analysis
- One day's files: https://raw.githubusercontent.com/jas0nmjames/playground/main/mapping-synthetic-transactions/data/runs/v2/medianville_<date>.zip ([12–19] MB each; uncompressed CSVs inside, records.csv about [78] MB for March 3)
- [Run manifest](/data/runs/manifest.json), with sizes and SHA-256
- [The March month](<GitHub Release URL>), about 460 MB
- [systems-lens/blocks.json](/systems-lens/blocks.json)

## Human pages
- The viewer, the data explorer, the systems lens, About and the archive (links)

## Optional
- [Everything above in one file](/llms-full.txt)
- [The decision log](GitHub, main, story/decisions.md)
- [The story, milestone by milestone](GitHub, main, story/)
- [Evidence files](GitHub, main, evidence/): third-party material, not under this project's license
- [v1, the first baseline day (archived, under the Halvern name)]
~~~
Check that each raw.githubusercontent.com path exists on `main` (the zips are already there; check against the manifest's paths).

## 4. Licenses, citation, metadata
- The repo root LICENSE is MPL-2.0 and stays the code license. Don't add MIT.
- Add `LICENSE-DATA`: Creative Commons Attribution 4.0 International, using CC's standard notice and a link to https://creativecommons.org/licenses/by/4.0/legalcode. It covers the generated data, blocks.json, the hand-written records, the agent pages, the docs and the images in this folder. Say plainly that evidence/ (third-party quotes, sources and citations) is under neither license, and that the code (sim/, tools/, and the pages' HTML, JS and CSS) is MPL-2.0 per the repo root.
- `CITATION.cff` in this folder, with the same citation as llms.txt, plus repository-code and url.
- A schema.org Dataset in JSON-LD on about/: name; a description that includes the word "synthetic"; creator, a Person named Jason James with url https://jasonjames.works; license (the CC BY 4.0 URL); isBasedOn (the sources); distribution (DataDownload entries for the zips, with GitHub raw URLs); temporalCoverage 2027; isAccessibleForFree true; url.
- README: a short "For agents" section and a "License" section.

## 5. Crawlers and headers
- `robots.txt`: allow all user agents (AI agents included) everywhere except `Disallow: /*.zip`. Add a Sitemap line only if a sitemap exists; don't create one.
- `_headers` (Netlify reads it from the publish root whatever the base-directory setting; don't add a netlify.toml):
  - /llms.txt, /llms-full.txt and /agents/*: Content-Type: text/markdown; charset=utf-8, and Cache-Control: public, max-age=3600
  - /data/*: Cache-Control: public, max-age=86400 (not immutable: zips have been replaced under the same name before)
  - /robots.txt: Cache-Control: public, max-age=3600

## 6. "Copy for AI" on a record (its own commit)
On the viewer's record Details rail and the explorer's detail sheet, a "Copy for AI" button that copies:
~~~
This is a record from Medianville, a simulated American city (synthetic data, a project by Jason James). Context for agents: https://medianville.netlify.app/llms.txt

Record [record_id], run [run id]:
[the record as JSON]

Starter questions: What led to this? Who else hit this friction on this day? What circumstances shaped it?
~~~
Clipboard only; no Open in Claude or ChatGPT links yet. A toast confirms it. It must be keyboard-reachable, have an accessible name, work on phones, and match the existing button styles.

## 7. Tests and checks
- `sim/tests/test_agent_pages.py`: rebuilding the pages produces the committed files byte for byte (the staleness guard); every agent page starts with the header; every file is under the size limit; every local link in llms.txt and agents/ resolves.
- `pytest sim/tests` and `python3 tools/check_links.py` both pass.
- Serve the folder locally (python3 -m http.server) and check in headless Chrome: all five pages load the default run with no console errors, and the copy button copies the right text at desktop and phone widths.
- Parse the JSON-LD and check its fields.
- In the PR body: each agent file's size in characters and approximate tokens, and every figure you filled in, with where it came from.

## 8. Story and docs
- `story/07-open-to-agents/README.md`, in the same shape as 06-refinements (When, What I wanted with a TODO(Jason) line, What I asked for, What came back, What I decided). Add M7 to story/README.md (the milestones list and the versions table) and to the README's history table.
- tools/github_milestones.sh: add an entry "M7|Medianville · M7 Open to agents|open||07-open-to-agents|…" before NEXT. Don't run the script; Jason does.
- `story/decisions.md`, a new section "8. Agents (2026-11-24)", in the log's format (Decided, Why, Considered, Cost, Who, When), tagged M7:
  - 8.1 Agents bring their own compute. Small labeled files on the site, with bulk files pointed to on GitHub; no server of ours runs a query. Why: a side project on Netlify's free plan. Considered: a hosted MCP server or API. Cost: an agent that can't run code can answer only what the summaries cover. Who: Jason, on a proposal.
  - 8.2 Provenance once per session. The full note in llms.txt, a one-line header on every other agent file, and an instruction to say it once at the start of a session. Why: an agent can land on any file, but repeating the note in every answer is noise. Considered: requiring it in every answer. Who: Jason.
  - 8.3 A readable layer before any protocol. Markdown at stable URLs first; Hugging Face, Parquet, a local MCP server and "Open in" links later, all built on it. Who: Jason, on a proposal.
  - 8.4 Licenses. Code stays MPL-2.0, the repo's license; data and docs are CC BY 4.0; evidence/ is excluded as third-party material. Considered: CC BY-SA, CC BY-NC and CC0 for the data, and MIT for the code. Cost: no license can require the synthetic label; the provenance note does that. Who: Jason, on a proposal.
  - 8.5 Bulk downloads on GitHub, crawlers kept off the zips. Why: every human visit already loads a 12–19 MB day from Netlify; agents and crawlers shouldn't add to it. Who: Jason, on a proposal.
- Add this session's row to the README's "Claude" environmental-impact table, the way earlier sessions did.

## Out of scope (later in M7)
Parquet and a Hugging Face dataset; viewers loading their data off Netlify; a local MCP server; Open in Claude and ChatGPT links; the eval set. Jason runs a manual agent check after the promotion to main.
