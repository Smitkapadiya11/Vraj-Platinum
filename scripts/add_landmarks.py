"""Real neighbourhood landmarks for the live 3D view (same placements as blender/photoreal/landmarks.py).

Positions come from the 23 Nov 2026 14th-floor balcony photos (Tower B, flat B-1402, road side): azimuth in the
stitched panorama + distance from camera height / angle below the horizon, cross-checked on Google Maps
(BMR Box Cricket, party plot lawns, eucalyptus block, The Future Corner).
  - buildings -> appended to src/data/context.json as [ring(x,z), h, levels, 0, '#rrggbb'] (z = south)
  - small objects (gates, tents, hedges, cricket cage, silos, eucalyptus grove) -> src/data/landmarks.json
Idempotent: records with a colour (5th field) are replaced on every run.
"""
import json, math, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAM = (37.3, -12.8)          # x = east, y = north
CAM_H = 44.15


def at(lon, d):
    a = math.radians(lon)
    return CAM[0] + d * math.cos(a), CAM[1] - d * math.sin(a)


def dist(lat):
    return CAM_H / math.tan(math.radians(-lat))


def facing(x, y):
    return math.atan2(CAM[1] - y, CAM[0] - x) + math.pi / 2


def rect(cx, cy, w, d, rot, ox=0.0):
    c, s = math.cos(rot), math.sin(rot)
    cx, cy = cx + ox * c, cy + ox * s
    ring = []
    for px, py in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        x, y = cx + px * c - py * s, cy + px * s + py * c
        ring += [round(x, 2), round(-y, 2)]      # context z = south
    return ring


B = []   # buildings


def bld(ring, h, col):
    B.append([ring, round(h, 1), max(1, round(h / 3.1)), 0, col])


for lon, d, w, dd in ((-35.0, dist(-17.5) + 10, 26, 18), (-24.0, dist(-15.0) + 10, 24, 18)):   # twin towers
    x, y = at(lon, d)
    bld(rect(x, y, w, dd, facing(x, y)), 45.0, '#E6D6B8')
x, y = at(-19.0, dist(-11.5) + 8)                                                                # under construction
UC = (x, y, facing(x, y))
bld(rect(x, y, 24, 18, UC[2]), 26.0, '#A29D94')
x, y = at(-16.0, dist(-6.6))                                                                     # The Future Corner
r = facing(x, y)
for w, f1 in ((56, 3), (52, 6), (47, 8), (42, 10), (36, 11)):
    bld(rect(x, y, w, 26, r, (56 - w) / 2), f1 * 3.4, '#8E3D2E')
for lon, d in ((-2.2, 520), (1.0, 540)):
    x, y = at(lon, d)
    bld(rect(x, y, 18, 16, facing(x, y)), 40, '#9E6E52')
pal = ['#DCD3C3', '#CFC8BC', '#E4DDD0', '#C9BFAE', '#D8CFBF', '#BDB6AA']
for k, (lon, d, h) in enumerate(((-74, 480, 42), (-69, 470, 44), (-64, 500, 42), (-59, 430, 39), (-54, 470, 45), (-49, 520, 42),
                                 (-44, 560, 40), (-8, 760, 44), (8, 820, 40), (-28, 700, 42))):
    x, y = at(lon, d)
    bld(rect(x, y, 22 + (k % 3) * 4, 16, facing(x, y)), h, pal[k % 6])
random.seed(11)
hp = ['#E6E1D7', '#CFCAC2', '#B9B6B1', '#EDE8DD', '#D7CDBB', '#A9A7A3']
n = 0
for lon in range(-72, -40, 4):
    for d in (105, 130, 158, 186):
        x, y = at(lon + random.uniform(-1.5, 1.5), d + random.uniform(-6, 6))
        if x < 82:
            continue
        h = random.choice((10.5, 13.5, 13.5, 16.5))
        w, dd = random.uniform(9, 13), random.uniform(12, 16)
        bld(rect(x, y, w, dd, facing(x, y) + random.uniform(-0.1, 0.1)), h, hp[n % 6])
        n += 1

P = []   # primitives: dict(t, x, z, y0, y1, w, d, rot, c)   (x east, z south, rot = rotation about +Y)


def prim(t, x, y, y0, y1, w, d, rot, c, **kw):
    P.append(dict(t=t, x=round(x, 2), z=round(-y, 2), y0=y0, y1=y1, w=round(w, 2), d=round(d, 2), rot=round(rot, 4), c=c, **kw))


