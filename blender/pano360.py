"""Builds a furnished, light-baked 'dollhouse' interior for a Vraj Platinum unit type.

Usage:  python3 blender/interiors.py A [--res 2048] [--samples 64] [--nobake]
Output: blender/out/interior_<T>.glb  (+ interior_<T>_bake.png)
Palette follows the real Vraj Platinum sample flat (video walkthrough): white large-format
vitrified tiles, burnt-orange sofa, grey patterned armchairs, oak slat TV wall, black granite counter.
"""
import sys, os, json, math, random, time
import numpy as np
import bpy, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bcommon import *

args = sys.argv[1:]
T = args[0] if args else 'A'
RES = int(args[args.index('--res') + 1]) if '--res' in args else 2048
SAMPLES = int(args[args.index('--samples') + 1]) if '--samples' in args else 64
NOBAKE = '--nobake' in args
random.seed(7)

plans = json.load(open(os.path.join(ROOT, 'src', 'data', 'plans.json')))
P = plans[T]
MPP = P['mpp']
xs = [r['r'][0] for r in P['rooms']] + [r['r'][2] for r in P['rooms']]
ys = [r['r'][1] for r in P['rooms']] + [r['r'][3] for r in P['rooms']]
CX, CY = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def X(px):
    return (px - CX) * MPP


def Y(py):
    return -(py - CY) * MPP


def rect_m(r, shrink=0.0):
    x0, x1 = sorted((X(r[0]), X(r[2])))
    y0, y1 = sorted((Y(r[1]), Y(r[3])))
    return [x0 + shrink, x1 - shrink, y0 + shrink, y1 - shrink]


reset()
reset_mats()
scene = bpy.context.scene
col = scene.collection
H = 2.95  # full storey for the 360 balcony render

# ---------------------------------------------------------------- materials
M = dict(
    wall=mat('wall', '#EEECE8', 0.9),
    cap=mat('wallcap', '#2F3033', 0.8),
    base=mat('base', '#F4F2EE', 0.9),
    tile=mat('tile', '#EDEBE7', 0.25, fn=proc_tiles('#EFEDEA', '#E8E5E0', '#BDB8B1', 0.61, 1.22)),
    wetfloor=mat('wetfloor', '#7A7A76', 0.5, fn=proc_tiles('#7C7C78', '#74746F', '#5A5A57', 0.3, 0.3, vein=False)),
    deck=mat('deck', '#8A5A3B', 0.6, fn=proc_wood('#7A4C30', '#A06E4A', 4, 'X')),
    soil=mat('soil', '#3B2A1E', 1.0, fn=proc_noise('#2E2118', '#4A3626', 60)),
    leaf=mat('leaf', '#3F6B2E', 0.7, fn=proc_noise('#2F5A22', '#6C9A3E', 18)),
    leaf2=mat('leaf2', '#5C8A3A', 0.7, fn=proc_noise('#4E7E30', '#8DB45A', 14)),
    concrete=mat('concrete', '#B9B6B0', 0.9, fn=proc_noise('#A9A69F', '#C8C5BF', 25)),
    sofa=mat('sofa', '#B4532B', 0.9, fn=proc_noise('#A84B25', '#BE5C31', 80)),
    grey_fab=mat('greyfab', '#8C8C8A', 0.95, fn=proc_noise('#6E6E6C', '#B5B5B2', 140)),
    beige_fab=mat('beigefab', '#D9CFC0', 0.95, fn=proc_noise('#D2C7B6', '#E2D9CC', 90)),
    linen=mat('linen', '#F3F1EC', 0.9),
    duvet=mat('duvet', '#9C9489', 0.95, fn=proc_noise('#8F877C', '#ABA398', 60)),
    walnut=mat('walnut', '#5A3A26', 0.5, fn=proc_wood('#4A2E1D', '#6E4A31', 5)),
    oak=mat('oak', '#C9A57C', 0.5, fn=proc_wood('#BE9868', '#D8B98F', 5, 'Y')),
    laminate=mat('laminate', '#E9E5DE', 0.4),
    lgrey=mat('lgrey', '#C4C3C0', 0.4),
    dgrey=mat('dgrey', '#3E4044', 0.5),
    orange=mat('orange', '#C2602F', 0.45),
    black=mat('black', '#151515', 0.35),
    granite=mat('granite', '#1C1C1E', 0.2, fn=proc_noise('#111113', '#3A3A3D', 220)),
    rust=mat('rust', '#7B3A22', 0.35, fn=proc_tiles('#7E3C24', '#6F321D', '#3B1E14', 0.2, 0.6, vein=False)),
    steel=mat('steel', '#B8BBBE', 0.3, 0.9),
    ceramic=mat('ceramic', '#F7F7F5', 0.15),
    screen=mat('screen', '#0B0C10', 0.1),
    rug=mat('rug', '#A9A39A', 1.0, fn=proc_noise('#9C968C', '#BDB7AD', 160)),
    rug_warm=mat('rugwarm', '#CFC6B8', 1.0, fn=proc_noise('#C3B9AA', '#DCD3C6', 160)),
    led=mat('led', '#FFD7A0', 0.5, emit='#FFC27A', emit_strength=6),
    lampshade=mat('shade', '#F2E6D2', 0.8, emit='#FFD9A8', emit_strength=2.5),
    pot=mat('pot', '#D8D4CC', 0.6),
    frame=mat('frame', '#2A2B2E', 0.4, 0.6),
)
GLASS = mat('glass', '#BFD6E0', 0.05, alpha=0.25)

