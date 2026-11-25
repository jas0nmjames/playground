#!/usr/bin/env node
/**
 * Medianville: retakes the project README's GIFs, readme-media/01-city.gif to 07-lens.gif, from a local server of
 * this folder, so they show the work as it is on disk.
 *
 *   node tools/capture_readme_gifs.mjs                 all seven (run from mapping-synthetic-transactions/)
 *   node tools/capture_readme_gifs.mjs 02 05           just these
 *   node tools/capture_readme_gifs.mjs --frames DIR    also save about one frame a second of each GIF as PNG, to look at
 *
 * Like scripts/capture-media.mjs (the playground's thumbnails), it drives the Google Chrome already on this computer
 * over the DevTools protocol with Node's built-in WebSocket, so nothing needs installing: Node 22 or later, Chrome,
 * and internet access for three.js and the fonts. It writes the GIFs itself: one 255-colour palette per GIF (median
 * cut, then k-means), no dithering, and each frame stores only the pixels that changed, so a still city costs little.
 *
 * Every GIF is a 1280×800 viewport written 800 px wide at 10 frames a second, looping, with the intro skipped
 * (?intro=0) and a drawn cursor and click ring, since headless Chrome draws neither. Two other things are drawn
 * for the camera only and change nothing on the site:
 * - Live plays at the visitor's time of day, so the scenes that show Live set the page's clock to a fixed morning hour.
 * - Headless Chrome doesn't capture a <select>'s native menu, so 05-days draws the day menu's own options in a plain
 *   menu below the control, then picks the storm day on the real <select>, which reloads the page as a click would.
 */

import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { createReadStream, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { inflateSync, deflateSync } from 'node:zlib';

const PROJECT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const OUT = path.join(PROJECT, 'readme-media');
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const VW = 1280, VH = 800;          // the viewport
const SCALE = 0.625;                // → 800×500
const GW = Math.round(VW * SCALE), GH = Math.round(VH * SCALE);
const FPS = 10;
const RUN = 'v2-2027-03-03';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => performance.now();

// ─── a static server for this folder ──────────────────────────────────────────────────────────────────────────────
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp',
  '.gif': 'image/gif', '.zip': 'application/zip', '.txt': 'text/plain; charset=utf-8', '.md': 'text/markdown; charset=utf-8',
  '.woff2': 'font/woff2', '.mp4': 'video/mp4' };
function serve() {
  const server = createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    let file = path.join(PROJECT, decodeURIComponent(url.pathname));
    if (!file.startsWith(PROJECT)) { res.writeHead(403).end(); return; }
    if (existsSync(file) && statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!existsSync(file)) { res.writeHead(404).end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

// ─── Chrome over the DevTools protocol (as in scripts/capture-media.mjs) ──────────────────────────────────────────
async function launchChrome() {
  const profile = mkdtempSync(path.join(tmpdir(), 'medianville-gifs-'));
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run',
    '--no-default-browser-check', '--hide-scrollbars', '--mute-audio', '--use-angle=metal', `--window-size=${VW},${VH}`, 'about:blank'],
  { stdio: ['ignore', 'ignore', 'pipe'] });
  const wsUrl = await new Promise((resolve, reject) => {
    let buf = '';
    chrome.stderr.on('data', (d) => { buf += d; const m = buf.match(/DevTools listening on (ws:\/\/\S+)/); if (m) resolve(m[1]); });
    chrome.on('exit', (code) => reject(new Error(`Chrome exited (${code}) before it was ready`)));
  });
  const ws = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let nextId = 1;
  const pending = new Map(), listeners = new Set();
  ws.onmessage = ({ data }) => {
    const msg = JSON.parse(data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id); pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    } else if (msg.method) listeners.forEach((fn) => fn(msg));
  };
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = nextId++; pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params, sessionId }));
  });
  const close = () => { ws.close(); chrome.kill(); setTimeout(() => rmSync(profile, { recursive: true, force: true }), 500); };
  return { send, on: (fn) => { listeners.add(fn); return () => listeners.delete(fn); }, close };
}

