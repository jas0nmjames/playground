#!/usr/bin/env python3
"""Write the pages for agents and LLMs: agents/*.md, llms-full.txt and the JSON-LD on about/.

    python3 tools/build_agent_pages.py           # from mapping-synthetic-transactions/: write the pages
    python3 tools/build_agent_pages.py --check   # write nothing; exit 1 if a committed page is stale

Standard library only. Run it locally and commit what it writes; Netlify serves the files as they are,
with no build step. llms.txt is written by hand and is not touched here (llms-full.txt starts with it).

What it reads, all from this folder:
- about/index.html                          -> agents/about.md
- the generator prompt, the run READMEs, the simulator's output code and the baseline day's tables
                                            -> agents/data-dictionary.md (descriptions written below, each with its source)
- data/runs/manifest.json                   -> agents/runs.md
- each run's zip (README.md and summary.md, read with zipfile; nothing is unpacked)
                                            -> agents/runs/<run id>.md
- systems-lens/blocks.json                  -> agents/districts.md (and agents/districts/<block>.md if it runs long)
- story/05-more-time/medianville-2027-03-month-run-record.md
                                            -> agents/month.md
- the manifest, sources/manifest.csv and the About page's calibration anchors
                                            -> the schema.org Dataset (JSON-LD) in about/index.html, between
                                               <script type="application/ld+json" id="dataset-jsonld"> and </script>

Every page starts with HEADER and stays under LIMIT characters (about 8,000 tokens); a page that would run
over is split. sim/tests/test_agent_pages.py rebuilds everything and compares it with the committed files.
"""
import csv
import io
import json
import os
import posixpath
import re
import sys
import zipfile
from collections import Counter
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)

SITE = "https://medianville.netlify.app/"
GH = "https://github.com/jas0nmjames/playground/blob/main/mapping-synthetic-transactions/"
GH_TREE = "https://github.com/jas0nmjames/playground/tree/main/mapping-synthetic-transactions/"
RAW = "https://raw.githubusercontent.com/jas0nmjames/playground/main/mapping-synthetic-transactions/"
HEADER = "> Synthetic data from Medianville, a project by Jason James. Read https://medianville.netlify.app/llms.txt first.\n"
LIMIT = 32000  # characters, about 8,000 tokens

MONTH_RECORD = "story/05-more-time/medianville-2027-03-month-run-record.md"
PROMPT = "story/01-one-day/medianville-transaction-generator-prompt.md"


def path(*p):
    return os.path.join(PROJECT, *p)


def read(rel):
    with open(path(rel), encoding="utf-8") as f:
        return f.read()


def fmt(n):
    return "{:,}".format(n)


def page(body):
    """A page: the header, a blank line, then the body, ending in one newline."""
    return HEADER + "\n" + body.strip("\n") + "\n"


# ─── relative links in a repo document, made absolute ──────────────────────────────────────────────────────────
MD_LINK = re.compile(r"(\]\()([^)\s]+)(\))")


def absolute_links(text, src_rel):
    """Rewrite the relative links of a Markdown file at src_rel (relative to this folder) to GitHub on main."""
    base = posixpath.dirname(src_rel)

    def fix(m):
        url = m.group(2)
        if re.match(r"^[a-z]+:", url) or url.startswith(("#", "/")):
            return m.group(0)
        target, _, anchor = url.partition("#")
        p = posixpath.normpath(posixpath.join(base, target))
        full = (GH_TREE if not posixpath.splitext(p)[1] else GH) + p + ("#" + anchor if anchor else "")
        return m.group(1) + full + m.group(3)

    return MD_LINK.sub(fix, text)


# ─── about/index.html as Markdown ──────────────────────────────────────────────────────────────────────────────
class AboutToMarkdown(HTMLParser):
    """Just enough HTML to Markdown for the About page: headings, paragraphs, lists, a definition list, links."""

    SKIP = {"style", "script", "head", "header", "nav"}

    def __init__(self, page_url):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.out = []          # finished blocks
        self.buf = []          # the block being written
        self.skip = 0
        self.lists = []        # "ul" or "ol" counters
        self.links = []
        self.block = None
        self.in_article = False
        self.in_footer = False

    def url(self, href):
        """A link on about/index.html, made absolute on the Netlify site."""
        if re.match(r"^[a-z]+:", href):
            return href
        if href.startswith("#"):
            return self.page_url + href
        trail = href.endswith("/")
        p = posixpath.normpath(posixpath.join("about", href))
        p = "" if p == "." else p
        return SITE + p + ("/" if trail and p else "")

    def flush(self):
        text = re.sub(r"[ \t\r\n]+", " ", "".join(self.buf)).strip()
        self.buf = []
        if not text:
            return
        kind = self.block
        if kind in ("h1", "h2", "h3"):
            self.out.append("#" * int(kind[1]) + " " + text)
        elif kind == "li":
            depth = len(self.lists) - 1
            marker = "-" if self.lists[-1] == "ul" else "1."
            self.out.append("  " * depth + marker + " " + text)
        elif kind == "dt":
            self.out.append("**" + text + "**")
        elif kind == "dd":
            self.out.append(text)
        else:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP or (tag == "a" and a.get("class") == "skip"):
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "article":
            self.in_article = True
        if tag == "footer":
            self.in_footer = True
        if not (self.in_article or self.in_footer):
            return
        if tag == "span" and "chip" in (a.get("class") or ""):
            self.skip += 1
            return
        if tag in ("h1", "h2", "h3", "p", "li", "dt", "dd"):
            self.flush()
            self.block = tag
        elif tag in ("ul", "ol"):
            self.flush()
            self.lists.append(tag)
        elif tag == "a":
            self.links.append(self.url(a.get("href", "")))
            self.buf.append("[")
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "cite", "i"):
            self.buf.append("*")
        elif tag == "br":
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip -= 1
            return
        if self.skip:
            if tag == "span":
                self.skip -= 1
            return
        if tag == "a" and self.links:
            self.buf.append("](%s)" % self.links.pop())
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "cite", "i"):
            self.buf.append("*")
        elif tag in ("h1", "h2", "h3", "p", "li", "dt", "dd"):
            self.flush()
            self.block = None
        elif tag in ("ul", "ol"):
            self.flush()
            self.lists.pop()
        elif tag == "article":
            self.flush()
            self.in_article = False
        elif tag == "footer":
            self.flush()
            self.in_footer = False

    def handle_data(self, data):
        if self.skip or not (self.in_article or self.in_footer):
            return
        self.buf.append(data)


