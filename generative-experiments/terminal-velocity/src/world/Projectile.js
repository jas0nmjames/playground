
import * as THREE from 'three';
export class Projectile {
  constructor(origin, dir) {
    this.speed = 120; this.life = 8.0; this.dir = dir.clone().normalize();
    const geo = new THREE.SphereGeometry(0.35, 10, 10);
    const mat = new THREE.MeshBasicMaterial({ color: 0xffd36b });
    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.position.copy(origin);
  }
  update(dt) { this.life -= dt; if (this.life <= 0) return; this.mesh.position.addScaledVector(this.dir, this.speed * dt); }
}
