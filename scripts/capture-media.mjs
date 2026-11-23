#!/usr/bin/env node

/**
 * Takes the directory's screenshots and preview videos with the Google Chrome
 * already on this computer. No npm packages: it talks to Chrome over the
 * DevTools protocol with Node's built-in WebSocket (Node 22 or later).
 *
 *   node scripts/capture-media.mjs                  thumbnails for projects that have none
 *   node scripts/capture-media.mjs marimba shapes   (re)take these projects' thumbnails
 *   node scripts/capture-media.mjs --preview liquid-hourglass
 *                                                   also record a short preview video
 *
 * Writes <project>/thumbnail.webp (800×500) and, with --preview,
 * <project>/preview.webm or preview.mp4 (800×500, about 6 seconds, no sound).
 * Then run `node scripts/build.js` to put them on the page.
 *
 * Projects on GitHub Pages are captured from a local server of this folder,
 * so you see uncommitted work; projects hosted elsewhere (url: in frontmatter)
 * from their live site. Per-project settings are in CAPTURE below.
 */

import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { createReadStream, existsSync, mkdtempSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { ROOT, GITHUB_PAGES_BASE, collectProjects } = require('./projects.js');

const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const WIDTH = 1280;
const HEIGHT = 800;
const SCALE = 0.625; // 1280×800 viewport → 800×500 image

/**
 * path: what to open, relative to the project folder (default: its site URL)
 * wait: milliseconds to let it settle before the screenshot (default 2500)
 * click: [x, y] in the 1280×800 viewport to click first (e.g. to start a demo)
 * seconds: preview length (default 6)
 */
const CAPTURE = {
  'mapping-synthetic-transactions': { path: '?intro=0', wait: 12000 },
  'liquid-hourglass': { wait: 6000 },
  'typography': { wait: 1500 },
  'dut-dut': { wait: 4000 },
  'project-scravax': { wait: 5000 },
  'strikefleet-omega-recreated': { wait: 3000 },
};

// ─── tiny static server for this folder ───────────────────────────────────

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.mp4': 'video/mp4',
  '.webm': 'video/webm', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.vtt': 'text/vtt',
  '.zip': 'application/zip', '.wasm': 'application/wasm', '.glb': 'model/gltf-binary',
};

/** Serves this folder, plus /__frames/N.jpg and /__encoder for record(). */
function serve(recording) {
  const server = createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const frame = url.pathname.match(/^\/__frames\/(\d+)\.jpg$/);
    if (frame && recording.frames[frame[1]]) {
      res.writeHead(200, { 'Content-Type': 'image/jpeg' }).end(recording.frames[frame[1]].data);
      return;
    }
    if (url.pathname === '/__encoder') {
      res.writeHead(200, { 'Content-Type': 'text/html' }).end('<!doctype html><title>encoder</title>');
      return;
    }
    let file = path.join(ROOT, decodeURIComponent(url.pathname));
    if (!file.startsWith(ROOT)) { res.writeHead(403).end(); return; }
    if (existsSync(file) && statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!existsSync(file)) { res.writeHead(404).end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream' });
    createReadStream(file).pipe(res);
  });
  return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server)));
}

// ─── Chrome over the DevTools protocol ────────────────────────────────────

