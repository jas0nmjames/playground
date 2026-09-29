'use strict';

// The design's tweakable props, at their defaults.
const SETTINGS = {
  showNoteNames: true,
  showDegrees: true,
  decay: 1.4, // seconds (the design allows 0.5–3)
};

// C3–C6, a practice-marimba range: naturals in the front row, accidentals in the back. x is the bar's center in
// natural-bar widths: a natural's center is n + 0.5 and an accidental sits on the line at n, where n counts the
// naturals below it.
const NATURALS = [0, 2, 4, 5, 7, 9, 11];
const BARS = [];
for (let midi = 48, n = 0; midi <= 84; midi++) {
  const pc = midi % 12;
  const front = NATURALS.includes(pc);
  BARS.push({ pc, midi, row: front ? 'f' : 'b', x: front ? n + 0.5 : n });
  if (front) n++;
}
const UNITS = BARS.filter(b => b.row === 'f').length; // the marimba is 22 naturals wide
const OCTAVES = 3; // the view stops at C3, C4 and C5, each showing 8 naturals (C to C)
const START_OCTAVE = 1; // opens on C4

// Piano layout relative to the octave in view: naturals on the home row (A–K, then L ; '), accidentals on the row
// above (W E, T Y U, O P). Values are semitones above the view's first C.
const PIANO_KEYS = { A: 0, W: 1, S: 2, E: 3, D: 4, F: 5, T: 6, G: 7, Y: 8, H: 9, U: 10, J: 11, K: 12, O: 13, L: 14, P: 15, ';': 16, "'": 17 };
const SCALES = { major: [0, 2, 4, 5, 7, 9, 11], minor: [0, 2, 3, 5, 7, 8, 10] };
const SOLFEGE = { major: ['Do', 'Re', 'Mi', 'Fa', 'Sol', 'La', 'Ti'], minor: ['Do', 'Re', 'Me', 'Fa', 'Sol', 'Le', 'Te'] };
const ROLES = {
  major: ['Tonic', 'Supertonic', 'Mediant', 'Subdominant', 'Dominant', 'Submediant', 'Leading tone'],
  minor: ['Tonic', 'Supertonic', 'Mediant', 'Subdominant', 'Dominant', 'Submediant', 'Subtonic'],
};
const INTERVALS = { // above the tonic
  major: ['unison', 'major 2nd', 'major 3rd', 'perfect 4th', 'perfect 5th', 'major 6th', 'major 7th'],
  minor: ['unison', 'major 2nd', 'minor 3rd', 'perfect 4th', 'perfect 5th', 'minor 6th', 'minor 7th'],
};
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

const state = { root: 0, mode: 'major' };
const synth = new Synth();
const held = new Set(); // pointers pressed on a bar; sliding one onto another bar plays it too
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');

const scroller = document.querySelector('.marimba-scroller');
const marimba = scroller.querySelector('.marimba');
const rails = marimba.querySelector('.marimba__rails');
const strip = document.querySelector('.scrub');
const thumb = strip.querySelector('.scrub__thumb');
const keySelect = document.querySelector('.key-select');
const modeButtons = [...document.querySelectorAll('.mode-toggle button')];
const keyName = document.querySelector('.hint__key');
const cards = [...document.querySelectorAll('.card-row .card')];

// Lengths and centers are % of the marimba's height. Each octave up is 2^(-1/3) as long.
function geometry({ row, midi }) {
  const front = row === 'f';
  const scale = 2 ** (-(midi - 60) / 36);
  return { front, length: (front ? 44 : 34) * scale, center: front ? 68 : 22, width: front ? 0.84 : 0.72 };
}

// 1–7 within the current key, 0 when the pitch class is out of it.
const degreeOf = pc => SCALES[state.mode].indexOf((pc - state.root + 12) % 12) + 1;

// Note names spelled for the current key.
const spelling = () => (FLAT_KEYS[state.mode].includes(state.root) ? FLAT : SHARP);

