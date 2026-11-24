"""
Vraj Platinum — vector "presentation model" map of the real neighbourhood.

Inputs (scripts/mapdata):
  osm_local.json   OpenStreetMap features (© OpenStreetMap contributors, ODbL) within ~1.5 km,
                   already projected to local metres: x = East, z = South, origin = SITE.geo origin.
  landcover_10m.npy 200x200 land-cover classes (10 m cells, ±1000 m) classified from Esri World
                   Imagery (Oct 2025) — only the class grid is used, never the imagery itself.
  GE_FEATURES      a few features OSM lacks, digitised from the developer's Google Earth 2026
                   reference screenshots (turf grounds / courts / sports sheds across the 30 m road).

Outputs:
  public/map/near_4k.webp  1200 m square around the site, 4096 px (0.29 m/px)  — desktop
  public/map/near_2k.webp  same, 2048 px — mobile
  public/map/far_2k.webp   4096 m square, 2048 px (2 m/px) with a soft haze fade at the rim
  src/data/context.json    neighbour buildings [ring[x,z..], height, levels, kind]
  src/data/trees.json      instanced tree positions per species

Run:  python3 scripts/build_map.py
"""
import json, math, os, random
import numpy as np
import cv2
import skia
from scipy.ndimage import gaussian_filter
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import contains_xy, prepare

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'scripts', 'mapdata')
F = json.load(open(os.path.join(D, 'osm_local.json')))
LC = np.load(os.path.join(D, 'landcover_10m.npy'))
SITE = json.load(open(os.path.join(ROOT, 'src', 'data', 'site.json')))
PREVIEW = os.environ.get('MAP_PREVIEW', '/home/claude/data')
rng = random.Random(7)

# ---------------------------------------------------------------- palette (sRGB)
# derived from the real class means of the satellite grid, cleaned up into a calm presentation palette
PAL = {
    'sand':      (192, 176, 140),   # open / fallow land   (real 131,123,93)
    'wet':       (110, 136, 86),   # dense wet fields     (real 29,55,36)
    'scrub':     (124, 146, 94),   # scrub / tree ground  (real 71,86,65)
    'grass':     (150, 172, 108),   # light grass          (real 133,144,126)
    'built':     (200, 192, 176),   # built ground         (real 218,215,195 / 108,111,88)
    'farm':      (140, 164, 98),
    'wood':      (96, 124, 76),
    'resi':      (206, 198, 182),
    'indu':      (204, 200, 192),
    'retail':    (208, 200, 188),
    'constr':    (196, 176, 136),
    'turf':      (88, 148, 74),
    'turf2':     (120, 156, 92),
    'court':     (70, 128, 86),
    'bank':      (170, 180, 140),
    'water':     (94, 150, 160),
    'water2':    (80, 136, 150),
    'verge':     (214, 206, 190),
    'curb':      (236, 233, 224),
    'asphalt':   (92, 94, 98),
    'mark':      (244, 242, 236),
    'pave':      (210, 204, 190),
    'haze':      (196, 188, 166),
}


PAL = {
    'sand': (150, 132, 100), 'wet': (70, 92, 52), 'scrub': (88, 104, 66), 'grass': (118, 134, 80),
    'built': (160, 153, 140), 'farm': (106, 124, 70), 'wood': (58, 78, 44), 'resi': (150, 141, 128),
    'indu': (160, 156, 150), 'retail': (160, 152, 140), 'constr': (155, 135, 105), 'turf': (64, 118, 56),
    'turf2': (90, 126, 66), 'court': (52, 104, 72), 'bank': (120, 124, 90), 'water': (60, 82, 74),
    'water2': (50, 70, 66), 'verge': (150, 140, 120), 'curb': (190, 186, 178), 'asphalt': (64, 66, 68),
    'mark': (222, 220, 210), 'pave': (170, 165, 155), 'haze': (168, 162, 148),
}
GRAIN = {'sand': 0.16, 'wet': 0.2, 'scrub': 0.24, 'grass': 0.18, 'farm': 0.2, 'wood': 0.3, 'built': 0.14, 'resi': 0.16, 'constr': 0.18, 'bank': 0.2}

