/*
 * Fluid simulation for one chamber of the hourglass.
 *
 * The dyed liquid is a set of equal-volume particles solved with position
 * based fluids (Macklin and Mueller 2013). The cell is treated as a thin gap
 * of varying depth, so the model is two dimensional and depth averaged:
 *
 *   - Incompressibility: a density constraint per particle. The target 2D
 *     density scales with the local depth, so liquid that leaves a deep end
 *     chamber spreads into a wide flat disc in the thin slot, and shrinks
 *     back into a bead when it reaches the other end.
 *   - Surface tension: short range cohesion between particles of one body of
 *     liquid, weighted by how exposed each particle is.
 *   - The clear oil is not simulated. Its effect is a linear drag, which is
 *     what the walls of a thin gap do to a slow flow (Hele-Shaw friction).
 *   - Bodies of liquid are tracked as blobs. A blob splits when it is no
 *     longer connected and two blobs merge only after they have touched for
 *     a while, which stands in for the oil film that has to drain first.
 *
 * Nothing here knows which way is up: gravity is passed in every step.
 *
 * The file is one named function so that its source can also be handed to a
 * Web Worker.
 */
function HGSimModule(root) {
  'use strict';

  var DEFAULTS = {
    spacing: 0.026,       // particle spacing in the thin slot
    eta: 2.1,             // kernel radius / spacing
    fillY: 0.30,          // initial liquid surface (y of the fill line)
    radius: 0.55,         // wall contact radius / local spacing

    gravity: 14,          // buoyancy-reduced gravity
    drag: 16,             // oil drag in the slot (1/s); fall speed is gravity/drag
    dragDeep: 0.5,        // drag in the end chambers relative to the slot
    nozzleDrag: 350,      // extra resistance of the nozzle bore
    ventDrag: 40,         // extra resistance of the vents
    smallBlob: 10,        // blobs near this many particles sink noticeably slower

    tension: 800,         // cohesion strength in the slot (1/s^2)
    cohRange: 3.8,        // cohesion range in the slot / local spacing
    cohEvery: 4,          // steps between rebuilds of the long-range pair list
    tensionDeep: 6000,    // short-range cohesion strength in the end chambers (1/s^2)
    cohIn: 0.15,          // short-range cohesion starts at this fraction of the kernel radius
    defMax: 0.6,          // short-range cohesion is weighted by how exposed a particle is
    hardCore: 0.8,        // closest approach inside a blob / lattice spacing
    film: 1.0,            // closest approach between two blobs / lattice spacing
    hardStiff: 0.4,

    epsRel: 0.6,          // constraint softening
    iterations: 2,
    xsph: 0.1,            // velocity smoothing inside a blob
    wallFriction: 3,      // tangential damping at walls (1/s)
    vmax: 6,

    neckRadius: 3.2,      // neighbourhood used to measure how thin a strand is / lattice spacing
    neckWidth: 0.55,      // a strand with an RMS half width below this is a filament
    neckLength: 1.4,      // ...provided it is at least this elongated
    pinchTime: 0.04,      // seconds a filament survives before it snaps
    link: 1.45,           // blob connectivity distance / lattice spacing
    contact: 1.35,        // blob contact distance / lattice spacing
    mergeMin: 0.7,        // seconds two blobs touch before they merge
    mergeMax: 4.0,
    tinyBlob: 3,          // blobs this small merge almost at once
    trackEvery: 4,        // steps between blob tracking passes
    neighEvery: 2,        // steps between neighbour list rebuilds
    skin: 0.1             // extra search radius that makes the reuse safe
  };

  var HEX = 1.0746;       // lattice spacing of a hex packing with unit area per particle
  var MAXB = 1024;

  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function Chamber(geom, opts, seed) {
    var P = this.P = {};
    var k;
    for (k in DEFAULTS) P[k] = DEFAULTS[k];
    if (opts) for (k in opts) P[k] = opts[k];
    this.geom = geom;
    this.rand = mulberry32(seed || 1);
    this.S = geom.params.depth;
    this.d = P.spacing;
    this.hThin = P.eta * P.spacing;
    this.time = 0;
    this.stepCount = 0;
    this.events = [];
    this.dropCount = 0;
    this.lastDrop = null;

    this._calibrate();
    this._seedParticles();
    this._allocate();
    this.bcount[0] = this.n;
    this._updateProps();
  }

  // Kernel sums on a perfect lattice, used to normalise rest density and the
  // constraint softening so that both are independent of resolution.
  Chamber.prototype._calibrate = function () {
    var eta = this.P.eta, a = HEX;
    var K4 = 4 / Math.PI, K30 = 30 / Math.PI;
    var rho = K4 / (eta * eta), g2 = 0;
    for (var j = -6; j <= 6; j++) {
      for (var i = -6; i <= 6; i++) {
        if (i === 0 && j === 0) continue;
        var x = (i + (j & 1) * 0.5) * a, y = j * a * Math.sqrt(3) / 2;
        var r = Math.sqrt(x * x + y * y), q = r / eta;
        if (q >= 1) continue;
        var t = 1 - q * q;
        rho += K4 / (eta * eta) * t * t * t;
        var gc = K30 / (eta * eta * eta) * (1 - q) * (1 - q);
        g2 += gc * gc;
      }
    }
    this.rho0base = rho / (this.d * this.d);      // rest density in the slot
    this.G0 = g2 / (rho * rho) * eta * eta;       // dimensionless gradient sum

    // Fraction of the kernel that lies beyond a flat wall at distance t*h.
    var N = 64, tab = new Float64Array(N + 1), der = new Float64Array(N + 1);
    var c = K4 * 32 / 35;
    for (var m = N; m >= 0; m--) {
      var u = m / N;
      der[m] = c * Math.pow(1 - u * u, 3.5);
      tab[m] = m === N ? 0 : tab[m + 1] + 0.5 * (der[m] + der[m + 1]) / N;
    }
    this.wallTab = tab; this.wallDer = der; this.wallN = N;
  };

  Chamber.prototype._seedParticles = function () {
    var P = this.P, g = this.geom, S = this.S;
    var a = HEX * this.d / Math.sqrt(S);
    var rad = P.radius * this.d / Math.sqrt(S);
    var pts = [];
    var row = 0;
    for (var y = g.yTip; y >= P.fillY; y -= a * Math.sqrt(3) / 2, row++) {
      for (var x = -0.5 + (row & 1) * a * 0.5; x <= 0.5; x += a) {
        if (g.sdfAt(x, y) < rad * 1.02) continue;
        if (g.depthAt(x, y) < S * 0.999) continue;
        pts.push(x, y);
      }
    }
    this.n = pts.length / 2;
    this._seed = pts;
  };

  Chamber.prototype._allocate = function () {
    var n = this.n, F = Float64Array, I = Int32Array, P = this.P;
    this.x = new F(n); this.y = new F(n);
    this.vx = new F(n); this.vy = new F(n);
    this.px = new F(n); this.py = new F(n);
    this.s = new F(n); this.h = new F(n); this.rad = new F(n);
    this.kb = new F(n); this.coh = new F(n);
    this.rho = new F(n); this.gsx = new F(n); this.gsy = new F(n); this.g2 = new F(n);
    this.lam = new F(n); this.def = new F(n);
    this.ddx = new F(n); this.ddy = new F(n);
    this.wphi = new F(n); this.wnx = new F(n); this.wny = new F(n);
    this.touch = new Uint8Array(n);
    this.slot = new Uint8Array(n);          // 1 where the particle is not in a fully deep region
    this.dl = new F(n);                     // local particle spacing
    var maxLong = n * 40;
    this.la = new I(maxLong); this.lb = new I(maxLong); this.nl = 0;
    this.blob = new I(n);
    this.parent = new I(n); this.rootOf = new I(n); this.csize = new I(n); this.newId = new I(n);
    for (var i = 0; i < n; i++) { this.x[i] = this._seed[2 * i]; this.y[i] = this._seed[2 * i + 1]; }
    this._seed = null;

    // neighbour grid
    this.cellSize = this.hThin / Math.sqrt(this.S) * (1 + P.skin) * 1.001;
    this.gx0 = -0.56; this.gy0 = -0.04;
    this.gw = Math.ceil(1.12 / this.cellSize) + 1;
    this.gh = Math.ceil((this.geom.H + 0.08) / this.cellSize) + 1;
    var nc = this.gw * this.gh;
    this.cellStart = new I(nc + 1); this.cellCursor = new I(nc);
    this.cellOf = new I(n); this.sorted = new I(n);
    var maxPairs = n * 28;
    this.pa = new I(maxPairs); this.pb = new I(maxPairs);
    this.pr = new F(maxPairs); this.pux = new F(maxPairs); this.puy = new F(maxPairs);
    this.pg = new F(maxPairs); this.ph = new F(maxPairs);
    this.np = 0;

    // blobs
    this.bcount = new I(MAXB); this.bsx = new F(MAXB); this.bsy = new F(MAXB);
    this.bchan = new Uint8Array(MAXB); this.balive = new Uint8Array(MAXB);
    this.bbest = new I(MAXB); this.bmask = new Uint8Array(MAXB);
    this.bneck = new I(MAXB); this.bthin = new F(MAXB); this.bax = new F(MAXB); this.bay = new F(MAXB);
    this.bneckT = new F(MAXB);
    this.mc = new I(n); this.mx = new F(n); this.my = new F(n);
    this.mxx = new F(n); this.myy = new F(n); this.mxy = new F(n);
    this.bfree = [];
    for (var b = MAXB - 1; b >= 1; b--) this.bfree.push(b);
    this.balive[0] = 1;
    this.contacts = new Map();
    this.stamp = 0;
  };

  // Per-particle properties that depend on where the particle is.
  Chamber.prototype._updateProps = function () {
    var P = this.P, g = this.geom, n = this.n, S = this.S;
    var x = this.x, y = this.y, s = this.s, h = this.h, rad = this.rad, kb = this.kb;
    var blob = this.blob, bcount = this.bcount;
    var depth = g.depth, zone = g.zone, gx0 = g.x0, gy0 = g.y0, inv = 1 / g.cell, nx = g.nx, ny = g.ny;
    var hThin = this.hThin, d = this.d;
    for (var i = 0; i < n; i++) {
      var fx = (x[i] - gx0) * inv, fy = (y[i] - gy0) * inv;
      var ix = fx | 0, iy = fy | 0;
      if (ix < 0) ix = 0; else if (ix > nx - 2) ix = nx - 2;
      if (iy < 0) iy = 0; else if (iy > ny - 2) iy = ny - 2;
      var tx = fx - ix, ty = fy - iy;
      var c = ix + iy * nx;
      var si = (depth[c] * (1 - tx) + depth[c + 1] * tx) * (1 - ty) +
        (depth[c + nx] * (1 - tx) + depth[c + nx + 1] * tx) * ty;
      if (si < 1) si = 1;
      s[i] = si;
      var isq = 1 / Math.sqrt(si);
      h[i] = hThin * isq;
      rad[i] = P.radius * d * isq;
      this.dl[i] = d * isq;
      var deepness = S > 1 ? (si - 1) / (S - 1) : 0;
      this.slot[i] = deepness < 0.97 ? 1 : 0;
      var cnt = bcount[blob[i]] || 1;
      var k = P.drag * (1 + (P.dragDeep - 1) * deepness) * (1 + P.smallBlob / cnt);
      var z = zone[(tx > 0.5 ? ix + 1 : ix) + (ty > 0.5 ? iy + 1 : iy) * nx];
      if (z === 1) k += P.nozzleDrag; else if (z === 2) k += P.ventDrag;
      kb[i] = k;
    }
  };

  Chamber.prototype._neighbors = function () {
    var n = this.n, px = this.px, py = this.py, hI = this.h;
    var inv = 1 / this.cellSize, gw = this.gw, gh = this.gh, gx0 = this.gx0, gy0 = this.gy0;
    var cellStart = this.cellStart, cellCursor = this.cellCursor, cellOf = this.cellOf, sorted = this.sorted;
    var nc = gw * gh, i, c;
    cellStart.fill(0);
    for (i = 0; i < n; i++) {
      var cx = ((px[i] - gx0) * inv) | 0, cy = ((py[i] - gy0) * inv) | 0;
      if (cx < 0) cx = 0; else if (cx >= gw) cx = gw - 1;
      if (cy < 0) cy = 0; else if (cy >= gh) cy = gh - 1;
      c = cx + cy * gw;
      cellOf[i] = c;
      cellStart[c + 1]++;
    }
    for (c = 0; c < nc; c++) cellStart[c + 1] += cellStart[c];
    for (c = 0; c < nc; c++) cellCursor[c] = cellStart[c];
    for (i = 0; i < n; i++) sorted[cellCursor[cellOf[i]]++] = i;

    // Each pair is listed once, by whichever particle has the larger kernel.
    var pa = this.pa, pb = this.pb, maxPairs = pa.length, np = 0;
    var cs = this.cellSize, reach = 1 + this.P.skin, reach2 = reach * reach;
    for (i = 0; i < n; i++) {
      var xi = px[i], yi = py[i], hi = hI[i];
      var ring = Math.ceil(hi * reach / cs - 1e-6);
      c = cellOf[i];
      var cx0 = c % gw, cy0 = (c / gw) | 0;
      var y0 = cy0 - ring, y1 = cy0 + ring, x0 = cx0 - ring, x1 = cx0 + ring;
      if (y0 < 0) y0 = 0; if (y1 >= gh) y1 = gh - 1;
      if (x0 < 0) x0 = 0; if (x1 >= gw) x1 = gw - 1;
      for (var qy = y0; qy <= y1; qy++) {
        var b0 = cellStart[x0 + qy * gw], b1 = cellStart[x1 + qy * gw + 1];
        for (var b = b0; b < b1; b++) {
          var j = sorted[b];
          var hj = hI[j];
          if (hj > hi || (hj === hi && j <= i)) continue;
          var dx = xi - px[j], dy = yi - py[j];
          var hh = 0.5 * (hi + hj);
          if (dx * dx + dy * dy < hh * hh * reach2 && np < maxPairs) { pa[np] = i; pb[np] = j; np++; }
        }
      }
    }
    this.np = np;
  };

  // Pairs for the longer-range cohesion that acts in the thin slot. Uses the
  // cell grid left behind by _neighbors().
  Chamber.prototype._longPairs = function () {
    var n = this.n, px = this.px, py = this.py, dl = this.dl, slot = this.slot, blob = this.blob;
    var gw = this.gw, gh = this.gh, cs = this.cellSize;
    var cellStart = this.cellStart, cellOf = this.cellOf, sorted = this.sorted;
    var la = this.la, lb = this.lb, maxLong = la.length, nl = 0;
    var cr = this.P.cohRange * 1.12, d = this.d;
    for (var i = 0; i < n; i++) {
      if (!slot[i]) continue;
      var xi = px[i], yi = py[i], di = dl[i], bi = blob[i];
      var ring = Math.ceil(cr * 0.5 * (di + d) / cs);
      var c = cellOf[i];
      var cx0 = c % gw, cy0 = (c / gw) | 0;
      var y0 = cy0 - ring, y1 = cy0 + ring, x0 = cx0 - ring, x1 = cx0 + ring;
      if (y0 < 0) y0 = 0; if (y1 >= gh) y1 = gh - 1;
      if (x0 < 0) x0 = 0; if (x1 >= gw) x1 = gw - 1;
      for (var qy = y0; qy <= y1; qy++) {
        var b1 = cellStart[x1 + qy * gw + 1];
        for (var b = cellStart[x0 + qy * gw]; b < b1; b++) {
          var j = sorted[b];
          if (blob[j] !== bi || (slot[j] && j <= i)) continue;
          var dx = xi - px[j], dy = yi - py[j];
          var R = cr * 0.5 * (di + dl[j]);
          if (dx * dx + dy * dy < R * R && nl < maxLong) { la[nl] = i; lb[nl] = j; nl++; }
        }
      }
    }
    this.nl = nl;
  };

  // Distance and direction to the nearest wall for every predicted position.
  Chamber.prototype._sampleWalls = function () {
    var g = this.geom, n = this.n, px = this.px, py = this.py;
    var sdf = g.sdf, gx0 = g.x0, gy0 = g.y0, inv = 1 / g.cell, nx = g.nx, ny = g.ny;
    var wphi = this.wphi, wnx = this.wnx, wny = this.wny;
    for (var i = 0; i < n; i++) {
      var fx = (px[i] - gx0) * inv, fy = (py[i] - gy0) * inv;
      var ix = fx | 0, iy = fy | 0;
      if (ix < 0) ix = 0; else if (ix > nx - 2) ix = nx - 2;
      if (iy < 0) iy = 0; else if (iy > ny - 2) iy = ny - 2;
      var tx = fx - ix, ty = fy - iy;
      if (tx < 0) tx = 0; else if (tx > 1) tx = 1;
      if (ty < 0) ty = 0; else if (ty > 1) ty = 1;
      var c = ix + iy * nx;
      var v00 = sdf[c], v10 = sdf[c + 1], v01 = sdf[c + nx], v11 = sdf[c + nx + 1];
      wphi[i] = (v00 * (1 - tx) + v10 * tx) * (1 - ty) + (v01 * (1 - tx) + v11 * tx) * ty;
      var gxn = (v10 - v00) * (1 - ty) + (v11 - v01) * ty;
      var gyn = (v01 - v00) * (1 - tx) + (v11 - v10) * tx;
      var len = Math.sqrt(gxn * gxn + gyn * gyn);
      if (len > 1e-9) { wnx[i] = gxn / len; wny[i] = gyn / len; } else { wnx[i] = 0; wny[i] = 0; }
    }
  };

  // Keep particles out of the walls and apply the one-way openings.
  Chamber.prototype._collide = function () {
    var g = this.geom, n = this.n, px = this.px, py = this.py, x = this.x, y = this.y;
    var wphi = this.wphi, wnx = this.wnx, wny = this.wny, rad = this.rad, touch = this.touch;
    var H = g.H, yTip = g.yTip, yVent = g.yVent, bw = g.boreHalf, xEnd = g.xEnd;
    var yTip2 = H - yTip, yVent2 = H - yVent;
    this._sampleWalls();
    for (var i = 0; i < n; i++) {
      var push = rad[i] - wphi[i];
      if (push > 0) {
        px[i] += wnx[i] * push; py[i] += wny[i] * push;
        touch[i] = 1;
      }
      var X = px[i], Y = py[i], yo = y[i];
      var ax = X < 0 ? -X : X;
      if (ax < bw) {
        // Nozzles let liquid out of an end chamber, not back in.
        if (yo >= yTip && Y < yTip && yo < H / 2) py[i] = yTip;
        else if (yo <= yTip2 && Y > yTip2 && yo > H / 2) py[i] = yTip2;
      } else if (ax > xEnd - 0.004) {
        // Vents let liquid into an end chamber, not out of it.
        if (yo <= yVent && Y > yVent) py[i] = yVent;
        else if (yo >= yVent2 && Y < yVent2) py[i] = yVent2;
      }
    }
  };

  Chamber.prototype._iterate = function (kc, kl) {
    var P = this.P, n = this.n, np = this.np;
    var pa = this.pa, pb = this.pb, px = this.px, py = this.py, hI = this.h, sI = this.s;
    var rho = this.rho, gsx = this.gsx, gsy = this.gsy, g2 = this.g2, lam = this.lam, def = this.def;
    var pr = this.pr, pux = this.pux, puy = this.puy, pg = this.pg, ph = this.ph;
    var ddx = this.ddx, ddy = this.ddy, blob = this.blob, slot = this.slot, dl = this.dl;
    var wphi = this.wphi, wnx = this.wnx, wny = this.wny;
    var wallTab = this.wallTab, wallDer = this.wallDer, wallN = this.wallN;
    var K4 = 4 / Math.PI, K30 = 30 / Math.PI;
    var i, j, k, h, r;

    for (i = 0; i < n; i++) {
      h = hI[i];
      rho[i] = K4 / (h * h); gsx[i] = 0; gsy[i] = 0; g2[i] = 0; ddx[i] = 0; ddy[i] = 0;
    }
    for (k = 0; k < np; k++) {
      i = pa[k]; j = pb[k];
      var dx = px[i] - px[j], dy = py[i] - py[j];
      var r2 = dx * dx + dy * dy;
      h = 0.5 * (hI[i] + hI[j]);
      var h2 = h * h;
      if (r2 >= h2) { pr[k] = -1; continue; }
      r = Math.sqrt(r2);
      var q = r / h, t = 1 - q * q, u = 1 - q;
      var w = K4 / h2 * t * t * t;
      rho[i] += w; rho[j] += w;
      var gc = -K30 / (h2 * h) * u * u;
      var ux, uy;
      if (r > 1e-12) { ux = dx / r; uy = dy / r; } else { ux = 0.7071; uy = 0.7071; }
      var gxk = gc * ux, gyk = gc * uy;
      gsx[i] += gxk; gsy[i] += gyk; gsx[j] -= gxk; gsy[j] -= gyk;
      g2[i] += gc * gc; g2[j] += gc * gc;
      pr[k] = r; pux[k] = ux; puy[k] = uy; pg[k] = gc; ph[k] = h;
    }

    var rho0b = this.rho0base, epsG = P.epsRel * this.G0, defMax = P.defMax;
    for (i = 0; i < n; i++) {
      var rho0 = rho0b * sI[i];
      h = hI[i];
      var fluid = rho[i] / rho0;
      // Walls count as liquid at rest density for the pressure, so that the
      // layer next to a wall is not squeezed flat.
      var wall = 0, wgrad = 0;
      var tw = wphi[i] / h;
      if (tw < 1) {
        if (tw < 0) tw = 0;
        var ft = tw * wallN, it = ft | 0;
        if (it >= wallN) it = wallN - 1;
        var fr = ft - it;
        wall = wallTab[it] * (1 - fr) + wallTab[it + 1] * fr;
        wgrad = (wallDer[it] * (1 - fr) + wallDer[it + 1] * fr) / h;   // d(wall)/d(phi), sign flipped
      }
      var C = fluid + wall - 1;
      var gxw = gsx[i] / rho0 - wgrad * wnx[i], gyw = gsy[i] / rho0 - wgrad * wny[i];
      var sumg = gxw * gxw + gyw * gyw + g2[i] / (rho0 * rho0);
      var l = C > 0 ? -C / (sumg + epsG / (h * h)) : 0;   // pressure only ever pushes
      lam[i] = l / rho0;
      ddx[i] = -l * wgrad * wnx[i]; ddy[i] = -l * wgrad * wny[i];
      var df = 1 - fluid;
      def[i] = df <= 0 ? 0 : df > defMax ? defMax : df;
    }

    // Cohesion profile: zero at contact, strongest near the lattice spacing,
    // fading to zero at the kernel radius. It always attracts, so a thin
    // strand has no stable rest shape and pulls itself into a bead.
    var q0 = P.cohIn, qp = (1 + 2 * q0) / 3, A = 1 / ((qp - q0) * (1 - qp) * (1 - qp));
    var invEta = HEX / P.eta, hc = P.hardCore, film = P.film, hs = P.hardStiff;
    for (k = 0; k < np; k++) {
      r = pr[k];
      if (r < 0) continue;
      i = pa[k]; j = pb[k]; h = ph[k];
      var c = (lam[i] + lam[j]) * pg[k];
      var rmin;
      if (blob[i] === blob[j]) {
        if (!slot[i] && !slot[j]) {
          var ds = def[i] + def[j];
          var qq = r / h;
          if (ds > 0 && qq > q0) {
            var uu = 1 - qq;
            c -= kc * 0.5 * ds * A * (qq - q0) * uu * uu * h;
          }
        }
        rmin = hc * invEta * h;
      } else {
        rmin = film * invEta * h;
      }
      if (r < rmin) c += hs * (rmin - r);
      var cx = c * pux[k], cy = c * puy[k];
      ddx[i] += cx; ddy[i] += cy; ddx[j] -= cx; ddy[j] -= cy;
    }
    // Longer-range cohesion: many weak pulls, which is what lets a strand of
    // liquid gather into a round drop instead of hanging like a chain.
    var la = this.la, lb = this.lb, nl = this.nl, cr = P.cohRange;
    for (k = 0; k < nl; k++) {
      i = la[k]; j = lb[k];
      if (blob[i] !== blob[j]) continue;
      var ex = px[i] - px[j], ey = py[i] - py[j];
      var e2 = ex * ex + ey * ey;
      var dm = 0.5 * (dl[i] + dl[j]);
      var R = cr * dm;
      if (e2 >= R * R || e2 < 1e-16) continue;
      var eq = e2 / (R * R), et = 1 - eq;
      var ef = kl * dm * 3.49 * et * et / R;          // pull is q(1-q^2)^2 along the pair, peak 1
      ex *= ef; ey *= ef;
      ddx[i] -= ex; ddy[i] -= ey; ddx[j] += ex; ddy[j] += ey;
    }
    for (i = 0; i < n; i++) { px[i] += ddx[i]; py[i] += ddy[i]; }
    this._collide();
  };

  Chamber.prototype.step = function (dt, gx, gy) {
    var P = this.P, n = this.n;
    var x = this.x, y = this.y, vx = this.vx, vy = this.vy, px = this.px, py = this.py;
    var kb = this.kb, touch = this.touch, i;

    for (i = 0; i < n; i++) {
      var f = 1 / (1 + kb[i] * dt);
      var vxi = (vx[i] + gx * dt) * f, vyi = (vy[i] + gy * dt) * f;
      vx[i] = vxi; vy[i] = vyi;
      px[i] = x[i] + vxi * dt; py[i] = y[i] + vyi * dt;
      touch[i] = 0;
    }

    if (this.stepCount % P.neighEvery === 0) {
      this._neighbors();
      if (this.stepCount % P.cohEvery === 0) this._longPairs();
    }
    this._sampleWalls();
    var kc = P.tensionDeep * dt * dt / P.iterations;
    var kl = P.tension * dt * dt / P.iterations;
    for (var it = 0; it < P.iterations; it++) this._iterate(kc, kl);

    var wnx = this.wnx, wny = this.wny, vmax = P.vmax, wf = 1 / (1 + P.wallFriction * dt);
    var idt = 1 / dt;
    for (i = 0; i < n; i++) {
      var ux = (px[i] - x[i]) * idt, uy = (py[i] - y[i]) * idt;
      if (touch[i]) {
        var vn = ux * wnx[i] + uy * wny[i];
        ux = vn * wnx[i] + (ux - vn * wnx[i]) * wf;
        uy = vn * wny[i] + (uy - vn * wny[i]) * wf;
      }
      var sp = ux * ux + uy * uy;
      if (sp > vmax * vmax) { sp = vmax / Math.sqrt(sp); ux *= sp; uy *= sp; }
      if (ux !== ux || uy !== uy) { ux = 0; uy = 0; px[i] = x[i]; py[i] = y[i]; }
      vx[i] = ux; vy[i] = uy;
      x[i] = px[i]; y[i] = py[i];
    }

    if (P.xsph > 0) this._smoothVelocity();
    this.time += dt;
    this.stepCount++;
    if (this.stepCount % P.trackEvery === 0) this._track(dt * P.trackEvery);
    this._updateProps();
  };

  Chamber.prototype._smoothVelocity = function () {
    var n = this.n, np = this.np, pa = this.pa, pb = this.pb, pr = this.pr, ph = this.ph;
    var vx = this.vx, vy = this.vy, blob = this.blob;
    var ax = this.ddx, ay = this.ddy, aw = this.g2, c = this.P.xsph;
    var i, j, k;
    for (i = 0; i < n; i++) { ax[i] = 0; ay[i] = 0; aw[i] = 0; }
    for (k = 0; k < np; k++) {
      var r = pr[k];
      if (r < 0) continue;
      i = pa[k]; j = pb[k];
      if (blob[i] !== blob[j]) continue;
      var w = 1 - r / ph[k];
      var dvx = (vx[j] - vx[i]) * w, dvy = (vy[j] - vy[i]) * w;
      ax[i] += dvx; ay[i] += dvy; ax[j] -= dvx; ay[j] -= dvy;
      aw[i] += w; aw[j] += w;
    }
    for (i = 0; i < n; i++) {
      var s = c / (aw[i] + 1);
      vx[i] += ax[i] * s; vy[i] += ay[i] * s;
    }
  };

  function find(parent, i) {
    while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; }
    return i;
  }

  // Work out which particles form one connected body of liquid, split bodies
  // that have come apart, and merge bodies that have been touching long enough.
  Chamber.prototype._track = function (dtTrack) {
    var P = this.P, n = this.n, np = this.np;
    var pa = this.pa, pb = this.pb, pr = this.pr, ph = this.ph, blob = this.blob;
    var parent = this.parent, rootOf = this.rootOf, csize = this.csize, newId = this.newId;
    var bcount = this.bcount, bsx = this.bsx, bsy = this.bsy, bchan = this.bchan;
    var balive = this.balive, bbest = this.bbest, bmask = this.bmask, bfree = this.bfree;
    var x = this.x, y = this.y;
    var linkF = P.link * HEX / P.eta, contactF = P.contact * HEX / P.eta;
    var i, j, k, b, r;

    // --- filaments -------------------------------------------------------
    // Measure the shape of each slot particle's neighbourhood. Where the
    // liquid has been drawn out into a strand about as thin as the slot is
    // deep, it would break up in the real device, so it is cut here.
    var la = this.la, lb = this.lb, nl = this.nl, dl = this.dl, slot = this.slot, wphi = this.wphi;
    var mc = this.mc, mx = this.mx, my = this.my, mxx = this.mxx, myy = this.myy, mxy = this.mxy;
    var bneck = this.bneck, bthin = this.bthin, bax = this.bax, bay = this.bay, bneckT = this.bneckT;
    var nr = P.neckRadius * HEX, wn2 = P.neckWidth * P.neckWidth, ln2 = P.neckLength * P.neckLength;
    for (i = 0; i < n; i++) { mc[i] = 0; mx[i] = 0; my[i] = 0; mxx[i] = 0; myy[i] = 0; mxy[i] = 0; }
    for (k = 0; k < nl; k++) {
      i = la[k]; j = lb[k];
      if (blob[i] !== blob[j]) continue;
      var ex = x[j] - x[i], ey = y[j] - y[i];
      var Rn = nr * 0.5 * (dl[i] + dl[j]);
      if (ex * ex + ey * ey > Rn * Rn) continue;
      mc[i]++; mx[i] += ex; my[i] += ey; mxx[i] += ex * ex; myy[i] += ey * ey; mxy[i] += ex * ey;
      mc[j]++; mx[j] -= ex; my[j] -= ey; mxx[j] += ex * ex; myy[j] += ey * ey; mxy[j] += ex * ey;
    }
    for (b = 0; b < MAXB; b++) { bneck[b] = -1; bthin[b] = 1e9; }
    for (i = 0; i < n; i++) {
      if (!slot[i] || mc[i] < 3) continue;
      var ai = HEX * dl[i];
      if (wphi[i] < 1.5 * ai) continue;                  // strands lying on a wall do not pinch
      var iv = 1 / (mc[i] + 1);
      var ux = mx[i] * iv, uy = my[i] * iv;
      var cxx = mxx[i] * iv - ux * ux, cyy = myy[i] * iv - uy * uy, cxy = mxy[i] * iv - ux * uy;
      var half = 0.5 * (cxx + cyy), dif = 0.5 * (cxx - cyy);
      var rt = Math.sqrt(dif * dif + cxy * cxy);
      var l1 = half + rt, l2 = half - rt, a2 = ai * ai;
      if (l2 >= wn2 * a2 || l1 <= ln2 * a2) continue;
      var ang = 0.5 * Math.atan2(2 * cxy, cxx - cyy);
      var cax = Math.cos(ang), cay = Math.sin(ang);
      var along = ux * cax + uy * cay;
      if (along * along > 0.12 * l1) continue;           // a free end, not a neck
      b = blob[i];
      if (l2 / a2 < bthin[b]) { bthin[b] = l2 / a2; bneck[b] = i; bax[b] = cax; bay[b] = cay; }
    }
    for (b = 0; b < MAXB; b++) {
      if (bneck[b] < 0) { bneckT[b] = 0; continue; }
      bneckT[b] += dtTrack;
      if (bneckT[b] < P.pinchTime) bneck[b] = -1; else bneckT[b] = 0;
    }

    // --- connectivity ----------------------------------------------------
    for (i = 0; i < n; i++) { parent[i] = i; csize[i] = 0; newId[i] = -1; }
    for (k = 0; k < np; k++) {
      r = pr[k];
      if (r < 0 || r >= linkF * ph[k]) continue;
      i = pa[k]; j = pb[k];
      b = blob[i];
      if (b !== blob[j]) continue;
      var cut = bneck[b];
      if (cut >= 0) {
        var qx = x[cut], qy = y[cut], cr2 = 6.5 * HEX * HEX * dl[cut] * dl[cut];
        var d1x = x[i] - qx, d1y = y[i] - qy, d2x = x[j] - qx, d2y = y[j] - qy;
        if (d1x * d1x + d1y * d1y < cr2 && d2x * d2x + d2y * d2y < cr2 &&
          (d1x * bax[b] + d1y * bay[b] > 0) !== (d2x * bax[b] + d2y * bay[b] > 0)) continue;
      }
      var ra = find(parent, i), rb = find(parent, j);
      if (ra !== rb) parent[rb] = ra;
    }
    for (i = 0; i < n; i++) { r = find(parent, i); rootOf[i] = r; csize[r]++; }
    for (b = 0; b < MAXB; b++) bbest[b] = -1;
    for (i = 0; i < n; i++) {
      b = blob[i]; r = rootOf[i];
      if (bbest[b] < 0 || csize[r] > csize[bbest[b]]) bbest[b] = r;
    }
    var born = null;
    for (i = 0; i < n; i++) {
      r = rootOf[i]; b = blob[i];
      if (r === bbest[b]) continue;
      if (newId[r] < 0) {
        if (!bfree.length) continue;
        var id = bfree.pop();
        balive[id] = 1;
        bchan[id] = (bchan[b] + 1 + ((this.rand() * 3) | 0)) & 3;
        newId[r] = id;
        (born || (born = [])).push(id, b);
      }
      blob[i] = newId[r];
    }

    for (b = 0; b < MAXB; b++) { bcount[b] = 0; bsx[b] = 0; bsy[b] = 0; bmask[b] = 0; }
    for (i = 0; i < n; i++) { b = blob[i]; bcount[b]++; bsx[b] += x[i]; bsy[b] += y[i]; }
    for (b = 0; b < MAXB; b++) {
      if (balive[b] && bcount[b] === 0) { balive[b] = 0; bfree.push(b); }
    }
    if (born) {
      for (k = 0; k < born.length; k += 2) {
        b = born[k];
        if (!bcount[b]) continue;
        var ev = {
          t: this.time, type: 'split', id: b, from: born[k + 1], n: bcount[b],
          x: bsx[b] / bcount[b], y: bsy[b] / bcount[b]
        };
        this.events.push(ev);
        // a drop: a sizeable piece that has just come away below a nozzle
        var g = this.geom, ey = ev.y < g.H / 2 ? ev.y : g.H - ev.y;
        if (ev.n >= 8 && Math.abs(ev.x) < 0.15 && ey > g.yTip && ey < g.yTip + 0.3) {
          this.dropCount++; this.lastDrop = ev;
        }
      }
      if (this.events.length > 4000) this.events.splice(0, 2000);
    }

    // contacts between different blobs
    var contacts = this.contacts, stamp = ++this.stamp;
    for (k = 0; k < np; k++) {
      r = pr[k];
      if (r < 0 || r >= contactF * ph[k]) continue;
      var bi = blob[pa[k]], bj = blob[pb[k]];
      if (bi === bj) continue;
      var lo = bi < bj ? bi : bj, hi = bi < bj ? bj : bi;
      var key = lo * MAXB + hi;
      var rec = contacts.get(key);
      if (!rec) {
        rec = { a: lo, b: hi, t: 0, T: this._mergeTime(lo, hi), seen: stamp, miss: 0 };
        contacts.set(key, rec);
      } else rec.seen = stamp;
      bmask[lo] |= 1 << bchan[hi]; bmask[hi] |= 1 << bchan[lo];
    }
    var merges = null, self = this;
    contacts.forEach(function (rec, key) {
      if (rec.seen === stamp) {
        rec.t += dtTrack; rec.miss = 0;
        if (rec.t >= rec.T) (merges || (merges = [])).push(rec);
        else if (bchan[rec.a] === bchan[rec.b]) self._recolour(rec.a, rec.b);
      } else {
        rec.miss += dtTrack;
        if (rec.miss > 0.12) contacts.delete(key);
      }
    });
    if (merges) {
      for (k = 0; k < merges.length; k++) {
        var m = merges[k];
        if (!balive[m.a] || !balive[m.b] || !bcount[m.a] || !bcount[m.b]) continue;
        var big = bcount[m.a] >= bcount[m.b] ? m.a : m.b;
        var small = big === m.a ? m.b : m.a;
        for (i = 0; i < n; i++) if (blob[i] === small) blob[i] = big;
        bsx[big] += bsx[small]; bsy[big] += bsy[small];
        bcount[big] += bcount[small]; bcount[small] = 0;
        balive[small] = 0; bfree.push(small);
        this.events.push({ t: this.time, type: 'merge', id: big, from: small, n: bcount[big] });
      }
      contacts.forEach(function (rec, key) {
        if (!balive[rec.a] || !balive[rec.b]) contacts.delete(key);
      });
    }
  };

  // Touching blobs are drawn in different channels so their outlines stay
  // separate. Move the smaller one to a channel none of its neighbours use.
  Chamber.prototype._recolour = function (a, b) {
    var bcount = this.bcount, bchan = this.bchan, bmask = this.bmask;
    var small = bcount[a] <= bcount[b] ? a : b;
    var mask = bmask[small];
    var start = (this.rand() * 4) | 0;
    for (var c = 0; c < 4; c++) {
      var ch = (start + c) & 3;
      if (!(mask & (1 << ch))) { bchan[small] = ch; return; }
    }
    bchan[small] = (bchan[small] + 1) & 3;
  };

  Chamber.prototype._mergeTime = function (a, b) {
    var P = this.P, bcount = this.bcount;
    var m = Math.min(bcount[a] || 1, bcount[b] || 1);
    if (m <= P.tinyBlob) return 0.05 + 0.2 * this.rand();
    var u = this.rand();
    return P.mergeMin + (P.mergeMax - P.mergeMin) * u * u;
  };

  // How much liquid is in each part of the device.
  Chamber.prototype.census = function () {
    var n = this.n, y = this.y, s = this.s, H = this.geom.H, S = this.S;
    var a = 0, mid = 0, b = 0;
    for (var i = 0; i < n; i++) {
      if (s[i] < 0.5 * (1 + S)) mid++;
      else if (y[i] < H / 2) a++;
      else b++;
    }
    var blobs = 0;
    for (var k = 0; k < MAXB; k++) if (this.balive[k]) blobs++;
    return { n: n, a: a, mid: mid, b: b, blobs: blobs };
  };

  // Copy what the renderer needs into a flat array: x, y, local spacing and
  // drawing channel for every particle.
  Chamber.prototype.pack = function (out) {
    var n = this.n, x = this.x, y = this.y, dl = this.dl, blob = this.blob, bchan = this.bchan;
    for (var i = 0, o = 0; i < n; i++, o += 4) {
      out[o] = x[i]; out[o + 1] = y[i]; out[o + 2] = dl[i]; out[o + 3] = bchan[blob[i]];
    }
    return out;
  };

  root.HGSim = { Chamber: Chamber, DEFAULTS: DEFAULTS, MAXB: MAXB };
}
HGSimModule(typeof self !== 'undefined' ? self : globalThis);
