/**
 * AST evaluator.
 *
 * Values are either numbers or strings; string support exists so Str1-Str9
 * and Disp "TEXT" work in TI-BASIC programs. Comparison and logic operators
 * return 1 or 0, matching the calculator.
 */

import { parseCached } from './parse.js';

export class MathError extends Error {}

const DEG = Math.PI / 180;

/**
 * Evaluation context.
 *
 * vars     — A-Z and θ
 * strs     — Str1..Str9
 * yvars    — Y1..Y9 as source text, parsed on demand
 * ans      — last answer
 * angleDeg — true in Degree mode
 */
export function createContext(overrides = {}) {
  return {
    vars: {},
    strs: {},
    yvars: {},
    ans: 0,
    angleDeg: false,
    depth: 0,
    ...overrides,
  };
}

function num(v) {
  if (typeof v !== 'number') throw new MathError('DATA TYPE');
  return v;
}

function str(v) {
  if (typeof v !== 'string') throw new MathError('DATA TYPE');
  return v;
}

function bool(b) {
  return b ? 1 : 0;
}

function factorial(n) {
  if (n < 0 || n !== Math.floor(n) || n > 69) throw new MathError('DOMAIN');
  let out = 1;
  for (let i = 2; i <= n; i++) out *= i;
  return out;
}

function gcd2(a, b) {
  a = Math.abs(Math.round(a));
  b = Math.abs(Math.round(b));
  while (b) [a, b] = [b, a % b];
  return a;
}

const FUNCS = {
  sin: (ctx, x) => Math.sin(ctx.angleDeg ? x * DEG : x),
  cos: (ctx, x) => Math.cos(ctx.angleDeg ? x * DEG : x),
  tan: (ctx, x) => Math.tan(ctx.angleDeg ? x * DEG : x),
  asin: (ctx, x) => {
    if (x < -1 || x > 1) throw new MathError('DOMAIN');
    return ctx.angleDeg ? Math.asin(x) / DEG : Math.asin(x);
  },
  acos: (ctx, x) => {
    if (x < -1 || x > 1) throw new MathError('DOMAIN');
    return ctx.angleDeg ? Math.acos(x) / DEG : Math.acos(x);
  },
  atan: (ctx, x) => (ctx.angleDeg ? Math.atan(x) / DEG : Math.atan(x)),
  sinh: (_c, x) => Math.sinh(x),
  cosh: (_c, x) => Math.cosh(x),
  tanh: (_c, x) => Math.tanh(x),
  ln: (_c, x) => {
    if (x <= 0) throw new MathError('DOMAIN');
    return Math.log(x);
  },
  log: (_c, x) => {
    if (x <= 0) throw new MathError('DOMAIN');
    return Math.log10(x);
  },
  exp: (_c, x) => Math.exp(x),
  tenpow: (_c, x) => Math.pow(10, x),
  '√': (_c, x) => {
    if (x < 0) throw new MathError('DOMAIN');
    return Math.sqrt(x);
  },
  abs: (_c, x) => Math.abs(x),
  int: (_c, x) => Math.floor(x),
  iPart: (_c, x) => Math.trunc(x),
  fPart: (_c, x) => x - Math.trunc(x),
  not: (_c, x) => bool(x === 0),
};

