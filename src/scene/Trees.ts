import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import data from '../data/trees.json';

/**
 * Stylised low-poly trees for the neighbourhood (positions from scripts/build_map.py: OSM woods,
 * mangroves along the creek, satellite tree cover, avenue trees). One InstancedMesh per species.
 */
type Species = 'r' | 'b' | 't';

function part(g: THREE.BufferGeometry, hex: string) {
  const ng = g.index ? g.toNonIndexed() : g;
  const c = new THREE.Color(hex);
  const n = ng.attributes.position.count, cols = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { cols[i * 3] = c.r; cols[i * 3 + 1] = c.g; cols[i * 3 + 2] = c.b; }
  ng.setAttribute('color', new THREE.BufferAttribute(cols, 3));
  ng.deleteAttribute('uv');
  return ng;
}

function speciesGeometry(s: Species) {
  const parts: THREE.BufferGeometry[] = [];
  if (s === 'r') { // rounded shade tree (neem / peepal)
    parts.push(part(new THREE.CylinderGeometry(0.2, 0.32, 2.8, 5).translate(0, 1.4, 0), '#5a4a3a'));
    parts.push(part(new THREE.IcosahedronGeometry(2.6, 1).scale(1, 0.8, 1).translate(0, 4.5, 0), '#4f7336'));
    parts.push(part(new THREE.IcosahedronGeometry(1.7, 0).scale(1, 0.85, 1).translate(1.2, 5.4, -0.5), '#5d8240'));
  } else if (s === 'b') { // mangrove / bush clump
    parts.push(part(new THREE.IcosahedronGeometry(1.6, 0).scale(1, 0.7, 1).translate(0, 1.15, 0), '#3f5f2e'));
    parts.push(part(new THREE.IcosahedronGeometry(1.3, 0).scale(1, 0.7, 1).translate(1.3, 0.95, 0.5), '#4a6c34'));
    parts.push(part(new THREE.IcosahedronGeometry(1.2, 0).scale(1, 0.75, 1).translate(-0.9, 0.9, -0.9), '#3a5729'));
  } else { // tall columnar (ashoka / eucalyptus)
    parts.push(part(new THREE.CylinderGeometry(0.15, 0.22, 3.4, 5).translate(0, 1.7, 0), '#625240'));
    parts.push(part(new THREE.IcosahedronGeometry(1.45, 1).scale(1, 2.1, 1).translate(0, 5.9, 0), '#62843d'));
  }
  const g = mergeGeometries(parts)!;
  g.computeVertexNormals();
  return g;
}

export class Trees {
  group = new THREE.Group();
  count = 0;

  constructor(mobile: boolean) {
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.88, metalness: 0, flatShading: true });
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), sc = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
    const col = new THREE.Color();
    for (const s of ['r', 'b', 't'] as Species[]) {
      const v = (data as Record<Species, number[]>)[s];
      const idx: number[] = [];
      for (let i = 0; i < v.length / 3; i++) if (!mobile || i % 8 < 3) idx.push(i);
      const mesh = new THREE.InstancedMesh(speciesGeometry(s), mat, idx.length);
      idx.forEach((i, k) => {
        const x = v[i * 3], z = v[i * 3 + 1], s0 = v[i * 3 + 2];
        const r = Math.sin(x * 12.9898 + z * 78.233) * 43758.5453, h = r - Math.floor(r);
        q.setFromAxisAngle(up, h * Math.PI * 2);
        sc.set(s0, s0 * (0.88 + h * 0.28), s0);
        m.compose(p.set(x, 0, z), q, sc);
        mesh.setMatrixAt(k, m);
        const b = 0.86 + h * 0.26;
        col.setRGB(b * (0.97 + (h - 0.5) * 0.1), b, b * (1.0 - (h - 0.5) * 0.12));
        mesh.setColorAt(k, col);
      });
      mesh.instanceMatrix.needsUpdate = true;
      mesh.receiveShadow = true;
      mesh.frustumCulled = false; // instances cover the whole neighbourhood
      this.count += idx.length;
      this.group.add(mesh);
    }
  }
}
