/*
 * Page logic: runs the two chamber simulations (in Web Workers where
 * possible), turns the device over, and draws each frame.
 *
 * URL options:
 *   ?debug   show the particle fields and a stats readout
 *   ?seed=N  change the random seed
 *   ?still   start paused, as if reduced motion were requested
 *   ?main    simulate on the main thread instead of in workers
 */
(function () {
  'use strict';

  var DT = 1 / 240;          // simulation step; the tuning in sim.js assumes this value
  var MAX_STEPS = 8;         // per batch; if that is not enough the simulation runs in slow motion
  var FLIP_TIME = 1.3;       // seconds for a half turn
  var PREROLL = 0.3;         // seconds simulated before the first frame is shown

  var query = new URLSearchParams(location.search);
  var debug = query.has('debug');
  var seed = parseInt(query.get('seed'), 10) || 2686;
  var reduced = query.has('still') ||
    (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  var $ = function (id) { return document.getElementById(id); };
  var stage = $('stage'), device = $('device'), shadow = $('shadow');
  var fluidCanvas = $('fluid'), bubbleCanvas = $('bubbles'), shineA = $('shine-a'), shineB = $('shine-b');
  var playButton = $('play'), flipButton = $('flip'), autoBox = $('auto'), startButton = $('start');
  var hud = $('hud'), notice = $('notice');

  var geom = HGGeometry.build({});
  var view = { x0: -0.56, y0: -0.04, w: 1.12, h: geom.H + 0.08 };
  var GRAVITY = HGSim.DEFAULTS.gravity;

  // The two chambers are the same design. A slightly different nozzle
  // resistance makes them drip at slightly different rates, so the two
  // streams drift in and out of step as they do in the real toy.
  var CHAMBERS = [
    { sim: {}, seed: seed },
    { sim: { nozzleDrag: HGSim.DEFAULTS.nozzleDrag * 1.02 }, seed: seed + 101 }
  ];

  // ---- simulation hosts -------------------------------------------------

  function snapshot(chamber, ms, steps) {
    var buf = new Float32Array(chamber.n * 4);
    chamber.pack(buf);
    var last = chamber.lastDrop;
    return {
      n: chamber.n, buf: buf, time: chamber.time, census: chamber.census(),
      drops: chamber.dropCount, lastDrop: last ? { t: last.t, n: last.n } : null,
      ms: ms, steps: steps
    };
  }

  // Runs inside the worker. It only uses names that exist there.
  function workerBody() {
    var chamber = null;
    self.onmessage = function (e) {
      var m = e.data, t0 = performance.now(), steps = 0;
      if (m.type === 'init') {
        chamber = new self.HGSim.Chamber(self.HGGeometry.build(m.geom), m.sim, m.seed);
      } else if (m.type === 'step') {
        var g = m.g;
        for (var i = 0; i < g.length; i += 2) chamber.step(m.dt, g[i], g[i + 1]);
        steps = g.length / 2;
      }
      var s = self.HGSnapshot(chamber, performance.now() - t0, steps);
      s.id = m.id;
      self.postMessage(s, [s.buf.buffer]);
    };
  }

  function Host(config) {
    this.config = config;
    this.pending = {};
    this.nextId = 1;
    this.chamber = null;
    this.worker = null;
    var self = this;
    if (query.has('main') || typeof Worker === 'undefined') return;
    try {
      var src = '(' + HGGeometryModule.toString() + ')(self);\n' +
        '(' + HGSimModule.toString() + ')(self);\n' +
        'self.HGSnapshot = ' + snapshot.toString() + ';\n' +
        '(' + workerBody.toString() + ')();';
      this.worker = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
      this.worker.onmessage = function (e) {
        var done = self.pending[e.data.id];
        delete self.pending[e.data.id];
        if (done) done(e.data);
      };
      this.worker.onerror = function () { self._goLocal(); };
    } catch (err) {
      this.worker = null;
    }
  }

  // If a worker cannot be used, simulate on the main thread instead.
  Host.prototype._goLocal = function () {
    if (this.worker) { this.worker.terminate(); this.worker = null; }
    var waiting = this.pending;
    this.pending = {};
    for (var id in waiting) waiting[id](this._run(waiting[id].msg));
  };

  Host.prototype._run = function (m) {
    var t0 = performance.now(), steps = 0;
    if (m.type === 'init' || !this.chamber) {
      this.chamber = new HGSim.Chamber(geom, this.config.sim, this.config.seed);
    }
    if (m.type === 'step') {
      for (var i = 0; i < m.g.length; i += 2) this.chamber.step(m.dt, m.g[i], m.g[i + 1]);
      steps = m.g.length / 2;
    }
    return snapshot(this.chamber, performance.now() - t0, steps);
  };

  Host.prototype.call = function (m) {
    var self = this;
    if (!this.worker) return Promise.resolve(this._run(m));
    return new Promise(function (resolve) {
      m.id = self.nextId++;
      resolve.msg = m;
      self.pending[m.id] = resolve;
      self.worker.postMessage(m);
    });
  };

  var hosts = CHAMBERS.map(function (c) { return new Host(c); });
  var states = [null, null];
  var totalParticles = 0;

  // ---- time, turning and gravity ----------------------------------------

  var simTime = 0, accumulator = 0, inflight = false, manual = false;
  var running = !reduced, started = false, everPlayed = false;
  var turn = { from: 0, to: 0, t0: -1e9, queued: 0 };

  function turning(t) { return t < turn.t0 + FLIP_TIME; }
  function angleAt(t) {
    var u = (t - turn.t0) / FLIP_TIME;
    if (u >= 1) return turn.to;
    if (u <= 0) return turn.from;
    return turn.from + (turn.to - turn.from) * u * u * (3 - 2 * u);
  }
  function requestFlip(dir) {
    dir = dir < 0 ? -1 : 1;
    if (turning(simTime)) { turn.queued = dir; return; }
    turn.from = turn.to;
    turn.to = turn.from + dir * Math.PI;
    turn.t0 = simTime;
    idleSince = simTime;
    setRunning(true);
  }

  var bubbles = new HGBubbles(geom, seed);

  // Advance both chambers by a number of steps. Gravity for every step comes
  // from where the turn will be at that moment, so the liquid feels the turn.
  function launch(steps) {
    inflight = true;
    var g = new Float32Array(steps * 2);
    for (var k = 0; k < steps; k++) {
      var a = angleAt(simTime + k * DT);
      g[2 * k] = GRAVITY * Math.sin(a);
      g[2 * k + 1] = GRAVITY * Math.cos(a);
      bubbles.step(DT, g[2 * k], g[2 * k + 1]);
    }
    return Promise.all(hosts.map(function (h) {
      return h.call({ type: 'step', dt: DT, g: g });
    })).then(function (res) {
      states = res;
      simTime += steps * DT;
      inflight = false;
      afterStep();
    });
  }

  // ---- auto flip --------------------------------------------------------

  var idleSince = 0, lastLower = -1;
  function afterStep() {
    if (turn.queued && !turning(simTime)) { var q = turn.queued; turn.queued = 0; requestFlip(q); }
    var up = Math.cos(angleAt(simTime)) > 0;
    var upper = 0, lower = 0;
    states.forEach(function (s) {
      upper += up ? s.census.a : s.census.b;
      lower += up ? s.census.b : s.census.a;
    });
    if (lower !== lastLower) { lastLower = lower; idleSince = simTime; }
    if (autoBox.checked && !turning(simTime) && simTime - idleSince > 3.5 && upper < 0.12 * totalParticles) {
      requestFlip(1);
    }
  }

  // ---- layout and drawing -----------------------------------------------

  var renderer = null, backCanvas = document.createElement('canvas');
  var size = { w: 0, h: 0, sw: 0, sh: 0 };

  function layout() {
    var sw = stage.clientWidth, sh = stage.clientHeight;
    var unit = Math.floor(Math.min(sh * 0.9 / view.h, sw * 0.9 / view.w));
    if (unit < 50) unit = 50;
    var w = Math.round(view.w * unit), h = Math.round(view.h * unit);
    size = { w: w, h: h, sw: sw, sh: sh };
    device.style.width = w + 'px'; device.style.height = h + 'px';
    device.style.marginLeft = (-w / 2) + 'px'; device.style.marginTop = (-h / 2) + 'px';
    shadow.style.width = (w * 1.05) + 'px'; shadow.style.height = (w * 0.2) + 'px';
    shadow.style.marginLeft = (-w * 0.525) + 'px'; shadow.style.marginTop = (h / 2 - w * 0.14) + 'px';

    var dpr = Math.min(2, window.devicePixelRatio || 1);
    var bw = Math.round(w * dpr), bh = Math.round(h * dpr);
    [fluidCanvas, bubbleCanvas, shineA, shineB, backCanvas].forEach(function (c) { c.width = bw; c.height = bh; });
    HGGlass.drawBack(backCanvas, geom, view, HGLook.offsetB);
    HGGlass.drawShine(shineA, geom, view);
    HGGlass.drawShine(shineB, geom, view);
    if (renderer) renderer.resize(backCanvas);
  }

  function draw() {
    if (!states[0] || !renderer) return;
    var a = angleAt(simTime);
    renderer.draw(states[0], states[1], a);
    bubbles.draw(bubbleCanvas, view, a);

    var c = Math.cos(a), s = Math.sin(a);
    var bw = Math.abs(size.w * c) + Math.abs(size.h * s), bh = Math.abs(size.w * s) + Math.abs(size.h * c);
    var zoom = Math.min(1, size.sw * 0.98 / bw, size.sh * 0.98 / bh);
    device.style.transform = 'rotate(' + a.toFixed(4) + 'rad) scale(' + zoom.toFixed(4) + ')';
    // The reflections belong to the room, not the device: fade to a copy
    // that is drawn the other way up as the device goes over.
    var upright = 0.5 + 0.5 * c;
    shineA.style.opacity = upright.toFixed(3);
    shineB.style.opacity = (1 - upright).toFixed(3);
    shineB.style.transform = 'rotate(180deg)';
    shadow.style.opacity = (c * c).toFixed(3);

    if (debug) {
      var lines = ['t ' + simTime.toFixed(2) + ' s   angle ' + (a * 180 / Math.PI).toFixed(0)];
      states.forEach(function (st, i) {
        lines.push('chamber ' + i + ': ' + (st.steps ? (st.ms / st.steps).toFixed(2) : '-') + ' ms/step  n ' + st.n +
          '  A ' + st.census.a + ' slot ' + st.census.mid + ' B ' + st.census.b +
          '  blobs ' + st.census.blobs + '  drops ' + st.drops);
      });
      lines.push(hosts[0].worker ? 'workers' : 'main thread');
      hud.textContent = lines.join('\n');
    }
  }

  // Keep the simulation fed. Called every frame and again whenever a batch
  // of steps comes back, so a slow display does not slow the physics down.
  var lastPump = 0;
  function pump() {
    var now = performance.now();
    var dt = Math.min(0.1, (now - lastPump) / 1000);
    lastPump = now;
    if (!started || manual) return;
    if (running) accumulator += dt;
    if (inflight) return;
    var onMain = !hosts[0].worker;
    var steps = Math.min(onMain ? 4 : MAX_STEPS, Math.floor(accumulator / DT));
    if (steps < 1) return;
    accumulator -= steps * DT;
    if (accumulator > 4 * DT) accumulator = 4 * DT;       // cannot keep up: run in slow motion
    // Without workers the steps run right here, so wait for the next frame
    // rather than starving the page.
    launch(steps).then(onMain ? null : pump);
  }

  function frame() {
    requestAnimationFrame(frame);
    pump();
    if (started) draw();
  }

  // ---- controls ---------------------------------------------------------

  function setRunning(on) {
    running = on;
    playButton.textContent = on ? 'Pause' : 'Play';
    playButton.setAttribute('aria-pressed', on ? 'true' : 'false');
    if (on) everPlayed = true;
    startButton.hidden = everPlayed;      // the large button is only for a page that starts paused
    if (!on) accumulator = 0;
  }

  playButton.addEventListener('click', function () { setRunning(!running); });
  startButton.addEventListener('click', function () { setRunning(true); });
  flipButton.addEventListener('click', function () { requestFlip(1); });
  device.addEventListener('click', function (e) {
    var r = stage.getBoundingClientRect();
    requestFlip(e.clientX < r.left + r.width / 2 ? -1 : 1);
  });
  device.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); requestFlip(1); }
  });
  window.addEventListener('keydown', function (e) {
    if (e.target !== document.body) return;
    if (e.key === 'f') requestFlip(1);
    else if (e.key === 'p' || e.key === ' ') { e.preventDefault(); setRunning(!running); }
  });
  var resizeTimer = 0;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { layout(); draw(); }, 80);
  });

  // ---- start ------------------------------------------------------------

  if (debug) hud.hidden = false;
  try {
    renderer = new HGRenderer(fluidCanvas, view, geom);
    renderer.debug = debug;
  } catch (err) {
    notice.textContent = 'This needs WebGL, which is not available in this browser.';
    notice.hidden = false;
  }
  layout();
  setRunning(running);

  var ready = Promise.all(hosts.map(function (h, i) {
    return h.call({ type: 'init', geom: {}, sim: CHAMBERS[i].sim, seed: CHAMBERS[i].seed });
  })).then(function (res) {
    states = res;
    totalParticles = res[0].n + res[1].n;
    return launch(Math.round(PREROLL / DT));
  }).then(function () {
    started = true;
    lastPump = performance.now();
    draw();
  });
  requestAnimationFrame(frame);

  // For tests and for poking at it from the console.
  window.hourglass = {
    ready: ready,
    flip: requestFlip,
    play: function () { setRunning(true); },
    pause: function () { setRunning(false); },
    // Simulate a number of seconds as fast as possible, then draw once.
    advance: function (seconds) {
      manual = true;
      var left = Math.round(seconds / DT);
      function next() {
        if (left <= 0) { manual = false; draw(); return window.hourglass.stats(); }
        var n = Math.min(60, left);
        left -= n;
        return launch(n).then(next);
      }
      var wait = inflight ? new Promise(function (r) { (function poll() { inflight ? setTimeout(poll, 2) : r(); })(); }) : Promise.resolve();
      return wait.then(next);
    },
    stats: function () {
      return {
        time: simTime, angle: angleAt(simTime), running: running, workers: !!hosts[0].worker,
        chambers: states.map(function (s) {
          return { n: s.n, census: s.census, drops: s.drops, lastDrop: s.lastDrop, msPerStep: s.steps ? s.ms / s.steps : 0 };
        })
      };
    },
    look: HGLook,
    redraw: function () { layout(); draw(); }
  };
})();
