
import * as THREE from 'three';
const GEOM = new THREE.IcosahedronGeometry(2.2, 0);
export class Enemy {
  constructor() {
    const mat = new THREE.MeshStandardMaterial({ color: 0xff5d5d, metalness: 0.1, roughness: 0.6 });
    this.mesh = new THREE.Mesh(GEOM, mat);
    this.health = 100;
    this.vel = new THREE.Vector3(0, 0, 85);
    this.w = Math.random() * Math.PI * 2;
  }
  update(dt, player) {
    this.w += dt * 2.6;
    this.mesh.position.x += Math.sin(this.w * 1.3) * 2.2 * dt * 10 + this.vel.x * dt;
    this.mesh.position.z += this.vel.z * dt;
    this.mesh.position.y += (player.camera.position.y - this.mesh.position.y) * dt * 0.2;
    this.mesh.lookAt(player.camera.position);
  }
}
