/**
 * TI-BASIC compiler and runtime.
 *
 * Programs compile to a flat statement array with jump targets resolved up
 * front, executed against a program counter. That shape (rather than a tree
 * walk) is what makes Goto/Lbl work naturally — and Goto is load-bearing in
 * real TI-BASIC, since Menu( dispatches to labels.
 *
 * Execution is a generator that yields effects the host must service:
 *   {type:'pause'}                 → resume when the user presses ENTER
 *   {type:'input', prompt}         → resume with the typed string
 *   {type:'menu', title, items}    → resume with the chosen label name
 *   {type:'tick'}                  → yield to the browser, resume immediately
 *   {type:'done'} / {type:'error'} → terminal
 *
 * The host repaints ctx.screen between resumes, so Disp output animates
 * instead of arriving all at once.
 */

import { parseExpression } from './parse.js';
import { evaluate, MathError } from './evaluate.js';
import { formatNumber } from './format.js';
import { clearHome, dispLine, outputAt } from './screen.js';

export class BasicError extends Error {}

/** Split on a delimiter, ignoring occurrences inside strings or parens. */
export function splitTop(text, delim) {
  const parts = [];
  let depth = 0;
  let inStr = false;
  let cur = '';
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      inStr = !inStr;
      cur += c;
      continue;
    }
    if (!inStr) {
      if (c === '(') depth++;
      else if (c === ')') depth--;
      if (depth === 0 && text.startsWith(delim, i)) {
        parts.push(cur);
        cur = '';
        i += delim.length - 1;
        continue;
      }
    }
    cur += c;
  }
  parts.push(cur);
  return parts;
}

/** Break program source into one statement per entry. */
function splitStatements(source) {
  const out = [];
  for (const line of source.split('\n')) {
    for (const stmt of splitTop(line, ':')) {
      out.push(stmt.trim());
    }
  }
  return out;
}

/** Strip a leading keyword, returning the remainder, or null if absent. */
function keyword(text, kw) {
  if (text === kw) return '';
  if (text.startsWith(kw)) {
    const rest = text.slice(kw.length);
    // "Disp X" and "For(A,1,5)" match; "Display" and "Ending" must not.
    if (rest[0] === ' ' || rest[0] === '(' || rest[0] === '"') return rest.trim();
  }
  return null;
}

/** Contents of a trailing "(...)" argument list. */
function parenArgs(text) {
  const open = text.indexOf('(');
  if (open === -1) return [];
  let close = text.lastIndexOf(')');
  if (close === -1) close = text.length;
  const inner = text.slice(open + 1, close);
  return inner.trim() === '' ? [] : splitTop(inner, ',').map((s) => s.trim());
}

function parseStatement(text) {
  const t = text.trim();
  if (t === '' || t.startsWith('//')) return { type: 'Nop', src: t };

  let rest;

  if (t === 'ClrHome') return { type: 'ClrHome', src: t };
  if (t === 'ClrDraw') return { type: 'ClrDraw', src: t };
  if (t === 'Then') return { type: 'Then', src: t };
  if (t === 'Else') return { type: 'Else', src: t };
  if (t === 'End') return { type: 'End', src: t };
  if (t === 'Stop') return { type: 'Stop', src: t };
  if (t === 'Return') return { type: 'Return', src: t };

  if ((rest = keyword(t, 'Disp')) !== null) {
    return { type: 'Disp', args: splitTop(rest, ',').map((s) => s.trim()).filter(Boolean), src: t };
  }
  if ((rest = keyword(t, 'Output')) !== null) {
    const a = parenArgs(t);
    if (a.length < 3) throw new BasicError('ARGUMENT');
    return { type: 'Output', row: a[0], col: a[1], value: a[2], src: t };
  }
  if ((rest = keyword(t, 'Pause')) !== null) {
    return { type: 'Pause', value: rest || null, src: t };
  }
  if ((rest = keyword(t, 'Input')) !== null) {
    const a = splitTop(rest, ',').map((s) => s.trim());
    if (a.length === 1) return { type: 'Input', prompt: null, target: a[0], src: t };
    return { type: 'Input', prompt: a[0], target: a[1], src: t };
  }
  if ((rest = keyword(t, 'Prompt')) !== null) {
    return { type: 'Prompt', targets: splitTop(rest, ',').map((s) => s.trim()), src: t };
  }
  if ((rest = keyword(t, 'Menu')) !== null) {
    const a = parenArgs(t);
    if (a.length < 3) throw new BasicError('ARGUMENT');
    const items = [];
    for (let i = 1; i + 1 < a.length; i += 2) {
      items.push({ label: a[i], lbl: a[i + 1] });
    }
    return { type: 'Menu', title: a[0], items, src: t };
  }
  if ((rest = keyword(t, 'Lbl')) !== null) return { type: 'Lbl', name: rest, src: t };
  if ((rest = keyword(t, 'Goto')) !== null) return { type: 'Goto', name: rest, src: t };
  if ((rest = keyword(t, 'If')) !== null) return { type: 'If', cond: rest, src: t };
  if ((rest = keyword(t, 'While')) !== null) return { type: 'While', cond: rest, src: t };
  if ((rest = keyword(t, 'Repeat')) !== null) return { type: 'Repeat', cond: rest, src: t };
  if ((rest = keyword(t, 'DelVar')) !== null) return { type: 'DelVar', name: rest, src: t };
  if ((rest = keyword(t, 'For')) !== null) {
    const a = parenArgs(t);
    if (a.length < 3) throw new BasicError('ARGUMENT');
    return { type: 'For', varName: a[0], start: a[1], limit: a[2], step: a[3] || null, src: t };
  }

  // Assignment: <expr>→<target>
  const stored = splitTop(t, '→');
  if (stored.length === 2) {
    return { type: 'Store', value: stored[0].trim(), target: stored[1].trim(), src: t };
  }

  return { type: 'Expr', value: t, src: t };
}

