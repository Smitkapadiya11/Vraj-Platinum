import * as THREE from 'three';
import { SITE } from '../data/project';

/**
 * Ground around the real site (21.2318 N, 72.9133 E), local metres (x = East, z = South).
 *
 * Default: a vector-rendered presentation map baked by scripts/build_map.py from OpenStreetMap
 * (© OpenStreetMap contributors) + a land-cover grid classified from satellite imagery —
 * near tile 1.2 km (0.29 m/px desktop, 0.59 m/px mobile), far tile 4.1 km with a haze fade,
 * on a haze-coloured base disk that the fog swallows.
 * Optional: live Esri World Imagery satellite tiles (loaded only when the user switches to them).
 */
const R = 6378137;
const TILE_URL = (z: number, x: number, y: number) =>
  `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`;
const HAZE = '#8f8873';

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

export type GroundMode = 'map' | 'sat';

export class Ground {
  group = new THREE.Group();
  mode: GroundMode = 'map';
  loaded = 0;
  failed = 0;
  private map = new THREE.Group();
  private sat?: THREE.Group;
  private loader = new THREE.TextureLoader();

  constructor(private anisotropy: number, private mobile: boolean) {
    this.loader.setCrossOrigin('anonymous');
    const base = new THREE.Mesh(
      new THREE.CircleGeometry(9000, 64).rotateX(-Math.PI / 2),
      new THREE.MeshStandardMaterial({ color: HAZE, roughness: 1, metalness: 0 }),
    );
    base.position.y = -0.7;
    base.receiveShadow = true;
    this.group.add(base, this.map);
    this.tile(`/map/far_2k.webp?v=${__BUILD__}`, 4096, -0.45, false);
    this.tile(`/map/${mobile ? 'near_2k' : 'near_4k'}.webp?v=${__BUILD__}`, 1200, -0.15, true);
  }

  private tile(url: string, size: number, y: number, shadows: boolean) {
    const mat = new THREE.MeshStandardMaterial({ color: HAZE, roughness: 1, metalness: 0 });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size).rotateX(-Math.PI / 2), mat);
    m.position.y = y;
    m.receiveShadow = shadows;
    this.map.add(m);
    this.loader.load(url, (tex) => {
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.anisotropy = this.anisotropy;
      mat.map = tex; mat.color.set(0xffffff); mat.needsUpdate = true;
      this.loaded++;
    }, undefined, () => { this.failed++; });
  }

  setMode(mode: GroundMode) {
    this.mode = mode;
    if (mode === 'sat' && !this.sat) {
      this.sat = new THREE.Group();
      this.ring(15, this.mobile ? 2 : 3, -0.12);
      this.ring(18, this.mobile ? 3 : 4, -0.1);
      this.group.add(this.sat);
    }
    this.map.visible = mode === 'map';
    if (this.sat) this.sat.visible = mode === 'sat';
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
        m.position.set(a.x + w / 2, y - (z === 15 ? 0.02 : 0), a.z + h / 2);
        m.receiveShadow = true;
        this.sat!.add(m);
        this.loader.load(TILE_URL(z, tx, ty), (tex) => {
          tex.colorSpace = THREE.SRGBColorSpace;
          tex.anisotropy = this.anisotropy;
          mat.map = tex; mat.color.set(0xffffff); mat.needsUpdate = true;
        }, undefined, () => { this.failed++; });
      }
    }
  }
}
