"""The pages for agents and LLMs: agents/*.md, llms.txt and llms-full.txt (tools/build_agent_pages.py)."""
import json
import os
import re
import sys

import pytest

from conftest import REPO_DIR

TOOLS = os.path.join(REPO_DIR, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import build_agent_pages as B  # noqa: E402
import check_links as L  # noqa: E402

URL = re.compile(r"https?://[^\s)>\]`\"'<]+")
TEMPLATE = re.compile(r"https?://\S*<date>\S*?\.zip")
OURS = (L.NETLIFY, L.RAW, L.GH, L.PAGES)


@pytest.fixture(scope="module")
def built():
    return B.build()


def committed():
    """Every agent file in the folder: the generated ones and the hand-written llms.txt."""
    out = {"llms.txt": os.path.join(REPO_DIR, "llms.txt"), "llms-full.txt": os.path.join(REPO_DIR, "llms-full.txt")}
    for root, _, names in os.walk(os.path.join(REPO_DIR, "agents")):
        for n in names:
            p = os.path.join(root, n)
            out[os.path.relpath(p, REPO_DIR).replace(os.sep, "/")] = p
    return out


def text(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def test_committed_pages_are_current(built):
    """The staleness guard: rebuilding gives the committed files byte for byte, and nothing else is in agents/."""
    have = {k: v for k, v in committed().items() if k != "llms.txt"}
    have["about/index.html"] = os.path.join(REPO_DIR, "about", "index.html")  # its JSON-LD block is written by the build
    assert sorted(have) == sorted(built), "run python3 tools/build_agent_pages.py and commit what it writes"
    stale = [k for k, v in built.items() if text(have[k]) != v]
    assert not stale, "stale (run python3 tools/build_agent_pages.py): %s" % stale


def test_every_page_starts_with_the_header():
    for k, p in committed().items():
        if k == "llms.txt":
            continue  # llms.txt carries the full provenance note instead
        assert text(p).startswith(B.HEADER), k


def test_llms_txt_has_the_provenance_note():
    t = text(os.path.join(REPO_DIR, "llms.txt"))
    assert t.startswith("# Medianville\n\n> ")
    for phrase in ("The data is synthetic.", "Say this once, at the start of a session",
                   "composites of documented US patterns", "No what-if scenarios are modeled yet",
                   "Cite as: James, J. (2026).", "CC BY 4.0"):
        assert phrase in t, phrase


def test_every_file_is_under_the_size_limit():
    """About 8,000 tokens each; llms-full.txt is everything in one file, so it is the one exception."""
    for k, p in committed().items():
        if k == "llms-full.txt":
            continue
        assert len(text(p)) <= B.LIMIT, (k, len(text(p)))


def test_every_local_link_resolves():
    """Every link into this site or this repo, as a Markdown link or a bare URL, points at a file that exists."""
    broken, checked = [], 0
    for k, p in committed().items():
        t = text(p)
        # a template such as .../medianville_<date>.zip stands for every v2 day in the manifest
        dates = [r["date"] for r in B.manifest()["runs"] if r["version"] == "v2"]
        urls = {u.replace("<date>", d) for u in TEMPLATE.findall(t) for d in dates}
        t = TEMPLATE.sub("", t)
        urls |= set(L.links_in(p)) | {u.rstrip(".,;:") for u in URL.findall(t)}
        for u in sorted(urls):
            if u.startswith("http") and not any(rx.match(u) for rx in OURS):
                continue  # other sites are not fetched
            r = L.resolve(p, u)
            if r is None:
                continue
            checked += 1
            err = L.check_target(*r)
            if err:
                broken.append("%s: %s (%s)" % (k, u, err))
    assert checked > 100
    assert not broken, broken


def test_absolute_urls_only():
    """The agent files link with absolute URLs, so a page read on its own still leads somewhere."""
    md_link = re.compile(r"\]\(\s*<?([^)\s>]+)")
    for k, p in committed().items():
        for u in md_link.findall(text(p)):
            assert re.match(r"^https?://", u), (k, u)


def test_downloads_are_on_github_not_netlify():
    """Bulk files are pointed to on GitHub, so agent downloads don't use the site's bandwidth."""
    for k, p in committed().items():
        for u in URL.findall(text(p)):
            assert not (u.startswith(B.SITE) and u.endswith(".zip")), (k, u)


def test_about_page_dataset_jsonld():
    """The schema.org Dataset on about/: parse it and check the fields search engines and agents read."""
    with open(os.path.join(REPO_DIR, "about", "index.html"), encoding="utf-8") as f:
        page = f.read()
    blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S)
    assert len(blocks) == 1
    d = json.loads(blocks[0])
    assert d["@context"] == "https://schema.org" and d["@type"] == "Dataset"
    assert d["name"] and "synthetic" in d["description"].lower()
    assert d["creator"] == {"@type": "Person", "name": "Jason James", "url": "https://jasonjames.works"}
    assert d["license"] == "https://creativecommons.org/licenses/by/4.0/"
    assert d["isAccessibleForFree"] is True and d["temporalCoverage"] == "2027" and d["url"] == B.SITE
    assert len([x for x in d["isBasedOn"] if x["@type"] == "Dataset"]) >= 42
    runs = B.manifest()["runs"]
    zips = [x for x in d["distribution"] if x["contentUrl"].startswith(B.RAW) and x["contentUrl"].endswith(".zip")]
    assert [x["contentUrl"] for x in zips] == [B.RAW + r["path"] for r in runs]
    assert all(x["@type"] == "DataDownload" and x["encodingFormat"] == "application/zip" for x in zips)
    assert [x["sha256"] for x in zips] == [r["sha256"] for r in runs]


def test_robots_and_headers():
    """Crawlers are kept off the zips only, and Netlify serves the agent files as Markdown."""
    with open(os.path.join(REPO_DIR, "robots.txt"), encoding="utf-8") as f:
        rules = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    assert rules == ["User-agent: *", "Allow: /", "Disallow: /*.zip"]
    with open(os.path.join(REPO_DIR, "_headers"), encoding="utf-8") as f:
        blocks, cur = {}, None
        for ln in f:
            if not ln.strip() or ln.startswith("#"):
                continue
            if not ln[0].isspace():
                cur = ln.strip()
                blocks[cur] = {}
            else:
                k, _, v = ln.strip().partition(": ")
                blocks[cur][k] = v
    md = {"Content-Type": "text/markdown; charset=utf-8", "Cache-Control": "public, max-age=3600"}
    for p in ("/llms.txt", "/llms-full.txt", "/agents/*"):
        assert blocks[p] == md, p
    assert blocks["/data/*"] == {"Cache-Control": "public, max-age=86400"}
    assert blocks["/robots.txt"] == {"Cache-Control": "public, max-age=3600"}
    assert not os.path.exists(os.path.join(REPO_DIR, "netlify.toml"))


@pytest.mark.parametrize("page", ["index.html", "explorer/index.html", "systems-lens/index.html", "about/index.html", "archive/index.html"])
def test_every_page_links_for_agents(page):
    """A visible "For agents" link to llms.txt, beside the page's other links, and the alternate link in its head."""
    with open(os.path.join(REPO_DIR, page), encoding="utf-8") as f:
        html = f.read()
    links = re.findall(r'<a [^>]*href="((?:\.\./)?llms\.txt)"[^>]*>For agents</a>', html)
    assert links, page
    assert all(os.path.normpath(os.path.join(REPO_DIR, os.path.dirname(page), h)) == os.path.join(REPO_DIR, "llms.txt") for h in links)
    assert '<link rel="alternate" type="text/markdown" href="/llms.txt" title="For agents and LLMs">' in html
