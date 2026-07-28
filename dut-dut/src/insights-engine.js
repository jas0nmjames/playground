// insights-engine.js — rule-based music-theory analysis of a dut-dut project.
// Pure ES module, no DOM. Portable to the React port.
// analyzeProject(project, opts) -> [{ id, sectionId, title, body, terms:[{label,url}], color, targets:[{sectionId, groupId|null, beats:[..]}] }]

const W = 'https://en.wikipedia.org/wiki/';
const TERMS = {
  timeSig: { label: 'Time signature', url: W + 'Time_signature' },
  measure: { label: 'Measure (bar)', url: W + 'Bar_(music)' },
  tempo: { label: 'Tempo', url: W + 'Tempo' },
  beat: { label: 'Beat', url: W + 'Beat_(music)' },
  sixteenth: { label: 'Sixteenth note', url: W + 'Sixteenth_note' },
  triplet: { label: 'Triplet', url: W + 'Tuplet' },
  syncopation: { label: 'Syncopation', url: W + 'Syncopation' },
  accent: { label: 'Accent', url: W + 'Accent_(music)' },
  backbeat: { label: 'Backbeat', url: W + 'Beat_(music)#On-beat_and_off-beat' },
  rudiment: { label: 'Drum rudiment', url: W + 'Drum_rudiment' },
  pas: { label: 'PAS 40 rudiments', url: 'https://pas.org/rudiments/' },
  vicfirth: { label: 'Vic Firth lessons', url: 'https://ae.vicfirth.com/education/40-essential-rudiments/' },
  flam: { label: 'Flam', url: W + 'Drum_rudiment#Flam_rudiments' },
  diddle: { label: 'Diddle', url: W + 'Drum_rudiment#Diddle_rudiments' },
  roll: { label: 'Drum roll', url: W + 'Drum_roll' },
  ostinato: { label: 'Ostinato', url: W + 'Ostinato' },
  hemiola: { label: 'Hemiola', url: W + 'Hemiola' },
  polyrhythm: { label: 'Polyrhythm', url: W + 'Polyrhythm' },
  callResponse: { label: 'Call and response', url: W + 'Call_and_response_(music)' },
  unison: { label: 'Unison', url: W + 'Unison' },
  dynamics: { label: 'Dynamics', url: W + 'Dynamics_(music)' },
  rest: { label: 'Rest', url: W + 'Rest_(music)' },
  swing: { label: 'Swing', url: W + 'Swing_(jazz_performance_style)' },
  groove: { label: 'Groove', url: W + 'Groove_(music)' },
};
const PALETTE = ['oklch(58% 0.14 25)', 'oklch(60% 0.12 85)', 'oklch(54% 0.12 150)', 'oklch(55% 0.13 235)', 'oklch(55% 0.13 300)', 'oklch(54% 0.12 340)'];
const NEUTRAL = 'oklch(60% 0.02 260)';
// value bits: 1 hit, 2 accent, 4 flam, 8 diddle, 16 buzz
const VBIT = { 1: 1, 2: 2, 3: 4, 4: 8, 5: 16 };

function digest(sec, subs, notesForSec, groups, rows, gsubs) {
  const beats = sec.measures * 4;
  const scOf = (gid, b) => ((gsubs && gsubs[gid] && gsubs[gid][b]) || subs[b] || 4);
  const byGroup = {};
  for (const g of groups) byGroup[g.id] = Array.from({ length: beats }, (_, b) => ({ sc: scOf(g.id, b), m: new Array(scOf(g.id, b)).fill(0) }));
  for (const r of rows) {
    const beatsArr = (notesForSec && notesForSec[r.id]) || [];
    for (let b = 0; b < beats; b++) {
      const cell = byGroup[r.groupId][b];
      const arr = beatsArr[b] || [];
      for (let s = 0; s < cell.sc; s++) { const v = arr[s] || 0; if (v) cell.m[s] |= VBIT[v] || 1; }
    }
  }
  return { beats, byGroup };
}
function runs(beatIdxs) {
  const sorted = [...new Set(beatIdxs)].sort((a, b) => a - b);
  const out = [];
  for (const b of sorted) {
    const last = out[out.length - 1];
    if (last && b === last[1] + 1) last[1] = b; else out.push([b, b]);
  }
  return out;
}
const t = (...keys) => keys.map(k => TERMS[k]);