# ---------------------------------------------------------------- features
GE_FEATURES = {  # digitised from Google Earth reference (see header); local metres
    'turf1': [[170.5, 115.3], [105.3, 97.4], [111.5, 45.2], [179.3, 58.3]],
    'turf2': [[178.8, 54.6], [110.1, 38.7], [121.6, -14.5], [191.8, -5.9]],
    'courts': [[230.0, 62.7], [182.7, 51.9], [189.3, 16.8], [237.6, 25.7]],
    'shedW': [[277.3, 109.6], [220.4, 85.1], [238.0, 25.0], [285.0, 31.8]],
    'shedN': [[220.4, 85.1], [178.4, 68.9], [182.7, 51.9], [230.0, 62.7]],
    'shedS': [[285.0, 31.8], [238.0, 25.0], [188.0, 14.7], [187.1, -6.1], [292.6, -0.4]],
}
# the 30 m Sarthana–Gadhpur road in front of the project (centre x = 58, see site.json road rect)
MAIN_ROAD = [[58, -262], [58, 262]]   # same straight alignment as the Blender site road (site.py: ±260 m)

PLOT = SITE['plot']            # [x0, x1, z0, z1]
ROADR = SITE['road']['rect']   # [x0, x1, z0, z1]

ROAD_W = {  # carriageway widths (m); oneway carriageways narrower
    'primary': (18, 10.5), 'primary_link': (7, 7), 'secondary': (13, 8.5), 'tertiary': (9, 7),
    'tertiary_link': (6.5, 6.5), 'busway': (7.5, 7.5), 'unclassified': (6.5, 6), 'residential': (6, 5),
    'service': (4.5, 4), 'construction': (6, 6),
}
MARKED = {'primary', 'secondary', 'tertiary', 'busway'}

# towers visible on the Google Earth reference but missing from OSM (west column of the cluster)
# (two more stand further south on the imagery, but the OSM creek trace runs through those spots — the
#  creek is ~25 m off in OSM there — so they are left out rather than placed in the water)
GE_TOWERS = [[[-126, -47], [-95, -47], [-95, -25], [-126, -25]]]
# OSM footprints without building:levels that are clearly G+13/14 towers on the reference imagery
LEVEL_FIX = {(27, -66): 14, (20, -112): 14}
# keep neighbours off the project plot: drop OSM footprints that ARE the project (centroid inside the plot),
# push the rest (offset by a few metres in OSM) just outside it — same rule the app used before
PB = (-46, 46, -40.5, 40.5)

def centroid(ring):
    g = Polygon(ring)
    return (g.centroid.x, g.centroid.y)

def fit_outside_plot(ring):
    cx, cz = centroid(ring)
    if PB[0] - 2 < cx < PB[1] + 2 and PB[2] - 2 < cz < PB[3] + 2:
        return None
    xs = [p[0] for p in ring]; zs = [p[1] for p in ring]
    if max(xs) > PB[0] and min(xs) < PB[1] and max(zs) > PB[2] and min(zs) < PB[3]:
        moves = sorted([(PB[0] - max(xs), 0), (PB[1] - min(xs), 0), (0, PB[2] - max(zs)), (0, PB[3] - min(zs))], key=lambda m: math.hypot(*m))
        if math.hypot(*moves[0]) > 15:
            return None
        ring = [[p[0] + moves[0][0], p[1] + moves[0][1]] for p in ring]
    return ring