bake_objs = []
glass_objs = []


def add(o):
    bake_objs.append(o)
    return o


# ---------------------------------------------------------------- grid walls
CELL = 0.025
rooms = [dict(r, m=rect_m(r['r'], 0.03)) for r in P['rooms']]
allx = [v for r in rooms for v in r['m'][:2]]
ally = [v for r in rooms for v in r['m'][2:]]
gx0, gy0 = min(allx) - 0.35, min(ally) - 0.35
gx1, gy1 = max(allx) + 0.35, max(ally) + 0.35
NX, NY = int((gx1 - gx0) / CELL) + 1, int((gy1 - gy0) / CELL) + 1
lab = -np.ones((NX, NY), dtype=np.int32)
cx = gx0 + (np.arange(NX) + 0.5) * CELL
cy = gy0 + (np.arange(NY) + 0.5) * CELL
for i, r in enumerate(rooms):
    x0, x1, y0, y1 = r['m']
    lab[np.ix_((cx >= x0) & (cx < x1), (cy >= y0) & (cy < y1))] = i

INTERIOR = {'living', 'kitchen', 'bed', 'toilet', 'wash', 'pass'}
kinds = np.array([r['kind'] for r in rooms])
inside = lab >= 0
# dilation for exterior walls
from scipy import ndimage  # noqa
R_EXT = int(round(0.2 / CELL))
st = np.ones((2 * R_EXT + 1, 2 * R_EXT + 1), bool)
near = ndimage.binary_dilation(inside, structure=st)
wall = near & ~inside
# classify wall cells as full or parapet by neighbouring room kinds
interior_mask = np.isin(lab, [i for i, r in enumerate(rooms) if r['kind'] in INTERIOR])
near_int = ndimage.binary_dilation(interior_mask, structure=np.ones((2 * R_EXT + 3, 2 * R_EXT + 3), bool))
full = wall & near_int
para = wall & ~near_int

cls = np.zeros((NX, NY), dtype=np.int8)  # 0 none,1 full,2 parapet,3 window,4 lowwin,5 vent,6 door,7 grill
cls[full] = 1
cls[para] = 2


def carve(c, o, w, depth, val, only=(1, 2)):
    x, y = X(c[0]), Y(c[1])
    if o == 'h':
        xr, yr = (x - w / 2, x + w / 2), (y - depth / 2, y + depth / 2)
    else:
        xr, yr = (x - depth / 2, x + depth / 2), (y - w / 2, y + w / 2)
    m = np.zeros_like(cls, bool)
    m[np.ix_((cx >= xr[0]) & (cx < xr[1]), (cy >= yr[0]) & (cy < yr[1]))] = True
    m &= np.isin(cls, only)
    cls[m] = val
    return m


for d in P['doors']:
    carve(d['c'], d['o'], d['w'], 0.6, 6)
for wdef in P['windows']:
    v = 5 if wdef.get('vent') else 4 if wdef.get('low') else 7 if wdef.get('grill') else 3
    carve(wdef['c'], wdef['o'], wdef['w'], 0.6, v, only=(1,))


def greedy(mask):
    m = mask.copy()
    out = []
    for i in range(NX):
        j = 0
        while j < NY:
            if not m[i, j]:
                j += 1
                continue
            j2 = j
            while j2 + 1 < NY and m[i, j2 + 1]:
                j2 += 1
            i2 = i
            while i2 + 1 < NX and m[i2 + 1, j:j2 + 1].all():
                i2 += 1
            m[i:i2 + 1, j:j2 + 1] = False
            out.append((gx0 + i * CELL, gx0 + (i2 + 1) * CELL, gy0 + j * CELL, gy0 + (j2 + 1) * CELL))
            j = j2 + 1
    return out


def wall_boxes(rects, z0, z1, name, glass=None, frame=False, grill=False):
    for k, (x0, x1, y0, y1) in enumerate(rects):
        add(box(f'{name}{k}', x0, x1, y0, y1, z0, z1, M['wall'], top=M['cap'] if abs(z1 - H) < 1e-3 or z1 < 1.2 else None))


for k, (x0, x1, y0, y1) in enumerate(greedy(cls == 1)):
    add(box(f'w{k}', x0, x1, y0, y1, 0, H, M['wall'], top=M['cap']))
