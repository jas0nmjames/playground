#!/usr/bin/env python3
"""Download helpers for sources/manifest.csv. Standard library only.

    python3 -I sources/tools/fetch.py links URL [REGEX]       list a landing page's links (absolute), optionally filtered
    python3 -I sources/tools/fetch.py get ID URL [URL ...]    download into sources/raw/ID/, keeping the publisher's file name
    python3 -I sources/tools/fetch.py page ID URL [NAME]      save an HTML page itself into sources/raw/ID/ (for compiled sources)
    python3 -I sources/tools/fetch.py record ID URL FILE      log a file saved into sources/raw/ID/ by other means
    python3 -I sources/tools/fetch.py log                     print the download log

Every download is appended to sources/raw/_downloads.jsonl (id, url, file, bytes, sha256, time), which
`finalize.py` folds into the manifest. Files over 1 GB are refused: ask first, then pass --allow-large.
"""
import hashlib
import html.parser
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
RAW = os.path.join(SOURCES, "raw")
LOG = os.path.join(RAW, "_downloads.jsonl")
UA = "halvern-sources/0.1 (public data archiving)"
LIMIT = 1 << 30


def request(url, method="GET"):
    return urllib.request.urlopen(urllib.request.Request(url, method=method, headers={"User-Agent": UA}), timeout=120)


class Links(html.parser.HTMLParser):
    def __init__(self, base):
        super().__init__()
        self.base, self.out, self._href, self._text = base, [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, d):
        if self._href is not None:
            self._text.append(d)

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            self.out.append((urllib.parse.urljoin(self.base, self._href), " ".join("".join(self._text).split())))
            self._href = None


def links(url, pattern=None):
    with request(url) as r:
        body = r.read().decode("utf-8", "replace")
        base = r.geturl()
    p = Links(base)
    p.feed(body)
    seen = set()
    for href, text in p.out:
        if (pattern is None or re.search(pattern, href + " " + text, re.I)) and href not in seen:
            seen.add(href)
            print("%s\t%s" % (href, text[:100]))


def name_for(resp, url):
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd)
    name = m.group(1) if m else os.path.basename(urllib.parse.urlparse(resp.geturl()).path) or os.path.basename(urllib.parse.urlparse(url).path)
    return urllib.parse.unquote(name).replace("/", "_") or "download"


def download(rid, url, allow_large=False, name=None):
    folder = os.path.join(RAW, rid)
    os.makedirs(folder, exist_ok=True)
    with request(url) as r:
        size = int(r.headers.get("Content-Length") or 0)
        if size > LIMIT and not allow_large:
            sys.exit("REFUSED %s: %.2f GB is over 1 GB; ask first, then pass --allow-large" % (url, size / 1e9))
        fname = name or name_for(r, url)
        path = os.path.join(folder, fname)
        h, n = hashlib.sha256(), 0
        with open(path + ".part", "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                n += len(b)
                if n > LIMIT and not allow_large:
                    f.close()
                    os.remove(path + ".part")
                    sys.exit("REFUSED %s: passed 1 GB while downloading" % url)
                h.update(b)
                f.write(b)
        ctype = r.headers.get("Content-Type", "")
    os.replace(path + ".part", path)
    entry = {"id": rid, "url": url, "file": fname, "bytes": n, "sha256": h.hexdigest(), "content_type": ctype,
             "downloaded_on": time.strftime("%Y-%m-%d")}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print("%s\t%s\t%d bytes\t%s" % (rid, fname, n, ctype))


def record(rid, url, fname):
    path = os.path.join(RAW, rid, fname)
    h, n = hashlib.sha256(), 0
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
            n += len(b)
    entry = {"id": rid, "url": url, "file": fname, "bytes": n, "sha256": h.hexdigest(), "content_type": "",
             "downloaded_on": time.strftime("%Y-%m-%d")}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print("%s\t%s\t%d bytes (recorded)" % (rid, fname, n))


def main(argv):
    allow = "--allow-large" in argv
    argv = [a for a in argv if a != "--allow-large"]
    cmd = argv[0] if argv else ""
    if cmd == "links":
        try:
            links(argv[1], argv[2] if len(argv) > 2 else None)
        except Exception as e:
            print("FAILED %s: %s" % (argv[1], e))
    elif cmd == "get":
        for u in argv[2:]:
            try:
                download(argv[1], u, allow)
            except Exception as e:  # report and carry on with the rest
                print("FAILED %s %s: %s" % (argv[1], u, e))
    elif cmd == "page":
        download(argv[1], argv[2], allow, name=argv[3] if len(argv) > 3 else None)
    elif cmd == "record":  # log a file saved by other means (e.g. a form download): record ID URL FILE
        record(argv[1], argv[2], argv[3])
    elif cmd == "log":
        with open(LOG) as f:
            for line in f:
                print(line.rstrip())
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
