"""Vraj Platinum towers: per-block floor modules (instanced 14x in the web app), ground floor,
roof and planter modules. Facade language from the brochure renders: white balcony frames,
charcoal bands, rust/wood vertical cladding, black railings with glass, cascading creepers.

python3 blender/towers.py  ->  blender/out/towers.glb
"""
import sys, os, json, math, random
import bpy, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bcommon import *
import bcommon
bcommon.PROCEDURAL = False

random.seed(11)
site = json.load(open(os.path.join(ROOT, 'src', 'data', 'site.json')))
FH, GH = site['floorH'], site['groundH']

reset()
reset_mats()
M = dict(
    plaster=mat('plaster', '#EAE8E3', 0.85),
    white=mat('white', '#F1F0EC', 0.8),
    charcoal=mat('charcoal', '#686A6F', 0.85),
    grey=mat('grey', '#8E9196', 0.85),
    rust=mat('rust', '#8A4630', 0.65),
    glass=mat('glass', '#1F262C', 0.06, 0.6),
    rail=mat('rail', '#1E1F22', 0.45, 0.6),
    railwhite=mat('railwhite', '#E8E8E4', 0.45, 0.3),
    steel=mat('steel', '#7F848A', 0.4, 0.8),
    frame=mat('frame', '#4B4F55', 0.4, 0.6),
    lightgrey=mat('lightgrey', '#C8C8C4', 0.85),
    railglass=mat('railglass', '#9FB7C1', 0.05, alpha=0.35),
    stone=mat('stone', '#BFB19A', 0.8),
    wood=mat('wood', '#8B5A3A', 0.6),
    leaf=mat('leaf', '#4C7A33', 0.8),
    leafdark=mat('leafdark', '#2F5A25', 0.85),
    solar=mat('solar', '#1A2433', 0.15, 0.7),
    ceiling=mat('ceiling', '#E9E7E2', 0.9),
    gold=mat('gold', '#C9A15A', 0.35, 0.8),
    lobbyglow=mat('lobbyglow', '#FFE6BF', 0.6, emit='#FFD49A', emit_strength=1.5),
)

modules = {}


def new_mod(name):
    modules[name] = []
    return modules[name]


def B(lst, *a, **k):
    o = box(f'o{len(lst)}', *a, **k)
    lst.append(o)
    return o


def touching(r, others, side, tol=0.4):
    x0, x1, y0, y1 = r
    for o in others:
        ox0, ox1, oy0, oy1 = o
        if side == 'E' and abs(ox0 - x1) < tol and min(y1, oy1) - max(y0, oy0) > 1.0: return True
        if side == 'W' and abs(ox1 - x0) < tol and min(y1, oy1) - max(y0, oy0) > 1.0: return True
        if side == 'N' and abs(oy0 - y1) < tol and min(x1, ox1) - max(x0, ox0) > 1.0: return True
        if side == 'S' and abs(oy1 - y0) < tol and min(x1, ox1) - max(x0, ox0) > 1.0: return True
    return False


def side_frame(r, side):
    """returns (origin point along side, unit along-vector, outward normal, length)"""
    x0, x1, y0, y1 = r
    if side == 'N': return (x0, y1), (1, 0), (0, 1), x1 - x0
    if side == 'S': return (x0, y0), (1, 0), (0, -1), x1 - x0
    if side == 'E': return (x1, y0), (0, 1), (1, 0), y1 - y0
    return (x0, y0), (0, 1), (-1, 0), y1 - y0