function analyzeSection(sec, subs, notesForSec, groups, rows, gsubs, liveForSec) {
  const { beats, byGroup } = digest(sec, subs, notesForSec, groups, rows, gsubs);
  const out = [];
  const tgt = (groupId, beatList) => ({ sectionId: sec.id, groupId, beats: beatList });
  const gname = id => (groups.find(g => g.id === id) || {}).name || id;
  let anyOnset = false, soundedPos = 0, totalPos = 0;
  for (const g of groups) byGroup[g.id].forEach(c => { totalPos += c.sc; c.m.forEach(v => { if (v) { anyOnset = true; soundedPos++; } }); });
  if (!anyOnset) {
    out.push({ kind: 'empty', sectionId: sec.id, title: 'A blank slate', body: 'Nothing painted in "' + sec.name + '" yet. Pick a tool and click cells in the grid — each column is one slice of a beat, each row one drum.', terms: t('beat', 'sixteenth'), targets: [] });
    return out;
  }
  // Rudiments
  const RUD = [
    { bit: 4, kind: 'flam', title: 'Flams thicken the attack', body: 'A flam sneaks a soft grace note in just before the main stroke, fattening a single hit into a "brrap". It is one of the 40 standard drum rudiments every drumline learns.', terms: t('flam', 'rudiment', 'pas', 'vicfirth') },
    { bit: 8, kind: 'diddle', title: 'Diddles double up', body: 'Each diddle squeezes two strokes into one grid slot with a single hand motion — the building block of double-stroke rolls and paradiddles.', terms: t('diddle', 'rudiment', 'pas') },
    { bit: 16, kind: 'buzz', title: 'Buzz rolls sustain the sound', body: 'The z marks a multiple-bounce (buzz) roll: the stick is pressed into the head so it rebounds freely, turning a hit into a sustained crush of sound.', terms: t('roll', 'rudiment', 'vicfirth') },
  ];
  for (const r of RUD) {
    const targets = [];
    for (const g of groups) {
      const bs = [];
      byGroup[g.id].forEach((c, b) => { if (c.m.some(v => v & r.bit)) bs.push(b); });
      if (bs.length) targets.push(tgt(g.id, bs));
    }
    if (targets.length) out.push({ kind: r.kind, sectionId: sec.id, title: r.title, body: r.body, terms: r.terms, targets });
  }
  // Syncopation: offbeat onsets over a silent downbeat
  for (const g of groups) {
    const syncBeats = [];
    byGroup[g.id].forEach((c, b) => { if (!c.m[0] && c.m.some((v, s) => s > 0 && v)) syncBeats.push(b); });
    if (syncBeats.length >= 2) {
      out.push({ kind: 'sync-' + g.id, sectionId: sec.id, title: 'Syncopation in the ' + gname(g.id).toLowerCase(), body: 'In the highlighted beats the ' + gname(g.id).toLowerCase() + ' skips the downbeat and lands between the beats instead. That off-beat emphasis is syncopation — the tension that makes a groove lean forward.', terms: t('syncopation', 'beat', 'groove'), targets: [tgt(g.id, syncBeats)] });
    }
  }
  // Backbeat accents
  for (const g of groups) {
    const on24 = [], other = [];
    byGroup[g.id].forEach((c, b) => { if (c.m.some(v => v & 2)) ((b % 4 === 1 || b % 4 === 3) ? on24 : other).push(b); });
    if (on24.length >= 2 && other.length === 0) {
      out.push({ kind: 'backbeat-' + g.id, sectionId: sec.id, title: 'Backbeat accents', body: 'The ' + gname(g.id).toLowerCase() + ' accents fall on beats 2 and 4 — the backbeat, the same emphasis that powers rock, funk, and pop.', terms: t('backbeat', 'accent'), targets: [tgt(g.id, on24)] });
      break;
    }
  }
  // Accent melody: accents carving a shape inside a stream of taps
  for (const g of groups) {
    let hits = 0; const accBeats = [];
    byGroup[g.id].forEach((c, b) => { c.m.forEach(v => { if (v) hits++; }); if (c.m.some(v => v & 2)) accBeats.push(b); });
    const accents = byGroup[g.id].reduce((n, c) => n + c.m.filter(v => v & 2).length, 0);
    if (hits >= 8 && accents >= 3 && accents <= hits / 2) {
      out.push({ kind: 'accmel-' + g.id, sectionId: sec.id, title: 'An accent melody rides on top', body: 'Inside the ' + gname(g.id).toLowerCase() + '\'s stream of taps, the accented notes form their own rhythm. Listeners hear that accent pattern as the melody of the phrase — dynamics doing the singing.', terms: t('accent', 'dynamics'), targets: [tgt(g.id, accBeats)] });
      break;
    }
  }
  // Pulse / ostinato
  for (const g of groups) {
    let down = 0, off = 0, total = 0;
    byGroup[g.id].forEach(c => { if (c.m[0]) down++; c.m.forEach((v, s) => { if (v) { total++; if (s > 0) off++; } }); });
    if (down >= beats * 0.9 && total && off / total <= 0.25) {
      out.push({ kind: 'pulse-' + g.id, sectionId: sec.id, title: gname(g.id) + ' keeps the pulse', body: 'The ' + gname(g.id).toLowerCase() + ' marks every beat — a steady repeating figure (an ostinato) that everyone else locks onto. Someone always has to be the clock.', terms: t('ostinato', 'beat'), targets: [tgt(g.id, byGroup[g.id].map((c, b) => b))] });
      break;
    }
  }
  // Mixed subdivisions between parts (per-part subdivision writing)
  {
    const mixed = [];
    for (let b = 0; b < beats; b++) {
      const scs = new Set();
      for (const g of groups) { const c = byGroup[g.id][b]; if (c.m.some(v => v)) scs.add(c.sc); }
      if (scs.size >= 2) mixed.push(b);
    }
    if (mixed.length) {
      out.push({ kind: 'crossdiv', sectionId: sec.id, title: 'Two subdivisions at once', body: 'On the highlighted beats one part splits the beat into three while another splits it into four. Two different grids running against each other inside the same pulse is a cross-rhythm — the effect is a shimmer that resolves every time the parts meet on the downbeat.', terms: t('polyrhythm', 'hemiola', 'triplet'), targets: [tgt(null, mixed)] });
    }
  }
  // Timing of a live play-along take
  if (liveForSec) {
    let n = 0, sumMs = 0, worst = 0; const takeBeats = [];
    const beatMs = 60000 / (sec._tempo || 120);
    for (const r of rows) {
      const larr = liveForSec[r.id] || [];
      for (let b = 0; b < beats; b++) {
        const cell = larr[b] || [];
        const sc = byGroup[r.groupId] ? byGroup[r.groupId][b].sc : 4;
        for (let s = 0; s < cell.length; s++) {
          const m = cell[s] || 0;
          if (m < 2) continue;
          const off = m - 2;
          const dev = (off <= 0.5 ? off : off - 1) * (beatMs / sc);
          n++; sumMs += dev; if (Math.abs(dev) > Math.abs(worst)) worst = dev;
          takeBeats.push(b);
        }
      }
    }
    if (n >= 4) {
      const avg = sumMs / n;
      const lean = avg > 8 ? 'a touch behind the grid' : avg < -8 ? 'slightly ahead of the grid' : 'right on top of the grid';
      out.push({ kind: 'take', sectionId: sec.id, title: 'Your take, measured', body: 'Of the ' + n + ' notes you tapped in freely, the average landed ' + lean + ' (' + (avg >= 0 ? '+' : '') + Math.round(avg) + ' ms), the loosest by ' + Math.round(Math.abs(worst)) + ' ms. Small, consistent lateness reads as laid-back feel; scattered error reads as unsteady. Switch to auto-rhythm to hear the same idea locked to the grid.', terms: t('beat', 'groove', 'swing'), targets: [tgt(null, takeBeats)] });
    }
  }
  // Triplet vs straight subdivisions
  const tripBeats = [], eighthBeats = [];
  for (let b = 0; b < beats; b++) {
    let three = false, two = false;
    for (const g of groups) { const c = byGroup[g.id][b]; if (c.sc === 3) three = true; else if (c.sc === 2) two = true; }
    if (three) tripBeats.push(b); else if (two) eighthBeats.push(b);
  }
  if (tripBeats.length && tripBeats.length < beats) {
    out.push({ kind: 'triplets', sectionId: sec.id, title: 'Duple meets triple', body: 'The highlighted beats divide into triplets — three equal notes where the neighbors have four sixteenths' + (eighthBeats.length ? ' or two eighths' : '') + '. Switching the subdivision mid-phrase flips the feel from square to rolling.', terms: t('triplet', 'sixteenth'), targets: [tgt(null, tripBeats)] });
  } else if (tripBeats.length === beats) {
    out.push({ kind: 'triplets', sectionId: sec.id, title: 'A triplet feel throughout', body: 'Every beat here divides into three — a 12/8-style rolling feel rather than square sixteenths.', terms: t('triplet', 'timeSig'), targets: [] });
  }
  // Hemiola: onsets every 3 sixteenths across the grid
  for (const g of groups) {
    let flat = [], flatBeatOf = [], ok = true;
    for (let b = 0; b < beats; b++) {
      const c = byGroup[g.id][b];
      if (c.sc !== 4) { ok = flat.length >= 8 ? ok : false; if (flat.length < 8) { flat = []; flatBeatOf = []; } if (!ok) break; else break; }
      c.m.forEach((v, s) => { flat.push(v ? 1 : 0); flatBeatOf.push(b); });
    }
    if (flat.length >= 8) {
      const onsets = []; flat.forEach((v, i) => { if (v) onsets.push(i); });
      let runLen = 1, best = 1, endIdx = -1;
      for (let i = 1; i < onsets.length; i++) {
        if (onsets[i] - onsets[i - 1] === 3) { runLen++; if (runLen > best) { best = runLen; endIdx = i; } } else runLen = 1;
      }
      if (best >= 4) {
        const involved = onsets.slice(endIdx - best + 1, endIdx + 1).map(i => flatBeatOf[i]);
        out.push({ kind: 'hemiola-' + g.id, sectionId: sec.id, title: 'Three against four', body: 'The ' + gname(g.id).toLowerCase() + ' places notes every three sixteenths, cutting across the four-per-beat grid. This cross-rhythm (a hemiola) feels like it is tumbling out of sync until it lands back on a downbeat.', terms: t('hemiola', 'polyrhythm'), targets: [tgt(g.id, involved)] });
        break;
      }
    }
  }
  // Unison ensemble hits
  {
    const uniBeats = new Set();
    for (let b = 0; b < beats; b++) {
      const sc = subs[b] || 4;
      for (let s = 0; s < sc; s++) {
        let n = 0;
        for (const g of groups) if (byGroup[g.id][b].m[s]) n++;
        if (n >= 3) uniBeats.add(b);
      }
    }
    if (uniBeats.size >= 1 && uniBeats.size <= beats * 0.6) {
      out.push({ kind: 'unison', sectionId: sec.id, title: 'Ensemble impact points', body: 'At the highlighted moments most of the line hits together — unison shots that punctuate the phrase. Arrangers ration these; a hit everyone plays is only loud if it is rare.', terms: t('unison', 'dynamics'), targets: [tgt(null, [...uniBeats])] });
    }
  }
  // Call and response between two groups, measure to measure
  {
    const act = {};
    for (const g of groups) {
      act[g.id] = [];
      for (let m = 0; m < sec.measures; m++) {
        let n = 0;
        for (let b = m * 4; b < m * 4 + 4; b++) byGroup[g.id][b].m.forEach(v => { if (v) n++; });
        act[g.id].push(n);
      }
    }
    let found = null;
    for (const a of groups) {
      for (const bgrp of groups) {
        if (a.id === bgrp.id || found) continue;
        for (let m = 0; m + 1 < sec.measures; m++) {
          if (act[a.id][m] >= 3 && act[bgrp.id][m] <= 1 && act[bgrp.id][m + 1] >= 3 && act[a.id][m + 1] <= 1) { found = { a, b: bgrp, m }; break; }
        }
      }
    }
    if (found) {
      const mBeats = m0 => [m0 * 4, m0 * 4 + 1, m0 * 4 + 2, m0 * 4 + 3];
      out.push({ kind: 'callresp', sectionId: sec.id, title: 'Call and response', body: found.a.name + ' speaks in measure ' + (found.m + 1) + ' and the ' + found.b.name.toLowerCase() + ' answer in measure ' + (found.m + 2) + ' — a musical conversation borrowed from field hollers and gospel, and a staple of drumline writing.', terms: t('callResponse'), targets: [tgt(found.a.id, mBeats(found.m)), tgt(found.b.id, mBeats(found.m + 1))] });
    }
  }
  // Density
  const density = soundedPos / Math.max(1, totalPos);
  if (density > 0 && density < 0.1) {
    out.push({ kind: 'space', sectionId: sec.id, title: 'Space is an instrument', body: 'Most of this section is silence. Rests give the figures their shape — what you leave out reads as clearly as what you play.', terms: t('rest', 'groove'), targets: [] });
  } else if (density > 0.55) {
    out.push({ kind: 'dense', sectionId: sec.id, title: 'A wall of sound', body: 'Nearly every subdivision is filled. Try carving out rests or leaning on accents so the important notes poke through the texture.', terms: t('dynamics', 'rest'), targets: [] });
  }
  return out;
}

