"""Campus landscape + reusable props for Vraj Platinum.

python3 blender/site.py -> blender/out/site.glb (static campus) and blender/out/props.glb (palm, tree,
car, lamp, bench, shrub) + src/data/props.json (instance transforms used by the web app).
Plan: brochure 'Typical Layout Plan' + 'Ground Floor Plan': central lawn with kids' play area (west),
water body (east), gazebo & senior-citizen seating, peripheral parking, 30 m road on the East.
"""
import sys, os, json, math, random
import bpy, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bcommon import *

random.seed(5)
site = json.load(open(os.path.join(ROOT, 'src', 'data', 'site.json')))
reset()
reset_mats()
M = dict(
    paver=mat('paver', '#8F8C86', 0.9, fn=proc_tiles('#8E8B85', '#86837D', '#6E6B66', 0.2, 0.4, vein=False)),
    asphalt=mat('asphalt', '#3D3F42', 0.95, fn=proc_noise('#36383B', '#47494C', 90)),
    kerb=mat('kerb', '#B9B6AF', 0.8),
    footpath=mat('footpath', '#A49C8F', 0.9, fn=proc_tiles('#A79F92', '#9C9488', '#7D766B', 0.3, 0.3, vein=False)),
    lawn=mat('lawn', '#5E8C3A', 0.95),
    lawn2=mat('lawn2', '#6F9C45', 0.95),
    hedge=mat('hedge', '#3F6B2C', 0.9),
    wallw=mat('wallw', '#E6E2DA', 0.85),
    stone=mat('stone', '#BBAA8E', 0.8, fn=proc_noise('#B2A184', '#C8B89D', 12)),
    wood=mat('wood', '#A87A4E', 0.6, fn=proc_wood('#99693F', '#BC8E5F', 4, 'Y')),
    gold=mat('gold', '#D2A858', 0.3, 0.9, emit='#F3C46E', emit_strength=0.4),
    water=mat('water', '#2E6F86', 0.05, 0.3),
    rubber=mat('rubber', '#C4543C', 0.9),
    rubber2=mat('rubber2', '#3B7F9C', 0.9),
    play_y=mat('playy', '#E9B63B', 0.5),
    charcoal=mat('charcoal', '#45484D', 0.8),
    white=mat('white', '#F2F1ED', 0.7),
    mark=mat('mark', '#F1F1EC', 0.6),
    yellow=mat('yellowmark', '#E2B23A', 0.6),
    soil=mat('soil', '#4A3627', 1.0),
    leaf=mat('leaf', '#4C7A33', 0.8),
    glass=mat('glass', '#26343D', 0.08, 0.7),
)
objs = []


def B(*a, **k):
    o = box(f's{len(objs)}', *a, **k)
    objs.append(o)
    return o


