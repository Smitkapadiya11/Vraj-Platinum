import * as THREE from 'three';
import ctx from '../data/context.json';

/**
 * Neighbourhood as a clean architect's "white model".
 * Footprints + building:levels from OpenStreetMap (© OpenStreetMap contributors), a few towers OSM lacks
 * digitised from the Google Earth reference; built offline by scripts/build_map.py.
 * Record: [ring [x,z,...] (x = East, z = South, metres), height m, levels, kind (0 building, 1 sports shed)]
 *
 * Facades are drawn procedurally in the shader (floor bands, window grid, stilt parking, coping) so they stay
 * crisp at any distance — no photo textures. Towers get rooftop solar rows + a lift/water-tank room.
 */
type Rec = [number[], number, number, number];

const GH = 3.6, FH = 3.0, PARAPET = 1.0;

function hash(n: number) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }

function pointIn(px: number, pz: number, r: THREE.Vector2[]) {
  let inside = false;
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const a = r[i], b = r[j];
    if ((a.y > pz) !== (b.y > pz) && px < ((b.x - a.x) * (pz - a.y)) / (b.y - a.y) + a.x) inside = !inside;
  }
  return inside;
}

export class Context {
  group = new THREE.Group();
  wallMat: THREE.MeshStandardMaterial;
  /** neighbours closer than `clear` metres to the camera are cut away (orbit views); 0 in balcony views */
  clear = { value: 40 };
  private night = { value: 0 };

  constructor() {
    const wp: number[] = [], wn: number[] = [], wu: number[] = [], wc: number[] = [], wb: number[] = [];
    const rp: number[] = [], rc: number[] = [];
    const props: { m: THREE.Matrix4; c: THREE.Color }[] = [];
    const col = new THREE.Color();
    const SOLAR = new THREE.Color('#2f3d52'), ROOM = new THREE.Color('#ece8e0'), TANK = new THREE.Color('#d9d4ca');
    const q = new THREE.Quaternion(), e = new THREE.Euler();
    let bi = 0;

    for (const [ring, h, lv, kind] of ctx as unknown as Rec[]) {
      bi++;
      const seed = hash(bi);
      const pts: THREE.Vector2[] = [];
      for (let i = 0; i < ring.length; i += 2) pts.push(new THREE.Vector2(ring[i], ring[i + 1]));
      // signed area in (x,z): >0 ⇒ outward normal of edge (dx,dz) is (dz,-dx)
      let A = 0;
      for (let i = 0; i < pts.length; i++) { const a = pts[i], b = pts[(i + 1) % pts.length]; A += a.x * b.y - b.x * a.y; }
      const sgn = A > 0 ? 1 : -1;
      // warm off-white with gentle per-building variation; sheds a cooler light grey
      if (kind === 1) col.setRGB(0.86, 0.87, 0.87, THREE.SRGBColorSpace);
      else col.setHSL(0.09 + (seed - 0.5) * 0.03, 0.16 + seed * 0.12, 0.86 + (hash(bi + 7) - 0.5) * 0.06, THREE.SRGBColorSpace);
      const top = h + (kind === 1 ? 0.4 : PARAPET);

      let u = Math.floor(seed * 5) * 1.7;
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i], b = pts[(i + 1) % pts.length];
        const dx = b.x - a.x, dz = b.y - a.y, len = Math.hypot(dx, dz);
        if (len < 0.05) continue;
        const nx = (sgn * dz) / len, nz = (-sgn * dx) / len;
        const v = [[a.x, 0, a.y, u, 0], [b.x, 0, b.y, u + len, 0], [b.x, top, b.y, u + len, top], [a.x, top, a.y, u, top]];
        const order = sgn > 0 ? [0, 2, 1, 0, 3, 2] : [0, 1, 2, 0, 2, 3];
        for (const k of order) {
          wp.push(v[k][0], v[k][1], v[k][2]); wn.push(nx, 0, nz); wu.push(v[k][3], v[k][4]);
          wc.push(col.r, col.g, col.b); wb.push(lv, seed, kind, h);
        }
        u += len;
      }
      // roof (slightly darker), parapet comes from the wall extending above it
      const rcol = col.clone().multiplyScalar(kind === 1 ? 0.97 : 0.9);
      const tris = THREE.ShapeUtils.triangulateShape(pts, []);
      for (const t of tris) {
        const [i0, i1, i2] = t;
        const p0 = pts[i0], p1 = pts[i1], p2 = pts[i2];
        // winding so the face points up (+y) in three's x/z (z = South) frame
        const cy = (p1.y - p0.y) * (p2.x - p0.x) - (p1.x - p0.x) * (p2.y - p0.y);
        const tri = cy > 0 ? [p0, p1, p2] : [p0, p2, p1];
        for (const p of tri) { rp.push(p.x, h, p.y); rc.push(rcol.r, rcol.g, rcol.b); }
      }

