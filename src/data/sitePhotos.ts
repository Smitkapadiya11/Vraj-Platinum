// Actual photographs & clips taken at Vraj Platinum on 23 Nov 2026 (supplied by the developer's team).
import type { Dir } from './project';

export type PhotoSet = 'east-high' | 'campus-high' | 'northwest-high' | 'e-high' | 'garden-low' | 'garden-ground' | 'entrance';
export interface SitePhoto { id: string; set: PhotoSet; video?: boolean }

const ids = (set: PhotoSet, list: string[], video = false) => list.map((id) => ({ id, set, video }));
export const SITE_PHOTOS: SitePhoto[] = [
  ...ids('east-high', ['162350912', '162353359', '162356623', '164341812', '164345283', '164350281', '164358457']),
  ...ids('east-high', ['v162359770'], true),
  ...ids('campus-high', ['162021732', '162132917', '162212319', '162215852']),
  ...ids('campus-high', ['v162225096'], true),
  ...ids('northwest-high', ['162142362']),
  ...ids('e-high', ['163453891']),
  ...ids('e-high', ['v163457900'], true),
  ...ids('garden-low', ['163129595', '163134291', '163139928']),
  ...ids('garden-low', ['v163117795'], true),
  ...ids('garden-ground', ['163757637', '163815763', '163819932', '163823613', '163833537', '163838213', '163842093', '163845322']),
  ...ids('entrance', ['164550035', '164552954', '164556602', '164615648', '164618687', '164625562']),
];

export const SET_INFO: Record<PhotoSet, { en: string; gu: string; hi: string }> = {
  'east-high': { en: 'Upper floor (14th), Towers A/B, facing east: 100 ft road, Unity Party Plot, open land', gu: 'ઉપરનો માળ (14મો), ટાવર A/B, પૂર્વ તરફ: 100 ફૂટ રોડ, યુનિટી પાર્ટી પ્લોટ', hi: 'ऊपरी मंज़िल (14वीं), टावर A/B, पूर्व की ओर: 100 फुट रोड, यूनिटी पार्टी प्लॉट' },
  'campus-high': { en: 'Upper floor, Towers A/B, facing west across the campus towers', gu: 'ઉપરનો માળ, ટાવર A/B, પશ્ચિમ તરફ કેમ્પસ ટાવર્સ', hi: 'ऊपरी मंज़िल, टावर A/B, पश्चिम की ओर कैंपस टावर' },
  'northwest-high': { en: 'Upper floor, looking north-west to the Sarthana skyline', gu: 'ઉપરનો માળ, ઉત્તર-પશ્ચિમ તરફ સરથાણા સ્કાયલાઇન', hi: 'ऊपरी मंज़िल, उत्तर-पश्चिम सरथाणा स्काईलाइन' },
  'e-high': { en: 'Upper floor, Tower E, over the central garden', gu: 'ઉપરનો માળ, ટાવર E, સેન્ટ્રલ ગાર્ડન તરફ', hi: 'ऊपरी मंज़िल, टावर E, सेंट्रल गार्डन की ओर' },
  'garden-low': { en: '1st floor, Tower E, garden view', gu: '1લો માળ, ટાવર E, ગાર્ડન વ્યૂ', hi: '1ली मंज़िल, टावर E, गार्डन व्यू' },
  'garden-ground': { en: 'Central garden & elevations from ground level', gu: 'જમીન પરથી સેન્ટ્રલ ગાર્ડન અને એલિવેશન', hi: 'ज़मीन से सेंट्रल गार्डन और एलिवेशन' },
  'entrance': { en: 'Entrance, gates & front elevation on the 100 ft road', gu: 'પ્રવેશદ્વાર, ગેટ અને 100 ફૂટ રોડ પરનું ફ્રન્ટ એલિવેશન', hi: 'प्रवेश द्वार, गेट और 100 फुट रोड पर फ्रंट एलिवेशन' },
};

export const photoSrc = (p: SitePhoto, thumb = false) =>
  p.video ? (thumb ? `/site/${p.id}_p.jpg` : `/site/${p.id}.mp4`) : `/site/${p.id}${thumb ? '_t' : ''}.jpg`;