roads, waters, landuse, buildings = [], [], [], []
for f in F:
    k, p = f['k'], f['p']
    if k.startswith('h:'):
        cls = k[2:]
        if cls not in ROAD_W or len(p) < 2:
            continue
        w = ROAD_W[cls][1 if f.get('oneway') else 0]
        if all(35 < q[0] < 85 and -262 < q[1] < 262 for q in p):
            continue   # OSM trace of the 30 m road — replaced by MAIN_ROAD below
        roads.append((cls, w, p))
    elif k.startswith('w:'):
        w = {'river': 15, 'stream': 6, 'drain': 4}.get(k[2:], 4)
        waters.append((w, p))
    elif k == 'b':
        if len(p) >= 3:
            r = fit_outside_plot(p)
            if r:
                buildings.append(dict(f, p=r))
    else:
        if len(p) >= 3:
            landuse.append((k, p))
roads.append(('main', 24.0, MAIN_ROAD))
for r in GE_TOWERS:
    buildings.append({'k': 'b', 'p': r, 'levels': 15})

# ---------------------------------------------------------------- exclusion geometry (trees)
def poly(p):
    g = Polygon(p)
    return g if g.is_valid else g.buffer(0)

bld_polys = [poly(f['p']) for f in buildings] + [poly(v) for k, v in GE_FEATURES.items()]
road_geom = unary_union([LineString(p).buffer(w / 2 + 1.8, cap_style=1) for _, w, p in roads])
water_geom = unary_union([LineString(p).buffer(w / 2 + 1.0) for w, p in waters])
site_geom = box(PLOT[0] - 6, PLOT[2] - 6, ROADR[1] + 4, PLOT[3] + 6).union(box(ROADR[0] - 2, ROADR[2] - 4, ROADR[1] + 4, ROADR[3] + 4))
blocked = unary_union(bld_polys + [road_geom, water_geom, site_geom]).buffer(1.5)
prepare(blocked)
resi_geom = unary_union([poly(p) for k, p in landuse if k in ('l:residential', 'l:industrial', 'l:retail')])
prepare(resi_geom)

# ---------------------------------------------------------------- trees
trees = {'r': [], 'b': [], 't': []}   # round shade tree, mangrove/bush, tall columnar
cand = []

def along(p, step):
    ls = LineString(p)
    n = max(1, int(ls.length / step))
    for i in range(n + 1):
        d = (i + rng.random() * 0.6) * step
        if d > ls.length:
            break
        a = ls.interpolate(d)
        b = ls.interpolate(min(ls.length, d + 1.0))
        dx, dz = b.x - a.x, b.y - a.y
        L = math.hypot(dx, dz) or 1
        yield a.x, a.y, -dz / L, dx / L

# 1. mangroves along the creek
for w, p in waters:
    lo, hi = (w / 2 + 2.5, w / 2 + 14) if w > 10 else (w / 2 + 1.5, w / 2 + 7)
    for x, z, nx, nz in along(p, 4.2 if w > 10 else 6):
        for side in (-1, 1):
            o = lo + rng.random() * (hi - lo)
            cand.append((x + nx * o * side, z + nz * o * side, 'b', 0.8 + rng.random() * 0.6, 1))
# 2. woods (OSM)
for k, p in landuse:
    if k != 'n:wood':
        continue
    g = poly(p)
    x0, z0, x1, z1 = g.bounds
    if min(abs(x0), abs(x1), abs(z0), abs(z1)) > 1500:
        continue
    for x in np.arange(x0, x1, 9):
        for z in np.arange(z0, z1, 9):
            px, pz = x + rng.uniform(-3.5, 3.5), z + rng.uniform(-3.5, 3.5)
            if g.contains(Point(px, pz)):
                sp = 't' if rng.random() < 0.25 else 'r'
                cand.append((px, pz, sp, 0.8 + rng.random() * 0.6, 2))
# 3. scrub / tree cells in the satellite land-cover grid (smoothed)
tree_p = gaussian_filter((LC == 2).astype(np.float32), 0.8)
for r in range(200):
    for c in range(200):
        pr = tree_p[r, c]
        if pr > 0.55 and rng.random() < 0.42 * pr:
            x = -1000 + c * 10 + rng.uniform(1, 9)
            z = -1000 + r * 10 + rng.uniform(1, 9)
            cand.append((x, z, 'r' if rng.random() < 0.7 else 'b', 0.75 + rng.random() * 0.55, 3))
