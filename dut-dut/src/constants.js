export const GROUPS_META = [
  { id: 'cymbal', name: 'Cymbal', color: 'oklch(58% 0.15 85)', single: true, rowDefs: [{ id: 'cymbal', label: 'Cymbal' }] },
  { id: 'snare', name: 'Snare', color: 'oklch(55% 0.15 205)', single: true, rowDefs: [{ id: 'snare', label: 'Snare' }] },
  { id: 'tenor', name: 'Tenors', color: 'oklch(55% 0.15 300)', single: false, rowDefs: [1, 2, 3, 4, 5, 6].map(n => ({ id: 'tenor' + n, label: 'T' + n })) },
  { id: 'bass', name: 'Basses', color: 'oklch(50% 0.15 150)', single: false, rowDefs: [1, 2, 3, 4, 5].map(n => ({ id: 'bass' + n, label: 'B' + n })) },
];
export const ALL_ROWS = GROUPS_META.flatMap(g => g.rowDefs.map(r => ({ ...r, groupId: g.id, color: g.color })));

// Vertical staff position (px) for each row within its group's staff SVG.
export const LANE_Y = {
  cymbal: [56], snare: [56],
  tenor: [36, 44, 52, 60, 68, 76],
  bass: [52, 60, 68, 76, 84],
};

// note values: 0 empty, 1 hit, 2 accent, 3 flam, 4 diddle, 5 roll(buzz)
export const TOOLS = [
  { id: 'hit', v: 1, label: 'Hit' },
  { id: 'accent', v: 2, label: 'Accent ›' },
  { id: 'flam', v: 3, label: 'Flam' },
  { id: 'diddle', v: 4, label: 'Diddle' },
  { id: 'roll', v: 5, label: 'Roll z' },
  { id: 'erase', v: 0, label: 'Erase' },
];

export const STORAGE_KEY = 'dut-dut-project-v2';

export const COLORS = {
  text: 'oklch(20% 0.015 260)',
  mutedText: 'oklch(46% 0.02 260)',
  onAccent: 'oklch(99% 0.002 90)',
  accent: 'oklch(58% 0.16 235)',
  ink: 'oklch(24% 0.015 260)',
  border: 'oklch(85% 0.012 80)',
};

export function defaultSections() {
  return [
    { id: 'intro', name: 'Intro', measures: 2 },
    { id: 'verse', name: 'Verse', measures: 4 },
    { id: 'break', name: 'Break', measures: 4 },
  ];
}

export function beatCount(section) { return section.measures * 4; }

export function makeSectionNotes(section) {
  const n = {};
  for (const row of ALL_ROWS) n[row.id] = Array.from({ length: beatCount(section) }, () => new Array(4).fill(0));
  return n;
}

export function makeBeatSubs(section) { return new Array(beatCount(section)).fill(4); }

export function resizeBeatArray(arr, count, makeItem) {
  const out = arr.slice(0, count);
  while (out.length < count) out.push(makeItem(out.length));
  return out;
}

// Validates/repairs a loaded project (file or localStorage) into a safe shape.
export function normalizeProject(p) {
  if (!p || !Array.isArray(p.sections) || !p.sections.length) throw new Error('bad project');
  const sections = p.sections.map((s, i) => ({
    id: String(s.id || 'section' + i),
    name: String(s.name || 'Section ' + (i + 1)),
    measures: Math.max(1, Math.min(16, Math.round(Number(s.measures) || 4))),
  }));
  const beatSubs = {}, notes = {};
  for (const s of sections) {
    const count = s.measures * 4;
    const rawSubs = (p.beatSubs && p.beatSubs[s.id]) || [];
    const subs = [];
    for (let i = 0; i < count; i++) subs.push([2, 3, 4].includes(rawSubs[i]) ? rawSubs[i] : 4);
    beatSubs[s.id] = subs;
    const rows = {};
    for (const row of ALL_ROWS) {
      const rawBeats = (p.notes && p.notes[s.id] && p.notes[s.id][row.id]) || [];
      const beatsArr = [];
      for (let b = 0; b < count; b++) {
        const raw = Array.isArray(rawBeats[b]) ? rawBeats[b] : [];
        const na = new Array(subs[b]).fill(0);
        for (let i = 0; i < Math.min(na.length, raw.length); i++) {
          const v = Math.round(Number(raw[i]) || 0);
          na[i] = v >= 0 && v <= 5 ? v : 0;
        }
        beatsArr.push(na);
      }
      rows[row.id] = beatsArr;
    }
    notes[s.id] = rows;
  }
  const activeSectionId = sections.some(s => s.id === p.activeSectionId) ? p.activeSectionId : sections[0].id;
  return {
    sections, beatSubs, notes, activeSectionId,
    tempo: Math.max(40, Math.min(240, Math.round(Number(p.tempo) || 120))),
    swing: Math.max(0, Math.min(100, Math.round(Number(p.swing) || 0))),
  };
}
