/**
 * TI-83+ keypad layout.
 *
 * Grid positions match the real hardware: five columns, ten rows, with the
 * arrow cluster occupying columns 4-5 of rows 2-3. The ALPHA letters run
 * A-Z across the keyboard in the physical order Texas Instruments used.
 */

/** getKey codes, as reported by the real calculator. */
export const KEYCODES = {
  up: 25, left: 24, right: 26, down: 34,
  enter: 105, clear: 45,
  '0': 102, '1': 92, '2': 93, '3': 94, '4': 82,
  '5': 83, '6': 84, '7': 72, '8': 73, '9': 74,
};

/**
 * key fields:
 *   id            stable identifier used by the dispatcher
 *   main          printed label on the key face
 *   second/alpha  labels printed above the key
 *   ins           text inserted into the entry line (undefined = command key)
 *   ins2          text inserted when 2nd is active
 *   r, c          1-based grid position
 *   variant       styling hook
 */
export const KEYS = [
  // Row 1 — screen-context keys
  { id: 'Y=',      main: 'Y=',     second: 'STAT PLOT', r: 1, c: 1, variant: 'top' },
  { id: 'WINDOW',  main: 'WINDOW', second: 'TBLSET',    r: 1, c: 2, variant: 'top' },
  { id: 'ZOOM',    main: 'ZOOM',   second: 'FORMAT',    r: 1, c: 3, variant: 'top' },
  { id: 'TRACE',   main: 'TRACE',  second: 'CALC',      r: 1, c: 4, variant: 'top' },
  { id: 'GRAPH',   main: 'GRAPH',  second: 'TABLE',     r: 1, c: 5, variant: 'top' },

  // Row 2
  { id: '2ND',   main: '2nd',  r: 2, c: 1, variant: 'second' },
  { id: 'MODE',  main: 'MODE', second: 'QUIT', r: 2, c: 2 },
  { id: 'DEL',   main: 'DEL',  second: 'INS',  r: 2, c: 3 },

  // Row 3
  { id: 'ALPHA', main: 'ALPHA', second: 'A-LOCK', r: 3, c: 1, variant: 'alpha' },
  { id: 'XTON',  main: 'X,T,θ,n', second: 'LINK', ins: 'X', r: 3, c: 2 },
  { id: 'STAT',  main: 'STAT', second: 'LIST', r: 3, c: 3 },

  // Row 4
  { id: 'MATH',  main: 'MATH', second: 'TEST',  alpha: 'A', r: 4, c: 1 },
  { id: 'APPS',  main: 'APPS', second: 'ANGLE', alpha: 'B', r: 4, c: 2 },
  { id: 'PRGM',  main: 'PRGM', second: 'DRAW',  alpha: 'C', r: 4, c: 3 },
  { id: 'VARS',  main: 'VARS', second: 'DISTR',             r: 4, c: 4 },
  { id: 'CLEAR', main: 'CLEAR',                             r: 4, c: 5 },

  // Row 5
  { id: 'INV',  main: 'x⁻¹', second: 'MATRIX', alpha: 'D', ins: '⁻¹',   r: 5, c: 1 },
  { id: 'SIN',  main: 'SIN', second: 'SIN⁻¹',  alpha: 'E', ins: 'sin(', ins2: 'sin⁻¹(', r: 5, c: 2 },
  { id: 'COS',  main: 'COS', second: 'COS⁻¹',  alpha: 'F', ins: 'cos(', ins2: 'cos⁻¹(', r: 5, c: 3 },
  { id: 'TAN',  main: 'TAN', second: 'TAN⁻¹',  alpha: 'G', ins: 'tan(', ins2: 'tan⁻¹(', r: 5, c: 4 },
  { id: 'POW',  main: '^',   second: 'π',      alpha: 'H', ins: '^',    ins2: 'π',      r: 5, c: 5 },

  // Row 6
  { id: 'SQR',    main: 'x²', second: '√',  alpha: 'I', ins: '²', ins2: '√(', r: 6, c: 1 },
  { id: 'COMMA',  main: ',',  second: 'EE', alpha: 'J', ins: ',',              r: 6, c: 2 },
  { id: 'LPAREN', main: '(',  second: '{',  alpha: 'K', ins: '(',              r: 6, c: 3 },
  { id: 'RPAREN', main: ')',  second: '}',  alpha: 'L', ins: ')',              r: 6, c: 4 },
  { id: 'DIV',    main: '÷',  second: 'e',  alpha: 'M', ins: '/', ins2: 'e',   r: 6, c: 5 },

  // Row 7
  { id: 'LOG', main: 'LOG', second: '10ˣ', alpha: 'N', ins: 'log(', ins2: '10^(', r: 7, c: 1 },
  { id: '7',   main: '7',   second: 'u',   alpha: 'O', ins: '7',  r: 7, c: 2, variant: 'num' },
  { id: '8',   main: '8',   second: 'v',   alpha: 'P', ins: '8',  r: 7, c: 3, variant: 'num' },
  { id: '9',   main: '9',   second: 'w',   alpha: 'Q', ins: '9',  r: 7, c: 4, variant: 'num' },
  { id: 'MUL', main: '×',   second: '[',   alpha: 'R', ins: '*',  r: 7, c: 5 },

  // Row 8
  { id: 'LN',  main: 'LN', second: 'eˣ', alpha: 'S', ins: 'ln(', ins2: 'e^(', r: 8, c: 1 },
  { id: '4',   main: '4',  second: 'L4', alpha: 'T', ins: '4', r: 8, c: 2, variant: 'num' },
  { id: '5',   main: '5',  second: 'L5', alpha: 'U', ins: '5', r: 8, c: 3, variant: 'num' },
  { id: '6',   main: '6',  second: 'L6', alpha: 'V', ins: '6', r: 8, c: 4, variant: 'num' },
  { id: 'SUB', main: '−',  second: ']',  alpha: 'W', ins: '-', r: 8, c: 5 },

  // Row 9
  { id: 'STO', main: 'STO▸', second: 'RCL', alpha: 'X', ins: '→', r: 9, c: 1 },
  { id: '1',   main: '1',    second: 'L1',  alpha: 'Y', ins: '1', r: 9, c: 2, variant: 'num' },
  { id: '2',   main: '2',    second: 'L2',  alpha: 'Z', ins: '2', r: 9, c: 3, variant: 'num' },
  { id: '3',   main: '3',    second: 'L3',  alpha: 'θ', ins: '3', r: 9, c: 4, variant: 'num' },
  { id: 'ADD', main: '+',    second: 'MEM', alpha: '"', ins: '+', r: 9, c: 5 },

  // Row 10
  { id: 'ON',    main: 'ON',    second: 'OFF',     r: 10, c: 1, variant: 'on' },
  { id: '0',     main: '0',     second: 'CATALOG', alpha: ' ', ins: '0', r: 10, c: 2, variant: 'num' },
  { id: 'DOT',   main: '.',     second: 'i',       alpha: ':', ins: '.', r: 10, c: 3, variant: 'num' },
  { id: 'NEG',   main: '(−)',   second: 'ANS',     alpha: '?', ins: '-', ins2: 'Ans', r: 10, c: 4, variant: 'num' },
  { id: 'ENTER', main: 'ENTER', second: 'ENTRY',   r: 10, c: 5, variant: 'enter' },
];

export const KEY_BY_ID = Object.fromEntries(KEYS.map((k) => [k.id, k]));

/** Physical-keyboard shortcuts, so the emulator is usable without a mouse. */
export function mapPhysicalKey(event) {
  const { key } = event;
  if (/^[0-9]$/.test(key)) return key;
  switch (key) {
    case '+': return 'ADD';
    case '-': return 'SUB';
    case '*': return 'MUL';
    case '/': return 'DIV';
    case '^': return 'POW';
    case '(': return 'LPAREN';
    case ')': return 'RPAREN';
    case ',': return 'COMMA';
    case '.': return 'DOT';
    case 'Enter': return 'ENTER';
    case 'Backspace': return 'DEL';
    case 'Delete': return 'DEL';
    case 'Escape': return 'CLEAR';
    case 'ArrowUp': return 'UP';
    case 'ArrowDown': return 'DOWN';
    case 'ArrowLeft': return 'LEFT';
    case 'ArrowRight': return 'RIGHT';
    default: return null;
  }
}
