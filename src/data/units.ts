import { SITE, PLANS, PROJECT, type Dir, type FlatDef, type BlockDef } from './project';

export type Status = 'available' | 'hold' | 'sold';
export interface Unit {
  id: string; tower: string; floor: number; no: string; type: 'A' | 'B' | 'C';
  block: BlockDef; flat: FlatDef; status: Status; roomArea: number; roomAreaM2: number;
  facing: Dir; tag: string; heightM: number;
}

export const DIR_NAME: Record<Dir, string> = { N: 'North', S: 'South', E: 'East', W: 'West' };
export const DIR_VEC: Record<Dir, [number, number]> = { N: [0, 1], S: [0, -1], E: [1, 0], W: [-1, 0] };

/** Sum of the brochure's printed room dimensions (sq ft). */
export function roomArea(type: 'A' | 'B' | 'C') {
  return PLANS[type].rooms.reduce((s, r) => s + (r.ft ? r.ft[0] * r.ft[1] : 0), 0);
}

// deterministic demo inventory (replace with live data: see README "Inventory")
function hash(s: string) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return ((h >>> 0) % 10000) / 10000;
}
export const STATUS_OVERRIDES: Record<string, Status> = {
  // 'D-703': 'sold',
};

function statusFor(id: string, floor: number): Status {
  if (STATUS_OVERRIDES[id]) return STATUS_OVERRIDES[id];
  if (!PROJECT.commercial.demoInventory) return 'available';
  const r = hash(id);
  const soldBias = floor < 5 ? 0.42 : floor < 10 ? 0.3 : 0.18;
  return r < soldBias ? 'sold' : r < soldBias + 0.08 ? 'hold' : 'available';
}

export const UNITS: Unit[] = [];
for (const block of SITE.blocks) {
  for (const flat of block.flats) {
    for (let floor = 1; floor <= SITE.floors; floor++) {
      const id = `${flat.tower}-${floor}${flat.no.slice(1)}`;
      const ra = roomArea(flat.type);
      UNITS.push({
        id, tower: flat.tower, floor, no: flat.no, type: flat.type, block, flat,
        status: statusFor(id, floor), roomArea: Math.round(ra), roomAreaM2: +(ra * 0.092903).toFixed(1),
        facing: flat.face, tag: flat.tag, heightM: SITE.groundH + (floor - 1) * SITE.floorH,
      });
    }
  }
}
// floor lists read 1401, 1402, 1403, 1404 like the brochure's typical layout plan
UNITS.sort((a, b) => a.tower.localeCompare(b.tower) || a.floor - b.floor || a.no.localeCompare(b.no));
export const UNIT_BY_ID = new Map(UNITS.map((u) => [u.id, u]));
export const TOWERS = ['A', 'B', 'C', 'D', 'E', 'F'];
export const blockOfTower = (t: string) => SITE.blocks.find((b) => b.towers.includes(t))!;
export const unitsOf = (tower: string, floor?: number) => UNITS.filter((u) => u.tower === tower && (floor == null || u.floor === floor));
