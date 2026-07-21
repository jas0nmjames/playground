// Synthesized drumline voices — no sample files needed for playback preview.
let noiseBufferCache = null;
function getNoiseBuffer(ctx) {
  if (noiseBufferCache && noiseBufferCache.sampleRate === ctx.sampleRate) return noiseBufferCache;
  const buffer = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
  noiseBufferCache = buffer;
  return buffer;
}

function gainFor(vel) {
  // vel: 0 grace/buzz (quiet), 1 normal, 2 accent
  return vel === 2 ? 1.15 : vel === 0 ? 0.45 : 0.85;
}

export function playSnare(ctx, time, destination, vel = 1) {
  const g = gainFor(vel);
  const noise = ctx.createBufferSource();
  noise.buffer = getNoiseBuffer(ctx);
  const bandpass = ctx.createBiquadFilter();
  bandpass.type = 'bandpass';
  bandpass.frequency.value = 1800;
  const noiseGain = ctx.createGain();
  noiseGain.gain.setValueAtTime(g, time);
  noiseGain.gain.exponentialRampToValueAtTime(0.001, time + 0.15);
  noise.connect(bandpass).connect(noiseGain).connect(destination);
  noise.start(time);
  noise.stop(time + 0.2);

  const osc = ctx.createOscillator();
  osc.type = 'triangle';
  osc.frequency.setValueAtTime(180, time);
  const oscGain = ctx.createGain();
  oscGain.gain.setValueAtTime(0.6 * g, time);
  oscGain.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
  osc.connect(oscGain).connect(destination);
  osc.start(time);
  osc.stop(time + 0.1);
}

export function playCymbal(ctx, time, destination, vel = 1) {
  const g = gainFor(vel);
  const noise = ctx.createBufferSource();
  noise.buffer = getNoiseBuffer(ctx);
  const highpass = ctx.createBiquadFilter();
  highpass.type = 'highpass';
  highpass.frequency.value = 6000;
  const gain = ctx.createGain();
  gain.gain.setValueAtTime(0.7 * g, time);
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.5);
  noise.connect(highpass).connect(gain).connect(destination);
  noise.start(time);
  noise.stop(time + 0.5);
}

// idx 0 = highest-pitched tenor (T1) .. 5 = lowest (T6)
export function playTenor(ctx, time, destination, idx, vel = 1) {
  const g = gainFor(vel);
  const freq = 380 - idx * 38;
  const noise = ctx.createBufferSource();
  noise.buffer = getNoiseBuffer(ctx);
  const bandpass = ctx.createBiquadFilter();
  bandpass.type = 'bandpass';
  bandpass.frequency.value = freq * 4;
  const noiseGain = ctx.createGain();
  noiseGain.gain.setValueAtTime(0.4 * g, time);
  noiseGain.gain.exponentialRampToValueAtTime(0.001, time + 0.09);
  noise.connect(bandpass).connect(noiseGain).connect(destination);
  noise.start(time);
  noise.stop(time + 0.12);

  const osc = ctx.createOscillator();
  osc.type = 'triangle';
  osc.frequency.setValueAtTime(freq, time);
  osc.frequency.exponentialRampToValueAtTime(freq * 0.85, time + 0.12);
  const oscGain = ctx.createGain();
  oscGain.gain.setValueAtTime(0.75 * g, time);
  oscGain.gain.exponentialRampToValueAtTime(0.001, time + 0.14);
  osc.connect(oscGain).connect(destination);
  osc.start(time);
  osc.stop(time + 0.14);
}

// idx 0 = highest-pitched bass (B1) .. 4 = lowest (B5)
export function playBassDrum(ctx, time, destination, idx, vel = 1) {
  const g = gainFor(vel);
  const startFreq = 180 - idx * 28;
  const endFreq = 55 - idx * 5;
  const osc = ctx.createOscillator();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(startFreq, time);
  osc.frequency.exponentialRampToValueAtTime(Math.max(endFreq, 30), time + 0.18);
  const gain = ctx.createGain();
  gain.gain.setValueAtTime(g, time);
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.38);
  osc.connect(gain).connect(destination);
  osc.start(time);
  osc.stop(time + 0.38);
}

export function playMetronome(ctx, time, destination, accent) {
  const osc = ctx.createOscillator();
  osc.type = 'square';
  osc.frequency.setValueAtTime(accent ? 1600 : 1100, time);
  const gain = ctx.createGain();
  gain.gain.setValueAtTime(0.25, time);
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.04);
  osc.connect(gain).connect(destination);
  osc.start(time);
  osc.stop(time + 0.05);
}

export function buildVoicePlayers() {
  const players = { cymbal: (ctx, t, d, v) => playCymbal(ctx, t, d, v), snare: (ctx, t, d, v) => playSnare(ctx, t, d, v) };
  for (let i = 0; i < 6; i++) players[`tenor${i + 1}`] = (ctx, t, d, v) => playTenor(ctx, t, d, i, v);
  for (let i = 0; i < 5; i++) players[`bass${i + 1}`] = (ctx, t, d, v) => playBassDrum(ctx, t, d, i, v);
  return players;
}

const LOOKAHEAD_MS = 25;
const SCHEDULE_AHEAD_SEC = 0.1;

// Variable-duration scheduler: each position asks getDuration(pos), so beats can
// mix 8th / triplet / 16th subdivisions.
export class VarScheduler {
  constructor({ audioContext, getPositionCount, getDuration, onScheduleStep }) {
    this.ctx = audioContext;
    this.getPositionCount = getPositionCount;
    this.getDuration = getDuration;
    this.onScheduleStep = onScheduleStep;
    this.pos = 0;
    this.nextTime = 0;
    this.timerId = null;
    this.playing = false;
  }
  start() {
    if (this.playing) return;
    this.pos = 0;
    this.nextTime = this.ctx.currentTime + 0.05;
    this.playing = true;
    this.timerId = setInterval(() => this._tick(), LOOKAHEAD_MS);
  }
  stop() {
    this.playing = false;
    clearInterval(this.timerId);
    this.timerId = null;
  }
  _tick() {
    while (this.nextTime < this.ctx.currentTime + SCHEDULE_AHEAD_SEC) {
      const count = this.getPositionCount();
      if (this.pos >= count) this.pos = 0;
      this.onScheduleStep(this.pos, this.nextTime);
      this.nextTime += this.getDuration(this.pos);
      this.pos = (this.pos + 1) % count;
    }
  }
}
