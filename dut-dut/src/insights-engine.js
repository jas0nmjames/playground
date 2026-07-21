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

function digest(sec, subs, notesForSec, groups, rows) {
  const beats = sec.measures * 4;
  const byGroup = {};
  for (const g of groups) byGroup[g.id] = Array.from({ length: beats }, (_, b) => ({ sc: subs[b] || 4, m: new Array(subs[b] || 4).fill(0) }));
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

function analyzeSection(sec, subs, notesForSec, groups, rows) {
  const { beats, byGroup } = digest(sec, subs, notesForSec, groups, rows);
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
  // Triplet vs straight subdivisions
  const tripBeats = [], eighthBeats = [];
  for (let b = 0; b < beats; b++) { if ((subs[b] || 4) === 3) tripBeats.push(b); else if ((subs[b] || 4) === 2) eighthBeats.push(b); }
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
  const { sections, beatSubs, notes, tempo, swing } = project;
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
  for (const sec of secList) out.push(...analyzeSection(sec, beatSubs[sec.id] || [], notes[sec.id] || {}, groups, rows));
  // Cadence-wide dynamic arc
  if (scope === 'cadence' && sections.length >= 2) {
    const dens = sections.map(s => {
      const d = digest(s, beatSubs[s.id] || [], notes[s.id] || {}, groups, rows);
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

// Compact text description + teaching prompt for an LLM.
export function buildLLMPrompt(project, opts) {
  const { sections, beatSubs, notes, tempo, swing } = project;
  const { scope, activeSectionId, groups, rows } = opts;
  const secList = scope === 'cadence' ? sections : sections.filter(s => s.id === activeSectionId);
  const lines = ['Tempo ' + tempo + ' BPM, 4/4 time' + (swing ? ', swing ' + swing + '%' : '') + '.'];
  for (const sec of secList) {
    const { beats, byGroup } = digest(sec, beatSubs[sec.id] || [], notes[sec.id] || {}, groups, rows);
    lines.push('Section "' + sec.name + '" (' + sec.measures + ' measures):');
    for (const g of groups) {
      let any = false;
      const parts = [];
      for (let b = 0; b < beats; b++) {
        const c = byGroup[g.id][b];
        let cell = '';
        c.m.forEach(v => {
          if (!v) { cell += '.'; return; }
          any = true;
          cell += (v & 2) ? '>' : (v & 4) ? 'f' : (v & 8) ? 'd' : (v & 16) ? 'z' : 'x';
        });
        if (c.sc === 3) cell = '[' + cell + ']';
        parts.push(cell);
        if (b % 4 === 3 && b < beats - 1) parts.push('|');
      }
      if (any) lines.push('  ' + g.name + ': ' + parts.join(' '));
    }
  }
  const findings = analyzeProject(project, opts).filter(i => i.kind !== 'basics').map(i => i.title);
  return 'You are a friendly percussion educator helping a beginner understand a drumline pattern they just sketched in a step sequencer. Symbols per subdivision: . rest, x hit, > accented hit, f flam, d diddle (two strokes), z buzz roll. [..] means that beat is a triplet. | separates measures.\n\n' +
    lines.join('\n') + '\n\nAlready-detected features: ' + (findings.length ? findings.join('; ') : 'none') + '.\n\n' +
    'In 3-5 short, plain sentences: explain what makes this pattern tick musically (go beyond the detected list where you can), define at most one term in passing, and end with one concrete thing to try next. Warm and encouraging, no markdown, no lists, no headings.';
}
