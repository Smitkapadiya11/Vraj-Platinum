import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { SITE, PROPS, type BlockDef, type FlatDef } from '../data/project';
import { UNITS, type Unit, DIR_VEC } from '../data/units';
import BALCONIES from '../data/balconies.json';
import { sunPosition, istDate } from './sun';

// photo-derived tileable textures (public/tex, built by scripts/make_textures.py); size = metres per tile
const TEX: Record<string, { f: string; m: number; bump?: number }> = {
  plaster: { f: 'white', m: 1.5, bump: 0.6 }, white: { f: 'white', m: 1.5, bump: 0.6 }, wallw: { f: 'white', m: 1.5, bump: 0.6 },
  charcoal: { f: 'charcoal', m: 1.5, bump: 0.9 }, lightgrey: { f: 'lightgrey', m: 1.5, bump: 0.6 },
  wood: { f: 'wood', m: 1.2 }, rust: { f: 'wood', m: 1.2 }, stone: { f: 'stone', m: 1.8 }, bronze: { f: 'bronze', m: 1.5 },
  paver: { f: 'paver', m: 1.6 }, footpath: { f: 'paver', m: 1.2 }, lawn: { f: 'lawn', m: 4 }, asphalt: { f: 'asphalt', m: 6 },
};
const texLoader = new THREE.TextureLoader();
const texCache = new Map<string, THREE.Texture>();
function tex(f: string, m: number, anis: number) {
  const k = f + m;
  if (!texCache.has(k)) {
    const t = texLoader.load(`/tex/${f}.jpg`);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.colorSpace = THREE.SRGBColorSpace;
    t.repeat.set(1 / m, 1 / m);
    t.anisotropy = anis;
    texCache.set(k, t);
  }
  return texCache.get(k)!;
}
import type { World } from './World';

export const loader = new GLTFLoader();
loader.setMeshoptDecoder(MeshoptDecoder);

const GH = SITE.groundH, FH = SITE.floorH, NF = SITE.floors;
// (East, North) metres -> three (x, z)
export const toV = (e: number, n: number, y = 0) => new THREE.Vector3(e, y, -n);
export const STATUS_COLOR = { available: 0x2fbf71, hold: 0xf0a43a, sold: 0xd9534f } as const;

interface FloorStack { block: BlockDef; meshes: THREE.InstancedMesh[]; roof: THREE.Object3D; ghost: THREE.Mesh }

export class Campus {
  root = new THREE.Group();
  stacks: FloorStack[] = [];
  towerPick: THREE.Mesh[] = [];
  unitPick: THREE.Mesh[] = [];
  overlay = new THREE.Group();
  nightUniform = { value: 0 };
  timeUniform = { value: 0 };
  lampLights: THREE.PointLight[] = [];
  private glassMat?: THREE.MeshStandardMaterial;
  carMeshes: THREE.InstancedMesh[] = [];

  constructor(private world: World) {
    this.root.add(this.overlay);
    world.scene.add(this.root);
  }

  async load(onProgress: (p: number) => void) {
    const files = ['towers', 'site', 'props'].map((f) => `/models/${f}.glb?v=${__BUILD__}`);
    const done = [0, 0, 0];
    const gl = await Promise.all(files.map((f, i) => loader.loadAsync(f, (e) => {
      if (e.total) done[i] = e.loaded / e.total;
      onProgress(done.reduce((a, b) => a + b, 0) / files.length);
    })));
    const [towers, site, props] = gl;
    towers.scene.updateMatrixWorld(true);
    site.scene.updateMatrixWorld(true);
    props.scene.updateMatrixWorld(true);
    this.buildSite(site.scene);
    this.buildTowers(towers.scene);
    this.buildProps(props.scene);
    this.buildPickers();
  }