export function analyzeProject(project, opts) {
  const { sections, beatSubs, groupSubs, notes, live, tempo, swing } = project;
  const { scope, activeSectionId, groups, rows } = opts;
  const secList = scope === 'cadence' ? sections : sections.filter(s => s.id === activeSectionId);
  const out = [];
  // Global basics card
  const totalMeasures = secList.reduce((n, s) => n + s.measures, 0);
  out.push({
    kind: 'basics', sectionId: null,
    title: 'The canvas: 4/4 time',
    body: (scope === 'cadence' ? sections.length + ' sections, ' + totalMeasures + ' measures total' : '"' + (secList[0] ? secList[0].name : '') + '" is ' + totalMeasures + ' measures') + ' in 4/4 — four beats per measure at ' + tempo + ' BPM. The ruler splits each beat into sixteenths, triplets, or eighths; every column of the grid is one of those slices.',
    terms: t('timeSig', 'measure', 'tempo'), targets: [],
  });
  if (swing > 0) {
    out.push({ kind: 'swing', sectionId: null, title: 'Swung, not straight', body: 'Swing is set to ' + swing + '%, so every other subdivision plays late. The notation stays even but the feel shuffles — the lilt you hear in jazz and hip-hop.', terms: t('swing', 'groove'), targets: [] });
  }
  for (const sec of secList) out.push(...analyzeSection({ ...sec, _tempo: tempo }, beatSubs[sec.id] || [], notes[sec.id] || {}, groups, rows, (groupSubs || {})[sec.id], (live || {})[sec.id]));
  // Cadence-wide dynamic arc
  if (scope === 'cadence' && sections.length >= 2) {
    const dens = sections.map(s => {
      const d = digest(s, beatSubs[s.id] || [], notes[s.id] || {}, groups, rows, (groupSubs || {})[s.id]);
      let sounded = 0, total = 0;
      for (const g of groups) d.byGroup[g.id].forEach(c => { total += c.sc; c.m.forEach(v => { if (v) sounded++; }); });
      return { s, v: total ? sounded / total : 0 };
    }).filter(x => x.v > 0);
    if (dens.length >= 2) {
      const max = dens.reduce((a, b) => (b.v > a.v ? b : a)), min = dens.reduce((a, b) => (b.v < a.v ? b : a));
      if (max.v / Math.max(0.01, min.v) > 1.8) {
        out.push({ kind: 'arc', sectionId: null, title: 'A dynamic arc across sections', body: '"' + min.s.name + '" breathes while "' + max.s.name + '" piles notes on. Building and releasing intensity from section to section is what makes a cadence feel like a journey instead of a loop.', terms: t('dynamics', 'groove'), targets: [] });
      }
    }
  }
  const cap = scope === 'cadence' ? 14 : 9;
  const capped = out.slice(0, cap);
  let ci = 0;
  for (const ins of capped) {
    ins.id = ins.kind + ':' + (ins.sectionId || 'all');
    ins.color = ins.targets && ins.targets.length ? PALETTE[ci++ % PALETTE.length] : NEUTRAL;
  }
  return capped;
}

