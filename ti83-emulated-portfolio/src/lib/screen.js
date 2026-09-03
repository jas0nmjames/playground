/**
 * The home screen: a fixed 8-row by 16-column character grid.
 *
 * This is the real hardware model — the TI does not keep a scrollback buffer.
 * Writing past the last row shifts everything up by one and writes to row 7.
 */

export const ROWS = 8;
export const COLS = 16;

export function createScreen() {
  return {
    grid: Array.from({ length: ROWS }, () => ' '.repeat(COLS)),
    row: 0,
  };
}

export function cloneScreen(s) {
  return { grid: [...s.grid], row: s.row };
}

function pad(text) {
  return (text + ' '.repeat(COLS)).slice(0, COLS);
}

export function clearHome(s) {
  s.grid = Array.from({ length: ROWS }, () => ' '.repeat(COLS));
  s.row = 0;
}

function scroll(s) {
  s.grid = [...s.grid.slice(1), ' '.repeat(COLS)];
}

/** Write one line at the cursor row, scrolling if we've run off the bottom. */
export function writeLine(s, text) {
  if (s.row >= ROWS) {
    scroll(s);
    s.row = ROWS - 1;
  }
  s.grid[s.row] = pad(text);
  s.row++;
}

/**
 * Disp semantics: strings left-aligned, numbers right-aligned, each value
 * wrapping across as many rows as it needs.
 */
export function dispLine(s, text, alignRight = false) {
  const chunks = [];
  if (text.length === 0) {
    chunks.push('');
  } else {
    for (let i = 0; i < text.length; i += COLS) chunks.push(text.slice(i, i + COLS));
  }
  for (const chunk of chunks) {
    writeLine(s, alignRight ? ' '.repeat(Math.max(0, COLS - chunk.length)) + chunk : chunk);
  }
}

/** Output(row, col, text) — absolute placement, no scroll, no cursor move. */
export function outputAt(s, row, col, text) {
  const r = Math.max(1, Math.min(ROWS, Math.round(row))) - 1;
  const c = Math.max(1, Math.min(COLS, Math.round(col))) - 1;
  const line = s.grid[r].split('');
  for (let i = 0; i < text.length && c + i < COLS; i++) {
    line[c + i] = text[i];
  }
  s.grid[r] = line.join('');
}

/** Replace a whole row, used for live entry echo on the home screen. */
export function setRow(s, row, text) {
  if (row < 0 || row >= ROWS) return;
  s.grid[row] = pad(text);
}
