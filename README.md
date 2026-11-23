# Vraj Platinum · 3D Residence Explorer

Interactive 3D sales experience for **Vraj Platinum** (Vraj Group) — six G+14 towers, 336 2-BHK homes on the
100 ft Sarthana–Gadhpur Road, Surat. Built by **PinYourSite · Kapadiya & Sons**.

**Stack:** Blender 5 (Python/bpy, Cycles light-baking) → glTF/GLB (meshopt + WebP) → **TypeScript + Three.js (WebGL 2)**,
GSAP for camera choreography, **Vite** build, deployed as a static site on **Vercel** (no server needed).

## What's inside

| Feature | Notes |
|---|---|
| Real-location campus | Plot placed at the Google-Maps pin (21.2318 N, 72.9137 E, origin 43 m west of the gate), streamed Esri satellite ground, 177 real neighbouring buildings from OpenStreetMap with real storey counts |
| 6 towers matched to the real buildings | Re-modelled from the 23 Nov 2026 site photos: charcoal sand-finish piers, white textured walls, bronze strips, cantilevered balconies (MS-bar / glass railings), stilt ground floor, rooftop steel solar canopy, stone & bronze entrance signage, wooden slat gates, guard cabin, black steel garden portal |
| Photo-derived textures | `scripts/make_textures.py` builds tileable textures from the site photos; Blender exports world-metre UVs so they sit at real scale |
| Real balcony view (touch & look around) | Panoramas stitched (OpenCV) from the developer's 23 Nov 2026 clips — 14th-floor east (road / Unity Party Plot), 14th-floor west (campus), 1st-floor garden — wrapped at true angular width; drag, pinch or move the phone. Every flat gets its matching capture (or the nearest one, labelled) with a note on capture floor vs. the flat's floor, plus a toggle to the 3D view at the exact floor |
| Real site photos | 30 photos + 4 clips in a "Site today" gallery; the balcony view shows the matching real photos for that side & height |
| Drone tour | Captioned cinematic flight: aerial, entrance, front towers, garden fly-through, rooftop solar, neighbourhood |
| Sunlight hours | Direct sun on each balcony today / 21 June / 21 Dec, ray-traced against the towers and neighbouring buildings |
| Tower → floor → unit | Floor slicing with a ghost volume above, colour-coded availability plates, labels, hover & tap picking |
| Balcony view for every flat | First-person camera on the actual balcony at the real height and facing, drag to look, pinch/scroll zoom, floor ▲▼ hopping, compass heading |
| Furnished 3D interiors | Type A/B/C modelled from the brochure plans, furnished in the palette of the real sample flat, light baked in Cycles |
| Real sun & time | NOAA solar position for Surat; time slider; day/night with lit windows, lamps and bloom |
| Unit card | Room area (from brochure dims), facing, height, plan image, WhatsApp enquiry, shortlist, share deep-link |
| Cost & EMI | Gujarat stamp duty 4.9 %, registration 1 % (waived for sole woman buyer), GST 1 %/5 %/nil, EMI |
| Find your home | Filter by tower, type, view, floor band, availability |
| Sample flat | Actual walkthrough video + stills |
| Gallery, location, specs | Brochure renders, landmarks, Gujarati specifications translated |
| EN / ગુજરાતી / हिन्दी | UI and all project content (specs, amenities, highlights, nearby, rooms, views, tour) |
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
