import * as THREE from 'three';

export class Player {
  constructor(camera) {
    this.camera = camera;
    this.reset();
  }

  reset() {
    this.speed = 80;         // base forward speed
    this.maxSpeed = 180;
    this.minSpeed = 40;
    this.accel = 90;
    this.turnSpeed = 0.0025; // mouse look sensitivity handled by PointerLock
    this.health = 100;
    this.camera.position.set(0, 22, 0);
    this.pitch = 0; // manage pitch clamp independently
  }

  damage(n) { this.health = Math.max(0, this.health - n); }

  update(dt, input, controls) {
    // Forward push (always moving forward along -Z in camera space)
    const boost = input.down('ShiftLeft') || input.down('ShiftRight') ? 1 : 0;
    const targetSpeed = this.speed + boost * 50;
    this.speed += (targetSpeed - this.speed) * Math.min(1, dt * 5);

    // Strafe (A/D)
    const strafe = (input.down('KeyD') ? 1 : 0) - (input.down('KeyA') ? 1 : 0);
    // Pitch (W/S) — clamp pitch to avoid flipping
    const pitchInput = (input.down('KeyS') ? 1 : 0) - (input.down('KeyW') ? 1 : 0);
    this.pitch = THREE.MathUtils.clamp(this.pitch + pitchInput * dt * 0.8, -0.5, 0.5);

    // Apply pitch to camera
    if (controls.isLocked) {
      const euler = new THREE.Euler().setFromQuaternion(this.camera.quaternion, 'YXZ');
      euler.x = THREE.MathUtils.lerp(euler.x, this.pitch, 0.15);
      this.camera.quaternion.setFromEuler(euler);
    }

    // Move in camera space
    const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(this.camera.quaternion);
    const right   = new THREE.Vector3(1, 0,  0).applyQuaternion(this.camera.quaternion);
    const up      = new THREE.Vector3(0, 1,  0);

    // Maintain a low altitude range
    let nextPos = this.camera.position.clone();
    nextPos.addScaledVector(forward, this.speed * dt);
    nextPos.addScaledVector(right,   strafe * 35 * dt);
    // Vertical drift tied to pitch
    nextPos.addScaledVector(up, this.pitch * 15 * dt);

    nextPos.y = THREE.MathUtils.clamp(nextPos.y, 10, 60);
    this.camera.position.copy(nextPos);
  }
}
