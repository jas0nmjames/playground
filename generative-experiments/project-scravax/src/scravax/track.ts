import * as THREE from 'three'
import { clamp, wrap01 } from './util'

export type Track = {
  curve: THREE.CatmullRomCurve3
  width: number
  finishT: number
}

export function makeGeorgiaTrack(): Track {
  // A simple “Georgia backroads” loop: wide sweepers + one tight hairpin.
  const pts = [
    new THREE.Vector3(-120, 0, 40),
    new THREE.Vector3(-60, 0, 130),
    new THREE.Vector3(30, 0, 150),
    new THREE.Vector3(120, 0, 80),
    new THREE.Vector3(150, 0, -10),
    new THREE.Vector3(90, 0, -110),
    new THREE.Vector3(-20, 0, -140),
    new THREE.Vector3(-120, 0, -90),
    new THREE.Vector3(-160, 0, -10),
  ]
  const curve = new THREE.CatmullRomCurve3(pts, true, 'catmullrom', 0.45)
  return { curve, width: 18, finishT: 0.02 }
}

export function buildTrackMeshes(track: Track) {
  const group = new THREE.Group()

  const roadMat = new THREE.MeshStandardMaterial({
    color: 0x1a1f2a,
    roughness: 0.95,
    metalness: 0,
  })
  const edgeMat = new THREE.MeshStandardMaterial({
    color: 0xffd25a,
    roughness: 0.75,
    metalness: 0.05,
  })
  const dirtMat = new THREE.MeshStandardMaterial({
    color: 0x8a3b2a, // Georgia “red clay”
    roughness: 1,
    metalness: 0,
  })

  // Road ribbon
  const segs = 260
  const roadGeo = new THREE.BufferGeometry()
  const positions: number[] = []
  const normals: number[] = []
  const uvs: number[] = []
  const indices: number[] = []

  const up = new THREE.Vector3(0, 1, 0)
  for (let i = 0; i <= segs; i++) {
    const t = i / segs
    const p = track.curve.getPointAt(t)
    const tan = track.curve.getTangentAt(t).normalize()
    const right = new THREE.Vector3().crossVectors(up, tan).normalize()
    const leftP = p.clone().addScaledVector(right, -track.width * 0.5)
    const rightP = p.clone().addScaledVector(right, track.width * 0.5)
    positions.push(leftP.x, leftP.y, leftP.z, rightP.x, rightP.y, rightP.z)
    normals.push(0, 1, 0, 0, 1, 0)
    uvs.push(0, t * 8, 1, t * 8)
  }

  for (let i = 0; i < segs; i++) {
    const a = i * 2
    const b = i * 2 + 1
    const c = i * 2 + 2
    const d = i * 2 + 3
    indices.push(a, b, c, b, d, c)
  }

  roadGeo.setIndex(indices)
  roadGeo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  roadGeo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3))
  roadGeo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2))
  roadGeo.computeBoundingSphere()

  const road = new THREE.Mesh(roadGeo, roadMat)
  road.receiveShadow = true
  group.add(road)

  // Dirt ground plane
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(900, 900), dirtMat)
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.02
  ground.receiveShadow = true
  group.add(ground)

  // Finish gate
  const finishP = track.curve.getPointAt(track.finishT)
  const finishTangent = track.curve.getTangentAt(track.finishT).normalize()
  const finishRight = new THREE.Vector3().crossVectors(up, finishTangent).normalize()
  const gateW = track.width * 0.96
  const gateH = 6
  const postGeo = new THREE.BoxGeometry(0.6, gateH, 0.6)
  const barGeo = new THREE.BoxGeometry(gateW, 0.55, 0.55)
  const postMat = new THREE.MeshStandardMaterial({ color: 0xeaf0ff, roughness: 0.35, metalness: 0.2 })

  const postL = new THREE.Mesh(postGeo, postMat)
  postL.position.copy(finishP.clone().addScaledVector(finishRight, -gateW * 0.5))
  postL.position.y = gateH / 2
  const postR = new THREE.Mesh(postGeo, postMat)
  postR.position.copy(finishP.clone().addScaledVector(finishRight, gateW * 0.5))
  postR.position.y = gateH / 2
  const bar = new THREE.Mesh(barGeo, edgeMat)
  bar.position.copy(finishP)
  bar.position.y = gateH - 0.6

  // Orient gate perpendicular to road tangent
  const yaw = Math.atan2(finishTangent.x, finishTangent.z)
  postL.rotation.y = yaw
  postR.rotation.y = yaw
  bar.rotation.y = yaw

  postL.castShadow = true
  postR.castShadow = true
  bar.castShadow = true
  group.add(postL, postR, bar)

  // Some “pines” + “Atlanta-ish” skyline blocks far away
  const treeMat = new THREE.MeshStandardMaterial({ color: 0x183624, roughness: 1 })
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x3b2b1f, roughness: 1 })
  const coneGeo = new THREE.ConeGeometry(3.2, 10, 8)
  const trunkGeo = new THREE.CylinderGeometry(0.6, 0.8, 3.5, 8)
  for (let i = 0; i < 60; i++) {
    const t = Math.random()
    const p = track.curve.getPointAt(t)
    const tan = track.curve.getTangentAt(t).normalize()
    const right = new THREE.Vector3().crossVectors(up, tan).normalize()
    const side = (Math.random() < 0.5 ? -1 : 1) * (track.width * (1 + Math.random() * 2.6))
    const jitter = (Math.random() - 0.5) * 30
    const base = p.clone().addScaledVector(right, side).addScaledVector(tan, jitter)
    base.y = 0
    const trunk = new THREE.Mesh(trunkGeo, trunkMat)
    trunk.position.copy(base)
    trunk.position.y = 1.75
    trunk.castShadow = true
    const crown = new THREE.Mesh(coneGeo, treeMat)
    crown.position.copy(base)
    crown.position.y = 8.2
    crown.castShadow = true
    group.add(trunk, crown)
  }

  const skyline = new THREE.Group()
  const bMat = new THREE.MeshStandardMaterial({ color: 0x1d2b48, roughness: 0.8, metalness: 0.1 })
  for (let i = 0; i < 18; i++) {
    const w = 8 + Math.random() * 18
    const h = 20 + Math.random() * 90
    const d = 8 + Math.random() * 18
    const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), bMat)
    b.position.set(260 + (Math.random() - 0.5) * 80, h / 2, 240 + (Math.random() - 0.5) * 80)
    skyline.add(b)
  }
  group.add(skyline)

  return { group, finishPoint: finishP.clone(), finishYaw: Math.atan2(finishTangent.x, finishTangent.z) }
}

export function closestTrackT(track: Track, pos: THREE.Vector3) {
  // Coarse sample + local refine: fast and “good enough” for ranking.
  const samples = 200
  let bestT = 0
  let bestD2 = Infinity
  const tmp = new THREE.Vector3()
  for (let i = 0; i <= samples; i++) {
    const t = i / samples
    tmp.copy(track.curve.getPointAt(t))
    const d2 = tmp.distanceToSquared(pos)
    if (d2 < bestD2) {
      bestD2 = d2
      bestT = t
    }
  }
  // Refine around bestT
  let t = bestT
  let step = 1 / samples
  for (let k = 0; k < 10; k++) {
    const t1 = wrap01(t - step)
    const t2 = wrap01(t + step)
    const p1 = track.curve.getPointAt(t1)
    const p2 = track.curve.getPointAt(t2)
    const d1 = p1.distanceToSquared(pos)
    const d2 = p2.distanceToSquared(pos)
    if (d1 < bestD2) {
      bestD2 = d1
      t = t1
    } else if (d2 < bestD2) {
      bestD2 = d2
      t = t2
    } else {
      step *= 0.5
    }
  }
  return clamp(t, 0, 1)
}

