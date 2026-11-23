"""Vraj Platinum towers: per-block floor modules (instanced 14x in the web app), ground floor,
roof and planter modules. Facade language from the brochure renders: white balcony frames,
charcoal bands, rust/wood vertical cladding, black railings with glass, cascading creepers.

python3 blender/towers.py  ->  blender/out/towers.glb
"""
import sys, os, json, math, random
import bpy, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bcommon import *

random.seed(11)
site = json.load(open(os.path.join(ROOT, 'src', 'data', 'site.json')))
FH, GH = site['floorH'], site['groundH']

reset()
reset_mats()
M = dict(
    plaster=mat('plaster', '#DCDAD5', 0.85),
    white=mat('white', '#F5F4F0', 0.7),
    charcoal=mat('charcoal', '#4A4D53', 0.8),
    grey=mat('grey', '#8E9196', 0.85),
    rust=mat('rust', '#8A4630', 0.65),
    glass=mat('glass', '#26343D', 0.08, 0.7),
    rail=mat('rail', '#1E1F22', 0.45, 0.6),
    railglass=mat('railglass', '#9FB7C1', 0.05, alpha=0.35),
    stone=mat('stone', '#BFB19A', 0.8),
    wood=mat('wood', '#9A6A43', 0.6),
    leaf=mat('leaf', '#4C7A33', 0.8),
    leafdark=mat('leafdark', '#2F5A25', 0.85),
    solar=mat('solar', '#1B2A44', 0.2, 0.6),
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


def window(lst, o, u, n, a0, a1, z0, z1, mullions=2):
    g = sbox(lst, o, u, n, a0, a1, -0.04, 0.03, z0, z1, M['glass'])
    glass_windows.append(g)
    sbox(lst, o, u, n, a0 - 0.05, a1 + 0.05, -0.02, 0.06, z0 - 0.05, z0, M['rail'])
    sbox(lst, o, u, n, a0 - 0.05, a1 + 0.05, -0.02, 0.06, z1, z1 + 0.05, M['rail'])
    for i in range(1, mullions):
        a = a0 + (a1 - a0) * i / mullions
        sbox(lst, o, u, n, a - 0.025, a + 0.025, -0.02, 0.06, z0, z1, M['rail'])


def balcony(lst, o, u, n, a0, a1, depth, with_frames=True):
    sbox(lst, o, u, n, a0, a1, 0, depth, -0.05, 0.12, M['white'])                         # slab
    sbox(lst, o, u, n, a0, a1, depth - 0.06, depth - 0.02, 0.12, 1.0, M['railglass'])     # glass
    sbox(lst, o, u, n, a0, a1, depth - 0.08, depth, 1.0, 1.06, M['rail'])                  # top rail
    for a in [a0 + 0.08 + i * 1.2 for i in range(int((a1 - a0) / 1.2) + 1)] + [a1 - 0.08]:
        sbox(lst, o, u, n, a - 0.02, a + 0.02, depth - 0.08, depth - 0.04, 0.12, 1.0, M['rail'])
    if with_frames:
        for a in (a0 - 0.22, a1):
            sbox(lst, o, u, n, a, a + 0.22, 0, depth + 0.05, -0.05, FH - 0.05, M['white'])


def facade(lst, r, side, style, flat_idx):
    o, u, n, L = side_frame(r, side)
    if style == 'primary':
        # charcoal end band, rust cladding, glazing behind a deep balcony frame
        sbox(lst, o, u, n, 0, 0.95, 0, 0.5, 0, FH, M['charcoal'])
        sbox(lst, o, u, n, L - 1.05, L, 0, 0.35, 0, FH, M['rust'])
        b0, b1 = 1.1, L - 1.3
        window(lst, o, u, n, b0 + 0.2, b1 - 0.2, 0.15, 2.45, mullions=max(2, int((b1 - b0) / 1.6)))
        balcony(lst, o, u, n, b0, b1, 1.25)
    elif style == 'end':
        sbox(lst, o, u, n, 0, 0.5, 0, 0.3, 0, FH, M['charcoal'])
        mid = L * 0.55
        window(lst, o, u, n, 0.9, mid - 0.4, 0.8, 2.3, 2)
        window(lst, o, u, n, mid + 0.3, L - 0.8, 0.15, 2.45, 2)
        balcony(lst, o, u, n, mid + 0.1, L - 0.5, 1.0)
        sbox(lst, o, u, n, mid - 0.35, mid + 0.05, 0, 0.35, 0, FH, M['rust'])
    else:  # secondary: service side with small windows
        for a in (L * 0.25, L * 0.7):
            window(lst, o, u, n, a - 0.35, a + 0.35, 1.6, 2.3, 1)
        sbox(lst, o, u, n, L * 0.42, L * 0.55, 0, 0.18, 0, FH, M['charcoal'])


def build_block(b):
    bid = b['id']
    rects = [f['rect'] for f in b['flats']]
    core = b['core']
    floor = new_mod(f'{bid}_floor')
    # core
    B(floor, core[0], core[1], core[2], core[3], 0, FH, M['charcoal'])
    for i, f in enumerate(b['flats']):
        r = f['rect']
        x0, x1, y0, y1 = r
        B(floor, x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, 0.0, FH - 0.18, M['plaster'])
        B(floor, x0 - 0.12, x1 + 0.12, y0 - 0.12, y1 + 0.12, FH - 0.2, FH, M['white'])
        others = [q for q in rects if q is not r] + [core]
        dirs = [v['dir'] for v in f['views']]
        for side in 'NSEW':
            if touching(r, others, side):
                continue
            style = 'primary' if side == dirs[0] else 'end' if side in dirs[1:] else 'secondary'
            facade(floor, r, side, style, i)
    # ground floor (stilts + lobby + ceiling)
    g = new_mod(f'{bid}_ground')
    for f in b['flats']:
        x0, x1, y0, y1 = f['rect']
        B(g, x0 - 0.12, x1 + 0.12, y0 - 0.12, y1 + 0.12, GH - 0.35, GH, M['white'])
        B(g, x0, x1, y0, y1, GH - 0.36, GH - 0.35, M['ceiling'])
        nx, ny = max(2, int((x1 - x0) / 5.5) + 1), max(2, int((y1 - y0) / 5.5) + 1)
        for i in range(nx):
            for j in range(ny):
                cx_ = x0 + 0.35 + (x1 - x0 - 0.7) * i / (nx - 1)
                cy_ = y0 + 0.35 + (y1 - y0 - 0.7) * j / (ny - 1)
                B(g, cx_ - 0.23, cx_ + 0.23, cy_ - 0.3, cy_ + 0.3, 0, GH - 0.35, M['grey'])
    cx0, cx1, cy0, cy1 = core
    B(g, cx0, cx1, cy0, cy1, 0, GH, M['stone'])
    # glass lobby box around the core
    lx0, lx1, ly0, ly1 = cx0 - 2.2, cx1 + 2.2, cy0 - 0.6, cy1 + 0.6
    lob = B(g, lx0, lx1, ly0, ly1, 0, GH - 0.36, M['glass'])
    glass_windows.append(lob)
    B(g, lx0 + 0.3, lx1 - 0.3, ly0 + 0.3, ly1 - 0.3, GH - 0.42, GH - 0.37, M['lobbyglow'])
    # roof
    rf = new_mod(f'{bid}_roof')
    for i, f in enumerate(b['flats']):
        x0, x1, y0, y1 = f['rect']
        B(rf, x0 - 0.12, x1 + 0.12, y0 - 0.12, y1 + 0.12, -0.05, 0.25, M['white'])
        for (a, bb, c, d) in ((x0 - 0.12, x1 + 0.12, y0 - 0.12, y0 + 0.1), (x0 - 0.12, x1 + 0.12, y1 - 0.1, y1 + 0.12),
                              (x0 - 0.12, x0 + 0.1, y0 - 0.12, y1 + 0.12), (x1 - 0.1, x1 + 0.12, y0 - 0.12, y1 + 0.12)):
            B(rf, a, bb, c, d, 0.25, 1.5, M['charcoal'])
        # solar array (south tilted)
        px0, px1, py0, py1 = x0 + 1.0, x1 - 1.0, y0 + 1.0, y1 - 1.0
        rows = max(1, int((py1 - py0) / 2.3))
        for rr in range(rows):
            yy = py0 + rr * (py1 - py0) / rows
            panel = B(rf, -(px1 - px0) / 2, (px1 - px0) / 2, -0.8, 0.8, -0.025, 0.025, M['solar'])
            panel.rotation_euler = (math.radians(21), 0, 0)
            panel.location = ((px0 + px1) / 2, yy + 0.8, 0.72)
            B(rf, px0, px0 + 0.06, yy + 0.2, yy + 0.3, 0.25, 0.75, M['rail'])
            B(rf, px1 - 0.06, px1, yy + 0.2, yy + 0.3, 0.25, 0.75, M['rail'])
    # stair/lift heads + tank
    B(rf, cx0 - 0.6, cx1 + 0.6, cy0 - 0.6, cy1 + 0.6, 0, 3.6, M['charcoal'])
    B(rf, cx0 - 0.8, cx1 + 0.8, cy0 - 0.8, cy1 + 0.8, 3.6, 3.85, M['white'])
    B(rf, cx0, cx1, cy0 + 0.4, cy1 - 0.4, 3.85, 5.3, M['grey'])
    # planters with cascading creepers (instanced on a few floors)
    pl = new_mod(f'{bid}_planter')
    for i, f in enumerate(b['flats']):
        if i % 2:
            continue
        o, u, n, L = side_frame(f['rect'], f['views'][0]['dir'])
        a0, a1 = 1.1, min(L - 1.3, 1.1 + 4.5)
        sbox(pl, o, u, n, a0, a1, 1.25, 1.75, 0.0, 0.7, M['charcoal'])
        steps = int((a1 - a0) / 0.22)
        for k in range(steps):
            a = a0 + 0.1 + k * 0.22
            ln = 0.8 + random.random() * 2.2
            sbox(pl, o, u, n, a - 0.09, a + 0.09, 1.55 + random.random() * 0.15, 1.8 + random.random() * 0.12,
                 0.7 - ln, 0.75, M['leaf' if k % 3 else 'leafdark'])
        for k in range(int((a1 - a0) / 0.35)):
            a = a0 + 0.2 + k * 0.35
            pl.append(sphere(f'bush{bid}{i}{k}', 0.28, o[0] + u[0] * a + n[0] * 1.5, o[1] + u[1] * a + n[1] * 1.5, 0.85, M['leaf'], sub=1, sz=0.8))


for b in site['blocks']:
    build_block(b)

# random per-window value in UV.x so the web shader can light windows at night
for gobj in glass_windows:
    me = gobj.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    v = random.random()
    for loop in me.uv_layers[0].data:
        loop.uv = (v, 0.5)

exported = []
for name, objs in modules.items():
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name='UVMap')
    j = join(objs, name)
    if j:
        exported.append(j)
export_glb(os.path.join(OUT, 'towers.glb'), exported)