// ---------------------------------------------------------------------------
// Portable context envelope
//
// A self-describing description of the cadence that any assistant can consume —
// MCP's spirit (a well-specified context contract) without requiring a server.
// Deliberately human-readable: the user previews this exact text before it is
// sent anywhere, so it has to be auditable by a person, not just a model.
// ---------------------------------------------------------------------------

export const LEVELS = [
  { id: 'new', label: 'New to this' },
  { id: 'playing', label: 'I play' },
  { id: 'deep', label: 'Go deeper' },
];

const SUB_NAME = { 4: '16th notes', 3: 'triplets', 2: '8th notes' };

// "16th notes" or "16th notes; triplets on beats 2, 6" — voices can now carry
// their own subdivision per beat, so an even character count per beat is not
// something the reader can assume.
function describeSubs(scPerBeat) {
  const uniq = [...new Set(scPerBeat)];
  if (uniq.length === 1) return SUB_NAME[uniq[0]] || 'mixed';
  const counts = uniq.map(u => ({ u, n: scPerBeat.filter(x => x === u).length })).sort((a, b) => b.n - a.n);
  const parts = [SUB_NAME[counts[0].u] || 'mixed'];
  for (const { u } of counts.slice(1)) {
    const bs = scPerBeat.map((c, i) => (c === u ? i + 1 : 0)).filter(Boolean);
    parts.push((SUB_NAME[u] || 'mixed') + ' on beat' + (bs.length > 1 ? 's' : '') + ' ' + bs.join(', '));
  }
  return parts.join('; ');
}

