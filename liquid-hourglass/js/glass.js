/*
 * Draws the clear acrylic body with Canvas 2D. Nothing here moves, so it is
 * drawn once per resize: a "back" layer that the liquid is filtered over, and
 * a "shine" layer of reflections that sits on top of everything.
 */
(function (root) {
  'use strict';

  function trace(ctx, pts) {
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.closePath();
  }

  // Stroke the current path several times with shrinking width to fake a
  // soft edge without relying on canvas filters.
  function softStroke(ctx, colour, widths, alphas) {
    for (var i = 0; i < widths.length; i++) {
      ctx.strokeStyle = colour.replace('A', alphas[i]);
      ctx.lineWidth = widths[i];
      ctx.stroke();
    }
  }

  function begin(ctx, view, canvas) {
    var s = canvas.width / view.w;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.setTransform(s, 0, 0, s, -view.x0 * s, -view.y0 * s);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
  }

  function scallops(ctx, geom, flip) {
    var H = geom.H, cap = geom.params.cap, r = 0.034;
    var xs = [-0.305, -0.225, -0.145, 0.145, 0.225, 0.305];
    for (var i = 0; i < xs.length; i++) {
      var y = flip ? H - cap : cap;
      ctx.beginPath();
      ctx.arc(xs[i], y, r, flip ? 0 : Math.PI, flip ? Math.PI : 0, false);
      ctx.closePath();
      ctx.fillStyle = '#f4f6f8';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(xs[i], y, r, flip ? 0 : Math.PI, flip ? Math.PI : 0, false);
      ctx.strokeStyle = 'rgba(255,255,255,0.95)'; ctx.lineWidth = 0.011; ctx.stroke();
      ctx.strokeStyle = 'rgba(84,98,116,0.45)'; ctx.lineWidth = 0.004; ctx.stroke();
    }
  }

  function drawBack(canvas, geom, view, ghostOffset) {
    var ctx = canvas.getContext('2d');
    begin(ctx, view, canvas);
    var g;

    // solid acrylic
    trace(ctx, geom.outer);
    g = ctx.createLinearGradient(-0.5, 0, 0.5, 0);
    g.addColorStop(0, '#c3cad3'); g.addColorStop(0.07, '#dfe4ea'); g.addColorStop(0.5, '#eef1f4');
    g.addColorStop(0.93, '#dde2e8'); g.addColorStop(1, '#bcc4ce');
    ctx.fillStyle = g;
    ctx.fill();
    ctx.save();
    ctx.clip();
    softStroke(ctx, 'rgba(70,84,104,A)', [0.11, 0.07, 0.04, 0.02], [0.05, 0.06, 0.08, 0.12]);
    ctx.strokeStyle = 'rgba(52,64,82,0.55)'; ctx.lineWidth = 0.008; ctx.stroke();
    ctx.restore();

    // the cavity, full of clear oil
    trace(ctx, geom.cavity);
    g = ctx.createLinearGradient(-0.45, 0, 0.45, 0);
    g.addColorStop(0, '#e9edf1'); g.addColorStop(0.2, '#f6f7f9'); g.addColorStop(0.8, '#f5f6f8'); g.addColorStop(1, '#e6eaef');
    ctx.fillStyle = g;
    ctx.fill();
    ctx.save();
    ctx.clip();
    softStroke(ctx, 'rgba(80,96,118,A)', [0.08, 0.045, 0.02], [0.035, 0.05, 0.07]);
    ctx.restore();
    scallops(ctx, geom, false);
    scallops(ctx, geom, true);
    trace(ctx, geom.cavity);
    ctx.strokeStyle = 'rgba(255,255,255,0.95)'; ctx.lineWidth = 0.013; ctx.stroke();
    ctx.strokeStyle = 'rgba(84,98,116,0.5)'; ctx.lineWidth = 0.004; ctx.stroke();

    // the plates: once faintly for the rear chamber, then for the front one
    function plates(alpha) {
      ctx.globalAlpha = alpha;
      geom.plates.forEach(function (pl) {
        trace(ctx, pl);
        ctx.fillStyle = 'rgba(214,221,229,0.9)'; ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.95)'; ctx.lineWidth = 0.011; ctx.stroke();
        ctx.strokeStyle = 'rgba(78,92,110,0.6)'; ctx.lineWidth = 0.0038; ctx.stroke();
      });
      ctx.globalAlpha = 1;
    }
    ctx.save();
    ctx.translate(ghostOffset[0], ghostOffset[1]);
    plates(0.35);
    ctx.restore();
    plates(1);
  }

  function drawShine(canvas, geom, view) {
    var ctx = canvas.getContext('2d');
    begin(ctx, view, canvas);
    var H = geom.H, y;

    function along(half, inset, y0, y1, side) {
      ctx.beginPath();
      for (y = y0; y <= y1; y += 0.02) {
        var x = side * (half(y) - inset);
        if (y === y0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
    }

    // long soft reflection down the lit side, a thinner one on the far side
    along(geom.innerHalf, 0.06, 0.2, H - 0.2, -1);
    softStroke(ctx, 'rgba(255,255,255,A)', [0.075, 0.05, 0.028, 0.012], [0.07, 0.1, 0.16, 0.3]);
    along(geom.innerHalf, 0.035, 0.3, H - 0.3, 1);
    softStroke(ctx, 'rgba(255,255,255,A)', [0.03, 0.012], [0.08, 0.2]);

    // bright edges of the block itself
    along(geom.outerHalf, 0.014, 0.12, 1.0, -1);
    softStroke(ctx, 'rgba(255,255,255,A)', [0.022, 0.009], [0.25, 0.75]);
    along(geom.outerHalf, 0.014, 1.75, H - 0.1, -1);
    softStroke(ctx, 'rgba(255,255,255,A)', [0.022, 0.009], [0.2, 0.6]);
    along(geom.outerHalf, 0.016, 0.5, 2.0, 1);
    softStroke(ctx, 'rgba(255,255,255,A)', [0.012], [0.4]);

    // end caps catch the light along their length
    ctx.beginPath(); ctx.moveTo(-0.4, 0.028); ctx.lineTo(0.36, 0.028);
    softStroke(ctx, 'rgba(255,255,255,A)', [0.03, 0.012], [0.2, 0.6]);
    ctx.beginPath(); ctx.moveTo(-0.38, H - 0.03); ctx.lineTo(0.3, H - 0.03);
    softStroke(ctx, 'rgba(255,255,255,A)', [0.026, 0.01], [0.15, 0.4]);

    // a faint slanted sheen across the waist
    var g = ctx.createLinearGradient(-0.3, 1.0, 0.3, 1.5);
    g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.45, 'rgba(255,255,255,0.10)');
    g.addColorStop(0.55, 'rgba(255,255,255,0.10)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.save();
    trace(ctx, geom.cavity); ctx.clip();
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(-0.5, 1.05); ctx.lineTo(0.5, 0.75); ctx.lineTo(0.5, 1.3); ctx.lineTo(-0.5, 1.6); ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  root.HGGlass = { drawBack: drawBack, drawShine: drawShine };
})(window);
