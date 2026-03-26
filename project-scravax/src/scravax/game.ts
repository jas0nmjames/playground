import * as THREE from 'three'
import { setupInput } from './input'
import { closestTrackT, buildTrackMeshes, makeGeorgiaTrack } from './track'
import { clamp, damp, headingToForward, mphFromMps, wrap01 } from './util'
import { createNetSession, type NetPeerState } from './net'

type Car = {
  id: string
  name: string
  color: number
  mesh: THREE.Group
  pos: THREE.Vector3
  vel: THREE.Vector3
  yaw: number
  progress: number
  lap: number
  finished: boolean
  lastProgress: number
  lastStateAt: number
}

function makeCarMesh(color: number) {
  const g = new THREE.Group()
  const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.45, metalness: 0.25 })
  const glassMat = new THREE.MeshStandardMaterial({ color: 0x0b1a2c, roughness: 0.15, metalness: 0.2, transparent: true, opacity: 0.7 })
  const tireMat = new THREE.MeshStandardMaterial({ color: 0x101318, roughness: 1, metalness: 0.05 })

  const body = new THREE.Mesh(new THREE.BoxGeometry(3.2, 1.0, 6.2), bodyMat)
  body.position.y = 0.9
  body.castShadow = true
  const cabin = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.9, 2.6), glassMat)
  cabin.position.set(0, 1.55, -0.2)
  cabin.castShadow = true

  const wheelGeo = new THREE.CylinderGeometry(0.55, 0.55, 0.55, 14)
  const mkWheel = (x: number, z: number) => {
    const w = new THREE.Mesh(wheelGeo, tireMat)
    w.rotation.z = Math.PI / 2
    w.position.set(x, 0.55, z)
    w.castShadow = true
    return w
  }
  g.add(body, cabin, mkWheel(-1.35, 2.2), mkWheel(1.35, 2.2), mkWheel(-1.35, -2.2), mkWheel(1.35, -2.2))

  const underGlow = new THREE.PointLight(color, 0.55, 10, 2)
  underGlow.position.set(0, 0.25, 0)
  g.add(underGlow)

  return g
}

function setCarTransform(c: Car) {
  c.mesh.position.copy(c.pos)
  c.mesh.rotation.y = c.yaw
}

function makeNameTag(name: string) {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 64
  const ctx = canvas.getContext('2d')!
  ctx.fillStyle = 'rgba(10,14,24,0.55)'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.font = '900 28px system-ui, -apple-system, Segoe UI, Roboto'
  ctx.fillStyle = 'rgba(234,240,255,0.92)'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(name, canvas.width / 2, canvas.height / 2)
  const tex = new THREE.CanvasTexture(canvas)
  tex.minFilter = THREE.LinearFilter
  const mat = new THREE.SpriteMaterial({ map: tex, transparent: true })
  const sprite = new THREE.Sprite(mat)
  sprite.scale.set(10, 2.5, 1)
  sprite.position.set(0, 4.2, 0)
  return sprite
}