def off(x, y, rot, ox, oy=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return x + ox * c - oy * s, y + ox * s + oy * c


# party-plot gates: body, dark arch, three domes, two minarets
for lon, d, body, dm in ((1.0, dist(-33), '#8C2430', '#D9A84A'), (32.0, dist(-35), '#E9B98E', '#EFC9A0'), (57.0, dist(-26), '#E9B98E', '#EFC9A0')):
    x, y = at(lon, d)
    r = facing(x, y)
    prim('box', x, y, 0, 8.5, 20, 3.5, r, body)
    prim('box', x, y, 0, 6.0, 6, 3.7, r, '#3B2622')
    for ox, rr in ((0, 2.6), (-6.5, 1.6), (6.5, 1.6)):
        px, py = off(x, y, r, ox)
        prim('dome', px, py, 8.5, 8.5 + rr * 1.25, rr * 2, rr * 2, 0, dm)
    for ox in (-10.5, 10.5):
        px, py = off(x, y, r, ox)
        prim('cyl', px, py, 0, 12, 1.8, 1.8, 0, body)
        prim('dome', px, py, 12, 13.25, 2, 2, 0, dm)
# long grey tents with red skirts, axis pointing away from the balcony
for lon, d, L in ((19.0, dist(-27), 42), (30.0, dist(-22), 38)):
    x, y = at(lon, d)
    r = math.atan2(y - CAM[1], x - CAM[0])
    prim('tent', x, y, 1.2, 5.7, L, 9, r, '#8D9196')
    prim('box', x, y, 0, 1.3, L, 9.2, r, '#B83A2C')
# silos of the under-construction tower
x, y, r = UC
for ox, oy in ((-16, -12), (-12.4, -12)):
    px, py = off(x, y, r, ox, oy)
    prim('cyl', px, py, 1.5, 16, 3.2, 3.2, 0, '#C2551F')
# hedge walls around the two lawns (traced on Google Earth; context coords y = south)
GE = {'turf1': [[170.5, 115.3], [105.3, 97.4], [111.5, 45.2], [179.3, 58.3]],
      'turf2': [[178.8, 54.6], [110.1, 38.7], [121.6, -14.5], [191.8, -5.9]],
      'courts': [[230.0, 62.7], [182.7, 51.9], [189.3, 16.8], [237.6, 25.7]]}


def poly(k):
    return [(x, -y) for x, y in GE[k]]


def strip(a, b, y0, y1, w, c, t='box'):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    prim(t, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, y0, y1, L, w, math.atan2(b[1] - a[1], b[0] - a[0]), c)


for k in ('turf1', 'turf2'):
    Pp = poly(k)
    cx = sum(p[0] for p in Pp) / 4; cy = sum(p[1] for p in Pp) / 4
    Pp = [(cx + (p[0] - cx) * 1.06, cy + (p[1] - cy) * 1.06) for p in Pp]
    for i in range(4):
        strip(Pp[i], Pp[(i + 1) % 4], 0, 2.6, 1.4, '#3E5A2C')
# BMR box cricket: poles + translucent green net
Pp = poly('courts')
for i in range(4):
    a, b = Pp[i], Pp[(i + 1) % 4]
    strip(a, b, 0, 9, 0.05, '#2F4A3A', 'net')
    prim('cyl', a[0], a[1], 0, 9, 0.3, 0.3, 0, '#5E6266')
# eucalyptus plantation (dense tall trees), block from the land-cover map
random.seed(5)
G = []
for gx in range(380, 560, 8):
    for gy in range(-30, 110, 8):
        G += [round(gx + random.uniform(-3, 3), 1), round(-(gy + random.uniform(-3, 3)), 1), round(random.uniform(0.8, 1.05), 2)]

cp = os.path.join(ROOT, 'src', 'data', 'context.json')
ctx = [r for r in json.load(open(cp)) if len(r) < 5]
json.dump(ctx + B, open(cp, 'w'), separators=(',', ':'))
json.dump({'prims': P, 'grove': G}, open(os.path.join(ROOT, 'src', 'data', 'landmarks.json'), 'w'), separators=(',', ':'))
print('buildings', len(B), 'prims', len(P), 'grove trees', len(G) // 3)
