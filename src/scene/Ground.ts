import * as THREE from 'three';
import { SITE } from '../data/project';

/**
 * Real-location ground: streams Esri World Imagery tiles around the actual site
 * (21.2318 N, 72.9137 E) and lays them out in local metres (x = East, z = South).
 * Two rings: z18 near (~0.6 m/px) and z15 far, with a neutral fallback plane underneath.
 */
const R = 6378137;
const TILE_URL = (z: number, x: number, y: number) =>
  `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`;

function lng2tile(lng: number, z: number) { return ((lng + 180) / 360) * 2 ** z; }
function lat2tile(lat: number, z: number) {
  const r = (lat * Math.PI) / 180;
  return ((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2) * 2 ** z;
}
function tile2lng(x: number, z: number) { return (x / 2 ** z) * 360 - 180; }
function tile2lat(y: number, z: number) {
  const n = Math.PI - (2 * Math.PI * y) / 2 ** z;
  return (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
}

export class Ground {
  group = new THREE.Group();
  loaded = 0;
  failed = 0;
  private loader = new THREE.TextureLoader();

  constructor(private anisotropy: number, mobile: boolean) {
    this.loader.setCrossOrigin('anonymous');
    const base = new THREE.Mesh(
      new THREE.CircleGeometry(9000, 64).rotateX(-Math.PI / 2),
      new THREE.MeshStandardMaterial({ color: 0x8a8670, roughness: 1 }),
    );
    base.position.y = -0.6;
    base.receiveShadow = true;
    this.group.add(base);
    this.ring(15, mobile ? 2 : 3, -0.4);
    this.ring(18, mobile ? 3 : 4, -0.15);
  }

  private ring(z: number, rad: number, y: number) {
    const lat = SITE.geo.originLat, lng = SITE.geo.originLng;
    const cx = Math.floor(lng2tile(lng, z)), cy = Math.floor(lat2tile(lat, z));
    const cosLat = Math.cos((lat * Math.PI) / 180);
    const toLocal = (la: number, lo: number) => ({
      x: ((lo - lng) * Math.PI / 180) * R * cosLat,
      z: -((la - lat) * Math.PI / 180) * R,
    });
    for (let dx = -rad; dx <= rad; dx++) {
      for (let dy = -rad; dy <= rad; dy++) {
        const tx = cx + dx, ty = cy + dy;
        const a = toLocal(tile2lat(ty, z), tile2lng(tx, z));
        const b = toLocal(tile2lat(ty + 1, z), tile2lng(tx + 1, z));
        const w = b.x - a.x, h = b.z - a.z;
        const mat = new THREE.MeshStandardMaterial({ color: 0x9a9480, roughness: 1, metalness: 0 });
        const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h).rotateX(-Math.PI / 2), mat);
        m.position.set(a.x + w / 2, y, a.z + h / 2);
        m.receiveShadow = true;
        this.group.add(m);
        this.loader.load(TILE_URL(z, tx, ty), (tex) => {
          tex.colorSpace = THREE.SRGBColorSpace;
          tex.anisotropy = this.anisotropy;
          mat.map = tex;
          mat.color.set(0xffffff);
          mat.needsUpdate = true;
          this.loaded++;
        }, undefined, () => { this.failed++; });
      }
    }
  }
}