# 4. avenue trees along the bigger roads near the site
for cls, w, p in roads:
    if cls not in ('primary', 'secondary', 'tertiary', 'main', 'busway'):
        continue
    for x, z, nx, nz in along(p, 13):
        if math.hypot(x, z) > 900:
            continue
        for side in (-1, 1):
            o = w / 2 + 3.2
            cand.append((x + nx * o * side, z + nz * o * side, 'r' if rng.random() < 0.6 else 't', 0.85 + rng.random() * 0.35, 4))

xs = np.array([c[0] for c in cand]); zs = np.array([c[1] for c in cand])
ok = ~contains_xy(blocked, xs, zs) & (np.abs(xs) < 1900) & (np.abs(zs) < 1900)
# fewer trees deep inside built-up residential blocks (keeps the row-house fabric readable)
inres = contains_xy(resi_geom, xs, zs)
kept = []
for i, c in enumerate(cand):
    if not ok[i]:
        continue
    if inres[i] and c[4] == 3 and rng.random() < 0.7:
        continue
    d = math.hypot(c[0], c[1])
    keep = 1.0 if d < 450 else max(0.18, 1.0 - (d - 450) / 1300)
    if rng.random() < keep:
        kept.append(c)
# thin anything closer than 3.2 m to an already-kept tree
kept.sort(key=lambda c: (c[4], math.hypot(c[0], c[1])))
grid = {}
final = []
for c in kept:
    gx, gz = int(c[0] // 4), int(c[1] // 4)
    clash = False
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            for q in grid.get((gx + a, gz + b), ()):
                if (q[0] - c[0]) ** 2 + (q[1] - c[1]) ** 2 < 3.2 ** 2:
                    clash = True
    if not clash:
        grid.setdefault((gx, gz), []).append(c)
        final.append(c)
MAX_TREES = 4000
if len(final) > MAX_TREES:
    final.sort(key=lambda c: math.hypot(c[0], c[1]) * (0.6 + rng.random() * 0.8))
    final = final[:MAX_TREES]
rng.shuffle(final)   # so a mobile stride-subset stays evenly spread
for x, z, sp, s, _ in final:
    trees[sp] += [round(x, 1), round(z, 1), round(s, 2)]
json.dump(trees, open(os.path.join(ROOT, 'src', 'data', 'trees.json'), 'w'), separators=(',', ':'))
print('trees', {k: len(v) // 3 for k, v in trees.items()})

# ---------------------------------------------------------------- buildings → context.json
out = []
for f in buildings:
    ring = f['p'][:-1] if f['p'][0] == f['p'][-1] else f['p']
    if len(ring) < 3:
        continue
    lv = f.get('levels') or LEVEL_FIX.get(tuple(round(v) for v in centroid(ring))) or 2
    lv = max(1, min(30, round(lv)))
    h = 3.6 + (lv - 1) * 3.0   # OSM levels include the ground floor (G+14 = 15 levels → 45.6 m, same as our towers)
    try:
        if f.get('height'):
            h = float(str(f['height']).split()[0])
    except ValueError:
        pass
    flat = [round(v, 1) for pt in ring for v in pt]
    out.append([flat, round(h, 1), lv, 0])
for k in ('shedW', 'shedN', 'shedS'):
    out.append([[v for pt in GE_FEATURES[k] for v in pt], 8.0, 2, 1])
json.dump(out, open(os.path.join(ROOT, 'src', 'data', 'context.json'), 'w'), separators=(',', ':'))
print('buildings', len(out))

# ---------------------------------------------------------------- land-cover raster
GROUPS = {1: 'wet', 2: 'scrub', 3: 'grass', 4: 'sand', 5: 'built', 6: 'built', 7: 'built'}
names = ['sand', 'wet', 'scrub', 'grass', 'built']
probs = []
for n in names:
    m = np.zeros(LC.shape, np.float32)
    for c, g in GROUPS.items():
        if g == n:
            m[LC == c] = 1
    probs.append(gaussian_filter(m, 1.15))
probs = np.stack(probs)  # [G, 200, 200]

# synthetic field patchwork for the area beyond the satellite grid (fades out in fog anyway)
nr = np.random.RandomState(3)
SYN = 160  # 4 km / 25 m cells
syn = np.stack([gaussian_filter(nr.rand(SYN, SYN).astype(np.float32), 2.2) for _ in names])
syn[0] *= 1.25; syn[4] *= 0.55; syn[3] *= 0.9  # mostly open sand + fields

def landcover_rgb(X0, Z0, mpp, N):
    t = ((np.arange(N) + 0.5) * mpp).astype(np.float32)
    X, Z = np.meshgrid(np.float32(X0) + t, np.float32(Z0) + t)
    gc = ((X + 1000) / 10 - 0.5).astype(np.float32)
    gr = ((Z + 1000) / 10 - 0.5).astype(np.float32)
    sc = ((X + 2000) / 25 - 0.5).astype(np.float32)
    sr = ((Z + 2000) / 25 - 0.5).astype(np.float32)
    inside = np.clip(np.minimum(1000 - np.abs(X), 1000 - np.abs(Z)) / 120.0, 0, 1)
    acc = np.zeros((N, N, 3), np.float32)
    ws = []
    for i, n in enumerate(names):
        a = cv2.remap(probs[i], gc, gr, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        b = cv2.remap(syn[i], sc, sr, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        b = (b - syn[i].mean()) * 3 + 0.4
        ws.append(a * inside + b * (1 - inside))
    W = np.stack(ws)
    W = np.exp((W - W.max(0, keepdims=True)) * 70.0)   # crisp but anti-aliased class borders
    W /= W.sum(0, keepdims=True)
    for i, n in enumerate(names):
        acc += W[i][..., None] * np.array(PAL[n], np.float32)
    # gentle large-scale tonal variation
    tone = cv2.resize(gaussian_filter(nr.rand(64, 64).astype(np.float32), 3), (N, N), interpolation=cv2.INTER_CUBIC)
    tone = 1 + (tone - tone.mean()) * 0.6
    acc *= tone[..., None]
    # photographic grain / clumps per class (fBm), like real aerial imagery
    rng = np.random.default_rng(3)
    fbm = np.zeros((N, N), np.float32)
    for k, amp in ((2, 0.35), (6, 0.25), (18, 0.2), (60, 0.12), (N // 2, 0.08)):
        g = rng.random((k, k)).astype(np.float32)
        fbm += cv2.resize(g, (N, N), interpolation=cv2.INTER_CUBIC) * amp
    fbm = (fbm - fbm.mean()) / (fbm.std() + 1e-6)
    gain = np.zeros((N, N), np.float32)
    for i, n in enumerate(names):
        gain += W[i] * GRAIN.get(n, 0.06)
    acc *= (1 + fbm * gain)[..., None]
    return np.clip(acc, 0, 255)

# ---------------------------------------------------------------- vector drawing
def C(rgb, a=255):
    return skia.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(a))

def render(X0, Z0, size_m, N, fade=None):
    mpp = size_m / N
    rgb = landcover_rgb(X0, Z0, mpp, N)
    arr = np.dstack([rgb.astype(np.uint8), np.full((N, N), 255, np.uint8)]).copy()
    surf = skia.Surface(arr)  # RGBA backing
    cv = surf.getCanvas()
    cv.scale(1 / mpp, 1 / mpp)
    cv.translate(-X0, -Z0)
    px = mpp  # one pixel in world metres

    def path(p, close=False):
        pa = skia.Path()
        pa.moveTo(*p[0])
        for q in p[1:]:
            pa.lineTo(*q)
        if close:
            pa.close()
        return pa

    def fill(p, col, a=255, blur=0):
        paint = skia.Paint(AntiAlias=True, Color=C(col, a))
        if blur:
            paint.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        cv.drawPath(path(p, True), paint)

    def stroke(p, col, w, a=255, dash=None, cap=skia.Paint.kRound_Cap, blur=0):
        paint = skia.Paint(AntiAlias=True, Color=C(col, a), Style=skia.Paint.kStroke_Style,
                           StrokeWidth=max(w, px * 0.6), StrokeCap=cap, StrokeJoin=skia.Paint.kRound_Join)
        if dash:
            paint.setPathEffect(skia.DashPathEffect.Make(dash, 0))
        if blur:
            paint.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        cv.drawPath(path(p), paint)

    # landuse (OSM)
    order = ['l:farmland', 'l:construction', 'l:residential', 'l:retail', 'l:industrial', 'n:wood', 's:pitch']
    col = {'l:farmland': 'farm', 'l:construction': 'constr', 'l:residential': 'resi', 'l:retail': 'retail',
           'l:industrial': 'indu', 'n:wood': 'wood', 's:pitch': 'turf'}
    for k0 in order:
        for k, p in landuse:
            if k != k0:
                continue
            a = 215 if k in ('l:residential', 'l:retail', 'l:industrial') else 235
            fill(p, PAL[col[k]], a)
            if k == 'l:farmland':   # crop rows along the longest edge
                g = Polygon(p)
                if not g.is_valid:
                    continue
                e = max(zip(p, p[1:] + p[:1]), key=lambda ab: math.dist(ab[0], ab[1]))
                ang = math.atan2(e[1][1] - e[0][1], e[1][0] - e[0][0])
                cx, cz = g.centroid.x, g.centroid.y
                R = math.dist(*[g.bounds[:2], g.bounds[2:]]) / 2 + 2
                cv.save(); cv.clipPath(path(p, True), doAntiAlias=True)
                cv.translate(cx, cz); cv.rotate(math.degrees(ang))
                paint = skia.Paint(AntiAlias=True, Color=C((120, 146, 88), 46), StrokeWidth=1.0, Style=skia.Paint.kStroke_Style)
                y = -R
                while y < R:
                    cv.drawLine(-R, y, R, y, paint); y += 3.2
                cv.restore()
                stroke(p + p[:1], (150, 168, 112), 0.8, 120)

    # sports grounds across the road (Google Earth reference)
    def pitch(p, base, lines=True):
        fill(p, base)
        if lines:
            g = Polygon(p).buffer(-2.5, join_style=2)
            if not g.is_empty and g.geom_type == 'Polygon':
                q = [list(c) for c in g.exterior.coords][:-1]
                stroke(q + q[:1], PAL['mark'], 0.18, 230)
                # halfway line
                m1 = [(q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2]
                m2 = [(q[2][0] + q[3][0]) / 2, (q[2][1] + q[3][1]) / 2]
                stroke([m1, m2], PAL['mark'], 0.18, 230)
                c = Polygon(q).centroid
                cv.drawCircle(c.x, c.y, 6.0, skia.Paint(AntiAlias=True, Color=C(PAL['mark'], 220), Style=skia.Paint.kStroke_Style, StrokeWidth=0.18))
        stroke(p + p[:1], (60, 92, 64), 0.6, 200)   # perimeter net / fence
    pitch(GE_FEATURES['turf1'], PAL['turf'])
    pitch(GE_FEATURES['turf2'], PAL['turf2'])
    fill(GE_FEATURES['courts'], PAL['court'])
    q = GE_FEATURES['courts']
    for i in range(1, 3):
        a = [q[1][0] + (q[0][0] - q[1][0]) * i / 3, q[1][1] + (q[0][1] - q[1][1]) * i / 3]
        b = [q[2][0] + (q[3][0] - q[2][0]) * i / 3, q[2][1] + (q[3][1] - q[2][1]) * i / 3]
        stroke([a, b], PAL['mark'], 0.25, 220)
    stroke(q + q[:1], PAL['mark'], 0.25, 220)

    # water: bank, water, deeper centre
    for w, p in waters:
        stroke(p, PAL['bank'], w + 9, 255, blur=1.5)
    for w, p in waters:
        stroke(p, PAL['water'], w)
    for w, p in waters:
        if w > 5:
            stroke(p, PAL['water2'], w * 0.45, 200, blur=1.2)

    # soft canopy shadows under trees
    shp = skia.Paint(AntiAlias=True, Color=C((62, 78, 48), 70))
    shp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.4))
    for sp, rad in (('r', 2.9), ('b', 2.3), ('t', 1.9)):
        v = trees[sp]
        for i in range(0, len(v), 3):
            cv.drawCircle(v[i] + 0.8, v[i + 1] + 0.8, rad * v[i + 2], shp)

    # building contact shadow (AO) + plinth
    for f in buildings:
        fill(f['p'], (70, 64, 52), 80, blur=2.2)
    for k in ('shedW', 'shedN', 'shedS'):
        fill(GE_FEATURES[k], (70, 64, 52), 50, blur=1.6)
    for f in buildings:
        fill(f['p'], (232, 228, 220))

    # roads: verge/footpath → curb line → asphalt → markings (all classes per layer for clean joins)
    srt = sorted(roads, key=lambda r: r[1])
    for cls, w, p in srt:
        stroke(p, PAL['verge'], w + (5 if cls == 'main' else 3.2 if w >= 7 else 2.0))
    for cls, w, p in srt:
        stroke(p, PAL['curb'], w + 0.7)
    for cls, w, p in srt:
        stroke(p, PAL['asphalt'], w)
    for cls, w, p in srt:
        if cls in MARKED or cls == 'main':
            stroke(p, PAL['mark'], 0.22, 215, dash=[3.0, 5.0], cap=skia.Paint.kButt_Cap)
        if cls == 'main':   # lane lines + edge lines on the 30 m road
            ls = LineString(p)
            for off in (-6.0, 6.0):
                o = ls.offset_curve(off)
                stroke([list(c) for c in o.coords], PAL['mark'], 0.15, 150, dash=[3.0, 5.0], cap=skia.Paint.kButt_Cap)
            for off in (-w / 2 + 0.5, w / 2 - 0.5):
                o = ls.offset_curve(off)
                stroke([list(c) for c in o.coords], PAL['mark'], 0.15, 200)

    # project plot — neutral paving under the Blender site model
    pr = [[PLOT[0] - 1, PLOT[2] - 1], [PLOT[1], PLOT[2] - 1], [PLOT[1], PLOT[3] + 1], [PLOT[0] - 1, PLOT[3] + 1]]
    fill(pr, PAL['pave'])

    img = surf.toarray()[..., :3].astype(np.float32)
    if fade:
        r0, r1 = fade
        t = (np.arange(N) + 0.5) * mpp
        X, Z = np.meshgrid(X0 + t, Z0 + t)
        R = np.hypot(X, Z)
        a = np.clip((R - r0) / (r1 - r0), 0, 1)
        a = a * a * (3 - 2 * a)
        img = img * (1 - a[..., None]) + np.array(PAL['haze'], np.float32) * a[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


def save(img, path, q):
    cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_WEBP_QUALITY, q])
    print(path, os.path.getsize(path) // 1024, 'KB')

OUTD = os.path.join(ROOT, 'blender', 'out')
os.makedirs(OUTD, exist_ok=True)
NEAR = 1200
near = render(-NEAR / 2, -NEAR / 2, NEAR, 6144)
cv2.imwrite(os.path.join(OUTD, 'ground_near_6k.jpg'), cv2.cvtColor(near, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
FAR = 4096
far = render(-FAR / 2, -FAR / 2, FAR, 4096, fade=(1500, 2000))
cv2.imwrite(os.path.join(OUTD, 'ground_far_4k.jpg'), cv2.cvtColor(far, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
cv2.imwrite('/tmp/ground_crop.jpg', cv2.cvtColor(near[2500:3700, 2700:3900], cv2.COLOR_RGB2BGR))
print('ok')
