/*
 * Geometry of one chamber of the hourglass, in device units.
 *
 * The device is 1 unit wide at its ends and H units tall. x runs from -0.5 to
 * 0.5, y runs from 0 (one end) to H (the other end). The shape is symmetric
 * left to right and end to end, so turning it over gives the same object.
 *
 * Each end holds a deep chamber. The middle section is a thin slot. A V-shaped
 * plate separates them, with a nozzle at its centre and a vent at each wall.
 *
 * The file is one named function so that its source can also be handed to a
 * Web Worker.
 *
 * It builds three lookup grids from the shape:
 *   sdf   signed distance to the nearest wall (positive in free space)
 *   depth how deep the cell is at that point, relative to the thin slot
 *   zone  marks the nozzle bore (1) and the vents (2)
 */
function HGGeometryModule(root) {
  'use strict';

  var DEFAULTS = {
    H: 2.6,
    endHalf: 0.5,        // half width of the body at its ends
    waistHalf: 0.385,    // half width at the waist
    shoulder: 0.62,      // where the waist curve meets the straight end block
    profExp: 1.2,
    wall: 0.055,         // side wall thickness
    cap: 0.085,          // end cap thickness
    outerRadius: 0.075,
    innerRadius: 0.045,

    plateY: 0.80,        // centre line of the plate at x = 0
    plateSlope: 0.268,   // rise of the plate toward the walls (about 15 degrees)
    plateThick: 0.035,   // vertical thickness of the plate
    bore: 0.05,          // nozzle bore width
    boreChamfer: 0.014,
    lipLen: 0.03,        // how far the spout sticks out of the plate
    lipBase: 0.062,      // half width of the spout where it meets the plate
    lipTip: 0.038,       // half width of the spout at its tip
    vent: 0.06,          // gap between the plate end and the side wall

    depth: 4,            // end chambers are this many times deeper than the slot
    depthBlend: 0.03,    // length over which the depth changes at an opening
    ventPocket: 0.03,    // the depth change starts this far outside a vent

    cell: 0.004,         // grid resolution
    band: 0.07           // distances are only tracked this close to a wall
  };

  function smooth(t) {
    t = t < 0 ? 0 : t > 1 ? 1 : t;
    return t * t * (3 - 2 * t);
  }

  function build(opts) {
    var G = {};
    var k;
    for (k in DEFAULTS) G[k] = DEFAULTS[k];
    if (opts) for (k in opts) G[k] = opts[k];

    var H = G.H;
    var th = G.plateThick / 2;
    var bw = G.bore / 2;

    function outerHalf(y) {
      var u = Math.abs(y - H / 2) / (H / 2);
      var t = Math.min(1, u / G.shoulder);
      return G.waistHalf + (G.endHalf - G.waistHalf) *
        Math.pow(Math.sin(t * Math.PI / 2), G.profExp);
    }
    function innerHalf(y) { return outerHalf(y) - G.wall; }

    // Centre line of the plate in the y < H/2 half.
    function plateY(ax) { return G.plateY - G.plateSlope * ax; }

    // Where the plate ends, leaving the vent gap to the wall.
    var xEnd = 0.38;
    for (var it = 0; it < 20; it++) xEnd = innerHalf(plateY(xEnd)) - G.vent;

    var yTip = G.plateY + th + G.lipLen;   // spout tip
    var yVent = plateY(xEnd) - th;         // chamber-side mouth of the vent
    var yVentSlot = plateY(xEnd) + th;     // slot-side mouth of the vent

    // ---- outlines -------------------------------------------------------

    function roundedProfile(half, y0, y1, rad, step) {
      var pts = [];
      var i, a, y;
      var n = 10;
      var xr0 = half(y0 + rad), xr1 = half(y1 - rad);
      for (i = 0; i <= n; i++) {           // top right corner
        a = -Math.PI / 2 + (Math.PI / 2) * (i / n);
        pts.push([xr0 - rad + rad * Math.cos(a), y0 + rad + rad * Math.sin(a)]);
      }
      for (y = y0 + rad + step; y < y1 - rad; y += step) pts.push([half(y), y]);
      for (i = 0; i <= n; i++) {           // bottom right corner
        a = (Math.PI / 2) * (i / n);
        pts.push([xr1 - rad + rad * Math.cos(a), y1 - rad + rad * Math.sin(a)]);
      }
      var m = pts.length;
      for (i = m - 1; i >= 0; i--) pts.push([-pts[i][0], pts[i][1]]);
      return pts;
    }

    var outer = roundedProfile(outerHalf, 0, H, G.outerRadius, 0.02);
    var cavity = roundedProfile(innerHalf, G.cap, H - G.cap, G.innerRadius, 0.012);

    // One half of the plate (x > 0, y < H/2), then mirrored into four pieces.
    var cz = G.boreChamfer;
    var plate = [
      [bw + cz, plateY(bw + cz) - th],
      [xEnd, plateY(xEnd) - th],
      [xEnd, plateY(xEnd) + th],
      [G.lipBase, plateY(G.lipBase) + th],
      [G.lipTip, yTip],
      [bw, yTip],
      [bw, plateY(bw) - th + cz]
    ];
    function mirror(poly, sx, flipY) {
      return poly.map(function (p) { return [p[0] * sx, flipY ? H - p[1] : p[1]]; });
    }
    var plates = [
      mirror(plate, 1, false), mirror(plate, -1, false),
      mirror(plate, 1, true), mirror(plate, -1, true)
    ];

    // ---- depth and zones ------------------------------------------------

    // The y at which a point directly "below" the plate is fully in the slot.
    function mouthY(ax) {
      if (ax <= G.lipTip) return yTip;
      if (ax < G.lipBase) {
        var t = (ax - G.lipTip) / (G.lipBase - G.lipTip);
        return yTip + (plateY(G.lipBase) + th - yTip) * t;
      }
      var base = plateY(Math.min(ax, xEnd)) + th;
      var pocket = G.ventPocket * smooth((ax - (xEnd - G.ventPocket)) / G.ventPocket);
      return base + pocket;
    }
    function depthAt(x, y) {
      var yy = y < H / 2 ? y : H - y;
      var ax = Math.abs(x);
      var ym = mouthY(ax);
      var blend = G.depthBlend + (ax > xEnd - G.ventPocket ? G.ventPocket * 0.5 : 0);
      if (yy >= ym) return 1;
      if (yy <= ym - blend) return G.depth;
      return G.depth + (1 - G.depth) * smooth((yy - (ym - blend)) / blend);
    }
    function zoneAt(x, y) {
      var yy = y < H / 2 ? y : H - y;
      var ax = Math.abs(x);
      if (ax <= bw + 0.004 && yy >= G.plateY - th - 0.012 && yy <= yTip + 0.002) return 1;
      if (ax >= xEnd - 0.002 && yy >= yVent - 0.006 && yy <= yVentSlot + 0.006) return 2;
      return 0;
    }

    // ---- grids ----------------------------------------------------------

    var gs = G.cell, band = G.band;
    var x0 = -0.56, y0 = -0.04;
    var nx = Math.ceil(1.12 / gs) + 1;
    var ny = Math.ceil((H + 0.08) / gs) + 1;
    var sdf = new Float32Array(nx * ny);
    var depth = new Float32Array(nx * ny);
    var zone = new Uint8Array(nx * ny);
    var i, j, c;
    for (i = 0; i < sdf.length; i++) sdf[i] = band;

    function stampSegment(ax, ay, bx, by) {
      var minx = Math.min(ax, bx) - band, maxx = Math.max(ax, bx) + band;
      var miny = Math.min(ay, by) - band, maxy = Math.max(ay, by) + band;
      var i0 = Math.max(0, Math.floor((minx - x0) / gs));
      var i1 = Math.min(nx - 1, Math.ceil((maxx - x0) / gs));
      var j0 = Math.max(0, Math.floor((miny - y0) / gs));
      var j1 = Math.min(ny - 1, Math.ceil((maxy - y0) / gs));
      var ex = bx - ax, ey = by - ay;
      var el = ex * ex + ey * ey || 1e-12;
      for (var jj = j0; jj <= j1; jj++) {
        var py = y0 + jj * gs;
        for (var ii = i0; ii <= i1; ii++) {
          var px = x0 + ii * gs;
          var t = ((px - ax) * ex + (py - ay) * ey) / el;
          t = t < 0 ? 0 : t > 1 ? 1 : t;
          var dx = px - (ax + t * ex), dy = py - (ay + t * ey);
          var dd = Math.sqrt(dx * dx + dy * dy);
          var cc = ii + jj * nx;
          if (dd < sdf[cc]) sdf[cc] = dd;
        }
      }
    }
    function stampPoly(poly) {
      for (var p = 0; p < poly.length; p++) {
        var a = poly[p], b = poly[(p + 1) % poly.length];
        stampSegment(a[0], a[1], b[0], b[1]);
      }
    }
    stampPoly(cavity);
    plates.forEach(stampPoly);

    // Scanline fill to decide which cells are free space.
    function crossings(poly, y) {
      var xs = [];
      for (var p = 0; p < poly.length; p++) {
        var a = poly[p], b = poly[(p + 1) % poly.length];
        if ((a[1] > y) !== (b[1] > y)) {
          xs.push(a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]));
        }
      }
      xs.sort(function (p, q) { return p - q; });
      return xs;
    }
    function insideSpans(xs, x) {
      var inside = false;
      for (var q = 0; q < xs.length; q++) { if (xs[q] > x) break; inside = !inside; }
      return inside;
    }
    for (j = 0; j < ny; j++) {
      var y = y0 + j * gs;
      var cx = crossings(cavity, y);
      var px = plates.map(function (pl) { return crossings(pl, y); });
      for (i = 0; i < nx; i++) {
        var x = x0 + i * gs;
        var free = insideSpans(cx, x);
        if (free) {
          for (var q = 0; q < px.length; q++) {
            if (px[q].length && insideSpans(px[q], x)) { free = false; break; }
          }
        }
        c = i + j * nx;
        if (!free) sdf[c] = -sdf[c];
        depth[c] = depthAt(x, y);
        zone[c] = zoneAt(x, y);
      }
    }

    function sample(grid, x, y) {
      var fx = (x - x0) / gs, fy = (y - y0) / gs;
      var ix = Math.floor(fx), iy = Math.floor(fy);
      if (ix < 0) ix = 0; else if (ix > nx - 2) ix = nx - 2;
      if (iy < 0) iy = 0; else if (iy > ny - 2) iy = ny - 2;
      var tx = fx - ix, ty = fy - iy;
      tx = tx < 0 ? 0 : tx > 1 ? 1 : tx;
      ty = ty < 0 ? 0 : ty > 1 ? 1 : ty;
      var cc = ix + iy * nx;
      return (grid[cc] * (1 - tx) + grid[cc + 1] * tx) * (1 - ty) +
        (grid[cc + nx] * (1 - tx) + grid[cc + nx + 1] * tx) * ty;
    }

    return {
      params: G,
      H: H,
      x0: x0, y0: y0, cell: gs, nx: nx, ny: ny,
      sdf: sdf, depth: depth, zone: zone,
      outer: outer, cavity: cavity, plates: plates,
      outerHalf: outerHalf, innerHalf: innerHalf, plateY: plateY,
      boreHalf: bw, xEnd: xEnd, yTip: yTip, yVent: yVent,
      plateTop: G.plateY - th,
      sdfAt: function (x, y) { return sample(sdf, x, y); },
      depthAt: depthAt,
      zoneAt: zoneAt
    };
  }

  root.HGGeometry = { build: build, DEFAULTS: DEFAULTS };
}
HGGeometryModule(typeof self !== 'undefined' ? self : globalThis);