def about_md():
    p = AboutToMarkdown(SITE + "about/")
    p.feed(read("about/index.html"))
    p.flush()
    blocks, lines = p.out, []
    for i, b in enumerate(blocks):
        is_li = re.match(r"^\s*(-|1\.) ", b)
        prev_li = i > 0 and re.match(r"^\s*(-|1\.) ", blocks[i - 1])
        if lines and not (is_li and prev_li):
            lines.append("")
        lines.append(b)
    # the page links to the repo on development until Jason promotes it; these pages are served from main
    body = re.sub(r"(github\.com/jas0nmjames/playground/(?:blob|tree))/development/", r"\1/main/", "\n".join(lines))
    intro = ("The About page of https://medianville.netlify.app/about/ as plain Markdown, written from about/index.html "
             "by tools/build_agent_pages.py. Links into the repository point at its main branch.\n\n")
    return page(intro + body)


# ─── the run's tables ──────────────────────────────────────────────────────────────────────────────────────────
def manifest():
    with open(path("data", "runs", "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def run_by_id(m, rid):
    return next(r for r in m["runs"] if r["id"] == rid)


def zip_member(zpath, name):
    """The bytes of the member whose path ends in /name (the shortest such path), or None."""
    with zipfile.ZipFile(path(zpath)) as z:
        names = sorted((n for n in z.namelist() if n == name or n.endswith("/" + name)), key=len)
        return z.read(names[0]).decode("utf-8") if names else None


def table_rows(zpath, name):
    with zipfile.ZipFile(path(zpath)) as z:
        member = sorted((n for n in z.namelist() if n.endswith("/" + name)), key=len)[0]
        with z.open(member) as f:
            yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline=""))


MULTI = {"friction_tags", "lens_tags", "context_ids", "benefits_received", "accepts", "caregiver_for"}


def value_counts(zpath, name, cols):
    """Counts of each value (each item, for ;-separated columns) and the header, from one table of a run."""
    counts = {c: Counter() for c in cols}
    header, n = None, 0
    for row in table_rows(zpath, name):
        if header is None:
            header = list(row.keys())
        n += 1
        for c in cols:
            v = row[c]
            if c in MULTI:
                for x in (v.split(";") if v else [""]):
                    counts[c][x] += 1
            elif c == "job_category":
                counts[c][v.split(".", 1)[0]] += 1
            else:
                counts[c][v] += 1
    return header, n, counts


# ─── data dictionary ───────────────────────────────────────────────────────────────────────────────────────────
# Each column: (description, sources). The descriptions say what the repo says, in its words where it can; a
# column nothing describes in writing says "undocumented". Source keys are listed in SOURCES.
SOURCES = [
    ("prompt", "the generator prompt the first run was made from, " + GH + PROMPT + " (\"Output files\")"),
    ("v1 README", "the README.md inside the v1 zip, " + RAW + "data/medianville_2027-03-03.zip (\"Reading records.csv\")"),
    ("day README", "the README.md inside each v2 zip (\"Files\"); see " + SITE + "agents/runs/v2-2027-03-03.md"),
    ("summary", "the run's summary.md; the baseline day's is in " + SITE + "agents/runs/v2-2027-03-03.md"),
    ("README", "the project README, " + GH + "README.md"),
    ("explorer", "the label the data explorer gives the column, " + SITE + "explorer/"),
    ("output.py", "the code that writes the tables, " + GH + "sim/medianville_sim/output.py"),
    ("engine.py", "the code that writes each record, " + GH + "sim/medianville_sim/engine.py"),
    ("blocks.py", "the code that tags records with the systems lens's blocks, " + GH + "sim/medianville_sim/blocks.py"),
    ("population.py", GH + "sim/medianville_sim/population.py"),
    ("config.py", GH + "sim/medianville_sim/config.py"),
    ("text.py", GH + "sim/medianville_sim/text.py"),
    ("sample_records.py", "the tool that prints records as cards for reading, " + GH + "tools/sample_records.py"),
    ("month record", SITE + "agents/month.md"),
]