  private tuneMaterial(m: THREE.MeshStandardMaterial) {
    const n = m.name;
    const tx = TEX[n];
    if (tx && !m.map) {
      const anis = Math.min(8, this.world.renderer.capabilities.getMaxAnisotropy());
      m.map = tex(tx.f, tx.m, anis);
      if (tx.bump) { m.bumpMap = m.map; m.bumpScale = tx.bump; }
      m.color.set(tx.f === 'white' ? 0xdcdad5 : tx.f === 'lightgrey' ? 0xe6e6e3 : 0xffffff);
      m.needsUpdate = true;
    }
    if (n === 'glass' || n === 'carglass') {
      m.metalness = 0.85; m.roughness = 0.06; m.envMapIntensity = 1.6;
      if (n === 'glass') this.glassMat = m;
    }
    if (n === 'railglass') { m.transparent = true; m.opacity = 0.3; m.depthWrite = false; m.metalness = 0.4; m.roughness = 0.05; }
    if (n === 'water') { m.metalness = 0.6; m.roughness = 0.03; m.color.set(0x2a6a80); }
    if (n === 'gold') { m.emissiveIntensity = 0; m.userData.nightEmissive = 1.4; }
    if (n === 'lobbyglow' || n === 'lamphead' || n === 'headlight' || n === 'taillight') {
      m.userData.nightEmissive = n === 'lobbyglow' ? 2.2 : n === 'lamphead' ? 4 : 1.5;
      m.emissiveIntensity = 0.05;
    }
    if (n.startsWith('leaf') || n === 'frond' || n.startsWith('canopy') || n.startsWith('hedge') || n === 'lawn' || n === 'lawn2') {
      m.roughness = 0.9; m.envMapIntensity = 0.6;
    }
  }

