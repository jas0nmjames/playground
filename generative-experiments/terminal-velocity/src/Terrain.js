import * as THREE from 'three';
import { makeNoise2D } from './utils/Noise.js';

/**
 * Infinite scrolling terrain made of a 2D grid of tiles that are repositioned forward.
 * Each tile's vertices are displaced via 2D noise, sampled with a world offset to create continuity.
 */
export class Terrain {
  constructor() {
    this.group = new THREE.Group();
    this.group.position.set(0, 0, -50);

    this.tileSize = 80;
    this.res = 32;         // segments per tile edge
    this.grid = 5;         // 5x5 tiles
    this.speedFactor = 1;  // scaled by player speed
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

    // Simple fog to blend horizon
    this.fog = new THREE.FogExp2(0x02121f, 0.0026);
    this.group.fog = this.fog; // not used by default, but kept for reference
  }

  createTile(gx, gz) {
    const size = this.tileSize;
    const res = this.res;

    const geom = new THREE.PlaneGeometry(size, size, res, res);
    geom.rotateX(-Math.PI / 2);

    const mat = new THREE.MeshStandardMaterial({
      color: 0x0a3b4e,
      roughness: 0.95,
      metalness: 0.0,
      flatShading: true,
    });

    const mesh = new THREE.Mesh(geom, mat);
    mesh.position.set(gx * size, 0, gz * size);
    mesh.receiveShadow = true;

    return { mesh, gx, gz, geom };
  }

  sampleHeight(x, z) {
    // Scale down inputs for smoother noise
    const n = this.noise(x * 0.02, (z + this.worldZ) * 0.02);
    // Shift into [0..1], then scale
    return (n * 0.5 + 0.5) * 8.0; // up to ~8 units high
  }

  updateTileHeights(tile) {
    const pos = tile.geom.attributes.position;
    const size = this.tileSize;
    for (let i = 0; i < pos.count; i++) {
      // vertex local position
      const vx = pos.getX(i);
      const vz = pos.getZ(i);
      const worldX = vx + tile.mesh.position.x;
      const worldZ = vz + tile.mesh.position.z;
      const h = this.sampleHeight(worldX, worldZ);
      pos.setY(i, h);
    }
    pos.needsUpdate = true;
    tile.geom.computeVertexNormals();
  }

  update(dt, player) {
    if (!player) return;
    const move = player.speed * dt * this.speedFactor;
    this.worldZ += move;

    // Move tiles backward (toward +Z in camera space), then wrap forward
    for (const t of this.tiles) {
      t.mesh.position.z += move;

      // If tile passed behind camera, wrap it far ahead and refresh heights
      if (t.mesh.position.z - this.group.position.z > this.tileSize * (Math.floor(this.grid / 2))) {
        t.mesh.position.z -= this.tileSize * this.grid;
      }
      this.updateTileHeights(t);
    }
  }
}
