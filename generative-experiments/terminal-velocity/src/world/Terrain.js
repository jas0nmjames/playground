import * as THREE from 'three';
import { makeTerrainTriplanarMaterial } from '../materials/TerrainTriplanarMaterial.js';
import { generateGrassTexture, generateRockTexture, generateSnowTexture, generateMacroNoise, generateDetailNoise } from '../utils/TextureGen.js';
import { Turret } from './Turret.js';

const __DUMMY__ = new THREE.Object3D();

export class Terrain {
  constructor(renderer) {
    this.group = new THREE.Group();
    this.group.position.set(0, 0, -50);

    this.tileSize = 90;
    this.res = 64; // higher res per tile
    this.grid = 5;
    this.speedFactor = 1;
    this.worldZ = 0;
    this.seed = Math.random() * 1e9;

    // Textures
    this.grassTex = generateGrassTexture(512);
    this.rockTex  = generateRockTexture(512);
    this.snowTex  = generateSnowTexture(512);
    this.macroTex = generateMacroNoise(512);
    this.detailTex= generateDetailNoise(512);
    const anis = (renderer.capabilities.getMaxAnisotropy ? renderer.capabilities.getMaxAnisotropy() : 8);
    [this.grassTex, this.rockTex, this.snowTex, this.macroTex, this.detailTex].forEach(t => t.anisotropy = anis);

    this.terrainMat = makeTerrainTriplanarMaterial(this.grassTex, this.rockTex, this.snowTex, this.macroTex, this.detailTex);

    this.tiles = [];
    this.turrets = [];
    const half = Math.floor(this.grid / 2);
    for (let gz = -half; gz <= half; gz++) {
      for (let gx = -half; gx <= half; gx++) {
        const tile = this.createTile(gx, gz);
        this.tiles.push(tile);
        this.group.add(tile.mesh);
        this.populateProps(tile, true);
        this.populateClutter(tile);
      }
    }

    // Water plane
    const waterGeo = new THREE.PlaneGeometry(8000, 8000, 1, 1);
    waterGeo.rotateX(-Math.PI/2);
    this.water = new THREE.Mesh(
      waterGeo,
      new THREE.MeshPhysicalMaterial({
        color: 0x2b7cff,
        roughness: 0.45,
        metalness: 0.05,
        transparent: true,
        opacity: 0.6,
        transmission: 0.0
      })
    );
    this.water.position.y = 0.9;
    this.group.add(this.water);

    // Far mountains
    this.mountainRing = this.createMountainRing();
    this.group.add(this.mountainRing);
  }

  // --- noise helpers ---
  noise(x, y) {
    const n = Math.sin(x * 127.1 + y * 311.7 + this.seed) * 43758.5453123;
    return n - Math.floor(n);
  }
  fbm(x, y) {
    let f = 0, amp = 0.5, freq = 1.0;
    for (let i = 0; i < 4; i++) { f += this.noise(x*freq, y*freq) * amp; amp *= 0.5; freq *= 2.0; }
    return f;
  }

  // --- tile creation ---
  createTile(gx, gz) {
    const size = this.tileSize, res = this.res;
    const geom = new THREE.PlaneGeometry(size, size, res, res);
    geom.rotateX(-Math.PI/2);
    const mesh = new THREE.Mesh(geom, this.terrainMat);
    mesh.position.set(gx * size, 0, gz * size);
    const props = new THREE.Group(); mesh.add(props);
    const clutterGroup = new THREE.Group(); mesh.add(clutterGroup);
    return { mesh, gx, gz, geom, props, clutterGroup, clutter: null };
  }

  sampleHeight(x, z) {
    const n1 = this.fbm(x * 0.02, (z + this.worldZ) * 0.02);
    const n2 = this.fbm(x * 0.06, (z + this.worldZ) * 0.06) * 0.35;
    const n = (n1 * 0.7 + n2 * 0.3);
    return (n * 0.5 + 0.5) * 12.0;
  }

  updateTileHeights(tile) {
    const pos = tile.geom.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const vx = pos.getX(i); const vz = pos.getZ(i);
      const worldX = vx + tile.mesh.position.x;
      const worldZ = vz + tile.mesh.position.z;
      const h = this.sampleHeight(worldX, worldZ);
      pos.setY(i, h);
    }
    pos.needsUpdate = true;
    tile.geom.computeVertexNormals();

    // props standing height
    for (const child of tile.props.children) {
      if (child.userData && child.userData.onUpdateHeight) child.userData.onUpdateHeight();
    }

