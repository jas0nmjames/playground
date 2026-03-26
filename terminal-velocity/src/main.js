
import * as THREE from 'three';
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { Sky } from 'three/examples/jsm/objects/Sky.js';

import { Input } from './systems/Input.js';
import { Player } from './systems/Player.js';
import { Terrain } from './world/Terrain.js';
import { Enemy } from './world/Enemy.js';
import { Bullet } from './world/Bullet.js';

const root = document.getElementById('game');

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
root.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x89c6ff);
scene.fog = new THREE.Fog(0x89c6ff, 600, 2800);
const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 8000);

const sky = new Sky();
sky.scale.setScalar(8000);
scene.add(sky);
const U = sky.material.uniforms;
U['turbidity'].value = 10;
U['rayleigh'].value = 2;
U['mieCoefficient'].value = 0.004;
U['mieDirectionalG'].value = 0.8;
U['sunPosition'].value.copy(new THREE.Vector3().setFromSphericalCoords(1, THREE.MathUtils.degToRad(80), THREE.MathUtils.degToRad(12)));

scene.add(new THREE.HemisphereLight(0xcfe9ff, 0x405060, 0.9));
const dir = new THREE.DirectionalLight(0xffffff, 0.9);
dir.position.set(100, 200, -150);
scene.add(dir);

const controls = new PointerLockControls(camera, renderer.domElement);
renderer.domElement.addEventListener('click', () => { if (!controls.isLocked) controls.lock(); else tryFire(); });
controls.addEventListener('lock', () => setMessage(''));
controls.addEventListener('unlock', () => setMessage('Click to start · WASD · Mouse look · Space/Click fire · Shift afterburner · P pause'));

const input = new Input();
const player = new Player(camera);
const terrain = new Terrain(renderer);
scene.add(terrain.group);

const bullets = [];
const projectiles = [];
const enemies = [];
let enemyTimer = 0;
let enemyInterval = 1.0;

const hud = {
  speed: document.getElementById('hudSpeed'),
  alt: document.getElementById('hudAlt'),
  hdg: document.getElementById('hudHdg'),
  ab: document.getElementById('hudAB'),
  health: document.getElementById('hudHealth'),
  score: document.getElementById('hudScore'),
  fps: document.getElementById('hudFps'),
  msg: document.getElementById('hudMessage'),
};
let score = 0;

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), 0.45, 0.8, 0.85);
composer.addPass(bloom);

function handleResize() {
  const w = window.innerWidth, h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  composer.setSize(w, h);
  bloom.setSize(w, h);
}
window.addEventListener('resize', handleResize);

document.addEventListener('keydown', (e) => {
  if (e.code === 'KeyP') togglePause();
  if (e.code === 'Space') { e.preventDefault(); tryFire(); }
});

function setMessage(t) { if (hud.msg) hud.msg.textContent = t; }
let isPaused = false;
function togglePause() { isPaused = !isPaused; setMessage(isPaused ? 'Paused — press P to resume' : ''); }
function tryFire() {
  if (isPaused) return;
  const b = new Bullet(camera);
  scene.add(b.mesh); bullets.push(b);
}

function spawnEnemy() {
  const xRange = 220, yMin = 14, yMax = 54, zAhead = -460;
  const e = new Enemy();
  e.mesh.position.set(THREE.MathUtils.randFloatSpread(xRange), THREE.MathUtils.randFloat(yMin, yMax), camera.position.z + zAhead);
  e.vel.x = THREE.MathUtils.randFloatSpread(9);
  scene.add(e.mesh); enemies.push(e);
}

const clock = new THREE.Clock();
let fpsAcc = 0, fpsFrames = 0, fpsTime = 0;

handleResize();
setMessage('Click to start · WASD · Mouse look · Space/Click fire · Shift afterburner · P pause');
animate();

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  if (isPaused) return;

  fpsAcc += dt; fpsFrames++; fpsTime += dt;
  if (fpsTime >= 0.5) {
    const fps = Math.round(fpsFrames / fpsAcc);
    if (hud.fps) hud.fps.textContent = `FPS ${fps}`;
    fpsTime = fpsAcc = 0; fpsFrames = 0;
  }

  player.update(dt, input, controls);
  if (hud.speed) hud.speed.textContent = `SPD ${player.speed.toFixed(0)}`;
  if (hud.alt) hud.alt.textContent = `ALT ${camera.position.y.toFixed(0)}`;
  if (hud.hdg) {
    const euler = new THREE.Euler().setFromQuaternion(camera.quaternion, 'YXZ');
    let hdg = THREE.MathUtils.radToDeg(euler.y); hdg = (hdg % 360 + 360) % 360;
    hud.hdg.textContent = `HDG ${hdg.toFixed(0)}`;
  }
  if (hud.ab) hud.ab.style.width = `${player.afterburner.toFixed(0)}%`;
  if (hud.health) hud.health.textContent = `HP ${player.health}`;
  if (hud.score) hud.score.textContent = `SCORE ${score}`;

  terrain.update(dt, player);

  enemyTimer += dt;
  if (enemyTimer >= enemyInterval) { enemyTimer = 0; spawnEnemy(); }
  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i];
    e.update(dt, player);
    if (e.mesh.position.z > camera.position.z + 50 || e.health <= 0) {
      scene.remove(e.mesh); enemies.splice(i, 1);
    }
  }

  for (let i = bullets.length - 1; i >= 0; i--) {
    const b = bullets[i];
    b.update(dt);
    if (b.life <= 0) { scene.remove(b.mesh); bullets.splice(i, 1); continue; }

    for (let j = enemies.length - 1; j >= 0; j--) {
      const e = enemies[j];
      if (b.mesh.position.distanceTo(e.mesh.position) < 4.5) {
        e.health -= 34; b.life = 0; if (e.health <= 0) score += 100; break;
      }
    }
    for (let k = terrain.turrets.length - 1; k >= 0; k--) {
      const t = terrain.turrets[k];
      if (b.mesh.position.distanceTo(t.mesh.position) < 5.0) {
        t.health -= 50; b.life = 0; if (t.health <= 0) { scene.remove(t.mesh); terrain.turrets.splice(k,1); score += 150; } break;
      }
    }
  }

  for (let i = terrain.turrets.length - 1; i >= 0; i--) {
    const t = terrain.turrets[i];
    t.update(dt, player, (proj) => { scene.add(proj.mesh); projectiles.push(proj); });
  }
  for (let i = projectiles.length - 1; i >= 0; i--) {
    const p = projectiles[i];
    p.update(dt);
    if (p.life <= 0) { scene.remove(p.mesh); projectiles.splice(i, 1); continue; }
    if (p.mesh.position.distanceTo(camera.position) < 3.5) {
      player.damage(12);
      scene.remove(p.mesh); projectiles.splice(i, 1);
      if (player.health <= 0) {
        isPaused = true;
        setMessage(`GAME OVER — Score ${score}. Click to restart.`);
        renderer.domElement.addEventListener('click', () => location.reload(), { once: true });
        return;
      }
    }
  }

  composer.render();
}
