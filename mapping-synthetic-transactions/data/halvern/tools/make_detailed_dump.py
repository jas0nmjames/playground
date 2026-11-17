"""Pick the stratified sample of records that gets hand-written text, and dump their context for the writer."""
import json
import sys

sys.path.insert(0, ".")
from halvern_sim import main, output as O
from halvern_sim.config import PARAMS

cfg = dict(PARAMS)
sim = main.build(cfg, log=lambda *a: None)
main.simulate(sim, log=lambda *a: None)
sim.write_records("/tmp/_records_tmp.csv")
idx = O.select_detailed(sim, 500)
pm = {p.pid: p for p in sim.persons}
hm = {H.hid: H for H in sim.households}
om = {o.oid: o for o in sim.orgs}
RT = {"purchase": "PUR", "bill_payment": "BILL", "income": "INC", "benefit_issuance": "BEN+", "benefit_redemption": "BEN-", "transfer": "XFER", "tax": "TAX", "b2b": "B2B",
      "public_service_encounter": "PSE", "insurance_claim": "CLM", "non_monetary_job": "NMJ", "failed_attempt": "FAIL"}
sel, lines = [], []
for i in idx:
    r = sim.rows[i]
    rid = sim.rid[i]
    p = pm.get(r[O.ACT])
    H = hm.get(r[O.HID])
    who = ""
    if p is not None:
        who = "%s%d %s" % (p.sex, p.age, (p.occ or p.emp).replace("employed_", ""))
        if p.dis != "none":
            who += " dis:" + p.dis
    hh = ""
    if H is not None:
        hh = "%s %dp $%dk %s %s %s%s veh%d" % (H.htype.replace("group_quarters:", "GQ:"), len(H.members), round(H.income / 1000), H.alice, H.banked,
                                                 H.tenure.replace("owner_", "own_"), "" if H.lang == "English" else " " + H.lang + ("/LEP" if H.lep else ""), H.vehicles)
    other = ""
    for x in (r[O.TO], r[O.FRM]):
        if x in om:
            other = om[x].name
            break
    ben = ""
    if r[O.BEN] and r[O.BEN] != r[O.ACT] and r[O.BEN] in pm:
        b = pm[r[O.BEN]]
        ben = " for:%s%d" % (b.sex, b.age)
    money = "g%.2f u%.2f" % (r[O.GROSS], r[O.USER])
    if r[O.THIRD]:
        money += " t%.2f[%s]" % (r[O.THIRD], r[O.PAYER][:38])
    if r[O.FEE]:
        money += " fee%.2f(%s)" % (r[O.FEE], r[O.FEET][:26])
    tm = "%dm" % r[O.TMIN] + (" w%d" % r[O.WAIT] if r[O.WAIT] else "") + (" %.0fmi %s" % (r[O.MILES], r[O.MODE]) if r[O.MILES] else "")
    rel = ""
    if r[O.REL] is not None:
        rel = " rel:" + sim.rows[r[O.REL]][O.JC].split(".")[1] + "/" + sim.rows[r[O.REL]][O.OUT][:4]
    lines.append("%s %02d%02d %s %s %s | %s | %s | %s%s | %s %s/%s | %s | %s %s%s | %s" % (
        rid, r[O.T] // 60, r[O.T] % 60, RT[r[O.RT]], r[O.JC], r[O.DIS], who, hh, other, ben, money, r[O.PM], r[O.CH][:4], tm, r[O.OUT][:5], r[O.FR], rel, r[O.NARR]))
    sel.append([rid, r[O.JC], r[O.ACT]])
json.dump(sel, open("detail_parts/selection.json", "w"))
open("/tmp/detail_dump.txt", "w").write("\n".join(lines) + "\n")
from collections import Counter
print(len(lines), Counter(sim.rows[i][O.RT] for i in idx).most_common(), Counter(sim.rows[i][O.DIS] for i in idx).most_common())
print(sum(len(x) for x in lines) / len(lines), "chars per line")