    // clutter instance matrices
    this.updateClutter(tile);
  }

  populateProps(tile, initial=false) {
    // clear existing props
    for (let i = tile.props.children.length - 1; i >= 0; i--) tile.props.remove(tile.props.children[i]);
    const count = Math.floor(Math.random() * 4);
    for (let i = 0; i < count; i++) {
      const lx = THREE.MathUtils.randFloatSpread(this.tileSize * 0.8);
      const lz = THREE.MathUtils.randFloatSpread(this.tileSize * 0.8);
      if (Math.random() < 0.4) {
        const wx = lx + tile.mesh.position.x;
        const wz = lz + tile.mesh.position.z;
        const turret = new Turret(wx, wz, (x,z)=>this.sampleHeight(x,z));
        turret.placeOnTerrain();
        tile.props.add(turret.mesh);
        this.turrets.push(turret);
      } else {
        const h = THREE.MathUtils.randFloat(8, 18);
        const box = new THREE.Mesh(
          new THREE.BoxGeometry(THREE.MathUtils.randFloat(2,4), h, THREE.MathUtils.randFloat(2,4)),
          new THREE.MeshStandardMaterial({ color: 0x808680, roughness: 0.95, flatShading: true })
        );
        box.position.set(lx, 0, lz);
        box.userData.onUpdateHeight = () => {
          const wx = box.position.x + tile.mesh.position.x;
          const wz = box.position.z + tile.mesh.position.z;
          box.position.y = this.sampleHeight(wx, wz) + h * 0.5;
        };
        tile.props.add(box);
      }
    }
  }

  populateClutter(tile) {
    // clear previous clutter meshes and dispose GPU resources
    while (tile.clutterGroup.children.length > 0) {
      const m = tile.clutterGroup.children[0];
      if (m.geometry) m.geometry.dispose();
      if (m.material) {
        if (Array.isArray(m.material)) m.material.forEach(mat => mat && mat.dispose && mat.dispose());
        else if (m.material.dispose) m.material.dispose();
      }
      tile.clutterGroup.remove(m);
    }
    const count = 18 + Math.floor(Math.random()*8);
    const geom = new THREE.DodecahedronGeometry(0.6, 0);
    const mat = new THREE.MeshStandardMaterial({ color: 0x6b6b6b, roughness: 1.0, metalness: 0.0, flatShading: true });
    const inst = new THREE.InstancedMesh(geom, mat, count);
    tile.clutterGroup.add(inst);
    tile.clutter = { inst, count, items: [] };
    for (let i = 0; i < count; i++) {
      const lx = THREE.MathUtils.randFloatSpread(this.tileSize * 0.9);
      const lz = THREE.MathUtils.randFloatSpread(this.tileSize * 0.9);
      const s = THREE.MathUtils.randFloat(0.5, 1.4);
      const ry = Math.random() * Math.PI * 2;
      tile.clutter.items.push({ lx, lz, s, ry });
    }
    this.updateClutter(tile);
  }

  updateClutter(tile) {
    if (!tile.clutter) return;
    const dummy = __DUMMY__;
    for (let i = 0; i < tile.clutter.count; i++) {
      const it = tile.clutter.items[i];
      const wx = it.lx + tile.mesh.position.x;
      const wz = it.lz + tile.mesh.position.z;
      const y = this.sampleHeight(wx, wz) + 0.3;
      dummy.position.set(it.lx, y, it.lz);
      dummy.rotation.set(0, it.ry, 0);
      dummy.scale.set(it.s, it.s, it.s);
      dummy.updateMatrix();
      tile.clutter.inst.setMatrixAt(i, dummy.matrix);
    }
    tile.clutter.inst.instanceMatrix.needsUpdate = true;
  }

  createMountainRing() {
    const g = new THREE.Group();
    const segments = 18, radius = 1200, minH = 120, maxH = 260;
    for (let i = 0; i < segments; i++) {
      const ang = (i / segments) * Math.PI * 2;
      const h = THREE.MathUtils.lerp(minH, maxH, Math.random());
      const r = radius + THREE.MathUtils.randFloatSpread(140);
      const geo = new THREE.ConeGeometry(THREE.MathUtils.randFloat(90, 180), h, 6);
      const mat = new THREE.MeshStandardMaterial({ color: 0x6e6a63, roughness: 0.95, flatShading: true });
      const m = new THREE.Mesh(geo, mat);
      m.position.set(Math.cos(ang) * r, h * 0.5, Math.sin(ang) * r - 1400);
      m.rotation.y = Math.random() * Math.PI;
      g.add(m);
    }
    return g;
  }

  updateMountainRing(camera) {
    const targetZ = camera.position.z - 1400;
    this.mountainRing.position.z = targetZ;
    this.mountainRing.position.x = camera.position.x * 0.3;
  }

  update(dt, player) {
    const move = player.speed * dt * this.speedFactor;
    this.worldZ += move;

    for (const t of this.tiles) {
      t.mesh.position.z += move;
      const limit = this.tileSize * (Math.floor(this.grid / 2));
      if (t.mesh.position.z - this.group.position.z > limit) {
        t.mesh.position.z -= this.tileSize * this.grid;
        this.populateProps(t);
        this.populateClutter(t);
      }
      this.updateTileHeights(t);
    }

    this.water.position.x = player.camera.position.x;
    this.water.position.z = player.camera.position.z - 1600;

    this.updateMountainRing(player.camera);
  }
}
