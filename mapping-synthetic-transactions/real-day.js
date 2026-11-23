// ===== Medianville in Motion v3 · the real synthetic day =====
// Loads one day's run and puts it on v3's city. Which day comes from data/runs/manifest.json through runs.js: the
// manifest's default, or ?run=<id>. Without a manifest it loads data/medianville_2027-03-03.zip (v1's 201,753 records
// under the city's new name). v3 draws one small town, so the run's six districts and its organizations are
// folded onto its homes and buildings (see FOLD and kindOf below). Records keep their
// real ids, names, amounts, districts and text; only their position on the map is
// approximate. Until the zip has loaded, v3's own placeholder day plays.
(function () {
  const FALLBACK = 'data/medianville_2027-03-03.zip';
  let RUN = FALLBACK, RUN_BYTES = 16182979;
  const pad = (n, w) => String(n).padStart(w, '0');

  // ---------- CSV read straight from bytes (same reader as the night map) ----------
  const TD = new TextDecoder();
  class Reader {
    constructor(b) { this.b = b; this.p = b[0] === 0xef && b[1] === 0xbb && b[2] === 0xbf ? 3 : 0; this.fs = new Int32Array(64); this.fe = new Int32Array(64); this.fq = new Uint8Array(64); }
    row() {
      const b = this.b, N = b.length, fs = this.fs, fe = this.fe, fq = this.fq; let p = this.p, nf = 0;
      for (;;) {
        if (nf >= 64) { while (p < N && b[p] !== 10) p++; this.p = p + 1; return nf; }
        if (p < N && b[p] === 34) {
          const s = ++p; let e2 = 0;
          while (p < N) { if (b[p] === 34) { if (b[p + 1] === 34) { p += 2; e2 = 1; continue; } break; } p++; }
          fs[nf] = s; fe[nf] = p; fq[nf] = 1 + e2; nf++; p++;
        } else { const s = p; while (p < N) { const c = b[p]; if (c === 44 || c === 10 || c === 13) break; p++; } fs[nf] = s; fe[nf] = p; fq[nf] = 0; nf++; }
        if (p >= N) { this.p = N; return nf; }
        const c = b[p];
        if (c === 44) { p++; continue; }
        if (c === 13) { p++; if (b[p] === 10) p++; this.p = p; return nf; }
        if (c === 10) { this.p = p + 1; return nf; }
        while (p < N && b[p] !== 44 && b[p] !== 10 && b[p] !== 13) p++;
        if (p < N && b[p] === 44) { p++; continue; }
        if (b[p] === 13) p++; if (b[p] === 10) p++; this.p = p; return nf;
      }
    }
    str(k) {
      const b = this.b, s = this.fs[k], e = this.fe[k];
      if (e - s < 28 && !this.fq[k]) { let r = ''; for (let i = s; i < e; i++) { const c = b[i]; if (c > 127) { r = null; break; } r += String.fromCharCode(c); } if (r !== null) return r; }
      const r = TD.decode(b.subarray(s, e)); return this.fq[k] === 2 ? r.replace(/""/g, '"') : r;
    }
    num(k) { const v = parseFloat(this.str(k)); return v === v ? v : 0; }
  }
  function header(R) { const nf = R.row(), H = {}; for (let k = 0; k < nf; k++) H[R.str(k).trim().toLowerCase()] = k; return H; }
  function eachRow(bytes, fn) { const R = new Reader(bytes), H = header(R), N = bytes.length; while (R.p < N) { const n = R.row(); if (n < 2) continue; fn(R, H); } }

  // ---------- unzip the run as it downloads ----------
  class Grow {
    constructor(n) { this.b = new Uint8Array(n > 0 ? n : 1 << 22); this.n = 0; }
    push(c) { if (this.n + c.length > this.b.length) { const nb = new Uint8Array(Math.max(this.b.length * 2, this.n + c.length)); nb.set(this.b.subarray(0, this.n)); this.b = nb; } this.b.set(c, this.n); this.n += c.length; }
    done() { return this.n === this.b.length ? this.b : this.b.subarray(0, this.n); }
  }
  const WANT = { 'records.csv': 'records', 'organizations.csv': 'organizations', 'households.csv': 'households', 'persons.csv': 'persons' };
  async function download(prog) {
    if (!window.fflate) throw new Error('the unzip helper did not load');
    const res = await fetch(RUN); if (!res.ok) throw new Error('the server answered ' + res.status);
    const total = +res.headers.get('content-length') || RUN_BYTES, rd = res.body.getReader(), got = {};
    let fail = null, seen = 0;
    const unz = new fflate.Unzip(); unz.register(fflate.UnzipInflate);
    unz.onfile = (f) => {
      const key = WANT[f.name.split('/').pop().toLowerCase()]; if (!key || got[key]) return;
      const g = (got[key] = new Grow(f.originalSize || 0));
      f.ondata = (err, chunk) => { if (err) { fail = err; return; } g.push(chunk); };
      f.start();
    };
    for (;;) {
      const { done, value } = await rd.read();
      if (done) { unz.push(new Uint8Array(0), true); break; }
      unz.push(value, false); if (fail) throw fail;
      seen += value.length; prog(Math.min(1, seen / total));
    }
    const out = {}; for (const k in got) out[k] = got[k].done();
    if (!out.records) throw new Error('records.csv was not in the zip');
    return out;
  }
  const tick = () => new Promise((r) => setTimeout(r));

  // ---------- where the real city lands on v3's town ----------
  // Homes: v3 has rowhouses (Millbank), newer houses (Brookfield Commons) and one farm (Cutler Fields).
  const FOLD = { D1: 'older', D2: 'older', D3: 'subdivision', D4: 'subdivision', D5: 'subdivision', D6: 'rural' };
  const DNAME = { D1: 'Downtown', D2: 'Inner suburbs', D3: 'Outer suburbs', D4: 'Satellite city', D5: 'Rural town', D6: 'Open country', outside: 'Outside Medianville' };
  // Organizations: each one is drawn at a v3 building of the closest kind.
  function kindOf(o) {
    const n = o.name, s = o.sector, t = o.org_type;
    if (o.district === 'outside') return 'outside';
    if (t === 'religious' || /Church|Parish|Chapel|Temple|Mosque|Synagogue|Ministr|Fellowship|Congregation|Mission/.test(n)) return 'church';
    if (/Transit|Bus Line|Paratransit/.test(n)) return 'bushub';
    if (/Library/.test(n)) return 'office';
    if (/School|Elementary|Academy|Preschool|Head Start|Pre-K|Montessori|Child ?care|Day ?care|Early Learning/i.test(n) || /educational/.test(s)) return 'school';
    if (/Pharmacy|Drug/.test(n)) return 'bigbox';
    if (/Health care/.test(s)) return 'clinic';
    if (/Bank|Credit Union|Savings|Check Cash|Cash Advance|Payday|Pawn|Title Loan|Lending|Loan/i.test(n)) return 'bank';
    if (/Utilities/.test(s) || /Water|Power|Electric Co|Gas Co|Sanitation|Waste/.test(n) && t === 'government') return 'utility';
    if (t === 'government') return 'cityhall';
    if (/Agriculture/.test(s)) return /Grain|Co-op|Elevator|Seed|Feed/.test(n) ? 'silo' : 'farmstand';
    if (/Fuel|Gas & Go|Gas Station|Petro|Quick Stop|Truck Stop|Gas\b/.test(n)) return 'gas';
    if (/Retail/.test(s)) {
      if (/Market|Grocer|Foods|Supermarket|Fresh|Butcher|Bakery/.test(n)) return 'grocery';
      if (/Corner|Mart\b|Mini|Bodega|Deli|Convenience|Smoke|Liquor/.test(n)) return 'cornershop';
      return 'bigbox';
    }
    if (/Accommodation/.test(s)) return 'diner';
    if (/Barber|Salon|Hair|Beauty|Nail|Laundr|Tailor|Cleaners/.test(n)) return 'cornershop';
    if (/Auto|Collision|Garage|Tire|Car Wash/.test(n)) return 'bigbox';
    if (/Manufacturing|Wholesale|Transportation|Construction/.test(s)) return 'shed';
    if (/Finance|Professional|Information|Management/.test(s)) return 'tower';
    return 'office';
  }
  const hash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; };

  // ---------- record kinds and words ----------
  const TYPES = ['purchase', 'bill_payment', 'income', 'benefit_issuance', 'benefit_redemption', 'transfer', 'tax', 'b2b', 'public_service_encounter', 'insurance_claim', 'non_monetary_job', 'failed_attempt', 'other'];
  const OUTS = ['completed', 'partial', 'declined', 'abandoned', 'failed', 'rescheduled'];
  // A failure is what the run's summary counts: any failed attempt, and anything declined, abandoned, failed or rescheduled. Partial counts as done.
  const isFail = (ty, oc) => ty === 11 || oc === 2 || oc === 3 || oc === 4 || oc === 5;
  const vkOf = (ty, oc) => isFail(ty, oc) ? 'fail' : ty === 10 ? 'unpaid' : ty === 2 || ty === 3 ? 'income' : ty === 1 || ty === 6 || ty === 9 ? 'bill' : ty === 8 ? 'service' : 'purchase';
  const FRICTION = { wait: 'long wait', distance: 'too far', no_transit: 'no transit', hours_mismatch: 'closed when they got there', missing_document: 'missing document', language: 'language barrier', disability_access: 'not accessible', digital_barrier: 'online barrier', fee: 'fee', insufficient_funds: 'not enough money', pending_hold: 'money on hold', benefits_cliff: 'benefits cliff', eligibility_confusion: 'eligibility confusion', out_of_stock: 'out of stock', outage: 'outage', caregiving_conflict: 'caregiving conflict', schedule_volatility: 'schedule changed', scam_attempt: 'scam attempt', price_spike: 'price spike', paperwork: 'paperwork', repeat_trip: 'repeat trip', other: 'other' };
  const NUM = new Set(['amount_gross', 'amount_paid_by_user', 'amount_paid_by_third_party', 'imputed_public_cost', 'sales_tax', 'fee_amount', 'time_minutes', 'wait_minutes', 'travel_miles']);
  const COLS = ['record_id', 'timestamp_local', 'record_type', 'job_category', 'job_statement', 'actor_person_id', 'household_id', 'from_party_id', 'to_party_id', 'beneficiary_person_id', 'district', 'channel', 'payment_method', 'amount_gross', 'amount_paid_by_user', 'amount_paid_by_third_party', 'third_party_payer', 'funding_level', 'imputed_public_cost', 'sales_tax', 'fee_type', 'fee_amount', 'time_minutes', 'wait_minutes', 'travel_miles', 'travel_mode', 'outcome', 'friction_tags', 'lens_tags', 'related_record_id', 'narrative', 'block_id', 'block_pattern', 'context_ids'];

  let D = null; // the loaded day's columns
  // One small object per record; the full row is read from the CSV bytes only when a sheet asks for it.
  function Rec(i) { this._i = i; }
  const P = Rec.prototype;
  P._real = true;
  P._blk = ''; P._pat = ''; // the systems lens's mapped block and pattern, set at load for the few records that have them
  P._row = function () {
    if (this._o) return this._o;
    const R = new Reader(D.bytes); R.p = D.off[this._i]; const n = R.row(), o = {};
    for (const k in D.H) { const c = D.H[k]; if (c < n) o[k] = NUM.has(k) ? R.num(c) : R.str(c); }
    return (this._o = o);
  };
  for (const k of COLS) Object.defineProperty(P, k, { get() { const o = this._row(); return o[k] ?? (NUM.has(k) ? 0 : ''); }, configurable: true });
  Object.defineProperties(P, {
    record_id: { get() { return D.ids ? D.ids[this._i] : 'R' + pad(this._i + 1, 7); } },
    household_id: { get() { const h = D.hid[this._i]; return h < 0 ? '' : D.hhList[h].id; } },
    record_type: { get() { return TYPES[D.type[this._i]]; } },
    outcome: { get() { return OUTS[D.out[this._i]] || 'completed'; } },
    job_category: { get() { return D.cats[D.cat[this._i]]; } },
    amount_gross: { get() { return D.amt[this._i]; } },
    amount_paid_by_user: { get() { return D.paid[this._i]; } },
    time_minutes: { get() { return Math.round(D.mins[this._i]); } },
    wait_minutes: { get() { return Math.round(this._row().wait_minutes || 0); } },
    narrative: { get() { return (this._row().narrative || '').replace(/^\[detailed\]\s*/, ''); } },
    _handWritten: { get() { return D.hand[this._i] === 1; } },
  });

  // ---------- build ----------
  async function build(b, prog) {
    const plan = H.plan, tiles = H.tiles;
    // v3 buildings by kind, and v3 homes by district
    const byKind = {}; for (const o of H.orgs) if (o.tile && o.kind !== 'transit') (byKind[o.kind] = byKind[o.kind] || []).push(o);
    byKind.bushub = byKind.bushub || [H.transit];
    const homes = {}; for (const hh of H.households) (homes[hh.district] = homes[hh.district] || []).push(hh);
    const edge = H.T(19, 13), EDGE = [10.25, 0.32, 3.5];
    const outsideParty = (id, name) => ({ id, type: 'org', name, sector: 'Outside Medianville', district: 'commercial', where: 'Outside Medianville', tile: edge, anchor: EDGE, outside: true });
    const unknown = outsideParty('X-UNKNOWN', 'Someone outside Medianville');
    const stands = new Map(); // v3 building → real places it stands for

    // organizations
    const ORG = new Map();
    if (b.organizations) eachRow(b.organizations, (R, Hd) => {
      const g = (k) => (Hd[k] != null ? R.str(Hd[k]) : '');
      const o = { org_id: g('org_id'), name: g('name'), org_type: g('org_type'), sector: g('sector'), district: g('district') };
      const kind = kindOf(o);
      let p;
      if (kind === 'outside') p = outsideParty(o.org_id, o.name);
      else {
        const list = byKind[kind] || byKind.office, v3 = list[hash(o.org_id) % list.length];
        p = { id: o.org_id, type: 'org', name: o.name, sector: o.sector, district: v3.district, where: DNAME[o.district] || o.district, tile: v3.tile, anchor: null, v3 };
        (stands.get(v3) || stands.set(v3, []).get(v3)).push(p);
      }
      ORG.set(o.org_id, p); H.party.set(o.org_id, p);
    });
    await tick();
    // households, each placed at a v3 home in its folded district
    const HHM = new Map(), hhList = [], members = new Map();
    if (b.households) eachRow(b.households, (R, Hd) => {
      const g = (k) => (Hd[k] != null ? R.str(Hd[k]) : '');
      const id = g('household_id'), dc = g('district'), fold = FOLD[dc] || 'older', list = homes[fold] || H.households, home = list[hash(id) % list.length];
      const p = { id, type: 'household', name: 'Household ' + id, district: home.district, dist: dc, where: DNAME[dc] || dc, tile: home.tile, anchor: home.anchor, dwell: home.dwell, home,
        info: { type: g('household_type'), size: +g('size') || 0, income: +g('annual_income') || 0, alice: g('alice_status'), bank: g('banked_status'), tenure: g('housing_tenure') }, hi: hhList.length, block: g('block_id') };
      hhList.push(p); HHM.set(id, p); H.party.set(id, p); members.set(home, (members.get(home) || 0) + 1);
    });
    await tick();
    const PER = new Map();
    if (b.persons) eachRow(b.persons, (R, Hd) => { const h = HHM.get(R.str(Hd.household_id)); if (h) PER.set(R.str(Hd.person_id), h); });
    b.persons = null;
    await tick();

    // records
    const bytes = b.records; let cap = 2; for (let i = 0; i < bytes.length; i++) if (bytes[i] === 10) cap++;
    const R = new Reader(bytes), N = bytes.length, Hd = header(R), c = (k) => (Hd[k] == null ? -1 : Hd[k]);
    if (c('timestamp_local') < 0 || c('record_type') < 0) throw new Error('records.csv is missing its columns');
    const cT = c('timestamp_local'), cTy = c('record_type'), cCat = c('job_category'), cHH = c('household_id'), cFr = c('from_party_id'), cTo = c('to_party_id'), cG = c('amount_gross'), cU = c('amount_paid_by_user'), c3 = c('amount_paid_by_third_party'), cMin = c('time_minutes'), cOut = c('outcome'), cNar = c('narrative'), cId = c('record_id');
    D = { bytes, H: Hd, off: new Uint32Array(cap), sec: new Float64Array(cap), type: new Uint8Array(cap), out: new Uint8Array(cap), cat: new Uint16Array(cap), amt: new Float32Array(cap), paid: new Float32Array(cap), mins: new Float32Array(cap), hid: new Int32Array(cap), hand: new Uint8Array(cap), cats: [], hhList, ids: null };
    const cBlk = c('block_id'), cPat = c('block_pattern');
    // per-minute counts the sound uses for traffic, buses, people walking and people out in person
    const cTm = c('travel_mode'), cCh = c('channel'), SD = { car: new Float32Array(1440), bus: new Float32Array(1440), walk: new Float32Array(1440), inp: new Float32Array(1440) };
    const CAR = new Set(['car', 'ride_from_family_or_friend', 'carpool']), BUS = new Set(['transit', 'school_bus', 'paratransit']), WALK = new Set(['walk', 'bike']);
    const tyMap = new Map(TYPES.map((t, i) => [t, i])), ocMap = new Map(OUTS.map((t, i) => [t, i])), catMap = new Map();
    const tre = /(?:T|\s)(\d{1,2}):(\d{2})(?::(\d{2}))?/;
    const recs = []; let i = 0, last = performance.now(), anySec = false, firstId = '', lastId = '', firstTs = '';
    const resolve = (id, hh) => {
      if (!id) return null;
      return PER.get(id) || HHM.get(id) || ORG.get(id) || unknown;
    };
    const stopNear = new Map();
    const nearestStop = (t) => { let s = stopNear.get(t); if (s) return s; let bd = 1e9; for (const st of H.stops) { const d = Math.abs(st.x - t.x) + Math.abs(st.y - t.y); if (d < bd) (bd = d), (s = st); } stopNear.set(t, s); return s; };
    while (R.p < N) {
      const o = R.p, n = R.row(); if (n < 8) continue;
      D.off[i] = o;
      if (!i) firstTs = R.str(cT);
      const m = tre.exec(R.str(cT)); let s = 0;
      if (m) { s = +m[1] * 3600 + +m[2] * 60 + (m[3] ? +m[3] : 0); if (m[3] && m[3] !== '00') anySec = true; }
      D.sec[i] = Math.min(86399, s);
      { const mi = Math.floor(D.sec[i] / 60); if (cTm >= 0) { const tm = R.str(cTm); if (CAR.has(tm)) SD.car[mi]++; else if (BUS.has(tm)) SD.bus[mi]++; else if (WALK.has(tm)) SD.walk[mi]++; } if (cCh >= 0 && R.str(cCh) === 'in_person') SD.inp[mi]++; }
      const ty = tyMap.get(R.str(cTy)) ?? 12, oc = cOut < 0 ? 0 : ocMap.get(R.str(cOut)) ?? 0;
      D.type[i] = ty; D.out[i] = oc;
      const cs = R.str(cCat); let ci = catMap.get(cs); if (ci === undefined) { ci = D.cats.length; D.cats.push(cs); catMap.set(cs, ci); } D.cat[i] = ci;
      let g = cG < 0 ? 0 : R.num(cG); if (!g) g = (cU < 0 ? 0 : R.num(cU)) + (c3 < 0 ? 0 : R.num(c3));
      D.amt[i] = g; D.paid[i] = cU < 0 ? g : R.num(cU); D.mins[i] = cMin < 0 ? 0 : R.num(cMin);
      if (cNar >= 0) { const st = R.fs[cNar]; if (bytes[st] === 91 && bytes[st + 1] === 100 && bytes[st + 2] === 101) D.hand[i] = 1; }
      if (cId >= 0) { if (!i) firstId = R.str(cId); lastId = R.str(cId); }
      const hhP = cHH < 0 ? null : HHM.get(R.str(cHH)) || null;
      D.hid[i] = hhP ? hhP.hi : -1;
      const r = new Rec(i);
      if (cBlk >= 0) { const bk = R.str(cBlk); if (bk) { r._blk = bk; if (cPat >= 0) r._pat = R.str(cPat); } }
      const from = resolve(cFr < 0 ? '' : R.str(cFr)), to = resolve(cTo < 0 ? '' : R.str(cTo));
      r._from = from || hhP || to || unknown; r._to = to || hhP || r._from;
      r._hh = hhP || (r._from.type === 'household' ? r._from : r._to.type === 'household' ? r._to : r._from);
      r._vk = vkOf(ty, oc);
      if (r._vk === 'fail') {
        if (/missed_bus|transit/.test(cs)) { r._stop = nearestStop(r._hh.tile); r._place = r._stop; }
        else { const at = r._to.type === 'org' ? r._to : r._from.type === 'org' ? r._from : null; if (at) r._place = at.tile; } // failures at home get no pin
      }
      recs.push(r); i++;
      if ((i & 8191) === 0 && performance.now() - last > 30) { prog(R.p / N); await tick(); last = performance.now(); }
    }
    const n = i;
    if (!n) throw new Error('records.csv has no records');
    // ids are R0000001… in file order; keep a list only if a run ever breaks that
    if (firstId !== 'R' + pad(1, 7) || lastId !== 'R' + pad(n, 7)) { D.ids = []; const Rr = new Reader(bytes); for (let k = 0; k < n; k++) { Rr.p = D.off[k]; Rr.row(); D.ids.push(Rr.str(cId)); } }
    // minutes as v3 uses them; whole-minute timestamps are spread evenly across their minute, in file order
    let sorted = true; for (let k = 1; k < n; k++) if (D.sec[k] < D.sec[k - 1]) { sorted = false; break; }
    if (!sorted) recs.sort((a, b2) => D.sec[a._i] - D.sec[b2._i] || a._i - b2._i);
    for (let k = 0; k < n;) {
      const s0 = D.sec[recs[k]._i]; let j = k; while (j < n && D.sec[recs[j]._i] === s0) j++;
      const span = anySec ? 1 : 60;
      for (let q = k; q < j; q++) recs[q]._t = Math.min(1439.999, (s0 + ((q - k + 0.5) / (j - k)) * span) / 60);
      k = j;
    }
    // prefix sums, minute index, and lookups the app uses
    const cm = new Float64Array(n + 1), cf = new Int32Array(n + 1), cu = new Float64Array(n + 1), hourly = new Float64Array(24);
    recs.forEach((r, k) => {
      const ii = r._i, vk = r._vk;
      cm[k + 1] = cm[k] + (vk !== 'fail' && vk !== 'unpaid' ? D.amt[ii] : 0);
      cf[k + 1] = cf[k] + (vk === 'fail' ? 1 : 0);
      cu[k + 1] = cu[k] + (vk === 'unpaid' ? D.mins[ii] : 0);
      if (D.type[ii] === 0) hourly[Math.min(23, Math.floor(r._t / 60))]++;
    });
    const minute = new Int32Array(1442); let j = 0;
    for (let m = 0; m <= 1441; m++) { while (j < n && recs[j]._t < m) j++; minute[m] = j; }
    const pos = new Int32Array(n); recs.forEach((r, k) => (pos[r._i] = k));
    const byId = D.ids ? new Map(D.ids.map((id, k) => [id, k])) : null;
    // v3 homes and buildings now stand for many real ones
    for (const hh of H.households) { hh.members = members.get(hh) || 0; hh.name = `${H.DISTRICTS[hh.district]}, home ${hh.dwell + 1}`; }
    for (const [v3, list] of stands) v3.stands = list;
    const mx = Math.max(...hourly) || 1;
    return {
      records: recs, date: (/^\d{4}-\d{2}-\d{2}/.exec(firstTs) || [''])[0], cum: { money: cm, fails: cf, unpaid: cu }, minuteIdx: minute, soundDensity: SD,
      recById: { get: (id) => { const ii = byId ? byId.get(id) : /^R\d+$/.test(id) ? parseInt(id.slice(1), 10) - 1 : -1; return ii >= 0 && ii < n ? recs[pos[ii]] : undefined; } },
      purchaseRate: (t) => { const h = (t / 60) % 24, a = Math.floor(h), f = h - a; return (4 * (hourly[a] * (1 - f) + hourly[(a + 1) % 24] * f)) / mx; },
    };
  }

  // ---------- words for real records ----------
  // 'grocery_snap_purchase' → 'Grocery SNAP purchase', 'over_the_counter_medicine' → 'Over-the-counter medicine'.
  // The acronyms match the data explorer's; the joins are the compounds that the run's 383 categories use.
  const WORD = { snap: 'SNAP', wic: 'WIC', tanf: 'TANF', ssi: 'SSI', ebt: 'EBT', irs: 'IRS', va: 'VA', ach: 'ACH', atm: 'ATM', ev: 'EV', ems: 'EMS', medicare: 'Medicare', medicaid: 'Medicaid', medigap: 'Medigap',
    p2p: 'P2P', bnpl: 'BNPL', hoa: 'HOA', fica: 'FICA', ssa: 'SSA', dmv: 'DMV', er: 'ER', ged: 'GED', ui: 'UI', id: 'ID', prek: 'pre-K', bhph: 'buy-here-pay-here', wont: 'won’t', dropoff: 'drop-off' };
  const JOIN = [['over the counter', 'over-the-counter'], ['after school', 'after-school'], ['rent to own', 'rent-to-own'], ['buy here pay here', 'buy-here-pay-here'],
    ['follow up', 'follow-up'], ['self employed', 'self-employed'], ['self employment', 'self-employment'], ['self pay', 'self-pay'], ['one time', 'one-time'], ['top up', 'top-up'],
    ['jump start', 'jump-start'], ['sit down', 'sit-down'], ['big box', 'big-box'], ['fill up', 'fill-up'], ['fill in', 'fill-in'], ['move in', 'move-in'], ['buy in', 'buy-in'],
    ['no show', 'no-show'], ['cash out', 'cash-out'], ['part b', 'Part B'], ['real ID', 'REAL ID'], ['head start', 'Head Start'], ['social security', 'Social Security']];
  const nice = (s) => {
    s = String(s || '').split('.').pop().split('_').map((w) => WORD[w] || w).join(' ');
    for (const [a, b] of JOIN) s = s.replace(new RegExp('\\b' + a + '\\b', 'g'), b);
    return s.charAt(0).toUpperCase() + s.slice(1);
  };
  const OUTWORD = { declined: 'Declined', abandoned: 'Abandoned', failed: 'Failed', rescheduled: 'Rescheduled', partial: 'Partly done' };
  function patchWords() {
    const cat = H.catLabel, out = H.outcomeWord, why = H.reason, meth = H.methodLabel;
    H.catLabel = (r) => (r._real ? nice(r.job_category) : cat(r));
    H.outcomeWord = (r) => (!r._real ? out(r) : r._vk !== 'fail' ? 'Completed' : /missed_bus/.test(r.job_category) ? 'Missed' : OUTWORD[r.outcome] || 'Didn’t work');
    H.reason = (r) => {
      if (!r._real) return why(r);
      if (r._vk !== 'fail') return '';
      const tags = String(r.friction_tags || '').split(';').filter(Boolean).map((t) => FRICTION[t] || t.replace(/_/g, ' '));
      const head = /missed_bus/.test(r.job_category) ? 'Missed the bus' : `${H.outcomeWord(r)} · ${nice(r.job_category)}`;
      return tags.length ? `${head} · ${tags.join(', ')}` : head;
    };
    const M = { ebt_cash: 'EBT cash', wic: 'WIC', check: 'Check', bnpl: 'Buy now, pay later', money_order: 'Money order', paycard: 'Paycard', payroll_deduction: 'Payroll deduction', insurance: 'Insurance' };
    H.methodLabel = (r) => (r._real && M[r.payment_method] ? M[r.payment_method] : meth(r));
  }

  // ---------- run ----------
  async function run() {
    const status = (t) => App.status && App.status(t);
    status({ state: 'loading', p: 0 });
    try {
      const sel = window.MedianvilleRuns ? await window.MedianvilleRuns.resolve(['']) : null;
      if (sel) { RUN = sel.url; RUN_BYTES = sel.run.bytes || RUN_BYTES; }
      if (App.onRuns) App.onRuns(sel);
      const bufs = await download((p) => status({ state: 'loading', p: p * 0.55 }));
      const day = await build(bufs, (p) => status({ state: 'loading', p: 0.55 + p * 0.45 }));
      patchWords();
      H.realLoaded = true;
      Object.assign(H, { records: day.records, cum: day.cum, minuteIdx: day.minuteIdx, recById: day.recById, soundDensity: day.soundDensity });
      H.RATE.purchase = day.purchaseRate;
      App.useDay();
      status({ state: 'real', n: day.records.length, date: day.date });
    } catch (e) {
      console.error(e);
      status({ state: 'failed', msg: String(e.message || e) });
    }
  }
  if (document.readyState === 'loading') window.addEventListener('DOMContentLoaded', () => setTimeout(run)); else setTimeout(run);
})();
