import * as THREE from 'three';
import gsap from 'gsap';
import type { World } from './World';
import { IS_MOBILE } from './World';

/**
 * Real-photo balcony viewer: a stitched site panorama (or single photo) wrapped on the inside of a
 * cylinder at its true angular width, so the buyer can drag / swipe / pinch — or move the phone — to look around.
 */
export class RealView {
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(IS_MOBILE ? 64 : 55, innerWidth / innerHeight, 0.1, 100);
  active = false;
  private mesh?: THREE.Mesh;
  private span = 1.6; private vspan = 0.9; private full = false;
  private yaw = 0; private pitch = 0; private tYaw = 0; private tPitch = 0; private fov = 55; private tFov = 55;
  private drag?: { x: number; y: number; yaw: number; pitch: number };
  private pinch?: number;
  private loader = new THREE.TextureLoader();
  private gyro?: { a0: number; b0: number; yaw0: number; pitch0: number };
  onLoad?: (ok: boolean) => void;

  constructor(private world: World) {
    this.scene.background = new THREE.Color(0x0b0f14);
    const c = world.canvas;
    c.addEventListener('pointerdown', (e) => { if (this.active) { this.drag = { x: e.clientX, y: e.clientY, yaw: this.tYaw, pitch: this.tPitch }; c.setPointerCapture(e.pointerId); } });
    c.addEventListener('pointermove', (e) => {
      if (!this.active || !this.drag) return;
      const k = THREE.MathUtils.degToRad(this.fov) / innerHeight;
      this.tYaw = this.drag.yaw - (e.clientX - this.drag.x) * k;
      this.tPitch = this.drag.pitch + (e.clientY - this.drag.y) * k;
      this.clamp();
    });
    const up = () => (this.drag = undefined);
    c.addEventListener('pointerup', up); c.addEventListener('pointercancel', up);
    c.addEventListener('wheel', (e) => { if (!this.active) return; e.preventDefault(); this.tFov = THREE.MathUtils.clamp(this.tFov + e.deltaY * 0.03, 22, this.maxFov()); this.clamp(); }, { passive: false });
    c.addEventListener('touchmove', (e) => {
      if (!this.active || e.touches.length !== 2) return;
      const d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
      if (this.pinch) { this.tFov = THREE.MathUtils.clamp(this.tFov - (d - this.pinch) * 0.08, 22, this.maxFov()); this.clamp(); }
      this.pinch = d;
    }, { passive: true });
    c.addEventListener('touchend', () => (this.pinch = undefined));
    world.onTick(() => this.update());
  }

  private maxFov() { return this.full ? (IS_MOBILE ? 90 : 85) : Math.min(IS_MOBILE ? 78 : 70, THREE.MathUtils.radToDeg(this.vspan) * 0.98); }

  private clamp() {
    const hf = THREE.MathUtils.degToRad(this.tFov) / 2;
    const hfh = Math.atan(Math.tan(hf) * this.camera.aspect);
    const ylim = Math.max(0, this.span / 2 - hfh), plim = Math.max(0, this.vspan / 2 - hf);
    if (this.full) { this.tPitch = THREE.MathUtils.clamp(this.tPitch, -Math.PI / 2 + 0.02, Math.PI / 2 - 0.02); return; }
    this.tYaw = THREE.MathUtils.clamp(this.tYaw, -ylim, ylim);
    this.tPitch = THREE.MathUtils.clamp(this.tPitch, -plim, plim);
  }