// Aggregate timing of a live play-along take, if one exists for this section.
function takeSummary(sec, liveForSec, byGroup, rows, tempo) {
  if (!liveForSec) return null;
  const beats = sec.measures * 4;
  const beatMs = 60000 / (tempo || 120);
  let free = 0, snapped = 0, sumMs = 0, worst = 0;
  const perBeat = {};
  for (const r of rows) {
    const larr = liveForSec[r.id] || [];
    for (let b = 0; b < beats; b++) {
      const cell = larr[b] || [];
      const sc = byGroup[r.groupId] ? byGroup[r.groupId][b].sc : 4;
      for (let s = 0; s < cell.length; s++) {
        const m = cell[s] || 0;
        if (m === 1) { snapped++; continue; }
        if (m < 2) continue;
        const off = m - 2;
        const dev = (off <= 0.5 ? off : off - 1) * (beatMs / sc);
        free++; sumMs += dev;
        if (Math.abs(dev) > Math.abs(worst)) worst = dev;
        (perBeat[b] = perBeat[b] || []).push(dev);
      }
    }
  }
  if (!free && !snapped) return null;
  const avg = free ? sumMs / free : 0;
  // Beats where the player was most consistently off — useful coaching signal.
  const drift = Object.entries(perBeat)
    .map(([b, devs]) => ({ beat: Number(b) + 1, avg: devs.reduce((x, y) => x + y, 0) / devs.length }))
    .filter(d => Math.abs(d.avg) > 15)
    .sort((a, b) => Math.abs(b.avg) - Math.abs(a.avg))
    .slice(0, 3);
  return { free, snapped, avgMs: Math.round(avg), worstMs: Math.round(worst), drift };
}

