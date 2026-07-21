// Export helpers: MIDI file, rendered WAV audio, score PNG, file download.
import { buildVoicePlayers } from './audio-engine.js';

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

// ---------- MIDI ----------
const PPQ = 480;
const NOTE_MAP = {
  cymbal: 49, snare: 38,
  tenor1: 50, tenor2: 48, tenor3: 47, tenor4: 45, tenor5: 43, tenor6: 41,
  bass1: 45, bass2: 43, bass3: 41, bass4: 36, bass5: 35,
};
const GROUP_ROWS = {
  Cymbal: ['cymbal'], Snare: ['snare'],
  Tenors: ['tenor1', 'tenor2', 'tenor3', 'tenor4', 'tenor5', 'tenor6'],
  Basses: ['bass1', 'bass2', 'bass3', 'bass4', 'bass5'],
};

function vlq(n) {
  n = Math.max(0, Math.round(n));
  const bytes = [n & 0x7f];
  while ((n >>= 7)) bytes.unshift((n & 0x7f) | 0x80);
  return bytes;
}
function u32(n) { return [(n >> 24) & 255, (n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function u16(n) { return [(n >> 8) & 255, n & 255]; }
function str(s) { return [...s].map(c => c.charCodeAt(0)); }
function trackChunk(events) {
  return [...str('MTrk'), ...u32(events.length), ...events];
}

export function buildMidi(project) {
  const { sections, beatSubs, notes, tempo } = project;
  const tempoTrack = [
    0, 0xff, 0x51, 0x03, ...u32(Math.round(60000000 / tempo)).slice(1),
    0, 0xff, 0x58, 0x04, 4, 2, 24, 8,
    0, 0xff, 0x2f, 0x00,
  ];
  const tracks = [trackChunk(tempoTrack)];
  for (const [name, rowIds] of Object.entries(GROUP_ROWS)) {
    const evts = [];
    let tickOff = 0;
    for (const s of sections) {
      const subs = beatSubs[s.id];
      for (let b = 0; b < subs.length; b++) {
        const sc = subs[b];
        const subTicks = PPQ / sc;
        for (let sub = 0; sub < sc; sub++) {
          const t = tickOff + b * PPQ + sub * subTicks;
          for (const rowId of rowIds) {
            const v = notes[s.id]?.[rowId]?.[b]?.[sub];
            if (!v) continue;
            const note = NOTE_MAP[rowId];
            const len = Math.min(110, subTicks - 10);
            const push = (tick, vel, l) => {
              evts.push({ tick: Math.max(0, tick), type: 1, note, vel });
              evts.push({ tick: Math.max(0, tick) + l, type: 0, note, vel: 64 });
            };
            if (v === 1) push(t, 92, len);
            else if (v === 2) push(t, 115, len);
            else if (v === 3) { push(t - 40, 56, 36); push(t, 92, len); }
            else if (v === 4) { push(t, 92, subTicks / 2 - 6); push(t + subTicks / 2, 92, len / 2); }
            else if (v === 5) { for (let i = 0; i < 4; i++) push(t + i * subTicks / 4, i === 0 ? 92 : 56, subTicks / 4 - 4); }
          }
        }
      }
      tickOff += s.measures * 4 * PPQ;
    }
    evts.sort((a, b2) => a.tick - b2.tick || a.type - b2.type);
    const data = [0, 0xff, 0x03, name.length, ...str(name)];
    let last = 0;
    for (const e of evts) {
      data.push(...vlq(e.tick - last));
      last = e.tick;
      data.push(e.type ? 0x99 : 0x89, e.note, Math.round(e.vel));
    }
    data.push(0, 0xff, 0x2f, 0x00);
    tracks.push(trackChunk(data));
  }
  const bytes = [...str('MThd'), ...u32(6), ...u16(1), ...u16(tracks.length), ...u16(PPQ), ...tracks.flat()];
  return new Uint8Array(bytes);
}

// ---------- WAV ----------
function encodeWav(audioBuffer) {
  const ch = audioBuffer.getChannelData(0);
  const n = ch.length, rate = audioBuffer.sampleRate;
  const buf = new ArrayBuffer(44 + n * 2);
  const dv = new DataView(buf);
  const ws = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
  ws(0, 'RIFF'); dv.setUint32(4, 36 + n * 2, true); ws(8, 'WAVE'); ws(12, 'fmt ');
  dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true);
  dv.setUint32(24, rate, true); dv.setUint32(28, rate * 2, true); dv.setUint16(32, 2, true); dv.setUint16(34, 16, true);
  ws(36, 'data'); dv.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) {
    const v = Math.max(-1, Math.min(1, ch[i]));
    dv.setInt16(44 + i * 2, v < 0 ? v * 0x8000 : v * 0x7fff, true);
  }
  return new Blob([buf], { type: 'audio/wav' });
}

export async function renderWav(project) {
  const { sections, beatSubs, notes, tempo, swing } = project;
  const beatDur = 60 / tempo;
  let total = 0.1;
  for (const s of sections) total += s.measures * 4 * beatDur;
  const ctx = new OfflineAudioContext(1, Math.ceil((total + 0.6) * 44100), 44100);
  const players = buildVoicePlayers();
  let off = 0.05;
  for (const s of sections) {
    const subs = beatSubs[s.id];
    for (let b = 0; b < subs.length; b++) {
      const sc = subs[b];
      const dur = beatDur / sc;
      for (let sub = 0; sub < sc; sub++) {
        let t = off + b * beatDur + sub * dur;
        if (sc % 2 === 0 && sub % 2 === 1) t += dur * (swing / 100) * 0.5;
        for (const rowId in players) {
          const v = notes[s.id]?.[rowId]?.[b]?.[sub];
          if (!v) continue;
          const play = players[rowId];
          if (v === 1) play(ctx, t, ctx.destination, 1);
          else if (v === 2) play(ctx, t, ctx.destination, 2);
          else if (v === 3) { play(ctx, Math.max(0.001, t - 0.028), ctx.destination, 0); play(ctx, t, ctx.destination, 1); }
          else if (v === 4) { play(ctx, t, ctx.destination, 1); play(ctx, t + dur / 2, ctx.destination, 1); }
          else if (v === 5) { for (let i = 0; i < 4; i++) play(ctx, t + i * dur / 4, ctx.destination, i === 0 ? 1 : 0); }
        }
      }
    }
    off += s.measures * 4 * beatDur;
  }
  const rendered = await ctx.startRendering();
  return encodeWav(rendered);
}

// ---------- Score PNG ----------
const INK = '#16181f';
const GRAY = '#7a7f8c';
const LINE = '#565b68';

function drawShapes(ctx, s, ox, oy) {
  ctx.strokeStyle = LINE; ctx.lineWidth = 1;
  for (const ln of s.lines) { ctx.beginPath(); ctx.moveTo(ox + 16, oy + ln.y); ctx.lineTo(ox + s.lineEndX, oy + ln.y); ctx.stroke(); }
  ctx.strokeStyle = '#2b2e38';
  for (const bl of s.barlines) { ctx.lineWidth = bl.w; ctx.beginPath(); ctx.moveTo(ox + bl.x, oy + s.barTop); ctx.lineTo(ox + bl.x, oy + s.barBot); ctx.stroke(); }
  ctx.fillStyle = INK;
  ctx.fillRect(ox + 20, oy + s.clefY, 3.6, 16);
  ctx.fillRect(ox + 27, oy + s.clefY, 3.6, 16);
  ctx.textAlign = 'left';
  ctx.font = 'bold 15px Georgia, serif';
  ctx.fillText('4', ox + 42, oy + s.ts1Y);
  ctx.fillText('4', ox + 42, oy + s.ts2Y);
  ctx.fillStyle = GRAY; ctx.font = 'italic 9px Georgia, serif';
  for (const mn of s.measureNums) ctx.fillText(mn.n, ox + mn.x, oy + s.numY);
  ctx.strokeStyle = INK;
  ctx.lineWidth = 1.3;
  for (const st of s.stems) { ctx.beginPath(); ctx.moveTo(ox + st.x, oy + st.y1); ctx.lineTo(ox + st.x, oy + st.y2); ctx.stroke(); }
  ctx.lineWidth = 3.4;
  for (const bm of [...s.beams, ...s.beams2]) { ctx.beginPath(); ctx.moveTo(ox + bm.x1, oy + bm.y); ctx.lineTo(ox + bm.x2, oy + bm.y); ctx.stroke(); }
  ctx.lineWidth = 2.2;
  for (const fl of s.flags) { ctx.beginPath(); ctx.moveTo(ox + fl.x1, oy + fl.y1); ctx.lineTo(ox + fl.x2, oy + fl.y2); ctx.stroke(); }
  ctx.lineWidth = 1.8;
  for (const sl of s.slashes) { ctx.beginPath(); ctx.moveTo(ox + sl.x1, oy + sl.y1); ctx.lineTo(ox + sl.x2, oy + sl.y2); ctx.stroke(); }
  ctx.fillStyle = INK; ctx.textAlign = 'center';
  ctx.font = 'italic bold 10px Georgia, serif';
  for (const tp of s.tuplets) ctx.fillText('3', ox + tp.x, oy + tp.y);
  ctx.font = 'bold 11px Georgia, serif';
  for (const ac of s.accents) ctx.fillText('>', ox + ac.x, oy + ac.y);
  ctx.font = 'italic bold 11px Georgia, serif';
  for (const zz of s.zs) ctx.fillText('z', ox + zz.x, oy + zz.y);
  ctx.lineWidth = 1.1;
  for (const gr of s.graces) {
    ctx.beginPath(); ctx.arc(ox + gr.x, oy + gr.y, 3.1, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(ox + gr.sx, oy + gr.sy1); ctx.lineTo(ox + gr.sx, oy + gr.sy2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ox + gr.k1x, oy + gr.k1y); ctx.lineTo(ox + gr.k2x, oy + gr.k2y); ctx.stroke();
  }
  for (const nt of s.notes) {
    if (nt.isX) {
      ctx.lineWidth = 1.7;
      ctx.beginPath(); ctx.moveTo(ox + nt.x1a, oy + nt.y1a); ctx.lineTo(ox + nt.x2a, oy + nt.y2a); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(ox + nt.x1b, oy + nt.y1b); ctx.lineTo(ox + nt.x2b, oy + nt.y2b); ctx.stroke();
    } else {
      ctx.beginPath(); ctx.ellipse(ox + nt.x, oy + nt.y, 5.2, 3.9, -18 * Math.PI / 180, 0, Math.PI * 2); ctx.fill();
    }
  }
  ctx.textAlign = 'left';
}

export async function renderScorePng(sectionsRender, meta) {
  const M = 40, scale = 2;
  let maxW = 0;
  for (const sec of sectionsRender) for (const g of sec.groups) maxW = Math.max(maxW, g.shapes.width);
  let H = 84;
  for (const sec of sectionsRender) {
    H += 30;
    for (const g of sec.groups) H += 14 + g.shapes.height + 6;
    H += 14;
  }
  const W = maxW + M * 2;
  const canvas = document.createElement('canvas');
  canvas.width = W * scale; canvas.height = H * scale;
  const ctx = canvas.getContext('2d');
  ctx.scale(scale, scale);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = INK;
  ctx.font = 'bold 22px Georgia, serif';
  ctx.fillText(meta.title, M, 40);
  ctx.fillStyle = GRAY;
  ctx.font = 'italic 12px Georgia, serif';
  ctx.fillText('Tempo: ' + meta.tempo + ' BPM · 4/4', M, 60);
  let y = 84;
  for (const sec of sectionsRender) {
    ctx.fillStyle = INK;
    ctx.font = 'bold 14px Georgia, serif';
    ctx.fillText(sec.name, M, y + 14);
    y += 30;
    for (const g of sec.groups) {
      ctx.fillStyle = g.color;
      ctx.font = 'bold 8px system-ui, sans-serif';
      ctx.fillText(g.name.toUpperCase(), M, y + 8);
      drawShapes(ctx, g.shapes, M, y + 12);
      y += 14 + g.shapes.height + 6;
    }
    y += 14;
  }
  const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
  downloadBlob(blob, 'dut-dut-score.png');
}