      // tower roof: lift/water-tank room + rows of solar panels
      if (kind === 0 && lv >= 10) {
        let best = 0, ang = 0;
        for (let i = 0; i < pts.length; i++) {
          const a = pts[i], b = pts[(i + 1) % pts.length], L = a.distanceTo(b);
          if (L > best) { best = L; ang = Math.atan2(b.y - a.y, b.x - a.x); }
        }
        const ca = Math.cos(ang), sa = Math.sin(ang);
        const loc = pts.map((p) => new THREE.Vector2(p.x * ca + p.y * sa, -p.x * sa + p.y * ca));
        const bb = new THREE.Box2().setFromPoints(loc);
        const c = bb.getCenter(new THREE.Vector2()), sz = bb.getSize(new THREE.Vector2());
        const toW = (lu: number, lvv: number) => new THREE.Vector2(lu * ca - lvv * sa, lu * sa + lvv * ca);
        e.set(0, -ang, 0); q.setFromEuler(e);
        // machine room
        const rw = Math.min(7, sz.x * 0.35), rd = Math.min(5, sz.y * 0.4);
        const cw = toW(c.x, c.y);
        props.push({ m: new THREE.Matrix4().compose(new THREE.Vector3(cw.x, h + 1.7, cw.y), q, new THREE.Vector3(rw, 3.4, rd)), c: ROOM });
        if (seed > 0.4) {
          const tw = toW(c.x + rw * 0.25, c.y);
          props.push({ m: new THREE.Matrix4().compose(new THREE.Vector3(tw.x, h + 4.0, tw.y), q, new THREE.Vector3(rw * 0.5, 1.4, rd * 0.8)), c: TANK });
        }
        // solar rows (tilted 12° to the south), clipped to the footprint
        e.set(-0.21, -ang, 0, 'YXZ'); const qs = new THREE.Quaternion().setFromEuler(e);
        for (let vv = bb.min.y + 2.2; vv < bb.max.y - 2.0; vv += 2.5) {
          if (Math.abs(vv - c.y) < rd / 2 + 1.4) continue;
          const u0 = bb.min.x + 2.0, u1 = bb.max.x - 2.0;
          if (u1 - u0 < 3) continue;
          const mid = toW((u0 + u1) / 2, vv);
          if (!pointIn(mid.x, mid.y, pts)) continue;
          props.push({ m: new THREE.Matrix4().compose(new THREE.Vector3(mid.x, h + 0.75, mid.y), qs, new THREE.Vector3(u1 - u0, 0.12, 1.7)), c: SOLAR });
        }
      }
    }

    const wg = new THREE.BufferGeometry();
    wg.setAttribute('position', new THREE.Float32BufferAttribute(wp, 3));
    wg.setAttribute('normal', new THREE.Float32BufferAttribute(wn, 3));
    wg.setAttribute('aUV', new THREE.Float32BufferAttribute(wu, 2));
    wg.setAttribute('color', new THREE.Float32BufferAttribute(wc, 3));
    wg.setAttribute('aB', new THREE.Float32BufferAttribute(wb, 4));
    this.wallMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.88, metalness: 0, side: THREE.DoubleSide });
    this.facadeShader(this.wallMat);
    const walls = new THREE.Mesh(wg, this.wallMat);
    walls.castShadow = true; walls.receiveShadow = true;

    const rg = new THREE.BufferGeometry();
    rg.setAttribute('position', new THREE.Float32BufferAttribute(rp, 3));
    rg.setAttribute('color', new THREE.Float32BufferAttribute(rc, 3));
    rg.computeVertexNormals();
    const roofMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95 });
    this.fadeShader(roofMat);
    const roofs = new THREE.Mesh(rg, roofMat);
    roofs.receiveShadow = true;

    const pm = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial({ roughness: 0.55, metalness: 0.1 }), props.length);
    props.forEach((p, i) => { pm.setMatrixAt(i, p.m); pm.setColorAt(i, p.c); });
    pm.instanceMatrix.needsUpdate = true;
    this.fadeShader(pm.material as THREE.Material);
    pm.castShadow = true; pm.receiveShadow = true;
    this.group.add(walls, roofs, pm);
  }

  private fadeShader(m: THREE.Material, extra?: (sh: THREE.WebGLProgramParametersWithUniforms) => void) {
    m.onBeforeCompile = (sh) => {
      sh.uniforms.uClear = this.clear;
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWP;')
        .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWP = (modelMatrix * vec4(transformed, 1.0)).xyz;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vWP;\nuniform float uClear;')
        .replace('void main() {', 'void main() {\n if (distance(vWP, cameraPosition) < uClear) discard;');
      extra?.(sh);
    };
  }

  /** procedural facade: floor bands, window grid, stilt parking, coping; warm lit windows at night */
  private facadeShader(mat: THREE.MeshStandardMaterial) {
    this.fadeShader(mat, (sh) => {
      sh.uniforms.uNight = this.night;
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nattribute vec2 aUV;\nattribute vec4 aB;\nvarying vec2 vF;\nvarying vec4 vB;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvF = aUV; vB = aB;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
varying vec2 vF;
varying vec4 vB;
uniform float uNight;
float hh(vec3 p){ return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float band(float x, float a, float b, float w){ return smoothstep(a - w, a + w, x) - smoothstep(b - w, b + w, x); }`)
        .replace('#include <color_fragment>', `#include <color_fragment>
  float lv = vB.x, seed = vB.y, kind = vB.z, Hb = vB.w;
  float tower = step(7.5, lv);
  float isGround = step(vF.y, ${GH.toFixed(1)});
  float fl = isGround > 0.5 ? 0.0 : 1.0 + floor((vF.y - ${GH.toFixed(1)}) / ${FH.toFixed(1)});
  float ly = isGround > 0.5 ? vF.y / ${GH.toFixed(1)} : fract((vF.y - ${GH.toFixed(1)}) / ${FH.toFixed(1)});
  float bw = mix(4.4, 3.4, tower) + seed * 0.5;
  float bx = vF.x / bw;
  float lx = fract(bx), bay = floor(bx);
  vec2 fw = fwidth(vec2(bx, vF.y / ${FH.toFixed(1)}));
  float aa = clamp(max(fw.x, fw.y) * 1.4 - 0.15, 0.0, 1.0);
  float para = step(Hb, vF.y);
  float win = band(lx, 0.2, 0.8, fw.x) * band(ly, 0.3, 0.86, fw.y) * (1.0 - para);
  // sports sheds: one long clerestory band, no punched windows
  win = mix(win, band(vF.y, Hb - 2.4, Hb - 1.2, fw.y * 3.0) * band(lx, 0.04, 0.96, fw.x), step(0.5, kind));
  // towers: open stilt parking at ground level, columns every bay
  float stilt = tower * isGround * (1.0 - band(lx, -0.1, 0.16, fw.x)) * step(0.05, ly);
  win *= (1.0 - tower * isGround);
  vec3 wall = diffuseColor.rgb;
  vec3 glass = vec3(0.13, 0.16, 0.19) + vec3(0.07, 0.08, 0.09) * ly;
  vec3 c = wall * (1.0 - 0.06 * band(ly, -0.02, 0.07, fw.y) * (1.0 - isGround));   // slab lines
  c = mix(c, glass, win);
  c = mix(c, wall * 0.22, stilt);
  c = mix(c, wall * 1.05, para);
  vec3 avg = mix(wall, glass, 0.3 * (1.0 - para) * (1.0 - step(0.5, kind)));
  diffuseColor.rgb = mix(c, avg, aa);
  float lit = step(0.6, hh(vec3(bay, fl, seed * 97.0))) * win;`)
        .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n  roughnessFactor = mix(roughnessFactor, 0.3, win * (1.0 - aa));')
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance += vec3(1.0, 0.72, 0.42) * 0.8 * uNight * mix(lit, 0.1, aa);');
    });
  }

  setNight(n: number) { this.night.value = n; }
}
