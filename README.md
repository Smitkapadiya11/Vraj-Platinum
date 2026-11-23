# Vraj Platinum · 3D Residence Explorer

Interactive 3D sales experience for **Vraj Platinum** (Vraj Group) — six G+14 towers, 336 2-BHK homes on the
100 ft Sarthana–Gadhpur Road, Surat. Built by **PinYourSite · Kapadiya & Sons**.

**Stack:** Blender 5 (Python/bpy, Cycles light-baking) → glTF/GLB (meshopt + WebP) → **TypeScript + Three.js (WebGL 2)**,
GSAP for camera choreography, **Vite** build, deployed as a static site on **Vercel** (no server needed).

## What's inside

| Feature | Notes |
|---|---|
| Real-location campus | Plot placed at the Google-Maps pin (21.2318 N, 72.9137 E, origin 43 m west of the gate), streamed Esri satellite ground, 177 real neighbouring buildings from OpenStreetMap with real storey counts |
| 6 towers from the brochure layout | A/B (Type A), C–F (Type B ends, Type C middle), G+14, rooftop solar, creeper planters, signage, gate, 30 m road |
| Tower → floor → unit | Floor slicing with a ghost volume above, colour-coded availability plates, labels, hover & tap picking |
| Balcony view for every flat | First-person camera on the actual balcony at the real height and facing, drag to look, pinch/scroll zoom, floor ▲▼ hopping, compass heading |
| Furnished 3D interiors | Type A/B/C modelled from the brochure plans, furnished in the palette of the real sample flat, light baked in Cycles |
| Real sun & time | NOAA solar position for Surat; time slider; day/night with lit windows, lamps and bloom |
| Unit card | Room area (from brochure dims), facing, height, plan image, WhatsApp enquiry, shortlist, share deep-link |
| Cost & EMI | Gujarat stamp duty 4.9 %, registration 1 % (waived for sole woman buyer), GST 1 %/5 %/nil, EMI |
| Find your home | Filter by tower, type, view, floor band, availability |
| Sample flat | Actual walkthrough video + stills |
| Gallery, location, specs | Brochure renders, landmarks, Gujarati specifications translated |
| EN / ગુજરાતી / हिन्दी | UI language switch |
| Mobile + desktop | Bottom sheets & compact controls on phones, adaptive resolution |

## Before going live (developer data)

* **Inventory** — availability is a *demo* pattern. Set `PROJECT.commercial.demoInventory = false` in
  `src/data/project.ts` and list real statuses in `STATUS_OVERRIDES` (`src/data/units.ts`), e.g. `'D-703': 'sold'`.
* **Prices** — the cost calculator starts from an example agreement value (`defaultAgreementLakh`). Replace with the price list.
* **Areas** — "room area" is the sum of the brochure's printed room sizes; add RERA carpet / super built-up if supplied.

## Rebuilding the 3D assets

```bash
pip install bpy==5.3.0            # Blender as a Python module (or run with `blender -b -P`)
python3 blender/gen_site_data.py  # layout → src/data/site.json
python3 blender/towers.py         # tower floor/ground/roof/planter modules
python3 blender/site.py           # campus landscape + props (palms, trees, cars, lamps)
python3 blender/interiors.py A --res 2048 --samples 40   # also B and C (Cycles bake, ~7 min each on 2 cores)
npm run models                    # meshopt + WebP compression → public/models
npm run dev
```

## Credits
Renders, plans, logo and brochure © Vraj Group. Ground imagery © Esri, Maxar, Earthstar Geographics.
Building footprints © OpenStreetMap contributors (ODbL). Experience by PinYourSite · Kapadiya & Sons.