  async open(src: string, kind: 'pano' | 'photo' | 'sphere') {
    this.full = kind === 'sphere';
    this.active = true;
    this.world.controls.enabled = false;
    this.world.overrideScene = { scene: this.scene, camera: this.camera };
    this.world.overrideResize = (w, h) => { this.camera.aspect = w / h; this.camera.updateProjectionMatrix(); this.clamp(); };
    this.camera.aspect = innerWidth / innerHeight;
    const tex = await new Promise<THREE.Texture | null>((res) => this.loader.load(src, res, undefined, () => res(null)));
    if (!tex || !this.active) { this.onLoad?.(false); return; }
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    if (this.full) return this.openSphere(tex);
    const img = tex.image as HTMLImageElement;
    const aspect = img.width / img.height;
    // angular size: phone main camera ≈ 42° vertical for clips, ≈ 64° for portrait photos
    const vdeg = kind === 'pano' ? 46 : aspect < 1 ? 70 : 52;
    const hdeg = THREE.MathUtils.clamp(vdeg * aspect, 50, 300);
    this.span = THREE.MathUtils.degToRad(hdeg);
    const R = 10;
    const H = (R * this.span) / aspect;
    this.vspan = 2 * Math.atan(H / 2 / R);
    if (this.mesh) { this.scene.remove(this.mesh); this.mesh.geometry.dispose(); ((this.mesh.material as THREE.MeshBasicMaterial).map)?.dispose(); }
    const g = new THREE.CylinderGeometry(R, R, H, 96, 1, true, Math.PI - this.span / 2, this.span);
    g.scale(-1, 1, 1);
    this.mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: tex, side: THREE.FrontSide, toneMapped: false }));
    this.scene.add(this.mesh);
    this.tFov = this.fov = Math.min(IS_MOBILE ? 72 : 58, this.maxFov());
    this.yaw = this.tYaw = 0; this.pitch = this.tPitch = 0;
    this.clamp();
    // start looking slightly down, towards the ground detail rather than the sky
    const plim0 = Math.max(0, this.vspan / 2 - THREE.MathUtils.degToRad(this.tFov) / 2);
    this.pitch = this.tPitch = -plim0 * 0.55;
    this.camera.fov = this.fov; this.camera.updateProjectionMatrix();
    // gentle intro sweep so people discover they can look around
    const ylim = Math.max(0, this.span / 2 - Math.atan(Math.tan(THREE.MathUtils.degToRad(this.fov) / 2) * this.camera.aspect));
    if (ylim > 0.1) { this.tYaw = -ylim * 0.6; gsap.delayedCall(1.4, () => { if (this.active && !this.drag) this.tYaw = 0; }); }
    this.onLoad?.(true);
  }

  /** true 360°: an equirectangular image on the inside of a sphere — look anywhere, up and down included */
  private openSphere(tex: THREE.Texture) {
    tex.generateMipmaps = true;
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    if (this.mesh) { this.scene.remove(this.mesh); this.mesh.geometry.dispose(); ((this.mesh.material as THREE.MeshBasicMaterial).map)?.dispose(); }
    const g = new THREE.SphereGeometry(10, 96, 64);
    g.scale(-1, 1, 1);
    this.mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
    this.mesh.rotation.y = -Math.PI / 2;          // image centre = straight out from the balcony
    this.scene.add(this.mesh);
    this.span = Math.PI * 2; this.vspan = Math.PI;
    this.tFov = this.fov = IS_MOBILE ? 80 : 70;
    this.camera.fov = this.fov; this.camera.updateProjectionMatrix();
    this.yaw = this.tYaw = -0.5; this.pitch = this.tPitch = -0.12;
    // slow reveal sweep across the real view so people discover they can look around
    gsap.delayedCall(0.6, () => { if (this.active && !this.drag) this.tYaw = 0.35; });
    gsap.delayedCall(2.4, () => { if (this.active && !this.drag) this.tYaw = 0; });
    this.onLoad?.(true);
  }

  async enableGyro() {
    const D = DeviceOrientationEvent as unknown as { requestPermission?: () => Promise<string> };
    if (D.requestPermission) { try { if ((await D.requestPermission()) !== 'granted') return false; } catch { return false; } }
    addEventListener('deviceorientation', this.onOrient);
    return true;
  }
  private onOrient = (e: DeviceOrientationEvent) => {
    if (!this.active || e.alpha == null || e.beta == null) return;
    if (!this.gyro) this.gyro = { a0: e.alpha, b0: e.beta, yaw0: this.tYaw, pitch0: this.tPitch };
    let da = e.alpha - this.gyro.a0; if (da > 180) da -= 360; if (da < -180) da += 360;
    this.tYaw = this.gyro.yaw0 - THREE.MathUtils.degToRad(da);
    this.tPitch = this.gyro.pitch0 + THREE.MathUtils.degToRad(e.beta - this.gyro.b0) * 0.8;
    this.clamp();
  };

  close() {
    this.active = false;
    this.gyro = undefined;
    removeEventListener('deviceorientation', this.onOrient);
    this.world.overrideScene = undefined;
    this.world.overrideResize = undefined;
  }

  private update() {
    if (!this.active) return;
    this.yaw += (this.tYaw - this.yaw) * 0.12;
    this.pitch += (this.tPitch - this.pitch) * 0.12;
    this.fov += (this.tFov - this.fov) * 0.12;
    this.camera.quaternion.setFromEuler(new THREE.Euler(this.pitch, -this.yaw, 0, 'YXZ'));
    if (Math.abs(this.camera.fov - this.fov) > 0.01) { this.camera.fov = this.fov; this.camera.updateProjectionMatrix(); }
  }
}