export function buildCadenceContext(project, opts) {
  const { sections, beatSubs, groupSubs, notes, live, tempo, swing } = project;
  const { scope, activeSectionId, groups, rows } = opts;
  const secList = scope === 'cadence' ? sections : sections.filter(s => s.id === activeSectionId);

  const outSections = secList.map(sec => {
    const { beats, byGroup } = digest(sec, beatSubs[sec.id] || [], notes[sec.id] || {}, groups, rows, (groupSubs || {})[sec.id]);
    const voices = [];
    for (const g of groups) {
      let any = false;
      const parts = [];
      const scPerBeat = [];
      for (let b = 0; b < beats; b++) {
        const c = byGroup[g.id][b];
        scPerBeat.push(c.sc);
        let cell = '';
        c.m.forEach(v => {
          if (!v) { cell += '.'; return; }
          any = true;
          cell += (v & 2) ? '>' : (v & 4) ? 'f' : (v & 8) ? 'd' : (v & 16) ? 'z' : 'x';
        });
        if (c.sc === 3) cell = '[' + cell + ']';
        else if (c.sc === 2) cell = '(' + cell + ')';
        parts.push(cell);
        if (b % 4 === 3 && b < beats - 1) parts.push('|');
      }
      if (any) voices.push({ name: g.name, line: parts.join(' '), subs: describeSubs(scPerBeat) });
    }
    return {
      name: sec.name,
      measures: sec.measures,
      voices,
      take: takeSummary(sec, (live || {})[sec.id], byGroup, rows, tempo),
    };
  });

  return {
    app: 'dut dut',
    tempo, swing, timeSig: '4/4',
    scope: scope === 'cadence' ? 'cadence' : 'section',
    sections: outSections,
    findings: analyzeProject(project, opts).filter(i => i.kind !== 'basics').map(i => i.title),
  };
}

