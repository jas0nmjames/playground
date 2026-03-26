
import * as THREE from 'three';

export class Player {
  constructor(camera) {
    this.camera = camera;
    this.reset();
  }
  reset() {
    this.speed = 90;
    this.maxSpeed = 220;
    this.minSpeed = 40;
    this.accel = 100;
    this.turnSpeed = 0.0025;
    this.health = 100;
    this.camera.position.set(0, 24, 0);
    this.pitch = 0;
    this.roll = 0;
    this.afterburner = 100;
  }
  damage(n) { this.health = Math.max(0, this.health - n); }
  update(dt, input, controls) {
    const boosting = (input.down('ShiftLeft') || input.down('ShiftRight')) && this.afterburner > 0.5;
    const boostMul = boosting ? 1.9 : 1.0;
    if (boosting) this.afterburner = Math.max(0, this.afterburner - 25 * dt);
    else          this.afterburner = Math.min(100, this.afterburner + 12 * dt);

    const targetSpeed = THREE.MathUtils.clamp(this.speed * boostMul, this.minSpeed, this.maxSpeed);
    this.speed += (targetSpeed - this.speed) * Math.min(1, dt * 2.5);

    const strafe = (input.down('KeyD') ? 1 : 0) - (input.down('KeyA') ? 1 : 0);
    const pitchInput = (input.down('KeyS') ? 1 : 0) - (input.down('KeyW') ? 1 : 0);
    this.pitch = THREE.MathUtils.clamp(this.pitch + pitchInput * dt * 0.8, -0.55, 0.55);

    const targetRoll = THREE.MathUtils.clamp(-strafe * 0.35, -0.45, 0.45);
    this.roll = THREE.MathUtils.lerp(this.roll, targetRoll, 1 - Math.pow(0.0001, dt));

    if (controls.isLocked) {
      const euler = new THREE.Euler().setFromQuaternion(this.camera.quaternion, 'YXZ');
      euler.x = THREE.MathUtils.lerp(euler.x, this.pitch, 0.15);
      const q = new THREE.Quaternion().setFromEuler(euler);
      const rollQ = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1), this.roll);
      q.multiply(rollQ);
      this.camera.quaternion.copy(q);
    }

    const forward = new THREE.Vector3(0,0,-1).applyQuaternion(this.camera.quaternion);
    const right   = new THREE.Vector3(1,0, 0).applyQuaternion(this.camera.quaternion);
    const up      = new THREE.Vector3(0,1, 0);

    let nextPos = this.camera.position.clone();
    nextPos.addScaledVector(forward, this.speed * dt);
    nextPos.addScaledVector(right,   strafe * 35 * dt);
    nextPos.addScaledVector(up, this.pitch * 15 * dt);
    nextPos.y = THREE.MathUtils.clamp(nextPos.y, 8, 80);
    this.camera.position.copy(nextPos);
  }
}
