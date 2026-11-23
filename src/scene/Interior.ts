import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import gsap from 'gsap';
import { loader } from './Campus';
import { PLANS } from '../data/project';
import type { World } from './World';
import { IS_MOBILE } from './World';

/** Light-baked furnished dollhouse of a unit type (models baked in Blender Cycles). */
export class Interior {
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(IS_MOBILE ? 48 : 35, innerWidth / innerHeight, 0.05, 200);
  controls: OrbitControls;
  private cache = new Map<string, THREE.Object3D>();
  current?: THREE.Object3D;
  type: 'A' | 'B' | 'C' = 'A';
  labels: { el: HTMLElement; pos: THREE.Vector3; room: string }[] = [];
  active = false;

  constructor(private world: World, private labelLayer: HTMLElement) {
    this.scene.background = new THREE.Color(0xe8e4de);
    const disc = new THREE.Mesh(new THREE.CircleGeometry(30, 64).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: 0xdcd7cf }));
    disc.position.y = -0.33;
    this.scene.add(disc);
    this.controls = new OrbitControls(this.camera, world.canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.07;
    this.controls.maxPolarAngle = Math.PI * 0.47;
    this.controls.minDistance = 2.5;
    this.controls.maxDistance = 90;
    this.controls.enabled = false;
    world.onTick(() => { if (this.active) { this.controls.update(); this.updateLabels(); } });
  }

  async open(type: 'A' | 'B' | 'C', onProgress?: (p: number) => void) {
    this.type = type;
    this.active = true;
    this.world.controls.enabled = false;
    this.controls.enabled = true;
    this.world.overrideScene = { scene: this.scene, camera: this.camera };
    this.world.overrideResize = (w, h) => { this.camera.aspect = w / h; this.camera.updateProjectionMatrix(); };
    this.camera.aspect = innerWidth / innerHeight;
    this.camera.updateProjectionMatrix();
    if (this.current) this.scene.remove(this.current);
    let obj = this.cache.get(type);
    if (!obj) {
      const g = await loader.loadAsync(`/models/interior_${type}.glb`, (e) => e.total && onProgress?.(e.loaded / e.total));
      obj = g.scene;
      obj.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh) return;
        const src = m.material as THREE.MeshStandardMaterial;
        if (src.name === 'glass') {
          m.material = new THREE.MeshPhysicalMaterial({ color: 0xcfe2ea, transparent: true, opacity: 0.22, roughness: 0.05, metalness: 0.1, depthWrite: false });
          m.renderOrder = 2;
        } else {
          const map = src.map;
          if (map) { map.colorSpace = THREE.SRGBColorSpace; map.anisotropy = 8; }
          m.material = new THREE.MeshBasicMaterial({ map, toneMapped: false });
        }
      });
      this.cache.set(type, obj);
    }
    if (!this.active || this.type !== type) return;
    this.current = obj;
    this.scene.add(obj);
    this.buildLabels();
    const box = new THREE.Box3().setFromObject(obj);
    const size = box.getSize(new THREE.Vector3());
    const d = this.fitDist(size);
    this.controls.target.set(0, 0, 0);
    this.camera.position.set(d * 0.55, d * 1.6, d * 0.95);
    gsap.from(this.camera.position, { x: d * 1.2, y: d * 2.6, z: d * 1.6, duration: 1.6, ease: 'power3.out' });
  }

  close() {
    this.active = false;
    this.controls.enabled = false;
    this.world.controls.enabled = true;
    this.world.overrideScene = undefined;
    this.world.overrideResize = undefined;
    this.labelLayer.innerHTML = '';
    this.labels = [];
  }

  private buildLabels() {
    this.labelLayer.innerHTML = '';
    this.labels = [];
    const P = PLANS[this.type];
    const xs = P.rooms.flatMap((r) => [r.r[0], r.r[2]]), ys = P.rooms.flatMap((r) => [r.r[1], r.r[3]]);
    const CX = (Math.min(...xs) + Math.max(...xs)) / 2, CY = (Math.min(...ys) + Math.max(...ys)) / 2;
    for (const r of P.rooms) {
      if (!r.dim) continue;
      const x = ((r.r[0] + r.r[2]) / 2 - CX) * P.mpp, z = ((r.r[1] + r.r[3]) / 2 - CY) * P.mpp;
      const el = document.createElement('button');
      el.className = 'room-label';
      el.innerHTML = `<b>${r.name}</b><span>${r.dim}</span>`;
      el.onclick = () => this.focusRoom(r.id);
      this.labelLayer.appendChild(el);
      this.labels.push({ el, pos: new THREE.Vector3(x, 1.0, z), room: r.id });
    }
  }

  focusRoom(id: string) {
    const l = this.labels.find((x) => x.room === id);
    if (!l) return;
    const t = l.pos.clone().setY(0.4);
    const off = this.camera.position.clone().sub(this.controls.target).normalize().multiplyScalar(IS_MOBILE ? 7 : 5.5);
    gsap.to(this.controls.target, { x: t.x, y: t.y, z: t.z, duration: 1.2, ease: 'power2.inOut' });
    gsap.to(this.camera.position, { x: t.x + off.x, y: Math.max(3.2, t.y + off.y), z: t.z + off.z, duration: 1.2, ease: 'power2.inOut' });
  }

  overview() {
    if (!this.current) return;
    const box = new THREE.Box3().setFromObject(this.current);
    const s = box.getSize(new THREE.Vector3());
    const d = this.fitDist(s);
    gsap.to(this.controls.target, { x: 0, y: 0, z: 0, duration: 1.2 });
    gsap.to(this.camera.position, { x: d * 0.55, y: d * 1.6, z: d * 0.95, duration: 1.2, ease: 'power2.inOut' });
  }

  private fitDist(size: THREE.Vector3) {
    const span = Math.max(size.x, size.z);
    const vf = THREE.MathUtils.degToRad(this.camera.fov) / 2;
    const eff = Math.min(1, this.camera.aspect);
    return (span / (2 * Math.tan(vf) * eff)) * 0.76 * (this.camera.aspect < 1 ? 1.3 : 1);
  }

  private v = new THREE.Vector3();
  private updateLabels() {
    const w = innerWidth, h = innerHeight;
    for (const l of this.labels) {
      this.v.copy(l.pos).project(this.camera);
      const vis = this.v.z < 1;
      l.el.style.transform = `translate(-50%,-50%) translate(${(this.v.x * 0.5 + 0.5) * w}px, ${(-this.v.y * 0.5 + 0.5) * h}px)`;
      l.el.style.opacity = vis ? '1' : '0';
    }
  }
}
