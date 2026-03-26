import { clamp } from './util'

export type InputState = {
  steer: number // -1..1
  throttle: number // 0..1
  brake: number // 0..1
  drift: boolean
  reset: boolean
}

type Lever = {
  el: HTMLElement
  knob: HTMLElement
  axis: 'x' | 'y'
  value: number
  activePointerId: number | null
}

function makeLever(el: HTMLElement, axis: 'x' | 'y'): Lever {
  const knob = el.querySelector<HTMLElement>('.knob')
  if (!knob) throw new Error('Lever knob missing')
  const lever: Lever = { el, knob, axis, value: 0, activePointerId: null }

  const updateFromPointer = (clientX: number, clientY: number) => {
    const r = el.getBoundingClientRect()
    const cx = clamp((clientX - r.left) / r.width, 0, 1)
    const cy = clamp((clientY - r.top) / r.height, 0, 1)
    const vx = (cx - 0.5) * 2
    const vy = (0.5 - cy) * 2
    lever.value = clamp(axis === 'x' ? vx : vy, -1, 1)
    const knobX = axis === 'x' ? 50 + lever.value * 40 : 50
    const knobY = axis === 'y' ? 50 - lever.value * 40 : 50
    knob.style.left = `${knobX}%`
    knob.style.top = `${knobY}%`
  }

  el.addEventListener('pointerdown', (e) => {
    lever.activePointerId = e.pointerId
    ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
    updateFromPointer(e.clientX, e.clientY)
  })
  el.addEventListener('pointermove', (e) => {
    if (lever.activePointerId !== e.pointerId) return
    updateFromPointer(e.clientX, e.clientY)
  })
  const end = (e: PointerEvent) => {
    if (lever.activePointerId !== e.pointerId) return
    lever.activePointerId = null
    lever.value = 0
    knob.style.left = `50%`
    knob.style.top = `50%`
  }
  el.addEventListener('pointerup', end)
  el.addEventListener('pointercancel', end)

  return lever
}

export function setupInput() {
  const state: InputState = { steer: 0, throttle: 0, brake: 0, drift: false, reset: false }

  const keys = new Set<string>()
  window.addEventListener('keydown', (e) => keys.add(e.key.toLowerCase()))
  window.addEventListener('keyup', (e) => keys.delete(e.key.toLowerCase()))

  const btnDrift = document.getElementById('btnDrift') as HTMLButtonElement | null
  const btnReset = document.getElementById('btnReset') as HTMLButtonElement | null

  btnDrift?.addEventListener('click', () => {
    state.drift = !state.drift
    btnDrift.classList.toggle('secondary', !state.drift)
  })
  btnReset?.addEventListener('click', () => {
    state.reset = true
    setTimeout(() => (state.reset = false), 0)
  })

  const leverSteerEl = document.getElementById('leverSteer')
  const leverThrottleEl = document.getElementById('leverThrottle')
  const leverSteer = leverSteerEl ? makeLever(leverSteerEl, 'x') : null
  const leverThrottle = leverThrottleEl ? makeLever(leverThrottleEl, 'y') : null

  const poll = () => {
    // Keyboard
    const left = keys.has('a') || keys.has('arrowleft')
    const right = keys.has('d') || keys.has('arrowright')
    const up = keys.has('w') || keys.has('arrowup')
    const down = keys.has('s') || keys.has('arrowdown')
    const driftKey = keys.has(' ') || keys.has('shift')

    // Reverse keyboard steering: left arrow turns right, right arrow turns left
    const steerK = (left ? 1 : 0) - (right ? 1 : 0)
    const throttleK = up ? 1 : 0
    const brakeK = down ? 1 : 0

    const steerL = leverSteer?.value ?? 0
    const throttleL = leverThrottle ? clamp(Math.max(0, leverThrottle.value), 0, 1) : 0
    const brakeL = leverThrottle ? clamp(Math.max(0, -leverThrottle.value), 0, 1) : 0

    state.steer = clamp(Math.abs(steerL) > Math.abs(steerK) ? steerL : steerK, -1, 1)
    state.throttle = clamp(Math.max(throttleL, throttleK), 0, 1)
    state.brake = clamp(Math.max(brakeL, brakeK), 0, 1)
    if (driftKey) state.drift = true
  }

  return { state, poll }
}

