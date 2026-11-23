import * as THREE from 'three';
import gsap from 'gsap';
import type { World } from './World';
import { IS_MOBILE } from './World';

/** First-person 'stand on your balcony' camera: drag to look around, wheel/pinch to change FOV. */
export class BalconyView {
  active = false;
  private yaw = 0; private pitch = 0; private tYaw = 0; private tPitch = 0;
  private baseYaw = 0;
  private fov = 62; private tFov = 62;
  private saved?: { pos: THREE.Vector3; target: THREE.Vector3; fov: number };
  private drag?: { x: number; y: number; yaw: number; pitch: number };
  private pinch?: number;
  onHeading?: (deg: number) => void;

  constructor(private world: World) {
    const c = world.canvas;
    c.addEventListener('pointerdown', (e) => {
      if (!this.active) return;
      this.drag = { x: e.clientX, y: e.clientY, yaw: this.tYaw, pitch: this.tPitch };
      c.setPointerCapture(e.pointerId);
    });
    c.addEventListener('pointermove', (e) => {
      if (!this.active || !this.drag) return;
      const k = (this.fov / 62) * (IS_MOBILE ? 0.0055 : 0.0035);
      this.tYaw = THREE.MathUtils.clamp(this.drag.yaw - (e.clientX - this.drag.x) * k, -1.9, 1.9);
      this.tPitch = THREE.MathUtils.clamp(this.drag.pitch + (e.clientY - this.drag.y) * k, -0.75, 0.45);
    });
    const end = () => { this.drag = undefined; };
    c.addEventListener('pointerup', end);
    c.addEventListener('pointercancel', end);
    c.addEventListener('wheel', (e) => {
      if (!this.active) return;
      e.preventDefault();
      this.tFov = THREE.MathUtils.clamp(this.tFov + e.deltaY * 0.03, 28, 80);
    }, { passive: false });
    c.addEventListener('touchmove', (e) => {
      if (!this.active || e.touches.length !== 2) return;
      const d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
      if (this.pinch) this.tFov = THREE.MathUtils.clamp(this.tFov - (d - this.pinch) * 0.08, 28, 80);
      this.pinch = d;
    }, { passive: true });
    c.addEventListener('touchend', () => (this.pinch = undefined));
    world.onTick(() => this.update());
  }

  async enter(pos: THREE.Vector3, look: THREE.Vector3) {
    const w = this.world;
    if (!this.active) this.saved = { pos: w.camera.position.clone(), target: w.controls.target.clone(), fov: w.camera.fov };
    w.controls.enabled = false;
    const d = look.clone().sub(pos);
    this.baseYaw = Math.atan2(d.x, -d.z); // 0 = north
    this.yaw = this.tYaw = 0;
    this.pitch = this.tPitch = Math.atan2(-d.y, Math.hypot(d.x, d.z)) * -1;
    this.tFov = this.fov = IS_MOBILE ? 70 : 62;
    // cinematic approach: from outside, glide into the balcony
    const approach = pos.clone().add(new THREE.Vector3(Math.sin(this.baseYaw), 0.4, -Math.cos(this.baseYaw)).multiplyScalar(22));
    w.camera.position.copy(approach);
    w.camera.lookAt(pos);
    this.active = false;
    await new Promise<void>((res) => {
      const p = { t: 0 };
      const from = approach.clone();
      const qFrom = w.camera.quaternion.clone();
      gsap.to(p, {
        t: 1, duration: 2.2, ease: 'power2.inOut',
        onUpdate: () => {
          w.camera.position.lerpVectors(from, pos, p.t);
          const q = this.quat(this.baseYaw, this.pitch);
          w.camera.quaternion.slerpQuaternions(qFrom, q, Math.min(1, p.t * 1.3));
        },
        onComplete: () => res(),
      });
    });
    this.active = true;
  }

  exit() {
    this.active = false;
    const w = this.world;
    w.camera.fov = this.saved?.fov ?? w.camera.fov;
    w.camera.updateProjectionMatrix();
    w.controls.enabled = true;
    if (this.saved) w.flyTo(this.saved.pos, this.saved.target, 1.6);
  }

  private quat(yaw: number, pitch: number) {
    const e = new THREE.Euler(pitch, -yaw, 0, 'YXZ');
    return new THREE.Quaternion().setFromEuler(e);
  }

  private update() {
    if (!this.active) return;
    this.yaw += (this.tYaw - this.yaw) * 0.12;
    this.pitch += (this.tPitch - this.pitch) * 0.12;
    this.fov += (this.tFov - this.fov) * 0.12;
    const cam = this.world.camera;
    cam.quaternion.copy(this.quat(this.baseYaw + this.yaw, this.pitch));
    if (Math.abs(cam.fov - this.fov) > 0.01) { cam.fov = this.fov; cam.updateProjectionMatrix(); }
    this.onHeading?.((THREE.MathUtils.radToDeg(this.baseYaw + this.yaw) + 360) % 360);
  }
}
