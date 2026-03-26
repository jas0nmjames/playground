
import * as THREE from 'three';
import { Projectile } from './Projectile.js';

export class Turret {
  constructor(x, z, getHeightFn) {
    this.getHeight = getHeightFn;
    const base = new THREE.CylinderGeometry(1.8, 2.2, 4, 12);
    const head = new THREE.SphereGeometry(1.2, 12, 10);
    const baseMat = new THREE.MeshStandardMaterial({ color: 0x575b65, roughness: 0.9, metalness: 0.05, flatShading: true });
    const headMat = new THREE.MeshStandardMaterial({ color: 0x7b828f, roughness: 0.7, metalness: 0.1, flatShading: true });
    this.mesh = new THREE.Group();
    this.baseMesh = new THREE.Mesh(base, baseMat);
    this.headMesh = new THREE.Mesh(head, headMat);
    this.baseMesh.position.y = 2; this.headMesh.position.y = 4.2;
    this.mesh.add(this.baseMesh); this.mesh.add(this.headMesh);
    this.mesh.position.set(x, 0, z);
    this.health = 100; this.cooldown = 0; this.range = 450;
  }
  placeOnTerrain() { const y = this.getHeight(this.mesh.position.x, this.mesh.position.z); this.mesh.position.y = y; }
  update(dt, player, fireCb) {
    if (this.health <= 0) return;
    this.placeOnTerrain();
    this.headMesh.lookAt(player.camera.position);
    this.cooldown -= dt;
    const toPlayer = new THREE.Vector3().subVectors(player.camera.position, this.mesh.position);
    if (toPlayer.length() < this.range && this.cooldown <= 0) {
      this.cooldown = 1.2 + Math.random() * 0.6;
      const dir = toPlayer.normalize(); const muzzle = this.headMesh.getWorldPosition(new THREE.Vector3()).addScaledVector(dir, 1.6);
      fireCb(new Projectile(muzzle, dir));
    }
  }
}
