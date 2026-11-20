"""Crude text from a PDF, standard library only: decompresses Flate streams and joins the Tj/TJ strings.

    from pdftext import text
    t = text(path)          # one string, whitespace collapsed

Good enough for the statistical tables the source tools read (numbers and labels in reading order); it does not
handle encrypted files, image-only pages or fonts with custom encodings.
"""
import re
import zlib


def text(path):
    b = open(path, "rb").read()
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", b, re.S):
        try:
            d = zlib.decompress(m.group(1))
        except zlib.error:
            continue
        for a, s, op in re.findall(rb"\[(.*?)\]\s*TJ|\((.*?)\)\s*Tj|(T\*|Td|TD|ET)", d, re.S):
            if op:
                out.append(" ")
            elif s:
                out.append(s.decode("latin-1"))
            else:
                out.append("".join(x.decode("latin-1") for x in re.findall(rb"\((.*?)(?<!\\)\)", a)))
    return re.sub(r"\s+", " ", "".join(out))
