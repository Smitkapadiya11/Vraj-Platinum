import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import data from '../data/landmarks.json';

/**
 * Real neighbourhood details across the 100 ft road (placed from the 14th-floor balcony photos and Google Maps,
 * see scripts/add_landmarks.py): party-plot gates with domes, long tents, hedge-walled lawns, the netted
 * BMR box-cricket cage, the silos of the under-construction tower and the eucalyptus plantation.
 * Coordinates: x = east, z = south (metres from the plot centre), rot = rotation about +Y.
 */
interface Prim { t: 'box' | 'cyl' | 'dome' | 'tent' | 'net'; x: number; z: number; y0: number; y1: number; w: number; d: number; rot: number; c: string }

function colorize(g: THREE.BufferGeometry, hex: string) {
  const ng = g.index ? g.toNonIndexed() : g;
  const c = new THREE.Color(hex);
  const n = ng.attributes.position.count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { a[i * 3] = c.r; a[i * 3 + 1] = c.g; a[i * 3 + 2] = c.b; }
  ng.setAttribute('color', new THREE.BufferAttribute(a, 3));
  ng.deleteAttribute('uv');
  return ng;
}

function shape(p: Prim) {
  const h = p.y1 - p.y0;
  let g: THREE.BufferGeometry;
  if (p.t === 'cyl') g = new THREE.CylinderGeometry(p.w / 2, p.w / 2, h, 14).translate(0, h / 2, 0);
  else if (p.t === 'dome') g = new THREE.SphereGeometry(p.w / 2, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2).scale(1, (h / (p.w / 2)), 1);
  else if (p.t === 'tent') g = new THREE.CylinderGeometry(p.d / 2, p.d / 2, p.w, 18, 1, false, 0, Math.PI).rotateZ(Math.PI / 2);
  else g = new THREE.BoxGeometry(p.w, h, p.d).translate(0, h / 2, 0);
  g.rotateY(p.rot);
  g.translate(p.x, p.y0, p.z);
  return colorize(g, p.c);
}

export function buildLandmarks() {
  const group = new THREE.Group();
  group.name = 'landmarks';
  const prims = data.prims as Prim[];
  const solid = prims.filter((p) => p.t !== 'net').map(shape);
  const nets = prims.filter((p) => p.t === 'net').map(shape);
  const m = new THREE.Mesh(mergeGeometries(solid), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.8 }));
  m.castShadow = m.receiveShadow = true;
  group.add(m);
  if (nets.length) {
    const nm = new THREE.Mesh(mergeGeometries(nets), new THREE.MeshStandardMaterial({ vertexColors: true, transparent: true, opacity: 0.38, roughness: 0.9, side: THREE.DoubleSide, depthWrite: false }));
    group.add(nm);
  }
  // eucalyptus: slim pale trunk + tall narrow crown
  const trunk = colorize(new THREE.CylinderGeometry(0.18, 0.28, 9, 5).translate(0, 4.5, 0), '#cfc6b4');
  const crown = colorize(new THREE.IcosahedronGeometry(1.9, 1).scale(1, 2.4, 1).translate(0, 12.5, 0), '#55703f');
  const crown2 = colorize(new THREE.IcosahedronGeometry(1.3, 0).scale(1, 1.8, 1).translate(0.8, 15.2, 0.4), '#647f48');
  const tg = mergeGeometries([trunk, crown, crown2]);
  const G = data.grove as number[];
  const n = G.length / 3;
  const im = new THREE.InstancedMesh(tg, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9, flatShading: true }), n);
  const mx = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), pos = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  for (let i = 0; i < n; i++) {
    const k = G[i * 3 + 2];
    q.setFromAxisAngle(up, i * 2.399);
    mx.compose(pos.set(G[i * 3], 0, G[i * 3 + 1]), q, s.set(k, k, k));
    im.setMatrixAt(i, mx);
  }
  im.castShadow = true;
  group.add(im);
  return group;
}
