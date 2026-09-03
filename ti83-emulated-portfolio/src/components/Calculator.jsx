import {
  useCallback, useEffect, useMemo, useRef, useState,
} from 'react';

import Display from './Display.jsx';
import Keypad from './Keypad.jsx';

import { createScreen, cloneScreen, clearHome, writeLine, dispLine } from '../lib/screen.js';
import { createContext, evaluate } from '../lib/evaluate.js';
import { parseExpression, parseCached } from '../lib/parse.js';
import { formatNumber, wrap } from '../lib/format.js';
import { compile, run, splitTop, storeInto } from '../lib/basic.js';
import { DEFAULT_PROGRAMS } from '../lib/programs.js';
import { KEY_BY_ID, KEYCODES, mapPhysicalKey } from '../lib/keys.js';
import { WINDOW_FIELDS, ZOOM_ITEMS } from '../lib/render.js';
import {
  DEFAULT_WINDOW, ZOOM_PRESETS, squareWindow, zoomBy, xAt, pyAt, GRAPH_W,
} from '../lib/graph.js';

/** Modes whose active field accepts typed characters. */
const TEXT_MODES = new Set(['home', 'yeq', 'window']);

const emptyEdit = { text: '', pos: 0 };

export default function Calculator() {
  // Mutable state the interpreter writes to directly.
  const screenRef = useRef(createScreen());
  const ctxRef = useRef(null);
  if (ctxRef.current === null) {
    ctxRef.current = createContext({ screen: screenRef.current, yvars: {} });
  }
  const runnerRef = useRef(null);

  // React-visible snapshots.
  const [screenState, setScreenState] = useState(() => cloneScreen(screenRef.current));
  const [yvars, setYvars] = useState({});

  const [mode, setMode] = useState('run');
  const [edit, setEdit] = useState(emptyEdit);
  const [second, setSecond] = useState(false);
  const [alpha, setAlpha] = useState(false);
  const [busy, setBusy] = useState(false);
  const [waiting, setWaiting] = useState(null);
  const [lastEntry, setLastEntry] = useState('');
  const [angleDeg, setAngleDeg] = useState(false);

  const [win, setWin] = useState(DEFAULT_WINDOW);
  const [winSel, setWinSel] = useState(0);
  const [ySel, setYSel] = useState(1);
  const [yScroll, setYScroll] = useState(0);
  const [zoomSel, setZoomSel] = useState(0);

  const [programs] = useState(DEFAULT_PROGRAMS);
  const [prgmTab, setPrgmTab] = useState(0);
  const [prgmSel, setPrgmSel] = useState(0);
  const [editScroll, setEditScroll] = useState(0);

  const [traceN, setTraceN] = useState(1);
  const [tracePx, setTracePx] = useState(Math.floor(GRAPH_W / 2));

  // Keep the evaluation context in step with settings on every render.
  ctxRef.current.angleDeg = angleDeg;

  /** Publish the mutable screen and Y= store into React state. */
  const commit = useCallback(() => {
    setScreenState(cloneScreen(screenRef.current));
    setYvars({ ...ctxRef.current.yvars });
  }, []);

  // ---------------------------------------------------------------- program

  const finish = useCallback((result) => {
    runnerRef.current = null;
    const s = screenRef.current;
    if (result?.type === 'error') {
      dispLine(s, `ERR:${result.message}`, false);
    } else {
      dispLine(s, 'Done', true);
    }
    setBusy(false);
    setWaiting(null);
    setMode('home');
    setEdit(emptyEdit);
    commit();
  }, [commit]);

  /** Drive the interpreter until it blocks, finishes, or asks to yield. */
  const pump = useCallback((resumeValue) => {
    const runner = runnerRef.current;
    if (!runner) return;

    let value = resumeValue;
    for (;;) {
      let res;
      try {
        res = runner.iter.next(value);
      } catch (err) {
        finish({ type: 'error', message: err?.message || 'SYNTAX' });
        return;
      }
      value = undefined;

      if (res.done) {
        finish(res.value);
        return;
      }

      const effect = res.value;

      if (effect.type === 'render') continue;

      if (effect.type === 'tick') {
        commit();
        runner.timer = setTimeout(() => pump(), 0);
        return;
      }

      if (effect.type === 'pause') {
        setBusy(false);
        setWaiting({ kind: 'pause' });
        setMode('run');
        commit();
        return;
      }

      if (effect.type === 'input') {
        setBusy(false);
        setEdit(emptyEdit);
        setWaiting({ kind: 'input', prompt: effect.prompt });
        setMode('run');
        commit();
        return;
      }

      if (effect.type === 'menu') {
        setBusy(false);
        setWaiting({
          kind: 'menu', title: effect.title, items: effect.items, index: 0,
        });
        setMode('menu');
        commit();
        return;
      }
    }
  }, [commit, finish]);

  const runProgram = useCallback((index) => {
    const prog = programs[index];
    if (!prog) return;

    let compiled;
    try {
      compiled = compile(prog.source);
    } catch (err) {
      clearHome(screenRef.current);
      dispLine(screenRef.current, `ERR:${err.message}`, false);
      setMode('home');
      commit();
      return;
    }

    clearHome(screenRef.current);
    runnerRef.current = { iter: run(compiled, ctxRef.current), timer: null };
    setEdit(emptyEdit);
    setWaiting(null);
    setBusy(true);
    setMode('run');
    pump(undefined);
  }, [programs, pump, commit]);

  const stopProgram = useCallback((message) => {
    const runner = runnerRef.current;
    if (runner?.timer) clearTimeout(runner.timer);
    runnerRef.current = null;
    if (message) dispLine(screenRef.current, message, false);
    setBusy(false);
    setWaiting(null);
    setEdit(emptyEdit);
    commit();
  }, [commit]);

  // The portfolio program is the front door: it runs on power-on.
  useEffect(() => {
    runProgram(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ------------------------------------------------------------- edit field

  const insertText = useCallback((text) => {
    setEdit((e) => ({
      text: e.text.slice(0, e.pos) + text + e.text.slice(e.pos),
      pos: e.pos + text.length,
    }));
  }, []);

  const backspace = useCallback(() => {
    setEdit((e) => (
      e.pos > 0
        ? { text: e.text.slice(0, e.pos - 1) + e.text.slice(e.pos), pos: e.pos - 1 }
        : e
    ));
  }, []);

  const moveCursor = useCallback((delta) => {
    setEdit((e) => ({ ...e, pos: Math.max(0, Math.min(e.text.length, e.pos + delta)) }));
  }, []);

  // ----------------------------------------------------------- home screen

  const submitHome = useCallback(() => {
    const s = screenRef.current;
    const ctx = ctxRef.current;
    const text = edit.text;

    for (const chunk of wrap(text, 16)) writeLine(s, chunk);
    setEdit(emptyEdit);

    if (text.trim() === '') {
      commit();
      return;
    }
    setLastEntry(text);

    try {
      const parts = splitTop(text, '→');
      let value;
      if (parts.length === 2) {
        value = evaluate(parseExpression(parts[0]), ctx);
        storeInto(parts[1].trim(), value, ctx);
      } else {
        value = evaluate(parseExpression(text), ctx);
      }
      if (typeof value === 'number') ctx.ans = value;
      dispLine(s, typeof value === 'string' ? value : formatNumber(value), typeof value !== 'string');
    } catch (err) {
      dispLine(s, `ERR:${err?.message || 'SYNTAX'}`, false);
    }

    commit();
  }, [edit.text, commit]);

  // -------------------------------------------------------- editor commits

  const commitY = useCallback((n, text) => {
    ctxRef.current.yvars[n] = text;
    commit();
  }, [commit]);

  const commitWindowField = useCallback((index, text) => {
    const field = WINDOW_FIELDS[index];
    try {
      const value = evaluate(parseExpression(text), ctxRef.current);
      if (typeof value === 'number' && Number.isFinite(value)) {
        setWin((w) => ({ ...w, [field]: value }));
      }
    } catch {
      // An unparseable field simply keeps its previous value, as on hardware.
    }
  }, []);

  const commitCurrentEdit = useCallback(() => {
    if (mode === 'yeq') commitY(ySel, edit.text);
    else if (mode === 'window') commitWindowField(winSel, edit.text);
  }, [mode, ySel, winSel, edit.text, commitY, commitWindowField]);

  // ------------------------------------------------------------ navigation

  // The hardware parks the cursor at the start of a field when you open an
  // editor, which also keeps a leading minus sign in view on long values.
  const enterYeq = useCallback(() => {
    setMode('yeq');
    setEdit({ text: ctxRef.current.yvars[ySel] || '', pos: 0 });
  }, [ySel]);

  const enterWindow = useCallback(() => {
    setMode('window');
    setEdit({ text: formatNumber(win[WINDOW_FIELDS[winSel]] ?? 1), pos: 0 });
  }, [win, winSel]);

  const firstDefinedY = useCallback(() => {
    for (let n = 1; n <= 9; n++) {
      if ((ctxRef.current.yvars[n] || '').trim()) return n;
    }
    return null;
  }, []);

  const enterTrace = useCallback(() => {
    const n = firstDefinedY();
    if (n === null) {
      setMode('graph');
      return;
    }
    setTraceN(n);
    setTracePx(Math.floor(GRAPH_W / 2));
    setMode('trace');
  }, [firstDefinedY]);

  const quitToHome = useCallback(() => {
    if (runnerRef.current) stopProgram(null);
    setMode('home');
    setEdit(emptyEdit);
  }, [stopProgram]);

  // ------------------------------------------------------------- the trace

  const trace = useMemo(() => {
    if (mode !== 'trace') return null;
    const source = yvars[traceN];
    if (!source || !source.trim()) return null;

    const ctx = ctxRef.current;
    const x = xAt(tracePx, win);
    const savedX = ctx.vars.X;
    ctx.vars.X = x;
    let y = null;
    try {
      const v = evaluate(parseCached(source), ctx);
      if (typeof v === 'number' && Number.isFinite(v)) y = v;
    } catch {
      y = null;
    }
    ctx.vars.X = savedX;

    if (y === null) return { label: `Y${traceN}=${source}`.slice(0, 16), x, y: NaN, point: null };
    return {
      label: `Y${traceN}=${source}`.slice(0, 16),
      x,
      y,
      point: { px: tracePx, py: pyAt(y, win) },
    };
  }, [mode, traceN, tracePx, win, yvars]);

  // -------------------------------------------------------------- dispatch

  const applyZoom = useCallback((index) => {
    setWin((w) => {
      switch (ZOOM_ITEMS[index]) {
        case 'ZStandard': return { ...ZOOM_PRESETS.ZStandard };
        case 'ZSquare': return squareWindow(w);
        case 'ZTrig': return { ...ZOOM_PRESETS.ZTrig };
        case 'ZDecimal': return { ...ZOOM_PRESETS.ZDecimal };
        case 'Zoom In': return zoomBy(w, 0.25);
        case 'Zoom Out': return zoomBy(w, 4);
        default: return w;
      }
    });
    setMode('graph');
  }, []);

  const dispatch = useCallback((id, sec, alp) => {
    const key = KEY_BY_ID[id];

    // ON breaks a running program; otherwise it is a no-op.
    if (id === 'ON') {
      if (runnerRef.current) {
        stopProgram('ERR:BREAK');
        setMode('home');
      }
      return;
    }

    // 2nd + MODE is QUIT, and works from everywhere.
    if (sec && id === 'MODE') {
      quitToHome();
      return;
    }

    // --- a program is waiting on the user ---

    if (waiting?.kind === 'menu') {
      const count = waiting.items.length;
      if (id === 'UP') {
        setWaiting((w) => ({ ...w, index: (w.index - 1 + count) % count }));
      } else if (id === 'DOWN') {
        setWaiting((w) => ({ ...w, index: (w.index + 1) % count }));
      } else if (id === 'ENTER') {
        const chosen = waiting.items[waiting.index];
        setWaiting(null);
        setMode('run');
        setBusy(true);
        pump(chosen.lbl);
      } else if (/^[1-9]$/.test(id)) {
        const index = Number(id) - 1;
        if (index < count) {
          const chosen = waiting.items[index];
          setWaiting(null);
          setMode('run');
          setBusy(true);
          pump(chosen.lbl);
        }
      }
      return;
    }

    if (waiting?.kind === 'pause') {
      if (id === 'ENTER') {
        setWaiting(null);
        setBusy(true);
        pump(undefined);
      }
      return;
    }

    if (waiting?.kind === 'input') {
      const ins = sec ? key?.ins2 : alp ? key?.alpha : key?.ins;
      if (id === 'ENTER') {
        const value = edit.text;
        setEdit(emptyEdit);
        setWaiting(null);
        setBusy(true);
        // Echo the answer so the transcript reads like the real thing.
        writeLine(screenRef.current, `${waiting.prompt}${value}`);
        pump(value);
      } else if (id === 'DEL') {
        backspace();
      } else if (id === 'CLEAR') {
        setEdit(emptyEdit);
      } else if (id === 'LEFT') {
        moveCursor(-1);
      } else if (id === 'RIGHT') {
        moveCursor(1);
      } else if (ins) {
        insertText(ins);
      }
      return;
    }

    // A program is mid-execution; only ON and QUIT get through.
    if (busy) return;

    // --- text entry ---

    const ins = sec ? key?.ins2 : alp ? key?.alpha : key?.ins;
    if (ins && TEXT_MODES.has(mode)) {
      insertText(ins);
      return;
    }

    // --- screen navigation, available from any mode ---

    switch (id) {
      case 'Y=': commitCurrentEdit(); enterYeq(); return;
      case 'WINDOW': commitCurrentEdit(); enterWindow(); return;
      case 'GRAPH': commitCurrentEdit(); setMode('graph'); return;
      case 'TRACE': commitCurrentEdit(); enterTrace(); return;
      case 'ZOOM': commitCurrentEdit(); setZoomSel(0); setMode('zoom'); return;
      case 'PRGM': commitCurrentEdit(); setPrgmTab(0); setPrgmSel(0); setMode('prgm'); return;
      case 'MODE': setMode('mode'); return;
      case 'STAT': setMode('stat'); return;
      case 'MATH': setMode('math'); return;
      case 'APPS': setMode('apps'); return;
      case 'VARS': setMode('vars'); return;
      case 'INV':
        if (sec) { setMode('matrix'); return; }
        break;
      default:
        break;
    }

    // --- per-mode handling ---

    switch (mode) {
      case 'home':
        if (id === 'ENTER') submitHome();
        else if (id === 'DEL') backspace();
        else if (id === 'LEFT') moveCursor(-1);
        else if (id === 'RIGHT') moveCursor(1);
        else if (id === 'CLEAR') {
          if (edit.text === '') {
            clearHome(screenRef.current);
            commit();
          } else {
            setEdit(emptyEdit);
          }
        } else if (id === 'ENTER' || (sec && id === 'ENTER')) {
          submitHome();
        }
        // 2nd + ENTER recalls the previous entry.
        if (sec && id === 'ENTER') setEdit({ text: lastEntry, pos: lastEntry.length });
        return;

      case 'yeq': {
        if (id === 'DEL') { backspace(); return; }
        if (id === 'LEFT') { moveCursor(-1); return; }
        if (id === 'RIGHT') { moveCursor(1); return; }
        if (id === 'CLEAR') { setEdit(emptyEdit); return; }
        if (id === 'UP' || id === 'DOWN' || id === 'ENTER') {
          commitY(ySel, edit.text);
          const next = Math.max(1, Math.min(9, ySel + (id === 'UP' ? -1 : 1)));
          setYSel(next);
          setYScroll((s) => Math.max(0, Math.min(next - 1, Math.max(s, next - 7))));
          setEdit({ text: ctxRef.current.yvars[next] || '', pos: 0 });
        }
        return;
      }

      case 'window': {
        if (id === 'DEL') { backspace(); return; }
        if (id === 'LEFT') { moveCursor(-1); return; }
        if (id === 'RIGHT') { moveCursor(1); return; }
        if (id === 'CLEAR') { setEdit(emptyEdit); return; }
        if (id === 'UP' || id === 'DOWN' || id === 'ENTER') {
          commitWindowField(winSel, edit.text);
          const next = Math.max(0, Math.min(
            WINDOW_FIELDS.length - 1,
            winSel + (id === 'UP' ? -1 : 1),
          ));
          setWinSel(next);
          const current = winSel === next
            ? edit.text
            : formatNumber(win[WINDOW_FIELDS[next]] ?? 1);
          setEdit({ text: current, pos: 0 });
        }
        return;
      }

      case 'graph':
      case 'trace': {
        if (id === 'CLEAR') { setMode('home'); return; }
        if (mode !== 'trace') return;
        if (id === 'LEFT') setTracePx((p) => Math.max(0, p - 1));
        else if (id === 'RIGHT') setTracePx((p) => Math.min(GRAPH_W - 1, p + 1));
        else if (id === 'UP' || id === 'DOWN') {
          // Step to the next defined function, wrapping.
          const step = id === 'UP' ? -1 : 1;
          for (let i = 1; i <= 9; i++) {
            const n = ((traceN - 1 + step * i) % 9 + 9) % 9 + 1;
            if ((ctxRef.current.yvars[n] || '').trim()) { setTraceN(n); break; }
          }
        }
        return;
      }

      case 'zoom': {
        if (id === 'CLEAR') { setMode('graph'); return; }
        if (id === 'UP') setZoomSel((z) => (z - 1 + ZOOM_ITEMS.length) % ZOOM_ITEMS.length);
        else if (id === 'DOWN') setZoomSel((z) => (z + 1) % ZOOM_ITEMS.length);
        else if (id === 'ENTER') applyZoom(zoomSel);
        else if (/^[1-6]$/.test(id)) applyZoom(Number(id) - 1);
        return;
      }

      case 'prgm': {
        if (id === 'CLEAR') { setMode('home'); return; }
        if (id === 'LEFT') { setPrgmTab((t) => Math.max(0, t - 1)); return; }
        if (id === 'RIGHT') { setPrgmTab((t) => Math.min(2, t + 1)); return; }
        if (prgmTab === 2) return;
        if (id === 'UP') setPrgmSel((s) => (s - 1 + programs.length) % programs.length);
        else if (id === 'DOWN') setPrgmSel((s) => (s + 1) % programs.length);
        else if (id === 'ENTER') {
          if (prgmTab === 0) runProgram(prgmSel);
          else { setEditScroll(0); setMode('prgmedit'); }
        } else if (/^[1-9]$/.test(id)) {
          const index = Number(id) - 1;
          if (index < programs.length) {
            setPrgmSel(index);
            if (prgmTab === 0) runProgram(index);
            else { setEditScroll(0); setMode('prgmedit'); }
          }
        }
        return;
      }

      case 'prgmedit': {
        const lines = programs[prgmSel]?.source.split('\n').length ?? 0;
        if (id === 'CLEAR') { setMode('prgm'); return; }
        if (id === 'UP') setEditScroll((s) => Math.max(0, s - 1));
        else if (id === 'DOWN') setEditScroll((s) => Math.min(Math.max(0, lines - 7), s + 1));
        return;
      }

      case 'mode': {
        if (id === 'CLEAR') { setMode('home'); return; }
        if (id === 'ENTER' || id === 'LEFT' || id === 'RIGHT') setAngleDeg((d) => !d);
        return;
      }

      default:
        if (id === 'CLEAR') setMode('home');
        return;
    }
  }, [
    mode, waiting, busy, edit.text, ySel, winSel, win, zoomSel, prgmTab, prgmSel,
    programs, traceN, lastEntry, pump, stopProgram, quitToHome, submitHome,
    insertText, backspace, moveCursor, commitCurrentEdit, commitY,
    commitWindowField, enterYeq, enterWindow, enterTrace, applyZoom, runProgram,
    commit,
  ]);

  const pressKey = useCallback((id) => {
    if (id === '2ND') {
      setSecond((s) => !s);
      setAlpha(false);
      return;
    }
    if (id === 'ALPHA') {
      setAlpha((a) => !a);
      setSecond(false);
      return;
    }

    const sec = second;
    const alp = alpha;
    setSecond(false);
    setAlpha(false);

    // getKey sees arrow/enter/digit presses while a program polls for them.
    const code = KEYCODES[id.toLowerCase()] ?? KEYCODES[id];
    if (code) ctxRef.current.getKey = code;

    dispatch(id, sec, alp);
  }, [second, alpha, dispatch]);

  // Letter pseudo-keys bypass the key table and insert straight into the field.
  const handlePress = useCallback((id) => {
    if (id.startsWith('LETTER:')) {
      const letter = id.slice(7);
      if (TEXT_MODES.has(mode) || waiting?.kind === 'input') insertText(letter);
      return;
    }
    pressKey(id);
  }, [mode, waiting, insertText, pressKey]);

  // Physical keyboard support, routed through the same dispatcher the keypad
  // uses — including the LETTER: pseudo-keys, which pressKey alone cannot map.
  const pressRef = useRef(handlePress);
  pressRef.current = handlePress;

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;

      const mapped = mapPhysicalKey(event);
      if (mapped) {
        event.preventDefault();
        pressRef.current(mapped);
        return;
      }

      // Letters type directly, which is friendlier than chording ALPHA.
      if (/^[a-zA-Z]$/.test(event.key)) {
        event.preventDefault();
        pressRef.current(`LETTER:${event.key.toUpperCase()}`);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const state = {
    mode, screen: screenState, entry: edit.text, cursor: edit.pos,
    waiting, yvars, ySel, yScroll, win, winSel, programs, prgmTab, prgmSel,
    editScroll, angleDeg, second, alpha, busy, trace, zoomSel,
  };

  return (
    <div className="calculator">
      <div className="brand">
        <span className="brand-ti">TI-83 Plus</span>
        <span className="brand-sub">portfolio edition</span>
      </div>
      <div className="screen-bezel">
        <Display state={state} evalCtx={ctxRef.current} />
      </div>
      <Keypad onPress={handlePress} second={second} alpha={alpha} />
    </div>
  );
}
