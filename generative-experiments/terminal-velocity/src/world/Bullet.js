
import * as THREE from 'three';
export class Bullet {
  constructor(camera) {
    this.speed = 240; this.life = 1.2;
    const geom = new THREE.SphereGeometry(0.25, 8, 8);
    const mat = new THREE.MeshBasicMaterial({ color: 0x69e1ff });
    this.mesh = new THREE.Mesh(geom, mat);
    this.mesh.position.copy(camera.position);
    const forward = new THREE.Vector3(0,0,-1).applyQuaternion(camera.quaternion);
    this.dir = forward.clone().normalize();
    this.mesh.position.addScaledVector(forward, 1.5);
  }
  update(dt) { this.life -= dt; if (this.life <= 0) return; this.mesh.position.addScaledVector(this.dir, this.speed * dt); }
}
