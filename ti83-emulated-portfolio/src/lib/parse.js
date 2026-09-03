/**
 * Recursive-descent parser for TI-83+ expressions.
 *
 * The one genuinely TI-specific wrinkle is implicit multiplication: 2X,
 * 3(X+1) and Asin(B) all multiply. Implicit products bind at the same
 * precedence as an explicit *, which is how the 83+ (unlike the 85) does it,
 * so 1/2X evaluates as (1/2)*X.
 */

import { tokenize } from './tokenize.js';

export class ParseError extends Error {}

// Tokens that can begin a value, and therefore can follow another value as an
// implicit multiplication.
const VALUE_START = new Set([
  'num', 'var', 'strvar', 'yvar', 'const', 'func', 'lparen', 'ans', 'getkey',
]);

class Parser {
  constructor(tokens) {
    this.tokens = tokens;
    this.i = 0;
  }

  peek(offset = 0) {
    return this.tokens[this.i + offset];
  }

  next() {
    return this.tokens[this.i++];
  }

  at(type, value) {
    const t = this.peek();
    return t.type === type && (value === undefined || t.value === value);
  }

  eat(type, value) {
    if (this.at(type, value)) {
      this.i++;
      return true;
    }
    return false;
  }

  expect(type, message) {
    if (!this.at(type)) throw new ParseError(message || 'SYNTAX');
    return this.next();
  }

  parseExpression() {
    return this.parseOr();
  }

  parseOr() {
    let left = this.parseAnd();
    while (this.at('op', 'or') || this.at('op', 'xor')) {
      const op = this.next().value;
      left = { t: 'bin', op, l: left, r: this.parseAnd() };
    }
    return left;
  }

  parseAnd() {
    let left = this.parseComparison();
    while (this.at('op', 'and')) {
      this.next();
      left = { t: 'bin', op: 'and', l: left, r: this.parseComparison() };
    }
    return left;
  }

  parseComparison() {
    let left = this.parseAdditive();
    while (
      this.at('op', '=') || this.at('op', '≠') || this.at('op', '<') ||
      this.at('op', '>') || this.at('op', '≤') || this.at('op', '≥')
    ) {
      const op = this.next().value;
      left = { t: 'bin', op, l: left, r: this.parseAdditive() };
    }
    return left;
  }

  parseAdditive() {
    let left = this.parseMultiplicative();
    while (this.at('op', '+') || this.at('op', '-')) {
      const op = this.next().value;
      left = { t: 'bin', op, l: left, r: this.parseMultiplicative() };
    }
    return left;
  }

  parseMultiplicative() {
    let left = this.parseUnary();
    for (;;) {
      if (this.at('op', '*') || this.at('op', '/')) {
        const op = this.next().value;
        left = { t: 'bin', op, l: left, r: this.parseUnary() };
        continue;
      }
      // Implicit multiplication: a value token directly follows a value.
      // Two adjacent numbers ("2 3") are a syntax error on hardware, not a
      // product, so those are excluded.
      const t = this.peek();
      if (VALUE_START.has(t.type) && t.type !== 'num') {
        left = { t: 'bin', op: '*', l: left, r: this.parseUnary() };
        continue;
      }
      return left;
    }
  }

  parseUnary() {
    if (this.at('op', '-')) {
      this.next();
      return { t: 'un', op: '-', x: this.parseUnary() };
    }
    return this.parsePower();
  }

  parsePower() {
    const base = this.parsePostfix();
    if (this.at('op', '^')) {
      this.next();
      // Right-associative, and the exponent may itself be negated: 2^-3.
      return { t: 'bin', op: '^', l: base, r: this.parseUnary() };
    }
    return base;
  }

  parsePostfix() {
    let x = this.parsePrimary();
    while (this.at('post')) {
      const op = this.next().value;
      x = { t: 'post', op, x };
    }
    return x;
  }

  parsePrimary() {
    const t = this.peek();

    switch (t.type) {
      case 'num':
        this.next();
        return { t: 'num', v: t.value };
      case 'str':
        this.next();
        return { t: 'str', v: t.value };
      case 'var':
        this.next();
        return { t: 'var', name: t.value };
      case 'strvar':
        this.next();
        return { t: 'strvar', n: t.value };
      case 'yvar':
        this.next();
        return { t: 'yvar', n: t.value };
      case 'ans':
        this.next();
        return { t: 'ans' };
      case 'getkey':
        this.next();
        return { t: 'getkey' };
      case 'const':
        this.next();
        return { t: 'const', name: t.value };
      case 'lparen': {
        this.next();
        const inner = this.parseExpression();
        // A missing ')' closes implicitly at end of expression, as on the TI.
        this.eat('rparen');
        return inner;
      }
      case 'func': {
        this.next();
        const args = [];
        if (this.eat('lparen')) {
          if (!this.at('rparen') && !this.at('eof')) {
            args.push(this.parseExpression());
            while (this.eat('comma')) args.push(this.parseExpression());
          }
          this.eat('rparen');
        } else {
          // Bare "sin X" — the TI tolerates the missing paren.
          args.push(this.parseUnary());
        }
        return { t: 'call', name: t.value, args };
      }
      default:
        throw new ParseError('SYNTAX');
    }
  }
}

/** Parse a full expression string into an AST. Throws ParseError/TokenizeError. */
export function parseExpression(src) {
  const parser = new Parser(tokenize(src));
  const ast = parser.parseExpression();
  if (!parser.at('eof')) throw new ParseError('SYNTAX');
  return ast;
}

const cache = new Map();

/** Parse with memoization — graphing re-parses the same Y= text every frame. */
export function parseCached(src) {
  if (cache.has(src)) return cache.get(src);
  const ast = parseExpression(src);
  cache.set(src, ast);
  return ast;
}
