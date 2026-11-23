// Trilingual project content (English · ગુજરાતી · हिन्दी). Gujarati specifications follow the original brochure wording.
import { getLang } from '../ui/i18n';

export type T3 = { en: string; gu: string; hi: string };
export const L = (t: T3 | string) => (typeof t === 'string' ? t : t[getLang()] || t.en);

export const DIR3: Record<string, T3> = {
  N: { en: 'North', gu: 'ઉત્તર', hi: 'उत्तर' },
  S: { en: 'South', gu: 'દક્ષિણ', hi: 'दक्षिण' },
  E: { en: 'East', gu: 'પૂર્વ', hi: 'पूर्व' },
  W: { en: 'West', gu: 'પશ્ચિમ', hi: 'पश्चिम' },
};
export const TAG3: Record<string, T3> = {
  'Road facing': { en: 'Road facing', gu: 'રોડ ફેસિંગ', hi: 'रोड फेसिंग' },
  'Garden & campus facing': { en: 'Garden & campus facing', gu: 'ગાર્ડન અને કેમ્પસ ફેસિંગ', hi: 'गार्डन और कैंपस फेसिंग' },
  'Garden facing': { en: 'Garden facing', gu: 'ગાર્ડન ફેસિંગ', hi: 'गार्डन फेसिंग' },
  'Open side facing': { en: 'Open side facing', gu: 'ખુલ્લી બાજુ ફેસિંગ', hi: 'खुली तरफ़ फेसिंग' },
};
export const VIEW3: Record<string, T3> = {
  'Living & balcony': { en: 'Living & balcony', gu: 'લિવિંગ અને બાલ્કની', hi: 'लिविंग और बालकनी' },
  'Bedroom side': { en: 'Bedroom side', gu: 'બેડરૂમ બાજુ', hi: 'बेडरूम की तरफ़' },
  'Living room': { en: 'Living room', gu: 'લિવિંગ રૂમ', hi: 'लिविंग रूम' },
  'Bedroom balcony': { en: 'Bedroom balcony', gu: 'બેડરૂમ બાલ્કની', hi: 'बेडरूम बालकनी' },
};
export const ROOM3: Record<string, T3> = {
  'Living Room': { en: 'Living Room', gu: 'લિવિંગ રૂમ', hi: 'लिविंग रूम' },
  'Kitchen / Dining': { en: 'Kitchen / Dining', gu: 'કિચન / ડાઇનિંગ', hi: 'किचन / डाइनिंग' },
  'Bedroom 1': { en: 'Bedroom 1', gu: 'બેડરૂમ 1', hi: 'बेडरूम 1' },
  'Bedroom 2': { en: 'Bedroom 2', gu: 'બેડરૂમ 2', hi: 'बेडरूम 2' },
  'Master Bedroom': { en: 'Master Bedroom', gu: 'માસ્ટર બેડરૂમ', hi: 'मास्टर बेडरूम' },
  'Common Toilet': { en: 'Common Toilet', gu: 'કોમન ટોઇલેટ', hi: 'कॉमन टॉयलेट' },
  'Attached Toilet': { en: 'Attached Toilet', gu: 'એટેચ્ડ ટોઇલેટ', hi: 'अटैच्ड टॉयलेट' },
  Wash: { en: 'Wash', gu: 'વોશ', hi: 'वॉश' },
  Balcony: { en: 'Balcony', gu: 'બાલ્કની', hi: 'बालकनी' },
  Passage: { en: 'Passage', gu: 'પેસેજ', hi: 'पैसेज' },
  Chokdi: { en: 'Chokdi', gu: 'ચોકડી', hi: 'चौकड़ी' },
  'Flower Bed': { en: 'Flower Bed', gu: 'ફ્લાવર બેડ', hi: 'फ्लावर बेड' },
};
export const room = (n: string) => L(ROOM3[n] || n);

