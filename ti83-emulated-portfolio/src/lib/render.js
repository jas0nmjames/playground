/**
 * Builds the 8x16 character rows for whichever screen is active.
 *
 * Every mode reduces to the same output shape — eight rows plus an optional
 * cursor — so the Display component never needs to know what mode it is in.
 */

import { ROWS, COLS } from './screen.js';
import { formatNumber } from './format.js';

const BLANK = ' '.repeat(COLS);

function row(text = '', inverse = false) {
  return { text: (text + BLANK).slice(0, COLS), inverse };
}

function emptyRows() {
  return Array.from({ length: ROWS }, () => row());
}

/** Split text into display-width chunks, always yielding at least one. */
function chunks(text) {
  if (!text) return [''];
  const out = [];
  for (let i = 0; i < text.length; i += COLS) out.push(text.slice(i, i + COLS));
  return out;
}

/**
 * Show a text field that may be longer than the space available, keeping the
 * cursor in view by scrolling the window rightward.
 */
function fieldView(text, cursor, width) {
  if (text.length <= width) return { view: text, offset: 0 };
  const offset = Math.max(0, Math.min(text.length - width, cursor - width + 1));
  return { view: text.slice(offset, offset + width), offset };
}

function buildHome(state) {
  const { screen, entry, cursor } = state;

  // Defensively scroll if the cursor row ran past the bottom.
  let grid = screen.grid;
  let start = screen.row;
  if (start >= ROWS) {
    const shift = start - (ROWS - 1);
    grid = [...grid.slice(shift), ...Array.from({ length: shift }, () => BLANK)];
    start = ROWS - 1;
  }

  const rows = grid.map((g) => row(g));
  const parts = chunks(entry);

  parts.forEach((part, i) => {
    if (start + i < ROWS) rows[start + i] = row(part);
  });

  const cr = start + Math.floor(cursor / COLS);
  const cc = cursor % COLS;
  return { rows, cursor: cr < ROWS ? { r: cr, c: cc } : null };
}

function buildRun(state) {
  const { screen, waiting, entry, cursor } = state;
  const rows = screen.grid.map((g) => row(g));

  if (waiting?.kind === 'input') {
    const line = waiting.prompt + entry;
    const r = Math.min(screen.row, ROWS - 1);
    rows[r] = row(line);
    return { rows, cursor: { r, c: Math.min(COLS - 1, waiting.prompt.length + cursor) } };
  }

  return { rows, cursor: null };
}

function buildMenu(state) {
  const { waiting } = state;
  const rows = emptyRows();
  rows[0] = row(waiting.title, true);

  waiting.items.forEach((item, i) => {
    if (i + 1 >= ROWS) return;
    rows[i + 1] = row(`${i + 1}:${item.label}`, i === waiting.index);
  });

  return { rows, cursor: null };
}

function buildYEq(state) {
  const { yvars, ySel, yScroll, entry, cursor } = state;
  const rows = emptyRows();
  rows[0] = row('Plot1 Plot2 Plt3');

  let cursorPos = null;
  const visible = ROWS - 1;

  for (let i = 0; i < visible; i++) {
    const n = yScroll + i + 1;
    if (n > 9) break;
    const selected = n === ySel;
    const label = `\\Y${n}=`;
    const width = COLS - label.length;
    const text = selected ? entry : yvars[n] || '';
    // Only the row being edited scrolls; the rest show from the start.
    const { view, offset } = fieldView(text, selected ? cursor : 0, width);
    rows[i + 1] = row(label + view);
    if (selected) cursorPos = { r: i + 1, c: label.length + (cursor - offset) };
  }

  return { rows, cursor: cursorPos };
}

export const WINDOW_FIELDS = ['xmin', 'xmax', 'xscl', 'ymin', 'ymax', 'yscl', 'xres'];
const WINDOW_LABELS = {
  xmin: 'Xmin', xmax: 'Xmax', xscl: 'Xscl',
  ymin: 'Ymin', ymax: 'Ymax', yscl: 'Yscl', xres: 'Xres',
};

function buildWindow(state) {
  const { win, winSel, entry, cursor } = state;
  const rows = emptyRows();
  rows[0] = row('WINDOW');

  let cursorPos = null;

  WINDOW_FIELDS.forEach((field, i) => {
    const selected = i === winSel;
    const label = `${WINDOW_LABELS[field]}=`;
    const width = COLS - label.length;
    const text = selected ? entry : formatNumber(win[field] ?? 1);
    const { view, offset } = fieldView(text, selected ? cursor : 0, width);
    rows[i + 1] = row(label + view);
    if (selected) cursorPos = { r: i + 1, c: label.length + (cursor - offset) };
  });

  return { rows, cursor: cursorPos };
}