for k, (x0, x1, y0, y1) in enumerate(greedy(cls == 2)):
    add(box(f'p{k}', x0, x1, y0, y1, 0, 0.55, M['wall'], top=M['cap']))


def window_set(val, sill, head, kind):
    for k, (x0, x1, y0, y1) in enumerate(greedy(cls == val)):
        add(box(f'ws{val}_{k}', x0, x1, y0, y1, 0, sill, M['wall'], top=M['cap']))
        add(box(f'wh{val}_{k}', x0, x1, y0, y1, head, H, M['wall'], top=M['cap']))
        horiz = (x1 - x0) > (y1 - y0)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if horiz:
            g = box(f'gl{val}_{k}', x0, x1, my - 0.008, my + 0.008, sill, head, GLASS)
            add(box(f'fr{val}_{k}a', x0, x1, my - 0.03, my + 0.03, sill, sill + 0.05, M['frame']))
            add(box(f'fr{val}_{k}b', x0, x1, my - 0.03, my + 0.03, head - 0.05, head, M['frame']))
            add(box(f'fr{val}_{k}c', mx - 0.025, mx + 0.025, my - 0.03, my + 0.03, sill, head, M['frame']))
            if kind == 'grill':
                for t in np.arange(x0 + 0.1, x1, 0.12):
                    add(box(f'gr{val}_{k}_{t:.2f}', t - 0.01, t + 0.01, y0, y1, sill, head, M['frame']))
        else:
            g = box(f'gl{val}_{k}', mx - 0.008, mx + 0.008, y0, y1, sill, head, GLASS)
            add(box(f'fr{val}_{k}a', mx - 0.03, mx + 0.03, y0, y1, sill, sill + 0.05, M['frame']))
            add(box(f'fr{val}_{k}b', mx - 0.03, mx + 0.03, y0, y1, head - 0.05, head, M['frame']))
            add(box(f'fr{val}_{k}c', mx - 0.03, mx + 0.03, my - 0.025, my + 0.025, sill, head, M['frame']))
            if kind == 'grill':
                for t in np.arange(y0 + 0.1, y1, 0.12):
                    add(box(f'gr{val}_{k}_{t:.2f}', x0, x1, t - 0.01, t + 0.01, sill, head, M['frame']))
        if kind != 'grill':
            glass_objs.append(g)
        else:
            bpy.data.objects.remove(g)


window_set(3, 0.9, 2.1, 'win')
window_set(4, 0.02, 2.2, 'win')
window_set(5, 1.75, 2.15, 'vent')
window_set(7, 0.9, 2.1, 'grill')
for k, (x0, x1, y0, y1) in enumerate(greedy(cls == 6)):
    add(box(f'dl{k}', x0, x1, y0, y1, 2.1, H, M['wall'], top=M['cap']))

# ---------------------------------------------------------------- floors / base
solid = inside | (cls > 0)
for k, (x0, x1, y0, y1) in enumerate(greedy(solid)):
    add(box(f'base{k}', x0, x1, y0, y1, -0.32, -0.012, M['base']))
FLOORMAT = {'living': 'tile', 'kitchen': 'tile', 'bed': 'tile', 'pass': 'tile', 'toilet': 'wetfloor', 'wash': 'wetfloor', 'balcony': 'deck', 'fb': 'soil'}
for i, r in enumerate(rooms):
    x0, x1, y0, y1 = r['m']
    e = 0.035
    z1 = 0.0 if r['kind'] != 'fb' else 0.42
    add(box(f'floor_{r["id"]}', x0 - e, x1 + e, y0 - e, y1 + e, -0.012, z1, M[FLOORMAT[r['kind']]]))
# door thresholds (floor under carved door cells)
for k, (x0, x1, y0, y1) in enumerate(greedy(cls == 6)):
    add(box(f'th{k}', x0, x1, y0, y1, -0.012, 0.004, M['tile']))

# ---------------------------------------------------------------- furniture


def room_at(x, y):
    for r in rooms:
        x0, x1, y0, y1 = r['m']
        if x0 - 0.05 <= x <= x1 + 0.05 and y0 - 0.05 <= y <= y1 + 0.05:
            return r
    return None


class G:
    """Collects local-space parts, then places them (front = +Y)."""

    def __init__(s, name):
        s.name, s.parts = name, []

    def b(s, *a, **k):
        o = box(f'{s.name}_{len(s.parts)}', *a, **k)
        s.parts.append(o)
        return o

    def c(s, *a, **k):
        o = cyl(f'{s.name}_{len(s.parts)}', *a, **k)
        s.parts.append(o)
        return o

    def s(s_, *a, **k):
        o = sphere(f'{s_.name}_{len(s_.parts)}', *a, **k)
        s_.parts.append(o)
        return o

    def place(s, x, y, rot):
        a = -math.radians(rot)
        for o in s.parts:
            o.matrix_world = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(a, 4, 'Z') @ o.matrix_world
            add(o)


