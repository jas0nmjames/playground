"""Tag the day's records with the systems lens's mapped blocks.

The lens maps a few composite blocks, one per district, in systems-lens/blocks.json. Each block says which of
its district's households live there ("select") and which kinds of record its circumstances shape ("patterns",
each with "match" rules). This pass runs after the day is simulated and uses no random numbers, so the records
themselves are unchanged; it only adds three columns:

    block_id        the block whose household made the record, or ""
    block_pattern   the first pattern in that block the record matches, or ""
    context_ids     the circumstances that pattern links to, separated by ";"

Households are chosen deterministically: each household in the block's district scores one point for every
"prefer" field it matches and two for every distinct pattern its records hit (up to three patterns), ties broken
by a hash of the household id. The best few households for each pattern ("reserve", default 4) are taken first, so
every pattern the day supports has records, and the rest of the block's "n" households fill by score.
"""
import json
import os
import re
import zlib

COLS = ["block_id", "block_pattern", "context_ids"]
# record columns the match rules can test (indexes into engine.COLS)
FIELD = {"cat": 3, "type": 2, "fee": 20, "outcome": 26}
# household fields the select rules can test (households.csv names -> Household attributes)
HFIELD = {"alice_status": "alice", "banked_status": "banked", "housing_tenure": "tenure", "household_type": "htype",
          "vehicles": "vehicles", "internet_at_home": "internet", "primary_language": "lang"}


def find_blocks(start=None):
    """systems-lens/blocks.json from the repository, or a copy shipped beside the simulator."""
    here = os.path.dirname(os.path.abspath(start or __file__))
    d = here
    for _ in range(6):
        for cand in (os.path.join(d, "systems-lens", "blocks.json"), os.path.join(d, "blocks.json")):
            if os.path.exists(cand):
                return cand
        d = os.path.dirname(d)
    return None


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _rules(p):
    return [{k: re.compile(v) for k, v in m.items()} for m in p.get("match", [])]


def _hits(rules, row):
    for m in rules:
        if all(rx.search(str(row[FIELD[k]] if row[FIELD[k]] is not None else "")) for k, rx in m.items()):
            return True
    return False


class Tagger:
    def __init__(self, sim, doc, income_mix=None):
        self.doc = doc
        self.block_of = {}      # household id -> block id
        self.pats = {}          # block id -> [(pattern id, rules, "ctx;ctx")]
        for b in doc["blocks"]:
            self.pats[b["id"]] = [(p["id"], _rules(p), ";".join(p["links"])) for p in b["patterns"] if p.get("match")]
        # which patterns each household's records hit, for every block in its district
        by_district = {}
        for b in doc["blocks"]:
            by_district.setdefault(b["district"], []).append(b)
        hits = {}
        hh = {H.hid: H for H in sim.households}
        for row in sim.rows:
            hid = row[6]
            H = hh.get(hid) if hid else None
            if H is None:
                continue
            d = H.district
            for b in by_district.get(d, ()):
                for pid, rules, _ in self.pats[b["id"]]:
                    if _hits(rules, row):
                        hits.setdefault((b["id"], hid), set()).add(pid)
                        break
        taken = set()
        for b in doc["blocks"]:
            sel = b.get("select", {})
            prefer = {k: re.compile(v) for k, v in sel.get("prefer", {}).items()}
            scored = []
            for H in sim.households:
                if H.district != b["district"] or H.hid in taken:
                    continue
                s = 0
                for k, rx in prefer.items():
                    v = income_mix(H) if k == "income_source_mix" and income_mix else getattr(H, HFIELD.get(k, k), "")
                    if rx.search(str(v)):
                        s += 1
                s += 2 * min(3, len(hits.get((b["id"], H.hid), ())))
                scored.append((-s, zlib.crc32(H.hid.encode()), H.hid))
            scored.sort()
            # every pattern the day supports gets its best few households first, then the rest fill by score
            picked, n = [], sel.get("n", 400)
            for pid, _, _ in self.pats[b["id"]]:
                k = 0
                for t in scored:
                    if k >= sel.get("reserve", 4):
                        break
                    if pid in hits.get((b["id"], t[2]), ()) and t[2] not in taken:
                        picked.append(t[2]); taken.add(t[2]); k += 1
            for t in scored:
                if len(picked) >= n:
                    break
                if t[2] not in taken:
                    picked.append(t[2]); taken.add(t[2])
            for hid in picked:
                self.block_of[hid] = b["id"]

    def tag(self, row):
        """The three block columns for one record row (as built by the engine, before formatting)."""
        bid = self.block_of.get(row[6]) if row[6] else None
        if not bid:
            return ["", "", ""]
        for pid, rules, ctx in self.pats[bid]:
            if _hits(rules, row):
                return [bid, pid, ctx]
        return [bid, "", ""]

    def household_block(self, hid):
        return self.block_of.get(hid, "")
