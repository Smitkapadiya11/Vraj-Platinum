"""Real neighbourhood landmarks east of Vraj Platinum, placed from the 23 Nov 2026 balcony photos/videos.

Every position comes from the stitched 360 taken on the 14th floor of Tower B (flat B-1402, road side):
direction = azimuth in the panorama, distance = camera height (44.15 m) / tan(angle of the base below the
horizon); cross-checked against the Esri land-cover ground map (party-plot lawns, courts, eucalyptus block).
Scene axes: x = east, y = north, z = up (metres from the plot centre).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

CAM = Vector((37.3, -12.8))
CAM_H = 44.15


def at(lon_deg, d):
    """photo azimuth (0 = straight out = east, + = right/south) and ground distance -> (x, y)"""
    a = math.radians(lon_deg)
    return CAM.x + d * math.cos(a), CAM.y - d * math.sin(a)


def dist(lat_deg):
    return CAM_H / math.tan(math.radians(-lat_deg))


def hexc(h, a=1.0):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*c, a)


_M = {}


def mat(name, col, rough=0.7, metal=0.0, emit=None):
    if name in _M:
        return _M[name]
    m = bpy.data.materials.new('lm_' + name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hexc(col)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    _M[name] = m
    return m


def facade_mat(name, wall, win='#2B3138', storey=3.0, bay=3.4, wfrac=(0.3, 0.8), hfrac=(0.18, 0.82), stripe=None, lit=0.38):
    """box-projected storeys + windows from object coordinates; optional vertical stripe colour every 2 bays"""
    key = 'fac_' + name
    if key in _M:
        return _M[key]
    m = bpy.data.materials.new('lm_' + key)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    N = nt.nodes.new
    geo = N('ShaderNodeNewGeometry')
    tc = N('ShaderNodeTexCoord')
    sp = N('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs[0])
    sn = N('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    ax = N('ShaderNodeMath'); ax.operation = 'ABSOLUTE'; nt.links.new(sn.outputs['X'], ax.inputs[0])
    gx = N('ShaderNodeMath'); gx.operation = 'GREATER_THAN'; gx.inputs[1].default_value = 0.5; nt.links.new(ax.outputs[0], gx.inputs[0])
    hz = N('ShaderNodeMix'); hz.data_type = 'FLOAT'
    nt.links.new(gx.outputs[0], hz.inputs['Factor']); nt.links.new(sp.outputs['X'], hz.inputs[2]); nt.links.new(sp.outputs['Y'], hz.inputs[3])

    def frac(inp, div):
        d = N('ShaderNodeMath'); d.operation = 'DIVIDE'; d.inputs[1].default_value = div; nt.links.new(inp, d.inputs[0])
        f = N('ShaderNodeMath'); f.operation = 'FRACT'; nt.links.new(d.outputs[0], f.inputs[0])
        return f.outputs[0], d.outputs[0]

    def band(v, a, c):
        g1 = N('ShaderNodeMath'); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = a; nt.links.new(v, g1.inputs[0])
        g2 = N('ShaderNodeMath'); g2.operation = 'LESS_THAN'; g2.inputs[1].default_value = c; nt.links.new(v, g2.inputs[0])
        mm = N('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(g1.outputs[0], mm.inputs[0]); nt.links.new(g2.outputs[0], mm.inputs[1])
        return mm.outputs[0]
    fz, zz = frac(sp.outputs['Z'], storey)
    fh, hh = frac(hz.outputs[0], bay)
    win = N('ShaderNodeMath'); win.operation = 'MULTIPLY'
    nt.links.new(band(fz, *wfrac), win.inputs[0]); nt.links.new(band(fh, *hfrac), win.inputs[1])
    # no windows on the ground storey and the top 0.5 m
    g0 = N('ShaderNodeMath'); g0.operation = 'GREATER_THAN'; g0.inputs[1].default_value = storey * 0.9; nt.links.new(sp.outputs['Z'], g0.inputs[0])
    w2 = N('ShaderNodeMath'); w2.operation = 'MULTIPLY'; nt.links.new(win.outputs[0], w2.inputs[0]); nt.links.new(g0.outputs[0], w2.inputs[1])
    wallc = N('ShaderNodeRGB'); wallc.outputs[0].default_value = hexc(wall)
    col_wall = wallc.outputs[0]
    if stripe:
        # stripe on every 3rd bay (orange vertical fin bands like the real twin towers)
        sb, _ = frac(hz.outputs[0], bay * 3)
        st = band(sb, 0.0, 0.16)
        sc = N('ShaderNodeRGB'); sc.outputs[0].default_value = hexc(stripe)
        mx = N('ShaderNodeMix'); mx.data_type = 'RGBA'
        nt.links.new(st, mx.inputs['Factor']); nt.links.new(wallc.outputs[0], mx.inputs[6]); nt.links.new(sc.outputs[0], mx.inputs[7])
        col_wall = mx.outputs[2]
    noise = N('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 0.6; nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    dirt = N('ShaderNodeMapRange'); dirt.inputs[1].default_value = 0.3; dirt.inputs[2].default_value = 0.75; dirt.inputs[3].default_value = 0.86; dirt.inputs[4].default_value = 1.0
    nt.links.new(noise.outputs['Fac'], dirt.inputs[0])
    wd = N('ShaderNodeMix'); wd.data_type = 'RGBA'; wd.blend_type = 'MULTIPLY'; wd.inputs['Factor'].default_value = 1.0
    nt.links.new(col_wall, wd.inputs[6]); nt.links.new(dirt.outputs[0], wd.inputs[7])
    winc = N('ShaderNodeRGB'); winc.outputs[0].default_value = hexc(win)
    fin = N('ShaderNodeMix'); fin.data_type = 'RGBA'
    nt.links.new(w2.outputs[0], fin.inputs['Factor']); nt.links.new(wd.outputs[2], fin.inputs[6]); nt.links.new(winc.outputs[0], fin.inputs[7])
    nt.links.new(fin.outputs[2], b.inputs['Base Color'])
    rr = N('ShaderNodeMapRange'); rr.inputs[3].default_value = 0.85; rr.inputs[4].default_value = 0.12
    nt.links.new(w2.outputs[0], rr.inputs[0]); nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    # night: a share of windows lit warm, driven by the 'night' view-layer property like the rest of the scene
    cell = N('ShaderNodeCombineXYZ')
    fl1 = N('ShaderNodeMath'); fl1.operation = 'FLOOR'; nt.links.new(zz, fl1.inputs[0])
    fl2 = N('ShaderNodeMath'); fl2.operation = 'FLOOR'; nt.links.new(hh, fl2.inputs[0])
    nt.links.new(fl1.outputs[0], cell.inputs[0]); nt.links.new(fl2.outputs[0], cell.inputs[1]); nt.links.new(gx.outputs[0], cell.inputs[2])
    wn = N('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '3D'; nt.links.new(cell.outputs[0], wn.inputs['Vector'])
    lt = N('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = lit; nt.links.new(wn.outputs['Value'], lt.inputs[0])
    nv = N('ShaderNodeAttribute'); nv.attribute_type = 'VIEW_LAYER'; nv.attribute_name = 'night'
    e1 = N('ShaderNodeMath'); e1.operation = 'MULTIPLY'; nt.links.new(lt.outputs[0], e1.inputs[0]); nt.links.new(w2.outputs[0], e1.inputs[1])
    e2 = N('ShaderNodeMath'); e2.operation = 'MULTIPLY'; nt.links.new(e1.outputs[0], e2.inputs[0]); nt.links.new(nv.outputs['Fac'], e2.inputs[1])
    e3 = N('ShaderNodeMath'); e3.operation = 'MULTIPLY'; e3.inputs[1].default_value = 1.6; nt.links.new(e2.outputs[0], e3.inputs[0])
    nt.links.new(e3.outputs[0], b.inputs['Emission Strength'])
    b.inputs['Emission Color'].default_value = (1.0, 0.68, 0.38, 1)
    _M[key] = m
    return m


COLL = None


def link(o):
    COLL.objects.link(o)
    return o


def box(name, cx, cy, w, d, z0, z1, m, rot=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * d, (v.co.z + 0.5) * (z1 - z0) + z0))
    bm.to_mesh(me); bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    o.location = (cx, cy, 0)
    o.rotation_euler = (0, 0, rot)
    return link(o)


def cyl(name, cx, cy, r, z0, z1, m, seg=20, r2=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=z1 - z0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, (z0 + z1) / 2))
    bm.to_mesh(me); bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    o.location = (cx, cy, 0)
    return link(o)


def dome(name, cx, cy, z, r, m, rot=0.0, off=(0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=r)
    for v in bm.verts:
        if v.co.z < 0:
            v.co.z *= 0.15
        else:
            v.co.z *= 1.25
    bm.to_mesh(me); bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    c, s = math.cos(rot), math.sin(rot)
    o.location = (cx + off[0] * c - off[1] * s, cy + off[0] * s + off[1] * c, z)
    return link(o)


def facing_cam(x, y):
    """rotation so the object's -y face looks back at the balcony"""
    return math.atan2(CAM.y - y, CAM.x - x) + math.pi / 2