export const ABOUT: T3 = {
  en: 'Vraj Platinum is a fully residential community of six G+14 towers by Vraj Group on the 100 ft Sarthana–Gadhpur Road, Surat — 336 two-bedroom homes in three plan types, wrapped around a landscaped central garden, with ground + basement parking and rooftop solar for the common areas.',
  gu: 'વ્રજ પ્લેટિનમ એ વ્રજ ગ્રુપનો સંપૂર્ણ રહેણાંક પ્રોજેક્ટ છે — સરથાણા-ગઢપુર 100 ફૂટ રોડ, સુરત પર G+14 માળના 6 ટાવર, 3 પ્રકારના પ્લાનિંગમાં 336 બે બેડરૂમના ઘર, લેન્ડસ્કેપ સેન્ટ્રલ ગાર્ડન, ગ્રાઉન્ડ + બેઝમેન્ટ પાર્કિંગ અને કોમન એરિયા માટે રૂફટોપ સોલાર.',
  hi: 'व्रज प्लैटिनम, व्रज ग्रुप का पूर्णतः आवासीय प्रोजेक्ट है — सरथाणा-गढ़पुर 100 फुट रोड, सूरत पर G+14 मंज़िल के 6 टावर, 3 प्रकार की प्लानिंग में 336 दो-बेडरूम घर, लैंडस्केप सेंट्रल गार्डन, ग्राउंड + बेसमेंट पार्किंग और कॉमन एरिया के लिए रूफटॉप सोलर।',
};

export const HIGHLIGHTS3: T3[] = [
  { en: 'Fully residential community', gu: 'સંપૂર્ણ રહેણાંક પ્રોજેક્ટ', hi: 'पूर्णतः आवासीय प्रोजेक्ट' },
  { en: '2-BHK · 3 types of spacious planning', gu: '2-BHK · 3 પ્રકારનું વિશાળ પ્લાનિંગ', hi: '2-BHK · 3 प्रकार की विशाल प्लानिंग' },
  { en: 'G+14 storeyed · 6 towers', gu: 'G+14 માળ · 6 ટાવર', hi: 'G+14 मंज़िल · 6 टावर' },
  { en: 'Landscaped garden design', gu: 'લેન્ડસ્કેપ ગાર્ડન ડિઝાઇન', hi: 'लैंडस्केप गार्डन डिज़ाइन' },
  { en: 'Grand foyer area', gu: 'ભવ્ય ફોયર એરિયા', hi: 'भव्य फ़ोयर एरिया' },
  { en: 'Well-connected prime location', gu: 'સારી કનેક્ટિવિટી ધરાવતું પ્રાઇમ લોકેશન', hi: 'बेहतरीन कनेक्टिविटी वाला प्राइम लोकेशन' },
  { en: 'Near 300 ft Outer Ring Road', gu: '300 ફૂટ આઉટર રિંગ રોડ પાસે', hi: '300 फुट आउटर रिंग रोड के पास' },
];

