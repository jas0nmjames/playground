/*
 * A small TI-BASIC interpreter for the TI-83/84 home screen.
 *
 * It covers the commands a menu-driven program needs: ClrHome, Disp,
 * Output(, Pause, Wait, Menu(, Lbl/Goto, Input, Prompt, If/Then/Else/End,
 * While, Repeat, For(, Stop/Return, DelVar, → (store) and getKey, with
 * real-variable (A–Z, θ) and string (Str0–Str9) storage.
 *
 * No DOM here: the page wires a Screen and key presses into a Runner.
 */
(function (global) {
  'use strict';

  const ROWS = 8;
  const COLS = 16;

  class TIError extends Error {
    constructor(kind, stmt) {
      super('ERR:' + kind);
      this.kind = kind;
      this.stmt = stmt;
    }
  }

  /* ---------- Screen: an 8×16 character home screen ---------- */

  class Screen {
    constructor() {
      this.onChange = null;
      this.cursor = null; // { r, c, ch } while text is being typed
      this.clear();
    }
    blankRow() { return Array(COLS).fill(' '); }
    clear() {
      this.chars = Array.from({ length: ROWS }, () => this.blankRow());
      this.inv = Array.from({ length: ROWS }, () => Array(COLS).fill(false));
      this.row = 0; // next line Disp writes to
      this.changed();
    }
    changed() { if (this.onChange) this.onChange(); }
    snapshot() {
      return { chars: this.chars.map(r => r.slice()), inv: this.inv.map(r => r.slice()), row: this.row };
    }
    restore(s) {
      this.chars = s.chars.map(r => r.slice());
      this.inv = s.inv.map(r => r.slice());
      this.row = s.row;
      this.changed();
    }
    put(r, c, ch, inv = false) {
      if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return;
      this.chars[r][c] = ch;
      this.inv[r][c] = inv;
    }
    clearRow(r) {
      for (let c = 0; c < COLS; c++) this.put(r, c, ' ');
    }
    // Writes text from (r, c), wrapping onto the next rows like Output(.
    write(r, c, text, inv = false) {
      for (const ch of text) {
        if (r >= ROWS) break;
        this.put(r, c, ch, inv);
        if (++c >= COLS) { c = 0; r++; }
      }
      this.changed();
    }
    // Claims the next home-screen line, scrolling when the screen is full.
    nextLine() {
      if (this.row >= ROWS) {
        this.chars.shift(); this.inv.shift();
        this.chars.push(this.blankRow()); this.inv.push(Array(COLS).fill(false));
        this.row = ROWS - 1;
      }
      const r = this.row++;
      this.clearRow(r);
      return r;
    }
    line(text, right = false) {
      const r = this.nextLine();
      let t = [...text];
      if (t.length > COLS) t = t.slice(0, COLS - 1).concat('…');
      const start = right ? COLS - t.length : 0;
      t.forEach((ch, i) => this.put(r, start + i, ch));
      this.changed();
      return r;
    }
  }

  /* ---------- Values ---------- */

  function fmtNum(n) {
    if (Number.isNaN(n) || !Number.isFinite(n)) throw new TIError('OVERFLOW');
    if (n === 0) return '0';
    const a = Math.abs(n);
    let s;
    if (a >= 1e10 || a < 1e-3) {
      let [m, e] = n.toExponential(9).split('e');
      m = m.replace(/\.?0+$/, '');
      s = m + 'ᴇ' + parseInt(e, 10);
    } else {
      s = String(parseFloat(n.toPrecision(10)));
    }
    return s.replace(/^(-?)0\./, '$1.').replace(/-/g, '⁻');
  }

  function toText(v) { return typeof v === 'string' ? v : fmtNum(v); }
  function num(v) { if (typeof v !== 'number') throw new TIError('DATA TYPE'); return v; }
  function str(v) { if (typeof v !== 'string') throw new TIError('DATA TYPE'); return v; }
  function truth(v) { return num(v) !== 0; }
  const bool = b => (b ? 1 : 0);

  /* ---------- Tokenizer ---------- */

  const FUNCS = ['randInt(', 'remainder(', 'toString(', 'length(', 'iPart(', 'fPart(',
    'round(', 'sqrt(', 'int(', 'abs(', 'min(', 'max(', 'not(', 'sub(', '√('];
  const WORDS = ['getKey', 'rand', 'Ans', 'xor', 'and', 'or', 'π'];
  const OPS2 = { '!=': '≠', '<=': '≤', '>=': '≥' };
  const OPS1 = { '=': '=', '≠': '≠', '<': '<', '>': '>', '≤': '≤', '≥': '≥', '+': '+', '-': '-',
    '−': '-', '⁻': '⁻', '*': '*', '×': '*', '/': '/', '÷': '/', '^': '^', '(': '(', ')': ')', ',': ',' };

  function tokenize(src) {
    const toks = [];
    let i = 0;
    while (i < src.length) {
      const ch = src[i];
      if (ch === ' ' || ch === '\t') { i++; continue; }
      if (ch === '"') {
        let j = i + 1;
        while (j < src.length && src[j] !== '"' && src[j] !== '→') j++;
        toks.push({ t: 'str', v: src.slice(i + 1, j) });
        i = src[j] === '"' ? j + 1 : j;
        continue;
      }
      const m = /^(\d+\.?\d*|\.\d+)(ᴇ[⁻-]?\d+)?/.exec(src.slice(i));
      if (m) {
        toks.push({ t: 'num', v: parseFloat(m[0].replace('ᴇ', 'e').replace('⁻', '-')) });
        i += m[0].length;
        continue;
      }
      const rest = src.slice(i);
      const fn = FUNCS.find(f => rest.startsWith(f));
      if (fn) { toks.push({ t: 'fn', v: fn.slice(0, -1) }); i += fn.length; continue; }
      const sv = /^Str(\d)/.exec(rest);
      if (sv) { toks.push({ t: 'strvar', v: 'Str' + sv[1] }); i += 4; continue; }
      const w = WORDS.find(x => rest.startsWith(x));
      if (w) { toks.push(w === 'and' || w === 'or' || w === 'xor' ? { t: 'op', v: w } : { t: 'word', v: w }); i += w.length; continue; }
      const two = rest.slice(0, 2);
      if (OPS2[two]) { toks.push({ t: 'op', v: OPS2[two] }); i += 2; continue; }
      if (OPS1[ch]) { toks.push({ t: 'op', v: OPS1[ch] }); i++; continue; }
      if (/[A-Zθ]/.test(ch)) { toks.push({ t: 'var', v: ch }); i++; continue; }
      throw new TIError('SYNTAX');
    }
    // TI-BASIC allows implied multiplication: 2A, 3(A+1), A B
    const out = [];
    const endsValue = t => t && (t.t === 'num' || t.t === 'var' || t.t === 'strvar' || t.t === 'word' || (t.t === 'op' && t.v === ')'));
    const startsValue = t => t.t === 'num' || t.t === 'var' || t.t === 'strvar' || t.t === 'word' || t.t === 'fn' || (t.t === 'op' && (t.v === '(' || t.v === '⁻'));
    for (const t of toks) {
      if (endsValue(out[out.length - 1]) && startsValue(t)) out.push({ t: 'op', v: '*' });
      out.push(t);
    }
    return out;
  }

  /* ---------- Parser: tokens → closures that take the Runner ---------- */

  class Parser {
    constructor(toks) { this.toks = toks; this.i = 0; }
    peek() { return this.toks[this.i]; }
    next() { return this.toks[this.i++]; }
    at(v) { const t = this.peek(); return !!t && t.t === 'op' && t.v === v; }
    done() { return this.i >= this.toks.length; }

    expr() { return this.or(); }
    or() {
      let l = this.and();
      while (this.at('or') || this.at('xor')) {
        const op = this.next().v, L = l, R = this.and();
        l = op === 'or' ? c => bool(truth(L(c)) || truth(R(c))) : c => bool(truth(L(c)) !== truth(R(c)));
      }
      return l;
    }
    and() {
      let l = this.rel();
      while (this.at('and')) {
        this.next();
        const L = l, R = this.rel();
        l = c => bool(truth(L(c)) && truth(R(c)));
      }
      return l;
    }
    rel() {
      let l = this.add();
      while (['=', '≠', '<', '>', '≤', '≥'].some(o => this.at(o))) {
        const op = this.next().v, L = l, R = this.add();
        l = c => {
          const a = L(c), b = R(c);
          if (op === '=' || op === '≠') {
            if (typeof a !== typeof b) throw new TIError('DATA TYPE');
            return bool((a === b) === (op === '='));
          }
          num(a); num(b);
          return bool(op === '<' ? a < b : op === '>' ? a > b : op === '≤' ? a <= b : a >= b);
        };
      }
      return l;
    }
    add() {
      let l = this.mul();
      while (this.at('+') || this.at('-')) {
        const op = this.next().v, L = l, R = this.mul();
        l = c => {
          const a = L(c), b = R(c);
          if (op === '+' && typeof a === 'string' && typeof b === 'string') return a + b;
          return op === '+' ? num(a) + num(b) : num(a) - num(b);
        };
      }
      return l;
    }
    mul() {
      let l = this.neg();
      while (this.at('*') || this.at('/')) {
        const op = this.next().v, L = l, R = this.neg();
        l = c => {
          const a = num(L(c)), b = num(R(c));
          if (op === '/' && b === 0) throw new TIError('DIVIDE BY 0');
          return op === '*' ? a * b : a / b;
        };
      }
      return l;
    }
    neg() {
      if (this.at('⁻') || this.at('-')) {
        this.next();
        const e = this.neg();
        return c => -num(e(c));
      }
      return this.pow();
    }
    pow() {
      let l = this.primary();
      while (this.at('^')) {
        this.next();
        let R;
        if (this.at('⁻') || this.at('-')) { this.next(); const p = this.primary(); R = c => -num(p(c)); }
        else R = this.primary();
        const L = l;
        l = c => Math.pow(num(L(c)), num(R(c)));
      }
      return l;
    }
    closeParen() { if (this.at(')')) this.next(); } // a missing ) is fine in TI-BASIC
    primary() {
      const t = this.next();
      if (!t) throw new TIError('SYNTAX');
      switch (t.t) {
        case 'num': return () => t.v;
        case 'str': return () => t.v;
        case 'var': return c => c.vars[t.v] || 0;
        case 'strvar': return c => {
          if (!(t.v in c.strs)) throw new TIError('UNDEFINED');
          return c.strs[t.v];
        };
        case 'word':
          if (t.v === 'getKey') return c => c.readKey();
          if (t.v === 'rand') return () => Math.random();
          if (t.v === 'Ans') return c => c.ans;
          if (t.v === 'π') return () => Math.PI;
          break;
        case 'fn': {
          const args = [];
          if (!this.at(')') && !this.done()) {
            args.push(this.expr());
            while (this.at(',')) { this.next(); args.push(this.expr()); }
          }
          this.closeParen();
          return makeCall(t.v, args);
        }
        case 'op':
          if (t.v === '(') { const e = this.expr(); this.closeParen(); return e; }
          break;
      }
      throw new TIError('SYNTAX');
    }
    list() {
      const out = [this.expr()];
      while (this.at(',')) { this.next(); out.push(this.expr()); }
      this.closeParen();
      if (!this.done()) throw new TIError('SYNTAX');
      return out;
    }
  }

  function makeCall(name, args) {
    const need = (lo, hi = lo) => { if (args.length < lo || args.length > hi) throw new TIError('ARGUMENT'); };
    const N = (c, i) => num(args[i](c));
    switch (name) {
      case 'randInt': need(2, 3); return c => {
        const a = Math.ceil(Math.min(N(c, 0), N(c, 1))), b = Math.floor(Math.max(N(c, 0), N(c, 1)));
        return a + Math.floor(Math.random() * (b - a + 1));
      };
      case 'int': need(1); return c => Math.floor(N(c, 0));
      case 'iPart': need(1); return c => Math.trunc(N(c, 0));
      case 'fPart': need(1); return c => { const x = N(c, 0); return x - Math.trunc(x); };
      case 'abs': need(1); return c => Math.abs(N(c, 0));
      case 'round': need(1, 2); return c => {
        const d = args[1] ? N(c, 1) : 9, k = Math.pow(10, d);
        return Math.round(N(c, 0) * k) / k;
      };
      case 'min': need(2); return c => Math.min(N(c, 0), N(c, 1));
      case 'max': need(2); return c => Math.max(N(c, 0), N(c, 1));
      case 'not': need(1); return c => bool(!truth(args[0](c)));
      case 'remainder': need(2); return c => {
        const b = N(c, 1);
        if (b === 0) throw new TIError('DIVIDE BY 0');
        return N(c, 0) % b;
      };
      case 'sqrt': case '√': need(1); return c => {
        const x = N(c, 0);
        if (x < 0) throw new TIError('NONREAL ANS');
        return Math.sqrt(x);
      };
      case 'length': need(1); return c => [...str(args[0](c))].length;
      case 'sub': need(3); return c => {
        const s = [...str(args[0](c))], start = N(c, 1), len = N(c, 2);
        if (start < 1 || len < 1 || start + len - 1 > s.length) throw new TIError('INVALID DIM');
        return s.slice(start - 1, start - 1 + len).join('');
      };
      case 'toString': need(1); return c => toText(args[0](c));
    }
    throw new TIError('SYNTAX');
  }

  function compileExpr(src) {
    const p = new Parser(tokenize(src));
    if (p.done()) throw new TIError('SYNTAX');
    const e = p.expr();
    if (!p.done()) throw new TIError('SYNTAX');
    return e;
  }
  function compileList(src) {
    const p = new Parser(tokenize(src));
    if (p.done()) throw new TIError('SYNTAX');
    return p.list();
  }

  /* ---------- Statements ---------- */

  // Splits on commas outside strings and parentheses; drops one closing ).
  function splitArgs(src) {
    const parts = [];
    let cur = '', depth = 0, inStr = false;
    for (const ch of src) {
      if (ch === '"') inStr = !inStr;
      else if (!inStr && ch === '(') depth++;
      else if (!inStr && ch === ')') {
        if (depth === 0) break;
        depth--;
      } else if (!inStr && ch === ',' && depth === 0) { parts.push(cur.trim()); cur = ''; continue; }
      cur += ch;
    }
    parts.push(cur.trim());
    return parts;
  }

  const isVar = s => /^[A-Zθ]$/.test(s);
  const isStrVar = s => /^Str\d$/.test(s);
  const isLabel = s => /^[A-Z0-9θ]{1,2}$/.test(s);

  function lastStoreArrow(src) {
    let inStr = false, at = -1;
    for (let i = 0; i < src.length; i++) {
      if (src[i] === '"') inStr = !inStr;
      else if (src[i] === '→') { at = i; inStr = false; }
    }
    return at;
  }

  function compileStatement(x) {
    const word = (w) => x === w;
    const starts = (w) => x.startsWith(w);
    if (word('ClrHome')) return { k: 'clr' };
    if (word('Then')) return { k: 'then' };
    if (word('Else')) return { k: 'else' };
    if (word('End')) return { k: 'end' };
    if (word('Stop') || word('Return')) return { k: 'stop' };
    if (word('Pause')) return { k: 'pause' };
    if (word('Disp')) return { k: 'disp', args: [] };
    if (starts('Lbl ')) {
      const name = x.slice(4).trim();
      if (!isLabel(name)) throw new TIError('SYNTAX');
      return { k: 'lbl', name };
    }
    if (starts('Goto ')) {
      const name = x.slice(5).trim();
      if (!isLabel(name)) throw new TIError('SYNTAX');
      return { k: 'goto', name };
    }
    if (starts('If ')) return { k: 'if', cond: compileExpr(x.slice(3)) };
    if (starts('While ')) return { k: 'while', cond: compileExpr(x.slice(6)) };
    if (starts('Repeat ')) return { k: 'repeat', cond: compileExpr(x.slice(7)) };
    if (starts('For(')) {
      const m = /^For\(\s*([A-Zθ])\s*,(.*)$/.exec(x);
      if (!m) throw new TIError('SYNTAX');
      const args = compileList(m[2]);
      if (args.length < 2 || args.length > 3) throw new TIError('ARGUMENT');
      return { k: 'for', v: m[1], from: args[0], to: args[1], step: args[2] };
    }
    if (starts('Pause ')) return { k: 'pause', arg: compileExpr(x.slice(6)) };
    if (starts('Wait ')) return { k: 'wait', arg: compileExpr(x.slice(5)) };
    if (starts('Disp ')) return { k: 'disp', args: compileList(x.slice(5)) };
    if (starts('Output(')) {
      const args = compileList(x.slice(7));
      if (args.length !== 3) throw new TIError('ARGUMENT');
      return { k: 'output', args };
    }
    if (starts('Menu(')) {
      const parts = splitArgs(x.slice(5));
      if (parts.length < 3 || parts.length % 2 === 0) throw new TIError('ARGUMENT');
      const items = [];
      for (let i = 1; i < parts.length; i += 2) {
        if (!isLabel(parts[i + 1])) throw new TIError('SYNTAX');
        items.push({ text: compileExpr(parts[i]), label: parts[i + 1] });
      }
      if (items.length > 7) throw new TIError('ARGUMENT');
      return { k: 'menu', title: compileExpr(parts[0]), items };
    }
    if (starts('Input ')) {
      const parts = splitArgs(x.slice(6));
      const target = parts[parts.length - 1];
      if (parts.length > 2 || !(isVar(target) || isStrVar(target))) throw new TIError('SYNTAX');
      return { k: 'input', prompt: parts.length === 2 ? compileExpr(parts[0]) : null, target };
    }
    if (starts('Prompt ')) {
      const vars = x.slice(7).split(',').map(s => s.trim());
      if (!vars.every(v => isVar(v) || isStrVar(v))) throw new TIError('SYNTAX');
      return { k: 'prompt', vars };
    }
    if (starts('DelVar ')) {
      const v = x.slice(7).trim();
      if (!(isVar(v) || isStrVar(v))) throw new TIError('SYNTAX');
      return { k: 'delvar', v };
    }
    const at = lastStoreArrow(x);
    if (at >= 0) {
      const target = x.slice(at + 1).trim();
      if (!(isVar(target) || isStrVar(target))) throw new TIError('SYNTAX');
      return { k: 'store', e: compileExpr(x.slice(0, at)), target };
    }
    return { k: 'expr', e: compileExpr(x) };
  }

  // Splits source into statements on newlines and on colons outside strings.
  function splitStatements(src) {
    const out = [];
    src.replace(/\r/g, '').replace(/->/g, '→').split('\n').forEach((line, ln) => {
      let cur = '', inStr = false;
      const push = () => { const s = cur.trim(); if (s) out.push({ src: s, line: ln }); cur = ''; };
      for (const ch of line) {
        if (ch === '"') inStr = !inStr;
        else if (ch === '→') inStr = false;
        if (ch === ':' && !inStr) push(); else cur += ch;
      }
      push();
    });
    return out;
  }

  class Program {
    constructor(src) {
      this.stmts = splitStatements(src).map(s => {
        let st;
        try { st = compileStatement(s.src); } catch (e) { st = { k: 'bad', err: e.kind || 'SYNTAX' }; }
        st.line = s.line;
        st.src = s.src;
        return st;
      });
      this.labels = {};
      this.stmts.forEach((s, i) => { if (s.k === 'lbl' && !(s.name in this.labels)) this.labels[s.name] = i; });
      // Pair each block opener with its Else and End.
      const S = this.stmts, open = [];
      S.forEach((s, i) => {
        if (s.k === 'if' && S[i + 1] && S[i + 1].k === 'then') { s.block = true; open.push(i); }
        else if (s.k === 'while' || s.k === 'repeat' || s.k === 'for') open.push(i);
        else if (s.k === 'else') {
          const o = open[open.length - 1];
          if (o !== undefined && S[o].k === 'if') { S[o].elseAt = i; s.open = o; }
        } else if (s.k === 'end') {
          const o = open.pop();
          if (o !== undefined) {
            s.open = o;
            S[o].endAt = i;
            if (S[o].elseAt !== undefined) S[S[o].elseAt].endAt = i;
          }
        }
      });
    }
  }

  /* ---------- Runner ---------- */

  const KEY = { LEFT: 24, UP: 25, RIGHT: 26, DOWN: 34, ENTER: 105, CLEAR: 45, DEL: 23 };
  const DIGIT_KEYS = { 92: 1, 93: 2, 94: 3, 82: 4, 83: 5, 84: 6, 72: 7, 73: 8, 74: 9 };

  class Runner {
    constructor(screen) {
      this.screen = screen;
      this.vars = {};
      this.strs = {};
      this.ans = 0;
      this.lastKey = 0;
      this.waiter = null;
      this.queue = [];
      this.mode = 'idle'; // idle | running | paused | waiting
      this.onMode = null;
    }
    setMode(m) { if (m !== this.mode) this.queue = []; this.mode = m; if (this.onMode) this.onMode(m); }
    readKey() { const k = this.lastKey; this.lastKey = 0; return k; }

    // key: { code, ch } — code is the TI getKey code, ch the character it types.
    press(key) {
      if (this.waiter) { const w = this.waiter; this.waiter = null; w(key); }
      else if (this.mode === 'waiting' || this.mode === 'paused') this.queue.push(key);
      else if (key.code) this.lastKey = key.code;
    }
    break() {
      this.broken = true;
      if (this.waiter) { const w = this.waiter; this.waiter = null; w('BREAK'); }
      if (this.cancelSleep) this.cancelSleep();
    }
    async waitKey() {
      if (this.broken) throw new TIError('BREAK');
      if (this.queue.length) return this.queue.shift();
      const k = await new Promise(res => { this.waiter = res; });
      if (k === 'BREAK') throw new TIError('BREAK');
      return k;
    }
    sleep(ms) {
      return new Promise((res, rej) => {
        const t = setTimeout(() => { this.cancelSleep = null; res(); }, ms);
        this.cancelSleep = () => { clearTimeout(t); this.cancelSleep = null; rej(new TIError('BREAK')); };
      });
    }

    // Runs a Program. Resolves with the last statement run; rejects with a TIError.
    async run(prog) {
      const S = prog.stmts;
      this.prog = prog;
      this.broken = false;
      this.stopped = false;
      this.lastKey = 0;
      this.pc = 0;
      let steps = 0, last = null;
      this.setMode('running');
      try {
        while (this.pc < S.length && !this.stopped) {
          const i = this.pc, s = S[i];
          if (this.broken) throw new TIError('BREAK', i);
          this.pc = i + 1;
          try {
            const r = this.exec(s, i, S, prog);
            if (r) await r;
          } catch (e) {
            if (e instanceof TIError) { if (e.stmt === undefined) e.stmt = i; throw e; }
            throw new TIError('SYNTAX', i);
          }
          last = s;
          // Let the page breathe so getKey loops can see key presses.
          if (++steps % 40 === 0) await this.sleep(0);
        }
        return last;
      } finally {
        this.waiter = null;
        this.setMode('idle');
      }
    }

    store(target, v) {
      if (isStrVar(target)) this.strs[target] = str(v);
      else this.vars[target] = num(v);
    }

    exec(s, i, S, prog) {
      const scr = this.screen;
      const skipTo = (at) => { this.pc = at === undefined ? S.length : at + 1; };
      switch (s.k) {
        case 'bad': throw new TIError(s.err);
        case 'clr': scr.clear(); return;
        case 'lbl': case 'then': return;
        case 'goto': {
          const at = prog.labels[s.name];
          if (at === undefined) throw new TIError('LABEL');
          this.pc = at + 1;
          return;
        }
        case 'if': {
          const ok = truth(s.cond(this));
          if (s.block) { if (ok) this.pc = i + 2; else skipTo(s.elseAt !== undefined ? s.elseAt : s.endAt); }
          else if (!ok) this.pc = i + 2;
          return;
        }
        case 'else': skipTo(s.endAt); return;
        case 'while': if (!truth(s.cond(this))) skipTo(s.endAt); return;
        case 'repeat': return;
        case 'for': {
          const from = num(s.from(this)), to = num(s.to(this)), step = s.step ? num(s.step(this)) : 1;
          this.vars[s.v] = from;
          if (step > 0 ? from > to : from < to) skipTo(s.endAt);
          return;
        }
        case 'end': {
          if (s.open === undefined) throw new TIError('SYNTAX');
          const o = S[s.open];
          if (o.k === 'while') this.pc = s.open;
          else if (o.k === 'repeat') { if (!truth(o.cond(this))) this.pc = s.open + 1; }
          else if (o.k === 'for') {
            const to = num(o.to(this)), step = o.step ? num(o.step(this)) : 1;
            const v = (this.vars[o.v] || 0) + step;
            this.vars[o.v] = v;
            if (step > 0 ? v <= to : v >= to) this.pc = s.open + 1;
          }
          return;
        }
        case 'stop': this.stopped = true; return;
        case 'disp':
          for (const e of s.args) {
            const v = e(this);
            scr.line(toText(v), typeof v === 'number');
          }
          return;
        case 'output': {
          const r = num(s.args[0](this)), c = num(s.args[1](this));
          if (!Number.isInteger(r) || !Number.isInteger(c) || r < 1 || r > ROWS || c < 1 || c > COLS) throw new TIError('DOMAIN');
          scr.write(r - 1, c - 1, toText(s.args[2](this)));
          return;
        }
        case 'pause': return this.pause(s);
        case 'wait': return this.sleep(Math.max(0, num(s.arg(this))) * 1000);
        case 'menu': return this.menu(s, prog);
        case 'input': return this.input(s.prompt ? toText(s.prompt(this)) : '?', s.target);
        case 'prompt': return (async () => { for (const v of s.vars) await this.input(v + '=?', v); })();
        case 'delvar': if (isStrVar(s.v)) delete this.strs[s.v]; else this.vars[s.v] = 0; return;
        case 'store': { const v = s.e(this); this.store(s.target, v); this.ans = v; return; }
        case 'expr': this.ans = s.e(this); return;
      }
      throw new TIError('SYNTAX');
    }

    async pause(s) {
      if (s.arg) {
        const v = s.arg(this);
        this.screen.line(toText(v), typeof v === 'number');
        this.ans = v;
      }
      this.setMode('paused');
      try {
        while ((await this.waitKey()).code !== KEY.ENTER) { /* only ENTER resumes */ }
      } finally { this.setMode('running'); }
    }

    async menu(s, prog) {
      const scr = this.screen;
      const title = toText(s.title(this));
      const items = s.items.map(it => ({ text: toText(it.text(this)), label: it.label }));
      const saved = scr.snapshot();
      let sel = 0;
      const draw = () => {
        scr.clear();
        for (let c = 0; c < 16; c++) scr.put(0, c, ' ', true);
        scr.write(0, 0, [...title].slice(0, 16).join(''), true);
        items.forEach((it, n) => {
          scr.write(n + 1, 0, (n + 1) + ':', n === sel);
          scr.write(n + 1, 2, [...it.text].slice(0, 14).join(''));
        });
      };
      draw();
      this.setMode('waiting');
      let chosen = null;
      try {
        while (chosen === null) {
          const k = await this.waitKey();
          if (k.code === KEY.UP) { sel = (sel + items.length - 1) % items.length; draw(); }
          else if (k.code === KEY.DOWN) { sel = (sel + 1) % items.length; draw(); }
          else if (k.code === KEY.ENTER) chosen = sel;
          else if (DIGIT_KEYS[k.code] && DIGIT_KEYS[k.code] <= items.length) chosen = DIGIT_KEYS[k.code] - 1;
        }
      } finally { this.setMode('running'); }
      scr.restore(saved);
      const at = prog.labels[items[chosen].label];
      if (at === undefined) throw new TIError('LABEL');
      this.pc = at + 1;
    }

    async input(prompt, target) {
      const scr = this.screen;
      const r = scr.nextLine();
      let text = '';
      const room = Math.max(1, 15 - [...prompt].length);
      const draw = () => {
        scr.clearRow(r);
        const shown = [...text].slice(-room).join('');
        scr.write(r, 0, prompt + shown);
        scr.cursor = { r, c: Math.min(15, [...prompt].length + [...shown].length) };
        scr.changed();
      };
      draw();
      this.setMode('waiting');
      try {
        for (;;) {
          const k = await this.waitKey();
          if (k.code === KEY.ENTER) {
            if (isStrVar(target)) { this.store(target, text); break; }
            if (text.trim() === '') continue;
            this.store(target, num(compileExpr(text)(this)));
            break;
          } else if (k.code === KEY.DEL) text = [...text].slice(0, -1).join('');
          else if (k.code === KEY.CLEAR) text = '';
          else if (k.ch) text += k.ch;
          draw();
        }
      } finally {
        scr.cursor = null;
        scr.changed();
        this.setMode('running');
      }
    }
  }

  global.TIBasic = { Screen, Program, Runner, TIError, fmtNum, toText, KEY, ROWS, COLS };
})(typeof window !== 'undefined' ? window : globalThis);