export async function startGame() {
  const canvas = document.getElementById('game') as HTMLCanvasElement | null
  if (!canvas) throw new Error('Canvas not found')

  // Ensure keyboard works immediately without clicking
  canvas.focus()
  window.addEventListener('click', () => {
    if (document.activeElement !== canvas) {
      canvas.focus()
    }
  })

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap

  const scene = new THREE.Scene()
  // Softer, more realistic daytime blue sky
  scene.fog = new THREE.Fog(0x87ceeb, 180, 720)
  scene.background = new THREE.Color(0x87ceeb)

  const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 1400)
  camera.position.set(0, 10, -18)

  const hemi = new THREE.HemisphereLight(0xa8c7ff, 0x3b1f17, 0.75)
  scene.add(hemi)
  const sun = new THREE.DirectionalLight(0xffffff, 1.1)
  sun.position.set(120, 220, -80)
  sun.castShadow = true
  sun.shadow.mapSize.set(2048, 2048)
  sun.shadow.camera.left = -280
  sun.shadow.camera.right = 280
  sun.shadow.camera.top = 280
  sun.shadow.camera.bottom = -280
  scene.add(sun)

  const track = makeGeorgiaTrack()
  const { group: trackGroup, finishPoint, finishYaw } = buildTrackMeshes(track)
  scene.add(trackGroup)

  const finishLine = new THREE.Mesh(new THREE.PlaneGeometry(track.width * 0.95, 1.6), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.65, metalness: 0 }))
  finishLine.rotation.x = -Math.PI / 2
  finishLine.rotation.z = Math.PI / 2
  finishLine.rotation.y = finishYaw
  finishLine.position.copy(finishPoint)
  finishLine.position.y = 0.01
  finishLine.receiveShadow = true
  scene.add(finishLine)

  const { state: input, poll: pollInput } = setupInput()

  // HUD
  const elSpeed = document.getElementById('speed')
  const elPoints = document.getElementById('points')
  const elPlace = document.getElementById('place')
  const elTotal = document.getElementById('total')
  const elLap = document.getElementById('lap')
  const elNet = document.getElementById('netStatus')

  let points = 0
  let above100Timer = 0

  // Cars
  const cars: Car[] = []
  const spawnT = 0.98
  const spawnP = track.curve.getPointAt(spawnT)
  const spawnTan = track.curve.getTangentAt(spawnT).normalize()
  const spawnYaw = Math.atan2(spawnTan.x, spawnTan.z)

  const player: Car = {
    id: 'local',
    name: 'You',
    color: 0x5d82ff,
    mesh: makeCarMesh(0x5d82ff),
    pos: spawnP.clone().add(new THREE.Vector3(-2.2, 0, 0)),
    vel: new THREE.Vector3(),
    yaw: spawnYaw,
    progress: spawnT,
    lap: 1,
    finished: false,
    lastProgress: spawnT,
    lastStateAt: performance.now(),
  }
  player.mesh.add(makeNameTag(player.name))
  scene.add(player.mesh)
  cars.push(player)

  const aiColors = [0xff6a5d, 0x55ffa1, 0xffd25a]
  for (let i = 0; i < 3; i++) {
    const t = wrap01(spawnT - 0.02 * (i + 1))
    const p = track.curve.getPointAt(t)
    const tan = track.curve.getTangentAt(t).normalize()
    const yaw = Math.atan2(tan.x, tan.z)
    const c: Car = {
      id: `ai-${i}`,
      name: `AI-${i + 1}`,
      color: aiColors[i % aiColors.length],
      mesh: makeCarMesh(aiColors[i % aiColors.length]),
      pos: p.clone().add(new THREE.Vector3(2.2, 0, 0)),
      vel: new THREE.Vector3(),
      yaw,
      progress: t,
      lap: 1,
      finished: false,
      lastProgress: t,
      lastStateAt: performance.now(),
    }
    c.mesh.add(makeNameTag(c.name))
    scene.add(c.mesh)
    cars.push(c)
  }

  // Multiplayer
  const net = createNetSession()
  let remote: Car | null = null

  net.onPeerHello((p) => {
    if (remote && remote.id === p.id) return
    if (remote) {
      scene.remove(remote.mesh)
      cars.splice(cars.indexOf(remote), 1)
      remote = null
    }
    const t = wrap01(spawnT - 0.06)
    const rp = track.curve.getPointAt(t)
    const rt = track.curve.getTangentAt(t).normalize()
    remote = {
      id: p.id,
      name: p.name,
      color: p.color,
      mesh: makeCarMesh(p.color),
      pos: rp.clone().add(new THREE.Vector3(0, 0, 2.6)),
      vel: new THREE.Vector3(),
      yaw: Math.atan2(rt.x, rt.z),
      progress: t,
      lap: 1,
      finished: false,
      lastProgress: t,
      lastStateAt: performance.now(),
    }
    remote.mesh.add(makeNameTag(remote.name))
    scene.add(remote.mesh)
    cars.push(remote)
  })

  net.onPeerState((s) => {
    if (!remote || remote.id !== s.id) return
    remote.lastStateAt = performance.now()
    remote.finished = s.finished
    remote.lap = s.lap
    remote.progress = s.progress
    remote.yaw = s.yaw
    remote.pos.set(s.x, s.y, s.z)
    remote.vel.set(s.vx, 0, s.vz)
  })

  // Multiplayer modal wiring
  const modal = document.getElementById('modal')
  const btnMultiplayer = document.getElementById('btnMultiplayer')
  const btnCloseModal = document.getElementById('btnCloseModal')
  const btnHost = document.getElementById('btnHost')
  const btnJoin = document.getElementById('btnJoin')
  const btnSetAnswer = document.getElementById('btnSetAnswer')
  const outOffer = document.getElementById('outOffer') as HTMLTextAreaElement | null
  const inOffer = document.getElementById('inOffer') as HTMLTextAreaElement | null
  const outAnswer = document.getElementById('outAnswer') as HTMLTextAreaElement | null
  const inAnswer = document.getElementById('inAnswer') as HTMLTextAreaElement | null

  const showModal = (show: boolean) => {
    if (!modal) return
    modal.classList.toggle('hidden', !show)
  }

  btnMultiplayer?.addEventListener('click', () => showModal(true))
  btnCloseModal?.addEventListener('click', () => showModal(false))
  modal?.addEventListener('click', (e) => {
    if (e.target === modal) showModal(false)
  })

  btnHost?.addEventListener('click', async () => {
    const offer = await net.createOffer()
    if (outOffer) outOffer.value = offer
  })
  btnJoin?.addEventListener('click', async () => {
    const offer = inOffer?.value?.trim()
    if (!offer) return
    const answer = await net.acceptOfferCreateAnswer(offer)
    if (outAnswer) outAnswer.value = answer
  })
  btnSetAnswer?.addEventListener('click', async () => {
    const ans = inAnswer?.value?.trim()
    if (!ans) return
    await net.acceptAnswer(ans)
  })

  const resize = () => {
    const w = window.innerWidth
    const h = window.innerHeight
    renderer.setSize(w, h, false)
    camera.aspect = w / h
    camera.updateProjectionMatrix()
  }
  window.addEventListener('resize', resize)
  resize()

  // Race state
  const race = {
    finished: false,
    message: '' as '' | 'You win!' | 'You lose!',
  }

  const messageEl = document.createElement('div')
  messageEl.style.position = 'fixed'
  messageEl.style.inset = '0'
  messageEl.style.display = 'grid'
  messageEl.style.placeItems = 'center'
  messageEl.style.pointerEvents = 'none'
  messageEl.style.fontWeight = '950'
  messageEl.style.fontSize = 'min(10vw, 72px)'
  messageEl.style.letterSpacing = '0.02em'
  messageEl.style.textShadow = '0 20px 80px rgba(0,0,0,0.6)'
  messageEl.style.zIndex = '15'
  document.body.appendChild(messageEl)

  // Countdown state: at load 10s, on reset 3s, then brief "Go!"
  let countdownSeconds = 10
  let countdownRemaining = countdownSeconds
  let showGoRemaining = 1.0
  messageEl.textContent = String(countdownSeconds)

  const resetRace = () => {
    race.finished = false
    race.message = ''
    // Shorter countdown on reset
    countdownSeconds = 3
    countdownRemaining = countdownSeconds
    showGoRemaining = 0
    messageEl.textContent = String(countdownSeconds)
    points = 0
    above100Timer = 0
    const startCars = cars.slice()
    for (let idx = 0; idx < startCars.length; idx++) {
      const c = startCars[idx]
      const t = wrap01(spawnT - 0.02 * idx)
      const p = track.curve.getPointAt(t)
      const tan = track.curve.getTangentAt(t).normalize()
      c.pos.copy(p.clone().add(new THREE.Vector3((idx % 2 === 0 ? -1 : 1) * 2.2, 0, 0)))
      c.vel.set(0, 0, 0)
      c.yaw = Math.atan2(tan.x, tan.z)
      c.progress = t
      c.lastProgress = t
      c.lap = 1
      c.finished = false
      setCarTransform(c)
    }
  }

  // Car simulation
  const tmp = new THREE.Vector3()
  const up = new THREE.Vector3(0, 1, 0)
  const simCar = (c: Car, dt: number) => {
    if (c.finished) return

    const speed = Math.hypot(c.vel.x, c.vel.z)
    const f = headingToForward(c.yaw)
    const forward = new THREE.Vector3(f.x, 0, f.z)
    const right = new THREE.Vector3().crossVectors(up, forward).normalize()

    // AI driver
    let steer = 0
    let throttle = 0
    let brake = 0
    let drifting = false
    if (c.id === 'local') {
      steer = input.steer
      throttle = input.throttle
      brake = input.brake
      drifting = input.drift
    } else if (c.id.startsWith('ai-')) {
      const lookAhead = 0.012 + clamp(speed / 90, 0, 1) * 0.03
      const targetT = wrap01(c.progress + lookAhead)
      const targetP = track.curve.getPointAt(targetT)
      tmp.copy(targetP).sub(c.pos)
      const desiredYaw = Math.atan2(tmp.x, tmp.z)
      let dy = desiredYaw - c.yaw
      while (dy > Math.PI) dy -= Math.PI * 2
      while (dy < -Math.PI) dy += Math.PI * 2
      steer = clamp(dy * 1.4, -1, 1)
      // AI: slower so kids have time to chase and overtake
      const targetSpeed = (48 + (Number(c.id.split('-')[1]) || 0) * 2.5) * 0.5
      throttle = speed < targetSpeed ? 1 : 0.2
      brake = speed > targetSpeed + 14 ? 0.6 : 0
      drifting = Math.abs(steer) > 0.55 && speed > 30
    } else {
      // remote cars are driven by the peer state
      return
    }

    // Road constraint (soft)
    const centerT = closestTrackT(track, c.pos)
    const centerP = track.curve.getPointAt(centerT)
    const distToCenter = centerP.distanceTo(c.pos)
    const offRoad = distToCenter > track.width * 0.62

    const accel = 38
    const brakeDecel = 52
    const maxSpeed = 95 // m/s (~212 mph), arcade-y

    // Steering rate scales with speed
    const steerRate = (1.65 + clamp(speed / 70, 0, 1) * 1.05) * steer
    c.yaw += steerRate * dt

    // Forward/back forces
    const drive = throttle * accel - brake * brakeDecel
    c.vel.addScaledVector(forward, drive * dt)

    // Limit speed
    const sp = Math.hypot(c.vel.x, c.vel.z)
    if (sp > maxSpeed) {
      c.vel.multiplyScalar(maxSpeed / sp)
    }

    // Drift/grip model: damp lateral speed more when not drifting
    const lateral = c.vel.dot(right)
    const longi = c.vel.dot(forward)
    const baseGrip = offRoad ? 2.0 : 6.5
    const driftGrip = offRoad ? 1.1 : 2.4
    const grip = drifting ? driftGrip : baseGrip

    const latTarget = drifting ? lateral * 0.92 : 0
    const newLat = damp(lateral, latTarget, grip, dt)
    // keep forward component, adjust lateral
    c.vel.copy(forward.clone().multiplyScalar(longi).add(right.multiplyScalar(newLat)))

    // Drag
    const drag = offRoad ? 0.985 : 0.992
    c.vel.multiplyScalar(Math.pow(drag, dt * 60))

    // Soft “spring” back to road center if far out (keeps kids on track)
    if (distToCenter > track.width * 0.85) {
      const pull = clamp((distToCenter - track.width * 0.85) / (track.width * 1.8), 0, 1)
      const dir = centerP.clone().sub(c.pos).setY(0).normalize()
      c.vel.addScaledVector(dir, 26 * pull * dt)
    }

    c.pos.addScaledVector(c.vel, dt)
    c.pos.y = 0
    setCarTransform(c)

    // Progress + laps
    const newT = closestTrackT(track, c.pos)
    c.progress = newT
    if (c.lastProgress > 0.85 && newT < 0.15) {
      c.lap += 1
    }
    c.lastProgress = newT

    // Finish check: require multiple laps before the finish counts
    const lapsToWin = 5
    const nearFinish = Math.abs(wrap01(newT - track.finishT)) < 0.012
    if (c.lap - 1 >= lapsToWin && nearFinish) {
      c.finished = true
    }
  }

  const updateCamera = (dt: number) => {
    const speed = Math.hypot(player.vel.x, player.vel.z)
    const f = headingToForward(player.yaw)
    const forward = new THREE.Vector3(f.x, 0, f.z)
    const camBack = 12 + clamp(speed / 12, 0, 1) * 8
    const camUp = 7 + clamp(speed / 18, 0, 1) * 4
    const targetPos = player.pos.clone().addScaledVector(forward, -camBack).add(new THREE.Vector3(0, camUp, 0))
    camera.position.lerp(targetPos, 1 - Math.exp(-6 * dt))
    const lookAt = player.pos.clone().addScaledVector(forward, 8).add(new THREE.Vector3(0, 2.2, 0))
    camera.lookAt(lookAt)
  }

  const computePlaces = () => {
    const total = cars.length
    const scores = cars.map((c) => {
      const prog = (c.lap - 1) + c.progress
      return { id: c.id, prog, finished: c.finished }
    })
    scores.sort((a, b) => {
      if (a.finished !== b.finished) return a.finished ? -1 : 1
      return b.prog - a.prog
    })
    const place = scores.findIndex((s) => s.id === 'local') + 1
    return { place, total }
  }

  const maybeEndRace = () => {
    if (race.finished) return
    const someoneFinished = cars.some((c) => c.finished)
    if (!someoneFinished) return
    const { place } = computePlaces()
    if (player.finished) {
      race.finished = true
      race.message = place === 1 ? 'You win!' : 'You lose!'
      messageEl.textContent = race.message
    } else {
      // if somebody else finished first, you lose
      const { place: p } = computePlaces()
      const topIsNotYou = p !== 1 && cars.some((c) => c.finished)
      if (topIsNotYou) {
        race.finished = true
        race.message = 'You lose!'
        messageEl.textContent = race.message
      }
    }
  }

  let last = performance.now()
  const tick = (now: number) => {
    const dt = clamp((now - last) / 1000, 0, 0.05)
    last = now

    pollInput()
    if (input.reset) resetRace()

    // Countdown handling: freeze cars until countdown done
    if (countdownRemaining > 0) {
      countdownRemaining -= dt
      const shown = Math.max(0, Math.ceil(countdownRemaining))
      messageEl.textContent = String(shown)
    } else if (showGoRemaining > 0) {
      showGoRemaining -= dt
      messageEl.textContent = 'Go!'
    } else if (!race.finished && messageEl.textContent && (race.message === '' || messageEl.textContent === 'Go!')) {
      // Clear countdown / "Go!" once active racing starts (leave win/lose text)
      messageEl.textContent = ''
    }

    const racingActive = countdownRemaining <= 0 && showGoRemaining <= 0

    // Simulate only while race is active
    if (racingActive) {
      for (const c of cars) simCar(c, dt)
    }

    // Smooth remote car a bit (when peer sends sparse updates)
    if (remote) {
      const age = (performance.now() - remote.lastStateAt) / 1000
      if (age < 0.25) {
        remote.pos.addScaledVector(remote.vel, dt * 0.9)
        setCarTransform(remote)
      }
    }

    updateCamera(dt)
    renderer.render(scene, camera)

    // HUD updates
    const mph = mphFromMps(Math.hypot(player.vel.x, player.vel.z))
    if (elSpeed) elSpeed.textContent = String(Math.round(mph))
    if (elPoints) elPoints.textContent = String(points)
    if (elLap) elLap.textContent = String(player.lap)
    const { place, total } = computePlaces()
    if (elPlace) elPlace.textContent = String(place)
    if (elTotal) elTotal.textContent = String(total)
    if (elNet) elNet.textContent = net.connectionLabel()

    // Points: +5 each second while >100 mph
    if (mph > 100) {
      above100Timer += dt
      while (above100Timer >= 1) {
        above100Timer -= 1
        points += 5
      }
    } else {
      above100Timer = 0
    }

    // Send local state to peer
    if (net.isConnected()) {
      const s: Omit<NetPeerState, 'id' | 'name' | 'color'> = {
        x: player.pos.x,
        y: player.pos.y,
        z: player.pos.z,
        vx: player.vel.x,
        vz: player.vel.z,
        yaw: player.yaw,
        progress: player.progress,
        lap: player.lap,
        finished: player.finished,
        t: now,
      }
      net.sendState(s)
    }

    maybeEndRace()
    requestAnimationFrame(tick)
  }

  requestAnimationFrame(tick)
}