export const AMENITIES3: { icon: string; t: T3 }[] = [
  { icon: 'gate', t: { en: 'Entrance gate', gu: 'એન્ટ્રન્સ ગેટ', hi: 'एंट्रेंस गेट' } },
  { icon: 'shield', t: { en: 'Security cabin', gu: 'સિક્યુરિટી કેબિન', hi: 'सिक्योरिटी केबिन' } },
  { icon: 'cctv', t: { en: '24×7 CCTV', gu: '24×7 CCTV', hi: '24×7 CCTV' } },
  { icon: 'water', t: { en: 'Water body', gu: 'વોટર બોડી', hi: 'वॉटर बॉडी' } },
  { icon: 'tree', t: { en: 'Landscape garden', gu: 'લેન્ડસ્કેપ ગાર્ડન', hi: 'लैंडस्केप गार्डन' } },
  { icon: 'kids', t: { en: 'Kids play area', gu: 'બાળકો માટે રમતનું મેદાન', hi: 'बच्चों का प्ले एरिया' } },
  { icon: 'gazebo', t: { en: 'Gazebo seating', gu: 'ગાઝેબો બેઠક', hi: 'गज़ेबो सीटिंग' } },
  { icon: 'bench', t: { en: 'Senior-citizen seating', gu: 'સિનિયર સિટીઝન બેઠક', hi: 'वरिष्ठ नागरिक सीटिंग' } },
  { icon: 'desk', t: { en: 'Reception', gu: 'રિસેપ્શન', hi: 'रिसेप्शन' } },
  { icon: 'sofa', t: { en: 'Waiting area', gu: 'વેઇટિંગ એરિયા', hi: 'वेटिंग एरिया' } },
  { icon: 'lift', t: { en: 'Auto-door lifts', gu: 'ઓટો ડોર લિફ્ટ', hi: 'ऑटो-डोर लिफ़्ट' } },
  { icon: 'fire', t: { en: 'Fire safety', gu: 'ફાયર સેફ્ટી', hi: 'फ़ायर सेफ़्टी' } },
  { icon: 'bolt', t: { en: 'Power backup generator', gu: 'પાવર બેકઅપ જનરેટર', hi: 'पावर बैकअप जनरेटर' } },
  { icon: 'sun', t: { en: 'Rooftop solar for common areas', gu: 'કોમન એરિયા માટે સોલાર', hi: 'कॉमन एरिया के लिए सोलर' } },
  { icon: 'car', t: { en: 'Ground + basement parking', gu: 'ગ્રાઉન્ડ + બેઝમેન્ટ પાર્કિંગ', hi: 'ग्राउंड + बेसमेंट पार्किंग' } },
];

