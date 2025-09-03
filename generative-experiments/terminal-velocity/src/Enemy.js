import * as THREE from 'three';

const ENEMY_GEOM = new THREE.IcosahedronGeometry(2.2, 0);

export class Enemy {
  constructor() {
    const mat = new THREE.MeshStandardMaterial({ color: 0xff5d5d, metalness: 0.1, roughness: 0.6 });
    this.mesh = new THREE.Mesh(ENEMY_GEOM, mat);
    this.health = 100;
    this.vel = new THREE.Vector3(0, 0, 65); // moving toward +Z (toward player)
    this.wobbleT = Math.random() * Math.PI * 2;
  }
  update(dt, player) {
    // Move forward with slight sine wobble to feel alive
    this.wobbleT += dt * 2;
    this.mesh.position.x += Math.sin(this.wobbleT * 1.3) * 2.2 * dt * 10 + this.vel.x * dt;
    this.mesh.position.z += this.vel.z * dt;
    // slight altitude adjust toward player's y
    this.mesh.position.y += (player.camera.position.y - this.mesh.position.y) * dt * 0.2;
    // face the player
    this.mesh.lookAt(player.camera.position);
  }
}
