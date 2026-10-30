/* The page: draws the screen, builds the keypad, and runs the home screen. */
(function () {
  'use strict';
  const { Screen, Program, Runner, TIError, toText, ROWS, COLS } = window.TIBasic;

  const $ = (id) => document.getElementById(id);
  const cellsEl = $('cells'), busyEl = $('busy'), statusEl = $('status');
  const source = $('source'), srText = $('screen-text');
  const STORE_KEY = 'ti-basic:prgmHOME';

  /* ---------- Program source ---------- */

  try { source.value = localStorage.getItem(STORE_KEY) || window.PRGM_HOME; }
  catch (e) { source.value = window.PRGM_HOME; }
  source.addEventListener('input', () => {
    try { localStorage.setItem(STORE_KEY, source.value); } catch (e) { /* storage off */ }
  });
  $('reset').addEventListener('click', () => {
    source.value = window.PRGM_HOME;
    try { localStorage.removeItem(STORE_KEY); } catch (e) { /* storage off */ }
  });

  /* ---------- Screen ---------- */

  const scr = new Screen();
  const runner = new Runner(scr);
  const cells = [];
  for (let i = 0; i < ROWS * COLS; i++) {
    const s = document.createElement('span');
    cellsEl.appendChild(s);
    cells.push(s);
  }

  let alpha = false, frame = 0, srTimer = 0;
  function render() {
    frame = 0;
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const el = cells[r * COLS + c];
        const ch = scr.chars[r][c];
        if (el.textContent !== ch) el.textContent = ch;
        el.className = scr.inv[r][c] ? 'inv' : '';
      }
    }
    const cur = scr.cursor;
    if (cur) {
      const el = cells[cur.r * COLS + Math.min(cur.c, COLS - 1)];
      el.classList.add('cur');
      if (alpha) el.classList.add('alpha');
    }
    clearTimeout(srTimer);
    srTimer = setTimeout(() => {
      srText.textContent = scr.chars.map(row => row.join('').trimEnd()).filter(Boolean).join('. ');
    }, 400);
  }
  scr.onChange = () => { if (!frame) frame = requestAnimationFrame(render); };

  const STATUS = { running: 'Running', paused: 'Paused: press ENTER', waiting: 'Waiting for you' };
  runner.onMode = (m) => {
    busyEl.className = 'busy' + (m === 'running' ? ' run' : m === 'paused' ? ' pause' : '');
    if (STATUS[m]) setStatus(STATUS[m]);
  };
  function setStatus(t) { statusEl.textContent = t; }

  /* ---------- Home screen ---------- */

  let state = 'idle'; // idle | running | error
  let entry = '', entryRow = 0, lastEntry = 'prgmHOME';
  let current = null, quietBreak = false, err = null;

  function beginEntry(text) {
    entry = text;
    entryRow = scr.nextLine();
    drawEntry();
    setStatus('Ready');
  }
  function drawEntry() {
    scr.clearRow(entryRow);
    const shown = [...entry].slice(-(COLS - 1)).join('');
    scr.write(entryRow, 0, shown);
    scr.cursor = { r: entryRow, c: [...shown].length };
    scr.changed();
  }

  function execute(text) {
    lastEntry = text;
    scr.cursor = null;
    state = 'running';
    const t = text.trim();
    const isPrgm = t.startsWith('prgm');
    err = { prog: null, isPrgm };
    current = (async () => {
      try {
        if (isPrgm && t !== 'prgmHOME') throw new TIError('UNDEFINED');
        const prog = new Program(isPrgm ? source.value : t);
        err.prog = prog;
        const last = await runner.run(prog);
        if (isPrgm) scr.line('Done', true);
        else if (last && (last.k === 'expr' || last.k === 'store')) {
          scr.line(toText(runner.ans), typeof runner.ans === 'number');
        }
        state = 'idle';
        beginEntry('');
      } catch (e) {
        if (quietBreak) { quietBreak = false; state = 'idle'; scr.clear(); beginEntry(''); return; }
        showError(e instanceof TIError ? e : new TIError('SYNTAX'), isPrgm);
      }
    })();
    return current;
  }

  function showError(e, isPrgm) {
    state = 'error';
    err = Object.assign(err || {}, { kind: e.kind, stmt: e.stmt, isPrgm, sel: 0 });
    err.options = isPrgm && e.stmt !== undefined ? ['Quit', 'Goto'] : ['Quit'];
    setStatus('ERR:' + e.kind);
    drawError();
  }
  function drawError() {
    scr.clear();
    scr.cursor = null;
    for (let c = 0; c < COLS; c++) scr.put(0, c, ' ', true);
    scr.write(0, 0, ('ERR:' + err.kind).slice(0, COLS), true);
    err.options.forEach((o, i) => {
      scr.write(i + 1, 0, (i + 1) + ':', i === err.sel);
      scr.write(i + 1, 2, o);
    });
  }
  function quitError(gotoLine) {
    state = 'idle';
    scr.clear();
    beginEntry('');
    if (gotoLine && err.prog) {
      const st = err.prog.stmts[err.stmt];
      if (st) selectLine(st.line);
    }
  }
  function selectLine(n) {
    const lines = source.value.split('\n');
    let start = 0;
    for (let i = 0; i < n; i++) start += lines[i].length + 1;
    source.focus();
    source.setSelectionRange(start, start + (lines[n] || '').length);
    const lh = parseFloat(getComputedStyle(source).lineHeight) || 20;
    source.scrollTop = Math.max(0, n * lh - source.clientHeight / 2);
  }

  async function runFromEditor() {
    if (state === 'running') { quietBreak = true; runner.break(); await current; }
    if (state === 'error') quitError(false);
    entry = 'prgmHOME';
    drawEntry();
    execute(entry);
  }
  $('run').addEventListener('click', runFromEditor);
  $('stop').addEventListener('click', () => press({ code: 101 }));

  /* ---------- Keys ---------- */

  function press(key) {
    if (key.code === 101) { if (state === 'running') runner.break(); return; }
    if (state === 'running') { runner.press(key); return; }
    if (state === 'error') {
      const n = err.options.length;
      if (key.code === 25) { err.sel = (err.sel + n - 1) % n; drawError(); }
      else if (key.code === 34) { err.sel = (err.sel + 1) % n; drawError(); }
      else if (key.code === 92) quitError(false);
      else if (key.code === 93 && n > 1) quitError(true);
      else if (key.code === 105) quitError(err.options[err.sel] === 'Goto');
      return;
    }
    // idle: typing on the home screen
    if (key.code === 105) {
      if (!entry.trim()) {
        if (!lastEntry) return;
        entry = lastEntry;
        drawEntry();
      }
      execute(entry);
      return;
    }
    if (key.code === 45) {
      if (entry) { entry = ''; drawEntry(); } else { scr.clear(); beginEntry(''); }
      return;
    }
    if (key.code === 23) { entry = [...entry].slice(0, -1).join(''); drawEntry(); return; }
    if (key.ch) { entry += key.ch; drawEntry(); return; }
    if (key.code === 43) { entry += 'prgmHOME'; drawEntry(); }
  }

  // [label, getKey code, character typed, ALPHA character, style]
  const GRAPH_ROW = [['Y=', 11], ['WINDOW', 12], ['ZOOM', 13], ['TRACE', 14], ['GRAPH', 15]];
  const LEFT_BLOCK = [
    ['2nd', 21, null, null, 'second'], ['MODE', 22], ['DEL', 23],
    ['ALPHA', 31, null, null, 'alpha'], ['X,T,θ,n', 32, 'X'], ['STAT', 33],
  ];
  const MAIN = [
    ['MATH', 41, null, 'A'], ['APPS', 42, null, 'B'], ['PRGM', 43, null, 'C'], ['VARS', 44], ['CLEAR', 45],
    ['x⁻¹', 51, null, 'D'], ['SIN', 52, null, 'E'], ['COS', 53, null, 'F'], ['TAN', 54, null, 'G'], ['^', 55, '^', 'H'],
    ['x²', 61, null, 'I'], [',', 62, ',', 'J'], ['(', 63, '(', 'K'], [')', 64, ')', 'L'], ['÷', 65, '/', 'M'],
    ['LOG', 71, null, 'N'], ['7', 72, '7', 'O', 'num'], ['8', 73, '8', 'P', 'num'], ['9', 74, '9', 'Q', 'num'], ['×', 75, '*', 'R'],
    ['LN', 81, null, 'S'], ['4', 82, '4', 'T', 'num'], ['5', 83, '5', 'U', 'num'], ['6', 84, '6', 'V', 'num'], ['−', 85, '-', 'W'],
    ['STO→', 91, '→', 'X'], ['1', 92, '1', 'Y', 'num'], ['2', 93, '2', 'Z', 'num'], ['3', 94, '3', 'θ', 'num'], ['+', 95, '+', '"'],
    ['ON', 101, null, null, 'on'], ['0', 102, '0', ' ', 'num'], ['.', 103, '.', ':', 'num'], ['(−)', 104, '⁻', '?', 'num'], ['ENTER', 105, null, null, 'enter'],
  ];
  const ARROWS = [['▲', 25, 'up', 'Up'], ['◀', 24, 'left', 'Left'], ['▶', 26, 'right', 'Right'], ['▼', 34, 'down', 'Down']];

  const keypad = $('keypad');
  const byCode = {};
  function makeKey([label, code, ch, alphaCh, style], extra) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'key' + (style ? ' ' + style : '') + (extra ? ' ' + extra : '');
    b.innerHTML = (alphaCh ? `<i aria-hidden="true">${alphaCh === ' ' ? '␣' : alphaCh}</i>` : '') + `<span>${label}</span>`;
    b.setAttribute('aria-label', label);
    b.addEventListener('click', () => {
      if (code === 31) { alpha = !alpha; scr.changed(); runner.press({ code }); return; }
      const typed = alpha && alphaCh ? alphaCh : ch;
      alpha = false;
      press({ code, ch: typed });
      scr.changed();
    });
    byCode[code] = b;
    return b;
  }
  const graphRow = document.createElement('div');
  graphRow.className = 'row graph-row';
  GRAPH_ROW.forEach(k => graphRow.appendChild(makeKey(k, 'graph')));
  keypad.appendChild(graphRow);

  const upper = document.createElement('div');
  upper.className = 'upper';
  const left = document.createElement('div');
  left.className = 'left-block';
  LEFT_BLOCK.forEach(k => left.appendChild(makeKey(k)));
  const dpad = document.createElement('div');
  dpad.className = 'dpad';
  ARROWS.forEach(([sym, code, cls, name]) => {
    const b = makeKey([sym, code], 'arrow ' + cls);
    b.setAttribute('aria-label', name);
    dpad.appendChild(b);
  });
  upper.append(left, dpad);
  keypad.appendChild(upper);

  const main = document.createElement('div');
  main.className = 'main-keys';
  MAIN.forEach(k => main.appendChild(makeKey(k)));
  keypad.appendChild(main);

  // Physical keyboard
  const KB = {
    ArrowUp: [25], ArrowDown: [34], ArrowLeft: [24], ArrowRight: [26],
    Enter: [105], Escape: [45], Backspace: [23], Delete: [23],
    '0': [102, '0'], '1': [92, '1'], '2': [93, '2'], '3': [94, '3'], '4': [82, '4'],
    '5': [83, '5'], '6': [84, '6'], '7': [72, '7'], '8': [73, '8'], '9': [74, '9'],
    '.': [103, '.'], '+': [95, '+'], '-': [85, '-'], '*': [75, '*'], '/': [65, '/'],
    '^': [55, '^'], '(': [63, '('], ')': [64, ')'], ',': [62, ','], '~': [104, '⁻'],
  };
  const TYPE_ONLY = /^[A-Za-z"': ?=<>!]$/;
  document.addEventListener('keydown', (e) => {
    const t = e.target;
    if (t === source || (t.tagName === 'INPUT') || (t.tagName === 'SUMMARY')) return;
    if (e.ctrlKey && (e.key === 'b' || e.key === 'B')) { e.preventDefault(); flash(101); press({ code: 101 }); return; }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (t.tagName === 'BUTTON' && (e.key === 'Enter' || e.key === ' ')) return; // let the button act
    let key = null;
    if (KB[e.key]) key = { code: KB[e.key][0], ch: KB[e.key][1] || null };
    else if (TYPE_ONLY.test(e.key)) key = { code: 0, ch: /[a-z]/.test(e.key) ? e.key.toUpperCase() : e.key };
    else if (e.key === ' ') key = { code: 0, ch: ' ' };
    if (!key) return;
    e.preventDefault();
    alpha = false;
    flash(key.code);
    press(key);
  });
  function flash(code) {
    const b = byCode[code];
    if (!b) return;
    b.classList.add('pressed');
    setTimeout(() => b.classList.remove('pressed'), 120);
  }

  /* ---------- Start ---------- */
  beginEntry('prgmHOME');
  render();
})();
