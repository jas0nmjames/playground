export function clamp(v: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, v))
}

export function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t
}

export function damp(current: number, target: number, lambda: number, dt: number) {
  const t = 1 - Math.exp(-lambda * dt)
  return lerp(current, target, t)
}

export function wrap01(t: number) {
  let x = t % 1
  if (x < 0) x += 1
  return x
}

export function headingToForward(yaw: number) {
  return { x: Math.sin(yaw), z: Math.cos(yaw) }
}

export function mphFromMps(mps: number) {
  return mps * 2.2369362920544
}