U = "undocumented"
DICT = {
    "records.csv": [
        ("record_id", "One row per transaction, encounter or job attempt. `R` and 7 digits; the table is in time order. Ids start again at R0000001 in every run (and every day of the month), so name a record by its run and id.", "prompt, day README, month record"),
        ("timestamp_local", "When the record started (the explorer's \"Started\"), as `YYYY-MM-DDTHH:MM:SS` on the simulated date. The engine keeps every record inside the day's 1,440 minutes.", "explorer, engine.py"),
        ("record_type", "One of 12 kinds (values below). The prompt lists them without defining each.", "prompt"),
        ("job_category", "`category.kind`, for example `food.grocery_snap_purchase`. 383 distinct on the v2 baseline day (367 in v1). Categories below.", "v1 README, summary"),
        ("job_statement", "\"When [situation], I want to [motivation], so I can [outcome].\" Written from the actor's point of view, in plain words. Templated, except the hand-written records.", "prompt, v1 README"),
        ("actor_person_id", "A person id (`P…`). The prompt writes `job_statement` from the actor's point of view; no fuller definition is written down.", "v1 README, prompt"),
        ("household_id", "A household id (`H…`), as in households.csv. Otherwise undocumented.", "v1 README"),
        ("from_party_id", "The party the record goes from: `P…` people, `H…` households, `O…` organizations, including outside parties such as the Treasury, card networks and \"Customers (general public)\". The viewer draws each record as an arc from one party to the other.", "v1 README, README"),
        ("to_party_id", "The party the record goes to; ids as in `from_party_id`.", "v1 README, README"),
        ("beneficiary_person_id", "A person id. The record-reading tool labels it \"For\" when it differs from the actor. Otherwise undocumented.", "sample_records.py"),
        ("district", "District code, D1 to D6 (table below).", "prompt"),
        ("channel", "in_person, online, app, phone, mail or automatic.", "prompt"),
        ("payment_method", "cash, debit, credit, prepaid, ebt_snap, ebt_cash, wic, check, ach, p2p_app, bnpl, money_order, paycard, payroll_deduction, insurance or none.", "prompt"),
        ("amount_gross", "The face amount, in dollars: the price including sales tax and before fees; for a transfer the amount moved; for a prescription the cash price; for a public service the full cost of providing it.", "v1 README"),
        ("amount_paid_by_user", "What left the person's pocket, fees included (often 0).", "v1 README, prompt"),
        ("amount_paid_by_third_party", "What an insurer, program or agency paid.", "v1 README"),
        ("third_party_payer", "Names who paid `amount_paid_by_third_party`: the program, insurer or agency.", "v1 README, prompt"),
        ("funding_level", "federal, state, local, mixed, private or philanthropic.", "prompt"),
        ("imputed_public_cost", "The full cost of a public service whether or not anyone was charged; the estimates are in assumptions.csv.", "v1 README, prompt"),
        ("sales_tax", "Included in `amount_gross`, at 7% on taxable goods (groceries and prescriptions exempt).", "v1 README, config.py"),
        ("fee_type", "The kind of fee, such as `overdraft_fee` or `late_fee`; `+` joins two (`late_fee+postage`).", "text.py"),
        ("fee_amount", "The fee in dollars. Fees include overdraft, late, ATM, check-cashing, money-order, convenience, delivery, card-interest and loan finance charges. A fee above 0 adds the `fee` friction tag.", "summary, engine.py"),
        ("time_minutes", "Time spent, in minutes (the explorer's \"Time spent\"). It counts the wait but not the travel.", "explorer, README, engine.py"),
        ("wait_minutes", "Waiting, in minutes (the explorer's \"Waiting\"). A wait of 20 minutes or more adds the `wait` friction tag.", "explorer, engine.py"),
        ("travel_miles", "Travel, in miles. Distances come from a district-to-district table, so some single trips look long for the errand. 24 miles or more adds the `distance` friction tag.", "explorer, v1 README, engine.py"),
        ("travel_mode", "The explorer's \"Travel mode\". Otherwise undocumented (values below).", "explorer"),
        ("outcome", "completed, partial, declined, abandoned, rescheduled or failed. A record \"didn't work\" when it is a `failed_attempt` or ended declined, abandoned, failed or rescheduled; partial counts as worked.", "prompt, README"),
        ("friction_tags", "What got in the way, `;`-separated, from the 22 tags below; empty for none. The engine adds `fee`, `wait` and `distance` by rule (above).", "prompt, engine.py"),
        ("lens_tags", "Which perspective would flag this record, `;`-separated (values below). Not the systems lens: that is `block_id`, `block_pattern` and `context_ids`.", "prompt, README"),
        ("related_record_id", "Links records: every paycheck has linked rows for income tax withholding and FICA; a Social Security deposit shows the gross benefit and the Part B premium is a linked row; a retry points to the attempt that failed.", "v1 README"),
        ("narrative", "One short sentence of context. Hand-written narratives start with `[detailed]` (300 on the v2 baseline day, 500 in v1).", "prompt, day README"),
        ("block_id", "The block whose household made the record, or empty.", "blocks.py"),
        ("block_pattern", "The first pattern in that block the record matches, or empty.", "blocks.py"),
        ("context_ids", "The circumstances that pattern links to, separated by `;`.", "blocks.py"),
    ],
    "households.csv": [
        ("household_id", "`H` and 5 digits.", "v1 README"),
        ("district", "D1 to D6.", "prompt"),
        ("weight", "1 for the full city and larger when you run a sample (written as 1 ÷ the run's scale). Every published run is the full city.", "v1 README, output.py"),
        ("household_type", "Values below. People in nursing homes, the jail, dorms, shelters and group homes are one-person units with a type starting `group_quarters:`. The other codes are not defined one by one.", "v1 README"),
        ("size", "The number of members.", "output.py"),
        ("annual_income", "The household's annual income, rounded to the dollar; the summary gives its median in 2027 dollars.", "output.py, summary"),
        ("income_source_mix", "Each source's share of income, `source:share` separated by `;`, largest first, sources under 0.5% left out; `none` with no income. Sources: wages, self_employment, social_security, ssi, pension, investments_and_retirement_draws, unemployment_insurance, va_compensation, child_support, tanf.", "output.py"),
        ("alice_status", "poverty, alice or above. Below United For ALICE's survival-budget threshold means in poverty or employed but unable to afford basics.", "prompt"),
        ("banked_status", "banked, underbanked or unbanked.", "prompt"),
        ("housing_tenure", U + " (values below).", ""),
        ("monthly_housing_cost", U + "; whole dollars.", "output.py"),
        ("vehicles", U + "; a count (values below).", ""),
        ("internet_at_home", "yes, no or mobile_only.", "prompt"),
        ("primary_language", U + " (values below).", ""),
        ("notes", "Free text, often empty; households with SNAP carry `snap_monthly=<n>`.", "output.py"),
        ("block_id", "The mapped block the household lives on, or empty.", "v1 README"),
    ],
    "persons.csv": [
        ("person_id", "`P` and 6 digits.", "v1 README"),
        ("household_id", "The person's household.", "output.py"),
        ("age", U + ".", ""),
        ("birth_cohort", "The generation and birth year, for example `millennial_1987`. Generations by birth year: gen_alpha 2013 on, gen_z 1997, millennial 1981, gen_x 1965, baby_boomer 1946, silent 1928, greatest before.", "v1 README, config.py"),
        ("sex", U + " (F or M).", ""),
        ("race_ethnicity", U + " (values below).", ""),
        ("relationship_to_head", U + " (values below).", ""),
        ("education", U + " (values below; `not_applicable` when none is set).", "output.py"),
        ("disability", "none, or the type (values below).", "prompt"),
        ("health_coverage", U + " (values below).", ""),
        ("employment_status", U + " (values below).", ""),
        ("occupation", U + "; free text, such as `line cook`.", ""),
        ("employer_org_id", "The employer's organization id, or empty.", "output.py"),
        ("industry_sector", "The employer's sector: one of the 21 sectors of the prompt's economy table, or empty when none is set.", "prompt"),
        ("union_member", "yes or no.", "prompt"),
        ("work_schedule", "fixed, variable, night or none.", "prompt"),
        ("pay_cadence", "weekly, biweekly, semimonthly, monthly, irregular or none.", "prompt"),
        ("caregiver_for", "The person ids this person cares for, `;`-separated, or none.", "prompt, output.py"),
        ("benefits_received", "`;`-separated, or none. Social Security and SSDI carry their pay day: `(pay:3rd)` for long-time beneficiaries, people who also get SSI and people whose Medicare premium the state pays; otherwise `(pay:wed2)`, `(pay:wed3)` or `(pay:wed4)`, the second, third or fourth Wednesday, by birthday (1st to 10th, 11th to 20th, 21st on). SSI and VA compensation `(pay:1st)`; SNAP `(issue_day:N)`, the day of the month it is loaded.", "output.py, population.py, summary"),
    ],
    "organizations.csv": [
        ("org_id", "`O` and 4 digits; outside parties included.", "v1 README"),
        ("name", "Invented, like every business and local agency; federal programs and agencies keep their real names.", "day README, v1 README"),
        ("org_type", "business, nonprofit, government, religious or financial.", "prompt"),
        ("sector", "The sector (values below).", "prompt"),
        ("district", "D1 to D6, or `outside` for parties outside the city.", "output.py"),
        ("size_employees", U + "; empty for outside parties.", "output.py"),
        ("accepts", "The payment methods it takes, `;`-separated.", "prompt"),
        ("hours", U + "; `HH:MM-HH:MM`.", ""),
        ("notes", "Free text; employers in the city carry `medianville_residents_on_staff=<n>`.", "output.py"),
    ],
    "household_ledger.csv": [
        ("household_id", "The household.", "output.py"),
        ("wallets", "The number of the household's wallets. Otherwise undocumented.", "output.py"),
        ("open_checking", "Checking at the start of the day, in dollars, summed over the household's wallets; the same for each `open_` and `close_` column.", "output.py"),
        ("open_cash", "Cash at the start of the day.", "output.py"),
        ("open_prepaid", "Prepaid cards at the start of the day.", "output.py"),
        ("open_savings", "Savings at the start of the day.", "output.py"),
        ("open_card_debt", "Credit card balance owed at the start of the day.", "output.py"),
        ("inflows", "Money in during the day.", "output.py"),
        ("outflows", "Money out during the day.", "output.py"),
        ("close_checking", "Checking at the end of the day.", "output.py"),
        ("close_cash", "Cash at the end of the day.", "output.py"),
        ("close_prepaid", "Prepaid cards at the end of the day.", "output.py"),
        ("close_savings", "Savings at the end of the day.", "output.py"),
        ("close_card_debt", "Credit card balance owed at the end of the day.", "output.py"),
        ("open_net", "checking + cash + prepaid + savings − card debt, at the start of the day.", "output.py"),
        ("close_net", "The same at the end of the day.", "output.py"),
        ("reconciles", "yes when `open_net + inflows − outflows` equals `close_net` to within 6 cents. \"The money reconciles.\"", "output.py, day README"),
        ("snap_open", "The SNAP balance at the start of the day.", "output.py"),
        ("snap_close", "The SNAP balance at the end of the day.", "output.py"),
        ("could_cover_400_emergency", "yes or no. The SHED anchor: 63% of adults would cover a $400 emergency with cash or its equivalent; the run solves a liquid-funds threshold ($4,263 on the baseline day) or $400 free on a card paid in full.", "output.py, summary"),
    ],
    "public_services_context.csv": [
        ("agency_or_service", "One row per agency or service, with its approximate daily operating cost and main funding source, so analysts can see the full public budget behind the day.", "prompt"),
        ("level", "federal, state or local.", "prompt"),
        ("daily_operating_cost_estimate", "The approximate daily operating cost, in dollars.", "prompt"),
        ("main_funding_source", "The main funding source; free text.", "prompt"),
        ("notes", U + "; free text.", ""),
    ],
    "assumptions.csv": [
        ("assumption", "Every estimate, its value, a one-line rationale, and whether it is an anchor or an estimate.", "v1 README"),
        ("value", "The value.", "prompt"),
        ("rationale", "A one-line rationale.", "v1 README"),
        ("source_or_estimate", "Whether it is an anchor or an estimate, and its source.", "v1 README, prompt"),
    ],
}

