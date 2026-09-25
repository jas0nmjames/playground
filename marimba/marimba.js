'use strict';

// The design's tweakable props, at their defaults.
const SETTINGS = {
  showNoteNames: true,
  showDegrees: true,
  decay: 1.4, // seconds (the design allows 0.5–3)
};

// E♭4–E♭5. Naturals sit in the front row, accidentals in the back; x is the bar's center in eighths of the frame's width.
const BARS = [
  { pc: 3, midi: 63, row: 'b', x: 0.5 }, { pc: 4, midi: 64, row: 'f', x: 1 }, { pc: 5, midi: 65, row: 'f', x: 2 },
  { pc: 6, midi: 66, row: 'b', x: 2.5 }, { pc: 7, midi: 67, row: 'f', x: 3 }, { pc: 8, midi: 68, row: 'b', x: 3.5 },
  { pc: 9, midi: 69, row: 'f', x: 4 }, { pc: 10, midi: 70, row: 'b', x: 4.5 }, { pc: 11, midi: 71, row: 'f', x: 5 },
  { pc: 0, midi: 72, row: 'f', x: 6 }, { pc: 1, midi: 73, row: 'b', x: 6.5 }, { pc: 2, midi: 74, row: 'f', x: 7 },
  { pc: 3, midi: 75, row: 'b', x: 7.5 },
];
const KEYS = 'QASEDRFTGHUJI'; // KEYS[i] plays BARS[i]: home row for naturals, the row above for accidentals, like a piano
const SCALES = { major: [0, 2, 4, 5, 7, 9, 11], minor: [0, 2, 3, 5, 7, 8, 10] };
const SOLFEGE = { major: ['Do', 'Re', 'Mi', 'Fa', 'Sol', 'La', 'Ti'], minor: ['Do', 'Re', 'Me', 'Fa', 'Sol', 'Le', 'Te'] };
const SHARP = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B'];
const FLAT = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'G♭', 'G', 'A♭', 'A', 'B♭', 'B'];
const FLAT_KEYS = { major: [5, 10, 3, 8, 1, 6], minor: [2, 7, 0, 5, 10, 3] }; // roots whose key signature uses flats

// A sine fundamental plus the two overtones a marimba bar is tuned to (4× and ~10×), which die away much faster,
// over a 40 ms burst of band-passed noise for the mallet.
class Synth {
  ensure() {
    if (!this.ctx) {
      this.ctx = new AudioContext();
      const compressor = this.ctx.createDynamicsCompressor();
      this.out = this.ctx.createGain();
      this.out.gain.value = 0.5;
      this.out.connect(compressor).connect(this.ctx.destination);
      const rate = this.ctx.sampleRate;
      this.noise = this.ctx.createBuffer(1, Math.floor(rate * 0.04), rate);
      const data = this.noise.getChannelData(0);
      for (let i = 0; i < data.length; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / data.length) ** 3;
    }
    this.resume();
  }

  // Audio may only start on a user activation, and a touch's pointerdown isn't one — so the context a first tap
  // creates can start suspended. Resuming again on the pointerup/touchend that follows lets that first note sound.
  resume() {
    if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume();
  }

  play(midi, decay) {
    this.ensure();
    const { ctx } = this;
    const t = ctx.currentTime;
    const f = 440 * 2 ** ((midi - 69) / 12);
    for (const [ratio, peak, length] of [[1, 0.8, decay], [4, 0.2, decay * 0.22], [9.9, 0.05, decay * 0.07]]) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = f * ratio;
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(peak, t + 0.003);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + length);
      osc.connect(gain).connect(this.out);
      osc.start(t);
      osc.stop(t + length + 0.05);
    }
    const mallet = ctx.createBufferSource();
    const band = ctx.createBiquadFilter();
    const gain = ctx.createGain();
    mallet.buffer = this.noise;
    band.type = 'bandpass';
    band.frequency.value = Math.min(f * 5, 8000);
    band.Q.value = 1.2;
    gain.gain.value = 0.3;
    mallet.connect(band).connect(gain).connect(this.out);
    mallet.start(t);
  }
}

const state = { root: 3, mode: 'major' };
const synth = new Synth();
const held = new Set(); // pointers pressed on a bar; sliding one onto another bar plays it too

const marimba = document.querySelector('.marimba');
const rails = marimba.querySelector('.marimba__rails');
const keySelect = document.querySelector('.key-select');
const modeButtons = [...document.querySelectorAll('.mode-toggle button')];
const keyName = document.querySelector('.hint__key');
const cards = [...document.querySelectorAll('.card')];

// Lengths and centers are % of the frame's height. Each semitone up is 2^(-1/24) shorter, so an octave is 1/√2 as long.
function geometry({ row, midi }) {
  const front = row === 'f';
  const scale = 2 ** (-(midi - 63) / 24);
  return { front, length: (front ? 50 : 38) * scale, center: front ? 66 : 24, width: front ? 0.84 : 0.72 };
}