def sbox(lst, o, u, n, a0, a1, d0, d1, z0, z1, m, **k):
    """box in side-local coords: along [a0,a1], outward [d0,d1]"""
    pts = [(o[0] + u[0] * a + n[0] * d, o[1] + u[1] * a + n[1] * d) for a in (a0, a1) for d in (d0, d1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return B(lst, min(xs), max(xs), min(ys), max(ys), z0, z1, m, **k)


glass_windows = []
anchors = {}   # flat key -> list of balcony anchors (centre point, outward dir) for the web balcony camera


def window(lst, o, u, n, a0, a1, z0, z1, mullions=2):
    g = sbox(lst, o, u, n, a0, a1, -0.04, 0.02, z0, z1, M['glass'])
    glass_windows.append(g)
    for (b0, b1, c0, c1) in ((a0 - 0.06, a1 + 0.06, z0 - 0.06, z0), (a0 - 0.06, a1 + 0.06, z1, z1 + 0.06),
                             (a0 - 0.06, a0, z0, z1), (a1, a1 + 0.06, z0, z1)):
        sbox(lst, o, u, n, b0, b1, -0.02, 0.05, c0, c1, M['frame'])
    for i in range(1, mullions):
        a = a0 + (a1 - a0) * i / mullions
        sbox(lst, o, u, n, a - 0.025, a + 0.025, -0.02, 0.05, z0, z1, M['frame'])


def railing(lst, o, u, n, a0, a1, depth, kind):
    """3-sided balcony railing: kind 'glass' (steel top rail + glass) or 'bars' (white MS balusters)."""
    H = 1.05
    if kind == 'glass':
        sbox(lst, o, u, n, a0 + 0.05, a1 - 0.05, depth - 0.07, depth - 0.05, 0.15, H - 0.05, M['railglass'])
        for a in (a0 + 0.04, a1 - 0.04):
            sbox(lst, o, u, n, a - 0.01, a + 0.01, 0.1, depth - 0.05, 0.15, H - 0.05, M['railglass'])
        top = M['steel']
    else:
        top = M['railwhite']
        k = a0 + 0.08
        while k < a1 - 0.05:
            sbox(lst, o, u, n, k - 0.012, k + 0.012, depth - 0.09, depth - 0.065, 0.15, H, M['railwhite'])
            k += 0.12
        for a in (a0 + 0.05, a1 - 0.05):
            d = 0.25
            while d < depth - 0.1:
                sbox(lst, o, u, n, a - 0.012, a + 0.012, d - 0.012, d + 0.012, 0.15, H, M['railwhite'])
                d += 0.14
        sbox(lst, o, u, n, a0 + 0.05, a1 - 0.05, depth - 0.1, depth - 0.05, 0.32, 0.35, M['railwhite'])
    sbox(lst, o, u, n, a0 + 0.03, a1 - 0.03, depth - 0.11, depth - 0.03, H, H + 0.05, top)
    for a in (a0 + 0.03, a1 - 0.07):
        sbox(lst, o, u, n, a, a + 0.04, 0.05, depth - 0.03, H, H + 0.05, top)


def balcony_bay(lst, o, u, n, a0, a1, depth, kind):
    # cantilevered white slab with a deeper fascia (as on site), sliding door behind
    sbox(lst, o, u, n, a0, a1, 0, depth, -0.16, 0.12, M['white'])
    sbox(lst, o, u, n, a0, a1, depth - 0.04, depth, -0.28, 0.12, M['white'])
    window(lst, o, u, n, a0 + 0.25, a1 - 0.25, 0.12, 2.35, mullions=3)
    railing(lst, o, u, n, a0, a1, depth, kind)


def add_anchor(key, o, u, n, a, depth, label, d):
    p = (o[0] + u[0] * a + n[0] * depth * 0.45, o[1] + u[1] * a + n[1] * depth * 0.45)
    anchors.setdefault(key, []).append(dict(e=round(p[0], 3), n=round(p[1], 3), dir=d, label=label))


def facade(lst, r, side, style, flat, kind):
    o, u, n, L = side_frame(r, side)
    key = f"{flat['tower']}-{flat['no']}"
    if style == 'primary':
        # massive charcoal textured pier + bronze strip (photos 163134291 / 164556602)
        P = 3.1 if L > 10 else 2.2
        sbox(lst, o, u, n, 0, P, 0, 0.45, 0, FH, M['charcoal'])
        sbox(lst, o, u, n, P, P + 0.3, 0, 0.3, 0, FH, M['wood'])
        b0 = P + 0.5
        m = (b0 + L - 0.35) / 2
        balcony_bay(lst, o, u, n, b0, m - 0.12, 1.3, kind)
        balcony_bay(lst, o, u, n, m + 0.12, L - 0.35, 1.3, kind)
        sbox(lst, o, u, n, m - 0.12, m + 0.12, 0, 1.3, -0.28, FH - 0.28, M['white'])  # separator fin
        sbox(lst, o, u, n, L - 0.35, L, 0, 0.18, 0, FH, M['lightgrey'])
        add_anchor(key, o, u, n, (b0 + m - 0.12) / 2, 1.3, 'Living & balcony', side)
    elif style == 'end':
        mid = L * 0.55
        sbox(lst, o, u, n, 0, 1.9, 0, 0.4, 0, FH, M['charcoal'])
        window(lst, o, u, n, 2.2, mid - 0.4, 0.9, 2.3, 2)
        sbox(lst, o, u, n, 2.0, mid - 0.2, -0.01, 0.0, 0.0, FH, M['lightgrey'])
        balcony_bay(lst, o, u, n, mid + 0.1, L - 0.5, 1.1, kind)
        sbox(lst, o, u, n, mid - 0.2, mid + 0.1, 0, 0.26, 0, FH, M['wood'])
        add_anchor(key, o, u, n, (mid + 0.1 + L - 0.5) / 2, 1.1, 'Bedroom balcony', side)
    else:  # service side: small windows on light-grey recess panels
        for a in (L * 0.25, L * 0.7):
            sbox(lst, o, u, n, a - 0.6, a + 0.6, -0.01, 0.0, 0.8, 2.6, M['lightgrey'])
            window(lst, o, u, n, a - 0.4, a + 0.4, 1.5, 2.3, 1)
        sbox(lst, o, u, n, L * 0.4, L * 0.6, 0, 0.3, 0, FH, M['charcoal'])


def build_block(b):
    bid = b['id']
    rects = [f['rect'] for f in b['flats']]
    core = b['core']
    floor = new_mod(f'{bid}_floor')
    B(floor, core[0], core[1], core[2], core[3], 0, FH, M['charcoal'])
    for i, f in enumerate(b['flats']):
        r = f['rect']
        x0, x1, y0, y1 = r
        B(floor, x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, 0.0, FH, M['plaster'])
        B(floor, x0, x1, y0, y1, FH - 0.04, FH, M['lightgrey'])
        others = [q for q in rects if q is not r] + [core]
        dirs = [v['dir'] for v in f['views']]
        for side in 'NSEW':
            if touching(r, others, side):
                continue
            style = 'primary' if side == dirs[0] else 'end' if side in dirs[1:] else 'secondary'
            kind = 'glass' if (b['kind'] == 'square' and side == 'E') else 'bars'
            facade(floor, r, side, style, f, kind)
    # ---- ground: stilts, charcoal first-floor band, lobby
    g = new_mod(f'{bid}_ground')
    for f in b['flats']:
        x0, x1, y0, y1 = f['rect']
        B(g, x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, GH - 0.75, GH, M['charcoal'])
        B(g, x0, x1, y0, y1, GH - 0.76, GH - 0.75, M['ceiling'])
        nx, ny = max(2, int((x1 - x0) / 4.5) + 1), max(2, int((y1 - y0) / 4.5) + 1)
        for i in range(nx):
            for j in range(ny):
                cx_ = x0 + 0.35 + (x1 - x0 - 0.7) * i / (nx - 1)
                cy_ = y0 + 0.35 + (y1 - y0 - 0.7) * j / (ny - 1)
                B(g, cx_ - 0.23, cx_ + 0.23, cy_ - 0.3, cy_ + 0.3, 0, GH - 0.75, M['white'])
                B(g, cx_ - 0.25, cx_ + 0.25, cy_ - 0.32, cy_ + 0.32, 0, 0.45, M['charcoal'])
    cx0, cx1, cy0, cy1 = core
    B(g, cx0, cx1, cy0, cy1, 0, GH, M['stone'])
    lx0, lx1, ly0, ly1 = cx0 - 2.2, cx1 + 2.2, cy0 - 0.6, cy1 + 0.6
    lob = B(g, lx0, lx1, ly0, ly1, 0, GH - 0.8, M['glass'])
    glass_windows.append(lob)
    B(g, lx0 + 0.3, lx1 - 0.3, ly0 + 0.3, ly1 - 0.3, GH - 0.86, GH - 0.81, M['lobbyglow'])
    # ---- roof: parapet + steel solar canopy (signature element in the site photos)
    rf = new_mod(f'{bid}_roof')
    for i, f in enumerate(b['flats']):
        x0, x1, y0, y1 = f['rect']
        B(rf, x0, x1, y0, y1, -0.05, 0.2, M['lightgrey'])
        for (a, bb, c, d) in ((x0 - 0.1, x1 + 0.1, y0 - 0.1, y0 + 0.12), (x0 - 0.1, x1 + 0.1, y1 - 0.12, y1 + 0.1),
                              (x0 - 0.1, x0 + 0.12, y0 - 0.1, y1 + 0.1), (x1 - 0.12, x1 + 0.1, y0 - 0.1, y1 + 0.1)):
            B(rf, a, bb, c, d, 0.2, 1.25, M['plaster'])
            B(rf, a, bb, c, d, 1.25, 1.33, M['charcoal'])
    bx0, bx1, by0, by1 = b['rect']
    H = 3.6
    nx, ny = max(2, int((bx1 - bx0) / 4.2) + 1), max(2, int((by1 - by0) / 4.2) + 1)
    for i in range(nx):
        for j in range(ny):
            px = bx0 + 0.4 + (bx1 - bx0 - 0.8) * i / (nx - 1)
            py = by0 + 0.4 + (by1 - by0 - 0.8) * j / (ny - 1)
            B(rf, px - 0.08, px + 0.08, py - 0.08, py + 0.08, 0.2, H, M['steel'])
    for j in range(ny):
        py = by0 + 0.4 + (by1 - by0 - 0.8) * j / (ny - 1)
        B(rf, bx0 + 0.2, bx1 - 0.2, py - 0.07, py + 0.07, H - 0.22, H, M['steel'])
    for i in range(nx):
        px = bx0 + 0.4 + (bx1 - bx0 - 0.8) * i / (nx - 1)
        B(rf, px - 0.05, px + 0.05, by0 + 0.2, by1 - 0.2, H, H + 0.12, M['steel'])
    pw = 1.05
    yy = by0 - 0.3
    while yy < by1 + 0.3:
        panel = B(rf, -(bx1 - bx0 + 0.6) / 2, (bx1 - bx0 + 0.6) / 2, -pw / 2, pw / 2, -0.02, 0.02, M['solar'])
        panel.rotation_euler = (math.radians(8), 0, 0)
        panel.location = ((bx0 + bx1) / 2, yy + pw / 2, H + 0.2)
        yy += pw + 0.04
    for k in range(int((bx1 - bx0) / 1.7)):
        xx = bx0 + 0.2 + k * 1.7
        B(rf, xx, xx + 0.035, by0 - 0.3, by1 + 0.3, H + 0.22, H + 0.25, M['steel'])
    B(rf, cx0 - 0.6, cx1 + 0.6, cy0 - 0.6, cy1 + 0.6, 0, H - 0.3, M['charcoal'])
    # ---- accent floors: bronze balcony fascia (instanced on a few floors, as on site)
    pl = new_mod(f'{bid}_planter')
    for i, f in enumerate(b['flats']):
        o, u, n, L = side_frame(f['rect'], f['views'][0]['dir'])
        P = 3.1 if L > 10 else 2.2
        b0 = P + 0.5
        m = (b0 + L - 0.35) / 2
        sbox(pl, o, u, n, b0, m - 0.12, 1.3, 1.36, -0.3, 0.14, M['wood'])
        sbox(pl, o, u, n, m + 0.12, L - 0.35, 1.3, 1.36, -0.3, 0.14, M['wood'])


for b in site['blocks']:
    build_block(b)

# random per-window value in UV.x (glass only) so the web shader can light windows at night
for gobj in glass_windows:
    me = gobj.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    v = random.random()
    for loop in me.uv_layers[0].data:
        loop.uv = (v, 0.5)
    gobj['keepuv'] = True

json.dump(anchors, open(os.path.join(ROOT, 'src', 'data', 'balconies.json'), 'w'))
exported = []
for name, objs in modules.items():
    glass_set = set(id(g) for g in glass_windows)
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name='UVMap')
    j = join(objs, name)
    if j:
        world_uv(j)
        exported.append(j)
export_glb(os.path.join(OUT, 'towers.glb'), exported)