from mathutils import Matrix  # noqa


def f_bed(g, w=1.8):
    L = 2.1
    g.b(-w / 2 - 0.05, w / 2 + 0.05, -L / 2, L / 2, 0.06, 0.34, M['walnut'], bevel=0.01)
    g.b(-w / 2 - 0.15, w / 2 + 0.15, -L / 2 - 0.08, -L / 2 + 0.02, 0.0, 1.15, M['beige_fab'], bevel=0.03)
    g.b(-w / 2, w / 2, -L / 2 + 0.05, L / 2 - 0.04, 0.34, 0.56, M['linen'], bevel=0.04)
    g.b(-w / 2 - 0.03, w / 2 + 0.03, -L / 2 + 0.75, L / 2 - 0.02, 0.5, 0.62, M['duvet'], bevel=0.05)
    g.b(-w / 2 - 0.02, w / 2 + 0.02, L / 2 - 0.55, L / 2 - 0.2, 0.6, 0.64, M['dgrey'], bevel=0.02)
    for sx in (-1, 1):
        g.b(sx * w / 4 - 0.3, sx * w / 4 + 0.3, -L / 2 + 0.1, -L / 2 + 0.45, 0.55, 0.72, M['linen'], bevel=0.06)
    g.b(-0.25, 0.25, -L / 2 + 0.38, -L / 2 + 0.6, 0.56, 0.7, M['orange'], bevel=0.05)
    return L


def f_nightstand(g):
    g.b(-0.23, 0.23, -0.2, 0.2, 0.0, 0.5, M['walnut'], bevel=0.008)
    g.c(0.07, 0.5, 0.78, M['dgrey'], x=0.05, y=-0.05, seg=12)
    g.c(0.14, 0.7, 0.92, M['lampshade'], x=0.05, y=-0.05, seg=20, r2=0.11)
    return 0.4


def f_wardrobe(g, L=1.6):
    g.b(-L / 2, L / 2, -0.3, 0.3, 0.0, 2.2, M['oak'], bevel=0.005)
    n = max(2, int(round(L / 0.5)))
    for i in range(1, n):
        x = -L / 2 + i * L / n
        g.b(x - 0.004, x + 0.004, 0.3, 0.305, 0.05, 2.15, M['dgrey'])
    for i in range(n):
        x = -L / 2 + (i + 0.5) * L / n + (0.18 if i % 2 == 0 else -0.18) * L / n
        g.b(x - 0.008, x + 0.008, 0.3, 0.33, 0.9, 1.35, M['black'])
    return 0.6