// 1–7 within the current key, 0 when the pitch class is out of it.
const degreeOf = pc => SCALES[state.mode].indexOf((pc - state.root + 12) % 12) + 1;

const bars = BARS.map((bar, i) => {
  const { front, length, center, width } = geometry(bar);
  const el = document.createElement('div');
  el.className = 'bar';
  Object.assign(el.style, {
    left: `${(bar.x - width / 2) / 8 * 100}%`,
    width: `${width / 8 * 100}%`,
    top: `${center - length / 2}%`,
    height: `${length}%`,
    zIndex: front ? 2 : 1,
  });
  el.innerHTML = '<span class="bar__nail"></span><span class="bar__nail"></span><span class="bar__degree"></span><span class="bar__name"></span>';

  el.addEventListener('pointerdown', e => {
    e.preventDefault();
    // Touch pointers are implicitly captured by the bar they land on; release so pointerenter fires on the others.
    if (el.hasPointerCapture(e.pointerId)) el.releasePointerCapture(e.pointerId);
    held.add(e.pointerId);
    hit(i);
  });
  el.addEventListener('pointerenter', e => {
    if (!held.has(e.pointerId)) return;
    if (!e.buttons) held.delete(e.pointerId); // released somewhere we never heard about, e.g. outside the window
    else hit(i);
  });

  marimba.append(el);
  return { el, degree: el.querySelector('.bar__degree'), name: el.querySelector('.bar__name') };
});

// Two rails per row, under the nail holes (22% and 78% along each bar), from the row's first bar to its last and
// overhanging each end by 0.45. The SVG's 800 × 500 viewBox maps x (eighths) × 100 and y (%) × 5.
for (const row of ['f', 'b']) {
  const rowBars = BARS.filter(b => b.row === row);
  const first = rowBars[0], last = rowBars[rowBars.length - 1];
  const a = geometry(first), z = geometry(last);
  for (const k of [-0.28, 0.28]) {
    const ya = a.center + k * a.length, yz = z.center + k * z.length;
    const slope = (yz - ya) / (last.x - first.x);
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', (first.x - 0.45) * 100);
    line.setAttribute('y1', (ya - slope * 0.45) * 5);
    line.setAttribute('x2', (last.x + 0.45) * 100);
    line.setAttribute('y2', (yz + slope * 0.45) * 5);
    rails.append(line);
  }
}

function render() {
  const { root, mode } = state;
  const names = FLAT_KEYS[mode].includes(root) ? FLAT : SHARP;
  bars.forEach(({ el, degree, name }, i) => {
    const d = degreeOf(BARS[i].pc);
    if (d) el.dataset.degree = d;
    else delete el.dataset.degree;
    degree.textContent = SETTINGS.showDegrees && d ? d : '';
    name.textContent = SETTINGS.showNoteNames ? names[BARS[i].pc] : '';
  });
  for (const card of cards) card.querySelector('.card__solfege').textContent = SOLFEGE[mode][card.dataset.degree - 1];
  keyName.textContent = `${names[root]} ${mode}`;
  keySelect.value = root;
  for (const button of modeButtons) button.setAttribute('aria-pressed', button.value === mode);
}

function hit(i) {
  synth.play(BARS[i].midi, SETTINGS.decay);
  bars[i].el.animate(
    [{ transform: 'scale(0.93)', filter: 'brightness(1.1)' }, { transform: 'scale(1)', filter: 'brightness(1)' }],
    { duration: 380, easing: 'cubic-bezier(.2,.8,.2,1)' },
  );

  // Ring the matching card, then let a second ring ripple out and fade.
  const card = cards.find(c => Number(c.dataset.degree) === degreeOf(BARS[i].pc));
  if (!card) return;
  const channels = getComputedStyle(card).getPropertyValue('--deg').trim();
  const color = alpha => `oklch(${channels} / ${alpha})`;
  card.animate([
    { boxShadow: `0 0 0 3px ${color(1)}, 0 0 0 3px ${color(0.6)}` },
    { boxShadow: `0 0 0 3px ${color(1)}, 0 0 0 18px ${color(0)}`, offset: 0.3 },
    { boxShadow: `0 0 0 3px ${color(0)}, 0 0 0 18px ${color(0)}` },
  ], { duration: 1600, easing: 'ease-out' });
}

window.addEventListener('keydown', e => {
  if (e.repeat || e.metaKey || e.ctrlKey || e.altKey || e.key.length !== 1) return;
  if (/^(SELECT|INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
  const i = KEYS.indexOf(e.key.toUpperCase());
  if (i >= 0) {
    e.preventDefault();
    hit(i);
  }
});

window.addEventListener('pointerup', e => {
  held.delete(e.pointerId);
  synth.resume();
});
window.addEventListener('pointercancel', e => held.delete(e.pointerId));
window.addEventListener('touchend', () => synth.resume());

keySelect.addEventListener('change', () => {
  state.root = Number(keySelect.value);
  render();
});
for (const button of modeButtons) {
  button.addEventListener('click', () => {
    state.mode = button.value;
    render();
  });
}

render();