# The values listed under each table, counted on the baseline day (multi-value columns count each item).
VALUES = {
    "records.csv": ["record_type", "outcome", "friction_tags", "lens_tags", "channel", "payment_method", "funding_level",
                    "travel_mode", "job_category", "district", "block_id"],
    "households.csv": ["household_type", "housing_tenure", "alice_status", "banked_status", "internet_at_home", "vehicles", "primary_language"],
    "persons.csv": ["sex", "race_ethnicity", "relationship_to_head", "education", "disability", "health_coverage", "employment_status",
                    "work_schedule", "pay_cadence"],
    "organizations.csv": ["org_type", "district", "sector"],
}
FRICTIONS = ("wait, distance, no_transit, hours_mismatch, missing_document, language, disability_access, digital_barrier, fee, "
             "insufficient_funds, pending_hold, benefits_cliff, eligibility_confusion, out_of_stock, outage, caregiving_conflict, "
             "schedule_volatility, scam_attempt, price_spike, paperwork, repeat_trip, other").split(", ")
DISTRICTS = [  # from the generator prompt's district table
    ("D1", "Downtown and core neighborhoods", "31%", "Dense, transit-served, renters, government offices, night shifts"),
    ("D2", "Inner suburbs", "20%", "Older housing and apartments, immigrant gateways, airport and service jobs"),
    ("D3", "Outer suburbs", "22%", "New-build subdivisions, car-dependent, big-box retail, long commutes"),
    ("D4", "Satellite city", "13%", "Historic downtown, regional hospital, county seat, mixed old and new industry"),
    ("D5", "Rural town", "8%", "County seat of a few thousand, dollar stores, thin services, long drives"),
    ("D6", "Open country", "6%", "Farms, scattered homes, well water, distance to everything"),
]