def f_sofa3(g):
    W, D = 2.2, 0.92
    g.b(-W / 2, W / 2, -D / 2, D / 2, 0.08, 0.4, M['sofa'], bevel=0.04)
    g.b(-W / 2, W / 2, -D / 2, -D / 2 + 0.24, 0.35, 0.82, M['sofa'], bevel=0.07)
    for sx in (-1, 1):
        g.b(sx * W / 2 - 0.13 * sx - 0.065, sx * W / 2 - 0.13 * sx + 0.065, -D / 2, D / 2, 0.08, 0.6, M['sofa'], bevel=0.05)
    for i in range(3):
        x = -0.62 + i * 0.62
        g.b(x - 0.3, x + 0.3, -D / 2 + 0.22, D / 2 - 0.02, 0.4, 0.52, M['sofa'], bevel=0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.b(sx * (W / 2 - 0.1) - 0.02, sx * (W / 2 - 0.1) + 0.02, sy * (D / 2 - 0.1) - 0.02, sy * (D / 2 - 0.1) + 0.02, 0, 0.08, M['black'])
    g.b(0.45, 0.85, -D / 2 + 0.22, -D / 2 + 0.34, 0.5, 0.86, M['beige_fab'], bevel=0.05)
    return D


def f_armchair(g):
    g.b(-0.4, 0.4, -0.4, 0.4, 0.1, 0.42, M['grey_fab'], bevel=0.05)
    g.b(-0.4, 0.4, -0.4, -0.22, 0.4, 0.85, M['grey_fab'], bevel=0.06)
    for sx in (-1, 1):
        g.b(sx * 0.34 - 0.06, sx * 0.34 + 0.06, -0.4, 0.4, 0.1, 0.62, M['grey_fab'], bevel=0.04)
    g.c(0.02, 0, 0.1, M['black'], x=0.3, y=0.3, seg=8)
    g.c(0.02, 0, 0.1, M['black'], x=-0.3, y=0.3, seg=8)
    return 0.8


def f_coffee(g):
    g.c(0.4, 0.38, 0.42, M['ceramic'], seg=40)
    g.c(0.03, 0.0, 0.38, M['black'], seg=10)
    g.c(0.28, 0.0, 0.02, M['black'], seg=24)
    g.c(0.3, 0.28, 0.32, M['ceramic'], x=0.45, y=0.3, seg=36)
    g.c(0.025, 0.0, 0.28, M['black'], x=0.45, y=0.3, seg=10)
    g.c(0.08, 0.42, 0.5, M['pot'], x=0.05, y=0.05, seg=16)
    g.s(0.09, 0.05, 0.05, 0.56, M['leaf2'], sub=1)
    return 0.8


def f_tvunit(g, L=1.9):
    g.b(-L / 2 - 0.25, L / 2 + 0.25, -0.22, -0.18, 0.0, 2.45, M['oak'])
    for x in np.arange(-L / 2 - 0.2, L / 2 + 0.25, 0.07):
        g.b(x - 0.015, x + 0.015, -0.18, -0.15, 0.0, 2.45, M['oak'])
    g.b(-L / 2, L / 2, -0.15, 0.25, 0.18, 0.5, M['lgrey'], bevel=0.02)
    g.b(-L / 4, L / 4, 0.25, 0.262, 0.22, 0.46, M['orange'], bevel=0.005)
    g.b(-0.7, 0.7, -0.15, -0.1, 1.05, 1.85, M['screen'], bevel=0.005)
    g.c(0.05, 0.5, 0.78, M['ceramic'], x=L / 2 - 0.2, y=0.05, seg=12)
    g.s(0.08, L / 2 - 0.2, 0.05, 0.86, M['leaf2'], sub=1, sz=1.6)
    return 0.47


def f_lamp(g):
    for a in (0, 2.1, 4.2):
        g.b(math.cos(a) * 0.18 - 0.012, math.cos(a) * 0.18 + 0.012, math.sin(a) * 0.18 - 0.012, math.sin(a) * 0.18 + 0.012, 0, 1.25, M['black'])
    g.c(0.16, 1.25, 1.55, M['black'], seg=20, r2=0.2)
    g.c(0.15, 1.27, 1.30, M['led'], seg=20)
    return 0.4


def f_plant(g, s=1.0):
    g.c(0.18 * s, 0.0, 0.42 * s, M['pot'], seg=20, r2=0.14 * s)
    for i in range(6):
        a = i * 1.05
        g.s(0.17 * s, math.cos(a) * 0.11 * s, math.sin(a) * 0.11 * s, (0.72 + 0.2 * (i % 3)) * s, M['leaf' if i % 2 else 'leaf2'], sub=2, sz=1.5)
    return 0.36


def f_kitchen(g, L=2.0, hob=False, sink=False):
    g.b(-L / 2, L / 2, -0.3, 0.3, 0.1, 0.86, M['laminate'], bevel=0.004)
    g.b(-L / 2, L / 2, -0.25, 0.26, 0.0, 0.1, M['dgrey'])
    n = max(2, int(L / 0.5))
    for i in range(1, n):
        x = -L / 2 + i * L / n
        g.b(x - 0.003, x + 0.003, 0.3, 0.305, 0.12, 0.84, M['lgrey'])
    g.b(-L / 2 - 0.01, L / 2 + 0.01, -0.31, 0.32, 0.86, 0.9, M['granite'], bevel=0.004)
    g.b(-L / 2, L / 2, -0.32, -0.3, 0.9, 1.5, M['rust'])
    g.b(-L / 2, L / 2, -0.32, 0.03, 1.5, 2.2, M['dgrey'], bevel=0.004)
    g.b(-L / 2 + 0.05, L / 2 - 0.05, -0.02, 0.02, 1.48, 1.5, M['led'])
    if hob:
        g.b(-0.3 - L / 5, 0.3 - L / 5, -0.22, 0.22, 0.9, 0.91, M['black'])
        for dx in (-0.15, 0.15):
            for dy in (-0.1, 0.1):
                g.c(0.06, 0.91, 0.925, M['dgrey'], x=dx - L / 5, y=dy, seg=16)
    if sink:
        sx = L / 5 if hob else 0
        g.b(sx - 0.35, sx + 0.35, -0.2, 0.2, 0.86, 0.905, M['steel'])
        g.b(sx - 0.3, sx + 0.3, -0.16, 0.16, 0.8, 0.906, M['dgrey'])
        g.c(0.015, 0.9, 1.2, M['steel'], x=sx, y=-0.24, seg=10)
    return 0.62


def f_fridge(g):
    g.b(-0.36, 0.36, -0.35, 0.35, 0.0, 1.85, M['steel'], bevel=0.02)
    g.b(0.25, 0.28, 0.35, 0.38, 0.9, 1.5, M['dgrey'])
    return 0.7


def f_dining(g):
    g.b(-0.62, 0.62, -0.42, 0.42, 0.72, 0.76, M['ceramic'], bevel=0.01)
    for sx in (-1, 1):
        g.b(sx * 0.45 - 0.025, sx * 0.45 + 0.025, -0.3, 0.3, 0.0, 0.72, M['black'])
    for x in (-0.3, 0.3):
        for sy in (-1, 1):
            yy = sy * 0.62
            g.b(x - 0.22, x + 0.22, yy - 0.21, yy + 0.21, 0.42, 0.47, M['grey_fab'], bevel=0.02)
            g.b(x - 0.22, x + 0.22, yy + sy * 0.17, yy + sy * 0.21, 0.42, 0.9, M['grey_fab'], bevel=0.02)
            g.b(x - 0.015, x + 0.015, yy - 0.015, yy + 0.015, 0, 0.42, M['black'])
    g.c(0.09, 0.76, 0.84, M['oak'], seg=16)
    return 1.6


def f_store(g, L=2.0):
    g.b(-L / 2, L / 2, -0.17, 0.17, 0.0, 2.1, M['laminate'], bevel=0.004)
    n = max(2, int(L / 0.45))
    for i in range(1, n):
        x = -L / 2 + i * L / n
        g.b(x - 0.003, x + 0.003, 0.17, 0.175, 0.05, 2.05, M['lgrey'])
    return 0.34


def f_washer(g):
    g.b(-0.3, 0.3, -0.3, 0.3, 0.0, 0.85, M['ceramic'], bevel=0.02)
    g.b(-0.2, 0.2, 0.3, 0.315, 0.25, 0.65, M['dgrey'], bevel=0.01)
    g.b(-0.25, 0.25, 0.3, 0.31, 0.72, 0.8, M['lgrey'])
    return 0.6


def f_wc(g):
    g.b(-0.19, 0.19, -0.35, -0.18, 0.4, 0.85, M['ceramic'], bevel=0.03)
    g.c(0.19, 0.0, 0.4, M['ceramic'], y=0.05, seg=24)
    g.c(0.2, 0.4, 0.43, M['ceramic'], y=0.05, seg=24)
    return 0.6


def f_basin(g):
    g.b(-0.25, 0.25, -0.22, 0.22, 0.5, 0.82, M['walnut'], bevel=0.01)
    g.c(0.17, 0.82, 0.92, M['ceramic'], seg=24)
    g.b(-0.25, 0.25, -0.24, -0.22, 1.1, 1.7, M['steel'])
    return 0.44


def f_balcony(g):
    g.c(0.22, 0.45, 0.48, M['black'], seg=24)
    g.c(0.02, 0.0, 0.45, M['black'], seg=8)
    for sx in (-1, 1):
        g.b(sx * 0.42 - 0.2, sx * 0.42 + 0.2, -0.2, 0.2, 0.0, 0.4, M['walnut'], bevel=0.03)
        g.b(sx * 0.42 - 0.2, sx * 0.42 + 0.2, -0.24, -0.16, 0.0, 0.75, M['walnut'], bevel=0.02)
        g.b(sx * 0.42 - 0.18, sx * 0.42 + 0.18, -0.16, 0.18, 0.4, 0.48, M['beige_fab'], bevel=0.03)
    return 0.6


BUILD = dict(bed=f_bed, nightstand=f_nightstand, wardrobe=f_wardrobe, sofa3=f_sofa3, armchair=f_armchair,
             coffee=f_coffee, tvunit=f_tvunit, lamp=f_lamp, plant=f_plant, kitchen_run=f_kitchen,
             fridge=f_fridge, dining4=f_dining, store=f_store, washer=f_washer, wc=f_wc, basin=f_basin,
             balcony_set=f_balcony)
SNAP = {'bed', 'nightstand', 'wardrobe', 'sofa3', 'tvunit', 'kitchen_run', 'fridge', 'store', 'washer', 'wc', 'basin'}

for k, f in enumerate(P['furniture']):
    t = f['t']
    if t == 'planters':
        x0, x1, y0, y1 = rect_m(f['r'], 0.03)
        n = max(2, int(max(x1 - x0, y1 - y0) / 0.32))
        horiz = (x1 - x0) > (y1 - y0)
        for i in range(n):
            u = (i + 0.5) / n
            px = x0 + (x1 - x0) * u if horiz else (x0 + x1) / 2
            py = (y0 + y1) / 2 if horiz else y0 + (y1 - y0) * u
            rr = 0.12 + random.random() * 0.06
            for j in range(3):
                ox, oy = (random.random() - 0.5) * 0.12, (random.random() - 0.5) * 0.12
                add(sphere(f'shrub{k}_{i}_{j}', rr * (1 - j * 0.15), px + ox, py + oy, 0.48 + rr * (0.5 + j * 0.45), M['leaf' if (i + j) % 2 else 'leaf2'], sub=2, sz=1.15))
        continue
    if t == 'rug':
        x, y = X(f['c'][0]), Y(f['c'][1])
        w, d = f['s']
        add(box(f'rug{k}', x - w / 2, x + w / 2, y - d / 2, y + d / 2, 0, 0.012, M['rug_warm' if f.get('warm') else 'rug']))
        continue
    g = G(f'{t}{k}')
    fn = BUILD[t]
    if t == 'bed':
        depth = fn(g, f.get('w', 1.8))
    elif t in ('wardrobe', 'tvunit', 'store'):
        depth = fn(g, f.get('len', 1.6))
    elif t == 'kitchen_run':
        depth = fn(g, f.get('len', 2.0), f.get('hob', False), f.get('sink', False))
    else:
        depth = fn(g)
    rot = f.get('rot', 0)
    x, y = X(f['c'][0]), Y(f['c'][1])
    if t in SNAP:
        r = room_at(x, y)
        if r:
            x0, x1, y0, y1 = r['m']
            bx, by = -round(math.sin(math.radians(rot))), -round(math.cos(math.radians(rot)))
            gap = 0.01
            if bx < 0: x = x0 + depth / 2 + gap
            if bx > 0: x = x1 - depth / 2 - gap
            if by < 0: y = y0 + depth / 2 + gap
            if by > 0: y = y1 - depth / 2 - gap
    g.place(x, y, rot)

# toilet shower glass
for r in rooms:
    if r['id'] == 'atoilet':
        x0, x1, y0, y1 = r['m']
        if (x1 - x0) < (y1 - y0):
            ym = y0 + (y1 - y0) * 0.45
            glass_objs.append(box('shower', x0, x1, ym - 0.005, ym + 0.005, 0.05, 2.0, GLASS))
        else:
            xm = x0 + (x1 - x0) * 0.45
            glass_objs.append(box('shower', xm - 0.005, xm + 0.005, y0, y1, 0.05, 2.0, GLASS))

# ---------------------------------------------------------------- lighting
world = bpy.data.worlds.new('w')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.78, 0.84, 0.95, 1)
bg.inputs['Strength'].default_value = 0.42
sun = bpy.data.lights.new('sun', 'SUN')
sun.energy = 2.6
sun.angle = math.radians(9)
sun.color = (1.0, 0.95, 0.87)
so = bpy.data.objects.new('sun', sun)
col.objects.append if False else col.objects.link(so)
so.rotation_euler = (math.radians(38), math.radians(8), math.radians(32))
for r in rooms:
    if r['kind'] in ('living', 'bed', 'kitchen'):
        x0, x1, y0, y1 = r['m']
        L = bpy.data.lights.new('room', 'AREA')
        L.energy = 14 * (x1 - x0) * (y1 - y0)
        L.color = (1.0, 0.82, 0.62)
        L.size = min(x1 - x0, y1 - y0) * 0.6
        lo = bpy.data.objects.new('roomlight', L)
        lo.location = ((x0 + x1) / 2, (y0 + y1) / 2, 2.55)
        col.objects.link(lo)

