import * as THREE from 'three';
import ctx from '../data/context.json';

/**
 * Surrounding real buildings (OpenStreetMap footprints + building:levels, © OpenStreetMap contributors),
 * extruded around the site so balcony views show the actual neighbourhood skyline.
 * Data: [flat [e,n,...] ring, height m, levels, colour, name]
 */
type Rec = [number[], number, number, string, string];
const COLORS: Record<string, string> = { white: '#e6e3dc', beige: '#d8c9ad', grey: '#a8a8a4', lightyellow: '#e6dcb9', '': '#d2ccbf' };

function windowTexture(lit: boolean) {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d')!;
  g.fillStyle = lit ? '#000' : '#fff';
  g.fillRect(0, 0, 128, 128);
  // one 3 m x 3 m facade bay: window band + slab line
  for (let i = 0; i < 2; i++) {
    const x = 10 + i * 62;
    if (lit) {
      g.fillStyle = (i + 1) % 2 ? '#ffcf8a' : '#000';
      g.fillRect(x, 34, 46, 58);
    } else {
      g.fillStyle = '#5d6670';
      g.fillRect(x, 34, 46, 58);
      g.fillStyle = '#8b96a1';
      g.fillRect(x + 3, 37, 40, 20);
    }
  }
  if (!lit) { g.fillStyle = '#d9d6d0'; g.fillRect(0, 118, 128, 10); }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

export class Context {
  group = new THREE.Group();
  wallMat: THREE.MeshStandardMaterial;

  constructor(offsetE = 0) {
    const wp: number[] = [], wu: number[] = [], wc: number[] = [], wi: number[] = [];
    const rp: number[] = [], rc: number[] = [];
    const col = new THREE.Color();
    for (const [ring, hM, lv, colour] of ctx as unknown as Rec[]) {
      const h = hM || (lv ? lv * 3.05 + 1.2 : 8);
      col.set(COLORS[colour] ?? COLORS['']);
      const pts: THREE.Vector2[] = [];
      for (let i = 0; i < ring.length; i += 2) pts.push(new THREE.Vector2(ring[i] + offsetE, ring[i + 1]));
      if (THREE.ShapeUtils.isClockWise(pts)) pts.reverse();
      // walls
      let u = 0;
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i], b = pts[(i + 1) % pts.length];
        const len = a.distanceTo(b);
        const base = wp.length / 3;
        // three: x = E, z = -N
        wp.push(a.x, 0, -a.y, b.x, 0, -b.y, b.x, h, -b.y, a.x, h, -a.y);
        wu.push(u / 3, 0, (u + len) / 3, 0, (u + len) / 3, h / 3, u / 3, h / 3);
        for (let k = 0; k < 4; k++) wc.push(col.r, col.g, col.b);
        wi.push(base, base + 1, base + 2, base, base + 2, base + 3);
        u += len;
      }
      // roof
      const tris = THREE.ShapeUtils.triangulateShape(pts, []);
      for (const tri of tris) for (const k of tri) { rp.push(pts[k].x, h, -pts[k].y); rc.push(col.r * 0.92, col.g * 0.92, col.b * 0.92); }
    }
    const wg = new THREE.BufferGeometry();
    wg.setAttribute('position', new THREE.Float32BufferAttribute(wp, 3));
    wg.setAttribute('uv', new THREE.Float32BufferAttribute(wu, 2));
    wg.setAttribute('color', new THREE.Float32BufferAttribute(wc, 3));
    wg.setIndex(wi);
    wg.computeVertexNormals();
    this.wallMat = new THREE.MeshStandardMaterial({
      vertexColors: true, map: windowTexture(false), emissiveMap: windowTexture(true), emissive: 0xffffff,
      emissiveIntensity: 0, roughness: 0.85, side: THREE.DoubleSide,
    });
    const walls = new THREE.Mesh(wg, this.wallMat);
    walls.castShadow = true; walls.receiveShadow = true;
    const rg = new THREE.BufferGeometry();
    rg.setAttribute('position', new THREE.Float32BufferAttribute(rp, 3));
    rg.setAttribute('color', new THREE.Float32BufferAttribute(rc, 3));
    rg.computeVertexNormals();
    const roofs = new THREE.Mesh(rg, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, side: THREE.DoubleSide }));
    roofs.receiveShadow = true;
    this.group.add(walls, roofs);
  }

  setNight(n: number) { this.wallMat.emissiveIntensity = 0.9 * n; }
}
