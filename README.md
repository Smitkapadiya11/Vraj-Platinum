# Vraj Platinum · 3D Residence Explorer

Interactive 3D sales experience for **Vraj Platinum** (Vraj Group) — six G+14 towers, 336 2-BHK homes on the
100 ft Sarthana–Gadhpur Road, Surat. Built by **PinYourSite · Kapadiya & Sons**.

**Stack:** Blender 5 (Python/bpy, Cycles light-baking) → glTF/GLB (meshopt + WebP) → **TypeScript + Three.js (WebGL 2)**,
GSAP for camera choreography, **Vite** build, deployed as a static site on **Vercel** (no server needed).

## What's inside

| Feature | Notes |
|---|---|
| Customer guide | 4 simple steps on first visit (drone tour → pick your home → real balcony view → WhatsApp), reopen from the ? button |
| Mobile-first navigation | One bottom tab bar: Explore · Drone · Balcony · Homes · More; WhatsApp in the header; day/night & reset as floating buttons |
| Real-location presentation map | Crisp vector map baked from OpenStreetMap (roads, creek, land use, 720 buildings) + land cover classified from satellite imagery; turf grounds across the 30 m road from the 2026 Google Earth reference |
| Neighbourhood as an architect's white model | Real footprints and storey counts, procedural window grid, rooftop solar, ~4000 instanced trees (mangroves along the creek) |
| 6 towers | Clean vector materials in the real site colours: charcoal piers, white bands, wood strips, glass/bar railings, stilts, solar canopy, stone & bronze entrance |
| Drone tour | One continuous spline flight (~1 min): aerial → road & entrance → through the gap between A and B → over the garden → solar roofs → neighbourhood orbit; captions in 3 languages |
| Real balcony view | The real 14th-floor road-side panorama from Tower A/B (23 Nov 2026); the drone glides to the balcony, then drag, pinch or move the phone to look around |
| Tower → floor → flat | Floor slicing, colour-coded availability, flat card with plan, size, facing, height |
| Furnished 3D interiors | Type A/B/C from the brochure plans, sample-flat palette, light baked in Cycles |
| Cost & EMI | Gujarat stamp duty 4.9 %, registration 1 % (waived for sole woman buyer), GST 1 %/5 %/nil, EMI |
| Homes finder, sample flat, gallery, location, specs | In the Homes tab and the More sheet |
| EN / ગુજરાતી / हिन्दी | All UI and project content |

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
