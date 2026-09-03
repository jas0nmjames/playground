/**
 * Tokenizer for TI-83+ expressions.
 *
 * TI function names carry their opening paren as part of the token
 * ("sin(" not "sin"), so functions are matched name-first and the paren is
 * emitted separately. Longest-match ordering matters: "sin^-1(" must be
 * tried before "sin(", and "Ans" before the variable "A".
 */

// Longest first so prefixes never shadow longer names.
export const FUNCTIONS = [
  'sin⁻¹', 'cos⁻¹', 'tan⁻¹',
  'randInt', 'iPart', 'fPart', 'length', 'round', 'asin', 'acos', 'atan',
  'sinh', 'cosh', 'tanh', 'sqrt', 'abs', 'int', 'max', 'min', 'gcd', 'lcm',
  'not', 'sub', 'sin', 'cos', 'tan', 'ln', 'log', '√',
];

const OPERATORS = [
  'and', 'xor', 'or',
  '->', '→', '<=', '≤', '>=', '≥', '!=', '≠', '=/=',
  '+', '-', '−', '*', '×', '/', '÷', '^', '=', '<', '>',
];

// Canonical spelling for operators that have several input forms.
const OP_ALIAS = {
  '->': '→', '−': '-', '×': '*', '÷': '/',
  '<=': '≤', '>=': '≥', '!=': '≠', '=/=': '≠',
};

const FUNC_ALIAS = {
  sqrt: '√', 'sin⁻¹': 'asin', 'cos⁻¹': 'acos', 'tan⁻¹': 'atan',
};

export class TokenizeError extends Error {}

export function tokenize(src) {
  const tokens = [];
  let i = 0;

  const push = (type, value) => tokens.push({ type, value, pos: i });

  while (i < src.length) {
    const c = src[i];

    if (c === ' ' || c === '\t') {
      i++;
      continue;
    }

    // String literal. An unterminated string runs to end of line, which is
    // what the TI does when you omit the closing quote.
    if (c === '"') {
      let j = i + 1;
      let out = '';
      while (j < src.length && src[j] !== '"') out += src[j++];
      push('str', out);
      i = j < src.length ? j + 1 : j;
      continue;
    }

    // Number, including E-notation exponents (1E5, 2.5E-3).
    if (/[0-9]/.test(c) || (c === '.' && /[0-9]/.test(src[i + 1] || ''))) {
      let j = i;
      let text = '';
      while (j < src.length && /[0-9.]/.test(src[j])) text += src[j++];
      if (src[j] === 'E' && /[0-9+\-]/.test(src[j + 1] || '')) {
        text += src[j++];
        if (/[+\-]/.test(src[j])) text += src[j++];
        while (j < src.length && /[0-9]/.test(src[j])) text += src[j++];
      }
      const value = parseFloat(text);
      if (Number.isNaN(value)) throw new TokenizeError(`SYNTAX: ${text}`);
      push('num', value);
      i = j;
      continue;
    }

    // Ans must beat the variable A.
    if (src.startsWith('Ans', i)) {
      push('ans', 'Ans');
      i += 3;
      continue;
    }

    // Str1..Str9 must beat the variable S.
    if (src.startsWith('Str', i) && /[1-9]/.test(src[i + 3] || '')) {
      push('strvar', parseInt(src[i + 3], 10));
      i += 4;
      continue;
    }

    // Y1..Y9 must beat the variable Y.
    if (c === 'Y' && /[1-9]/.test(src[i + 1] || '')) {
      push('yvar', parseInt(src[i + 1], 10));
      i += 2;
      continue;
    }

    // e^( and 10^( are single tokens on the real keypad.
    if (src.startsWith('e^(', i)) {
      push('func', 'exp');
      push('lparen', '(');
      i += 3;
      continue;
    }
    if (src.startsWith('10^(', i)) {
      push('func', 'tenpow');
      push('lparen', '(');
      i += 4;
      continue;
    }

    // getKey reads the last key pressed; it is a value, not a call.
    if (src.startsWith('getKey', i)) {
      push('getkey', 'getKey');
      i += 6;
      continue;
    }

    // Named functions; the '(' is emitted as its own token.
    let matchedFunc = null;
    for (const fn of FUNCTIONS) {
      if (src.startsWith(fn, i)) {
        matchedFunc = fn;
        break;
      }
    }
    if (matchedFunc) {
      push('func', FUNC_ALIAS[matchedFunc] || matchedFunc);
      i += matchedFunc.length;
      if (src[i] === '(') {
        push('lparen', '(');
        i++;
      }
      continue;
    }

    if (src.startsWith('pi', i) || c === 'π') {
      push('const', 'π');
      i += c === 'π' ? 1 : 2;
      continue;
    }

    if (c === 'e') {
      push('const', 'e');
      i++;
      continue;
    }

    if (/[A-Z]/.test(c) || c === 'θ') {
      push('var', c);
      i++;
      continue;
    }

    if (c === '(') { push('lparen', '('); i++; continue; }
    if (c === ')') { push('rparen', ')'); i++; continue; }
    if (c === ',') { push('comma', ','); i++; continue; }
    if (c === '²') { push('post', '²'); i++; continue; }
    if (c === '!') {
      // '!' is factorial unless it starts the '!=' operator.
      if (src[i + 1] !== '=') { push('post', '!'); i++; continue; }
    }
    if (src.startsWith('⁻¹', i)) { push('post', '⁻¹'); i += 2; continue; }

    let matchedOp = null;
    for (const op of OPERATORS) {
      if (src.startsWith(op, i)) {
        matchedOp = op;
        break;
      }
    }
    if (matchedOp) {
      push('op', OP_ALIAS[matchedOp] || matchedOp);
      i += matchedOp.length;
      continue;
    }

    throw new TokenizeError(`SYNTAX: ${c}`);
  }

  tokens.push({ type: 'eof', value: null, pos: i });
  return tokens;
}