# ------------------------------------------------------------------ landmarks
def twin_towers():
    m = facade_mat('twin', '#E9DCC2', '#3A3F46', stripe='#B5612D', bay=3.2)
    roof = mat('twin_roof', '#D9D3C8', 0.8)
    out = []
    for name, lon, d, w, dd in (('twin_L', -35.0, dist(-17.5) + 10, 26, 18), ('twin_R', -24.0, dist(-15.0) + 10, 24, 18)):
        x, y = at(lon, d)
        r = facing_cam(x, y)
        out.append(box(name, x, y, w, dd, 0, 45.0, m, r))
        box(name + '_head', x, y, w * 0.35, dd * 0.4, 45.0, 48.5, roof, r)    # lift machine room
        box(name + '_stilt', x, y, w, dd, 0, 3.0, mat('stilt', '#6E6A64', 0.9), r)
    return out


def under_construction():
    x, y = at(-19.0, dist(-11.5) + 8)
    r = facing_cam(x, y)
    conc = mat('uc_concrete', '#9C978E', 0.95)
    for k in range(9):                       # 9 slabs, open frame
        box(f'uc_slab{k}', x, y, 24, 18, k * 3.0, k * 3.0 + 0.25, conc, r)
    c, s = math.cos(r), math.sin(r)
    for i in (-1, 0, 1):
        for j in (-1, 1):
            ox, oy = i * 11, j * 8
            box(f'uc_col{i}{j}', x + ox * c - oy * s, y + ox * s + oy * c, 0.6, 0.6, 0, 26, conc, r)
    box('uc_core', x, y, 5, 5, 0, 29, conc, r)
    orange = mat('silo', '#C2551F', 0.55, 0.3)
    for k, (ox, oy) in enumerate(((-16, -12), (-12.4, -12))):
        cx, cy = x + ox * c - oy * s, y + ox * s + oy * c
        cyl(f'silo{k}', cx, cy, 1.6, 4, 16, orange)
        cyl(f'silo{k}_cone', cx, cy, 1.6, 1.5, 4, orange, r2=0.3)
    # labour-camp sheds (blue tin) in front
    tin = mat('tin_blue', '#4C6E9A', 0.6, 0.4)
    for k in range(4):
        ox, oy = -6 + k * 7, -22
        box(f'camp{k}', x + ox * c - oy * s, y + ox * s + oy * c, 6, 14, 0, 3, tin, r)