def check_prompt_districts():
    """The district table above must match the generator prompt's, word for word."""
    text = read(PROMPT)
    for code, name, share, char in DISTRICTS:
        row = "| %s | %s | %s | %s |" % (code, name, share, char)
        if row not in text:
            raise SystemExit("district table no longer matches %s: %s" % (PROMPT, row))
    for t in FRICTIONS:
        if t not in text:
            raise SystemExit("friction tag %s not in %s" % (t, PROMPT))


def counts_line(counter, total=None, empty="(empty)"):
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return ", ".join("`%s` %s" % (k, fmt(v)) if k else "%s %s" % (empty, fmt(v)) for k, v in items)


def data_dictionary(m):
    check_prompt_districts()
    base = run_by_id(m, m["default"])
    zp = base["path"]
    blocks = json.load(open(path("systems-lens", "blocks.json"), encoding="utf-8"))
    out = []
    out.append("# Data dictionary\n")
    out.append("Every column of the tables in a Medianville run, what each value means, and where that is written down. "
               "Columns nothing in the repository describes are marked *undocumented*: read their values, not a meaning. "
               "Counts are from the baseline day, `%s` (%s records), unless a column says otherwise. "
               "Every table is synthetic: no row describes a real person, household, business or place.\n" % (base["id"], fmt(base["records"])))
    out.append("## The files in a run\n")
    out.append("A run is one zip (download links in %sagents/runs.md). Inside a v2 zip, under `medianville_<date>/`:\n" % SITE)
    out.append("- `records.csv`: every record of the day, one job someone was trying to get done, in time order.\n"
               "- `households.csv`, `persons.csv`, `organizations.csv`: who is in the city.\n"
               "- `household_ledger.csv`: each household's opening and closing balances; the money reconciles.\n"
               "- `public_services_context.csv`, `assumptions.csv`, `summary.md`: what public services cost, every estimate and its source, and the day in figures.\n"
               "- `blocks.json`: the systems lens's mapped blocks (%sagents/districts.md).\n"
               "- `simulate.py`, `medianville_sim/`: the simulator. `SHA256SUMS`: the SHA-256 of every file.\n"
               "- The baseline day only: `detailed_overrides.csv` and `detailed_sample.csv`, the hand-written text and the hand-written records on their own.\n" % SITE)
    out.append("The v1 zip keeps its tables under `medianville/out/` and its 500 hand-written records in `detailed_sample_500.csv`. "
               "The carried month adds `links.csv` to each day (%sagents/month.md).\n" % SITE)
    out.append("## Units and formats\n")
    out.append("- Money: US dollars, two decimals in records.csv and household_ledger.csv, whole dollars for `annual_income` and `monthly_housing_cost`. "
               "Dollar figures are 2027 dollars where the summary says so (the median household income).\n"
               "- Time: minutes (`time_minutes`, `wait_minutes`); `timestamp_local` is `YYYY-MM-DDTHH:MM:SS`, local to the city.\n"
               "- Distance: miles (`travel_miles`).\n"
               "- Lists inside a cell are separated by `;`. Empty means none.\n"
               "- Text is UTF-8 CSV with a header row.\n")
    out.append("## Ids\n")
    out.append("| Id | Format | Example | Table |\n|---|---|---|---|\n"
               "| Record | `R` + 7 digits | `R0000001` | records.csv (restarts in every run and every day) |\n"
               "| Household | `H` + 5 digits | `H05202` | households.csv |\n"
               "| Person | `P` + 6 digits | `P011429` | persons.csv |\n"
               "| Organization | `O` + 4 digits | `O1076` | organizations.csv (outside parties included) |\n"
               "| Run | `v<version>-<date>` | `v2-2027-03-03` | data/runs/manifest.json |\n"
               "| Block | a lowercase name | `larkin` | blocks.json `blocks[].id` |\n"
               "| Pattern | letters and a number, per block | `R3` | blocks.json `patterns[].id` (unique within a block, not across blocks) |\n"
               "| Circumstance | letters and a number, per block | `EC1`, `DH1` | blocks.json `contexts[].id`; the D… ids are the district tier |\n"
               "| Evidence | `E` + 3 digits | `E009` | evidence/evidence.csv on GitHub (third-party material) |\n")
    out.append("## Districts\n")
    out.append("Shares are the prompt's targets; the baseline day's are in its summary (30.5 / 19.7 / 21.6 / 14.3 / 7.9 / 6.0%). "
               "Each district has one mapped block in the systems lens.\n")
    out.append("| Code | District | Share of residents | Character | Mapped block |\n|---|---|---|---|---|")
    bmap = {b["district"]: b for b in blocks["blocks"]}
    for code, name, share, char in DISTRICTS:
        b = bmap.get(code)
        out.append("| %s | %s | %s | %s | %s |" % (code, name, share, char, "%s (`%s`)" % (b["name"], b["id"]) if b else ""))
    out.append("")

    for r in m["runs"]:  # every published run has the same columns as the baseline day
        with zipfile.ZipFile(path(r["path"])) as z:
            for table, cols in DICT.items():
                member = sorted((n for n in z.namelist() if n.endswith("/" + table)), key=len)[0]
                got = next(csv.reader(io.TextIOWrapper(z.open(member), encoding="utf-8", newline="")))
                if got != [c for c, _, _ in cols]:
                    raise SystemExit("%s in %s has columns %s, not the dictionary's" % (table, r["id"], got))
    out.append("Every published run, v1 included, has exactly these columns in each table.\n")

    names = {"records.csv": "records.csv", "households.csv": "households.csv", "persons.csv": "persons.csv",
             "organizations.csv": "organizations.csv", "household_ledger.csv": "household_ledger.csv",
             "public_services_context.csv": "public_services_context.csv", "assumptions.csv": "assumptions.csv"}
    for table, cols in DICT.items():
        header, n, counts = value_counts(zp, table, VALUES.get(table, []))
        documented = [c for c, _, _ in cols]
        if header != documented:
            raise SystemExit("%s: the columns in %s are %s, the dictionary has %s" % (table, zp, header, documented))
        out.append("## %s\n" % names[table])
        out.append("%s rows on the baseline day, %d columns.\n" % (fmt(n), len(header)))
        out.append("| Column | Meaning | Source |\n|---|---|---|")
        for c, desc, src in cols:
            out.append("| `%s` | %s | %s |" % (c, desc.replace("|", "\\|"), src or "—"))
        out.append("")
        for c in VALUES.get(table, []):
            label = "categories (the part before the dot)" if c == "job_category" else "values"
            out.append("**`%s` %s:** %s.\n" % (c, label, counts_line(counts[c])))
    out.append("## Sources\n")
    for k, v in SOURCES:
        out.append("- **%s**: %s" % (k, v))
    return page("\n".join(out))