async function launchChrome() {
  const profile = mkdtempSync(path.join(tmpdir(), 'playground-capture-'));
  const chrome = spawn(CHROME, [
    '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--mute-audio',
    '--use-angle=metal', '--autoplay-policy=no-user-gesture-required',
    `--window-size=${WIDTH},${HEIGHT}`, 'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  const wsUrl = await new Promise((resolve, reject) => {
    let buf = '';
    chrome.stderr.on('data', d => {
      buf += d;
      const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
      if (m) resolve(m[1]);
    });
    chrome.on('exit', code => reject(new Error(`Chrome exited (${code}) before it was ready`)));
  });
  const ws = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });

  let nextId = 1;
  const pending = new Map();
  const listeners = new Set();
  ws.onmessage = ({ data }) => {
    const msg = JSON.parse(data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    } else if (msg.method) {
      listeners.forEach(fn => fn(msg));
    }
  };
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params, sessionId }));
  });
  const close = () => { ws.close(); chrome.kill(); setTimeout(() => rmSync(profile, { recursive: true, force: true }), 500); };
  return { send, on: fn => { listeners.add(fn); return () => listeners.delete(fn); }, close };
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function openPage(cdp, url) {
  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  const s = (method, params) => cdp.send(method, params, sessionId);
  await s('Page.enable');
  await s('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: HEIGHT, deviceScaleFactor: 1, mobile: false });
  // Capture the light, full-motion version of each page, as a first visit sees it
  await s('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }, { name: 'prefers-reduced-motion', value: 'no-preference' }] });
  const loaded = new Promise(resolve => {
    const off = cdp.on(msg => {
      if (msg.sessionId === sessionId && msg.method === 'Page.loadEventFired') { off(); resolve(); }
    });
  });
  await s('Page.navigate', { url });
  await Promise.race([loaded, sleep(20000)]);
  return { s, sessionId, targetId };
}

async function click(s, [x, y]) {
  for (const type of ['mousePressed', 'mouseReleased']) {
    await s('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1 });
  }
}

async function screenshot(s) {
  const { data } = await s('Page.captureScreenshot', {
    format: 'webp', quality: 80,
    clip: { x: 0, y: 0, width: WIDTH, height: HEIGHT, scale: SCALE },
  });
  return Buffer.from(data, 'base64');
}

/**
 * Records the page with Page.startScreencast, then re-plays the frames onto a
 * canvas in a second tab and encodes them with MediaRecorder, so Chrome does
 * the video encoding and nothing else needs installing.
 */
async function record(cdp, page, seconds, frameServer) {
  const frames = [];
  const span = () => (frames.length > 1 ? frames[frames.length - 1].t - frames[0].t : 0);
  const off = cdp.on(msg => {
    if (msg.sessionId !== page.sessionId || msg.method !== 'Page.screencastFrame') return;
    page.s('Page.screencastFrameAck', { sessionId: msg.params.sessionId }).catch(() => {});
    const t = msg.params.metadata.timestamp;
    // keep at most 30 frames a second; the video is 30 fps
    if (frames.length && t - frames[frames.length - 1].t < 1 / 30) return;
    frames.push({ data: Buffer.from(msg.params.data, 'base64'), t });
  });
  await page.s('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: WIDTH * SCALE, maxHeight: HEIGHT * SCALE });
  // Frames can start late, so go by their own timestamps rather than the clock
  const deadline = Date.now() + seconds * 3000;
  while (span() < seconds && Date.now() < deadline) await sleep(200);
  await page.s('Page.stopScreencast');
  off();
  if (frames.length < 2) throw new Error('the page did not repaint while recording');

  frameServer.frames = frames;
  const encoder = await openPage(cdp, `${frameServer.base}__encoder`);
  const { result } = await encoder.s('Runtime.evaluate', {
    awaitPromise: true,
    returnByValue: true,
    expression: `(${encodeInPage.toString()})(${JSON.stringify(frames.map(f => f.t))}, ${WIDTH * SCALE}, ${HEIGHT * SCALE})`,
  });
  await cdp.send('Target.closeTarget', { targetId: encoder.targetId });
  if (!result.value || result.value.error) throw new Error(result.value ? result.value.error : 'encoder failed');
  return { type: result.value.type, data: Buffer.from(result.value.data, 'base64'), frames: frames.length };
}

/* Runs inside Chrome: draws each frame at its original time and records the canvas. */
async function encodeInPage(times, width, height) {
  const images = await Promise.all(times.map((_, i) => new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = `/__frames/${i}.jpg`;
  })));
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(images[0], 0, 0, width, height);
  // H.264 MP4 plays everywhere, Safari included; WebM is the fallback for older Chromes
  const type = ['video/mp4;codecs=avc1.42E01E', 'video/webm;codecs=vp9', 'video/webm;codecs=vp8']
    .find(t => MediaRecorder.isTypeSupported(t));
  if (!type) return { error: 'no MediaRecorder video format' };
  const stream = canvas.captureStream(30);
  const recorder = new MediaRecorder(stream, { mimeType: type, videoBitsPerSecond: 1_200_000 });
  const chunks = [];
  recorder.ondataavailable = e => e.data.size && chunks.push(e.data);
  const done = new Promise(resolve => { recorder.onstop = resolve; });
  recorder.start();
  const start = performance.now();
  const t0 = times[0];
  for (let i = 0; i < images.length; i++) {
    const due = (times[i] - t0) * 1000;
    const wait = due - (performance.now() - start);
    if (wait > 0) await new Promise(r => setTimeout(r, wait));
    ctx.drawImage(images[i], 0, 0, width, height);
  }
  await new Promise(r => setTimeout(r, 120));
  recorder.stop();
  await done;
  const blob = new Blob(chunks, { type });
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let bin = '';
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return { type, data: btoa(bin) };
}

// ─── main ─────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const withPreview = args.includes('--preview');
const named = args.filter(a => !a.startsWith('--'));
const projects = collectProjects();
const targets = named.length
  ? named.map(d => projects.find(p => p.dir === d) || (() => { throw new Error(`No project folder "${d}"`); })())
  : projects.filter(p => !p.thumbnail && (p.siteUrl || CAPTURE[p.dir]?.path));

if (!targets.length) {
  console.log('Every project with a site already has a thumbnail. Name projects to retake them.');
  process.exit(0);
}

const frameServer = { base: '', frames: [] };
const server = await serve(frameServer);
const base = `http://127.0.0.1:${server.address().port}/`;
frameServer.base = base;

const cdp = await launchChrome();
let failures = 0;

for (const p of targets) {
  const opts = CAPTURE[p.dir] || {};
  let url;
  if (opts.path) url = `${base}${p.dir}/${opts.path}`;
  else if (p.siteUrl && p.siteUrl.startsWith(GITHUB_PAGES_BASE)) url = base + p.siteUrl.slice(GITHUB_PAGES_BASE.length);
  else url = p.siteUrl;
  if (!url) { console.log(`– ${p.dir}: no site to capture`); continue; }

  try {
    const page = await openPage(cdp, url);
    if (opts.click) { await sleep(800); await click(page.s, opts.click); }
    await sleep(opts.wait ?? 2500);
    const image = await screenshot(page.s);
    writeFileSync(path.join(ROOT, p.dir, 'thumbnail.webp'), image);
    let note = `thumbnail.webp ${(image.length / 1024).toFixed(0)} KB`;
    if (withPreview) {
      const video = await record(cdp, page, opts.seconds ?? 6, frameServer);
      const ext = video.type.startsWith('video/mp4') ? 'mp4' : 'webm';
      writeFileSync(path.join(ROOT, p.dir, `preview.${ext}`), video.data);
      note += `, preview.${ext} ${(video.data.length / 1024).toFixed(0)} KB from ${video.frames} frames`;
    }
    await cdp.send('Target.closeTarget', { targetId: page.targetId });
    console.log(`✓ ${p.dir}: ${note}  (${url})`);
  } catch (err) {
    failures++;
    console.log(`✗ ${p.dir}: ${err.message}  (${url})`);
  }
}

cdp.close();
server.close();
process.exit(failures ? 1 : 0);