export const SPECS_EXT3: [T3, T3][] = [
  [{ en: 'Construction', gu: 'કન્સ્ટ્રક્શન', hi: 'निर्माण' }, { en: 'Earthquake-resistant RCC frame structure; double-coat plaster outside, single-coat plaster inside.', gu: 'ભૂકંપપ્રૂફ RCC સ્ટ્રક્ચર, બિલ્ડિંગની બહાર ડબલ કોટ પ્લાસ્ટર અને અંદર સિંગલ કોટ પ્લાસ્ટર.', hi: 'भूकंपरोधी RCC फ्रेम संरचना; बाहर डबल-कोट प्लास्टर, अंदर सिंगल-कोट प्लास्टर।' }],
  [{ en: 'Security', gu: 'સિક્યુરિટી', hi: 'सुरक्षा' }, { en: '24×7 CCTV cameras of a standard brand across the campus.', gu: 'કેમ્પસમાં સ્ટાન્ડર્ડ કંપનીના 24×7 CCTV કેમેરા.', hi: 'पूरे कैंपस में स्टैंडर्ड ब्रांड के 24×7 CCTV कैमरे।' }],
  [{ en: 'Entry foyer', gu: 'એન્ટ્રી ફોયર', hi: 'एंट्री फ़ोयर' }, { en: 'Vitrified flooring, designer false ceiling, reception table & chair and name board.', gu: 'વિટ્રિફાઇડ ફ્લોરિંગ, પ્રોફેશનલ ડિઝાઇન સીલિંગ, રિસેપ્શન ટેબલ-ખુરશી અને નેમ બોર્ડ.', hi: 'विट्रिफ़ाइड फ़्लोरिंग, डिज़ाइनर फ़ॉल्स सीलिंग, रिसेप्शन टेबल-कुर्सी और नेम बोर्ड।' }],
  [{ en: 'Terrace', gu: 'ટેરેસ', hi: 'टैरेस' }, { en: 'Waterproofing with china-mosaic finish.', gu: 'ચાઇના મોઝેક સાથે વોટરપ્રૂફિંગ.', hi: 'चाइना-मोज़ेक फ़िनिश के साथ वॉटरप्रूफ़िंग।' }],
  [{ en: 'Lifts', gu: 'લિફ્ટ', hi: 'लिफ़्ट' }, { en: 'ISI-standard auto-door lifts with safety devices.', gu: 'સેફ્ટી ડિવાઇસ સાથે ISI સ્ટાન્ડર્ડ કંપનીની ઓટો ડોર લિફ્ટ.', hi: 'सेफ़्टी डिवाइस के साथ ISI-स्टैंडर्ड ऑटो-डोर लिफ़्ट।' }],
  [{ en: 'Colour', gu: 'કલર', hi: 'रंग' }, { en: 'Rustic texture / colour on the exterior as per design; putty finish on the flat’s inner walls.', gu: 'બહારની બાજુ ડિઝાઇન મુજબ રસ્ટિક ટેક્સચર / કલર અને ફ્લેટની અંદરની દીવાલો પર પુટ્ટી ફિનિશ.', hi: 'बाहर डिज़ाइन अनुसार रस्टिक टेक्सचर / रंग; फ़्लैट की अंदरूनी दीवारों पर पुट्टी फ़िनिश।' }],
  [{ en: 'Parking', gu: 'પાર્કિંગ', hi: 'पार्किंग' }, { en: 'Ground + basement parking.', gu: 'ગ્રાઉન્ડ + બેઝમેન્ટ પાર્કિંગ.', hi: 'ग्राउंड + बेसमेंट पार्किंग।' }],
  [{ en: 'Generator', gu: 'જનરેટર', hi: 'जनरेटर' }, { en: 'One auto generator for each building’s common areas.', gu: 'દરેક બિલ્ડિંગના કોમન એરિયા માટે એક ઓટો જનરેટર.', hi: 'हर बिल्डिंग के कॉमन एरिया के लिए एक ऑटो जनरेटर।' }],
];
export const SPECS_INT3: [T3, T3][] = [
  [{ en: 'Flooring', gu: 'ફ્લોરિંગ', hi: 'फ़्लोरिंग' }, { en: '2 × 4 ft granamite / vitrified tiles in living room, kitchen and bedrooms.', gu: 'લિવિંગ રૂમ, કિચન અને બેડરૂમમાં 2 × 4 ગ્રેનામાઇટ / વિટ્રિફાઇડ ટાઇલ્સ.', hi: 'लिविंग रूम, किचन और बेडरूम में 2 × 4 फुट ग्रैनामाइट / विट्रिफ़ाइड टाइल्स।' }],
  [{ en: 'Electrical', gu: 'ઇલેક્ટ્રિક', hi: 'इलेक्ट्रिकल' }, { en: 'ISI-standard concealed wiring with modular switch boards.', gu: 'ISI સ્ટાન્ડર્ડ કન્સીલ્ડ ફિટિંગ અને મોડ્યુલર સ્વિચ બોર્ડ.', hi: 'ISI-स्टैंडर्ड कंसील्ड वायरिंग और मॉड्यूलर स्विच बोर्ड।' }],
  [{ en: 'Doors', gu: 'દરવાજા', hi: 'दरवाज़े' }, { en: 'Attractive main door with wooden frame; flush doors with granite frames inside.', gu: 'લાકડાની ફ્રેમ સાથે આકર્ષક મુખ્ય દરવાજો, અંદર ગ્રેનાઇટ ફ્રેમ સાથે ફ્લશ ડોર.', hi: 'लकड़ी की फ़्रेम वाला आकर्षक मुख्य दरवाज़ा; अंदर ग्रेनाइट फ़्रेम के साथ फ़्लश डोर।' }],
  [{ en: 'Kitchen', gu: 'કિચન', hi: 'किचन' }, { en: 'Granite platform, S.S. sink, glazed-tile dado up to lintel level.', gu: 'ગ્રેનાઇટ પ્લેટફોર્મ, S.S. સિંક, લિન્ટલ લેવલ સુધી ગ્લેઝ ટાઇલ્સ.', hi: 'ग्रेनाइट प्लेटफ़ॉर्म, S.S. सिंक, लिंटल लेवल तक ग्लेज़्ड टाइल्स।' }],
  [{ en: 'Windows', gu: 'બારી', hi: 'खिड़कियाँ' }, { en: 'Aluminium section windows with granite frames.', gu: 'ગ્રેનાઇટ ફ્રેમ સાથે એલ્યુમિનિયમ સેક્શન બારી.', hi: 'ग्रेनाइट फ़्रेम के साथ एल्युमिनियम सेक्शन खिड़कियाँ।' }],
  [{ en: 'Plumbing', gu: 'પ્લમ્બિંગ', hi: 'प्लंबिंग' }, { en: 'ISI-standard UPVC & CPVC concealed fittings.', gu: 'ISI કંપનીની સ્ટાન્ડર્ડ UPVC અને CPVC કન્સીલ્ડ ફિટિંગ.', hi: 'ISI-स्टैंडर्ड UPVC और CPVC कंसील्ड फ़िटिंग।' }],
  [{ en: 'Staircase', gu: 'દાદર', hi: 'सीढ़ियाँ' }, { en: 'Granite treads in staircases; vitrified tiles in passages.', gu: 'દાદરમાં ગ્રેનાઇટ પગથિયાં અને પેસેજમાં વિટ્રિફાઇડ ટાઇલ્સ.', hi: 'सीढ़ियों में ग्रेनाइट, पैसेज में विट्रिफ़ाइड टाइल्स।' }],
];

