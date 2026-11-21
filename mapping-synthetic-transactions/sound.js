// ===== Medianville in Motion v3 · sound: a quiet city in the background, a pluck for each record =====
// Ported from the project's sound lab (Mix A, chosen Nov 20, 2026). Everything is generated with the Web Audio API.
// Sound is off until the person turns it on (the speaker button or the S key). The mix is remembered in this browser.
(function () {
  'use strict';
  const KEY = 'medianville-sound-v1';
  // The mix was saved under this key before the city was renamed (Nov 20, 2026). It's read once, copied to KEY and removed.
  const OLD_KEY = 'halvern-v3-sound-v1';
  const DEF = { master: 0.7, amb: { on: true, vol: 0.25 }, rec: { on: true, vol: 0.6 } };
  let set = JSON.parse(JSON.stringify(DEF));
  const load = () => {
    try {
      const v = localStorage.getItem(KEY);
      if (v !== null) return v;
      const old = localStorage.getItem(OLD_KEY);
      if (old !== null) { try { localStorage.setItem(KEY, old); localStorage.removeItem(OLD_KEY); } catch (e) {} }
      return old;
    } catch (e) { return null; }
  };
  try { const s = JSON.parse(load() || 'null'); if (s && s.amb && s.rec) set = { master: +s.master || DEF.master, amb: { on: !!s.amb.on, vol: +s.amb.vol }, rec: { on: !!s.rec.on, vol: +s.rec.vol } }; } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(set)); } catch (e) {} };

  // pitch by record kind (C major pentatonic); failures get their own low thud
  const NOTE = { purchase: 523.25, bill: 587.33, income: 783.99, service: 261.63, unpaid: 293.66 };
  const THRESH = 12; // records a second; above this, single plucks give way to a pluck cloud
  const CAM = {
    street: { traffic: 1, hiss: 1, veh: 1, bus: 1, cross: 1, birds: 1, wind: 0.55, voices: 1, verb: 0.12, lp: 10000 },
    tabletop: { traffic: 0.85, hiss: 0.45, veh: 0.5, bus: 0.6, cross: 0.35, birds: 0.7, wind: 0.8, voices: 0.55, verb: 0.28, lp: 4200 },
    skyline: { traffic: 0.7, hiss: 0.12, veh: 0.12, bus: 0.18, cross: 0, birds: 0.35, wind: 1.3, voices: 0.18, verb: 0.55, lp: 1300 },
  };
  const lerpCam = (A, B, f) => { const o = {}; for (const k in A) o[k] = A[k] + (B[k] - A[k]) * f; return o; };

  // ---------- day curves (minutes 0–1439) ----------
  let SER = null;
  function smooth(a, w) { const n = a.length, o = new Float32Array(n), h = w >> 1; for (let i = 0; i < n; i++) { let s = 0; for (let j = -h; j <= h; j++) s += a[(i + j + n) % n]; o[i] = s / (2 * h + 1); } return o; }
  function norm(a, q = 0.95) { const s = Array.from(a).sort((x, y) => x - y), p = s[Math.floor(q * (s.length - 1))] || 1; return a.map((v) => Math.min(1.4, v / p)); }
  function build() {
    const sd = window.H && H.soundDensity;
    let car, bus, walk, inp;
    if (sd) ({ car, bus, walk, inp } = sd);
    else { // placeholder day: every record stands in for traffic and people out
      car = new Float32Array(1440); for (const r of (window.H && H.records) || []) car[Math.min(1439, Math.floor(r._t))]++;
      bus = car.map((v) => v * 0.15); walk = car.map((v) => v * 0.1); inp = car;
    }
    const birds = new Float32Array(1440).map((_, i) => { const h = i / 60; return Math.min(1, Math.exp(-Math.pow((h - 7.1) / 0.7, 2)) + (h > 7.5 && h < 17.6 ? 0.22 : 0) + 0.35 * Math.exp(-Math.pow((h - 17.9) / 0.45, 2))); });
    SER = {
      traffic: norm(smooth(car.map((c, i) => c + 2 * bus[i]), 41)).map((v) => 0.06 + 0.94 * v),
      bus: norm(smooth(bus, 41)), walk: norm(smooth(walk.map((w, i) => w + 0.15 * inp[i]), 31)),
      voices: norm(smooth(inp, 31)).map((v) => 0.04 + 0.96 * v), birds,
      real: !!sd,
    };
  }
  const at = (a, m) => { m = ((m % 1440) + 1440) % 1440; const i = Math.floor(m), f = m - i; return a[i] * (1 - f) + a[(i + 1) % 1440] * f; };

  // ---------- engine ----------
  let ctx = null, E = null, on = false;
  const poisson = (l) => { if (l <= 0) return 0; if (l > 30) return Math.max(0, Math.round(l + Math.sqrt(l) * (Math.random() * 2 - 1))); const L = Math.exp(-l); let k = 0, p = 1; do { k++; p *= Math.random(); } while (p > L); return k - 1; };
  function engine(c) {
    const sr = c.sampleRate, e = { c, ends: [], voices: 0, acc: {}, accF: 0, cnt: {}, fails: 0 };
    const noise = (sec, brown) => { const b = c.createBuffer(2, sr * sec, sr); for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); let l = 0; for (let i = 0; i < d.length; i++) { const w = Math.random() * 2 - 1; if (brown) { l = (l + 0.02 * w) / 1.02; d[i] = l * 3.5; } else d[i] = w * 0.5; } } return b; };
    const ir = (sec, dec) => { const b = c.createBuffer(2, sr * sec, sr); for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); let lp = 0; for (let i = 0; i < d.length; i++) { lp = lp * 0.6 + (Math.random() * 2 - 1) * 0.4; d[i] = lp * Math.pow(1 - i / d.length, dec); } } return b; };
    const G = (v = 0) => { const g = c.createGain(); g.gain.value = v; return g; };
    const F = (t, f, q = 0.7) => { const b = c.createBiquadFilter(); b.type = t; b.frequency.value = f; b.Q.value = q; return b; };
    const loop = (buf) => { const s = c.createBufferSource(); s.buffer = buf; s.loop = true; s.start(0, Math.random() * buf.duration); return s; };
    e.white = noise(3, false); const brown = noise(4, true); e.G = G; e.F = F;
    e.master = G(0); const lim = c.createDynamicsCompressor(); lim.threshold.value = -9; lim.knee.value = 3; lim.ratio.value = 18; lim.attack.value = 0.002; lim.release.value = 0.2;
    e.master.connect(lim); lim.connect(c.destination);
    e.amb = G(0); e.rec = G(0); e.amb.connect(e.master); e.rec.connect(e.master);
    e.ambLP = F('lowpass', 4200, 0.5); e.ambIn = G(1); e.ambIn.connect(e.ambLP); e.ambLP.connect(e.amb);
    const verb = c.createConvolver(); verb.buffer = ir(2.8, 3); e.verbRet = G(0.3); verb.connect(e.verbRet); e.verbRet.connect(e.ambIn); e.send = G(1); e.send.connect(verb);
    const rv = c.createConvolver(); rv.buffer = ir(1.3, 4); const rvg = G(0.22); rv.connect(rvg); rvg.connect(e.rec); e.rsend = G(1); e.rsend.connect(rv);
    const t1 = loop(brown); e.tLP = F('lowpass', 380, 0.4); e.gTraffic = G(0); t1.connect(e.tLP); e.tLP.connect(e.gTraffic); e.gTraffic.connect(e.ambIn);
    const t2 = loop(e.white), tBP = F('bandpass', 1100, 0.6); e.gHiss = G(0); t2.connect(tBP); tBP.connect(e.gHiss); e.gHiss.connect(e.ambIn);
    const w1 = loop(e.white); e.wBP = F('bandpass', 420, 1.3); e.gWind = G(0); w1.connect(e.wBP); e.wBP.connect(e.gWind); e.gWind.connect(e.ambIn); e.gWind.connect(e.send);
    const v1 = loop(brown); e.gVoices = G(0); e.vAM = G(0.5); v1.connect(e.vAM);
    [[520, 5, 1], [1250, 6, 0.7], [2400, 7, 0.35]].forEach(([f, q, a]) => { const b = F('bandpass', f, q), g = G(a); e.vAM.connect(b); b.connect(g); g.connect(e.gVoices); });
    e.gVoices.connect(e.ambIn); e.gVoices.connect(e.send);
    return e;
  }
  const ramp = (p, v, t, tc = 0.35) => p.setTargetAtTime(v, t, tc);
  const env = (g, t, a, pk, d) => { g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(pk, 0.0002), t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + d); };
  const track = (e, n, stop) => { e.ends.push(stop); e.voices++; n.stop(stop); };
  const nsrc = (e, t) => { const s = e.c.createBufferSource(); s.buffer = e.white; s.start(t, Math.random() * 2); return s; };
  const pan = (e, v) => { const p = e.c.createStereoPanner(); p.pan.value = v; return p; };

  function vehicle(e, t, big, lvl) {
    const c = e.c, d = big ? 5.2 : 2.4 + Math.random() * 2, dir = Math.random() < 0.5 ? -1 : 1, pk = (big ? 0.5 : 0.32) * lvl * (0.6 + Math.random() * 0.6);
    const p = c.createStereoPanner(); p.pan.setValueAtTime(-0.85 * dir, t); p.pan.linearRampToValueAtTime(0.85 * dir, t + d);
    const g = e.G(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(pk, t + d * 0.5); g.gain.exponentialRampToValueAtTime(0.0001, t + d);
    const n = nsrc(e, t), bp = e.F('bandpass', 380, 0.9); bp.frequency.setValueAtTime(big ? 260 : 360, t); bp.frequency.linearRampToValueAtTime(big ? 520 : 900 + Math.random() * 300, t + d * 0.5); bp.frequency.linearRampToValueAtTime(big ? 220 : 300, t + d); n.connect(bp); bp.connect(g);
    const o = c.createOscillator(); o.type = 'sawtooth'; const f0 = big ? 36 : 50 + Math.random() * 30; o.frequency.setValueAtTime(f0, t); o.frequency.linearRampToValueAtTime(f0 * 1.05, t + d * 0.5); o.frequency.linearRampToValueAtTime(f0 * 0.9, t + d);
    const olp = e.F('lowpass', big ? 200 : 160, 0.7), og = e.G(big ? 0.9 : 0.5); o.connect(olp); olp.connect(og); og.connect(g); o.start(t);
    g.connect(p); p.connect(e.ambIn); const s = e.G(0.12); g.connect(s); s.connect(e.send);
    track(e, n, t + d + 0.05); o.stop(t + d + 0.05);
    if (big && Math.random() < 0.55) { const h = nsrc(e, t + d * 0.62), hp = e.F('highpass', 2600, 0.7), hg = e.G(), hpn = pan(e, 0.2 * dir); env(hg, t + d * 0.62, 0.02, 0.16 * lvl, 0.7); h.connect(hp); hp.connect(hg); hg.connect(hpn); hpn.connect(e.ambIn); track(e, h, t + d * 0.62 + 0.8); }
  }
  function chirp(e, t, lvl) { const o = e.c.createOscillator(), g = e.G(), p = pan(e, -0.35); o.frequency.setValueAtTime(2700, t); o.frequency.exponentialRampToValueAtTime(3500, t + 0.035); env(g, t, 0.004, 0.05 * lvl, 0.05); o.connect(g); g.connect(p); p.connect(e.ambIn); o.start(t); track(e, o, t + 0.08); }
  function bird(e, t, lvl) {
    const c = e.c, kind = Math.floor(Math.random() * 3), n = 1 + Math.floor(Math.random() * 5), base = 2200 + Math.random() * 2200, p = pan(e, Math.random() * 1.6 - 0.8), bus = e.G(0.07 * lvl);
    bus.connect(p); p.connect(e.ambIn); const s = e.G(0.5); bus.connect(s); s.connect(e.send);
    let tt = t;
    for (let i = 0; i < n; i++) {
      const d = 0.05 + Math.random() * 0.1, o = c.createOscillator(), g = e.G();
      if (kind === 0) { o.frequency.setValueAtTime(base, tt); o.frequency.exponentialRampToValueAtTime(base * 1.5, tt + d); }
      else if (kind === 1) { o.frequency.setValueAtTime(base * 1.4, tt); o.frequency.exponentialRampToValueAtTime(base * 0.8, tt + d); }
      else { o.frequency.value = base; const m = c.createOscillator(), mg = e.G(base * 0.08); m.frequency.value = 28 + Math.random() * 14; m.connect(mg); mg.connect(o.frequency); m.start(tt); m.stop(tt + d + 0.02); }
      env(g, tt, 0.01, 1, d); o.connect(g); g.connect(bus); o.start(tt); track(e, o, tt + d + 0.03); tt += d + 0.04 + Math.random() * 0.1;
    }
  }
  function pluck(e, t, f, gain, pv) {
    const c = e.c, out = e.G(1), p = pan(e, pv); out.connect(p); p.connect(e.rec); const s = e.G(0.5); out.connect(s); s.connect(e.rsend);
    const o = c.createOscillator(), lp = e.F('lowpass', f * 6, 1), g = e.G(); o.type = 'triangle'; o.frequency.value = f;
    lp.frequency.setValueAtTime(f * 8, t); lp.frequency.exponentialRampToValueAtTime(f * 1.2, t + 0.25); env(g, t, 0.004, gain * 2.2, 0.3);
    o.connect(lp); lp.connect(g); g.connect(out); o.start(t); track(e, o, t + 0.4);
  }
  function thud(e, t, gain, pv) { const o = e.c.createOscillator(), g = e.G(), p = pan(e, pv); o.frequency.setValueAtTime(110, t); o.frequency.exponentialRampToValueAtTime(52, t + 0.22); env(g, t, 0.004, gain * 2.2, 0.28); o.connect(g); g.connect(p); p.connect(e.rec); o.start(t); track(e, o, t + 0.35); }

  // one step: real seconds [now, now + dt), at day minute m
  function step(e, now, dt, m, cam, playing) {
    e.ends = e.ends.filter((x) => x > now); e.voices = e.ends.length;
    const L = { traffic: at(SER.traffic, m), bus: at(SER.bus, m), walk: at(SER.walk, m), voices: at(SER.voices, m), birds: at(SER.birds, m) };
    ramp(e.master.gain, on ? set.master : 0, now, 0.08);
    ramp(e.amb.gain, set.amb.on ? set.amb.vol : 0, now, 0.15);
    ramp(e.rec.gain, set.rec.on ? set.rec.vol : 0, now, 0.15);
    ramp(e.ambLP.frequency, cam.lp, now, 0.3); ramp(e.verbRet.gain, cam.verb, now, 0.3);
    // the background follows the time of day in real seconds, so it never speeds up with playback
    ramp(e.gTraffic.gain, 0.14 * L.traffic * cam.traffic, now, 0.8); ramp(e.tLP.frequency, 260 + 380 * L.traffic, now, 1);
    ramp(e.gHiss.gain, 0.025 * L.traffic * cam.hiss, now, 0.8);
    if (Math.random() < dt * 0.4) ramp(e.wBP.frequency, 280 + Math.random() * 500, now, 2);
    ramp(e.gWind.gain, (0.022 + 0.018 * Math.random()) * cam.wind, now, 1.5);
    ramp(e.gVoices.gain, 0.055 * L.voices * cam.voices, now, 0.8);
    for (let k = 0; k < 3; k++) e.vAM.gain.setTargetAtTime(0.25 + Math.random() * 0.75, now + Math.random() * dt, 0.04);
    if (on && set.amb.on && e.voices < 140) {
      const n1 = poisson(dt * 0.55 * L.traffic * (cam.veh > 0 ? 1 : 0)); for (let i = 0; i < n1; i++) vehicle(e, now + Math.random() * dt, false, cam.veh);
      const n2 = poisson(dt * 0.09 * L.bus * (cam.bus > 0 ? 1 : 0)); for (let i = 0; i < n2; i++) vehicle(e, now + Math.random() * dt, true, cam.bus);
      if (L.birds > 0.02) { const n3 = poisson(dt * 1.6 * L.birds); for (let i = 0; i < n3; i++) bird(e, now + Math.random() * dt, cam.birds); }
      const hr = m / 60;
      if (cam.cross > 0.02 && hr > 6 && hr < 22 && L.walk > 0.08) for (let k = Math.ceil(now * 1.6); k < (now + dt) * 1.6; k++) { const tt = k / 1.6; if (tt % 15 < 6) chirp(e, tt, cam.cross * Math.min(1, L.walk)); }
    }
    // records: the kinds counted since the last step
    let tot = 0; for (const k in e.cnt) tot += e.cnt[k];
    const rate = dt > 0 ? tot / dt : 0, go = on && set.rec.on && e.voices < 180;
    if (rate <= THRESH) {
      for (const k in e.cnt) { e.acc[k] = (e.acc[k] || 0) + e.cnt[k]; while (e.acc[k] >= 1) { e.acc[k] -= 1; if (go) pluck(e, now + Math.random() * dt, NOTE[k] || 523.25, 0.11, Math.random() * 1.2 - 0.6); } }
    } else { // pluck cloud: a sample that grows only a little busier and louder as the count climbs
      e.acc = {};
      const lg = Math.log10(1 + rate / THRESH), dens = Math.min(0.9, 0.45 + 0.15 * lg), cg = Math.min(0.085, 0.07 * (1 + 0.1 * lg)), ks = Object.keys(e.cnt), n = poisson(dt * THRESH * dens);
      for (let i = 0; i < n; i++) { let r = Math.random() * tot, k = ks[0]; for (const kk of ks) { r -= e.cnt[kk]; if (r <= 0) { k = kk; break; } } if (go) pluck(e, now + Math.random() * dt, NOTE[k] || 523.25, cg, Math.random() * 1.4 - 0.7); }
    }
    e.accF += Math.min(e.fails, 3 * dt); // records that didn't work: always heard, at most 3 a second
    while (e.accF >= 1) { e.accF -= 1; if (go) thud(e, now + Math.random() * dt, 0.11, Math.random() * 1.2 - 0.6); }
    e.cnt = {}; e.fails = 0;
    if (!playing) e.accF = 0;
  }

  // camera: zoom and tilt choose between street, tabletop and skyline
  function camera(S) {
    const z = Math.log(App.cam.zoom / App.ZMIN) / Math.log(App.ZMAX / App.ZMIN); // 0 far … 1 close
    let c = z < 0.45 ? lerpCam(CAM.skyline, CAM.tabletop, Math.max(0, z / 0.45) * 0.6 + 0.4) : lerpCam(CAM.tabletop, CAM.street, (z - 0.45) / 0.55);
    if (S.view === 'mini' && window.MiniView && MiniView.angle) { const p = MiniView.angle().pitch; if (p < 22) c = lerpCam(c, CAM.skyline, Math.min(1, (22 - p) / 14)); }
    return c;
  }

  // ---------- public hooks the app calls ----------
  let acc = 0;
  const Sound = (window.MedianvilleSound = {
    rec(vk) { if (!E || !on) return; if (vk === 'fail') E.fails++; else E.cnt[vk] = (E.cnt[vk] || 0) + 1; },
    frame(dt) {
      if (!E) return; acc += dt; if (acc < 0.05) return; // schedule about 20 times a second
      if (!SER || (!SER.real && window.H && H.soundDensity)) build();
      const S = App.S; step(E, ctx.currentTime + 0.12, acc, S.t, camera(S), S.playing); acc = 0;
    },
    async toggle(force) {
      const want = force === undefined ? !on : !!force;
      try {
        if (want && !ctx) { const AC = window.AudioContext || window.webkitAudioContext; ctx = new AC(); build(); E = engine(ctx); }
        if (want && ctx.state === 'suspended') await ctx.resume();
        on = want;
      } catch (err) { on = false; console.error(err); }
      ui(); say(on ? 'Sound on.' : 'Sound off.');
    },
    get on() { return on; },
  });
  function say(msg) { const l = document.getElementById('live'); if (!l) return; l.textContent = ''; setTimeout(() => (l.textContent = msg), 30); }
  // a hidden tab stops the animation, so stop the sound with it
  document.addEventListener('visibilitychange', () => { if (!ctx) return; if (document.hidden) ctx.suspend(); else if (on) ctx.resume(); });

  // ---------- controls: the speaker button and its panel ----------
  function ui() {
    const b = document.getElementById('snd-btn'); if (!b) return;
    b.setAttribute('aria-pressed', String(on)); b.classList.toggle('on', on);
    b.querySelector('.snd-w').style.display = on ? '' : 'none'; b.querySelector('.snd-x').style.display = on ? 'none' : '';
    b.setAttribute('aria-label', on ? 'Sound on. Open sound settings' : 'Sound off. Open sound settings');
    const p = document.getElementById('snd-pop'); if (!p) return;
    p.querySelector('#snd-on').textContent = on ? 'Turn sound off' : 'Turn sound on';
    p.querySelector('#snd-on').setAttribute('aria-pressed', String(on));
    for (const k of ['amb', 'rec']) { const t = p.querySelector(`[data-snd-t="${k}"]`); t.setAttribute('aria-pressed', String(set[k].on)); t.textContent = set[k].on ? 'On' : 'Off'; }
    p.querySelector('[data-snd-r="master"]').value = set.master; p.querySelector('[data-snd-r="amb"]').value = set.amb.vol; p.querySelector('[data-snd-r="rec"]').value = set.rec.vol;
  }
  function mount() {
    const b = document.getElementById('snd-btn'), p = document.getElementById('snd-pop'); if (!b || !p) return;
    const open = (v) => { p.hidden = !v; b.setAttribute('aria-expanded', String(v)); };
    b.addEventListener('click', (e) => { e.stopPropagation(); open(p.hidden); });
    document.addEventListener('click', (e) => { if (!p.hidden && !p.contains(e.target) && e.target !== b) open(false); });
    p.addEventListener('keydown', (e) => { if (e.key === 'Escape') { e.stopPropagation(); open(false); b.focus(); } });
    p.querySelector('#snd-on').addEventListener('click', () => Sound.toggle());
    p.querySelectorAll('[data-snd-t]').forEach((t) => t.addEventListener('click', () => { const k = t.dataset.sndT; set[k].on = !set[k].on; save(); ui(); }));
    p.querySelectorAll('[data-snd-r]').forEach((r) => r.addEventListener('input', () => { const k = r.dataset.sndR; if (k === 'master') set.master = +r.value; else set[k].vol = +r.value; save(); }));
    p.querySelector('#snd-reset').addEventListener('click', () => { set = JSON.parse(JSON.stringify(DEF)); save(); ui(); });
    ui();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();

  // offline check for tests: renders a few seconds without speakers and reports the level
  Sound._offline = async (startMin, secs, minPerSec) => {
    if (!SER) build();
    const oc = new OfflineAudioContext(2, 44100 * secs, 44100), e = engine(oc), was = on; on = true;
    const recs = H.records, T = (i) => recs[i]._t; let m = startMin, idx = H.indexAt ? H.indexAt(m) : 0;
    for (let t = 0; t < secs - 0.3; t += 0.05) {
      const m1 = m + 0.05 * minPerSec;
      while (idx < recs.length && T(idx) <= m1) { const vk = recs[idx]._vk; if (vk === 'fail') e.fails++; else e.cnt[vk] = (e.cnt[vk] || 0) + 1; idx++; }
      step(e, t + 0.05, 0.05, m, CAM.tabletop, true); m = m1;
    }
    on = was;
    const r = await oc.startRendering(); let pk = 0, q = 0, n = 0;
    for (let ch = 0; ch < 2; ch++) { const d = r.getChannelData(ch); for (let i = 0; i < d.length; i++) { const a = Math.abs(d[i]); if (a > pk) pk = a; q += d[i] * d[i]; n++; } }
    return { peak: +pk.toFixed(3), rmsDb: +(10 * Math.log10(q / n)).toFixed(1) };
  };
})();