def future_corner():
    """THE FUTURE CORNER: red-brown terraced commercial block, stepping down to one side"""
    x, y = at(-16.0, dist(-6.6))
    r = facing_cam(x, y)
    m = facade_mat('tfc', '#8E3D2E', '#2A2D33', storey=3.4, bay=3.0, wfrac=(0.25, 0.85), hfrac=(0.12, 0.88))
    c, s = math.cos(r), math.sin(r)
    steps = [(56, 0, 3), (52, 3, 6), (47, 6, 8), (42, 8, 10), (36, 10, 11)]
    for k, (w, f0, f1) in enumerate(steps):
        ox = (56 - w) / 2
        box(f'tfc_{k}', x + ox * c, y + ox * s, w, 26, f0 * 3.4, f1 * 3.4, m, r)
    box('tfc_sign', x - 8 * c, y - 8 * s, 14, 1.0, 37.4, 39.5, mat('sign', '#F2EFE8', 0.5), r)


def far_towers():
    out = []
    m1 = facade_mat('brown', '#9E6E52', '#33373C', bay=3.3)
    for k, (lon, d) in enumerate(((-2.2, 520), (1.0, 540))):
        x, y = at(lon, d)
        out.append(box(f'far_brown{k}', x, y, 18, 16, 0, 40, m1, facing_cam(x, y)))
    pal = ['#DCD3C3', '#CFC8BC', '#E4DDD0', '#C9BFAE', '#D8CFBF', '#BDB6AA']
    for k, (lon, d, h) in enumerate(((-74, 480, 42), (-69, 470, 44), (-64, 500, 42), (-59, 430, 39), (-54, 470, 45), (-49, 520, 42),
                                     (-44, 560, 40), (-8, 760, 44), (8, 820, 40), (-28, 700, 42))):
        x, y = at(lon, d)
        m = facade_mat(f'res{k % 6}', pal[k % 6], '#353a40', bay=3.2 + (k % 3) * 0.2)
        out.append(box(f'far_res{k}', x, y, 22 + (k % 3) * 4, 16, 0, h, m, facing_cam(x, y)))
    return out