export const NEARBY3: { t: T3; note: T3 }[] = [
  { t: { en: 'Unity Party Plot', gu: 'યુનિટી પાર્ટી પ્લોટ', hi: 'यूनिटी पार्टी प्लॉट' }, note: { en: 'Directly opposite', gu: 'બરાબર સામે', hi: 'ठीक सामने' } },
  { t: { en: 'N.C. Thakar School', gu: 'એન.સી. ઠાકર સ્કૂલ', hi: 'एन.सी. ठाकर स्कूल' }, note: { en: 'Next to the site', gu: 'સાઇટની બાજુમાં', hi: 'साइट के पास' } },
  { t: { en: '100 ft Sarthana–Gadhpur Road', gu: '100 ફૂટ સરથાણા-ગઢપુર રોડ', hi: '100 फुट सरथाणा-गढ़पुर रोड' }, note: { en: 'Site frontage', gu: 'સાઇટની સામે', hi: 'साइट के सामने' } },
  { t: { en: '300 ft Outer Ring Road & Ring Road Chokdi', gu: '300 ફૂટ આઉટર રિંગ રોડ અને રિંગ રોડ ચોકડી', hi: '300 फुट आउटर रिंग रोड और रिंग रोड चौकड़ी' }, note: { en: 'Close by, east', gu: 'નજીક, પૂર્વમાં', hi: 'पास में, पूर्व' } },
  { t: { en: 'Gadhpur–Kathodara Road', gu: 'ગઢપુર-કઠોદરા રોડ', hi: 'गढ़पुर-कठोदरा रोड' }, note: { en: 'North', gu: 'ઉત્તરમાં', hi: 'उत्तर' } },
  { t: { en: 'Mangiba Cricket Ground', gu: 'માંગીબા ક્રિકેટ ગ્રાઉન્ડ', hi: 'मांगीबा क्रिकेट ग्राउंड' }, note: { en: 'North-east', gu: 'ઉત્તર-પૂર્વ', hi: 'उत्तर-पूर्व' } },
  { t: { en: 'Dreamland & Sagwadi', gu: 'ડ્રીમલેન્ડ અને સાગવાડી', hi: 'ड्रीमलैंड और सागवाड़ी' }, note: { en: 'North', gu: 'ઉત્તર', hi: 'उत्तर' } },
  { t: { en: 'Shyamdham Mandir & Chokdi', gu: 'શ્યામધામ મંદિર અને ચોકડી', hi: 'श्यामधाम मंदिर और चौकड़ी' }, note: { en: 'Surat–Kamrej Highway', gu: 'સુરત-કામરેજ હાઇવે', hi: 'सूरत-कामरेज हाईवे' } },
  { t: { en: 'Sarthana Nature Park', gu: 'સરથાણા નેચર પાર્ક', hi: 'सरथाणा नेचर पार्क' }, note: { en: 'West', gu: 'પશ્ચિમ', hi: 'पश्चिम' } },
  { t: { en: 'D-Mart, Avadh Mall', gu: 'ડી-માર્ટ, અવધ મોલ', hi: 'डी-मार्ट, अवध मॉल' }, note: { en: 'Sarthana', gu: 'સરથાણા', hi: 'सरथाणा' } },
  { t: { en: 'SMC Garden, Sarthana Police Station', gu: 'SMC ગાર્ડન, સરથાણા પોલીસ સ્ટેશન', hi: 'SMC गार्डन, सरथाणा पुलिस स्टेशन' }, note: { en: 'South-west', gu: 'દક્ષિણ-પશ્ચિમ', hi: 'दक्षिण-पश्चिम' } },
  { t: { en: 'Surat–Kamrej Highway (NH 48)', gu: 'સુરત-કામરેજ હાઇવે (NH 48)', hi: 'सूरत-कामरेज हाईवे (NH 48)' }, note: { en: 'North-west', gu: 'ઉત્તર-પશ્ચિમ', hi: 'उत्तर-पश्चिम' } },
  { t: { en: 'Tapi River', gu: 'તાપી નદી', hi: 'तापी नदी' }, note: { en: 'North-west', gu: 'ઉત્તર-પશ્ચિમ', hi: 'उत्तर-पश्चिम' } },
];