# ─── runs ──────────────────────────────────────────────────────────────────────────────────────────────────────
def readme_field(readme, field):
    m = re.search(r"^\| %s \| (.+?) \|$" % re.escape(field), readme or "", re.M)
    return m.group(1) if m else None


def mb(b):
    return "%.1f MB" % (b / 1e6)


def run_files(r):
    readme = zip_member(r["path"], "README.md")
    summary = zip_member(r["path"], "summary.md")
    return readme, summary


def runs_md(m, files):
    out = ["# Runs\n"]
    out.append("Every published run of Medianville: v1, the first baseline day, and v2, the baseline day and the 18 typed days "
               "that stand for 2027 (their weights add up to the 365 days of the year). Each is one simulated day of the whole city; "
               "nothing carries from one day to the next except in the March month (%sagents/month.md), a separate download.\n" % SITE)
    out.append("The site opens `%s` by default; `?run=<id>` opens another, as in %s?run=v2-2027-07-22. "
               "Downloads are from GitHub, not this site; the manifest (%sdata/runs/manifest.json) has each file's size and SHA-256.\n"
               % (m["default"], SITE, SITE))
    out.append("| Run | Date | Kind of day | Weather | Weight (days of 2027) | Records | Hand-written records | Size | Summary | Download |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in m["runs"]:
        readme, _ = files[r["id"]]
        kind = readme_field(readme, "Kind of day") or r["class"]
        weight = "%.2f" % r["weight"] if r["weight"] is not None else "not weighted"
        out.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | [summary](%sagents/runs/%s.md) | [zip](%s%s) |" % (
            r["id"], r["date"], kind, r["weather"], weight, fmt(r["records"]), fmt(r["handwritten"]), mb(r["bytes"]),
            SITE, r["id"], RAW, r["path"]))
    out.append("")
    out.append("Simulator: %s. Each zip holds the day's tables, its `summary.md`, the systems lens's `blocks.json` and the simulator that made it; "
               "the data dictionary is %sagents/data-dictionary.md.\n" % (m["simulator_commit"], SITE))
    return page("\n".join(out))


def run_page(m, r, readme, summary):
    view = SITE if r["id"] == m["default"] else SITE + "?run=" + r["id"]
    out = ["# Run %s\n" % r["id"]]
    out.append("%s.\n" % r["label"])
    out.append("| | |\n|---|---|")
    out.append("| Download | %s%s |" % (RAW, r["path"]))
    out.append("| Size | %s bytes (%s) |" % (fmt(r["bytes"]), mb(r["bytes"])))
    out.append("| SHA-256 | `%s` |" % r["sha256"])
    out.append("| Records | %s |" % fmt(r["records"]))
    out.append("| Hand-written records | %s |" % fmt(r["handwritten"]))
    out.append("| In the viewer | %s |" % view)
    out.append("| In the data explorer | %sexplorer/%s |" % (SITE, "" if r["id"] == m["default"] else "?run=" + r["id"]))
    out.append("")
    out.append("Below are the zip's own README.md and summary.md, as they are. Columns are explained in %sagents/data-dictionary.md.\n" % SITE)
    out.append("---\n\n<!-- README.md from the zip -->\n")
    out.append(readme.strip("\n") + "\n")
    out.append("---\n\n<!-- summary.md from the zip -->\n")
    out.append(summary.strip("\n"))
    return page("\n".join(out))


# ─── districts ─────────────────────────────────────────────────────────────────────────────────────────────────
# The lens's layers, top to bottom, with how fast each changes, and its type tags (systems-lens/index.html, PLATES and TYPES)
LAYERS = [("econ", "Economic", "changes over years"), ("pol", "Political", "changes over decades"),
          ("env", "Built & natural", "changes over generations"), ("soc", "Social & cultural", "changes over generations"),
          ("hist", "Historical", "bedrock, lasts a century")]
TYPES = {"hist": "historical", "pol": "political", "econ": "economic", "env": "environmental", "soc": "social", "cult": "cultural"}
KIND = {"R": "reinforcing", "B": "balancing"}


