/*
 * Draws the two liquids.
 *
 * Each chamber's particles are splatted into an offscreen "field" texture.
 * The four colour channels of that texture hold four separate fields, and
 * the simulation gives touching blobs different channels, so two drops that
 * are pressed together still get two outlines. A final pass turns each field
 * into a crisp, anti-aliased shape, shades it, and multiplies the two
 * chambers' colours over the glass, the way two stacked colour filters would.
 */
(function (root) {
  'use strict';

  var VS_POINT = [
    'attribute vec4 a_p;',             // x, y, local spacing, channel
    'uniform vec4 u_view;',            // x0, y0, 2/w, 2/h
    'uniform vec2 u_offset;',
    'uniform float u_size;',
    'varying vec4 v_mask;',
    'void main() {',
    '  vec2 p = a_p.xy + u_offset;',
    '  gl_Position = vec4((p.x - u_view.x) * u_view.z - 1.0, 1.0 - (p.y - u_view.y) * u_view.w, 0.0, 1.0);',
    '  gl_PointSize = a_p.z * u_size;',
    '  float c = a_p.w;',
    '  v_mask = vec4(float(c < 0.5), float(c > 0.5 && c < 1.5), float(c > 1.5 && c < 2.5), float(c > 2.5));',
    '}'
  ].join('\n');

  var FS_POINT = [
    'precision mediump float;',
    'varying vec4 v_mask;',
    'void main() {',
    '  vec2 c = gl_PointCoord * 2.0 - 1.0;',
    '  float w = 1.0 - dot(c, c);',
    '  if (w <= 0.0) discard;',
    '  gl_FragColor = v_mask * (w * w);',
    '}'
  ].join('\n');

  var VS_QUAD = [
    'attribute vec2 a_q;',
    'varying vec2 v_uv;',
    'void main() { v_uv = a_q * 0.5 + 0.5; gl_Position = vec4(a_q, 0.0, 1.0); }'
  ].join('\n');

  var FS_BLUR = [
    'precision mediump float;',
    'varying vec2 v_uv;',
    'uniform sampler2D u_tex;',
    'uniform vec2 u_dir;',
    'void main() {',
    '  vec4 s = texture2D(u_tex, v_uv) * 0.375;',
    '  s += (texture2D(u_tex, v_uv + u_dir) + texture2D(u_tex, v_uv - u_dir)) * 0.25;',
    '  s += (texture2D(u_tex, v_uv + 2.0 * u_dir) + texture2D(u_tex, v_uv - 2.0 * u_dir)) * 0.0625;',
    '  gl_FragColor = s;',
    '}'
  ].join('\n');

  var FS_COMPOSE = [
    'precision highp float;',
    'varying vec2 v_uv;',
    'uniform sampler2D u_a, u_b, u_back;',
    'uniform vec2 u_texel;',           // one field texel in uv
    'uniform float u_px;',             // screen pixels per field texel
    'uniform float u_thresh;',
    'uniform float u_rim;',            // rim width in screen pixels
    'uniform vec2 u_light;',           // direction toward the light, in texture space
    'uniform vec3 u_colA, u_rimA, u_colB, u_rimB;',
    'uniform float u_debug;',
    '',
    'vec3 layer(sampler2D tex, vec3 col, vec3 rimCol, out float alpha, out float gloss) {',
    '  vec4 f = texture2D(tex, v_uv);',
    '  vec4 fx = texture2D(tex, v_uv + vec2(u_texel.x, 0.0)) - texture2D(tex, v_uv - vec2(u_texel.x, 0.0));',
    '  vec4 fy = texture2D(tex, v_uv + vec2(0.0, u_texel.y)) - texture2D(tex, v_uv - vec2(0.0, u_texel.y));',
    '  vec4 g = sqrt(fx * fx + fy * fy) * 0.5 + 0.003;',
    '  vec4 d = (f - u_thresh) / g * u_px;',      // distance inside each blob edge, in pixels
    '  vec4 cov = clamp(d + 0.5, 0.0, 1.0);',
    '  alpha = max(max(cov.r, cov.g), max(cov.b, cov.a));',
    '  float dm = max(max(d.r, d.g), max(d.b, d.a));',
    '  vec4 pick = step(dm - 0.01, d);',
    '  vec2 n = -vec2(dot(pick, fx), dot(pick, fy));',
    '  n /= (length(n) + 1e-5);',
    '  float rim = 1.0 - smoothstep(0.0, u_rim, dm);',
    '  float band = smoothstep(0.35 * u_rim, 1.3 * u_rim, dm) * (1.0 - smoothstep(1.8 * u_rim, 4.0 * u_rim, dm));',
    '  float facing = max(dot(n, u_light), 0.0);',
    '  gloss = band * facing * facing * facing;',
    '  float shade = max(dot(n, -u_light), 0.0) * (1.0 - smoothstep(0.0, 3.0 * u_rim, dm));',
    '  vec3 c = mix(col, rimCol, clamp(rim * 0.8 + shade * 0.35, 0.0, 1.0));',
    '  return mix(c, vec3(1.0), gloss * 0.45);',
    '}',
    '',
    'void main() {',
    '  float aA, gA, aB, gB;',
    '  vec3 cA = layer(u_a, u_colA, u_rimA, aA, gA);',
    '  vec3 cB = layer(u_b, u_colB, u_rimB, aB, gB);',
    '  vec4 back = texture2D(u_back, v_uv);',
    '  vec3 through = mix(vec3(1.0), cA, aA) * mix(vec3(1.0), cB, aB);',
    '  vec3 col = back.rgb * through;',
    '  col += back.a * 0.10 * max(gA * aA, gB * aB);',
    '  if (u_debug > 0.5) {',
    '    vec4 f = texture2D(u_a, v_uv);',
    '    col = mix(back.rgb, vec3(f.r + f.a, f.g + f.a * 0.6, f.b), 0.85);',
    '  }',
    '  gl_FragColor = vec4(col, back.a);',
    '}'
  ].join('\n');

  function compile(gl, type, src) {
    var sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      throw new Error('Shader compile failed: ' + gl.getShaderInfoLog(sh));
    }
    return sh;
  }
  function program(gl, vs, fs) {
    var p = gl.createProgram();
    gl.attachShader(p, compile(gl, gl.VERTEX_SHADER, vs));
    gl.attachShader(p, compile(gl, gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      throw new Error('Shader link failed: ' + gl.getProgramInfoLog(p));
    }
    var u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (var i = 0; i < n; i++) {
      var info = gl.getActiveUniform(p, i);
      u[info.name] = gl.getUniformLocation(p, info.name);
    }
    return { p: p, u: u };
  }

  var LOOK = {
    splat: 1.3,            // splat radius / local particle spacing
    threshold: 0.6,
    rim: 0.011,            // width of the darker outline, in device units
    offsetB: [-0.005, -0.014],     // parallax of the rear chamber, in device units
    colA: [0.16, 0.66, 0.93], rimA: [0.05, 0.42, 0.80],      // front chamber: cyan
    colB: [0.95, 0.17, 0.72], rimB: [0.74, 0.05, 0.55],      // rear chamber: magenta
    light: [-0.55, -0.83]  // toward the light, in screen space (x right, y down)
  };

  function Renderer(canvas, view) {
    var gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: true, antialias: false }) ||
      canvas.getContext('experimental-webgl');
    if (!gl) throw new Error('WebGL is not available');
    this.gl = gl;
    this.canvas = canvas;
    this.view = view;                  // { x0, y0, w, h } in device units
    this.look = LOOK;
    this.debug = false;

    this.pPoint = program(gl, VS_POINT, FS_POINT);
    this.pBlur = program(gl, VS_QUAD, FS_BLUR);
    this.pCompose = program(gl, VS_QUAD, FS_COMPOSE);

    this.quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    this.points = gl.createBuffer();
    this.pointCap = 0;

    this.back = gl.createTexture();
    this.fields = null;
    this.maxPoint = gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE)[1];
    gl.disable(gl.DEPTH_TEST);
  }

  Renderer.prototype._target = function (w, h) {
    var gl = this.gl;
    var tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    var fb = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    return { tex: tex, fb: fb, w: w, h: h };
  };

  // Call after the canvas backing size changes. backCanvas is the 2D canvas
  // holding the glass body, drawn at the same size.
  Renderer.prototype.resize = function (backCanvas) {
    var gl = this.gl, cw = this.canvas.width, ch = this.canvas.height;
    var pxPerUnit = cw / this.view.w;
    // The field can be coarser than the screen: edges are rebuilt from its
    // gradient. Keep the largest splat within the point size limit.
    var scale = Math.min(1, Math.max(0.4, 300 / pxPerUnit));
    var spacing = 0.03;
    var limit = this.maxPoint / (2 * this.look.splat * spacing * pxPerUnit);
    if (scale > limit) scale = limit;
    var fw = Math.max(16, Math.round(cw * scale)), fh = Math.max(16, Math.round(ch * scale));
    var self = this;
    if (this.fields) {
      this.fields.forEach(function (t) { gl.deleteTexture(t.tex); gl.deleteFramebuffer(t.fb); });
    }
    this.fields = [this._target(fw, fh), this._target(fw, fh), this._target(fw, fh)];
    this.fieldScale = fw / cw;

    gl.bindTexture(gl.TEXTURE_2D, this.back);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, backCanvas);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    self.ready = true;
  };

  Renderer.prototype._quad = function (prog) {
    var gl = this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    var loc = gl.getAttribLocation(prog.p, 'a_q');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  };

  Renderer.prototype._splat = function (target, buf, n, offset) {
    var gl = this.gl, P = this.pPoint, v = this.view;
    gl.bindFramebuffer(gl.FRAMEBUFFER, target.fb);
    gl.viewport(0, 0, target.w, target.h);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    if (!n) return;
    gl.useProgram(P.p);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.points);
    if (buf.byteLength > this.pointCap) {
      gl.bufferData(gl.ARRAY_BUFFER, buf, gl.DYNAMIC_DRAW);
      this.pointCap = buf.byteLength;
    } else {
      gl.bufferSubData(gl.ARRAY_BUFFER, 0, buf);
    }
    var loc = gl.getAttribLocation(P.p, 'a_p');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 4, gl.FLOAT, false, 0, 0);
    gl.uniform4f(P.u.u_view, v.x0, v.y0, 2 / v.w, 2 / v.h);
    gl.uniform2f(P.u.u_offset, offset[0], offset[1]);
    gl.uniform1f(P.u.u_size, 2 * this.look.splat * target.w / v.w);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE);
    gl.drawArrays(gl.POINTS, 0, n);
    gl.disable(gl.BLEND);
  };

  Renderer.prototype._blur = function (src, tmp) {
    var gl = this.gl, P = this.pBlur;
    gl.useProgram(P.p);
    gl.activeTexture(gl.TEXTURE0);
    gl.uniform1i(P.u.u_tex, 0);
    gl.viewport(0, 0, src.w, src.h);
    gl.bindFramebuffer(gl.FRAMEBUFFER, tmp.fb);
    gl.bindTexture(gl.TEXTURE_2D, src.tex);
    gl.uniform2f(P.u.u_dir, 1 / src.w, 0);
    this._quad(P);
    gl.bindFramebuffer(gl.FRAMEBUFFER, src.fb);
    gl.bindTexture(gl.TEXTURE_2D, tmp.tex);
    gl.uniform2f(P.u.u_dir, 0, 1 / src.h);
    this._quad(P);
  };

  // a and b are { buf: Float32Array of x,y,spacing,channel, n }. angle is the
  // rotation of the device, used to keep the light fixed in the room.
  Renderer.prototype.draw = function (a, b, angle) {
    if (!this.ready) return;
    var gl = this.gl, L = this.look, F = this.fields;
    this._splat(F[0], a.buf, a.n, [0, 0]);
    this._blur(F[0], F[2]);
    this._splat(F[1], b.buf, b.n, L.offsetB);
    this._blur(F[1], F[2]);

    var P = this.pCompose;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(P.p);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, F[0].tex);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, F[1].tex);
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, this.back);
    gl.uniform1i(P.u.u_a, 0); gl.uniform1i(P.u.u_b, 1); gl.uniform1i(P.u.u_back, 2);
    gl.uniform2f(P.u.u_texel, 1 / F[0].w, 1 / F[0].h);
    gl.uniform1f(P.u.u_px, 1 / this.fieldScale);
    gl.uniform1f(P.u.u_thresh, L.threshold);
    gl.uniform1f(P.u.u_rim, L.rim * this.canvas.width / this.view.w);
    // light direction in the device's own frame, then into texture space (y up)
    var c = Math.cos(angle), s = Math.sin(angle);
    var lx = L.light[0] * c + L.light[1] * s, ly = -L.light[0] * s + L.light[1] * c;
    gl.uniform2f(P.u.u_light, lx, -ly);
    gl.uniform3fv(P.u.u_colA, L.colA); gl.uniform3fv(P.u.u_rimA, L.rimA);
    gl.uniform3fv(P.u.u_colB, L.colB); gl.uniform3fv(P.u.u_rimB, L.rimB);
    gl.uniform1f(P.u.u_debug, this.debug ? 1 : 0);
    gl.activeTexture(gl.TEXTURE0);
    this._quad(P);
  };

  root.HGRenderer = Renderer;
  root.HGLook = LOOK;
})(window);