// The cursor and click ring, drawn in the top document over everything (the systems lens is an iframe, so the
// pointer's position comes from here rather than from mouse events). Also, optionally, a fixed time of day for Live.
const SHIM = (clock) => `(() => {
  if (window.top !== window) return;
  ${clock == null ? '' : `{ const want = ${clock}, Real = Date, d = new Real();
    const off = (want - (d.getHours() * 60 + d.getMinutes() + d.getSeconds() / 60)) * 60000;
    class D extends Real { constructor(...a) { if (a.length) super(...a); else super(Real.now() + off); } static now() { return Real.now() + off; } }
    window.Date = D; }`}
  const arrow = '<svg width="24" height="28" viewBox="0 0 24 28" style="position:absolute;left:-2px;top:-1px;overflow:visible"><path d="M2 1.5 L2 21.5 L7.2 16.8 L10.8 25 L14.4 23.4 L10.9 15.4 L17.8 15.4 Z" fill="#0E1B2E" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/></svg>';
  window.__cap = {
    move(x, y) {
      let c = document.getElementById('__cap-cursor');
      if (!c) { c = document.createElement('div'); c.id = '__cap-cursor'; c.setAttribute('aria-hidden', 'true');
        c.style.cssText = 'position:fixed;left:0;top:0;width:0;height:0;z-index:2147483647;pointer-events:none'; c.innerHTML = arrow;
        document.documentElement.appendChild(c); }
      c.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    },
    ring(x, y) {
      const r = document.createElement('div'); r.setAttribute('aria-hidden', 'true');
      r.style.cssText = 'position:fixed;left:' + (x - 16) + 'px;top:' + (y - 16) + 'px;width:32px;height:32px;border-radius:50%;box-sizing:border-box;border:3px solid rgba(47,107,255,.95);background:rgba(47,107,255,.16);z-index:2147483646;pointer-events:none;transition:transform .5s ease-out,opacity .5s ease-in';
      document.documentElement.appendChild(r);
      requestAnimationFrame(() => requestAnimationFrame(() => { r.style.transform = 'scale(1.7)'; r.style.opacity = '0'; }));
      setTimeout(() => r.remove(), 700);
    },
  };
})();`;