export const TOUR3: T3[] = [
  { en: 'Six G+14 towers on the 100 ft Sarthana–Gadhpur Road', gu: '100 ફૂટ સરથાણા-ગઢપુર રોડ પર G+14 માળના 6 ટાવર', hi: '100 फुट सरथाणा-गढ़पुर रोड पर G+14 मंज़िल के 6 टावर' },
  { en: 'Grand entrance with stone & bronze signage and a manned security cabin', gu: 'સ્ટોન અને બ્રોન્ઝ સાઇનેજ સાથે ભવ્ય પ્રવેશદ્વાર અને સિક્યુરિટી કેબિન', hi: 'स्टोन और ब्रॉन्ज़ साइनेज के साथ भव्य प्रवेश द्वार और सिक्योरिटी केबिन' },
  { en: 'Front towers A & B — road-facing homes with glass balconies', gu: 'આગળના ટાવર A અને B — ગ્લાસ બાલ્કની સાથે રોડ ફેસિંગ ઘર', hi: 'सामने के टावर A और B — ग्लास बालकनी वाले रोड-फेसिंग घर' },
  { en: 'The central landscaped garden between towers C–F', gu: 'ટાવર C–F વચ્ચે સેન્ટ્રલ લેન્ડસ્કેપ ગાર્ડન', hi: 'टावर C–F के बीच सेंट्रल लैंडस्केप गार्डन' },
  { en: 'Rooftop solar canopy powering the common areas', gu: 'કોમન એરિયા માટે રૂફટોપ સોલાર કેનોપી', hi: 'कॉमन एरिया के लिए रूफटॉप सोलर कैनोपी' },
  { en: 'Real neighbourhood: Unity Party Plot, open land and the Sarthana skyline', gu: 'વાસ્તવિક આસપાસ: યુનિટી પાર્ટી પ્લોટ, ખુલ્લી જમીન અને સરથાણા સ્કાયલાઇન', hi: 'असली आस-पास: यूनिटी पार्टी प्लॉट, खुली ज़मीन और सरथाणा स्काईलाइन' },
];