  private glassShader(m: THREE.MeshStandardMaterial) {
    const night = this.nightUniform;
    m.onBeforeCompile = (sh) => {
      sh.uniforms.uNight = night;
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying float vWin;')
        .replace('#include <uv_vertex>', `#include <uv_vertex>
          float iid = 0.0;
          #ifdef USE_INSTANCING
            iid = float(gl_InstanceID);
          #endif
          vWin = fract(uv.x * 7.31 + iid * 0.6180339);`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying float vWin;\nuniform float uNight;')
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          float lit = step(0.5, vWin);
          vec3 warm = mix(vec3(1.0, 0.72, 0.42), vec3(1.0, 0.86, 0.66), fract(vWin * 13.7));
          totalEmissiveRadiance += warm * lit * uNight * (0.35 + 0.75 * fract(vWin * 5.3));`);
    };
    m.customProgramCacheKey = () => 'vp-glass';
  }

  private eachMesh(o: THREE.Object3D, f: (m: THREE.Mesh) => void) {
    o.traverse((c) => { if ((c as THREE.Mesh).isMesh) f(c as THREE.Mesh); });
  }

  private buildSite(scene: THREE.Object3D) {
    this.eachMesh(scene, (m) => {
      m.castShadow = true; m.receiveShadow = true;
      this.tuneMaterial(m.material as THREE.MeshStandardMaterial);
    });
    this.root.add(scene);
  }

  private buildTowers(scene: THREE.Object3D) {
    const get = (n: string) => scene.getObjectByName(n)!;
    for (const block of SITE.blocks) {
      const floorNode = get(`${block.id}_floor`);
      const meshes: THREE.InstancedMesh[] = [];
      this.eachMesh(floorNode, (m) => {
        const mat = m.material as THREE.MeshStandardMaterial;
        this.tuneMaterial(mat);
        if (mat.name === 'glass') this.glassShader(mat);
        const im = new THREE.InstancedMesh(m.geometry, mat, NF);
        for (let f = 0; f < NF; f++) {
          const mm = new THREE.Matrix4().makeTranslation(0, GH + f * FH, 0).multiply(m.matrixWorld);
          im.setMatrixAt(f, mm);
        }
        im.castShadow = true; im.receiveShadow = true;
        im.computeBoundingSphere();
        im.frustumCulled = false;
        meshes.push(im);
        this.root.add(im);
      });
      const ground = get(`${block.id}_ground`);
      this.eachMesh(ground, (m) => {
        m.castShadow = true; m.receiveShadow = true;
        const mat = m.material as THREE.MeshStandardMaterial;
        this.tuneMaterial(mat);
        if (mat.name === 'glass' && !mat.onBeforeCompile.toString().includes('vWin')) this.glassShader(mat);
      });
      this.root.add(ground);
      const roof = get(`${block.id}_roof`);
      roof.position.y = GH + NF * FH;
      this.eachMesh(roof, (m) => { m.castShadow = true; m.receiveShadow = true; this.tuneMaterial(m.material as THREE.MeshStandardMaterial); });
      this.root.add(roof);
      // planters with creepers on selected floors
      const pl = get(`${block.id}_planter`);
      this.eachMesh(pl, (m) => {
        const im = new THREE.InstancedMesh(m.geometry, m.material, SITE.planterFloors.length);
        SITE.planterFloors.forEach((f, i) => im.setMatrixAt(i, new THREE.Matrix4().makeTranslation(0, GH + (f - 1) * FH, 0).multiply(m.matrixWorld)));
        im.castShadow = true;
        im.userData.planterFloors = SITE.planterFloors;
        im.frustumCulled = false;
        meshes.push(im);
        this.root.add(im);
      });
      // ghost volume shown above a sliced floor
      const [x0, x1, y0, y1] = block.rect;
      const ghost = new THREE.Mesh(
        new THREE.BoxGeometry(x1 - x0 + 0.3, 1, y1 - y0 + 0.3),
        new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.07, depthWrite: false }),
      );
      ghost.position.copy(toV((x0 + x1) / 2, (y0 + y1) / 2));
      const edges = new THREE.LineSegments(new THREE.EdgesGeometry(ghost.geometry), new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 }));
      ghost.add(edges);
      ghost.visible = false;
      this.root.add(ghost);
      this.stacks.push({ block, meshes, roof, ghost });
    }
  }

  private buildProps(scene: THREE.Object3D) {
    const dummy = new THREE.Object3D();
    for (const kind of Object.keys(PROPS)) {
      const node = scene.getObjectByName(kind);
      const list = PROPS[kind];
      if (!node || !list?.length) continue;
      this.eachMesh(node, (m) => {
        const mat = (m.material as THREE.MeshStandardMaterial);
        this.tuneMaterial(mat);
        const im = new THREE.InstancedMesh(m.geometry, mat, list.length);
        list.forEach((p, i) => {
          dummy.position.copy(toV(p.x, p.y));
          dummy.rotation.set(0, p.r, 0);
          dummy.scale.setScalar(p.s);
          dummy.updateMatrix();
          im.setMatrixAt(i, dummy.matrix.clone().multiply(m.matrixWorld));
          if (kind === 'car' && mat.name === 'carpaint') im.setColorAt(i, new THREE.Color(p.c || '#ffffff'));
        });
        if (im.instanceColor) im.instanceColor.needsUpdate = true;
        im.castShadow = kind !== 'shrub';
        im.receiveShadow = true;
        im.frustumCulled = false;
        this.root.add(im);
        if (kind === 'car') this.carMeshes.push(im);
      });
    }
    // a handful of real point lights near the entrance for night mood
    for (const [e, n] of [[40, -8], [40, 8], [27, 0], [-10, 0], [-28, 0]]) {
      const l = new THREE.PointLight(0xffc98a, 0, 26, 1.6);
      l.position.copy(toV(e, n, 4));
      this.lampLights.push(l);
      this.root.add(l);
    }
  }

  private buildPickers() {
    const inv = new THREE.MeshBasicMaterial({ visible: false });
    for (const t of ['A', 'B', 'C', 'D', 'E', 'F']) {
      const flats = SITE.blocks.flatMap((b) => b.flats).filter((f) => f.tower === t);
      const xs = flats.flatMap((f) => [f.rect[0], f.rect[1]]), ys = flats.flatMap((f) => [f.rect[2], f.rect[3]]);
      const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
      const h = GH + NF * FH + 2;
      const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0 + 1, h, y1 - y0 + 1), inv);
      m.position.copy(toV((x0 + x1) / 2, (y0 + y1) / 2, h / 2));
      m.userData.tower = t;
      this.towerPick.push(m);
      this.root.add(m);
    }
  }

  towerCenter(t: string) {
    const m = this.towerPick.find((p) => p.userData.tower === t)!;
    return m.position.clone();
  }

  /** Slice: show floors 1..floor for the block containing `tower`; null = show all. */
  slice(tower: string | null, floor: number | null) {
    for (const s of this.stacks) {
      const active = tower != null && s.block.towers.includes(tower) && floor != null;
      const n = active ? floor! : NF;
      for (const im of s.meshes) {
        const pf = im.userData.planterFloors as number[] | undefined;
        im.count = pf ? pf.filter((f) => f <= n - (active ? 1 : 0)).length : n;
      }
      s.roof.visible = !active;
      s.ghost.visible = active;
      if (active) {
        const top = GH + n * FH, full = GH + NF * FH + 1.5;
        s.ghost.scale.y = full - top;
        s.ghost.position.y = top + (full - top) / 2;
      }
    }
  }

  /** Coloured unit volumes for a tower floor */
  showFloorUnits(tower: string | null, floor: number | null, selected?: string, hoverId?: string) {
    this.overlay.clear();
    this.unitPick = [];
    if (!tower || !floor) return;
    for (const u of UNITS.filter((x) => x.tower === tower && x.floor === floor)) {
      const [x0, x1, y0, y1] = u.flat.rect;
      const sel = u.id === selected, hov = u.id === hoverId;
      // translucent plate on the exposed (sliced) floor top + a light volume rising from it
      const g = new THREE.BoxGeometry(x1 - x0 - 0.2, 0.22, y1 - y0 - 0.2);
      const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({
        color: STATUS_COLOR[u.status], transparent: true, opacity: sel ? 0.95 : hov ? 0.85 : 0.7, depthWrite: false,
      }));
      const top = GH + floor * FH;
      m.position.copy(toV((x0 + x1) / 2, (y0 + y1) / 2, top + 0.14));
      m.renderOrder = 5;
      m.userData.unit = u.id;
      const e = new THREE.LineSegments(new THREE.EdgesGeometry(g), new THREE.LineBasicMaterial({ color: sel ? 0xffffff : 0x0d1117, transparent: true, opacity: sel ? 1 : 0.5, depthTest: false }));
      e.renderOrder = 6;
      m.add(e);
      if (sel || hov) {
        const vg = new THREE.BoxGeometry(x1 - x0 + 0.4, FH, y1 - y0 + 0.4);
        const v = new THREE.Mesh(vg, new THREE.MeshBasicMaterial({ color: sel ? 0xffffff : STATUS_COLOR[u.status], transparent: true, opacity: sel ? 0.16 : 0.1, depthWrite: false }));
        v.position.y = FH / 2;
        const ve = new THREE.LineSegments(new THREE.EdgesGeometry(vg), new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9 }));
        v.add(ve);
        m.add(v);
      }
      this.overlay.add(m);
      this.unitPick.push(m);
    }
  }

  setNight(n: number) {
    this.nightUniform.value = n;
    this.root.traverse((o) => {
      const m = (o as THREE.Mesh).material as THREE.MeshStandardMaterial | undefined;
      if (m && m.userData?.nightEmissive) {
        m.emissiveIntensity = 0.05 + m.userData.nightEmissive * n;
      }
    });
    this.lampLights.forEach((l) => (l.intensity = 60 * n));
  }

  /** Balcony camera pose for a unit + view index */
  balconyPose(u: Unit, viewIdx = 0) {
    const f: FlatDef = u.flat;
    const v = f.views[Math.min(viewIdx, f.views.length - 1)];
    const [x0, x1, y0, y1] = f.rect;
    const [dx, dy] = DIR_VEC[v.dir];
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const hx = (x1 - x0) / 2, hy = (y1 - y0) / 2;
    let px = cx + dx * (hx + 0.3), py = cy + dy * (hy + 0.3);
    // exact balcony anchor exported from blender/towers.py
    const a = (BALCONIES as Record<string, { e: number; n: number; dir: string }[]>)[`${f.tower}-${f.no}`]?.find((q) => q.dir === v.dir);
    if (a) { px = a.e; py = a.n; }
    const eye = GH + (u.floor - 1) * FH + 1.55;
    const pos = toV(px, py, eye);
    const look = toV(px + dx * 50, py + dy * 50, eye - 9);
    return { pos, look, dir: v.dir, label: v.label };
  }

  /** Hours of direct sun reaching a balcony on a given date (ray-tested against towers + neighbours). */
  sunHours(u: Unit, viewIdx: number, date: Date, blockers: THREE.Object3D[]) {
    const p = this.balconyPose(u, viewIdx);
    const [dx, dy] = DIR_VEC[p.dir as keyof typeof DIR_VEC];
    const out = new THREE.Vector3(dx, 0, -dy);
    const origin = p.pos.clone().addScaledVector(out, 1.4).setY(p.pos.y - 0.4);
    const rc = new THREE.Raycaster();
    let hours = 0;
    for (let h = 5.5; h <= 19; h += 0.25) {
      const sp = sunPosition(istDate(h, date), SITE.geo.lat, SITE.geo.lng);
      if (sp.altitude <= 0.03) continue;
      const dir = new THREE.Vector3(Math.sin(sp.azimuth) * Math.cos(sp.altitude), Math.sin(sp.altitude), -Math.cos(sp.azimuth) * Math.cos(sp.altitude));
      if (dir.dot(out) <= 0.05) continue;
      rc.set(origin, dir);
      rc.far = 600;
      if (rc.intersectObjects(blockers, true).length === 0) hours += 0.25;
    }
    return hours;
  }
}