async function openPage(cdp, url, { clock = null } = {}) {
  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  const s = (method, params) => cdp.send(method, params, sessionId);
  const errors = [];
  cdp.on((m) => {
    if (m.sessionId !== sessionId) return;
    if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map((a) => a.value ?? a.description).join(' '));
  });
  await s('Page.enable'); await s('Runtime.enable');
  await s('Emulation.setDeviceMetricsOverride', { width: VW, height: VH, deviceScaleFactor: 1, mobile: false });
  await s('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }, { name: 'prefers-reduced-motion', value: 'no-preference' }] });
  await s('Page.addScriptToEvaluateOnNewDocument', { source: SHIM(clock) });
  const page = { s, sessionId, targetId, errors, x: VW * 0.55, y: VH * 0.55 };
  await navigate(cdp, page, url);
  return page;
}
async function navigate(cdp, page, url) {
  const loaded = new Promise((resolve) => { const off = cdp.on((m) => { if (m.sessionId === page.sessionId && m.method === 'Page.loadEventFired') { off(); resolve(); } }); });
  await page.s('Page.navigate', { url });
  await Promise.race([loaded, sleep(30000)]);
}
async function evaluate(page, expression) {
  const { result, exceptionDetails } = await page.s('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (exceptionDetails) throw new Error(`in the page: ${exceptionDetails.exception?.description || exceptionDetails.text}`);
  return result.value;
}
async function waitFor(page, expression, ms = 60000, what = expression) {
  const t0 = now();
  while (now() - t0 < ms) { try { if (await evaluate(page, `!!(${expression})`)) return; } catch (e) { /* the page is still loading */ } await sleep(150); }
  throw new Error(`timed out waiting for ${what}`);
}
// the centre of the first element matching a selector (scrolled into view first when asked)
async function spot(page, sel, { scroll = false, dx = 0, dy = 0, pick = '' } = {}) {
  const r = await evaluate(page, `(() => { const all = [...document.querySelectorAll(${JSON.stringify(sel)})]${pick};
    const el = Array.isArray(all) ? all.find((e) => e.offsetParent !== null || e.getClientRects().length) : all; if (!el) return null;
    ${scroll ? "el.scrollIntoView({ block: 'center', behavior: 'instant' });" : ''}
    const b = el.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2, w: b.width, h: b.height, left: b.left, top: b.top }; })()`);
  if (!r) throw new Error(`nothing on the page matches ${sel}`);
  return { ...r, x: r.x + dx, y: r.y + dy };
}

// ─── the pointer ──────────────────────────────────────────────────────────────────────────────────────────────────
const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
async function place(page, x, y) { page.x = x; page.y = y; await evaluate(page, `window.__cap && __cap.move(${x}, ${y})`); }
async function moveTo(page, x, y, ms = 600, { button = 'none' } = {}) {
  const x0 = page.x, y0 = page.y, t0 = now();
  for (;;) {
    const t = Math.min(1, (now() - t0) / ms), k = ease(t), px = x0 + (x - x0) * k, py = y0 + (y - y0) * k;
    await page.s('Input.dispatchMouseEvent', { type: 'mouseMoved', x: px, y: py, button, buttons: button === 'left' ? 1 : 0 });
    await place(page, px, py);
    if (t >= 1) break;
    await sleep(16);
  }
}
async function click(page, x = page.x, y = page.y) {
  if (x !== page.x || y !== page.y) await moveTo(page, x, y);
  await evaluate(page, `window.__cap && __cap.ring(${x}, ${y})`);
  await page.s('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
  await sleep(60);
  await page.s('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
}
// the ring alone, where a real click would open a native control the camera can't see
async function tap(page) { await evaluate(page, `window.__cap && __cap.ring(${page.x}, ${page.y})`); }
async function drag(page, x, y, ms) {
  await evaluate(page, `window.__cap && __cap.ring(${page.x}, ${page.y})`);
  await page.s('Input.dispatchMouseEvent', { type: 'mousePressed', x: page.x, y: page.y, button: 'left', buttons: 1, clickCount: 1 });
  await moveTo(page, x, y, ms, { button: 'left' });
  await page.s('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
}

// ─── recording: screenshots as fast as Chrome gives them, timed, with pauses that cut time out ────────────────────
function record(page) {
  const frames = []; let on = true, paused = false, offset = 0, pausedAt = 0;
  const loop = (async () => {
    while (on) {
      const t0 = now();
      try {
        // a screenshot asked for while the page navigates can wait for ever, so give up on it after a second
        const shot = page.s('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true, clip: { x: 0, y: 0, width: VW, height: VH, scale: SCALE } });
        const r = await Promise.race([shot, sleep(1000).then(() => null)]);
        if (r && !paused) frames.push({ t: (t0 + now()) / 2 - offset, png: Buffer.from(r.data, 'base64') });
      } catch (e) { await sleep(50); /* navigating */ }
    }
  })();
  return {
    frames,
    pause() { if (!paused) { paused = true; pausedAt = now(); } },
    resume() { if (paused) { paused = false; offset += now() - pausedAt; } },
    kept: (t0) => now() - t0 - offset,
    async stop() { on = false; await loop; return frames; },
  };
}

// ─── PNG in (Chrome's screenshots: 8-bit RGB or RGBA, not interlaced) ─────────────────────────────────────────────
function decodePNG(buf) {
  let p = 8, w = 0, h = 0, ct = 0; const idat = [];
  while (p < buf.length) {
    const len = buf.readUInt32BE(p), type = buf.toString('latin1', p + 4, p + 8), body = buf.subarray(p + 8, p + 8 + len);
    if (type === 'IHDR') { w = body.readUInt32BE(0); h = body.readUInt32BE(4); ct = body[9]; if (body[8] !== 8 || body[12]) throw new Error('unexpected PNG'); }
    else if (type === 'IDAT') idat.push(body);
    else if (type === 'IEND') break;
    p += 12 + len;
  }
  const bpp = ct === 6 ? 4 : ct === 2 ? 3 : 0; if (!bpp) throw new Error('unexpected PNG colour type ' + ct);
  const raw = inflateSync(Buffer.concat(idat)), stride = w * bpp, out = new Uint8Array(w * h * 3), prev = new Uint8Array(stride), cur = new Uint8Array(stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)], row = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? cur[i - bpp] : 0, b = prev[i], c = i >= bpp ? prev[i - bpp] : 0;
      let v = row[i];
      if (f === 1) v += a; else if (f === 2) v += b; else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) { const q = a + b - c, pa = Math.abs(q - a), pb = Math.abs(q - b), pc = Math.abs(q - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      cur[i] = v & 255;
    }
    for (let x = 0; x < w; x++) { const o = (y * w + x) * 3; out[o] = cur[x * bpp]; out[o + 1] = cur[x * bpp + 1]; out[o + 2] = cur[x * bpp + 2]; }
    prev.set(cur);
  }
  return { w, h, rgb: out };
}
// PNG out, for --frames
function encodePNG(w, h, rgb) {
  const crcT = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c; });
  const crc = (b) => { let c = -1; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };
  const chunk = (type, body) => { const t = Buffer.from(type, 'latin1'), l = Buffer.alloc(4), c = Buffer.alloc(4); l.writeUInt32BE(body.length); c.writeUInt32BE(crc(Buffer.concat([t, body]))); return Buffer.concat([l, t, body, c]); };
  const raw = Buffer.alloc((w * 3 + 1) * h); for (let y = 0; y < h; y++) { raw[y * (w * 3 + 1)] = 0; Buffer.from(rgb.buffer, rgb.byteOffset + y * w * 3, w * 3).copy(raw, y * (w * 3 + 1) + 1); }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

// ─── GIF out ──────────────────────────────────────────────────────────────────────────────────────────────────────
// A palette for the whole GIF: median cut on a sample of every frame, split where the error is largest, then a few
// rounds of k-means. Index 255 is kept for "unchanged".
function palette(frames, n = 255) {
  const per = Math.max(1, Math.floor(frames.length * frames[0].length / 3 / 240000));
  const sm = []; let k = 0;
  for (const f of frames) for (let i = 0; i < f.length; i += 3) if (k++ % per === 0) sm.push(f[i], f[i + 1], f[i + 2]);
  const S = Uint8Array.from(sm), N = S.length / 3;
  const stat = (ix) => { const s = [0, 0, 0], q = [0, 0, 0]; for (const i of ix) for (let c = 0; c < 3; c++) { const v = S[i * 3 + c]; s[c] += v; q[c] += v * v; } const v = q.map((x, c) => x - s[c] * s[c] / ix.length); return { err: v[0] + v[1] + v[2], ch: v.indexOf(Math.max(...v)) }; };
  let boxes = [{ ix: Uint32Array.from({ length: N }, (_, i) => i) }]; boxes[0].st = stat(boxes[0].ix);
  while (boxes.length < n) {
    let bi = -1, be = 0; boxes.forEach((b, i) => { if (b.ix.length > 1 && b.st.err > be) { be = b.st.err; bi = i; } });
    if (bi < 0) break;
    const b = boxes[bi], ch = b.st.ch, sorted = Array.from(b.ix).sort((p, q) => S[p * 3 + ch] - S[q * 3 + ch]), mid = sorted.length >> 1;
    const A = Uint32Array.from(sorted.slice(0, mid)), B = Uint32Array.from(sorted.slice(mid));
    boxes.splice(bi, 1, { ix: A, st: stat(A) }, { ix: B, st: stat(B) });
  }
  let P = boxes.map((b) => { const s = [0, 0, 0]; for (const i of b.ix) for (let c = 0; c < 3; c++) s[c] += S[i * 3 + c]; return s.map((x) => x / b.ix.length); });
  for (let round = 0; round < 4; round++) {
    const sum = P.map(() => [0, 0, 0, 0]);
    for (let i = 0; i < N; i++) { const j = nearest(P, S[i * 3], S[i * 3 + 1], S[i * 3 + 2]); const t = sum[j]; t[0] += S[i * 3]; t[1] += S[i * 3 + 1]; t[2] += S[i * 3 + 2]; t[3]++; }
    P = P.map((p, j) => (sum[j][3] ? [sum[j][0] / sum[j][3], sum[j][1] / sum[j][3], sum[j][2] / sum[j][3]] : p));
  }
  P = P.map((p) => p.map((v) => Math.round(v)));
  while (P.length < 255) P.push([0, 0, 0]);
  return P;
}
function nearest(P, r, g, b) { let bj = 0, bd = Infinity; for (let j = 0; j < P.length; j++) { const p = P[j], d = (p[0] - r) ** 2 * 2 + (p[1] - g) ** 2 * 4 + (p[2] - b) ** 2 * 3; if (d < bd) { bd = d; bj = j; } } return bj; }
function mapper(P) {
  const cache = new Int16Array(1 << 18).fill(-1);
  return (r, g, b) => { const key = ((r >> 2) << 12) | ((g >> 2) << 6) | (b >> 2); let j = cache[key]; if (j < 0) { j = nearest(P, r, g, b); cache[key] = j; } return j; };
}
// GIF's LZW, as omggif writes it
function lzw(ix, out) {
  const MIN = 8, CLEAR = 256, EOI = 257;
  let size = MIN + 1, next = EOI + 1, cur = 0, shift = 0;
  const bytes = [];
  const emit = (c) => { cur |= c << shift; shift += size; while (shift >= 8) { bytes.push(cur & 255); cur >>>= 8; shift -= 8; } };
  const codes = new Int16Array(1 << 20), stamp = new Int32Array(1 << 20); let gen = 1;
  emit(CLEAR);
  let pre = ix[0];
  for (let i = 1; i < ix.length; i++) {
    const k = ix[i], key = (pre << 8) | k;
    if (stamp[key] === gen) { pre = codes[key]; continue; }
    emit(pre);
    if (next === 4096) { emit(CLEAR); next = EOI + 1; size = MIN + 1; gen++; }
    else { if (next >= 1 << size) size++; codes[key] = next++; stamp[key] = gen; }
    pre = k;
  }
  emit(pre); emit(EOI);
  if (shift > 0) bytes.push(cur & 255);
  out.push(MIN);
  for (let i = 0; i < bytes.length; i += 255) { const n = Math.min(255, bytes.length - i); out.push(n); for (let j = 0; j < n; j++) out.push(bytes[i + j]); }
  out.push(0);
}
// frames: [{ rgb, delay (centiseconds) }]; tol: how far (0–255, per channel) a pixel may drift before it's redrawn
function writeGIF(file, frames, tol) {
  const P = palette(frames.map((f) => f.rgb)), map = mapper(P), N = GW * GH;
  const out = [];
  const u16 = (v) => out.push(v & 255, v >> 8);
  out.push(...Buffer.from('GIF89a', 'latin1')); u16(GW); u16(GH); out.push(0xf7, 0, 0);
  for (let j = 0; j < 256; j++) { const p = P[j] || [0, 0, 0]; out.push(p[0], p[1], p[2]); }
  out.push(0x21, 0xff, 11, ...Buffer.from('NETSCAPE2.0', 'latin1'), 3, 1, 0, 0, 0);
  const shown = new Int16Array(N).fill(-1), ix = new Uint8Array(N);
  const blocks = [];
  for (const f of frames) {
    const rgb = f.rgb; let x0 = GW, y0 = GH, x1 = -1, y1 = -1;
    for (let p = 0; p < N; p++) {
      const r = rgb[p * 3], g = rgb[p * 3 + 1], b = rgb[p * 3 + 2], s = shown[p];
      if (s >= 0) { const q = P[s]; if (Math.abs(q[0] - r) <= tol && Math.abs(q[1] - g) <= tol && Math.abs(q[2] - b) <= tol) { ix[p] = 255; continue; } }
      const j = map(r, g, b);
      if (j === s) { ix[p] = 255; continue; }
      ix[p] = j; shown[p] = j;
      const x = p % GW, y = (p / GW) | 0; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    if (x1 < 0) { if (blocks.length) blocks[blocks.length - 1].delay += f.delay; continue; }
    const w = x1 - x0 + 1, h = y1 - y0 + 1, sub = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) sub.set(ix.subarray((y0 + y) * GW + x0, (y0 + y) * GW + x0 + w), y * w);
    blocks.push({ x0, y0, w, h, sub, delay: f.delay });
  }
  for (const b of blocks) {
    out.push(0x21, 0xf9, 4, (1 << 2) | 1); u16(b.delay); out.push(255, 0);
    out.push(0x2c); u16(b.x0); u16(b.y0); u16(b.w); u16(b.h); out.push(0);
    lzw(b.sub, out);
  }
  out.push(0x3b);
  const buf = Buffer.from(out); writeFileSync(file, buf);
  return { bytes: buf.length, frames: blocks.length };
}

// Reads a GIF back (as written above: one palette, frames that keep what's under them) and returns about one
// frame a second, composited, for --frames. It's also the check that the file decodes to what was meant.
function decodeGIF(buf) {
  let p = 6; const w = buf.readUInt16LE(p), h = buf.readUInt16LE(p + 2), flags = buf[p + 4]; p += 7;
  const gct = flags & 0x80 ? buf.subarray(p, p + 3 * (2 << (flags & 7))) : null; if (gct) p += gct.length;
  const canvas = new Uint8Array(w * h * 3), out = []; let ti = -1, delay = 0, at = 0, nextAt = 0;
  const blocks = () => { const parts = []; for (let n = buf[p++]; n; n = buf[p++]) { parts.push(buf.subarray(p, p + n)); p += n; } return Buffer.concat(parts); };
  while (p < buf.length) {
    const b = buf[p++];
    if (b === 0x3b) break;
    if (b === 0x21) { const label = buf[p++]; const body = blocks(); if (label === 0xf9) { delay = body.readUInt16LE(1); ti = body[0] & 1 ? body[3] : -1; } continue; }
    if (b !== 0x2c) throw new Error('bad GIF block ' + b);
    const x0 = buf.readUInt16LE(p), y0 = buf.readUInt16LE(p + 2), fw = buf.readUInt16LE(p + 4), fh = buf.readUInt16LE(p + 6), lf = buf[p + 8]; p += 9;
    let pal = gct; if (lf & 0x80) { pal = buf.subarray(p, p + 3 * (2 << (lf & 7))); p += pal.length; }
    const min = buf[p++], data = blocks(), ix = new Uint8Array(fw * fh);
    // LZW
    const CLEAR = 1 << min, EOI = CLEAR + 1, pre = new Int32Array(4096), suf = new Uint8Array(4096), len = new Int32Array(4096);
    let size = min + 1, next = EOI + 1, prev = -1, bits = 0, cur = 0, q = 0, o = 0;
    for (let i = 0; i < CLEAR; i++) { pre[i] = -1; suf[i] = i; len[i] = 1; }
    const first = (c) => { while (pre[c] >= 0) c = pre[c]; return suf[c]; };
    while (o < ix.length) {
      while (bits < size && q < data.length) { cur |= data[q++] << bits; bits += 8; }
      if (bits < size) break;
      const c = cur & ((1 << size) - 1); cur >>>= size; bits -= size;
      if (c === CLEAR) { size = min + 1; next = EOI + 1; prev = -1; continue; }
      if (c === EOI) break;
      let code = c;
      if (prev >= 0 && next < 4096) { pre[next] = prev; suf[next] = c < next ? first(c) : first(prev); len[next] = len[prev] + 1; next++; if (next === 1 << size && size < 12) size++; }
      if (code >= next) throw new Error('bad LZW code');
      const L = len[code]; for (let k = L - 1, c2 = code; k >= 0; k--, c2 = pre[c2]) if (o + k < ix.length) ix[o + k] = suf[c2];
      o += L; prev = c;
    }
    for (let y = 0; y < fh; y++) for (let x = 0; x < fw; x++) {
      const j = ix[y * fw + x]; if (j === ti) continue;
      const d = ((y0 + y) * w + x0 + x) * 3; canvas[d] = pal[j * 3]; canvas[d + 1] = pal[j * 3 + 1]; canvas[d + 2] = pal[j * 3 + 2];
    }
    if (at >= nextAt) { out.push({ at: at / 100, rgb: canvas.slice() }); nextAt += 100; }
    at += delay;
  }
  return out;
}

// the recorded screenshots, resampled to FPS: each tick shows the latest screenshot taken by then
function resample(shots, seconds) {
  const t0 = shots[0].t, ticks = Math.round(seconds * FPS), out = []; let j = 0, last = null, lastJ = -1;
  for (let k = 0; k < ticks; k++) {
    const t = t0 + (k * 1000) / FPS;
    while (j + 1 < shots.length && shots[j + 1].t <= t) j++;
    if (j === lastJ) { out[out.length - 1].delay += 100 / FPS; continue; }
    last = decodePNG(shots[j].png); lastJ = j;
    if (last.w !== GW || last.h !== GH) throw new Error(`a screenshot came back ${last.w}×${last.h}`);
    out.push({ rgb: last.rgb, delay: 100 / FPS, t: t - t0 });
  }
  return out;
}

// ─── the scenes ───────────────────────────────────────────────────────────────────────────────────────────────────
// Each opens its page, gets it ready off camera, then records its steps; `seconds` is the GIF's length.
const loaded = "(document.getElementById('datachip') || {}).textContent.includes('records in the day')";
const ready = async (page) => { await waitFor(page, loaded, 120000, 'the day to load'); await sleep(2500); };
const viewer = (base, q = '', h = '') => `${base}?intro=0&run=${RUN}${q}${h ? '#' + h : ''}`;
const label = (id) => `label[for="${id}"]`;

const SCENES = {
  '01-city': {
    seconds: 8, tol: 9, alt: 'Medianville',
    async setup(page) { await ready(page); await evaluate(page, "document.getElementById('s5').click(); App.seek(712)"); await place(page, 700, 470); await sleep(1500); },
    async run(page) {
      await sleep(1300);
      const map = await spot(page, label('v-map')); await moveTo(page, map.x, map.y, 800); await click(page);
      await sleep(2700);
      const mini = await spot(page, label('v-mini')); await moveTo(page, mini.x, mini.y, 500); await click(page);
      await sleep(200); await moveTo(page, 760, 520, 900);
    },
  },
  '02-household': {
    seconds: 12, tol: 7,
    url: (base) => viewer(base, '', 'record=R0093156'),
    async setup(page) { await ready(page); await waitFor(page, "App.S.selId === 'R0093156' && !document.getElementById('sheet').hidden", 20000, 'the record sheet'); await place(page, 1000, 420); await sleep(800); },
    async run(page) {
      await sleep(2600);
      // scrub the timeline to 6:10 p.m.
      const tl = await spot(page, '#tl'), at = (m) => tl.left + 8 + (tl.w - 16) * (m / 1439);
      await moveTo(page, at(683), tl.y, 700); await drag(page, at(1090), tl.y, 1500);
      await sleep(500);
      const go = await spot(page, '#sheet [data-hhday]', { scroll: true }); await moveTo(page, go.x, go.y, 800); await click(page);
      await sleep(900);
      await moveTo(page, go.x - 40, go.y + 160, 900);
      await sleep(3000);
    },
  },
  '03-beyond-money': {
    seconds: 8, tol: 9,
    async setup(page) { await ready(page); await evaluate(page, "document.getElementById('s5').click(); App.seek(505)"); await place(page, 800, 300); await sleep(1500); },
    async run(page) {
      await sleep(700);
      for (const k of ['purchase', 'income', 'bill', 'fail']) { const b = await spot(page, `#filters button[data-k="${k}"]`); await moveTo(page, b.x, b.y, 450); await click(page); await sleep(350); }
      await moveTo(page, 820, 470, 1200);
      await sleep(1600);
    },
  },
  '04-speed': {
    seconds: 8, tol: 9, clock: 7 * 60 + 41,
    url: (base) => viewer(base),
    async setup(page) { await ready(page); await place(page, 640, 560); await sleep(800); },
    async run(page) {
      const live = await spot(page, label('slive')); await moveTo(page, live.x, live.y - 2, 900);
      await sleep(500);
      const s5 = await spot(page, label('s5')); await moveTo(page, s5.x, s5.y, 450); await click(page);
      await sleep(1600);
      const s20 = await spot(page, label('s20')); await moveTo(page, s20.x, s20.y, 450); await click(page);
      await sleep(1500);
      const tl = await spot(page, '#tl'), at = (m) => tl.left + 8 + (tl.w - 16) * (m / 1439), t = await evaluate(page, 'App.S.t');
      await moveTo(page, at(t), tl.y, 500); await drag(page, at(1050), tl.y, 1300);
      await sleep(250);
    },
  },
  '05-days': {
    seconds: 6, tol: 9, clock: 10 * 60 + 5,
    url: (base) => viewer(base),
    async setup(page) { await ready(page); await place(page, 520, 330); await sleep(600); },
    async run(page, cdp) {
      await sleep(400);
      const dp = await spot(page, '.daypick'); await moveTo(page, dp.x, dp.y, 700); await tap(page);
      // the day menu's own options, in a plain menu below the control (headless Chrome can't capture the native one)
      const pick = await evaluate(page, `(() => {
        const sel = document.getElementById('runpick'), at = document.querySelector('.daypick').getBoundingClientRect();
        const m = document.createElement('div'); m.id = '__cap-menu';
        m.style.cssText = 'position:fixed;left:' + at.left + 'px;top:' + (at.bottom + 4) + 'px;min-width:' + Math.max(300, at.width) + 'px;z-index:2147483640;background:#fff;color:#0E1B2E;border-radius:8px;box-shadow:0 2px 6px rgba(14,27,46,.14),0 12px 32px rgba(14,27,46,.22);padding:5px 0;font:13px/1.25 -apple-system,BlinkMacSystemFont,sans-serif';
        let hit = null;
        for (const g of sel.querySelectorAll('optgroup')) {
          const h = document.createElement('div'); h.textContent = g.label; h.style.cssText = 'padding:5px 12px 3px;font-weight:600;color:#5B6676'; m.appendChild(h);
          for (const o of g.querySelectorAll('option')) { const r = document.createElement('div'); r.textContent = (o.selected ? '✓ ' : '\\u2003') + o.textContent; r.dataset.v = o.value; r.style.cssText = 'padding:3px 12px 3px 10px;white-space:nowrap;border-radius:4px;margin:0 5px'; m.appendChild(r); if (o.value === 'v2-2027-01-19') hit = r; }
        }
        document.documentElement.appendChild(m);
        const b = hit.getBoundingClientRect(); return { x: b.left + 70, y: b.top + b.height / 2 };
      })()`);
      await sleep(700);
      await moveTo(page, pick.x, pick.y, 700);
      await evaluate(page, "document.querySelector('#__cap-menu [data-v=\"v2-2027-01-19\"]').style.cssText += ';background:#2F6BFF;color:#fff'");
      await sleep(350); await tap(page);
      await evaluate(page, "document.getElementById('__cap-menu').remove(); const s = document.getElementById('runpick'); s.value = 'v2-2027-01-19'; s.dispatchEvent(new Event('change'))");
      await sleep(700);
      // the storm day loads: keep a moment of it, cut the rest of the wait
      this.rec.pause();
      await waitFor(page, "location.search.includes('2027-01-19') && document.readyState !== 'loading'", 20000, 'the storm day to open');
      await place(page, pick.x, pick.y);
      this.rec.resume(); await sleep(500); this.rec.pause();
      await waitFor(page, loaded, 120000, 'the storm day to load'); await sleep(1800);
      this.rec.resume();
      await moveTo(page, pick.x + 120, pick.y + 120, 800);
      await sleep(800);
    },
  },
  '06-explorer': {
    seconds: 8, tol: 4,
    url: (base) => `${base}explorer/?run=${RUN}`,
    async setup(page) { await waitFor(page, "document.querySelector('.rows .rr')", 120000, 'the explorer to load'); await place(page, 640, 420); await sleep(1200); },
    async run(page) {
      await sleep(700);
      const f = await spot(page, 'input[data-f="fail"]', { scroll: true }); await moveTo(page, f.x + 30, f.y, 800); await click(page);
      await sleep(1500);
      const row = await spot(page, '.rows .rr', { dx: -80 }); await moveTo(page, row.x, row.y, 900); await click(page);
      await sleep(900); await moveTo(page, row.x + 120, row.y + 220, 900);
      await sleep(2000);
    },
  },
  '07-lens': {
    seconds: 13, tol: 7,
    url: (base) => viewer(base, '', 'household=H22924'),
    async setup(page) { await ready(page); await waitFor(page, "App.S.hhDay === 'H22924'", 20000, 'the household day'); await place(page, 1000, 560); await sleep(800); },
    async run(page, cdp) {
      await sleep(1000);
      const go = await spot(page, '#sheet [data-lens]', { scroll: true }); await moveTo(page, go.x, go.y, 800); await click(page);
      await sleep(1900);
      // the lens is an iframe: find its layer list there, and lift each layer in turn
      const frame = await spot(page, '#lens-frame');
      for (const name of ['Today', 'Economic', 'Political', 'Built & natural', 'Social & cultural', 'Historical']) {
        const r = await evaluate(page, `(() => { const d = document.getElementById('lens-frame').contentDocument;
          const el = [...d.querySelectorAll('#platelist .pbtn')].find((e) => e.querySelector('b').textContent.startsWith(${JSON.stringify(name)}));
          if (!el) return null; const b = el.getBoundingClientRect(); return { x: b.left + Math.min(60, b.width / 2), y: b.top + b.height / 2 }; })()`);
        if (!r) throw new Error(`no ${name} layer in the lens`);
        await moveTo(page, frame.left + r.x, frame.top + r.y, 450);
        await sleep(1000);
      }
    },
  },
};

// ─── main ─────────────────────────────────────────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const fi = args.indexOf('--frames'), framesDir = fi >= 0 ? path.resolve(args[fi + 1]) : null;
const wanted = args.filter((a, i) => !a.startsWith('--') && i !== fi + 1);
const names = Object.keys(SCENES).filter((n) => !wanted.length || wanted.some((w) => n.startsWith(w)));
if (!names.length) { console.log(`No scene matches ${wanted.join(' ')}. Scenes: ${Object.keys(SCENES).join(', ')}`); process.exit(1); }
mkdirSync(OUT, { recursive: true });
if (framesDir) mkdirSync(framesDir, { recursive: true });

const server = await serve();
const base = `http://127.0.0.1:${server.address().port}/`;
const cdp = await launchChrome();
let failures = 0;
for (const name of names) {
  const sc = SCENES[name];
  try {
    const page = await openPage(cdp, (sc.url || viewer)(base), { clock: sc.clock ?? null });
    await sc.setup(page);
    await place(page, page.x, page.y);
    const rec = record(page); sc.rec = rec;
    const t0 = now();
    await sc.run(page, cdp);
    rec.resume();
    const took = rec.kept(t0) / 1000, left = sc.seconds * 1000 - rec.kept(t0);
    if (left > 0) await sleep(left + 200);
    const shots = await rec.stop();
    const frames = resample(shots, sc.seconds);
    const file = path.join(OUT, `${name}.gif`);
    const { bytes, frames: written } = writeGIF(file, frames, sc.tol);
    if (framesDir) for (const f of decodeGIF(readFileSync(file))) writeFileSync(path.join(framesDir, `${name}-${f.at.toFixed(1).padStart(4, '0')}s.png`), encodePNG(GW, GH, f.rgb));
    const fps = shots.length / ((shots[shots.length - 1].t - shots[0].t) / 1000);
    console.log(`✓ ${name}.gif  ${(bytes / 1048576).toFixed(2)} MB, ${sc.seconds} s, ${written} frames written (${shots.length} screenshots at ${fps.toFixed(1)} a second; steps took ${took.toFixed(1)} s on camera)`);
    if (took > sc.seconds + 0.3) console.log(`  note: the steps ran ${(took - sc.seconds).toFixed(1)} s past the GIF's ${sc.seconds} s, so the end is cut`);
    if (page.errors.length) { console.log(`  page errors:\n    ${page.errors.join('\n    ')}`); }
    await cdp.send('Target.closeTarget', { targetId: page.targetId });
  } catch (err) {
    failures++;
    console.log(`✗ ${name}: ${err.message}`);
  }
}
cdp.close();
server.close();
process.exit(failures ? 1 : 0);