/** Resolve block structure: match If/Then/Else/End, For/End, While/End, Repeat/End. */
function link(stmts) {
  const stack = [];

  stmts.forEach((s, idx) => {
    switch (s.type) {
      case 'If':
        // An If only opens a block when Then is the very next statement.
        s.hasThen = stmts[idx + 1] && stmts[idx + 1].type === 'Then';
        if (s.hasThen) stack.push({ kind: 'if', node: s, idx });
        break;

      case 'Else': {
        const top = stack[stack.length - 1];
        if (!top || top.kind !== 'if') throw new BasicError('SYNTAX: Else');
        top.node.elseIdx = idx;
        top.elseNode = s;
        break;
      }

      case 'For':
      case 'While':
      case 'Repeat':
        stack.push({ kind: s.type.toLowerCase(), node: s, idx });
        break;

      case 'End': {
        const top = stack.pop();
        if (!top) throw new BasicError('SYNTAX: End');
        top.node.endIdx = idx;
        if (top.elseNode) top.elseNode.endIdx = idx;
        s.opens = top.idx;
        s.kind = top.kind;
        break;
      }

      default:
        break;
    }
  });

  if (stack.length) throw new BasicError('SYNTAX: missing End');
}

export function compile(source) {
  const stmts = splitStatements(source).map(parseStatement);
  link(stmts);

  const labels = {};
  stmts.forEach((s, i) => {
    if (s.type === 'Lbl') labels[s.name] = i;
  });

  return { stmts, labels, source };
}

/** Evaluate a source fragment in the program's context. */
function evalText(text, ctx) {
  return evaluate(parseExpression(text), ctx);
}

function displayValue(screen, value) {
  if (typeof value === 'string') dispLine(screen, value, false);
  else dispLine(screen, formatNumber(value), true);
}

export function storeInto(target, value, ctx) {
  const m = /^Str([1-9])$/.exec(target);
  if (m) {
    ctx.strs[Number(m[1])] = typeof value === 'string' ? value : formatNumber(value);
    return;
  }
  const y = /^Y([1-9])$/.exec(target);
  if (y) {
    ctx.yvars[Number(y[1])] = String(value);
    return;
  }
  if (/^[A-Zθ]$/.test(target)) {
    ctx.vars[target] = value;
    return;
  }
  throw new BasicError('DATA TYPE');
}

const STEPS_PER_TICK = 400;

/**
 * Run a compiled program. Drive it with .next(resumeValue) until done.
 */
