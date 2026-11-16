/*
 * The trapped air bubbles. They are decoration with simple physics: each one
 * rises against gravity at a speed that grows with its size, cannot enter a
 * wall, and cannot overlap another bubble. They ignore the dyed liquid.
 * Bubbles smaller than an opening can work their way through it, so after a
 * flip the small ones drift up to the new top while the large ones stay
 * caught under the plate.
 */
(function (root) {
  'use strict';

  function Bubbles(geom, seed) {
    this.geom = geom;
    var rnd = (function (a) {
      return function () {
        a |= 0; a = a + 0x6D2B79F5 | 0;
        var t = Math.imul(a ^ a >>> 15, 1 | a);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
      };
    })(seed || 7);
    var radii = [0.034, 0.027, 0.024, 0.020, 0.017, 0.015, 0.013, 0.012, 0.010, 0.010, 0.008, 0.008, 0.007, 0.006];
    this.n = radii.length;
    this.x = new Float64Array(this.n); this.y = new Float64Array(this.n);
    this.r = new Float64Array(radii);
    this.vx = new Float64Array(this.n); this.vy = new Float64Array(this.n);
    for (var i = 0; i < this.n; i++) {
      // most start against the ceiling of the full chamber, a few under the far plate
      var low = i % 4 === 3;
      this.x[i] = (rnd() - 0.5) * 0.6;
      this.y[i] = low ? geom.H - geom.plateTop + 0.05 + rnd() * 0.05 : geom.params.cap + 0.04 + rnd() * 0.05;
    }
  }

  Bubbles.prototype.step = function (dt, gx, gy) {
    var g = this.geom, n = this.n, x = this.x, y = this.y, r = this.r, vx = this.vx, vy = this.vy;
    var gl = Math.sqrt(gx * gx + gy * gy) || 1;
    var ux = -gx / gl, uy = -gy / gl;
    var i, j, e = 0.004;
    for (i = 0; i < n; i++) {
      var rise = 0.9 * Math.pow(r[i] / 0.03, 1.3) + 0.05;
      var k = Math.min(1, dt * 12);
      vx[i] += (ux * rise - vx[i]) * k; vy[i] += (uy * rise - vy[i]) * k;
      x[i] += vx[i] * dt; y[i] += vy[i] * dt;
    }
    for (var pass = 0; pass < 3; pass++) {
      for (i = 0; i < n; i++) {
        for (j = i + 1; j < n; j++) {
          var dx = x[j] - x[i], dy = y[j] - y[i], d2 = dx * dx + dy * dy, rr = r[i] + r[j];
          if (d2 < rr * rr && d2 > 1e-12) {
            var d = Math.sqrt(d2), push = 0.5 * (rr - d) / d;
            var wi = r[j] / rr, wj = r[i] / rr;      // the smaller bubble gives way more
            x[i] -= dx * push * 2 * wi; y[i] -= dy * push * 2 * wi;
            x[j] += dx * push * 2 * wj; y[j] += dy * push * 2 * wj;
          }
        }
        var rad = r[i] * 0.92;
        var phi = g.sdfAt(x[i], y[i]);
        if (phi < rad) {
          var nx = g.sdfAt(x[i] + e, y[i]) - g.sdfAt(x[i] - e, y[i]);
          var ny = g.sdfAt(x[i], y[i] + e) - g.sdfAt(x[i], y[i] - e);
          var nl = Math.sqrt(nx * nx + ny * ny);
          if (nl > 1e-9) {
            nx /= nl; ny /= nl;
            x[i] += nx * (rad - phi); y[i] += ny * (rad - phi);
            var vn = vx[i] * nx + vy[i] * ny;
            if (vn < 0) { vx[i] -= vn * nx; vy[i] -= vn * ny; }
          }
        }
      }
    }
  };

  // angle is the device rotation; the glint stays on the side facing the light.
  Bubbles.prototype.draw = function (canvas, view, angle) {
    var ctx = canvas.getContext('2d');
    var s = canvas.width / view.w;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.setTransform(s, 0, 0, s, -view.x0 * s, -view.y0 * s);
    var c = Math.cos(angle), sn = Math.sin(angle);
    var lx = -0.55 * c - 0.83 * sn, ly = 0.55 * sn - 0.83 * c;
    for (var i = 0; i < this.n; i++) {
      var x = this.x[i], y = this.y[i], r = this.r[i];
      var g = ctx.createRadialGradient(x, y, r * 0.35, x, y, r);
      g.addColorStop(0, 'rgba(255,255,255,0.10)');
      g.addColorStop(0.72, 'rgba(255,255,255,0.22)');
      g.addColorStop(0.9, 'rgba(70,86,108,0.30)');
      g.addColorStop(1, 'rgba(50,64,84,0.55)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.beginPath(); ctx.arc(x + lx * r * 0.45, y + ly * r * 0.45, r * 0.22, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.45)';
      ctx.beginPath(); ctx.arc(x - lx * r * 0.5, y - ly * r * 0.5, r * 0.12, 0, Math.PI * 2); ctx.fill();
    }
  };

  root.HGBubbles = Bubbles;
})(window);
