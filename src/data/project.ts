// Project facts transcribed from the Vraj Platinum brochure (Vraj Group, Surat).
import siteJson from './site.json';
import plansJson from './plans.json';
import propsJson from './props.json';

export type Dir = 'N' | 'S' | 'E' | 'W';
export interface FlatDef { tower: string; no: string; type: 'A' | 'B' | 'C'; rect: number[]; face: Dir; views: { dir: Dir; label: string }[]; tag: string }
export interface BlockDef { id: string; kind: 'square' | 'long'; towers: string[]; rect: number[]; core: number[]; flats: FlatDef[] }
export interface RoomDef { id: string; name: string; kind: string; dim?: string; ft?: number[]; r: number[] }
export interface PlanDef { label: string; buildings: string[]; mpp: number; rooms: RoomDef[] }

export const SITE = siteJson as unknown as {
  geo: { lat: number; lng: number; originLat: number; originLng: number; rotationDeg: number };
  groundH: number; floorH: number; floors: number; plot: number[];
  road: { rect: number[]; width: number; name: string };
  garden: number[]; blocks: BlockDef[]; planterFloors: number[]; gate: { x: number; y: number; width: number };
};
export const PLANS = plansJson as unknown as Record<'A' | 'B' | 'C', PlanDef>;
export const PROPS = propsJson as unknown as Record<string, { x: number; y: number; r: number; s: number; c?: string }[]>;

export const PROJECT = {
  name: 'Vraj Platinum',
  developer: 'Vraj Group',
  tagline: '2-BHK Superior Living',
  subline: 'Life within a high-end skyline',
  address: 'Opp. Unity Party Plot, Nr. N.C. Thakar School, Sarthana–Gadhpur Road, Surat, Gujarat',
  addressGu: 'યુનિટી પાર્ટી પ્લોટની સામે, એન.સી. ઠાકર સ્કૂલ પાસે, સરથાણા-ગઢપુર રોડ, સુરત.',
  phone: '+918140770800',
  phoneDisplay: '81407 70800',
  mapsUrl: 'https://www.google.com/maps/search/?api=1&query=21.2318382,72.9136999',
  mapsShort: 'https://goo.gl/maps/is2XXMe5j7LtyRaS9',
  brochure: '/media/Vraj-Platinum-Brochure.pdf',
  team: [
    { role: 'A project by', name: 'Vraj Group' },
    { role: 'Architect', name: 'Aayojan Architect' },
    { role: 'Structure', name: 'Altitude Associates' },
    { role: '3D & walkthrough (brochure)', name: 'Inception Visual Studio' },
  ],
  highlights: [
    'Fully residential community', '2-BHK · 3 types of spacious planning', 'G+14 storeyed · 6 towers',
    'Landscaped garden design', 'Grand foyer area', 'Well-connected prime location', 'Near 300 ft Outer Ring Road',
  ],
  amenities: [
    { icon: 'gate', name: 'Entrance gate' }, { icon: 'shield', name: 'Security cabin' }, { icon: 'cctv', name: '24×7 CCTV' },
    { icon: 'water', name: 'Water body' }, { icon: 'tree', name: 'Landscape garden' }, { icon: 'kids', name: 'Kids play area' },
    { icon: 'gazebo', name: 'Gazebo seating' }, { icon: 'bench', name: 'Senior-citizen seating' }, { icon: 'desk', name: 'Reception' },
    { icon: 'sofa', name: 'Waiting area' }, { icon: 'lift', name: 'Auto-door lifts' }, { icon: 'fire', name: 'Fire safety' },
    { icon: 'bolt', name: 'Power backup generator' }, { icon: 'sun', name: 'Solar for common areas' }, { icon: 'car', name: 'Ground + basement parking' },
  ],
  specsExternal: [
    ['Construction', 'Earthquake-resistant RCC frame structure; double-coat plaster outside, single-coat plaster inside.'],
    ['Security', '24×7 CCTV cameras of a standard brand across the campus.'],
    ['Entry foyer', 'Vitrified flooring, designer false ceiling, reception table & chair and name board.'],
    ['Terrace', 'Waterproofing with china-mosaic finish.'],
    ['Lifts', 'ISI-standard auto-door lifts with safety devices.'],
    ['Colour', 'Rustic texture / colour on the exterior as per design; putty finish on the flat’s inner walls.'],
    ['Parking', 'Ground + basement parking.'],
    ['Generator', 'One auto generator for each building’s common areas.'],
  ],
  specsInternal: [
    ['Flooring', '2 × 4 ft granamite / vitrified tiles in living room, kitchen and bedrooms.'],
    ['Electrical', 'ISI-standard concealed wiring with modular switch boards.'],
    ['Doors', 'Attractive main door with wooden frame; flush doors with granite frames inside.'],
    ['Kitchen', 'Granite platform, S.S. sink, glazed-tile dado up to lintel level.'],
    ['Windows', 'Aluminium section windows with granite frames.'],
    ['Plumbing', 'ISI-standard UPVC & CPVC concealed fittings.'],
    ['Staircase', 'Granite treads in staircases; vitrified tiles in passages.'],
  ],
  nearby: [
    { name: 'Unity Party Plot', note: 'Directly opposite', cat: 'Landmark' },
    { name: 'N.C. Thakar School', note: 'Next to the site', cat: 'Education' },
    { name: '100 ft Road (Sarthana–Gadhpur)', note: 'Site frontage', cat: 'Connectivity' },
    { name: '300 ft Outer Ring Road & Ring Road Chokdi', note: 'Close by, east', cat: 'Connectivity' },
    { name: 'Gadhpur–Kathodara Road', note: 'North of the site', cat: 'Connectivity' },
    { name: 'Mangiba Cricket Ground', note: 'North-east', cat: 'Leisure' },
    { name: 'Dreamland & Sagwadi', note: 'North', cat: 'Leisure' },
    { name: 'Shyamdham Mandir & Chokdi', note: 'Surat–Kamrej Highway', cat: 'Landmark' },
    { name: 'Sarthana Nature Park', note: 'West', cat: 'Leisure' },
    { name: 'D-Mart, Avadh Mall', note: 'Sarthana', cat: 'Shopping' },
    { name: 'SMC Garden, Sarthana Police Station', note: 'South-west', cat: 'Civic' },
    { name: 'Surat–Kamrej Highway (NH 48)', note: 'North-west', cat: 'Connectivity' },
    { name: 'Tapi River', note: 'North-west', cat: 'Landmark' },
  ],
  // Developer-editable commercial settings ----------------------------------------------
  commercial: {
    // Indicative only — replace with the developer's live price list before publishing.
    defaultAgreementLakh: 34,
    underConstruction: true,
    demoInventory: true,
  },
};

