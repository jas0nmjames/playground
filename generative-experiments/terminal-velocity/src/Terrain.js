import * as THREE from 'three';
import { makeNoise2D } from './utils/Noise.js';

/**
 * Infinite scrolling terrain:
 * - Altitude-colored vertices (grass/rock/snow)
 * - Soft fog synced with scene fog for depth cues
 * - Distant low-poly mountain ring that stays ahead of the player
 */
export class Terrain {
  constructor() {
    this.group = new THREE.Group();
    this.group.position.set(0, 0, -50);

    this.tileSize = 90;
    this.res = 40;         // segments per tile edge
    this.grid = 5;         // 5x5 tiles
    this.speedFactor = 1;
    this.noise = makeNoise2D(Math.random() * 1e9);

    this.worldZ = 0;

    this.tiles = [];
    const half = Math.floor(this.grid / 2);
    for (let gz = -half; gz <= half; gz++) {
      for (let gx = -half; gx <= half; gx++) {
        const tile = this.createTile(gx, gz);
        this.tiles.push(tile);
        this.group.add(tile.mesh);
      }
    }

    // Mountain ring for horizon context
    this.mountainRing = this.createMountainRing();
    this.group.add(this.mountainRing);
  }

  createTile(gx, gz) {
    const size = this.tileSize;
    const res = this.res;

    const geom = new THREE.PlaneGeometry(size, size, res, res);
    geom.rotateX(-Math.PI / 2);

    // Enable vertex colors for altitude-based shading
    const mat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.95,
      metalness: 0.0,
      flatShading: true,
    });

    const mesh = new THREE.Mesh(geom, mat);
    mesh.position.set(gx * size, 0, gz * size);
    mesh.receiveShadow = true;

    // Seed color attribute
    const colors = new Float32Array(geom.attributes.position.count * 3);
    geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    return { mesh, gx, gz, geom };
  }

  altitudeToColor(h) {
    // Color stops: water (rare), grass, rock, snow
    // Map height ~[0..12]
    if (h < 1.2) return new THREE.Color(0x2b7cff); // occasional water tint (blue)
    if (h < 4)   return new THREE.Color(0x2e8b57); // sea green grass
    if (h < 7.5) return new THREE.Color(0x6fa35e); // lighter grassy hills
    if (h < 9.5) return new THREE.Color(0x7a6e5a); // rocky
    return new THREE.Color(0xf0f4f7);              // snow cap
  }

  sampleHeight(x, z) {
    // Blend two noise octaves for nicer shapes
    const n1 = this.noise(x * 0.018, (z + this.worldZ) * 0.018);
    const n2 = this.noise(x * 0.06,  (z + this.worldZ) * 0.06) * 0.35;
    const n = (n1 * 0.7 + n2 * 0.3);
    return (n * 0.5 + 0.5) * 12.0; // 0..~12
  }

  updateTileHeights(tile) {
    const pos = tile.geom.attributes.position;
    const col = tile.geom.attributes.color;
    const size = this.tileSize;
    const c = new THREE.Color();

    for (let i = 0; i < pos.count; i++) {
      const vx = pos.getX(i);
      const vz = pos.getZ(i);
      const worldX = vx + tile.mesh.position.x;
      const worldZ = vz + tile.mesh.position.z;
      const h = this.sampleHeight(worldX, worldZ);
      pos.setY(i, h);

      // altitude color
      c.copy(this.altitudeToColor(h));
      col.setXYZ(i, c.r, c.g, c.b);
    }
    pos.needsUpdate = true;
    col.needsUpdate = true;
    tile.geom.computeVertexNormals();
  }

  createMountainRing() {
    const g = new THREE.Group();
    const segments = 16;
    const radius = 1200;
    const minH = 120, maxH = 260;
    for (let i = 0; i < segments; i++) {
      const ang = (i / segments) * Math.PI * 2;
      const h = THREE.MathUtils.lerp(minH, maxH, Math.random());
      const r = radius + THREE.MathUtils.randFloatSpread(120);
      const geo = new THREE.ConeGeometry(THREE.MathUtils.randFloat(80, 160), h, 6);
      const mat = new THREE.MeshStandardMaterial({ color: 0x6e6a63, roughness: 0.95, flatShading: true });
      const m = new THREE.Mesh(geo, mat);
      m.position.set(Math.cos(ang) * r, h * 0.5, Math.sin(ang) * r - 1400); // place far ahead
      m.rotation.y = Math.random() * Math.PI;
      g.add(m);
    }
    return g;
  }

  updateMountainRing(camera) {
    // Keep mountains roughly ahead for a stable horizon anchor
    const targetZ = camera.position.z - 1400;
    this.mountainRing.position.z = targetZ;
    // Center on X to camera for better parallax
    this.mountainRing.position.x = camera.position.x * 0.3;
  }

  update(dt, player) {
    if (!player) return;
    const move = player.speed * dt * this.speedFactor;
    this.worldZ += move;

    // Move tiles backward then wrap
    for (const t of this.tiles) {
      t.mesh.position.z += move;
      if (t.mesh.position.z - this.group.position.z > this.tileSize * (Math.floor(this.grid / 2))) {
        t.mesh.position.z -= this.tileSize * this.grid;
      }
      this.updateTileHeights(t);
    }

    // Mountains
    this.updateMountainRing(player.camera);
  }
}
