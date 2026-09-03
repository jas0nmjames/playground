/**
 * Graphing: sampling and pixel mapping for the 96x64 LCD.
 *
 * One sample per pixel column, exactly as the hardware does — which is why
 * a TI graph of tan(X) shows near-vertical connecting segments at the
 * asymptotes rather than a clean break.
 */

import { parseCached } from './parse.js';
import { evaluate } from './evaluate.js';

export const GRAPH_W = 96;
export const GRAPH_H = 64;

export const DEFAULT_WINDOW = {
  xmin: -10, xmax: 10, xscl: 1,
  ymin: -10, ymax: 10, yscl: 1,
};

/** Real x for a pixel column. */
export function xAt(px, win) {
  return win.xmin + (px * (win.xmax - win.xmin)) / (GRAPH_W - 1);
}

/** Pixel column for a real x (may fall outside the screen). */
export function pxAt(x, win) {
  return ((x - win.xmin) / (win.xmax - win.xmin)) * (GRAPH_W - 1);
}

/** Pixel row for a real y; row 0 is the top of the screen. */
export function pyAt(y, win) {
  return ((win.ymax - y) / (win.ymax - win.ymin)) * (GRAPH_H - 1);
}

/** Real y for a pixel row. */
export function yAt(py, win) {
  return win.ymax - (py * (win.ymax - win.ymin)) / (GRAPH_H - 1);
}

/**
 * Sample one function across every pixel column.
 * Returns an array of {x, y, py} or null where the function is undefined.
 */
export function samplePlot(source, win, ctx) {
  const out = new Array(GRAPH_W);
  const savedX = ctx.vars.X;

  for (let px = 0; px < GRAPH_W; px++) {
    const x = xAt(px, win);
    ctx.vars.X = x;
    let y;
    try {
      y = evaluate(parseCached(source), ctx);
    } catch {
      out[px] = null;
      continue;
    }
    out[px] = typeof y === 'number' && Number.isFinite(y) ? { x, y, py: pyAt(y, win) } : null;
  }

  ctx.vars.X = savedX;
  return out;
}

/** Tick positions along each axis, in pixel coordinates. */
export function axisTicks(win) {
  const xTicks = [];
  const yTicks = [];

  if (win.xscl > 0) {
    const span = win.xmax - win.xmin;
    // Guard against a tiny scale producing thousands of ticks.
    if (span / win.xscl <= 200) {
      const start = Math.ceil(win.xmin / win.xscl) * win.xscl;
      for (let x = start; x <= win.xmax; x += win.xscl) xTicks.push(pxAt(x, win));
    }
  }
  if (win.yscl > 0) {
    const span = win.ymax - win.ymin;
    if (span / win.yscl <= 200) {
      const start = Math.ceil(win.ymin / win.yscl) * win.yscl;
      for (let y = start; y <= win.ymax; y += win.yscl) yTicks.push(pyAt(y, win));
    }
  }

  return { xTicks, yTicks };
}

/** Zoom presets available from the ZOOM key. */
export const ZOOM_PRESETS = {
  ZStandard: { xmin: -10, xmax: 10, xscl: 1, ymin: -10, ymax: 10, yscl: 1 },
  ZTrig: {
    xmin: -2 * Math.PI, xmax: 2 * Math.PI, xscl: Math.PI / 2,
    ymin: -4, ymax: 4, yscl: 1,
  },
  ZDecimal: { xmin: -4.7, xmax: 4.7, xscl: 1, ymin: -3.1, ymax: 3.1, yscl: 1 },
  ZSquare: null, // computed from the current window
};

/** Adjust y-range so one pixel is the same width and height. */
export function squareWindow(win) {
  const xSpan = win.xmax - win.xmin;
  const ySpan = (xSpan * (GRAPH_H - 1)) / (GRAPH_W - 1);
  const yMid = (win.ymax + win.ymin) / 2;
  return { ...win, ymin: yMid - ySpan / 2, ymax: yMid + ySpan / 2 };
}

export function zoomBy(win, factor) {
  const xMid = (win.xmax + win.xmin) / 2;
  const yMid = (win.ymax + win.ymin) / 2;
  const xHalf = ((win.xmax - win.xmin) / 2) * factor;
  const yHalf = ((win.ymax - win.ymin) / 2) * factor;
  return {
    ...win,
    xmin: xMid - xHalf, xmax: xMid + xHalf,
    ymin: yMid - yHalf, ymax: yMid + yHalf,
  };
}