/** Which real photos best match a balcony view (tower, floor, direction). */
export function photosForView(tower: string, floor: number, dir: Dir, gardenFacing: boolean): SitePhoto[] {
  const high = floor >= 8;
  const pick = (s: PhotoSet) => SITE_PHOTOS.filter((p) => p.set === s);
  if ((tower === 'A' || tower === 'B') && dir === 'E') return high ? pick('east-high') : [...pick('entrance'), ...pick('east-high')];
  if ((tower === 'A' || tower === 'B') && dir === 'W') return high ? pick('campus-high') : pick('garden-ground');
  if (gardenFacing) return high ? [...pick('e-high'), ...pick('campus-high')] : [...pick('garden-low'), ...pick('garden-ground')];
  if (dir === 'W' || dir === 'N') return high ? pick('northwest-high') : [];
  if (dir === 'E') return high ? pick('east-high') : [];
  return [];
}

// ---------------------------------------------------------------- real balcony views (stitched from the site clips)
export interface RealSrc { src: string; thumb: string; kind: 'pano' | 'photo'; capFloor: number; capTower: string; set: PhotoSet; nearest?: boolean }
const pano = (id: string, set: PhotoSet, capFloor: number, capTower: string): RealSrc => ({ src: `/site/pano/${id}.jpg`, thumb: `/site/pano/${id}_t.jpg`, kind: 'pano', capFloor, capTower, set });
const photo = (id: string, set: PhotoSet, capFloor: number, capTower: string): RealSrc => ({ src: `/site/${id}.jpg`, thumb: `/site/${id}_t.jpg`, kind: 'photo', capFloor, capTower, set });

const EAST_HIGH = [pano('162359770', 'east-high', 14, 'A/B'), pano('164327625', 'east-high', 14, 'A/B'), pano('162414116', 'east-high', 14, 'A/B'),
  pano('162422290', 'east-high', 14, 'A/B'), photo('162353359', 'east-high', 14, 'A/B'), photo('164350281', 'east-high', 14, 'A/B')];
const CAMPUS_HIGH = [pano('162026208', 'campus-high', 14, 'A/B'), photo('162212319', 'campus-high', 14, 'A/B'), photo('162215852', 'campus-high', 14, 'A/B'),
  photo('162021732', 'campus-high', 14, 'A/B'), photo('162132917', 'campus-high', 14, 'A/B')];
const E_HIGH = [photo('163453891', 'e-high', 14, 'E')];
const GARDEN_LOW = [pano('163117795', 'garden-low', 1, 'E'), photo('163134291', 'garden-low', 1, 'E'), photo('163129595', 'garden-low', 1, 'E'), photo('163139928', 'garden-low', 1, 'E')];
const GARDEN_GROUND = ['163815763', '163845322', '163842093', '163819932'].map((i) => photo(i, 'garden-ground', 0, 'garden'));
const ENTRANCE = ['164625562', '164552954', '164556602'].map((i) => photo(i, 'entrance', 0, 'A/B'));
const NW_HIGH = [photo('162142362', 'northwest-high', 14, 'A/B')];
const near = (l: RealSrc[]) => l.map((r) => ({ ...r, nearest: true }));

/** Real captured views for a flat's balcony; `nearest` marks views from a different side/tower shown for reference. */
export function realViewsFor(tower: string, floor: number, dir: Dir, gardenFacing: boolean): RealSrc[] {
  const front = tower === 'A' || tower === 'B';
  const high = floor >= 5;
  if (front && dir === 'E') return high ? EAST_HIGH : [...EAST_HIGH, ...ENTRANCE];
  if (front && dir === 'W') return high ? CAMPUS_HIGH : [...GARDEN_GROUND, ...CAMPUS_HIGH];
  if (front) return near(high ? EAST_HIGH : ENTRANCE);
  if (gardenFacing) return high ? [...E_HIGH, ...GARDEN_LOW, ...near(CAMPUS_HIGH)] : [...GARDEN_LOW, ...GARDEN_GROUND];
  if (dir === 'W' || dir === 'N') return near(high ? NW_HIGH : GARDEN_GROUND);
  return near(high ? CAMPUS_HIGH : GARDEN_GROUND);
}
