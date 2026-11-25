#!/usr/bin/env python3
"""Check every link in Medianville's documents and pages.

    python3 tools/check_links.py            # from mapping-synthetic-transactions/
    python3 tools/check_links.py --verbose  # also list every link checked

Reads every .md and .html file in the project folder (not data/, which is frozen as
delivered), and llms.txt and llms-full.txt as Markdown, and checks:

- relative links and image paths: the file or folder exists (a folder needs an
  index.html or README.md), and a #heading anchor into a Markdown file matches one
  of its headings, slugged the way GitHub slugs them. A page's root-relative links
  start from this folder, which Netlify publishes; a Markdown file's start from the
  repo root, as GitHub reads them;
- links to this repo on GitHub (github.com/jas0nmjames/playground/blob|tree/<branch>/… and
  raw.githubusercontent.com/jas0nmjames/playground/<branch>/…), to GitHub Pages
  (jas0nmjames.github.io/playground/…) and to the Netlify site (medianville.netlify.app/…,
  served from this folder): the path exists here.

Other web links are not fetched. Exits 1 and lists the broken links if any.
"""
import os
import re
import sys
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.dirname(PROJECT)
SKIP_DIRS = {"data", ".git", "node_modules", "__pycache__"}

GH = re.compile(r"^https://github\.com/jas0nmjames/playground/(?:blob|tree|raw)/[^/]+/(.*)$")
PAGES = re.compile(r"^https://jas0nmjames\.github\.io/playground/(.*)$")
RAW = re.compile(r"^https://raw\.githubusercontent\.com/jas0nmjames/playground/[^/]+/(.*)$")
NETLIFY = re.compile(r"^https://medianville\.netlify\.app/(.*)$")  # publishes this folder
MARKDOWN_TXT = {"llms.txt", "llms-full.txt"}
MD_LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
MD_REF = re.compile(r"^\s*\[(?!\^)[^\]]+\]:\s*(\S+)", re.M)
HTML_ATTR = re.compile(r"""\b(?:href|src)\s*=\s*["']([^"']+)["']""")
FENCE = re.compile(r"^(```|~~~).*?^\1", re.M | re.S)
CODE = re.compile(r"`[^`\n]*`")


def slug(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # link text only
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)  # GitHub keeps letters, digits, _, -, spaces
    return text.replace(" ", "-")


_anchors = {}


def anchors(path):
    if path not in _anchors:
        found, seen = set(), {}
        body = FENCE.sub("", open(path, encoding="utf-8").read())
        for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", body, re.M):
            s = slug(m.group(1))
            n = seen.get(s, 0)
            found.add(s if n == 0 else "%s-%d" % (s, n))
            seen[s] = n + 1
        for m in re.finditer(r"""\b(?:id|name)\s*=\s*["']([^"']+)["']""", body):
            found.add(m.group(1))
        _anchors[path] = found
    return _anchors[path]


def html_ids(path):
    if path not in _anchors:
        body = open(path, encoding="utf-8").read()
        _anchors[path] = set(re.findall(r"""\bid\s*=\s*["']([^"']+)["']""", body))
    return _anchors[path]


def routes_hash(path):
    """Pages whose script reads the address's #hash (the viewer, the explorer, the lens) take any anchor."""
    text = open(path, encoding="utf-8").read()
    return "location.hash" in text or "hashchange" in text


def check_target(target, anchor, on_github=False):
    """target is an absolute filesystem path. Returns an error string or None."""
    if os.path.isdir(target):
        # GitHub shows a folder's README; a served page shows its index.html
        for index in (("README.md",) if on_github else ("index.html", "README.md")):
            if os.path.exists(os.path.join(target, index)):
                if anchor:
                    return check_target(os.path.join(target, index), anchor)
                return None
        return None if not anchor else "anchor on a folder with no index"
    if not os.path.exists(target):
        return "missing"
    if anchor:
        if target.endswith(".md") and unquote(anchor).lower() not in anchors(target):
            return "no heading #%s" % anchor
        if target.endswith(".html") and anchor not in html_ids(target) and not routes_hash(target):
            return "no id #%s" % anchor
    return None


def resolve(src, url):
    """Returns (filesystem path, anchor) or None for links not checked here."""
    url = url.strip()
    if url.startswith(("mailto:", "tel:", "data:", "javascript:")):
        return None
    n = NETLIFY.match(url)
    if n:
        path, _, anchor = n.group(1).partition("#")
        path = path.split("?")[0]
        return os.path.join(PROJECT, unquote(path)), anchor, False
    m = GH.match(url) or PAGES.match(url) or RAW.match(url)
    if m:
        rest = m.group(1)
        path, _, anchor = rest.partition("#")
        path = path.split("?")[0]
        return os.path.join(REPO, unquote(path)), anchor, bool(GH.match(url))
    if re.match(r"^[a-z]+://", url) or url.startswith("//"):
        return None
    path, _, anchor = url.partition("#")
    path = path.split("?")[0]
    if not path:
        return src, anchor, False
    # a root-relative link: GitHub reads a Markdown file's from the repo root; Netlify serves a page's from this folder
    base = (PROJECT if src.endswith(".html") else REPO) if path.startswith("/") else os.path.dirname(src)
    # a Markdown file is read on GitHub, so a folder link there opens the folder's README
    return os.path.normpath(os.path.join(base, unquote(path.lstrip("/")))), anchor, src.endswith(".md")


def links_in(path):
    text = open(path, encoding="utf-8").read()
    if path.endswith(".md") or os.path.basename(path) in MARKDOWN_TXT:
        text = FENCE.sub("", text)
        text = CODE.sub("", text)
        found = MD_LINK.findall(text) + MD_REF.findall(text) + HTML_ATTR.findall(text)
    else:
        text = re.sub(r"<script\b(?![^>]*\bsrc=)[^>]*>.*?</script>", "", text, flags=re.S)
        found = HTML_ATTR.findall(text)
    return found


def main():
    verbose = "--verbose" in sys.argv
    files = []
    for root, dirs, names in os.walk(PROJECT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        files += [os.path.join(root, n) for n in sorted(names) if n.endswith((".md", ".html")) or
                  (root == PROJECT and n in MARKDOWN_TXT)]
    broken, checked = [], 0
    for f in files:
        for url in links_in(f):
            r = resolve(f, url)
            if r is None:
                continue
            checked += 1
            err = check_target(*r)
            rel = os.path.relpath(f, PROJECT)
            if err:
                broken.append("%s: %s (%s)" % (rel, url, err))
            elif verbose:
                print("ok  %s: %s" % (rel, url))
    print("%d files, %d links checked, %d broken." % (len(files), checked, len(broken)))
    for b in broken:
        print("  " + b)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