const LEVEL_ASK = {
  new: `I'm new to music theory — assume I can hear rhythm but can't read notation.

In 4-6 plain sentences, help me understand what I've written: what gives it its feel, one comparison to music I'd likely have heard, one thing that's already working, and one concrete change to try next. Define at most two terms in passing, in plain words. No jargon I'd have to look up, no markdown, no lists, no headings.`,

  playing: `I play and can read basic drum notation — skip the fundamentals.

In 5-8 sentences: what makes this pattern work rhythmically; a suggested sticking (which hand plays what, R/L) for the busiest voice; whether this is realistically playable at the tempo above and where the hard spot is; and one arranging change that would improve it. Be specific about beat numbers. No markdown, no lists.`,

  deep: `I know the fundamentals — go deep.

Cover the metric structure and where the phrase resolves, any stylistic lineage this evokes (corps, street, HBCU idiom) and why, and a critique of the arranging: voice balance across the line, tension and release, and whether each part is idiomatic for its instrument. Flag anything unidiomatic or physically awkward. Prose, no markdown, no lists.`,
};

export function renderContextMarkdown(ctx, { level = 'new' } = {}) {
  const L = [];
  L.push('# Drumline cadence — context for explanation');
  L.push('');
  L.push(`I sketched this drum pattern in **dut dut**, a step sequencer for drumline cadences, and I'd like help understanding it musically. Everything you need is below.`);
  L.push('');

  L.push('## How to read the notation');
  L.push('');
  L.push('Each line is one voice of the drumline. Characters are consecutive slices of a beat, `|` separates measures, and beats are space-separated:');
  L.push('');
  L.push('- `.` rest · `x` hit · `>` accented hit · `f` flam (grace note before the stroke) · `d` diddle (two strokes in one slot) · `z` buzz roll');
  L.push('- A beat with no brackets is **four 16th notes**. `[...]` marks a **triplet** beat, `(..)` marks a beat of **two 8th notes**.');
  L.push('- Voices can use *different* subdivisions on the same beat, so lines will not always have equal character counts. Each voice notes its own subdivisions.');
  L.push('');

  L.push('## The pattern');
  L.push('');
  L.push(`Tempo **${ctx.tempo} BPM** · ${ctx.timeSig}${ctx.swing ? ` · swing ${ctx.swing}%` : ''}`);
  L.push('');

  for (const sec of ctx.sections) {
    L.push(`### "${sec.name}" — ${sec.measures} measure${sec.measures === 1 ? '' : 's'}`);
    L.push('');
    if (!sec.voices.length) {
      L.push('_(nothing written in this section yet)_');
      L.push('');
      continue;
    }
    L.push('```');
    const pad = Math.max(...sec.voices.map(v => v.name.length));
    for (const v of sec.voices) L.push(`${v.name.padEnd(pad)} : ${v.line}`);
    L.push('```');
    L.push('');
    for (const v of sec.voices) L.push(`- **${v.name}** — ${v.subs}`);
    L.push('');
    if (sec.take) {
      const t2 = sec.take;
      L.push(`**My live take:** I played ${t2.free + t2.snapped} of these notes in by hand` +
        (t2.snapped ? ` (${t2.snapped} snapped to the grid, ${t2.free} kept at free timing)` : '') + '.');
      if (t2.free) {
        L.push(`Average timing was ${t2.avgMs >= 0 ? '+' : ''}${t2.avgMs} ms against the grid (positive = behind the beat), loosest note ${t2.worstMs >= 0 ? '+' : ''}${t2.worstMs} ms.`);
        if (t2.drift.length) {
          L.push('Consistently off on: ' + t2.drift.map(d => `beat ${d.beat} (${d.avg >= 0 ? '+' : ''}${Math.round(d.avg)} ms)`).join(', ') + '.');
        }
        L.push('Please comment on my timing too.');
      }
      L.push('');
    }
  }

  L.push(`## What the app's built-in analyzer already spotted`);
  L.push('');
  if (ctx.findings.length) {
    for (const f of ctx.findings) L.push(`- ${f}`);
    L.push('');
    L.push('_Please go past these rather than restating them._');
  } else {
    L.push('_Nothing notable detected — the pattern may be sparse or unusual._');
  }
  L.push('');

  L.push('## What I would like');
  L.push('');
  L.push(LEVEL_ASK[level] || LEVEL_ASK.new);

  return L.join('\n');
}

// Back-compat wrapper for the in-artifact `window.claude.complete` path.
export function buildLLMPrompt(project, opts) {
  return renderContextMarkdown(buildCadenceContext(project, opts), { level: (opts && opts.level) || 'new' });
}