export function* run(program, ctx) {
  const { stmts, labels } = program;
  const forState = {};
  let pc = 0;
  let steps = 0;

  const jumpToLabel = (name) => {
    if (!(name in labels)) throw new BasicError(`LABEL ${name}`);
    return labels[name];
  };

  try {
    while (pc < stmts.length) {
      // Keep the browser responsive and stop a runaway loop from hanging it.
      if (++steps % STEPS_PER_TICK === 0) yield { type: 'tick' };

      const s = stmts[pc];

      switch (s.type) {
        case 'Nop':
        case 'Lbl':
        case 'Then':
          pc++;
          break;

        case 'ClrHome':
          clearHome(ctx.screen);
          pc++;
          break;

        case 'ClrDraw':
          ctx.clearDraw?.();
          pc++;
          break;

        case 'Disp':
          for (const arg of s.args) displayValue(ctx.screen, evalText(arg, ctx));
          yield { type: 'render' };
          pc++;
          break;

        case 'Output': {
          const v = evalText(s.value, ctx);
          const text = typeof v === 'string' ? v : formatNumber(v);
          outputAt(ctx.screen, evalText(s.row, ctx), evalText(s.col, ctx), text);
          yield { type: 'render' };
          pc++;
          break;
        }

        case 'Pause':
          if (s.value) displayValue(ctx.screen, evalText(s.value, ctx));
          yield { type: 'pause' };
          pc++;
          break;

        case 'Input': {
          const prompt = s.prompt ? String(evalText(s.prompt, ctx)) : '?';
          const entered = yield { type: 'input', prompt, target: s.target };
          const isStr = /^Str[1-9]$/.test(s.target);
          storeInto(s.target, isStr ? entered : evalText(entered || '0', ctx), ctx);
          pc++;
          break;
        }

        case 'Prompt': {
          for (const target of s.targets) {
            const entered = yield { type: 'input', prompt: `${target}=`, target };
            const isStr = /^Str[1-9]$/.test(target);
            storeInto(target, isStr ? entered : evalText(entered || '0', ctx), ctx);
          }
          pc++;
          break;
        }

        case 'Menu': {
          const title = String(evalText(s.title, ctx));
          const items = s.items.map((it) => ({
            label: String(evalText(it.label, ctx)),
            lbl: it.lbl,
          }));
          const chosen = yield { type: 'menu', title, items };
          pc = jumpToLabel(chosen);
          break;
        }

        case 'Goto':
          pc = jumpToLabel(s.name);
          break;

        case 'If': {
          const truthy = evalText(s.cond, ctx) !== 0;
          if (s.hasThen) {
            if (truthy) pc += 2; // skip the Then
            else pc = (s.elseIdx != null ? s.elseIdx : s.endIdx) + 1;
          } else {
            pc += truthy ? 1 : 2; // skip the single controlled statement
          }
          break;
        }

        case 'Else':
          // Reached only by falling out of the Then branch.
          pc = s.endIdx + 1;
          break;

        case 'For': {
          const start = evalText(s.start, ctx);
          const limit = evalText(s.limit, ctx);
          const step = s.step ? evalText(s.step, ctx) : 1;
          ctx.vars[s.varName] = start;
          forState[pc] = { limit, step };
          const ok = step > 0 ? start <= limit : start >= limit;
          pc = ok ? pc + 1 : s.endIdx + 1;
          break;
        }

        case 'While':
          pc = evalText(s.cond, ctx) !== 0 ? pc + 1 : s.endIdx + 1;
          break;

        case 'Repeat':
          pc++;
          break;

        case 'End': {
          if (s.kind === 'for') {
            const open = stmts[s.opens];
            const st = forState[s.opens] || { limit: 0, step: 1 };
            const next = (ctx.vars[open.varName] || 0) + st.step;
            ctx.vars[open.varName] = next;
            const ok = st.step > 0 ? next <= st.limit : next >= st.limit;
            pc = ok ? s.opens + 1 : pc + 1;
          } else if (s.kind === 'while') {
            pc = s.opens; // re-test
          } else if (s.kind === 'repeat') {
            const open = stmts[s.opens];
            pc = evalText(open.cond, ctx) !== 0 ? pc + 1 : s.opens + 1;
          } else {
            pc++;
          }
          break;
        }

        case 'DelVar':
          delete ctx.vars[s.name];
          pc++;
          break;

        case 'Store': {
          const v = evalText(s.value, ctx);
          storeInto(s.target, v, ctx);
          if (typeof v === 'number') ctx.ans = v;
          pc++;
          break;
        }

        case 'Expr': {
          const v = evalText(s.value, ctx);
          if (typeof v === 'number') ctx.ans = v;
          displayValue(ctx.screen, v);
          yield { type: 'render' };
          pc++;
          break;
        }

        case 'Stop':
        case 'Return':
          return { type: 'done' };

        default:
          throw new BasicError('SYNTAX');
      }
    }
  } catch (err) {
    const message =
      err instanceof MathError || err instanceof BasicError
        ? err.message
        : err?.message || 'SYNTAX';
    return { type: 'error', message };
  }

  return { type: 'done' };
}