marimba.style.setProperty('--units', UNITS);

const bars = BARS.map((bar, i) => {
  const { length, center, width } = geometry(bar);
  const el = document.createElement('div');
  el.className = 'bar';
  el.dataset.row = bar.row;
  Object.assign(el.style, {
    left: `${(bar.x - width / 2) / UNITS * 100}%`,
    width: `${width / UNITS * 100}%`,
    top: `${center - length / 2}%`,
    height: `${length}%`,
  });
  el.innerHTML = '<span class="bar__nail"></span><span class="bar__nail"></span><span class="bar__degree"></span><span class="bar__name"></span>';

  el.addEventListener('pointerdown', e => {
    e.preventDefault();
    // Touch pointers are implicitly captured by the bar they land on; release so pointerenter fires on the others.
    if (el.hasPointerCapture(e.pointerId)) el.releasePointerCapture(e.pointerId);
    held.add(e.pointerId);
    play(i);
  });
  el.addEventListener('pointerenter', e => {
    if (!held.has(e.pointerId)) return;
    if (!e.buttons) held.delete(e.pointerId); // released somewhere we never heard about, e.g. outside the window
    else play(i);
  });

  marimba.append(el);
  return { el, degree: el.querySelector('.bar__degree'), name: el.querySelector('.bar__name') };
});

// Two rails per row, through every bar's nail holes (22% and 78% along it) and overhanging each end by 0.45 along
// the end segment. The viewBox maps x (natural widths) × 100 and y (%) × 5.
rails.setAttribute('viewBox', `0 0 ${UNITS * 100} 500`);
for (const row of ['f', 'b']) {
  const rowBars = BARS.filter(b => b.row === row);
  for (const k of [-0.28, 0.28]) {
    const points = rowBars.map(b => {
      const { center, length } = geometry(b);
      return [b.x, center + k * length];
    });
    const overhang = ([x, y], [px, py]) => {
      const dx = Math.abs(x - px);
      return [x + (x - px) / dx * 0.45, y + (y - py) / dx * 0.45];
    };
    points.unshift(overhang(points[0], points[1]));
    points.push(overhang(points[points.length - 1], points[points.length - 2]));
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    line.setAttribute('points', points.map(([x, y]) => `${(x * 100).toFixed(1)},${(y * 5).toFixed(1)}`).join(' '));
    rails.append(line);
  }
}

// One snap point per octave view, at its first C.
for (let o = 0; o < OCTAVES; o++) {
  const snap = document.createElement('span');
  snap.className = 'marimba__snap';
  snap.style.left = `${o * 7 / UNITS * 100}%`;
  marimba.append(snap);
}

// The strip is a minimap of the whole marimba, labelled under each C.
for (const bar of BARS.filter(b => b.pc === 0)) {
  const label = document.createElement('span');
  label.className = 'scrub__label';
  label.textContent = `C${bar.midi / 12 - 1}`;
  label.style.left = `${bar.x / UNITS * 100}%`;
  strip.append(label);
}

function render() {
  const { root, mode } = state;
  const names = spelling();
  bars.forEach(({ el, degree, name }, i) => {
    const d = degreeOf(BARS[i].pc);
    if (d) el.dataset.degree = d;
    else delete el.dataset.degree;
    degree.textContent = SETTINGS.showDegrees && d ? d : '';
    name.textContent = SETTINGS.showNoteNames ? names[BARS[i].pc] : '';
  });
  for (const card of cards) {
    const d = card.dataset.degree - 1;
    card.querySelector('.card__solfege').textContent = SOLFEGE[mode][d];
    card.querySelector('.card__image').textContent = INTERVALS[mode][d];
    card.querySelector('.card__title').textContent = ROLES[mode][d];
    card.querySelector('.card__note').textContent = names[(root + SCALES[mode][d]) % 12];
  }
  keyName.textContent = `${names[root]} ${mode}`;
  keySelect.value = root;
  for (const button of modeButtons) button.setAttribute('aria-pressed', button.value === mode);
}

