"""A minimal Stata .dta reader (formats 113-115, the "old" binary layout MEPS uses), standard library only.

    from dta import read
    for row in read(path_or_file, ["DUPERSID", "OBXP24X"]):   # dicts with just those columns
        ...

Numbers come back as int or float; Stata missing values (the top of each type's range) come back as None.
Strings are decoded as latin-1 and stripped of trailing NULs. Value labels are not read.
"""
import io
import struct
import zipfile

_NUM = {251: ("b", 1, 100), 252: ("h", 2, 32740), 253: ("i", 4, 2147483620), 254: ("f", 4, 1.7e38), 255: ("d", 8, 8.98e307)}


def _open(path):
    if hasattr(path, "read"):
        return path
    if str(path).endswith(".zip"):
        z = zipfile.ZipFile(path)
        name = next(n for n in z.namelist() if n.lower().endswith(".dta"))
        return io.BytesIO(z.read(name))
    return open(path, "rb")


def read(path, columns=None):
    f = _open(path)
    head = f.read(4)
    fmt, order = head[0], head[1]
    if fmt not in (113, 114, 115):
        raise ValueError("unsupported .dta format %d" % fmt)
    e = "<" if order == 2 else ">"
    nvar = struct.unpack(e + "H", f.read(2))[0]
    nobs = struct.unpack(e + "I", f.read(4))[0]
    f.read(81 + 18)                                   # data label, time stamp
    types = list(f.read(nvar))
    names = [f.read(33).split(b"\0")[0].decode("latin-1") for _ in range(nvar)]
    f.read(2 * (nvar + 1))                            # sort list
    f.read((49 if fmt >= 114 else 12) * nvar)         # formats
    f.read(33 * nvar)                                 # value label names
    f.read((81 if fmt >= 114 else 32) * nvar)         # variable labels
    while True:                                       # expansion fields
        t = f.read(1)[0]
        ln = struct.unpack(e + "i", f.read(4))[0]
        if t == 0 and ln == 0:
            break
        f.read(ln)
    widths = [_NUM[t][1] if t in _NUM else t for t in types]
    offs, o = [], 0
    for w in widths:
        offs.append(o)
        o += w
    reclen = o
    want = range(nvar) if columns is None else [names.index(c) for c in columns]
    plan = []
    for i in want:
        t = types[i]
        if t in _NUM:
            code, w, top = _NUM[t]
            plan.append((names[i], offs[i], struct.Struct(e + code), top, False, w))
        else:
            plan.append((names[i], offs[i], None, None, True, t))
    for _ in range(nobs):
        rec = f.read(reclen)
        row = {}
        for name, off, st, top, is_str, w in plan:
            if is_str:
                row[name] = rec[off:off + w].split(b"\0")[0].decode("latin-1").rstrip()
            else:
                v = st.unpack_from(rec, off)[0]
                row[name] = None if v > top else v
        yield row