# ---------------------------------------------------------------- 360 balcony render
import mathutils
PX, PY = [float(v) for v in args[args.index('--at') + 1].split(',')] if '--at' in args else (1430.0, 632.0)
RESX = int(args[args.index('--w') + 1]) if '--w' in args else 4096
xs_ = [r['m'][0] for r in rooms] + [r['m'][1] for r in rooms]
ys_ = [r['m'][2] for r in rooms] + [r['m'][3] for r in rooms]
# ceiling over the whole flat
add(box('ceiling', min(xs_) - 0.4, max(xs_) + 0.4, min(ys_) - 0.4, max(ys_) + 0.4, H, H + 0.18, M['wall']))
wx, wy = X(PX), Y(PY)            # outer face of the living-room wall
D, HW = 1.25, 2.6                # balcony depth / half width (m)
CH = mat('charcoal_b', '#4A4B4E', 0.85)
SL = mat('slab_b', '#D9D4CB', 0.9)
TL = mat('tile_b', '#B9B6B1', 0.3, fn=proc_tiles('#BDBAB5', '#B3B0AB', '#8E8B86', 0.6, 0.6))
FR = mat('frame_b', '#3A3C40', 0.4, metal=0.6)
GL = mat('glass_b', '#CFE3EA', 0.03, alpha=0.18)
y_out = wy - D
add(box('bal_floor', wx - HW, wx + HW, y_out, wy, -0.25, 0.0, TL))
add(box('bal_slab', wx - HW - 0.3, wx + HW + 0.3, y_out - 0.05, wy, H, H + 0.25, SL))
for sx in (-1, 1):
    x0 = wx + sx * HW
    add(box(f'bal_wall{sx}', min(x0, x0 + sx * 0.45), max(x0, x0 + sx * 0.45), y_out - 0.05, wy, -0.25, H + 0.25, CH))
