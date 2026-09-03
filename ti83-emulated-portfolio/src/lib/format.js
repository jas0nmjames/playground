/**
 * TI-83+ number formatting.
 *
 * The calculator carries 14 digits internally but displays 10 significant
 * digits, drops the leading zero on values below 1, and switches to
 * scientific notation outside [1e-3, 1e10).
 */

const MAX_SIG = 10;

/** Trim trailing zeros from a decimal string, then a trailing point. */
function trim(s) {
  if (!s.includes('.')) return s;
  return s.replace(/0+$/, '').replace(/\.$/, '');
}

/** Drop the leading zero the way the TI does: 0.5 displays as .5 */
function dropLeadingZero(s) {
  if (s.startsWith('0.')) return s.slice(1);
  if (s.startsWith('-0.')) return '-' + s.slice(2);
  return s;
}

export function formatNumber(x) {
  if (typeof x === 'string') return x;
  if (Number.isNaN(x)) return 'ERR';
  if (!Number.isFinite(x)) return x > 0 ? '1E99' : '-1E99';
  if (x === 0) return '0';

  const ax = Math.abs(x);

  if (ax >= 1e10 || ax < 1e-3) {
    let exp = Math.floor(Math.log10(ax));
    let mant = x / Math.pow(10, exp);
    // log10 rounding can push the mantissa out of [1, 10)
    if (Math.abs(mant) >= 10) {
      mant /= 10;
      exp += 1;
    } else if (Math.abs(mant) < 1) {
      mant *= 10;
      exp -= 1;
    }
    let ms = trim(mant.toPrecision(MAX_SIG));
    // Rounding the mantissa itself can carry into the next decade
    if (Math.abs(parseFloat(ms)) >= 10) {
      ms = trim((parseFloat(ms) / 10).toPrecision(MAX_SIG));
      exp += 1;
    }
    return `${ms}E${exp}`;
  }

  let s = x.toPrecision(MAX_SIG);
  if (s.includes('e')) s = x.toFixed(MAX_SIG);
  return dropLeadingZero(trim(s));
}

/** Right-align a value inside the 16-column display, TI style. */
export function alignRight(text, width = 16) {
  if (text.length >= width) return text.slice(0, width);
  return ' '.repeat(width - text.length) + text;
}

/** Hard-wrap text into fixed-width display rows. */
export function wrap(text, width = 16) {
  if (text === '') return [''];
  const out = [];
  for (let i = 0; i < text.length; i += width) {
    out.push(text.slice(i, i + width));
  }
  return out;
}
