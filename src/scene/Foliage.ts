import * as THREE from 'three';

/** Painted alpha-cutout foliage (palm fronds & leafy crowns) for cross-billboard trees — far more natural than solid blobs. */
function frondTexture() {
  const c = document.createElement('canvas'); c.width = 256; c.height = 512;
  const g = c.getContext('2d')!;
  g.translate(128, 500);
  const rib = (len: number) => {
    g.strokeStyle = '#4d5f2a'; g.lineWidth = 4;
    g.beginPath(); g.moveTo(0, 0); g.quadraticCurveTo(10, -len * 0.5, 0, -len); g.stroke();
    for (let i = 0; i < 46; i++) {
      const t = i / 46, y = -len * t, w = 110 * Math.sin(Math.PI * Math.min(1, t * 1.1)) * (0.75 + Math.random() * 0.35);
      for (const s of [-1, 1]) {
        const hue = 78 + Math.random() * 22, l = 22 + Math.random() * 16;
        g.strokeStyle = `hsl(${hue} 45% ${l}%)`; g.lineWidth = 3 + Math.random() * 2;
        g.beginPath(); g.moveTo(5 * Math.sin(t * 3), y); g.quadraticCurveTo(s * w * 0.5, y - 14, s * w, y + 28 + Math.random() * 20); g.stroke();
      }
    }
  };
  rib(480);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}
function crownTexture() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 512;
  const g = c.getContext('2d')!;
  for (let i = 0; i < 2600; i++) {
    const a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * 220;
    const x = 256 + Math.cos(a) * r, y = 250 + Math.sin(a) * r * 0.85;
    const hue = 70 + Math.random() * 40, l = 18 + Math.random() * 26 + (y < 200 ? 8 : 0);
    g.fillStyle = `hsl(${hue} 42% ${l}%)`;
    g.beginPath(); g.ellipse(x, y, 7 + Math.random() * 6, 3 + Math.random() * 3, Math.random() * Math.PI, 0, Math.PI * 2); g.fill();
  }
  g.strokeStyle = '#4a3a2a'; g.lineWidth = 9;
  g.beginPath(); g.moveTo(256, 512); g.lineTo(256, 330); g.stroke();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}

export function makePalmGeometry() {
  const geos: THREE.BufferGeometry[] = [];
  const N = 12;
  for (let i = 0; i < N; i++) {
    const g = new THREE.PlaneGeometry(1.4, 3.2, 1, 4);
    g.translate(0, 1.6, 0);
    const p = g.attributes.position as THREE.BufferAttribute;
    for (let k = 0; k < p.count; k++) { const y = p.getY(k); p.setZ(k, -0.06 * y * y); } // droop
    g.rotateX(-0.55 - Math.random() * 0.5);
    g.rotateY((i / N) * Math.PI * 2 + Math.random() * 0.3);
    g.translate(0, 7.2, 0);
    geos.push(g);
  }
  return merge(geos);
}
export function makeCrownGeometry() {
  const geos: THREE.BufferGeometry[] = [];
  for (let i = 0; i < 3; i++) {
    const g = new THREE.PlaneGeometry(5.2, 5.2);
    g.translate(0, 3.6, 0);
    g.rotateY((i / 3) * Math.PI);
    geos.push(g);
  }
  return merge(geos);
}
export const palmMaterial = () => new THREE.MeshStandardMaterial({ map: frondTexture(), alphaTest: 0.45, side: THREE.DoubleSide, roughness: 0.85 });
export const crownMaterial = () => new THREE.MeshStandardMaterial({ map: crownTexture(), alphaTest: 0.4, side: THREE.DoubleSide, roughness: 0.9 });

function merge(gs: THREE.BufferGeometry[]) {
  const pos: number[] = [], nor: number[] = [], uv: number[] = [], idx: number[] = [];
  let base = 0;
  for (const g of gs) {
    g.computeVertexNormals();
    const p = g.attributes.position, n = g.attributes.normal, u = g.attributes.uv;
    for (let i = 0; i < p.count; i++) { pos.push(p.getX(i), p.getY(i), p.getZ(i)); nor.push(0, 1, 0); uv.push(u.getX(i), u.getY(i)); void n; }
    const ix = g.index!; for (let i = 0; i < ix.count; i++) idx.push(ix.getX(i) + base);
    base += p.count;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  out.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  out.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  out.setIndex(idx);
  return out;
}