const PRGM_TABS = ['EXEC', 'EDIT', 'NEW'];

function buildPrgm(state) {
  const { programs, prgmTab, prgmSel } = state;
  const rows = emptyRows();

  rows[0] = row(
    PRGM_TABS.map((t, i) => (i === prgmTab ? `[${t}]` : ` ${t} `)).join('').slice(0, COLS)
  );

  if (prgmTab === 2) {
    rows[1] = row('NEW PROGRAM');
    rows[2] = row('NOT AVAILABLE');
    rows[3] = row('IN THIS BUILD.');
    return { rows, cursor: null };
  }

  programs.forEach((p, i) => {
    if (i + 1 >= ROWS) return;
    rows[i + 1] = row(`${i + 1}:${p.name}`, i === prgmSel);
  });

  return { rows, cursor: null };
}

function buildPrgmEdit(state) {
  const { programs, prgmSel, editScroll } = state;
  const prog = programs[prgmSel];
  const rows = emptyRows();

  if (!prog) return { rows, cursor: null };

  // "PRGM:" rather than the hardware's "PROGRAM:" so a 9-character name
  // still fits the 16-column display.
  rows[0] = row(`PRGM:${prog.name}`, true);
  const lines = prog.source.split('\n');

  for (let i = 0; i < ROWS - 1; i++) {
    const line = lines[editScroll + i];
    if (line === undefined) break;
    rows[i + 1] = row(line);
  }

  return { rows, cursor: null };
}

export const ZOOM_ITEMS = [
  'ZStandard', 'ZSquare', 'ZTrig', 'ZDecimal', 'Zoom In', 'Zoom Out',
];

function buildZoom(state) {
  const rows = emptyRows();
  rows[0] = row('ZOOM', true);
  ZOOM_ITEMS.forEach((label, i) => {
    if (i + 1 < ROWS) rows[i + 1] = row(`${i + 1}:${label}`, i === state.zoomSel);
  });
  return { rows, cursor: null };
}

function buildMode(state) {
  const rows = emptyRows();
  rows[0] = row('MODE', true);
  rows[1] = row(state.angleDeg ? ' RADIAN [DEGREE]' : '[RADIAN] DEGREE ');
  rows[2] = row('FUNC  PAR  POL');
  rows[3] = row('CONNECTED  DOT');
  rows[4] = row('FLOAT 0123456789');
  rows[6] = row('ENTER TOGGLES');
  rows[7] = row('ANGLE MODE');
  return { rows, cursor: null };
}

function buildStub(title, body) {
  const rows = emptyRows();
  rows[0] = row(title, true);
  body.forEach((line, i) => {
    if (i + 2 < ROWS) rows[i + 2] = row(line);
  });
  return { rows, cursor: null };
}

const STUBS = {
  stat: ['STAT EDITOR', 'NOT IMPLEMENTED', 'IN THIS BUILD.', '', 'PRESS CLEAR'],
  matrix: ['MATRIX EDITOR', 'NOT IMPLEMENTED', 'IN THIS BUILD.', '', 'PRESS CLEAR'],
  math: ['1:▸Frac', '2:▸Dec', '3:³', '4:³√(', '', 'PRESS CLEAR'],
  vars: ['1:Window', '2:Y-VARS', '3:Statistics', '', 'PRESS CLEAR'],
  apps: ['NO APPS', 'INSTALLED.', '', 'PRESS CLEAR'],
};

const STUB_TITLES = {
  stat: 'STAT', matrix: 'MATRIX', math: 'MATH', vars: 'VARS', apps: 'APPLICATIONS',
};

/** Build the active screen. Returns {rows, cursor}. */
export function buildScreen(state) {
  switch (state.mode) {
    case 'home': return buildHome(state);
    case 'run': return buildRun(state);
    case 'menu': return buildMenu(state);
    case 'yeq': return buildYEq(state);
    case 'window': return buildWindow(state);
    case 'prgm': return buildPrgm(state);
    case 'prgmedit': return buildPrgmEdit(state);
    case 'zoom': return buildZoom(state);
    case 'mode': return buildMode(state);
    default:
      if (STUBS[state.mode]) return buildStub(STUB_TITLES[state.mode], STUBS[state.mode]);
      return { rows: emptyRows(), cursor: null };
  }
}