def district_section(b):
    out = ["## %s %s: %s\n" % (b["district"], b["districtName"], b["name"])]
    out.append("Block id `%s`, on %s. %s\n" % (b["id"], b["street"], b["summary"]))
    out.append("The simulator puts %s of the district's households on this block (`block_id = %s` in households.csv and records.csv)."
               % (fmt(b["select"].get("n", 400)), b["id"]) + "\n")
    ctx = {c["id"]: c for c in b["contexts"]}
    for scope, title in (("district", "Across the whole district (the district tier)"), ("block", "On %s itself" % b["name"])):
        out.append("### %s\n" % title)
        for lk, ln, pace in LAYERS:
            cs = [c for c in b["contexts"] if c["layer"] == lk and (c.get("scope") == "district") == (scope == "district")]
            if not cs:
                continue
            out.append("**%s** (%s)\n" % (ln, pace))
            for c in cs:
                meta = []
                if c.get("types"):
                    meta.append("Types: " + ", ".join(TYPES[t] for t in c["types"]) + ".")
                if c.get("under"):
                    meta.append("Rests on: " + "; ".join("%s, %s" % (u, ctx[u]["title"]) if u in ctx else u for u in c["under"]) + ".")
                if c.get("evidence_ids"):
                    meta.append("Evidence: " + ", ".join(c["evidence_ids"]) + ".")
                if c.get("source_note"):
                    meta.append("Source: " + c["source_note"] + ".")
                out.append("- **%s** · %s · %s. %s" % (c["id"], c["year"], c["title"], c["body"]))
                if meta:
                    out.append("  - " + " ".join(meta))
            out.append("")
    out.append("### Patterns: the records the block's circumstances shape\n")
    out.append("A record from the block's households that matches a pattern (the first that matches, in this order; the rules are regular expressions) "
               "carries its id in `block_pattern` and the circumstances it links to in `context_ids`. Pattern ids and loop ids are separate: pattern R1 is not loop R1.\n")
    for p in b["patterns"]:
        rules = " or ".join(" and ".join("%s matches `%s`" % ({"cat": "job_category", "type": "record_type", "fee": "fee_type"}.get(k, k), v)
                                         for k, v in mm.items()) for mm in p.get("match", []))
        out.append("- **%s** %s (%s): links %s; %s." % (p["id"], p["title"], p["kind"], ", ".join(p["links"]),
                                                        "tagged when " + rules if rules else "no match rule, so no record carries it"))
    out.append("")
    out.append("### Loops (hypotheses, not findings)\n")
    for k, L in b["loops"].items():
        nodes = {n["k"]: n["t"] for n in L["nodes"]}
        out.append("- **%s %s** (%s). %s" % (k, L["name"], KIND.get(L["kind"], L["kind"]), L["text"]))
        for a, z, sign, why in L["links"]:
            out.append("  - %s → %s (%s): %s" % (nodes[a], nodes[z], sign, why))
        for d in L.get("drivers", []):
            out.append("  - Pushed %s by %s: %s" % (d["sign"], d["from"], d["t"]))
        if L.get("seen"):
            out.append("  - Seen in the records of pattern%s %s." % ("s" if len(L["seen"]) > 1 else "", ", ".join(L["seen"])))
    out.append("")
    return "\n".join(out)


def districts_pages(blocks):
    note = blocks["note"]
    intro = ["# Districts and circumstances\n",
             "**Composite.** Every block, circumstance and loop here is a composite of documented US patterns on an invented block, "
             "not a real place. The district tier's figures are national or from documented cases and say so, and nothing local is named. "
             "The file's own note: \"%s\"\n" % note,
             "Rendered from %ssystems-lens/blocks.json (version %s), the file the systems lens (%ssystems-lens/) draws and the simulator tags records from. "
             "Layers run from the fastest-changing to the slowest: Economic, Political, Built & natural, Social & cultural, Historical. "
             "Evidence ids (E…) are findings in the evidence folder on GitHub (%sevidence/evidence.csv), third-party material that is not under this project's license. "
             "No what-if scenarios are modeled: a loop is a hypothesis, not a model result.\n" % (SITE, blocks["version"], SITE, GH),
             "| District | Name | Mapped block | Circumstances | Patterns | Loops |", "|---|---|---|---|---|---|"]
    for b in blocks["blocks"]:
        intro.append("| %s | %s | %s (`%s`) | %d (%d district-wide) | %d | %s |" % (
            b["district"], b["districtName"], b["name"], b["id"], len(b["contexts"]),
            sum(1 for c in b["contexts"] if c.get("scope") == "district"), len(b["patterns"]), ", ".join(b["loops"])))
    intro.append("")
    sections = [district_section(b) for b in blocks["blocks"]]
    whole = page("\n".join(intro) + "\n" + "\n".join(sections))
    if len(whole) <= LIMIT:
        return {"agents/districts.md": whole}
    # too long for one page: an index, then one page per district
    pages = {}
    idx = intro[:]
    idx.append("One page per district, to keep each under about 8,000 tokens:\n")
    for b in blocks["blocks"]:
        idx.append("- %s %s, %s: %sagents/districts/%s.md" % (b["district"], b["districtName"], b["name"], SITE, b["id"]))
    pages["agents/districts.md"] = page("\n".join(idx))
    for b, s in zip(blocks["blocks"], sections):
        lead = ("# %s %s: %s\n\n**Composite**: an invented block drawn from documented US patterns, not a real place. "
                "Part of %sagents/districts.md, which explains the layers and the ids.\n\n" % (b["district"], b["districtName"], b["name"], SITE))
        body = s.split("\n", 1)[1].lstrip("\n").replace("\n### ", "\n## ")
        pages["agents/districts/%s.md" % b["id"]] = page(lead + body)
    return pages


# ─── the month ─────────────────────────────────────────────────────────────────────────────────────────────────
def month_md():
    text = absolute_links(read(MONTH_RECORD), MONTH_RECORD)
    lead = ("The March 2027 month: 31 days of the city carried day to day, a GitHub Release download of about 460 MB that this site never loads. "
            "Below is its run record as it is in the repository (%s%s), with its links made absolute. "
            "Columns are explained in %sagents/data-dictionary.md; `links.csv` is described under \"What is in it\".\n\n---\n\n" % (GH, MONTH_RECORD, SITE))
    return page(lead + text)


# ─── the schema.org Dataset on about/ ──────────────────────────────────────────────────────────────────────────
# The first run's calibration anchors, as the About page lists them under "1. Calibration anchors" (each URL must
# still be on the page); the downloaded datasets come from sources/manifest.csv.
ANCHORS = [
    ("American Community Survey", "Census Bureau", "https://www.census.gov/programs-surveys/acs"),
    ("Current Employment Statistics", "Bureau of Labor Statistics", "https://www.bls.gov/ces/"),
    ("United For ALICE", "United For ALICE", "https://www.unitedforalice.org/"),
    ("Consumer Expenditure Survey", "Bureau of Labor Statistics", "https://www.bls.gov/cex/"),
    ("Social Security cost-of-living adjustment", "Social Security Administration", "https://www.ssa.gov/cola/"),
    ("Supplemental Nutrition Assistance Program", "USDA Food and Nutrition Service", "https://www.fns.usda.gov/snap"),
    ("Medicare costs", "Centers for Medicare & Medicaid Services", "https://www.medicare.gov/basics/costs/medicare-costs"),
]
JSONLD_OPEN = '<script type="application/ld+json" id="dataset-jsonld">'


