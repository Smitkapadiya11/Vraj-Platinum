import * as THREE from 'three';
import { SITE } from '../data/project';
import { DIR_VEC } from '../data/units';

/**
 * Photographic facades: the main faces of every tower are clad with a perspective-rectified photo of the
 * real Vraj Platinum elevation (2 storeys of the garden-side bay, 23 Nov 2026), instanced per floor so
 * floor slicing still works. The modelled geometry stays underneath for depth, night lighting & balcony views.
 */
const GH = SITE.groundH, FH = SITE.floorH, NF = SITE.floors;
const OFFSET: Record<string, number> = { primary: 1.42, end: 1.2 };

export class PhotoFacades {
  group = new THREE.Group();
  meshes: { block: string; mesh: THREE.InstancedMesh; floors: number[] }[] = [];
  mat: THREE.MeshStandardMaterial;

  constructor(anisotropy: number) {
    const tex = new THREE.TextureLoader().load('/tex/facade_garden.jpg');
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = anisotropy;
    this.mat = new THREE.MeshStandardMaterial({
      map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: 0.32, roughness: 0.9, metalness: 0, envMapIntensity: 0.25,
      polygonOffset: true, polygonOffsetFactor: -1,
    });
    for (const block of SITE.blocks) {
      for (const parity of [1, 0]) {
        const geos: THREE.BufferGeometry[] = [];
        for (const f of block.flats) {
          const [x0, x1, y0, y1] = f.rect;
          f.views.forEach((v, i) => {
            const off = OFFSET[i === 0 ? 'primary' : 'end'];
            const [dx, dy] = DIR_VEC[v.dir];
            const along = dx !== 0 ? y1 - y0 : x1 - x0;
            const g = new THREE.PlaneGeometry(along + 0.1, FH);
            // odd floors use the lower storey of the 2-storey photo, even floors the upper one
            const uv = g.attributes.uv as THREE.BufferAttribute;
            for (let k = 0; k < uv.count; k++) uv.setY(k, uv.getY(k) * 0.5 + (parity ? 0 : 0.5));
            const cx = (x0 + x1) / 2 + dx * ((x1 - x0) / 2 + off), cn = (y0 + y1) / 2 + dy * ((y1 - y0) / 2 + off);
            // plane faces +Z by default; three: x = East, z = -North
            const rotY = v.dir === 'S' ? 0 : v.dir === 'N' ? Math.PI : v.dir === 'E' ? Math.PI / 2 : -Math.PI / 2;
            g.rotateY(rotY);
            g.translate(cx, FH / 2 - 0.02, -cn);
            geos.push(g);
          });
        }
        const merged = mergeGeos(geos);
        const floors = Array.from({ length: NF }, (_, k) => k + 1).filter((fl) => fl % 2 === parity);
        const im = new THREE.InstancedMesh(merged, this.mat, floors.length);
        floors.forEach((fl, k) => im.setMatrixAt(k, new THREE.Matrix4().makeTranslation(0, GH + (fl - 1) * FH, 0)));
        im.receiveShadow = true;
        im.frustumCulled = false;
        this.group.add(im);
        this.meshes.push({ block: block.id, mesh: im, floors });
      }
    }
  }

  slice(blockId: string | null, floor: number | null) {
    for (const m of this.meshes) {
      const n = blockId === m.block && floor ? floor : NF;
      m.mesh.count = m.floors.filter((f) => f <= n).length;
    }
  }
}

function mergeGeos(gs: THREE.BufferGeometry[]) {
  const pos: number[] = [], nor: number[] = [], uv: number[] = [], idx: number[] = [];
  let base = 0;
  for (const g of gs) {
    const p = g.attributes.position, n = g.attributes.normal, u = g.attributes.uv;
    for (let i = 0; i < p.count; i++) { pos.push(p.getX(i), p.getY(i), p.getZ(i)); nor.push(n.getX(i), n.getY(i), n.getZ(i)); uv.push(u.getX(i), u.getY(i)); }
    const ix = g.index!;
    for (let i = 0; i < ix.count; i++) idx.push(ix.getX(i) + base);
    base += p.count;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  out.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  out.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  out.setIndex(idx);
  return out;
}
