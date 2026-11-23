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