def dataset_jsonld(m):
    about = read("about/index.html")
    for name, _, url in ANCHORS:
        if 'href="%s"' % url not in about:
            raise SystemExit("calibration anchor %s is no longer linked from about/index.html" % url)
    based, seen = [], set()
    for name, org, url in ANCHORS:
        based.append({"@type": "Dataset", "name": name, "publisher": {"@type": "Organization", "name": org}, "url": url})
        seen.add((name, url))
    with open(path("sources", "manifest.csv"), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["status"] == "fetched" and (r["dataset"], r["landing_url"]) not in seen:
                based.append({"@type": "Dataset", "name": r["dataset"], "publisher": {"@type": "Organization", "name": r["publisher"]},
                              "url": r["landing_url"]})
                seen.add((r["dataset"], r["landing_url"]))
    with open(path("evidence", "sources.csv"), encoding="utf-8", newline="") as f:
        n_sources = sum(1 for _ in csv.DictReader(f))
    based.append({"@type": "CreativeWork", "name": "Medianville human evidence report: the first day read beside %d real sources" % n_sources,
                  "url": GH + "evidence/report.md"})
    dist = [{"@type": "DataDownload", "name": r["label"], "encodingFormat": "application/zip", "contentUrl": RAW + r["path"],
             "contentSize": "%d bytes" % r["bytes"], "sha256": r["sha256"]} for r in m["runs"]]
    dist.append({"@type": "DataDownload", "name": "March 2027, 31 days carried day to day (GitHub Release, about 460 MB)",
                 "encodingFormat": "application/zip",
                 "contentUrl": "https://github.com/jas0nmjames/playground/releases/download/medianville-v2-month-2027-03/medianville_2027-03_month.zip"})
    dist.append({"@type": "DataDownload", "name": "The systems lens's mapped blocks (systems-lens/blocks.json)",
                 "encodingFormat": "application/json", "contentUrl": RAW + "systems-lens/blocks.json"})
    d = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Medianville: a simulated American city's transactions",
        "description": ("Synthetic data: a simulated American city of about 100,000 people, weighted to the United States as a whole. "
                        "Its records are every job someone did to get something done: purchases, bills, benefit deposits, forms, waits, "
                        "declined cards and unpaid care, one simulated day at a time across 2027. Every person, household, business and "
                        "street is invented; rates and targets come from real public research, but no record describes a real person or place."),
        "url": SITE,
        "sameAs": GH_TREE.rstrip("/"),
        "creator": {"@type": "Person", "name": "Jason James", "url": "https://jasonjames.works"},
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isAccessibleForFree": True,
        "temporalCoverage": "2027",
        "keywords": ["synthetic data", "simulation", "household finance", "jobs to be done", "public services", "United States"],
        "citation": "James, J. (2026). Medianville: a simulated American city's transactions [synthetic dataset]. https://medianville.netlify.app/",
        "isBasedOn": based,
        "distribution": dist,
    }
    return json.dumps(d, indent=1, ensure_ascii=False)


def about_html(m):
    """about/index.html with its JSON-LD block written (inserted before </head> the first time)."""
    s = read("about/index.html")
    block = "%s\n%s\n</script>" % (JSONLD_OPEN, dataset_jsonld(m).replace("</", "<\\/"))
    if JSONLD_OPEN in s:
        a = s.index(JSONLD_OPEN)
        z = s.index("</script>", a) + len("</script>")
        return s[:a] + block + s[z:]
    return s.replace("</head>", block + "\n</head>", 1)


# ─── everything ────────────────────────────────────────────────────────────────────────────────────────────────
def strip_header(p):
    assert p.startswith(HEADER)
    return p[len(HEADER):].lstrip("\n")


def build():
    """Every generated file: {path relative to this folder: text}."""
    m = manifest()
    pages = {}
    pages["agents/about.md"] = about_md()
    pages["agents/data-dictionary.md"] = data_dictionary(m)
    files = {r["id"]: run_files(r) for r in m["runs"]}
    pages["agents/runs.md"] = runs_md(m, files)
    for r in m["runs"]:
        readme, summary = files[r["id"]]
        pages["agents/runs/%s.md" % r["id"]] = run_page(m, r, readme, summary)
    with open(path("systems-lens", "blocks.json"), encoding="utf-8") as f:
        blocks = json.load(f)
    districts = districts_pages(blocks)
    pages.update(districts)
    pages["agents/month.md"] = month_md()

    # llms-full.txt: llms.txt, then about, the data dictionary, runs, districts and the baseline day's summary
    parts = [read("llms.txt").strip("\n")]
    order = ["agents/about.md", "agents/data-dictionary.md", "agents/runs.md"] + list(districts)  # the index, then D1 to D6
    for k in order:
        parts.append("<!-- %s%s -->\n\n%s" % (SITE, k, strip_header(pages[k]).strip("\n")))
    _, base_summary = files[m["default"]]
    parts.append("<!-- the baseline day's summary.md, from %s%s -->\n\n%s" % (RAW, run_by_id(m, m["default"])["path"], base_summary.strip("\n")))
    full = ("# Medianville: everything in one file\n\nllms.txt, the About page, the data dictionary, the runs, the districts and the "
            "baseline day's summary, in one request. Each part starts with a comment naming the page it comes from.\n\n---\n\n"
            + "\n\n---\n\n".join(parts))
    pages["llms-full.txt"] = page(full)
    pages["about/index.html"] = about_html(m)
    return pages


def main():
    check = "--check" in sys.argv
    pages = build()
    stale = []
    for rel, text in sorted(pages.items()):
        p = path(rel)
        have = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if have != text:
            stale.append(rel)
            if not check:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
    # pages left over from an earlier build (a run or district that no longer exists)
    extra = []
    for root, _, names in os.walk(path("agents")):
        for n in names:
            rel = os.path.relpath(os.path.join(root, n), PROJECT).replace(os.sep, "/")
            if rel not in pages:
                extra.append(rel)
                if not check:
                    os.remove(os.path.join(root, n))
    for rel in sorted(k for k in pages if k.endswith((".md", ".txt"))):
        print("%-36s %7s characters, about %5s tokens" % (rel, fmt(len(pages[rel])), fmt(round(len(pages[rel]) / 4))))
    if check:
        if stale or extra:
            print("stale: " + ", ".join(stale + extra))
            return 1
        print("all %d pages are current" % len(pages))
    else:
        print("wrote %d, removed %d" % (len(stale), len(extra)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