function hit(i) {
  reveal(i);
  synth.play(BARS[i].midi, SETTINGS.decay);
  bars[i].el.animate(
    [{ transform: 'scale(0.93)', filter: 'brightness(1.1)' }, { transform: 'scale(1)', filter: 'brightness(1)' }],
    { duration: 380, easing: 'cubic-bezier(.2,.8,.2,1)' },
  );

  const card = cards.find(c => Number(c.dataset.degree) === degreeOf(BARS[i].pc));
  if (card) pulse(card);
}

// Ring a card in its degree's color, then let a second ring ripple out and fade.
function pulse(card) {
  const channels = getComputedStyle(card).getPropertyValue('--deg').trim();
  const color = alpha => `oklch(${channels} / ${alpha})`;
  card.animate([
    { boxShadow: `0 0 0 3px ${color(1)}, 0 0 0 3px ${color(0.6)}` },
    { boxShadow: `0 0 0 3px ${color(1)}, 0 0 0 18px ${color(0)}`, offset: 0.3 },
    { boxShadow: `0 0 0 3px ${color(0)}, 0 0 0 18px ${color(0)}` },
  ], { duration: 1600, easing: 'ease-out' });
}

// Octaves. The scroller snaps to one octave view at a time, and the keyboard plays whichever octave is in view.
const octaveWidth = () => scroller.scrollWidth * 7 / UNITS;
const octaveInView = () => Math.max(0, Math.min(OCTAVES - 1, Math.round(scroller.scrollLeft / octaveWidth())));

// Returns the scroll position it's heading to.
function goOctave(octave, smooth = true) {
  const left = Math.max(0, Math.min(OCTAVES - 1, octave)) * octaveWidth();
  scroller.scrollTo({ left, behavior: smooth && !reduceMotion.matches ? 'smooth' : 'auto' });
  return left;
}

// Keep a played bar in view. Neighbouring views share a C, so the C bars always sit at a view's edge; moving for them
// would bounce between octaves. Only a bar that's cut off or off screen moves the view, to the nearest octave that
// shows it whole.
function reveal(i) {
  const view = scroller.getBoundingClientRect();
  const bar = bars[i].el.getBoundingClientRect();
  if (bar.left >= view.left - 1 && bar.right <= view.right + 1) return;
  const left = bar.left - view.left + scroller.scrollLeft;
  const right = left + bar.width;
  const shows = o => left >= o * octaveWidth() - 1 && right <= o * octaveWidth() + scroller.clientWidth + 1;
  const current = octaveInView();
  const [nearest] = [...Array(OCTAVES).keys()].filter(shows).sort((a, b) => Math.abs(a - current) - Math.abs(b - current));
  if (nearest !== undefined) goOctave(nearest);
}

// The strip's thumb and value, and the scroller's edge fades, follow the scroll position.
function measure() {
  const { scrollLeft, scrollWidth, clientWidth } = scroller;
  const max = scrollWidth - clientWidth;
  const overflow = max > 2;
  strip.hidden = !overflow;
  scroller.classList.toggle('fade-left', overflow && scrollLeft > 2);
  scroller.classList.toggle('fade-right', overflow && scrollLeft < max - 2);
  thumb.style.left = `${scrollLeft / scrollWidth * 100}%`;
  thumb.style.width = `${Math.min(100, clientWidth / scrollWidth * 100)}%`;
  strip.setAttribute('aria-valuenow', max > 0 ? Math.round(scrollLeft / max * 100) : 0);
}

scroller.addEventListener('scroll', measure, { passive: true });
window.addEventListener('resize', measure);
const resizes = new ResizeObserver(measure);
resizes.observe(scroller);
resizes.observe(marimba);

// Strip gestures: a drag moves the view like a minimap (snapping off meanwhile), a flick pages one octave, a tap jumps
// to the octave under it, and letting go settles on the nearest octave.
let gesture = null;
let settling = 0; // counts settles, so a new gesture can cancel the last one's wait

