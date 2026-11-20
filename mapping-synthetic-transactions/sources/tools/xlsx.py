"""A minimal .xlsx reader, standard library only, for the source tools.

    from xlsx import sheets, rows
    sheets(path)               -> list of sheet names, in workbook order
    rows(path, sheet=None)     -> iterator of row lists (str, float or None), first sheet if none given

Reads cell values only (shared strings, inline strings, numbers, booleans). Formulas give their cached value.
Dates come back as Excel serial numbers. Gaps between cells are filled with None so column positions hold.
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
_REF = re.compile(r"([A-Z]+)(\d+)")


def _col(letters):
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def _book(z):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels.findall("p:Relationship", NS)}
    out = []
    for s in wb.find("m:sheets", NS).findall("m:sheet", NS):
        t = target[s.get("{%s}id" % NS["r"])].lstrip("/")
        out.append((s.get("name"), t if t.startswith("xl/") else "xl/" + t))
    return out


def sheets(path):
    with zipfile.ZipFile(path) as z:
        return [n for n, _ in _book(z)]


def _strings(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    out = []
    for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
        out.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    return out


def rows(path, sheet=None):
    with zipfile.ZipFile(path) as z:
        book = _book(z)
        part = book[0][1] if sheet is None else dict(book)[sheet]
        strings = _strings(z)
        with z.open(part) as f:
            for _, el in ET.iterparse(f):
                if el.tag != "{%s}row" % NS["m"]:
                    continue
                vals = []
                for c in el.findall("m:c", NS):
                    m = _REF.match(c.get("r", ""))
                    i = _col(m.group(1)) if m else len(vals)
                    while len(vals) < i:
                        vals.append(None)
                    t, v = c.get("t"), c.find("m:v", NS)
                    if t == "s":
                        val = strings[int(v.text)] if v is not None else None
                    elif t == "inlineStr":
                        val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                    elif t in ("str", "e"):
                        val = v.text if v is not None else None
                    elif t == "b":
                        val = (v.text == "1") if v is not None else None
                    else:
                        val = float(v.text) if v is not None and v.text not in (None, "") else None
                    vals.append(val)
                yield vals
                el.clear()