def houses():
    random.seed(11)
    pal = ['#E6E1D7', '#CFCAC2', '#B9B6B1', '#EDE8DD', '#D7CDBB', '#A9A7A3']
    n = 0
    for lon in range(-72, -40, 4):
        for d in (105, 130, 158, 186):
            x, y = at(lon + random.uniform(-1.5, 1.5), d + random.uniform(-6, 6))
            if x < 82:             # keep off the 100 ft road and its verge
                continue
            h = random.choice((10.5, 13.5, 13.5, 16.5))
            m = facade_mat(f'house{n % 6}', pal[n % 6], '#3A3E44', storey=3.3, bay=3.6, wfrac=(0.35, 0.78), hfrac=(0.25, 0.75), lit=0.5)
            box(f'house{n}', x, y, random.uniform(9, 13), random.uniform(12, 16), 0, h, m, facing_cam(x, y) + random.uniform(-0.1, 0.1))
            n += 1
    return n


def party_plot():
    """the wedding venue in front: two domed gates (maroon/gold and peach), long grey tents, palms along the lawn"""
    cream = mat('gate_peach', '#E9B98E', 0.7)
    maroon = mat('gate_maroon', '#8C2430', 0.6)
    gold = mat('gold', '#D9A84A', 0.35, 0.8)
    dark = mat('arch', '#3B2622', 0.8)
    for name, lon, d, body, dm in (('gate1', 1.0, dist(-33), maroon, gold), ('gate2', 32.0, dist(-35), cream, cream), ('gate3', 57.0, dist(-26), cream, cream)):
        x, y = at(lon, d)
        r = facing_cam(x, y)
        box(name + '_body', x, y, 20, 3.5, 0, 8.5, body, r)
        box(name + '_arch', x, y - 0.0, 6, 3.7, 0, 6.0, dark, r)
        c, s = math.cos(r), math.sin(r)
        for ox, rr in ((0, 2.6), (-6.5, 1.6), (6.5, 1.6)):
            dome(f'{name}_dome{ox}', x, y, 8.5, rr, dm, r, (ox, 0))
        for ox in (-10.5, 10.5):
            cx, cy = x + ox * c, y + ox * s
            cyl(f'{name}_min{ox}', cx, cy, 0.9, 0, 12, body, seg=12)
            dome(f'{name}_mtop{ox}', cx, cy, 12, 1.0, dm)
    tent = mat('tent', '#8D9196', 0.75)
    stripe = mat('tent_stripe', '#B83A2C', 0.7)
    for name, lon, d, L in (('tent1', 19.0, dist(-27), 42), ('tent2', 30.0, dist(-22), 38)):
        x, y = at(lon, d)
        r = math.atan2(y - CAM.y, x - CAM.x)          # long axis points away from the balcony
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=4.5, radius2=4.5, depth=L)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
        bm.to_mesh(me); bm.free()
        me.materials.append(tent)
        o = bpy.data.objects.new(name, me)
        o.location = (x, y, 1.2); o.rotation_euler = (0, 0, r)
        link(o)
        box(name + '_skirt', x, y, L, 9.2, 0, 1.3, stripe, r)


def eucalyptus(proto_name='TREE_r_ph'):
    """dense eucalyptus plantation (dark band on the horizon): block e 380-560, n -30..110 from the land-cover map"""
    proto = bpy.data.objects.get(proto_name) or bpy.data.objects.get('TREE_r')
    if not proto:
        return 0
    random.seed(5)
    n = 0
    me = proto.data
    for gx in range(380, 560, 7):
        for gy in range(-30, 110, 7):
            x, y = gx + random.uniform(-3, 3), gy + random.uniform(-3, 3)
            o = bpy.data.objects.new(f'euc{n}', me)
            s = random.uniform(0.75, 1.0)
            o.scale = (s * 0.7, s * 0.7, s * 2.1)
            o.location = (x, y, 0)
            o.rotation_euler = (0, 0, random.uniform(0, 6.28))
            link(o)
            n += 1
    return n


def build():
    global COLL
    COLL = bpy.data.collections.get('LANDMARKS') or bpy.data.collections.new('LANDMARKS')
    if COLL.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(COLL)
    for o in list(COLL.objects):
        bpy.data.objects.remove(o)
    twin_towers(); under_construction(); future_corner(); far_towers()
    nh = houses(); party_plot(); ne = eucalyptus()
    return {'objects': len(COLL.objects), 'houses': nh, 'eucalyptus': ne}


def balcony_camera(name='cam_b1402', lens=16.0):
    """perspective camera at the photo position, for side-by-side checks against the real panorama"""
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    o = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if o.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(o)
    o.location = (CAM.x + 1.0, CAM.y, CAM_H)
    o.rotation_euler = (math.radians(90 - 12), 0, math.radians(-90))   # look east, 12 deg down
    return o
