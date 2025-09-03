/**
 * Lightweight 2D value noise-ish function.
 * For visual variety and performance, we provide a tiny pseudo-noise (not full simplex/perlin).
 * You can swap this for 'simplex-noise' by changing imports and using its noise2D.
 */
export function makeNoise2D(seed = 1337) {
  // Simple xorshift
  let s = seed | 0;
  const rand = () => {
    s ^= s << 13; s ^= s >>> 17; s ^= s << 5;
    return (s >>> 0) / 4294967296;
  };

  // Hash to gradient
  const grad = (x, y) => {
    const n = Math.sin(x * 127.1 + y * 311.7 + seed) * 43758.5453123;
    return n - Math.floor(n);
  };

  // Smoothstep
  const smooth = (t) => t * t * (3 - 2 * t);

  // 2D noise via bilinear interpolation of grid values
  return function noise(x, y) {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;

    const a = grad(xi, yi);
    const b = grad(xi + 1, yi);
    const c = grad(xi, yi + 1);
    const d = grad(xi + 1, yi + 1);

    const u = smooth(xf), v = smooth(yf);
    const x1 = a * (1 - u) + b * u;
    const x2 = c * (1 - u) + d * u;
    const val = x1 * (1 - v) + x2 * v;

    // Map to [-1,1]
    return val * 2 - 1;
  };
}
