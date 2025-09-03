import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { Input } from './Input.js';
import { Player } from './Player.js';
import { Terrain } from './Terrain.js';
import { Enemy } from './Enemy.js';
import { Bullet } from './Bullet.js';

export class Game {
  constructor(rootEl) {
    this.rootEl = rootEl;
    this.clock = new THREE.Clock();

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    rootEl.appendChild(this.renderer.domElement);

    // Scene & Camera
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x02121f);
    this.camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 2500);

    // Lighting
    const hemi = new THREE.HemisphereLight(0xaadfff, 0x223344, 0.6);
    this.scene.add(hemi);
    const dir = new THREE.DirectionalLight(0xffffff, 0.9);
    dir.position.set(50, 100, -30);
    this.scene.add(dir);

    // Controls
    this.controls = new PointerLockControls(this.camera, this.renderer.domElement);
    this.renderer.domElement.addEventListener('click', () => {
      if (!this.controls.isLocked) this.controls.lock();
      else this.tryFire();
    });
    this.controls.addEventListener('lock', () => this.setMessage(''));
    this.controls.addEventListener('unlock', () => this.setMessage('Click to start · WASD move · Mouse look · Space/Click fire · Shift boost · P pause'));

    // Systems
    this.input = new Input();
    this.player = new Player(this.camera);
    this.terrain = new Terrain();
    this.scene.add(this.terrain.group);

    // Pools/Entities
    this.bullets = [];
    this.enemies = [];
    this.enemyTimer = 0;
    this.enemyInterval = 1.2; // seconds

    // HUD
    this.hud = {
      speed: document.getElementById('hudSpeed'),
      health: document.getElementById('hudHealth'),
      score: document.getElementById('hudScore'),
      fps: document.getElementById('hudFps'),
      msg: document.getElementById('hudMessage'),
    };

    // State
    this.isPaused = false;
    this.score = 0;
    this.fpsAccumulator = 0; this.fpsFrames = 0; this.fpsTime = 0;

    // Event listeners
    window.addEventListener('resize', () => this.onResize());
    document.addEventListener('keydown', (e) => {
      if (e.code === 'KeyP') this.togglePause();
      if (e.code === 'Space') { e.preventDefault(); this.tryFire(); }
    });

    // Start loop
    this.onResize();
    this.setMessage('Click to start · WASD move · Mouse look · Space/Click fire · Shift boost · P pause');
    this.animate();
  }

  setMessage(text) {
    if (this.hud.msg) this.hud.msg.textContent = text;
  }

  onResize() {
    const w = window.innerWidth, h = window.innerHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  togglePause() {
    this.isPaused = !this.isPaused;
    this.setMessage(this.isPaused ? 'Paused — press P to resume' : '');
  }

  tryFire() {
    if (this.isPaused) return;
    const bullet = new Bullet(this.camera);
    this.scene.add(bullet.mesh);
    this.bullets.push(bullet);
  }

  spawnEnemy() {
    const xRange = 180;
    const yMin = 12, yMax = 50;
    const zAhead = -400; // in front of camera (negative z in our forward direction)
    const e = new Enemy();
    e.mesh.position.set(
      THREE.MathUtils.randFloatSpread(xRange),
      THREE.MathUtils.randFloat(yMin, yMax),
      this.camera.position.z + zAhead
    );
    // Slight lateral motion
    e.vel.x = THREE.MathUtils.randFloatSpread(6);
    this.scene.add(e.mesh);
    this.enemies.push(e);
  }

  // Main loop
  animate() {
    requestAnimationFrame(() => this.animate());
    const dt = Math.min(this.clock.getDelta(), 0.05); // clamp large tab switches
    if (this.isPaused) return;

    // Update FPS (lightweight)
    this.fpsAccumulator += dt; this.fpsFrames += 1;
    this.fpsTime += dt;
    if (this.fpsTime >= 0.5) {
      const fps = Math.round(this.fpsFrames / this.fpsAccumulator);
      if (this.hud.fps) this.hud.fps.textContent = `FPS ${fps}`;
      this.fpsTime = 0; this.fpsFrames = 0; this.fpsAccumulator = 0;
    }

    // Player & input
    this.player.update(dt, this.input, this.controls);
    if (this.hud.speed) this.hud.speed.textContent = `SPD ${this.player.speed.toFixed(0)}`;
    if (this.hud.health) this.hud.health.textContent = `HP ${this.player.health}`;
    if (this.hud.score) this.hud.score.textContent = `SCORE ${this.score}`;

    // World
    this.terrain.update(dt, this.player);

    // Enemies
    this.enemyTimer += dt;
    if (this.enemyTimer >= this.enemyInterval) {
      this.enemyTimer = 0;
      this.spawnEnemy();
    }
    for (let i = this.enemies.length - 1; i >= 0; i--) {
      const e = this.enemies[i];
      e.update(dt, this.player);
      // Cull if far behind
      if (e.mesh.position.z > this.camera.position.z + 50 || e.health <= 0) {
        this.scene.remove(e.mesh); this.enemies.splice(i, 1);
      }
    }

    // Bullets & collisions
    for (let i = this.bullets.length - 1; i >= 0; i--) {
      const b = this.bullets[i];
      b.update(dt);
      if (b.life <= 0) {
        this.scene.remove(b.mesh); this.bullets.splice(i, 1); continue;
      }
      // Bullet-enemy collision (sphere distance check)
      for (let j = this.enemies.length - 1; j >= 0; j--) {
        const e = this.enemies[j];
        const dist = b.mesh.position.distanceTo(e.mesh.position);
        if (dist < 4.5) { // hit radius
          e.health -= 34;
          b.life = 0;
          if (e.health <= 0) {
            this.score += 100;
          }
          break;
        }
      }
    }

    // Enemy-player collision / passing too close
    for (const e of this.enemies) {
      const dist = e.mesh.position.distanceTo(this.camera.position);
      if (dist < 6.0) {
        this.player.damage(10);
        e.health = 0;
        if (this.player.health <= 0) {
          this.gameOver();
          return;
        }
      }
    }

    // Render
    this.renderer.render(this.scene, this.camera);
  }

  gameOver() {
    this.isPaused = true;
    this.setMessage(`GAME OVER — Score ${this.score}. Click to restart.`);
    this.renderer.domElement.addEventListener('click', this.onRestart, { once: true });
  }

  onRestart = () => {
    // Clear entities
    for (const b of this.bullets) this.scene.remove(b.mesh);
    for (const e of this.enemies) this.scene.remove(e.mesh);
    this.bullets.length = 0;
    this.enemies.length = 0;
    this.score = 0;
    this.player.reset();
    this.isPaused = false;
  }
}
