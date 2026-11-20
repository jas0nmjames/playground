#!/usr/bin/env python3
"""Download FFIEC Call Report bulk files (manifest row ffiec_call_reports). Standard library only.

    python3 -I sources/tools/ffiec_bulk.py list            show the reporting periods on offer
    python3 -I sources/tools/ffiec_bulk.py get [N]         download the latest N periods (default 4) and log them

The FFIEC page serves its bulk files through an ASP.NET form, not plain links, so this script fills in
the form the way a browser does: Call Reports -- Single Period, tab delimited. No sign-in is involved.
Each zip holds every schedule, including RI and RI-E.
"""
import html
import http.cookiejar
import os
import re
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch  # noqa: E402

URL = "https://cdr.ffiec.gov/public/PWS/DownloadBulkData.aspx"
RID = "ffiec_call_reports"
P = "ctl00$MainContentHolder$"


def opener():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = [("User-Agent", fetch.UA)]
    return op


def hidden(page):
    return {m.group(1): html.unescape(m.group(2))
            for m in re.finditer(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', page)}


def periods(op):
    page = op.open(URL, timeout=120).read().decode()
    form = hidden(page)
    form.update({"__EVENTTARGET": P + "ListBox1", P + "ListBox1": "ReportingSeriesSinglePeriod", P + "FormatType": "TSVRadioButton"})
    page = op.open(URL, urllib.parse.urlencode(form).encode(), timeout=120).read().decode()
    sel = page.split('name="%sDatesDropDownList"' % P)[1].split("</select>")[0]
    return page, re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', sel)


def main(argv):
    op = opener()
    page, opts = periods(op)
    if not argv or argv[0] == "list":
        for v, label in opts:
            print(label)
        return
    n = int(argv[1]) if len(argv) > 1 else 4
    folder = os.path.join(fetch.RAW, RID)
    os.makedirs(folder, exist_ok=True)
    for value, label in opts[:n]:
        form = hidden(page)
        form.update({"__EVENTTARGET": "", P + "ListBox1": "ReportingSeriesSinglePeriod", P + "FormatType": "TSVRadioButton",
                     P + "DatesDropDownList": value, P + "TabStrip1$Download_0": "Download"})
        r = op.open(URL, urllib.parse.urlencode(form).encode(), timeout=600)
        m = re.search(r'filename="?([^";]+)', r.headers.get("Content-Disposition", ""))
        if not m:
            print("no file offered for", label)
            continue
        size = int(r.headers.get("Content-Length") or 0)
        if size > fetch.LIMIT:
            print("over 1 GB, skipped:", label)
            continue
        name = m.group(1)
        with open(os.path.join(folder, name), "wb") as f:
            for b in iter(lambda: r.read(1 << 20), b""):
                f.write(b)
        stamp = re.sub(r"\D", "", label)
        fetch.record(RID, "%s (Call Reports -- Single Period, tab delimited, %s)" % (URL, stamp), name)


if __name__ == "__main__":
    main(sys.argv[1:])