add(box('rail_top', wx - HW, wx + HW, y_out, y_out + 0.06, 1.02, 1.07, FR))
add(box('rail_bot', wx - HW, wx + HW, y_out, y_out + 0.06, 0.0, 0.08, FR))
for t in np.linspace(wx - HW + 0.03, wx + HW - 0.03, 4):
    add(box(f'rail_post{t:.2f}', t - 0.025, t + 0.025, y_out, y_out + 0.06, 0.0, 1.07, FR))
glass_objs.append(box('rail_glass', wx - HW, wx + HW, y_out + 0.02, y_out + 0.04, 0.08, 1.02, GL))
cam = bpy.data.cameras.new('pano')
cam.type = 'PANO'
try:
    cam.panorama_type = 'EQUIRECTANGULAR'
except Exception:
    cam.cycles.panorama_type = 'EQUIRECTANGULAR'
co = bpy.data.objects.new('pano', cam)
col.objects.link(co)
co.location = (wx, y_out + 0.35, 1.5)
co.rotation_euler = (math.radians(90), 0, math.radians(180))   # look straight out (-Y)
scene.camera = co
# late-afternoon sun from behind the building (east-facing balcony is in shade, like the photos)
so.rotation_euler = (math.radians(65), 0, math.radians(0))
bg.inputs['Strength'].default_value = 1.1
for o in list(bpy.data.objects):
    if o.name.startswith('shrub') or o.name.startswith('floor_fb'):
        bpy.data.objects.remove(o)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = int(args[args.index('--samples') + 1]) if '--samples' in args else 48
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = RESX, RESX // 2
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = os.path.join(OUT, f'pano360_{T}.png')
t0 = time.time()
bpy.ops.render.render(write_still=True)
print('pano secs', time.time() - t0)
sys.exit(0)