strip.addEventListener('pointerdown', e => {
  e.preventDefault();
  try {
    strip.setPointerCapture(e.pointerId);
  } catch {} // the pointer is already gone
  settling++;
  gesture = { id: e.pointerId, x: e.clientX, t: performance.now(), scrollLeft: scroller.scrollLeft, octave: octaveInView(), moved: false };
  scroller.classList.add('is-dragging');
});

strip.addEventListener('pointermove', e => {
  if (e.pointerId !== gesture?.id) return;
  const dx = e.clientX - gesture.x;
  if (Math.abs(dx) > 6) gesture.moved = true;
  scroller.scrollLeft = gesture.scrollLeft + dx * scroller.scrollWidth / strip.getBoundingClientRect().width;
});

strip.addEventListener('pointerup', e => {
  if (e.pointerId !== gesture?.id) return;
  const { x, t, octave, moved } = gesture;
  const dx = e.clientX - x;
  if (!moved) {
    const r = strip.getBoundingClientRect();
    settle(Math.floor((e.clientX - r.left) / r.width * OCTAVES));
  } else if (performance.now() - t < 350 && Math.abs(dx) > 24) {
    settle(octave + Math.sign(dx));
  } else {
    settle(octaveInView());
  }
});

strip.addEventListener('pointercancel', e => {
  if (e.pointerId === gesture?.id) settle(octaveInView());
});

// Scroll to an octave at the end of a gesture. Snapping stays off until the view gets there: switching it back on
// mid-scroll can stop the scroll where it is.
function settle(octave) {
  gesture = null;
  const target = goOctave(octave);
  const run = ++settling;
  const started = performance.now();
  (function arrived() {
    if (run !== settling) return;
    if (Math.abs(scroller.scrollLeft - target) > 1 && performance.now() - started < 2000) requestAnimationFrame(arrived);
    else scroller.classList.remove('is-dragging');
  })();
}

strip.addEventListener('keydown', e => {
  const octave = { Home: 0, End: OCTAVES - 1 }[e.key];
  if (octave === undefined) return;
  e.preventDefault();
  goOctave(octave);
});