export function evaluate(node, ctx) {
  switch (node.t) {
    case 'num':
      return node.v;

    case 'str':
      return node.v;

    case 'const':
      return node.name === 'π' ? Math.PI : Math.E;

    case 'ans':
      return ctx.ans;

    case 'getkey': {
      // Reads once and clears, so a polling loop sees each press exactly once.
      const k = ctx.getKey || 0;
      ctx.getKey = 0;
      return k;
    }

    case 'var': {
      const v = ctx.vars[node.name];
      return v === undefined ? 0 : v;
    }

    case 'strvar': {
      const v = ctx.strs[node.n];
      return v === undefined ? '' : v;
    }

    case 'yvar': {
      const src = ctx.yvars[node.n];
      if (!src) return 0;
      // Guard against Y1=Y2, Y2=Y1 style cycles.
      if (ctx.depth > 16) throw new MathError('MEMORY');
      ctx.depth++;
      try {
        return evaluate(parseCached(src), ctx);
      } finally {
        ctx.depth--;
      }
    }

    case 'un':
      return -num(evaluate(node.x, ctx));

    case 'post': {
      const x = evaluate(node.x, ctx);
      if (node.op === '²') return num(x) * num(x);
      if (node.op === '!') return factorial(num(x));
      if (node.op === '⁻¹') {
        if (num(x) === 0) throw new MathError('DIVIDE BY 0');
        return 1 / x;
      }
      throw new MathError('SYNTAX');
    }

    case 'bin': {
      const l = evaluate(node.l, ctx);
      const r = evaluate(node.r, ctx);

      // '+' is overloaded for string concatenation.
      if (node.op === '+' && (typeof l === 'string' || typeof r === 'string')) {
        return str(l) + str(r);
      }
      // Equality works on strings too.
      if (typeof l === 'string' || typeof r === 'string') {
        if (node.op === '=') return bool(l === r);
        if (node.op === '≠') return bool(l !== r);
        throw new MathError('DATA TYPE');
      }

      const a = num(l);
      const b = num(r);
      switch (node.op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/':
          if (b === 0) throw new MathError('DIVIDE BY 0');
          return a / b;
        case '^': {
          const out = Math.pow(a, b);
          if (Number.isNaN(out)) throw new MathError('DOMAIN');
          return out;
        }
        case '=': return bool(a === b);
        case '≠': return bool(a !== b);
        case '<': return bool(a < b);
        case '>': return bool(a > b);
        case '≤': return bool(a <= b);
        case '≥': return bool(a >= b);
        case 'and': return bool(a !== 0 && b !== 0);
        case 'or': return bool(a !== 0 || b !== 0);
        case 'xor': return bool((a !== 0) !== (b !== 0));
        default: throw new MathError('SYNTAX');
      }
    }

    case 'call': {
      const { name, args } = node;

      // Variadic and string functions are handled before the unary table.
      if (name === 'max' || name === 'min') {
        const vals = args.map((a) => num(evaluate(a, ctx)));
        if (!vals.length) throw new MathError('ARGUMENT');
        return name === 'max' ? Math.max(...vals) : Math.min(...vals);
      }
      if (name === 'round') {
        const x = num(evaluate(args[0], ctx));
        const d = args.length > 1 ? num(evaluate(args[1], ctx)) : 9;
        const f = Math.pow(10, d);
        return Math.round(x * f) / f;
      }
      if (name === 'gcd' || name === 'lcm') {
        const a = num(evaluate(args[0], ctx));
        const b = num(evaluate(args[1], ctx));
        const g = gcd2(a, b);
        return name === 'gcd' ? g : g === 0 ? 0 : Math.abs(a * b) / g;
      }
      if (name === 'randInt') {
        const lo = num(evaluate(args[0], ctx));
        const hi = num(evaluate(args[1], ctx));
        return lo + Math.floor(Math.random() * (hi - lo + 1));
      }
      if (name === 'sub') {
        const s = str(evaluate(args[0], ctx));
        const start = num(evaluate(args[1], ctx));
        const len = num(evaluate(args[2], ctx));
        return s.substr(start - 1, len);
      }
      if (name === 'length') {
        const v = evaluate(args[0], ctx);
        return typeof v === 'string' ? v.length : String(v).length;
      }

      const fn = FUNCS[name];
      if (!fn) throw new MathError('SYNTAX');
      if (!args.length) throw new MathError('ARGUMENT');
      return fn(ctx, num(evaluate(args[0], ctx)));
    }

    default:
      throw new MathError('SYNTAX');
  }
}