# ---------------------------------------------------------------- preview render
if '--preview' in args:
    cam = bpy.data.cameras.new('cam')
    cam.lens = 40
    co = bpy.data.objects.new('cam', cam)
    col.objects.link(co)
    co.location = (5.5, -8.0, 13.5)
    scene.view_settings.view_transform = 'Standard'
    import mathutils
    d = mathutils.Vector((0, 0, 0)) - co.location
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.camera = co
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.render.resolution_x, scene.render.resolution_y = 1100, 750
    scene.render.filepath = os.path.join(OUT, f'preview_{T}.png')
    bpy.ops.render.render(write_still=True)
    sys.exit(0)

# ---------------------------------------------------------------- join + bake
interior = join(bake_objs, f'interior_{T}')
glass = join(glass_objs, f'glass_{T}')
print('tris', len(interior.data.polygons))

bpy.ops.object.select_all(action='DESELECT')
interior.select_set(True)
bpy.context.view_layer.objects.active = interior
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0025, correct_aspect=True)
bpy.ops.uv.pack_islands(margin=0.002)
bpy.ops.object.mode_set(mode='OBJECT')

img = bpy.data.images.new(f'bake_{T}', RES, RES, float_buffer=True)
for m in interior.data.materials:
    n = m.node_tree.nodes.new('ShaderNodeTexImage')
    n.image = img
    m.node_tree.nodes.active = n

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.max_bounces = 6
scene.render.bake.margin = 6
scene.render.bake.use_pass_direct = True
scene.render.bake.use_pass_indirect = True
for p in ('use_pass_diffuse', 'use_pass_emit', 'use_pass_transmission'):
    setattr(scene.render.bake, p, True)
scene.render.bake.use_pass_glossy = False
scene.render.threads_mode = 'AUTO'
t0 = time.time()
if not NOBAKE:
    bpy.ops.object.bake(type='COMBINED', margin=6)
print('bake secs', time.time() - t0)

px = np.empty(RES * RES * 4, np.float32)
img.pixels.foreach_get(px)
px = px.reshape(RES, RES, 4)[:, :, :3]
# filmic-ish tone curve (ACES fitted) then sRGB encode
expo = 1.15
x = px * expo
a, b_, c_, d_, e_ = 2.51, 0.03, 2.43, 0.59, 0.14
y = np.clip((x * (a * x + b_)) / (x * (c_ * x + d_) + e_), 0, 1)
y = np.where(y <= 0.0031308, y * 12.92, 1.055 * np.power(y, 1 / 2.4) - 0.055)
out = (np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8)[::-1]
from PIL import Image
pngp = os.path.join(OUT, f'interior_{T}_bake.png')
Image.fromarray(out).save(pngp)
print('saved', pngp)

# single material for export
for m in list(interior.data.materials):
    pass
interior.data.materials.clear()
bm_ = bpy.data.materials.new('baked')
bm_.use_nodes = True
tex = bm_.node_tree.nodes.new('ShaderNodeTexImage')
img2 = bpy.data.images.load(pngp)
tex.image = img2
bm_.node_tree.links.new(tex.outputs['Color'], bm_.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
interior.data.materials.append(bm_)
for p in interior.data.polygons:
    p.material_index = 0
if glass:
    glass.data.materials.clear()
    glass.data.materials.append(GLASS)
# record room centres for labels
export_glb(os.path.join(OUT, f'interior_{T}.glb'), [o for o in (interior, glass) if o])