export const GALLERY = [
  { src: '/img/night.jpg', title: 'Twin towers at dusk', cat: 'Exterior' },
  { src: '/img/entrance.jpg', title: 'Grand entrance on the 100 ft road', cat: 'Exterior' },
  { src: '/img/exterior-day.jpg', title: 'Enter a world like no other', cat: 'Exterior' },
  { src: '/img/garden-aerial.jpg', title: 'Central landscaped garden', cat: 'Amenities' },
  { src: '/img/balcony-render.jpg', title: 'A view that soothes your soul', cat: 'Lifestyle' },
  { src: '/img/lobby.jpg', title: 'Grand foyer & reception', cat: 'Amenities' },
  { src: '/img/water-feature.jpg', title: 'Water body & fountains', cat: 'Amenities' },
  { src: '/img/pathway.jpg', title: 'Landscaped pathways', cat: 'Amenities' },
  { src: '/img/tower-day.jpg', title: 'Garden-side elevation', cat: 'Exterior' },
  { src: '/img/twin-towers.jpg', title: 'Front elevation', cat: 'Exterior' },
  { src: '/img/aerial-top.jpg', title: 'Aerial view with rooftop solar', cat: 'Exterior' },
  { src: '/img/campus-model.jpg', title: 'Campus massing model', cat: 'Plans' },
  { src: '/img/layout.jpg', title: 'Typical layout plan', cat: 'Plans' },
  { src: '/img/iso-a.jpg', title: 'Type A · isometric', cat: 'Plans' },
  { src: '/img/iso-b.jpg', title: 'Type B · isometric', cat: 'Plans' },
];

export const SAMPLE_FLAT = {
  video: '/media/sample-flat.mp4',
  poster: '/media/sample-flat-poster.jpg',
  stills: [1, 2, 3, 4, 5, 6, 7, 8].map((i) => `/img/sample-${i}.jpg`),
};

export const PLAN_IMG: Record<string, string> = { A: '/img/plan-a.jpg', B: '/img/plan-b.jpg', C: '/img/plan-c.jpg' };
export const ISO_IMG: Record<string, string> = { A: '/img/iso-a.jpg', B: '/img/iso-b.jpg', C: '/img/iso-b.jpg' };
