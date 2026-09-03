import { useEffect, useRef } from 'react';
import {
  GRAPH_W, GRAPH_H, samplePlot, axisTicks, pxAt, pyAt,
} from '../lib/graph.js';
import { formatNumber } from '../lib/format.js';

const LCD_BG = [154, 166, 133, 255];
const LCD_INK = [26, 34, 18, 255];

/** 1-bit framebuffer at true LCD resolution, upscaled with pixelated rendering. */
function createBuffer() {
  return new Uint8Array(GRAPH_W * GRAPH_H);
}

function plot(buf, x, y) {
  const ix = Math.round(x);
  const iy = Math.round(y);
  if (ix < 0 || ix >= GRAPH_W || iy < 0 || iy >= GRAPH_H) return;
  buf[iy * GRAPH_W + ix] = 1;
}

/** Bresenham — the calculator connects consecutive samples with a segment. */
function drawLine(buf, x0, y0, x1, y1) {
  let x = Math.round(x0);
  let y = Math.round(y0);
  const xEnd = Math.round(x1);
  const yEnd = Math.round(y1);
  const dx = Math.abs(xEnd - x);
  const dy = -Math.abs(yEnd - y);
  const sx = x < xEnd ? 1 : -1;
  const sy = y < yEnd ? 1 : -1;
  let err = dx + dy;

  // A near-vertical asymptote can generate a very long segment; cap the work.
  for (let guard = 0; guard < 4096; guard++) {
    plot(buf, x, y);
    if (x === xEnd && y === yEnd) return;
    const e2 = 2 * err;
    if (e2 >= dy) { err += dy; x += sx; }
    if (e2 <= dx) { err += dx; y += sy; }
  }
}

function drawAxes(buf, win) {
  const { xTicks, yTicks } = axisTicks(win);
  const axisY = pyAt(0, win);
  const axisX = pxAt(0, win);

  const showX = axisY >= 0 && axisY < GRAPH_H;
  const showY = axisX >= 0 && axisX < GRAPH_W;

  if (showX) for (let x = 0; x < GRAPH_W; x++) plot(buf, x, axisY);
  if (showY) for (let y = 0; y < GRAPH_H; y++) plot(buf, axisX, y);

  // Tick marks sit on the axis, or along the screen edge when it's off-screen.
  if (showX) {
    for (const tx of xTicks) {
      plot(buf, tx, axisY - 1);
      plot(buf, tx, axisY + 1);
    }
  }
  if (showY) {
    for (const ty of yTicks) {
      plot(buf, axisX - 1, ty);
      plot(buf, axisX + 1, ty);
    }
  }
}

function drawFunction(buf, source, win, ctx) {
  const samples = samplePlot(source, win, ctx);
  let prev = null;

  for (let px = 0; px < GRAPH_W; px++) {
    const s = samples[px];
    if (!s) {
      prev = null;
      continue;
    }
    // Skip points far outside the viewport so a pole doesn't paint a wall.
    const offscreen = s.py < -GRAPH_H * 4 || s.py > GRAPH_H * 5;
    if (offscreen) {
      prev = null;
      continue;
    }
    if (prev) drawLine(buf, prev.px, prev.py, px, s.py);
    else plot(buf, px, s.py);
    prev = { px, py: s.py };
  }

  return samples;
}

/**
 * Trace readouts share one 16-column row, so each value gets about half of
 * it — the hardware truncates rather than wrapping.
 */
function traceValue(v) {
  if (!Number.isFinite(v)) return '';
  return formatNumber(v).slice(0, 8);
}

export default function GraphCanvas({ win, yvars, evalCtx, trace, scale = 5 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const c2d = canvas.getContext('2d');
    const buf = createBuffer();

    drawAxes(buf, win);

    for (let n = 1; n <= 9; n++) {
      const source = yvars[n];
      if (source && source.trim()) drawFunction(buf, source, win, evalCtx);
    }

    // Trace cursor: a small plus sign, as the hardware draws it.
    if (trace && trace.point) {
      const { px, py } = trace.point;
      for (let d = -2; d <= 2; d++) {
        plot(buf, px + d, py);
        plot(buf, px, py + d);
      }
    }

    const image = c2d.createImageData(GRAPH_W, GRAPH_H);
    for (let i = 0; i < buf.length; i++) {
      const color = buf[i] ? LCD_INK : LCD_BG;
      image.data.set(color, i * 4);
    }
    c2d.putImageData(image, 0, 0);
  }, [win, yvars, evalCtx, trace]);

  return (
    <div className="graph">
      <canvas
        ref={canvasRef}
        width={GRAPH_W}
        height={GRAPH_H}
        style={{ width: GRAPH_W * scale, height: GRAPH_H * scale }}
      />
      {trace && (
        <>
          <div className="graph-label graph-label-top">{trace.label}</div>
          <div className="graph-label graph-label-x">X={traceValue(trace.x)}</div>
          <div className="graph-label graph-label-y">Y={traceValue(trace.y)}</div>
        </>
      )}
    </div>
  );
}