def text(body, x, y, z, size, m, rot_z=0.0, extrude=0.04):
    cu = bpy.data.curves.new('t', 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = 'CENTER'
    ob = bpy.data.objects.new('txt', cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, y, z)
    ob.rotation_euler = (math.pi / 2, 0, rot_z)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.view_layer.objects.active
    ob.data.materials.clear()
    ob.data.materials.append(m)
    objs.append(ob)
    return ob


px0, px1, py0, py1 = site['plot']
# plot paving + boundary
B(px0, px1, py0, py1, -0.05, 0.03, M['paver'])
for (a, b, c, d) in ((px0 - 0.25, px0, py0, py1), (px0, px1, py1, py1 + 0.25), (px0, px1, py0 - 0.25, py0)):
    B(a, b, c, d, 0, 2.2, M['wallw'], top=M['charcoal'])
gx, gy, gw = site['gate']['x'], site['gate']['y'], site['gate']['width']
# front: stone pylons + wood louvres + signage
for (y0, y1, sgn) in ((py0, gy - gw / 2, -1), (gy + gw / 2, py1, 1)):
    B(px1 - 0.3, px1, y0, y1, 0, 0.6, M['stone'])
    for yy in [y0 + i * 0.18 for i in range(int((y1 - y0) / 0.18))]:
        B(px1 - 0.25, px1 - 0.1, yy, yy + 0.09, 0.6, 2.6, M['wood'])
    B(px1 - 0.3, px1, y0, y1, 2.6, 2.75, M['charcoal'])
    # signage wall near the gate
    sy0, sy1 = (gy - gw / 2 - 9, gy - gw / 2 - 0.4) if sgn < 0 else (gy + gw / 2 + 0.4, gy + gw / 2 + 9)
    B(px1 - 1.2, px1 - 0.3, sy0, sy1, 0, 3.4, M['stone'], top=M['charcoal'])
    B(px1 - 1.0, px1 - 0.4, sy0 - 0.4, sy0, 0, 3.8, M['charcoal'])
    B(px1 - 1.0, px1 - 0.4, sy1, sy1 + 0.4, 0, 3.8, M['charcoal'])
    cyy = (sy0 + sy1) / 2
    text('VRAJ', px1 - 0.27, cyy, 1.95, 0.85, M['gold'], rot_z=math.pi / 2)
    text('Platinum', px1 - 0.27, cyy, 1.0, 0.8, M['gold'], rot_z=math.pi / 2)
    B(px1 - 1.6, px1 - 1.2, sy0, sy1, 0, 0.5, M['soil'])
# guard cabin + boom barrier
B(gx - 4.5, gx - 1.5, gy + gw / 2 + 0.5 - 9.5 + 9.5, gy + gw / 2 + 3.0, 0, 2.7, M['white'], top=M['charcoal'])
B(gx - 4.6, gx - 1.4, gy + gw / 2 + 0.4, gy + gw / 2 + 3.1, 2.7, 2.9, M['charcoal'])
B(gx - 0.6, gx - 0.4, gy - gw / 2 + 0.3, gy + gw / 2 - 0.3, 0.95, 1.05, M['yellow'])
# road (30 m) with footpaths, median and markings
rx0, rx1 = site['road']['rect'][0], site['road']['rect'][1]
ry0, ry1 = -260, 260
B(rx0, rx0 + 2.6, ry0, ry1, 0, 0.15, M['footpath'])
B(rx1 - 2.6, rx1, ry0, ry1, 0, 0.15, M['footpath'])
B(rx0 + 2.6, rx1 - 2.6, ry0, ry1, -0.05, 0.02, M['asphalt'])
mx = (rx0 + rx1) / 2
B(mx - 1.0, mx + 1.0, ry0, ry1, 0, 0.25, M['kerb'])
B(mx - 0.85, mx + 0.85, ry0, ry1, 0.25, 0.3, M['hedge'])
for lane in (rx0 + 2.6 + 4.1, rx0 + 2.6 + 8.2, mx + 1 + 4.1, mx + 1 + 8.2):
    y = ry0
    while y < ry1:
        B(lane - 0.07, lane + 0.07, y, y + 3, 0.02, 0.026, M['mark'])
        y += 9
for e in (rx0 + 2.9, rx1 - 2.9, mx - 1.3, mx + 1.3):
    B(e - 0.07, e + 0.07, ry0, ry1, 0.02, 0.026, M['mark'])
# garden
gx0, gx1, gy0, gy1 = site['garden']
B(gx0 - 0.6, gx1 + 0.6, gy0 - 0.6, gy1 + 0.6, 0.0, 0.18, M['kerb'])
stripe = 2.4
x = gx0
i = 0
while x < gx1:
    B(x, min(gx1, x + stripe), gy0, gy1, 0.0, 0.2, M['lawn' if i % 2 else 'lawn2'])
    x += stripe
    i += 1
for side in (gy0 + 0.6, gy1 - 0.6):
    for k in range(int((gx1 - gx0) / 1.3)):
        xx = gx0 + 0.6 + k * 1.3
        sphere(f'hedge{side}{k}', 0.55, xx, side, 0.55, M['hedge'], sub=2, sz=0.75)
        objs.append(bpy.data.objects[f'hedge{side}{k}'])
# play area (west end)
ax0, ax1, ay0, ay1 = site['playArea']
B(ax0, ax1, ay0, ay1, 0.0, 0.22, M['rubber'])
B(ax0 + 1.0, ax0 + 2.8, ay0 + 1.5, ay0 + 3.3, 0.22, 0.24, M['rubber2'])
B(ax0 + 1.2, ax0 + 2.6, ay0 + 1.7, ay0 + 3.1, 0.22, 2.6, M['play_y'])
B(ax0 + 1.0, ax0 + 2.8, ay0 + 1.5, ay0 + 3.3, 2.6, 3.1, M['rubber'])
B(ax0 + 2.8, ax0 + 5.2, ay0 + 2.1, ay0 + 2.7, 0.3, 1.6, M['rubber2'])
for k in range(4):
    cyl(f'post{k}', 0.07, 0.2, 2.2, M['charcoal'], x=ax1 - 1.2 - (k % 2) * 2.2, y=(ay0 + ay1) / 2 + (k // 2 - 0.5) * 2.0)
    objs.append(bpy.data.objects[f'post{k}'])
B(ax1 - 3.6, ax1 - 1.0, (ay0 + ay1) / 2 - 1.2, (ay0 + ay1) / 2 + 1.2, 2.1, 2.2, M['charcoal'])
# water body with fountain jets (east end of garden)
wx0, wx1, wy0, wy1 = site['waterBody']
B(wx0 - 1.6, wx1 + 0.3, wy0 - 1.5, wy1 + 1.5, 0, 0.55, M['stone'], top=M['white'])
B(wx0 - 1.3, wx1, wy0 - 1.2, wy1 + 1.2, 0.3, 0.5, M['water'])
for k in range(6):
    yy = wy0 - 0.8 + k * ((wy1 - wy0) + 1.6) / 5
    cyl(f'jet{k}', 0.05, 0.5, 1.3, M['white'], x=(wx0 + wx1) / 2, y=yy, seg=8, r2=0.01)
    objs.append(bpy.data.objects[f'jet{k}'])
# gazebo (pergola) mid-garden + benches
gzx, gzy = (gx0 + gx1) / 2 - 6, gy1 - 2.2
for dx in (-1.6, 1.6):
    for dy in (-1.4, 1.4):
        B(gzx + dx - 0.1, gzx + dx + 0.1, gzy + dy - 0.1, gzy + dy + 0.1, 0.2, 2.8, M['wood'])
for k in range(9):
    B(gzx - 2.0 + k * 0.5, gzx - 1.9 + k * 0.5, gzy - 1.8, gzy + 1.8, 2.8, 3.0, M['wood'])
B(gzx - 2.0, gzx + 2.1, gzy - 1.6, gzy - 1.4, 2.6, 2.8, M['wood'])
B(gzx - 2.0, gzx + 2.1, gzy + 1.4, gzy + 1.6, 2.6, 2.8, M['wood'])
# central planter between towers A & B
cx0, cx1, cy0, cy1 = site['centralPlanter']
B(cx0, cx1, cy0, cy1, 0, 0.5, M['stone'], top=M['soil'])
# creeper pergola linking towers A and B over the entrance drive (as in the night render)
for xx in (33.8, 35.4):
    B(xx, xx + 0.3, -5.7, 5.8, 5.4, 5.8, M['charcoal'])
for k in range(int(11.5 / 0.25)):
    yy = -5.6 + k * 0.25
    ln = 0.6 + random.random() * 1.6
    B(33.9 + random.random() * 1.4, 34.1 + random.random() * 1.4, yy, yy + 0.18, 5.4 - ln, 5.9, M['leaf'])

# ---------------------------------------------------------------- props
props = dict(palm=[], tree=[], car=[], lamp=[], bench=[], shrub=[])


def add_prop(kind, x, y, rot=0.0, s=1.0, c=None):
    p = dict(x=round(x, 2), y=round(y, 2), r=round(rot, 3), s=round(s, 2))
    if c:
        p['c'] = c
    props[kind].append(p)


# palms around garden + central planter + front
for k in range(5):
    t = (k + 0.5) / 5
    add_prop('palm', gx0 + (gx1 - gx0) * t, gy0 - 0.2, random.random() * 6, 0.9 + random.random() * 0.3)
    add_prop('palm', gx0 + (gx1 - gx0) * t, gy1 + 0.2, random.random() * 6, 0.9 + random.random() * 0.3)
for k in range(4):
    add_prop('palm', cx0 + 2 + k * (cx1 - cx0 - 4) / 3, (cy0 + cy1) / 2, random.random() * 6, 1.0 + random.random() * 0.2)
for yy in (py0 + 2, py1 - 2, -16, 16):
    add_prop('palm', px1 - 2.0, yy, random.random() * 6, 1.1)
# boundary trees
for k in range(14):
    add_prop('tree', px0 + 1.2, py0 + 3 + k * (py1 - py0 - 6) / 13, random.random() * 6, 0.8 + random.random() * 0.35)
for k in range(12):
    add_prop('tree', px0 + 6 + k * (px1 - px0 - 14) / 11, py0 + 1.2, random.random() * 6, 0.8 + random.random() * 0.35)
    add_prop('tree', px0 + 6 + k * (px1 - px0 - 14) / 11, py1 - 1.2, random.random() * 6, 0.8 + random.random() * 0.35)
# road-side avenue trees + median shrubs
for k in range(-24, 25):
    yy = k * 10.5
    if abs(yy) < 8:
        continue
    add_prop('tree', rx1 - 1.3, yy + 3, random.random() * 6, 0.9 + random.random() * 0.3)
    if abs(yy) > 40:
        add_prop('tree', rx0 + 1.3, yy, random.random() * 6, 0.85 + random.random() * 0.3)
    add_prop('shrub', mx, yy, 0, 1.0)
    add_prop('lamp', mx, yy + 5, 0, 1.0)
# parking (perimeter, as per layout plan)
colors = ['#f2f2f0', '#c9ccd1', '#1d1f24', '#8a1f22', '#2a4f7a', '#6e7277', '#f2f2f0', '#d8d2c4']
for k in range(16):
    add_prop('car', px0 + 3.2, py0 + 6 + k * 4.0, math.pi / 2, 1.0, random.choice(colors)) if random.random() < 0.8 else None
for k in range(9):
    for yy in (py0 + 3.2, py1 - 3.2):
        if random.random() < 0.75:
            add_prop('car', px0 + 9 + k * 2.6, yy, 0, 1.0, random.choice(colors))
for k in range(6):
    if random.random() < 0.8:
        add_prop('car', 12 + k * 2.6, -3.0 if k % 2 else 3.0, 0, 1.0, random.choice(colors))
# road traffic (static)
for k in range(10):
    lane = rx0 + 2.6 + 2.0 + (k % 3) * 4.1 if k % 2 else mx + 1 + 2.0 + (k % 3) * 4.1
    add_prop('car', lane, -120 + k * 26 + random.random() * 6, 0 if k % 2 else math.pi, 1.0, random.choice(colors))
# lamps inside campus + benches in garden
for k in range(6):
    add_prop('lamp', -30 + k * 11, -8.5, 0, 0.8)
    add_prop('lamp', -30 + k * 11, 8.5, 0, 0.8)
for k in range(4):
    add_prop('bench', gx0 + 8 + k * 9, gy0 + 1.6, 0, 1.0)
    add_prop('bench', gx0 + 8 + k * 9, gy1 - 1.6, math.pi, 1.0)
props = {k: [p for p in v if p] for k, v in props.items()}
json.dump(props, open(os.path.join(ROOT, 'src', 'data', 'props.json'), 'w'))

site_obj = join(objs, 'campus')
export_glb(os.path.join(OUT, 'site.glb'), [site_obj])

# ---- prop meshes (each centred at origin) ----
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
P = {}


def palm():
    parts = []
    h = 7.5
    seg = 10
    for i in range(seg):
        z0, z1 = h * i / seg, h * (i + 1) / seg
        bend = 0.35 * (i / seg) ** 2
        parts.append(cyl(f'tr{i}', 0.2 - 0.07 * i / seg, z0, z1 + 0.02, mat('trunk', '#7D6A55', 0.9), x=bend, seg=10))
    tx = 0.35
    for k in range(11):
        a = k / 11 * math.tau + random.random() * 0.3
        L = 2.6 + random.random() * 0.8
        for j in range(5):
            t0, t1 = j / 5, (j + 1) / 5
            r0, r1 = L * t0, L * t1
            z0 = h - 0.15 * (r0 ** 1.6)
            w = 0.55 * math.sin(math.pi * (t0 + t1) / 2) + 0.08
            me = bpy.data.meshes.new('fr')
            bm = bmesh.new()
            ca, sa = math.cos(a), math.sin(a)
            pa, pb = (-sa, ca), (sa, -ca)
            z1 = h - 0.15 * (r1 ** 1.6)
            vs = [bm.verts.new((tx + ca * r0 + pa[0] * w, sa * r0 + pa[1] * w, z0)),
                  bm.verts.new((tx + ca * r0 + pb[0] * w, sa * r0 + pb[1] * w, z0)),
                  bm.verts.new((tx + ca * r1 + pb[0] * w, sa * r1 + pb[1] * w, z1)),
                  bm.verts.new((tx + ca * r1 + pa[0] * w, sa * r1 + pa[1] * w, z1)),
                  bm.verts.new((tx + ca * (r0 + r1) / 2, sa * (r0 + r1) / 2, (z0 + z1) / 2 + 0.12))]
            bm.faces.new((vs[0], vs[4], vs[3]))
            bm.faces.new((vs[1], vs[2], vs[4]))
            bm.faces.new((vs[0], vs[1], vs[4]))
            bm.faces.new((vs[4], vs[2], vs[3]))
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new('fr', me)
            bpy.context.scene.collection.objects.link(ob)
            ob.data.materials.append(mat('frond', '#4E7C2E', 0.8))
            parts.append(ob)
    parts.append(sphere('coco', 0.3, tx, 0, h - 0.2, mat('trunk', '#7D6A55'), sub=1))
    return join(parts, 'palm')


def tree():
    parts = [cyl('trunk', 0.16, 0, 2.6, mat('bark', '#5E4B3A', 0.9), seg=8, r2=0.1)]
    for k in range(7):
        a = k * 2.4
        r = 1.0 + random.random() * 0.6
        parts.append(sphere(f'c{k}', r, math.cos(a) * 0.9 * (k > 0), math.sin(a) * 0.9 * (k > 0), 3.4 + (k % 3) * 0.6,
                            mat('canopy' if k % 2 else 'canopy2', '#46702F' if k % 2 else '#5B8638', 0.85), sub=2, sz=0.85))
    return join(parts, 'tree')


def car():
    body = mat('carpaint', '#FFFFFF', 0.25, 0.4)
    parts = [box('cb', -2.25, 2.25, -0.88, 0.88, 0.3, 0.95, body, bevel=0.12),
             box('cc', -1.2, 1.0, -0.78, 0.78, 0.95, 1.45, body, bevel=0.12),
             box('cw', -1.15, 0.95, -0.8, 0.8, 1.0, 1.4, mat('carglass', '#15191E', 0.1, 0.6), bevel=0.06)]
    for sx in (-1.45, 1.45):
        for sy in (-0.82, 0.82):
            c = cyl('wh', 0.34, -0.12, 0.12, mat('tyre', '#121212', 0.9), seg=16)
            c.rotation_euler = (math.pi / 2, 0, 0)
            c.location = (sx, sy, 0.34)
            parts.append(c)
    parts.append(box('hl', 2.2, 2.27, -0.7, 0.7, 0.62, 0.76, mat('headlight', '#FFF4DD', 0.2, emit='#FFF1D0', emit_strength=0.2)))
    parts.append(box('tl', -2.27, -2.2, -0.7, 0.7, 0.68, 0.8, mat('taillight', '#8A1010', 0.3, emit='#FF2020', emit_strength=0.2)))
    return join(parts, 'car')


def lamp():
    parts = [cyl('pole', 0.07, 0, 6.5, mat('pole', '#2A2C30', 0.5, 0.6), seg=10, r2=0.05),
             box('arm', -0.05, 1.2, -0.05, 0.05, 6.3, 6.4, mat('pole', '#2A2C30')),
             box('head', 0.8, 1.5, -0.18, 0.18, 6.2, 6.32, mat('lamphead', '#FFF3D6', 0.3, emit='#FFE2A8', emit_strength=1.0))]
    return join(parts, 'lamp')


def bench():
    w = mat('benchwood', '#9B6B44', 0.6)
    k = mat('benchleg', '#2A2C30', 0.5, 0.5)
    parts = [box('s', -0.9, 0.9, -0.22, 0.22, 0.42, 0.47, w), box('b', -0.9, 0.9, -0.24, -0.2, 0.5, 0.85, w),
             box('l1', -0.8, -0.74, -0.22, 0.22, 0, 0.42, k), box('l2', 0.74, 0.8, -0.22, 0.22, 0, 0.42, k)]
    return join(parts, 'bench')


def shrub():
    parts = []
    for k in range(4):
        parts.append(sphere(f'sh{k}', 0.5, (k - 1.5) * 0.45, 0, 0.6, mat('hedge2', '#3F6B2C', 0.9), sub=2, sz=0.8))
    return join(parts, 'shrub')


exp = [palm(), tree(), car(), lamp(), bench(), shrub()]
export_glb(os.path.join(OUT, 'props.glb'), exp)
print({k: len(v) for k, v in props.items()})