window.addEventListener('keydown', e => {
  if (secretDialog.open || /^(SELECT|INPUT|TEXTAREA)$/.test(e.target.tagName)) return; // the dialog handles Esc itself
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const arrow = { ArrowLeft: -1, ArrowRight: 1 }[e.key];
  if (arrow) {
    if (!/^(BUTTON|A|SUMMARY)$/.test(e.target.tagName)) {
      e.preventDefault();
      goOctave(octaveInView() + arrow);
    }
    return;
  }
  if (e.repeat || e.key.length !== 1) return;
  const key = e.key.toUpperCase();
  if (key === 'Z' || key === 'X') {
    e.preventDefault();
    goOctave(octaveInView() + (key === 'Z' ? -1 : 1));
    return;
  }
  if (!(key in PIANO_KEYS)) return;
  const i = octaveInView() * 12 + PIANO_KEYS[key];
  if (i < BARS.length) {
    e.preventDefault();
    play(i);
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

// Easter egg: C4 E4 G4 C5 — 1 (low), 3, 5, 1 (high) in C major, the key the page opens in — unlocks a hidden card.
// The pitches are fixed, so the melody is the same whichever key is selected.
// The ▶ button plays the melody and rings each bar as it sounds, so it can be matched by ear or by eye; the status
// beside it is a live region, and once the melody has played it also reads the notes and their keys aloud.
const SECRET = [12, 16, 19, 24]; // indexes into BARS
const SECRET_STEP = 650; // ms between the demo's notes

const secretBox = document.querySelector('.secret');
const secretButton = secretBox.querySelector('.secret__button');
const secretStatus = secretBox.querySelector('.secret__status');
const secretDots = SECRET.map(() => document.createElement('span'));
secretBox.querySelector('.secret__dots').append(...secretDots);
const secretDialog = document.querySelector('.secret-dialog');

const secret = {
  state: 'idle', // idle → demo (melody playing) → turn (waiting for the visitor) → unlocked
  recent: [], // the visitor's last few bars
  timers: [],
  status: '',
};

function setSecretState(next) {
  secret.state = next;
  secretBox.dataset.state = next;
}

function showDots(count) {
  secretDots.forEach((dot, n) => dot.classList.toggle('is-on', n < count));
}

// `spoken` is appended for screen readers only.
function showStatus(text, spoken = '') {
  if (secret.status === text + spoken) return; // don't re-announce an unchanged live region
  secret.status = text + spoken;
  secretStatus.textContent = text;
  if (spoken) {
    const extra = document.createElement('span');
    extra.className = 'visually-hidden';
    extra.textContent = spoken;
    secretStatus.append(extra);
  }
}

function stopDemo() {
  secret.timers.forEach(clearTimeout);
  secret.timers = [];
  for (const { el } of bars) el.classList.remove('is-cued');
}

function playDemo() {
  stopDemo();
  synth.ensure(); // start audio inside the click; the notes themselves play from timers
  setSecretState('demo');
  secret.recent = [];
  showDots(0);
  showStatus('Listen…');
  SECRET.forEach((i, n) => {
    secret.timers.push(setTimeout(() => {
      hit(i);
      showDots(n + 1);
      bars[i].el.classList.add('is-cued');
      secret.timers.push(setTimeout(() => bars[i].el.classList.remove('is-cued'), SECRET_STEP - 150));
    }, n * SECRET_STEP));
  });
  secret.timers.push(setTimeout(yourTurn, SECRET.length * SECRET_STEP + 300));
}

function yourTurn() {
  stopDemo();
  setSecretState('turn');
  showDots(0);
  const names = spelling();
  const notes = SECRET.map(i => names[BARS[i].pc].replace('♭', ' flat').replace('♯', ' sharp')).join(', ');
  const keys = SECRET.map(i => Object.keys(PIANO_KEYS).find(k => START_OCTAVE * 12 + PIANO_KEYS[k] === i)).join(', ');
  showStatus('Your turn', `: play ${notes} (from the middle octave, keys ${keys})`);
}

// The visitor played bar i. The demo calls hit() directly, so its notes never count.
function play(i) {
  if (secret.state === 'demo') yourTurn();
  hit(i);
  if (secret.state === 'unlocked') return;
  secret.recent = [...secret.recent, i].slice(-SECRET.length);
  const count = matched(secret.recent);
  if (count === SECRET.length) unlock();
  else if (secret.state === 'turn') {
    showDots(count);
    showStatus(count ? `${count} of ${SECRET.length}` : 'Your turn');
  }
}

// How many of the melody's opening notes the end of `recent` matches.
function matched(recent) {
  for (let n = Math.min(recent.length, SECRET.length); n > 0; n--) {
    if (recent.slice(-n).every((bar, j) => bar === SECRET[j])) return n;
  }
  return 0;
}

function unlock() {
  setSecretState('unlocked');
  secretButton.setAttribute('aria-label', 'Open the hidden card');
  showDots(SECRET.length);
  showStatus('Unlocked');
  setTimeout(openSecret, 450); // let the last note land first
}

function openSecret() {
  if (secretDialog.open) return;
  secretDialog.showModal();
  pulse(secretDialog.querySelector('.card'));
}

secretButton.addEventListener('click', () => (secret.state === 'unlocked' ? openSecret() : playDemo()));

// Clicking the backdrop closes the dialog, like Esc and the Close button.
secretDialog.addEventListener('click', e => {
  const r = secretDialog.getBoundingClientRect();
  const outside = e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
  if (e.target === secretDialog && outside) secretDialog.close();
});

// Everything the page downloaded, from the browser's resource timings (Google Fonts lets its sizes be read). A file
// the browser only revalidated reports just its headers, so each file's full size is remembered from the visit that
// downloaded it, and every visit estimates the same page.
function pageBytes() {
  let sizes = {};
  try {
    sizes = JSON.parse(localStorage.getItem('marimba-sizes')) || {};
  } catch {}
  let total = 0;
  for (const e of [...performance.getEntriesByType('navigation'), ...performance.getEntriesByType('resource')]) {
    if (e.name.startsWith('https://api.websitecarbon.com/')) continue;
    const url = e.entryType === 'navigation' ? e.name.split(/[?#]/)[0] : e.name;
    if (e.encodedBodySize > 0) sizes[url] = Math.max(e.transferSize, e.encodedBodySize);
    total += sizes[url] ?? e.transferSize;
  }
  try {
    localStorage.setItem('marimba-sizes', JSON.stringify(sizes));
  } catch {}
  return total;
}

// The Sustainable Web Design model with Website Carbon's constants, which reproduce its calculator exactly: 0.3 kWh
// per GiB at the 494 g CO₂e/kWh global grid average, with a quarter of views being repeat visits that load 2% of the
// page. The hosting isn't assumed to be green.
const carbonPerView = bytes => bytes * (0.75 + 0.25 * 0.02) / 2 ** 30 * 0.3 * 494;

// Footer: this page's carbon per view. Website Carbon measures it, and its answer is cached for a day. If it fails (its
// API has been answering 503) or takes over 10 seconds, the page estimates the figure from its own size instead, and
// doesn't cache that, so the next visit asks Website Carbon again.
function loadCarbon() {
  const line = document.querySelector('.carbon__line');
  const note = document.querySelector('.carbon__note');
  const source = document.querySelector('.carbon__source');
  const perView = c => `≈ ${c < 0.01 ? c.toFixed(3) : c.toFixed(2)} g CO₂e per view`;
  const show = (lineText, noteText) => {
    line.textContent = lineText;
    note.textContent = noteText;
  };
  const showMeasured = ({ c, p }) => show(perView(c), `Cleaner than ${Math.round(p)}% of pages tested`);
  const unavailable = () => show('Measured per view on the live site', 'Estimate unavailable here');
  const pageLoaded = new Promise(resolve => (document.readyState === 'complete' ? resolve() : addEventListener('load', resolve, { once: true })));
  const estimateHere = async () => {
    await Promise.all([pageLoaded, document.fonts.ready]);
    const bytes = pageBytes();
    if (!bytes) return unavailable();
    show(perView(carbonPerView(bytes)), `Estimated from this page's ${Math.round(bytes / 1000)} kB`);
    source.textContent = 'Sustainable Web Design';
    source.href = 'https://sustainablewebdesign.org/estimating-digital-emissions/';
  };

  const url = location.href.split('#')[0].split('?')[0];
  const key = `marimba-wcb:${url}`;
  try {
    const cached = JSON.parse(localStorage.getItem(key));
    if (cached && Date.now() - cached.t < 24 * 60 * 60 * 1000) return showMeasured(cached.d);
  } catch {}
  if (!/^https?:$/.test(location.protocol)) return unavailable();
  fetch(`https://api.websitecarbon.com/b?url=${encodeURIComponent(url)}`, { signal: AbortSignal.timeout?.(10000) })
    .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
    .then(data => {
      const d = { c: Number(data.c), p: Number(data.p) };
      if (!Number.isFinite(d.c) || !Number.isFinite(d.p)) throw new Error('unexpected response');
      showMeasured(d);
      try {
        localStorage.setItem(key, JSON.stringify({ t: Date.now(), d }));
      } catch {}
    })
    .catch(() => estimateHere().catch(unavailable));
}

render();
goOctave(START_OCTAVE, false);
measure();
requestAnimationFrame(measure);
setTimeout(measure, 500);
loadCarbon();
